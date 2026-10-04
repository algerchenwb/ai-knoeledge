"""Fake-clock cache invariants and business invalidation checks."""
from dataclasses import replace
import json
from pathlib import Path
import unittest

from api_agent_demo import BusinessError
from business_cache_demo import CachedBusiness, ResultCache, fixture_query, example


class CacheChecks(unittest.TestCase):
    def setUp(self):
        self.now = [0.0]
        self.app = CachedBusiness(cache=ResultCache(timer=lambda: self.now[0]))
        self.p = self.app.demo.authenticate("Bearer demo-tenant-a")

    def test_01_hit_and_exact_ttl_boundary(self):
        self.assertEqual([x["cache"]["status"] for x in example()["events"]], ["miss", "hit", "miss"])
        self.assertEqual(example()["executions"], 2)

    def test_02_normalized_defaults(self):
        q = fixture_query(); self.app.query(self.p, q)
        q["max_tool_calls"] = 2
        self.assertEqual(self.app.query(self.p, q)["cache"]["status"], "hit")

    def test_03_data_revision_invalidates(self):
        self.app.query(self.p, fixture_query())
        key = ("tenant-a", "area-alpha")
        self.app.demo.snapshots[key] = replace(self.app.demo.snapshots[key], data_version="synthetic-r2", category_visitors=("u1",))
        output = self.app.query(self.p, fixture_query())
        self.assertEqual(output["cache"]["status"], "miss")
        self.assertEqual(output["business"]["result"]["ratio"], .25)

    def test_04_policy_revision_and_scope_in_identity(self):
        self.app.query(self.p, fixture_query())
        self.assertEqual(self.app.query(self.p, fixture_query(), permission_revision="fixture-policy-v2")["cache"]["status"], "miss")
        self.assertEqual(self.app.query(replace(self.p, regions=("area-alpha",)), fixture_query())["cache"]["status"], "miss")

    def test_05_revocation_before_lookup(self):
        self.app.query(self.p, fixture_query())
        with self.assertRaises(BusinessError) as caught:
            self.app.query(replace(self.p, regions=()), fixture_query())
        self.assertEqual(caught.exception.code, "OBJECT_FORBIDDEN")

    def test_06_competitor_revocation_before_lookup(self):
        q = {**fixture_query(), "intent": "co_visit", "metric_version": "co-visit-v1", "competitor_id": "poi-rival"}
        self.app.query(self.p, q)
        del self.app.demo.competitors[("tenant-a", "poi-rival")]
        with self.assertRaises(BusinessError) as caught:
            self.app.query(self.p, q)
        self.assertEqual(caught.exception.code, "COMPETITOR_FORBIDDEN")

    def test_07_non_ok_not_cached(self):
        for region in ("area-empty", "area-provisional"):
            for _ in range(2):
                output = self.app.query(self.p, {**fixture_query(), "region_id": region})
                self.assertEqual(output["cache"]["status"], "bypass")
        self.assertEqual(self.app.executions, 4)
        self.assertEqual(len(self.app.cache.entries), 0)

    def test_08_unavailable_never_serves_old_hit(self):
        self.app.query(self.p, fixture_query())
        key = ("tenant-a", "area-alpha")
        self.app.demo.snapshots[key] = replace(self.app.demo.snapshots[key], available=False)
        with self.assertRaises(BusinessError) as caught:
            self.app.query(self.p, fixture_query())
        self.assertEqual(caught.exception.code, "UPSTREAM_UNAVAILABLE")

    def test_09_invalid_window_and_budget_do_not_reuse(self):
        self.app.query(self.p, fixture_query())
        for changes, code in (({"start": "2026-09-02"}, "DATA_SCOPE_MISMATCH"), ({"max_tool_calls": 1}, "TOOL_BUDGET_EXCEEDED")):
            with self.assertRaises(BusinessError) as caught:
                self.app.query(self.p, {**fixture_query(), **changes})
            self.assertEqual(caught.exception.code, code)

    def test_10_mutation_does_not_change_stored_result(self):
        output = self.app.query(self.p, fixture_query())
        output["business"]["result"]["ratio"] = 99
        hit = self.app.query(self.p, fixture_query())
        self.assertEqual(hit["business"]["result"]["ratio"], .5)
        hit["business"]["result"]["ratio"] = 98
        self.assertEqual(self.app.query(self.p, fixture_query())["business"]["result"]["ratio"], .5)

    def test_11_bounded_lru_and_expiration(self):
        c = ResultCache(max_entries=2, timer=lambda: self.now[0])
        c.put("a", 1); c.put("b", 2); c.get("a"); c.put("c", 3)
        self.assertIsNone(c.get("b"))
        self.assertEqual(c.get("a")[0], 1)
        self.now[0] = 5; c.expire()
        self.assertEqual(len(c.entries), 0)

    def test_12_configuration_and_tenant_separation(self):
        for kwargs in ({"ttl": 0}, {"ttl": float("nan")}, {"max_entries": True}):
            with self.assertRaises(ValueError):
                ResultCache(**kwargs)
        self.app.query(self.p, fixture_query())
        pb = self.app.demo.authenticate("Bearer demo-tenant-b")
        output = self.app.query(pb, {**fixture_query(), "region_id": "area-beta"})
        self.assertEqual(output["cache"]["status"], "miss")
        self.assertEqual(output["business"]["result"]["ratio"], 0)

    def test_13_competitor_data_invalidates(self):
        q = {**fixture_query(), "intent": "co_visit", "metric_version": "co-visit-v1", "competitor_id": "poi-rival"}
        self.app.query(self.p, q)
        self.app.demo.competitors[("tenant-a", "poi-rival")] = ("u1",)
        output = self.app.query(self.p, q)
        self.assertEqual(output["cache"]["status"], "miss")
        self.assertEqual(output["business"]["result"]["overlap"], 1)
        self.assertEqual(output["business"]["result"]["reference_share"], .25)

    def test_14_snapshot_definition_change(self):
        self.app.query(self.p, fixture_query())
        key = ("tenant-a", "area-alpha")
        self.app.demo.snapshots[key] = replace(self.app.demo.snapshots[key], definition_version="old-population")
        with self.assertRaises(BusinessError) as caught:
            self.app.query(self.p, fixture_query())
        self.assertEqual(caught.exception.code, "DATA_DEFINITION_MISMATCH")


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CacheChecks))
    if not result.wasSuccessful():
        raise SystemExit(1)
    Path(__file__).with_name("business-cache-results.json").write_text(json.dumps(
        {"date": "2026-10-05", "checks_passed": result.testsRun,
         "scope": "single-process sequential fake-clock fixture checks; no distributed cache or real backend",
         "example": example()}, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
