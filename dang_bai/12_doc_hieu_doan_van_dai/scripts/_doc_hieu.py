"""Phần tách / kiểm tra / hiển thị lời giải ĐỌC HIỂU (schema reading_listening.v1) – viết cho dạng 12 (2026-10-08),
viết tách riêng để dùng lại cho các dạng đọc hiểu 10 / 11 / 13 / 14 / 15 (cùng khuôn 'Trích dẫn … → ĐÚNG/SAI').

Không import _dang (tránh vòng lặp): các hàm nhận dữ liệu qua tham số; tokenizer Sudachi truyền vào bằng dat_tokenizer().

Khuôn lời giải (khuon_goc trong norm):
  chuan        câu hỏi tiếng Nhật + nghĩa → 4 khối 'i. <lựa chọn>' / Nghĩa / Trích dẫn 「…」(nghĩa) / Giải thích / → ĐÚNG|SAI
  chi_ban_dich chỉ có bản dịch tiếng Việt (đoạn văn + câu hỏi + 4 lựa chọn [+ 'Câu trả lời đúng là: …']) – không có phân tích
  tu_do        một đoạn văn xuôi về đáp án (không có khối lựa chọn)
  trong        không có lời giải
"""
import collections
import difflib
import re

from pipeline_chung.common import JA_RE, LOCK_RE, norm_ja, strip_marks, vi_words

# ---------------- tokenizer Sudachi (tùy chọn) ----------------
_TOK = {"t": None}


def dat_tokenizer(tok):
    _TOK["t"] = tok or None


def _hira(s):
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s or "")


def _yomi(t):
    tok = _TOK["t"]
    if not tok or not t:
        return ""
    from sudachipy import SplitMode
    try:
        return _hira("".join(m.reading_form() for m in tok.tokenize(t, SplitMode.C)))
    except Exception:                                                     # noqa: BLE001
        return ""


# ---------------- chuẩn hóa để so tiếng Nhật ----------------
GHI_CHU_RE = re.compile(r"注\s*[0-9０-９]+|※\s*[0-9０-９]*|\(\s*注\s*[0-9０-９]+\s*\)|（\s*注\s*[0-9０-９]+\s*）")
DOC_NGOAC_RE = re.compile(r"[(（][぀-ゟ゠-ヿー]+[)）]")            # cách đọc trong ngoặc: 会社(かいしゃ)


def phang(s):
    """Chuỗi tiếng Nhật 'phẳng' để so: bỏ furigana, { }, ⟪ ⟫, chú thích 注1, cách đọc trong ngoặc, ①②, dấu câu, khoảng trắng."""
    s = strip_marks(s or "").replace("{", "").replace("}", "")
    s = GHI_CHU_RE.sub("", s)
    s = DOC_NGOAC_RE.sub("", s)
    s = norm_ja(s)
    s = re.sub(r"[①-⑳⑴-⒇❶-❿]", "", s)
    s = re.sub(r"[^\w぀-ヿ㐀-䶿一-鿿々〆ヶ]", "", s)
    return s.replace("ー", "一").replace("_", "")


def giong(a, b):
    """So câu / lựa chọn tiếng Nhật (bỏ furigana, dấu, khoảng trắng); hoặc cùng cách đọc khi có Sudachi."""
    fa, fb = phang(a), phang(b)
    if fa and fa == fb:
        return True
    if fa and fb and _TOK["t"]:
        ya, yb = _yomi(fa), _yomi(fb)
        return bool(ya) and ya == yb
    return False


def co_tieng_nhat(s):
    return bool(re.search(r"[぀-ヿ㐀-䶿一-鿿]", strip_marks(s or "")))


# ---------------- K-TD: câu trích ↔ đoạn văn ----------------
CHIA_TRICH_RE = re.compile(r"…+|‥+|\.{3,}|・{3,}|（略）|\(略\)|〜|～")
MUC_TD = ["khop", "khop_doc", "lech_nhe", "lech_nang", "khong_tim_thay"]      # mức tăng dần; khop_dien tính như khop_doc


def _co_trong(fc, fp, lua_chon):
    """Câu trích = câu đoạn văn đã ĐIỀN một lựa chọn vào chỗ trống (①、（　）…): bỏ chữ của lựa chọn thì các phần còn lại đều có trong đoạn văn."""
    for lc in lua_chon or ():
        po = phang(lc)
        if len(po) >= 1 and po in fc:
            parts = [x for x in fc.split(po) if len(x) >= 2]
            if parts and all(x in fp for x in parts):
                return True
    return False


