"""Giai đoạn 0 – Chuẩn bị (Python, không sửa nội dung) – dạng 17 Nghe hiểu điểm chính.

- Chuẩn hóa lời thoại (cột transcript_vi – TIẾNG NHẬT) và lời giải (giai_thich_vi): ruby → ｜…《…》, bỏ in đậm (Q4 – chỉ làm gợi ý)
- Tách lượt thoại + nhãn người nói (chuẩn hóa 男/M/Ｍ → M, 女/F/Ｆ → F – Q5), tách nhãn ở giữa dòng; bỏ 4 lựa chọn ở cuối lời thoại
- Tách lời giải: bản dịch từng dòng / câu hỏi / 4 nghĩa lựa chọn / phần sau ### → khuôn A (Thông tin) · B (Đáp án … Vì …) · C (chỉ dịch) · D (không có tiếng Việt)
- Ghép cặp gợi ý Nhật ↔ Việt, dựng KHUNG JSON cho tác tử TẠO (output/samples/norm/<id>.json, khóa "khung")
- Cờ gợi ý cho tác tử KIỂM TRA; khuôn D → LỖI_GĐ1 (bỏ qua – Q2), danh sách output/reports/khuon_D.csv
- Thứ tự chạy output/thu_tu_chay.csv (một lần): 100 câu đầu = 20 câu mỗi cấp, xen kẽ; khuôn D xếp cuối
- Báo cáo: output/reports/khao_sat_s0.csv (khuôn, cờ, cách ghép từng câu), ruby_hong_ban_goc.csv

Cách chạy (từ thư mục dạng bài):  python3 scripts/s0_chuan_bi.py   [--tao-lai-thu-tu]
"""
import argparse
import collections
import os

import _dang as D
from pipeline_chung.common import read_csv, save_json, write_csv
from pipeline_chung.trang_thai import Status

LOI_D = "Khuôn D – lời giải không có tiếng Việt (chỉ chép lại lời thoại): bỏ qua theo Q2, chuyển CTV dịch bổ sung (output/reports/khuon_D.csv)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tao-lai-thu-tu", action="store_true", help="tạo lại output/thu_tu_chay.csv (mặc định giữ file cũ)")
    args = ap.parse_args()
    cfg = D.cfg()
    rows = read_csv(D.data_path())
    st = Status(D.status_path())
    recs, changed = [], []
    for row in rows:
        rec = D.chuan_bi(row)
        recs.append(rec)
        save_json(rec, D.OUT("samples", "norm", rec["sample_id"] + ".json"))
        sid, la_d = rec["sample_id"], rec["khuon_goc"] == "D"
        old = st.get(sid)
        if old and old.get("hash_goc") and old["hash_goc"] != rec["hash_goc"]:
            changed.append(sid)
        if not old or sid in changed:
            st.update(sid, trang_thai="LỖI_GĐ1" if la_d else "ĐANG_XỬ_LÝ", giai_doan_loi="1" if la_d else "",
                      loi=LOI_D if la_d else ("Dữ liệu gốc đã thay đổi – cần chạy lại từ giai đoạn 1" if sid in changed else ""))
        st.update(sid, question_id=rec["question_id"], cau_con=rec["cau_con"], cap_do=rec["cap_do"], khuon_goc=rec["khuon_goc"],
                  co=" ".join(rec["co"]), hash_goc=rec["hash_goc"], ghi_chu_ban_goc=rec["ghi_chu_ban_goc"])
    n_dd, _ = D.danh_dau_da_duyet(st, {r["sample_id"]: r["hash_goc"] for r in recs})
    st.save()

    write_csv([{"sample_id": r["sample_id"], "ruby": x} for r in recs for x in r["ruby_hong"]],
              D.OUT("reports", "ruby_hong_ban_goc.csv"), ["sample_id", "ruby"])
    write_csv([{"sample_id": r["sample_id"], "question_id": r["question_id"], "cap_do": r["cap_do"],
                "loi_thoai": "\n".join(r["loi_thoai_goc"]), "giai_thich_vi": "\n".join(r["loi_giai_goc"])}
               for r in recs if r["khuon_goc"] == "D"], D.OUT("reports", "khuon_D.csv"))
    write_csv([{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "khuon": r["khuon_goc"],
                "so_luot": len(r["luot"]), "so_dong_viet": len((r.get("vi") or {}).get("dong_thoai") or []),
                "cach_ghep": (r.get("ghep") or {}).get("cach") or "", "co": " ".join(r["co"]),
                "ghi_chu_ban_goc": "\n".join(r["ghi_chu_ban_goc"])} for r in recs], D.OUT("reports", "khao_sat_s0.csv"))

    k = collections.Counter(r["khuon_goc"] for r in recs)
    g = collections.Counter((r.get("ghep") or {}).get("cach") or "khong_ghep" for r in recs if r["khuon_goc"] != "D")
    co = collections.Counter(c for r in recs for c in r["co"])
    print(f"Đã chuẩn hóa {len(recs)} câu → {D.OUT('samples', 'norm')}")
    print(f"Khuôn: {dict(sorted(k.items()))}  (D = không có tiếng Việt → LỖI_GĐ1, bỏ qua)")
    print(f"Ghép cặp Nhật ↔ Việt (khuôn A–C): {dict(g)}")
    for c, n in co.most_common():
        print(f"  cờ {c:32} {n:5}  – {D.FLAG_TEXT.get(c, '')}")
    print(f"Kho đã duyệt: {len(D.da_duyet_rows())} câu" + (f" – đánh dấu ĐÃ_DUYỆT_CTV: {n_dd}" if n_dd else ""))
    if changed:
        print(f"CHÚ Ý: {len(changed)} câu có dữ liệu gốc thay đổi so với lần chạy trước → đặt lại trạng thái")
    if args.tao_lai_thu_tu or not os.path.exists(D.OUT("thu_tu_chay.csv")):
        tt = D.tao_thu_tu(recs, cfg)
        write_csv(tt, D.OUT("thu_tu_chay.csv"))
        print(f"Đã tạo thứ tự chạy → output/thu_tu_chay.csv (100 câu đầu: cấp {dict(collections.Counter(x['cap_do'] for x in tt[:100]))}, "
              f"khuôn {dict(collections.Counter(x['khuon'] for x in tt[:100]))})")


if __name__ == "__main__":
    main()
