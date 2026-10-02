"""Bước 2 – Kiểm tra JSON tiếng Việt do Claude tạo ra.

Kiểm tra cho từng mẫu trong json_vi/<run>/ (run = haiku | sonnet | final):
  1. Có file và parse được JSON
  2. Khớp schema (explanation_schemas_v1.json)
  3. question_id, cau_con, correct.index khớp dữ liệu gốc
  4. Không mất tiếng Nhật: mọi đoạn tiếng Nhật trong lời giải gốc đều có trong JSON
  5. Không mất / không tự viết lại tiếng Việt: độ phủ từ và tỷ lệ từ thừa
  6. Quy tắc đánh dấu: { } gạch chân (ja có thì reading/meaning cũng có), ⟪ ⟫ chỉ bọc tiếng Nhật

Cách chạy:
  python scripts/validate_json_vi.py haiku
  python scripts/validate_json_vi.py sonnet
  python scripts/validate_json_vi.py final
Kết quả: reports/validate_vi_<run>.json và bảng tóm tắt in ra màn hình.
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (JA_RE, LOCK_RE, clean_html, iter_lang_fields, iter_sentences, load_config, load_json,  # noqa: E402
                    load_raw, load_samples, norm_ja, p, raw_ja_runs, raw_vi_text, save_json, strip_labels,
                    vi_words)

try:
    import jsonschema
except ImportError:
    jsonschema = None


STRUCT_WORDS = {"nghĩa", "là", "có", "ví", "dụ", "mang"}


def _validator_cls():
    """jsonschema bản mới có Draft202012Validator; bản cũ dùng Draft7Validator (vẫn đọc được $ref '#/$defs/...')."""
    return getattr(jsonschema, "Draft202012Validator", None) or jsonschema.Draft7Validator


def check_one(sample, run, schemas, cfg):
    sid = sample["sample_id"]
    issues, warnings = [], []
    path = p("json_vi", run, sid + ".json")
    if not os.path.exists(path):
        return {"sample_id": sid, "status": "THIẾU FILE", "issues": ["Không có file JSON"], "warnings": []}
    try:
        data = load_json(path)
    except json.JSONDecodeError as e:
        return {"sample_id": sid, "status": "LỖI JSON", "issues": [f"Không parse được: {e}"], "warnings": []}
    raw = load_raw(sid)

    # 2. schema
    schema = schemas.get(sample["schema"])
    if jsonschema is None:
        warnings.append("Chưa cài jsonschema – bỏ qua kiểm tra schema")
    elif schema is None:
        issues.append(f"Không tìm thấy schema {sample['schema']}")
    else:
        for err in sorted(_validator_cls()(schema).iter_errors(data), key=lambda e: list(e.path)):
            issues.append(f"Schema: {'/'.join(map(str, err.path)) or '(gốc)'} – {err.message[:160]}")

    # 3. định danh & đáp án
    if str(data.get("question_id")) != str(raw["question_id"]):
        issues.append(f"question_id {data.get('question_id')} ≠ {raw['question_id']}")
    if str(data.get("cau_con")) != str(raw["cau_con"]):
        issues.append(f"cau_con {data.get('cau_con')} ≠ {raw['cau_con']}")
    correct = data.get("correct") or {}
    if str(correct.get("index")) != str(raw["dap_an_so"]):
        issues.append(f"correct.index {correct.get('index')} ≠ dap_an_so {raw['dap_an_so']}")
    ans = clean_html(raw.get(f"lua_chon_{raw['dap_an_so']}", ""))
    if ans and norm_ja(correct.get("option_ja", "")) != norm_ja(ans):
        warnings.append(f"correct.option_ja '{correct.get('option_ja')}' khác lựa chọn gốc '{ans}'")

    # 4. tiếng Nhật không bị mất
    dump = norm_ja(json.dumps(data, ensure_ascii=False))
    missing = [r for r in raw_ja_runs(raw) if norm_ja(r) not in dump]
    if missing:
        issues.append(f"Mất {len(missing)} đoạn tiếng Nhật: {missing[:8]}")

    # 5. tiếng Việt: độ phủ & từ thừa (so theo túi từ)
    # Bỏ các từ nối thường bị lược khi tách "Nghĩa là ...", "có nghĩa là", "Ví dụ:" sang trường riêng
    src = collections.Counter(w for w in vi_words(strip_labels(raw_vi_text(raw))) if w not in STRUCT_WORDS)
    out = collections.Counter(w for _, o in iter_lang_fields(data) for w in vi_words(o["vi"]) if w not in STRUCT_WORDS)
    if src:
        coverage = sum((src & out).values()) / sum(src.values())
        extra = sum((out - src).values()) / max(1, sum(out.values()))
        if coverage < cfg["checks"]["vi_word_coverage_min"]:
            lost = [w for w, _ in (src - out).most_common(12)]
            issues.append(f"Độ phủ tiếng Việt {coverage:.1%} (thiếu các từ như: {lost})")
        if extra > cfg["checks"]["vi_extra_words_max"]:
            added = [w for w, _ in (out - src).most_common(12)]
            warnings.append(f"Từ thừa {extra:.1%} – có thể đã viết lại câu (VD: {added})")
    else:
        coverage, extra = None, None

    # 6. quy tắc đánh dấu
    for sp, s in iter_sentences(data):
        n = (s.get("ja") or "").count("{")
        if n > 1 or (s.get("ja") or "").count("}") != n:
            issues.append(f"{sp}.ja: dấu {{ }} sai (mỗi câu tối đa 1 cặp)")
        if n == 1:
            for key, val in (("reading", s.get("reading")), ("meaning.vi", (s.get("meaning") or {}).get("vi"))):
                if val is not None and not (val.count("{") == 1 and val.count("}") == 1):
                    issues.append(f"{sp}.{key}: ja có gạch chân {{ }} nhưng trường này không có đúng 1 cặp")
    empty = [fp for fp, o in iter_lang_fields(data) if not o["vi"].strip()]
    if empty:
        issues.append(f"{len(empty)} trường tiếng Việt bị để trống, VD: {empty[:4]}")
    for fp, o in iter_lang_fields(data):
        t = o["vi"]
        if t.count("⟪") != t.count("⟫"):
            issues.append(f"{fp}: số ⟪ và ⟫ không bằng nhau")
        for inner in LOCK_RE.findall(t):
            if not JA_RE.search(inner):
                warnings.append(f"{fp}: ⟪{inner}⟫ không chứa tiếng Nhật")
        outside = LOCK_RE.sub("", t)
        if JA_RE.search(outside):
            warnings.append(f"{fp}: còn tiếng Nhật chưa bọc ⟪ ⟫: {JA_RE.findall(outside)[:5]}")

    status = "LỖI" if issues else ("CẢNH BÁO" if warnings else "ĐẠT")
    return {"sample_id": sid, "dang_bai": sample["dang_bai"], "status": status,
            "vi_coverage": coverage, "vi_extra": extra, "issues": issues, "warnings": warnings}


def main():
    if len(sys.argv) != 2:
        sys.exit("Cách dùng: python scripts/validate_json_vi.py <haiku|sonnet|final>")
    run = sys.argv[1]
    cfg = load_config()
    schemas = load_json(p(cfg["schema_file"]))
    results = [check_one(s, run, schemas, cfg) for s in load_samples()]
    save_json({"run": run, "results": results}, p("reports", f"validate_vi_{run}.json"))

    counts = collections.Counter(r["status"] for r in results)
    print(f"== Kiểm tra JSON tiếng Việt – {run} ==")
    for r in results:
        print(f"{r['status']:9} {r['sample_id']}")
        for i in r["issues"]:
            print("   ✗", i)
        for w in r["warnings"]:
            print("   !", w)
    print("Tổng:", dict(counts), f"→ reports/validate_vi_{run}.json")


if __name__ == "__main__":
    main()
