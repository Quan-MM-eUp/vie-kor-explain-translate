"""Dạng 17 – Nghe hiểu điểm chính: phần riêng giai đoạn 2.

  Dịch TRỰC TIẾP từ tiếng Nhật (bản Việt chỉ để tham khảo ý):
    full_translation[*].lines[*].meaning   (lời thoại – giữ mức kính ngữ của câu Nhật, giữ (i))
    question.meaning                       (câu hỏi)
    options[*].meaning                     (nghĩa lựa chọn)
    key_info[*].meaning                    (dòng then chốt – trùng NGUYÊN một dòng thoại → Python CHÉP bản Hàn của dòng đó, không dịch lại)
  Dịch từ tiếng Việt: options[*].analysis (lý do khuôn B / câu giải thích của Thông tin) – văn phong -습니다.
"""
import re

import _dang as D
from pipeline_chung.common import get_path, parse_path, strip_marks
from pipeline_chung.dich import prefill, tagged_copy

NOTE_JA = "[dịch từ tiếng Nhật]"
JA_RE_PATH = re.compile(r"^\$\.(?:full_translation\[(\d+)\]\.lines\[(\d+)\]|(question)|options\[(\d+)\]|key_info\[(\d+)\])\.meaning$")


def nguon_ja(doc, path):
    """→ (câu tiếng Nhật, người nói, lưu ý)."""
    m = JA_RE_PATH.match(path)
    if not m:
        raise KeyError(path)
    if m.group(2) is not None:
        ln = doc["full_translation"][int(m.group(1))]["lines"][int(m.group(2))]
        return ln.get("ja"), ln.get("speaker"), "Lượt thoại – dịch tự nhiên theo văn nói, giữ mức kính ngữ / thân mật của câu Nhật; giữ (i) đúng chỗ."
    if m.group(3):
        q = doc.get("question") or {}
        return q.get("ja"), None, "Câu hỏi của đề – văn hỏi trang trọng (-ㅂ니까 / -습니까)."
    if m.group(4) is not None:
        o = doc["options"][int(m.group(4))]
        return o.get("option_ja"), None, "Lựa chọn – dịch ngắn gọn, giữ đúng hình thức (danh từ / câu) như tiếng Nhật."
    x = doc["key_info"][int(m.group(5))]
    return x.get("ja"), x.get("speaker"), "Dòng thoại then chốt (Thông tin) – dịch như lời thoại."


def _k(s):
    return re.sub(r"[\s　]+", "", strip_marks(D.bo_i(s or "")))


def sao_chep(doc):
    """{đường dẫn key_info[k].meaning: đường dẫn dòng thoại .meaning} khi key_info trùng NGUYÊN một dòng thoại."""
    out = {}
    lines = [(bi, li, ln) for bi, li, ln in D._lines(doc)]
    for k, x in enumerate(doc.get("key_info") or []):
        if not x.get("meaning"):
            continue
        hit = next(((bi, li) for bi, li, ln in lines if ln.get("meaning") and _k(ln.get("ja")) == _k(x.get("ja"))), None)
        if hit:
            out[f"$.key_info[{k}].meaning"] = f"$.full_translation[{hit[0]}].lines[{hit[1]}].meaning"
    return out


def danh_dau(fmap, doc, cfg):
    """nguon_dich: ja (dịch thẳng từ tiếng Nhật) · sao_chep (key_info trùng dòng thoại) · vi (analysis)."""
    sc = sao_chep(doc)
    by_path = {f["path"]: f["id"] for f in fmap}
    for f in fmap:
        if f["path"] in sc and sc[f["path"]] in by_path:
            f["nguon_dich"], f["sao_chep_tu"] = "sao_chep", by_path[sc[f["path"]]]
            f["ja"] = nguon_ja(doc, f["path"])[0]
        elif JA_RE_PATH.match(f["path"]):
            ja, sp, _ = nguon_ja(doc, f["path"])
            f["nguon_dich"], f["ja"], f["nguoi_noi"] = "ja", ja, sp
        else:
            f["nguon_dich"] = "vi"
    return fmap


