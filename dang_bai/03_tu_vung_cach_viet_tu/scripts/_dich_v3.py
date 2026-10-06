"""Dạng 03 – Cách viết từ: phần riêng giai đoạn 2 (dựng 2026-10-05 theo cách làm v3 của dạng 01/02).

  - question.meaning (Nghĩa câu)  ← dịch TRỰC TIẾP từ question.ja; GPT không thấy bản tiếng Việt của trường này.
  - analysis.options[i].analysis  ← KẾT HỢP: dịch từ tiếng Việt, nhưng GPT nhận kèm lựa chọn tiếng Nhật (option_ja, cách đọc)
    và dịch nghĩa trong 'có nghĩa là "…"' THEO ĐÚNG lựa chọn tiếng Nhật đó.
  - reference (có câu ví dụ)      ← VI + VD: dịch từ tiếng Việt, riêng dòng nghĩa của mỗi câu ví dụ dịch TRỰC TIẾP từ câu ví dụ
    tiếng Nhật ngay phía trên (config dich_tu_nhat.vi_du_tham_khao).
  - phần còn lại (intro, conclusion = đoạn giải thích bẫy) dịch từ tiếng Việt.
Trường dịch từ tiếng Nhật không dùng câu cố định / bộ nhớ dịch.
"""
import re

import _dang  # noqa: F401  (đặt sys.path tới thư mục Vie-Kor để import pipeline_chung)
from pipeline_chung.common import get_path, parse_path, strip_marks
from pipeline_chung.dich import prefill, tagged_copy

NOTE_JA = "[dịch từ tiếng Nhật]"
NOTE_KH = "[kết hợp: nghĩa theo lựa chọn tiếng Nhật]"
NOTE_VD = "[tham khảo: dòng nghĩa câu ví dụ dịch theo câu ví dụ tiếng Nhật]"
VD_RE = re.compile(r"(?m)^\s*[+\-•]?\s*⟪[^⟫]*[㐀-鿿぀-ゟ゠-ヿ][^⟫]*[。．！？!?]?⟫\s*$")   # dòng chỉ gồm một câu tiếng Nhật trong ⟪ ⟫
OPT_RE = re.compile(r"^\$\.analysis\.options\[(\d+)\]\.analysis$")


def ja_paths(cfg):
    return {"$." + p.lstrip("$.") for p in (cfg.get("dich_tu_nhat") or {}).get("truong", [])}


def nguon_ja(doc, path):
    q = doc.get("question") or {}
    if path == "$.question.meaning":
        return {"cau_tieng_nhat": q.get("ja"), "cach_doc": q.get("reading")}
    raise KeyError(path)


def nguon_ja_text(doc, path):
    return nguon_ja(doc, path)["cau_tieng_nhat"] or ""


def _opt(doc, path):
    m = OPT_RE.match(path)
    if not m:
        return None
    return ((doc.get("analysis") or {}).get("options") or [])[int(m.group(1))]


def danh_dau(fmap, doc, cfg):
    """nguon_dich: ja (dịch thẳng từ tiếng Nhật) · ket_hop (VI + lựa chọn tiếng Nhật) · vi_vd (tham khảo có câu ví dụ) · vi."""
    jp, kh = ja_paths(cfg), (cfg.get("dich_tu_nhat") or {}).get("ket_hop_lua_chon", True)
    vd = (cfg.get("dich_tu_nhat") or {}).get("vi_du_tham_khao", True)
    for f in fmap:
        o = _opt(doc, f["path"])
        if f["path"] in jp:
            f["nguon_dich"], f["ja"] = "ja", nguon_ja_text(doc, f["path"])
        elif kh and o is not None:
            f["nguon_dich"], f["ja"] = "ket_hop", (o.get("option_ja") or "") + (f" ({o['reading']})" if o.get("reading") else "")
        elif vd and f["path"] == "$.reference" and VD_RE.search(f["vi"] or ""):
            f["nguon_dich"], f["ja"] = "vi_vd", "câu ví dụ tiếng Nhật trong chính trường này"
        else:
            f["nguon_dich"] = "vi"
    return fmap


