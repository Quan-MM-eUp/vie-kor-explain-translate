"""Bước 1 – Chọn mẫu test.

Chọn `samples_per_type` câu cho mỗi dạng bài trong config (mặc định 5), cố gắng trải đều N1–N5
và ưu tiên câu "khó" (có gạch chân, có tiếng Nhật chèn giữa câu tiếng Việt, có lựa chọn
"không tồn tại"). Kết quả cố định theo `seed` nên chạy lại vẫn ra cùng bộ mẫu.

Đầu ra:
  samples/samples.csv          – danh sách mẫu
  samples/raw/<sample_id>.json – dữ liệu gốc của từng mẫu (đầu vào cho Claude ở bước 2)

Cách chạy:
  python scripts/select_samples.py            # không ghi đè nếu đã có samples.csv
  python scripts/select_samples.py --force    # chọn lại và ghi đè
"""
import argparse
import csv
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (JA_RE, VI_DIACRITIC_RE, clean_html, load_config, p, save_json)  # noqa: E402

RAW_FIELDS = ["cap_do", "dang_bai", "question_id", "cau_con", "de_bai_chung", "doan_van", "cau_hoi",
              "lua_chon_1", "lua_chon_2", "lua_chon_3", "lua_chon_4", "dap_an_so", "dap_an_noi_dung",
              "giai_thich_vi", "giai_thich_ko"]


QUOTED_RE = re.compile(r"「.*?」|『.*?』|\".*?\"|“.*?”|'.*?'|\(.*?\)|（.*?）")
INLINE_JA_RE = re.compile(r"[a-zà-ỹđ]\s+[" + JA_RE.pattern[1:-2] + r"]+\s+[a-zà-ỹđ]", re.I)


def difficulty(row):
    """Điểm 'khó' để ưu tiên chọn và lý do chọn."""
    g = row["giai_thich_vi"]
    text = clean_html(g)
    reasons = []
    if re.search(r"<u[ >]", row["cau_hoi"] + g):
        reasons.append("có gạch chân")
    if any(INLINE_JA_RE.search(QUOTED_RE.sub(" ", line)) for line in text.split("\n")):
        reasons.append("tiếng Nhật xen giữa câu tiếng Việt")
    if re.search(r"không tồn tại|không có nghĩa", text, re.I):
        reasons.append("có lựa chọn không tồn tại/không có nghĩa")
    if re.search(r"Thể từ điển", text) or re.search(r'"kanji_jishokei"\s*:\s*"[^"]+"', g):
        reasons.append("có thể từ điển")
    return len(reasons), reasons


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="ghi đè bộ mẫu đã có")
    args = ap.parse_args()

    cfg = load_config()
    out_csv = p("samples", "samples.csv")
    if os.path.exists(out_csv) and not args.force:
        sys.exit("Đã có samples/samples.csv. Dùng --force nếu muốn chọn lại (bộ mẫu cũ sẽ bị ghi đè).")

    rng = random.Random(cfg["seed"])
    types = cfg["dang_bai"]
    pool = {d: {lv: [] for lv in cfg["levels"]} for d in types}

    with open(p(cfg["source_csv"]), encoding="utf-8-sig") as f:
        for row in csv.DictReader(line.replace("\0", "") for line in f):  # bỏ ký tự NUL lẫn trong CSV
            d = row["dang_bai"].strip()
            if d in pool and row["giai_thich_vi"].strip() and row["cap_do"] in pool[d]:
                pool[d][row["cap_do"]].append(row)

    selected = []
    for d, levels in pool.items():
        n_need = cfg["samples_per_type"]
        chosen = []
        # 1 câu mỗi cấp độ, ưu tiên câu khó; nếu thiếu cấp độ thì bù từ cấp khác
        # cấp độ ở vị trí chẵn (N1, N3, N5) ưu tiên câu khó; cấp độ lẻ (N2, N4) chọn ngẫu nhiên
        for i, lv in enumerate(cfg["levels"]):
            cands = levels[lv][:]
            rng.shuffle(cands)
            if i % 2 == 0:
                cands.sort(key=lambda r: -difficulty(r)[0])
            if cands and len(chosen) < n_need:
                chosen.append(cands[0])
        leftovers = [r for lv in cfg["levels"] for r in levels[lv] if r not in chosen]
        rng.shuffle(leftovers)
        chosen += leftovers[: n_need - len(chosen)]
        for r in chosen:
            selected.append((d, r))

    os.makedirs(p("samples", "raw"), exist_ok=True)
    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sample_id", "dang_bai", "schema", "question_id", "cau_con", "cap_do", "dap_an_so", "ly_do_chon"])
        for d, r in selected:
            info = types[d]
            sid = f"{info['code']}_{r['question_id']}_{r['cau_con']}"
            _, reasons = difficulty(r)
            w.writerow([sid, d, info["schema"], r["question_id"], r["cau_con"], r["cap_do"], r["dap_an_so"],
                        "; ".join(reasons) or "câu thông thường"])
            save_json({k: r.get(k, "") for k in RAW_FIELDS} | {"sample_id": sid, "schema": info["schema"]},
                      p("samples", "raw", sid + ".json"))
    print(f"Đã chọn {len(selected)} mẫu → samples/samples.csv và samples/raw/")


if __name__ == "__main__":
    main()