def so_trich(trich, doan_van, nguong=0.9, lua_chon=()):
    """Câu trích (một hoặc nhiều đoạn nối bằng …) có nằm trong đoạn văn không.
    → (khop | khop_doc | khop_dien | lech_nhe | lech_nang | khong_tim_thay | khong_co, chi_tiet). Lấy mức xấu nhất của các đoạn.
    khop_doc: chỉ khác chữ Hán ↔ kana; khop_dien: câu đoạn văn đã điền lựa chọn vào chỗ trống; trích quá ngắn (< 3 chữ) → khong_co."""
    fp = phang(doan_van)
    doan = [phang(x) for x in CHIA_TRICH_RE.split(strip_marks(trich or ""))]
    doan = [x for x in doan if len(x) >= 3]
    if not doan or not fp:
        return "khong_co", ""
    xau, ct, dien = 0, [], False
    for fc in doan:
        if fc in fp:
            continue
        if _co_trong(fc, fp, lua_chon):
            xau, dien = max(xau, 1), True
            continue
        sm = difflib.SequenceMatcher(None, fp, fc, autojunk=False)
        m = sm.find_longest_match(0, len(fp), 0, len(fc))
        if m.size < min(4, len(fc)):
            xau = max(xau, 4)
            ct.append(f"không thấy '{fc[:25]}'")
            continue
        a0 = max(0, m.a - m.b - 8)
        win = fp[a0:min(len(fp), m.a - m.b + len(fc) + 8)]
        sm2 = difflib.SequenceMatcher(None, win, fc, autojunk=False)
        bl = [b for b in sm2.get_matching_blocks() if b.size]
        if bl:
            win = win[max(0, bl[0].a - bl[0].b): bl[-1].a + bl[-1].size + (len(fc) - bl[-1].b - bl[-1].size)]
        if _TOK["t"] and _yomi(win) and _yomi(win) == _yomi(fc):
            xau = max(xau, 1)
            continue
        r = difflib.SequenceMatcher(None, win, fc, autojunk=False).ratio()
        d = [(win[i1:i2], fc[j1:j2]) for op, i1, i2, j1, j2 in
             difflib.SequenceMatcher(None, win, fc, autojunk=False).get_opcodes() if op != "equal"]
        ct.append(f"giống {r:.0%}: " + "; ".join(f"'{x}'→'{y}'" for x, y in d[:3]))
        xau = max(xau, 2 if r >= nguong else 3)
    kq = MUC_TD[xau]
    if kq == "khop_doc" and dien:
        kq = "khop_dien"
    return kq, " | ".join(ct)


# ---------------- tách lời giải ----------------
NHAN_NHAT_TRICH = r"｜引用《いんよう》(?:\s*đoạn\s*｜文《ぶん》)?"
NHAN_NHAT_GT = r"(?:｜解説《かいせつ》|｜解《かい》\s*｜説《せつ》|｜解《かい》\s*｜釈《しゃく》)"
NHAN_NHAT_NGHIA = r"｜意味《いみ》"
NHAN_NHAT_RE_ALL = re.compile(rf"(?m)^(\s*(?:[-•]\s*)?)(?:{NHAN_NHAT_TRICH}|{NHAN_NHAT_GT}|{NHAN_NHAT_NGHIA})\s*[:：]\s*")
DANH_GIA_NHAT_RE = re.compile(r"(?:→|->|=>)\s*(｜正《ただ》しい|｜誤《あやま》り|正しい|誤り)\s*\.?\s*$")


def bo_nhan_nhat(text):
    """Bỏ nhãn tiếng Nhật thay nhãn Việt ('｜引用《いんよう》:', '｜解説《かいせつ》:', '｜意味《いみ》:') và chữ đánh giá tiếng Nhật
    ('→ ｜正《ただ》しい.') – dùng làm chuẩn so 'mất tiếng Nhật' / furigana (JSON không chép các nhãn này)."""
    text = NHAN_NHAT_RE_ALL.sub(lambda m: m.group(1), text or "")
    return re.sub(r"(?m)" + DANH_GIA_NHAT_RE.pattern, "→ ĐÚNG.", text)


SO_LC_RE = re.compile(r"^\s*(?:[-•]\s*)?([1-4１-４])\s*[\.．、)）]\s*(.*)$")
GACH_RE = re.compile(r"^\s*[-•]\s+(.*)$")
DANH_GIA_RE = re.compile(r"^\s*(?:[-•]\s*)?(?:→|->|=>)\s*\.?\s*(ĐÚNG|SAI|Đúng|Sai|｜正《ただ》しい|｜誤《あやま》り)\s*\.?\s*$")
DANH_GIA_CUOI_RE = re.compile(r"\s*(?:→|->|=>)\s*\.?\s*(ĐÚNG|SAI)\s*\.?\s*$")
NHAN_NGHIA_RE = re.compile(r"(?i)^\s*(?:[-•]\s*)?(?:nghĩa|｜意味《いみ》)\s*[:：]\s*(.*)$")
NHAN_CAU_HOI_RE = re.compile(r"(?i)^\s*\{?\s*câu hỏi\s*\}?\s*[:：]\s*")
NHAN_TRICH = (r"(?:trích dẫn(?: đoạn văn| câu văn| câu thoại| từ đoạn văn)?|câu trích dẫn|câu trong đoạn văn|câu gốc"
              r"|(?:trong )?đoạn văn,? (?:có câu|có nói|có viết|viết|nói(?: rõ)?)|câu liên quan(?: trong đoạn văn)?(?: là)?|câu then chốt"
              r"|｜引用《いんよう》(?:\s*đoạn\s*｜文《ぶん》)?)")
NHAN_TRICH_RE = re.compile(rf"(?i)^\s*(?:[-•]\s*)?{NHAN_TRICH}\s*[:：]\s*(.*)$")
NHAN_GIAI_THICH_RE = re.compile(r"(?i)^\s*(?:[-•]\s*)?(?:giải thích|phân tích|｜解説《かいせつ》|｜解《かい》\s*｜説《せつ》|｜解《かい》\s*｜釈《しゃく》)\s*[:：]\s*(.*)$")
TRICH_RE = re.compile(r"「([^「」]*(?:「[^「」]*」[^「」]*)*)」")
NGHIA_NGOAC_RE = re.compile(r"^\s*[（(]\s*(?:(?:nghĩa|dịch|câu dịch)\s*[:：]\s*)?(.*?)\s*[)）]\s*\.?\s*$", re.I | re.S)
DAP_AN_CUOI_RE = re.compile(r"(?i)^\s*(?:[-•]\s*)?(?:câu trả lời đúng là|đáp án đúng là)\s*[:：]?\s*(.*)$")
NHAN_DOAN_VAN_RE = re.compile(r"(?i)^\s*\{?\s*đoạn văn\s*\}?\s*[:：]\s*\}?\s*$")


