"""Original conservative catalog guard, not an MCP client or schema validator."""
from dataclasses import dataclass
import hashlib
import json
import unittest


MODERN = "2026-07-28"
LEGACY = "2025-11-25"


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode()


def digest(tool, semantic_revision):
    # Deliberately conservative: descriptions/annotations also affect planning.
    return hashlib.sha256(encoded({"definition": tool,
                                  "semantic_revision": semantic_revision})).hexdigest()


@dataclass(frozen=True)
class Scope:
    endpoint: str
    tenant: str
    subject: str
    permission_revision: str
    protocol: str


@dataclass(frozen=True)
class Plan:
    scope: Scope
    generation: int
    name: str
    fingerprint: str
    arguments: bytes


class Catalog:
    def __init__(self, scope):
        self.scope = scope
        self.generation = 0
        self.valid = False
        self.definitions = {}

    def invalidate(self):
        self.generation += 1
        self.valid = False

    def refresh(self, tools, semantic_revision):
        # All pages must have been collected by the caller; no incremental publish.
        staged = {}
        for tool in tools:
            name = tool["name"]
            if not isinstance(name, str) or not name or name in staged:
                raise ValueError("invalid or duplicate tool name")
            staged[name] = digest(tool, semantic_revision)
        self.definitions = staged
        self.generation += 1
        self.valid = True

    def plan(self, name, arguments):
        if not self.valid:
            raise ValueError("catalog invalid")
        if name not in self.definitions:
            raise ValueError("unknown tool")
        return Plan(self.scope, self.generation, name,
                    self.definitions[name], encoded(arguments))

    def dispatch(self, plan, current_scope, operation):
        if not self.valid or plan.scope != self.scope or current_scope != self.scope:
            raise ValueError("scope/catalog changed")
        if plan.generation != self.generation:
            raise ValueError("stale generation")
        if self.definitions.get(plan.name) != plan.fingerprint:
            raise ValueError("contract changed")
        return operation(plan.name, json.loads(plan.arguments))


def choose_version(client_preference, server_supported):
    for version in client_preference:
        if version in server_supported:
            return version
    raise ValueError("no mutually supported version")


def classify(response, request_id, protocol):
    if protocol not in (MODERN, LEGACY):
        raise ValueError("unsupported teaching profile")
    if response.get("jsonrpc") != "2.0":
        raise ValueError("invalid envelope")
    if type(response.get("id")) is not type(request_id) or response.get("id") != request_id:
        raise ValueError("response id mismatch")
    if ("result" in response) == ("error" in response):
        raise ValueError("exactly one result/error required")
    if "error" in response:
        error = response["error"]
        if not isinstance(error, dict) or type(error.get("code")) is not int:
            raise ValueError("invalid error")
        if not isinstance(error.get("message"), str):
            raise ValueError("invalid error message")
        return "protocol_error"
    result = response["result"]
    if not isinstance(result, dict):
        raise ValueError("invalid result")
    kind = result.get("resultType", "complete" if protocol == LEGACY else None)
    if kind == "input_required":
        if protocol != MODERN or not isinstance(result.get("inputRequests"), dict):
            raise ValueError("invalid input request")
        return "needs_input"
    if kind != "complete":
        raise ValueError("missing/unknown resultType")
    if type(result.get("isError", False)) is not bool:
        raise ValueError("invalid isError")
    return "tool_error" if result.get("isError", False) else "complete_candidate"


TOOL = {"name": "poi_profile", "description": "monthly visitor profile",
        "inputSchema": {"type": "object", "properties": {"poi_id": {"type": "string"}}},
        "outputSchema": {"type": "object"}, "annotations": {"readOnlyHint": True}}


