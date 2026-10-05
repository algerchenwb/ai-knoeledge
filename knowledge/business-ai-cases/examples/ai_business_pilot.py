"""Synthetic tenant-level pilot accounting; no significance test or winner choice."""
from dataclasses import dataclass
from decimal import Decimal
import hashlib
import json
import re


def assign(tenant, unit, experiment, version):
    if any(not isinstance(v, str) or not v for v in (tenant, unit, experiment, version)):
        raise ValueError("assignment identifiers required")
    key = json.dumps([tenant, unit, experiment, version], separators=(",", ":"))
    bucket = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big")
    return "A" if bucket < 2**63 else "B"


@dataclass(frozen=True)
class Enrollment:
    tenant: str
    unit: str
    experiment: str
    version: str
    arm: str
    enrolled_at: int


@dataclass(frozen=True)
class Outcome:
    unit: str
    success: bool
    safety_failure: bool
    cost: str


def summarize(enrollments, outcomes, tenant, experiment, version, now,
              min_per_arm=10, max_failure_rate=0.2, max_average_cost="3.50"):
    if type(now) is not int or now < 0 or type(min_per_arm) is not int or min_per_arm < 1:
        raise ValueError("invalid clock or sample policy")
    if type(max_failure_rate) not in (int, float) or not 0 <= max_failure_rate <= 1:
        raise ValueError("invalid failure policy")
    if not isinstance(max_average_cost, str) or not re.fullmatch(r"\d+(?:\.\d{1,2})?", max_average_cost):
        raise ValueError("invalid cost policy")
    cost_limit = Decimal(max_average_cost)
    units = {}
    for row in enrollments:
        if (row.tenant, row.experiment, row.version) != (tenant, experiment, version):
            continue
        if row.arm != assign(tenant, row.unit, experiment, version):
            raise ValueError("assignment mismatch")
        if type(row.enrolled_at) is not int or not 0 <= row.enrolled_at <= now:
            raise ValueError("invalid enrollment time")
        if row.unit in units and units[row.unit] != row:
            raise ValueError("conflicting enrollment")
        units[row.unit] = row
    measured = {}
    for row in outcomes:
        if row.unit not in units:
            raise ValueError("unregistered outcome")
        if type(row.success) is not bool or type(row.safety_failure) is not bool:
            raise ValueError("boolean outcome required")
        if not isinstance(row.cost, str) or not re.fullmatch(r"\d+(?:\.\d{1,2})?", row.cost):
            raise ValueError("nonnegative two-decimal cost required")
        if row.unit in measured and measured[row.unit] != row:
            raise ValueError("conflicting outcome")
        measured[row.unit] = row
    arms = {}
    for arm in ("A", "B"):
        group = [row for row in units.values() if row.arm == arm]
        eligible = [row for row in group if row.enrolled_at + 7 <= now]
        complete = [measured[row.unit] for row in eligible if row.unit in measured]
        missing = len(eligible) - len(complete)
        successes = sum(row.success for row in complete)
        failures = sum(row.safety_failure for row in complete)
        cost = sum((Decimal(row.cost) for row in complete), Decimal(0))
        arms[arm] = {"enrolled": len(group), "eligible": len(eligible),
                     "pending": len(group) - len(eligible), "observed": len(complete), "missing": missing,
                     "successes": successes, "safety_failures": failures,
                     "success_rate": successes / len(eligible) if eligible and not missing else None,
                     "failure_rate": failures / len(eligible) if eligible and not missing else None,
                     "total_observed_cost": f"{cost:.2f}",
                     "average_observed_cost": str(cost / len(complete)) if complete else None}
    if any(a["missing"] for a in arms.values()):
        decision = "data_incomplete"
    elif any(a["eligible"] < min_per_arm for a in arms.values()):
        decision = "insufficient_sample"
    elif any(a["failure_rate"] > max_failure_rate or Decimal(a["average_observed_cost"]) > cost_limit
             for a in arms.values()):
        decision = "guardrail_failed"
    else:
        decision = "ready_for_statistical_review"
    effect = arms["B"]["success_rate"] - arms["A"]["success_rate"] if all(
        a["success_rate"] is not None for a in arms.values()) else None
    return {"tenant": tenant, "experiment": experiment, "version": version, "as_of": now,
            "window_days": 7, "arms": arms, "observed_absolute_difference": effect,
            "decision": decision, "statistical_inference": "not implemented; no winner declared"}


def fixtures():
    tenant, experiment, version = "tenant-demo", "report-assistant", "pilot-1"
    enrollments, outcomes, counts = [], [], {"A": 0, "B": 0}
    for number in range(1000):
        unit = f"account-{number}"
        arm = assign(tenant, unit, experiment, version)
        if counts[arm] == 10:
            continue
        index = counts[arm]
        counts[arm] += 1
        enrollments.append(Enrollment(tenant, unit, experiment, version, arm, 100))
        outcomes.append(Outcome(unit, index < {"A": 6, "B": 8}[arm], arm == "A" and index == 9,
                                {"A": "2.00", "B": "3.00"}[arm]))
        if counts == {"A": 10, "B": 10}:
            break
    options = dict(tenant=tenant, experiment=experiment, version=version, now=107)
    return enrollments, outcomes, options


def examples():
    enrollments, outcomes, options = fixtures()
    return {"complete": summarize(enrollments, outcomes, **options),
            "missing_one_outcome": summarize(enrollments, outcomes[:-1], **options),
            "cost_guardrail": summarize(enrollments, outcomes, **options, max_average_cost="2.50")}


if __name__ == "__main__":
    print(json.dumps(examples(), ensure_ascii=False, indent=2))
