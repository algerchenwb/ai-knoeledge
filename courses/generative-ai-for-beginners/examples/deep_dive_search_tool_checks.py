# 原创离线教学示例：无模型调用、无外部网络请求。
# 验证 deep-dives 第08与11课中的局部机制。
import math

def cosine(a, b):
    if len(a) != len(b) or not a:
        raise ValueError("向量维度必须相同且非空")
    if any(not math.isfinite(x) for x in (*a, *b)):
        raise ValueError("向量包含非有限值")
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        raise ValueError("零向量不可计算余弦相似度")
    score = sum(x * y for x, y in zip(a, b)) / (na * nb)
    return max(-1.0, min(1.0, score))


import json
import re

def execute_tool(name, raw_arguments, principal):
    if name != "get_region_profile":
        raise ValueError("未知工具")

    args = json.loads(raw_arguments)
    required = {"region_id", "month", "population_type"}
    if not isinstance(args, dict) or set(args) != required:
        raise ValueError("工具字段错误")
    if any(type(args[k]) is not str for k in required):
        raise ValueError("字段必须是字符串")
    if not re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])", args["month"]):
        raise ValueError("月份非法")
    if args["population_type"] not in {"resident", "work", "regular", "visitor"}:
        raise ValueError("人群类型非法")

    # principal由可信服务端身份层提供，不能来自模型参数。
    if args["region_id"] not in principal["allowed_regions"]:
        raise PermissionError("无区域访问权限")

    data = {
        ("example-A", "2026-09", "work"): 123
    }
    key = (args["region_id"], args["month"], args["population_type"])
    if key not in data:
        return {"status": "no_data", "data": None}

    return {
        "status": "ok",
        "data": {"population_scale": data[key]},
        "source": "fictional-fixture"
    }

import unittest

class DeepDiveChecks(unittest.TestCase):
    def test_cosine_geometry(self):
        self.assertAlmostEqual(cosine([1, 0], [2, 0]), 1)
        self.assertAlmostEqual(cosine([1, 0], [0, 1]), 0)
        self.assertAlmostEqual(cosine([1, 0], [-2, 0]), -1)

    def test_cosine_invalid_vectors(self):
        for a, b in [([], []), ([1], [1, 2]), ([0, 0], [1, 0]), ([float("nan")], [1]), ([float("inf")], [1])]:
            with self.subTest(a=a, b=b):
                with self.assertRaises(ValueError):
                    cosine(a, b)

    def setUp(self):
        self.args = {"region_id": "example-A", "month": "2026-09", "population_type": "work"}
        self.principal = {"allowed_regions": {"example-A"}}

    def run_tool(self, args, principal=None, name="get_region_profile"):
        return execute_tool(name, json.dumps(args), self.principal if principal is None else principal)

    def test_tool_known_result(self):
        result = self.run_tool(self.args)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["data"]["population_scale"], 123)

    def test_tool_empty_is_not_zero(self):
        result = self.run_tool(dict(self.args, month="2026-08"))
        self.assertEqual(result, {"status": "no_data", "data": None})

    def test_tool_rejects_unknown(self):
        with self.assertRaises(ValueError):
            self.run_tool(self.args, name="delete_all")

    def test_tool_rejects_missing_and_extra_fields(self):
        for args in [
            {"region_id": "example-A", "month": "2026-09"},
            dict(self.args, tenant_id="someone-else"),
        ]:
            with self.assertRaises(ValueError):
                self.run_tool(args)

    def test_tool_rejects_invalid_arguments(self):
        for patch in [{"month": "2026-13"}, {"month": 202609}, {"population_type": "all"}]:
            with self.assertRaises(ValueError):
                self.run_tool(dict(self.args, **patch))

    def test_tool_denies_untrusted_resource(self):
        with self.assertRaises(PermissionError):
            self.run_tool(dict(self.args, region_id="example-B"))
        with self.assertRaises(PermissionError):
            self.run_tool(self.args, {"allowed_regions": set()})

    def test_tool_rejects_non_object_json(self):
        with self.assertRaises(ValueError):
            execute_tool("get_region_profile", "[]", self.principal)

    def test_tool_rejects_invalid_json(self):
        with self.assertRaises(json.JSONDecodeError):
            execute_tool("get_region_profile", "{broken", self.principal)

if __name__ == "__main__":
    unittest.main()
