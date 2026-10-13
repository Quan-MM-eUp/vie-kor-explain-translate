"""Dạng 11 – Đọc hiểu: Đoạn văn trung bình: phần riêng giai đoạn 2 (dựng 2026-10-08 theo khung dạng 08).

  - TRỰC TIẾP từ tiếng Nhật (tác tử TẠO không thấy bản Việt của các trường này; có đoạn văn làm ngữ cảnh):
      question.meaning                  (nghĩa câu hỏi)
      options[i].meaning                (nghĩa lựa chọn)
      options[i].quotes[j].meaning      (nghĩa câu trích – cùng câu trích ở các câu con của một đoạn phải dịch giống nhau: D4)
  - còn lại (options[i].analysis, full_translation – khuôn lạ, không dịch vì bị gắn cờ) dịch từ tiếng Việt.
Trường dịch từ tiếng Nhật không dùng câu cố định / bộ nhớ dịch.
"""
import re

import _dang  # noqa: F401  (sys.path → Vie-Kor)
from pipeline_chung.common import LOCK_RE, get_path, parse_path, strip_marks
from pipeline_chung.dich import prefill, tagged_copy

NOTE_JA = "[dịch từ tiếng Nhật]"
NOTE_KH = "[kết hợp: nghĩa theo tiếng Nhật]"
NOTE_VD = "[tham khảo]"
JA_RE = re.compile(r"^\$\.(?:(question)\.meaning|options\[(\d+)\]\.meaning|options\[(\d+)\]\.quotes\[(\d+)\]\.meaning)$")


def _is_ja(path, cfg):
    return bool(JA_RE.match(path)) and bool((cfg or {}).get("dich_tu_nhat", {}).get("truong", True))


def _khoi(vi):
    return [f"⟪{x}⟫" for x in LOCK_RE.findall(vi or "")]


def nguon_ja(doc, path):
    m = JA_RE.match(path)
    if not m:
        raise KeyError(path)
    if m.group(1):
        q = doc.get("question") or {}
        vi = ((q.get("meaning") or {}).get("vi")) or ""
        return {"loai": "nghia_cau_hoi", "cau_tieng_nhat": q.get("ja"), "khoi_tieng_nhat_ban_viet_giu": _khoi(vi),
                "so_cap_ngoac_nhon": vi.count("{"),
                "luu_y": "Nghĩa CÂU HỎI: dịch tự nhiên, bám sát câu Nhật (giữ số khoanh ①②, dấu 「」 / \"…\" quanh phần trích trong câu hỏi). "
                         "Phần câu hỏi trích nguyên văn đoạn văn ('①「…」とあるが') dịch theo nghĩa trong đoạn văn."}
    if m.group(2) is not None:
        o = (doc.get("options") or [])[int(m.group(2))]
        vi = ((o.get("meaning") or {}).get("vi")) or ""
        return {"loai": "nghia_lua_chon", "cau_tieng_nhat": o.get("option_ja"), "khoi_tieng_nhat_ban_viet_giu": _khoi(vi),
                "so_cap_ngoac_nhon": vi.count("{"),
                "luu_y": "Nghĩa LỰA CHỌN: dịch sát câu / cụm Nhật (thì, phủ định, chủ thể); lựa chọn là cụm danh từ thì dịch thành cụm, không thêm '-습니다'."}
    o = (doc.get("options") or [])[int(m.group(3))]
    qt = (o.get("quotes") or [])[int(m.group(4))]
    vi = ((qt.get("meaning") or {}).get("vi")) or ""
    return {"loai": "nghia_cau_trich", "cau_tieng_nhat": qt.get("ja"), "khoi_tieng_nhat_ban_viet_giu": _khoi(vi),
            "so_cap_ngoac_nhon": vi.count("{"),
            "luu_y": "Nghĩa CÂU TRÍCH (nguyên văn đoạn văn): dịch sát, đúng văn cảnh đoạn văn, văn phong theo câu Nhật (thể thường → -다, です/ます → -습니다/-요). "
                     "Cùng một câu trích (kể cả ở câu con khác của cùng đoạn) phải dịch giống hệt nhau."}


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
_BO_QUA_JA = ("furigana khác bản tiếng Việt", "tỷ lệ độ dài KO/VI", "câu cố định phải dịch là", "văn phong -습니다")


