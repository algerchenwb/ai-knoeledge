"""Local HTTP orchestration demo with synthetic data and public fixture tokens.

No LLM, OAuth/JWT, external network, production database or framework required.
Python's http.server is used for teaching, not as a production deployment server.
"""
from dataclasses import dataclass
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import argparse
import json
import re
import uuid


class BusinessError(Exception):
    def __init__(self, http_status, code, message):
        self.http_status, self.code, self.message = http_status, code, message


def fail(status, code, message):
    raise BusinessError(status, code, message)


@dataclass(frozen=True)
class Principal:
    tenant: str
    regions: tuple[str, ...]


@dataclass(frozen=True)
class Query:
    intent: str
    region_id: str
    population_type: int
    start: str
    end_exclusive: str
    metric_version: str
    competitor_id: str | None
    max_tool_calls: int


def parse_query(raw):
    required = {"intent", "region_id", "population_type", "start", "end_exclusive", "metric_version"}
    allowed = required | {"competitor_id", "max_tool_calls"}
    if not isinstance(raw, dict) or not required <= raw.keys() or raw.keys() - allowed:
        fail(422, "INVALID_FIELDS", "缺少必需字段或包含未允许字段")
    for key in ["intent", "region_id", "start", "end_exclusive", "metric_version"]:
        if not isinstance(raw[key], str) or not 1 <= len(raw[key]) <= 80:
            fail(422, "INVALID_TYPE", f"{key}必须是非空且长度受限的字符串")
    if raw["intent"] not in {"category_coverage", "co_visit"}:
        fail(422, "UNSUPPORTED_INTENT", "只支持两个只读分析意图")
    population = raw["population_type"]
    budget = raw.get("max_tool_calls", 2)
    if type(population) is not int or population not in {1, 2, 3, 4}:
        fail(422, "INVALID_POPULATION", "population_type必须是1到4的整数")
    if type(budget) is not int or not 1 <= budget <= 3:
        fail(422, "INVALID_BUDGET", "工具调用预算必须是1到3的整数")
    try:
        if any(not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw[k]) for k in ["start", "end_exclusive"]):
            raise ValueError()
        start, end = date.fromisoformat(raw["start"]), date.fromisoformat(raw["end_exclusive"])
        if not 1 <= (end - start).days <= 90:
            raise ValueError()
    except ValueError:
        fail(422, "INVALID_WINDOW", "日期必须是YYYY-MM-DD，窗口为1到90天的半开区间")
    competitor = raw.get("competitor_id")
    if raw["intent"] == "co_visit":
        if not isinstance(competitor, str) or not 1 <= len(competitor) <= 80:
            fail(422, "MISSING_COMPETITOR", "共访需要competitor_id")
    elif competitor is not None:
        fail(422, "UNUSED_COMPETITOR", "业态占比不能携带竞品参数")
    return Query(raw["intent"], raw["region_id"], population, raw["start"], raw["end_exclusive"],
                 raw["metric_version"], competitor, budget)


@dataclass(frozen=True)
class Snapshot:
    users: tuple[str, ...]
    category_visitors: tuple[str, ...]
    start: str = "2026-09-01"
    end_exclusive: str = "2026-10-01"
    population_type: int = 4
    definition_version: str = "population-v1"
    data_version: str = "synthetic-2026-09"
    mature: bool = True
    available: bool = True


