"""Giai đoạn 0 – Chuẩn bị (Python, không sửa nội dung) – dạng 02 Thay đổi cách nói.

- Chuẩn hóa lời giải gốc (100% văn bản ###): ruby → ｜…《…》; mọi in đậm / gạch chân → { } (WF chung mục 3a);
  bỏ nhãn in đậm, đánh dấu rác; giữ xuống dòng
- Đề gửi GPT: bỏ mọi đánh dấu (GPT chỉ theo { } của lời giải)
- Tách phần (câu đề / PHÂN TÍCH / LỰA CHỌN ĐÚNG / THAM KHẢO), gắn cờ gợi ý + ghi chú [Bản gốc VI] tự động
- Tạo/cập nhật output/reports/trang_thai.csv; phát hiện câu có dữ liệu gốc thay đổi (so hash)
- Báo cáo: ruby_hong_ban_goc.csv, doc_trong_ngoac.csv, danh_dau_rac.csv, co_ban_goc.csv
- (--chon-pilot) chọn mẫu pilot theo config → output/pilot.csv

Cách chạy (từ thư mục dạng bài):
  python scripts/s0_chuan_bi.py                 # chuẩn hóa toàn bộ 1.028 câu
  python scripts/s0_chuan_bi.py --chon-pilot    # + chọn mẫu pilot
"""
import argparse
import collections
import random

import _dang as D
from pipeline_chung.common import read_csv, save_json, sha, write_csv
from pipeline_chung.normalize import has_reserved_marks, mark_segments, normalize_html, paren_readings, pairs
from pipeline_chung.trang_thai import Status


def plain(html):
    """Chuẩn hóa và bỏ { } (dùng cho đề / lựa chọn gửi GPT)."""
    t, b = normalize_html(html or "")
    return t.replace("{", "").replace("}", ""), b


def prepare(row):
    sid = D.sid_of(row)
    g = (row.get("giai_thich_vi") or "").strip()
    lua_chon = [plain(row.get(f"lua_chon_{i}", ""))[0] for i in range(1, 5)]
    cau_hoi, b0 = plain(row.get("cau_hoi", ""))
    rec = {"sample_id": sid, "question_id": int(row["question_id"]), "cau_con": int(row["cau_con"]),
           "cap_do": row["cap_do"], "hash_goc": sha(g + "|" + row.get("cau_hoi", "") + "|" + "|".join(lua_chon) + "|" + row["dap_an_so"]),
           "de": {"cau_hoi": cau_hoi, "lua_chon": lua_chon, "dap_an_so": int(row["dap_an_so"]) if row["dap_an_so"].isdigit() else row["dap_an_so"],
                  "dap_an_noi_dung": plain(row.get("dap_an_noi_dung", ""))[0]},
           "co": [], "ghi_chu_ban_goc": [], "ruby_hong": list(b0), "danh_dau_rac": []}
    if not g:
        rec.update(khuon_goc="trong", dau_vao=None, src_text="", src_vi_text="", src_text_furi="", marks_src=[], phan=None)
        rec["ghi_chu_ban_goc"].append("[Bản gốc VI] Không có lời giải")
        return rec
    if has_reserved_marks(g):
        rec["co"].append("ky_hieu_trung")
    rac = []
    text, broken = normalize_html(g, "u+b", rac)
    phan, co, gc = D.parse_and_flag(text, g, lua_chon, row["dap_an_so"], row.get("cau_hoi", ""))
    no_lcd = D.text_without_lcd(text)
    rec.update(khuon_goc="###", dau_vao=text, src_text=text, src_vi_text=text, src_text_furi=no_lcd,
               marks_src=mark_segments(no_lcd), phan=phan, danh_dau_rac=rac)
    rec["co"] += co
    rec["ghi_chu_ban_goc"] += gc
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


