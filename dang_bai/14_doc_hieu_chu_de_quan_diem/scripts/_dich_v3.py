"""Dạng 14 – Đọc hiểu chủ đề / quan điểm: phần riêng giai đoạn 2.

  - question.meaning                 (nghĩa câu hỏi – giữ ①②, { })
    options[i].meaning               (nghĩa câu lựa chọn)
    options[i].quotes[j].meaning     (nghĩa câu trích từ đoạn văn)
      ← dịch TRỰC TIẾP từ tiếng Nhật (tác tử TẠO không thấy bản tiếng Việt của các trường này – như dạng 07/09).
  - analysis, full_translation dịch từ tiếng Việt.
Trường dịch từ tiếng Nhật không dùng câu cố định / bộ nhớ dịch; câu trích giống nhau phải dịch giống nhau (D4 theo câu Nhật, D15).
"""
import re

import _dang  # noqa: F401  (đặt sys.path tới thư mục Vie-Kor để import pipeline_chung)
from pipeline_chung.common import get_path, iter_lang_fields, parse_path, path_str, strip_marks
from pipeline_chung.dich import prefill, tagged_copy

NOTE_JA = "[dịch từ tiếng Nhật]"
JA_RE_PATH = re.compile(r"^\$\.(?:(question)\.meaning|options\[(\d+)\]\.meaning|options\[(\d+)\]\.quotes\[(\d+)\]\.meaning)$")


def nguon_ja(doc, path):
    m = JA_RE_PATH.match(path)
    if not m:
        raise KeyError(path)
    if m.group(1):
        q = doc.get("question") or {}
        return {"cau_tieng_nhat": q.get("ja"),
                "luu_y": "Nghĩa CÂU HỎI: dịch câu hỏi tiếng Nhật tự nhiên; giữ mốc ①②… và cụm 「…」 được hỏi (dịch cụm trong nháy '…'); "
                         "câu hỏi nhiều dòng giữ xuống dòng."}
    if m.group(2) is not None:
        o = (doc.get("options") or [])[int(m.group(2))]
        return {"cau_tieng_nhat": o.get("option_ja"),
                "luu_y": f"Nghĩa LỰA CHỌN {o.get('index')}: dịch sát câu tiếng Nhật (giữ phủ định, bị động, sai khiến, mức khẳng định); "
                         "lựa chọn sai vẫn dịch đúng như câu đang viết – không sửa cho hợp lý."}
    o = (doc.get("options") or [])[int(m.group(3))]
    qt = (o.get("quotes") or [])[int(m.group(4))]
    return {"cau_tieng_nhat": qt.get("ja"),
            "luu_y": "Nghĩa CÂU TRÍCH từ đoạn văn: dịch sát câu tiếng Nhật (văn viết -다/-ㄴ다 nếu câu gốc thể thường); "
                     "cùng một câu trích xuất hiện ở nhiều lựa chọn / câu con → dịch GIỐNG HỆT."}


def nguon_ja_text(doc, path):
    return nguon_ja(doc, path)["cau_tieng_nhat"] or ""


def danh_dau(fmap, doc, cfg=None):
    """nguon_dich: ja (dịch thẳng từ tiếng Nhật) · vi."""
    for f in fmap:
        if JA_RE_PATH.match(f["path"]):
            f["nguon_dich"], f["ja"] = "ja", nguon_ja_text(doc, f["path"])
        else:
            f["nguon_dich"] = "vi"
    return fmap


def prefill_v3(fmap, fixed, tm):
    """Câu cố định / bộ nhớ dịch chỉ cho trường dịch từ tiếng Việt."""
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


def _ko(o, lang):
    return ((o or {}).get(lang) or "").strip() if o else ""


MOC_RE = re.compile(r"[①-⑳]")


def kiem_tra_v3(doc_ko, lang="ko"):
    """D7 (lỗi): nghĩa tiếng Hàn có số { } khác câu tiếng Nhật (khi câu Nhật có { }).
    D13 (lỗi): nghĩa câu hỏi phải giữ đủ mốc ①②… như câu hỏi tiếng Nhật.
    D15 (cảnh báo): cùng một câu trích (tiếng Nhật) trong lời giải nhưng bản dịch khác nhau.
    D12 (cảnh báo): trợ từ sau ⟪kana⟫ theo âm cuối cách đọc."""
    loi, canh_bao = [], []
    q = doc_ko.get("question") or {}
    qk = _ko(q.get("meaning"), lang)
    if qk and sorted(MOC_RE.findall(q.get("ja") or "")) != sorted(MOC_RE.findall(qk)):
        loi.append(f"D13: question.meaning – bản Hàn phải giữ mốc {MOC_RE.findall(q.get('ja') or '')} như câu hỏi tiếng Nhật")
    items = [("question", q.get("ja"), q.get("meaning"))]
    seen = {}
    for i, o in enumerate(doc_ko.get("options") or []):
        items.append((f"options[{i}]", o.get("option_ja"), o.get("meaning")))
        for j, qt in enumerate(o.get("quotes") or []):
            items.append((f"options[{i}].quotes[{j}]", qt.get("ja"), qt.get("meaning")))
            k, ko = strip_marks(qt.get("ja") or "").replace(" ", ""), _ko(qt.get("meaning"), lang)
            if ko:
                if k in seen and seen[k][1] != ko:
                    canh_bao.append(f"D15: options[{i}].quotes[{j}] – cùng câu trích với {seen[k][0]} nhưng bản dịch khác – nên thống nhất")
                seen.setdefault(k, (f"options[{i}].quotes[{j}]", ko))
    for name, ja, mean in items:
        ja, ko = ja or "", _ko(mean, lang)
        if ko and "{" in ja and (ja.count("{"), ja.count("}")) != (ko.count("{"), ko.count("}")):
            loi.append(f"D7: {name}.meaning – số dấu {{ }} khác câu tiếng Nhật")
    canh_bao += tro_tu(doc_ko, lang)
    return loi, canh_bao


def d4_key(f, doc):
    if f.get("nguon_dich") == "ja":
        return NOTE_JA + " " + strip_marks(nguon_ja_text(doc, f["path"])).replace(" ", "")
    return None


PARTICLE_RE = re.compile(r"⟪([぀-ゟ゠-ヿー]+)⟫[\"'”」』)）]*(이라는|라는|이라고|라고|이며|며|으로|로|은|는|이|가|을|를|과|와)(?![가-힣])")
BATCHIM = {"이라는", "이라고", "이며", "으로", "은", "이", "을", "과"}
DOI = {"이라는": "라는", "라는": "이라는", "이라고": "라고", "라고": "이라고", "이며": "며", "며": "이며", "으로": "로", "로": "으로",
       "은": "는", "는": "은", "이": "가", "가": "이", "을": "를", "를": "을", "과": "와", "와": "과"}


def tro_tu(doc_ko, lang="ko"):
    """D12 (cảnh báo): trợ từ ngay sau ⟪kana⟫ theo âm cuối cách đọc (ん → có patchim, nguyên âm → không patchim)."""
    out = []
    for fp, o in iter_lang_fields(doc_ko):
        for m in PARTICLE_RE.finditer(o.get(lang) or ""):
            kana, p = m.group(1), m.group(2)
            if (kana[-1] == "ん") != (p in BATCHIM):
                out.append(f"D12: {path_str(fp)}: '{kana}' + '{p}' – trợ từ sai theo âm cuối, nên là '{DOI[p]}'")
    return out
