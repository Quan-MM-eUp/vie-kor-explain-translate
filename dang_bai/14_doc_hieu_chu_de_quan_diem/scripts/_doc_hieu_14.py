"""Phần ĐỌC HIỂU của dạng 14 (schema reading_listening.v1) – dựng 2026-10-08.

(Đặt trong thư mục dạng vì pipeline_chung/doc_hieu.py đang do phiên dạng 15 phát triển song song – gộp sau ở phiên điều phối.)
Gồm:
  1. Làm sạch HTML: đoạn văn (bóc khung <table> / thẻ Word mso), nhãn in đậm của lời giải khuôn lạ.
  2. Tách lời giải khuôn chuẩn (2 kiểu nhãn):
       Kiểu A: câu hỏi + dịch → "i. <lựa chọn>" / "Nghĩa:" / "Trích dẫn:" 「…」 (dịch) / "Giải thích:" / "→ ĐÚNG|SAI"
       Kiểu B: như A nhưng trích dẫn + nhận xét viết thành gạch đầu dòng "- Đoạn văn có câu: 「…」 (dịch)", "- <nhận xét>"
     → dict phan (cờ, kiểm tra Python, gợi ý); ban_nhap() dựng JSON nháp theo đúng quy tắc của prompt (chỉ để tự kiểm thử).
  3. So trích dẫn với đoạn văn (so mờ), phân loại câu hỏi, cụm được hỏi 「…」 trong câu hỏi.
  4. Nhãn cố định (bỏ khi đo độ phủ / so tiếng Nhật).
  5. Hiển thị (render) cho Excel CTV.
Quy tắc nhãn / trích dẫn ở đây phải KHỚP với prompts/s1_chuyen_json.md (mục "Trích dẫn").
"""
import difflib
import re

from pipeline_chung.common import JA_RE, VI_DIACRITIC_RE, strip_marks
from pipeline_chung.normalize import normalize_html

# ---------------------------------------------------------------- 1. làm sạch HTML
_KHUNG_RE = re.compile(r"</?(?:table|tbody|thead|tr|td|th|colgroup|col)\b[^>]*>", re.I)
_WORD_RE = re.compile(r"<o:p>.*?</o:p>|<!--.*?-->", re.I | re.S)
_DAM_NHAN_RE = re.compile(r"<(strong|b)\b[^>]*>\s*([^<>{}]{1,40}?[:：])\s*</\1>", re.I)


def bo_khung(html):
    """Bỏ khung bảng (dạng 14: <table> chỉ là khung viền quanh cả đoạn văn) và thẻ rác của Word – không đổi chữ."""
    s = _WORD_RE.sub("", html or "")
    s = re.sub(r"</td>\s*<td\b[^>]*>", "\n", s, flags=re.I)        # nhiều ô trên một hàng → xuống dòng
    return _KHUNG_RE.sub("", s)


def bo_dam_nhan(html):
    """<strong>Đoạn văn:</strong> → 'Đoạn văn:' (nhãn in đậm của lời giải khuôn lạ, không phải chỗ in đậm nội dung)."""
    return _DAM_NHAN_RE.sub(lambda m: m.group(2), html or "")


def lam_sach_doan_van(html):
    """Đoạn văn → văn bản chuẩn hóa (ruby → ｜…《…》, gạch chân / in đậm → { }, giữ ①②, 注…). Trả về (văn bản, ruby hỏng)."""
    return normalize_html(bo_khung(html))


# ---------------------------------------------------------------- 2. nhãn
# Nhãn dẫn trích dẫn "thuần" (chỉ báo 'đoạn văn có câu này') – KHÔNG chép vào JSON khi đứng ngay trước 「…」.
NHAN_TRICH = [
    "Trích dẫn", "Câu trích dẫn", "Câu trích dẫn liên quan", "Trích dẫn từ đoạn văn", "Trích dẫn đoạn văn",
    "Trích dẫn đoạn liên quan", "Đoạn văn có câu", "Trong đoạn văn có câu", "Trong đoạn văn, có câu", "Đoạn văn viết",
    "Đoạn văn có viết", "Đoạn văn có nói", "Đoạn văn có nói rõ", "Đoạn văn nói", "Đoạn văn nói rõ", "Câu trong đoạn văn",
    "Trong bài văn có đoạn", "Trong đoạn văn, có đoạn", "Đoạn văn có nhắc đến", "Đoạn văn có đề cập", "Câu",
    "｜引用《いんよう》", "引用", "Trích ｜引用《いんよう》", "Trích 引用", "Trích ｜引《いん》", "Trích 引",
]
# Nhãn mở đầu phần nhận xét – bỏ nhãn, giữ chữ phía sau
NHAN_PHAN_TICH = ["Giải thích", "Giải釈", "Phân tích", "Phân tích đoạn hội thoại", "Nhận xét"]