def _lc_khop(text, lua_chon):
    """Số lựa chọn của đề khớp với dòng lựa chọn trong lời giải (0 = không khớp)."""
    for i, lc in enumerate(lua_chon, 1):
        if lc and giong(text, lc):
            return i
    return 0


def _vi_dong(s):
    return bool(s.strip()) and not co_tieng_nhat(LOCK_RE.sub("", s))


def _dong_sau(lines, k):
    return next((x for x in lines[k + 1:] if x.strip()), "")


def tim_khoi(lines, lua_chon):
    """Vị trí các dòng bắt đầu khối lựa chọn 'i. <lựa chọn>' (số tăng dần 1→4; dòng có tiếng Nhật, hoặc khớp lựa chọn của đề,
    hoặc dòng ngắn ngay sau là 'Nghĩa:' – vd lựa chọn 'B—D—A—C')."""
    starts, can = [], 1
    for k, ln in enumerate(lines):
        m = SO_LC_RE.match(ln)
        if not m:
            continue
        so = int(norm_ja(m.group(1)))
        txt = m.group(2).strip()
        if so != can:
            continue
        if co_tieng_nhat(txt) or _lc_khop(txt, lua_chon) == so or (len(txt) <= 60 and NHAN_NGHIA_RE.match(_dong_sau(lines, k))):
            starts.append((k, so, txt))
            can += 1
    return starts


def tach_khoi(block_lines):
    """Một khối lựa chọn (bỏ dòng đầu) → {nghia, trich:[{ja, nghia}], giai_thich:[dòng], danh_gia, nhan_lap, dong_trich_long}."""
    it = {"nghia": None, "trich": [], "giai_thich": [], "danh_gia": None, "danh_gia_lap": False, "nghia_lap": False,
          "co_nhan_trich": False}
    i, n = 0, len(block_lines)
    cho_trich = False
    while i < n:
        ln = block_lines[i]
        if not ln.strip():
            i += 1
            continue
        m = DANH_GIA_RE.match(ln)
        if m:
            v = m.group(1).upper() == "ĐÚNG" or "正" in m.group(1)
            if it["danh_gia"] is not None:
                it["danh_gia_lap"] = True
            it["danh_gia"] = v
            i += 1
            continue
        m = DANH_GIA_CUOI_RE.search(ln)
        if m and ln[:m.start()].strip():
            it["danh_gia"] = m.group(1) == "ĐÚNG"
            ln = ln[:m.start()]
        m = NHAN_NGHIA_RE.match(ln)
        if m and it["nghia"] is None and not it["trich"] and not it["giai_thich"]:
            it["nghia"] = m.group(1).strip()
            i += 1
            continue
        m = NHAN_TRICH_RE.match(ln)
        if m:
            it["co_nhan_trich"] = True
            rest = m.group(1).strip()
            if not rest:
                cho_trich = True
                i += 1
                continue
            ln = rest
        else:
            m = None
        tr = TRICH_RE.search(ln)
        dau_dong = bool(tr) and bool(re.match(r"^\s*(?:[-•]\s*)?「", ln))
        sau0 = ln[tr.end():].strip() if tr else ""
        if dau_dong and not (m or cho_trich) and sau0 and not NGHIA_NGOAC_RE.match(sau0):
            tr = None          # '「しかし」 (Tuy nhiên) là từ dùng để …' – câu giải thích bắt đầu bằng từ trong 「」, không phải trích dẫn
        if tr and (m or cho_trich or dau_dong) and co_tieng_nhat(tr.group(1)):
            truoc, sau = ln[:tr.start()].strip(), ln[tr.end():].strip()
            q = {"ja": tr.group(1), "nghia": None}
            if sau:
                mm = NGHIA_NGOAC_RE.match(sau)
                q["nghia"] = mm.group(1).strip() if mm else sau
            elif i + 1 < n:
                nx = block_lines[i + 1]
                mm = NGHIA_NGOAC_RE.match(nx) or NHAN_NGHIA_RE.match(nx)
                if mm and not TRICH_RE.search(nx):
                    q["nghia"] = mm.group(1).strip()
                    i += 1
            if truoc and truoc not in ("-", "•"):
                it["giai_thich"].append(truoc)
            it["trich"].append(q)
            cho_trich = False
            i += 1
            continue
        cho_trich = False
        m = NHAN_GIAI_THICH_RE.match(ln)
        it["giai_thich"].append(m.group(1).strip() if m else ln.strip())
        i += 1
    it["giai_thich"] = [x for x in it["giai_thich"] if x]
    return it


def _lay_dau(lines):
    """Phần trước khối 1: câu hỏi (dòng đầu, bỏ nhãn 'Câu hỏi:'), nghĩa (dòng sau), còn lại = khac."""
    ls = [x for x in lines if x.strip()]
    hd = {"cau": None, "nghia": None, "khac": []}
    if ls and NHAN_CAU_HOI_RE.match(ls[0]) and not NHAN_CAU_HOI_RE.sub("", ls[0]).strip():
        ls = ls[1:]
    if ls:
        hd["cau"] = NHAN_CAU_HOI_RE.sub("", ls[0]).strip()
    if len(ls) > 1:
        m = NHAN_NGHIA_RE.match(ls[1])
        hd["nghia"] = "\n".join([(m.group(1) if m else ls[1]).strip()] + [x.strip() for x in ls[2:]])   # mọi dòng còn lại của phần đầu
    hd["khac"] = ls[2:]
    return hd


