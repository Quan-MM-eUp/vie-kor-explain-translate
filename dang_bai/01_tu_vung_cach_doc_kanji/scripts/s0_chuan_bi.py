"""Giai đoạn 0 – Chuẩn bị (Python, không sửa nội dung).

- Phân loại khuôn lời giải gốc (json / ### / trống)
- Chuẩn hóa: ruby → ｜…《…》, <u> → { }, bỏ thẻ HTML thừa (giữ xuống dòng, danh sách "- ")
- Gắn cờ gợi ý cho từng câu (workflow chi tiết mục 3) + ghi chú [Bản gốc VI] tự động
- Tạo/cập nhật output/reports/trang_thai.csv; phát hiện câu có dữ liệu gốc thay đổi (so hash)
- Báo cáo: ruby_hong_ban_goc.csv, doc_trong_ngoac.csv, co_ban_goc.csv
- (--chon-pilot) chọn 30 câu pilot theo config → output/pilot.csv

Cách chạy (từ thư mục dạng bài):
  python scripts/s0_chuan_bi.py                 # chuẩn hóa toàn bộ 1.872 câu
  python scripts/s0_chuan_bi.py --chon-pilot    # + chọn mẫu pilot
"""
import argparse
import collections
import json
import random

import _dang as D
from pipeline_chung.common import read_csv, save_json, sha, write_csv
from pipeline_chung.normalize import has_reserved_marks, normalize_html, normalize_json, paren_readings, pairs
from pipeline_chung.trang_thai import Status

# Tạm giữ quy tắc cũ (chỉ <u> → { }) cho tới khi cập nhật dạng 01 theo WF chung mục 3a (xem workflow_chi_tiet.md mục 11)
DANH_DAU = "u"


def prepare(row):
    sid = D.sid_of(row)
    g = (row.get("giai_thich_vi") or "").strip()
    lua_chon = [normalize_html(row.get(f"lua_chon_{i}", ""), DANH_DAU)[0] for i in range(1, 5)]
    cau_hoi, b0 = normalize_html(row.get("cau_hoi", ""), DANH_DAU)
    rec = {"sample_id": sid, "question_id": int(row["question_id"]), "cau_con": int(row["cau_con"]),
           "cap_do": row["cap_do"], "hash_goc": sha(g + "|" + row.get("cau_hoi", "") + "|" + "|".join(lua_chon) + "|" + row["dap_an_so"]),
           "de": {"cau_hoi": cau_hoi, "lua_chon": lua_chon, "dap_an_so": int(row["dap_an_so"]) if row["dap_an_so"].isdigit() else row["dap_an_so"],
                  "dap_an_noi_dung": normalize_html(row.get("dap_an_noi_dung", ""), DANH_DAU)[0]},
           "co": [], "ghi_chu_ban_goc": [], "ruby_hong": list(b0)}
    if not g:
        rec.update(khuon_goc="trong", dau_vao=None, src_text="", src_vi_text="")
        rec["ghi_chu_ban_goc"].append("[Bản gốc VI] Không có lời giải")
        return rec
    if has_reserved_marks(g):
        rec["co"].append("ky_hieu_trung")
    if g.startswith("{"):
        try:
            old = json.loads(g)
        except json.JSONDecodeError:
            old = None
        if isinstance(old, dict):
            for a in old.get("answers") or []:          # note rỗng dạng {} / thiếu → ""
                if not isinstance(a.get("note"), str):
                    a["note"] = ""
            norm, broken = normalize_json(old, DANH_DAU)
            flags, ban_goc = D.flags_old_json(norm, lua_chon, row["dap_an_so"])
            rec.update(khuon_goc="json", dau_vao=norm,
                       src_text="\n".join(s for s in _strings(norm)),
                       src_vi_text=D.vi_text_old_json(norm))
            rec["co"] += flags
            rec["ghi_chu_ban_goc"] += ban_goc
            rec["ruby_hong"] += broken
    if "khuon_goc" not in rec:
        text, broken = normalize_html(g, DANH_DAU)
        rec.update(khuon_goc="###", dau_vao=text, src_text=text, src_vi_text=text)
        rec["co"].append("dang_###")
        rec["ruby_hong"] += broken
        lines = [x.strip() for x in text.split("\n")]
        qi = next((i for i, x in enumerate(lines) if x.lower().startswith("câu hỏi:")), None)
        mean = lines[qi + 1] if qi is not None and qi + 1 < len(lines) else ""
        if qi is None or "{" not in lines[qi] or (mean.lower().startswith("nghĩa:") and "{" not in mean):
            rec["co"].append("thieu_gach_chan")
    if pairs(rec["src_text"]):
        rec["co"].append("co_furigana")
    if rec["ruby_hong"]:
        rec["co"].append("ruby_hong")
        rec["ghi_chu_ban_goc"].append(f"[Bản gốc VI] Có {len(rec['ruby_hong'])} thẻ ruby hỏng")
    rec["doc_trong_ngoac"] = paren_readings(rec["src_text"])
    rec["co"] = sorted(set(rec["co"]))
    return rec


