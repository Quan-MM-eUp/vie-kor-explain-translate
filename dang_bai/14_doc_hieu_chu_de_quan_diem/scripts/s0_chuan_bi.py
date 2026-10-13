"""Giai đoạn 0 – Chuẩn bị (Python, không sửa nội dung) – dạng 14 Đọc hiểu chủ đề / quan điểm (đoạn văn dài).

- Đoạn văn: bóc khung <table> / thẻ Word, ruby → ｜…《…》, gạch chân / in đậm → { } (giữ ①②, 注…) → norm['doan_van']
- Lời giải: bỏ nhãn in đậm của khuôn lạ (<strong>Đoạn văn:</strong>), chuẩn hóa (ruby → ｜…《…》, in đậm / gạch chân → { }), giữ xuống dòng
- Tách lời giải (scripts/_doc_hieu_14.py): khuôn chuẩn kiểu A / B (4 lựa chọn: Nghĩa / trích dẫn / nhận xét / → ĐÚNG|SAI) hoặc khuôn lạ
  (la_dich_doan / la_chi_dap_an / la_ngan → TẠO MỚI, bắt buộc CTV tiếng Nhật duyệt)
- Gắn cờ gợi ý + ghi chú [Bản gốc VI]; phân loại câu hỏi (hoi_*); so trích dẫn với đoạn văn (so mờ)
- Tạo output/thu_tu_chay.csv + output/lo_chay.csv (một lần): theo ĐOẠN VĂN – 3 đoạn pilot, rồi khuôn chuẩn N1/N2 xen kẽ, khuôn lạ cuối
- Tạo/cập nhật output/reports/trang_thai.csv; phát hiện câu có dữ liệu gốc thay đổi (so hash)
- Báo cáo: output/reports/khao_sat_s0.csv, trich_dan.csv, co_ban_goc.csv, ruby_hong_ban_goc.csv

Cách chạy (từ thư mục dạng bài):
  python scripts/s0_chuan_bi.py                     # chuẩn hóa toàn bộ 265 câu
  python scripts/s0_chuan_bi.py --tao-lai-thu-tu    # tạo lại thứ tự chạy (CHỈ khi chưa chạy lô nào)
"""
import argparse
import collections
import os
import re

import _dang as D
from pipeline_chung.common import read_csv, save_json, sha, write_csv
from pipeline_chung.normalize import has_reserved_marks, mark_segments, normalize_html, pairs
from pipeline_chung.trang_thai import Status

DH = D.DH


def plain(html):
    """Chuẩn hóa và bỏ { } (đề / lựa chọn)."""
    t, b = normalize_html(DH.bo_khung(html or ""))
    return t.replace("{", "").replace("}", ""), b


