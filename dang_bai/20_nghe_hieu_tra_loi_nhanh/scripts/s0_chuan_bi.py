"""Giai đoạn 0 – Chuẩn bị (Python, không sửa nội dung) – dạng 20 Nghe hiểu: Trả lời nhanh.

- Chuẩn hóa lời giải gốc: ruby → ｜…《…》; in đậm / gạch chân → { } (WF chung mục 3a); bỏ furigana gắn lên chữ Việt
- Tách SCRIPT nghe (cột transcript_vi; lỗi thì thử doan_van): nhãn người nói, câu nói, các câu trả lời, ghi chú
- Tách lời giải: khuôn A (dịch + ### + khối lựa chọn) / B (khối, không ###) / C (chỉ bản dịch) / D (tự do);
  phần dịch lựa chọn trước ### là TRÙNG LẶP với 'Nghĩa:' → không đưa vào chuẩn kiểm tra (chỉ so để cảnh báo K-TL)
- Gắn cờ gợi ý + ghi chú [Bản gốc VI]; so câu Nhật của lựa chọn với script (K-SC)
- Tạo output/thu_tu_chay.csv (một lần): 100 câu đầu = 20 câu mỗi cấp N1–N5 xen kẽ (lô 10 = 2 câu mỗi cấp);
  lô 1 (1–10) có các trường hợp pilot: khuôn C, 1 chen từ Nhật, 3 có furigana trong phân tích, 1 lua_chon_4 thừa
- Tạo/cập nhật output/reports/trang_thai.csv; phát hiện câu có dữ liệu gốc thay đổi (so hash)
- Báo cáo: khao_sat_s0.csv, script.csv, du_lieu_goc.csv, ruby_hong_ban_goc.csv, doc_trong_ngoac.csv, danh_dau_rac.csv, co_ban_goc.csv

Cách chạy (từ thư mục dạng bài):
  python scripts/s0_chuan_bi.py
  python scripts/s0_chuan_bi.py --tao-lai-thu-tu      # tạo lại thứ tự chạy (CHỈ khi chưa chạy lô nào)
"""
import argparse
import collections
import os
import random

import _dang as D
from pipeline_chung.common import read_csv, save_json, sha, write_csv
from pipeline_chung.normalize import has_reserved_marks, mark_segments, normalize_html, paren_readings, pairs
from pipeline_chung.trang_thai import Status


def prepare(row):
    sid = D.sid_of(row)
    g = (row.get("giai_thich_vi") or "").strip()
    dap = int(row["dap_an_so"]) if str(row.get("dap_an_so", "")).isdigit() else row.get("dap_an_so")
    rec = {"sample_id": sid, "question_id": int(row["question_id"]), "cau_con": int(row["cau_con"]), "cap_do": row["cap_do"],
           "hash_goc": sha(g + "|" + (row.get("transcript_vi") or "") + "|" + str(row.get("dap_an_so"))),
           "co": [], "ghi_chu_ban_goc": [], "ruby_hong": [], "danh_dau_rac": []}
    if not g:
        rec.update(khuon_goc="trong", dau_vao=None, src_text="", src_vi_text="", src_text_furi="", marks_src=[], phan=None,
                   de={"cau_hoi": None, "lua_chon": [], "dap_an_so": dap, "dap_an_noi_dung": row.get("dap_an_noi_dung")})
        rec["ghi_chu_ban_goc"].append("[Bản gốc VI] Không có lời giải")
        return rec
    if has_reserved_marks(g):
        rec["co"].append("ky_hieu_trung")
    rac = []
    text, broken = normalize_html(g, "u+b", rac)
    text, furi_vi = D.bo_furigana_chu_viet(text)
    phan, co, gc, src, src_vi = D.parse_and_flag(text, row)
    sc = phan["script"]
    rec["de"] = {"cau_hoi": sc.get("cau_noi"), "lua_chon": list(sc.get("lua_chon") or []), "dap_an_so": dap,
                 "dap_an_noi_dung": row.get("dap_an_noi_dung")}
    rec.update(khuon_goc=phan["khuon"], dau_vao=text, src_text=src, src_vi_text=src_vi, src_text_furi=src,
               marks_src=mark_segments(src), phan=phan, danh_dau_rac=rac)
    rec["co"] += co
    rec["ghi_chu_ban_goc"] += gc
    if furi_vi:
        rec["co"].append("furigana_chu_viet")
        rec["ghi_chu_ban_goc"].append("[Python sửa định dạng] Bỏ furigana gắn lên chữ tiếng Việt: " + ", ".join(f"'{a}' → '{b}'" for a, b in furi_vi))
    rec["ruby_hong"] += broken + list(sc.get("ruby_hong") or [])
    if rac:
        rec["co"].append("danh_dau_rac")
    if pairs(src):
        rec["co"].append("co_furigana")
    if rec["ruby_hong"]:
        rec["co"].append("ruby_hong")
        rec["ghi_chu_ban_goc"].append(f"[Bản gốc VI] Có {len(rec['ruby_hong'])} thẻ ruby hỏng")
    rec["doc_trong_ngoac"] = paren_readings(text)
    rec["co"] = sorted(set(rec["co"]))
    return rec


