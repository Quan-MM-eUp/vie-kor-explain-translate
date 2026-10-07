"""Xuất Excel cho CTV theo đúng format 17 cột CTV đã quen (tham khảo Vie-Kor/to_ctv), thêm:
  - cột R "Claude đã sửa" (tham khảo, không làm lệch các cột A–Q)
  - sheet "CHI TIẾT THEO TRƯỜNG": mỗi dòng 1 trường cần dịch (Mã / Vị trí / VI / KO / Bản sửa CTV),
    để bản sửa của CTV đưa ngược được vào JSON bằng bảng đối chiếu mã ↔ đường dẫn.

Phần dựng văn bản lời giải (render) do từng dạng bài cung cấp.
Quy ước đánh dấu trong chuỗi render: B0…B1 = in đậm, U0…U1 = gạch chân.
"""
import datetime
import re

from .common import FURI_RE
from .normalize import normalize_html

B0, B1, U0, U1 = "\x01", "\x02", "\x03", "\x04"

COL_GOC = "Giải thích VI gốc"
COL_VI = "Giải thích VI JSON mới"
COL_KO = "Giải thích KOR JSON mới"
COL_EDIT = "KO — CTV SỬA TẠI ĐÂY"
COL_EDIT_VI = "VI — CTV SỬA TẠI ĐÂY"
COL_FMT = "Chi tiết lỗi format đã sửa"
COL_KQ = "Kết quả"
COL_GC = "Ghi chú CTV"
COL_GD1 = "Thay đổi so với lời giải gốc khi chuyển sang JSON (GĐ1)"
COL_CLAUDE = "Claude đã sửa bản dịch (tham khảo)"
COL_RAW = "Giải thích VI gốc (nguyên văn CSV)"
BASE_HEADERS = ["question_id", "câu con", "Cấp độ", "Dạng bài", "Loại đề", "Free/Premium", "Nhóm review",
                "Điểm cần chú ý", "Câu hỏi", "Các lựa chọn", "Đáp án đúng (DB)", "Ngữ liệu (đoạn văn / transcript)"]


def headers(gd1=False):
    """Thứ tự cột sheet chính: … → VI gốc → VI JSON mới → KO JSON mới → CTV sửa → Kết quả → Ghi chú CTV → (GĐ1)."""
    return BASE_HEADERS + [COL_GOC, COL_VI, COL_KO, COL_EDIT, COL_KQ, COL_GC] + ([COL_GD1] if gd1 else [])


HEADERS = headers()
EDIT_COLS = {COL_EDIT, COL_EDIT_VI, COL_KQ, COL_GC}
WIDTH_BY_NAME = {"question_id": 10, "câu con": 6, "Cấp độ": 7, "Dạng bài": 16, "Loại đề": 14, "Free/Premium": 9, "Nhóm review": 18,
                 "Điểm cần chú ý": 30, "Câu hỏi": 30, "Các lựa chọn": 20, "Đáp án đúng (DB)": 8, "Ngữ liệu (đoạn văn / transcript)": 20,
                 COL_GOC: 55, COL_VI: 55, COL_KO: 55, COL_EDIT: 55, COL_EDIT_VI: 55, COL_FMT: 45, COL_KQ: 11, COL_GC: 30, COL_GD1: 60, COL_CLAUDE: 40, COL_RAW: 40}
HEAD_FILL, EDIT_HEAD_FILL, REF_FILL, EDIT_FILL = "305496", "BF8F00", "EDEDED", "FFF2CC"


def show(s, mark="b"):
    """Chuỗi JSON → chuỗi hiển thị: bỏ ⟪ ⟫, ẩn ｜ của furigana, { } → định dạng của bản gốc:
    mark="u" gạch chân (bản gốc gạch chân), "b" in đậm (bản gốc in đậm), "" không định dạng."""
    s = FURI_RE.sub(lambda m: f"{m.group(1)}《{m.group(2)}》", s or "")
    s = s.replace("⟪", "").replace("⟫", "")
    o, c = {"b": (B0, B1), "u": (U0, U1), "": ("", "")}[mark]
    return s.replace("{", o).replace("}", c)


