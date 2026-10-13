"""Dạng 18 – Nghe hiểu khái quát: TÁCH lời thoại tiếng Nhật và lời giải tiếng Việt (chỉ tách, không sửa câu chữ).

Lời thoại (cột transcript_vi; 4 câu dán nhầm lời giải vào transcript_vi → lấy doan_van):
    [dòng dẫn] + các lượt thoại 'người nói：…' + câu hỏi + 4 lựa chọn (đánh số '1.' / '１．' / '1 ' hoặc không đánh số)
    → tach_loi_thoai(row) = {nguon, kieu, dong: [{so: 'L1', speaker, ja}], cau_hoi, lua_chon[4], sau_lua_chon, bo_dau}
Lời giải (cột giai_thich_vi):
    [bản dịch VI lời thoại] + [câu hỏi VI] + '###' + 4 khối 'n. lựa chọn' / 'Nghĩa:' / phân tích (câu trích 「…」(dịch)) / '→ ĐÚNG|SAI'
    → tach_loi_giai(html) = {text, broken, khuon (A/C/D/E/trong), dich: [dòng VI], cau_hoi_vi, lua_chon_vi[4] (khuôn D),
                             khoi: [{so, lua_chon, nghia, dong, ket_luan, trich}]}
Khuôn: A = có '###' + phân tích 4 lựa chọn · C = phân tích nhưng không có '###' · D = chỉ bản dịch + câu hỏi + 4 lựa chọn tiếng Việt
       (không phân tích) · E = không có tiếng Việt (chỉ chép lời thoại Nhật) · trong = không có lời giải.
"""
import re

import _dang  # noqa: F401  (đặt sys.path tới Vie-Kor)
from pipeline_chung.common import FURI_RE, JA_RE, norm_ja, strip_marks
from pipeline_chung.normalize import normalize_html

VI_RE = re.compile(r"[ăâđêôơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]", re.I)
NUM = str.maketrans("１２３４", "1234")
_ATTR_RAC_RE = re.compile(r'\\?&quot;|\\"')


def lam_sach(html, giu_furigana=True):
    """HTML → văn bản chuẩn hóa (normalize_html: furigana ｜《》, <br>/<p> → \\n). Bỏ rác thuộc tính lang="\\&quot;JA\\&quot;"."""
    s = _ATTR_RAC_RE.sub("", html or "")
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", s)
    t, broken = normalize_html(s)
    t = t.replace("　", " ").replace("\xa0", " ")
    if not giu_furigana:
        t = FURI_RE.sub(lambda m: m.group(1), t)
    return t, broken


def _k(s):
    """Khóa so sánh tiếng Nhật: bỏ furigana, ⟪⟫{}, khoảng trắng, dấu câu, số thứ tự."""
    return re.sub(r"[\s　。．｡、,，.！!？?「」『』・（）()…‥\-－―~〜:：;；]", "", norm_ja(s or ""))


# ======================= LỜI THOẠI =======================
SPK_RE = re.compile(r"^\s*([^\s：:；「」『』。、，,！？!?()（）\[\]【】0-9０-９][^\s：:；「」『』。、，,！？!?()（）\[\]【】]{0,5}?)\s*([：:；])\s*(.*)$")
SPK_BO = {"注", "※", "Q", "問", "答"}
OPTN_RE = re.compile(r"^\s*([1-4１-４])(?:\s*[\.．。、,，\)）:：・]\s*|\s+)(\S.*)$")
QEND_RE = re.compile(r"(か|の|？|\?)\s*[。．｡、,，]?\s*(?:\(i\))?\s*$")
DE_BAI_RE = re.compile(r"^問題\s*[0-9０-９]*.*(問題用紙|せんたくし|選択肢)")


def _dong(text):
    out = []
    for l in (text or "").split("\n"):
        l = l.replace("{", "").replace("}", "").strip()
        if l and l not in ("-", "―", "ー"):
            out.append(l)
    return out


def chon_nguon(row):
    """Cột chứa lời thoại Nhật: transcript_vi; rỗng hoặc có chữ Việt (dán nhầm lời giải) → doan_van."""
    for col in ("transcript_vi", "doan_van"):
        t = lam_sach(row.get(col), giu_furigana=False)[0]
        if t.strip() and not VI_RE.search(t):
            return col, t
    return None, ""


def tach_nguoi_noi(line):
    m = SPK_RE.match(line)
    if not m:
        return None, line
    lab, sep, rest = m.group(1).strip(), m.group(2), m.group(3).strip()
    if lab in SPK_BO or not rest or (sep == "；" and len(lab) > 3):
        return None, line
    return lab, rest


