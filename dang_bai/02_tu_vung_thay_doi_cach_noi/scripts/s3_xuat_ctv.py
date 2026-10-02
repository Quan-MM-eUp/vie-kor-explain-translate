"""Giai đoạn 3 – xuất Excel cho CTV tiếng Hàn (format 17 cột quen thuộc + cột R "Claude đã sửa" + sheet chi tiết theo trường).

Chỉ đưa các câu ĐẠT vào file CTV. Câu LỖI_GĐ2 / CẦN_SỬA_GĐ1 được ghi riêng vào output/reports/cau_loi_gd2.csv (cho bạn xem).

Cách chạy:  python scripts/s3_xuat_ctv.py --pilot      (hoặc --ids / --tat-ca)
Kết quả:    output/reports/ctv/<ngày>-CTV-02_thay_doi_cach_noi.xlsx
"""
import argparse
import os

import _dang as D
from pipeline_chung.common import get_path, load_json, parse_path, read_csv, write_csv
from pipeline_chung.ctv_excel import COL_CLAUDE, COL_GOC, COL_KO, COL_RAW, COL_VI, build, html_cell, question_cell, today
from pipeline_chung.dich import build_map
from pipeline_chung.trang_thai import Status


def attention(row):
    items = []
    for x in (row.get("canh_bao") or "").split("\n"):
        if x.strip():
            items.append(f"[Kiểm tra tự động – dịch] {x[6:]}" if x.startswith("[GĐ2] ") else f"[Kiểm tra tự động – JSON VI] {x}")
    for x in (row.get("ghi_chu_ban_goc") or "").split("\n"):
        if x.strip():
            items.append(x)
    for c in (row.get("co") or "").split():
        if c in D.CTV_FLAGS:
            items.append(f"[Kiểm tra tự động] {D.FLAG_TEXT[c]}")
    for x in (row.get("claude_da_sua_vi") or "").split("\n"):
        if x.strip():
            items.append(f"[Claude – JSON VI] {x}")
    return "\n".join(f"- {x}" for x in items)


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
    rows, frows, errs = [], [], []
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
            "Nhóm review": "KO do GPT dịch từ JSON, Claude kiểm tra (dạng 02)", "Điểm cần chú ý": attention(s),
            "Câu hỏi": question_cell(raw["cau_hoi"]),
            "Các lựa chọn": "\n".join(f"{i + 1}. {x}" for i, x in enumerate(norm["de"]["lua_chon"])),
            "Đáp án đúng (DB)": raw["dap_an_so"], "Ngữ liệu (đoạn văn / transcript)": None,
            COL_GOC: html_cell(raw.get("giai_thich_vi"))[:32000], COL_VI: D.render(d, "vi"), COL_KO: ko, "KO — CTV SỬA TẠI ĐÂY": ko,
            "Kết quả": None, "Ghi chú CTV": None, COL_CLAUDE: s.get("claude_da_sua_ko") or None,
            COL_RAW: (raw.get("giai_thich_vi") or "")[:32000]})
        for f in build_map(d):
            node = get_path(d, parse_path(f["path"]))
            frows.append({"sample_id": sid, "question_id": int(raw["question_id"]), "Mã": f["id"], "Vị trí": f["path"],
                          "Tiếng Việt": f["vi"], "Tiếng Hàn hiện tại": node.get(lang)})
    guide = [
        ("Nội dung", f"Dạng 02 – Thay đổi cách nói · {len(rows)} câu · tạo ngày {today()}. Bản KO do GPT dịch từ JSON tiếng Việt, Claude đã kiểm tra và sửa."),
        ("Nhiệm vụ", 'So sánh "Giải thích KOR JSON mới" với "Giải thích VI JSON mới". Chọn Kết quả; cần sửa thì sửa ở cột VÀNG "KO — CTV SỬA TẠI ĐÂY".'),
        ("Kết quả", "Đạt = không cần sửa · Sửa nhỏ = đã sửa ở cột vàng · Không đạt = sai nghiêm trọng, ghi lý do ở \"Ghi chú CTV\""),
        ("Lưu ý", "KO phải bám VI. Nếu thấy chính VI sai → ghi ở Ghi chú, KHÔNG tự sửa KO theo ý mình. "
                  'Cột "Điểm cần chú ý" liệt kê chỗ kiểm tra tự động hoặc AI nghi có vấn đề – nên xem trước. '
                  'Cột "Claude đã sửa" cho biết chỗ Claude đã đổi so với bản GPT.'),
        ("Nhãn", "Nội dung tách thành các khối 【Câu hỏi】【Cách đọc câu】…【Lựa chọn 1: …】【Tham khảo】. Chỉ sửa phần chữ SAU nhãn, không sửa/xóa nhãn."),
        ("Furigana", "Ghi dạng 漢字《かな》 – giữ nguyên, không sửa."),
        ("Sheet CHI TIẾT THEO TRƯỜNG", "Mỗi dòng là một đoạn cần dịch. Nếu tiện, CTV có thể sửa ở cột \"Bản sửa CTV\" của sheet này thay cho cột vàng ở sheet chính – bản sửa ở đây đưa ngược vào dữ liệu chính xác hơn."),
        ("Cột được sửa", "Chỉ sửa ở các cột nền VÀNG. Không xóa, không đổi thứ tự cột hay đổi tên sheet."),
    ]
    os.makedirs(D.OUT("reports", "ctv"), exist_ok=True)
    out = D.OUT("reports", "ctv", f"{today()}-CTV-02_thay_doi_cach_noi.xlsx")
    build(out, "DẠNG 02 – THAY ĐỔI CÁCH NÓI · bản dịch tiếng Hàn", guide, f"02 THAY DOI CACH NOI ({len(rows)})", rows, frows)
    write_csv(errs, D.OUT("reports", "cau_loi_gd2.csv"), ["sample_id", "question_id", "trang_thai", "loi"])
    print(f"→ {out} ({len(rows)} câu ĐẠT)" + (f" | {len(errs)} câu lỗi → output/reports/cau_loi_gd2.csv" if errs else ""))


if __name__ == "__main__":
    main()