def prefill_v3(fmap, fixed, tm):
    """Câu cố định / bộ nhớ dịch: chỉ cho trường dịch từ tiếng Việt và trường kết hợp (bộ nhớ dịch: chỉ trường VI)."""
    filled_vi, todo_vi = prefill([f for f in fmap if f["nguon_dich"] == "vi"], fixed, tm)
    todo_vi += [f["id"] for f in fmap if f["nguon_dich"] == "vi_vd"]           # tham khảo có ví dụ: luôn gửi GPT (không câu cố định / bộ nhớ dịch)
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
            o = _opt(doc, f["path"])
            parent[path[-1]] = {"id": f["id"], "vi": f["vi"], "lua_chon_tieng_nhat": o.get("option_ja"),
                                "cach_doc": o.get("reading"),
                                "luu_y": "Nghĩa trong 'có nghĩa là \"…\"' dịch theo ĐÚNG lựa chọn tiếng Nhật này (từ loại, dạng); lựa chọn bị ghi không tồn tại thì không thêm nghĩa; phần còn lại dịch sát tiếng Việt."}
        elif f["nguon_dich"] == "vi_vd":
            parent[path[-1]] = {"id": f["id"], "vi": f["vi"], "vi_du_tieng_nhat": True,
                                "luu_y": "Dòng nghĩa của mỗi câu ví dụ dịch TRỰC TIẾP từ câu ví dụ tiếng Nhật ⟪…⟫ ngay phía trên (bỏ qua bản Việt của dòng đó); dòng câu ví dụ và dòng cách đọc chép nguyên; các dòng khác dịch từ tiếng Việt."}
    return d


# ---------------- kiểm tra riêng ----------------
_BO_QUA_JA = ("nội dung ⟪ ⟫ khác bản tiếng Việt", "furigana khác bản tiếng Việt", "tỷ lệ độ dài KO/VI", "câu cố định phải dịch là")


def loc_kiem_tra(msgs, fmap):
    jp = [f["path"] for f in fmap if f.get("nguon_dich") == "ja"]
    out = []
    for m in msgs:
        p = next((x for x in jp if re.search(re.escape(x) + r"(?![\w\[])", m)), None)
        if p and any(k in m for k in _BO_QUA_JA):
            continue
        out.append(m)
    return out


NEG_JA = re.compile(r"(ない|なかった|ず|ぬ|ません|ませんでした)[。.]?$")
NEG_KO = re.compile(r"(않|안 |없|못|말|지 마|불|비)")
PASS_JA = re.compile(r"(される|された|されて|られる|られた|られて|れる|れた|れて)[。.]?$")
PASS_KO = re.compile(r"(되|받|어지|아지|여지|당하|히다|히었|혔|리다|렸|기다|겼)")


def kiem_tra_v3(doc_ko, lang="ko"):
    """D7 (lỗi): số { } của Nghĩa câu ≠ câu tiếng Nhật. D6 (cảnh báo): câu 'Nghĩa là' của lựa chọn có vẻ mất phủ định / bị động."""
    loi, canh_bao = [], []
    q = doc_ko.get("question") or {}
    qj, qm = q.get("ja") or "", ((q.get("meaning") or {}).get(lang) or "")
    if qm and (qj.count("{"), qj.count("}")) != (qm.count("{"), qm.count("}")):
        loi.append("D7: question.meaning – số dấu { } khác câu tiếng Nhật (question.ja)")
    for i, o in enumerate(((doc_ko.get("analysis") or {}).get("options") or [])):
        oj = strip_marks(o.get("option_ja") or "").strip()
        ko = ((o.get("analysis") or {}).get(lang) or "")
        head = ko.split("뜻", 1)[0] if "뜻" in ko else ""
        if not (oj and head):
            continue
        if NEG_JA.search(oj) and not NEG_KO.search(head):
            canh_bao.append(f"D6: analysis.options[{i}] – lựa chọn '{oj}' ở dạng PHỦ ĐỊNH nhưng phần nghĩa tiếng Hàn không thấy phủ định")
        if PASS_JA.search(oj) and not PASS_KO.search(head):
            canh_bao.append(f"D6: analysis.options[{i}] – lựa chọn '{oj}' có thể ở dạng BỊ ĐỘNG nhưng phần nghĩa tiếng Hàn không thấy bị động (xem lại)")
    return loi, canh_bao


def d4_key(f, doc):
    if f.get("nguon_dich") == "ja" and f["path"] == "$.question.meaning":
        return NOTE_JA + " " + strip_marks(nguon_ja_text(doc, f["path"]))
    return None
