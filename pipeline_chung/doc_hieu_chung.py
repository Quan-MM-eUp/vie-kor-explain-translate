"""Phần dùng chung cho các dạng ĐỌC HIỂU (10–15) – schema reading_listening.v1. Dựng 2026-10-08 cùng dạng 15 (Tìm thông tin). Tên file có hậu tố _chung để không trùng các parser riêng đang dựng song song (12: _doc_hieu.py, 13: _doc_hieu_13.py).

Các dạng đọc hiểu cùng khuôn lời giải: câu hỏi (+ dịch) → 4 lựa chọn (Nghĩa / trích dẫn 「…」 + (dịch) / phân tích) → '→ ĐÚNG' / '→ SAI'.
Mỗi dạng chỉ giữ phần riêng trong scripts/_dang.py; ở đây là:
  1. ngu_lieu()          – ngữ liệu HTML → văn bản: TRẢI BẢNG (<table> → '| ô | ô |', ô gộp lặp lại), ảnh → [ẢNH: …]
  2. chuan_so / khop_ngu_lieu – so mờ câu tiếng Nhật (trích dẫn ↔ ngữ liệu / lời giải)
  3. tach_loi_giai()     – tách câu hỏi / 4 khối lựa chọn / kết luận ĐÚNG–SAI, phân khuôn A / B / C, ứng viên trích dẫn
  4. kiem_tra_tinh_toan() – K-TT: tính lại phép tính 'a + b = c', '600円 × 0.7 = 420円', giờ 13:00 + 30 = 13:30
  5. gan_co()            – cờ s0 + ghi chú [Bản gốc VI] dùng chung
  6. check_reading()     – kiểm tra JSON tiếng Việt (K1–K6, K-TD, K-NQ, K-TT, K-FT)
  7. render()            – dựng lời giải cho Excel CTV
  8. GĐ2: danh_dau / prefill / tagged_copy (nghĩa câu dịch TRỰC TIẾP từ tiếng Nhật), D-SO (số), D12 (trợ từ sau ⟪kana⟫), D4
  9. tao_thu_tu_ngu_lieu() – thứ tự chạy + cột lô theo ngữ liệu (không cắt đôi ngữ liệu)
Python chỉ GỢI Ý / KIỂM TRA – không sửa nội dung lời giải.
"""
import collections
import copy
import difflib
import html as _html
import random
import re
import unicodedata

from .common import FURI_RE, JA_RE, LOCK_RE, VI_DIACRITIC_RE, get_path, iter_lang_fields, norm_ja, parse_path, path_str, strip_marks
from .normalize import normalize_html

# =====================================================================
# 1. Ngữ liệu: trải bảng, ảnh
# =====================================================================
_TABLE_RE = re.compile(r"<table\b[^>]*>((?:(?!<table\b).)*?)</table>", re.S | re.I)
_TR_RE = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.S | re.I)
_TD_RE = re.compile(r"<t([dh])\b([^>]*)>(.*?)</t[dh]>", re.S | re.I)
_SPAN_RE = {k: re.compile(k + r"\s*=\s*[\"']?(\d+)", re.I) for k in ("colspan", "rowspan")}
_IMG_RE = re.compile(r"<img\b[^>]*?src\s*=\s*[\"']([^\"']+)[\"'][^>]*>", re.I)
PH = "⟦BANG{}⟧"


def _cell_text(h):
    t = normalize_html(h, "u+b")[0]
    return " ／ ".join(x.strip() for x in t.split("\n") if x.strip())


def _table_lines(inner):
    """Một bảng HTML → các dòng '| ô | ô |' (rowspan / colspan: lặp lại nội dung ô gộp)."""
    grid, carry = [], {}                       # carry[col] = (text, số hàng còn lại)
    for tr in _TR_RE.findall(inner):
        row, col = [], 0
        cells = _TD_RE.findall(tr)
        ci = 0
        while ci < len(cells) or any(c >= col for c in carry):
            if col in carry:
                txt, left = carry[col]
                row.append(txt)
                if left <= 1:
                    del carry[col]
                else:
                    carry[col] = (txt, left - 1)
                col += 1
                continue
            if ci >= len(cells):
                break
            _, attrs, h = cells[ci]
            ci += 1
            txt = _cell_text(h)
            cs = int((_SPAN_RE["colspan"].search(attrs) or [0, 1])[1])
            rs = int((_SPAN_RE["rowspan"].search(attrs) or [0, 1])[1])
            for _ in range(max(1, min(cs, 20))):
                row.append(txt)
                if rs > 1:
                    carry[col] = (txt, rs - 1)
                col += 1
        if any(x for x in row):
            grid.append(row)
    if not grid and not _TR_RE.search(inner):    # bảng không có <tr>: bỏ thẻ
        t = normalize_html(inner, "u+b")[0]
        return [x for x in t.split("\n") if x.strip()]
    return ["| " + " | ".join(r) + " |" for r in grid]


def ngu_lieu(html):
    """Ngữ liệu HTML → (văn bản, info). info = {bang: số bảng, anh: [src], rong: bool, do_dai}.
    Bảng → mỗi hàng một dòng '| ô | ô |' (ô có nhiều dòng nối bằng ' ／ '); ảnh → '[ẢNH: tên file]'; furigana → ｜…《…》; gạch chân → { }."""
    s = html or ""
    anh = []

    def _img(m):
        anh.append(m.group(1))
        return f"<br>[ẢNH: {m.group(1).rsplit('/', 1)[-1][:60]}]<br>"
    s = _IMG_RE.sub(_img, s)
    bangs = []
    while True:
        m = _TABLE_RE.search(s)
        if not m:
            break
        bangs.append(_table_lines(m.group(1)))
        s = s[:m.start()] + "<br>" + PH.format(len(bangs) - 1) + "<br>" + s[m.end():]
    t = normalize_html(s, "u+b")[0]
    for i, b in enumerate(bangs):
        t = t.replace(PH.format(i), "\n".join(b))
    t = re.sub(r"\n{3,}", "\n\n", t).strip()
    return t, {"bang": len(bangs), "anh": anh, "rong": not t.strip(), "do_dai": len(t)}


# =====================================================================
# 2. So mờ chuỗi tiếng Nhật
# =====================================================================
_PUNCT_RE = re.compile(r"[\s　、。，．・…‥「」『』｢｣（）()\[\]［］【】〈〉<>\"'“”‘’,.:：;；!！?？~〜～\-－―‐|｜/／*＊※→⇒⟪⟫{}#]")
_CHU_THICH_RE = re.compile(r"[（(]?\s*注\s*[0-9０-９]+\s*[)）]?")


