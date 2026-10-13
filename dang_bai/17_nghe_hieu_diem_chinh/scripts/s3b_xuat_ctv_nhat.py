"""[Dạng 17] Giai đoạn 3b – Excel cho CTV TIẾNG NHẬT: các câu bị gắn cờ nghi sai nội dung (CHỜ_DUYỆT_NỘI_DUNG – chưa dịch).

Cột chính: Ngữ liệu (lời thoại Nhật) → Giải thích VI gốc → VI JSON mới → Chi tiết lỗi format đã sửa → Nghi ngờ sai nội dung →
VI — CTV SỬA TẠI ĐÂY → Kết quả → Ghi chú CTV.
Thêm --khuon-d: sheet thứ hai liệt kê các câu khuôn D (lời giải không có tiếng Việt – Q2) để CTV dịch bổ sung.

Cách chạy:  python3 scripts/s3b_xuat_ctv_nhat.py --tu 1 --den 100 [--khuon-d]
Kết quả:    output/reports/ctv/<ngày>-CTV-NHAT-17_nghe_hieu_diem_chinh-co.xlsx
"""
import argparse
import datetime
import os

import _dang as D
from pipeline_chung.claude_log import NOTE_DD
from pipeline_chung.common import load_json, read_csv
from pipeline_chung.ctv_excel import BASE_HEADERS, COL_EDIT_VI, COL_GC, COL_GOC, COL_KQ, COL_VI, _style_main, guide_sheet, rich, today
from pipeline_chung.trang_thai import Status
from s3_xuat_ctv import attention, goc

COL_ND, COL_ND_CT, COL_DD = "Nghi ngờ sai nội dung (có/không)", "Chi tiết nghi ngờ sai nội dung", "Chi tiết lỗi format đã sửa"
KET_QUA = '"Sai – đã sửa,Không sai,Khác"'


