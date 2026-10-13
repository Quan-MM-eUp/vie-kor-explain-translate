"""Giai đoạn 0 – Chuẩn bị (Python, không sửa nội dung) – dạng 11 Đọc hiểu: Đoạn văn trung bình.

- Chuẩn hóa lời giải gốc (HTML): ruby → ｜…《…》; in đậm / gạch chân → { } (WF chung mục 3a); bỏ { } quanh nhãn đứng riêng dòng ({Đoạn văn:});
  bỏ furigana gắn lên chữ Việt; giữ xuống dòng
- dau_vao (đưa tác tử TẠO) = lời giải đã chuẩn hóa; src_text (chuẩn kiểm tra) = dau_vao bỏ nhãn tiếng Nhật đầu dòng (引用: / 解説: …)
- Đoạn văn chuẩn hóa (giữ ①②③, { }) lưu trong norm['doan_van'] – xem_gd1 in một lần mỗi đoạn; GĐ2 dùng làm ngữ cảnh dịch
- Tách lời giải (câu hỏi + dịch / 4 lựa chọn: Nghĩa, câu trích 「…」, nhận xét, → ĐÚNG|SAI), phân loại khuôn, gắn cờ gợi ý + ghi chú [Bản gốc VI]
- Dò câu trích trong đoạn văn (khop / mot_phan / khong) → output/reports/trich_dan.csv
- Tạo output/thu_tu_chay.csv (một lần) theo ĐOẠN VĂN: 35 đoạn đầu = 7 đoạn mỗi cấp xen kẽ; cột 'lo' = lô 3–4 đoạn ≈ 9–12 câu
  → output/lo_chay.csv (lô, từ stt, đến stt, số câu, các đoạn)
- Tạo/cập nhật output/reports/trang_thai.csv; phát hiện câu có dữ liệu gốc thay đổi (so hash)
- Báo cáo: khuon.csv, co_ban_goc.csv, ruby_hong_ban_goc.csv, doc_trong_ngoac.csv, danh_dau_rac.csv

Cách chạy (từ thư mục dạng bài):
  python scripts/s0_chuan_bi.py                    # chuẩn hóa toàn bộ 1151 câu (giữ thứ tự chạy cũ nếu đã có)
  python scripts/s0_chuan_bi.py --tao-lai-thu-tu   # tạo lại thứ tự chạy (chỉ khi chưa chạy lô nào)
"""
import argparse
import collections
import os

import _dang as D
from pipeline_chung.common import read_csv, save_json, sha, write_csv
from pipeline_chung.normalize import has_reserved_marks, mark_segments, normalize_html, paren_readings, pairs
from pipeline_chung.trang_thai import Status


