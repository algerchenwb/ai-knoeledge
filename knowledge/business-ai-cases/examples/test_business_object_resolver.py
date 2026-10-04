"""Synthetic exact lookup and clarification lifecycle checks."""
from dataclasses import replace
import json
from pathlib import Path
import unittest

from business_object_resolver import Resolver, FIXTURES, fixture_access, ObjectRecord, example


class ResolverChecks(unittest.TestCase):
    def setUp(self):
        self.r, self.a = Resolver(), fixture_access()

    def test_01_alias_normalization(self):
        result, _ = self.r.resolve(self.a, "  ＸＨ   ＰＡＲＫ  ", "region")
        self.assertEqual(result["status"], "resolved")
        self.assertEqual(result["candidates"][0]["object_id"], "area-a")

    def test_02_same_name_does_not_select_first(self):
        result, _ = self.r.resolve(self.a, "星河", "region")
        self.assertEqual(result["status"], "needs_clarification")
        self.assertEqual([x["object_id"] for x in result["candidates"]], ["area-a", "area-b"])

    def test_03_city_and_type_narrowing(self):
        result, _ = self.r.resolve(self.a, "星河", "region", "乙城")
        self.assertEqual(result["candidates"][0]["object_id"], "area-b")
        result, _ = self.r.resolve(self.a, "星河", "poi", "甲城")
        self.assertEqual(result["candidates"][0]["object_id"], "poi-a")

    def test_04_not_found_after_lookup(self):
        result, _ = self.r.resolve(self.a, "未收录园区", "region")
        self.assertEqual(result["status"], "not_found")
        self.assertEqual(self.r.searches, 1)

    def test_05_no_cross_tenant_candidates(self):
        access = replace(self.a, object_ids=self.a.object_ids + ("area-hidden",))
        result, _ = self.r.resolve(access, "星河", "region", "甲城")
        self.assertEqual(len(result["candidates"]), 1)
        self.assertNotIn("area-hidden", json.dumps(result))

    def test_06_unauthorized_and_unknown_id_same_shape(self):
        self.assertEqual(self.r.resolve_id(self.a, "area-hidden"), self.r.resolve_id(self.a, "does-not-exist"))

    def test_07_inactive_excluded(self):
        self.assertEqual(self.r.resolve(self.a, "旧园", "region")[0]["status"], "not_found")
        self.assertEqual(self.r.resolve_id(self.a, "area-old")["status"], "not_found")

    def test_08_choice_must_be_presented_candidate(self):
        _, ticket = self.r.resolve(self.a, "星河", "region")
        self.assertEqual(self.r.choose(self.a, ticket, "area-b")["object_id"], "area-b")
        with self.assertRaisesRegex(ValueError, "INVALID_SELECTION"):
            self.r.choose(self.a, ticket, "poi-a")

    def test_09_changed_scope_rejects_ticket(self):
        _, ticket = self.r.resolve(self.a, "星河", "region")
        with self.assertRaisesRegex(ValueError, "STALE_ACCESS"):
            self.r.choose(replace(self.a, object_ids=("area-b",)), ticket, "area-b")

    def test_10_policy_version_rejects_ticket(self):
        _, ticket = self.r.resolve(self.a, "星河", "region")
        with self.assertRaisesRegex(ValueError, "STALE_ACCESS"):
            self.r.choose(replace(self.a, policy_version="v2"), ticket, "area-b")

    def test_11_catalog_update_rejects_ticket(self):
        _, ticket = self.r.resolve(self.a, "星河", "region")
        r = Resolver((replace(FIXTURES[0], version="2"), *FIXTURES[1:]))
        with self.assertRaisesRegex(ValueError, "STALE_CATALOG"):
            r.choose(self.a, ticket, "area-b")

    def test_12_truncation_requires_refinement(self):
        r = Resolver(max_candidates=1)
        result, ticket = r.resolve(self.a, "星河", "region")
        self.assertTrue(result["has_more"])
        with self.assertRaisesRegex(ValueError, "NEEDS_REFINEMENT"):
            r.choose(self.a, ticket, "area-a")

    def test_13_registration_and_invalid_input(self):
        with self.assertRaises(ValueError):
            Resolver((FIXTURES[0], FIXTURES[0]))
        for text in (" ", None, "a" * 81):
            with self.assertRaises(ValueError):
                self.r.resolve(self.a, text, "region")
        with self.assertRaises(ValueError):
            self.r.resolve(self.a, "星河", "table")

    def test_14_catalog_order_is_not_decision(self):
        r = Resolver(tuple(reversed(FIXTURES)))
        self.assertEqual(r.revision, self.r.revision)
        self.assertEqual(r.resolve(self.a, "星河", "region")[0], self.r.resolve(self.a, "星河", "region")[0])


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ResolverChecks))
    if not result.wasSuccessful():
        raise SystemExit(1)
    Path(__file__).with_name("business-object-results.json").write_text(json.dumps(
        {"date": "2026-10-05", "checks_passed": result.testsRun,
         "scope": "offline exact lookup and internal clarification tickets; no LLM, embeddings or Qdrant execution",
         "example": example()}, ensure_ascii=False, indent=2) + "\n")
