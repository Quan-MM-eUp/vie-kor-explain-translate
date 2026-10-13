"""Dạng 10 – Đọc hiểu đoạn văn ngắn: phần riêng giai đoạn 2 (dựng 2026-10-08 từ dạng 08).

  - KẾT HỢP (tác tử TẠO thấy bản Việt + câu tiếng Nhật; nghĩa phải đúng với TIẾNG NHẬT, bản Việt để đối chiếu):
      question.meaning                    nghĩa câu hỏi            (tu_tieng_nhat = question.ja)
      options[i].meaning                  nghĩa lựa chọn           (tu_tieng_nhat = options[i].option_ja)
      options[i].quotes[j].meaning        bản dịch câu trích dẫn   (tu_tieng_nhat = quotes[j].ja)
  - còn lại (options[i].analysis, summary, full_translation) dịch từ tiếng Việt (ngữ cảnh: đoạn văn tiếng Nhật).
Trường kết hợp chỉ dùng câu cố định (không bộ nhớ dịch).
Kiểm tra riêng: D-QT (cùng câu trích dẫn tiếng Nhật trong một mẫu phải cùng bản Hàn), D12 (trợ từ sau ⟪kana⟫).
"""
import re

import _dang  # noqa: F401  (sys.path → Vie-Kor)
from pipeline_chung.common import get_path, parse_path, strip_marks
from pipeline_chung.dich import prefill, tagged_copy

NOTE_JA = "[dịch từ tiếng Nhật]"
NOTE_KH = "[kết hợp: nghĩa theo tiếng Nhật]"
NOTE_VD = "[tham khảo]"
KH_Q_RE = re.compile(r"^\$\.question\.meaning$")
KH_OPT_RE = re.compile(r"^\$\.options\[(\d+)\]\.meaning$")
KH_QT_RE = re.compile(r"^\$\.options\[(\d+)\]\.quotes\[(\d+)\]\.meaning$")

LUU_Y_KH = {
    "nghia_cau_hoi": "Nghĩa câu hỏi: dịch câu hỏi tiếng Nhật (tu_tieng_nhat) sang tiếng Hàn tự nhiên, đối chiếu bản Việt; câu hỏi giữ dạng câu hỏi (-습니까 / -ㄴ가 / -는가 theo câu Nhật).",
    "nghia_lua_chon": "Nghĩa lựa chọn: dịch đúng câu / cụm tiếng Nhật của lựa chọn (thì, phủ định, chủ thể, mức độ) – bản Việt chỉ để đối chiếu; giữ mức lịch sự theo câu Nhật. Không thêm / bớt ý.",
    "trich_dan": "Bản dịch câu trích dẫn: dịch câu tiếng Nhật trích từ đoạn văn (tu_tieng_nhat) – bản Việt chỉ để đối chiếu; không cần ngoặc ( ). Cùng một câu trích dẫn xuất hiện nhiều lần → dịch GIỐNG HỆT nhau.",
}


def ket_hop_nguon(doc, path, cfg=None):
    dn = (cfg or {}).get("dich_tu_nhat") or {}
    if cfg is not None and not dn.get("ket_hop_y_nghia", True):
        return None
    if KH_Q_RE.match(path):
        return {"loai": "nghia_cau_hoi", "tu_tieng_nhat": (doc.get("question") or {}).get("ja")}
    m = KH_OPT_RE.match(path)
    if m:
        return {"loai": "nghia_lua_chon", "tu_tieng_nhat": (doc.get("options") or [])[int(m.group(1))].get("option_ja")}
    m = KH_QT_RE.match(path)
    if m:
        q = ((doc.get("options") or [])[int(m.group(1))].get("quotes") or [])[int(m.group(2))]
        return {"loai": "trich_dan", "tu_tieng_nhat": q.get("ja")}
    return None


def danh_dau(fmap, doc, cfg):
    for f in fmap:
        kh = ket_hop_nguon(doc, f["path"], cfg)
        if kh is not None:
            f["nguon_dich"], f["ja"], f["loai"] = "ket_hop", (kh["tu_tieng_nhat"] or ""), kh["loai"]
        else:
            f["nguon_dich"] = "vi"
    return fmap