def prepare(row):
    sid = D.sid_of(row)
    g = (row.get("giai_thich_vi") or "").strip()
    lua_chon = [D.plain(row.get(f"lua_chon_{i}", ""))[0] for i in range(1, 5)]
    cau_hoi, b0 = D.plain(row.get("cau_hoi", ""))
    dap = row["dap_an_so"].strip()
    rec = {"sample_id": sid, "question_id": int(row["question_id"]), "cau_con": int(row["cau_con"]), "cap_do": row["cap_do"],
           "hash_goc": sha(g + "|" + row.get("cau_hoi", "") + "|" + "|".join(lua_chon) + "|" + dap + "|" + sha(row.get("doan_van", ""))),
           "de": {"cau_hoi": cau_hoi, "lua_chon": lua_chon, "dap_an_so": int(dap) if dap.isdigit() else dap,
                  "dap_an_noi_dung": D.plain(row.get("dap_an_noi_dung", ""))[0], "de_bai_chung": D.plain(row.get("de_bai_chung", ""))[0]},
           "doan_van": D.chuan_doan_van(row.get("doan_van", "")),
           "co": [], "ghi_chu_ban_goc": [], "ruby_hong": list(b0), "danh_dau_rac": []}
    if not g:
        rec.update(khuon_goc="trong", dau_vao=None, src_text="", src_vi_text="", src_text_furi="", marks_src=[], phan=None)
        rec["ghi_chu_ban_goc"].append("[Bản gốc VI] Không có lời giải")
        return rec
    if has_reserved_marks(g):
        rec["co"].append("ky_hieu_trung")
    if dap not in ("1", "2", "3", "4"):
        rec["co"].append("dap_an_de_loi")
        rec["ghi_chu_ban_goc"].append(f"[Bản gốc VI] dap_an_so = '{dap}' không phải 1–4 – báo nhóm dữ liệu")
    rac = []
    text, broken = normalize_html(g, "u+b", rac)
    text, furi_vi = D.bo_furigana_chu_viet(text)
    text, n_dam = D.bo_dam_nhan(text)
    phan, co, gc = D.parse_and_flag(text, lua_chon, dap, cau_hoi, rec["doan_van"], row.get("doan_van", ""))
    src = D.bo_nhan_nhat(text)        # chuẩn kiểm tra: bỏ nhãn tiếng Nhật đầu dòng (引用: …) – tác tử TẠO không chép nhãn
    rec.update(khuon_goc="chuan" if phan["so_lua_chon"] == 4 else "la", dau_vao=text, src_text=src, src_vi_text=src,
               src_text_furi=src, marks_src=mark_segments(src), phan=phan, danh_dau_rac=rac)
    rec["co"] += co
    rec["ghi_chu_ban_goc"] += gc
    if n_dam:
        rec["co"].append("nhan_in_dam")
    if furi_vi:
        rec["co"].append("furigana_chu_viet")
        rec["ghi_chu_ban_goc"].append("[Python sửa định dạng] Bỏ furigana gắn lên chữ tiếng Việt: "
                                      + ", ".join(f"'{a}' → '{b}'" for a, b in furi_vi))
    rec["ruby_hong"] += broken
    if rac:
        rec["co"].append("danh_dau_rac")
    if pairs(text):
        rec["co"].append("co_furigana")
    if rec["ruby_hong"]:
        rec["co"].append("ruby_hong")
        rec["ghi_chu_ban_goc"].append(f"[Bản gốc VI] Có {len(rec['ruby_hong'])} thẻ ruby hỏng")
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
        rec = prepare(row)
        recs.append(rec)
        save_json(rec, D.OUT("samples", "norm", rec["sample_id"] + ".json"))
        old = st.get(rec["sample_id"])
        if old and old.get("hash_goc") and old["hash_goc"] != rec["hash_goc"]:
            changed.append(rec["sample_id"])
            st.update(rec["sample_id"], trang_thai="ĐANG_XỬ_LÝ", giai_doan_loi="",
                      loi="Dữ liệu gốc đã thay đổi – cần chạy lại từ giai đoạn 1")
        if not old or rec["sample_id"] in changed:
            st.update(rec["sample_id"], trang_thai="ĐANG_XỬ_LÝ" if rec["khuon_goc"] != "trong" else "LỖI_GĐ1",
                      giai_doan_loi="" if rec["khuon_goc"] != "trong" else "1",
                      loi="" if rec["khuon_goc"] != "trong" else "Không có lời giải gốc")
        st.update(rec["sample_id"], question_id=rec["question_id"], cau_con=rec["cau_con"], cap_do=rec["cap_do"],
                  khuon_goc=rec["khuon_goc"], co=" ".join(rec["co"]), hash_goc=rec["hash_goc"],
                  ghi_chu_ban_goc=rec["ghi_chu_ban_goc"])
    n_dd, _ = D.danh_dau_da_duyet(st, {r["sample_id"]: r["hash_goc"] for r in recs})
    st.save()

    write_csv([{"sample_id": r["sample_id"], "ruby": x} for r in recs for x in r["ruby_hong"]],
              D.OUT("reports", "ruby_hong_ban_goc.csv"), ["sample_id", "ruby"])
    write_csv([{"sample_id": r["sample_id"], "doan": x} for r in recs for x in r.get("doc_trong_ngoac", [])],
              D.OUT("reports", "doc_trong_ngoac.csv"), ["sample_id", "doan"])
    write_csv([{"sample_id": r["sample_id"], "doan_bi_bo_the": x} for r in recs for x in r["danh_dau_rac"]],
              D.OUT("reports", "danh_dau_rac.csv"), ["sample_id", "doan_bi_bo_the"])
    write_csv([{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "lua_chon": x["so"], "ket_qua": x["ket_qua"], "trich": x["trich"]}
               for r in recs for x in (r.get("phan") or {}).get("trich_dan", [])],
              D.OUT("reports", "trich_dan.csv"), ["sample_id", "cap_do", "lua_chon", "ket_qua", "trich"])
    write_csv([{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "khuon": r["khuon_goc"],
                "chi_tiet": " ".join(c for c in r["co"] if c.startswith("khuon_")),
                "so_lua_chon_tach_duoc": (r.get("phan") or {}).get("so_lua_chon", 0)} for r in recs],
              D.OUT("reports", "khuon.csv"))
    write_csv([{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "co": " ".join(r["co"]),
                "ghi_chu_ban_goc": "\n".join(r["ghi_chu_ban_goc"])} for r in recs if r["co"] or r["ghi_chu_ban_goc"]],
              D.OUT("reports", "co_ban_goc.csv"))

    co = collections.Counter(c for r in recs for c in r["co"])
    print(f"Đã chuẩn hóa {len(recs)} câu ({len({r['question_id'] for r in recs})} đoạn văn) → {D.OUT('samples', 'norm')}")
    print("Khuôn lời giải:", dict(collections.Counter(r["khuon_goc"] for r in recs)))
    print("Câu trích ↔ đoạn văn (output/reports/trich_dan.csv):",
          dict(collections.Counter(x["ket_qua"] for r in recs for x in (r.get("phan") or {}).get("trich_dan", []))))
    print(f"  có đánh dấu {{ }} trong lời giải: {sum(bool(r['marks_src']) for r in recs)} câu")
    for c, n in co.most_common():
        print(f"  cờ {c:24} {n:5}  – {D.FLAG_TEXT.get(c, '')}")
    kho = D.da_duyet_rows()
    print(f"Kho đã duyệt: {len(kho)} câu" + (f" – đánh dấu ĐÃ_DUYỆT_CTV: {n_dd}" if n_dd else ""))
    if changed:
        print(f"CHÚ Ý: {len(changed)} câu có dữ liệu gốc thay đổi so với lần chạy trước → đặt lại ĐANG_XỬ_LÝ")
    if args.tao_lai_thu_tu or not os.path.exists(D.OUT("thu_tu_chay.csv")):
        tt = D.tao_thu_tu_doan(recs, cfg)
        write_csv(tt, D.OUT("thu_tu_chay.csv"))
        lo = collections.OrderedDict()
        for x in tt:
            g_ = lo.setdefault(x["lo"], {"lo": x["lo"], "tu": x["stt"], "den": x["stt"], "so_cau": 0, "doan": []})
            g_["den"], g_["so_cau"] = x["stt"], g_["so_cau"] + 1
            if x["question_id"] not in g_["doan"]:
                g_["doan"].append(x["question_id"])
        write_csv([{**g_, "doan": " ".join(str(q) for q in g_["doan"])} for g_ in lo.values()], D.OUT("lo_chay.csv"))
        print(f"Đã tạo thứ tự chạy → {D.OUT('thu_tu_chay.csv')} (100 câu đầu: {dict(collections.Counter(x['cap_do'] for x in tt[:100]))}); "
              f"{len(lo)} lô → {D.OUT('lo_chay.csv')} (số câu mỗi lô: {dict(sorted(collections.Counter(g_['so_cau'] for g_ in lo.values()).items()))})")


if __name__ == "__main__":
    main()
