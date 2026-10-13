"""Hàm dùng chung cho các dạng NGHE HIỂU (schema reading_listening.v1) – đưa lên từ dạng 21 (2026-10-08), dùng lại cho 16/17/18.

- loi_thoai_dong(html)          : lời thoại HTML (cột transcript_vi – tên cột sai, thực là tiếng Nhật) → danh sách dòng sạch
                                   (bỏ thẻ / <b> / { }, bỏ khoảng trắng chen giữa chữ Nhật)
- cat_loi_thoai(dong, lua_chon) : cắt lời dẫn đề ở đầu (3番 / まず話を聞いてください…) và câu hỏi + danh sách lựa chọn ở cuối
- tach_nguoi_noi(dong)          : '男：…' → ('男', '…'); không có nhãn → (None, dòng)
- so_loi_thoai(lines, goc)      : so full_translation.lines[].ja với lời thoại gốc (K-FT) → chữ thừa / chữ thiếu
- tim_trich(cau, goc)           : câu trích có trong lời thoại không ('khop' / 'mot_phan' / 'khong')
- furigana_lua_chon(s)          : '<手帳(てちょう)>' → '｜手帳《てちょう》' (cách ghi furigana của cột lựa chọn)
Không sửa câu chữ – chỉ bỏ rác trình bày (thẻ, khoảng trắng chen giữa chữ Nhật).
"""
import difflib
import re
import unicodedata

from .common import strip_marks
from .normalize import normalize_html

JA_CLS = r"぀-ヿ㐀-䶿一-鿿々〆ヶｦ-ﾟ。、「」『』？！・…ー（）〜～：:"
_SP_JA_RE = re.compile(rf"(?<=[{JA_CLS}])[ 　\t]+(?=[{JA_CLS}])")
_NUM = r"[1-4１-４]"
OPT_PREFIX_RE = re.compile(rf"^\s*{_NUM}\s*(?:[\.．。、・:：)）]\s*|\s+)")
Q_LABEL_RE = re.compile(r"^\s*(?:質問\s*[0-9０-９一二三]*|問題\s*[0-9０-９]+|❔|Question\s*\d*|[QＱ](?=\s*[:：]))\s*[:：.．]?\s*")
DAU_RE = re.compile(r"まず話を聞いてください|問題用紙に何も印刷|^\s*[0-9０-９]+\s*番\s*$")
SEP_RE = re.compile(r"^[~～\-ー・…\s]+$")
SPK_RE = re.compile(r"^\s*([^\s：:「」『』。、？！?!（）()…]{1,8}?)\s*[：:]\s*(.+)$", re.S)
FURI_LC_RE = re.compile(r"<([^<>()（）]+)[(（]([぀-ゟ゠-ヿー]+)[)）]>")


def nfkc(s):
    return unicodedata.normalize("NFKC", s or "")


def bo_cach_chu_nhat(s):
    """Bỏ khoảng trắng chen giữa chữ Nhật ('話 し て い ま す' → '話しています')."""
    prev = None
    while prev != s:
        prev, s = s, _SP_JA_RE.sub("", s)
    return s


def loi_thoai_dong(html):
    """HTML lời thoại → (danh sách dòng, số chỗ đã bỏ khoảng trắng chen giữa chữ Nhật)."""
    s = (html or "").replace("\\&quot;", "").replace("&quot;", "")
    t, _ = normalize_html(s, "u")
    t = t.replace("{", "").replace("}", "")
    out, n = [], 0
    for line in t.split("\n"):
        line = line.strip()
        if not line:
            continue
        b = bo_cach_chu_nhat(line)
        n += b != line
        out.append(b)
    return out, n


def furigana_lua_chon(s):
    return FURI_LC_RE.sub(lambda m: f"｜{m.group(1)}《{m.group(2)}》", s or "")


def _k(s):
    """Khóa so sánh: NFKC, bỏ furigana / ⟪ ⟫ / { }, bỏ khoảng trắng và dấu câu."""
    s = nfkc(strip_marks(s))
    return re.sub(r"[\s、。,，.．・…「」『』？！?!（）()\[\]\"'“”:：~〜～\-ー]", "", s)


def la_cau_hoi(line):
    t = line.strip()
    return len(t) < 150 and bool(re.search(r"(か|か。|か？|か\?|？|\?)\s*$", t))