def _strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from _strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from _strings(v)


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

    for q in pc.get("cau_cu_bat_buoc", []):
        if q in by_id and by_id[q]["sample_id"] not in why:
            chosen.append(by_id[q]); why[by_id[q]["sample_id"]] = "pilot cũ (so sánh với Opus)"
    n = pc["nhom"]
    groups = {
        "nghi_don_phan_tich": lambda r: "nghi_don_phan_tich" in r["co"],
        "thieu_phan_tich_hoac_lua_chon": lambda r: {"thieu_phan_tich", "thieu_lua_chon"} & set(r["co"]),
        "lech_dap_an": lambda r: "lech_dap_an" in r["co"],
        "thieu_gach_chan": lambda r: "thieu_gach_chan" in r["co"] and r["khuon_goc"] == "json",
        "the_tu_dien": lambda r: {"the_tu_dien", "tu_dien_dinh_cach_doc"} & set(r["co"]),
        "dang_###": lambda r: r["khuon_goc"] == "###",
        "khong_ton_tai_nhieu": lambda r: "khong_ton_tai_nhieu" in r["co"],
    }
    for g, fn in groups.items():
        take([r for r in recs if fn(r)], n.get(g, 0), g)
    per_level = max(1, n.get("thuong_theo_cap_do", 10) // 5)
    for lv in ["N1", "N2", "N3", "N4", "N5"]:
        take([r for r in recs if r["cap_do"] == lv and not r["co"]], per_level, f"thông thường {lv}")
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
    n_dd, _ = D.danh_dau_da_duyet(st, {r["sample_id"]: r["hash_goc"] for r in recs})
    if n_dd:
        print(f"Đánh dấu ĐÃ_DUYỆT_CTV cho {n_dd} câu có trong kho đã duyệt (không chạy lại)")
    st.save()

    write_csv([{"sample_id": r["sample_id"], "ruby": x} for r in recs for x in r["ruby_hong"]],
              D.OUT("reports", "ruby_hong_ban_goc.csv"), ["sample_id", "ruby"])
    write_csv([{"sample_id": r["sample_id"], "doan": x} for r in recs for x in r["doc_trong_ngoac"]],
              D.OUT("reports", "doc_trong_ngoac.csv"), ["sample_id", "doan"])
    write_csv([{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "khuon_goc": r["khuon_goc"], "co": " ".join(r["co"]),
                "ghi_chu_ban_goc": "\n".join(r["ghi_chu_ban_goc"])} for r in recs if r["co"] or r["ghi_chu_ban_goc"]],
              D.OUT("reports", "co_ban_goc.csv"))

    khuon = collections.Counter(r["khuon_goc"] for r in recs)
    co = collections.Counter(c for r in recs for c in r["co"])
    print(f"Đã chuẩn hóa {len(recs)} câu → {D.cfg()['output']}/samples/norm/  | khuôn: {dict(khuon)}")
    for c, n in co.most_common():
        print(f"  cờ {c:24} {n:5}  – {D.FLAG_TEXT.get(c, '')}")
    if changed:
        print(f"CHÚ Ý: {len(changed)} câu có dữ liệu gốc thay đổi so với lần chạy trước → đặt lại ĐANG_XỬ_LÝ")
    kho = D.da_duyet_rows()
    lech = [r["sample_id"] for r in recs if r["sample_id"] in kho and kho[r["sample_id"]].get("hash_goc") != r["hash_goc"]]
    if kho:
        print(f"Kho đã duyệt: {len(kho)} câu" + (f" – CHÚ Ý: {len(lech)} câu có dữ liệu gốc đã đổi so với lúc CTV duyệt → cần duyệt lại: {lech[:10]}" if lech else " – dữ liệu gốc không đổi"))
    if args.chon_pilot:
        pilot = choose_pilot(recs, cfg)
        write_csv(pilot, D.OUT("pilot.csv"))
        print(f"Đã chọn {len(pilot)} câu pilot → {D.cfg()['output']}/pilot.csv")
        for g, n in collections.Counter(p["nhom"] for p in pilot).items():
            print(f"  {g}: {n}")


if __name__ == "__main__":
    main()
