"""Giai đoạn 0 – Chuẩn bị (Python, không sửa nội dung) – dạng 07 Ngữ pháp: Lựa chọn ngữ pháp.

- Chuẩn hóa lời giải gốc (100% văn bản ###): ruby → ｜…《…》; mọi in đậm / gạch chân → { } (WF chung mục 3a);
  bỏ nhãn in đậm, đánh dấu rác; giữ xuống dòng
- Đề gửi GPT: bỏ mọi đánh dấu (GPT chỉ theo { } của lời giải)
- Tách phần (câu đề – Cách đọc – Nghĩa / PHÂN TÍCH: Cấu trúc chung + từng lựa chọn / LỰA CHỌN ĐÚNG), gắn cờ gợi ý + ghi chú [Bản gốc VI] tự động;
  so câu 'Áp dụng vào câu' với câu đề đã điền lựa chọn (lệch nhẹ / nặng); ghép cách đọc câu đề từ furigana khi thiếu dòng 'Cách đọc:'
- Tạo output/thu_tu_chay.csv (một lần): 100 câu đầu = 20 câu mỗi cấp N1–N5, xen kẽ; rồi các câu còn lại theo file dữ liệu
- Tạo/cập nhật output/reports/trang_thai.csv; phát hiện câu có dữ liệu gốc thay đổi (so hash)
- Báo cáo: ruby_hong_ban_goc.csv, doc_trong_ngoac.csv, danh_dau_rac.csv, co_ban_goc.csv
- (--chon-pilot) chọn mẫu pilot theo config → output/pilot.csv

Cách chạy (từ thư mục dạng bài):
  python scripts/s0_chuan_bi.py                 # chuẩn hóa toàn bộ 2564 câu
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
    """Đề (kế thừa dạng 06): vài dòng có thẻ HTML bị mã hóa (&lt;p&gt;, &lt;span …&gt;) và furigana kiểu &lt;翻訳:ほんやく&gt;
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
    text, furi_vi = D.bo_furigana_chu_viet(text)   # furigana gắn lên chữ Việt (｜Nhận xét《にんてい》) – lỗi định dạng bản gốc, Python tự bỏ
    text, n_tach = D.tach_dong_cach_doc(text)       # 'Cách đọc:' dính vào cuối câu đề – lỗi định dạng bản gốc, Python tự xuống dòng
    text, gc_goc = D.sua_goc(text)                  # 2026-10-12: mã định dạng Word ở đầu lời giải (3571)
    de_raw = de_html(row.get("cau_hoi", "")) + "\x00" + "\x00".join(de_html(row.get(f"lua_chon_{i}", "")) for i in range(1, 5))
    phan, co, gc = D.parse_and_flag(text, g, lua_chon, row["dap_an_so"], de_raw)
    no_ref = D.text_without_ref(text)          # quy tắc THAM KHẢO 2026-10-07: GPT và kiểm tra không dùng phần tham khảo
    rec["ghi_chu_ban_goc"] += gc_goc
    rec.update(khuon_goc="###", dau_vao=no_ref, src_text=no_ref, src_vi_text=no_ref, src_text_furi=no_ref,   # dạng 07: LỰA CHỌN ĐÚNG cũng được chép vào JSON (correct.*)
               marks_src=mark_segments(no_ref), phan=phan, danh_dau_rac=rac)
    rec["co"] += co
    rec["ghi_chu_ban_goc"] += gc
    if n_tach:
        rec["ghi_chu_ban_goc"].append("[Python sửa định dạng] Tách dòng 'Cách đọc:' / 'Nghĩa:' bị dính vào cuối câu tiếng Nhật (xuống dòng)")
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


def choose_pilot(recs, cfg):
    pc = cfg["pilot"]
    by_id = {r["question_id"]: r for r in recs}
    out = []
    for q in pc.get("cau_bat_buoc", []):
        if q in by_id:
            r = by_id[q]
            out.append({"sample_id": r["sample_id"], "question_id": q, "cap_do": r["cap_do"], "nhom": "câu chỉ định", "co": " ".join(r["co"])})
    return out


def tao_thu_tu(recs, cfg):
    """100 câu đầu: 20 câu ngẫu nhiên mỗi cấp N1–N5 (bỏ câu không có lời giải), xen kẽ N1→N5; sau đó các câu còn lại theo file dữ liệu."""
    tc = cfg.get("thu_tu_chay") or {}
    rng = random.Random(tc.get("seed", 2026))
    n = tc.get("moi_cap_do", 20)
    lv = {}
    for k in ["N1", "N2", "N3", "N4", "N5"]:
        pool = [r for r in recs if r["cap_do"] == k and r["khuon_goc"] != "trong"]
        rng.shuffle(pool)
        lv[k] = pool[:n]
    dau = [lv[k][i] for i in range(n) for k in ["N1", "N2", "N3", "N4", "N5"] if i < len(lv[k])]
    seen = {r["sample_id"] for r in dau}
    rows = dau + [r for r in recs if r["sample_id"] not in seen]
    return [{"stt": i + 1, "sample_id": r["sample_id"], "question_id": r["question_id"], "cap_do": r["cap_do"]} for i, r in enumerate(rows)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chon-pilot", action="store_true")
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
        print(f"Gợi ý Sudachi R1 / câu áp dụng lệch đề A (output/reports/sudachi_goi_y.csv): {dict(cnt)} – trên {len({x['sample_id'] for x in goi_y})} câu")
    else:
        print("(Chưa cài SudachiPy – bỏ qua gợi ý từ điển. Cài: pip install sudachipy sudachidict_core)")
    kho = D.da_duyet_rows()
    print(f"Kho đã duyệt: {len(kho)} câu" + (f" – đánh dấu ĐÃ_DUYỆT_CTV: {n_dd}" if n_dd else ""))
    if changed:
        print(f"CHÚ Ý: {len(changed)} câu có dữ liệu gốc thay đổi so với lần chạy trước → đặt lại ĐANG_XỬ_LÝ")
    import os
    if args.tao_lai_thu_tu or not os.path.exists(D.OUT("thu_tu_chay.csv")):
        tt = tao_thu_tu(recs, cfg)
        write_csv(tt, D.OUT("thu_tu_chay.csv"))
        print(f"Đã tạo thứ tự chạy → {D.OUT('thu_tu_chay.csv')} (100 câu đầu: "
              f"{dict(collections.Counter(x['cap_do'] for x in tt[:100]))})")
    if args.chon_pilot:
        pilot = choose_pilot(recs, cfg)
        write_csv(pilot, D.OUT("pilot.csv"))
        print(f"Đã chọn {len(pilot)} câu pilot → {D.OUT('pilot.csv')}")
        for g, n in collections.Counter(p["nhom"] for p in pilot).items():
            print(f"  {g}: {n}")


if __name__ == "__main__":
    main()
