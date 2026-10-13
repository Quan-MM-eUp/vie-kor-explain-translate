"""Giai đoạn 0 – Chuẩn bị (Python, không sửa nội dung) – dạng 10 Đọc hiểu: Đoạn văn ngắn.

- Chuẩn hóa lời giải gốc: ruby → ｜…《…》; in đậm / gạch chân → { } (WF chung mục 3a); bỏ { } quanh nhãn cố định
  ('{Đoạn văn:}', '{Trích dẫn:}' …); bỏ rác HTML (span data-start, &nbsp;); giữ xuống dòng.
- Chuẩn hóa đoạn văn gốc (doan_van) – ngữ cảnh cho tác tử và để so trích dẫn (K-TD).
- Tách khung: khuôn A (phân tích từng lựa chọn) / khuôn B ('Đoạn văn:' dịch cả bài) / khuôn lẻ; gắn cờ + ghi chú [Bản gốc VI].
- Dò chữ Hán chèn giữa câu tiếng Việt (K-KC) → output/reports/kanji_chen_cau_viet.csv
- So câu trích dẫn với đoạn văn gốc (K-TD) → output/reports/trich_dan_lech.csv
- Tạo output/thu_tu_chay.csv (một lần): 100 câu đầu = 20 câu khuôn A mỗi cấp N1–N5 (xen kẽ); rồi khuôn A còn lại
  (câu chung một đoạn văn xếp liền nhau); cuối cùng khuôn B và khuôn lẻ. Cột lo_nho = câu nên chạy lô 5.
- Tạo/cập nhật output/reports/trang_thai.csv; phát hiện câu có dữ liệu gốc thay đổi (so hash).
- Báo cáo: ruby_hong_ban_goc.csv, doc_trong_ngoac.csv, danh_dau_rac.csv, co_ban_goc.csv, khuon.csv

Cách chạy (từ thư mục dạng bài):  python scripts/s0_chuan_bi.py   [--tao-lai-thu-tu]
"""
import argparse
import collections
import html as _html
import os
import random
import re

import _dang as D
from pipeline_chung.common import read_csv, save_json, sha, write_csv
from pipeline_chung.normalize import has_reserved_marks, mark_segments, normalize_html, paren_readings, pairs
from pipeline_chung.trang_thai import Status


def sach_html(s):
    """Bỏ ký tự điều khiển lạc và thẻ đóng cụt cuối chuỗi."""
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", s or "")
    s = re.sub(r"<(?=\|)", "&lt;", s)          # ký hiệu furigana hỏng '<|今;いま|' (27 câu) – giữ nguyên dạng chữ, không để bị coi là thẻ HTML
    return re.sub(r"</?[a-zA-Z]*$", "", s.rstrip())


def plain(html):
    t, b = normalize_html(sach_html(html))
    return t.replace("{", "").replace("}", ""), b


def doan_van_chuan(html):
    """Đoạn văn gốc → văn bản (giữ furigana ｜《》, bỏ { }); ảnh → '[hình]'."""
    s = re.sub(r"<img\b[^>]*>", "[hình]", sach_html(html), flags=re.I)
    return normalize_html(s)[0].replace("{", "").replace("}", "")


