"""[Dạng 13 – Đọc hiểu tổng hợp, 2026-10-08] Giai đoạn 3 – xuất Excel cho CTV tiếng Hàn (format cột quen thuộc + sheet chi tiết theo trường).

Chỉ đưa các câu ĐẠT vào file CTV, NHÓM THEO ĐOẠN VĂN (thứ tự output/thu_tu_chay.csv): cột "Ngữ liệu" hiện đoạn văn A / B
một lần ở câu con đầu tiên của đoạn, các câu con sau ghi "(cùng đoạn văn với câu …)". Câu LỖI_GĐ2 / CẦN_SỬA_GĐ1 → output/reports/cau_loi_gd2.csv.

Cách chạy:  python scripts/s3_xuat_ctv.py --tu A --den B      (hoặc --ids / --tat-ca)
Kết quả:    output/reports/ctv/<ngày>-CTV-13_doc_hieu_tong_hop.xlsx
"""
import argparse
import os

import _dang as D
from pipeline_chung.common import get_path, load_json, parse_path, read_csv, write_csv
from pipeline_chung.ctv_excel import (BASE_HEADERS, COL_EDIT, COL_FMT, COL_GC, COL_GOC, COL_KO, COL_KQ, COL_VI, build,  # noqa: F401
                                      html_cell, today)
from pipeline_chung.dich import build_map
from pipeline_chung.trang_thai import Status
from _dich_v3 import NOTE_JA, danh_dau

MAX_CELL = 32000


def attention(row, bo_dinh_dang=True):
    items = []
    for x in (row.get("canh_bao") or "").split("\n"):
        if x.strip():
            items.append(f"[Kiểm tra tự động – dịch] {x[6:]}" if x.startswith("[GĐ2] ") else f"[Kiểm tra tự động – JSON VI] {x}")
    for x in (row.get("ghi_chu_ban_goc") or "").split("\n"):
        if x.strip() and x.startswith("[") and not (bo_dinh_dang and x.startswith("[Đã sửa định dạng]")):
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


def ngu_lieu(norm, da_hien):
    """Đoạn văn A/B một lần cho mỗi đoạn (theo thứ tự xuất)."""
    q = norm["question_id"]
    if q in da_hien:
        return f"(cùng đoạn văn với câu {da_hien[q]})"
    da_hien[q] = norm["sample_id"]
    return (norm.get("doan_van") or "")[:MAX_CELL]


