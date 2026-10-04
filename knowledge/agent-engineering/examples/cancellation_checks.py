"""Deterministic cancellation interleavings; no real network or framework."""
import json
from dataclasses import dataclass


class Blocked(Exception):
    pass


@dataclass
class Operation:
    generation: int = 1
    state: str = "pending"
    receipt: str | None = None


class Task:
    def __init__(self):
        self.operations = {"build": Operation(), "publish": Operation()}
        self.cancel_requested = False
        self.terminal = None
        self.events = []

    def cancel(self):
        if self.terminal is not None:
            return self.terminal  # preserve an already finalized result
        if not self.cancel_requested:
            self.cancel_requested = True
            self.events.append("cancel_requested")
            for op in self.operations.values():
                if op.state == "pending":
                    op.state = "skipped"
        return self.snapshot()["status"]

    def begin(self, name):
        op = self.operations[name]
        if self.cancel_requested or self.terminal or op.state != "pending":
            raise Blocked("new action is blocked")
        if name == "publish" and self.operations["build"].state != "succeeded":
            raise Blocked("build receipt is required")
        op.state = "running"
        self.events.append("started:" + name)
        return op.generation

    def complete(self, name, generation, receipt):
        op = self.operations[name]
        if generation != op.generation or op.state not in ("running", "unknown"):
            raise Blocked("stale or duplicate callback")
        if not receipt:
            raise Blocked("authoritative receipt required")
        # A valid result can arrive after cancellation; record the actual fact.
        op.state, op.receipt = "succeeded", receipt
        self.events.append("completed:" + name)

    def mark_unknown(self, name):
        op = self.operations[name]
        if op.state != "running":
            raise Blocked("only an in-flight operation can become unknown")
        op.state = "unknown"

    def finalize_success(self):
        if self.cancel_requested or any(o.state != "succeeded" for o in self.operations.values()):
            raise Blocked("success predicate not met")
        self.terminal = "succeeded"

    def snapshot(self):
        states = [o.state for o in self.operations.values()]
        if self.terminal:
            status = self.terminal
        elif self.cancel_requested:
            status = ("cancelling" if "running" in states else
                      "cancelled_with_unknown" if "unknown" in states else
                      "cancelled_partial" if "succeeded" in states else "cancelled")
        else:
            status = "running" if any(s != "pending" for s in states) else "queued"
        return {"status": status,
                "confirmed": [n for n, o in self.operations.items() if o.state == "succeeded"],
                "unknown": [n for n, o in self.operations.items() if o.state == "unknown"],
                "skipped": [n for n, o in self.operations.items() if o.state == "skipped"]}


def blocked(call):
    try:
        call()
    except Blocked:
        return
    raise AssertionError("expected blocked action")


def checks():
    results = []
    t = Task(); t.cancel()
    blocked(lambda: t.begin("build"))
    assert t.snapshot()["status"] == "cancelled" and len(t.snapshot()["skipped"]) == 2
    results.append("cancel_before_launch")
    t = Task(); generation = t.begin("build"); t.cancel()
    assert t.snapshot()["status"] == "cancelling"
    blocked(lambda: t.begin("publish"))
    t.complete("build", generation, "report-1")
    assert t.snapshot() == {"status": "cancelled_partial", "confirmed": ["build"],
                            "unknown": [], "skipped": ["publish"]}
    results.append("cancel_while_running_with_late_receipt")
    t.cancel(); assert t.events.count("cancel_requested") == 1
    results.append("duplicate_cancel")
    t = Task(); t.begin("build"); t.mark_unknown("build"); t.cancel()
    assert t.snapshot()["status"] == "cancelled_with_unknown"
    results.append("unknown_remote_result_is_retained")
    t.complete("build", 1, "report-confirmed-by-query")
    assert t.snapshot()["status"] == "cancelled_partial"
    results.append("reconciliation_after_cancel")
    t = Task(); generation = t.begin("build")
    blocked(lambda: t.complete("build", generation - 1, "old-result"))
    assert t.operations["build"].state == "running"
    results.append("stale_generation_callback")
    t = Task(); blocked(lambda: t.begin("publish"))
    results.append("dependency_guard")
    for name in ["build", "publish"]:
        generation = t.begin(name); t.complete(name, generation, "receipt-" + name)
    t.finalize_success(); assert t.cancel() == "succeeded"
    assert t.snapshot()["confirmed"] == ["build", "publish"]
    results.append("late_cancel_does_not_rewrite_success")
    assert len(results) == 8
    return {"passed": results, "example_final_state": t.snapshot()}


if __name__ == "__main__":
    print(json.dumps(checks(), indent=2))
