"""Giai đoạn 0 – Chuẩn bị (Python, không sửa nội dung) – dạng 12 Đọc hiểu: Đoạn văn dài.

- Chuẩn hóa lời giải gốc: ruby → ｜chữ《cách đọc》; in đậm / gạch chân → { }; giữ xuống dòng.
  Python sửa định dạng chắc chắn (ghi [Python sửa định dạng]): thu gọn chuỗi khoảng trắng / ký tự rác dài, bỏ dòng chỉ có dấu nháy '"'.
- Đề: câu hỏi, 4 lựa chọn, đáp án; ĐOẠN VĂN chuẩn hóa (doan_van – chỉ để hiểu ngữ cảnh / đối chiếu, không vào JSON).
- Nhận khuôn lời giải (scripts/_doc_hieu.py): chuan | chi_ban_dich | tu_do | trong.
  Khuôn chỉ bản dịch: bỏ bản dịch đoạn văn khỏi đầu vào (dau_vao) – vẫn giữ ở phan.ban_dich (CTV xem ở cột lời giải gốc).
- Tách khuôn chuẩn (câu hỏi / nghĩa / 4 khối: Nghĩa, Trích dẫn, Giải thích, → ĐÚNG|SAI), gắn cờ + ghi chú [Bản gốc VI] tự động;
  K-TD: so từng câu trích 「…」 với đoạn văn gốc (khop / khop_doc / lech_nhe / lech_nang / khong_tim_thay) → output/reports/trich_dan.csv
- Tạo output/thu_tu_chay.csv (một lần; --tao-lai-thu-tu để tạo lại): theo ĐOẠN VĂN, cột 'lo' = 2 đoạn / lô
- Tạo/cập nhật output/reports/trang_thai.csv; phát hiện câu có dữ liệu gốc thay đổi (so hash)

Cách chạy (từ thư mục dạng bài):  python3 scripts/s0_chuan_bi.py
"""
import argparse
import collections
import html as _html
import os
import re

import _dang as D
from pipeline_chung.common import read_csv, save_json, sha, write_csv
from pipeline_chung.normalize import has_reserved_marks, mark_segments, normalize_html, paren_readings, pairs
from pipeline_chung.trang_thai import Status

ESC_TAG_RE = re.compile(r"&lt;(/?(?:p|span|u|b|br|div|strong|ruby|rt|rp|font|em)\b.*?)&gt;", re.I)
RAC_RE = re.compile(r"[ \t　 ]{6,}")


def de_html(html):
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", html or "")
    s = re.sub(r"</?[a-zA-Z]*$", "", s.rstrip())
    return ESC_TAG_RE.sub(lambda m: "<" + _html.unescape(m.group(1)) + ">", s)


def plain(html):
    t, b = normalize_html(de_html(html))
    return t.replace("{", "").replace("}", ""), b


FURI_HONG_RE = re.compile(r"<?\|([㐀-鿿々〆ヶ]+);([぀-ゟー]+)(?:\|;?|;)?>?")      # <|着;つ|  <|昔;むかし||読;よ|>  <|心臓;しんぞう;>
MOC_HONG_RE = re.compile(r"<\|([^<>|;]{1,20})>")                                  # <|ジュース>
MOC_LE_RE = re.compile(r"<\|")


def lam_sach_raw(g):
    """Furigana viết kiểu lạ '<|漢字;よみ|' (8 câu: 12695_3, 12717_1, 12728_2, 17022_3, 17041_4 …) → ruby chuẩn; dấu '<|' lẻ bỏ đi
    (để normalize_html không coi '<|…>' là thẻ HTML và xóa mất chữ). Trả (html, ghi_chu)."""
    doi = []
    g = FURI_HONG_RE.sub(lambda m: (doi.append(f"'{m.group(0)}' → '｜{m.group(1)}《{m.group(2)}》'"),
                                    f"<ruby>{m.group(1)}<rt>{m.group(2)}</rt></ruby>")[1], g)
    g = MOC_HONG_RE.sub(lambda m: (doi.append(f"'{m.group(0)}' → '{m.group(1)}'"), m.group(1))[1], g)
    n = len(MOC_LE_RE.findall(g))
    g = MOC_LE_RE.sub("", g)
    gc = []
    if doi or n:
        gc.append("[Python sửa định dạng] Ký hiệu furigana / đánh dấu hỏng '<|…' trong lời giải gốc: " + "; ".join(doi[:8])
                  + (f"; bỏ {n} dấu '<|' lẻ" if n else ""))
    return g, gc


