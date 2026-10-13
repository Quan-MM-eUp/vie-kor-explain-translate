"""Dạng 18 – Nghe hiểu khái quát: phần riêng giai đoạn 2.

  Dịch TRỰC TIẾP từ tiếng Nhật (bản Việt chỉ tham khảo, giữ sắc thái nói 반말 / 존댓말 theo câu Nhật):
    full_translation[g].lines[k].meaning   (từng dòng lời thoại)
    question.meaning                       (câu hỏi)
    options[i].meaning                     (lựa chọn)
    options[i].quotes[j].meaning           (câu trích – trùng dòng lời thoại thì dịch giống dòng đó)
  Dịch từ tiếng Việt: options[i].analysis (văn phong -습니다).
Trường dịch từ tiếng Nhật không dùng câu cố định / bộ nhớ dịch.
"""
import collections
import re

import _dang as D
from pipeline_chung.common import get_path, iter_lang_fields, parse_path, path_str, strip_marks
from pipeline_chung.dich import prefill, tagged_copy

NOTE_JA = "[dịch từ tiếng Nhật]"
NOTE_KH = "[kết hợp]"
NOTE_VD = "[tham khảo]"
JA_RE = re.compile(r"^\$\.(?:full_translation\[(\d+)\]\.lines\[(\d+)\]\.meaning|question\.meaning|options\[(\d+)\]\.meaning"
                   r"|options\[(\d+)\]\.quotes\[(\d+)\]\.meaning)$")


def _is_ja(path, cfg=None):
    return bool(JA_RE.match(path))


def nguon_ja(doc, path):
    m = JA_RE.match(path)
    if not m:
        raise KeyError(path)
    node = get_path(doc, parse_path(path)) or {}
    vi = node.get("vi")
    if m.group(1) is not None:
        ln = doc["full_translation"][int(m.group(1))]["lines"][int(m.group(2))]
        return {"cau_tieng_nhat": ln.get("ja"), "nguoi_noi": ln.get("speaker"), "ban_viet_tham_khao": vi,
                "luu_y": "Dòng lời thoại L" + str(int(m.group(2)) + 1) + " – dịch thành câu nói tiếng Hàn tự nhiên, đúng sắc thái của câu Nhật "
                         "(thể thường → 반말, です/ます → 존댓말, kính ngữ nhân viên ↔ khách → 존댓말 / 하십시오체); không thêm nhãn người nói; giữ '(i)' nếu có."}
    if path == "$.question.meaning":
        q = doc.get("question") or {}
        return {"cau_tieng_nhat": q.get("ja"), "ban_viet_tham_khao": vi,
                "luu_y": "Câu hỏi của bài nghe – dịch sát câu Nhật, đuôi -니까? / -습니까? như sách luyện thi JLPT tiếng Hàn."}
    if m.group(3) is not None:
        o = doc["options"][int(m.group(3))]
        return {"cau_tieng_nhat": o.get("option_ja"), "ban_viet_tham_khao": vi,
                "luu_y": "Lựa chọn " + str(o.get("index")) + " – dịch sát lựa chọn tiếng Nhật (cụm danh từ giữ dạng cụm, câu giữ dạng câu)."}
    o = doc["options"][int(m.group(4))]
    x = o["quotes"][int(m.group(5))]
    return {"cau_tieng_nhat": x.get("ja"), "ban_viet_tham_khao": vi,
            "luu_y": "Câu trích từ lời thoại – nếu trùng (một phần) dòng lời thoại thì dịch GIỐNG bản dịch dòng đó; giữ sắc thái nói."}


def nguon_ja_text(doc, path):
    return nguon_ja(doc, path)["cau_tieng_nhat"] or ""


def danh_dau(fmap, doc, cfg):
    for f in fmap:
        if _is_ja(f["path"], cfg):
            f["nguon_dich"], f["ja"] = "ja", nguon_ja_text(doc, f["path"])
        else:
            f["nguon_dich"] = "vi"
    return fmap


def prefill_v3(fmap, fixed, tm):
    """Câu cố định / bộ nhớ dịch chỉ cho trường dịch từ tiếng Việt (analysis)."""
    filled, todo_vi = prefill([f for f in fmap if f["nguon_dich"] == "vi"], fixed, tm)
    keep = set(todo_vi) | {f["id"] for f in fmap if f["nguon_dich"] == "ja"}
    return filled, [f["id"] for f in fmap if f["id"] in keep]


