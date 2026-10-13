"""Dạng 19 – Nghe hiểu diễn đạt: phần riêng giai đoạn 2.

  - prompt.utterance.meaning          (nghĩa câu tình huống)
    options[i].sentence.meaning       (nghĩa câu nói của lựa chọn i)
      ← dịch TRỰC TIẾP từ câu tiếng Nhật (tác tử TẠO không thấy bản Việt của các trường này – như dạng 07); không dùng câu cố định / bộ nhớ dịch (khóa theo tiếng Việt).
  - options[i].analysis (phân tích) ← dịch từ tiếng Việt, văn phong -습니다.
Kiểm tra riêng: D7 ({ } của nghĩa câu ↔ câu Nhật), D12 (trợ từ sau ⟪kana⟫), D15 (cùng câu Nhật trong một câu → cùng bản Hàn).
D4 (s2_kiem_tra): nghĩa câu so theo câu tiếng Nhật giữa các câu.
"""
import re

import _dang  # noqa: F401  (đặt sys.path tới thư mục Vie-Kor để import pipeline_chung)
from pipeline_chung.common import get_path, parse_path, strip_marks
from pipeline_chung.dich import prefill, tagged_copy

NOTE_JA = "[dịch từ tiếng Nhật]"
NOTE_KH = "[kết hợp]"
NOTE_VD = "[tham khảo]"
JA_RE = re.compile(r"^\$\.(?:prompt\.(utterance)\.meaning|options\[(\d+)\]\.(sentence)\.meaning)$")


def _is_ja(path, cfg):
    return bool(JA_RE.match(path)) and bool((cfg or {}).get("dich_tu_nhat", {}).get("truong", True))


def nguon_ja(doc, path):
    m = JA_RE.match(path)
    if not m:
        raise KeyError(path)
    if m.group(1):
        u = (doc.get("prompt") or {}).get("utterance") or {}
        return {"cau_tieng_nhat": u.get("ja"), "cach_doc": None,
                "luu_y": "Câu TÌNH HUỐNG của đề nghe (… 何と言いますか): dịch tự nhiên sang tiếng Hàn, bám sát câu Nhật (ai làm gì, với ai); "
                         "'何と言いますか' → '뭐라고 말합니까?' (theo cách hỏi của đề JLPT tiếng Hàn)."}
    o = (doc.get("options") or [])[int(m.group(2))]
    s = o.get("sentence") or {}
    return {"cau_tieng_nhat": s.get("ja"), "cach_doc": None,
            "luu_y": (f"Câu nói của lựa chọn {o.get('index')} – " + ("ĐÁP ÁN: " if o.get("is_correct") else "lựa chọn SAI: ")
                      + "dịch thành câu nói tiếng Hàn tự nhiên, ĐÚNG mức lịch sự / sắc thái của câu Nhật (kính ngữ → 존댓말, thân mật → 반말; "
                        "ai làm cho ai: てあげる / てくれる / てもらう; xin phép / đề nghị / nhờ vả). Lời chào cố định dùng câu tương đương tiếng Hàn "
                        "(いただきます → 잘 먹겠습니다). Lựa chọn sai vẫn dịch đúng như câu đang viết, không sửa cho hợp tình huống.")}


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
            parent = get_path(d, path[:-1])
            parent[path[-1]] = {"id": f["id"], "dich_tu_tieng_nhat": True, "nguon": nguon_ja(doc, f["path"])}
    return d


# ---------------- kiểm tra riêng ----------------
_BO_QUA_JA = ("nội dung ⟪ ⟫ khác bản tiếng Việt", "furigana khác bản tiếng Việt", "tỷ lệ độ dài KO/VI", "câu cố định phải dịch là",
              "văn phong -습니다")   # nghĩa câu nói giữ mức lịch sự của câu Nhật (반말 / -요 / -습니다)


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


def kiem_tra_v3(doc_ko, lang="ko"):
    """D7 (lỗi): nghĩa câu tiếng Hàn có số { } khác câu tiếng Nhật (khi câu tiếng Nhật có { }).
    D15 (cảnh báo): hai câu nói giống hệt nhau (tiếng Nhật) trong cùng một câu nhưng bản dịch khác nhau.
    D12 (cảnh báo): trợ từ sau ⟪kana⟫ theo âm cuối cách đọc."""
    loi, canh_bao = [], []
    u = (doc_ko.get("prompt") or {}).get("utterance") or {}
    items = [("prompt.utterance", u)] + [(f"options[{i}].sentence", o.get("sentence") or {}) for i, o in enumerate(doc_ko.get("options") or [])]
    seen = {}
    for name, s in items:
        ja, ko = s.get("ja") or "", _ko(s.get("meaning"), lang)
        if ko and "{" in ja and (ja.count("{"), ja.count("}")) != (ko.count("{"), ko.count("}")):
            loi.append(f"D7: {name}.meaning – số dấu {{ }} khác câu tiếng Nhật")
        k = strip_marks(ja).replace(" ", "")
        if ko and k:
            if k in seen and seen[k][1] != ko:
                canh_bao.append(f"D15: {name}.meaning khác bản dịch của {seen[k][0]} dù câu tiếng Nhật giống nhau – nên thống nhất")
            seen.setdefault(k, (name, ko))
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
    """D12 (cảnh báo): trợ từ ngay sau ⟪kana⟫ phải theo âm cuối cách đọc: ん → dạng có patchim, nguyên âm → dạng không patchim."""
    from pipeline_chung.common import iter_lang_fields, path_str
    out = []
    for fp, o in iter_lang_fields(doc_ko):
        for m in PARTICLE_RE.finditer(o.get(lang) or ""):
            kana, p = m.group(1), m.group(2)
            if (kana[-1] == "ん") != (p in BATCHIM):
                out.append(f"D12: {path_str(fp)}: '{kana}' + '{p}' – trợ từ sai theo âm cuối, nên là '{DOI[p]}'")
    return out
