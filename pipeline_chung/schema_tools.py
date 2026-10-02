"""Công cụ schema dùng chung cho 21 dạng bài.

1. make_api_schema(): từ schema đầy đủ (dùng cho Python kiểm tra) tạo bản gửi GPT ở chế độ strict:
   - bỏ các khóa ngoài chuẩn: $schema, title, $id, các khóa bắt đầu bằng "x-"
   - bỏ các định nghĩa trong $defs không được dùng tới
   - (tùy chọn --bo-rang-buoc) bỏ minimum/maximum/minItems/maxItems nếu gateway không hỗ trợ
2. check_strict(): kiểm tra schema có đúng yêu cầu chế độ strict không
   (mọi object có additionalProperties: false, mọi thuộc tính đều nằm trong required, gốc là object,
   không dùng từ khóa lạ).

Cách chạy:
  python pipeline_chung/schema_tools.py <schema.json>                  # tạo <tên>.api.json cạnh file gốc
  python pipeline_chung/schema_tools.py <schema.json> --bo-rang-buoc   # bỏ thêm min/max
"""
import argparse
import copy
import json
import os
import sys

DROP_KEYS = {"$schema", "title", "$id", "$comment"}
CONSTRAINT_KEYS = {"minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "minItems", "maxItems"}
ALLOWED_KEYS = {"type", "properties", "required", "additionalProperties", "items", "enum", "const", "anyOf",
                "$ref", "$defs", "description", "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
                "minItems", "maxItems", "pattern", "format", "multipleOf"}


def _refs(o, out):
    if isinstance(o, dict):
        if isinstance(o.get("$ref"), str) and o["$ref"].startswith("#/$defs/"):
            out.add(o["$ref"].split("/")[-1])
        for v in o.values():
            _refs(v, out)
    elif isinstance(o, list):
        for v in o:
            _refs(v, out)


def _clean(o, strip_constraints, in_properties=False):
    if isinstance(o, dict):
        res = {}
        for k, v in o.items():
            if not in_properties:  # tên thuộc tính (trong "properties") thì giữ nguyên
                if k in DROP_KEYS or k.startswith("x-"):
                    continue
                if strip_constraints and k in CONSTRAINT_KEYS:
                    continue
            res[k] = _clean(v, strip_constraints, in_properties=(k in ("properties", "$defs") and not in_properties))
        return res
    if isinstance(o, list):
        return [_clean(v, strip_constraints) for v in o]
    return o


def make_api_schema(schema, strip_constraints=False):
    s = _clean(copy.deepcopy(schema), strip_constraints)
    if "$defs" in s:
        used = set()
        _refs({k: v for k, v in s.items() if k != "$defs"}, used)
        changed = True
        while changed:  # định nghĩa này có thể dùng định nghĩa khác
            before = set(used)
            for name in list(used):
                _refs(s["$defs"].get(name, {}), used)
            changed = used != before
        s["$defs"] = {k: v for k, v in s["$defs"].items() if k in used}
        if not s["$defs"]:
            del s["$defs"]
    return s


def check_strict(schema):
    problems = []
    if schema.get("type") != "object":
        problems.append("gốc phải là type: object")

    def walk(o, path):
        if isinstance(o, dict):
            for k in o:
                if k not in ALLOWED_KEYS and not path.endswith(("properties", "$defs")):
                    problems.append(f"{path}: từ khóa '{k}' có thể không được chế độ strict hỗ trợ")
            t = o.get("type")
            if t == "object" or (isinstance(t, list) and "object" in t):
                if o.get("additionalProperties") is not False:
                    problems.append(f"{path}: thiếu additionalProperties: false")
                props = set((o.get("properties") or {}).keys())
                req = set(o.get("required") or [])
                if props != req:
                    problems.append(f"{path}: required phải gồm đủ mọi thuộc tính (thiếu: {sorted(props - req)})")
            for k, v in o.items():
                walk(v, f"{path}.{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{path}[{i}]")

    walk(schema, "$")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("schema")
    ap.add_argument("--bo-rang-buoc", action="store_true", help="bỏ minimum/maximum/minItems/maxItems")
    args = ap.parse_args()
    with open(args.schema, encoding="utf-8") as f:
        full = json.load(f)
    api = make_api_schema(full, args.bo_rang_buoc)
    out = os.path.splitext(args.schema)[0] + ".api.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(api, f, ensure_ascii=False, indent=2)
    probs = check_strict(api)
    print(f"Đã tạo {out}")
    print("Kiểm tra chế độ strict:", "ĐẠT" if not probs else "")
    for x in probs:
        print("  -", x)
    sys.exit(1 if probs else 0)


if __name__ == "__main__":
    main()