def chuan_so(s):
    """Chuỗi để so mờ: NFKC, bỏ cách đọc furigana (giữ chữ gốc), chú thích 注n, dấu câu, khoảng trắng."""
    s = FURI_RE.sub(lambda m: m.group(1), s or "")
    s = unicodedata.normalize("NFKC", s)
    s = _CHU_THICH_RE.sub("", s)
    s = re.sub(r"\[ẢNH:[^\]]*\]", "", s)
    s = re.sub(r"(?<=[㐀-䶿一-鿿々])[（(][぀-ゟー]+[)）]", "", s)          # cách đọc viết trong ngoặc sau chữ Hán: 教室(きょうしつ)
    return _PUNCT_RE.sub("", s).lower()


def khop_ngu_lieu(q, p_norm):
    """So câu trích (q) với ngữ liệu đã chuan_so (p_norm). → (kết quả, tỷ lệ):
    'khop' (có nguyên văn / ≥ 90%), 'mot_phan' (≥ 75%), 'khong' (< 75% – nghi trích tự dựng / sai chỗ), 'ngan' (quá ngắn để so)."""
    qn = chuan_so(q)
    if len(qn) < 4:
        return "ngan", 1.0
    if qn in p_norm:
        return "khop", 1.0
    sm = difflib.SequenceMatcher(None, p_norm, qn, autojunk=False)
    tl = sum(b.size for b in sm.get_matching_blocks() if b.size >= 3) / len(qn)
    return ("khop" if tl >= 0.9 else "mot_phan" if tl >= 0.75 else "khong"), round(tl, 2)


def giong(a, b):
    """Tỷ lệ giống nhau của hai chuỗi tiếng Nhật (sau chuan_so)."""
    a, b = chuan_so(a), chuan_so(b)
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def ja_chiem(s):
    """Dòng chủ yếu là tiếng Nhật: không có chữ Việt có dấu, ≥ 2 ký tự Nhật và ≥ 30% ký tự không trắng."""
    t = strip_marks(LOCK_RE.sub(lambda m: m.group(1), s or ""))
    t = re.sub(r"^\s*[-•*+]\s*", "", t)
    if VI_DIACRITIC_RE.search(t):
        return False
    n_ja = sum(len(x) for x in JA_RE.findall(t))
    n = len(re.sub(r"\s", "", t))
    return n_ja >= 2 and n_ja / max(1, n) >= 0.3


# =====================================================================
# 3. Tách lời giải
# =====================================================================
OPT_RE = re.compile(r"^\s*\{?\s*([1-4１-４])\s*\}?\s*[\.．、)）]\s*(.*)$")
VERDICT_RE = re.compile(r"(?:→|->|=>|⇒)\s*\{?\s*(ĐÚNG|SAI|Đúng|Sai|đúng|sai)(?![A-Za-zÀ-ỹĐđ])")
NGHIA_RE = re.compile(r"^\s*[-•*+]?\s*Nghĩa\s*[:：]\s*(.*)$", re.I)
CAU_HOI_LAB_RE = re.compile(r"^\s*[-•*+]?\s*Câu hỏi\s*[:：]\s*(.*)$", re.I)
DAP_AN_RE = re.compile(r"(?i)(?:lựa chọn|đáp án|câu trả lời)\s*(?:chính xác|đúng)?\s*(?:là)?\s*(?:lựa chọn\s*)?(?:số\s*)?([1-4])\b")


def _so(x):
    return int(unicodedata.normalize("NFKC", x))


def trich_dan_ung_vien(text):
    """Ứng viên trích dẫn tiếng Nhật trong một khối: đoạn 「…」 (cân ngoặc lồng) có tiếng Nhật, và dòng chủ yếu tiếng Nhật."""
    out = []
    i, n = 0, len(text)
    while i < n:
        if text[i] == "「":
            d, j = 0, i
            while j < n:
                if text[j] == "「":
                    d += 1
                elif text[j] == "」":
                    d -= 1
                    if d == 0:
                        break
                j += 1
            seg = text[i + 1:j]
            if len(JA_RE.findall(strip_marks(seg))) and sum(len(x) for x in JA_RE.findall(strip_marks(seg))) >= 4 and not VI_DIACRITIC_RE.search(seg):
                out.append(seg)
            i = j + 1
            continue
        i += 1
    for ln in text.split("\n"):
        s = ln.strip()
        if s.startswith("「") or not ja_chiem(s):
            continue
        s = re.sub(r"^\s*[-•*+]\s*", "", s)
        if s.startswith(("(", "（")) and s.endswith((")", "）")):
            s = s[1:-1].strip()
        if sum(len(x) for x in JA_RE.findall(strip_marks(s))) >= 6:
            out.append(s)
    seen, res = set(), []
    for q in out:
        k = chuan_so(q)
        if k and k not in seen:
            seen.add(k)
            res.append(q)
    return res