_ALT = lambda xs: "|".join(re.escape(x) for x in sorted(xs, key=len, reverse=True))  # noqa: E731
NHAN_TRICH_RE = re.compile(rf"^\s*(?:-\s*)?(?:{_ALT(NHAN_TRICH)})\s*[:：]\s*", re.I)
NHAN_PT_RE = re.compile(rf"^\s*(?:-\s*)?(?:{_ALT(NHAN_PHAN_TICH)})\s*[:：]\s*", re.I)
NHAN_NGHIA_RE = re.compile(r"^\s*(?:-\s*)?Nghĩa\s*[:：]\s*(.*)$", re.I | re.S)
KET_LUAN_RE = re.compile(r"^\s*→\s*(ĐÚNG|SAI)\b[\s.。!]*(.*)$", re.S)
LUA_CHON_RE = re.compile(r"^\s*([1-4１-４])\s*[.．]\s*(\S.*)$")

# nhãn cố định của lời giải gốc – bỏ khi đo độ phủ tiếng Việt (strip_labels)
_NHAN_DONG = NHAN_TRICH + NHAN_PHAN_TICH + ["Nghĩa", "Dịch", "Câu trả lời đúng là", "Đáp án đúng là", "Đoạn văn", "Câu hỏi",
                                             "Chú thích", "Gợi ý", "ヒント"]
_NHAN_DONG_RE = re.compile(rf"(?im)^\s*(?:-\s*)?(?:{_ALT(_NHAN_DONG)})\s*[:：]\s*")


def strip_labels(text):
    """Bỏ nhãn cố định khi đo độ phủ tiếng Việt: nhãn đầu dòng, '(Dịch:', '→ ĐÚNG/SAI', gạch đầu dòng."""
    t = "\n".join("" if (LUA_CHON_RE.match(x) and co_tieng_nhat(x) and not co_tieng_viet(x)) else x
                  for x in (text or "").split("\n"))          # dòng lựa chọn tiếng Nhật ('1. A:ありがとう B:…') không phải chữ Việt
    t = _NHAN_DONG_RE.sub("", t)
    t = re.sub(r"[(（]\s*(?:Dịch|Nghĩa)\s*[:：]", "(", t, flags=re.I)
    t = re.sub(r"(?m)→\s*(?:ĐÚNG|SAI)\b\.?", "", t)
    t = re.sub(r"(?m)^\s*[-•]\s+", "", t)
    return t


def bo_nhan_tieng_nhat(text):
    """Bản lời giải dùng để so tiếng Nhật / furigana với JSON: bỏ các nhãn dẫn viết bằng tiếng Nhật (｜引用《いんよう》: …)
    và nhãn hỏng 'Giải釈:' – các nhãn này không được chép vào JSON."""
    out = []
    for line in (text or "").split("\n"):
        m = NHAN_TRICH_RE.match(line) or NHAN_PT_RE.match(line)
        if m and JA_RE.search(strip_marks(m.group(0))):
            line = line[m.end():]
        out.append(line)
    return "\n".join(out)


# ---------------------------------------------------------------- 3. tách lời giải khuôn chuẩn
def _ja(s):
    return re.sub(r"[\s　]", "", strip_marks(s or ""))


def _giong(a, b):
    a, b = _ja(a), _ja(b)
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def co_tieng_viet(s):
    return bool(VI_DIACRITIC_RE.search(strip_marks(s or "")))


def co_tieng_nhat(s):
    return bool(JA_RE.search(strip_marks(s or "")))


