"""Dạng 13 – Đọc hiểu tổng hợp: phần riêng giai đoạn 2.

  Dịch TRỰC TIẾP từ câu tiếng Nhật (tác tử TẠO không thấy bản Việt của các trường này – như dạng 07/09):
    question.meaning                      (nghĩa câu hỏi)
    options[i].meaning                    (nghĩa lựa chọn)
    options[i].quotes[j].meaning          (nghĩa câu trích – câu trích giống nhau dịch giống nhau, D4 theo câu Nhật)
  Dịch từ tiếng Việt: options[i].analysis (văn phong -습니다), full_translation[k].lines[l].meaning (bản dịch đoạn văn).
Trường dịch từ tiếng Nhật không dùng câu cố định / bộ nhớ dịch.
"""
import re

import _dang  # noqa: F401  (đặt sys.path tới thư mục Vie-Kor để import pipeline_chung)
from pipeline_chung.common import get_path, parse_path, strip_marks
from pipeline_chung.dich import prefill, tagged_copy

NOTE_JA = "[dịch từ tiếng Nhật]"
NOTE_KH = "[kết hợp]"
NOTE_VD = "[tham khảo]"
JA_RE = re.compile(r"^\$\.(?:(question)\.meaning|options\[(\d+)\]\.meaning|options\[(\d+)\]\.quotes\[(\d+)\]\.meaning)$")


def _is_ja(path, cfg):
    return bool(JA_RE.match(path)) and bool((cfg or {}).get("dich_tu_nhat", {}).get("truong", True))


def nguon_ja(doc, path):
    m = JA_RE.match(path)
    if not m:
        raise KeyError(path)
    node = get_path(doc, parse_path(path))
    so_ngoac = (node.get("vi") or "").count("{")
    chung = f" Bản Việt có {so_ngoac} cặp {{ }} – bản Hàn giữ đúng {so_ngoac} cặp quanh phần tương ứng." if so_ngoac else ""
    if m.group(1):
        q = doc.get("question") or {}
        return {"cau_tieng_nhat": q.get("ja"), "loai": "nghia_cau_hoi",
                "luu_y": "Nghĩa CÂU HỎI: dịch câu hỏi tiếng Nhật sang câu hỏi tiếng Hàn tự nhiên (giữ ①②, 'A와 B', 「…」 → '…' / 「…」 như câu Nhật)." + chung}
    if m.group(2) is not None:
        o = (doc.get("options") or [])[int(m.group(2))]
        return {"cau_tieng_nhat": o.get("option_ja"), "loai": "nghia_lua_chon",
                "luu_y": f"Nghĩa LỰA CHỌN {o.get('index')}: dịch sát câu tiếng Nhật (chủ thể A/B, phủ định, so sánh, mức độ) – lựa chọn sai vẫn dịch đúng như câu đang viết." + chung}
    o = (doc.get("options") or [])[int(m.group(3))]
    x = (o.get("quotes") or [])[int(m.group(4))]
    return {"cau_tieng_nhat": x.get("ja"), "loai": "nghia_cau_trich",
            "luu_y": "Nghĩa CÂU TRÍCH từ đoạn văn: dịch sát câu tiếng Nhật, đúng mạch đoạn văn; câu trích giống nhau ở các lựa chọn / câu con khác dịch GIỐNG HỆT nhau." + chung}


def nguon_ja_text(doc, path):
    return nguon_ja(doc, path)["cau_tieng_nhat"] or ""


def danh_dau(fmap, doc, cfg):
    """nguon_dich: ja (dịch thẳng từ tiếng Nhật) · vi."""
    for f in fmap:
        if _is_ja(f["path"], cfg):
            f["nguon_dich"], f["ja"] = "ja", nguon_ja_text(doc, f["path"])
        else:
            f["nguon_dich"] = "vi"
    return fmap


