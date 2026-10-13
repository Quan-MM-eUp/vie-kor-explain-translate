"""Dạng 08 – Lắp ghép câu: phần riêng giai đoạn 2 (dựng 2026-10-08 từ dạng 07).

  - TRỰC TIẾP từ tiếng Nhật (tác tử TẠO không thấy bản Việt, chỉ thấy ký hiệu ô trống của bản Việt):
      question.meaning                     (nghĩa câu đề – giữ ô trống ＿ / __ và ★ đúng như bản Việt)
      arrangement.full_sentence.meaning    (nghĩa câu hoàn chỉnh)
  - KẾT HỢP (bản Việt + tiếng Nhật):
      options[i].gloss                      '⟪cách đọc⟫ - nghĩa' của lựa chọn → nghĩa đúng với lựa chọn tiếng Nhật
      arrangement.explanation[j]           "'⟪cụm⟫' → 'nghĩa'" / câu giải thích cụm → nghĩa trong nháy đúng với cụm tiếng Nhật
  - còn lại (sentence_analysis, options[i].grammar, options[i].arrangement) dịch từ tiếng Việt.
Trường dịch từ tiếng Nhật không dùng câu cố định / bộ nhớ dịch.
"""
import re

import _dang  # noqa: F401  (sys.path → Vie-Kor)
from pipeline_chung.common import get_path, parse_path, strip_marks
from pipeline_chung.dich import prefill, tagged_copy

NOTE_JA = "[dịch từ tiếng Nhật]"
NOTE_KH = "[kết hợp: nghĩa theo tiếng Nhật]"
NOTE_VD = "[tham khảo]"
JA_RE = re.compile(r"^\$\.(?:(question)\.meaning|arrangement\.(full_sentence)\.meaning)$")
KH_GLOSS_RE = re.compile(r"^\$\.options\[(\d+)\]\.gloss$")
KH_EX_RE = re.compile(r"^\$\.arrangement\.explanation\[(\d+)\]$")
SLOT_RE = re.compile(r"[＿_]+|★|＊")
JA_IN_VI = re.compile(r"⟪([^⟫]+)⟫")


def _is_ja(path, cfg):
    return bool(JA_RE.match(path)) and bool((cfg or {}).get("dich_tu_nhat", {}).get("truong", True))


def nguon_ja(doc, path):
    m = JA_RE.match(path)
    if not m:
        raise KeyError(path)
    if m.group(1):
        q = doc.get("question") or {}
        vi = ((q.get("meaning") or {}).get("vi")) or ""
        return {"cau_tieng_nhat": q.get("ja"), "cach_doc": q.get("reading"),
                "ky_hieu_o_trong_ban_viet": " ".join(SLOT_RE.findall(vi)),
                "luu_y": "Nghĩa câu ĐỀ (4 ô trống, 1 ô ★): dịch câu tiếng Nhật, đặt các ô trống ở vị trí tương ứng trong câu Hàn, dùng ĐÚNG ký hiệu và "
                         "số ô như 'ky_hieu_o_trong_ban_viet' (vd '__ __ ★ __') – không tự điền. Hội thoại giữ xuống dòng / tên người nói."}
    fs = (doc.get("arrangement") or {}).get("full_sentence") or {}
    return {"cau_tieng_nhat": fs.get("ja"), "cach_doc": fs.get("reading"),
            "luu_y": "Câu hoàn chỉnh (đáp án đã sắp xếp) – dịch tự nhiên, bám sát câu tiếng Nhật. Dấu { } trong câu Nhật chỉ là in đậm 4 mảnh – KHÔNG đưa { } vào bản Hàn."}


def nguon_ja_text(doc, path):
    return nguon_ja(doc, path)["cau_tieng_nhat"] or ""


def ket_hop_nguon(doc, path, cfg=None):
    dn = (cfg or {}).get("dich_tu_nhat") or {}
    if not dn.get("ket_hop_y_nghia", True):
        return None
    m = KH_GLOSS_RE.match(path)
    if m:
        o = (doc.get("options") or [])[int(m.group(1))]
        return {"loai": "nghia_lua_chon", "tu_tieng_nhat": o.get("option_ja"), "ngoac": None}
    m = KH_EX_RE.match(path)
    if m:
        vi = (((doc.get("arrangement") or {}).get("explanation") or [])[int(m.group(1))] or {}).get("vi") or ""
        cum = JA_IN_VI.findall(vi)
        return {"loai": "cum_sap_xep", "tu_tieng_nhat": " / ".join(cum) if cum else None, "ngoac": None}
    return None