def tach_chuan(text, lua_chon):
    lines = text.split("\n")
    st = tim_khoi(lines, lua_chon)
    hd = _lay_dau(lines[:st[0][0]])
    items = []
    for j, (k, so, txt) in enumerate(st):
        end = st[j + 1][0] if j + 1 < len(st) else len(lines)
        it = tach_khoi(lines[k + 1:end])
        it.update(so=so, lua_chon=txt, khop=_lc_khop(txt, lua_chon), vi_text="\n".join(lines[k + 1:end]))
        items.append(it)
    return {"dau": hd, "lua_chon": items}


def tach_ban_dich(text):
    """Khuôn chỉ có bản dịch: [Đoạn văn: …] câu hỏi, 4 dòng lựa chọn, [Câu trả lời đúng là: …]."""
    ls = [x.strip() for x in text.split("\n")]
    ls = [x for x in ls if x and x not in ('"', '""', "“", "”")]
    k_dap = next((k for k, x in enumerate(ls) if DAP_AN_CUOI_RE.match(x)), None)
    body = ls[:k_dap] if k_dap is not None else ls
    tail = ls[k_dap:] if k_dap is not None else []
    dap_text = None
    if tail:
        m = DAP_AN_CUOI_RE.match(tail[0])
        rest = [m.group(1)] + tail[1:] if m.group(1).strip() else tail[1:]
        dap_text = " ".join(re.sub(r"^\s*[-•]\s*", "", x) for x in rest).strip() or None
    # 4 dòng lựa chọn cuối của phần thân
    is_opt = lambda x: bool(SO_LC_RE.match(x) or GACH_RE.match(x))  # noqa: E731
    k = len(body)
    while k > 0 and is_opt(body[k - 1]):
        k -= 1
    opts = body[k:]
    if len(opts) > 4:
        k += len(opts) - 4
        opts = body[k:]
    lc = []
    for x in opts:
        m = SO_LC_RE.match(x)
        lc.append((m.group(2) if m else GACH_RE.match(x).group(1)).strip())
    truoc = body[:k]
    while truoc and NHAN_CAU_HOI_RE.match(truoc[-1]) and not NHAN_CAU_HOI_RE.sub("", truoc[-1]).strip():
        truoc = truoc[:-1]
    cau = NHAN_CAU_HOI_RE.sub("", truoc[-1]).strip() if truoc else None
    dv = truoc[:-1]
    while dv and NHAN_CAU_HOI_RE.match(dv[-1]) and not NHAN_CAU_HOI_RE.sub("", dv[-1]).strip():
        dv = dv[:-1]
    if dv and NHAN_DOAN_VAN_RE.match(dv[0]):
        dv = dv[1:]
    return {"cau_vi": cau, "lua_chon_vi": lc, "dap_an_vi": dap_text, "ban_dich_doan_van": "\n".join(dv) or None}


def nhan_khuon(text, lua_chon):
    lines = (text or "").split("\n")
    st = tim_khoi(lines, lua_chon)
    if len(st) >= 2:
        return "chuan"
    ls = [x for x in lines if x.strip()]
    if not ls:
        return "trong"
    so_dong_lc = sum(1 for x in ls if SO_LC_RE.match(x) or GACH_RE.match(x))
    if (NHAN_DOAN_VAN_RE.match(ls[0]) or not co_tieng_nhat(ls[0])) and so_dong_lc >= 3 \
            and not any(DANH_GIA_RE.match(x) for x in ls):
        return "chi_ban_dich"
    return "tu_do"


# ---------------- gắn cờ ----------------
VI_DAU_RE = re.compile(r"[ăâđêôơưàáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ]", re.I)
NHAN_NHAT_RE = re.compile(r"^\s*(?:[-•]\s*)?(?:｜[^｜《》]+《[^》]+》\s*){1,3}[^\n:：]{0,8}[:：]")   # '｜引用《いんよう》:', '｜解説《かいせつ》:'


def dich_nguoc(text):
    """'nhan' = nhãn tiếng Nhật thay nhãn Việt ('｜引用《いんよう》:', '｜解説《かいせつ》:' – dịch máy ngược: 13483, 17029, 17033…);
    'tron' = dòng tiếng Việt có ≥ 2 từ tiếng Nhật có furigana nằm trần (không trong 「」 / nháy) – có khi là cách viết bình thường,
    có khi là lỗi dịch máy ('không ｜言及《げんきゅう》 đến'); None = không có."""
    kq = None
    for ln in (text or "").split("\n"):
        if NHAN_NHAT_RE.match(ln) or re.search(r"→\s*｜", ln):
            return "nhan"
        bare = re.sub(r'「[^」]*」|『[^』]*』|"[^"]*"|“[^”]*”', "", ln)
        if VI_DAU_RE.search(bare) and len(re.findall(r"｜[^｜《》]+《[^》]+》", bare)) >= 2:
            kq = "tron"
    return kq


