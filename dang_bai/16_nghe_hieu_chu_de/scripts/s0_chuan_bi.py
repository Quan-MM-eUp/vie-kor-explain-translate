"""Giai đoạn 0 – Chuẩn bị (Python, không sửa nội dung) – dạng 16 Nghe hiểu chủ đề.

- Chọn nguồn: lời thoại tiếng Nhật (transcript_vi / doan_van / đầu lời giải), bản dịch Việt, phần phân tích (giai_thich_vi / transcript_vi)
- Làm sạch HTML (rác thuộc tính, &nbsp;), ruby → ｜…《…》, in đậm / gạch chân → { } (WF chung 3a; '{男：…}' → nhãn ra ngoài)
- Tách dòng + nhãn người nói; cắt danh sách lựa chọn / khối phụ (từ vựng) ở cuối; ghép dòng JA ↔ VI (full_translation dựng sẵn)
- Tách phân tích thành khối 1.–4. (kết luận → ĐÚNG/SAI), gợi ý câu trích 「…」(dịch) / phần dẫn / nghĩa lựa chọn; đoạn phân tích mở đầu → summary
- Khuôn: A (có phân tích) · C (chỉ bản dịch) · D (chỉ lời thoại) · E (không có lời thoại); tao_bang = python (không phân tích) | tac_tu
- Gắn cờ + ghi chú [Bản gốc VI]; output/thu_tu_chay.csv (một lần): 100 câu đầu = 20 câu mỗi cấp, xen kẽ
- Báo cáo: output/reports/khao_sat_s0.csv (mỗi câu một dòng), co_ban_goc.csv, ruby_hong_ban_goc.csv, danh_dau_rac.csv

Cách chạy (từ thư mục dạng bài):
  python3 scripts/s0_chuan_bi.py                    # chuẩn hóa toàn bộ 1084 câu
  python3 scripts/s0_chuan_bi.py --tao-lai-thu-tu   # tạo lại thứ tự chạy (mặc định giữ file cũ)
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
        sid = rec["sample_id"]
        old = st.get(sid)
        if old and old.get("hash_goc") and old["hash_goc"] != rec["hash_goc"]:
            changed.append(sid)
            st.update(sid, trang_thai="ĐANG_XỬ_LÝ", giai_doan_loi="", loi="Dữ liệu gốc đã thay đổi – cần chạy lại từ giai đoạn 1")
        if not old or sid in changed:
            trong = rec["khuon_goc"] == "trong"
            st.update(sid, trang_thai="LỖI_GĐ1" if trong else "ĐANG_XỬ_LÝ", giai_doan_loi="1" if trong else "",
                      loi="Không có lời giải gốc" if trong else "")
        st.update(sid, question_id=rec["question_id"], cau_con=rec["cau_con"], cap_do=rec["cap_do"],
                  khuon_goc=rec["khuon_goc"], co=" ".join(rec["co"]), hash_goc=rec["hash_goc"], ghi_chu_ban_goc=rec["ghi_chu_ban_goc"])
    n_dd, _ = D.danh_dau_da_duyet(st, {r["sample_id"]: r["hash_goc"] for r in recs})
    st.save()

    ks = []
    for r in recs:
        t = r.get("nghe") or {}
        ks.append({"sample_id": r["sample_id"], "cap_do": r["cap_do"], "khuon": r["khuon_goc"], "tao_bang": r.get("tao_bang") or "",
                   "nguon_ja": (t.get("nguon") or {}).get("nguon_ja") or "", "nguon_vi": (t.get("nguon") or {}).get("nguon_vi") or "",
                   "nguon_phan_tich": (t.get("nguon") or {}).get("nguon_phan_tich") or "",
                   "so_dong_ja": len(t.get("loi_thoai_ja") or []), "so_dong_vi": len(t.get("ban_dich_vi") or []),
                   "ghep_python": "x" if t.get("full_translation") is not None else "",
                   "so_khoi": len(t.get("khoi") or []), "so_trich": sum(len(g["trich"]) for g in r.get("goi_y_khoi") or []),
                   "co": " ".join(r["co"]), "ghi_chu_ban_goc": "\n".join(r["ghi_chu_ban_goc"])})
    write_csv(ks, D.OUT("reports", "khao_sat_s0.csv"))
    write_csv([{"sample_id": r["sample_id"], "ruby": x} for r in recs for x in r["ruby_hong"]],
              D.OUT("reports", "ruby_hong_ban_goc.csv"), ["sample_id", "ruby"])
    write_csv([{"sample_id": r["sample_id"], "doan_bi_bo_the": x} for r in recs for x in r["danh_dau_rac"]],
              D.OUT("reports", "danh_dau_rac.csv"), ["sample_id", "doan_bi_bo_the"])
    write_csv([{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "co": " ".join(r["co"]),
                "ghi_chu_ban_goc": "\n".join(r["ghi_chu_ban_goc"])} for r in recs if r["co"] or r["ghi_chu_ban_goc"]],
              D.OUT("reports", "co_ban_goc.csv"))

    print(f"Đã chuẩn hóa {len(recs)} câu → {os.path.relpath(D.OUT('samples', 'norm'), D.DANG)}")
    print("  khuôn:", dict(collections.Counter(r["khuon_goc"] for r in recs)),
          "| tạo bằng:", dict(collections.Counter(r.get("tao_bang") for r in recs)))
    print("  ghép dòng Python:", sum(1 for x in ks if x["ghep_python"]), "/", len(ks))
    co = collections.Counter(c for r in recs for c in r["co"])
    for c, n in co.most_common():
        print(f"  cờ {c:32} {n:5}  – {D.FLAG_TEXT.get(c, '')}")
    print(f"Kho đã duyệt: {len(D.da_duyet_rows())} câu" + (f" – đánh dấu ĐÃ_DUYỆT_CTV: {n_dd}" if n_dd else ""))
    if changed:
        print(f"CHÚ Ý: {len(changed)} câu có dữ liệu gốc thay đổi so với lần chạy trước → đặt lại ĐANG_XỬ_LÝ")
    if args.tao_lai_thu_tu or not os.path.exists(D.OUT("thu_tu_chay.csv")):
        tt = D.tao_thu_tu(recs, cfg)
        write_csv(tt, D.OUT("thu_tu_chay.csv"))
        dau = tt[:100]
        print(f"Đã tạo thứ tự chạy → output/thu_tu_chay.csv (100 câu đầu: {dict(collections.Counter(x['cap_do'] for x in dau))}, "
              f"tranh {sum(1 for x in dau if x['lua_chon_tranh'])}, Python dựng {sum(1 for x in dau if x['tao_bang'] == 'python')})")


if __name__ == "__main__":
    main()
