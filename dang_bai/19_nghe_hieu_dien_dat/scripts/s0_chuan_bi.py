"""Giai đoạn 0 – Chuẩn bị (Python, không sửa nội dung) – dạng 19 Nghe hiểu diễn đạt.

- Lời giải: furigana đọc Hán Việt gắn lên chữ Hán trong câu Việt → chữ Việt ([Python sửa định dạng], Q4); ruby → ｜…《…》;
  in đậm / gạch chân → { }; tách khuôn A (### chuẩn) / B (thiếu dịch tình huống) / C (chỉ chép transcript) / D (chỉ dịch, không phân tích).
- Transcript (cột transcript_vi – thực chất là tiếng Nhật): tách câu tình huống ('… 何と言いますか') + 3 câu nói; không dùng được thì thử cột doan_van.
  Câu tình huống → prompt.utterance.ja (Python điền khi --nhan, khóa – K-TH).
- So câu nói trong lời giải với transcript (theo cách đọc – Sudachi), dòng nghĩa ở phần đầu với dòng 'Nghĩa:', kết luận ĐÚNG với đáp án.
- Câu SAI DẠNG (即時応答 N1/N2, đề 4 lựa chọn) và khuôn C → trạng thái KHÔNG_CHẠY, không vào thứ tự chạy
  (output/reports/sai_dang.csv, khong_co_loi_giai.csv).
- Tạo output/thu_tu_chay.csv (một lần): 12 câu đầu = lô pilot; tới câu 100 xen kẽ N3/N4/N5; rồi theo file dữ liệu.
- Tạo/cập nhật output/reports/trang_thai.csv; báo cáo khao_sat_s0.csv, co_ban_goc.csv, ruby_hong_ban_goc.csv, sudachi_goi_y.csv.

Cách chạy (từ thư mục dạng bài):
  python3 scripts/s0_chuan_bi.py                    # chuẩn hóa toàn bộ 406 câu
  python3 scripts/s0_chuan_bi.py --tao-lai-thu-tu   # tạo lại thứ tự chạy (CHỈ khi chưa chạy lô nào)
"""
import argparse
import collections
import os
import re

import _dang as D
from pipeline_chung.common import read_csv, save_json, sha, write_csv
from pipeline_chung.normalize import has_reserved_marks, mark_segments, normalize_html, paren_readings, pairs
from pipeline_chung.trang_thai import Status

IMG_RE = re.compile(r"<img\b[^>]*\bsrc=[\"']([^\"']+)", re.I)


def plain(html):
    t, b = normalize_html(html or "")
    return t.replace("{", "").replace("}", ""), b


