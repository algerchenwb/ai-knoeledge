"""Fault injection verifies the grader rejects plausible wrong outputs."""
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from business_golden_eval import load_dataset, evaluate, grade, summarize, run_case, Registry, fixture_access


class GraderChecks(unittest.TestCase):
    def setUp(self):
        self.data = load_dataset()
        self.case = self.data["cases"][0]
        self.r = Registry()
        self.output = run_case(self.r, fixture_access(self.r), self.case)

    def test_01_twelve_case_baseline(self):
        report = evaluate(self.data)
        self.assertEqual(report["summary"]["passed_cases"], 12)
        self.assertEqual(report["summary"]["gate"], "pass")
        self.assertEqual(report["summary"]["dimensions"]["evidence"]["applicable_cases"], 1)

    def test_02_wrong_route(self):
        self.output["value"]["route"]["tool_name"] = "region_competitor_overlap"
        row = grade(self.case, self.output)
        self.assertFalse(row["passed"])
        self.assertEqual([x["dimension"] for x in row["checks"] if not x["passed"]], ["route"])

    def test_03_wrong_ratio(self):
        self.output["value"]["business"]["result"]["ratio"] = .75
        self.assertFalse(grade(self.case, self.output)["passed"])

    def test_04_bool_is_not_count_and_nan_is_not_ratio(self):
        for field, value in (("numerator", True), ("ratio", float("nan")), ("ratio", float("inf"))):
            output = deepcopy(self.output)
            output["value"]["business"]["result"][field] = value
            self.assertFalse(grade(self.case, output)["passed"])

    def test_05_missing_or_wrong_evidence(self):
        for evidence in ([], [{"source_id": "wrong", "data_version": "synthetic-2026-09"}]):
            output = deepcopy(self.output)
            output["value"]["business"]["evidence"] = evidence
            self.assertFalse(grade(self.case, output)["passed"])

    def test_06_missing_null_is_not_null(self):
        case = self.data["cases"][2]
        output = run_case(self.r, fixture_access(self.r), case)
        self.assertTrue(grade(case, output)["passed"])
        del output["value"]["business"]["result"]["ratio"]
        self.assertFalse(grade(case, output)["passed"])

    def test_07_error_stage_and_critical_gate(self):
        case = self.data["cases"][5]
        output = {"kind": "error", "stage": "plan", "code": "OBJECT_FORBIDDEN"}
        row = grade(case, output)
        summary = summarize([row])
        self.assertEqual(summary["critical_failures"], ["cross-tenant"])
        self.assertEqual(summary["gate"], "fail")

    def test_08_assertion_count_does_not_weight_case(self):
        row = grade(self.case, self.output)
        summary = summarize([row])
        self.assertEqual(summary["dimensions"]["business"]["applicable_cases"], 1)
        bad = deepcopy(row); bad["checks"][0]["passed"] = False; bad["passed"] = False
        self.assertEqual(summarize([row, bad])["dimensions"]["business"], {"passed_cases": 1, "applicable_cases": 2})

    def test_09_dataset_fingerprint_tracks_labels(self):
        original = evaluate(self.data)
        altered = deepcopy(self.data)
        altered["cases"][0]["checks"][-1]["expected"] = "other-version"
        report = evaluate(altered)
        self.assertNotEqual(original["dataset_sha256"], report["dataset_sha256"])
        self.assertEqual(report["summary"]["gate"], "fail")

    def test_10_duplicate_and_empty_dataset_rejected(self):
        with TemporaryDirectory() as d:
            path = Path(d) / "bad.json"
            for cases in ([], [self.case, self.case]):
                path.write_text(json.dumps({**self.data, "cases": cases}))
                with self.assertRaises(ValueError):
                    load_dataset(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
