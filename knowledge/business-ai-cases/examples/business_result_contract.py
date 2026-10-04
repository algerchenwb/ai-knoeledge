"""Independent output validator using hand-defined trusted fixture receipts.

Receipts are server-side teaching facts, never model-provided ground truth.
Free-text answer and trace are excluded from the returned validated view.
"""
from dataclasses import dataclass
from copy import deepcopy
import json
import math

from api_agent_demo import DemoService, parse_query


class ContractError(ValueError):
    pass


@dataclass(frozen=True)
class Receipt:
    region_id: str
    intent: str
    source_id: str
    data_version: str
    numerator: int
    denominator: int
    competitor_id: str | None = None
    competitor_denominator: int | None = None
    mature: bool = True
    population_type: int = 4
    start: str = "2026-09-01"
    end_exclusive: str = "2026-10-01"
    definition_version: str = "population-v1"


RECEIPTS = (
    Receipt("area-alpha", "category_coverage", "fixture:tenant-a:area-alpha", "synthetic-2026-09", 2, 4),
    Receipt("area-alpha", "co_visit", "fixture:tenant-a:area-alpha", "synthetic-2026-09", 2, 4, "poi-rival", 2),
    Receipt("area-empty", "category_coverage", "fixture:tenant-a:area-empty", "synthetic-2026-09", 0, 0),
    Receipt("area-alpha", "co_visit", "fixture:tenant-a:area-alpha", "synthetic-2026-09", 0, 4, "poi-empty", 0),
    Receipt("area-provisional", "category_coverage", "fixture:tenant-a:area-provisional", "synthetic-2026-09", 1, 1, mature=False),
)


def same(actual, expected, path):
    if isinstance(expected, dict):
        if type(actual) is not dict or set(actual) != set(expected):
            raise ContractError(f"{path}: object keys mismatch")
        for key in expected:
            same(actual[key], expected[key], f"{path}.{key}")
    elif isinstance(expected, list):
        if type(actual) is not list or len(actual) != len(expected):
            raise ContractError(f"{path}: list mismatch")
        for i, value in enumerate(expected):
            same(actual[i], value, f"{path}.{i}")
    elif type(expected) is float:
        if type(actual) not in (int, float) or not 0 <= actual <= 1 or not math.isfinite(actual) or not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-12):
            raise ContractError(f"{path}: finite ratio mismatch")
    elif type(actual) is not type(expected) or actual != expected:
        raise ContractError(f"{path}: value or type mismatch")


def validate_result(raw, query, receipt):
    # Caller must already bind receipt to authorized identity and immutable source.
    if type(raw) is not dict or type(receipt) is not Receipt:
        raise ContractError("invalid output or trusted receipt")
    expected_metric = "coverage-v1" if receipt.intent == "category_coverage" else "co-visit-v1"
    if (query.region_id, query.intent, query.competitor_id, query.population_type, query.start,
        query.end_exclusive, query.metric_version) != (receipt.region_id, receipt.intent,
        receipt.competitor_id, receipt.population_type, receipt.start, receipt.end_exclusive, expected_metric):
        raise ContractError("request and receipt scope mismatch")
    for count in (receipt.numerator, receipt.denominator):
        if type(count) is not int or count < 0:
            raise ContractError("invalid receipt count")
    if receipt.numerator > receipt.denominator:
        raise ContractError("receipt numerator exceeds denominator")
    if receipt.intent == "co_visit" and (type(receipt.competitor_denominator) is not int or
        receipt.competitor_denominator < receipt.numerator):
        raise ContractError("invalid competitor denominator")
    context = {"region_id": receipt.region_id, "population_type": receipt.population_type,
               "window": {"start": receipt.start, "end_exclusive": receipt.end_exclusive, "timezone": "Asia/Shanghai"},
               "metric_version": expected_metric, "data_version": receipt.data_version,
               "population_definition_version": receipt.definition_version}
    same(raw.get("context"), context, "context")
    if not receipt.mature:
        status, result, evidence = "provisional", None, []
    else:
        ratio = None if receipt.denominator == 0 else receipt.numerator / receipt.denominator
        if receipt.intent == "category_coverage":
            result = {"numerator": receipt.numerator, "denominator": receipt.denominator, "ratio": ratio}
            status = "ok" if receipt.denominator else "no_denominator"
        else:
            competitor_ratio = None if receipt.competitor_denominator == 0 else receipt.numerator / receipt.competitor_denominator
            result = {"competitor_id": receipt.competitor_id, "overlap": receipt.numerator,
                      "reference_share": ratio, "competitor_share": competitor_ratio}
            status = "ok" if ratio is not None and competitor_ratio is not None else "no_denominator"
        evidence = [{"source_id": receipt.source_id, "data_version": receipt.data_version}]
    same(raw.get("status"), status, "status")
    if "result" not in raw:
        raise ContractError("missing result (null must be explicit)")
    same(raw["result"], result, "result")
    # Prior provisional adapter omits evidence. Mature results must include it.
    if receipt.mature and "evidence" not in raw:
        raise ContractError("missing evidence")
    same(raw.get("evidence", []), evidence, "evidence")
    return deepcopy({"status": status, "context": context, "result": result, "evidence": evidence})


def examples():
    service = DemoService()
    principal = service.authenticate("Bearer demo-tenant-a")
    rows = []
    for receipt in RECEIPTS:
        raw_query = {"region_id": receipt.region_id, "intent": receipt.intent, "population_type": 4,
                     "start": receipt.start, "end_exclusive": receipt.end_exclusive,
                     "metric_version": "coverage-v1" if receipt.intent == "category_coverage" else "co-visit-v1"}
        if receipt.competitor_id:
            raw_query["competitor_id"] = receipt.competitor_id
        query = parse_query(raw_query)
        rows.append(validate_result(service.execute(principal, query), query, receipt))
    return rows


if __name__ == "__main__":
    print(json.dumps(examples(), ensure_ascii=False, indent=2, allow_nan=False))