class DemoService:
    def __init__(self):
        # Public test tokens: not real credentials or authentication design.
        self.principals = {
            "demo-tenant-a": Principal("tenant-a", ("area-alpha", "area-empty", "area-provisional", "area-version-mismatch", "area-unavailable")),
            "demo-tenant-b": Principal("tenant-b", ("area-beta",)),
        }
        self.snapshots = {
            ("tenant-a", "area-alpha"): Snapshot(("u1", "u2", "u3", "u4"), ("u2", "u2", "u4", "u9")),
            ("tenant-a", "area-empty"): Snapshot((), ()),
            ("tenant-a", "area-provisional"): Snapshot(("u1",), ("u1",), mature=False),
            ("tenant-a", "area-version-mismatch"): Snapshot(("u1",), ("u1",), definition_version="population-old"),
            ("tenant-a", "area-unavailable"): Snapshot((), (), available=False),
            ("tenant-b", "area-beta"): Snapshot(("b1",), ()),
        }
        self.competitors = {("tenant-a", "poi-rival"): ("u2", "u4"), ("tenant-a", "poi-empty"): ()}

    def authenticate(self, authorization):
        if not authorization or not authorization.startswith("Bearer "):
            fail(401, "UNAUTHENTICATED", "需要Bearer演示身份")
        principal = self.principals.get(authorization[7:])
        if principal is None:
            fail(401, "UNAUTHENTICATED", "演示身份无效")
        return principal

    def execute(self, principal, q):
        # Authorization occurs before any object/metric tool call.
        if q.region_id not in principal.regions:
            fail(403, "OBJECT_FORBIDDEN", "对象不在当前身份允许范围")
        expected = "coverage-v1" if q.intent == "category_coverage" else "co-visit-v1"
        if q.metric_version != expected:
            fail(409, "METRIC_VERSION_MISMATCH", "请求指标版本与意图不一致")
        trace = []
        def call(name, function):
            if len(trace) >= q.max_tool_calls:
                fail(429, "TOOL_BUDGET_EXCEEDED", "本次任务工具预算不足")
            trace.append({"step": len(trace) + 1, "tool": name})
            return function()
        snapshot = call("resolve_authorized_snapshot", lambda: self.snapshots.get((principal.tenant, q.region_id)))
        if snapshot is None:
            fail(404, "NO_SNAPSHOT", "当前授权对象没有数据快照")
        if not snapshot.available:
            fail(502, "UPSTREAM_UNAVAILABLE", "模拟数据源不可用")
        if (q.start, q.end_exclusive, q.population_type) != (snapshot.start, snapshot.end_exclusive, snapshot.population_type):
            fail(409, "DATA_SCOPE_MISMATCH", "数据快照不覆盖请求窗口或人群口径")
        if snapshot.definition_version != "population-v1":
            fail(409, "DATA_DEFINITION_MISMATCH", "数据快照的集合定义版本不匹配")
        context = {"region_id": q.region_id, "population_type": q.population_type,
                   "window": {"start": q.start, "end_exclusive": q.end_exclusive, "timezone": "Asia/Shanghai"},
                   "metric_version": q.metric_version, "data_version": snapshot.data_version,
                   "population_definition_version": snapshot.definition_version}
        if not snapshot.mature:
            return {"status": "provisional", "context": context, "result": None,
                    "answer": "数据尚未成熟，暂不输出正式占比。", "trace": trace}
        users = set(snapshot.users)
        if q.intent == "category_coverage":
            def calculate():
                numerator, denominator = len(users & set(snapshot.category_visitors)), len(users)
                return {"numerator": numerator, "denominator": denominator,
                        "ratio": None if denominator == 0 else numerator / denominator}
            result = call("calculate_category_coverage", calculate)
            status = "ok" if users else "no_denominator"
            answer = (f"指定窗口内，{result['denominator']}名去重区域用户中有{result['numerator']}名到访目标业态，占{result['ratio']:.0%}。"
                      if users else "分母为空，无法计算占比。")
        else:
            def calculate():
                rival = self.competitors.get((principal.tenant, q.competitor_id))
                if rival is None:
                    fail(403, "COMPETITOR_FORBIDDEN", "竞品不在当前身份可查询范围")
                b = set(rival)
                overlap = len(users & b)
                return {"competitor_id": q.competitor_id, "overlap": overlap,
                        "reference_share": None if not users else overlap / len(users),
                        "competitor_share": None if not b else overlap / len(b)}
            result = call("calculate_co_visit", calculate)
            status = "ok" if users and result["competitor_share"] is not None else "no_denominator"
            # One-sided empty populations are not described as zero-percent.
            answer = (f"共访{result['overlap']}人；本区域人群方向为{result['reference_share']:.0%}，竞品人群方向为{result['competitor_share']:.0%}。"
                      if result['reference_share'] is not None and result['competitor_share'] is not None
                      else "至少一个方向分母为空，不能输出完整方向比例。")
        return {"status": status, "context": context, "result": result, "answer": answer,
                "evidence": [{"source_id": f"fixture:{principal.tenant}:{q.region_id}", "data_version": snapshot.data_version}], "trace": trace}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # No tokens or request bodies in access logs.

    def send_json(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        if status == 401:
            self.send_header("WWW-Authenticate", "Bearer")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        request_id = uuid.uuid4().hex
        try:
            if self.path != "/v1/agent/query":
                fail(404, "NO_ROUTE", "接口不存在")
            principal = self.server.service.authenticate(self.headers.get("Authorization"))
            if self.headers.get("Transfer-Encoding"):
                fail(400, "UNSUPPORTED_TRANSFER", "演示服务仅接受Content-Length请求")
            if self.headers.get_content_type() != "application/json":
                fail(415, "UNSUPPORTED_MEDIA", "需要application/json")
            try:
                length = int(self.headers.get("Content-Length", "-1"))
            except ValueError:
                fail(400, "INVALID_LENGTH", "请求长度无效")
            if not 0 <= length <= 16384:
                fail(413, "BODY_TOO_LARGE", "请求体缺少长度或超过16KiB")
            self.connection.settimeout(3)
            try:
                raw = self.rfile.read(length)
            except TimeoutError:
                fail(408, "BODY_TIMEOUT", "读取请求体超时")
            if len(raw) != length:
                fail(400, "INCOMPLETE_BODY", "请求体长度与声明不一致")
            def reject_constant(value):
                raise ValueError("non-standard JSON constant")
            def unique_object(pairs):
                data = {}
                for key, value in pairs:
                    if key in data:
                        raise ValueError("duplicate JSON key")
                    data[key] = value
                return data
            try:
                raw = json.loads(raw, parse_constant=reject_constant, object_pairs_hook=unique_object)
            except (ValueError, UnicodeDecodeError):
                fail(400, "INVALID_JSON", "JSON无效、重复字段或含非标准数值")
            result = self.server.service.execute(principal, parse_query(raw))
            self.send_json(200, {"request_id": request_id, **result})
        except BusinessError as e:
            self.send_json(e.http_status, {"request_id": request_id, "status": "error",
                                         "error": {"code": e.code, "message": e.message}})


def make_server(port=0):
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.service = DemoService()
    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    with make_server(args.port) as server:
        print(f"Local synthetic demo: http://127.0.0.1:{server.server_port}/v1/agent/query", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