def tach_loi_thoai(row):
    nguon, text = chon_nguon(row)
    L = _dong(text)
    bo_dau = []
    while L and DE_BAI_RE.search(L[0]):          # câu dẫn đề '問題3 では、問題用紙に…' dán đầu doan_van
        bo_dau.append(L.pop(0))
    res = {"nguon": nguon, "kieu": "khong_co", "dong": [], "cau_hoi": None, "lua_chon": None, "sau_lua_chon": [], "bo_dau": bo_dau}
    qi = None
    for i in range(len(L) - 4, -1, -1):          # 4 dòng đánh số 1–4 liên tiếp (lần cuối cùng)
        ms = [OPTN_RE.match(L[i + k]) for k in range(4)]
        if all(m and m.group(1).translate(NUM) == str(k + 1) for k, m in enumerate(ms)):
            res.update(kieu="so", lua_chon=[m.group(2).strip() for m in ms], sau_lua_chon=L[i + 4:])
            qi = i - 1
            break
    if res["lua_chon"] is None and len(L) >= 5 and QEND_RE.search(L[-5]) \
            and not any(re.search(r"[：:]", re.sub(r"^\s*Q\s*[：:]", "", x)) for x in L[-5:]):
        res.update(kieu="khong_so", lua_chon=L[-4:])
        qi = len(L) - 5
    if res["lua_chon"] is None:
        body = L
    else:
        body = L[:max(qi, 0)]
        if qi is not None and qi >= 0:
            res["cau_hoi"] = re.sub(r"^\s*Q\s*[：:]\s*", "", L[qi]).strip()
    for k, l in enumerate(body, 1):
        spk, ja = tach_nguoi_noi(l)
        res["dong"].append({"so": f"L{k}", "speaker": spk, "ja": ja})
    return res


def hien_thi_loi_thoai(lt):
    """Lời thoại đánh số cho tác tử TẠO / KIỂM TRA: 'L3 [男] …'."""
    out = [f"{d['so']} [{d['speaker'] or '-'}] {d['ja']}" for d in lt["dong"]]
    if lt.get("cau_hoi"):
        out.append(f"(câu hỏi) {lt['cau_hoi']}")
    for i, x in enumerate(lt.get("lua_chon") or [], 1):
        out.append(f"(lựa chọn {i}) {x}")
    for x in lt.get("sau_lua_chon") or []:
        out.append(f"(dòng sau lựa chọn – không đưa vào JSON) {x}")
    return "\n".join(out)


# ======================= LỜI GIẢI =======================
OPT_LG_RE = re.compile(r"^\s*([1-4])\s*[\.．。](?![0-9０-９])\s*(.*)$")  # (?!số): '4.5 là …' không phải đầu lựa chọn (14125_1)
NGHIA_RE = re.compile(r"^\s*Nghĩa\s*[:：]\s*(.*)$", re.I)
VERD_RE = re.compile(r"(?:→|->|=>)\s*(ĐÚNG|SAI)\b\s*[.。!]?", re.I)
CAU_HOI_NHAN_RE = re.compile(r"^\s*(?:Câu hỏi|Hỏi|Question|Q)\s*[:：]\s*", re.I)
SPK_VI_RE = re.compile(r"^\s*((?:[^\s:：.,!?「」()]+)(?:[ \t][^\s:：.,!?「」()]+){0,4})\s*[:：]\s+")
KHONG_PHAI_NHAN = {"nghĩa", "lưu ý", "chú ý", "ví dụ", "đáp án", "câu hỏi", "giải thích", "dịch", "lý do", "phân tích đoạn hội thoại"}
# Dòng "meta" của người soạn lời giải (17711_1) – không phải câu dịch (lô 161–170)
META_DICH_RE = re.compile(r"^(Tôi sẽ dịch từng câu|Chúng ta hãy bắt đầu với phần dịch|Tạm dịch tiếng Việt( đầy đủ)?\s*:?\s*$)")
QUOTE_RE = re.compile(r"「((?:[^「」]|「[^「」]*」)+)」")


def _vi(s):
    return bool(VI_RE.search(strip_marks(s or "")))


def bo_nhan_vi(line):
    """'Người phụ nữ: Gần đây…' → ('Người phụ nữ', 'Gần đây…'); không có nhãn → (None, line)."""
    m = SPK_VI_RE.match(line)
    if not m or m.group(1).strip().lower() in KHONG_PHAI_NHAN or JA_RE.search(strip_marks(m.group(1))):
        return None, line
    return m.group(1).strip(), line[m.end():].strip()


def cau_trich(text):
    return [m.group(1).strip() for m in QUOTE_RE.finditer(text or "") if JA_RE.search(strip_marks(m.group(1)))]


