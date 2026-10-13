"""Dạng 07 – Lựa chọn ngữ pháp: phần riêng giai đoạn 2 (dựng 2026-10-07 từ dạng 06).

  - question.meaning                        (nghĩa câu đề – giữ chỗ trống)
    analysis.options[i].applied.meaning     (nghĩa câu đã điền lựa chọn)
    correct.full_sentence.meaning           (nghĩa câu hoàn chỉnh)
      ← dịch TRỰC TIẾP từ câu tiếng Nhật; GPT không thấy bản tiếng Việt của các trường này.
  - KẾT HỢP (bản Việt + tiếng Nhật – nghĩa phải đúng với mẫu ngữ pháp tiếng Nhật):
      analysis.options[i].meaning ← 'Ý nghĩa' của lựa chọn (option_ja)
  - phần còn lại (structure, grammar_note, semantic_note, other, analysis.intro, question_note, correct.note) dịch từ tiếng Việt.
Trường dịch từ tiếng Nhật không dùng câu cố định / bộ nhớ dịch.
"""
import re

import _dang  # noqa: F401  (đặt sys.path tới thư mục Vie-Kor để import pipeline_chung)
from pipeline_chung.common import get_path, parse_path, strip_marks
from pipeline_chung.dich import prefill, tagged_copy

NOTE_JA = "[dịch từ tiếng Nhật]"
NOTE_KH = "[kết hợp: nghĩa theo mẫu ngữ pháp tiếng Nhật]"
NOTE_VD = "[tham khảo]"
JA_RE = re.compile(r"^\$\.(?:(question)\.meaning|analysis\.options\[(\d+)\]\.(applied)\.meaning|correct\.(full_sentence)\.meaning)$")
KH_RE = re.compile(r"^\$\.analysis\.options\[(\d+)\]\.meaning$")
BLANK_RE = re.compile(r"_{2,}|＿{2,}|[（(][\s　]*[)）]")


def ja_paths(cfg):
    return {"$." + p.lstrip("$.") for p in (cfg.get("dich_tu_nhat") or {}).get("truong", [])}


def _is_ja(path, cfg):
    return bool(JA_RE.match(path)) and bool((cfg or {}).get("dich_tu_nhat", {}).get("truong", True))


def nguon_ja(doc, path):
    m = JA_RE.match(path)
    if not m:
        raise KeyError(path)
    if m.group(1):
        q = doc.get("question") or {}
        return {"cau_tieng_nhat": q.get("ja"), "cach_doc": q.get("reading"),
                "luu_y": "Nghĩa câu ĐỀ (câu có chỗ trống): dịch câu tiếng Nhật, GIỮ NGUYÊN ký hiệu chỗ trống (________ / ＿＿＿ / （　　　）) "
                         "ở vị trí tương ứng trong câu Hàn – không tự điền. Hội thoại nhiều dòng thì giữ xuống dòng / tên người nói."}
    if m.group(3):
        o = ((doc.get("analysis") or {}).get("options") or [])[int(m.group(2))]
        a = o.get("applied") or {}
        sai = o.get("grammar_ok") is False or o.get("semantic_ok") is False
        return {"cau_tieng_nhat": a.get("ja"), "cach_doc": None,
                "luu_y": (f"Câu đề đã điền lựa chọn {o.get('index')} '{o.get('option_ja')}'"
                          + (" – lời giải coi lựa chọn này SAI / KHÔNG PHÙ HỢP: dịch sát đúng như câu đang viết (kể cả gượng), không tự sửa cho hợp lý; "
                             "phần giống các câu áp dụng khác dịch giống nhau, chỉ khác ở chỗ điền." if sai
                             else " – dịch tự nhiên, bám sát câu tiếng Nhật."))}
    c = doc.get("correct") or {}
    fs = c.get("full_sentence") or {}
    return {"cau_tieng_nhat": fs.get("ja"), "cach_doc": None,
            "luu_y": "Câu hoàn chỉnh (đáp án đúng) – nếu giống câu áp dụng của đáp án thì dịch GIỐNG HỆT bản dịch nghĩa câu áp dụng đó."}


def nguon_ja_text(doc, path):
    return nguon_ja(doc, path)["cau_tieng_nhat"] or ""


def ket_hop_nguon(doc, path, cfg=None):
    """Trường kết hợp → {loai, tu_tieng_nhat, ngoac} hoặc None."""
    dn = (cfg or {}).get("dich_tu_nhat") or {}
    m = KH_RE.match(path)
    if m and dn.get("ket_hop_y_nghia", True):
        o = ((doc.get("analysis") or {}).get("options") or [])[int(m.group(1))]
        return {"loai": "y_nghia_mau_ngu_phap", "tu_tieng_nhat": o.get("option_ja"), "ngoac": None}
    return None


