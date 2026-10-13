"""[Dạng 17 – Nghe hiểu điểm chính] Giai đoạn 3 – xuất Excel cho CTV tiếng Hàn (format quen thuộc + sheet chi tiết theo trường).

Chỉ đưa các câu ĐẠT. Câu LỖI_GĐ2 / CẦN_SỬA_GĐ1 ghi riêng vào output/reports/cau_loi_gd2.csv.
Cột "Ngữ liệu" = lời thoại tiếng Nhật (người nói: câu). Cột VI / KO: 【Lời thoại】 từng lượt + "→ bản dịch" (dòng then chốt in đậm),
【Câu hỏi】, 【Lựa chọn】 (✔ = đáp án, kèm lý do nếu có), 【Thông tin】, 【Đáp án】.

Cách chạy:  python3 scripts/s3_xuat_ctv.py --tu 1 --den 100      (hoặc --ids / --tat-ca)
Kết quả:    output/reports/ctv/<ngày>-CTV-17_nghe_hieu_diem_chinh.xlsx
"""
import argparse
import os

import _dang as D
from pipeline_chung.common import get_path, load_json, parse_path, read_csv, write_csv
from pipeline_chung.ctv_excel import (BASE_HEADERS, COL_CLAUDE, COL_EDIT, COL_FMT, COL_GC, COL_GOC, COL_KO, COL_KQ, COL_VI,
                                      build, html_cell, today)
from pipeline_chung.dich import build_map
from pipeline_chung.trang_thai import Status
from _dich_17 import NOTE_JA, danh_dau

MAX_CELL = 32000


def attention(row, bo_dinh_dang=True):
    items = []
    for x in (row.get("canh_bao") or "").split("\n"):
        if x.strip():
            items.append(f"[Kiểm tra tự động – dịch] {x[6:]}" if x.startswith("[GĐ2] ") else f"[Kiểm tra tự động – JSON VI] {x}")
    for x in (row.get("ghi_chu_ban_goc") or "").split("\n"):
        if x.strip().startswith("[") and not (bo_dinh_dang and x.startswith("[Đã sửa định dạng]")):
            items.append(x)
    for c in (row.get("co") or "").split():
        if c in D.CTV_FLAGS:
            items.append(f"[Kiểm tra tự động] {D.FLAG_TEXT[c]}")
    for x in (row.get("claude_da_sua_vi") or "").split("\n"):
        if x.strip() and not (bo_dinh_dang and "(sua_dinh_dang)" in x):
            items.append(f"[Claude – JSON VI] {x}")
    return "\n".join(f"- {x}" for x in items)