def tim_lua_chon(lines, lua_chon):
    """Vị trí dòng tiêu đề lựa chọn 1–4 (theo thứ tự). Dòng 'k. …' chỉ nhận khi đứng đầu khối (đầu văn bản / sau dòng trống /
    sau dòng → ĐÚNG|SAI) và có tiếng Nhật hoặc giống lựa chọn k của đề."""
    pos, k = [], 1
    for i, line in enumerate(lines):
        if k > 4:
            break
        m = LUA_CHON_RE.match(line)
        if not m or int(m.group(1).translate(str.maketrans("１２３４", "1234"))) != k:
            continue
        prev = next((x for x in reversed(lines[:i]) if x.strip()), "")
        dau_khoi = i == 0 or not lines[i - 1].strip() or KET_LUAN_RE.match(prev) or k == 1
        if dau_khoi and (co_tieng_nhat(m.group(2)) or _giong(m.group(2), lua_chon[k - 1] if lua_chon else "") > 0.6):
            pos.append(i)
            k += 1
    return pos


def _tach_ngoac_dich(s):
    """'(…)' ở đầu chuỗi → (bản dịch không nhãn, phần còn lại). Không có → (None, s)."""
    s = s.lstrip()
    if not s or s[0] not in "(（":
        return None, s
    depth = 0
    for j, ch in enumerate(s):
        if ch in "(（":
            depth += 1
        elif ch in ")）":
            depth -= 1
            if depth == 0:
                inner = s[1:j].strip()
                inner = re.sub(r"^(?:Dịch|Nghĩa)\s*[:：]\s*", "", inner, flags=re.I)
                return inner, s[j + 1:]
    return None, s


def _tach_ngoac_kep(s):
    """'「…」' ở đầu chuỗi (cân bằng 「」 lồng nhau) → (nội dung không có 「」 ngoài cùng, phần còn lại)."""
    s = s.lstrip()
    if not s.startswith("「"):
        return None, s
    depth = 0
    for j, ch in enumerate(s):
        if ch == "「":
            depth += 1
        elif ch == "」":
            depth -= 1
            if depth == 0:
                return s[1:j], s[j + 1:]
    return None, s


def _dich_dong_ke(lines, i):
    """Bản dịch '(…)' ở dòng kế (bỏ dòng trống). Trả về (bản dịch, vị trí dòng tiếp theo) hoặc (None, i)."""
    j = i
    while j < len(lines) and not lines[j].strip():
        j += 1
    if j < len(lines):
        vi, r = _tach_ngoac_dich(lines[j].strip())
        if vi is not None and not r.strip(" .。"):
            return vi, j + 1
    return None, i


