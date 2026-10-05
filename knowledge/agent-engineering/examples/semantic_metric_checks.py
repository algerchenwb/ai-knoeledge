"""Original SQLite fixtures for cohort metrics; not MetricFlow execution."""
from dataclasses import dataclass, replace
from datetime import date
from fractions import Fraction
import sqlite3
import unittest


@dataclass(frozen=True)
class Context:
    tenant: str = "A"
    start: str = "2026-07-03"
    end: str = "2026-10-01"  # Exclusive; exactly 90 calendar days.
    population: str = "visitor"
    definition: str = "category_coverage_v1"
    snapshot: str = "snapshot-1"

    def validate(self):
        start, end = date.fromisoformat(self.start), date.fromisoformat(self.end)
        if start.isoformat() != self.start or end.isoformat() != self.end:
            raise ValueError("canonical ISO dates required")
        if not 0 < (end - start).days <= 90:
            raise ValueError("window must be 1..90 calendar days")


def coverage(db, context, regions, complete=True):
    context.validate()
    if not regions:
        raise ValueError("explicit nonempty region selection required")
    placeholders = ",".join("?" for _ in regions)
    sql = f"""
        WITH cohort AS (
            SELECT DISTINCT person FROM area_events
            WHERE tenant=? AND day>=? AND day<? AND population=?
              AND region IN ({placeholders}) AND person IS NOT NULL
        ), reached AS (
            SELECT DISTINCT c.person FROM cohort c
            WHERE EXISTS (
                SELECT 1 FROM category_events v
                WHERE v.tenant=? AND v.day>=? AND v.day<?
                  AND v.category='4S' AND v.person=c.person
            )
        )
        SELECT (SELECT COUNT(*) FROM reached), (SELECT COUNT(*) FROM cohort)
    """
    n, d = db.execute(sql, (context.tenant, context.start, context.end, context.population,
                           *regions, context.tenant, context.start, context.end)).fetchone()
    status = "partial" if not complete else "no_denominator" if d == 0 else "ok"
    return {"numerator": n, "denominator": d, "ratio": Fraction(n, d) if status == "ok" else None,
            "status": status, "context": context}


def assert_comparable(left, right):
    # Region selection may differ; all other semantic context must match.
    if left["context"] != right["context"] or left["status"] != "ok" or right["status"] != "ok":
        raise ValueError("incompatible or incomplete comparison")


