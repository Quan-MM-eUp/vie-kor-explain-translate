"""Chuẩn hóa lời giải gốc (HTML) trước khi đưa cho GPT – theo mục 8 của workflow tổng quát.

- Furigana <ruby> → ｜chữ gốc《cách đọc》 (xử lý <rp>, thuộc tính, thẻ lồng, nhiều <rt> trong 1 ruby)
- Đánh dấu → { } (workflow tổng quát mục 3a), chọn bằng tham số danh_dau:
    "u+b" (quy tắc chung, mặc định): gạch chân <u>, <span … underline>, in đậm <b>, <strong>,
          <span … font-weight: 700/bold>, và { } / ｛ ｝ viết sẵn. Thẻ lồng / liền nhau gộp thành 1 cặp;
          nhãn cố định in đậm (PHÂN TÍCH, Câu hỏi…) chỉ bỏ thẻ; đoạn chỉ gồm dấu câu / khoảng trắng bỏ thẻ và ghi vào `rac`.
    "u"   (quy tắc cũ, dạng 01 đang dùng tạm): chỉ <u>.
- Xuống dòng: <br>, </div>, </p>, </li>, </tr> → \\n ; <li> → "- "
- Bỏ các thẻ còn lại, giải mã &nbsp; &amp; …
- Ghi lại ruby hỏng (không có chữ gốc, cách đọc không phải kana, lồng sai) – không đổi sang 《》, giữ phần chữ.

Không sửa câu chữ tiếng Việt / tiếng Nhật.
"""
import html as _html
import re

from .common import FURI_RE, KANJI_RE

