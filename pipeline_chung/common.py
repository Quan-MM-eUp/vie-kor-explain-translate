"""Hàm dùng chung: đọc/ghi file, đọc CSV gốc, .env, biểu thức nhận dạng chữ, duyệt trường cần dịch."""
import csv
import hashlib
import json
import os
import re

VIE_KOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # thư mục Vie-Kor
csv.field_size_limit(10**9)


# ---------- file ----------
def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(obj, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def read_csv(path):
    """Đọc CSV (UTF-8, có/không BOM), bỏ ký tự NUL."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        text = f.read().replace("\0", "")
    return list(csv.DictReader(text.splitlines(keepends=True)))


def write_csv(rows, path, fields=None):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fields = fields or (list(rows[0].keys()) if rows else [])
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def sha(text):
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()[:16]


ENV_FILES_USED = []


def load_env(extra_dirs=()):
    """Đọc .env (không in giá trị). Tìm lần lượt: các thư mục truyền vào, Vie-Kor/, Vie-Kor/test_5dang/."""
    for d in list(extra_dirs) + [VIE_KOR, os.path.join(VIE_KOR, "test_5dang")]:
        path = os.path.join(d, ".env")
        if os.path.exists(path):
            if path not in ENV_FILES_USED:
                ENV_FILES_USED.append(path)
            with open(path, encoding="utf-8-sig") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return os.environ.get("OPENAI_API_KEY")


# ---------- nhận dạng chữ ----------
KANA = "぀-ゟ゠-ヿｦ-ﾟー"
JA_CHARS = "぀-ヿ㐀-䶿一-鿿ｦ-ﾟ々〆ヶ"
JA_RE = re.compile(f"[{JA_CHARS}]+")
KANJI_RE = re.compile("[㐀-䶿一-鿿々〆ヶ]")
VI_DIACRITIC_RE = re.compile(
    r"[ăâđêôơưàáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ]", re.I)
HANGUL_RE = re.compile(r"[가-힯ᄀ-ᇿ㄰-㆏]")
LOCK_RE = re.compile(r"⟪(.*?)⟫", re.S)
FURI_RE = re.compile(r"｜([^｜《》\n]+)《([^《》\n]+)》")


def furigana_pairs(text):
    return FURI_RE.findall(text or "")


def strip_marks(s):
    """Bỏ ⟪ ⟫ { } ｜ và phần 《cách đọc》 để so sánh nội dung chữ."""
    s = FURI_RE.sub(lambda m: m.group(1), s or "")
    for ch in "⟪⟫{}｜":
        s = s.replace(ch, "")
    return s


def norm_ja(s):
    return re.sub(r"\s+", "", strip_marks(s))


def vi_words(s):
    s = JA_RE.sub(" ", strip_marks(s).lower())
    return re.findall(r"[a-zà-ỹđ]+", s)


# ---------- duyệt JSON ----------
def iter_lang_fields(obj, path=()):
    """Duyệt mọi trường cần dịch (object có khóa "vi" kiểu chuỗi). Trả về (đường dẫn dạng tuple, object)."""
    if isinstance(obj, dict):
        if isinstance(obj.get("vi"), str):
            yield path, obj
        for k, v in obj.items():
            yield from iter_lang_fields(v, path + (k,))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from iter_lang_fields(v, path + (i,))


def iter_strings(obj, path=()):
    """Duyệt mọi chuỗi trong JSON. Trả về (đường dẫn, chuỗi)."""
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from iter_strings(v, path + (k,))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from iter_strings(v, path + (i,))


def path_str(path):
    out = "$"
    for p_ in path:
        out += f"[{p_}]" if isinstance(p_, int) else f".{p_}"
    return out


def parse_path(s):
    """'$.options[1].analysis' → ('options', 1, 'analysis')"""
    parts = []
    for name, idx in re.findall(r"\.([^.\[\]]+)|\[(\d+)\]", s):
        parts.append(int(idx) if idx else name)
    return tuple(parts)


def get_path(obj, path):
    for p_ in path:
        obj = obj[p_]
    return obj


def drop_lang(obj, lang):
    """Bản sao JSON đã bỏ khóa ngôn ngữ `lang` ở mọi trường cần dịch."""
    if isinstance(obj, dict):
        return {k: drop_lang(v, lang) for k, v in obj.items() if not (k == lang and isinstance(obj.get("vi"), str))}
    if isinstance(obj, list):
        return [drop_lang(v, lang) for v in obj]
    return obj
