"""Dạng 05 – Hình thành từ: phần riêng giai đoạn 2 (dựng 2026-10-06 từ dạng 04).

  - question.meaning (câu đề có chỗ trống) và correct.full_sentence.meaning (câu hoàn chỉnh)
      ← dịch TRỰC TIẾP từ tiếng Nhật; GPT không thấy bản tiếng Việt của 2 trường này; giữ nguyên ký hiệu chỗ trống.
  - KẾT HỢP (bản Việt + tiếng Nhật – nghĩa phải đúng với từ tiếng Nhật):
      analysis.options[i].gloss             ← nghĩa gốc của lựa chọn (option_ja + label_paren)
      analysis.options[i].compound.meaning  ← nghĩa từ ghép (compound.ja + reading)
      reference.terms[j].meaning            ← nghĩa từ ví dụ tham khảo (terms[j].ja + reading)
  - phần còn lại (analysis.options[i].analysis, reference.intro, intro/conclusion) dịch từ tiếng Việt.
Trường dịch từ tiếng Nhật không dùng câu cố định / bộ nhớ dịch.
"""
import re

import _dang  # noqa: F401  (đặt sys.path tới thư mục Vie-Kor để import pipeline_chung)
from pipeline_chung.common import get_path, parse_path, strip_marks
from pipeline_chung.dich import prefill, tagged_copy

NOTE_JA = "[dịch từ tiếng Nhật]"
NOTE_KH = "[kết hợp: nghĩa theo từ tiếng Nhật]"
NOTE_VD = "[tham khảo: dòng nghĩa câu ví dụ dịch theo câu ví dụ tiếng Nhật]"
VD_RE = re.compile(r"(?m)^\s*[+\-•]?\s*⟪[^⟫]*[㐀-鿿぀-ゟ゠-ヿ][^⟫]*[。．！？!?]?⟫\s*$")   # dòng chỉ gồm một câu tiếng Nhật trong ⟪ ⟫
OPT_RE = re.compile(r"^\$\.analysis\.options\[(\d+)\]\.gloss$")
CP_RE = re.compile(r"^\$\.analysis\.options\[(\d+)\]\.compound\.meaning$")
TERM_RE_P = re.compile(r"^\$\.reference\.terms\[(\d+)\]\.meaning$")


def ja_paths(cfg):
    return {"$." + p.lstrip("$.") for p in (cfg.get("dich_tu_nhat") or {}).get("truong", [])}


def nguon_ja(doc, path):
    q = doc.get("question") or {}
    if path == "$.question.meaning":
        return {"cau_tieng_nhat": q.get("ja"), "cach_doc": q.get("reading"),
                "luu_y": "Câu đề có chỗ trống – giữ nguyên ký hiệu chỗ trống (cùng kiểu, cùng số lượng) ở vị trí tương ứng."}
    if path == "$.correct.full_sentence.meaning":
        fs = (doc.get("correct") or {}).get("full_sentence") or {}
        return {"cau_tieng_nhat": fs.get("ja"), "dap_an": (doc.get("correct") or {}).get("option_ja"),
                "luu_y": "Câu hoàn chỉnh (câu đề đã điền đáp án) – phần giống câu đề dịch giống question.meaning."}
    raise KeyError(path)


def nguon_ja_text(doc, path):
    return nguon_ja(doc, path)["cau_tieng_nhat"] or ""


def ket_hop_nguon(doc, path, cfg=None):
    """Trường kết hợp → {loai, tu_tieng_nhat, ngoac} hoặc None."""
    dn = (cfg or {}).get("dich_tu_nhat") or {}
    opts = (doc.get("analysis") or {}).get("options") or []
    m = OPT_RE.match(path)
    if m and dn.get("ket_hop_lua_chon", True):
        o = opts[int(m.group(1))]
        return {"loai": "nghia_goc_lua_chon", "tu_tieng_nhat": o.get("option_ja"), "ngoac": o.get("label_paren")}
    m = CP_RE.match(path)
    if m and dn.get("ket_hop_tu_ghep", True):
        cp = opts[int(m.group(1))].get("compound") or {}
        return {"loai": "nghia_tu_ghep", "tu_tieng_nhat": cp.get("ja"), "ngoac": cp.get("reading")}
    m = TERM_RE_P.match(path)
    if m and dn.get("ket_hop_tham_khao", True):
        t = ((doc.get("reference") or {}).get("terms") or [])[int(m.group(1))]
        return {"loai": "nghia_tu_tham_khao", "tu_tieng_nhat": t.get("ja"), "ngoac": t.get("reading")}
    return None