def prepare(row, bo_lap=True):
    sid = D.sid_of(row)
    g = (row.get("giai_thich_vi") or "").strip()
    lua_chon = [plain(row.get(f"lua_chon_{i}", ""))[0] for i in range(1, 5)]
    cau_hoi, b0 = plain(row.get("cau_hoi", ""))
    doan_van, b_dv = DH.lam_sach_doan_van(row.get("doan_van", ""))
    rec = {"sample_id": sid, "question_id": int(row["question_id"]), "cau_con": int(row["cau_con"]), "cap_do": row["cap_do"],
           "hash_goc": sha(g + "|" + row.get("cau_hoi", "") + "|" + "|".join(lua_chon) + "|" + row["dap_an_so"] + "|" + sha(row.get("doan_van", ""))),
           "de": {"cau_hoi": cau_hoi, "lua_chon": lua_chon,
                  "dap_an_so": int(row["dap_an_so"]) if row["dap_an_so"].isdigit() else row["dap_an_so"],
                  "dap_an_noi_dung": plain(row.get("dap_an_noi_dung", ""))[0], "de_bai_chung": plain(row.get("de_bai_chung", ""))[0]},
           "doan_van": doan_van, "loai_cau_hoi": DH.loai_cau_hoi(cau_hoi),
           "co": [], "ghi_chu_ban_goc": [], "ruby_hong": list(b0), "danh_dau_rac": []}
    if re.search(r"<table|mso-|lang=", row.get("doan_van", ""), re.I):
        rec["co"].append("doan_khung_html")
    if not g:
        rec.update(khuon_goc="trong", dau_vao=None, src_text="", src_vi_text="", src_text_furi="", marks_src=[], phan=None)
        rec["ghi_chu_ban_goc"].append("[Bản gốc VI] Không có lời giải")
        return rec
    if has_reserved_marks(g):
        rec["co"].append("ky_hieu_trung")
    rac = []
    text, broken = normalize_html(DH.bo_dam_nhan(g), "u+b", rac)
    text, furi_vi = D.bo_furigana_chu_viet(text)
    text, dong_bo = DH.bo_dong_lap(text) if bo_lap else (text, [])   # chỉ câu chưa qua GĐ1 (2026-10-10 lô 20)
    phan, co, gc = D.parse_and_flag(text, lua_chon, row["dap_an_so"], cau_hoi, doan_van)
    so = DH.bo_nhan_tieng_nhat(text)
    rec.update(khuon_goc=phan["khuon"], dau_vao=text, src_text=so, src_vi_text=text, src_text_furi=so,
               marks_src=mark_segments(text), phan=phan, danh_dau_rac=rac)
    rec["co"] += co + ["hoi_" + rec["loai_cau_hoi"]]
    rec["ghi_chu_ban_goc"] += gc
    if furi_vi:
        rec["co"].append("furigana_chu_viet")
        rec["ghi_chu_ban_goc"].append("[Python sửa định dạng] Bỏ furigana gắn lên chữ tiếng Việt: " + ", ".join(f"'{a}' → '{b}'" for a, b in furi_vi))
    if dong_bo:
        rec["co"].append("dong_lap")
        rec["ghi_chu_ban_goc"].append("[Python sửa định dạng] Bỏ dòng dán lặp: " + " ⏎ ".join(f"'{x[:40]}…'" for x in dong_bo))
    rec["ruby_hong"] += broken
    if pairs(text):
        rec["co"].append("co_furigana")
    if rec["ruby_hong"]:
        rec["co"].append("ruby_hong")
        rec["ghi_chu_ban_goc"].append(f"[Bản gốc VI] Có {len(rec['ruby_hong'])} thẻ ruby hỏng")
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
        _o = st.get(D.sid_of(row))
        rec = prepare(row, bo_lap=not _o or _o.get("trang_thai") in ("ĐANG_XỬ_LÝ", "LỖI_GĐ1"))
        recs.append(rec)
        save_json(rec, D.OUT("samples", "norm", rec["sample_id"] + ".json"))
        old = st.get(rec["sample_id"])
        if old and old.get("hash_goc") and old["hash_goc"] != rec["hash_goc"]:
            changed.append(rec["sample_id"])
            st.update(rec["sample_id"], trang_thai="ĐANG_XỬ_LÝ", giai_doan_loi="", loi="Dữ liệu gốc đã thay đổi – cần chạy lại từ giai đoạn 1")
        if not old or rec["sample_id"] in changed:
            st.update(rec["sample_id"], trang_thai="ĐANG_XỬ_LÝ" if rec["khuon_goc"] != "trong" else "LỖI_GĐ1",
                      giai_doan_loi="" if rec["khuon_goc"] != "trong" else "1",
                      loi="" if rec["khuon_goc"] != "trong" else "Không có lời giải gốc")
        st.update(rec["sample_id"], question_id=rec["question_id"], cau_con=rec["cau_con"], cap_do=rec["cap_do"],
                  khuon_goc=rec["khuon_goc"], co=" ".join(rec["co"]), hash_goc=rec["hash_goc"], ghi_chu_ban_goc=rec["ghi_chu_ban_goc"])
    n_dd, _ = D.danh_dau_da_duyet(st, {r["sample_id"]: r["hash_goc"] for r in recs})
    st.save()

    ks, td = [], []
    for r in recs:
        ph = r["phan"] or {}
        tr = [(b["so"], q) for b in ph.get("lua_chon") or [] for q in b["trich"]]
        ks.append({"sample_id": r["sample_id"], "question_id": r["question_id"], "cau_con": r["cau_con"], "cap_do": r["cap_do"],
                   "khuon": r["khuon_goc"], "loai_cau_hoi": r["loai_cau_hoi"], "so_trich_dan": len(tr),
                   "trich_ngoai_doan": sum(q.get("so_doan_van") == "khong" for _, q in tr),
                   "do_dai_loi_giai": len(r["dau_vao"] or ""), "co": " ".join(r["co"])})
        td += [{"sample_id": r["sample_id"], "lua_chon": so, "ket_qua": q.get("so_doan_van"), "co_dich": "x" if q["vi"] else "",
                "trich_dan": q["ja"][:200]} for so, q in tr]
    write_csv(ks, D.OUT("reports", "khao_sat_s0.csv"))
    write_csv(td, D.OUT("reports", "trich_dan.csv"), ["sample_id", "lua_chon", "ket_qua", "co_dich", "trich_dan"])
    write_csv([{"sample_id": r["sample_id"], "ruby": x} for r in recs for x in r["ruby_hong"]],
              D.OUT("reports", "ruby_hong_ban_goc.csv"), ["sample_id", "ruby"])
    write_csv([{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "co": " ".join(r["co"]),
                "ghi_chu_ban_goc": "\n".join(r["ghi_chu_ban_goc"])} for r in recs if r["co"] or r["ghi_chu_ban_goc"]],
              D.OUT("reports", "co_ban_goc.csv"))

    print(f"Đã chuẩn hóa {len(recs)} câu ({len({r['question_id'] for r in recs})} đoạn văn) → {D.OUT('samples', 'norm')}")
    print("Khuôn lời giải:", dict(collections.Counter(r["khuon_goc"] for r in recs)))
    print("Loại câu hỏi:", dict(collections.Counter(r["loai_cau_hoi"] for r in recs)))
    print("Trích dẫn ↔ đoạn văn (output/reports/trich_dan.csv):", dict(collections.Counter(x["ket_qua"] for x in td)))
    co = collections.Counter(c for r in recs for c in r["co"])
    for c, n in co.most_common():
        print(f"  cờ {c:26} {n:5}  – {D.FLAG_TEXT.get(c, '')}")
    kho = D.da_duyet_rows()
    print(f"Kho đã duyệt: {len(kho)} câu" + (f" – đánh dấu ĐÃ_DUYỆT_CTV: {n_dd}" if n_dd else ""))
    if changed:
        print(f"CHÚ Ý: {len(changed)} câu có dữ liệu gốc thay đổi so với lần chạy trước → đặt lại ĐANG_XỬ_LÝ")
    if args.tao_lai_thu_tu or not os.path.exists(D.OUT("thu_tu_chay.csv")):
        tt, lo = D.tao_thu_tu_doan(recs, cfg)
        write_csv(tt, D.OUT("thu_tu_chay.csv"))
        write_csv(lo, D.OUT("lo_chay.csv"))
        print(f"Đã tạo thứ tự chạy → output/thu_tu_chay.csv ({len(tt)} câu) và output/lo_chay.csv ({len(lo)} lô, 3 đoạn/lô)")
        for x in lo[:3]:
            print(f"  lô {x['lo']}: stt {x['tu']}–{x['den']} ({x['so_cau']} câu; đoạn {x['doan']}; {x['cap_do']}) {x['ghi_chu']}")


if __name__ == "__main__":
    main()