def tagged_copy_v3(doc, fmap, lang):
    d = tagged_copy(doc, fmap, lang)
    for f in fmap:
        if f["nguon_dich"] == "ja":
            path = parse_path(f["path"])
            parent = get_path(d, path[:-1])
            parent[path[-1]] = {"id": f["id"], "dich_tu_tieng_nhat": True, "nguon": nguon_ja(doc, f["path"])}
    return d


_BO_QUA_JA = ("nội dung ⟪ ⟫ khác bản tiếng Việt", "furigana khác bản tiếng Việt", "tỷ lệ độ dài KO/VI", "câu cố định phải dịch là",
              "văn phong -습니다", "số dấu { } khác bản tiếng Việt")   # bản Hàn còn chữ Việt / tiếng Nhật trần vẫn báo


def loc_kiem_tra(msgs, fmap):
    jp = [f["path"] for f in fmap if f.get("nguon_dich") == "ja"]
    out = []
    for m in msgs:
        p = next((x for x in jp if re.search(re.escape(x) + r"(?![\w\[])", m)), None)
        if p and any(k in m for k in _BO_QUA_JA):
            continue
        out.append(m)
    return out


def _ko(o, lang):
    return ((o or {}).get(lang) or "").strip() if o else ""


def _k(s):
    return re.sub(r"[\s　。．、,，.！!？?「」『』・（）()…]", "", strip_marks(s or ""))


def kiem_tra_v3(doc_ko, lang="ko"):
    """D15 (cảnh báo): câu trích trùng nguyên một dòng lời thoại nhưng bản Hàn khác bản Hàn của dòng đó.
    D16 (cảnh báo): cùng một câu trích (ja) ở nhiều lựa chọn nhưng dịch khác nhau.
    D12 (cảnh báo): trợ từ sau ⟪kana⟫ theo âm cuối cách đọc."""
    loi, cb = [], []
    dong = {}
    for g in doc_ko.get("full_translation") or []:
        for i, ln in enumerate(g.get("lines") or []):
            if ln.get("meaning") and _ko(ln["meaning"], lang):
                dong.setdefault(_k(ln.get("ja")), (i + 1, _ko(ln["meaning"], lang)))
    seen = collections.defaultdict(set)
    for oi, o in enumerate(doc_ko.get("options") or []):
        for qi, x in enumerate(o.get("quotes") or []):
            k, ko = _k(x.get("ja")), _ko(x.get("meaning"), lang)
            if not k or not ko:
                continue
            seen[k].add(ko)
            if k in dong and dong[k][1] != ko:
                cb.append(f"D15: options[{oi}].quotes[{qi}]: câu trích trùng dòng L{dong[k][0]} nhưng bản Hàn khác – nên thống nhất ('{dong[k][1][:40]}')")
    for k, v in seen.items():
        if len(v) > 1:
            cb.append(f"D16: câu trích '{k[:20]}…' có {len(v)} bản Hàn khác nhau giữa các lựa chọn")
    cb += tro_tu(doc_ko, lang)
    return loi, cb


def d4_key(f, doc):
    if f.get("nguon_dich") == "ja":
        return NOTE_JA + " " + strip_marks(nguon_ja_text(doc, f["path"]))
    return None


PARTICLE_RE = re.compile(r"⟪([぀-ゟ゠-ヿー]+)⟫[\"'”」』)）]*(이라는|라는|이라고|라고|이며|며|으로|로|은|는|이|가|을|를|과|와)(?![가-힣])")
BATCHIM = {"이라는", "이라고", "이며", "으로", "은", "이", "을", "과"}
DOI = {"이라는": "라는", "라는": "이라는", "이라고": "라고", "라고": "이라고", "이며": "며", "며": "이며", "으로": "로", "로": "으로",
       "은": "는", "는": "은", "이": "가", "가": "이", "을": "를", "를": "을", "과": "와", "와": "과"}


def tro_tu(doc_ko, lang="ko"):
    out = []
    for fp, o in iter_lang_fields(doc_ko):
        for m in PARTICLE_RE.finditer(o.get(lang) or ""):
            kana, p = m.group(1), m.group(2)
            if (kana[-1] == "ん") != (p in BATCHIM):
                out.append(f"D12: {path_str(fp)}: '{kana}' + '{p}' – trợ từ sai theo âm cuối, nên là '{DOI[p]}'")
    return out
