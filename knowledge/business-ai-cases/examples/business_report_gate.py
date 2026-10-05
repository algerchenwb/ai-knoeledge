"""Independent report manifest and approval gate; no natural-language generation."""
from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
import hashlib
import json


SUPPORTED = {"coverage", "co_visit", "traffic_change"}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class Metric:
    name: str
    object_id: str
    period: tuple[str, str]
    definition: str
    data_version: str
    numerator: int
    denominator: int
    mature: bool
    evidence_id: str


class ReportGate:
    def __init__(self, tenant, object_id, period, definitions, metrics):
        # All arguments are trusted service fixtures, never caller authorization.
        if not isinstance(tenant, str) or not tenant or not object_id:
            raise ValueError("invalid scope")
        if len(period) != 2 or date.fromisoformat(period[0]) >= date.fromisoformat(period[1]):
            raise ValueError("invalid half-open period")
        if set(definitions) != SUPPORTED or any(not v for v in definitions.values()):
            raise ValueError("definition set required")
        if len({m.name for m in metrics}) != len(metrics):
            raise ValueError("duplicate metric")
        self.tenant, self.object_id, self.period = tenant, object_id, tuple(period)
        self.definitions = dict(definitions)
        self.metrics = {m.name: m for m in metrics}

    def prepare(self, required, policy_version="report-policy-1"):
        if not required or len(required) != len(set(required)) or set(required) - SUPPORTED:
            raise ValueError("invalid required metric set")
        if not isinstance(policy_version, str) or not policy_version:
            raise ValueError("invalid policy")
        sections = []
        used_evidence = set()
        for name in sorted(required):
            metric = self.metrics.get(name)
            section = {"metric": name, "status": "missing", "value": None,
                       "evidence_id": None, "data_version": None}
            if metric:
                if metric.object_id != self.object_id or metric.period != self.period:
                    raise ValueError("metric scope mismatch")
                if metric.definition != self.definitions[name]:
                    raise ValueError("metric definition mismatch")
                if type(metric.numerator) is not int or type(metric.denominator) is not int:
                    raise ValueError("counts must be integers")
                if metric.numerator < 0 or metric.denominator < 0 or type(metric.mature) is not bool:
                    raise ValueError("invalid count or maturity")
                if name != "traffic_change" and metric.numerator > metric.denominator:
                    raise ValueError("invalid subset count")
                if not metric.data_version or not metric.evidence_id.strip():
                    raise ValueError("version and evidence required")
                if metric.evidence_id in used_evidence:
                    raise ValueError("one evidence id per metric fixture")
                used_evidence.add(metric.evidence_id)
                section.update(evidence_id=metric.evidence_id, data_version=metric.data_version)
                if metric.denominator == 0:
                    section["status"] = "undefined"
                else:
                    value = Decimal(metric.numerator) / Decimal(metric.denominator)
                    if name == "traffic_change":
                        value -= 1
                    section.update(value=str(value), status="ok" if metric.mature else "provisional")
            sections.append(section)
        ready = all(s["status"] == "ok" for s in sections)
        body = {"tenant": self.tenant, "object_id": self.object_id,
                "period": list(self.period), "policy_version": policy_version,
                "definitions": {k: self.definitions[k] for k in sorted(required)},
                "required": sorted(required), "status": "ready_for_review" if ready else "partial",
                "sections": sections}
        return {"body": body, "digest": digest(body)}

    def _validate_draft(self, draft):
        if set(draft) != {"body", "digest"} or digest(draft["body"]) != draft["digest"]:
            raise ValueError("draft digest mismatch")
        body = draft["body"]
        rebuilt = self.prepare(body["required"], body["policy_version"])
        if rebuilt != draft:
            raise ValueError("draft differs from trusted fixtures")
        if body["status"] != "ready_for_review":
            raise ValueError("incomplete or provisional report")

    def approve(self, draft, reviewer, now, expires_at):
        self._validate_draft(draft)
        if not isinstance(reviewer, str) or not reviewer.strip():
            raise ValueError("reviewer required")
        if type(now) is not int or type(expires_at) is not int or now < 0 or expires_at <= now:
            raise ValueError("invalid approval lifetime")
        return {"tenant": self.tenant, "reviewer": reviewer, "digest": draft["digest"],
                "approved_at": now, "expires_at": expires_at}

    def check_release(self, draft, approval, current_versions, current_policy, now):
        self._validate_draft(draft)
        # Approval is a trusted internal fixture, not a signed credential.
        if approval["tenant"] != self.tenant or approval["digest"] != draft["digest"]:
            raise ValueError("approval scope mismatch")
        if not isinstance(approval["reviewer"], str) or not approval["reviewer"].strip():
            raise ValueError("invalid reviewer")
        if type(now) is not int or not approval["approved_at"] <= now < approval["expires_at"]:
            raise ValueError("approval expired or not yet active")
        body = draft["body"]
        if current_policy != body["policy_version"]:
            raise ValueError("policy changed")
        expected = {s["metric"]: s["data_version"] for s in body["sections"]}
        if current_versions != expected:
            raise ValueError("current data snapshot changed or missing")
        return {"status": "eligible_for_release", "digest": draft["digest"],
                "reviewer": approval["reviewer"], "manifest": deepcopy(body)}


def fixture_gate(metrics=None):
    period = ("2026-09-01", "2026-10-01")
    definitions = {"coverage": "coverage-1", "co_visit": "co-visit-1", "traffic_change": "matched-day-1"}
    if metrics is None:
        metrics = [Metric("coverage", "area-demo", period, "coverage-1", "coverage-data-2", 50, 100, True, "receipt-coverage"),
                   Metric("co_visit", "area-demo", period, "co-visit-1", "co-data-2", 30, 100, True, "receipt-co"),
                   Metric("traffic_change", "area-demo", period, "matched-day-1", "trend-data-2", 90, 100, True, "receipt-trend")]
    return ReportGate("tenant-demo", "area-demo", period, definitions, metrics)


def examples():
    gate = fixture_gate()
    draft = gate.prepare(sorted(SUPPORTED))
    approval = gate.approve(draft, "reviewer-demo", 100, 200)
    versions = {m.name: m.data_version for m in gate.metrics.values()}
    released = gate.check_release(draft, approval, versions, "report-policy-1", 101)
    partial = fixture_gate(list(gate.metrics.values())[:2]).prepare(sorted(SUPPORTED))
    return {"ready_draft": draft, "approval_fixture": approval,
            "release_eligibility": released, "partial_draft": partial}


if __name__ == "__main__":
    print(json.dumps(examples(), ensure_ascii=False, indent=2))
