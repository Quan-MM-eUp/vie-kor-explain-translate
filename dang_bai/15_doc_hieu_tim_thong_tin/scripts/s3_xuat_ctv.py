"""[Dạng 15 – Đọc hiểu: Tìm thông tin] Giai đoạn 3 – xuất Excel cho CTV tiếng Hàn (câu ĐẠT).

Câu xếp theo thứ tự chạy, NHÓM THEO NGỮ LIỆU: cột "Ngữ liệu" hiện ngữ liệu (đã trải bảng) ở câu con đầu tiên của nhóm,
các câu con sau ghi "(cùng ngữ liệu với <id>)". Ngữ liệu có ảnh: '[ẢNH: …]' – xem ảnh trên admin theo question_id.
Câu LỖI_GĐ2 / CẦN_SỬA_GĐ1 → output/reports/cau_loi_gd2.csv.

Cách chạy:  python3 scripts/s3_xuat_ctv.py --tu 1 --den 11
Kết quả:    output/reports/ctv/<ngày>-CTV-15_doc_hieu_tim_thong_tin.xlsx
"""
import argparse
import os

import _dang as D
from pipeline_chung.common import get_path, load_json, parse_path, read_csv, write_csv
from pipeline_chung.ctv_excel import (BASE_HEADERS, COL_CLAUDE, COL_EDIT, COL_FMT, COL_GC, COL_GOC, COL_KO, COL_KQ, COL_RAW, COL_VI,  # noqa: F401
                                      build, html_cell, today)
from pipeline_chung.dich import build_map
from pipeline_chung.trang_thai import Status
from _dich_15 import NOTE_JA, danh_dau

MAX_CELL = 32000          # Excel giới hạn 32.767 ký tự mỗi ô
TEN = "15_doc_hieu_tim_thong_tin"


def attention(row, bo_dinh_dang=False):
    items = []
    for x in (row.get("canh_bao") or "").split("\n"):
        if x.strip():
            items.append(f"[Kiểm tra tự động – dịch] {x[6:]}" if x.startswith("[GĐ2] ") else f"[Kiểm tra tự động – JSON VI] {x}")
    for x in (row.get("ghi_chu_ban_goc") or "").split("\n"):
        if x.strip() and not x.startswith("["):
            continue
        if x.strip() and not (bo_dinh_dang and x.startswith("[Đã sửa định dạng]")):
            items.append(x)
    for c in (row.get("co") or "").split():
        if c in D.CTV_FLAGS:
            items.append(f"[Kiểm tra tự động] {D.FLAG_TEXT[c]}")
    for x in (row.get("claude_da_sua_vi") or "").split("\n"):
        if x.strip() and not (bo_dinh_dang and "(sua_dinh_dang)" in x):
            items.append(f"[Claude – JSON VI] {x}")
    return "\n".join(f"- {x}" for x in items)


def goc_de_doc(raw):
    return html_cell((raw or "").strip())[:MAX_CELL]