def tach_loi_giai(text, lua_chon, cau_hoi=""):
    """Lời giải đã chuẩn hóa → phan:
      cau_hoi_ja / cau_hoi_vi (dòng câu hỏi + dịch ở đầu), dau_khac (chữ khác ở phần đầu – vd bản dịch thông báo),
      lua_chon: [{so, dong (số dòng), ja (dòng lựa chọn), khop_de, nghia, ket_luan (True/False/None), so_ket_luan, than, trich_dan}],
      sau (chữ sau kết luận của lựa chọn cuối), dap_an_loi_giai (số lời giải nói là đáp án, khuôn B), khuon (A | B | C)."""
    lines = text.split("\n")
    cands = [(i, _so(m.group(1)), m.group(2).strip()) for i, ln in enumerate(lines) for m in [OPT_RE.match(ln)] if m]
    found, prev = [], -1
    for k in range(1, 5):
        best = None
        for i, n, c in cands:
            if i <= prev or n != k:
                continue
            g = giong(c, lua_chon[k - 1]) if k - 1 < len(lua_chon) else 0
            if g >= 0.6:
                best = (i, k, c, g)
                break
            if best is None:                 # không khớp đề: lấy dòng 'k.' đầu tiên (lựa chọn là tranh / số / đề hỏng / bản dịch tiếng Việt)
                best = (i, k, c, g)
        if best:
            found.append(best)
            prev = best[0]
    first = found[0][0] if found else len(lines)
    # phần đầu
    head = lines[:first]
    hq, hv, khac, j = [], [], [], 0
    while j < len(head) and not head[j].strip():
        j += 1
    while j < len(head) and head[j].strip() and ja_chiem(head[j]):
        hq.append(head[j].strip())
        j += 1
    while j < len(head) and head[j].strip() and not ja_chiem(head[j]) and hq:
        hv.append(head[j].strip())
        j += 1
    khac = [x for x in head[j:]]
    # các khối lựa chọn
    opts = []
    for t, (i, k, c, g) in enumerate(found):
        end = found[t + 1][0] if t + 1 < len(found) else len(lines)
        body = lines[i + 1:end]
        nghia = next((NGHIA_RE.match(x).group(1).strip() for x in body if NGHIA_RE.match(x)), None)
        vs = VERDICT_RE.findall("\n".join(body))
        kl = None
        if vs:
            kl = vs[-1].upper() == "ĐÚNG"
        ja = c if (ja_chiem(c) or g >= 0.6) else None          # dòng 'k.' không phải tiếng Nhật (vd 'Hình minh họa 1 …', bản dịch) → chữ thuộc phần thân
        than = "\n".join(([c] if c and ja is None else []) + body).strip()
        opts.append({"so": k, "dong": i, "ja": ja, "dong_so": c, "khop_de": round(g, 2), "nghia": nghia, "ket_luan": kl, "so_ket_luan": len(vs),
                     "than": than, "trich_dan": trich_dan_ung_vien("\n".join(body))})
    sau = ""
    if opts:
        last = opts[-1]["than"].split("\n")
        idx = max((n for n, x in enumerate(last) if VERDICT_RE.search(x)), default=None)
        if idx is not None:
            sau = "\n".join(last[idx + 1:]).strip()
    all_text = "\n".join(lines)
    n_vs = len(VERDICT_RE.findall(all_text))
    m_da = DAP_AN_RE.search(all_text) if not n_vs else None
    if len(opts) == 4 and all(o["so_ket_luan"] >= 1 for o in opts):
        khuon = "A"
    elif n_vs == 0:
        khuon = "B"
    else:
        khuon = "C"
    if khuon != "A" and not hq:      # khuôn lạ: tìm dòng 'Câu hỏi:' tiếng Việt
        for n_, x in enumerate(lines[:first]):
            m = CAU_HOI_LAB_RE.match(x)
            if m:
                nxt = m.group(1).strip() or next((y.strip() for y in lines[n_ + 1:first] if y.strip()), "")
                if nxt and not OPT_RE.match(nxt):
                    hv = [nxt]
                    break
    return {"cau_hoi_ja": "\n".join(hq) or None, "cau_hoi_vi": "\n".join(hv) or None,
            "dau_khac": "\n".join(khac).strip(), "lua_chon": opts, "sau": sau,
            "dap_an_loi_giai": int(m_da.group(1)) if m_da else None, "khuon": khuon}


# =====================================================================
# 4. Tính toán (K-TT)
# =====================================================================
_TIME_RE = re.compile(r"(\d{1,2})[:：](\d{2})")
_TOK_RE = re.compile(r"(\d{1,2}:\d{2})|(\d+(?:[.,]\d+)*)\s*(%)?|([+\-−–×*÷/])|([()])")


def _num(s):
    """'1,000' / '1.000' → 1000; '0,7' / '0.7' → 0.7; '13,812.5' → 13812.5. Không đọc được → ValueError."""
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", s) and not re.fullmatch(r"0[.,]\d+", s):
        return float(re.sub(r"[.,]", "", s))
    m = re.fullmatch(r"(\d{1,3}(?:([.,])\d{3})+)([.,])(\d+)", s)
    if m and m.group(2) != m.group(3):
        return float(re.sub(r"[.,]", "", m.group(1)) + "." + m.group(4))
    return float(s.replace(",", "."))


def _eval_trai(left, gio):
    expr, last, sau = [], None, 0
    for m in _TOK_RE.finditer(left):
        t, n, pct, op, ng = m.groups()
        if ng:
            if ng == "(" and last != "so":
                sau += 1
                expr.append("(")
                last = "("
            elif ng == ")" and last == "so" and sau > 0:
                sau -= 1
                expr.append(")")
            else:
                return None
            continue
        if t or n:
            if last == "so":
                return None
            if t:
                h, mi = t.split(":")
                v = int(h) * 60 + int(mi)
            else:
                try:
                    v = _num(n) / (100 if pct else 1)
                except ValueError:
                    return None
            expr.append(repr(v))
            last = "so"
        else:
            if last != "so":
                return None
            expr.append({"×": "*", "÷": "/", "−": "-", "–": "-"}.get(op, op))
            last = "op"
    if last != "so" or sau or len([x for x in expr if x not in "()"]) < 3:
        return None
    try:
        return eval("".join(expr), {"__builtins__": {}}, {})         # chỉ gồm số và + - * /
    except Exception:                                                 # noqa: BLE001
        return None


def kiem_tra_tinh_toan(text):
    """Tìm phép tính 'vế trái = kết quả' trong văn bản, tính lại. → [{dong, bieu_thuc, ket_qua_ghi, tinh_lai, dung}].
    Chỉ xét vế trái gồm số / giờ + phép toán (bỏ qua chữ, đơn vị, ngoặc chú thích); không chắc thì bỏ qua (không báo)."""
    out = []
    for raw in (text or "").split("\n"):
        line = unicodedata.normalize("NFKC", strip_marks(LOCK_RE.sub(lambda m: m.group(1), raw)))
        if "=" not in line or re.search(r"[~〜～]", line):
            continue
        line = re.sub(r"^\s*[-•*+]?\s*\d+[.)]\s+", "", line)
        line = re.sub(r"(?<![A-Za-zÀ-ỹĐđ])[xX](?![A-Za-zÀ-ỹĐđ])", "×", line)
        line = re.sub(r"\([^()]*[A-Za-zÀ-ỹĐđ぀-鿿][^()]*\)", " ", line)       # (viên con nhộng), (cá) …
        segs = line.split("=")
        for j in range(len(segs) - 1):
            left = re.split(r"[:：](?!\d)|\.\s|[;；]", segs[j])[-1]
            right = re.split(r"[:：](?!\d)|\.\s|[;；]", segs[j + 1])[0]
            mr = re.match(r"\s*(?:khoảng\s*)?(\d{1,2}:\d{2}|\d+(?:[.,]\d+)*)\s*(%)?", right)
            if not mr or not re.search(r"[+\-−–×*÷/]", left):
                continue
            gio = bool(_TIME_RE.search(left))
            if gio != bool(_TIME_RE.fullmatch(mr.group(1))) and gio:
                continue
            val = _eval_trai(left, gio)
            if val is None:
                continue
            rv = _eval_trai(right, gio) if re.search(r"\d\s*[^\d\s:.,%]{0,4}\s*[+\-−–×*÷/]\s*\(?\s*\d", right) else None
            try:
                if rv is not None:
                    rhs = rv
                elif _TIME_RE.fullmatch(mr.group(1)):
                    h, mi = mr.group(1).split(":")
                    rhs = int(h) * 60 + int(mi)
                else:
                    rhs = _num(mr.group(1)) / (100 if mr.group(2) else 1)
            except ValueError:
                continue
            dung = abs(val - rhs) <= max(0.01, 0.005 * abs(rhs)) or (rhs == int(rhs) and round(val) == rhs)
            out.append({"dong": raw.strip()[:160], "bieu_thuc": left.strip()[:80], "ket_qua_ghi": mr.group(1),
                        "tinh_lai": round(val, 4), "dung": dung})
    return out


