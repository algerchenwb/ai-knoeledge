"""Fault injection for result scope, arithmetic and evidence binding."""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import unittest

from api_agent_demo import DemoService, parse_query
from business_result_contract import RECEIPTS, ContractError, validate_result, examples


class ContractChecks(unittest.TestCase):
    def setUp(self):
        self.service = DemoService()
        self.q = parse_query({"intent": "category_coverage", "region_id": "area-alpha", "population_type": 4,
            "start": "2026-09-01", "end_exclusive": "2026-10-01", "metric_version": "coverage-v1"})
        p = self.service.authenticate("Bearer demo-tenant-a")
        self.raw = self.service.execute(p, self.q)
        self.receipt = RECEIPTS[0]

    def reject(self, raw):
        with self.assertRaises(ContractError):
            validate_result(raw, self.q, self.receipt)

    def test_01_five_valid_results(self):
        results = examples()
        self.assertEqual([r["status"] for r in results], ["ok", "ok", "no_denominator", "no_denominator", "provisional"])
        self.assertEqual(results[1]["result"]["competitor_share"], 1)

    def test_02_wrong_region(self):
        self.raw["context"]["region_id"] = "area-beta"; self.reject(self.raw)

    def test_03_wrong_window(self):
        self.raw["context"]["window"]["end_exclusive"] = "2026-10-02"; self.reject(self.raw)

    def test_04_wrong_population(self):
        self.raw["context"]["population_type"] = 1; self.reject(self.raw)

    def test_05_wrong_metric_or_definition(self):
        for field in ("metric_version", "population_definition_version"):
            raw = deepcopy(self.raw); raw["context"][field] = "other"; self.reject(raw)

    def test_06_wrong_data_version(self):
        self.raw["context"]["data_version"] = "new-version"; self.reject(self.raw)

    def test_07_wrong_source_or_evidence_version(self):
        for field in ("source_id", "data_version"):
            raw = deepcopy(self.raw); raw["evidence"][0][field] = "other"; self.reject(raw)

    def test_08_missing_evidence(self):
        del self.raw["evidence"]; self.reject(self.raw)

    def test_09_wrong_ratio_and_nonfinite(self):
        for value in (.75, float("nan"), float("inf"), "0.5"):
            raw = deepcopy(self.raw); raw["result"]["ratio"] = value; self.reject(raw)

    def test_10_self_consistent_wrong_counts(self):
        self.raw["result"] = {"numerator": 1, "denominator": 2, "ratio": .5}
        self.reject(self.raw)

    def test_11_bool_or_negative_counts(self):
        for value in (True, -1):
            raw = deepcopy(self.raw); raw["result"]["numerator"] = value; self.reject(raw)

    def test_12_wrong_status(self):
        self.raw["status"] = "provisional"; self.reject(self.raw)

    def test_13_missing_explicit_null(self):
        receipt = RECEIPTS[-1]
        q = replace(self.q, region_id=receipt.region_id)
        raw = self.service.execute(self.service.authenticate("Bearer demo-tenant-a"), q)
        del raw["result"]
        with self.assertRaises(ContractError):
            validate_result(raw, q, receipt)

    def test_14_top_level_extras_filtered(self):
        self.raw["internal_token"] = "public-fake-secret"
        self.raw["answer"] = "无依据地宣称收益翻倍"
        result = validate_result(self.raw, self.q, self.receipt)
        self.assertEqual(set(result), {"status", "context", "result", "evidence"})
        self.assertNotIn("public-fake-secret", json.dumps(result))
        self.assertNotIn("收益", json.dumps(result, ensure_ascii=False))

    def test_15_nested_extra_rejected(self):
        self.raw["result"]["users"] = ["fictional-u1"]; self.reject(self.raw)

    def test_16_request_receipt_mismatch(self):
        with self.assertRaises(ContractError):
            validate_result(self.raw, replace(self.q, region_id="area-beta"), self.receipt)

    def test_17_invalid_receipt(self):
        with self.assertRaises(ContractError):
            validate_result(self.raw, self.q, replace(self.receipt, numerator=9))

    def test_18_huge_or_negative_ratio_rejected(self):
        for value in (2 ** 2000, -.5):
            raw = deepcopy(self.raw); raw["result"]["ratio"] = value; self.reject(raw)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ContractChecks))
    if not result.wasSuccessful():
        raise SystemExit(1)
    Path(__file__).with_name("business-result-contract-results.json").write_text(json.dumps(
        {"date": "2026-10-05", "checks_passed": result.testsRun,
         "scope": "offline synthetic outputs and hand-defined trusted receipts; no LLM, HTTP or real provenance service",
         "validated_results": examples()}, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