def bold(s):
    return f"{B0}{s}{B1}"


# Font riêng cho cột có tiếng Hàn: Calibri không có chữ Hàn → Excel tự thay font, chữ Hàn trông như in đậm.
# Đặt font rõ ràng cho các cột này (và cho mọi đoạn trong ô rich text). Đổi tên font ở đây nếu cần.
FONT_KO = "Malgun Gothic"
FONT_BY_COL = {COL_KO: FONT_KO, COL_EDIT: FONT_KO, COL_CLAUDE: FONT_KO}


def rich(s, font=None):
    from openpyxl.cell.rich_text import CellRichText, TextBlock
    from openpyxl.cell.text import InlineFont
    if not s or not any(m in s for m in (B0, U0)):
        return s
    parts, buf, b, u = [], "", False, False

    def flush():
        nonlocal buf
        if buf:
            if b or u or font:
                parts.append(TextBlock(InlineFont(rFont=font, b=True if b else None, u="single" if u else None), buf))
            else:
                parts.append(buf)
            buf = ""
    for ch in s:
        if ch in (B0, B1, U0, U1):
            flush()
            b = True if ch == B0 else (False if ch == B1 else b)
            u = True if ch == U0 else (False if ch == U1 else u)
        else:
            buf += ch
    flush()
    return CellRichText(parts)


_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def question_cell(html):
    """Câu hỏi gốc: gạch chân thật, furigana dạng 漢字《かな》."""
    html = _CTRL_RE.sub("", html or "")          # ký tự điều khiển lạc trong dữ liệu gốc (vd \x08 ở 47225) – Excel không nhận
    s = re.sub(r"<u\b[^>]*>", "\x05", html or "", flags=re.I).replace("</u>", "\x06")
    t, _ = normalize_html(s)
    t = FURI_RE.sub(lambda m: f"{m.group(1)}《{m.group(2)}》", t)
    return t.replace("\x05", U0).replace("\x06", U1)


def html_cell(html):
    """Đoạn HTML của lời giải gốc → chuỗi hiển thị trong Excel: gạch chân / in đậm thật, xuống dòng, furigana 漢字《かな》."""
    html = _CTRL_RE.sub("", html or "")
    s = re.sub(r"<u\b[^>]*>", "\x05", html or "", flags=re.I).replace("</u>", "\x06").replace("</U>", "\x06")
    s = re.sub(r"<(b|strong)\b[^>]*>", "\x07", s, flags=re.I)
    s = re.sub(r"</(b|strong)>", "\x08", s, flags=re.I)
    s = re.sub(r"<span[^>]*font-weight:\s*(?:bold|[6-9]00)[^>]*>(.*?)</span>", "\x07\\1\x08", s, flags=re.I | re.S)
    s = re.sub(r"<span[^>]*underline[^>]*>(.*?)</span>", "\x05\\1\x06", s, flags=re.I | re.S)
    t, _ = normalize_html(s, "u")
    t = FURI_RE.sub(lambda m: f"{m.group(1)}《{m.group(2)}》", t)
    return t.replace("\x05", U0).replace("\x06", U1).replace("\x07", B0).replace("\x08", B1)


def guide_sheet(ws, title, lines):
    from openpyxl.styles import Alignment, Font
    ws.append([title])
    ws["A1"].font = Font(bold=True, size=14)
    for k, v in lines:
        ws.append([k, v])
    for r in range(2, ws.max_row + 1):
        ws.cell(r, 1).font = Font(bold=True)
        for c in (1, 2):
            ws.cell(r, c).alignment = Alignment(wrap_text=True, vertical="top")
    ws.column_dimensions["A"].width, ws.column_dimensions["B"].width = 24, 110


