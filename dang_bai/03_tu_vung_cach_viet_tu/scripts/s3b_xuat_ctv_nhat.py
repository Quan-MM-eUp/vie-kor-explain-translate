"""Giai đoạn 3b – xuất Excel cho CTV TIẾNG NHẬT kiểm tra các chỗ Claude sửa lỗi bản gốc khi chuyển sang JSON.

Gồm mọi câu có dang_gd1 = 2 (Claude sửa lỗi bản gốc ở GĐ1), kể cả câu đang là Dạng 3 vì lỗi Hán Việt ở GĐ2 –
JSON tiếng Việt của các câu này đã chốt, không phụ thuộc bản dịch tiếng Hàn.

Không có bản dịch tiếng Hàn. Cột chính: Giải thích VI gốc → Giải thích VI JSON mới → Thay đổi … (GĐ1) → Kết quả → Ghi chú CTV.
Cột "Thay đổi … (GĐ1)" chỉ ghi ngắn gọn:
  Ghi chú:  các dòng [Đã sửa bản gốc] (chỗ Claude đã sửa – CTV xác nhận)
  Chưa sửa: các dòng [Bản gốc VI] (Claude nghi sai nhưng không chắc nên giữ nguyên – CTV cho ý kiến)

Cách chạy:  python scripts/s3b_xuat_ctv_nhat.py --tu 1 --den 30     (chạy s8_phan_loai.py trước)
Kết quả:    output/reports/ctv/<ngày>-CTV-NHAT-03_cach_viet_tu-dang2.xlsx
"""
import argparse
import os

import _dang as D
from pipeline_chung.common import load_json, read_csv
from pipeline_chung.ctv_excel import COL_GC, COL_GD1, COL_GOC, COL_KQ, COL_VI, _style_main, guide_sheet, question_cell, rich, today
from pipeline_chung.trang_thai import Status
from s3_xuat_ctv import goc_de_doc

HEADS = ["question_id", "câu con", "Cấp độ", "Câu hỏi", "Các lựa chọn", "Đáp án đúng (DB)",
         COL_GOC, COL_VI, COL_GD1, COL_KQ, COL_GC]
KET_QUA = '"Đồng ý,Đồng ý một phần,Không đồng ý"'


def thay_doi_v2(c):
    dd, nd = c.get("da_sua_dinh_dang") or [], c.get("nghi_noi_dung") or []
    out = (["Đã sửa định dạng:"] + [f"  {x}" for x in dd]) if dd else ["Đã sửa định dạng: (không có)"]
    if nd:
        out += ["", "NGHI SAI NỘI DUNG – CTV xác nhận (câu chưa được dịch):"] + [f"  {x}" for x in nd]
    if c.get("da_sua_theo_ctv"):
        out += ["", "Đã sửa nội dung theo CTV:"] + [f"  {x}" for x in c["da_sua_theo_ctv"]]
    return "\n".join(out)


