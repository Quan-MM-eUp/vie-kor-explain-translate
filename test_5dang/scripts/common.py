"""Hàm dùng chung cho các script trong test_5dang.

Không gọi API nào. Chỉ đọc/ghi file và xử lý văn bản.
"""
import csv
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # thư mục test_5dang
csv.field_size_limit(10**9)

# ---------- cấu hình & đường dẫn ----------
def load_config():
    with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as f:
        return json.load(f)

def p(*parts):
    """Đường dẫn tính từ thư mục test_5dang."""
    return os.path.normpath(os.path.join(ROOT, *parts))

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def load_env():
    """Đọc OPENAI_API_KEY từ biến môi trường hoặc file .env (test_5dang/.env hoặc ../.env)."""
    for candidate in (p(".env"), p("..", ".env")):
        if os.path.exists(candidate):
            with open(candidate, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return os.environ.get("OPENAI_API_KEY")

# ---------- mẫu ----------
def load_samples():
    path = p("samples", "samples.csv")
    if not os.path.exists(path):
        sys.exit("Chưa có samples/samples.csv – hãy chạy scripts/select_samples.py trước.")
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def load_raw(sample_id):
    return load_json(p("samples", "raw", sample_id + ".json"))

# ---------- xử lý văn bản ----------
JA_CHARS = r"぀-ヿ㐀-䶿一-鿿ｦ-ﾟ々〆ヶ"
JA_RE = re.compile(f"[{JA_CHARS}]+")
VI_DIACRITIC_RE = re.compile(
    r"[ăâđêôơưàáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ]", re.I)
HANGUL_RE = re.compile(r"[가-힯ᄀ-ᇿ㄰-㆏]")
LOCK_RE = re.compile(r"⟪(.*?)⟫", re.S)

def clean_html(s):
    """Bỏ furigana (<rt>), đổi xuống dòng, bỏ thẻ, giải mã &nbsp;…"""
    if not s:
        return ""
    s = re.sub(r"<rt>.*?</rt>|<rp>.*?</rp>", "", s, flags=re.S)
    s = re.sub(r"<br\s*/?>|</div>|</p>|</li>|</tr>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s).replace(" ", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n", s)
    return s.strip()

def strip_markers(s):
    """Bỏ các dấu ⟪ ⟫ và { } để so sánh nội dung."""
    return s.replace("⟪", "").replace("⟫", "").replace("{", "").replace("}", "") if s else ""

def norm_ja(s):
    return re.sub(r"\s+", "", strip_markers(s or ""))

def vi_words(s):
    """Tách từ tiếng Việt (bỏ tiếng Nhật, dấu câu, số)."""
    s = JA_RE.sub(" ", strip_markers(s or "").lower())
    return re.findall(r"[a-zà-ỹđ]+", s)

def iter_lang_fields(obj, path="$"):
    """Duyệt mọi object có khóa "vi" (trường cần dịch). Trả về (đường dẫn, object)."""
    if isinstance(obj, dict):
        if isinstance(obj.get("vi"), str):
            yield path, obj
        for k, v in obj.items():
            yield from iter_lang_fields(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from iter_lang_fields(v, f"{path}[{i}]")

def iter_sentences(obj, path="$"):
    """Duyệt các object Sentence (có ja + reading + meaning)."""
    if isinstance(obj, dict):
        if {"ja", "reading", "meaning"} <= set(obj):
            yield path, obj
        for k, v in obj.items():
            yield from iter_sentences(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from iter_sentences(v, f"{path}[{i}]")

def drop_lang(obj, lang):
    """Bản sao của JSON sau khi bỏ khóa ngôn ngữ `lang` trong mọi trường cần dịch."""
    if isinstance(obj, dict):
        return {k: drop_lang(v, lang) for k, v in obj.items()
                if not (k == lang and isinstance(obj.get("vi"), str))}
    if isinstance(obj, list):
        return [drop_lang(v, lang) for v in obj]
    return obj

def raw_ja_runs(raw):
    """Các đoạn tiếng Nhật xuất hiện trong lời giải gốc (dùng để kiểm tra không mất nội dung)."""
    g = raw.get("giai_thich_vi", "")
    if g.lstrip().startswith("{"):          # khuôn JSON cũ (cách đọc kanji)
        try:
            text = "\n".join(_all_strings(json.loads(g)))
        except json.JSONDecodeError:
            text = g
        text = clean_html(text)
    else:
        text = clean_html(g)
    return sorted({m for m in JA_RE.findall(text)})

def explanation_text(g):
    """Lời giải (HTML hoặc JSON cũ) → văn bản thường."""
    g = g or ""
    if g.lstrip().startswith("{"):
        try:
            return clean_html("\n".join(_all_strings(json.loads(g))))
        except json.JSONDecodeError:
            pass
    return clean_html(g)


def raw_vi_text(raw):
    return explanation_text(raw.get("giai_thich_vi", ""))

def _all_strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from _all_strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from _all_strings(v)

# Nhãn cố định trong lời giải tiếng Việt – không lưu trong JSON (app tự hiển thị),
# nên bỏ khỏi văn bản gốc trước khi đo độ phủ. Thêm nhãn mới vào đây nếu cần.
LABEL_PATTERNS = [
    r"(?im)^\s*(câu hỏi|đề bài|cách đọc|nghĩa|từ|thể từ điển|câu hoàn chỉnh)\s*:",
    r"(?im)^\s*(phân tích|lựa chọn đúng|thông tin tham khảo)\s*:?\s*$",
    r"(?m)^\s*###\s*$",
]

def strip_labels(text):
    for pat in LABEL_PATTERNS:
        text = re.sub(pat, " ", text)
    return text