def tach_khoi(lines):
    """Tách các dòng của MỘT lựa chọn (sau dòng tiêu đề) theo quy tắc trích dẫn của prompt:
      - 「…」 là TRÍCH DẪN (→ quotes) khi phía trước trên cùng dòng là rỗng / '- ' / nhãn dẫn thuần (NHAN_TRICH), hoặc dòng trước
        chỉ có nhãn dẫn thuần; bản dịch = '(…)' ngay sau (cùng dòng hoặc dòng kế), bỏ nhãn 'Dịch:' / 'Nghĩa:' trong ngoặc;
        chữ tiếng Việt còn lại phía sau trên cùng dòng → nhận xét. Nhãn thuần + câu Nhật không có 「」 ở dòng kế, hoặc nhãn thuần +
        "…" (toàn tiếng Nhật) cũng là trích dẫn.
      - 「…」 nằm giữa câu tiếng Việt (phía trước có chữ không phải nhãn thuần) → giữ nguyên trong nhận xét (inline).
      - 'Nghĩa:' đầu tiên → meaning; 'Giải thích:' / 'Phân tích:' … → bỏ nhãn; '- ' đầu dòng → bỏ; '→ ĐÚNG/SAI' → ket_luan.
    Trả về dict {nghia, trich: [{ja, vi}], phan_tich: [dòng], ket_luan, sau_ket_luan}."""
    out = {"nghia": None, "trich": [], "phan_tich": [], "ket_luan": None, "sau_ket_luan": []}
    i, cho_trich = 0, False
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line:
            continue
        if out["ket_luan"] is not None:
            out["sau_ket_luan"].append(line)
            continue
        m = KET_LUAN_RE.match(line)
        if m:
            out["ket_luan"] = m.group(1) == "ĐÚNG"
            if m.group(2).strip():
                out["phan_tich"].append(m.group(2).strip())
            continue
        m = NHAN_NGHIA_RE.match(line)
        if m and out["nghia"] is None and not out["trich"] and not out["phan_tich"]:
            out["nghia"] = m.group(1).strip() or None
            continue
        m = NHAN_TRICH_RE.match(line)
        if m and not line[m.end():].strip():              # nhãn dẫn thuần đứng một mình
            nxt = next((x.strip() for x in lines[i:] if x.strip()), "")
            if nxt.startswith(("「", '"', "“")):
                cho_trich = True
            elif co_tieng_nhat(nxt) and not co_tieng_viet(nxt):        # câu trích không có 「」 ở dòng kế (25_4)
                while i < len(lines) and not lines[i].strip():
                    i += 1
                ja = lines[i].strip()
                vi, i = _dich_dong_ke(lines, i + 1)
                out["trich"].append({"ja": ja, "vi": vi})
            continue          # nhãn thuần không kèm trích dẫn (vd 'Trích dẫn:' rồi câu tiếng Việt) – bỏ nhãn
        rest = line[m.end():] if m else re.sub(r"^-\s*", "", line)
        if (m or cho_trich) and rest[:1] in ('"', "“"):            # trích dẫn trong nháy kép (nội dung toàn tiếng Nhật)
            mq = re.match(r'^["“]([^"”]+)["”]', rest)
            if mq and co_tieng_nhat(mq.group(1)) and not co_tieng_viet(mq.group(1)):
                rest = "「" + mq.group(1) + "」" + rest[mq.end():]
        if rest.startswith("「") and (m or cho_trich or line.startswith("「") or re.match(r"^-\s*「", line)):
            while rest.startswith("「"):
                ja, rest2 = _tach_ngoac_kep(rest)
                if ja is None:
                    break
                vi, rest3 = _tach_ngoac_dich(rest2)
                if vi is None and not rest2.strip():                    # bản dịch ở dòng kế
                    vi, i = _dich_dong_ke(lines, i)
                    rest3 = ""
                out["trich"].append({"ja": ja.strip(), "vi": vi})
                rest = (rest3 if vi is not None else rest2).lstrip()
                rest = re.sub(r"^[.。]\s*", "", rest)
            if rest.strip():
                out["phan_tich"].append(rest.strip())
            cho_trich = False
            continue
        cho_trich = False
        m2 = NHAN_PT_RE.match(line)
        text = line[m2.end():] if m2 else re.sub(r"^-\s*", "", line)
        if text.strip():
            out["phan_tich"].append(text.strip())
    return out


def phan_loai_khuon(text):
    if "Câu trả lời đúng" in text or "Đáp án đúng là" in text:
        return "la_chi_dap_an"
    if re.search(r"(?m)^\s*Đoạn văn\s*[:：]", text):
        return "la_dich_doan"
    return "la_ngan"


def bo_dong_lap(text, nguong=0.8):
    """Bỏ dòng dán lặp liền nhau (cờ dong_lap, vd 16865_3): dòng giống hệt dòng trước (> 15 ký tự) hoặc bản lặp bị cụt / lỗi gõ
    (≥ 12 ký tự, ≥ 80% chữ nằm trong dòng trước, không dài hơn). Trả về (văn bản, [dòng đã bỏ])."""
    out, bo, truoc = [], [], None
    for x in (text or "").split("\n"):
        c = x.strip()
        if c and truoc and not LUA_CHON_RE.match(c):
            a, b = strip_marks(c), strip_marks(truoc)
            lap = c == truoc and len(c) > 15
            if not lap and len(a) >= 12 and len(a) <= len(b) + 2:
                sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
                lap = sum(m.size for m in sm.get_matching_blocks() if m.size >= 3) / len(a) >= nguong
            if lap:
                bo.append(c)
                continue
        out.append(x)
        if c:
            truoc = c
    return "\n".join(out), bo