def thay_doi_ngan(sid):
    p = D.OUT("reports", "phan_loai", "chi_tiet", sid + ".json")
    c = load_json(p) if os.path.exists(p) else {}
    if "sua_dinh_dang" in c:
        return thay_doi_v2(c)
    sua = c.get("da_sua_ban_goc") or []
    nghi = c.get("van_de_ban_goc") or []
    out = ["Ghi chú:"] + [f"  {x}" for x in sua] if sua else ["Ghi chú: (không có)"]
    if nghi:
        out += ["", "Chưa sửa – Claude nghi sai nhưng không chắc, giữ nguyên như bản gốc (CTV cho ý kiến):"] + [f"  {x}" for x in nghi]
    return "\n".join(out)


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
    from s3_xuat_ctv import attention
    heads = BASE_HEADERS + [COL_GOC, COL_VI, COL_DD, COL_ND, COL_ND_CT, COL_HV, COL_EDIT_VI, COL_KQ, COL_GC]
    st = Status(D.status_path())
    src = {D.sid_of(r): r for r in read_csv(D.data_path())}
    rows = []
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
                     "Nhóm review": "VI do GPT chuyển JSON, Claude kiểm tra (dạng 03) – câu bị gắn cờ, CHƯA dịch",
                     "Điểm cần chú ý": attention(r, bo_dinh_dang=True) or None, "Ngữ liệu (đoạn văn / transcript)": None,
                     "Câu hỏi": question_cell(raw["cau_hoi"]),
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
    guide_sheet(wb.active, "DẠNG 03 – CÁCH VIẾT TỪ · CÂU BỊ GẮN CỜ (CTV tiếng Nhật)", [
        ("Nội dung", f"Dạng 03 – Cách viết từ · {len(rows)} câu · tạo ngày {today()}. Đây là các câu CHƯA được dịch sang tiếng Hàn vì "
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
    ws = wb.create_sheet(f"03 CACH VIET TU ({len(rows)})")
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
    out = D.OUT("reports", "ctv", f"{today()}-CTV-NHAT-03_cach_viet_tu-co.xlsx")
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
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--ids")
    ap.add_argument("--lo", type=int)
    ap.add_argument("--tat-ca", action="store_true")
    args = ap.parse_args()
    if D.cfg().get("cach_chia_dang") == "v2":
        return main_v2(args)
    p = D.OUT("reports", "phan_loai", "phan_loai.csv")
    if not os.path.exists(p):
        raise SystemExit("Chưa có phan_loai.csv – chạy python scripts/s8_phan_loai.py … trước")
    v2 = D.cfg().get("cach_chia_dang") == "v2"
    pl = {r["sample_id"]: r for r in read_csv(p)}
    if v2:      # cách chia v2: câu Dạng 2 (đã sửa định dạng) + mọi câu nghi sai nội dung
        dang = {k: "2" if (r.get("dang") == "2" or r.get("co_nghi_noi_dung")) else "1" for k, r in pl.items()}
    else:
        dang = {k: r.get("dang_gd1") for k, r in pl.items()}   # xét GĐ1: gồm cả câu Dạng 3 có dang_gd1 = 2
    st = Status(D.status_path())
    src = {D.sid_of(r): r for r in read_csv(D.data_path())}
    rows = []
    for sid in D.select_ids(args, st, ("ĐẠT", "LỖI_GĐ2") + (("GĐ1_XONG", "CHỜ_DUYỆT_NỘI_DUNG", "CHỜ_XỬ_LÝ_HÁN_VIỆT") if v2 else ())):
        if str(dang.get(sid)) != "2":
            continue
        raw, norm = src[sid], D.load_norm(sid)
        fp = D.OUT("json_vi", "final", sid + ".json")
        d = load_json(fp if os.path.exists(fp) else D.OUT("json_vi", "checked", sid + ".json"))   # câu bị chặn chưa có bản final
        rows.append({"question_id": int(raw["question_id"]), "câu con": int(raw["cau_con"]), "Cấp độ": raw["cap_do"],
                     "Câu hỏi": question_cell(raw["cau_hoi"]),
                     "Các lựa chọn": "\n".join(f"{i + 1}. {x}" for i, x in enumerate(norm["de"]["lua_chon"])),
                     "Đáp án đúng (DB)": raw["dap_an_so"],
                     COL_GOC: goc_de_doc(raw.get("giai_thich_vi")), COL_VI: D.render(d, "vi"),
                     COL_GD1: thay_doi_ngan(sid), COL_KQ: None, COL_GC: None})

    from openpyxl import Workbook
    from openpyxl.worksheet.datavalidation import DataValidation
    from openpyxl.utils import get_column_letter
    wb = Workbook()
    guide_sheet(wb.active, "DẠNG 03 – CÁCH VIẾT TỪ · KIỂM TRA CHỖ SỬA BẢN GỐC (CTV tiếng Nhật)", [
        ("Nội dung", f"Dạng 03 – Cách viết từ · {len(rows)} câu · tạo ngày {today()}. Đây là các câu mà lời giải tiếng Việt gốc có lỗi "
                     "(chính tả, cách đọc bị lẫn số ①②③, kiến thức…) và Claude đã sửa khi chuyển sang JSON."),
        ("Nhiệm vụ", f'Đối chiếu "{COL_GOC}" với "{COL_VI}" và đọc cột "{COL_GD1}": xác nhận từng chỗ sửa ([Đã sửa định dạng] / [Đã sửa bản gốc]) có đúng không; '
                     "cho ý kiến về các chỗ Claude nghi sai ([Nghi sai nội dung] / [Bản gốc VI]) – nếu sai thật, ghi cách sửa ở \"Ghi chú CTV\". "
                     "Câu [Nghi sai nội dung] chưa được dịch, chờ ý kiến CTV."),
        ("Kết quả", "Đồng ý = mọi chỗ sửa đều đúng · Đồng ý một phần = có chỗ sửa chưa đúng/thiếu · Không đồng ý = các chỗ sửa sai. "
                    "Trường hợp 2 và 3 ghi rõ chỗ nào và nên sửa thế nào ở \"Ghi chú CTV\"."),
        (COL_GOC, "Lời giải tiếng Việt gốc (trước khi sửa), đã bỏ thẻ HTML: gạch chân / in đậm hiển thị đúng như bản gốc, furigana dạng 漢字《かな》."),
        (COL_VI, "Lời giải sau khi chuyển sang JSON – đã sửa các lỗi ghi ở cột bên cạnh. Gạch chân = chỗ gạch chân của bản gốc."),
        (COL_GD1, "Ghi chú: mỗi dòng [Đã sửa bản gốc] là một chỗ sửa (vị trí: 'cũ' → 'mới' – lý do). "
                  "Chưa sửa: các dòng [Bản gốc VI] – Claude nghi có vấn đề nhưng không chắc nên giữ nguyên."),
        ("Cột được sửa", "Chỉ điền ở các cột nền VÀNG (Kết quả, Ghi chú CTV). Không xóa, không đổi thứ tự cột hay đổi tên sheet."),
    ])
    wb.active.title = "HƯỚNG DẪN"
    ws = wb.create_sheet(f"03 CACH VIET TU ({len(rows)})")
    ws.append(HEADS)
    for r in rows:
        ws.append([rich(r.get(h)) if isinstance(r.get(h), str) else r.get(h) for h in HEADS])
    _style_main(ws, HEADS)
    ws.data_validations.dataValidation = []
    col = get_column_letter(HEADS.index(COL_KQ) + 1)
    dv = DataValidation(type="list", formula1=KET_QUA, allow_blank=True)
    dv.add(f"{col}2:{col}{max(2, ws.max_row)}")
    ws.add_data_validation(dv)
    for h, w in ((COL_GD1, 70), (COL_GC, 40), (COL_KQ, 16)):
        ws.column_dimensions[get_column_letter(HEADS.index(h) + 1)].width = w

    os.makedirs(D.OUT("reports", "ctv"), exist_ok=True)
    out = D.OUT("reports", "ctv", f"{today()}-CTV-NHAT-03_cach_viet_tu-dang2.xlsx")
    try:
        wb.save(out)
    except PermissionError:
        import datetime
        base, ext = os.path.splitext(out)
        out = f"{base}-{datetime.datetime.now():%H%M%S}{ext}"
        wb.save(out)
        print(f"CHÚ Ý: file cũ đang được mở (Excel khóa) → đã lưu sang tên mới: {os.path.basename(out)}")
    print(f"→ {out} ({len(rows)} câu " + ("Dạng 2 / nghi sai nội dung)" if v2 else "có sửa lỗi bản gốc ở GĐ1)"))


if __name__ == "__main__":
    main()