def tach_loi_giai(html):
    t, broken = lam_sach(html)
    L = [l.strip() for l in t.split("\n") if l.strip()]
    res = {"text": "\n".join(L), "broken": broken, "khuon": "trong", "dich": [], "cau_hoi_vi": None, "lua_chon_vi": None,
           "khoi": [], "co_phan_cach": False, "dong_nhan_cau_hoi": False}
    if not L:
        return res
    if any(l == "###" for l in L):
        k = L.index("###")
        head, body = L[:k], [x for x in L[k + 1:] if x != "###"]
        res["co_phan_cach"] = True
    else:
        k = None
        for i, l in enumerate(L):
            m = OPT_LG_RE.match(l)
            if m and m.group(1) == "1" and any(NGHIA_RE.match(x) or VERD_RE.search(x) for x in L[i + 1:i + 4]):
                k = i
                break
        head, body = (L, []) if k is None else (L[:k], L[k:])
    # khối phân tích 1–4
    cur, exp = None, 1
    for l in body:
        m = OPT_LG_RE.match(l)
        if m and int(m.group(1)) == exp:
            cur = {"so": exp, "lua_chon": m.group(2).strip(), "dong": []}
            res["khoi"].append(cur)
            exp += 1
            continue
        if cur is None:
            cur = {"so": 0, "lua_chon": None, "dong": []}
            res["khoi"].append(cur)
        cur["dong"].append(l)
    for b in res["khoi"]:
        b["nghia"] = None
        for j, l in enumerate(b["dong"][:2]):
            m = NGHIA_RE.match(l)
            if m:
                b["nghia"] = m.group(1).strip()
                break
        b["ket_luan"] = [v.upper() for v in VERD_RE.findall("\n".join(b["dong"]))]
        b["trich"] = cau_trich("\n".join(b["dong"]))
    co_pt = any(b["so"] and b["ket_luan"] for b in res["khoi"])
    if not any(_vi(l) for l in L):
        res["khuon"] = "E"
        return res
    if co_pt:
        res["khuon"] = "A" if res["co_phan_cach"] else "C"
    else:
        res["khuon"] = "D"
        head, res["khoi"] = L, []
    # phần đầu: bản dịch + câu hỏi (+ 4 lựa chọn VI ở khuôn D)
    head = [x for x in head if not META_DICH_RE.match(x)]
    if res["khuon"] == "D" and len(head) >= 5:
        res["lua_chon_vi"] = [re.sub(r"^\s*[1-4１-４]\s*[\.．。、\)）:：]?\s*", "", x) for x in head[-4:]]
        head = head[:-4]
    qi = None
    for i in range(len(head) - 1, max(-1, len(head) - 3), -1):
        h = CAU_HOI_NHAN_RE.sub("", head[i]).strip()
        if h and h.rstrip().endswith(("?", "？")) and _vi(h):
            qi = i
            break
    if qi is not None:
        res["cau_hoi_vi"] = CAU_HOI_NHAN_RE.sub("", head[qi]).strip()
        res["dong_nhan_cau_hoi"] = bool(CAU_HOI_NHAN_RE.match(head[qi]))
        rest = head[:qi] + head[qi + 1:]
    else:
        rest = head
    res["dich"] = [x for x in rest if not re.fullmatch(r"\s*(?:Câu hỏi|Bản dịch|Dịch|Hội thoại)\s*[:：]?\s*", x, re.I)]
    return res


# ---------- chữ tiếng Việt cần có trong JSON (đo độ phủ) ----------
DAN_RE = re.compile(r"^[^「」]{0,80}[:：]\s*$")                  # dòng dẫn câu trích: 'Người đàn ông nói:' / 'Ví dụ, người cha nói:'
DAN_TRUOC_TRICH_RE = re.compile(r"^[^「」]{0,60}?[:：]\s*(?=「)")     # 'Nam: 「…」' → bỏ 'Nam:'
NHAN_BO_RE = re.compile(r"(?i)^\s*(?:phân tích đoạn hội thoại|phân tích|câu thoại liên quan|câu thoại then chốt|câu trích dẫn|câu trích)\s*[:：]?\s*$")


def vi_lua_chon(b):
    """Chữ tiếng Việt của một khối lựa chọn (đã bỏ nhãn được phép bỏ) – nguồn đo K9."""
    out = [b["nghia"]] if b.get("nghia") else []
    dong = list(b["dong"])
    if dong and NGHIA_RE.match(dong[0]):
        dong = dong[1:]
    elif len(dong) > 1 and NGHIA_RE.match(dong[1]):
        dong = dong[:1] + dong[2:]
    for l in dong:
        if NHAN_BO_RE.match(l) or DAN_RE.match(l):
            continue
        l = DAN_TRUOC_TRICH_RE.sub("", l)
        l = QUOTE_RE.sub(lambda m: " " if JA_RE.search(strip_marks(m.group(1))) else m.group(0), l)   # câu trích Nhật → quotes[].ja
        l = VERD_RE.sub(" ", l)
        l = re.sub(r"(?i)[（(]\s*dịch\s*[:：]\s*", "(", l)
        l = re.sub(r"(?i)^\s*dịch\s*[:：]\s*", "", l)   # dòng 'Dịch: …' đứng riêng (2026-10-08, 14144)
        out.append(l)
    return "\n".join(out)


def vi_dong_dich(lines):
    return "\n".join(bo_nhan_vi(x)[1] for x in lines)