# =====================================================================
# 5. Cờ s0 dùng chung
# =====================================================================
FLAG_TEXT = {
    "khuon_la": "Khuôn lời giải lạ (B: chỉ dịch ngữ liệu / câu hỏi + nêu đáp án, không phân tích 4 lựa chọn; C: thiếu kết luận / thiếu lựa chọn) – JSON phần có được, tác tử KIỂM TRA gắn cờ thieu_noi_dung",
    "co_ban_dich": "Phần đầu lời giải có bản dịch ngữ liệu (→ full_translation)",
    "so_lua_chon_khac_4": "Lời giải không có đủ 4 dòng lựa chọn đánh số 1–4",
    "lua_chon_lech": "Dòng lựa chọn trong lời giải viết khác lựa chọn của đề",
    "cau_hoi_lech": "Dòng câu hỏi trong lời giải viết khác câu hỏi của đề",
    "khong_cau_hoi_ja": "Lời giải không có dòng câu hỏi tiếng Nhật ở đầu (question.ja = null)",
    "khong_ket_luan": "Có lựa chọn không có kết luận '→ ĐÚNG / → SAI'",
    "lech_dap_an": "Lời giải chấm ĐÚNG lựa chọn khác dap_an_so của đề (nghi đáp án dữ liệu / lời giải sai)",
    "nhieu_dung": "Lời giải chấm ĐÚNG nhiều hơn một lựa chọn",
    "khong_dung": "Lời giải không chấm ĐÚNG lựa chọn nào (khuôn A)",
    "dap_an_de_loi": "Dữ liệu đề lỗi: dap_an_so không phải 1–4",
    "trich_dan_ngoai_ngu_lieu": "Có câu trích tiếng Nhật KHÔNG tìm thấy trong ngữ liệu (nghi trích tự dựng / sai chỗ – xem output/reports/trich_dan.csv)",
    "trich_dan_tieng_viet": "Có 'trích dẫn' chỉ bằng tiếng Việt (từ bản dịch) – để trong analysis, không đưa vào quotes",
    "co_tinh_toan": "Lời giải có phép tính",
    "tinh_toan_sai": "Python tính lại thấy phép tính trong lời giải SAI (xem output/reports/tinh_toan.csv)",
    "thieu_ngu_lieu": "Ngữ liệu (doan_van) RỖNG – không đối chiếu được trích dẫn / phân tích",
    "ngu_lieu_anh": "Ngữ liệu có ẢNH – Python và tác tử KIỂM TRA không đọc được nội dung ảnh",
    "ngu_lieu_bang": "Ngữ liệu có bảng – Python đã trải bảng thành dòng '| ô | ô |'",
    "chen_tu_nhat": "Câu tiếng Việt có chen từ tiếng Nhật (bọc ⟪ ⟫)",
    "markdown": "Lời giải có ký hiệu markdown (** / #) – Python đã bỏ ký hiệu, giữ dòng",
    "co_furigana": "Có furigana",
    "ruby_hong": "Có ruby hỏng trong bản gốc",
    "ky_hieu_trung": "Bản gốc có sẵn ký hiệu ｜《》 (trùng ký hiệu furigana)",
    "danh_dau_rac": "Bản gốc có đoạn in đậm / gạch chân rỗng hoặc chỉ là dấu câu (đã bỏ thẻ)",
    "furigana_chu_viet": "Furigana gắn lên chữ tiếng Việt – Python đã bỏ",
    "lua_chon_la_tranh": "Lựa chọn của đề chỉ là số 1–4 (chọn tranh / hình) – option_ja = số của đề; mô tả tranh trong lời giải để ở analysis",
    "lua_chon_de_hong": "Lựa chọn của đề bị đổi thành ngày giờ kiểu Excel ('9/1/2020 0:00') – dữ liệu gốc hỏng, báo người dùng",
    "co_phan_dau": "Có chữ ở phần đầu lời giải (sau câu hỏi, trước lựa chọn 1): bản dịch ngữ liệu → full_translation, tóm tắt / ghi chú thông tin → summary",
}
CTV_FLAGS = ("lech_dap_an", "nhieu_dung", "khuon_la", "thieu_ngu_lieu", "ngu_lieu_anh", "tinh_toan_sai", "trich_dan_ngoai_ngu_lieu", "dap_an_de_loi")
MD_RE = re.compile(r"\*\*|^\s*#{1,6}\s+", re.M)


def bo_markdown(text):
    """'**Mục đích:**' → 'Mục đích:'; '# Đáp án …' → 'Đáp án …'. Trả (text, số chỗ)."""
    n = len(MD_RE.findall(text))
    return MD_RE.sub("", text), n


FURI_VI_RE = re.compile(r"｜([^｜《》\n]*?[A-Za-zÀ-ỹĐđ][^｜《》\n]*?)《([^》\n]*)》")


def bo_furigana_chu_viet(text):
    doi = []

    def _r(m):
        doi.append((m.group(0), m.group(1)))
        return m.group(1)
    return FURI_VI_RE.sub(_r, text), doi