def prepare(row):
    sid = D.sid_of(row)
    g = (row.get("giai_thich_vi") or "").strip()
    dap = int(row["dap_an_so"]) if row["dap_an_so"].strip().isdigit() else row["dap_an_so"]
    rec = {"sample_id": sid, "question_id": int(row["question_id"]), "cau_con": int(row["cau_con"]), "cap_do": row["cap_do"],
           "hash_goc": sha(g + "|" + (row.get("transcript_vi") or "") + "|" + row["dap_an_so"]),
           "co": [], "ghi_chu_ban_goc": [], "ruby_hong": [], "danh_dau_rac": []}
    # ---- transcript → câu tình huống + câu nói
    tr_text, b1 = plain(row.get("transcript_vi"))
    th, tr_opts, tr_gc = D.tach_transcript(tr_text)
    if th is None or len(tr_opts) < 3:
        dv_text, _ = plain(row.get("doan_van"))
        th2, op2, gc2 = D.tach_transcript(dv_text)
        if th2 and len(op2) >= 3 and D.co_nanto(th2):
            th, tr_opts, tr_gc, tr_text = th2, op2, gc2, dv_text
            rec["co"].append("tinh_huong_tu_doan_van")
    anh = IMG_RE.findall((row.get("doan_van") or "") + (row.get("cau_hoi") or "") + (row.get("transcript_vi") or ""))
    rec.update(tinh_huong_ja=th, tr_lua_chon=tr_opts, tr_ghi_chu=tr_gc, anh=anh,
               doan_van=tr_text + ("\n" + "\n".join(f"[Ảnh] {x}" for x in anh) if anh else ""),
               de={"de_bai_chung": plain(row.get("de_bai_chung"))[0], "cau_hoi": th or "", "lua_chon": tr_opts, "dap_an_so": dap})
    if anh:
        rec["co"].append("co_anh")
    if th is None:
        rec["co"].append("khong_co_tinh_huong_ja")
        rec["ghi_chu_ban_goc"].append("[Bản gốc VI] Không tìm được câu tình huống tiếng Nhật trong transcript / đoạn văn (prompt.utterance.ja = '')")
    else:
        if not D.co_nanto(th):
            rec["co"].append("tinh_huong_khong_nanto")
        if "\n" in th:
            rec["co"].append("tinh_huong_nhieu_dong")
    if len(tr_opts) != 3:
        rec["co"].append("tr_khong_du_lua_chon")
    if tr_gc:
        rec["co"].append("tr_ghi_chu")
    # ---- câu sai dạng
    sd = D.sai_dang(row)
    if sd:
        rec.update(khuon_goc="sai_dang", ly_do_khong_chay=sd, dau_vao=None, src_text="", src_vi_text="", src_text_furi="", marks_src=[], phan=None)
        return rec
    if not g:
        rec.update(khuon_goc="trong", ly_do_khong_chay="Không có lời giải", dau_vao=None, src_text="", src_vi_text="", src_text_furi="",
                   marks_src=[], phan=None)
        return rec
    if has_reserved_marks(g):
        rec["co"].append("ky_hieu_trung")
    g2, rvn = D.bo_ruby_chu_viet(g)
    if rvn:
        rec["co"].append("ruby_han_viet")
        rec["ghi_chu_ban_goc"].append("[Python sửa định dạng] Bỏ furigana đọc Hán Việt gắn lên chữ Hán trong câu tiếng Việt: "
                                      + ", ".join(f"'{a}' → '{b}'" for a, b in dict.fromkeys(rvn)))
    rac = []
    text, broken = normalize_html(g2, "u+b", rac)
    phan = D.tach_loi_giai(text)
    if phan["khuon"] == "C":
        rec.update(khuon_goc="C", ly_do_khong_chay="Lời giải chỉ chép lại transcript tiếng Nhật – không có giải thích", dau_vao=text,
                   src_text="", src_vi_text="", src_text_furi="", marks_src=[], phan=phan)
        return rec
    rec["co"] += D.gan_co(phan, tr_opts, dap if isinstance(dap, int) else None, rec["ghi_chu_ban_goc"])
    src = D.bo_dong_nghia_dau(text)
    # khuôn D: sentence.ja chép từ transcript → furigana của transcript cũng là "bản gốc" khi so furigana
    furi = src + ("\n" + "\n".join(tr_opts) if phan["khuon"] == "D" else "")
    rec.update(khuon_goc=phan["khuon"], dau_vao=text, src_text=src, src_vi_text=src, src_text_furi=furi, marks_src=mark_segments(src),
               phan=phan, danh_dau_rac=rac)
    rec["ruby_hong"] += broken + b1
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
        rec["co"] = sorted(set(rec["co"]))
        recs.append(rec)
        save_json(rec, D.OUT("samples", "norm", rec["sample_id"] + ".json"))
        chay = rec["khuon_goc"] in ("A", "B", "D")
        old = st.get(rec["sample_id"])
        if old and old.get("hash_goc") and old["hash_goc"] != rec["hash_goc"]:
            changed.append(rec["sample_id"])
        if not old or rec["sample_id"] in changed or (not chay and old.get("trang_thai") != "KHÔNG_CHẠY"):
            st.update(rec["sample_id"], trang_thai="ĐANG_XỬ_LÝ" if chay else "KHÔNG_CHẠY", giai_doan_loi="",
                      loi="" if chay else f"Không chạy ở dạng 19: {rec.get('ly_do_khong_chay')}"
                      + (" – dữ liệu gốc đã thay đổi, cần chạy lại từ giai đoạn 1" if rec["sample_id"] in changed else ""))
        notes = rec["ghi_chu_ban_goc"] + ([f"[Không chạy] {rec['ly_do_khong_chay']}"] if not chay else [])
        st.update(rec["sample_id"], question_id=rec["question_id"], cau_con=rec["cau_con"], cap_do=rec["cap_do"],
                  khuon_goc=rec["khuon_goc"], co=" ".join(rec["co"]), hash_goc=rec["hash_goc"], ghi_chu_ban_goc=notes)
    n_dd, _ = D.danh_dau_da_duyet(st, {r["sample_id"]: r["hash_goc"] for r in recs})
    st.save()

    write_csv([{"sample_id": r["sample_id"], "ruby": x} for r in recs for x in r["ruby_hong"]],
              D.OUT("reports", "ruby_hong_ban_goc.csv"), ["sample_id", "ruby"])
    write_csv([{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "ly_do": r["ly_do_khong_chay"]} for r in recs if r["khuon_goc"] == "sai_dang"],
              D.OUT("reports", "sai_dang.csv"), ["sample_id", "cap_do", "ly_do"])
    write_csv([{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "ly_do": r["ly_do_khong_chay"]} for r in recs if r["khuon_goc"] in ("C", "trong")],
              D.OUT("reports", "khong_co_loi_giai.csv"), ["sample_id", "cap_do", "ly_do"])
    write_csv([{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "khuon": r["khuon_goc"], "co": " ".join(r["co"]),
                "tinh_huong_ja": r.get("tinh_huong_ja") or "", "so_cau_noi_transcript": len(r.get("tr_lua_chon") or []),
                "so_khoi": len(((r.get("phan") or {}).get("khoi")) or []),
                "lc_vs_transcript": " ".join(f"{x['so']}:{x['ket_qua']}" for x in ((r.get("phan") or {}).get("so_transcript") or []))}
               for r in recs], D.OUT("reports", "khao_sat_s0.csv"))
    goi_y = [{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "goi_y": x} for r in recs for x in D.sudachi_hints(r)]
    write_csv(goi_y, D.OUT("reports", "sudachi_goi_y.csv"), ["sample_id", "cap_do", "goi_y"])
    write_csv([{"sample_id": r["sample_id"], "cap_do": r["cap_do"], "co": " ".join(r["co"]),
                "ghi_chu_ban_goc": "\n".join(r["ghi_chu_ban_goc"])} for r in recs if r["co"] or r["ghi_chu_ban_goc"]],
              D.OUT("reports", "co_ban_goc.csv"))

    kh = collections.Counter(r["khuon_goc"] for r in recs)
    print(f"Đã chuẩn hóa {len(recs)} câu → {D.OUT('samples', 'norm')}")
    print(f"  khuôn: {dict(kh)}  (chạy: A + B + D = {kh['A'] + kh['B'] + kh['D']}; không chạy: sai_dang {kh['sai_dang']}, C {kh['C']}, trống {kh['trong']})")
    chay = [r for r in recs if r["khuon_goc"] in ("A", "B", "D")]
    co = collections.Counter(c for r in chay for c in r["co"])
    for c, n in co.most_common():
        print(f"  cờ {c:26} {n:5}  – {D.FLAG_TEXT.get(c, '')}")
    print(f"  so câu nói lời giải ↔ transcript: {dict(collections.Counter(x['ket_qua'] for r in chay for x in (r['phan'] or {}).get('so_transcript') or []))}")
    if not D._tok():
        print("(Chưa cài SudachiPy – so theo cách đọc bị bỏ qua. Cài: pip install sudachipy sudachidict_core)")
    print(f"Kho đã duyệt: {len(D.da_duyet_rows())} câu" + (f" – đánh dấu ĐÃ_DUYỆT_CTV: {n_dd}" if n_dd else ""))
    if changed:
        print(f"CHÚ Ý: {len(changed)} câu có dữ liệu gốc thay đổi so với lần chạy trước → đặt lại ĐANG_XỬ_LÝ")
    if args.tao_lai_thu_tu or not os.path.exists(D.OUT("thu_tu_chay.csv")):
        tt = D.tao_thu_tu(recs, cfg)
        write_csv(tt, D.OUT("thu_tu_chay.csv"))
        print(f"Đã tạo thứ tự chạy → {D.OUT('thu_tu_chay.csv')}: {len(tt)} câu; lô pilot 1–12: "
              f"{[(x['sample_id'], x['cap_do'], x['khuon']) for x in tt[:12]]}; 100 câu đầu: {dict(collections.Counter(x['cap_do'] for x in tt[:100]))}")


if __name__ == "__main__":
    main()