def _lines(s, prefix=None):
    out = [x for x in (s or "").split("\n") if x.strip()]
    return [x for x in out if x.startswith(prefix)] if prefix else out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--ids")
    ap.add_argument("--lo", type=int)
    ap.add_argument("--tat-ca", action="store_true")
    ap.add_argument("--khuon-d", action="store_true", help="thêm sheet các câu khuôn D (không có tiếng Việt)")
    args = ap.parse_args()
    heads = BASE_HEADERS + [COL_GOC, COL_VI, COL_DD, COL_ND, COL_ND_CT, COL_EDIT_VI, COL_KQ, COL_GC]
    st = Status(D.status_path())
    src = {D.sid_of(r): r for r in read_csv(D.data_path())}
    rows = []
    for sid in D.select_ids(args, st, ("CHỜ_DUYỆT_NỘI_DUNG", "CHỜ_XỬ_LÝ_HÁN_VIỆT")):
        r = st.get(sid) or {}
        nd = _lines(r.get("nghi_noi_dung")) + _lines(r.get("han_viet"))
        if not nd:
            continue
        raw, norm = src[sid], D.load_norm(sid)
        fp = D.OUT("json_vi", "final", sid + ".json")
        d = load_json(fp if os.path.exists(fp) else D.OUT("json_vi", "checked", sid + ".json"))
        vi = D.render(d, "vi")
        thi_thu = (raw.get("thi_thu_thuoc_de") or "").strip()
        rows.append({"question_id": int(raw["question_id"]), "câu con": int(raw["cau_con"]), "Cấp độ": raw["cap_do"],
                     "Dạng bài": raw.get("dang_bai"), "Loại đề": "Thi thử JLPT" if thi_thu else "Luyện tập",
                     "Free/Premium": (raw.get("thi_thu_mo_cho") if thi_thu else raw.get("luyen_tap_mo_cho")) or "",
                     "Nhóm review": "VI do Claude (tác tử tạo) chuyển JSON, Claude kiểm tra (dạng 17) – câu bị gắn cờ, CHƯA dịch",
                     "Điểm cần chú ý": attention(r) or None, "Ngữ liệu (đoạn văn / transcript)": D.loi_thoai_text(norm),
                     "Câu hỏi": (d.get("question") or {}).get("ja"),
                     "Các lựa chọn": "\n".join(f"{i + 1}. {x}" for i, x in enumerate(norm["de"]["lua_chon"])),
                     "Đáp án đúng (DB)": raw["dap_an_so"], COL_GOC: goc(raw), COL_VI: vi,
                     COL_DD: "\n".join(x.replace(NOTE_DD + " ", "", 1) for x in _lines(r.get("ghi_chu_ban_goc"), NOTE_DD)) or None,
                     COL_ND: "Có", COL_ND_CT: "\n".join(x.replace("[Nghi sai nội dung] ", "", 1) for x in nd),
                     COL_EDIT_VI: vi, COL_KQ: None, COL_GC: None})
    from openpyxl import Workbook
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation
    wb = Workbook()
    guide_sheet(wb.active, "DẠNG 17 – NGHE HIỂU ĐIỂM CHÍNH · CÂU BỊ GẮN CỜ (CTV tiếng Nhật)", [
        ("Nội dung", f"Dạng 17 – Nghe hiểu điểm chính · {len(rows)} câu · tạo ngày {today()}. Các câu CHƯA được dịch sang tiếng Hàn vì Claude nghi "
                     "lời giải tiếng Việt sai nội dung (dịch sai lời thoại làm sai thông tin dẫn tới đáp án, Thông tin không chứng minh đáp án, lý do sai, "
                     "đáp án đáng ngờ, lời thoại tiếng Nhật gõ sai, thiếu bản dịch…)."),
        (COL_ND_CT, "Mỗi dòng: <phần nào> (<loại lỗi>): <vì sao nghi> – đề xuất: <cách sửa Claude đề xuất>. Claude KHÔNG tự sửa."),
        ("Nhiệm vụ", f'Đối chiếu với lời thoại tiếng Nhật. Sai thật: sửa trực tiếp ở cột VÀNG "{COL_EDIT_VI}" và chọn "Sai – đã sửa". '
                     'Không sai: chọn "Không sai". Khác: chọn "Khác" và ghi ở "Ghi chú CTV".'),
        ("Cột được sửa", "Chỉ điền ở các cột nền VÀNG. Không xóa, không đổi thứ tự cột hay đổi tên sheet."),
    ] + ([("Sheet KHUÔN D", "Các câu có lời giải KHÔNG có tiếng Việt (chỉ chép lại lời thoại) – pipeline bỏ qua (Q2). CTV dịch bổ sung vào cột vàng, "
                            "sau đó nhóm dữ liệu cập nhật giai_thich_vi rồi chạy lại s0.")] if args.khuon_d else []))
    wb.active.title = "HƯỚNG DẪN"
    ws = wb.create_sheet(f"17 NGHE HIEU DIEM CHINH ({len(rows)})")
    ws.append(heads)
    for x in rows:
        ws.append([rich(x.get(h)) if isinstance(x.get(h), str) else x.get(h) for h in heads])
    _style_main(ws, heads)
    ws.data_validations.dataValidation = []
    col = get_column_letter(heads.index(COL_KQ) + 1)
    dv = DataValidation(type="list", formula1=KET_QUA, allow_blank=True)
    dv.add(f"{col}2:{col}{max(2, ws.max_row)}")
    ws.add_data_validation(dv)
    n_d = 0
    if args.khuon_d:
        hd = ["question_id", "Cấp độ", "Lời thoại (transcript_vi)", "Câu hỏi", "Các lựa chọn", "Đáp án đúng (DB)", "Bản dịch tiếng Việt – CTV ĐIỀN", "Ghi chú CTV"]
        wd = wb.create_sheet("KHUÔN D – thiếu tiếng Việt")
        wd.append(hd)
        for sid in D.thu_tu():
            n = D.load_norm(sid)
            if n.get("khuon_goc") != "D":
                continue
            raw = src[sid]
            wd.append([n["question_id"], n["cap_do"], "\n".join(n["loi_thoai_goc"]), n["de"]["cau_hoi"],
                       "\n".join(f"{i + 1}. {x}" for i, x in enumerate(n["de"]["lua_chon"])), raw["dap_an_so"], None, None])
            n_d += 1
        _style_main(wd, hd)
    os.makedirs(D.OUT("reports", "ctv"), exist_ok=True)
    out = D.OUT("reports", "ctv", f"{today()}-CTV-NHAT-17_nghe_hieu_diem_chinh-co.xlsx")
    try:
        wb.save(out)
    except PermissionError:
        base, ext = os.path.splitext(out)
        out = f"{base}-{datetime.datetime.now():%H%M%S}{ext}"
        wb.save(out)
        print(f"CHÚ Ý: file cũ đang được mở (Excel khóa) → đã lưu sang tên mới: {os.path.basename(out)}")
    print(f"→ {out} ({len(rows)} câu bị cờ" + (f", {n_d} câu khuôn D" if args.khuon_d else "") + ")")


if __name__ == "__main__":
    main()
