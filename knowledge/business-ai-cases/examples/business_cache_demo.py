"""Sequential in-process business result cache teaching demo.

No distributed cache, concurrent access, LLM, HTTP or production metadata service.
"""
from collections import OrderedDict
from copy import deepcopy
from dataclasses import asdict
import json
import hashlib
import math
import time

from api_agent_demo import DemoService, parse_query, fail


class ResultCache:
    def __init__(self, ttl=5.0, max_entries=10, timer=time.monotonic):
        if type(ttl) not in (int, float) or not math.isfinite(ttl) or ttl <= 0:
            raise ValueError("ttl must be finite and positive")
        if type(max_entries) is not int or not 1 <= max_entries <= 1000:
            raise ValueError("max_entries must be a bounded strict integer")
        self.ttl, self.max_entries, self.timer = ttl, max_entries, timer
        self.entries = OrderedDict()

    def expire(self):
        now = self.timer()
        for key, (created, _) in list(self.entries.items()):
            if now - created >= self.ttl:
                del self.entries[key]

    def get(self, key):
        self.expire()
        if key not in self.entries:
            return None
        created, result = self.entries[key]
        self.entries.move_to_end(key)
        return deepcopy(result), self.timer() - created

    def put(self, key, value):
        self.expire()
        self.entries[key] = (self.timer(), deepcopy(value))
        self.entries.move_to_end(key)
        while len(self.entries) > self.max_entries:
            self.entries.popitem(last=False)

    def clear(self):
        self.entries.clear()


class CachedBusiness:
    def __init__(self, demo=None, cache=None):
        self.demo = DemoService() if demo is None else demo
        self.cache = ResultCache() if cache is None else cache
        self.executions = 0

    def query(self, principal, raw, *, permission_revision="fixture-policy-v1"):
        q = parse_query(raw)
        # Trusted current context, not request or LLM fields. Check before lookup.
        if type(permission_revision) is not str or not permission_revision:
            raise ValueError("trusted permission revision required")
        if q.region_id not in principal.regions:
            fail(403, "OBJECT_FORBIDDEN", "区域没有授权")
        if q.intent == "co_visit" and (principal.tenant, q.competitor_id) not in self.demo.competitors:
            fail(403, "COMPETITOR_FORBIDDEN", "竞品没有授权")
        snapshot = self.demo.snapshots.get((principal.tenant, q.region_id))
        if snapshot is None:
            fail(404, "NO_SNAPSHOT", "没有授权对象快照")
        if not snapshot.available:
            fail(502, "UPSTREAM_UNAVAILABLE", "本例不在数据源不可用时返回旧缓存")
        # Metadata is read on every query; it is not a stale cached authorization.
        # Toy fixture has one snapshot. Real metadata and data must bind atomically.
        revision = {"data_version": snapshot.data_version, "definition_version": snapshot.definition_version,
                    "mature": snapshot.mature, "available": snapshot.available,
                    "window": [snapshot.start, snapshot.end_exclusive], "population_type": snapshot.population_type}
        if q.intent == "co_visit":
            # Fixture has no competitor revision service. Hash its normalized set.
            # Production should bind a trustworthy immutable competitor revision.
            rival = self.demo.competitors[(principal.tenant, q.competitor_id)]
            revision["competitor_set_sha256"] = hashlib.sha256(
                json.dumps(sorted(set(rival)), ensure_ascii=False).encode()).hexdigest()
        # Include effective parameters, full current scope, adapter and policy revision.
        identity = json.dumps([principal.tenant, sorted(principal.regions), permission_revision,
                               "adapter-v1", asdict(q), revision], sort_keys=True, ensure_ascii=False)
        hit = self.cache.get(identity) if snapshot.mature else None
        if hit is not None:
            result, age = hit
            return {"cache": {"status": "hit", "age_seconds": age, "trace_scope": "origin_calculation"},
                    "business": result}
        self.executions += 1
        result = self.demo.execute(principal, q)
        if result["status"] == "ok":
            self.cache.put(identity, result)
            status = "miss"
        else:
            status = "bypass"
        return {"cache": {"status": status, "age_seconds": 0, "trace_scope": "current_calculation"},
                "business": result}


def fixture_query():
    return {"intent": "category_coverage", "region_id": "area-alpha", "population_type": 4,
            "start": "2026-09-01", "end_exclusive": "2026-10-01", "metric_version": "coverage-v1"}


def example():
    now = [0.0]
    app = CachedBusiness(cache=ResultCache(timer=lambda: now[0]))
    p = app.demo.authenticate("Bearer demo-tenant-a")
    first = app.query(p, fixture_query())
    now[0] = 2.0
    second = app.query(p, fixture_query())
    now[0] = 5.0
    third = app.query(p, fixture_query())
    return {"events": [first, second, third], "executions": app.executions}


if __name__ == "__main__":
    print(json.dumps(example(), ensure_ascii=False, indent=2, allow_nan=False))
