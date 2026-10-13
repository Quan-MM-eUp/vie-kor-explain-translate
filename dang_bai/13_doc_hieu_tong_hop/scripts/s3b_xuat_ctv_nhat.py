"""[Dạng 13 – Đọc hiểu tổng hợp, 2026-10-08] Giai đoạn 3b – xuất Excel cho CTV TIẾNG NHẬT: các câu BỊ GẮN CỜ (nghi sai nội dung / âm Hán Việt –
chưa được dịch). Nhóm theo đoạn văn; cột "Ngữ liệu" hiện đoạn văn A / B một lần cho mỗi đoạn.

Cách chạy:  python scripts/s3b_xuat_ctv_nhat.py --tu A --den B      (hoặc --ids / --tat-ca)
Kết quả:    output/reports/ctv/<ngày>-CTV-NHAT-13_doc_hieu_tong_hop-co.xlsx
"""
import argparse
import os

import _dang as D
from pipeline_chung.common import load_json, read_csv
from pipeline_chung.ctv_excel import COL_GC, COL_GOC, COL_KQ, COL_VI, _style_main, guide_sheet, rich, today  # noqa: F401
from pipeline_chung.trang_thai import Status


# ======================= Cách chia v2: file CTV tiếng Nhật cho câu BỊ CỜ =======================
#   Chỉ gồm câu có cờ nghi sai nội dung và/hoặc cờ âm Hán Việt (câu chưa được dịch).
#   Câu không cờ (kể cả Dạng 2) đi dịch và gửi CTV tiếng Hàn bằng s3_xuat_ctv.py.
COL_ND, COL_ND_CT, COL_HV, COL_DD = ("Nghi ngờ sai nội dung (có/không)", "Chi tiết nghi ngờ sai nội dung",
                                     "Từ Hán Việt (có/không)", "Chi tiết lỗi format đã sửa")
KET_QUA_V2 = '"Sai – đã sửa,Không sai,Khác"'


def _lines(s, prefix=None):
    out = [x for x in (s or "").split("\n") if x.strip()]
    return [x for x in out if x.startswith(prefix)] if prefix else out