LUU_Y_KH = {
    "nghia_goc_lua_chon": "Nghĩa gốc của THÀNH PHẦN tiếng Nhật này (chữ Hán / đuôi / động từ ghép) – dịch đúng nghĩa của chính nó, giữ từ loại / thể (て, た, ます…) như bản Việt thể hiện; có thể dùng từ Hán Hàn tương ứng.",
    "nghia_tu_ghep": "Nghĩa của TỪ GHÉP tiếng Nhật này – dịch đúng nghĩa của từ ghép (thì / thể như dạng xuất hiện), không dịch theo nghĩa thành phần.",
    "nghia_tu_tham_khao": "Nghĩa của TỪ VÍ DỤ tiếng Nhật này – dịch đúng nghĩa của từ đó (kể cả phần giải thích trong ngoặc của bản Việt).",
}


def nghia_dap_an_trong_gioi_thieu(doc):
    """D9 – câu giới thiệu Tham khảo có nhắc lại NGUYÊN VĂN nghĩa gốc của đáp án trong ngoặc kép
    ('… với ý nghĩa là "tập hợp, tuyển tập":') → trả về (chỉ số lựa chọn đúng, nghĩa gốc tiếng Việt); không thì None."""
    intro = (((doc.get("reference") or {}).get("intro")) or {}).get("vi") or ""
    c = (doc.get("correct") or {}).get("index")
    opts = (doc.get("analysis") or {}).get("options") or []
    if not intro or not isinstance(c, int) or not (1 <= c <= len(opts)):
        return None
    g = (((opts[c - 1].get("gloss")) or {}).get("vi") or "").strip().rstrip(".")
    if g and re.search(r"[\"'“‘]" + re.escape(g) + r"\.?[\"'”’]", intro):
        return c - 1, g
    return None


def danh_dau(fmap, doc, cfg):
    """nguon_dich: ja (dịch thẳng từ tiếng Nhật) · ket_hop (VI + từ tiếng Nhật) · vi."""
    jp = ja_paths(cfg)
    for f in fmap:
        kh = ket_hop_nguon(doc, f["path"], cfg)
        if f["path"] in jp:
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
        elif f["path"] == "$.reference.intro" and nghia_dap_an_trong_gioi_thieu(doc):
            i, g = nghia_dap_an_trong_gioi_thieu(doc)
            gid = next((x["id"] for x in fmap if x["path"] == f"$.analysis.options[{i}].gloss"), None)
            parent[path[-1]] = {"id": f["id"], "vi": f["vi"], "nghia_trong_ngoac": g, "dung_lai_ban_dich_cua": gid,
                                "luu_y": f"Phần nghĩa trong ngoặc kép \"{g}\" là nghĩa gốc của đáp án – trong bản Hàn phải dùng ĐÚNG NGUYÊN VĂN bản dịch bạn đưa ra cho trường {gid}; phần còn lại của câu dịch từ tiếng Việt."}
        elif f["nguon_dich"] == "ket_hop":
            kh = ket_hop_nguon(doc, f["path"])
            parent[path[-1]] = {"id": f["id"], "vi": f["vi"], "tu_tieng_nhat": kh["tu_tieng_nhat"], "ngoac": kh.get("ngoac"),
                                "loai": kh["loai"], "luu_y": LUU_Y_KH[kh["loai"]]}
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
        kh = [f["path"] for f in fmap if f.get("nguon_dich") == "ket_hop"]
        if any(m.startswith(x + ":") for x in kh) and ("văn phong -습니다" in m or "tỷ lệ độ dài KO/VI" in m):
            continue        # nghĩa gốc / nghĩa từ ghép / nghĩa từ tham khảo là cụm từ (không phải câu -습니다; từ Hán Hàn ngắn hơn nhiều so với tiếng Việt)
        out.append(m)
    return out