def tach_loi_giai(text, lua_chon):
    """Tách lời giải đã chuẩn hóa. Trả về dict phan:
    {khuon: chuan_A|chuan_B|la_dich_doan|la_chi_dap_an|la_ngan, dau: {ja, vi}, lua_chon: [ {so, dong, than, nghia, trich, phan_tich,
     ket_luan, sau_ket_luan} ], sau: [...]}"""
    lines = (text or "").split("\n")
    pos = tim_lua_chon(lines, lua_chon)
    phan = {"khuon": None, "dau": None, "lua_chon": [], "sau": []}
    head = lines[:pos[0]] if pos else lines
    ja_l, vi_l = [], []
    for x in head:
        if not x.strip():
            continue
        (vi_l if co_tieng_viet(x) or vi_l else ja_l).append(x.strip())
    phan["dau"] = {"ja": "\n".join(ja_l) or None, "vi": "\n".join(vi_l) or None}
    if len(pos) == 4:
        blocks = []
        for k, p in enumerate(pos):
            end = pos[k + 1] if k < 3 else len(lines)
            block = lines[p + 1:end]
            kq = tach_khoi(block)
            kq.update(so=k + 1, dong=LUA_CHON_RE.match(lines[p]).group(2).strip(), than="\n".join(block).strip())
            blocks.append(kq)
        if sum(x["ket_luan"] is not None for x in blocks) == 4:
            phan["lua_chon"] = blocks
            kieu_b = sum(bool(re.match(r"^\s*-\s", x)) for b in blocks for x in b["than"].split("\n"))
            phan["khuon"] = "chuan_B" if kieu_b >= 4 else "chuan_A"
            phan["sau"], blocks[3]["sau_ket_luan"] = blocks[3]["sau_ket_luan"], []
            return phan
    phan["khuon"] = phan_loai_khuon(text)
    return phan


# ---------------------------------------------------------------- 4. so với đoạn văn, loại câu hỏi
_BO_SO_RE = re.compile(r"[\s　、。，,．.「」『』（）()…・!！?？：:\-－―─\"'“”‘’{}①-⑳⑴-⒇]|注\s*[0-9０-９]+|[0-9０-９]")


def _k(s):
    return _BO_SO_RE.sub("", strip_marks(s or ""))


def so_trich_dan(cau, doan_van):
    """So câu trích với đoạn văn (bỏ furigana, dấu câu, ①②, 注n, số). Trả về ('khop'|'mot_phan'|'khong', tỷ lệ)."""
    a, b = _k(cau), _k(doan_van)
    if not a or a in b:
        return "khop", 1.0
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    r = sum(x.size for x in sm.get_matching_blocks() if x.size >= 4) / len(a)
    return ("mot_phan" if r >= 0.6 else "khong"), round(r, 2)


LOAI_CAU_HOI = {
    "dien_cho": "Điền vào chỗ trống ①…",
    "chi_dinh": "Hỏi cụm gạch chân / chỉ định 「…」とあるが / とは / 指す",
    "quan_diem": "Quan điểm / suy nghĩ / chủ trương của tác giả",
    "chu_de": "Chủ đề / tóm tắt / ý chính của cả bài",
    "ly_do": "Lý do (なぜ / 理由)",
    "noi_dung": "Nội dung phù hợp với bài",
    "khac": "Khác (hỏi chi tiết)",
}


def loai_cau_hoi(q):
    q = strip_marks(q or "")
    if re.search(r"入る|入れる", q):
        return "dien_cho"
    if re.search(r"とあるが|とは(どう|何|だれ|誰|どんな|どの)|指して|指す|どういうこと|どんな(こと|意味)|どのような(こと|意味)", q):
        return "chi_dinh"
    if re.search(r"筆者|著者|作者", q) and re.search(r"考え|言いたい|主張|意見|観点|思って|気持ち|述べ|言って|立場|態度", q):
        return "quan_diem"
    if re.search(r"まとめ|テーマ|主旨|要旨|タイトル|題名|言いたいこと", q):
        return "chu_de"
    if re.search(r"理由|なぜ|どうして", q):
        return "ly_do"
    if re.search(r"合う|合って|正しい|内容", q):
        return "noi_dung"
    return "khac"


def cum_hoi(q):
    """Các cụm 「…」 trong câu hỏi (cụm được hỏi / gạch chân), đã bỏ furigana."""
    return [strip_marks(x).strip() for x in re.findall(r"「([^「」]{2,})」", q or "") if strip_marks(x).strip()]


def moc_hoi(q):
    """Mốc ①②… trong câu hỏi."""
    return re.findall(r"[①-⑳]", q or "")


