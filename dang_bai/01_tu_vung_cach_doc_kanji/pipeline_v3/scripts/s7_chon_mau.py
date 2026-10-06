"""Chọn mẫu thử theo cấp độ (không gọi API, không sửa dữ liệu) – bước 1–2 của kế hoạch "mỗi cấp độ 5 câu Dạng 1".

1. Lấy ứng viên: mỗi cấp độ xáo ngẫu nhiên (seed cố định → chạy lại ra cùng kết quả), chỉ lấy câu ĐANG_XỬ_LÝ
   (chưa chạy), mỗi câu đề (cùng câu tiếng Nhật) chỉ lấy 1 câu, bỏ câu đề đã có câu con được chạy trước đó.
2. Lọc tự động – loại câu nhiều khả năng KHÔNG thành Dạng 1:
   H  lời giải có "âm hán việt" / "hán việt"            → sẽ thành Dạng 3 (D5)
   C  có cờ s0: nghi_don_phan_tich, thieu_gach_chan, lech_dap_an; hoặc có ghi chú bản gốc tự động / ruby hỏng
   R  cách đọc câu không khớp câu đề (so với cách đọc tự sinh bằng pykakasi < 75% → loại, 75–90% → ghi cần xem; hoặc đầu dòng thừa いち/に/さん…)
      → dấu hiệu lẫn số ①②③, thiếu / thừa đoạn
   K  cách đọc của từ (kanji_reading) khác đáp án đúng
   Câu qua lọc được giữ tới đủ --giu câu mỗi cấp (để Claude đọc tiếp ở bước 3).

Cách chạy:  python scripts/s7_chon_mau.py --giu 12 --seed 2026
Kết quả:    output/reports/chon_mau/ung_vien.csv (mọi câu đã xét + lý do loại), qua_loc.csv, tong_hop.md
"""
import argparse
import collections
import difflib
import os
import random
import re

import _dang as D
from pipeline_chung.common import load_json, read_csv, write_csv
from pipeline_chung.trang_thai import Status

LEVELS = ["N5", "N4", "N3", "N2", "N1"]
BAD_FLAGS = {"nghi_don_phan_tich", "thieu_gach_chan", "lech_dap_an"}
HV_RE = re.compile(r"h[aá]n\s*vi[eệ]t", re.I)
NUM_HEAD = re.compile(r"^(いち|いっ|に|さん|よん|し)")
STRIP = re.compile(r"[{}\s①-⑳（）()「」『』、。・…!?！？]")


def kana(s):
    import pykakasi
    if not hasattr(kana, "k"):
        kana.k = pykakasi.kakasi()
    return "".join(x["hira"] for x in kana.k.convert(s))


def hira(s):
    """katakana → hiragana, số / chữ Latinh → cách đọc pykakasi (để so được cả câu có katakana, số)."""
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)


def reading_ratio(text, reading):
    a, b = STRIP.sub("", hira(kana(text))), STRIP.sub("", hira(kana(reading)))
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio(), a, b


