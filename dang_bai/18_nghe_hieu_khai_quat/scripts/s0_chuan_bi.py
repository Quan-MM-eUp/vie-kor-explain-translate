"""Giai đoạn 0 – Chuẩn bị (Python, không sửa nội dung) – dạng 18 Nghe hiểu khái quát.

- Chọn nguồn lời thoại Nhật (transcript_vi; dán nhầm lời giải → doan_van), tách dòng L1…Ln + người nói + câu hỏi + 4 lựa chọn
- Chuẩn hóa lời giải (ruby → ｜…《…》), tách: bản dịch VI / câu hỏi VI / 4 khối phân tích; phân loại khuôn A / C / D / E
- Gắn cờ gợi ý + ghi chú [Bản gốc VI] tự động (scripts/_dang.py: FLAG_TEXT)
- Tạo output/thu_tu_chay.csv (một lần): 100 câu đầu xen kẽ N1/N2/N3; rồi các câu còn lại theo file dữ liệu
- Tạo/cập nhật output/reports/trang_thai.csv; phát hiện câu có dữ liệu gốc thay đổi (so hash)
- Báo cáo: output/reports/khao_sat_s0.csv (khuôn, cờ, số dòng thoại / dịch), loi_thoai.csv (từng dòng L), ruby_hong_ban_goc.csv, co_ban_goc.csv

Cách chạy (từ thư mục dạng bài):
  python scripts/s0_chuan_bi.py                       # chuẩn hóa toàn bộ 351 câu
  python scripts/s0_chuan_bi.py --tao-lai-thu-tu      # tạo lại thứ tự chạy (mặc định giữ file cũ)
"""
import argparse
import collections
import os

import _dang as D
from pipeline_chung.common import read_csv, save_json, write_csv
from pipeline_chung.trang_thai import Status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tao-lai-thu-tu", action="store_true", help="tạo lại output/thu_tu_chay.csv (mặc định giữ file cũ)")
    args = ap.parse_args()
    cfg = D.cfg()
    rows = read_csv(D.data_path())
    st = Status(D.status_path())
    recs, changed = [], []
    for row in rows:
        rec = D.chuan_bi_mau(row)
        recs.append(rec)
        save_json(rec, D.OUT("samples", "norm", rec["sample_id"] + ".json"))
        old = st.get(rec["sample_id"])
        trong = rec["khuon_goc"] == "trong" or not rec["loi_thoai"]["nguon"]
        if old and old.get("hash_goc") and old["hash_goc"] != rec["hash_goc"]:
            changed.append(rec["sample_id"])
        if not old or rec["sample_id"] in changed:
            st.update(rec["sample_id"], trang_thai="LỖI_GĐ1" if trong else "ĐANG_XỬ_LÝ", giai_doan_loi="1" if trong else "",
                      loi=("Không có lời giải / lời thoại gốc" if trong else
                           ("Dữ liệu gốc đã thay đổi – cần chạy lại từ giai đoạn 1" if rec["sample_id"] in changed else "")))
        st.update(rec["sample_id"], question_id=rec["question_id"], cau_con=rec["cau_con"], cap_do=rec["cap_do"],
                  khuon_goc=rec["khuon_goc"], co=" ".join(rec["co"]), hash_goc=rec["hash_goc"], ghi_chu_ban_goc=rec["ghi_chu_ban_goc"])
    n_dd, _ = D.danh_dau_da_duyet(st, {r["sample_id"]: r["hash_goc"] for r in recs})
    st.save()

    write_csv([{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "khuon": r["khuon_goc"], "nguon_loi_thoai": r["loi_thoai"]["nguon"],
                "kieu_lua_chon": r["loi_thoai"]["kieu"], "so_dong_thoai": len(r["loi_thoai"]["dong"]), "so_dong_dich": len(r["phan"]["dich"]),
                "co_cau_hoi_vi": "x" if r["phan"]["cau_hoi_vi"] else "", "so_khoi": len(r["phan"]["khoi"]),
                "so_trich": sum(len(b["trich"]) for b in r["phan"]["khoi"]), "trich_ngoai_loi_thoai": len(r["phan"]["trich_ngoai"]),
                "co": " ".join(r["co"]), "ghi_chu_ban_goc": "\n".join(r["ghi_chu_ban_goc"])} for r in recs],
              D.OUT("reports", "khao_sat_s0.csv"))
    write_csv([{"sample_id": r["sample_id"], "so": d["so"], "speaker": d["speaker"] or "", "ja": d["ja"]}
               for r in recs for d in r["loi_thoai"]["dong"]], D.OUT("reports", "loi_thoai.csv"), ["sample_id", "so", "speaker", "ja"])
    write_csv([{"sample_id": r["sample_id"], "ruby": x} for r in recs for x in r["ruby_hong"]],
              D.OUT("reports", "ruby_hong_ban_goc.csv"), ["sample_id", "ruby"])
    write_csv([{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "co": " ".join(r["co"]),
                "ghi_chu_ban_goc": "\n".join(r["ghi_chu_ban_goc"])} for r in recs if r["co"] or r["ghi_chu_ban_goc"]],
              D.OUT("reports", "co_ban_goc.csv"))

    print(f"Đã chuẩn hóa {len(recs)} câu → {D.OUT('samples', 'norm')}")
    print("  khuôn lời giải:", dict(collections.Counter(r["khuon_goc"] for r in recs)))
    print("  nguồn lời thoại:", dict(collections.Counter(r["loi_thoai"]["nguon"] for r in recs)),
          "| lựa chọn trong lời thoại:", dict(collections.Counter(r["loi_thoai"]["kieu"] for r in recs)))
    co = collections.Counter(c for r in recs for c in r["co"])
    for c, n in co.most_common():
        print(f"  cờ {c:28} {n:5}  – {D.FLAG_TEXT.get(c, '')}")
    hv = [r["sample_id"] for r in recs if D.han_viet_src(r)]
    print(f"  câu có âm Hán Việt trong lời giải: {len(hv)} {hv[:8]}")
    print(f"Kho đã duyệt: {len(D.da_duyet_rows())} câu" + (f" – đánh dấu ĐÃ_DUYỆT_CTV: {n_dd}" if n_dd else ""))
    if changed:
        print(f"CHÚ Ý: {len(changed)} câu có dữ liệu gốc thay đổi so với lần chạy trước → đặt lại ĐANG_XỬ_LÝ")
    if args.tao_lai_thu_tu or not os.path.exists(D.OUT("thu_tu_chay.csv")):
        tt = D.tao_thu_tu(recs, cfg)
        write_csv(tt, D.OUT("thu_tu_chay.csv"))
        print(f"Đã tạo thứ tự chạy → output/thu_tu_chay.csv (100 câu đầu: {dict(collections.Counter(x['cap_do'] for x in tt[:100]))};"
              f" khuôn {dict(collections.Counter(x['khuon'] for x in tt[:100]))})")


if __name__ == "__main__":
    main()