FLAG_TEXT = {
    "khuon_chuan": "Khuôn chuẩn: câu hỏi + 4 khối lựa chọn (Nghĩa / Trích dẫn / Giải thích / → ĐÚNG|SAI)",
    "chi_ban_dich": "Lời giải CHỈ có bản dịch (đoạn văn + câu hỏi + lựa chọn), không có phân tích – Python bỏ bản dịch đoạn văn khỏi đầu vào; Claude KIỂM TRA gắn cờ thieu_noi_dung",
    "tu_do": "Lời giải viết tự do (không có khối lựa chọn) – toàn bộ vào options[đáp án].analysis; Claude KIỂM TRA gắn cờ thieu_noi_dung",
    "can_hinh": "Câu hỏi chọn HÌNH (lựa chọn là số 1–4 trỏ tới hình không có trong dữ liệu) – gắn cờ can_hinh, chuyển CTV tiếng Nhật",
    "khong_du_4_khoi": "Lời giải không có đủ 4 khối lựa chọn đánh số 1–4",
    "lua_chon_khac_de": "Dòng lựa chọn trong lời giải viết khác lựa chọn của đề",
    "cau_hoi_khac_de": "Dòng câu hỏi trong lời giải khác câu hỏi của đề",
    "cau_hoi_khong_tieng_nhat": "Dòng đầu lời giải không phải câu hỏi tiếng Nhật",
    "khong_nghia_cau_hoi": "Không có dòng nghĩa của câu hỏi",
    "thieu_nghia_lua_chon": "Có lựa chọn không có dòng 'Nghĩa:'",
    "thieu_danh_gia": "Có khối lựa chọn không có '→ ĐÚNG / → SAI' (is_match theo đáp án của đề)",
    "danh_gia_lap": "Một khối có 2 dòng đánh giá",
    "danh_gia_lech_dap_an": "Chữ đánh giá của lời giải lệch đáp án của đề (đáp án bị chấm SAI hoặc lựa chọn khác được chấm ĐÚNG) – nghi lỗi nội dung (dap_an)",
    "khong_danh_gia_dung": "Không khối nào được chấm ĐÚNG",
    "co_dau_khac": "Phần đầu có hơn 2 dòng (câu hỏi lặp / tách dòng) – dòng 1 vào question.ja, MỌI dòng còn lại vào question.meaning (giữ \\n, bọc ⟪ ⟫)",
    "trich_khong_nhan": "Có trích dẫn 「…」 không có nhãn 'Trích dẫn' (đứng đầu dòng / mục '- ')",
    "nhieu_trich_dan": "Có lựa chọn với nhiều câu trích dẫn",
    "trich_lech_doan_van_nhe": "Có câu trích lệch nhẹ đoạn văn gốc (lỗi gõ / furigana / ký hiệu – xem K-TD)",
    "trich_lech_doan_van_nang": "Có câu trích KHÁC đoạn văn gốc (mất / khác chữ) – Claude xem, nghi lỗi nội dung → cờ trich_dan",
    "trich_khong_tim_thay": "Có câu trích KHÔNG tìm thấy trong đoạn văn gốc – Claude đối chiếu tay, nghi lỗi nội dung → cờ trich_dan",
    "cau_hoi_trich_khong_thay": "Phần câu hỏi trích 「…」 không tìm thấy trong đoạn văn gốc",
    "dap_an_cuoi_lech": "'Câu trả lời đúng là: …' (khuôn chỉ bản dịch) khác lựa chọn đúng theo đề",
    "ky_tu_rac": "Lời giải có chuỗi khoảng trắng / ký tự rác dài – Python thu gọn (sửa định dạng)",
    "dong_nhay_le": "Lời giải có dòng chỉ gồm dấu nháy '\"' (lỗi xuất CSV) – Python bỏ",
    "nhan_tieng_nhat": "Lời giải có nhãn / chữ đánh giá bằng tiếng Nhật ('｜引用《いんよう》:', '｜解説《かいせつ》:', '→ ｜正《ただ》しい') và câu Việt lẫn tiếng Nhật – nghi dịch máy ngược, Claude KIỂM TRA gắn cờ khac",
    "tieng_nhat_tran": "Dòng tiếng Việt có từ tiếng Nhật (furigana) nằm trần – tác tử TẠO bọc ⟪ ⟫; Claude KIỂM TRA xem câu có đọc hiểu được không (vô nghĩa → cờ khac)",
    "furigana_hong": "Furigana viết kiểu lạ '<|漢字;よみ|' / dấu '<|' lẻ – Python đổi sang ｜《》 / bỏ dấu (sửa định dạng)",
    "dap_an_de_loi": "Dữ liệu đề lỗi: dap_an_so không phải 1–4",
    "co_furigana": "Có furigana",
    "ruby_hong": "Có ruby hỏng trong bản gốc",
    "danh_dau_rac": "Bản gốc có đoạn in đậm / gạch chân rỗng hoặc chỉ là dấu câu (đã bỏ thẻ)",
    "ky_hieu_trung": "Bản gốc có sẵn ký hiệu ｜《》 (trùng ký hiệu furigana)",
}
CTV_FLAGS = ("danh_gia_lech_dap_an", "khong_danh_gia_dung", "trich_lech_doan_van_nang", "trich_khong_tim_thay",
             "chi_ban_dich", "tu_do", "can_hinh", "dap_an_cuoi_lech", "nhan_tieng_nhat")


