"""Giai đoạn 3 – xuất Excel cho CTV tiếng Hàn (format 17 cột quen thuộc + cột R "Claude đã sửa" + sheet chi tiết theo trường).

Chỉ đưa các câu ĐẠT vào file CTV. Câu LỖI_GĐ2 / CẦN_SỬA_GĐ1 được ghi riêng vào output/reports/cau_loi_gd2.csv (cho bạn xem).

Cách chạy:  python scripts/s3_xuat_ctv.py --pilot      (hoặc --ids / --tu A --den B / --tat-ca)
            python scripts/s3_xuat_ctv.py --tu 1 --den 40 --dang 2   # chỉ câu Dạng 2 – Claude đã sửa lỗi bản gốc (chạy s8_phan_loai.py trước),
                        thêm cột "Thay đổi … (GĐ1)": GPT đã đổi gì, Claude sửa lỗi GPT, Claude sửa lỗi bản gốc, vấn đề bản gốc chưa sửa
Kết quả:    output/reports/ctv/<ngày>-CTV-01_cach_doc_kanji.xlsx
"""
import argparse
import os

import _dang as D
from pipeline_chung.common import get_path, load_json, parse_path, read_csv, write_csv
from pipeline_chung.ctv_excel import (B0, B1, COL_CLAUDE, COL_GD1, COL_GOC, COL_KO, COL_RAW, COL_VI, build, headers,  # noqa: F401
                                      html_cell, question_cell, today)
from pipeline_chung.dich import build_map
from pipeline_chung.trang_thai import Status


def attention(row, bo_dinh_dang=False):
    items = []
    for x in (row.get("canh_bao") or "").split("\n"):
        if x.strip():
            items.append(f"[Kiểm tra tự động – dịch] {x[6:]}" if x.startswith("[GĐ2] ") else f"[Kiểm tra tự động – JSON VI] {x}")
    for x in (row.get("ghi_chu_ban_goc") or "").split("\n"):
        if x.strip() and not (bo_dinh_dang and x.startswith("[Đã sửa định dạng]")):   # v2: đã có cột riêng
            items.append(x)
    for c in (row.get("co") or "").split():
        if c in ("nghi_don_phan_tich", "tu_dien_dinh_cach_doc", "thieu_gach_chan", "lech_dap_an"):
            items.append(f"[Kiểm tra tự động] {D.FLAG_TEXT[c]}")
    for x in (row.get("claude_da_sua_vi") or "").split("\n"):
        if x.strip() and not (bo_dinh_dang and "(sua_dinh_dang)" in x):
            items.append(f"[Claude – JSON VI] {x}")
    return "\n".join(f"- {x}" for x in items)


MAX_CELL = 32000          # Excel giới hạn 32.767 ký tự mỗi ô
OLD_KEYS = [("question", "text", "Câu hỏi"), ("question", "reading", "Cách đọc câu"), ("question", "mean", "Nghĩa câu"),
            ("question", "kanji", "Từ"), ("question", "kanji_reading", "Cách đọc từ"), ("question", "kanji_mean", "Nghĩa từ"),
            ("question", "kanji_jishokei", "Thể từ điển")]


def goc_de_doc(raw):
    """Lời giải gốc cho CTV đọc: JSON cũ → từng khóa một khối có nhãn; văn bản ### → giữ nguyên bố cục."""
    import json
    g = (raw or "").strip()
    try:
        old = json.loads(g) if g.startswith("{") else None
    except json.JSONDecodeError:
        old = None
    if not isinstance(old, dict):
        return html_cell(g)
    lab = lambda t: f"【{t}】 "  # noqa: E731   (nhãn không in đậm – chỉ định dạng chỗ bản gốc có)
    q = old.get("question") or {}
    out = [lab(f"{name} – {k}.{key}") + html_cell(str(q.get(key) or "")) for k, key, name in OLD_KEYS if (q.get(key) or "") != ""]
    out.append(lab("Đáp án đúng – correct_index / correct_answer") + f"{old.get('correct_index')}. {html_cell(str(old.get('correct_answer') or ''))}")
    for a in old.get("answers") or []:
        note = a.get("note") if isinstance(a.get("note"), str) else ""
        out.append(lab(f"Lựa chọn {a.get('index')}: {html_cell(str(a.get('answer') or ''))} – answers[].note") + (html_cell(note) or "(trống)"))
    out.append(lab("Tham khảo – reference"))
    out.append(html_cell(old.get("reference") if isinstance(old.get("reference"), str) else ""))
    return "\n".join(out)[:MAX_CELL]


