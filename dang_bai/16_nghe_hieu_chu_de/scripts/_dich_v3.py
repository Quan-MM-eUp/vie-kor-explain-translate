"""Dạng 16 – Nghe hiểu chủ đề: phần riêng giai đoạn 2 (dịch Hàn).

Dịch TRỰC TIẾP từ tiếng Nhật (tác tử TẠO không thấy bản Việt của các trường này – chủ ý; bản Việt chỉ hiện để đối chiếu khi soát):
  - full_translation[g].lines[k].meaning   (từng dòng lời thoại – văn nói, giữ quan hệ / kính ngữ theo câu Nhật; dòng ja = null → dịch từ VI)
  - question.meaning                         (câu hỏi)
  - options[i].quotes[j].meaning             (câu trích lời thoại – trùng dòng lời thoại thì dịch GIỐNG HỆT dòng đó)
  - options[i].meaning                       (nghĩa lựa chọn chữ; lựa chọn tranh không có meaning)
Phần còn lại (options[i].analysis, summary) dịch từ tiếng Việt, văn phong -습니다. Trường dịch từ tiếng Nhật không dùng câu cố định / bộ nhớ dịch.
"""
import re

import _dang  # noqa: F401  (đặt sys.path tới thư mục Vie-Kor để import pipeline_chung)
import _nghe as NH
from pipeline_chung.common import get_path, iter_lang_fields, parse_path, path_str, strip_marks
from pipeline_chung.dich import prefill, tagged_copy

NOTE_JA = "[dịch từ tiếng Nhật]"
NOTE_KH = "[kết hợp]"
NOTE_VD = "[tham khảo]"
JA_RE = re.compile(r"^\$\.(?:(question)\.meaning|options\[(\d+)\]\.(meaning)|options\[(\d+)\]\.quotes\[(\d+)\]\.meaning"
                   r"|full_translation\[(\d+)\]\.lines\[(\d+)\]\.meaning)$")


def _nguon(doc, path):
    """(loại, câu tiếng Nhật, thông tin thêm) hoặc None nếu trường không dịch từ tiếng Nhật."""
    m = JA_RE.match(path)
    if not m:
        return None
    try:
        if m.group(1):
            ja = (doc.get("question") or {}).get("ja")
            return ("cau_hoi", ja, None) if ja else None
        if m.group(3):
            o = doc["options"][int(m.group(2))]
            ja = o.get("option_ja") or ""
            return None if NH.TRANH_RE.match(strip_marks(ja)) or not ja.strip() else ("lua_chon", ja, o.get("index"))
        if m.group(5):
            q = doc["options"][int(m.group(4))]["quotes"][int(m.group(5))]
            return ("trich", q.get("ja"), doc["options"][int(m.group(4))].get("index")) if q.get("ja") else None
        ln = doc["full_translation"][int(m.group(6))]["lines"][int(m.group(7))]
        return ("loi_thoai", ln.get("ja"), ln.get("speaker")) if ln.get("ja") else None
    except (KeyError, IndexError, TypeError):
        return None


LUU_Y = {
    "loi_thoai": "Dòng lời thoại{nn} – dịch sang tiếng Hàn VĂN NÓI tự nhiên, giữ quan hệ / mức kính ngữ theo câu Nhật (thân mật → 반말, lịch sự → -요/-습니다); "
                 "giữ nguyên '(i)', '{{ }}', '…' như câu Nhật; không dịch nhãn người nói; đọc cả lời thoại để dịch nhất quán (tên người, đại từ).",
    "cau_hoi": "Câu hỏi của bài nghe – trùng dòng câu hỏi trong lời thoại thì dịch GIỐNG HỆT bản dịch dòng đó.",
    "trich": "Câu trích lời thoại (căn cứ cho lựa chọn {nn}) – trùng nguyên dòng lời thoại thì dịch GIỐNG HỆT bản dịch dòng đó; là một phần của dòng thì dịch "
             "khớp phần tương ứng; giữ mức kính ngữ như lời thoại.",
    "lua_chon": "Nghĩa của lựa chọn {nn} – cụm ngắn, sát câu Nhật (dạng câu như lựa chọn: '…する' → '…한다' / '…하기').",
}


