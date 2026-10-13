"""Dạng 06 – Ứng dụng từ: phần riêng giai đoạn 2 (dựng 2026-10-07 từ dạng 05).

  - analysis.options[i].sentence.meaning   (nghĩa câu của lựa chọn)
    analysis.options[i].correction.meaning (nghĩa câu sửa)
      ← dịch TRỰC TIẾP từ câu tiếng Nhật; GPT không thấy bản tiếng Việt của các trường này.
  - KẾT HỢP (bản Việt + tiếng Nhật – nghĩa phải đúng với từ tiếng Nhật):
      word.meaning ← câu nghĩa của từ được hỏi (word.ja + paren)
  - phần còn lại (word.usage, analysis.intro, analysis.options[i].analysis, correct.note) dịch từ tiếng Việt.
Trường dịch từ tiếng Nhật không dùng câu cố định / bộ nhớ dịch.
"""
import re

import _dang  # noqa: F401  (đặt sys.path tới thư mục Vie-Kor để import pipeline_chung)
from pipeline_chung.common import get_path, parse_path, strip_marks
from pipeline_chung.dich import prefill, tagged_copy

NOTE_JA = "[dịch từ tiếng Nhật]"
NOTE_KH = "[kết hợp: nghĩa theo từ tiếng Nhật]"
NOTE_VD = "[tham khảo]"
JA_RE = re.compile(r"^\$\.analysis\.options\[(\d+)\]\.(sentence|correction)\.meaning$")
WORD_RE_P = "$.word.meaning"


def ja_paths(cfg):
    return {"$." + p.lstrip("$.") for p in (cfg.get("dich_tu_nhat") or {}).get("truong", [])}


def _is_ja(path, cfg):
    return bool(JA_RE.match(path)) and bool((cfg or {}).get("dich_tu_nhat", {}).get("truong", True))


def nguon_ja(doc, path):
    m = JA_RE.match(path)
    if not m:
        raise KeyError(path)
    o = ((doc.get("analysis") or {}).get("options") or [])[int(m.group(1))]
    s = o.get(m.group(2)) or {}
    w = doc.get("word") or {}
    if m.group(2) == "sentence":
        luu_y = (f"Câu lựa chọn {o.get('index')} dùng từ '{w.get('ja')}'"
                 + (" – lời giải coi câu này DÙNG SAI từ: dịch đúng câu tiếng Nhật như nó đang viết, không tự sửa cho hợp lý." if o.get("usage_ok") is False
                    else " – dịch tự nhiên, bám sát câu tiếng Nhật."))
    else:
        luu_y = "Câu đã SỬA của lựa chọn này – phần giống câu gốc dịch giống bản dịch câu gốc (nếu có), khác ở chỗ được sửa."
    return {"cau_tieng_nhat": s.get("ja"), "cach_doc": s.get("reading"), "luu_y": luu_y}


def nguon_ja_text(doc, path):
    return nguon_ja(doc, path)["cau_tieng_nhat"] or ""


def ket_hop_nguon(doc, path, cfg=None):
    """Trường kết hợp → {loai, tu_tieng_nhat, ngoac} hoặc None."""
    dn = (cfg or {}).get("dich_tu_nhat") or {}
    if path == WORD_RE_P and dn.get("ket_hop_tu", True):
        w = doc.get("word") or {}
        return {"loai": "nghia_tu_duoc_hoi", "tu_tieng_nhat": w.get("ja"), "ngoac": w.get("paren")}
    return None


LUU_Y_KH = {
    "nghia_tu_duoc_hoi": "Câu nghĩa của TỪ ĐƯỢC HỎI tiếng Nhật này – hiển thị ngay sau từ, nên bản Hàn BẮT ĐẦU bằng trợ từ 는/은 theo âm cuối cách đọc của từ; dịch theo bản Việt (giữ cấu trúc câu 'có nghĩa là …' và số nghĩa), "
                         "nhưng từng nghĩa phải đúng với chính từ tiếng Nhật; nghĩa trong ngoặc kép là cụm ngắn tiếng Hàn.",
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


def kiem_tra_v3(doc_ko, lang="ko"):
    """D7 (lỗi): nghĩa câu tiếng Hàn của lựa chọn / câu sửa có số { } khác câu tiếng Nhật (khi câu tiếng Nhật có { }).
    D10 (cảnh báo): câu sửa giống câu gốc ở tiếng Nhật nhưng hai bản dịch khác nhau ngoài chỗ sửa – chỉ báo khi bản dịch câu sửa trùng hệt câu gốc dù câu Nhật khác."""
    loi, canh_bao = [], []
    wm = (((doc_ko.get("word") or {}).get("meaning") or {}).get(lang) or "").strip()
    if wm and not re.match(r"^(는|은)\s", wm):
        loi.append("D11: word.meaning – bản Hàn phải bắt đầu bằng trợ từ '는'/'은' (đứng ngay sau từ tiếng Nhật khi hiển thị)")
    for i, o in enumerate(((doc_ko.get("analysis") or {}).get("options") or [])):
        for k in ("sentence", "correction"):
            s = o.get(k) or {}
            ja, ko = s.get("ja") or "", ((s.get("meaning") or {}).get(lang) or "")
            if ko and "{" in ja and (ja.count("{"), ja.count("}")) != (ko.count("{"), ko.count("}")):
                loi.append(f"D7: analysis.options[{i}].{k}.meaning – số dấu {{ }} khác câu tiếng Nhật")
        s, c = o.get("sentence") or {}, o.get("correction") or {}
        sk, ck = ((s.get("meaning") or {}).get(lang) or "").strip(), ((c.get("meaning") or {}).get(lang) or "").strip()
        if sk and ck and sk == ck and strip_marks(s.get("ja") or "") != strip_marks(c.get("ja") or ""):
            canh_bao.append(f"D10: analysis.options[{i}]: nghĩa câu gốc và nghĩa câu sửa giống hệt nhau dù câu tiếng Nhật khác – xem lại")
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