def thay_doi_gd1(sid):
    """Nội dung cột S cho câu Dạng 2: vấn đề bản gốc (giữ nguyên), GPT đã đổi gì, Claude đã sửa gì ở GĐ1."""
    p = D.OUT("reports", "phan_loai", "chi_tiet", sid + ".json")
    if not os.path.exists(p):
        return None
    c = load_json(p)
    if "sua_dinh_dang" in c:          # cách chia v2: chỉ liệt kê các chỗ đã sửa định dạng (ghi chú ngắn)
        dd, ctv = c.get("da_sua_dinh_dang") or [], c.get("da_sua_theo_ctv") or []
        out = ["Đã sửa định dạng (so với lời giải gốc):"] + [f"  {x}" for x in dd] if dd else ["Không sửa định dạng."]
        if ctv:
            out += ["", "Đã sửa nội dung theo CTV tiếng Nhật:"] + [f"  {x}" for x in ctv]
        return "\n".join(out)
    ten = {"thay": "Thay", "xoa": "Bỏ", "them": "Thêm"}
    gpt = [f"- {ten[d['loai']]}: {d['goc']!r} → {d['gpt']!r} (ngữ cảnh: {d['ngu_canh']})" for d in c["gpt_so_chu"]["doi"]]
    def fmt(x):
        nhom = f"/{x['nhom']}" if x.get("nhom") else ""
        return (f"- {x['duong_dan']} [{x.get('loai') or '?'}{nhom}]: {str(x['truoc'])!r} → {str(x['sau'])!r}"
                + (f" – {x['ly_do']}" if x.get("ly_do") else ""))
    sua = c["claude_sua_vi"]
    cl_gpt = [fmt(x) for x in sua if x.get("loai") != "sua_ban_goc"]
    cl_src = [fmt(x) for x in sua if x.get("loai") == "sua_ban_goc"]
    notes = [f"  {x}" for x in c.get("da_sua_ban_goc", [])]
    bg = [f"- {x.replace('[Bản gốc VI] ', '', 1)}" for x in c["van_de_ban_goc"]]
    out = ["① GPT đã đổi so với lời giải gốc:"] + (gpt or ["- Không – GPT chép nguyên văn."])
    out += ["", "② Claude sửa lỗi của GPT (đưa JSON về đúng lời giải gốc):"] + (cl_gpt or ["- Không."])
    out += ["", "③ Claude sửa lỗi CÓ SẴN trong lời giải gốc (chính tả / cách đọc lẫn ①②③ / kiến thức) – CTV xác nhận:"]
    out += (cl_src + (["  Ghi chú:"] + notes if notes else [])) if cl_src else ["- Không."]
    out += ["", "④ Vấn đề của lời giải gốc CHƯA sửa (giữ nguyên như bản gốc – bản dịch KO bám theo bản gốc):"] + (bg or ["- Không."])
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--ids")
    ap.add_argument("--lo", type=int)
    ap.add_argument("--tat-ca", action="store_true")
    ap.add_argument("--dang", type=int, choices=(1, 2), help="chỉ xuất câu thuộc Dạng 1 hoặc 2 theo output/reports/phan_loai/phan_loai.csv")
    args = ap.parse_args()
    phan_loai = {}
    if args.dang:
        p = D.OUT("reports", "phan_loai", "phan_loai.csv")
        if not os.path.exists(p):
            raise SystemExit("Chưa có phan_loai.csv – chạy python scripts/s8_phan_loai.py … trước")
        phan_loai = {r["sample_id"]: r for r in read_csv(p)}
    cfg, lang = D.cfg(), D.cfg()["ngon_ngu_dich"]
    st = Status(D.status_path())
    src = {D.sid_of(r): r for r in read_csv(D.data_path())}
    v2 = D.cfg().get("cach_chia_dang") == "v2"
    from pipeline_chung.ctv_excel import BASE_HEADERS, COL_EDIT, COL_FMT, COL_GC, COL_KQ
    rows, frows, errs = [], [], []
    for sid in D.select_ids(args, st, ("ĐẠT", "LỖI_GĐ2", "CẦN_SỬA_GĐ1")):
        if args.dang and str((phan_loai.get(sid) or {}).get("dang")) != str(args.dang):
            continue
        s = st.get(sid)
        if s.get("trang_thai") != "ĐẠT":
            if s.get("trang_thai") in ("LỖI_GĐ2", "CẦN_SỬA_GĐ1"):
                errs.append({"sample_id": sid, "question_id": s.get("question_id"), "trang_thai": s.get("trang_thai"), "loi": s.get("loi")})
            continue
        d = load_json(D.OUT("json_ko", "final", sid + ".json"))
        raw, norm = src[sid], D.load_norm(sid)
        thi_thu = (raw.get("thi_thu_thuoc_de") or "").strip()
        ko = D.render(d, lang)
        rows.append({
            "question_id": int(raw["question_id"]), "câu con": int(raw["cau_con"]), "Cấp độ": raw["cap_do"],
            "Dạng bài": raw["dang_bai"], "Loại đề": "Thi thử JLPT" if thi_thu else "Luyện tập",
            "Free/Premium": (raw.get("thi_thu_mo_cho") if thi_thu else raw.get("luyen_tap_mo_cho")) or "",
            "Nhóm review": "KO do GPT dịch từ JSON, Claude kiểm tra (dạng 01)", "Điểm cần chú ý": attention(s, bo_dinh_dang=v2),
            "Câu hỏi": question_cell(raw["cau_hoi"]),
            "Các lựa chọn": "\n".join(f"{i + 1}. {x}" for i, x in enumerate(norm["de"]["lua_chon"])),
            "Đáp án đúng (DB)": raw["dap_an_so"], "Ngữ liệu (đoạn văn / transcript)": None,
            COL_VI: D.render(d, "vi"), COL_KO: ko, "KO — CTV SỬA TẠI ĐÂY": ko,
            "Kết quả": None, "Ghi chú CTV": None, COL_CLAUDE: s.get("claude_da_sua_ko") or None,
            COL_GD1: thay_doi_gd1(sid) if args.dang == 2 else None,
            COL_FMT: "\n".join(x.replace("[Đã sửa định dạng] ", "", 1) for x in (s.get("ghi_chu_ban_goc") or "").split("\n")
                               if x.startswith("[Đã sửa định dạng]")) or None,
            COL_GOC: goc_de_doc(raw.get("giai_thich_vi")), COL_RAW: (raw.get("giai_thich_vi") or "")[:MAX_CELL]})
        for f in build_map(d):
            node = get_path(d, parse_path(f["path"]))
            frows.append({"sample_id": sid, "question_id": int(raw["question_id"]), "Mã": f["id"], "Vị trí": f["path"],
                          "Tiếng Việt": f["vi"], "Tiếng Hàn hiện tại": node.get(lang)})
    guide = [
        ("Nội dung", f"Dạng 01 – Cách đọc kanji · {len(rows)} câu · tạo ngày {today()}. Bản KO do GPT dịch từ JSON tiếng Việt, Claude đã kiểm tra và sửa."),
        ("Nhiệm vụ", 'So sánh "Giải thích KOR JSON mới" với "Giải thích VI JSON mới" (bản tiếng Việt đã chuyển JSON – bản dịch bám theo bản này). Chọn Kết quả; cần sửa thì sửa ở cột VÀNG "KO — CTV SỬA TẠI ĐÂY".'),
        ("Kết quả", "Đạt = không cần sửa · Sửa nhỏ = đã sửa ở cột vàng · Không đạt = sai nghiêm trọng, ghi lý do ở \"Ghi chú CTV\""),
        ("Lưu ý", "KO phải bám VI. Nếu thấy chính VI sai → ghi ở Ghi chú, KHÔNG tự sửa KO theo ý mình. "
                  'Cột "Điểm cần chú ý" liệt kê chỗ kiểm tra tự động hoặc AI nghi có vấn đề – nên xem trước. '
                  ),
        ("Nhãn", "Nội dung tách thành các khối 【Câu hỏi】【Cách đọc câu】…【Lựa chọn 1: …】【Tham khảo】. Chỉ sửa phần chữ SAU nhãn, không sửa/xóa nhãn."),
        ("Furigana", "Ghi dạng 漢字《かな》 – giữ nguyên, không sửa."),
        ("Sheet CHI TIẾT THEO TRƯỜNG", "Mỗi dòng là một đoạn cần dịch. Nếu tiện, CTV có thể sửa ở cột \"Bản sửa CTV\" của sheet này thay cho cột vàng ở sheet chính – bản sửa ở đây đưa ngược vào dữ liệu chính xác hơn."),
        ("Cột được sửa", "Chỉ sửa ở các cột nền VÀNG. Không xóa, không đổi thứ tự cột hay đổi tên sheet."),
    ]
    guide.append((COL_GOC, "Lời giải tiếng Việt GỐC (trước khi chuyển sang JSON), đã bỏ thẻ HTML: gạch chân / in đậm hiển thị thật, furigana 漢字《かな》; "
                           "lời giải kiểu JSON cũ được tách theo từng khóa (vd 【Câu hỏi – question.text】). Dùng để đối chiếu với \"Giải thích VI JSON mới\"."))
    if v2 and not args.dang:
        guide.insert(1, ("Nhóm câu", "Gồm cả câu DẠNG 1 (lời giải gốc không sai định dạng – cột 'Chi tiết lỗi format đã sửa' để trống) và DẠNG 2 "
                                     "(lời giải gốc có lỗi định dạng như dính câu, thiếu xuống dòng, lặp từ, chính tả… và Claude đã sửa – từng chỗ ghi ở cột đó). "
                                     "Mọi câu đều KHÔNG có nghi vấn nội dung và KHÔNG có âm Hán Việt."))
    if v2 and args.dang:
        guide.insert(1, ("Nhóm câu", {1: "Câu DẠNG 1 (cách chia v2): lời giải gốc không sai định dạng; không có nghi vấn nội dung, không có âm Hán Việt.",
                                      2: "Câu DẠNG 2 (cách chia v2): lời giải gốc có lỗi định dạng (dính chữ, thiếu xuống dòng, lặp từ, chính tả…) "
                                         "và Claude đã sửa – từng chỗ sửa ghi ở cột 'Chi tiết lỗi format đã sửa'. Không có nghi vấn nội dung, không có âm Hán Việt."}[args.dang]))
    if v2:
        guide.append((COL_FMT, "Ngay trước \"Giải thích VI JSON mới\": mỗi dòng là một chỗ Claude sửa lỗi trình bày của lời giải gốc "
                               "(<chỗ>: 'cũ' → 'mới' – lý do). Câu Dạng 1 để trống. Chỉ để tham khảo – thấy sửa sai thì ghi ở \"Ghi chú CTV\"."))
    elif args.dang == 2:
        guide.insert(1, ("Nhóm câu", "Chỉ gồm câu DẠNG 2: lời giải gốc có lỗi (chính tả / cách đọc lẫn ①②③ / kiến thức) và Claude ĐÃ SỬA khi chuyển sang JSON; "
                                     "bản VI JSON mới và bản KO theo nội dung đã sửa. Kết quả cuối đạt kiểm tra tự động."))
        guide.append((COL_GD1, "Cột ngay sau \"Ghi chú CTV\" (nền xám, chỉ để tham khảo): ① GPT đã đổi gì so với lời giải gốc; ② Claude sửa lỗi của GPT; "
                               "③ Claude sửa lỗi CÓ SẴN trong lời giải gốc (cũ → mới, lý do) – CTV xem chỗ sửa có đúng không, không đúng thì ghi ở \"Ghi chú CTV\"; "
                               "④ Vấn đề của lời giải gốc chưa sửa (Claude không chắc chắn) – giữ nguyên, bản KO bám theo."))
    elif args.dang == 1:
        guide.insert(1, ("Nhóm câu", "Chỉ gồm câu DẠNG 1: Claude không sửa lỗi nào của lời giải gốc; bản VI JSON mới giữ đúng nội dung bản gốc. "
                                     "Nếu có chỗ nghi vấn của bản gốc (chưa sửa vì không chắc chắn) thì ghi ở cột \"Điểm cần chú ý\" với nhãn [Bản gốc VI]."))
    guide.append(("Thứ tự cột", "Giải thích VI gốc → " + ("Chi tiết lỗi format đã sửa → " if v2 else "") + "Giải thích VI JSON mới → Giải thích KOR JSON mới → KO — CTV SỬA TẠI ĐÂY → Kết quả → Ghi chú CTV"
                                + (" → Thay đổi so với lời giải gốc (GĐ1)" if args.dang == 2 and not v2 else "") + "."))
    suffix = f"-dang{args.dang}" if args.dang else ""
    os.makedirs(D.OUT("reports", "ctv"), exist_ok=True)
    out = D.OUT("reports", "ctv", f"{today()}-CTV-01_cach_doc_kanji{suffix}.xlsx")
    out = build(out, "DẠNG 01 – CÁCH ĐỌC KANJI · bản dịch tiếng Hàn" + (f" · DẠNG {args.dang}" if args.dang else ""), guide,
          f"01 CACH DOC KANJI ({len(rows)})", rows, frows,
          heads=(BASE_HEADERS + [COL_GOC, COL_FMT, COL_VI, COL_KO, COL_EDIT, COL_KQ, COL_GC]) if v2 else headers(gd1=args.dang == 2))
    if not args.dang:          # file lọc theo dạng không ghi đè danh sách câu lỗi
        write_csv(errs, D.OUT("reports", "cau_loi_gd2.csv"), ["sample_id", "question_id", "trang_thai", "loi"])
    print(f"→ {out} ({len(rows)} câu ĐẠT)" + (f" | {len(errs)} câu lỗi → output/reports/cau_loi_gd2.csv" if errs else ""))


if __name__ == "__main__":
    main()
