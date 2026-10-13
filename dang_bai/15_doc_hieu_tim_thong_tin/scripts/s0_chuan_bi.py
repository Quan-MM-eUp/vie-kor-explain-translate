"""Giai đoạn 0 – Chuẩn bị (Python, không sửa nội dung) – dạng 15 Đọc hiểu: Tìm thông tin.

- Ngữ liệu (doan_van): TRẢI BẢNG → mỗi hàng '| ô | ô |', ảnh → [ẢNH: …], furigana ｜…《…》 (pipeline_chung/doc_hieu_chung.ngu_lieu)
  → norm['doan_van'] + output/reports/ngu_lieu.csv
- Lời giải: HTML → văn bản chuẩn hóa (ruby → ｜…《…》; in đậm / gạch chân → { }); bỏ ký hiệu markdown ** / #; bỏ furigana gắn lên chữ Việt
- Tách lời giải: câu hỏi (+ dịch) / phần đầu khác / 4 khối lựa chọn (Nghĩa, kết luận ĐÚNG–SAI, ứng viên trích dẫn); khuôn A / B / C
- Cờ gợi ý + ghi chú [Bản gốc VI]: khuôn lạ, lệch đáp án, trích dẫn không có trong ngữ liệu (trich_dan.csv), phép tính sai (tinh_toan.csv),
  ngữ liệu rỗng / ảnh / bảng, lựa chọn là tranh, lựa chọn đề hỏng…
- Tạo output/thu_tu_chay.csv (một lần) theo NGỮ LIỆU, có cột 'lo' (lô ~10 câu, không cắt đôi ngữ liệu)
- Tạo/cập nhật output/reports/trang_thai.csv; phát hiện câu có dữ liệu gốc thay đổi (so hash)
- Báo cáo: khao_sat_s0.csv, ngu_lieu.csv, trich_dan.csv, tinh_toan.csv, co_ban_goc.csv, ruby_hong_ban_goc.csv, danh_dau_rac.csv

Cách chạy (từ thư mục dạng bài):
  python3 scripts/s0_chuan_bi.py                    # chuẩn hóa toàn bộ 354 câu
  python3 scripts/s0_chuan_bi.py --tao-lai-thu-tu   # tạo lại thứ tự chạy (CHỈ khi chưa chạy lô nào)
"""
import argparse
import collections
import os
import re

import _dang as D
import pipeline_chung.doc_hieu_chung as H
from pipeline_chung.common import read_csv, save_json, sha, write_csv
from pipeline_chung.normalize import has_reserved_marks, mark_segments, normalize_html, pairs
from pipeline_chung.trang_thai import Status


def plain(html):
    t, b = normalize_html((html or "").replace("\x08", ""))
    return t.replace("{", "").replace("}", ""), b


