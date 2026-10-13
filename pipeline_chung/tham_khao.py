"""Quy tắc THAM KHẢO (leader duyệt 2026-10-07) – áp dụng cho MỌI dạng bài.

Phần "THÔNG TIN THAM KHẢO" / "Tham khảo" (reference) của lời giải gốc:
  - KHÔNG gửi GPT ở giai đoạn 1 (bỏ khỏi lời giải gửi đi), KHÔNG kiểm tra, KHÔNG sửa định dạng, KHÔNG gắn cờ nội dung,
    KHÔNG dịch, KHÔNG đưa CTV duyệt.
  - Python chép NGUYÊN VĂN đoạn đó (văn bản đã chuẩn hóa: bỏ HTML, furigana ｜chữ《đọc》, { } – bỏ nhãn tiêu đề)
    vào một trường chuỗi duy nhất `reference_raw` (string | null) của JSON tiếng Việt; bản tiếng Hàn giữ nguyên trường này
    (không có khóa "ko").
  - Các phép kiểm tra (độ phủ tiếng Việt, tiếng Nhật, furigana, { }, âm Hán Việt, gợi ý định dạng / từ điển) chạy trên
    lời giải ĐÃ BỎ phần tham khảo.
Trường cũ `reference` (đã dịch) chỉ còn ở dữ liệu cũ; hàm hiển thị đọc được cả hai.
"""
TRUONG = "reference_raw"
NHAN = "【THÔNG TIN THAM KHẢO】"
GHI_CHU = "(giữ nguyên bản gốc – không kiểm tra, không dịch)"

SCHEMA_PROP = {
    "type": ["string", "null"],
    "x-python-dien": True,
    "description": "Phần THÔNG TIN THAM KHẢO của lời giải gốc, chép NGUYÊN VĂN (văn bản đã chuẩn hóa, bỏ nhãn tiêu đề) – "
                   "Python tự điền, GPT không sinh; không kiểm tra, không sửa, không dịch. Bản gốc không có thì null.",
}


def dien(doc, raw):
    """Đặt doc['reference_raw'] = nguyên văn tham khảo (hoặc None); bỏ trường cũ 'reference' nếu GPT/bản cũ còn sinh."""
    if not isinstance(doc, dict):
        return doc
    doc.pop("reference", None)
    doc[TRUONG] = (raw or "").strip() or None
    return doc


def kiem_tra(doc, raw):
    """Lỗi nếu reference_raw khác nguyên văn (Claude / GPT không được sửa trường này)."""
    want = (raw or "").strip() or None
    got = doc.get(TRUONG) if isinstance(doc, dict) else None
    if TRUONG not in (doc or {}):
        return [f"K-TK: thiếu trường {TRUONG} (Python điền ở s1_gpt_chuyen / s1_claude_goi – chạy lại s1_claude_goi)"]
    if got != want:
        return [f"K-TK: {TRUONG} phải giữ NGUYÊN VĂN phần tham khảo của bản gốc (không sửa, không dịch)"]
    if "reference" in doc:
        return ["K-TK: còn trường cũ 'reference' – theo quy tắc tham khảo mới chỉ dùng reference_raw (nguyên văn)"]
    return []


def render(doc, lang, show=lambda s: s, bold=lambda s: s):
    """Dòng hiển thị Excel cho phần tham khảo: bản Việt hiện nguyên văn kèm ghi chú; bản Hàn không hiện (không dịch)."""
    raw = (doc or {}).get(TRUONG)
    if not raw or lang != "vi":
        return []
    return [bold(NHAN) + " " + GHI_CHU, show(raw)]


def nguyen_van(norm):
    """Nguyên văn phần tham khảo của một mẫu đã chuẩn hóa (output/samples/norm/<id>.json):
    dạng ### lưu ở norm['phan']['tham_khao'], dạng 01 (JSON cũ) lưu ở norm['tham_khao']."""
    norm = norm or {}
    raw = norm.get("tham_khao")
    if raw is None:
        raw = (norm.get("phan") or {}).get("tham_khao")
    return (raw or "").strip() or None
