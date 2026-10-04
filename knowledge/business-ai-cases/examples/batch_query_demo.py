"""Bounded read-only batch queries on synthetic business fixtures.

No LLM, HTTP, retry, cross-request cache or production authorization provider.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from dataclasses import asdict
import json

from api_agent_demo import DemoService, BusinessError, parse_query, fail


def run_batch(service, principal, items, *, max_workers=2):
    # Envelope errors reject the whole batch before any execution.
    if type(items) is not list or not 1 <= len(items) <= 20:
        fail(422, "INVALID_BATCH", "批量必须是1至20项列表")
    if type(max_workers) is not int or not 1 <= max_workers <= 4:
        fail(422, "INVALID_CONCURRENCY", "并发必须是1至4的整数")
    seen = set()
    for item in items:
        if type(item) is not dict or set(item) != {"item_id", "query"}:
            fail(422, "INVALID_ITEM", "每项必须包含item_id与query")
        key = item["item_id"]
        if type(key) is not str or not 1 <= len(key) <= 40 or key in seen:
            fail(422, "INVALID_ITEM_ID", "item_id必须是唯一非空受限字符串")
        seen.add(key)

    rows, groups = {}, {}
    def error(exc):
        return {"status": "error", "error": {"code": exc.code, "http_status": exc.http_status}}

    # Validate each query; semantic failures are isolated to the corresponding item.
    for item in items:
        key = item["item_id"]
        try:
            query = parse_query(item["query"])
            if query.region_id not in principal.regions:
                fail(403, "OBJECT_FORBIDDEN", "对象不在当前身份范围")
            normalized = asdict(query)
            # Deduplication is request-local and includes all effective parameters,
            # current tenant and authorized region scope. No credentials in key.
            identity = json.dumps([principal.tenant, sorted(principal.regions), normalized],
                                  ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            groups.setdefault(identity, {"query": query, "ids": []})["ids"].append(key)
        except BusinessError as exc:
            rows[key] = error(exc)

    def execute(query):
        try:
            result = service.execute(principal, query)
            return {"status": result["status"], "business": result}
        except BusinessError as exc:
            return error(exc)
        except Exception:
            # Unexpected adapter failure: preserve siblings, never expose raw text.
            return {"status": "error", "error": {"code": "INTERNAL_ADAPTER_ERROR", "http_status": 500}}

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(execute, group["query"]): group["ids"] for group in groups.values()}
        for future in as_completed(futures):
            value = future.result()
            for key in futures[future]:
                rows[key] = deepcopy(value)

    ordered = [{"item_id": item["item_id"], **rows[item["item_id"]]} for item in items]
    counts = {status: sum(row["status"] == status for row in ordered)
              for status in ("ok", "no_denominator", "provisional", "error")}
    return {"status": "ok" if counts["ok"] == len(items) else "partial",
            "submitted_items": len(items), "executed_unique_queries": len(groups),
            "counts": counts, "items": ordered}


def query(region="area-alpha", **changes):
    value = {"intent": "category_coverage", "region_id": region, "population_type": 4,
             "start": "2026-09-01", "end_exclusive": "2026-10-01", "metric_version": "coverage-v1"}
    value.update(changes)
    return value


def example():
    service = DemoService()
    principal = service.authenticate("Bearer demo-tenant-a")
    regions = ("area-alpha", "area-alpha", "area-empty", "area-provisional", "area-unavailable", "area-beta")
    items = [{"item_id": f"item-{i + 1}", "query": query(region)} for i, region in enumerate(regions)]
    return run_batch(service, principal, items)


if __name__ == "__main__":
    print(json.dumps(example(), ensure_ascii=False, indent=2, allow_nan=False))