def gan_co(phan, de, ngu_lieu_text, ngu_lieu_info, text):
    """Cờ + ghi chú [Bản gốc VI] + số liệu (trích dẫn, tính toán) dùng chung cho dạng đọc hiểu."""
    co, gc = [], []
    dap = de.get("dap_an_so")
    dap = dap if isinstance(dap, int) and 1 <= dap <= 4 else None
    if dap is None:
        co.append("dap_an_de_loi")
        gc.append(f"[Bản gốc VI] Dữ liệu đề lỗi: dap_an_so = '{de.get('dap_an_so')}' (không phải 1–4)")
    if phan["khuon"] != "A":
        co.append("khuon_la")
        gc.append(f"[Bản gốc VI] Khuôn lời giải lạ ({phan['khuon']}): " + ("không phân tích từng lựa chọn" if phan["khuon"] == "B" else "thiếu kết luận / thiếu lựa chọn"))
    if phan["dau_khac"].strip():
        co.append("co_phan_dau")
    if len(re.sub(r"\s", "", phan["dau_khac"])) >= 200:
        co.append("co_ban_dich")
    if len(phan["lua_chon"]) != 4:
        co.append("so_lua_chon_khac_4")
    if all(re.fullmatch(r"\s*[1-4１-４]\s*", x or "") for x in de["lua_chon"]):
        co.append("lua_chon_la_tranh")
    if any(re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}", (x or "").strip()) for x in de["lua_chon"]):
        co.append("lua_chon_de_hong")
        gc.append("[Bản gốc VI] Lựa chọn của đề bị đổi thành ngày giờ kiểu Excel (vd '9/1/2020 0:00') – cần sửa dữ liệu gốc")
    for o in phan["lua_chon"]:
        if "lua_chon_la_tranh" in co or o["so"] - 1 >= len(de["lua_chon"]):
            continue
        if o["ja"] is None or o["khop_de"] < 0.9:
            co.append("lua_chon_lech")
            gc.append(f"[Bản gốc VI] Lựa chọn {o['so']} trong lời giải viết khác đề: '{strip_marks(o['ja'] or o['dong_so'])[:60]}' ↔ đề '{de['lua_chon'][o['so'] - 1][:60]}'")
    if phan["cau_hoi_ja"] is None:
        co.append("khong_cau_hoi_ja")
    elif giong(phan["cau_hoi_ja"], de.get("cau_hoi", "")) < 0.9:
        co.append("cau_hoi_lech")
        gc.append(f"[Bản gốc VI] Dòng câu hỏi trong lời giải khác đề: '{strip_marks(phan['cau_hoi_ja'])[:60]}'")
    if phan["khuon"] == "A" or phan["khuon"] == "C":
        if any(o["ket_luan"] is None for o in phan["lua_chon"]):
            co.append("khong_ket_luan")
        dung = [o["so"] for o in phan["lua_chon"] if o["ket_luan"]]
        if len(dung) > 1:
            co.append("nhieu_dung")
            gc.append(f"[Bản gốc VI] Lời giải chấm ĐÚNG {len(dung)} lựa chọn: {dung}")
        elif len(dung) == 1 and dap and dung[0] != dap:
            co.append("lech_dap_an")
            gc.append(f"[Bản gốc VI] Lời giải chấm ĐÚNG lựa chọn {dung[0]}, khác đáp án của đề (dap_an_so = {dap}) – cần xem dữ liệu gốc")
        elif not dung and phan["khuon"] == "A":
            co.append("khong_dung")
    elif phan.get("dap_an_loi_giai") and dap and phan["dap_an_loi_giai"] != dap:
        co.append("lech_dap_an")
        gc.append(f"[Bản gốc VI] Lời giải nói đáp án là {phan['dap_an_loi_giai']}, khác dap_an_so = {dap}")
    # ngữ liệu
    if ngu_lieu_info.get("rong"):
        co.append("thieu_ngu_lieu")
        gc.append("[Bản gốc VI] Ngữ liệu (doan_van) rỗng – không đối chiếu được")
    if ngu_lieu_info.get("anh"):
        co.append("ngu_lieu_anh")
    if ngu_lieu_info.get("bang"):
        co.append("ngu_lieu_bang")
    # trích dẫn
    p_norm = chuan_so(ngu_lieu_text)
    td = []
    for o in phan["lua_chon"]:
        for q in o["trich_dan"]:
            kq, tl = ("khong_ngu_lieu", 0) if not p_norm else khop_ngu_lieu(q, p_norm)
            if kq == "khong" and ngu_lieu_info.get("anh"):
                kq = "ngu_lieu_anh"            # nội dung nằm trong ảnh – không so được
            td.append({"lua_chon": o["so"], "trich": q, "ket_qua": kq, "ty_le": tl})
    if any(x["ket_qua"] == "khong" for x in td) and not ngu_lieu_info.get("anh"):
        co.append("trich_dan_ngoai_ngu_lieu")
        gc.append("[Bản gốc VI] Có câu trích không tìm thấy trong ngữ liệu: " + " | ".join(f"LC{x['lua_chon']}: '{strip_marks(x['trich'])[:40]}'" for x in td if x["ket_qua"] == "khong")[:300])
    if re.search(r"(?i)(trích dẫn|trích)\s+(từ|theo)\s+(bản dịch|phần dịch)|theo phần đọc tiếng Việt|trong phần dịch tiếng Việt", text):
        co.append("trich_dan_tieng_viet")
    # tính toán
    tt = kiem_tra_tinh_toan(text)
    if tt:
        co.append("co_tinh_toan")
    if any(not x["dung"] for x in tt):
        co.append("tinh_toan_sai")
        gc.append("[Bản gốc VI] Phép tính sai: " + "; ".join(f"'{x['bieu_thuc']} = {x['ket_qua_ghi']}' (tính lại: {x['tinh_lai']:g})" for x in tt if not x["dung"]))
    if any(VI_DIACRITIC_RE.search(ln) and JA_RE.search(strip_marks(ln)) and not ja_chiem(ln) for ln in text.split("\n")):
        co.append("chen_tu_nhat")
    return co, gc, {"trich_dan": td, "tinh_toan": tt}


# =====================================================================
# 6. Kiểm tra JSON tiếng Việt (reading_listening.v1)
# =====================================================================
def _k(s):
    return chuan_so(s)


def _v(o):
    return (o or {}).get("vi") if isinstance(o, dict) else None