def choose_pilot(recs, cfg):
    pc = cfg["pilot"]
    rng = random.Random(pc["seed"])
    by_id = {r["question_id"]: r for r in recs}
    chosen, why = [], {}

    def take(pool, n, label):
        pool = [r for r in pool if r["sample_id"] not in why]
        rng.shuffle(pool)
        for r in pool[:n]:
            chosen.append(r)
            why[r["sample_id"]] = label

    for q in pc.get("cau_bat_buoc", []):
        if q in by_id and by_id[q]["sample_id"] not in why:
            chosen.append(by_id[q]); why[by_id[q]["sample_id"]] = "câu chỉ định (ví dụ trong prompt / trường hợp đặc biệt)"
    n = pc["nhom"]
    is_sentence = lambda r: sum(len(x) >= 8 for x in r["de"]["lua_chon"]) >= 3   # noqa: E731 – chỉ để trải mẫu, không dùng cho JSON
    groups = {
        "lua_chon_la_cau": lambda r: is_sentence(r),
        "khong_danh_dau": lambda r: not r["marks_src"],
        "nhieu_doan_danh_dau": lambda r: "nhieu_doan_danh_dau" in r["co"],
        "dinh_lien_hoac_lech": lambda r: {"dong_pt_dinh_lien", "so_dong_pt_khac_4", "thu_tu_pt_lech"} & set(r["co"]),
        "thieu_phan": lambda r: {"thieu_dau_phan_cach", "thieu_tham_khao", "tham_khao_khong_nhan"} & set(r["co"]),
        "mo_dau_ket_luan": lambda r: {"co_mo_dau", "co_ket_luan"} & set(r["co"]),
        "co_furigana": lambda r: "co_furigana" in r["co"],
        "danh_dau_rac": lambda r: "danh_dau_rac" in r["co"],
    }
    for g, fn in groups.items():
        take([r for r in recs if r["khuon_goc"] != "trong" and fn(r)], n.get(g, 0), g)
    per_level = max(1, n.get("thuong_theo_cap_do", 5) // 5)
    for lv in ["N1", "N2", "N3", "N4", "N5"]:
        take([r for r in recs if r["cap_do"] == lv and not set(r["co"]) - {"thieu_cach_doc", "khong_ton_tai"}], per_level, f"thông thường {lv}")
    return [{"sample_id": r["sample_id"], "question_id": r["question_id"], "cap_do": r["cap_do"],
             "nhom": why[r["sample_id"]], "co": " ".join(r["co"])} for r in chosen]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chon-pilot", action="store_true")
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
    n_dd, _ = D.danh_dau_da_duyet(st, {r["sample_id"]: r["hash_goc"] for r in recs})   # mẫu đã có trong kho da_duyet/ → ĐÃ_DUYỆT_CTV
    st.save()

    write_csv([{"sample_id": r["sample_id"], "ruby": x} for r in recs for x in r["ruby_hong"]],
              D.OUT("reports", "ruby_hong_ban_goc.csv"), ["sample_id", "ruby"])
    write_csv([{"sample_id": r["sample_id"], "doan": x} for r in recs for x in r.get("doc_trong_ngoac", [])],
              D.OUT("reports", "doc_trong_ngoac.csv"), ["sample_id", "doan"])
    write_csv([{"sample_id": r["sample_id"], "doan_bi_bo_the": x} for r in recs for x in r["danh_dau_rac"]],
              D.OUT("reports", "danh_dau_rac.csv"), ["sample_id", "doan_bi_bo_the"])
    write_csv([{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "co": " ".join(r["co"]),
                "ghi_chu_ban_goc": "\n".join(r["ghi_chu_ban_goc"])} for r in recs if r["co"] or r["ghi_chu_ban_goc"]],
              D.OUT("reports", "co_ban_goc.csv"))

    co = collections.Counter(c for r in recs for c in r["co"])
    print(f"Đã chuẩn hóa {len(recs)} câu → {D.OUT('samples', 'norm')}")
    print(f"  có đánh dấu {{ }} trong lời giải: {sum(bool(r['marks_src']) for r in recs)} câu")
    for c, n in co.most_common():
        print(f"  cờ {c:32} {n:5}  – {D.FLAG_TEXT.get(c, '')}")
    kho = D.da_duyet_rows()
    print(f"Kho đã duyệt: {len(kho)} câu" + (f" – đánh dấu ĐÃ_DUYỆT_CTV: {n_dd}" if n_dd else ""))
    if changed:
        print(f"CHÚ Ý: {len(changed)} câu có dữ liệu gốc thay đổi so với lần chạy trước → đặt lại ĐANG_XỬ_LÝ")
    if args.chon_pilot:
        pilot = choose_pilot(recs, cfg)
        write_csv(pilot, D.OUT("pilot.csv"))
        print(f"Đã chọn {len(pilot)} câu pilot → {D.OUT('pilot.csv')}")
        for g, n in collections.Counter(p["nhom"] for p in pilot).items():
            print(f"  {g}: {n}")


if __name__ == "__main__":
    main()