def main():
    ap = argparse.ArgumentParser()
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
            "Nhóm review": "Nghĩa câu hỏi / lựa chọn / câu trích dịch TRỰC TIẾP từ tiếng Nhật; phần nhận xét (và bản dịch đoạn văn nếu có) dịch từ VI JSON. Claude kiểm tra (dạng 13)",
            "Điểm cần chú ý": attention(s), "Câu hỏi": norm["de"]["cau_hoi"],
            "Các lựa chọn": "\n".join(f"{i + 1}. {x}" for i, x in enumerate(norm["de"]["lua_chon"])),
            "Đáp án đúng (DB)": raw["dap_an_so"], "Ngữ liệu (đoạn văn / transcript)": ngu_lieu(norm, da_hien),
            COL_GOC: goc_de_doc(raw.get("giai_thich_vi")),
            COL_FMT: "\n".join(x.replace("[Đã sửa định dạng] ", "", 1) for x in (s.get("ghi_chu_ban_goc") or "").split("\n")
                               if x.startswith("[Đã sửa định dạng]")) or None,
            COL_VI: D.render(d, "vi"), COL_KO: ko, COL_EDIT: ko, COL_KQ: None, COL_GC: None})
        for f in danh_dau(build_map(d), d, cfg):
            node = get_path(d, parse_path(f["path"]))
            nguon = f"{NOTE_JA} {f['ja']}\n(VI tham khảo: {f['vi']})" if f["nguon_dich"] == "ja" else f["vi"]
            frows.append({"sample_id": sid, "question_id": int(raw["question_id"]), "Mã": f["id"], "Vị trí": f["path"],
                          "Tiếng Việt": nguon, "Tiếng Hàn hiện tại": node.get(lang)})
    guide = [
        ("Nội dung", f"Dạng 13 – Đọc hiểu tổng hợp · {len(rows)} câu · tạo ngày {today()}. Đoạn văn A / B (cột 'Ngữ liệu', hiện một lần cho mỗi đoạn – "
                     "các câu con của cùng đoạn đứng liền nhau). Nghĩa câu hỏi, nghĩa lựa chọn và nghĩa câu trích 「…」 được dịch TRỰC TIẾP từ tiếng Nhật; "
                     "phần nhận xét dịch từ JSON tiếng Việt. Tác tử TẠO (Claude) dịch, Claude kiểm tra đã soát toàn bộ."),
        ("Nhiệm vụ", 'Nghĩa câu hỏi / lựa chọn / câu trích: so với tiếng Nhật. Phần nhận xét: so với "Giải thích VI JSON mới". '
                     'Chọn Kết quả; cần sửa thì sửa ở cột VÀNG "KO — CTV SỬA TẠI ĐÂY".'),
        ("Kết quả", "Đạt = không cần sửa · Sửa nhỏ = đã sửa ở cột vàng · Không đạt = sai nghiêm trọng, ghi lý do ở \"Ghi chú CTV\""),
        ("Lưu ý", "Phần nhận xét: KO phải bám VI – thấy chính VI sai (vd gán nhầm quan điểm A/B, câu trích không chứng minh được) → ghi ở Ghi chú, không tự sửa KO. "
                  "Câu trích giống nhau ở các câu con cùng đoạn phải dịch giống nhau. Cột \"Điểm cần chú ý\" liệt kê chỗ kiểm tra tự động / AI nghi có vấn đề."),
        ("Nhãn", "【Câu hỏi】 (Nghĩa) 【Bản dịch đoạn văn】 (nếu có) 【PHÂN TÍCH】 (1.–4.: Nghĩa, 「câu trích」 (dịch), nhận xét, → ĐÚNG./→ SAI.) 【ĐÁP ÁN】. "
                 "Nhãn và chữ kết luận giữ bằng tiếng Việt – chỉ sửa phần chữ sau nhãn. Câu trích hiện trước phần nhận xét của lựa chọn."),
        ("Furigana", "Ghi dạng 漢字《かな》 – giữ nguyên. Chữ IN ĐẬM = chỗ in đậm / gạch chân của lời giải gốc."),
        ("Sheet CHI TIẾT THEO TRƯỜNG", "Mỗi dòng là một đoạn cần dịch; dòng dịch từ tiếng Nhật ghi [dịch từ tiếng Nhật] + câu Nhật (kèm bản VI để tham khảo). "
                                       "CTV có thể sửa ở cột \"Bản sửa CTV\" của sheet này thay cho cột vàng ở sheet chính."),
        (COL_FMT, "Mỗi dòng là một chỗ Claude sửa lỗi trình bày của lời giải gốc (<chỗ>: 'cũ' → 'mới' – lý do). Câu Dạng 1 để trống."),
        ("Cột được sửa", "Chỉ sửa ở các cột nền VÀNG. Không xóa, không đổi thứ tự cột hay đổi tên sheet."),
    ]
    os.makedirs(D.OUT("reports", "ctv"), exist_ok=True)
    out = D.OUT("reports", "ctv", f"{today()}-CTV-13_doc_hieu_tong_hop.xlsx")
    out = build(out, "DẠNG 13 – ĐỌC HIỂU TỔNG HỢP · bản dịch tiếng Hàn", guide, f"13 DOC HIEU TONG HOP ({len(rows)})", rows, frows,
                heads=BASE_HEADERS + [COL_GOC, COL_FMT, COL_VI, COL_KO, COL_EDIT, COL_KQ, COL_GC])
    write_csv(errs, D.OUT("reports", "cau_loi_gd2.csv"), ["sample_id", "question_id", "trang_thai", "loi"])
    print(f"→ {out} ({len(rows)} câu ĐẠT)" + (f" | {len(errs)} câu lỗi → output/reports/cau_loi_gd2.csv" if errs else ""))


if __name__ == "__main__":
    main()
