"""Independent task registry teaching demo. No LLM or external APIs.

Reuses synthetic calculations from api_agent_demo; not a framework adapter.
Plans are internal values, not signatures, authorization grants or public input.
"""
from dataclasses import dataclass, asdict
import hashlib
import json

from api_agent_demo import DemoService, Principal, BusinessError, parse_query, fail


@dataclass(frozen=True)
class Access:
    principal: Principal
    tool_names: tuple[str, ...]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    goal: str
    object_type: str
    intent: str
    metric_version: str
    tool_version: str = "1"
    enabled: bool = True
    available: bool = True
    effect: str = "read"


@dataclass(frozen=True)
class Plan:
    catalog_revision: str
    tool_name: str
    tool_version: str
    proposal_json: str
    query_json: str


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


DEFAULT_TOOLS = (
    ToolSpec("region_category_coverage", "coverage", "region", "category_coverage", "coverage-v1"),
    ToolSpec("region_competitor_overlap", "overlap", "region", "co_visit", "co-visit-v1"),
)


class Registry:
    def __init__(self, specs=DEFAULT_TOOLS, service=None):
        self.specs = tuple(specs)
        names = set()
        for s in self.specs:
            if not isinstance(s, ToolSpec) or not all(type(getattr(s, k)) is str and getattr(s, k)
                for k in ("name", "goal", "object_type", "intent", "metric_version", "tool_version")):
                raise ValueError("invalid tool metadata")
            if s.name in names:
                raise ValueError("duplicate tool name")
            names.add(s.name)
            if any(type(getattr(s, k)) is not bool for k in ("enabled", "available")):
                raise ValueError("flags must be strict booleans")
            expected = {"category_coverage": "coverage-v1", "co_visit": "co-visit-v1"}
            if s.effect != "read" or expected.get(s.intent) != s.metric_version:
                raise ValueError("only implemented read adapters may register")
        # Order-independent release fingerprint, including disabled metadata.
        data = sorted((asdict(s) for s in self.specs), key=lambda s: s["name"])
        self.revision = hashlib.sha256(canonical(data).encode()).hexdigest()
        self.service = service if service is not None else DemoService()

    def manifest(self, access):
        return [{"name": s.name, "goal": s.goal, "object_type": s.object_type,
                 "tool_version": s.tool_version, "metric_version": s.metric_version,
                 "effect": s.effect}
                for s in sorted(self.specs, key=lambda s: s.name)
                if s.enabled and s.available and s.name in access.tool_names]

    def plan(self, access, proposal):
        if type(proposal) is not dict or set(proposal) != {"goal", "object_type", "parameters"}:
            fail(422, "INVALID_PROPOSAL", "提案必须只含目标、对象类型和参数")
        if any(type(proposal[k]) is not str or not 1 <= len(proposal[k]) <= 40
               for k in ("goal", "object_type")):
            fail(422, "INVALID_PROPOSAL", "目标与对象类型必须为受限字符串")
        params = proposal["parameters"]
        allowed = {"region_id", "population_type", "start", "end_exclusive", "competitor_id", "max_tool_calls"}
        if type(params) is not dict or set(params) - allowed:
            fail(422, "INVALID_PARAMETERS", "参数不能含身份、工具名、意图、指标版本或未知字段")
        matches = [s for s in self.specs if s.enabled and
                   (s.goal, s.object_type) == (proposal["goal"], proposal["object_type"])]
        if not matches:
            fail(422, "UNSUPPORTED_TASK", "没有支持此目标与对象类型的能力")
        authorized = [s for s in matches if s.name in access.tool_names]
        if not authorized:
            fail(403, "CAPABILITY_FORBIDDEN", "当前身份没有此任务能力")
        ready = [s for s in authorized if s.available]
        if not ready:
            fail(503, "CAPABILITY_UNAVAILABLE", "授权能力当前不可用")
        if len(ready) > 1:
            fail(409, "NEEDS_CLARIFICATION", "多个授权能力匹配，需要补充业务条件")
        s = ready[0]
        # Inject trusted adapter constants before independent business validation.
        query = {**params, "intent": s.intent, "metric_version": s.metric_version}
        parse_query(query)
        return Plan(self.revision, s.name, s.tool_version, canonical(proposal), canonical(query))

    def execute(self, access, plan):
        if type(plan) is not Plan or plan.catalog_revision != self.revision:
            fail(409, "STALE_PLAN", "计划与注册表版本不一致")
        # Re-route under current access. A stored plan never grants permission.
        try:
            proposal = json.loads(plan.proposal_json)
        except (ValueError, TypeError):
            fail(422, "INVALID_PLAN", "计划提案不是JSON")
        expected = self.plan(access, proposal)
        if expected != plan:
            fail(409, "PLAN_MISMATCH", "计划工具、版本或参数被修改")
        result = self.service.execute(access.principal, parse_query(json.loads(plan.query_json)))
        return {"route": {"tool_name": plan.tool_name, "tool_version": plan.tool_version,
                          "catalog_revision": self.revision, "reason": "exact_goal_and_object_type"},
                "business": result}


def proposal(goal="coverage", **changes):
    parameters = {"region_id": "area-alpha", "population_type": 4,
                  "start": "2026-09-01", "end_exclusive": "2026-10-01"}
    parameters.update(changes)
    return {"goal": goal, "object_type": "region", "parameters": parameters}


def fixture_access(registry):
    return Access(registry.service.authenticate("Bearer demo-tenant-a"),
                  tuple(s.name for s in DEFAULT_TOOLS))


def examples():
    registry = Registry()
    access = fixture_access(registry)
    return [registry.execute(access, registry.plan(access, p)) for p in
            (proposal(), proposal("overlap", competitor_id="poi-rival"))]


if __name__ == "__main__":
    print(json.dumps(examples(), ensure_ascii=False, indent=2, allow_nan=False))