def nguon_ja(doc, path):
    n = _nguon(doc, path)
    if not n:
        raise KeyError(path)
    loai, ja, them = n
    nn = (f" (người nói: {them})" if them else "") if loai == "loi_thoai" else (str(them) if them else "")
    return {"cau_tieng_nhat": ja, "loai": loai, "luu_y": LUU_Y[loai].format(nn=nn)}


def nguon_ja_text(doc, path):
    return (_nguon(doc, path) or (None, "", None))[1] or ""


def danh_dau(fmap, doc, cfg=None):
    """nguon_dich: ja (dịch thẳng từ tiếng Nhật) · vi."""
    for f in fmap:
        if _nguon(doc, f["path"]):
            f["nguon_dich"], f["ja"] = "ja", nguon_ja_text(doc, f["path"])
        else:
            f["nguon_dich"] = "vi"
    return fmap


def prefill_v3(fmap, fixed, tm):
    """Câu cố định / bộ nhớ dịch chỉ cho trường dịch từ tiếng Việt."""
    filled, todo = prefill([f for f in fmap if f["nguon_dich"] == "vi"], fixed, tm)
    keep = set(todo) | {f["id"] for f in fmap if f["nguon_dich"] == "ja"}
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
              "văn phong -습니다", "số dấu { } khác bản tiếng Việt")


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
    return ((o or {}).get(lang) or "").strip() if isinstance(o, dict) else ""


def kiem_tra_v3(doc_ko, lang="ko"):
    """D7 (lỗi): trường dịch từ tiếng Nhật – số { } của bản Hàn khác câu Nhật.
    D15 (cảnh báo): câu trích / câu hỏi trùng nguyên một dòng lời thoại nhưng bản Hàn khác bản Hàn của dòng đó.
    D16 (cảnh báo): dòng lời thoại có '(i)' nhưng bản Hàn mất '(i)'.
    D12 (cảnh báo): trợ từ sau ⟪kana⟫ theo âm cuối cách đọc."""
    loi, cb = [], []
    dong = {}
    for gi, g in enumerate(doc_ko.get("full_translation") or []):
        for li, ln in enumerate(g.get("lines") or []):
            ja, ko = ln.get("ja") or "", _ko(ln.get("meaning"), lang)
            p = f"full_translation[{gi}].lines[{li}]"
            if ja and ko:
                dong.setdefault(NH._k(ja), (p, ko))
                if "{" in ja and (ja.count("{"), ja.count("}")) != (ko.count("{"), ko.count("}")):
                    loi.append(f"D7: {p}.meaning – số dấu {{ }} khác câu tiếng Nhật")
                if "(i)" in ja and "(i)" not in ko:
                    cb.append(f"D16: {p}.meaning – câu Nhật có '(i)' nhưng bản Hàn không có")
    ds = [("question", doc_ko.get("question") or {})]
    for oi, o in enumerate(doc_ko.get("options") or []):
        ds += [(f"options[{oi}].quotes[{qi}]", q) for qi, q in enumerate(o.get("quotes") or [])]
    for name, s in ds:
        ja, ko = s.get("ja") or "", _ko(s.get("meaning"), lang)
        if not (ja and ko):
            continue
        if "{" in ja and (ja.count("{"), ja.count("}")) != (ko.count("{"), ko.count("}")):
            loi.append(f"D7: {name}.meaning – số dấu {{ }} khác câu tiếng Nhật")
        hit = dong.get(NH._k(ja))
        if hit and strip_marks(hit[1]).replace(" ", "") != strip_marks(ko).replace(" ", ""):
            cb.append(f"D15: {name}.meaning khác bản dịch của dòng lời thoại trùng nguyên văn ({hit[0]}) – nên thống nhất")
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