NEG_JA = re.compile(r"(ない|なかった|ず|ぬ|ません|ませんでした)[。.]?$")
NEG_KO = re.compile(r"(않|안 |없|못|말|지 마|불|비)")
PASS_JA = re.compile(r"(される|された|されて|られる|られた|られて|[かさたなまらわがばぱ]れる|[かさたなまらわがばぱ]れた|[かさたなまらわがばぱ]れて)[。.]?$")   # bỏ れる/れて sau い・な・が… của động từ thường (いれて, 慣れて, ながれて)
PASS_KO = re.compile(r"(되|받|어지|아지|여지|당하|히다|히었|혔|리다|렸|기다|겼)")


def kiem_tra_v3(doc_ko, lang="ko"):
    """D7 (lỗi): số { } của Nghĩa câu ≠ câu tiếng Nhật. D8 (lỗi): số chỗ trống. D6 (cảnh báo): nghĩa gốc của lựa chọn có vẻ mất phủ định / bị động.
    D9 (cảnh báo): câu giới thiệu Tham khảo nhắc lại nghĩa gốc của đáp án nhưng bản Hàn không dùng đúng bản dịch nghĩa gốc đó."""
    loi, canh_bao = [], []
    q = doc_ko.get("question") or {}
    qj, qm = q.get("ja") or "", ((q.get("meaning") or {}).get(lang) or "")
    if qm and (qj.count("{"), qj.count("}")) != (qm.count("{"), qm.count("}")):
        loi.append("D7: question.meaning – số dấu { } khác câu tiếng Nhật (question.ja)")
    from _dang import BLANK_RE
    if qm and len(BLANK_RE.findall(qj)) != len(BLANK_RE.findall(qm)):
        loi.append(f"D8: question.meaning – số chỗ trống {len(BLANK_RE.findall(qm))} khác câu tiếng Nhật ({len(BLANK_RE.findall(qj))}) – phải giữ nguyên ký hiệu chỗ trống")
    nd = nghia_dap_an_trong_gioi_thieu(doc_ko)
    if nd:
        gk = ((((doc_ko["analysis"]["options"][nd[0]]).get("gloss")) or {}).get(lang) or "").strip().rstrip(".")
        ik = ((doc_ko["reference"].get("intro") or {}).get(lang) or "")
        if gk and gk not in ik:
            canh_bao.append(f"D9: reference.intro – nghĩa trong ngoặc kép phải dùng đúng bản dịch nghĩa gốc của đáp án (analysis.options[{nd[0]}].gloss = '{gk}')")
    for i, o in enumerate(((doc_ko.get("analysis") or {}).get("options") or [])):
        oj = strip_marks(o.get("option_ja") or "").strip()
        head = ((o.get("gloss") or {}).get(lang) or "")
        if not (oj and head):
            continue
        if NEG_JA.search(oj) and not NEG_KO.search(head):
            canh_bao.append(f"D6: analysis.options[{i}].gloss – lựa chọn '{oj}' ở dạng PHỦ ĐỊNH nhưng nghĩa gốc tiếng Hàn không thấy phủ định")
        if PASS_JA.search(oj) and not PASS_KO.search(head):
            canh_bao.append(f"D6: analysis.options[{i}].gloss – lựa chọn '{oj}' có thể ở dạng BỊ ĐỘNG nhưng nghĩa gốc tiếng Hàn không thấy bị động (xem lại)")
    return loi, canh_bao


def d4_key(f, doc):
    if f.get("nguon_dich") == "ja" and f["path"] in ("$.question.meaning", "$.correct.full_sentence.meaning"):
        return NOTE_JA + " " + strip_marks(nguon_ja_text(doc, f["path"]))
    return None