PILOT_LO1 = [("khuon_C", 2), ("chen_tu_nhat_dich", 1), ("furigana_phan_tich", 3), ("lua_chon_thua", 1)]


def tao_thu_tu(recs, cfg):
    """100 câu đầu: 20 câu mỗi cấp N1–N5 xen kẽ (bỏ câu không có lời giải); lô 1 (15 câu = 3 câu mỗi cấp) chứa các trường hợp pilot.
    Sau đó các câu còn lại theo file dữ liệu."""
    tc = cfg.get("thu_tu_chay") or {}
    rng = random.Random(tc.get("seed", 2026))
    n, lv_names = tc.get("moi_cap_do", 20), ["N1", "N2", "N3", "N4", "N5"]
    per_lo = max(1, int(tc.get("lo", 15)) // len(lv_names))
    lv = {}
    for k in lv_names:
        pool = [r for r in recs if r["cap_do"] == k and r["khuon_goc"] != "trong"]
        rng.shuffle(pool)
        lv[k] = pool
    # đưa các câu pilot lên đầu danh sách cấp độ (tối đa per_lo câu mỗi cấp trong lô 1)
    chon = {k: [] for k in lv_names}
    for co, sl in PILOT_LO1:
        for _ in range(sl):
            for k in sorted(lv_names, key=lambda x: len(chon[x])):
                if len(chon[k]) >= per_lo:
                    continue
                r = next((x for x in lv[k] if co in x["co"] and x not in chon[k] and not ({"khuon_D", "du_lieu_loi", "script_khong_tach"} & set(x["co"]))), None)
                if r:
                    chon[k].append(r)
                    break
    for k in lv_names:
        lv[k] = chon[k] + [x for x in lv[k] if x not in chon[k]]
        lv[k] = lv[k][:n]
    dau = []
    for b in range(0, n, per_lo):                       # từng lô: per_lo câu mỗi cấp, xen kẽ N1→N5
        for i in range(b, b + per_lo):
            dau += [lv[k][i] for k in lv_names if i < len(lv[k])]
    seen = {r["sample_id"] for r in dau}
    rows = dau + [r for r in recs if r["sample_id"] not in seen]
    return [{"stt": i + 1, "sample_id": r["sample_id"], "question_id": r["question_id"], "cap_do": r["cap_do"],
             "khuon": r["khuon_goc"]} for i, r in enumerate(rows)]


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
            st.update(rec["sample_id"], trang_thai="ĐANG_XỬ_LÝ", giai_doan_loi="", loi="Dữ liệu gốc đã thay đổi – cần chạy lại từ giai đoạn 1")
        if not old or rec["sample_id"] in changed:
            trong = rec["khuon_goc"] == "trong"
            st.update(rec["sample_id"], trang_thai="LỖI_GĐ1" if trong else "ĐANG_XỬ_LÝ", giai_doan_loi="1" if trong else "",
                      loi="Không có lời giải gốc" if trong else "")
        st.update(rec["sample_id"], question_id=rec["question_id"], cau_con=rec["cau_con"], cap_do=rec["cap_do"],
                  khuon_goc=rec["khuon_goc"], co=" ".join(rec["co"]), hash_goc=rec["hash_goc"], ghi_chu_ban_goc=rec["ghi_chu_ban_goc"])
    n_dd, _ = D.danh_dau_da_duyet(st, {r["sample_id"]: r["hash_goc"] for r in recs})
    st.save()

    R = lambda *p: D.OUT("reports", *p)  # noqa: E731
    write_csv([{"sample_id": r["sample_id"], "ruby": x} for r in recs for x in r["ruby_hong"]], R("ruby_hong_ban_goc.csv"), ["sample_id", "ruby"])
    write_csv([{"sample_id": r["sample_id"], "doan": x} for r in recs for x in r.get("doc_trong_ngoac", [])], R("doc_trong_ngoac.csv"), ["sample_id", "doan"])
    write_csv([{"sample_id": r["sample_id"], "doan_bi_bo_the": x} for r in recs for x in r["danh_dau_rac"]], R("danh_dau_rac.csv"), ["sample_id", "doan_bi_bo_the"])
    write_csv([{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "khuon": r["khuon_goc"], "co": " ".join(r["co"]),
                "ghi_chu_ban_goc": "\n".join(r["ghi_chu_ban_goc"])} for r in recs], R("khao_sat_s0.csv"))
    write_csv([{"sample_id": r["sample_id"], "co": " ".join(r["co"]), "ghi_chu_ban_goc": "\n".join(r["ghi_chu_ban_goc"])}
               for r in recs if r["co"] or r["ghi_chu_ban_goc"]], R("co_ban_goc.csv"))
    sc_rows = []
    for r in recs:
        sc = (r.get("phan") or {}).get("script") or {}
        ss = {x["so"]: x for x in (r.get("phan") or {}).get("so_script") or []}
        sc_rows.append({"sample_id": r["sample_id"], "cap_do": r["cap_do"], "tach_duoc": "x" if sc.get("ok") else "",
                        "nguoi_noi": sc.get("nguoi_noi"), "cau_noi": sc.get("cau_noi"),
                        **{f"tra_loi_{i + 1}": x for i, x in enumerate((sc.get("lua_chon") or [])[:4])},
                        "lech_loi_giai": "; ".join(f"{k}: {v['chi_tiet']}" for k, v in ss.items() if v["ket_qua"] == "lech"),
                        "ghi_chu_script": "\n".join(sc.get("ghi_chu") or []), "script_goc": sc.get("hien_thi")})
    write_csv(sc_rows, R("script.csv"), ["sample_id", "cap_do", "tach_duoc", "nguoi_noi", "cau_noi", "tra_loi_1", "tra_loi_2",
                                         "tra_loi_3", "tra_loi_4", "lech_loi_giai", "ghi_chu_script", "script_goc"])
    dl = [{"sample_id": r["sample_id"], "van_de": D.FLAG_TEXT[c]} for r in recs for c in r["co"]
          if c in ("lua_chon_thua", "du_lieu_loi", "script_khong_tach", "script_tu_doan_van", "ruby_hong")]
    write_csv(dl, R("du_lieu_goc.csv"), ["sample_id", "van_de"])

    co = collections.Counter(c for r in recs for c in r["co"])
    print(f"Đã chuẩn hóa {len(recs)} câu → {D.OUT('samples', 'norm')}")
    print("Khuôn:", dict(collections.Counter(r["khuon_goc"] for r in recs)), "| script tách được:",
          sum(bool(((r.get("phan") or {}).get("script") or {}).get("ok")) for r in recs))
    for c, k in co.most_common():
        print(f"  cờ {c:22} {k:5}  – {D.FLAG_TEXT.get(c, '')}")
    print(f"Báo cáo: output/reports/khao_sat_s0.csv, script.csv, du_lieu_goc.csv ({len(dl)} dòng)")
    print(f"Kho đã duyệt: {len(D.da_duyet_rows())} câu" + (f" – đánh dấu ĐÃ_DUYỆT_CTV: {n_dd}" if n_dd else ""))
    if changed:
        print(f"CHÚ Ý: {len(changed)} câu có dữ liệu gốc thay đổi so với lần chạy trước → đặt lại ĐANG_XỬ_LÝ")
    if args.tao_lai_thu_tu or not os.path.exists(D.OUT("thu_tu_chay.csv")):
        tt = tao_thu_tu(recs, cfg)
        write_csv(tt, D.OUT("thu_tu_chay.csv"))
        lo = int((cfg.get("thu_tu_chay") or {}).get("lo", 15))
        print(f"Đã tạo thứ tự chạy → {D.OUT('thu_tu_chay.csv')} (100 câu đầu: {dict(collections.Counter(x['cap_do'] for x in tt[:100]))}; "
              f"lô 1 (1–{lo}): {[x['sample_id'] for x in tt[:lo]]})")


if __name__ == "__main__":
    main()
