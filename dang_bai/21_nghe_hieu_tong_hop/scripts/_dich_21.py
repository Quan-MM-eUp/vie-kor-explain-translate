"""Dạng 21 – Nghe hiểu tổng hợp: phần riêng giai đoạn 2 (dịch Hàn).

Nguồn dịch của từng trường:
  - DỊCH TRỰC TIẾP TỪ TIẾNG NHẬT (tác tử TẠO không thấy bản Việt):
      full_translation[*].lines[*].meaning   ← lines[*].ja (+ speaker)      – văn nói, mức lịch sự theo câu Nhật
      key_info[*].meaning                    ← key_info[*].ja
      question.meaning                       ← question.ja
      options[*].meaning                     ← options[*].option_ja
      options[*].quotes[*].meaning           ← quotes[*].ja
    (trường có ja = null → dịch từ tiếng Việt)
  - DỊCH TỪ TIẾNG VIỆT: options[*].analysis (-습니다).
  - Câu con 2 (norm.ft_chep_tu): full_translation điền sẵn từ bản Hàn của câu con 1 (s2_claude_dich.py --nhan thay chỗ giữ chỗ).
Trường dịch từ tiếng Nhật không dùng câu cố định / bộ nhớ dịch.
"""
import copy
import re

import _dang as D
from pipeline_chung.common import get_path, iter_lang_fields, load_json, parse_path, path_str, strip_marks
from pipeline_chung.dich import prefill, tagged_copy

NOTE_JA = "[dịch từ tiếng Nhật]"
NOTE_KH = "[kết hợp]"
NOTE_VD = "[tham khảo]"
GIU_CHO = "⟦CHÉP_TỪ_CÂU_CON_1⟧"
JA_RE = re.compile(r"^\$\.(?:full_translation\[(\d+)\]\.lines\[(\d+)\]|key_info\[(\d+)\]|(question)|options\[(\d+)\]\.quotes\[(\d+)\]|options\[(\d+)\])\.meaning$")
FT_RE = re.compile(r"^\$\.full_translation\[")


def nguon_ja(doc, path):
    m = JA_RE.match(path)
    if not m:
        raise KeyError(path)
    if m.group(1) is not None:
        ln = doc["full_translation"][int(m.group(1))]["lines"][int(m.group(2))]
        return {"cau_tieng_nhat": ln.get("ja"), "nguoi_noi": ln.get("speaker"),
                "luu_y": "Một lượt thoại: dịch văn nói tự nhiên, giữ mức lịch sự / quan hệ trên–dưới theo câu Nhật (thể thường → 반말, です・ます → -요/-습니다); "
                         "giữ ký hiệu (i) / (ii) ở đúng chỗ; không thêm nhãn người nói."}
    if m.group(3) is not None:
        ln = doc["key_info"][int(m.group(3))]
        return {"cau_tieng_nhat": ln.get("ja"), "nguoi_noi": ln.get("speaker"),
                "luu_y": "Câu then chốt (khối Thông tin) – nếu trùng một lượt thoại thì dịch GIỐNG HỆT bản dịch lượt thoại đó."}
    if m.group(4):
        return {"cau_tieng_nhat": (doc.get("question") or {}).get("ja"), "luu_y": "Câu hỏi của đề – dịch như câu hỏi đề thi (-습니까 / -나요)."}
    if m.group(5) is not None:
        qt = doc["options"][int(m.group(5))]["quotes"][int(m.group(6))]
        return {"cau_tieng_nhat": qt.get("ja"), "luu_y": "Câu trích từ lời thoại – dịch GIỐNG HỆT bản dịch lượt thoại chứa câu này (cùng mức lịch sự)."}
    o = doc["options"][int(m.group(7))]
    return {"cau_tieng_nhat": o.get("option_ja"), "luu_y": "Lựa chọn của đề – cụm ngắn / câu ngắn như lựa chọn đề thi, không thêm ý."}


def nguon_ja_text(doc, path):
    return nguon_ja(doc, path)["cau_tieng_nhat"] or ""


def _is_ja(doc, path):
    return bool(JA_RE.match(path)) and bool(nguon_ja_text(doc, path).strip())


def danh_dau(fmap, doc, cfg):
    """nguon_dich: ja (dịch thẳng từ tiếng Nhật) · vi."""
    for f in fmap:
        if _is_ja(doc, f["path"]):
            f["nguon_dich"], f["ja"] = "ja", nguon_ja_text(doc, f["path"])
        else:
            f["nguon_dich"] = "vi"
    return fmap


def prefill_21(fmap, fixed, tm, chep_ft=False):
    filled, todo_vi = prefill([f for f in fmap if f["nguon_dich"] == "vi" and not (chep_ft and FT_RE.match(f["path"]))], fixed, tm)
    keep = set(todo_vi) | {f["id"] for f in fmap if f["nguon_dich"] == "ja"}
    if chep_ft:
        for f in fmap:
            if FT_RE.match(f["path"]):
                filled[f["id"]] = {"text": GIU_CHO, "nguon": "chep_cau_con_1"}
                keep.discard(f["id"])
    return filled, [f["id"] for f in fmap if f["id"] in keep]