def loc_kiem_tra(msgs, fmap):
    """Trường dịch từ tiếng Nhật: bỏ các phép so với bản Việt không áp dụng (furigana, tỷ lệ độ dài, câu cố định, văn phong).
    Vẫn giữ: '⟪ ⟫ khác bản tiếng Việt' (bản Hàn phải giữ đúng các khối ⟪ ⟫ của bản Việt – nguon.khoi_tieng_nhat_ban_viet_giu)."""
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
    """D7 (lỗi): nghĩa câu hỏi / lựa chọn / câu trích tiếng Hàn có số { } khác bản tiếng Việt.
    D12 (cảnh báo): trợ từ sau ⟪kana⟫ theo âm cuối cách đọc."""
    from pipeline_chung.common import iter_lang_fields, path_str
    loi, canh_bao = [], []
    for fp, o in iter_lang_fields(doc_ko):
        p = path_str(fp)
        if not JA_RE.match(p):
            continue
        v, k = o.get("vi") or "", _ko(o, lang)
        if k and (v.count("{"), v.count("}")) != (k.count("{"), k.count("}")):
            loi.append(f"D7: {p} – số dấu {{ }} khác bản tiếng Việt")
    canh_bao += tro_tu(doc_ko, lang)
    return loi, canh_bao


def d4_key(f, doc):
    if f.get("nguon_dich") == "ja":
        return NOTE_JA + " " + strip_marks(nguon_ja_text(doc, f["path"]))
    return None


PARTICLE_RE = re.compile(r"⟪([^⟪⟫]+)⟫[\"'”」』)）]*(이라는|라는|이라고|라고|이며|며|으로|로|은|는|이|가|을|를|과|와)(?![가-힣])")
BATCHIM = {"이라는", "이라고", "이며", "으로", "은", "이", "을", "과"}
DOI = {"이라는": "라는", "라는": "이라는", "이라고": "라고", "라고": "이라고", "이며": "며", "며": "이며", "으로": "로", "로": "으로",
       "은": "는", "는": "은", "이": "가", "가": "이", "을": "를", "를": "을", "과": "와", "와": "과"}
KANA_RE = re.compile(r"[぀-ゟ゠-ヿ]")


def am_cuoi(khoi):
    """Kana cuối theo CÁCH ĐỌC của khối ⟪…⟫: '｜表現《ひょうげん》' → 'ん'; 'なる' → 'る'; kết thúc bằng chữ Hán không furigana / ký hiệu → None."""
    t = re.sub(r"[\s　。、．，!！?？」』）)〜～…・]+$", "", khoi)
    m = re.search(r"《([^《》]*)》$", t)
    if m:
        t = m.group(1)
    if t and KANA_RE.match(t[-1]) and t[-1] != "ー":
        return t[-1]
    return None


def tro_tu(doc_ko, lang="ko"):
    """D12 (cảnh báo): trợ từ sau ⟪…⟫ phải theo âm cuối cách đọc tiếng Nhật (ん → 은/이/을/과…; kana khác → 는/가/를/와…).
    Dạng 11: kể cả khối có chữ Hán + furigana (⟪｜表現《ひょうげん》⟫ → 이/은/을…)."""
    from pipeline_chung.common import iter_lang_fields, path_str
    out = []
    for fp, o in iter_lang_fields(doc_ko):
        for m in PARTICLE_RE.finditer(o.get(lang) or ""):
            kana, p = am_cuoi(m.group(1)), m.group(2)
            if kana and (kana in "んン") != (p in BATCHIM):
                out.append(f"D12: {path_str(fp)}: '⟪{m.group(1)}⟫' + '{p}' – trợ từ sai theo âm cuối, nên là '{DOI[p]}'")
    return out