def prefill_17(fmap, fixed, tm):
    """Câu cố định chỉ cho trường dịch từ tiếng Việt; không dùng bộ nhớ dịch (gần như mọi trường dịch từ tiếng Nhật)."""
    filled, todo_vi = prefill([f for f in fmap if f["nguon_dich"] == "vi"], fixed, {})
    keep = set(todo_vi) | {f["id"] for f in fmap if f["nguon_dich"] in ("ja", "sao_chep")}
    return filled, [f["id"] for f in fmap if f["id"] in keep]


def tagged_copy_17(doc, fmap, lang):
    d = tagged_copy(doc, fmap, lang)
    for f in fmap:
        path = parse_path(f["path"])
        parent = get_path(d, path[:-1])
        if f["nguon_dich"] == "ja":
            _, sp, luu_y = nguon_ja(doc, f["path"])
            parent[path[-1]] = {"id": f["id"], "dich_tu_tieng_nhat": True, "nguoi_noi": sp, "ja": f["ja"], "vi_tham_khao": f["vi"], "luu_y": luu_y}
        elif f["nguon_dich"] == "sao_chep":
            parent[path[-1]] = {"id": f["id"], "sao_chep_tu": f["sao_chep_tu"]}
    return d


def sao_chep_ids(fmap):
    return {f["id"]: f["sao_chep_tu"] for f in fmap if f.get("nguon_dich") == "sao_chep"}


# ---------------- kiểm tra riêng ----------------
_BO_QUA_JA = ("nội dung ⟪ ⟫ khác bản tiếng Việt", "furigana khác bản tiếng Việt", "tỷ lệ độ dài KO/VI", "câu cố định phải dịch là",
              "văn phong -습니다", "số dấu { } khác bản tiếng Việt")


def loc_kiem_tra(msgs, fmap):
    jp = [f["path"] for f in fmap if f.get("nguon_dich") in ("ja", "sao_chep")]
    out = []
    for m in msgs:
        p = next((x for x in jp if re.search(re.escape(x) + r"(?![\w\[])", m)), None)
        if p and any(k in m for k in _BO_QUA_JA):
            continue
        out.append(m)
    return out


SO_RE = re.compile(r"[0-9０-９]+")


def _so(s):
    return [x.translate(str.maketrans("０１２３４５６７８９", "0123456789")) for x in SO_RE.findall(strip_marks(s or ""))]


def kiem_tra_17(doc_ko, lang="ko"):
    """D-I (lỗi): câu Nhật có (i) → bản Hàn phải có (i).
    D-KI (lỗi): key_info trùng nguyên dòng thoại → bản Hàn phải giống hệt bản Hàn của dòng đó.
    D-SO (cảnh báo): số (chữ số) trong câu Nhật phải có trong bản Hàn."""
    loi, cb = [], []
    items = [(f"$.full_translation[{bi}].lines[{li}]", ln) for bi, li, ln in D._lines(doc_ko)]
    items += [("$.question", doc_ko.get("question") or {})]
    items += [(f"$.options[{k}]", {"ja": o.get("option_ja"), "meaning": o.get("meaning")}) for k, o in enumerate(doc_ko.get("options") or [])]
    items += [(f"$.key_info[{k}]", x) for k, x in enumerate(doc_ko.get("key_info") or [])]
    for p, x in items:
        ko = ((x.get("meaning") or {}).get(lang) or "") if x.get("meaning") else ""
        if not ko:
            continue
        if D.I_RE.search(x.get("ja") or "") and not D.I_RE.search(ko):
            loi.append(f"D-I: {p}.meaning – câu Nhật có (i) nhưng bản Hàn không có")
        thieu = [n for n in _so(x.get("ja")) if n not in _so(ko)]
        if thieu:
            cb.append(f"D-SO: {p}.meaning – số {thieu} của câu Nhật không thấy trong bản Hàn (kiểm tra số / giờ / ngày)")
    for kp, lp in sao_chep(doc_ko).items():
        a, b = get_path(doc_ko, parse_path(kp)), get_path(doc_ko, parse_path(lp))
        if D.bo_i((a or {}).get(lang)) != D.bo_i((b or {}).get(lang)):
            loi.append(f"D-KI: {kp} phải giống bản Hàn của {lp} (bỏ (i))")
    return loi, cb


def d4_key(f, doc):
    return None