def goc(raw):
    return ("【LỜI THOẠI – transcript_vi】\n" + html_cell(raw.get("transcript_vi")) + "\n\n【LỜI GIẢI – giai_thich_vi】\n"
            + html_cell(raw.get("giai_thich_vi")))[:MAX_CELL]


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
            "Nhóm review": "Lời thoại, câu hỏi, lựa chọn, Thông tin dịch TRỰC TIẾP từ tiếng Nhật; lý do (nếu có) dịch từ VI JSON. Claude kiểm tra (dạng 17)",
            "Điểm cần chú ý": attention(s), "Câu hỏi": (d.get("question") or {}).get("ja"),
            "Các lựa chọn": "\n".join(f"{i + 1}. {x}" for i, x in enumerate(norm["de"]["lua_chon"])),
            "Đáp án đúng (DB)": raw["dap_an_so"], "Ngữ liệu (đoạn văn / transcript)": D.loi_thoai_text(norm)[:MAX_CELL],
            COL_VI: D.render(d, "vi"), COL_KO: ko, COL_EDIT: ko, COL_KQ: None, COL_GC: None,
            COL_CLAUDE: s.get("claude_da_sua_ko") or None,
            COL_FMT: "\n".join(x.replace("[Đã sửa định dạng] ", "", 1) for x in (s.get("ghi_chu_ban_goc") or "").split("\n")
                               if x.startswith("[Đã sửa định dạng]")) or None,
            COL_GOC: goc(raw)})
        for f in danh_dau(build_map(d), d, cfg):
            node = get_path(d, parse_path(f["path"]))
            nguon = (f"{NOTE_JA} {(f.get('nguoi_noi') + ': ') if f.get('nguoi_noi') else ''}{f['ja']}\n(VI tham khảo: {f['vi']})" if f["nguon_dich"] == "ja"
                     else f"[chép từ {f['sao_chep_tu']}] {f['ja']}" if f["nguon_dich"] == "sao_chep" else f["vi"])
            frows.append({"sample_id": sid, "question_id": int(raw["question_id"]), "Mã": f["id"], "Vị trí": f["path"],
                          "Tiếng Việt": nguon, "Tiếng Hàn hiện tại": node.get(lang)})
    guide = [
        ("Nội dung", f"Dạng 17 – Nghe hiểu điểm chính · {len(rows)} câu · tạo ngày {today()}. Lời thoại, câu hỏi, nghĩa 4 lựa chọn và dòng Thông tin: "
                     "tiếng Hàn dịch TRỰC TIẾP từ tiếng Nhật (Claude – tác tử tạo), giữ mức kính ngữ / thân mật của lời thoại; lý do chọn đáp án (nếu có) dịch từ JSON tiếng Việt. "
                     "Claude kiểm tra đã soát toàn bộ."),
        ("Nhiệm vụ", 'So bản Hàn với lời thoại tiếng Nhật (cột "Ngữ liệu") – phần lý do so với "Giải thích VI JSON mới". Chọn Kết quả; cần sửa thì sửa ở cột VÀNG "KO — CTV SỬA TẠI ĐÂY". '
                     "Bản Hàn bám tiếng Nhật nên có thể khác bản tiếng Việt – đó là chủ ý."),
        ("Kết quả", "Đạt = không cần sửa · Sửa nhỏ = đã sửa ở cột vàng · Không đạt = sai nghiêm trọng, ghi lý do ở \"Ghi chú CTV\""),
        ("Nhãn", "【Lời thoại】 mỗi lượt: 'người nói: câu Nhật' rồi '→ bản dịch'; dòng IN ĐẬM = dòng then chốt (Thông tin). 【Câu hỏi】【Lựa chọn】 (✔ = đáp án đúng) 【Thông tin】【Đáp án】. "
                 "Nhãn người nói giữ nguyên (M = nam, F = nữ; các nhãn khác như bản gốc). Dấu (i) = chỗ chứa đáp án – giữ nguyên. Chỉ sửa phần dịch, không sửa nhãn."),
        ("Furigana", "Ghi dạng 漢字《かな》 – giữ nguyên."),
        ("Sheet CHI TIẾT THEO TRƯỜNG", "Mỗi dòng là một đoạn cần dịch, cột \"Tiếng Việt\" ghi bản nguồn ([dịch từ tiếng Nhật] + câu Nhật, kèm VI tham khảo). "
                                       "CTV có thể sửa ở cột \"Bản sửa CTV\" của sheet này thay cho cột vàng ở sheet chính."),
        (COL_GOC, "Lời thoại + lời giải tiếng Việt GỐC (trước khi chuyển sang JSON), đã bỏ thẻ HTML."),
        (COL_FMT, "Mỗi dòng là một chỗ Claude sửa lỗi trình bày của bản gốc (<chỗ>: 'cũ' → 'mới' – lý do). Chỉ để tham khảo."),
        ("Cột được sửa", "Chỉ sửa ở các cột nền VÀNG. Không xóa, không đổi thứ tự cột hay đổi tên sheet."),
    ]
    os.makedirs(D.OUT("reports", "ctv"), exist_ok=True)
    out = D.OUT("reports", "ctv", f"{today()}-CTV-17_nghe_hieu_diem_chinh.xlsx")
    out = build(out, "DẠNG 17 – NGHE HIỂU ĐIỂM CHÍNH · bản dịch tiếng Hàn", guide, f"17 NGHE HIEU DIEM CHINH ({len(rows)})", rows, frows,
                heads=BASE_HEADERS + [COL_GOC, COL_FMT, COL_VI, COL_KO, COL_EDIT, COL_KQ, COL_GC])
    write_csv(errs, D.OUT("reports", "cau_loi_gd2.csv"), ["sample_id", "question_id", "trang_thai", "loi"])
    print(f"→ {out} ({len(rows)} câu ĐẠT)" + (f" | {len(errs)} câu lỗi → output/reports/cau_loi_gd2.csv" if errs else ""))


if __name__ == "__main__":
    main()