def lam_sach(text):
    """Sửa định dạng chắc chắn: chuỗi khoảng trắng dài (13483) → 1 dấu cách; dòng chỉ có dấu nháy '"' (53637_3, 53798_3) → bỏ."""
    gc = []
    text2, n = RAC_RE.subn(" ", text)
    if n:
        gc.append(f"[Python sửa định dạng] Thu gọn {n} chuỗi khoảng trắng dài (ký tự rác) thành một dấu cách")
    lines = text2.split("\n")
    keep = [x for x in lines if x.strip() not in ('"', '""', "“", "”")]
    if len(keep) != len(lines):
        gc.append("[Python sửa định dạng] Bỏ dòng chỉ có dấu nháy '\"' (lỗi xuất CSV)")
    return "\n".join(keep).strip(), gc


def prepare(row):
    sid = D.sid_of(row)
    g = (row.get("giai_thich_vi") or "").strip()
    lua_chon = [plain(row.get(f"lua_chon_{i}", ""))[0] for i in range(1, 5)]
    cau_hoi, b0 = plain(row.get("cau_hoi", ""))
    doan_van = normalize_html(de_html(row.get("doan_van", "")))[0]
    rec = {"sample_id": sid, "question_id": int(row["question_id"]), "cau_con": int(row["cau_con"]), "cap_do": row["cap_do"],
           "hash_goc": sha(g + "|" + row.get("cau_hoi", "") + "|" + "|".join(lua_chon) + "|" + row["dap_an_so"] + "|" + sha(row.get("doan_van", ""))),
           "de": {"cau_hoi": cau_hoi, "lua_chon": lua_chon,
                  "dap_an_so": int(row["dap_an_so"]) if row["dap_an_so"].strip().isdigit() else row["dap_an_so"],
                  "dap_an_noi_dung": plain(row.get("dap_an_noi_dung", ""))[0],
                  "de_bai_chung": plain(row.get("de_bai_chung", ""))[0]},
           "doan_van": doan_van, "co": [], "ghi_chu_ban_goc": [], "ruby_hong": list(b0), "danh_dau_rac": []}
    if not g:
        rec.update(khuon_goc="trong", dau_vao=None, src_text="", src_vi_text="", src_text_furi="", marks_src=[], phan=None)
        rec["ghi_chu_ban_goc"].append("[Bản gốc VI] Không có lời giải")
        return rec
    if has_reserved_marks(g):
        rec["co"].append("ky_hieu_trung")
    rac = []
    g_html, gc_raw = lam_sach_raw(g)
    text, broken = normalize_html(g_html, "u+b", rac)
    text, gc_sach = lam_sach(text)
    if gc_raw:
        rec["co"].append("furigana_hong")
    khuon, phan, co, gc = D.parse_and_flag(text, lua_chon, row["dap_an_so"], cau_hoi, doan_van)
    dau_vao = text
    if khuon == "chi_ban_dich":
        bd = phan["ban_dich"]
        # đầu vào cho tác tử TẠO: bỏ bản dịch đoạn văn (quyết định 2026-10-08) – giữ câu hỏi + lựa chọn + dòng đáp án
        parts = ([bd["cau_vi"]] if bd["cau_vi"] else []) + [f"{i}. {x}" for i, x in enumerate(bd["lua_chon_vi"], 1)]
        if bd["dap_an_vi"]:
            parts += ["", "Câu trả lời đúng là: " + bd["dap_an_vi"]]
        dau_vao = "\n".join(parts)
        if bd["ban_dich_doan_van"]:
            gc.append("[Python] Bản dịch đoạn văn trong lời giải gốc không đưa vào JSON (quyết định 2026-10-08) – CTV xem ở cột 'Giải thích VI gốc'")
    src = D.DH.bo_nhan_nhat(dau_vao) if khuon == "chuan" else dau_vao   # khuôn chuẩn: nhãn tiếng Nhật '｜引用《いんよう》:' … không chép vào JSON → không tính khi so tiếng Nhật / furigana
    rec.update(khuon_goc=khuon, dau_vao=dau_vao, src_text=src, src_vi_text=dau_vao, src_text_furi=src,
               marks_src=mark_segments(dau_vao), phan=phan, danh_dau_rac=rac)
    rec["co"] += co
    if gc_sach:
        rec["co"].append("ky_tu_rac" if "khoảng trắng" in gc_sach[0] else "dong_nhay_le")
        if len(gc_sach) > 1:
            rec["co"].append("dong_nhay_le")
    rec["ghi_chu_ban_goc"] += gc + gc_raw + gc_sach
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

    write_csv([{"sample_id": r["sample_id"], "ruby": x} for r in recs for x in r["ruby_hong"]],
              D.OUT("reports", "ruby_hong_ban_goc.csv"), ["sample_id", "ruby"])
    write_csv([{"sample_id": r["sample_id"], "doan_bi_bo_the": x} for r in recs for x in r["danh_dau_rac"]],
              D.OUT("reports", "danh_dau_rac.csv"), ["sample_id", "doan_bi_bo_the"])
    td = [{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "lua_chon": x["so"], "ket_qua": x["ket_qua"],
           "trich": D.strip_marks(x["ja"])[:120], "chi_tiet": x["chi_tiet"]}
          for r in recs for x in ((r.get("phan") or {}).get("trich_doan_van") or [])]
    write_csv(td, D.OUT("reports", "trich_dan.csv"), ["sample_id", "cap_do", "lua_chon", "ket_qua", "trich", "chi_tiet"])
    write_csv([{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "khuon_goc": r["khuon_goc"], "co": " ".join(r["co"]),
                "ghi_chu_ban_goc": "\n".join(r["ghi_chu_ban_goc"])} for r in recs], D.OUT("reports", "co_ban_goc.csv"))

    print(f"Đã chuẩn hóa {len(recs)} câu → {D.OUT('samples', 'norm')}")
    print("Khuôn lời giải:", dict(collections.Counter(r["khuon_goc"] for r in recs)))
    print(f"K-TD câu trích ↔ đoạn văn ({len(td)} câu trích, output/reports/trich_dan.csv):", dict(collections.Counter(x["ket_qua"] for x in td)))
    co = collections.Counter(c for r in recs for c in r["co"])
    for c, n in co.most_common():
        print(f"  cờ {c:28} {n:5}  – {D.FLAG_TEXT.get(c, '')}")
    if not D._tok():
        print("(Chưa cài SudachiPy – so câu trích theo cách đọc bị bỏ qua: pip install --user sudachipy sudachidict_core --break-system-packages)")
    kho = D.da_duyet_rows()
    print(f"Kho đã duyệt: {len(kho)} câu" + (f" – đánh dấu ĐÃ_DUYỆT_CTV: {n_dd}" if n_dd else ""))
    if changed:
        print(f"CHÚ Ý: {len(changed)} câu có dữ liệu gốc thay đổi so với lần chạy trước → đặt lại ĐANG_XỬ_LÝ")
    if args.tao_lai_thu_tu or not os.path.exists(D.OUT("thu_tu_chay.csv")):
        tt = D.tao_thu_tu_doan(recs, cfg)
        write_csv(tt, D.OUT("thu_tu_chay.csv"))
        nlo = max(x["lo"] for x in tt)
        print(f"Đã tạo thứ tự chạy → {D.OUT('thu_tu_chay.csv')}: {len(tt)} câu, {max(x['doan'] for x in tt)} đoạn, {nlo} lô; "
              f"8 đoạn đầu: {[x['cap_do'] for x in tt if x['doan'] <= 8][::4]}")


if __name__ == "__main__":
    main()
