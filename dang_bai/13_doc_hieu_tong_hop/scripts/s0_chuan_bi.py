"""Giai đoạn 0 – Chuẩn bị (Python, không sửa nội dung) – dạng 13 Đọc hiểu tổng hợp.

- Chuẩn hóa lời giải gốc: ruby → ｜…《…》; in đậm / gạch chân → { } (WF chung mục 3a); bỏ { } quanh nhãn in đậm của lời giải
  khuôn lạ ({Đoạn văn:} / {A}); ruby ghi kiểu lạ '<|貧;まず|しい' → '｜貧《まず》しい'; bỏ furigana gắn lên chữ Việt.
- Đoạn văn: chuẩn hóa, TÁCH THEO NHÃN A / B / C / 相談者 (回答者Ａ/Ｂ) → norm['doan_tach'], norm['doan_van'] (bản hiển thị 【A】…).
- Tách lời giải (câu hỏi + dịch → 4 lựa chọn: Nghĩa / nhận xét / câu trích 「…」 (dịch) / → ĐÚNG|SAI), phân loại khuôn
  (chuan / dich_doan_van / chi_dap_an / goi_y / khac), gắn cờ + ghi chú [Bản gốc VI] tự động:
  câu hỏi / lựa chọn lệch đề, ≠ 1 lựa chọn ĐÚNG, ĐÚNG lệch đáp án, câu trích không có trong đoạn văn (K-TD),
  câu trích lời giải gán cho đoạn A nhưng nằm ở đoạn B (K-NGUON), từ Nhật chen trong câu Việt, đoạn không có A/B…
- Tạo output/thu_tu_chay.csv (một lần) theo ĐOẠN VĂN, cột 'lo' = số lô (lô 1 = pilot 4 đoạn; đoạn khuôn lạ ở lô cuối).
- Tạo/cập nhật output/reports/trang_thai.csv; phát hiện câu có dữ liệu gốc thay đổi (so hash).
- Báo cáo: khao_sat_s0.csv (khuôn + cờ từng câu), doan_van_tach.csv, trich_dan.csv, ruby_hong_ban_goc.csv, co_ban_goc.csv.

Cách chạy (từ thư mục dạng bài):
  python scripts/s0_chuan_bi.py                    # chuẩn hóa toàn bộ 149 câu
  python scripts/s0_chuan_bi.py --tao-lai-thu-tu   # tạo lại thứ tự chạy (mặc định giữ file cũ)
"""
import argparse
import collections
import os
import re

import _dang as D
from pipeline_chung.common import read_csv, save_json, sha, write_csv
from pipeline_chung.normalize import has_reserved_marks, mark_segments, normalize_html, pairs, paren_readings
from pipeline_chung.trang_thai import Status

DH = D.DH


def plain(html):
    t, b = normalize_html(html or "")
    return t.replace("{", "").replace("}", ""), b


