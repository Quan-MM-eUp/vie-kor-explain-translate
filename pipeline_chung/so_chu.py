"""So chữ giữa lời giải gốc (tiếng Việt) và JSON của GPT – GPT đã đổi gì so với bản gốc.

GPT chỉ được chép nguyên, nên mọi chỗ khác nhau về CHỮ đều được liệt kê. Các khác biệt do
quy ước JSON thì bỏ qua: ⟪ ⟫, { }, ｜《》 (furigana), khoảng trắng, nhãn cố định đã bỏ.

Cách dùng (từ script của dạng bài):
    so_chu(src_segments, doc_segments)  – mỗi đối số là danh sách chuỗi theo cùng thứ tự
    → {"so_cho_doi": n, "doi": [{"loai": "thay|xoa|them", "goc": "...", "gpt": "...", "ngu_canh": "..."}]}
"""
import difflib
import re

from .common import strip_marks

TOKEN_RE = re.compile(r"[^\W_]+|[^\w\s]", re.U)
LOAI = {"replace": "thay", "delete": "xoa", "insert": "them"}


def tokens(text):
    return TOKEN_RE.findall(strip_marks(text or ""))


def _join(toks):
    """Ghép lại cho dễ đọc: cách sau chữ/dấu câu thường, trước '(' và dấu mở ngoặc kép."""
    out = ""
    for t in toks:
        word = re.match(r"[^\W_]", t)
        if out and ((word and re.search(r"[^\W_,.:;!?)\]」』%]$|[,.:;!?)\]」』]$", out)) or t in "(「『\"'"):
            out += " "
        out += t
    return out


def so_chu(src_segments, doc_segments, ngu_canh=6):
    a = [t for s in src_segments for t in tokens(s)]
    b = [t for s in doc_segments for t in tokens(s)]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    doi = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        doi.append({"loai": LOAI[op], "goc": _join(a[i1:i2]), "gpt": _join(b[j1:j2]),
                    "ngu_canh": "…" + _join(a[max(0, i1 - ngu_canh):i1]) + " [·] " + _join(a[i2:i2 + ngu_canh]) + "…"})
    return {"so_cho_doi": len(doi), "ty_le_giong": round(sm.ratio(), 4), "doi": doi}


def tom_tat(res, n=5):
    """Chuỗi ngắn cho CSV."""
    ten = {"thay": "thay", "xoa": "bỏ", "them": "thêm"}
    return "\n".join(f"{ten[d['loai']]}: {d['goc']!r} → {d['gpt']!r}" for d in res["doi"][:n]) + \
        (f"\n… (+{res['so_cho_doi'] - n} chỗ)" if res["so_cho_doi"] > n else "")