def parse_and_flag(text, lua_chon, dap_an_so, cau_hoi, doan_van, nguong=0.9):
    """→ (khuon, phan, co, ghi_chu_ban_goc). phan dùng cho kiểm tra K… và gợi ý."""
    co, gc = [], []
    dap = int(dap_an_so) if str(dap_an_so).strip() in ("1", "2", "3", "4") else None
    if dap is None:
        co.append("dap_an_de_loi")
        gc.append(f"[Bản gốc VI] Dữ liệu đề lỗi: dap_an_so = '{dap_an_so}' (không phải 1–4)")
    if all(re.fullmatch(r"\s*[1-4１-４]\s*", x or "") for x in lua_chon):
        co.append("can_hinh")
        gc.append("[Bản gốc VI] Câu hỏi chọn hình: lựa chọn chỉ là số 1–4, hình không có trong dữ liệu")
    khuon = nhan_khuon(text, lua_chon)
    phan = {"khuon": khuon, "dau": None, "lua_chon": [], "ban_dich": None, "trich_doan_van": []}
    if khuon == "trong":
        return khuon, phan, co, gc
    if khuon == "chuan":
        co.append("khuon_chuan")
        p = tach_chuan(text, lua_chon)
        phan.update(p)
        hd = p["dau"]
        if hd["cau"] and not co_tieng_nhat(hd["cau"]):
            co.append("cau_hoi_khong_tieng_nhat")
        elif hd["cau"] and not giong(hd["cau"], cau_hoi):
            co.append("cau_hoi_khac_de")
            gc.append(f"[Bản gốc VI] Câu hỏi trong lời giải khác câu hỏi của đề: '{strip_marks(hd['cau'])[:60]}' ↔ đề '{cau_hoi[:60]}'")
        if not hd["nghia"]:
            co.append("khong_nghia_cau_hoi")
        if hd["khac"]:
            co.append("co_dau_khac")
        items = p["lua_chon"]
        if [it["so"] for it in items] != [1, 2, 3, 4]:
            co.append("khong_du_4_khoi")
            gc.append(f"[Bản gốc VI] Lời giải chỉ có các khối lựa chọn {[it['so'] for it in items]}")
        n_dung = 0
        for it in items:
            if it["khop"] != it["so"]:
                co.append("lua_chon_khac_de")
                gc.append(f"[Bản gốc VI] Lựa chọn {it['so']} trong lời giải viết khác đề: '{strip_marks(it['lua_chon'])[:50]}' ↔ đề '{lua_chon[it['so'] - 1][:50]}'")
            if it["nghia"] is None:
                co.append("thieu_nghia_lua_chon")
            if it["danh_gia"] is None:
                co.append("thieu_danh_gia")
            if it["danh_gia_lap"]:
                co.append("danh_gia_lap")
            if len(it["trich"]) > 1:
                co.append("nhieu_trich_dan")
            if it["trich"] and not it["co_nhan_trich"]:
                co.append("trich_khong_nhan")
            n_dung += it["danh_gia"] is True
            if dap and ((it["so"] == dap and it["danh_gia"] is False) or (it["so"] != dap and it["danh_gia"] is True)):
                co.append("danh_gia_lech_dap_an")
                gc.append(f"[Bản gốc VI] Lựa chọn {it['so']} được chấm {'ĐÚNG' if it['danh_gia'] else 'SAI'} nhưng đáp án của đề là {dap}")
            for q in it["trich"]:
                kq, ct = so_trich(q["ja"], doan_van, nguong, lua_chon)
                phan["trich_doan_van"].append({"so": it["so"], "ja": q["ja"], "ket_qua": kq, "chi_tiet": ct})
            dn = dich_nguoc(it["vi_text"])
            if dn == "nhan":
                co.append("nhan_tieng_nhat")
            elif dn == "tron":
                co.append("tieng_nhat_tran")
        if items and n_dung == 0 and all(it["danh_gia"] is not None for it in items):
            co.append("khong_danh_gia_dung")
        for x in phan["trich_doan_van"]:
            if x["ket_qua"] in ("lech_nhe", "lech_nang", "khong_tim_thay"):
                ten = {"lech_nhe": "trich_lech_doan_van_nhe", "lech_nang": "trich_lech_doan_van_nang",
                       "khong_tim_thay": "trich_khong_tim_thay"}[x["ket_qua"]]
                co.append(ten)
                gc.append(f"[Bản gốc VI] Lựa chọn {x['so']}: câu trích {'lệch nhẹ' if x['ket_qua'] == 'lech_nhe' else 'khác' if x['ket_qua'] == 'lech_nang' else 'không tìm thấy trong'} đoạn văn gốc"
                          + (f" ({x['chi_tiet'][:120]})" if x["chi_tiet"] else ""))
    elif khuon == "chi_ban_dich":
        co.append("chi_ban_dich")
        p = tach_ban_dich(text)
        phan["ban_dich"] = p
        gc.append("[Bản gốc VI] Lời giải chỉ có bản dịch (đoạn văn / câu hỏi / lựa chọn), không phân tích từng lựa chọn")
        if p["dap_an_vi"] and dap and len(p["lua_chon_vi"]) == 4 and \
                re.sub(r"\W", "", p["dap_an_vi"].lower()) != re.sub(r"\W", "", p["lua_chon_vi"][dap - 1].lower()):
            co.append("dap_an_cuoi_lech")
            gc.append(f"[Bản gốc VI] 'Câu trả lời đúng là: {p['dap_an_vi'][:60]}' khác lựa chọn {dap} của đề ('{p['lua_chon_vi'][dap - 1][:60]}')")
    else:
        co.append("tu_do")
        gc.append("[Bản gốc VI] Lời giải viết tự do về đáp án, không phân tích từng lựa chọn")
    # phần câu hỏi trích 「…」 có trong đoạn văn không
    for m in TRICH_RE.finditer(cau_hoi or ""):
        if len(phang(m.group(1))) >= 3 and so_trich(m.group(1), doan_van, nguong)[0] in ("lech_nang", "khong_tim_thay"):
            co.append("cau_hoi_trich_khong_thay")
            gc.append(f"[Bản gốc VI] Câu hỏi trích '「{m.group(1)[:40]}」' không tìm thấy trong đoạn văn gốc (lỗi đề?)")
    return khuon, phan, sorted(set(co)), gc


