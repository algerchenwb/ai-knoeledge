"""Real loopback HTTP tests; no external API, database or language model."""
import json
from pathlib import Path
import sys
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from api_agent_demo import make_server


def proposal(**changes):
    data = {"intent": "category_coverage", "region_id": "area-alpha", "population_type": 4,
            "start": "2026-09-01", "end_exclusive": "2026-10-01", "metric_version": "coverage-v1"}
    return {**data, **changes}


def post(url, data, token="demo-tenant-a", raw=False, content_type="application/json"):
    body = data.encode() if raw else json.dumps(data).encode()
    headers = {"Content-Type": content_type}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(url, data=body, headers=headers, method="POST")
    try:
        response = urlopen(req, timeout=5)
    except HTTPError as e:
        response = e
    with response:
        return response.status, json.loads(response.read()), dict(response.headers)


class HTTPBusinessChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = make_server()
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}/v1/agent/query"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join(3)
        cls.server.server_close()

    def test_01_coverage_http(self):
        status, result, _ = post(self.url, proposal())
        self.assertEqual(status, 200)
        self.assertEqual(result["result"], {"numerator": 2, "denominator": 4, "ratio": .5})
        self.assertEqual([s["tool"] for s in result["trace"]], ["resolve_authorized_snapshot", "calculate_category_coverage"])
        self.assertEqual(result["context"]["metric_version"], "coverage-v1")
        self.assertEqual(result["evidence"][0]["data_version"], result["context"]["data_version"])

    def test_02_co_visit_direction(self):
        status, result, _ = post(self.url, proposal(intent="co_visit", competitor_id="poi-rival", metric_version="co-visit-v1"))
        self.assertEqual(status, 200)
        self.assertEqual(result["result"], {"competitor_id": "poi-rival", "overlap": 2, "reference_share": .5, "competitor_share": 1.0})

    def test_03_missing_identity(self):
        status, result, headers = post(self.url, proposal(), token=None)
        self.assertEqual(status, 401)
        self.assertEqual(headers["WWW-Authenticate"], "Bearer")
        self.assertEqual(result["error"]["code"], "UNAUTHENTICATED")

    def test_04_invalid_identity(self):
        self.assertEqual(post(self.url, proposal(), token="unknown")[0], 401)

    def test_05_tenant_isolation(self):
        status, result, _ = post(self.url, proposal(region_id="area-beta"))
        self.assertEqual(status, 403)
        self.assertNotIn("result", result)
        allowed, response, _ = post(self.url, proposal(region_id="area-beta"), token="demo-tenant-b")
        self.assertEqual(allowed, 200)
        self.assertEqual(response["result"]["denominator"], 1)
        self.assertEqual(response["result"]["ratio"], 0)

    def test_06_identity_injection_rejected(self):
        status, result, _ = post(self.url, proposal(tenant_id="tenant-b"))
        self.assertEqual((status, result["error"]["code"]), (422, "INVALID_FIELDS"))

    def test_07_bool_not_integer(self):
        status, result, _ = post(self.url, proposal(population_type=True))
        self.assertEqual((status, result["error"]["code"]), (422, "INVALID_POPULATION"))

    def test_08_invalid_dates(self):
        for dates in [{"start": "2026-09-31"}, {"end_exclusive": "2026-09-01"}, {"start": "2026-01-01"}, {"start": "20260901"}]:
            with self.subTest(dates=dates):
                self.assertEqual(post(self.url, proposal(**dates))[0], 422)

    def test_09_window_not_covered(self):
        status, result, _ = post(self.url, proposal(start="2026-09-02"))
        self.assertEqual((status, result["error"]["code"]), (409, "DATA_SCOPE_MISMATCH"))

    def test_10_population_not_covered(self):
        self.assertEqual(post(self.url, proposal(population_type=1))[0], 409)

    def test_11_metric_version(self):
        status, result, _ = post(self.url, proposal(metric_version="made-up"))
        self.assertEqual((status, result["error"]["code"]), (409, "METRIC_VERSION_MISMATCH"))

    def test_12_snapshot_definition(self):
        status, result, _ = post(self.url, proposal(region_id="area-version-mismatch"))
        self.assertEqual((status, result["error"]["code"]), (409, "DATA_DEFINITION_MISMATCH"))

    def test_13_empty_denominator(self):
        status, result, _ = post(self.url, proposal(region_id="area-empty"))
        self.assertEqual((status, result["status"]), (200, "no_denominator"))
        self.assertIsNone(result["result"]["ratio"])

    def test_14_provisional(self):
        status, result, _ = post(self.url, proposal(region_id="area-provisional"))
        self.assertEqual((status, result["status"]), (200, "provisional"))
        self.assertIsNone(result["result"])
        self.assertEqual(len(result["trace"]), 1)

    def test_15_budget(self):
        status, result, _ = post(self.url, proposal(max_tool_calls=1))
        self.assertEqual((status, result["error"]["code"]), (429, "TOOL_BUDGET_EXCEEDED"))

    def test_16_upstream_failure(self):
        status, result, _ = post(self.url, proposal(region_id="area-unavailable"))
        self.assertEqual((status, result["error"]["code"]), (502, "UPSTREAM_UNAVAILABLE"))

    def test_17_competitor_scope(self):
        status, result, _ = post(self.url, proposal(intent="co_visit", metric_version="co-visit-v1", competitor_id="unknown"))
        self.assertEqual((status, result["error"]["code"]), (403, "COMPETITOR_FORBIDDEN"))

    def test_18_invalid_json(self):
        for raw in ["{", '{"intent":NaN}', '{"intent":"co_visit","intent":"category_coverage"}']:
            with self.subTest(raw=raw):
                self.assertEqual(post(self.url, raw, raw=True)[0], 400)

    def test_19_media_and_size(self):
        self.assertEqual(post(self.url, proposal(), content_type="text/plain")[0], 415)
        self.assertEqual(post(self.url, " " * 17000, raw=True)[0], 413)

    def test_20_unsupported_or_incomplete_intent(self):
        for change in [{"intent": "send_campaign"}, {"intent": "co_visit", "metric_version": "co-visit-v1"}, {"competitor_id": "poi-rival"}]:
            self.assertEqual(post(self.url, proposal(**change))[0], 422)

    def test_21_no_raw_user_or_token_leak(self):
        status, result, _ = post(self.url, proposal())
        serialized = json.dumps(result)
        for value in ['"u1"', '"u2"', '"u9"', "demo-tenant-a"]:
            self.assertNotIn(value, serialized)
        self.assertEqual(status, 200)

    def test_22_request_id_and_unknown_scope(self):
        a = post(self.url, proposal())[1]
        b = post(self.url, proposal())[1]
        self.assertEqual(len(a["request_id"]), 32)
        self.assertNotEqual(a["request_id"], b["request_id"])
        hidden = post(self.url, proposal(region_id="area-beta"))[1]["error"]
        unknown = post(self.url, proposal(region_id="not-an-object"))[1]["error"]
        self.assertEqual(hidden, unknown)

    def test_23_empty_competitor(self):
        status, response, _ = post(self.url, proposal(intent="co_visit", competitor_id="poi-empty", metric_version="co-visit-v1"))
        self.assertEqual((status, response["status"]), (200, "no_denominator"))
        self.assertEqual(response["result"]["reference_share"], 0)
        self.assertIsNone(response["result"]["competitor_share"])


def record():
    server = make_server()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}/v1/agent/query"
    results = []
    try:
        scenarios = [proposal(), proposal(intent="co_visit", competitor_id="poi-rival", metric_version="co-visit-v1"),
                     proposal(region_id="area-empty"), proposal(region_id="area-provisional"), proposal(region_id="area-beta")]
        for data in scenarios:
            status, body, _ = post(url, data)
            body.pop("request_id")  # Dynamic IDs are checked separately; omit for stable output.
            results.append({"request": data, "http_status": status, "response": body})
    finally:
        server.shutdown()
        thread.join(3)
        server.server_close()
    Path(__file__).with_name("api-agent-http-results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    if "--record" in sys.argv:
        sys.argv.remove("--record")
        record()
    unittest.main(verbosity=2)