def tagged_copy_21(doc, fmap, lang):
    d = tagged_copy(doc, fmap, lang)
    for f in fmap:
        if f["nguon_dich"] == "ja":
            path = parse_path(f["path"])
            get_path(d, path[:-1])[path[-1]] = {"id": f["id"], "dich_tu_tieng_nhat": True, "nguon": nguon_ja(doc, f["path"])}
    return d


def chep_ft_tu_cau_1(doc_ko, norm, lang="ko"):
    """Câu con 2: thay chỗ giữ chỗ trong full_translation bằng bản Hàn của câu con 1. Trả về danh sách lỗi."""
    sid1 = norm.get("ft_chep_tu")
    src = None
    for lop in ("final", "checked", "claude_tao"):
        p = D.OUT("json_ko", lop, sid1 + ".json")
        if D.os.path.exists(p):
            src = load_json(p)
            break
    if src is None:
        return [f"chưa có bản Hàn của câu con 1 ({sid1}) – dịch / chạy --nhan câu con 1 trước"]
    if src.get("full_translation") is None or _bo_ko(src["full_translation"], lang) != _bo_ko(doc_ko.get("full_translation"), lang):
        return [f"full_translation (bản Việt) khác câu con 1 ({sid1}) – đồng bộ GĐ1 trước"]
    doc_ko["full_translation"] = copy.deepcopy(src["full_translation"])
    return []


def _bo_ko(o, lang):
    if isinstance(o, dict):
        return {k: _bo_ko(v, lang) for k, v in o.items() if not (k == lang and isinstance(o.get("vi"), str))}
    if isinstance(o, list):
        return [_bo_ko(v, lang) for v in o]
    return o


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


PARTICLE_RE = re.compile(r"⟪([぀-ゟ゠-ヿー]+)⟫[\"'”」』)）]*(이라는|라는|이라고|라고|이며|며|으로|로|은|는|이|가|을|를|과|와)(?![가-힣])")
BATCHIM = {"이라는", "이라고", "이며", "으로", "은", "이", "을", "과"}
DOI = {"이라는": "라는", "라는": "이라는", "이라고": "라고", "라고": "이라고", "이며": "며", "며": "이며", "으로": "로", "로": "으로",
       "은": "는", "는": "은", "이": "가", "가": "이", "을": "를", "를": "을", "과": "와", "와": "과"}


def kiem_tra_21(doc_ko, norm, lang="ko"):
    """D12 (cảnh báo): trợ từ sau ⟪kana⟫; D15 (cảnh báo): câu trích / câu then chốt trùng lượt thoại nhưng bản dịch khác;
    D16 (lỗi): câu con 2 – full_translation phải giống hệt câu con 1; D17 (lỗi): (i)/(ii) của lượt thoại phải giữ trong bản Hàn."""
    loi, cb = [], []
    for fp, o in iter_lang_fields(doc_ko):
        for m in PARTICLE_RE.finditer(o.get(lang) or ""):
            kana, p = m.group(1), m.group(2)
            if (kana[-1] == "ん") != (p in BATCHIM):
                cb.append(f"D12: {path_str(fp)}: '{kana}' + '{p}' – trợ từ sai theo âm cuối, nên là '{DOI[p]}'")
    dong = {}
    for i, blk in enumerate(doc_ko.get("full_translation") or []):
        for j, ln in enumerate(blk.get("lines") or []):
            ko = ((ln.get("meaning") or {}).get(lang) or "")
            if ln.get("ja"):
                dong[re.sub(r"\s", "", strip_marks(ln["ja"]))] = ko
                for mk in ("(i)", "(ii)", "(iii)"):
                    if mk in ln["ja"] and ko and mk not in ko:
                        loi.append(f"D17: full_translation[{i}].lines[{j}]: bản Hàn mất ký hiệu {mk}")
    items = [(f"options[{a}].quotes[{b}]", q) for a, o in enumerate(doc_ko.get("options") or []) for b, q in enumerate(o.get("quotes") or [])]
    items += [(f"key_info[{a}]", x) for a, x in enumerate(doc_ko.get("key_info") or [])]
    for name, q in items:
        k = re.sub(r"\s", "", strip_marks(q.get("ja") or ""))
        ko = ((q.get("meaning") or {}).get(lang) or "")
        if k in dong and dong[k] and ko and ko.strip() != dong[k].strip():
            cb.append(f"D15: {name}: câu Nhật trùng một lượt thoại nhưng bản dịch khác – nên dịch giống hệt lượt thoại")
    if norm.get("ft_chep_tu"):
        for lop in ("checked", "final"):
            p = D.OUT("json_ko", lop, norm["ft_chep_tu"] + ".json")
            if D.os.path.exists(p):
                if load_json(p).get("full_translation") != doc_ko.get("full_translation"):
                    loi.append(f"D16: full_translation phải giống hệt bản Hàn của câu con 1 ({norm['ft_chep_tu']}) – sửa ở câu con 1")
                break
    return loi, cb


def d4_key(f, doc):
    if f.get("nguon_dich") == "ja":
        return NOTE_JA + " " + strip_marks(nguon_ja_text(doc, f["path"]))
    return None