def _style_main(ws, heads):
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation
    ref_from = heads.index("Câu hỏi") + 1 if "Câu hỏi" in heads else len(heads) + 1
    for c in ws[1]:
        edit = heads[c.column - 1] in EDIT_COLS
        c.fill = PatternFill("solid", fgColor=EDIT_HEAD_FILL if edit else HEAD_FILL)
        c.font = Font(bold=True, color="FFFFFF")
        c.alignment = Alignment(wrap_text=True, vertical="top")
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
            if heads[c.column - 1] in FONT_BY_COL:
                c.font = Font(name=FONT_BY_COL[heads[c.column - 1]])
            if heads[c.column - 1] in EDIT_COLS:
                c.fill = PatternFill("solid", fgColor=EDIT_FILL)
            elif c.column >= ref_from:
                c.fill = PatternFill("solid", fgColor=REF_FILL)
        ws.row_dimensions[row[0].row].height = 405
    ws.row_dimensions[1].height = 43.5
    for i, h in enumerate(heads, 1):
        ws.column_dimensions[get_column_letter(i)].width = WIDTH_BY_NAME.get(h, 40)
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(heads))}{ws.max_row}"
    if COL_KQ in heads:
        col = get_column_letter(heads.index(COL_KQ) + 1)
        dv = DataValidation(type="list", formula1='"Đạt,Sửa nhỏ,Không đạt"', allow_blank=True)
        dv.add(f"{col}2:{col}{max(2, ws.max_row)}")
        ws.add_data_validation(dv)


def build(out_path, guide_title, guide_lines, main_title, rows, field_rows, error_rows=None, heads=None):
    """rows: list dict có khóa theo tên cột (giá trị đã là chuỗi render). field_rows: list dict cho sheet chi tiết.
    heads: danh sách cột sheet chính (mặc định headers()); cột sửa của CTV nền vàng, cột tham khảo nền xám."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    wb = Workbook()
    guide_sheet(wb.active, guide_title, guide_lines)
    wb.active.title = "HƯỚNG DẪN"

    ws = wb.create_sheet(main_title[:31])
    heads = heads or HEADERS
    ws.append(heads)
    for r in rows:
        ws.append([rich(r.get(h), FONT_BY_COL.get(h)) if isinstance(r.get(h), str) else r.get(h) for h in heads])
    _style_main(ws, heads)

    fh = ["sample_id", "question_id", "Mã", "Vị trí", "Tiếng Việt", "Tiếng Hàn hiện tại", "Bản sửa CTV (nếu sửa)", "Ghi chú CTV"]
    wf = wb.create_sheet("CHI TIẾT THEO TRƯỜNG")
    wf.append(fh)
    for r in field_rows:
        wf.append([r.get(h) for h in fh])
    for c in wf[1]:
        c.fill = PatternFill("solid", fgColor=EDIT_HEAD_FILL if c.column in (7, 8) else HEAD_FILL)
        c.font = Font(bold=True, color="FFFFFF")
    for row in wf.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
            if c.column in (6, 7):
                c.font = Font(name=FONT_KO)
            if c.column in (7, 8):
                c.fill = PatternFill("solid", fgColor=EDIT_FILL)
    for col, w in zip("ABCDEFGH", (18, 10, 6, 28, 60, 60, 60, 30)):
        wf.column_dimensions[col].width = w
    wf.freeze_panes = "E2"

    if error_rows:
        we = wb.create_sheet("CÂU LỖI (không gửi CTV)")
        eh = ["sample_id", "question_id", "trang_thai", "loi"]
        we.append(eh)
        for r in error_rows:
            we.append([r.get(h) for h in eh])
        for col, w in zip("ABCD", (18, 10, 14, 120)):
            we.column_dimensions[col].width = w
    try:
        wb.save(out_path)
    except PermissionError:           # file cũ đang mở trong Excel → lưu tên mới, không ghi đè
        import os
        base, ext = os.path.splitext(out_path)
        out_path = f"{base}-{datetime.datetime.now():%H%M%S}{ext}"
        wb.save(out_path)
        print(f"CHÚ Ý: file cũ đang được mở (Excel khóa) → đã lưu sang tên mới: {os.path.basename(out_path)}")
    return out_path


def today():
    return datetime.date.today().isoformat()