def ngu_lieu_o(sid, norm, da_hien):
    """Ngữ liệu cho cột 'Ngữ liệu': hiện ở câu đầu tiên của nhóm, các câu sau trỏ về câu đó."""
    q = norm["question_id"]
    if q in da_hien:
        return f"(cùng ngữ liệu với {da_hien[q]})"
    da_hien[q] = sid
    return D.ngu_lieu_text(norm, MAX_CELL)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--ids")
    ap.add_argument("--lo", type=int)
    ap.add_argument("--tat-ca", action="store_true")
    args = ap.parse_args()
    cfg, lang = D.cfg(), D.cfg()["ngon_ngu_dich"]
    st = Status(D.status_path())
    src = {D.sid_of(r): r for r in read_csv(D.data_path())}
    rows, frows, errs, da_hien = [], [], [], {}
    for sid in D.select_ids(args, st, ("ĐẠT", "LỖI_GĐ2", "CẦN_SỬA_GĐ1")):
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
            "Nhóm review": "Nghĩa câu hỏi / lựa chọn / câu trích dịch TRỰC TIẾP từ tiếng Nhật; phân tích dịch từ VI JSON. Claude kiểm tra (dạng 15)",
            "Điểm cần chú ý": attention(s, bo_dinh_dang=True),
            "Câu hỏi": norm["de"]["cau_hoi"],
            "Các lựa chọn": "\n".join(f"{i + 1}. {x}" for i, x in enumerate(norm["de"]["lua_chon"])),
            "Đáp án đúng (DB)": raw["dap_an_so"], "Ngữ liệu (đoạn văn / transcript)": ngu_lieu_o(sid, norm, da_hien),
            COL_VI: D.render(d, "vi"), COL_KO: ko, COL_EDIT: ko, COL_KQ: None, COL_GC: None,
            COL_FMT: "\n".join(x.replace("[Đã sửa định dạng] ", "", 1) for x in (s.get("ghi_chu_ban_goc") or "").split("\n")
                               if x.startswith("[Đã sửa định dạng]")) or None,
            COL_GOC: goc_de_doc(raw.get("giai_thich_vi")), COL_RAW: (raw.get("giai_thich_vi") or "")[:MAX_CELL]})
        for f in danh_dau(build_map(d), d, cfg):
            node = get_path(d, parse_path(f["path"]))
            nguon = f"{NOTE_JA} {f['ja']}\n(VI tham khảo: {f['vi']})" if f["nguon_dich"] == "ja" else f["vi"]
            frows.append({"sample_id": sid, "question_id": int(raw["question_id"]), "Mã": f["id"], "Vị trí": f["path"],
                          "Tiếng Việt": nguon, "Tiếng Hàn hiện tại": node.get(lang)})
    guide = [
        ("Nội dung", f"Dạng 15 – Đọc hiểu: Tìm thông tin · {len(rows)} câu · tạo ngày {today()}. Bản tạo: Claude (tác tử tạo) – Claude kiểm tra đã soát toàn bộ. "
                     "Nghĩa câu hỏi, nghĩa từng lựa chọn và nghĩa các câu trích (Trích dẫn) – tiếng Hàn dịch TRỰC TIẾP từ tiếng Nhật; phần phân tích / tóm tắt dịch từ JSON tiếng Việt."),
        ("Nhóm câu", "Chỉ gồm câu KHÔNG có nghi vấn nội dung và KHÔNG có âm Hán Việt. Câu Dạng 2 (Claude đã sửa lỗi trình bày của lời giải gốc) có ghi ở cột 'Chi tiết lỗi format đã sửa'."),
        ("Ngữ liệu", "Cột 'Ngữ liệu' hiện ngữ liệu ở câu con đầu tiên của mỗi nhóm; bảng được trải thành dòng '| ô | ô |' (ô gộp lặp lại). '[ẢNH: …]' = ngữ liệu có ảnh – xem trên admin. Ngữ liệu không dịch."),
        ("Nhiệm vụ", 'Nghĩa câu hỏi / lựa chọn / câu trích: so với tiếng Nhật (giữ đúng số, giá, giờ, ngày). Phần phân tích: so với "Giải thích VI JSON mới". '
                     'Chọn Kết quả; cần sửa thì sửa ở cột VÀNG "KO — CTV SỬA TẠI ĐÂY".'),
        ("Kết quả", "Đạt = không cần sửa · Sửa nhỏ = đã sửa ở cột vàng · Không đạt = sai nghiêm trọng, ghi lý do ở \"Ghi chú CTV\""),
        ("Lưu ý", "Phần phân tích: KO phải bám VI – nếu thấy chính VI sai (phép tính, điều kiện, trích dẫn…) → ghi ở Ghi chú, KHÔNG tự sửa KO theo ý mình. "
                  'Cột "Điểm cần chú ý" liệt kê chỗ kiểm tra tự động hoặc AI nghi có vấn đề – nên xem trước.'),
        ("Nhãn", "Khối 【Câu hỏi】 (Nghĩa) · 【Bản dịch ngữ liệu】 (nếu có) · 1.–4.: Nghĩa / Trích dẫn 「…」 (nghĩa) / phân tích / → ĐÚNG|SAI · 【Đáp án】. Nhãn tiếng Việt giữ nguyên – chỉ sửa phần chữ."),
        ("Furigana", "Ghi dạng 漢字《かな》 – giữ nguyên, không sửa."),
        ("Sheet CHI TIẾT THEO TRƯỜNG", "Mỗi dòng là một đoạn cần dịch. Trường dịch từ tiếng Nhật ghi [dịch từ tiếng Nhật] + câu tiếng Nhật (kèm bản VI để tham khảo). "
                                       "CTV có thể sửa ở cột \"Bản sửa CTV\" của sheet này thay cho cột vàng ở sheet chính."),
        (COL_GOC, "Lời giải tiếng Việt GỐC (trước khi chuyển sang JSON), đã bỏ thẻ HTML, furigana 漢字《かな》."),
        (COL_FMT, "Mỗi dòng là một chỗ Claude sửa lỗi trình bày của lời giải gốc (<chỗ>: 'cũ' → 'mới' – lý do). Câu Dạng 1 để trống."),
        ("Cột được sửa", "Chỉ sửa ở các cột nền VÀNG. Không xóa, không đổi thứ tự cột hay đổi tên sheet."),
        ("Thứ tự cột", "Giải thích VI gốc → Chi tiết lỗi format đã sửa → Giải thích VI JSON mới → Giải thích KOR JSON mới → KO — CTV SỬA TẠI ĐÂY → Kết quả → Ghi chú CTV."),
    ]
    os.makedirs(D.OUT("reports", "ctv"), exist_ok=True)
    out = build(D.OUT("reports", "ctv", f"{today()}-CTV-{TEN}.xlsx"), "DẠNG 15 – ĐỌC HIỂU: TÌM THÔNG TIN · bản dịch tiếng Hàn", guide,
                f"15 TIM THONG TIN ({len(rows)})", rows, frows,
                heads=BASE_HEADERS + [COL_GOC, COL_FMT, COL_VI, COL_KO, COL_EDIT, COL_KQ, COL_GC])
    write_csv(errs, D.OUT("reports", "cau_loi_gd2.csv"), ["sample_id", "question_id", "trang_thai", "loi"])
    print(f"→ {out} ({len(rows)} câu ĐẠT)" + (f" | {len(errs)} câu lỗi → output/reports/cau_loi_gd2.csv" if errs else ""))


if __name__ == "__main__":
    main()
