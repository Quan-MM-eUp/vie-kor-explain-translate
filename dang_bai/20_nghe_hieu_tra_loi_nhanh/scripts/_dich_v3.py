"""Dạng 20 – Nghe hiểu: Trả lời nhanh: phần riêng giai đoạn 2 (dựng 2026-10-08 từ dạng 08).

  - TRỰC TIẾP từ tiếng Nhật (tác tử TẠO không thấy bản Việt – lời thoại):
      prompt.utterance.meaning           (nghĩa câu nói)
      options[i].sentence.meaning        (nghĩa từng câu trả lời)
    → dịch như LỜI NÓI, giữ mức lịch sự của câu Nhật (ため口 → 반말, です/ます → 해요체, kính ngữ / khiêm nhường → 존댓말 tương ứng).
  - còn lại (options[i].analysis, prompt.analysis[]) dịch từ tiếng Việt, văn phong -습니다.
Trường dịch từ tiếng Nhật không dùng câu cố định / bộ nhớ dịch.
"""
import re

import _dang  # noqa: F401  (sys.path → Vie-Kor)
from pipeline_chung.common import get_path, parse_path, strip_marks
from pipeline_chung.dich import prefill, tagged_copy

NOTE_JA = "[dịch từ tiếng Nhật]"
NOTE_KH = "[kết hợp: nghĩa theo tiếng Nhật]"
NOTE_VD = "[tham khảo]"
JA_RE = re.compile(r"^\$\.(?:prompt\.(utterance)\.meaning|options\[(\d+)\]\.sentence\.meaning)$")

LUU_Y_LICH_SU = ("Dịch như LỜI NÓI tự nhiên của người Hàn trong cùng tình huống, bám sát câu Nhật (thì, phủ định, bị động, sai khiến, chủ thể, "
                 "cho/nhận あげる・くれる・もらう, sắc thái ね/よ/かな). GIỮ MỨC LỊCH SỰ của câu Nhật: thể thường / ため口 → 반말 (-아/어, -지, -네, -야); "
                 "です・ます → 해요체 (-아요/어요); kính ngữ / khiêm nhường (いらっしゃる, おっしゃる, 申す, いたす, ございます…) → 존댓말 / 하십시오체 tương ứng "
                 "(-(으)시-, -습니다). Không có { } trong bản Hàn trừ khi câu Nhật có.")


def _is_ja(path, cfg):
    return bool(JA_RE.match(path)) and bool((cfg or {}).get("dich_tu_nhat", {}).get("truong", True))


def nguon_ja(doc, path):
    m = JA_RE.match(path)
    if not m:
        raise KeyError(path)
    u = ((doc.get("prompt") or {}).get("utterance")) or {}
    if m.group(1):
        return {"vai_tro": "CÂU NÓI (lượt thoại thứ nhất)", "cau_tieng_nhat": u.get("ja"), "luu_y": LUU_Y_LICH_SU}
    i = int(m.group(2))
    o = (doc.get("options") or [])[i]
    return {"vai_tro": f"CÂU TRẢ LỜI {o.get('index')} (đáp lại câu nói)", "cau_tieng_nhat": (o.get("sentence") or {}).get("ja"),
            "cau_noi": u.get("ja"), "luu_y": LUU_Y_LICH_SU + " Câu trả lời SAI cũng dịch đúng như câu Nhật đang viết (không sửa cho hợp lý)."}


def nguon_ja_text(doc, path):
    return nguon_ja(doc, path)["cau_tieng_nhat"] or ""


def danh_dau(fmap, doc, cfg):
    for f in fmap:
        if _is_ja(f["path"], cfg) and nguon_ja_text(doc, f["path"]).strip():
            f["nguon_dich"], f["ja"] = "ja", nguon_ja_text(doc, f["path"])
        else:
            f["nguon_dich"] = "vi"          # không có câu Nhật (script không tách được) → dịch từ bản Việt
    return fmap


def prefill_v3(fmap, fixed, tm):
    """Câu cố định / bộ nhớ dịch: chỉ trường dịch từ tiếng Việt."""
    filled, todo_vi = prefill([f for f in fmap if f["nguon_dich"] == "vi"], fixed, tm)
    keep = set(todo_vi) | {f["id"] for f in fmap if f["nguon_dich"] == "ja"}
    return filled, [f["id"] for f in fmap if f["id"] in keep]


def tagged_copy_v3(doc, fmap, lang):
    d = tagged_copy(doc, fmap, lang)
    for f in fmap:
        if f["nguon_dich"] == "ja":
            path = parse_path(f["path"])
            parent = get_path(d, path[:-1])
            parent[path[-1]] = {"id": f["id"], "dich_tu_tieng_nhat": True, "nguon": nguon_ja(doc, f["path"])}
    return d


# ---------------- kiểm tra riêng ----------------
_BO_QUA_JA = ("nội dung ⟪ ⟫ khác bản tiếng Việt", "furigana khác bản tiếng Việt", "tỷ lệ độ dài KO/VI", "câu cố định phải dịch là",
              "văn phong -습니다", "có tiếng Nhật nằm ngoài ⟪ ⟫")


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


LICH_SU_JA = re.compile(r"(です|ます|ません|ました|ましょう|ませんか|でしょう|ございま|いらっしゃ|おっしゃ|申し|いたし|くださ)")
LICH_SU_KO = re.compile(r"(요|니다|니까|세요|십시오|죠)[\.\?!…~\s]*$")


def kiem_tra_v3(doc_ko, lang="ko"):
    """D7 (lỗi): số { } của nghĩa câu khác bản tiếng Việt. D12 (cảnh báo): trợ từ sau ⟪kana⟫.
    D15 (cảnh báo): mức lịch sự – câu Nhật có です/ます/kính ngữ mà bản Hàn kết thúc kiểu 반말; câu Nhật thể thường mà bản Hàn có -요/-니다."""
    loi, canh_bao = [], []
    u = ((doc_ko.get("prompt") or {}).get("utterance")) or {}
    cac = [("prompt.utterance", u)] + [(f"options[{i}].sentence", (o.get("sentence") or {})) for i, o in enumerate(doc_ko.get("options") or [])]
    for name, s in cac:
        mv = s.get("meaning") or {}
        v, k, ja = mv.get("vi") or "", _ko(mv, lang), strip_marks(s.get("ja") or "")
        if k and (v.count("{"), v.count("}")) != (k.count("{"), k.count("}")) and "{" not in ja:
            loi.append(f"D7: {name}.meaning – số dấu {{ }} khác bản tiếng Việt")
        if not k or not ja:
            continue
        cuoi = re.split(r"[\n。]", k.strip())[-1].strip() or k.strip()
        if LICH_SU_JA.search(ja) and not LICH_SU_KO.search(k):
            canh_bao.append(f"D15: {name}.meaning – câu Nhật lịch sự (です/ます/kính ngữ) nhưng bản Hàn không kết thúc -요/-니다: '{cuoi[-25:]}'")
        elif not LICH_SU_JA.search(ja) and LICH_SU_KO.search(k):
            canh_bao.append(f"D15: {name}.meaning – câu Nhật thể thường (ため口) nhưng bản Hàn dùng -요/-니다: '{cuoi[-25:]}' – xem lại (trừ khi quan hệ nói rõ cần lịch sự)")
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
            if (kana[-1] == "ん") != (p in BATCHIM):
                out.append(f"D12: {path_str(fp)}: '{kana}' + '{p}' – trợ từ sai theo âm cuối, nên là '{DOI[p]}'")
    return out