def check_reading(doc, norm, anh_em=()):
    """K1–K6, K-TD, K-NQ, K-TT, K-FT. anh_em = JSON (đã soát) của các câu con khác cùng ngữ liệu (cho K-NQ). → (lỗi, cảnh báo)."""
    loi, cb = [], []
    de, phan, co = norm["de"], norm.get("phan") or {}, set(norm.get("co") or [])
    opts = doc.get("options") or []
    q, c = doc.get("question") or {}, doc.get("correct") or {}
    dap = de.get("dap_an_so") if isinstance(de.get("dap_an_so"), int) and 1 <= de["dap_an_so"] <= 4 else None
    # K1 – đủ 4 lựa chọn, đúng thứ tự
    if [o.get("index") for o in opts] != [1, 2, 3, 4]:
        loi.append(f"K1: options phải đủ 4 lựa chọn index 1–4 theo thứ tự (đang có {[o.get('index') for o in opts]})")
    # K2 – correct
    if dap and c.get("index") != dap:
        loi.append(f"K2: correct.index = {c.get('index')} ≠ dap_an_so = {dap}")
    by = {o.get("index"): o for o in opts}
    ci = c.get("index")
    if ci in by and _k(c.get("option_ja")) != _k(by[ci].get("option_ja")):
        loi.append("K4: correct.option_ja phải giống hệt options[index-1].option_ja")
    if c.get("full_sentence") is not None:
        loi.append("K4: correct.full_sentence phải null (dạng đọc hiểu không có câu hoàn chỉnh)")
    # K3 – is_match theo lời giải
    pl = {o["so"]: o for o in phan.get("lua_chon") or []}
    for o in opts:
        i = o.get("index")
        kl = (pl.get(i) or {}).get("ket_luan")
        if kl is None and phan.get("khuon") == "B" and phan.get("dap_an_loi_giai"):
            kl = i == phan["dap_an_loi_giai"]
        mong = kl if kl is not None else (i == ci)
        if o.get("is_match") is not mong:
            loi.append(f"K3: options[{i - 1}].is_match = {o.get('is_match')} – lời giải "
                       + (f"kết luận {'ĐÚNG' if kl else 'SAI'}" if kl is not None else f"không kết luận → theo đáp án ({mong})"))
    trues = [o.get("index") for o in opts if o.get("is_match")]
    if trues != [ci]:
        msg = f"K3: lựa chọn is_match = true {trues} ≠ [correct.index = {ci}]"
        (cb if co & {"lech_dap_an", "nhieu_dung", "khong_dung", "khong_ket_luan", "dap_an_de_loi"} else loi).append(msg + " (bản gốc chấm lệch – gắn cờ dap_an)")
    # K5 – câu hỏi (khuôn C: Python tách không chắc → chỉ cảnh báo)
    k5 = loi if phan.get("khuon") in ("A", "B") else cb
    if phan.get("cau_hoi_ja"):
        if _k(q.get("ja")) != _k(phan["cau_hoi_ja"]):
            k5.append(f"K5: question.ja khác dòng câu hỏi của lời giải '{strip_marks(phan['cau_hoi_ja'])[:60]}'")
    elif q.get("ja") is not None:
        k5.append("K5: lời giải không có dòng câu hỏi tiếng Nhật → question.ja = null (không chép từ đề)")
    if phan.get("cau_hoi_vi") and _v(q.get("meaning")) is None:
        k5.append("K5: lời giải có dòng dịch câu hỏi nhưng question.meaning = null")
    # K6 – lựa chọn
    for o in opts:
        i = o.get("index")
        p = pl.get(i)
        goc = p["ja"] if p and p.get("ja") else (de["lua_chon"][i - 1] if isinstance(i, int) and 1 <= i <= len(de["lua_chon"]) else None)
        if goc is not None and _k(o.get("option_ja")) != _k(goc):
            (loi if phan.get("khuon") in ("A", "B") else cb).append(f"K6: options[{i - 1}].option_ja khác {'dòng lựa chọn của lời giải' if p and p.get('ja') else 'lựa chọn của đề'}: '{strip_marks(goc)[:50]}'")
        if o.get("reading") is not None:
            loi.append(f"K6: options[{i - 1}].reading phải null (lời giải không có dòng cách đọc riêng)")
        if p and p.get("nghia") and _v(o.get("meaning")) is None:
            loi.append(f"K6: options[{i - 1}].meaning = null nhưng lời giải có dòng 'Nghĩa:'")
    # K-TD – trích dẫn
    src = chuan_so(norm.get("src_text") or "")
    p_norm = chuan_so(norm.get("doan_van") or "")
    so_ngu_lieu = p_norm and not (co & {"ngu_lieu_anh"})
    for o in opts:
        for j, t in enumerate(o.get("quotes") or []):
            ja = t.get("ja") or ""
            ps = f"options[{o.get('index', 0) - 1}].quotes[{j}]"
            if not JA_RE.search(strip_marks(ja)):
                loi.append(f"K-TD: {ps}.ja không có tiếng Nhật – trích dẫn chỉ tiếng Việt để trong analysis")
                continue
            if chuan_so(ja) and chuan_so(ja) not in src:
                loi.append(f"K-TD: {ps}.ja không có nguyên văn trong lời giải (chép đúng câu trích của lời giải, không sửa / ghép): '{strip_marks(ja)[:50]}'")
            if so_ngu_lieu:
                kq, tl = khop_ngu_lieu(ja, p_norm)
                if kq == "khong":
                    cb.append(f"K-TD: {ps}.ja không tìm thấy trong ngữ liệu (giống {tl:.0%}) – xem có phải trích tự dựng / sai chỗ (cờ trich_dan): '{strip_marks(ja)[:50]}'")
    # K-NQ – cùng câu trích, nghĩa khác giữa các câu con
    mine = {chuan_so(t.get("ja")): _v(t.get("meaning")) for o in opts for t in o.get("quotes") or [] if _v(t.get("meaning"))}
    for d2 in anh_em or ():
        for o2 in d2.get("options") or []:
            for t2 in o2.get("quotes") or []:
                k2 = chuan_so(t2.get("ja"))
                if k2 in mine and _v(t2.get("meaning")) and _v(t2.get("meaning")).strip() != mine[k2].strip():
                    cb.append(f"K-NQ: câu trích '{strip_marks(t2.get('ja'))[:30]}' có nghĩa khác ở câu {d2.get('question_id')}_{d2.get('cau_con')} – xem có dịch sai không (không tự thống nhất)")
                    mine.pop(k2, None)
    # K-TT – tính toán trong analysis
    for o in opts:
        for x in kiem_tra_tinh_toan(_v(o.get("analysis")) or ""):
            if not x["dung"]:
                cb.append(f"K-TT: options[{o.get('index', 0) - 1}].analysis: '{x['bieu_thuc']} = {x['ket_qua_ghi']}' – Python tính lại = {x['tinh_lai']:g} (gắn cờ tinh_toan nếu sai thật)")
    # K-FT / trường không dùng
    if doc.get("full_translation") is not None and "co_ban_dich" not in co:
        cb.append("K-FT: full_translation có nội dung nhưng s0 không thấy bản dịch ngữ liệu trong lời giải – kiểm tra lại")
    for k in ("summary", "key_info"):
        if doc.get(k) is not None:
            loi.append(f"K-FT: {k} phải null (lời giải dạng này không có phần đó)")
    return loi, cb


