import copy
import json
import unittest
from offline_demo import (
    Principal, build_payload, execute_call, fake_generator, offline_rag, retrieve
)


class EvidenceTests(unittest.TestCase):
    def test_rag_query_retrieves_relevant_document(self):
        self.assertEqual(retrieve("RAG 检索原文证据")[0]["id"], "rag")

    def test_retrieved_text_is_actually_transmitted(self):
        evidence = retrieve("坐标系 GCJ-02")
        payload = build_payload("坐标系 GCJ-02", evidence)
        self.assertTrue(payload["input"]["evidence"])
        self.assertEqual(payload["input"]["evidence"][0]["text"], evidence[0]["text"])
        self.assertIn("GCJ-02", payload["input"]["evidence"][0]["text"])

    def test_unknown_query_abstains(self):
        payload, result = offline_rag("unicorn astrophysics")
        self.assertEqual(payload["input"]["evidence"], [])
        self.assertEqual(result["sources"], [])
        self.assertIn("无法确认", result["answer"])

    def test_removing_transmitted_context_changes_result(self):
        payload, result = offline_rag("RAG 检索原文证据")
        self.assertEqual(result["sources"], ["rag"])
        broken = copy.deepcopy(payload)
        broken["input"]["evidence"] = []
        self.assertEqual(fake_generator(broken)["sources"], [])

    def test_empty_query_and_invalid_k(self):
        self.assertEqual(retrieve(""), [])
        with self.assertRaises(ValueError):
            retrieve("RAG", k=0)


class ToolTests(unittest.TestCase):
    def setUp(self):
        self.principal = Principal("trusted-tenant", frozenset({"region-demo"}))
        self.args = {
            "region_id": "region-demo",
            "month": "2026-09",
            "population_type": "worker",
        }

    def call(self, args=None, name="query_region_population"):
        return {
            "name": name,
            "call_id": "call-42",
            "arguments": json.dumps(self.args if args is None else args),
        }

    def test_success_preserves_call_id_and_trusted_identity(self):
        output = execute_call(self.call(), self.principal)
        self.assertEqual(output["call_id"], "call-42")
        body = json.loads(output["output"])
        self.assertEqual(body["tenant_id"], "trusted-tenant")
        self.assertTrue(body["synthetic"])

    def test_unknown_tool_rejected(self):
        with self.assertRaises(ValueError):
            execute_call(self.call(name="delete_everything"), self.principal)

    def test_missing_field_rejected(self):
        args = dict(self.args)
        del args["month"]
        with self.assertRaises(ValueError):
            execute_call(self.call(args), self.principal)

    def test_extra_identity_field_rejected(self):
        args = dict(self.args, tenant_id="attacker-tenant")
        with self.assertRaises(ValueError):
            execute_call(self.call(args), self.principal)

    def test_invalid_month_and_enum_rejected(self):
        for args in [
            dict(self.args, month="2026-13"),
            dict(self.args, month="2026-9"),
            dict(self.args, population_type="anything"),
            dict(self.args, month=202609),
        ]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                execute_call(self.call(args), self.principal)

    def test_unauthorized_region_rejected(self):
        args = dict(self.args, region_id="other-region")
        with self.assertRaises(PermissionError):
            execute_call(self.call(args), self.principal)

    def test_invalid_json_and_envelope_rejected(self):
        call = self.call()
        call["arguments"] = "{broken"
        with self.assertRaises(ValueError):
            execute_call(call, self.principal)
        call = self.call()
        call["call_id"] = ""
        with self.assertRaises(ValueError):
            execute_call(call, self.principal)


if __name__ == "__main__":
    unittest.main()