def main_v2(args):
    from pipeline_chung.claude_log import NOTE_DD
    from pipeline_chung.ctv_excel import COL_EDIT_VI
    from pipeline_chung.ctv_excel import BASE_HEADERS
    from s3_xuat_ctv import attention, goc_de_doc, ngu_lieu
    heads = BASE_HEADERS + [COL_GOC, COL_VI, COL_DD, COL_ND, COL_ND_CT, COL_HV, COL_EDIT_VI, COL_KQ, COL_GC]
    st = Status(D.status_path())
    src = {D.sid_of(r): r for r in read_csv(D.data_path())}
    rows, da_hien = [], {}
    for sid in D.select_ids(args, st, ("CHỜ_DUYỆT_NỘI_DUNG", "CHỜ_XỬ_LÝ_HÁN_VIỆT")):
        r = st.get(sid) or {}
        nd, hv = _lines(r.get("nghi_noi_dung")), _lines(r.get("han_viet"))
        if not (nd or hv):
            continue
        raw, norm = src[sid], D.load_norm(sid)
        fp = D.OUT("json_vi", "final", sid + ".json")
        d = load_json(fp if os.path.exists(fp) else D.OUT("json_vi", "checked", sid + ".json"))
        vi = D.render(d, "vi")
        dd = _lines(r.get("ghi_chu_ban_goc"), NOTE_DD)
        thi_thu = (raw.get("thi_thu_thuoc_de") or "").strip()
        rows.append({"question_id": int(raw["question_id"]), "câu con": int(raw["cau_con"]), "Cấp độ": raw["cap_do"],
                     "Dạng bài": raw.get("dang_bai"), "Loại đề": "Thi thử JLPT" if thi_thu else "Luyện tập",
                     "Free/Premium": (raw.get("thi_thu_mo_cho") if thi_thu else raw.get("luyen_tap_mo_cho")) or "",
                     "Nhóm review": "VI do " + D.ten_ban_tao("json_vi", sid) + " chuyển JSON, Claude kiểm tra (dạng 13) – câu bị gắn cờ, CHƯA dịch",
                     "Điểm cần chú ý": attention(r, bo_dinh_dang=True) or None, "Ngữ liệu (đoạn văn / transcript)": ngu_lieu(norm, da_hien),
                     "Câu hỏi": norm["de"]["cau_hoi"],
                     "Các lựa chọn": "\n".join(f"{i + 1}. {x}" for i, x in enumerate(norm["de"]["lua_chon"])),
                     "Đáp án đúng (DB)": raw["dap_an_so"], COL_GOC: goc_de_doc(raw.get("giai_thich_vi")), COL_VI: vi,
                     COL_DD: "\n".join(x.replace(NOTE_DD + " ", "", 1) for x in dd) or None,   # Dạng 1 để trống
                     COL_ND: "Có" if nd else "Không",
                     COL_ND_CT: "\n".join(x.replace("[Nghi sai nội dung] ", "", 1) for x in nd) or "",
                     COL_HV: ("Có\n" + "\n".join(x.replace("[Âm Hán Việt] ", "", 1) for x in hv)) if hv else "Không",
                     COL_EDIT_VI: vi, COL_KQ: None, COL_GC: None})

    from openpyxl import Workbook
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation
    n_nd = sum(1 for x in rows if x[COL_ND] == "Có")
    n_hv = sum(1 for x in rows if x[COL_HV] != "Không")
    wb = Workbook()
    guide_sheet(wb.active, "DẠNG 13 – ĐỌC HIỂU TỔNG HỢP · CÂU BỊ GẮN CỜ (CTV tiếng Nhật)", [
        ("Nội dung", f"Dạng 13 – Đọc hiểu tổng hợp · {len(rows)} câu · tạo ngày {today()}. Đây là các câu CHƯA được dịch sang tiếng Hàn vì "
                     f"Claude nghi lời giải tiếng Việt sai nội dung ({n_nd} câu) và/hoặc lời giải có âm Hán Việt ({n_hv} câu)."),
        (COL_ND_CT, "Mỗi dòng là một chỗ nghi sai: <phần nào> (<loại lỗi>): <vì sao nghi> – đề xuất: <cách sửa Claude đề xuất>. Claude KHÔNG tự sửa."),
        ("Nhiệm vụ – nghi sai nội dung",
         f'Đối chiếu với câu tiếng Nhật. Nếu sai thật: sửa trực tiếp ở cột VÀNG "{COL_EDIT_VI}" (đã điền sẵn bản hiện tại) và chọn "Sai – đã sửa". '
         'Nếu không sai: chọn "Không sai" (không cần sửa). Trường hợp khác: chọn "Khác" và ghi rõ ở "Ghi chú CTV".'),
        ("Nhiệm vụ – âm Hán Việt",
         f'Chỉ cần xác nhận câu có âm Hán Việt và ghi ý kiến (nếu có) ở "Ghi chú CTV". KHÔNG sửa phần âm Hán Việt – cách xử lý chung đang chờ quyết định. '
         f'Câu chỉ có cờ Hán Việt (cột "{COL_ND}" = Không) thì không cần chọn Kết quả.'),
        (COL_DD, "Câu Dạng 2: mỗi dòng là một chỗ Claude đã sửa lỗi trình bày (dính câu, lặp từ, chính tả, xuống dòng…) khi chuyển sang JSON – "
                 "<chỗ>: 'cũ' → 'mới' – lý do. Câu Dạng 1 để trống. Thấy chỗ sửa nào sai thì ghi ở \"Ghi chú CTV\"."),
        ("Cột được sửa", "Chỉ điền ở các cột nền VÀNG. Không xóa, không đổi thứ tự cột hay đổi tên sheet."),
    ])
    wb.active.title = "HƯỚNG DẪN"
    ws = wb.create_sheet(f"13 DOC HIEU TONG HOP ({len(rows)})")
    ws.append(heads)
    for x in rows:
        ws.append([rich(x.get(h)) if isinstance(x.get(h), str) else x.get(h) for h in heads])
    _style_main(ws, heads)
    ws.data_validations.dataValidation = []
    col = get_column_letter(heads.index(COL_KQ) + 1)
    dv = DataValidation(type="list", formula1=KET_QUA_V2, allow_blank=True)
    dv.add(f"{col}2:{col}{max(2, ws.max_row)}")
    ws.add_data_validation(dv)
    for h, w in ((COL_DD, 35), (COL_ND, 12), (COL_ND_CT, 50), (COL_HV, 30), (COL_KQ, 14), (COL_GC, 40)):
        ws.column_dimensions[get_column_letter(heads.index(h) + 1)].width = w

    os.makedirs(D.OUT("reports", "ctv"), exist_ok=True)
    out = D.OUT("reports", "ctv", f"{today()}-CTV-NHAT-13_doc_hieu_tong_hop-co.xlsx")
    try:
        wb.save(out)
    except PermissionError:
        import datetime
        base, ext = os.path.splitext(out)
        out = f"{base}-{datetime.datetime.now():%H%M%S}{ext}"
        wb.save(out)
        print(f"CHÚ Ý: file cũ đang được mở (Excel khóa) → đã lưu sang tên mới: {os.path.basename(out)}")
    print(f"→ {out} ({len(rows)} câu bị cờ: {n_nd} nghi sai nội dung, {n_hv} có âm Hán Việt)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids")
    ap.add_argument("--lo", type=int)
    ap.add_argument("--tat-ca", action="store_true")
    return main_v2(ap.parse_args())


if __name__ == "__main__":
    main()