LUU_Y_KH = {
    "y_nghia_mau_ngu_phap": "Ý nghĩa của MẪU NGỮ PHÁP tiếng Nhật này (lựa chọn của đề) – dịch theo bản Việt (giữ cấu trúc câu, số nghĩa, dấu nháy), "
                            "nhưng từng nghĩa trích trong nháy phải đúng với chính mẫu tiếng Nhật (cụm ngắn tiếng Hàn tự nhiên, dùng thuật ngữ ngữ pháp tiếng Hàn chuẩn).",
}


def danh_dau(fmap, doc, cfg):
    """nguon_dich: ja (dịch thẳng từ tiếng Nhật) · ket_hop (VI + từ tiếng Nhật) · vi."""
    for f in fmap:
        kh = ket_hop_nguon(doc, f["path"], cfg)
        if _is_ja(f["path"], cfg):
            f["nguon_dich"], f["ja"] = "ja", nguon_ja_text(doc, f["path"])
        elif kh is not None:
            f["nguon_dich"], f["ja"] = "ket_hop", (kh["tu_tieng_nhat"] or "") + (f" ({kh['ngoac']})" if kh.get("ngoac") else "")
        else:
            f["nguon_dich"] = "vi"
    return fmap


def prefill_v3(fmap, fixed, tm):
    """Câu cố định / bộ nhớ dịch: chỉ cho trường dịch từ tiếng Việt và trường kết hợp (bộ nhớ dịch: chỉ trường VI)."""
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
            parent[path[-1]] = {"id": f["id"], "vi": f["vi"], "tu_tieng_nhat": kh["tu_tieng_nhat"], "ngoac": kh.get("ngoac"),
                                "loai": kh["loai"], "luu_y": LUU_Y_KH[kh["loai"]]}
    return d


# ---------------- kiểm tra riêng ----------------
_BO_QUA_JA = ("nội dung ⟪ ⟫ khác bản tiếng Việt", "furigana khác bản tiếng Việt", "tỷ lệ độ dài KO/VI", "câu cố định phải dịch là",
              "văn phong -습니다")   # nghĩa câu dịch từ tiếng Nhật giữ mức lịch sự của câu Nhật (thể thường → -다)


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
    D13 (lỗi): nghĩa câu đề tiếng Hàn phải giữ đủ số chỗ trống như bản tiếng Việt.
    D14 (cảnh báo): câu hoàn chỉnh giống câu áp dụng của đáp án nhưng hai bản dịch khác nhau.
    D12 (cảnh báo): trợ từ sau ⟪kana⟫ theo âm cuối cách đọc."""
    loi, canh_bao = [], []
    q = doc_ko.get("question") or {}
    qv, qk = ((q.get("meaning") or {}).get("vi") or ""), _ko(q.get("meaning"), lang)
    if qk and len(BLANK_RE.findall(qk)) != len(BLANK_RE.findall(qv)):
        loi.append(f"D13: question.meaning – bản Hàn phải giữ {len(BLANK_RE.findall(qv))} chỗ trống như bản tiếng Việt (đang có {len(BLANK_RE.findall(qk))})")
    items = [("question", q)]
    opts = (doc_ko.get("analysis") or {}).get("options") or []
    items += [(f"analysis.options[{i}].applied", o.get("applied") or {}) for i, o in enumerate(opts)]
    c = doc_ko.get("correct") or {}
    fs = c.get("full_sentence") or {}
    items.append(("correct.full_sentence", fs))
    for name, s in items:
        ja, ko = s.get("ja") or "", _ko(s.get("meaning"), lang)
        if ko and "{" in ja and (ja.count("{"), ja.count("}")) != (ko.count("{"), ko.count("}")):
            loi.append(f"D7: {name}.meaning – số dấu {{ }} khác câu tiếng Nhật")
    di = c.get("index")
    if isinstance(di, int) and 1 <= di <= len(opts):
        ap = opts[di - 1].get("applied") or {}
        a_k, f_k = _ko(ap.get("meaning"), lang), _ko(fs.get("meaning"), lang)
        if a_k and f_k and a_k != f_k and strip_marks(ap.get("ja") or "").replace(" ", "") == strip_marks(fs.get("ja") or "").replace(" ", ""):
            canh_bao.append("D14: correct.full_sentence.meaning khác bản dịch nghĩa câu áp dụng của đáp án dù câu tiếng Nhật giống nhau – nên thống nhất")
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
    """D12 (cảnh báo): trợ từ ngay sau ⟪kana⟫ phải theo âm cuối cách đọc: ん → dạng có patchim (은/이/을/과/이라는/이며/으로),
    nguyên âm → dạng không patchim. Chỉ xét khối ⟪ ⟫ toàn kana (cách đọc) – khối có chữ Hán bỏ qua."""
    from pipeline_chung.common import iter_lang_fields, path_str
    out = []
    for fp, o in iter_lang_fields(doc_ko):
        for m in PARTICLE_RE.finditer(o.get(lang) or ""):
            kana, p = m.group(1), m.group(2)
            if (kana[-1] == "ん") != (p in BATCHIM):
                out.append(f"D12: {path_str(fp)}: '{kana}' + '{p}' – trợ từ sai theo âm cuối, nên là '{DOI[p]}'")
    return out
