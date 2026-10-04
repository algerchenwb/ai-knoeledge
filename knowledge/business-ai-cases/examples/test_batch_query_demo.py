"""Offline batch boundary checks with synthetic business adapters."""
from collections import Counter
import json
from pathlib import Path
from threading import Event, Lock
import unittest

from batch_query_demo import DemoService, BusinessError, run_batch, query, example


class CountingService(DemoService):
    def __init__(self):
        super().__init__()
        self.calls = Counter()
        self.lock = Lock()

    def execute(self, principal, q):
        with self.lock:
            self.calls[(principal.tenant, q.region_id, q.start, q.max_tool_calls)] += 1
        return super().execute(principal, q)


class BatchChecks(unittest.TestCase):
    def setUp(self):
        self.s = CountingService()
        self.p = self.s.authenticate("Bearer demo-tenant-a")

    def items(self, *queries):
        return [{"item_id": str(i), "query": q} for i, q in enumerate(queries)]

    def error(self, code, fn):
        with self.assertRaises(BusinessError) as caught:
            fn()
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(sum(self.s.calls.values()), 0)

    def test_01_mixed_statuses(self):
        result = example()
        self.assertEqual(result["counts"], {"ok": 2, "no_denominator": 1, "provisional": 1, "error": 2})
        self.assertEqual(result["executed_unique_queries"], 4)
        self.assertEqual(result["status"], "partial")

    def test_02_duplicates_share_execution_not_result_objects(self):
        output = run_batch(self.s, self.p, self.items(query(), query()))
        self.assertEqual(sum(self.s.calls.values()), 1)
        self.assertEqual(output["submitted_items"], 2)
        self.assertEqual(output["status"], "ok")
        output["items"][0]["business"]["result"]["ratio"] = 99
        self.assertEqual(output["items"][1]["business"]["result"]["ratio"], .5)

    def test_03_invalid_envelope_before_execution(self):
        self.error("INVALID_ITEM_ID", lambda: run_batch(self.s, self.p,
            [{"item_id": "same", "query": query()}, {"item_id": "same", "query": query()}]))
        self.error("INVALID_ITEM", lambda: run_batch(self.s, self.p, [{"item_id": "x", "query": query(), "tenant": "x"}]))

    def test_04_batch_and_concurrency_limits(self):
        for items in ([], self.items(*([query()] * 21)), {}):
            self.error("INVALID_BATCH", lambda: run_batch(self.s, self.p, items))
        for workers in (0, 5, True):
            self.error("INVALID_CONCURRENCY", lambda: run_batch(self.s, self.p, self.items(query()), max_workers=workers))

    def test_05_invalid_query_isolated(self):
        output = run_batch(self.s, self.p, self.items(query(), query(population_type=True), None))
        self.assertEqual([r["status"] for r in output["items"]], ["ok", "error", "error"])
        self.assertEqual(sum(self.s.calls.values()), 1)

    def test_06_authorization_before_group_execution(self):
        output = run_batch(self.s, self.p, self.items(query("area-beta"), query("area-beta")))
        self.assertEqual(output["executed_unique_queries"], 0)
        self.assertEqual(output["counts"]["error"], 2)
        self.assertEqual(sum(self.s.calls.values()), 0)

    def test_07_effective_budget_in_identity(self):
        output = run_batch(self.s, self.p, self.items(query(max_tool_calls=1), query(max_tool_calls=2)))
        self.assertEqual(sum(self.s.calls.values()), 2)
        self.assertEqual([r["status"] for r in output["items"]], ["error", "ok"])

    def test_08_window_in_identity(self):
        output = run_batch(self.s, self.p, self.items(query(), query(start="2026-09-02")))
        self.assertEqual(output["executed_unique_queries"], 2)
        self.assertEqual(output["items"][1]["error"]["code"], "DATA_SCOPE_MISMATCH")

    def test_09_normalized_default_deduplication(self):
        output = run_batch(self.s, self.p, self.items(query(), query(max_tool_calls=2)))
        self.assertEqual(output["executed_unique_queries"], 1)

    def test_10_no_cross_request_cache(self):
        for _ in range(2):
            run_batch(self.s, self.p, self.items(query()))
        self.assertEqual(sum(self.s.calls.values()), 2)
        pb = self.s.authenticate("Bearer demo-tenant-b")
        output = run_batch(self.s, pb, self.items(query("area-beta")))
        self.assertEqual(output["items"][0]["business"]["result"]["ratio"], 0)

    def test_11_out_of_order_completion_preserves_item_ids(self):
        s = CountingService()
        second_done = Event()
        original = s.execute
        completed = []
        def execute(principal, q):
            if q.region_id == "area-alpha":
                if not second_done.wait(3):
                    raise AssertionError("parallel worker never started")
                result = original(principal, q)
                completed.append(q.region_id)
                return result
            result = original(principal, q)
            completed.append(q.region_id)
            second_done.set()
            return result
        s.execute = execute
        output = run_batch(s, self.p, self.items(query(), query("area-empty")), max_workers=2)
        self.assertEqual(completed, ["area-empty", "area-alpha"])
        self.assertEqual([r["item_id"] for r in output["items"]], ["0", "1"])
        self.assertEqual([r["status"] for r in output["items"]], ["ok", "no_denominator"])

    def test_12_worker_ceiling(self):
        from concurrent.futures import ThreadPoolExecutor
        s = CountingService()
        release, filled = Event(), Event()
        active, peak = 0, 0
        lock = Lock()
        original = s.execute
        def execute(principal, q):
            nonlocal active, peak
            with lock:
                active += 1; peak = max(peak, active)
                if active == 2:
                    filled.set()
            try:
                if not release.wait(3):
                    raise AssertionError("test gate timed out")
                return original(principal, q)
            finally:
                with lock:
                    active -= 1
        s.execute = execute
        with ThreadPoolExecutor(max_workers=1) as outer:
            future = outer.submit(run_batch, s, self.p,
                self.items(query(), query("area-empty"), query("area-provisional")), max_workers=2)
            ready = filled.wait(3)
            release.set()
            result = future.result(timeout=3)
        self.assertTrue(ready)
        self.assertEqual(peak, 2)
        self.assertEqual(result["counts"]["error"], 0)

    def test_13_unexpected_error_isolated_and_redacted(self):
        original = self.s.execute
        def execute(principal, q):
            if q.region_id == "area-empty":
                raise RuntimeError("secret-fixture-value")
            return original(principal, q)
        self.s.execute = execute
        output = run_batch(self.s, self.p, self.items(query(), query("area-empty")))
        self.assertEqual(output["items"][0]["status"], "ok")
        self.assertEqual(output["items"][1]["error"]["code"], "INTERNAL_ADAPTER_ERROR")
        self.assertNotIn("secret-fixture-value", json.dumps(output))


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(BatchChecks))
    if not result.wasSuccessful():
        raise SystemExit(1)
    Path(__file__).with_name("batch-query-results.json").write_text(json.dumps(
        {"date": "2026-10-05", "checks_passed": result.testsRun,
         "scope": "offline fixtures with real threads; no LLM, HTTP or production backend",
         "example": example()}, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
