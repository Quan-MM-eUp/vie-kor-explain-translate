"""Pipeline v3 – phần riêng của giai đoạn 2: trường dịch TRỰC TIẾP từ tiếng Nhật.

Theo đề xuất của CTV tiếng Hàn (phản hồi 02/10/2026): lỗi của bản Hàn đều do bản Việt (mất bị động / phủ định /
từ loại, dịch lệch nghĩa câu…). Vì vậy:
  - question.meaning  ← dịch từ question.ja (câu hỏi)
  - word.meaning      ← dịch từ word.ja (từ) theo ĐÚNG DẠNG xuất hiện trong câu (催された → 개최되었다, 詳しく → 자세히)
  - các trường còn lại (phân tích lựa chọn, tham khảo) vẫn dịch từ tiếng Việt như v2.
Trường dịch từ tiếng Nhật: GPT KHÔNG thấy bản tiếng Việt của trường đó; không dùng câu cố định / bộ nhớ dịch.
"""
import re

import _dang  # noqa: F401  (đặt sys.path tới thư mục Vie-Kor để import pipeline_chung)

from pipeline_chung.common import strip_marks
from pipeline_chung.dich import prefill, tagged_copy

NOTE_JA = "[dịch từ tiếng Nhật]"


def ja_paths(cfg):
    return {"$." + p.lstrip("$.") for p in (cfg.get("dich_tu_nhat") or {}).get("truong", [])}


def nguon_ja(doc, path):
    """Văn bản tiếng Nhật làm nguồn dịch cho trường path (dùng cho GPT, bảng xem nhanh của Claude và Excel CTV)."""
    w, q = doc.get("word") or {}, doc.get("question") or {}
    if path == "$.question.meaning":
        return {"cau_tieng_nhat": q.get("ja"), "cach_doc": q.get("reading")}
    if path == "$.word.meaning":
        dic = w.get("dictionary_form")
        return {"tu_tieng_nhat": w.get("ja"), "cach_doc": w.get("reading"),
                "the_tu_dien": f"{dic['ja']} ({dic['reading']})" if dic else None, "cau_chua_tu": q.get("ja")}
    raise KeyError(path)


def nguon_ja_text(doc, path):
    s = nguon_ja(doc, path)
    if path == "$.question.meaning":
        return s["cau_tieng_nhat"] or ""
    return s["tu_tieng_nhat"] + (f" (thể từ điển: {s['the_tu_dien']})" if s["the_tu_dien"] else "")


def danh_dau(fmap, doc, cfg):
    """Gắn nguon_dich = ja / vi cho từng mã trong bảng đối chiếu."""
    jp = ja_paths(cfg)
    for f in fmap:
        if f["path"] in jp:
            f["nguon_dich"], f["ja"] = "ja", nguon_ja_text(doc, f["path"])
        else:
            f["nguon_dich"] = "vi"
    return fmap


def prefill_v3(fmap, fixed, tm):
    """Câu cố định / bộ nhớ dịch chỉ áp dụng cho trường dịch từ tiếng Việt."""
    filled, todo_vi = prefill([f for f in fmap if f["nguon_dich"] == "vi"], fixed, tm)
    keep = set(todo_vi) | {f["id"] for f in fmap if f["nguon_dich"] == "ja"}
    return filled, [f["id"] for f in fmap if f["id"] in keep]


def tagged_copy_v3(doc, fmap, lang):
    """Bản gửi GPT: trường dịch từ tiếng Việt = {"id", "vi"}; trường dịch từ tiếng Nhật = {"id", "dich_tu_tieng_nhat", "nguon"}
    (KHÔNG kèm bản tiếng Việt để GPT không bị kéo theo bản Việt)."""
    from pipeline_chung.common import get_path, parse_path
    d = tagged_copy(doc, fmap, lang)
    for f in fmap:
        if f["nguon_dich"] == "ja":
            path = parse_path(f["path"])
            get_path(d, path[:-1])[path[-1]] = {"id": f["id"], "dich_tu_tieng_nhat": True, "nguon": nguon_ja(doc, f["path"])}
    return d


# ---------------- kiểm tra riêng v3 ----------------
# Các kiểm tra chung so bản Hàn với bản Việt – không áp dụng cho trường dịch từ tiếng Nhật
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


NEG_JA = re.compile(r"(ない|なかった|ず|ぬ|ません|ませんでした)$")
NEG_KO = re.compile(r"(않|안 |없|못|말|지 마|불|비)")
PASS_JA = re.compile(r"(される|された|されて|られる|られた|られて|れる|れた|れて)$")
PASS_KO = re.compile(r"(되|받|어지|아지|여지|당하|히다|히었|혔|리다|렸|기다|겼)")


def kiem_tra_v3(doc_ko, lang="ko"):
    """D6 (cảnh báo): Nghĩa từ dịch từ tiếng Nhật có giữ dạng của từ trong câu không (phủ định, bị động, dấu { })."""
    canh_bao, loi = [], []
    w, q = doc_ko.get("word") or {}, doc_ko.get("question") or {}
    wj = strip_marks(w.get("ja") or "").strip()
    wm = ((w.get("meaning") or {}).get(lang) or "")
    if wj and wm:
        if NEG_JA.search(wj) and not NEG_KO.search(wm):
            canh_bao.append(f"D6: word.meaning – từ '{wj}' ở dạng PHỦ ĐỊNH nhưng nghĩa tiếng Hàn '{wm}' không thấy phủ định")
        if PASS_JA.search(wj) and not PASS_KO.search(wm):
            canh_bao.append(f"D6: word.meaning – từ '{wj}' có thể ở dạng BỊ ĐỘNG nhưng nghĩa tiếng Hàn '{wm}' không thấy bị động (xem lại)")
    qj, qm = q.get("ja") or "", ((q.get("meaning") or {}).get(lang) or "")
    if qm and (qj.count("{"), qj.count("}")) != (qm.count("{"), qm.count("}")):
        loi.append("D7: question.meaning – số dấu { } khác câu tiếng Nhật (question.ja)")
    return loi, canh_bao


def d4_key(f, doc):
    """Khóa so nhất quán giữa các câu: trường dịch từ tiếng Nhật so theo câu tiếng Nhật (bỏ { }), còn lại theo tiếng Việt."""
    if f.get("nguon_dich") == "ja" and f["path"] == "$.question.meaning":
        return NOTE_JA + " " + strip_marks(nguon_ja_text(doc, f["path"]))
    return None