class Checks(unittest.TestCase):
    def setUp(self):
        self.scope = Scope("https://mock.invalid/mcp", "tenant-a", "user-a", "p1", MODERN)
        self.catalog = Catalog(self.scope)
        self.catalog.refresh([TOOL], "metric-v1")
        self.calls = []

    def operation(self, name, arguments):
        self.calls.append((name, arguments))
        return "mock receipt"

    def response(self, result):
        return {"jsonrpc": "2.0", "id": 1, "result": result}

    def test_01_valid_dispatch(self):
        p = self.catalog.plan("poi_profile", {"poi_id": "P1"})
        self.assertEqual(self.catalog.dispatch(p, self.scope, self.operation), "mock receipt")

    def test_02_object_key_order_stable(self):
        self.assertEqual(digest({"a": 1, "b": 2}, "v1"), digest({"b": 2, "a": 1}, "v1"))

    def test_03_semantic_change_detected(self):
        self.assertNotEqual(digest(TOOL, "metric-v1"), digest(TOOL, "metric-v2"))

    def test_04_description_change_detected(self):
        self.assertNotEqual(digest(TOOL, "v1"), digest(dict(TOOL, description="resident profile"), "v1"))

    def test_05_mutated_arguments_do_not_change_plan(self):
        args = {"poi_id": "P1"}
        p = self.catalog.plan("poi_profile", args)
        args["poi_id"] = "P2"
        self.catalog.dispatch(p, self.scope, self.operation)
        self.assertEqual(self.calls[0][1], {"poi_id": "P1"})

    def test_06_list_change_blocks_old_plan(self):
        p = self.catalog.plan("poi_profile", {})
        self.catalog.invalidate()
        with self.assertRaises(ValueError):
            self.catalog.dispatch(p, self.scope, self.operation)
        self.assertEqual(self.calls, [])

    def test_07_refresh_does_not_revive_old_plan(self):
        p = self.catalog.plan("poi_profile", {})
        self.catalog.refresh([TOOL], "metric-v1")
        with self.assertRaises(ValueError):
            self.catalog.dispatch(p, self.scope, self.operation)

    def test_08_permission_change_blocks(self):
        p = self.catalog.plan("poi_profile", {})
        changed = Scope(self.scope.endpoint, "tenant-a", "user-a", "p2", MODERN)
        with self.assertRaises(ValueError):
            self.catalog.dispatch(p, changed, self.operation)
        self.assertEqual(self.calls, [])

    def test_09_endpoint_and_tenant_are_isolated(self):
        p = self.catalog.plan("poi_profile", {})
        for changed in (Scope("https://other.invalid", "tenant-a", "user-a", "p1", MODERN),
                        Scope(self.scope.endpoint, "tenant-b", "user-a", "p1", MODERN)):
            with self.assertRaises(ValueError):
                self.catalog.dispatch(p, changed, self.operation)

    def test_10_duplicate_catalog_rejected_atomically(self):
        before = self.catalog.generation
        with self.assertRaises(ValueError):
            self.catalog.refresh([TOOL, TOOL], "v2")
        self.assertEqual(self.catalog.generation, before)
        self.assertEqual(set(self.catalog.definitions), {"poi_profile"})

    def test_11_version_selection_and_no_intersection(self):
        self.assertEqual(choose_version([MODERN, LEGACY], [LEGACY]), LEGACY)
        with self.assertRaises(ValueError):
            choose_version([MODERN], [LEGACY])

    def test_12_response_id_exact_type(self):
        for wrong in ("1", True, 2):
            r = self.response({"resultType": "complete"})
            r["id"] = wrong
            with self.assertRaises(ValueError):
                classify(r, 1, MODERN)

    def test_13_result_error_exclusive(self):
        r = self.response({"resultType": "complete"})
        r["error"] = {"code": -32602, "message": "bad"}
        with self.assertRaises(ValueError):
            classify(r, 1, MODERN)

    def test_14_protocol_error_vs_tool_error(self):
        self.assertEqual(classify({"jsonrpc": "2.0", "id": 1, "error": {"code": -32602, "message": "unknown"}}, 1, MODERN), "protocol_error")
        self.assertEqual(classify(self.response({"resultType": "complete", "isError": True}), 1, MODERN), "tool_error")

    def test_15_input_required_is_not_complete(self):
        self.assertEqual(classify(self.response({"resultType": "input_required", "inputRequests": {}}), 1, MODERN), "needs_input")

    def test_16_legacy_missing_tag_vs_modern(self):
        self.assertEqual(classify(self.response({}), 1, LEGACY), "complete_candidate")
        with self.assertRaises(ValueError):
            classify(self.response({}), 1, MODERN)

    def test_17_unknown_tag_and_bad_error_flag_rejected(self):
        for result in ({"resultType": "new_kind"}, {"resultType": "complete", "isError": "false"}):
            with self.assertRaises(ValueError):
                classify(self.response(result), 1, MODERN)

    def test_18_nonfinite_arguments_rejected(self):
        with self.assertRaises(ValueError):
            self.catalog.plan("poi_profile", {"value": float("nan")})


if __name__ == "__main__":
    unittest.main(verbosity=2)