RUBY_RE = re.compile(r"<ruby\b[^>]*>(.*?)</ruby>", re.S | re.I)
RT_SPLIT_RE = re.compile(r"<rt\b[^>]*>(.*?)</rt>", re.S | re.I)
RP_RE = re.compile(r"<rp\b[^>]*>.*?</rp>", re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")
KANA_ONLY_RE = re.compile(r"^[぀-ゟ゠-ヿｦ-ﾟー・\s]+$")
PAREN_READING_RE = re.compile(r"[㐀-䶿一-鿿々〆ヶ][㐀-䶿一-鿿々〆ヶ぀-ゟ]*\s?[（(][぀-ゟ゠-ヿー]+[）)]")


def _text(s):
    return _html.unescape(TAG_RE.sub("", s or "")).replace("\xa0", " ")


def _ruby(match, broken):
    inner = match.group(1)
    raw = match.group(0)
    if re.search(r"<ruby\b", inner, re.I):             # ruby lồng nhau → hỏng
        broken.append(raw)
        return _text(inner).replace("{", "").replace("}", "")
    inner = RP_RE.sub("", inner)
    parts = RT_SPLIT_RE.split(inner)                    # [chữ0, đọc0, chữ1, đọc1, …, phần còn lại]
    out = []
    for i in range(0, len(parts) - 1, 2):
        base, rt = _text(parts[i]), _text(parts[i + 1]).strip()
        pre = post = ""
        b = base.strip()
        # gạch chân nằm bên trong chữ gốc → đưa ra ngoài furigana
        while b.startswith("{"):
            pre += "{"; b = b[1:].strip()
        while b.endswith("}"):
            post += "}"; b = b[:-1].strip()
        if not rt:
            out.append(pre + b + post)                  # ruby không có cách đọc: giữ chữ gốc
        elif not b or not KANA_ONLY_RE.match(rt):
            broken.append(raw)
            out.append(pre + (b + rt).replace("{", "").replace("}", "") + post)
        else:
            out.append(f"{pre}｜{b}《{rt}》{post}")
    if len(parts) % 2 == 1:
        out.append(_text(parts[-1]))
    return "".join(out)


LABEL_WORDS = ["Từ", "Câu hỏi", "Cách đọc", "Nghĩa", "Thể từ điển", "PHÂN TÍCH", "LỰA CHỌN ĐÚNG", "THÔNG TIN THAM KHẢO"]
_LABEL_ALT = "|".join(re.escape(x) for x in LABEL_WORDS)
_LABEL_ONLY_RE = re.compile(rf"^\s*(?:{_LABEL_ALT})?\s*[:：]?\s*$", re.I)
_LABEL_HEAD_RE = re.compile(rf"^(\s*(?:{_LABEL_ALT})\s*[:：]\s*)(.*)$", re.I | re.S)
_MARK_TAG_RE = re.compile(r"<(/?)(u|b|strong|span)\b([^>]*)>", re.I)
_MARK_SPAN_RE = re.compile(r"text-decoration[^;\"']*underline|font-weight\s*:\s*(?:bold|[6-9]00)", re.I)
_HAS_LETTER_RE = re.compile(r"[^\W_]")


def _marks_to_braces(s):
    """Đổi mọi thẻ gạch chân / in đậm thành { } theo độ sâu (thẻ lồng nhau chỉ ra 1 cặp)."""
    s = s.replace("｛", "<u>").replace("｝", "</u>").replace("{", "<u>").replace("}", "</u>")
    out, depth, spans, pos = [], 0, [], 0
    for m in _MARK_TAG_RE.finditer(s):
        out.append(s[pos:m.start()])
        pos = m.end()
        close, name, attrs = m.group(1) == "/", m.group(2).lower(), m.group(3)
        if name == "span":
            if not close:
                is_mark = bool(_MARK_SPAN_RE.search(attrs))
                spans.append(is_mark)
                if is_mark:
                    depth += 1
                    out.append("{" if depth == 1 else "")
                else:
                    out.append(m.group(0))          # span thường: để _text bỏ sau
                continue
            if not (spans.pop() if spans else False):
                out.append(m.group(0))
                continue
        elif not close:
            depth += 1
            out.append("{" if depth == 1 else "")
            continue
        if depth > 0:
            depth -= 1
            out.append("}" if depth == 0 else "")
    out.append(s[pos:])
    if depth > 0:
        out.append("}")
    return "".join(out)


def _clean_braces(s, rac):
    """Sau khi bỏ HTML: tách cặp { } qua nhiều dòng, bỏ nhãn cố định và đánh dấu rác."""
    s = re.sub(r"\{([^{}]*)\}", lambda m: "{" + m.group(1).replace("\n", "}\n{") + "}", s)

    def fix(m):
        c = m.group(1)
        if _LABEL_ONLY_RE.match(c) and c.strip():
            if not _HAS_LETTER_RE.search(c):
                rac.append(c)
            return c
        h = _LABEL_HEAD_RE.match(c)
        if h:
            rest = h.group(2)
            return h.group(1) + (("{" + rest + "}") if _HAS_LETTER_RE.search(rest) else rest)
        if not _HAS_LETTER_RE.search(c):
            if c.strip():
                rac.append(c)
            return c
        lead, trail = c[:len(c) - len(c.lstrip())], c[len(c.rstrip()):]
        return lead + "{" + c.strip() + "}" + trail          # khoảng trắng đầu/cuối đưa ra ngoài { }
    return re.sub(r"\{([^{}]*)\}", fix, s)


def normalize_html(s, danh_dau="u+b", rac=None):
    """HTML → văn bản chuẩn hóa. Trả về (văn bản, danh sách ruby hỏng).
    rac: nếu truyền list thì nhận các đoạn đánh dấu rác đã bỏ thẻ (chỉ ở chế độ "u+b")."""
    broken = []
    rac = [] if rac is None else rac
    if not s:
        return "", broken
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    # đánh dấu trước (để ruby nằm trong { })
    if danh_dau == "u":
        s = re.sub(r"<u\b[^>]*>", "{", s, flags=re.I)
        s = re.sub(r"</u>", "}", s, flags=re.I)
    else:
        s = _marks_to_braces(s)
    s = RUBY_RE.sub(lambda m: _ruby(m, broken), s)
    s = re.sub(r"<rt\b[^>]*>.*?</rt>|<rp\b[^>]*>.*?</rp>", "", s, flags=re.S | re.I)  # rt/rp lẻ loi
    if danh_dau != "u":      # <div>/<p> mở đầu dòng mới ngay sau chữ (vd "…。<div>Cách đọc: …") cũng là xuống dòng
        s = re.sub(r"(</div>|</p>)(\s*)(<div\b[^>]*>|<p\b[^>]*>)", r"\1\2", s, flags=re.I)
        s = re.sub(r"<div\b[^>]*>|<p\b[^>]*>", "\n", s, flags=re.I)
    s = re.sub(r"<li\b[^>]*>", "\n- ", s, flags=re.I)
    s = re.sub(r"<br\s*/?>|</div>|</p>|</li>|</tr>|</h\d>", "\n", s, flags=re.I)
    s = _text(s)
    # gộp các đoạn đánh dấu liền nhau, bỏ cặp rỗng
    s = re.sub(r"\}([ \t]*)\{", r"\1", s)
    s = re.sub(r"\{\s*\}", "", s)
    if danh_dau != "u":
        s = _clean_braces(s, rac)
        s = re.sub(r"\}([ \t]*)\{", r"\1", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = "\n".join(line.strip() for line in s.split("\n"))
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"\n\s*\n(- )", r"\n\1", s)          # không để dòng trống giữa các mục danh sách
    return s.strip(), broken


def normalize_json(obj, danh_dau="u+b", rac=None):
    """Chuẩn hóa mọi chuỗi trong JSON cũ, giữ nguyên cấu trúc. Trả về (JSON mới, ruby hỏng)."""
    broken = []

    def walk(o):
        if isinstance(o, str):
            t, b = normalize_html(o, danh_dau, rac)
            broken.extend(b)
            return t
        if isinstance(o, dict):
            return {k: walk(v) for k, v in o.items()}
        if isinstance(o, list):
            return [walk(v) for v in o]
        return o
    return walk(obj), broken


def paren_readings(text):
    """Cách đọc viết trong ngoặc ngay sau chữ Hán, vd 六本木坂（ろっぽんぎざか） – giữ nguyên, chỉ liệt kê."""
    return PAREN_READING_RE.findall(text or "")


def has_reserved_marks(raw):
    """Lời giải gốc đã có sẵn ký hiệu dành cho furigana (｜ 《 》) → cần nhóm sửa dữ liệu gốc."""
    return any(ch in (raw or "") for ch in "｜《》")


def pairs(text):
    return FURI_RE.findall(text or "")


def mark_segments(text):
    """Danh sách đoạn nằm trong { } (đã bỏ furigana / ⟪ ⟫ / khoảng trắng) – dùng để so với JSON."""
    from .common import norm_ja
    return [norm_ja(x) for x in re.findall(r"\{([^{}]*)\}", text or "")]