def check(n, thr):
    why, nghi = [], []
    if HV_RE.search(n.get("src_text") or ""):
        why.append("H: có âm Hán Việt")
    bad = BAD_FLAGS & set(n.get("co") or [])
    if bad:
        why.append(f"C: cờ {sorted(bad)}")
    if n.get("ghi_chu_ban_goc"):
        why.append("C: có ghi chú bản gốc tự động")
    if n.get("ruby_hong"):
        why.append("C: furigana hỏng")
    dv = n.get("dau_vao")
    ratio = None
    if isinstance(dv, dict):
        q = dv.get("question") or {}
        text, rd = q.get("text") or "", q.get("reading") or ""
        if rd.strip():
            ratio, a, b = reading_ratio(text, rd)
            if ratio < thr:
                why.append(f"R: cách đọc câu khớp {ratio:.0%}")
            elif ratio < 0.9:
                nghi.append(f"cách đọc câu khớp {ratio:.0%} – Claude xem kỹ (pykakasi hay đọc sai câu ngắn, số, 日本…)")
            elif NUM_HEAD.match(b) and not a.startswith(b[:2]):
                why.append("R: đầu cách đọc thừa số (いち/に/さん…)")
        kr = (q.get("kanji_reading") or "").split("\n")[0].strip()
        if kr and kr != (n["de"].get("dap_an_noi_dung") or "").strip():
            why.append(f"K: cách đọc từ '{kr}' ≠ đáp án '{n['de'].get('dap_an_noi_dung')}'")
    return why, ratio, nghi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--giu", type=int, default=12, help="số câu qua lọc giữ lại mỗi cấp độ")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--nguong", type=float, default=0.75, help="ngưỡng khớp cách đọc câu (dưới ngưỡng → loại; 0.75–0.9 → ghi 'can_xem')")
    args = ap.parse_args()
    st = Status(D.status_path())
    rows = read_csv(D.data_path())
    by_lv = collections.defaultdict(list)
    da_chay = set()          # câu đề của các câu đã chạy → không lấy câu con khác cùng câu đề
    for i, r in enumerate(rows, 1):
        sid = D.sid_of(r)
        if st.get(sid).get("trang_thai") in ("ĐANG_XỬ_LÝ", ""):
            by_lv[r["cap_do"]].append((i, sid))
        else:
            da_chay.add(re.sub(r"[{}①-⑳\s]", "", D.load_norm(sid)["de"]["cau_hoi"]))
    out, keep, md = [], [], ["# Chọn mẫu thử theo cấp độ", "", f"seed={args.seed}, ngưỡng cách đọc={args.nguong:.0%}, giữ {args.giu} câu/cấp", "",
                             "| Cấp | Đã xét | Loại H | Loại C | Loại R | Loại K | Qua lọc |", "|---|---|---|---|---|---|---|"]
    for lv in LEVELS:
        pool = by_lv[lv][:]
        random.Random(f"{args.seed}-{lv}").shuffle(pool)
        seen, kept, cnt, xet = set(da_chay), 0, collections.Counter(), 0
        for stt, sid in pool:
            if kept >= args.giu:
                break
            n = D.load_norm(sid)
            sent = re.sub(r"[{}①-⑳\s]", "", n["de"]["cau_hoi"])
            if sent in seen:
                continue
            seen.add(sent)
            xet += 1
            why, ratio, nghi = check(n, args.nguong)
            for w in why:
                cnt[w[0]] += 1
            ok = not why
            kept += ok
            row = {"cap_do": lv, "stt_mau": stt, "sample_id": sid, "question_id": n["question_id"], "qua_loc": "x" if ok else "",
                   "ly_do_loai": "; ".join(why), "can_xem": "; ".join(nghi), "khop_cach_doc": f"{ratio:.2f}" if ratio is not None else "", "cau_hoi": n["de"]["cau_hoi"]}
            out.append(row)
            if ok:
                keep.append(row)
        md.append(f"| {lv} | {xet} | {cnt['H']} | {cnt['C']} | {cnt['R']} | {cnt['K']} | {kept} |")
    d = D.OUT("reports", "chon_mau")
    f = ["cap_do", "stt_mau", "sample_id", "question_id", "qua_loc", "ly_do_loai", "can_xem", "khop_cach_doc", "cau_hoi"]
    write_csv(out, os.path.join(d, "ung_vien.csv"), f)
    write_csv(keep, os.path.join(d, "qua_loc.csv"), f)
    md += ["", "(một câu có thể bị loại vì nhiều lý do)", "", "Qua lọc: " + ", ".join(f"{lv}: {sum(1 for x in keep if x['cap_do'] == lv)}" for lv in LEVELS)]
    with open(os.path.join(d, "tong_hop.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(md) + "\n")
    print("\n".join(md))
    print(f"→ {d}: ung_vien.csv, qua_loc.csv, tong_hop.md")


if __name__ == "__main__":
    main()