LUU_Y_KH = {
    "nghia_lua_chon": "Dòng tiêu đề của lựa chọn: '⟪cách đọc⟫ - nghĩa' (hoặc chỉ 'nghĩa'). Giữ nguyên khối ⟪ ⟫ và dấu ' - '; phần nghĩa dịch theo bản Việt "
                      "nhưng phải đúng với chính lựa chọn tiếng Nhật (từ / cụm ngắn tiếng Hàn tự nhiên, không viết thành câu -습니다).",
    "cum_sap_xep": "Cụm sắp xếp \"'⟪cụm⟫' → 'nghĩa'\" hoặc câu giải thích cụm: giữ nguyên ⟪ ⟫, mũi tên, dấu nháy; nghĩa trong nháy phải đúng với cụm tiếng Nhật "
                   "(dịch theo bản Việt, đối chiếu tiếng Nhật).",
}


def danh_dau(fmap, doc, cfg):
    for f in fmap:
        kh = ket_hop_nguon(doc, f["path"], cfg)
        if _is_ja(f["path"], cfg):
            f["nguon_dich"], f["ja"] = "ja", nguon_ja_text(doc, f["path"])
        elif kh is not None:
            f["nguon_dich"], f["ja"] = "ket_hop", (kh["tu_tieng_nhat"] or "")
        else:
            f["nguon_dich"] = "vi"
    return fmap


def prefill_v3(fmap, fixed, tm):
    """Câu cố định / bộ nhớ dịch: trường VI (cả hai) và trường kết hợp (chỉ câu cố định)."""
    filled_vi, todo_vi = prefill([f for f in fmap if f["nguon_dich"] == "vi"], fixed, tm)
    filled_kh, todo_kh = prefill([f for f in fmap if f["nguon_dich"] == "ket_hop"], fixed, {})
    filled = {**filled_vi, **filled_kh}
    keep = set(todo_vi) | set(todo_kh) | {f["id"] for f in fmap if f["nguon_dich"] == "ja"}
    return filled, [f["id"] for f in fmap if f["id"] in keep]


def tagged_copy_v3(doc, fmap, lang):
    d = tagged_copy(doc, fmap, lang)
    for f in fmap:
        path = parse_path(f["path"])
        parent = get_path(d, path[:-1])
        if f["nguon_dich"] == "ja":
            parent[path[-1]] = {"id": f["id"], "dich_tu_tieng_nhat": True, "nguon": nguon_ja(doc, f["path"])}
        elif f["nguon_dich"] == "ket_hop":
            kh = ket_hop_nguon(doc, f["path"])
            parent[path[-1]] = {"id": f["id"], "vi": f["vi"], "tu_tieng_nhat": kh["tu_tieng_nhat"], "loai": kh["loai"], "luu_y": LUU_Y_KH[kh["loai"]]}
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
    """D13 (lỗi): nghĩa câu đề tiếng Hàn phải giữ đủ ô trống + ★ như bản tiếng Việt (cùng thứ tự ★).
    D7 (lỗi): nghĩa câu tiếng Hàn có số { } khác bản tiếng Việt.
    D12 (cảnh báo): trợ từ sau ⟪kana⟫ theo âm cuối cách đọc."""
    loi, canh_bao = [], []
    q = doc_ko.get("question") or {}
    qv, qk = ((q.get("meaning") or {}).get("vi") or ""), _ko(q.get("meaning"), lang)
    if qk:
        sv, sk = ["★" if x in "★＊" else "_" for x in SLOT_RE.findall(qv)], ["★" if x in "★＊" else "_" for x in SLOT_RE.findall(qk)]
        if sv != sk:
            loi.append(f"D13: question.meaning – bản Hàn phải giữ ô trống như bản Việt ({' '.join(sv)}), đang có ({' '.join(sk)})")
    fs = (doc_ko.get("arrangement") or {}).get("full_sentence") or {}
    for name, s in (("question", q), ("arrangement.full_sentence", fs)):
        mv = (s.get("meaning") or {}) if s else {}
        v, k = mv.get("vi") or "", _ko(mv, lang)
        if k and (v.count("{"), v.count("}")) != (k.count("{"), k.count("}")):
            loi.append(f"D7: {name}.meaning – số dấu {{ }} khác bản tiếng Việt")
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
    from pipeline_chung.common import iter_lang_fields, path_str
    out = []
    for fp, o in iter_lang_fields(doc_ko):
        for m in PARTICLE_RE.finditer(o.get(lang) or ""):
            kana, p = m.group(1), m.group(2)
            if (kana[-1] in "んン") != (p in BATCHIM):      # 2026-10-13: + katakana ン (ノートパソコン은 – báo nhầm ở 389, 678, 707)
                out.append(f"D12: {path_str(fp)}: '{kana}' + '{p}' – trợ từ sai theo âm cuối, nên là '{DOI[p]}'")
    return out
