"""Dạng 12 – Đọc hiểu đoạn văn dài: phần riêng giai đoạn 2 (khung v3 của dạng 07/09).

  Dịch TRỰC TIẾP từ câu tiếng Nhật (tác tử TẠO thấy thêm bản Việt để tham khảo cách hiểu):
    question.meaning                       nghĩa câu hỏi
    options[i].meaning                     nghĩa lựa chọn
    options[i].quotes[j].meaning           nghĩa câu trích (cùng câu trích trong các câu hỏi của một đoạn văn → dịch giống hệt)
  Dịch từ tiếng Việt: options[i].analysis.
Trường dịch từ tiếng Nhật không dùng câu cố định / bộ nhớ dịch (khóa theo tiếng Việt).
"""
import re

import _dang  # noqa: F401  (đặt sys.path tới thư mục Vie-Kor để import pipeline_chung)
from pipeline_chung.common import get_path, parse_path, strip_marks
from pipeline_chung.dich import prefill, tagged_copy

NOTE_JA = "[dịch từ tiếng Nhật]"
NOTE_KH = "[kết hợp]"          # dạng 12 không có trường kết hợp – giữ tên cho s3_xuat_ctv
NOTE_VD = "[tham khảo]"
JA_RE = re.compile(r"^\$\.(?:(question)\.meaning|options\[(\d+)\]\.meaning|options\[(\d+)\]\.quotes\[(\d+)\]\.meaning)$")


def _is_ja(path, cfg):
    return bool(JA_RE.match(path)) and bool((cfg or {}).get("dich_tu_nhat", {}).get("truong", True))


def nguon_ja(doc, path):
    m = JA_RE.match(path)
    if not m:
        raise KeyError(path)
    if m.group(1):
        q = doc.get("question") or {}
        return {"cau_tieng_nhat": q.get("ja"),
                "luu_y": "Nghĩa CÂU HỎI: dịch câu hỏi tiếng Nhật sang câu hỏi tiếng Hàn tự nhiên; giữ ①②, 「」→ 따옴표 như bản Việt, { } quanh phần tương ứng nếu câu Nhật có."}
    if m.group(2):
        o = (doc.get("options") or [])[int(m.group(2))]
        return {"cau_tieng_nhat": o.get("option_ja"),
                "luu_y": f"Nghĩa LỰA CHỌN {o.get('index')}: dịch sát câu tiếng Nhật (lựa chọn sai vẫn dịch đúng như câu đang viết, không sửa cho hợp lý)."}
    o = (doc.get("options") or [])[int(m.group(3))]
    qq = (o.get("quotes") or [])[int(m.group(4))]
    return {"cau_tieng_nhat": qq.get("ja"),
            "luu_y": "Nghĩa CÂU TRÍCH từ đoạn văn: dịch sát, đầy đủ câu tiếng Nhật; cùng một câu trích xuất hiện ở lựa chọn / câu hỏi khác của CÙNG đoạn văn thì dịch GIỐNG HỆT."}


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
            parent[path[-1]] = {"id": f["id"], "dich_tu_tieng_nhat": True, "nguon": nguon_ja(doc, f["path"]), "vi_tham_khao": f["vi"]}
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


def kiem_tra_v3(doc_ko, lang="ko"):
    """D7 (lỗi): nghĩa câu hỏi có số { } khác câu tiếng Nhật (khi câu Nhật có { }).
    D15 (cảnh báo): cùng một câu trích tiếng Nhật trong một câu nhưng hai bản dịch khác nhau.
    D12 (cảnh báo): trợ từ sau ⟪kana⟫ theo âm cuối cách đọc."""
    loi, canh_bao = [], []
    q = doc_ko.get("question") or {}
    ja, ko = q.get("ja") or "", _ko(q.get("meaning"), lang)
    if ko and "{" in ja and (ja.count("{"), ja.count("}")) != (ko.count("{"), ko.count("}")):
        loi.append("D7: question.meaning – số dấu { } khác câu tiếng Nhật")
    seen = {}
    for i, o in enumerate(doc_ko.get("options") or []):
        for j, qq in enumerate(o.get("quotes") or []):
            k, v = strip_marks(qq.get("ja") or "").replace(" ", ""), _ko(qq.get("meaning"), lang)
            if k and v:
                if k in seen and seen[k][1] != v:
                    canh_bao.append(f"D15: options[{i}].quotes[{j}] cùng câu trích với {seen[k][0]} nhưng bản dịch khác – thống nhất")
                seen.setdefault(k, (f"options[{i}].quotes[{j}]", v))
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
    """D12 (cảnh báo): trợ từ ngay sau ⟪kana⟫ theo âm cuối cách đọc: ん → dạng có patchim, nguyên âm → không patchim."""
    from pipeline_chung.common import iter_lang_fields, path_str
    out = []
    for fp, o in iter_lang_fields(doc_ko):
        for m in PARTICLE_RE.finditer(o.get(lang) or ""):
            kana, p = m.group(1), m.group(2)
            if (kana[-1] == "ん") != (p in BATCHIM):
                out.append(f"D12: {path_str(fp)}: '{kana}' + '{p}' – trợ từ sai theo âm cuối, nên là '{DOI[p]}'")
    return out