# ---------------- nhãn bỏ khi đo độ phủ tiếng Việt ----------------
LABELS = [r"(?im)^\s*[-•]?\s*(?:→|->|=>)\s*\.?\s*(?:ĐÚNG|SAI|Đúng|Sai)\s*\.?\s*$",
          r"(?i)(?:→|->|=>)\s*\.?\s*(?:ĐÚNG|SAI)\s*\.?\s*$",
          r"(?im)^\s*[-•]?\s*(?:nghĩa|giải thích|phân tích|dịch|câu dịch)\s*[:：]",
          r"(?i)[（(]\s*(?:nghĩa|dịch|câu dịch)\s*[:：]",
          rf"(?im)^\s*[-•]?\s*{NHAN_TRICH}\s*[:：]",
          r"(?im)^\s*\{?\s*câu hỏi\s*\}?\s*[:：]",
          r"(?im)^\s*[-•]?\s*｜引用《いんよう》\s*đoạn\s*｜文《ぶん》\s*[:：]",
          r"(?im)^\s*[-•]?\s*(?:câu trả lời đúng là|đáp án đúng là)\s*[:：]?.*$",   # khuôn chỉ bản dịch: dòng đáp án lặp lại lựa chọn
          r"(?m)^\s*[-•]?\s*[Tt]rích\s*dẫn\s*$",                      # nhãn hỏng không có ':' đứng riêng dòng ('Tríchdẫn' – 16440_2, lô 21)
          r"(?m)^\s*[-•]?\s*Giải thích(?=\s+[A-ZĐÀ-Ỹ\"「])",           # nhãn hỏng 'Giải thích Đáp án …' không có ':' (16440_2, lô 21)
          r"(?im)^\s*[-•]?\s*(?:trích|giải)\s*[:：]"]                  # nhãn rút gọn 'trích:' / 'giải:' (16443_1, lô 22)


def strip_labels(text):
    for pat in LABELS:
        text = re.sub(pat, " ", text)
    return text


# ---------------- kiểm tra riêng GĐ1 ----------------
def _v(o):
    return (o or {}).get("vi") if o else None


def _cover(src_text, out_text):
    s = collections.Counter(vi_words(strip_labels(src_text or "")))
    o = collections.Counter(vi_words(out_text or ""))
    if not s:
        return 1.0, []
    return sum((s & o).values()) / sum(s.values()), [w for w, _ in (s - o).most_common(8)]


def opt_text(o):
    out = [_v(o.get("meaning")), _v(o.get("analysis"))] + [_v(q.get("meaning")) for q in o.get("quotes") or []]
    return "\n".join(x for x in out if x)