# =====================================================================
# 7. Hiển thị (Excel CTV)
# =====================================================================
def render(d, lang, show, bold, TK=None):
    def t(o):
        return show((o or {}).get(lang) or "") if isinstance(o, dict) else ""
    q, c = d.get("question") or {}, d.get("correct") or {}
    out = [f"{bold('【Câu hỏi】')} {show(q.get('ja') or '')}"]
    if q.get("meaning"):
        out.append(f"   Nghĩa: {t(q['meaning'])}")
    for blk in d.get("full_translation") or []:
        out.append(bold("【Bản dịch ngữ liệu】") + (f" {blk.get('label')}" if blk.get("label") else ""))
        for ln in blk.get("lines") or []:
            s = ((ln.get("speaker") + ": ") if ln.get("speaker") else "") + (show(ln.get("ja")) + " – " if ln.get("ja") else "") + t(ln.get("meaning"))
            out.append("   " + s.replace("\n", "\n   "))
    for o in d.get("options") or []:
        out.append(bold(f"{o.get('index')}. ") + show(o.get("option_ja") or ""))
        if o.get("meaning"):
            out.append("   Nghĩa: " + t(o["meaning"]))
        for x in o.get("quotes") or []:
            out.append("   Trích dẫn: 「" + show(x.get("ja") or "") + "」" + (f"\n      ({t(x.get('meaning'))})" if x.get("meaning") else ""))
        if o.get("analysis"):
            out.append("   " + t(o["analysis"]).replace("\n", "\n   "))
        out.append("   → " + ("ĐÚNG" if o.get("is_match") else "SAI"))
    out.append(bold("【Đáp án】") + f" {c.get('index')}. {show(c.get('option_ja') or '')}")
    if TK is not None:
        out += TK.render(d, lang, show, bold)
    return "\n".join(out)


# =====================================================================
# 8. GĐ2 – dịch tiếng Hàn
# =====================================================================
NOTE_JA = "[dịch từ tiếng Nhật]"
JA_PATH_RE = re.compile(r"^\$\.(?:question\.meaning|options\[(\d+)\]\.meaning|options\[(\d+)\]\.quotes\[(\d+)\]\.meaning|full_translation\[(\d+)\]\.lines\[(\d+)\]\.meaning)$")


def nguon_ja(doc, path):
    """Câu tiếng Nhật làm nguồn dịch cho trường nghĩa (None nếu không có tiếng Nhật → dịch từ tiếng Việt)."""
    m = JA_PATH_RE.match(path)
    if not m:
        return None
    try:
        node = get_path(doc, parse_path(path)[:-1])
    except (KeyError, IndexError, TypeError):
        return None
    ja = node.get("option_ja") if m.group(1) is not None else node.get("ja")
    return ja if isinstance(ja, str) and JA_RE.search(strip_marks(ja)) else None


def _loai_ja(path):
    if path == "$.question.meaning":
        return "Nghĩa CÂU HỎI – dịch câu hỏi tiếng Nhật sang câu hỏi tiếng Hàn tự nhiên."
    if ".quotes[" in path:
        return "Nghĩa CÂU TRÍCH từ ngữ liệu – dịch sát câu tiếng Nhật (giữ số, giờ, ngày, giá, tên riêng); cùng câu trích ở chỗ khác phải dịch giống hệt."
    if path.startswith("$.full_translation"):
        return "Một câu của bản dịch ngữ liệu – dịch câu tiếng Nhật."
    return "Nghĩa LỰA CHỌN – dịch sát lựa chọn tiếng Nhật (lựa chọn sai vẫn dịch đúng như đang viết, không sửa cho hợp lý); lựa chọn chỉ là số / giá / giờ thì giữ nguyên số + đơn vị tiếng Hàn."


def danh_dau(fmap, doc, cfg=None):
    """nguon_dich: 'ja' (dịch thẳng từ tiếng Nhật – nghĩa câu hỏi / lựa chọn / câu trích / câu bản dịch có tiếng Nhật) hoặc 'vi'."""
    bat = ((cfg or {}).get("dich_tu_nhat") or {}).get("dung", True)
    for f in fmap:
        ja = nguon_ja(doc, f["path"]) if bat else None
        if ja:
            f["nguon_dich"], f["ja"] = "ja", ja
        else:
            f["nguon_dich"] = "vi"
    return fmap


def prefill(fmap, fixed, tm):
    """Câu cố định / bộ nhớ dịch chỉ cho trường dịch từ tiếng Việt."""
    from .dich import prefill as _pf
    filled, todo = _pf([f for f in fmap if f["nguon_dich"] == "vi"], fixed, tm)
    keep = set(todo) | {f["id"] for f in fmap if f["nguon_dich"] == "ja"}
    return filled, [f["id"] for f in fmap if f["id"] in keep]


def tagged_copy(doc, fmap, lang):
    """Bản gửi tác tử TẠO: trường 'ja' → {id, dich_tu_tieng_nhat, cau_tieng_nhat, ban_viet_tham_khao, luu_y}."""
    from .dich import tagged_copy as _tc
    d = _tc(doc, fmap, lang)
    for f in fmap:
        if f["nguon_dich"] != "ja":
            continue
        path = parse_path(f["path"])
        parent = get_path(d, path[:-1])
        parent[path[-1]] = {"id": f["id"], "dich_tu_tieng_nhat": True, "cau_tieng_nhat": f["ja"],
                            "ban_viet_tham_khao": f["vi"], "luu_y": _loai_ja(f["path"])}
    return d


_SO_RE = re.compile(r"\d+(?:[.,:]\d+)*")


