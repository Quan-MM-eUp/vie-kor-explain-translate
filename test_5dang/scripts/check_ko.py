"""Bước 4 – Kiểm tra tự động bản dịch tiếng Hàn.

So json_ko/<model>/<id>.json với json_vi/final/<id>.json:
  1. Bỏ khóa "ko" đi thì phải GIỐNG HỆT bản tiếng Việt chuẩn (không sửa tiếng Nhật, không sửa tiếng Việt)
  2. Mọi trường "vi" đều có "ko" không rỗng
  3. Nội dung trong ⟪ ⟫ giữ nguyên từng ký tự (đủ, không thừa; được đổi thứ tự)
  4. Gạch chân { }: vi có 1 cặp thì ko cũng phải có đúng 1 cặp
  5. Không còn chữ tiếng Việt có dấu trong ko
  6. Không có tiếng Nhật nằm ngoài ⟪ ⟫ trong ko
  7. Văn phong: câu kết thúc bằng "다." phải là -습니다/-ㅂ니다 (không dùng -한다/-이다)
  8. Tỷ lệ độ dài ko/vi nằm trong khoảng cấu hình

Cách chạy:
  python scripts/check_ko.py haiku
  python scripts/check_ko.py sonnet
  python scripts/check_ko.py opus opus      # so bản dịch Opus với json_vi/opus
Kết quả: reports/check_ko_<model>.json (có danh sách lỗi theo từng trường).
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (HANGUL_RE, JA_RE, LOCK_RE, VI_DIACRITIC_RE, drop_lang, iter_lang_fields, load_config,  # noqa: E402
                    load_json, load_samples, p, save_json)

# Chỉ kiểm tra văn phong -습니다 ở các trường là câu giải thích; nghĩa của từ (meaning, gloss…) được viết dạng từ điển -다
STYLE_FIELDS = {"analysis", "reference", "intro", "text", "note", "usage", "comment",
                "grammar_note", "semantic_note", "structure"}
PLAIN_STYLE_RE = re.compile(r"(?<!니)다[.!?]?[\"'”’)\]]*\s*$")


def check_field(path, vi, ko, ratio_rng):
    errs = []
    if not isinstance(ko, str) or not ko.strip():
        return [("thiếu bản dịch", "nghiêm trọng")]
    if sorted(LOCK_RE.findall(vi)) != sorted(LOCK_RE.findall(ko)):  # cho phép đổi thứ tự theo ngữ pháp tiếng Hàn
        errs.append(("nội dung ⟪ ⟫ bị thay đổi/thiếu/thừa", "nghiêm trọng"))
    if vi.count("{") == 1 and not (ko.count("{") == 1 and ko.count("}") == 1):
        errs.append(("mất hoặc sai dấu gạch chân { }", "nặng"))
    outside = LOCK_RE.sub("", ko)
    if VI_DIACRITIC_RE.search(outside):
        errs.append(("còn chữ tiếng Việt", "nặng"))
    if JA_RE.search(outside):
        errs.append((f"tiếng Nhật ngoài ⟪ ⟫: {JA_RE.findall(outside)[:3]}", "nhẹ"))
    last_key = re.sub(r"\[\d+\]$", "", path.rsplit(".", 1)[-1])
    style_check = last_key in STYLE_FIELDS or ".sentence_analysis" in path or ".arrangement.explanation" in path
    for sent in (re.split(r"(?<=[.!?])\s+|\n", outside) if style_check else []):
        if sent.strip() and PLAIN_STYLE_RE.search(sent.strip()):
            errs.append((f"văn phong -다 (không phải -습니다): …{sent.strip()[-20:]}", "nhẹ"))
            break
    vlen, klen = len(LOCK_RE.sub("", vi)), len(outside)
    if vlen >= 20 and HANGUL_RE.search(ko):
        r = klen / vlen
        if not ratio_rng[0] <= r <= ratio_rng[1]:
            errs.append((f"độ dài bất thường (ko/vi = {r:.2f})", "nhẹ"))
    return errs


def main():
    if len(sys.argv) not in (2, 3):
        sys.exit("Cách dùng: python scripts/check_ko.py <model> [bản_tiếng_Việt_gốc, mặc định final]")
    model = sys.argv[1]
    base = sys.argv[2] if len(sys.argv) == 3 else "final"
    cfg = load_config()
    lang = cfg["target_lang"]
    ratio = cfg["checks"]["ko_vi_length_ratio"]
    results = []
    for s in load_samples():
        sid = s["sample_id"]
        ko_path, vi_path = p("json_ko", model, sid + ".json"), p("json_vi", base, sid + ".json")
        rec = {"sample_id": sid, "dang_bai": s["dang_bai"], "fields": [], "issues": []}
        if not os.path.exists(vi_path):
            rec["issues"].append(f"Thiếu json_vi/{base} – chưa có bản tiếng Việt gốc")
        elif not os.path.exists(ko_path):
            rec["issues"].append("Thiếu file bản dịch")
        else:
            vi_json, ko_json = load_json(vi_path), load_json(ko_path)
            if drop_lang(ko_json, lang) != vi_json:
                rec["issues"].append(f"Cấu trúc/tiếng Nhật/tiếng Việt bị thay đổi so với json_vi/{base}")
            for fp, o in iter_lang_fields(ko_json):
                errs = check_field(fp, o["vi"], o.get(lang), ratio)
                rec["fields"].append({"path": fp, "vi": o["vi"], lang: o.get(lang),
                                      "errors": [{"loai": e, "muc_do": m} for e, m in errs]})
        n_err = sum(bool(f["errors"]) for f in rec["fields"])
        rec["status"] = "LỖI" if rec["issues"] or any(
            e["muc_do"] != "nhẹ" for f in rec["fields"] for e in f["errors"]) else ("CẢNH BÁO" if n_err else "ĐẠT")
        results.append(rec)

    save_json({"model": model, "results": results}, p("reports", f"check_ko_{model}.json"))
    print(f"== Kiểm tra bản dịch – {model} ==")
    for r in results:
        bad = [f for f in r["fields"] if f["errors"]]
        print(f"{r['status']:9} {r['sample_id']}  ({len(bad)}/{len(r['fields'])} trường có lỗi)")
        for i in r["issues"]:
            print("   ✗", i)
        for f in bad:
            for e in f["errors"]:
                print(f"   [{e['muc_do']}] {f['path']}: {e['loai']}")
    print("Tổng:", dict(collections.Counter(r["status"] for r in results)), f"→ reports/check_ko_{model}.json")


if __name__ == "__main__":
    main()
