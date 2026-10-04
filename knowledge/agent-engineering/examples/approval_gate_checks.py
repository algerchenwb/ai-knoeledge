"""Pure offline approval gate model; no framework or external service calls."""
from dataclasses import dataclass, replace
import hashlib
import json
from threading import RLock


class Denied(Exception):
    pass


@dataclass(frozen=True)
class Actor:
    user: str
    tenant: str
    can_approve: bool


@dataclass(frozen=True)
class Proposal:
    approval_id: str
    operation_id: str
    tenant: str
    payload_digest: str
    object_version: int
    policy_version: int
    expires_at: int


def digest(payload):
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode()).hexdigest()


class Gate:
    """Trusted proposal store and one-process critical section. Not durable."""
    def __init__(self):
        self.lock = RLock()
        self.proposals = {}
        self.decisions = {}
        self.receipts = {}
        self.object_version = 7
        self.policy_version = 2
        self.cancelled = False
        self.side_effects = 0

    def propose(self, payload):
        p = Proposal("approval-1", "publish-report-1", "tenant-a", digest(payload),
                     self.object_version, self.policy_version, 100)
        self.proposals[p.approval_id] = p
        return p.approval_id

    def authorize(self, p, actor):
        if actor.tenant != p.tenant or not actor.can_approve:
            raise Denied("actor is outside approval scope")

    def decide(self, approval_id, actor, decision, now):
        with self.lock:
            p = self.proposals[approval_id]
            self.authorize(p, actor)
            if decision not in ("approve", "reject") or now >= p.expires_at:
                raise Denied("invalid or expired decision")
            if approval_id in self.decisions:
                old_actor, old_decision = self.decisions[approval_id]
                if (old_actor, old_decision) != (actor.user, decision):
                    raise Denied("decision already recorded")
                return  # identical duplicate submission
            self.decisions[approval_id] = (actor.user, decision)

    def execute(self, approval_id, actor, payload, now):
        with self.lock:
            p = self.proposals[approval_id]  # do not trust a proposal from the caller
            self.authorize(p, actor)
            if digest(payload) != p.payload_digest:
                raise Denied("payload changed; new proposal required")
            decision = self.decisions.get(approval_id)
            if decision != (actor.user, "approve"):
                raise Denied("approval not granted by this actor")
            key = (p.tenant, p.operation_id)
            # Already finished: returning a receipt does not repeat a write.
            if key in self.receipts:
                return self.receipts[key]
            if self.cancelled or now >= p.expires_at:
                raise Denied("cancelled or expired before execution")
            if p.object_version != self.object_version or p.policy_version != self.policy_version:
                raise Denied("object or policy changed")
            # In this mock, all mutations share one critical section.
            self.side_effects += 1
            self.object_version += 1
            receipt = {"operation_id": p.operation_id, "status": "succeeded",
                       "new_version": self.object_version}
            self.receipts[key] = receipt
            return receipt


def setup():
    gate = Gate()
    body = {"report_id": "report-demo", "audience": "internal", "month": "2026-09"}
    actor = Actor("reviewer-demo", "tenant-a", True)
    aid = gate.propose(body)
    gate.decide(aid, actor, "approve", 10)
    return gate, body, actor, aid


def assert_denied(call, gate):
    try:
        call()
    except Denied:
        assert gate.side_effects == 0
        return
    raise AssertionError("guard should reject execution")


def checks():
    g, body, actor, aid = setup()
    g.decide(aid, actor, "approve", 11)  # duplicate approval
    first = g.execute(aid, actor, body, 20)
    assert g.execute(aid, actor, body, 21) == first and g.side_effects == 1
    passed = ["valid_execution", "duplicate_approval_and_receipt"]
    scenarios = [
        ("changed_payload", lambda g, b, a: (g, {**b, "audience": "public"}, a, 20)),
        ("expiry_boundary", lambda g, b, a: (g, b, a, 100)),
        ("wrong_tenant", lambda g, b, a: (g, b, replace(a, tenant="tenant-b"), 20)),
        ("permission_revoked", lambda g, b, a: (g, b, replace(a, can_approve=False), 20)),
    ]
    for name, change in scenarios:
        g, body, actor, aid = setup()
        _, body, actor, now = change(g, body, actor)
        assert_denied(lambda: g.execute(aid, actor, body, now), g)
        passed.append(name)
    for name, attr, value in [("stale_object", "object_version", 8),
                              ("policy_changed", "policy_version", 3),
                              ("cancelled", "cancelled", True)]:
        g, body, actor, aid = setup()
        setattr(g, attr, value)
        assert_denied(lambda: g.execute(aid, actor, body, 20), g)
        passed.append(name)
    g, body, actor, aid = setup()
    # Separate proposal initially receives a rejection, not an approval.
    g.decisions.clear()
    g.decide(aid, actor, "reject", 10)
    assert_denied(lambda: g.execute(aid, actor, body, 20), g)
    passed.append("rejected_proposal")
    assert len(passed) == 10
    return {"checks_passed": passed, "valid_case_effect_count": 1,
            "denied_cases_effect_count": 0}


if __name__ == "__main__":
    print(json.dumps(checks(), indent=2))