def check_k(doc, norm, nguong=0.9):
    """K1–K9 + K-TD cho JSON tiếng Việt dạng đọc hiểu. Trả (loi, canh_bao)."""
    loi, cb = [], []
    de, phan = norm["de"], norm.get("phan") or {}
    khuon = phan.get("khuon") or norm.get("khuon_goc")
    dap = de["dap_an_so"] if de["dap_an_so"] in (1, 2, 3, 4) else None
    q, c, opts = doc.get("question") or {}, doc.get("correct") or {}, doc.get("options") or []
    # K0 – trường luôn null của dạng
    for k in ("full_translation", "summary", "key_info"):
        if doc.get(k) is not None:
            loi.append(f"K0: {k} phải là null (dạng này không dùng)")
    if c.get("full_sentence") is not None:
        loi.append("K0: correct.full_sentence phải là null")
    # K1 – 4 lựa chọn
    if [o.get("index") for o in opts] != [1, 2, 3, 4]:
        loi.append(f"K1: options phải đủ 4 lựa chọn theo thứ tự 1–4 (đang có {[o.get('index') for o in opts]})")
    # K3 – câu hỏi
    hd = phan.get("dau") or {}
    if khuon == "chuan" and hd.get("cau") and co_tieng_nhat(hd["cau"]):
        if phang(q.get("ja")) != phang(hd["cau"]):
            loi.append(f"K3: question.ja khác dòng câu hỏi của lời giải '{strip_marks(hd['cau'])[:60]}'")
    elif not giong(q.get("ja"), de["cau_hoi"]):
        loi.append(f"K3: lời giải không có dòng câu hỏi tiếng Nhật – question.ja phải chép câu hỏi của đề '{de['cau_hoi'][:60]}'")
    nghia_q = hd.get("nghia") if khuon == "chuan" else ((phan.get("ban_dich") or {}).get("cau_vi") if khuon == "chi_ban_dich" else None)
    if khuon == "chuan" and hd.get("cau") and not co_tieng_nhat(hd["cau"]):
        nghia_q = hd["cau"]          # dòng đầu là câu tiếng Việt → nghĩa câu hỏi
    if (nghia_q is None) != (q.get("meaning") is None):
        (loi if khuon in ("chuan", "chi_ban_dich") else cb).append(
            "K4: question.meaning phải null khi và chỉ khi lời giải không có dòng nghĩa câu hỏi" + (f" ('{nghia_q[:50]}')" if nghia_q else ""))
    elif nghia_q:
        cv, miss = _cover(nghia_q, _v(q.get("meaning")))
        if cv < 0.97:
            loi.append(f"K9: question.meaning thiếu chữ so với bản gốc: {miss}")
    # K2 / K5 / K6 / K9 – từng lựa chọn
    src = {it["so"]: it for it in phan.get("lua_chon") or []}
    bd = phan.get("ban_dich") or {}
    for o in opts:
        i = o.get("index")
        if not isinstance(i, int) or not 1 <= i <= 4:
            continue
        it = src.get(i)
        if o.get("reading") is not None:
            loi.append(f"K0: lựa chọn {i}: reading phải là null (furigana giữ trong option_ja)")
        if it is not None:
            if phang(o.get("option_ja")) != phang(it["lua_chon"]):
                loi.append(f"K2: lựa chọn {i}: option_ja khác dòng lựa chọn của lời giải '{strip_marks(it['lua_chon'])[:50]}'")
        elif not giong(o.get("option_ja"), de["lua_chon"][i - 1]):
            loi.append(f"K2: lựa chọn {i}: lời giải không có khối này – option_ja phải chép lựa chọn của đề '{de['lua_chon'][i - 1][:50]}'")
        # is_match
        if it is not None and it["danh_gia"] is not None:
            if o.get("is_match") is not it["danh_gia"]:
                loi.append(f"K6: lựa chọn {i}: is_match phải là {it['danh_gia']} (lời giải: → {'ĐÚNG' if it['danh_gia'] else 'SAI'})")
        elif dap and o.get("is_match") is not (i == dap):
            loi.append(f"K6: lựa chọn {i}: lời giải không chấm ĐÚNG/SAI – is_match phải là {i == dap} (theo đáp án của đề)")
        # nghĩa lựa chọn
        nghia = it["nghia"] if it is not None else (bd.get("lua_chon_vi") or [None] * 4)[i - 1] if len(bd.get("lua_chon_vi") or []) == 4 else None
        if khuon in ("chuan", "chi_ban_dich"):
            if (nghia is None) != (o.get("meaning") is None):
                loi.append(f"K5: lựa chọn {i}: meaning phải null khi và chỉ khi lời giải không có nghĩa của lựa chọn" + (f" ('{nghia[:40]}')" if nghia else ""))
        # độ phủ chữ của khối
        if it is not None:
            cv, miss = _cover(it["vi_text"], opt_text(o))
            if cv < 0.97:
                loi.append(f"K9: lựa chọn {i}: thiếu chữ so với khối của lời giải ({cv:.0%}): {miss}")
            if it["trich"] and not o.get("quotes"):
                cb.append(f"K7: lựa chọn {i}: lời giải có {len(it['trich'])} câu trích 「…」 nhưng quotes = [] – xem lại (trích đứng riêng → quotes)")
        if khuon == "chi_ban_dich" and (o.get("quotes") or o.get("analysis") is not None):
            loi.append(f"K7: lựa chọn {i}: khuôn chỉ có bản dịch – quotes = [] và analysis = null")
        for j, qq in enumerate(o.get("quotes") or []):
            if not co_tieng_nhat(qq.get("ja")):
                loi.append(f"K7: lựa chọn {i}: quotes[{j}].ja không có tiếng Nhật")
                continue
            if re.match(r"^\s*「.*」\s*$", qq.get("ja") or "", re.S) and qq["ja"].count("「") == 1:
                cb.append(f"K7: lựa chọn {i}: quotes[{j}].ja còn 「」 ngoài cùng – bỏ 「」")
            kq, ct = so_trich(qq["ja"], norm.get("doan_van") or "", nguong, de["lua_chon"])
            if kq == "lech_nhe":
                cb.append(f"K-TD: lựa chọn {i}: quotes[{j}] lệch nhẹ đoạn văn ({ct[:120]}) – lỗi gõ → sửa định dạng; khác chữ có nghĩa → cờ trich_dan")
            elif kq in ("lech_nang", "khong_tim_thay"):
                cb.append(f"K-TD: lựa chọn {i}: quotes[{j}] {'khác' if kq == 'lech_nang' else 'không tìm thấy trong'} đoạn văn ({ct[:120]}) – đối chiếu, nghi lỗi → cờ trich_dan")
    # K8 – đáp án
    if dap:
        if c.get("index") != dap:
            loi.append(f"K8: correct.index = {c.get('index')} khác dap_an_so = {dap}")
        elif 1 <= dap <= len(opts) and c.get("option_ja") != opts[dap - 1].get("option_ja"):
            loi.append(f"K8: correct.option_ja phải giống hệt options[{dap - 1}].option_ja")
        dung = [o.get("index") for o in opts if o.get("is_match") is True]
        if dung != [dap]:
            cb.append(f"K8: is_match = true ở lựa chọn {dung} nhưng đáp án của đề là {dap} – lời giải chấm lệch đáp án → nghi lỗi nội dung (cờ dap_an)")
    # analysis khuôn tự do
    if khuon == "tu_do" and dap and 1 <= dap <= len(opts) and opts[dap - 1].get("analysis") is None:
        loi.append(f"K7: khuôn tự do – toàn bộ lời giải vào options[{dap - 1}].analysis")
    return loi, cb


# ---------------- hiển thị cho Excel CTV ----------------
def render(d, lang, show=lambda s: s, bold=lambda s: s):
    def t(obj):
        return show((obj or {}).get(lang) or "") if obj else ""
    q, c = d.get("question") or {}, d.get("correct") or {}
    out = [f"{bold('【Câu hỏi】')} {show(q.get('ja') or '')}"]
    if q.get("meaning"):
        out.append(f"   Nghĩa: {t(q['meaning'])}")
    out.append(bold("【PHÂN TÍCH】"))
    for o in d.get("options") or []:
        out.append(bold(f"{o.get('index')}. ") + show(o.get("option_ja") or ""))
        if o.get("meaning"):
            out.append("   Nghĩa: " + t(o["meaning"]).replace("\n", "\n   "))
        for qq in o.get("quotes") or []:
            out.append("   Trích dẫn: 「" + show(qq.get("ja") or "") + "」")
            if qq.get("meaning"):
                out.append("      (" + t(qq["meaning"]).replace("\n", "\n      ") + ")")
        if o.get("analysis"):
            out.append("   Giải thích: " + t(o["analysis"]).replace("\n", "\n   "))
        out.append("   → " + ("ĐÚNG." if o.get("is_match") else "SAI."))
    out.append(bold("【ĐÁP ÁN】") + f" {c.get('index')}. {show(c.get('option_ja') or '')}")
    return "\n".join(out)