def prepare(row, nhom_dv):
    sid = D.sid_of(row)
    g = (row.get("giai_thich_vi") or "").strip()
    lua_chon = [plain(row.get(f"lua_chon_{i}", ""))[0] for i in range(1, 5)]
    cau_hoi, b0 = plain(row.get("cau_hoi", ""))
    dv = doan_van_chuan(row.get("doan_van", ""))
    rec = {"sample_id": sid, "question_id": int(row["question_id"]), "cau_con": int(row["cau_con"]),
           "cap_do": row["cap_do"],
           "hash_goc": sha(g + "|" + row.get("cau_hoi", "") + "|" + "|".join(lua_chon) + "|" + row["dap_an_so"] + "|" + (row.get("doan_van") or "")),
           "de": {"cau_hoi": cau_hoi, "lua_chon": lua_chon, "dap_an_so": int(row["dap_an_so"]) if row["dap_an_so"].isdigit() else row["dap_an_so"],
                  "dap_an_noi_dung": plain(row.get("dap_an_noi_dung", ""))[0], "de_bai_chung": plain(row.get("de_bai_chung", ""))[0]},
           "doan_van": dv, "nhom_doan_van": nhom_dv,
           "co": [], "ghi_chu_ban_goc": [], "ruby_hong": list(b0), "danh_dau_rac": [], "goi_y_python": []}
    if not dv.strip() or dv.strip() == "[hình]":
        rec["co"].append("doan_van_trong")
    if "<img" in (row.get("doan_van") or "").lower():
        rec["co"].append("doan_van_co_hinh")
    if len(dv) > (D.cfg().get("lo_nho") or {}).get("do_dai_doan_van", 2000):
        rec["co"].append("doan_van_dai")
    if not g:
        rec.update(khuon_goc="trong", dau_vao=None, src_text="", src_vi_text="", src_text_furi="", marks_src=[], phan=None)
        rec["ghi_chu_ban_goc"].append("[Bản gốc VI] Không có lời giải")
        return rec
    if has_reserved_marks(g):
        rec["co"].append("ky_hieu_trung")
    rac = []
    text, broken = normalize_html(sach_html(g), "u+b", rac)
    text, furi_vi = D.bo_furigana_chu_viet(text)
    text, _ = D.bo_dam_nhan(text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    phan, co, gc, goi_y = D.parse_and_flag(text, lua_chon, row["dap_an_so"], cau_hoi, dv)
    src = D.bo_nhan_trich_dan(text)
    if phan.get("khuon") == "B" and phan["b"].get("dap_an_dong"):
        # dòng 'Câu trả lời đúng là:' lặp lại nghĩa lựa chọn → JSON không chép; bỏ khỏi chuẩn đo độ phủ
        src = re.sub(r"(?ims)^\s*\{?\s*(?:Câu trả lời đúng(?: là)?|Đáp án đúng(?: là)?)\s*\}?\s*[:：][^\n]*\n?(?:[ \t]*[-•*+]?[ \t]*"
                     + re.escape(phan["b"]["dap_an_dong"]) + r"[ \t]*\n?)?", "", src)
    rec.update(khuon_goc=phan.get("khuon") or "le", dau_vao=text, src_text=src, src_vi_text=D.bo_dong_tieu_de_lua_chon(src) if phan.get("khuon") == "A" else src, src_text_furi=src,
               marks_src=mark_segments(src), phan=phan, danh_dau_rac=rac, goi_y_python=goi_y)
    rec["co"] += co
    rec["ghi_chu_ban_goc"] += gc
    if "<|" in text:
        rec["co"].append("ky_hieu_furigana_hong")
        rec["goi_y_python"].append("RAC: ký hiệu furigana hỏng của bản gốc: " + "; ".join(
            sorted({m.group(0) for m in re.finditer(r".{0,4}<\|[^\n]{0,14}", text)})[:4]))
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


def tao_thu_tu(recs, cfg):
    """100 câu đầu: 20 câu khuôn A mỗi cấp (xen kẽ N1→N5); rồi khuôn A còn lại theo file (cả nhóm đoạn văn liền nhau); cuối: khuôn B, khuôn lẻ."""
    tc = cfg.get("thu_tu_chay") or {}
    rng = random.Random(tc.get("seed", 2026))
    n = tc.get("moi_cap_do", 20)
    by_g = collections.OrderedDict()
    for r in recs:
        by_g.setdefault(r["nhom_doan_van"], []).append(r)
    nhom = list(by_g.values())

    def loai(g):
        k = {r["khuon_goc"] for r in g}
        return "B" if "B" in k else "le" if ("le" in k or "trong" in k) else "A"
    lv = {}
    for k in ["N1", "N2", "N3", "N4", "N5"]:
        pool = [g for g in nhom if loai(g) == "A" and len(g) == 1 and g[0]["cap_do"] == k]
        rng.shuffle(pool)
        lv[k] = pool[:n]
    dau = [lv[k][i] for i in range(n) for k in ["N1", "N2", "N3", "N4", "N5"] if i < len(lv[k])]
    seen = {id(g) for g in dau}
    rest = [g for g in nhom if id(g) not in seen]
    order = dau + [g for g in rest if loai(g) == "A"] + [g for g in rest if loai(g) == "B"] + [g for g in rest if loai(g) == "le"]
    lo = cfg.get("lo_nho") or {}
    out = []
    for g in order:
        for r in g:
            nho = r["khuon_goc"] == "B" or "doan_van_dai" in r["co"]
            out.append({"stt": len(out) + 1, "sample_id": r["sample_id"], "question_id": r["question_id"], "cap_do": r["cap_do"],
                        "khuon": r["khuon_goc"], "lo_nho": "x" if nho else "", "nhom_doan_van": r["nhom_doan_van"]})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tao-lai-thu-tu", action="store_true", help="tạo lại output/thu_tu_chay.csv (mặc định giữ file cũ)")
    args = ap.parse_args()
    cfg = D.cfg()
    rows = read_csv(D.data_path())
    st = Status(D.status_path())
    # nhóm đoạn văn: các câu dùng chung một đoạn văn (cùng doan_van gốc)
    key_dv = {}
    nhom_of = {}
    for row in rows:
        k = sha((row.get("doan_van") or "").strip()) if (row.get("doan_van") or "").strip() else "q" + row["question_id"]
        key_dv.setdefault(k, len(key_dv) + 1)
        nhom_of[D.sid_of(row)] = key_dv[k]
    dem = collections.Counter(nhom_of.values())
    recs, changed = [], []
    for row in rows:
        rec = prepare(row, nhom_of[D.sid_of(row)])
        if dem[rec["nhom_doan_van"]] > 1:
            rec["co"] = sorted(set(rec["co"] + ["chung_doan_van"]))
        recs.append(rec)
        save_json(rec, D.OUT("samples", "norm", rec["sample_id"] + ".json"))
        old = st.get(rec["sample_id"])
        if old and old.get("hash_goc") and old["hash_goc"] != rec["hash_goc"]:
            changed.append(rec["sample_id"])
            st.update(rec["sample_id"], trang_thai="ĐANG_XỬ_LÝ", giai_doan_loi="", loi="Dữ liệu gốc đã thay đổi – cần chạy lại từ giai đoạn 1")
        if not old or rec["sample_id"] in changed:
            st.update(rec["sample_id"], trang_thai="ĐANG_XỬ_LÝ" if rec["khuon_goc"] != "trong" else "LỖI_GĐ1",
                      giai_doan_loi="" if rec["khuon_goc"] != "trong" else "1",
                      loi="" if rec["khuon_goc"] != "trong" else "Không có lời giải gốc")
        st.update(rec["sample_id"], question_id=rec["question_id"], cau_con=rec["cau_con"], cap_do=rec["cap_do"],
                  khuon_goc=rec["khuon_goc"], co=" ".join(rec["co"]), hash_goc=rec["hash_goc"], ghi_chu_ban_goc=rec["ghi_chu_ban_goc"])
    n_dd, _ = D.danh_dau_da_duyet(st, {r["sample_id"]: r["hash_goc"] for r in recs})
    st.save()

    write_csv([{"sample_id": r["sample_id"], "ruby": x} for r in recs for x in r["ruby_hong"]],
              D.OUT("reports", "ruby_hong_ban_goc.csv"), ["sample_id", "ruby"])
    write_csv([{"sample_id": r["sample_id"], "doan": x} for r in recs for x in r.get("doc_trong_ngoac", [])],
              D.OUT("reports", "doc_trong_ngoac.csv"), ["sample_id", "doan"])
    write_csv([{"sample_id": r["sample_id"], "doan_bi_bo_the": x} for r in recs for x in r["danh_dau_rac"]],
              D.OUT("reports", "danh_dau_rac.csv"), ["sample_id", "doan_bi_bo_the"])
    write_csv([{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "doan": x[4:]} for r in recs for x in r["goi_y_python"] if x.startswith("KC:")],
              D.OUT("reports", "kanji_chen_cau_viet.csv"), ["sample_id", "cap_do", "doan"])
    write_csv([{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "goi_y": x[4:]} for r in recs for x in r["goi_y_python"] if x.startswith("TD:")],
              D.OUT("reports", "trich_dan_lech.csv"), ["sample_id", "cap_do", "goi_y"])
    write_csv([{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "khuon": r["khuon_goc"],
                "so_trich_dan": sum(len(x["quotes"]) for x in (r["phan"] or {}).get("lua_chon") or []),
                "do_dai_doan_van": len(r["doan_van"]), "do_dai_loi_giai": len(r.get("dau_vao") or "")} for r in recs],
              D.OUT("reports", "khuon.csv"))
    write_csv([{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "co": " ".join(r["co"]),
                "ghi_chu_ban_goc": "\n".join(r["ghi_chu_ban_goc"])} for r in recs if r["co"] or r["ghi_chu_ban_goc"]],
              D.OUT("reports", "co_ban_goc.csv"))

    co = collections.Counter(c for r in recs for c in r["co"])
    print(f"Đã chuẩn hóa {len(recs)} câu → {D.OUT('samples', 'norm')}")
    print("Khuôn:", dict(collections.Counter(r["khuon_goc"] for r in recs)))
    print(f"  K-KC chữ Hán chèn câu Việt: {sum(1 for r in recs if 'kanji_chen' in r['co'])} câu (output/reports/kanji_chen_cau_viet.csv)")
    print(f"  K-TD trích dẫn lệch đoạn văn: {sum(1 for r in recs if 'trich_dan_lech_doan_van' in r['co'])} câu (output/reports/trich_dan_lech.csv)")
    for c, k in co.most_common():
        print(f"  cờ {c:28} {k:5}  – {D.FLAG_TEXT.get(c, '')}")
    kho = D.da_duyet_rows()
    print(f"Kho đã duyệt: {len(kho)} câu" + (f" – đánh dấu ĐÃ_DUYỆT_CTV: {n_dd}" if n_dd else ""))
    if changed:
        print(f"CHÚ Ý: {len(changed)} câu có dữ liệu gốc thay đổi so với lần chạy trước → đặt lại ĐANG_XỬ_LÝ")
    if args.tao_lai_thu_tu or not os.path.exists(D.OUT("thu_tu_chay.csv")):
        tt = tao_thu_tu(recs, cfg)
        write_csv(tt, D.OUT("thu_tu_chay.csv"))
        print(f"Đã tạo thứ tự chạy → {D.OUT('thu_tu_chay.csv')} (100 câu đầu: {dict(collections.Counter(x['cap_do'] for x in tt[:100]))};"
              f" lô nhỏ: {sum(1 for x in tt if x['lo_nho'])} câu)")


if __name__ == "__main__":
    main()