def cac_so(s):
    """Multiset các số (NFKC, bỏ dấu phân cách nghìn) – để so số giữa bản nguồn và bản dịch."""
    s = unicodedata.normalize("NFKC", strip_marks(s or ""))
    out = collections.Counter()
    for m in _SO_RE.findall(s):
        out[re.sub(r"(?<=\d)[.,](?=\d{3}(?!\d))", "", m)] += 1
    return out


def kiem_tra_so(doc_ko, fmap, lang="ko"):
    """D-SO (cảnh báo): số trong bản Hàn phải trùng số trong bản nguồn (tiếng Nhật với trường dịch từ tiếng Nhật, tiếng Việt với phần còn lại)."""
    out = []
    by = {f["path"]: f for f in fmap}
    for fp, o in iter_lang_fields(doc_ko):
        ps = path_str(fp)
        ko = o.get(lang)
        if not isinstance(ko, str):
            continue
        f = by.get(ps) or {}
        nguon = f.get("ja") if f.get("nguon_dich") == "ja" else o.get("vi")
        a, b = cac_so(nguon), cac_so(ko)
        if not a and not b:
            continue
        if a != b:
            thieu, thua = sorted((a - b).elements()), sorted((b - a).elements())
            out.append(f"D-SO: {ps}: số khác bản nguồn" + (f" – thiếu {thieu[:6]}" if thieu else "") + (f" – thừa {thua[:6]}" if thua else ""))
    return out


PARTICLE_RE = re.compile(r"⟪([぀-ゟ゠-ヿー]+)⟫[\"'”」』)）]*(이라는|라는|이라고|라고|이며|며|으로|로|은|는|이|가|을|를|과|와)(?![가-힣])")
BATCHIM = {"이라는", "이라고", "이며", "으로", "은", "이", "을", "과"}
DOI = {"이라는": "라는", "라는": "이라는", "이라고": "라고", "라고": "이라고", "이며": "며", "며": "이며", "으로": "로", "로": "으로",
       "은": "는", "는": "은", "이": "가", "가": "이", "을": "를", "를": "을", "과": "와", "와": "과"}


def tro_tu(doc_ko, lang="ko"):
    """D12 (cảnh báo): trợ từ ngay sau ⟪kana⟫ theo âm cuối cách đọc (ん → có patchim)."""
    out = []
    for fp, o in iter_lang_fields(doc_ko):
        for m in PARTICLE_RE.finditer(o.get(lang) or ""):
            kana, p = m.group(1), m.group(2)
            if (kana[-1] == "ん") != (p in BATCHIM):
                out.append(f"D12: {path_str(fp)}: '{kana}' + '{p}' – trợ từ sai theo âm cuối, nên là '{DOI[p]}'")
    return out


_BO_QUA_JA = ("nội dung ⟪ ⟫ khác bản tiếng Việt", "furigana khác bản tiếng Việt", "tỷ lệ độ dài KO/VI", "câu cố định phải dịch là",
              "văn phong -습니다", "có tiếng Nhật nằm ngoài ⟪ ⟫")


def loc_kiem_tra(msgs, fmap):
    """Trường dịch từ tiếng Nhật: bỏ các phép so với bản Việt không áp dụng."""
    jp = [f["path"] for f in fmap if f.get("nguon_dich") == "ja"]
    out = []
    for m in msgs:
        p = next((x for x in jp if re.search(re.escape(x) + r"(?![\w\[])", m)), None)
        if p and any(k in m for k in _BO_QUA_JA):
            continue
        out.append(m)
    return out


def d4_key(f, doc):
    if f.get("nguon_dich") == "ja":
        return NOTE_JA + " " + strip_marks(f.get("ja") or nguon_ja(doc, f["path"]) or "")
    return None


# =====================================================================
# 9. Thứ tự chạy theo ngữ liệu
# =====================================================================
def tao_thu_tu_ngu_lieu(recs, cfg):
    """Thứ tự chạy: ngữ liệu bắt buộc (config.thu_tu_chay.dau_tien) → xen kẽ N1–N5 tới ~so_cau_dau câu → còn lại theo file dữ liệu.
    Các câu con của một ngữ liệu luôn liền nhau. Cột 'lo': lô ~lo câu, không cắt đôi ngữ liệu."""
    tc = cfg.get("thu_tu_chay") or {}
    rng = random.Random(tc.get("seed", 2026))
    n_dau, lo = tc.get("so_cau_dau", 100), tc.get("lo", 10)
    nhom, thu_tu = {}, []
    for r in recs:
        if r["question_id"] not in nhom:
            thu_tu.append(r["question_id"])
        nhom.setdefault(r["question_id"], []).append(r)
    for q in nhom:
        nhom[q].sort(key=lambda r: r["cau_con"])
    dau = [q for q in tc.get("dau_tien", []) if q in nhom]
    hang = {}
    for k in ["N1", "N2", "N3", "N4", "N5"]:
        pool = [q for q in thu_tu if nhom[q][0]["cap_do"] == k and q not in dau and all(r["khuon_goc"] != "trong" for r in nhom[q])]
        rng.shuffle(pool)
        hang[k] = pool
    dem = sum(len(nhom[q]) for q in dau)
    theo_cap = collections.Counter(nhom[q][0]["cap_do"] for q in dau for _ in nhom[q])
    while dem < n_dau and any(hang.values()):        # luôn lấy ngữ liệu của cấp đang ít CÂU nhất → ~20 câu mỗi cấp
        k = min((x for x in ["N1", "N2", "N3", "N4", "N5"] if hang[x]), key=lambda x: (theo_cap[x], x))
        q = hang[k].pop(0)
        dau.append(q)
        dem += len(nhom[q])
        theo_cap[k] += len(nhom[q])
    con = [q for q in thu_tu if q not in set(dau)]
    rows, so_lo, trong_lo = [], 1, 0
    for d_i, q in enumerate(dau + con, 1):
        g = nhom[q]
        if trong_lo and trong_lo + len(g) > lo + 1:
            so_lo, trong_lo = so_lo + 1, 0
        for r in g:
            rows.append({"stt": len(rows) + 1, "sample_id": r["sample_id"], "question_id": r["question_id"], "cap_do": r["cap_do"],
                         "doan": d_i, "lo": so_lo})
        trong_lo += len(g)
        if trong_lo >= lo:
            so_lo, trong_lo = so_lo + 1, 0
    return rows
