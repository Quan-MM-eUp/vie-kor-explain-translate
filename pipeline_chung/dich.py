"""Tách và ghép trường dịch – mục 6a của workflow tổng quát.

GPT nhận cả JSON làm ngữ cảnh (mã f1…fn gắn ngay tại trường cần dịch) nhưng chỉ trả về {"f1": "…", …}.
Python giữ bảng đối chiếu mã → đường dẫn → nội dung vi, rồi ghép bản dịch vào đúng chỗ, có kiểm tra khớp nội dung.
Câu cố định (bảng thuật ngữ) và bộ nhớ dịch được điền sẵn, không gửi GPT.
"""
import copy
import re

from .common import get_path, iter_lang_fields, parse_path, path_str


def key_norm(s):
    """Chuẩn hóa để tra câu cố định / bộ nhớ dịch: gộp khoảng trắng."""
    return re.sub(r"\s+", " ", (s or "").strip())


def build_map(doc):
    return [{"id": f"f{i}", "path": path_str(p), "vi": o["vi"]} for i, (p, o) in enumerate(iter_lang_fields(doc), 1)]


def tagged_copy(doc, fmap, lang):
    """Bản gửi GPT: mỗi trường cần dịch thành {"id": "fN", "vi": "…"} (bỏ bản dịch cũ nếu có)."""
    d = copy.deepcopy(doc)
    for f in fmap:
        path = parse_path(f["path"])
        parent = get_path(d, path[:-1]) if path else None
        node = {"id": f["id"], "vi": f["vi"]}
        if path:
            parent[path[-1]] = node
        else:
            d = node
    return d


def prefill(fmap, fixed, tm):
    """Điền sẵn từ câu cố định (ưu tiên) rồi bộ nhớ dịch. Trả về ({id: {"text", "nguon"}}, [id cần gửi GPT])."""
    fixed_n = {key_norm(k): v for k, v in (fixed or {}).items()}
    filled, todo = {}, []
    for f in fmap:
        k = key_norm(f["vi"])
        if k in fixed_n:
            filled[f["id"]] = {"text": fixed_n[k], "nguon": "cau_co_dinh"}
        elif tm and k in tm:
            filled[f["id"]] = {"text": tm[k]["ko"], "nguon": f"bo_nho_dich:{tm[k].get('nguon', '')}"}
        else:
            todo.append(f["id"])
    return filled, todo


def output_schema(ids):
    return {"type": "object", "additionalProperties": False,
            "properties": {i: {"type": "string", "description": "Bản dịch của trường có id này"} for i in ids},
            "required": list(ids)}


def merge(vi_doc, fmap, translations, lang):
    """Ghép bản dịch vào bản sao của vi_doc. Trả về (JSON đã ghép, danh sách lỗi)."""
    d = copy.deepcopy(vi_doc)
    errors = []
    ids = {f["id"] for f in fmap}
    extra = sorted(set(translations) - ids)
    if extra:
        errors.append(f"Output có mã lạ: {extra}")
    for f in fmap:
        text = translations.get(f["id"])
        if not isinstance(text, str) or not text.strip():
            errors.append(f"{f['id']} ({f['path']}): thiếu bản dịch")
            continue
        try:
            node = get_path(d, parse_path(f["path"]))
        except (KeyError, IndexError, TypeError):
            errors.append(f"{f['id']}: đường dẫn {f['path']} không còn tồn tại")
            continue
        if not isinstance(node, dict) or node.get("vi") != f["vi"]:
            errors.append(f"{f['id']} ({f['path']}): nội dung vi khác bảng đối chiếu – không ghép")
            continue
        node[lang] = text
    n_done = sum(1 for _, o in iter_lang_fields(d) if isinstance(o.get(lang), str) and o[lang].strip())
    if not errors and n_done != len(fmap):
        errors.append(f"Số trường có '{lang}' ({n_done}) ≠ số mã ({len(fmap)})")
    return d, errors
