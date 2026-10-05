import json
import platform
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from customer_data_import import Actor, Importer, MAPPING, CSV_TEXT, examples


class Checks(unittest.TestCase):
    def setUp(self):
        self.i, self.actor = Importer(), Actor("a", "operator")
        self.i.grant(self.actor, {"area-a", "area-b"})

    def preview(self, text=CSV_TEXT, mapping=None, now=100):
        return self.i.preview(self.actor, text, MAPPING if mapping is None else mapping, now)

    def test_preview_no_write(self):
        p = self.preview()
        self.assertEqual((p["status"], p["accepted_rows"]), ("ready", 2))
        self.assertEqual(self.i.records, {})

    def test_commit_counts(self):
        p = self.preview()
        r = self.i.commit(self.actor, p["plan_id"], 101)
        self.assertEqual((r["rows_written"], r["dataset_version"]), (2, 1))
        self.assertEqual(self.i.records["a"][("area-a", 4, "2026-09-30")]["population_count"], 100)

    def test_retry_writes_once(self):
        p = self.preview()
        self.i.commit(self.actor, p["plan_id"], 101)
        r = self.i.commit(self.actor, p["plan_id"], 102)
        self.assertTrue(r["replayed"])
        self.assertEqual(len(self.i.records["a"]), 2)
        self.assertEqual(self.i.versions["a"], 1)

    def test_atomic_reject_partial(self):
        p = self.preview(CSV_TEXT + "area-a,2,2026-09-30,-5\n")
        self.assertEqual((p["status"], p["accepted_rows"]), ("invalid", 2))
        with self.assertRaises(ValueError):
            self.i.commit(self.actor, p["plan_id"], 101)
        self.assertEqual(self.i.records, {})

    def test_population_enum(self):
        p = self.preview("地点,人群类型,日期,人数\narea-a,5,2026-09-30,3\n")
        self.assertEqual(p["errors"][0]["code"], "population_type")

    def test_bad_date(self):
        for day in ("2026-02-30", "20260930"):
            p = self.preview(f"地点,人群类型,日期,人数\narea-a,4,{day},3\n")
            self.assertEqual(p["errors"][0]["code"], "snapshot_date")

    def test_count_integer_and_bound(self):
        for count in ("1.2", "-3", "1000000000", ""):
            p = self.preview(f"地点,人群类型,日期,人数\narea-a,4,2026-09-30,{count}\n")
            self.assertEqual(p["errors"][0]["code"], "population_count")

    def test_duplicate_in_file(self):
        p = self.preview(CSV_TEXT + "area-a,4,2026-09-30,100\n")
        self.assertEqual(p["errors"][0]["code"], "duplicate_key")

    def test_existing_key_not_overwritten(self):
        p = self.preview()
        self.i.commit(self.actor, p["plan_id"], 101)
        p2 = self.preview()
        self.assertEqual(len(p2["errors"]), 2)

    def test_object_not_allowed_no_raw_echo(self):
        p = self.preview("地点,人群类型,日期,人数\nsecret-object,4,2026-09-30,1\n")
        self.assertEqual(p["errors"], [{"record_number": 2, "code": "object_not_allowed"}])

    def test_duplicate_header(self):
        with self.assertRaises(ValueError):
            self.preview("地点,地点,日期,人数\n")

    def test_missing_or_extra_cells(self):
        for row in ("area-a,4,2026-09-30", "area-a,4,2026-09-30,1,extra"):
            p = self.preview("地点,人群类型,日期,人数\n" + row + "\n")
            self.assertEqual(p["errors"][0]["code"], "cell_count")

    def test_mapping_one_to_one(self):
        bad = {**MAPPING, "人数": "population_type"}
        with self.assertRaises(ValueError):
            self.preview(mapping=bad)

    def test_bom_whitespace(self):
        p = self.preview("\ufeff 地点 , 人群类型 , 日期 , 人数 \n area-a , 4 , 2026-09-30 , 0 \n")
        self.assertEqual((p["status"], p["accepted_rows"]), ("ready", 1))

    def test_expiry_boundary(self):
        p = self.preview()
        for now in (99, 400):
            with self.assertRaises(ValueError):
                self.i.commit(self.actor, p["plan_id"], now)

    def test_grant_revision_changed(self):
        p = self.preview()
        self.i.grant(self.actor, {"area-a"})
        with self.assertRaises(ValueError):
            self.i.commit(self.actor, p["plan_id"], 101)

    def test_dataset_changed_requires_preview(self):
        first = self.preview()
        second = self.preview("地点,人群类型,日期,人数\narea-a,1,2026-09-30,1\n")
        self.i.commit(self.actor, first["plan_id"], 101)
        with self.assertRaises(ValueError):
            self.i.commit(self.actor, second["plan_id"], 102)

    def test_actor_and_tenant_binding(self):
        p = self.preview()
        for actor in (Actor("b", "operator"), Actor("a", "other")):
            self.i.grant(actor, {"area-a", "area-b"})
            with self.assertRaises(ValueError):
                self.i.commit(actor, p["plan_id"], 101)

    def test_size_and_empty(self):
        for text in ("", "地点,人群类型,日期,人数\n", "x" * 65537):
            with self.assertRaises(ValueError):
                self.preview(text)

    def test_parallel_duplicate_commit(self):
        p, gate = self.preview(), threading.Barrier(2)
        def worker():
            gate.wait(timeout=5)
            return self.i.commit(self.actor, p["plan_id"], 101)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: worker(), range(2)))
        self.assertEqual(sorted(r["replayed"] for r in results), [False, True])
        self.assertEqual(self.i.versions["a"], 1)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    if not result.wasSuccessful():
        raise SystemExit(1)
    report = {"date": "2026-10-05", "python": platform.python_version(), "checks_passed": result.testsRun,
              "examples": examples(), "limitations": "synthetic authorized objects; in-memory state and one-process lock; no LLM, real authentication, persistent storage or Frictionless execution"}
    Path(__file__).with_name("customer-data-import-results.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