def prefill_v3(fmap, fixed, tm):
    """Câu cố định / bộ nhớ dịch: chỉ cho trường dịch từ tiếng Việt."""
    filled, todo_vi = prefill([f for f in fmap if f["nguon_dich"] == "vi"], fixed, tm)
    keep = set(todo_vi) | {f["id"] for f in fmap if f["nguon_dich"] == "ja"}
    return filled, [f["id"] for f in fmap if f["id"] in keep]


def tagged_copy_v3(doc, fmap, lang):
    d = tagged_copy(doc, fmap, lang)
    for f in fmap:
        if f["nguon_dich"] == "ja":
            path = parse_path(f["path"])
            get_path(d, path[:-1])[path[-1]] = {"id": f["id"], "dich_tu_tieng_nhat": True, "nguon": nguon_ja(doc, f["path"])}
    return d


# ---------------- kiểm tra riêng ----------------
_BO_QUA_JA = ("nội dung ⟪ ⟫ khác bản tiếng Việt", "furigana khác bản tiếng Việt", "tỷ lệ độ dài KO/VI", "câu cố định phải dịch là",
              "văn phong -습니다")


def loc_kiem_tra(msgs, fmap):
    jp = [f["path"] for f in fmap if f.get("nguon_dich") == "ja"]
    out = []
    for m in msgs:
        p = next((x for x in jp if re.search(re.escape(x) + r"(?![\w\[])", m)), None)
        if p and any(k in m for k in _BO_QUA_JA):
            continue
        out.append(m)
    return out


def kiem_tra_v3(doc_ko, lang="ko"):
    """D12 (cảnh báo): trợ từ sau ⟪kana⟫ theo âm cuối cách đọc. D15 (cảnh báo): cùng câu trích (câu Nhật) trong một câu mà nghĩa Hàn khác nhau."""
    loi, canh_bao = [], []
    seen = {}
    for i, o in enumerate(doc_ko.get("options") or []):
        for j, x in enumerate(o.get("quotes") or []):
            k = strip_marks(x.get("ja") or "").replace(" ", "")
            ko = ((x.get("meaning") or {}).get(lang) or "").strip()
            if k and ko:
                if k in seen and seen[k][1] != ko:
                    canh_bao.append(f"D15: options[{i}].quotes[{j}] cùng câu trích với {seen[k][0]} nhưng bản dịch khác – nên thống nhất")
                seen.setdefault(k, (f"options[{i}].quotes[{j}]", ko))
    canh_bao += tro_tu(doc_ko, lang)
    return loi, canh_bao


def d4_key(f, doc):
    if f.get("nguon_dich") == "ja":
        return NOTE_JA + " " + strip_marks(nguon_ja_text(doc, f["path"]))
    return None


PARTICLE_RE = re.compile(r"⟪([぀-ゟ゠-ヿー]+)⟫[\"'”」』)）]*(이라는|라는|이라고|라고|이며|며|으로|로|은|는|이|가|을|를|과|와)(?![가-힣])")
BATCHIM = {"이라는", "이라고", "이며", "으로", "은", "이", "을", "과"}
DOI = {"이라는": "라는", "라는": "이라는", "이라고": "라고", "라고": "이라고", "이며": "며", "며": "이며", "으로": "로", "로": "으로",
       "은": "는", "는": "은", "이": "가", "가": "이", "을": "를", "를": "을", "과": "와", "와": "과"}


def tro_tu(doc_ko, lang="ko"):
    """D12 (cảnh báo): trợ từ ngay sau ⟪kana⟫: ん → dạng có patchim, nguyên âm → dạng không patchim (chỉ xét khối toàn kana)."""
    from pipeline_chung.common import iter_lang_fields, path_str
    out = []
    for fp, o in iter_lang_fields(doc_ko):
        for m in PARTICLE_RE.finditer(o.get(lang) or ""):
            kana, p = m.group(1), m.group(2)
            if (kana[-1] == "ん") != (p in BATCHIM):
                out.append(f"D12: {path_str(fp)}: '{kana}' + '{p}' – trợ từ sai theo âm cuối, nên là '{DOI[p]}'")
    return out
