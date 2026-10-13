"""Giai đoạn 0 – Chuẩn bị (Python, không sửa nội dung) – dạng 21 Nghe hiểu tổng hợp.

- Gộp theo BÀI NGHE (question_id): lời thoại JA lấy từ cột transcript_vi (bản dài nhất trong các câu con, bỏ bản dán nhầm lời giải),
  làm sạch HTML / <b> / khoảng trắng chen giữa chữ Nhật, cắt lời dẫn đề ở đầu và câu hỏi + danh sách lựa chọn ở cuối.
- Câu hỏi đề xuất (cột cau_hoi, hoặc câu hỏi cắt ở cuối lời thoại – 質問1 / 質問2 theo câu con).
- Chuẩn hóa lời giải (ruby → ｜…《…》), tách THAM KHẢO, phân khuôn A / B / C_vi / C_ja / trong, tách bản dịch VI / phân tích 1–4 / Thông tin.
- Cờ gợi ý (FLAG_TEXT trong _dang.py); dữ liệu đề lỗi (thiếu lựa chọn, không có lời giải) → LỖI_GĐ1 ngay.
- output/thu_tu_chay.csv + output/lo_chay.csv (lô 5 bài; lô 1 = pilot) – tạo một lần (--tao-lai-thu-tu để tạo lại).
- Báo cáo output/reports/khao_sat_s0.csv.

Cách chạy (từ thư mục dạng bài):  python3 scripts/s0_chuan_bi.py
"""
import argparse
import collections
import os

import _dang as D
from pipeline_chung.common import read_csv, save_json, write_csv
from pipeline_chung.trang_thai import Status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tao-lai-thu-tu", action="store_true", help="tạo lại output/thu_tu_chay.csv + lo_chay.csv (mặc định giữ file cũ)")
    args = ap.parse_args()
    cfg = D.cfg()
    rows = read_csv(D.data_path())
    bai = collections.OrderedDict()
    for r in rows:
        bai.setdefault(r["question_id"], []).append(r)
    st = Status(D.status_path())
    recs, changed = [], []
    for q, rs in bai.items():
        for rec in D.chuan_bi_bai(rs):
            recs.append(rec)
            save_json(rec, D.OUT("samples", "norm", rec["sample_id"] + ".json"))
            sid = rec["sample_id"]
            old = st.get(sid)
            loi_de = ("Không có lời giải gốc" if rec["khuon_goc"] == "trong"
                      else "Dữ liệu đề thiếu lựa chọn (lua_chon_i rỗng) – cần sửa dữ liệu gốc" if "lua_chon_thieu" in rec["co"] else "")
            if old and old.get("hash_goc") and old["hash_goc"] != rec["hash_goc"]:
                changed.append(sid)
            if not old or sid in changed:
                st.update(sid, trang_thai="LỖI_GĐ1" if loi_de else "ĐANG_XỬ_LÝ", giai_doan_loi="1" if loi_de else "",
                          loi=loi_de or ("Dữ liệu gốc đã thay đổi – cần chạy lại từ giai đoạn 1" if sid in changed else ""))
            st.update(sid, question_id=rec["question_id"], cau_con=rec["cau_con"], cap_do=rec["cap_do"],
                      khuon_goc=rec["khuon_goc"], co=" ".join(rec["co"]), hash_goc=rec["hash_goc"],
                      ghi_chu_ban_goc=rec["ghi_chu_ban_goc"])
    n_dd, _ = D.danh_dau_da_duyet(st, {r["sample_id"]: r["hash_goc"] for r in recs})
    st.save()

    write_csv([{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "khuon": r["khuon_goc"], "co": " ".join(r["co"]),
                "so_dong_loi_thoai": len(r["loi_thoai"]["dong"]), "so_dong_dich_vi": len((r.get("phan") or {}).get("dich_vi") or []),
                "ft_chep_tu": r.get("ft_chep_tu") or "", "cau_hoi_de_xuat": r.get("cau_hoi_de_xuat") or "",
                "cau_hoi_cat": " | ".join(r["loi_thoai"]["cau_hoi_cat"]), "dau_cat": " | ".join(r["loi_thoai"]["dau_cat"]),
                "ghi_chu_ban_goc": "\n".join(r["ghi_chu_ban_goc"])} for r in recs], D.OUT("reports", "khao_sat_s0.csv"))
    print(f"Đã chuẩn hóa {len(recs)} câu / {len(bai)} bài → {D.OUT('samples', 'norm')}")
    print("Khuôn:", dict(collections.Counter(r["khuon_goc"] for r in recs)))
    for c, n in collections.Counter(c for r in recs for c in r["co"]).most_common():
        print(f"  cờ {c:24} {n:4}  – {D.FLAG_TEXT.get(c, '')}")
    loi = [r["sample_id"] for r in recs if r["khuon_goc"] == "trong" or "lua_chon_thieu" in r["co"]]
    if loi:
        print(f"Dữ liệu gốc lỗi → LỖI_GĐ1 (báo người dùng sửa dữ liệu): {loi}")
    print(f"Kho đã duyệt: {len(D.da_duyet_rows())} câu" + (f" – đánh dấu ĐÃ_DUYỆT_CTV: {n_dd}" if n_dd else ""))
    if changed:
        print(f"CHÚ Ý: {len(changed)} câu có dữ liệu gốc thay đổi → đặt lại ĐANG_XỬ_LÝ: {changed}")
    if args.tao_lai_thu_tu or not os.path.exists(D.OUT("thu_tu_chay.csv")):
        tt, lo = D.tao_thu_tu_bai(recs, cfg)
        write_csv(tt, D.OUT("thu_tu_chay.csv"))
        write_csv(lo, D.OUT("lo_chay.csv"))
        print(f"Đã tạo thứ tự chạy → output/thu_tu_chay.csv ({len(tt)} câu) + output/lo_chay.csv ({len(lo)} lô)")
        print(f"  Lô 1 (pilot): mẫu {lo[0]['tu']}–{lo[0]['den']} · bài {lo[0]['bai']} · khuôn {lo[0]['khuon']}")


if __name__ == "__main__":
    main()