# ---------------------------------------------------------------- 5. JSON nháp (tự kiểm thử – theo đúng quy tắc của prompt)
_JA_CH = "぀-ヿ㐀-䶿一-鿿ｦ-ﾟ々〆ヶー〜～"
_JA_RUN_RE = re.compile(rf"(?:｜[^｜《》\n]+《[^《》\n]+》|[{_JA_CH}])(?:｜[^｜《》\n]+《[^《》\n]+》|[{_JA_CH}、。・！？0-9０-９％%]|[ 　](?=｜|[{_JA_CH}]))*")


def boc(s):
    """Bọc ⟪ ⟫ quanh mọi cụm tiếng Nhật trong câu tiếng Việt (dấu 「」 "" để ngoài)."""
    if s is None:
        return None
    return _JA_RUN_RE.sub(lambda m: "⟪" + m.group(0) + "⟫", s)


def _T(s):
    return {"vi": boc(s)} if s and s.strip() else None


def ban_nhap(norm, schema_id="reading_listening.v1"):
    """JSON nháp từ phan (khuôn chuẩn) – chỉ dùng tự kiểm thử pipeline, KHÔNG thay tác tử TẠO."""
    ph, de = norm["phan"], norm["de"]
    dap = de["dap_an_so"]
    opts = []
    for k, b in enumerate(ph["lua_chon"]):
        pt = "\n".join(b["phan_tich"] + b.get("sau_ket_luan", []) + (ph["sau"] if k == 3 else [])) or None
        opts.append({"index": k + 1, "option_ja": b["dong"], "reading": None, "meaning": _T(b["nghia"]),
                     "is_match": bool(b["ket_luan"]),
                     "quotes": [{"ja": q["ja"], "meaning": _T(q["vi"])} for q in b["trich"]],
                     "analysis": _T(pt)})
    return {"schema": schema_id, "question_id": norm["question_id"], "cau_con": norm["cau_con"],
            "full_translation": None, "summary": None,
            "question": {"ja": ph["dau"]["ja"], "meaning": _T(ph["dau"]["vi"])},
            "options": opts, "key_info": None,
            "correct": {"index": dap, "option_ja": opts[dap - 1]["option_ja"] if isinstance(dap, int) and 1 <= dap <= 4 else "",
                        "full_sentence": None}}


# ---------------------------------------------------------------- 6. hiển thị (Excel CTV)
def render(d, lang, show, bold, tk_render=None):
    """Dựng lời giải theo khuôn thống nhất: Câu hỏi + Nghĩa → (Bản dịch đoạn văn) → từng lựa chọn: Nghĩa / Trích dẫn / Giải thích /
    → ĐÚNG|SAI → Đáp án."""
    t = lambda o: show((o or {}).get(lang) or "") if o else ""  # noqa: E731
    q, c = d.get("question") or {}, d.get("correct") or {}
    out = [f"{bold('【Câu hỏi】')} {show(q.get('ja') or '')}"]
    if q.get("meaning"):
        out.append(f"   Nghĩa: {t(q['meaning'])}")
    for blk in d.get("full_translation") or []:
        out.append(bold("【Bản dịch đoạn văn】") + (f" {blk.get('label')}" if blk.get("label") else ""))
        for ln in blk.get("lines") or []:
            s = ((ln.get("speaker") + ": ") if ln.get("speaker") else "") + (show(ln.get("ja") or "") + " " if ln.get("ja") else "")
            out.append("   " + s + t(ln.get("meaning")))
    for o in d.get("options") or []:
        out.append("")
        out.append(bold(f"{o.get('index')}. ") + show(o.get("option_ja", "")))
        if o.get("meaning"):
            out.append("   Nghĩa: " + t(o["meaning"]))
        for qt in o.get("quotes") or []:
            out.append("   Trích dẫn: 「" + show(qt.get("ja", "")) + "」")
            if qt.get("meaning"):
                out.append("      (" + t(qt["meaning"]) + ")")
        if o.get("analysis"):
            out.append("   Giải thích: " + t(o["analysis"]).replace("\n", "\n   "))
        out.append("   → " + ("ĐÚNG." if o.get("is_match") else "SAI."))
    for ln in d.get("key_info") or []:
        out.append(bold("【Thông tin】") + " " + show(ln.get("ja") or "") + " " + t(ln.get("meaning")))
    out.append("")
    out.append(bold("【Đáp án】") + f" {c.get('index')}. {show(c.get('option_ja', ''))}")
    if tk_render:
        out += tk_render(d, lang, show, bold)
    return "\n".join(out)