def prepare(row, nl_cache):
    sid = D.sid_of(row)
    g = (row.get("giai_thich_vi") or "").strip()
    lua_chon = [plain(row.get(f"lua_chon_{i}", ""))[0] for i in range(1, 5)]
    cau_hoi, b0 = plain(row.get("cau_hoi", ""))
    dap = int(row["dap_an_so"]) if row["dap_an_so"].strip().isdigit() else row["dap_an_so"]
    qid = int(row["question_id"])
    if qid not in nl_cache:
        nl_cache[qid] = H.ngu_lieu(row.get("doan_van", ""))
    nl, info = nl_cache[qid]
    rec = {"sample_id": sid, "question_id": qid, "cau_con": int(row["cau_con"]), "cap_do": row["cap_do"],
           "hash_goc": sha(g + "|" + row.get("cau_hoi", "") + "|" + "|".join(lua_chon) + "|" + row["dap_an_so"] + "|" + row.get("doan_van", "")),
           "de": {"de_bai_chung": plain(row.get("de_bai_chung", ""))[0], "cau_hoi": cau_hoi, "lua_chon": lua_chon, "dap_an_so": dap,
                  "dap_an_noi_dung": plain(row.get("dap_an_noi_dung", ""))[0]},
           "doan_van": nl, "ngu_lieu": info, "co": [], "ghi_chu_ban_goc": [], "ruby_hong": list(b0), "danh_dau_rac": []}
    if not g:
        rec.update(khuon_goc="trong", dau_vao=None, src_text="", src_vi_text="", src_text_furi="", marks_src=[], phan=None)
        rec["ghi_chu_ban_goc"].append("[Bản gốc VI] Không có lời giải")
        return rec, {}
    if has_reserved_marks(g):
        rec["co"].append("ky_hieu_trung")
    rac = []
    gg = g
    if re.search(r"<table\b", gg, re.I):              # bảng trong lời giải (hiếm) → trải bảng như ngữ liệu
        gg = H.ngu_lieu(gg)[0].replace("\n", "<br>")
    text, broken = normalize_html(gg, "u+b", rac)
    text, n_md = H.bo_markdown(text)
    text, furi_vi = H.bo_furigana_chu_viet(text)
    phan = H.tach_loi_giai(text, lua_chon, cau_hoi)
    phan["tham_khao"] = None
    co, gc, so_lieu = H.gan_co(phan, rec["de"], nl, info, text)
    rec.update(khuon_goc=phan["khuon"], dau_vao=text, src_text=text, src_vi_text=text, src_text_furi=text,
               marks_src=mark_segments(text), phan=phan, danh_dau_rac=rac)
    rec["co"] += co
    rec["ghi_chu_ban_goc"] += gc
    if n_md:
        rec["co"].append("markdown")
        rec["ghi_chu_ban_goc"].append("[Python sửa định dạng] Bỏ ký hiệu markdown (** / #) của lời giải gốc, giữ nguyên dòng")
    if furi_vi:
        rec["co"].append("furigana_chu_viet")
        rec["ghi_chu_ban_goc"].append("[Python sửa định dạng] Bỏ furigana gắn lên chữ tiếng Việt: " + ", ".join(f"'{a}' → '{b}'" for a, b in furi_vi))
    rec["ruby_hong"] += broken
    if rac:
        rec["co"].append("danh_dau_rac")
    if pairs(text):
        rec["co"].append("co_furigana")
    if rec["ruby_hong"]:
        rec["co"].append("ruby_hong")
        rec["ghi_chu_ban_goc"].append(f"[Bản gốc VI] Có {len(rec['ruby_hong'])} thẻ ruby hỏng")
    rec["co"] = sorted(set(rec["co"]))
    rec["ghi_chu_ban_goc"] = list(dict.fromkeys(rec["ghi_chu_ban_goc"]))
    return rec, so_lieu


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tao-lai-thu-tu", action="store_true", help="tạo lại output/thu_tu_chay.csv (mặc định giữ file cũ)")
    args = ap.parse_args()
    cfg = D.cfg()
    rows = read_csv(D.data_path())
    st = Status(D.status_path())
    recs, changed, nl_cache = [], [], {}
    td_rows, tt_rows = [], []
    for row in rows:
        rec, sl = prepare(row, nl_cache)
        recs.append(rec)
        for x in sl.get("trich_dan", []):
            td_rows.append({"sample_id": rec["sample_id"], "cap_do": rec["cap_do"], "lua_chon": x["lua_chon"], "ket_qua": x["ket_qua"],
                            "ty_le": x["ty_le"], "trich": x["trich"]})
        for x in sl.get("tinh_toan", []):
            tt_rows.append({"sample_id": rec["sample_id"], "cap_do": rec["cap_do"], "dung": "đúng" if x["dung"] else "SAI",
                            "bieu_thuc": x["bieu_thuc"], "ket_qua_ghi": x["ket_qua_ghi"], "tinh_lai": f"{x['tinh_lai']:g}", "dong": x["dong"]})
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

    R = lambda *p: D.OUT("reports", *p)  # noqa: E731
    write_csv([{"sample_id": r["sample_id"], "ruby": x} for r in recs for x in r["ruby_hong"]], R("ruby_hong_ban_goc.csv"), ["sample_id", "ruby"])
    write_csv([{"sample_id": r["sample_id"], "doan_bi_bo_the": x} for r in recs for x in r["danh_dau_rac"]], R("danh_dau_rac.csv"),
              ["sample_id", "doan_bi_bo_the"])
    write_csv(td_rows, R("trich_dan.csv"), ["sample_id", "cap_do", "lua_chon", "ket_qua", "ty_le", "trich"])
    write_csv(tt_rows, R("tinh_toan.csv"), ["sample_id", "cap_do", "dung", "bieu_thuc", "ket_qua_ghi", "tinh_lai", "dong"])
    seen, nl_rows = set(), []
    for r in recs:
        if r["question_id"] in seen:
            continue
        seen.add(r["question_id"])
        info = r["ngu_lieu"]
        nl_rows.append({"question_id": r["question_id"], "cap_do": r["cap_do"], "so_cau": sum(1 for x in recs if x["question_id"] == r["question_id"]),
                        "bang": info["bang"], "anh": len(info["anh"]), "rong": "x" if info["rong"] else "", "do_dai": info["do_dai"],
                        "ngu_lieu": r["doan_van"][:3000]})
    write_csv(nl_rows, R("ngu_lieu.csv"))
    tdc = collections.Counter((x["sample_id"], x["ket_qua"]) for x in td_rows)
    write_csv([{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "khuon": r["khuon_goc"], "co": " ".join(r["co"]),
                "trich_dan": sum(v for (s, _), v in tdc.items() if s == r["sample_id"]),
                "td_khop": tdc[(r["sample_id"], "khop")], "td_mot_phan": tdc[(r["sample_id"], "mot_phan")], "td_khong": tdc[(r["sample_id"], "khong")],
                "phep_tinh": sum(1 for x in tt_rows if x["sample_id"] == r["sample_id"]),
                "phep_tinh_sai": sum(1 for x in tt_rows if x["sample_id"] == r["sample_id"] and x["dung"] == "SAI"),
                "ghi_chu_ban_goc": "\n".join(r["ghi_chu_ban_goc"])} for r in recs], R("khao_sat_s0.csv"))
    write_csv([{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "co": " ".join(r["co"]), "ghi_chu_ban_goc": "\n".join(r["ghi_chu_ban_goc"])}
               for r in recs if r["co"] or r["ghi_chu_ban_goc"]], R("co_ban_goc.csv"))

    co = collections.Counter(c for r in recs for c in r["co"])
    print(f"Đã chuẩn hóa {len(recs)} câu ({len(nl_cache)} ngữ liệu) → {D.OUT('samples', 'norm')}")
    print("Khuôn lời giải:", dict(collections.Counter(r["khuon_goc"] for r in recs)))
    print("Trích dẫn ↔ ngữ liệu (output/reports/trich_dan.csv):", dict(collections.Counter(x["ket_qua"] for x in td_rows)))
    print("Phép tính (output/reports/tinh_toan.csv):", dict(collections.Counter(x["dung"] for x in tt_rows)))
    for c, n in co.most_common():
        print(f"  cờ {c:26} {n:5}  – {D.FLAG_TEXT.get(c, '')}")
    kho = D.da_duyet_rows()
    print(f"Kho đã duyệt: {len(kho)} câu" + (f" – đánh dấu ĐÃ_DUYỆT_CTV: {n_dd}" if n_dd else ""))
    if changed:
        print(f"CHÚ Ý: {len(changed)} câu có dữ liệu gốc thay đổi so với lần chạy trước → đặt lại ĐANG_XỬ_LÝ")
    if args.tao_lai_thu_tu or not os.path.exists(D.OUT("thu_tu_chay.csv")):
        tt = H.tao_thu_tu_ngu_lieu(recs, cfg)
        write_csv(tt, D.OUT("thu_tu_chay.csv"))
        so_lo = collections.Counter(x["lo"] for x in tt)
        print(f"Đã tạo thứ tự chạy → {D.OUT('thu_tu_chay.csv')}: {len(so_lo)} lô (cỡ lô: {dict(collections.Counter(so_lo.values()))}); "
              f"100 câu đầu: {dict(collections.Counter(x['cap_do'] for x in tt[:100]))}")


if __name__ == "__main__":
    main()
