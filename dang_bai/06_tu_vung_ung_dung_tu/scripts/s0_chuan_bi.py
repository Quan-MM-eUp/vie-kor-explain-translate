"""Giai đoạn 0 – Chuẩn bị (Python, không sửa nội dung) – dạng 06 Ứng dụng từ.

- Chuẩn hóa lời giải gốc (100% văn bản ###): ruby → ｜…《…》; mọi in đậm / gạch chân → { } (WF chung mục 3a);
  bỏ nhãn in đậm, đánh dấu rác; giữ xuống dòng
- Đề gửi GPT: bỏ mọi đánh dấu (GPT chỉ theo { } của lời giải)
- Tách phần (giới thiệu từ / PHÂN TÍCH: câu – Cách đọc – Nghĩa – nhận xét – Sửa lại / LỰA CHỌN ĐÚNG), gắn cờ gợi ý + ghi chú [Bản gốc VI] tự động
- Tạo/cập nhật output/reports/trang_thai.csv; phát hiện câu có dữ liệu gốc thay đổi (so hash)
- Báo cáo: ruby_hong_ban_goc.csv, doc_trong_ngoac.csv, danh_dau_rac.csv, co_ban_goc.csv
- (--chon-pilot) chọn mẫu pilot theo config → output/pilot.csv

Cách chạy (từ thư mục dạng bài):
  python scripts/s0_chuan_bi.py                 # chuẩn hóa toàn bộ 676 câu
  python scripts/s0_chuan_bi.py --chon-pilot    # + chọn mẫu pilot
"""
import argparse
import collections
import html as _html
import random
import re

import _dang as D
from pipeline_chung.common import read_csv, save_json, sha, write_csv
from pipeline_chung.normalize import has_reserved_marks, mark_segments, normalize_html, paren_readings, pairs
from pipeline_chung.trang_thai import Status


ESC_TAG_RE = re.compile(r"&lt;(/?(?:p|span|u|b|br|div|strong|ruby|rt|rp)\b.*?)&gt;", re.I)
FURI_DE_RE = re.compile(r"<([^<>:/\s]+):([぀-ゟ゠-ヿー]+)>")         # đề viết furigana kiểu <翻訳:ほんやく>


def de_html(html):
    """Đề dạng 06: vài dòng có thẻ HTML bị mã hóa (&lt;p&gt;, &lt;span …&gt;) và furigana kiểu &lt;翻訳:ほんやく&gt;
    → trả về HTML thật, furigana đổi sang ruby để normalize_html xử lý như lời giải."""
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", html or "")         # ký tự điều khiển lạc (\x08 ở 18335, 47225…)
    s = re.sub(r"</?[a-zA-Z]*$", "", s.rstrip())                              # thẻ đóng bị cụt ở cuối ('…ませんか。</p' – 23384)
    s = ESC_TAG_RE.sub(lambda m: "<" + _html.unescape(m.group(1)) + ">", s)
    s = s.replace("&lt;", "<").replace("&gt;", ">") if FURI_DE_RE.search(s.replace("&lt;", "<").replace("&gt;", ">")) else s
    return FURI_DE_RE.sub(r"<ruby>\1<rt>\2</rt></ruby>", s)


def plain(html):
    """Chuẩn hóa và bỏ { } (dùng cho đề / lựa chọn gửi GPT)."""
    t, b = normalize_html(de_html(html))
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
    text, gc_goc = D.sua_goc(text)        # 2026-10-12: sửa định dạng hỏng của lời giải (54075, 54146)
    rec["ghi_chu_ban_goc"] += gc_goc
    de_raw = de_html(row.get("cau_hoi", "")) + "\x00" + "\x00".join(de_html(row.get(f"lua_chon_{i}", "")) for i in range(1, 5))
    phan, co, gc = D.parse_and_flag(text, g, lua_chon, row["dap_an_so"], de_raw)
    no_lcd = D.text_without_lcd(text)
    rec.update(khuon_goc="###", dau_vao=text, src_text=no_lcd, src_vi_text=no_lcd, src_text_furi=no_lcd,   # dạng 06: dòng câu đáp án ở LỰA CHỌN ĐÚNG là bản lặp
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
    groups = {
        "bien_the_dinh_nghia": lambda r: "bien_the_dinh_nghia" in r["co"],
        "lech_dap_an": lambda r: {"lech_dap_an", "khong_so_lcd"} & set(r["co"]),
        "dinh_lien_hoac_lech": lambda r: {"dong_pt_dinh_lien", "nhan_dinh_lien", "so_dong_pt_khac_4", "thu_tu_pt_lech"} & set(r["co"]),
        "thieu_sua_lai": lambda r: "thieu_sua_lai" in r["co"],
        "co_furigana": lambda r: "co_furigana" in r["co"],
        "danh_dau_rac": lambda r: "danh_dau_rac" in r["co"],
    }
    for g, fn in groups.items():
        take([r for r in recs if r["khuon_goc"] != "trong" and fn(r)], n.get(g, 0), g)
    per_level = max(1, n.get("thuong_theo_cap_do", 4) // 4)
    for lv in ["N1", "N2", "N3", "N4"]:
        take([r for r in recs if r["cap_do"] == lv and not set(r["co"]) - {"de_gach_chan"}], per_level, f"thông thường {lv}")
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
    goi_y = [{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "goi_y": x} for r in recs for x in D.sudachi_hints(r)]
    write_csv(goi_y, D.OUT("reports", "sudachi_goi_y.csv"), ["sample_id", "cap_do", "goi_y"])
    write_csv([{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "co": " ".join(r["co"]),
                "ghi_chu_ban_goc": "\n".join(r["ghi_chu_ban_goc"])} for r in recs if r["co"] or r["ghi_chu_ban_goc"]],
              D.OUT("reports", "co_ban_goc.csv"))

    co = collections.Counter(c for r in recs for c in r["co"])
    print(f"Đã chuẩn hóa {len(recs)} câu → {D.OUT('samples', 'norm')}")
    print(f"  có đánh dấu {{ }} trong lời giải: {sum(bool(r['marks_src']) for r in recs)} câu")
    for c, n in co.most_common():
        print(f"  cờ {c:32} {n:5}  – {D.FLAG_TEXT.get(c, '')}")
    if D._tok():
        cnt = collections.Counter(x["goi_y"].split(":")[0] for x in goi_y)
        print(f"Gợi ý Sudachi R1/R2 (output/reports/sudachi_goi_y.csv): {dict(cnt)} – trên {len({x['sample_id'] for x in goi_y})} câu")
    else:
        print("(Chưa cài SudachiPy – bỏ qua gợi ý từ điển. Cài: pip install sudachipy sudachidict_core)")
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