def cat_loi_thoai(dong, lua_chon=()):
    """Trả về (dòng lời thoại, câu hỏi bị cắt ở cuối [theo thứ tự], dòng lời dẫn bị cắt ở đầu)."""
    L = list(dong)
    lc = {_k(OPT_PREFIX_RE.sub("", x)) for x in lua_chon if x and _k(x)}
    dau = []
    while L[:1] and DAU_RE.search(L[0]) and len(dau) < 3:
        dau.append(L.pop(0))
    cau_hoi, saw_opt = [], False
    while L:
        l = L[-1]
        body = OPT_PREFIX_RE.sub("", l)
        if SEP_RE.match(l):
            L.pop(); continue
        if Q_LABEL_RE.match(l) and Q_LABEL_RE.sub("", l) != l.strip():
            cau_hoi.insert(0, L.pop()); saw_opt = False; continue
        if OPT_PREFIX_RE.match(l) and la_cau_hoi(body) and not saw_opt:
            cau_hoi.insert(0, L.pop()); continue            # '1.  男の人はどのコースを選びましたか。'
        if (OPT_PREFIX_RE.match(l) and len(body) <= 80) or (_k(body) and _k(body) in lc):
            L.pop(); saw_opt = True; continue
        if saw_opt and la_cau_hoi(l):
            cau_hoi.insert(0, L.pop()); saw_opt = False; continue
        break
    return L, cau_hoi, dau


def bo_nhan_cau_hoi(q):
    """'質問１：食堂の…' → '食堂の…'; '1.  男の人は…' → '男の人は…'."""
    q = Q_LABEL_RE.sub("", bo_cach_chu_nhat(q or ""))
    return re.sub(r"^[.．\s]+", "", OPT_PREFIX_RE.sub("", q)).strip()


def so_cau_hoi(q):
    """Số thứ tự câu hỏi ghi trong nhãn ('質問２' → 2, '質問一' → 1); không có → None."""
    m = re.match(r"^\s*(?:(?:質問|問題)\s*([0-9０-９一二三])|([1-4１-４])\s*[\.．])", q or "")
    if not m:
        return None
    c = m.group(1) or m.group(2)
    return {"一": 1, "二": 2, "三": 3}.get(c) or int(nfkc(c))


def tach_nguoi_noi(line):
    m = SPK_RE.match(line or "")
    if m and re.search(rf"[{JA_CLS[:-6]}A-Za-zＡ-Ｚａ-ｚ]", m.group(1)) and len(m.group(2).strip()) > 0:
        return m.group(1), m.group(2).strip()
    return None, (line or "").strip()


def _k_loi_thoai(s, nguoi_noi=()):
    s = nfkc(strip_marks(s))
    for sp in sorted({nfkc(x) for x in nguoi_noi if x}, key=len, reverse=True):
        s = re.sub(re.escape(sp) + r"\s*:", "", s)
    return re.sub(r"\s", "", s)


def so_loi_thoai(lines, goc_dong):
    """So lines[].ja (đã bỏ nhãn người nói) với lời thoại gốc. Trả về (đoạn thừa, đoạn thiếu, tỷ lệ thiếu)."""
    nguoi = [ln.get("speaker") for ln in lines]
    J = "".join(_k_loi_thoai(ln.get("ja") or "") for ln in lines)
    D = _k_loi_thoai("".join(goc_dong), nguoi)
    if not D:
        return [], [], 0.0
    sm = difflib.SequenceMatcher(None, D, J, autojunk=False)
    thua, thieu = [], []
    for t, i1, i2, j1, j2 in sm.get_opcodes():
        if t in ("delete", "replace"):
            thieu.append(D[i1:i2])
        if t in ("insert", "replace"):
            thua.append(J[j1:j2])
    return thua, thieu, sum(len(x) for x in thieu) / len(D)


def tim_trich(cau, goc):
    """'khop' (có nguyên văn) / 'mot_phan' (khớp ≥ 60%) / 'khong'."""
    a, b = _k(cau), _k(goc)
    if not a or not b:
        return "khong"
    if a in b:
        return "khop"
    m = difflib.SequenceMatcher(None, a, b, autojunk=False).find_longest_match(0, len(a), 0, len(b))
    return "mot_phan" if m.size >= 0.6 * len(a) else "khong"