class Checks(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.executescript("""
            CREATE TABLE area_events(tenant TEXT, region TEXT, person TEXT, day TEXT, population TEXT);
            CREATE TABLE category_events(tenant TEXT, person TEXT, day TEXT, category TEXT);
            CREATE TABLE person_tags(person TEXT, tag TEXT);
        """)
        self.ctx = Context()
        self.db.executemany("INSERT INTO area_events VALUES(?,?,?,?,?)", [
            ("A", "R1", "u1", "2026-07-03", "visitor"),
            ("A", "R1", "u1", "2026-08-01", "visitor"),
            ("A", "R1", "u2", "2026-08-01", "visitor"),
            ("A", "R1", "u3", "2026-09-30", "visitor"),
            ("A", "R2", "u1", "2026-08-01", "visitor"),
            ("A", "R2", "u4", "2026-08-01", "visitor"),
            ("A", "R2", "u5", "2026-08-01", "visitor"),
            ("A", "R1", "resident", "2026-08-01", "resident"),
            ("B", "R1", "other", "2026-08-01", "visitor"),
            ("A", "R1", "end_boundary", "2026-10-01", "visitor"),
            ("A", "R1", "before_start", "2026-07-02", "visitor"),
            ("A", "R1", None, "2026-08-01", "visitor"),
        ])
        self.db.executemany("INSERT INTO category_events VALUES(?,?,?,?)", [
            ("A", "u1", "2026-08-01", "4S"),
            ("A", "u1", "2026-08-02", "4S"),
            ("A", "u4", "2026-08-01", "4S"),
            ("A", "outside", "2026-08-01", "4S"),
            ("B", "u2", "2026-08-01", "4S"),
            ("A", "u2", "2026-10-01", "4S"),
            ("A", "u3", "2026-08-01", "restaurant"),
        ])
        self.db.executemany("INSERT INTO person_tags VALUES(?,?)", [
            ("u1", "x"), ("u1", "y"), ("u2", "x"), ("u3", "x")])

    def tearDown(self):
        self.db.close()

    def result(self, regions, **kwargs):
        return coverage(self.db, self.ctx, regions, **kwargs)

    def test_01_r1_distinct_cohort(self):
        r = self.result(["R1"])
        self.assertEqual((r["numerator"], r["denominator"], r["ratio"]), (1, 3, Fraction(1, 3)))

    def test_02_r2_distinct_cohort(self):
        self.assertEqual(self.result(["R2"])["ratio"], Fraction(2, 3))

    def test_03_global_union_recomputed(self):
        r = self.result(["R1", "R2"])
        self.assertEqual((r["numerator"], r["denominator"], r["ratio"]), (2, 5, Fraction(2, 5)))

    def test_04_group_counts_not_additive(self):
        rows = [self.result([region]) for region in ("R1", "R2")]
        self.assertEqual(sum(r["denominator"] for r in rows), 6)
        self.assertEqual(sum(r["numerator"] for r in rows), 3)
        self.assertNotEqual(Fraction(3, 6), self.result(["R1", "R2"])["ratio"])

    def test_05_average_and_pooled_ratio_for_disjoint_groups(self):
        # Separate hand fixture: groups are disjoint, sizes 10 and 90.
        self.assertEqual((Fraction(1, 10) + Fraction(45, 90)) / 2, Fraction(3, 10))
        self.assertEqual(Fraction(1 + 45, 10 + 90), Fraction(23, 50))

    def test_06_join_fanout_inflates_rows(self):
        raw, distinct_people = self.db.execute("""
            SELECT COUNT(*), COUNT(DISTINCT e.person)
            FROM area_events e JOIN person_tags t ON e.person=t.person
            WHERE e.tenant='A' AND e.region='R1' AND e.population='visitor'
              AND e.day>='2026-07-03' AND e.day<'2026-10-01'
        """).fetchone()
        self.assertEqual((raw, distinct_people), (6, 3))

    def test_07_duplicate_visits_do_not_inflate_numerator(self):
        self.db.execute("INSERT INTO category_events VALUES('A','u1','2026-08-01','4S')")
        self.assertEqual(self.result(["R1"])["numerator"], 1)

    def test_08_half_open_window(self):
        self.assertEqual(self.result(["R1"])["denominator"], 3)
        self.assertEqual((date.fromisoformat(self.ctx.end) - date.fromisoformat(self.ctx.start)).days, 90)

    def test_09_tenant_and_population_filters(self):
        self.assertEqual(coverage(self.db, replace(self.ctx, tenant="B"), ["R1"])["denominator"], 1)
        self.assertEqual(coverage(self.db, replace(self.ctx, population="resident"), ["R1"])["denominator"], 1)
        self.assertEqual(self.result(["R1"])["numerator"], 1)  # B/u2 cannot reach A/u2.

    def test_10_empty_denominator_is_not_zero_rate(self):
        r = self.result(["missing"])
        self.assertEqual(r["status"], "no_denominator")
        self.assertIsNone(r["ratio"])

    def test_11_observed_zero_differs_from_missing(self):
        self.db.execute("DELETE FROM category_events")
        r = self.result(["R1"])
        self.assertEqual((r["status"], r["ratio"]), ("ok", Fraction(0)))

    def test_12_partial_data_suppresses_final_rate(self):
        r = self.result(["R1"], complete=False)
        self.assertEqual(r["denominator"], 3)
        self.assertEqual(r["status"], "partial")
        self.assertIsNone(r["ratio"])

    def test_13_context_mismatch_blocks_comparison(self):
        left = self.result(["R1"])
        for context in (replace(self.ctx, snapshot="snapshot-2"), replace(self.ctx, definition="v2"),
                        replace(self.ctx, start="2026-07-04"), replace(self.ctx, population="resident")):
            right = coverage(self.db, context, ["R1"])
            with self.assertRaises(ValueError):
                assert_comparable(left, right)

    def test_14_same_context_comparison_allowed(self):
        assert_comparable(self.result(["R1"]), self.result(["R2"]))

    def test_15_bound_parameters_and_window_validation(self):
        self.assertEqual(self.result(["R1' OR 1=1 --"])["denominator"], 0)
        with self.assertRaises(ValueError):
            coverage(self.db, replace(self.ctx, start="2026-07-01"), ["R1"])
        with self.assertRaises(ValueError):
            self.result([])


if __name__ == "__main__":
    unittest.main(verbosity=2)