def prefill_v3(fmap, fixed, tm):
    """Câu cố định / bộ nhớ dịch: trường VI (cả hai) và trường kết hợp (chỉ câu cố định)."""
    filled_vi, todo_vi = prefill([f for f in fmap if f["nguon_dich"] == "vi"], fixed, tm)
    filled_kh, todo_kh = prefill([f for f in fmap if f["nguon_dich"] == "ket_hop"], fixed, {})
    filled = {**filled_vi, **filled_kh}
    keep = set(todo_vi) | set(todo_kh)
    return filled, [f["id"] for f in fmap if f["id"] in keep]


def tagged_copy_v3(doc, fmap, lang):
    d = tagged_copy(doc, fmap, lang)
    for f in fmap:
        if f["nguon_dich"] != "ket_hop":
            continue
        path = parse_path(f["path"])
        parent = get_path(d, path[:-1])
        kh = ket_hop_nguon(doc, f["path"])
        parent[path[-1]] = {"id": f["id"], "vi": f["vi"], "tu_tieng_nhat": kh["tu_tieng_nhat"], "loai": kh["loai"], "luu_y": LUU_Y_KH[kh["loai"]]}
    return d


# ---------------- kiểm tra riêng ----------------
def loc_kiem_tra(msgs, fmap):
    """Dạng 10 không có trường dịch thuần từ tiếng Nhật → giữ nguyên mọi thông báo."""
    return list(msgs)


def _ko(o, lang):
    return ((o or {}).get(lang) or "").strip() if o else ""


def kiem_tra_v3(doc_ko, lang="ko"):
    """D-QT (lỗi): cùng câu trích dẫn tiếng Nhật xuất hiện nhiều lần trong một mẫu phải có cùng bản Hàn.
    D12 (cảnh báo): trợ từ sau ⟪kana⟫ theo âm cuối cách đọc."""
    loi, canh_bao = [], []
    seen = {}
    for i, o in enumerate(doc_ko.get("options") or []):
        for j, q in enumerate(o.get("quotes") or []):
            k = re.sub(r"\s+", "", strip_marks(q.get("ja") or ""))
            ko = _ko(q.get("meaning"), lang)
            if not k or not ko:
                continue
            if k in seen and seen[k][1] != ko:
                loi.append(f"D-QT: options[{i}].quotes[{j}] – cùng câu trích dẫn với {seen[k][0]} nhưng bản Hàn khác (phải dịch giống hệt)")
            seen.setdefault(k, (f"options[{i}].quotes[{j}]", ko))
    canh_bao += tro_tu(doc_ko, lang)
    return loi, canh_bao


def d4_key(f, doc):
    """Khóa so nhất quán giữa các mẫu (D4): câu trích dẫn theo câu tiếng Nhật; trường khác theo bản Việt (mặc định)."""
    if f.get("nguon_dich") == "ket_hop" and f.get("loai") == "trich_dan":
        return "[trích dẫn] " + re.sub(r"\s+", "", strip_marks(f.get("ja") or ""))
    return None


PARTICLE_RE = re.compile(r"⟪([぀-ゟ゠-ヿー]+)⟫[\"'”」』)）]*(이라는|라는|이라고|라고|이며|며|으로|로|은|는|이|가|을|를|과|와)(?![가-힣])")
BATCHIM = {"이라는", "이라고", "이며", "으로", "은", "이", "을", "과"}
DOI = {"이라는": "라는", "라는": "이라는", "이라고": "라고", "라고": "이라고", "이며": "며", "며": "이며", "으로": "로", "로": "으로",
       "은": "는", "는": "은", "이": "가", "가": "이", "을": "를", "를": "을", "과": "와", "와": "과"}


def tro_tu(doc_ko, lang="ko"):
    from pipeline_chung.common import iter_lang_fields, path_str
    out = []
    for fp, o in iter_lang_fields(doc_ko):
        for m in PARTICLE_RE.finditer(o.get(lang) or ""):
            kana, p = m.group(1), m.group(2)
            if (kana[-1] == "ん") != (p in BATCHIM):
                out.append(f"D12: {path_str(fp)}: '{kana}' + '{p}' – trợ từ sai theo âm cuối, nên là '{DOI[p]}'")
    return out
