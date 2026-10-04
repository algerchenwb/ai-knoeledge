"""Original teaching checks; Python 3.12+, single event loop, no external API."""
import asyncio
from dataclasses import dataclass
import unittest


@dataclass
class Job:
    key: str
    deadline: float
    cancelled: bool = False


STOP = object()


async def worker(queue, outcomes, operation):
    while True:
        item = await queue.get()
        try:
            if item is STOP:
                return
            if item.cancelled:
                outcomes[item.key] = "cancelled_before_start"
                continue
            if asyncio.get_running_loop().time() >= item.deadline:
                outcomes[item.key] = "expired_before_start"
                continue
            outcomes[item.key] = "running"
            try:
                await operation(item)
            except asyncio.CancelledError:
                # An external effect may already exist; do not claim rollback.
                outcomes[item.key] = "unknown"
                raise
            except Exception:
                outcomes[item.key] = "failed"
            else:
                outcomes[item.key] = "succeeded"
        finally:
            # This acknowledges local handling, not business success.
            queue.task_done()


async def parked(call, entered):
    entered.set()
    return await call()


class Checks(unittest.IsolatedAsyncioTestCase):
    async def wait_parked(self, call):
        entered = asyncio.Event()
        task = asyncio.create_task(parked(call, entered))
        await entered.wait()
        await asyncio.sleep(0)
        return task

    async def ack_join(self, queue):
        await asyncio.wait_for(queue.join(), 1)

    async def test_01_bounded_backpressure(self):
        q = asyncio.Queue(maxsize=1)
        q.put_nowait("first")
        put = await self.wait_parked(lambda: q.put("second"))
        self.assertFalse(put.done())
        self.assertEqual(q.get_nowait(), "first")
        q.task_done()
        await asyncio.wait_for(put, 1)
        self.assertEqual(q.get_nowait(), "second")
        q.task_done()
        await self.ack_join(q)

    async def test_02_cancelled_put_does_not_enqueue(self):
        q = asyncio.Queue(1)
        q.put_nowait("first")
        put = await self.wait_parked(lambda: q.put("cancelled"))
        put.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await put
        self.assertEqual(q.get_nowait(), "first")
        q.task_done()
        q.put_nowait("next")
        self.assertEqual(q.get_nowait(), "next")
        q.task_done()
        await self.ack_join(q)

    async def test_03_cancelled_get_does_not_consume(self):
        q = asyncio.Queue()
        get = await self.wait_parked(q.get)
        get.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await get
        survivor = await self.wait_parked(q.get)
        q.put_nowait("survives")
        self.assertEqual(await asyncio.wait_for(survivor, 1), "survives")
        q.task_done()
        await self.ack_join(q)

    async def test_04_empty_queue_is_not_completed_work(self):
        q = asyncio.Queue()
        q.put_nowait("work")
        q.get_nowait()
        join = await self.wait_parked(q.join)
        self.assertTrue(q.empty())
        self.assertFalse(join.done())
        q.task_done()
        await asyncio.wait_for(join, 1)

    async def test_05_duplicate_ack_rejected(self):
        q = asyncio.Queue()
        q.put_nowait("work")
        q.get_nowait()
        q.task_done()
        with self.assertRaises(ValueError):
            q.task_done()

    async def test_06_failure_still_acknowledged(self):
        q, outcomes = asyncio.Queue(), {}
        async def fail(_):
            raise RuntimeError("mock failure")
        q.put_nowait(Job("bad", float("inf")))
        q.put_nowait(STOP)
        await asyncio.wait_for(worker(q, outcomes, fail), 1)
        await self.ack_join(q)
        self.assertEqual(outcomes, {"bad": "failed"})

    async def test_07_running_cancel_is_unknown(self):
        q, outcomes = asyncio.Queue(), {}
        entered, gate = asyncio.Event(), asyncio.Event()
        async def blocked(_):
            entered.set()
            await gate.wait()
        q.put_nowait(Job("active", float("inf")))
        task = asyncio.create_task(worker(q, outcomes, blocked))
        await asyncio.wait_for(entered.wait(), 1)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        await self.ack_join(q)
        self.assertEqual(outcomes["active"], "unknown")

    async def test_08_logical_cancel_skips_tool(self):
        q, outcomes, calls = asyncio.Queue(), {}, []
        async def record(item):
            calls.append(item.key)
        q.put_nowait(Job("skip", float("inf"), cancelled=True))
        q.put_nowait(STOP)
        await asyncio.wait_for(worker(q, outcomes, record), 1)
        await self.ack_join(q)
        self.assertEqual(calls, [])
        self.assertEqual(outcomes["skip"], "cancelled_before_start")

    async def test_09_expired_job_skips_tool(self):
        q, outcomes, calls = asyncio.Queue(), {}, []
        async def record(item):
            calls.append(item.key)
        q.put_nowait(Job("stale", asyncio.get_running_loop().time() - 1))
        q.put_nowait(STOP)
        await asyncio.wait_for(worker(q, outcomes, record), 1)
        await self.ack_join(q)
        self.assertEqual(calls, [])
        self.assertEqual(outcomes["stale"], "expired_before_start")

    async def test_10_admission_timeout_preserves_existing_job(self):
        q = asyncio.Queue(1)
        q.put_nowait("existing")
        with self.assertRaises(TimeoutError):
            async with asyncio.timeout(0.01):
                await q.put("too_late")
        self.assertEqual(q.qsize(), 1)
        self.assertEqual(q.get_nowait(), "existing")
        q.task_done()
        await self.ack_join(q)

    async def test_11_taskgroup_failure_cleans_sibling(self):
        entered, cleaned = asyncio.Event(), asyncio.Event()
        async def sibling():
            try:
                entered.set()
                await asyncio.Event().wait()
            finally:
                cleaned.set()
        async def fail():
            await entered.wait()
            raise RuntimeError("fatal infrastructure failure")
        with self.assertRaises(ExceptionGroup) as caught:
            async with asyncio.TaskGroup() as group:
                group.create_task(sibling())
                group.create_task(fail())
        self.assertTrue(cleaned.is_set())
        self.assertTrue(any(isinstance(e, RuntimeError) for e in caught.exception.exceptions))

    async def test_12_stop_after_drain(self):
        q, outcomes, calls = asyncio.Queue(2), {}, []
        async def record(item):
            calls.append(item.key)
        task = asyncio.create_task(worker(q, outcomes, record))
        await q.put(Job("one", float("inf")))
        await q.put(Job("two", float("inf")))
        await self.ack_join(q)  # Producers have stopped before this barrier.
        await q.put(STOP)
        await asyncio.wait_for(task, 1)
        await self.ack_join(q)
        self.assertEqual(calls, ["one", "two"])
        self.assertEqual(outcomes, {"one": "succeeded", "two": "succeeded"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
