"""Independent deterministic business regression evaluation; no LLM or Opik SDK."""
import hashlib
import json
import math
from pathlib import Path

from tool_registry_demo import Registry, fixture_access, BusinessError

DATASET = Path(__file__).with_name("business-golden-dataset.json")


def load_dataset(path=DATASET):
    data = json.loads(path.read_text())
    if not isinstance(data, dict) or data.get("version") != "synthetic-business-v1":
        raise ValueError("unsupported dataset version")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("dataset must have cases")
    ids = set()
    for case in cases:
        if type(case.get("id")) is not str or not case["id"] or case["id"] in ids:
            raise ValueError("case IDs must be unique nonempty strings")
        ids.add(case["id"])
        if type(case.get("critical")) is not bool or not case.get("checks"):
            raise ValueError("missing critical flag or checks")
        for check in case["checks"]:
            if set(check) != {"dimension", "path", "expected"} or check["dimension"] not in {"route", "business", "evidence", "boundary"}:
                raise ValueError("invalid rubric")
            if type(check["path"]) is not str or not check["path"]:
                raise ValueError("invalid path")
    return data


def run_case(registry, access, case):
    stage = "plan"
    try:
        plan = registry.plan(access, case["proposal"])
        stage = "execute"
        return {"kind": "result", "value": registry.execute(access, plan)}
    except BusinessError as exc:
        return {"kind": "error", "stage": stage, "code": exc.code}
    except Exception:
        return {"kind": "harness_error", "stage": stage}


def lookup(output, path):
    value = output
    for key in path.split("."):
        if isinstance(value, dict) and key in value:
            value = value[key]
        elif isinstance(value, list) and key.isdigit() and int(key) < len(value):
            value = value[int(key)]
        else:
            return False, None
    return True, value


def equals(actual, expected):
    if type(expected) is float:
        return type(actual) in (int, float) and math.isfinite(actual) and math.isclose(actual, expected, rel_tol=0, abs_tol=1e-12)
    # bool is not an integer count; null must actually be present.
    return type(actual) is type(expected) and actual == expected


def grade(case, output):
    checks = []
    for rule in case["checks"]:
        present, actual = lookup(output, rule["path"])
        checks.append({"dimension": rule["dimension"], "path": rule["path"],
                       "passed": present and equals(actual, rule["expected"])})
    return {"case_id": case["id"], "critical": case["critical"],
            "passed": all(x["passed"] for x in checks), "checks": checks}


def summarize(rows):
    dimensions = {}
    for row in rows:
        # Per-case dimension counts: more assertions must not give extra weight.
        grouped = {}
        for check in row["checks"]:
            grouped.setdefault(check["dimension"], []).append(check["passed"])
        for dimension, flags in grouped.items():
            counts = dimensions.setdefault(dimension, {"passed_cases": 0, "applicable_cases": 0})
            counts["applicable_cases"] += 1
            counts["passed_cases"] += int(all(flags))
    blocked = [row["case_id"] for row in rows if row["critical"] and not row["passed"]]
    failures = [row["case_id"] for row in rows if not row["passed"]]
    return {"case_count": len(rows), "passed_cases": sum(row["passed"] for row in rows),
            "dimensions": dimensions, "critical_failures": blocked, "failed_cases": failures,
            # This teaching gate requires all cases, not a production acceptance policy.
            "gate": "pass" if rows and not failures else "fail"}


def evaluate(data, registry=None):
    registry = Registry() if registry is None else registry
    access = fixture_access(registry)
    rows = [grade(case, run_case(registry, access, case)) for case in data["cases"]]
    fingerprint = hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False,
                                           allow_nan=False).encode()).hexdigest()
    return {"date": "2026-10-05", "dataset_version": data["version"], "dataset_sha256": fingerprint,
            "catalog_revision": registry.revision, "scope": "offline structured proposals and synthetic fixtures; no LLM, HTTP or Opik execution",
            "summary": summarize(rows), "cases": rows}


if __name__ == "__main__":
    report = evaluate(load_dataset())
    Path(__file__).with_name("business-golden-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["summary"]["gate"] == "pass" else 1)