def prepare(row):
    sid = D.sid_of(row)
    g = (row.get("giai_thich_vi") or "").strip()
    lua_chon = [plain(row.get(f"lua_chon_{i}", ""))[0] for i in range(1, 5)]
    cau_hoi, b0 = plain(row.get("cau_hoi", ""))
    doan_van, b_dv = normalize_html(row.get("doan_van") or "")
    segs = DH.tach_doan_van(doan_van)
    dap = int(row["dap_an_so"]) if row["dap_an_so"].strip().isdigit() else row["dap_an_so"]
    rec = {"sample_id": sid, "question_id": int(row["question_id"]), "cau_con": int(row["cau_con"]), "cap_do": row["cap_do"],
           "hash_goc": sha(g + "|" + row.get("cau_hoi", "") + "|" + "|".join(lua_chon) + "|" + row["dap_an_so"] + "|" + sha(row.get("doan_van", ""))),
           "de": {"cau_hoi": cau_hoi, "lua_chon": lua_chon, "dap_an_so": dap, "dap_an_noi_dung": plain(row.get("dap_an_noi_dung", ""))[0],
                  "de_bai_chung": plain(row.get("de_bai_chung", ""))[0]},
           "doan_tach": [list(x) for x in segs], "doan_van": DH.dinh_dang_doan_van(segs),
           "co": [], "ghi_chu_ban_goc": [], "ruby_hong": list(b0), "danh_dau_rac": []}
    if not g:
        rec.update(khuon_goc="trong", khuon="trong", dau_vao=None, src_text="", src_vi_text="", src_text_furi="", marks_src=[], phan=None)
        rec["ghi_chu_ban_goc"].append("[Bản gốc VI] Không có lời giải")
        return rec
    if has_reserved_marks(g):
        rec["co"].append("ky_hieu_trung")
    rac = []
    text, broken = normalize_html(g, "u+b", rac)
    text, n_dam = D.bo_dam_nhan(text)
    text, ruby_la = D.sua_ruby_la(text)
    text, furi_vi = D.bo_furigana_chu_viet(text)
    ph = DH.phan_tich_loi_giai(text, segs)
    co, gc = DH.gan_co(ph, rec["de"], segs)
    rec.update(khuon_goc="chuan" if ph["khuon"] == "chuan" else "la", khuon=ph["khuon"], dau_vao=text, src_text=text, src_vi_text=text,
               src_text_furi=DH.bo_dong_lap(text, ph), marks_src=mark_segments(text), phan={**ph, "tham_khao": None}, danh_dau_rac=rac)
    rec["co"] += co
    rec["ghi_chu_ban_goc"] += gc
    for x in (ph.get("dau") or {}).get("lap") or []:
        rec["ghi_chu_ban_goc"].append(f"[Python sửa định dạng] Lời giải lặp dòng câu hỏi tiếng Nhật – bỏ khỏi phần dịch câu hỏi và khi so furigana: '{x[:60]}'")
    if n_dam:
        rec["ghi_chu_ban_goc"].append(f"[Python sửa định dạng] Bỏ {{ }} quanh {n_dam} nhãn in đậm (Đoạn văn: / A / Câu hỏi: …)")
    if ruby_la:
        rec["co"].append("ruby_hong")
        rec["ghi_chu_ban_goc"].append("[Python sửa định dạng] Ruby ghi kiểu lạ → furigana: " + ", ".join(f"'{a}' → '{b}'" for a, b in ruby_la))
    if furi_vi:
        rec["co"].append("furigana_chu_viet")
        rec["ghi_chu_ban_goc"].append("[Python sửa định dạng] Bỏ furigana gắn lên chữ tiếng Việt: " + ", ".join(f"'{a}' → '{b}'" for a, b in furi_vi))
    if DH.chen_tu_nhat(text):
        rec["co"].append("chen_tu_nhat")
    if len(segs) == 1 and segs[0][0] is None:
        rec["co"].append("doan_khong_ab")
    if re.search(r"<table", row.get("doan_van") or "", re.I):
        rec["co"].append("doan_co_bang")
    if re.search(r"<u\b|underline|font-weight", (row.get("cau_hoi") or "") + "".join(row.get(f"lua_chon_{i}") or "" for i in range(1, 5)), re.I):
        rec["co"].append("de_gach_chan")
    rec["ruby_hong"] += broken
    if rac:
        rec["co"].append("danh_dau_rac")
    if pairs(text):
        rec["co"].append("co_furigana")
    if rec["ruby_hong"]:
        rec["co"].append("ruby_hong")
        if broken or b0:
            rec["ghi_chu_ban_goc"].append(f"[Bản gốc VI] Có {len(broken) + len(b0)} thẻ ruby hỏng")
    rec["doc_trong_ngoac"] = paren_readings(text)
    rec["co"] = sorted(set(rec["co"]))
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tao-lai-thu-tu", action="store_true", help="tạo lại output/thu_tu_chay.csv (mặc định giữ file cũ)")
    args = ap.parse_args()
    cfg = D.cfg()
    rows = read_csv(D.data_path())
    st = Status(D.status_path())
    recs, changed = [], []
    for row in rows:
        recs.append(prepare(row))
    cung = collections.defaultdict(list)
    for r in recs:
        cung[r["question_id"]].append(r["sample_id"])
    for rec in recs:
        rec["cau_cung_doan"] = cung[rec["question_id"]]
        save_json(rec, D.OUT("samples", "norm", rec["sample_id"] + ".json"))
        old = st.get(rec["sample_id"])
        if old and old.get("hash_goc") and old["hash_goc"] != rec["hash_goc"]:
            changed.append(rec["sample_id"])
            st.update(rec["sample_id"], trang_thai="ĐANG_XỬ_LÝ", giai_doan_loi="", loi="Dữ liệu gốc đã thay đổi – cần chạy lại từ giai đoạn 1")
        if not old or rec["sample_id"] in changed:
            trong = rec["khuon_goc"] == "trong"
            st.update(rec["sample_id"], trang_thai="LỖI_GĐ1" if trong else "ĐANG_XỬ_LÝ", giai_doan_loi="1" if trong else "",
                      loi="Không có lời giải gốc" if trong else "")
        st.update(rec["sample_id"], question_id=rec["question_id"], cau_con=rec["cau_con"], cap_do=rec["cap_do"],
                  khuon_goc=rec["khuon"], co=" ".join(rec["co"]), hash_goc=rec["hash_goc"], ghi_chu_ban_goc=rec["ghi_chu_ban_goc"])
    n_dd, _ = D.danh_dau_da_duyet(st, {r["sample_id"]: r["hash_goc"] for r in recs})
    st.save()

    write_csv([{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "khuon": r["khuon"], "so_doan": len(r["doan_tach"]),
                "nhan_doan": " ".join(str(x[0]) for x in r["doan_tach"]), "co": " ".join(r["co"]),
                "ghi_chu_ban_goc": "\n".join(r["ghi_chu_ban_goc"])} for r in recs], D.OUT("reports", "khao_sat_s0.csv"))
    seen = set()
    write_csv([{"question_id": r["question_id"], "cap_do": r["cap_do"], "nhan": x[0] or "", "so_ky_tu": len(x[1]), "van_ban": x[1]}
               for r in recs if not (r["question_id"] in seen or seen.add(r["question_id"])) for x in r["doan_tach"]],
              D.OUT("reports", "doan_van_tach.csv"))
    write_csv([{"sample_id": r["sample_id"], "lua_chon": o["so"], "khoi": "x" if q["khoi"] else "", "nhan_neu": q["nhan_neu"] or "",
                "nhan_thay": q["nhan_thay"] or "", "muc": q["muc"], "ja": q["ja"], "nghia": q["nghia"] or ""}
               for r in recs for o in ((r["phan"] or {}).get("lua_chon") or []) for q in o["trich_dan"]], D.OUT("reports", "trich_dan.csv"))
    write_csv([{"sample_id": r["sample_id"], "ruby": x} for r in recs for x in r["ruby_hong"]],
              D.OUT("reports", "ruby_hong_ban_goc.csv"), ["sample_id", "ruby"])
    write_csv([{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "co": " ".join(r["co"]), "ghi_chu_ban_goc": "\n".join(r["ghi_chu_ban_goc"])}
               for r in recs if r["co"] or r["ghi_chu_ban_goc"]], D.OUT("reports", "co_ban_goc.csv"))

    print(f"Đã chuẩn hóa {len(recs)} câu ({len(cung)} đoạn văn) → {D.OUT('samples', 'norm')}")
    print("Khuôn lời giải:", dict(collections.Counter(r["khuon"] for r in recs)))
    print("Nhãn đoạn văn:", dict(collections.Counter(" ".join(str(x[0]) for x in r["doan_tach"]) for r in recs)))
    tq = collections.Counter(q["muc"] for r in recs for o in ((r["phan"] or {}).get("lua_chon") or []) for q in o["trich_dan"])
    print("Câu trích 「…」 so với đoạn văn (output/reports/trich_dan.csv):", dict(tq))
    for c, n in collections.Counter(c for r in recs for c in r["co"]).most_common():
        print(f"  cờ {c:24} {n:4}  – {D.FLAG_TEXT.get(c, '')}")
    kho = D.da_duyet_rows()
    print(f"Kho đã duyệt: {len(kho)} câu" + (f" – đánh dấu ĐÃ_DUYỆT_CTV: {n_dd}" if n_dd else ""))
    if changed:
        print(f"CHÚ Ý: {len(changed)} câu có dữ liệu gốc thay đổi so với lần chạy trước → đặt lại ĐANG_XỬ_LÝ")
    if args.tao_lai_thu_tu or not os.path.exists(D.OUT("thu_tu_chay.csv")):
        tt = D.tao_thu_tu_doan(recs, cfg)
        write_csv(tt, D.OUT("thu_tu_chay.csv"))
        print(f"Đã tạo thứ tự chạy → {D.OUT('thu_tu_chay.csv')}")
    tt = read_csv(D.OUT("thu_tu_chay.csv"))
    print("Các lô (stt từ–đến · số đoạn · số câu):")
    for lo, xs in sorted(collections.defaultdict(list, {k: [x for x in tt if x["lo"] == k] for k in {x["lo"] for x in tt}}).items(), key=lambda kv: int(kv[0])):
        print(f"  lô {lo:>2}: {xs[0]['stt']:>3}–{xs[-1]['stt']:<3} · {len({x['question_id'] for x in xs})} đoạn · {len(xs)} câu"
              f" · {', '.join(sorted({x['kieu_doan'] for x in xs}))}")


if __name__ == "__main__":
    main()
