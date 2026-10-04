"""Registry boundary checks; no LLM routing accuracy is measured."""
from dataclasses import replace
import json
from pathlib import Path
import unittest

from tool_registry_demo import Registry, DEFAULT_TOOLS, Access, Plan, BusinessError, proposal, fixture_access, examples


class RegistryChecks(unittest.TestCase):
    def setUp(self):
        self.r = Registry()
        self.a = fixture_access(self.r)

    def error(self, code, function):
        with self.assertRaises(BusinessError) as caught:
            function()
        self.assertEqual(caught.exception.code, code)

    def test_01_coverage_result(self):
        result = self.r.execute(self.a, self.r.plan(self.a, proposal()))
        self.assertEqual(result["business"]["result"]["ratio"], .5)
        self.assertEqual(result["route"]["tool_name"], "region_category_coverage")

    def test_02_overlap_direction(self):
        result = self.r.execute(self.a, self.r.plan(self.a, proposal("overlap", competitor_id="poi-rival")))
        self.assertEqual(result["business"]["result"]["reference_share"], .5)
        self.assertEqual(result["business"]["result"]["competitor_share"], 1)

    def test_03_manifest_permissions(self):
        access = replace(self.a, tool_names=(DEFAULT_TOOLS[0].name,))
        self.assertEqual([s["name"] for s in self.r.manifest(access)], [DEFAULT_TOOLS[0].name])
        self.error("CAPABILITY_FORBIDDEN", lambda: self.r.plan(access, proposal("overlap", competitor_id="poi-rival")))

    def test_04_disabled_is_unsupported(self):
        r = Registry((replace(DEFAULT_TOOLS[0], enabled=False),))
        self.assertEqual(r.manifest(self.a), [])
        self.error("UNSUPPORTED_TASK", lambda: r.plan(self.a, proposal()))

    def test_05_available_is_separate(self):
        r = Registry((replace(DEFAULT_TOOLS[0], available=False),))
        self.assertEqual(r.manifest(self.a), [])
        self.error("CAPABILITY_UNAVAILABLE", lambda: r.plan(self.a, proposal()))

    def test_06_no_fallback_for_unsupported(self):
        self.error("UNSUPPORTED_TASK", lambda: self.r.plan(self.a, proposal("trend")))
        p = proposal(); p["object_type"] = "poi"
        self.error("UNSUPPORTED_TASK", lambda: self.r.plan(self.a, p))

    def test_07_ambiguity_does_not_select_first(self):
        other = replace(DEFAULT_TOOLS[0], name="other_coverage")
        a = replace(self.a, tool_names=self.a.tool_names + (other.name,))
        for specs in ((DEFAULT_TOOLS[0], other), (other, DEFAULT_TOOLS[0])):
            r = Registry(specs)
            self.error("NEEDS_CLARIFICATION", lambda: r.plan(a, proposal()))

    def test_08_duplicate_and_write_registration(self):
        for specs in ((DEFAULT_TOOLS[0], DEFAULT_TOOLS[0]),
                      (replace(DEFAULT_TOOLS[0], effect="write"),),
                      (replace(DEFAULT_TOOLS[0], intent="delete_all"),),
                      (replace(DEFAULT_TOOLS[0], enabled=1),)):
            with self.assertRaises(ValueError):
                Registry(specs)

    def test_09_parameter_injection(self):
        for key in ("tenant_id", "url", "tool_name", "metric_version", "intent"):
            self.error("INVALID_PARAMETERS", lambda: self.r.plan(self.a, proposal(**{key: "injected"})))

    def test_10_business_input_validation(self):
        self.error("INVALID_POPULATION", lambda: self.r.plan(self.a, proposal(population_type=True)))
        self.error("MISSING_COMPETITOR", lambda: self.r.plan(self.a, proposal("overlap")))
        self.error("INVALID_WINDOW", lambda: self.r.plan(self.a, proposal(start="2026-10-01")))

    def test_11_capability_is_not_object_authorization(self):
        plan = self.r.plan(self.a, proposal(region_id="area-beta"))
        self.error("OBJECT_FORBIDDEN", lambda: self.r.execute(self.a, plan))

    def test_12_revoked_access_blocks_old_plan(self):
        plan = self.r.plan(self.a, proposal())
        self.error("CAPABILITY_FORBIDDEN", lambda: self.r.execute(replace(self.a, tool_names=()), plan))

    def test_13_version_change_blocks_plan(self):
        plan = self.r.plan(self.a, proposal())
        r = Registry((replace(DEFAULT_TOOLS[0], tool_version="2"), DEFAULT_TOOLS[1]))
        self.error("STALE_PLAN", lambda: r.execute(self.a, plan))

    def test_14_tampered_plan(self):
        plan = self.r.plan(self.a, proposal())
        for change in ({"tool_name": "other"}, {"tool_version": "2"},
                       {"query_json": "{}"}):
            self.error("PLAN_MISMATCH", lambda: self.r.execute(self.a, replace(plan, **change)))

    def test_15_plan_copies_proposal(self):
        p = proposal(); plan = self.r.plan(self.a, p)
        p["parameters"]["region_id"] = "area-beta"
        self.assertEqual(self.r.execute(self.a, plan)["business"]["result"]["ratio"], .5)

    def test_16_order_independent_revision(self):
        r = Registry(tuple(reversed(DEFAULT_TOOLS)))
        self.assertEqual(r.revision, self.r.revision)
        self.assertEqual(r.manifest(self.a), self.r.manifest(self.a))

    def test_17_data_status_survives_routing(self):
        for region, status in (("area-empty", "no_denominator"), ("area-provisional", "provisional")):
            output = self.r.execute(self.a, self.r.plan(self.a, proposal(region_id=region)))
            self.assertEqual(output["business"]["status"], status)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(RegistryChecks))
    if not result.wasSuccessful():
        raise SystemExit(1)
    Path(__file__).with_name("tool-registry-results.json").write_text(
        json.dumps({"date": "2026-10-04", "checks_passed": result.testsRun,
                    "scope": "offline synthetic registry and reused business adapters; no LLM or HTTP",
                    "examples": examples()}, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
