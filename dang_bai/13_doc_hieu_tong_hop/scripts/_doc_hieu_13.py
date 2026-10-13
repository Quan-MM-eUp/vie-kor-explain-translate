"""Dạng 13 – Đọc hiểu tổng hợp: tách đoạn văn A/B, tách lời giải, gắn cờ, kiểm tra JSON, hiển thị (2026-10-08).

Viết riêng trong thư mục dạng 13 (KHÔNG đặt vào pipeline_chung/doc_hieu.py – file đó do phiên dạng 14 đang dựng song song);
khi các phiên đọc hiểu xong có thể gộp vào pipeline_chung. Không sửa nội dung lời giải: chỉ tách / so / hiển thị.

Lời giải khuôn chuẩn:
    <câu hỏi tiếng Nhật>            → question.ja
    <dịch câu hỏi>                  → question.meaning
    1. <lựa chọn tiếng Nhật>        → options[0].option_ja
    Nghĩa: <dịch lựa chọn>          → options[0].meaning
    <nhận xét: 'Đoạn A có câu:' 「…」 (dịch) …>  → options[0].analysis + options[0].quotes[]
    → ĐÚNG. / → SAI.                → options[0].is_match
"""
import difflib
import re
import unicodedata

from pipeline_chung.common import JA_RE, norm_ja, strip_marks

VI_RE = re.compile(r"[ăâđêôơưàáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ]", re.I)
JA_CHAR_RE = re.compile(r"[぀-ヿ㐀-鿿々〆]")
OPT_RE = re.compile(r"^\s*\{?\s*([1-4１-４])\s*\}?\s*[\.．]\s*(.*)$")
NGHIA_RE = re.compile(r"^\s*[-+•]?\s*Nghĩa\s*[:：]\s*(.*)$")
VERDICT_RE = re.compile(r"^\s*(?:→|->|=>)\s*(ĐÚNG|SAI|Đúng|Sai)\s*\.?\s*$")
QUOTE_RE = re.compile(r"「(?:[^「」]|「[^「」]*」)*」")


# ---------------- tiện ích ----------------
def co_nhat(s):
    return bool(JA_CHAR_RE.search(strip_marks(s or "")))


def co_viet(s):
    return bool(VI_RE.search(s or ""))


def _f(s):
    """Chuẩn hóa để so câu tiếng Nhật: bỏ furigana / { } / ⟪⟫, NFKC, bỏ chú thích 注, dấu câu và khoảng trắng."""
    s = unicodedata.normalize("NFKC", strip_marks(s or "").replace("{", "").replace("}", ""))
    s = re.sub(r"[(（]\s*注\s*[0-9]*\s*[)）]|※\s*[0-9]*", "", s)
    return re.sub(r"[\s。\.、,!?「」『』｢｣・'\"“”‘’…:;\-―ー~〜()\[\]【】①-⑳]", "", s)


def eq(a, b):
    return bool(_f(a)) and _f(a) == _f(b)


def nhan_chuan(x):
    x = unicodedata.normalize("NFKC", x or "").strip().upper()
    return x or None


# ---------------- đoạn văn ----------------
NHAN_DOAN_RE = re.compile(r"^\s*[【\[［]?\s*(?:回答者\s*[:：]?\s*)?([A-CＡ-Ｃ])\s*[】\]］]?\s*(?:[（(][^）)]{0,20}[）)])?\s*[:：]?\s*$")
NHAN_HOI_RE = re.compile(r"^\s*(相談者)\s*[:：]?\s*$")


def tach_doan_van(text):
    """Tách đoạn văn (đã chuẩn hóa) theo dòng nhãn riêng: 'A' / 'B' / 'C' / '回答者：Ａ' / '回答者：A（弁護士）' / '相談者：'.
    → [(nhãn, văn bản)]; phần trước nhãn đầu tiên có nhãn None. Ít hơn 2 nhãn A/B/C → [(None, toàn bộ)]."""
    segs, cur, buf, so_nhan = [], None, [], 0
    for ln in (text or "").split("\n"):
        m, h = NHAN_DOAN_RE.match(ln), NHAN_HOI_RE.match(ln)
        if m or h:
            if "\n".join(buf).strip():
                segs.append((cur, "\n".join(buf).strip()))
            cur, buf = (nhan_chuan(m.group(1)) if m else h.group(1)), []
            so_nhan += bool(m)
            continue
        buf.append(ln)
    if "\n".join(buf).strip():
        segs.append((cur, "\n".join(buf).strip()))
    if so_nhan < 2:
        return [(None, (text or "").strip())]
    return segs


def dinh_dang_doan_van(segs):
    if len(segs) == 1 and segs[0][0] is None:
        return segs[0][1]
    return "\n\n".join((f"【{lab}】\n" if lab else "") + t for lab, t in segs)


def _phu(q, ft):
    """Tỷ lệ ký tự của q khớp với đoạn ft quanh chỗ khớp dài nhất (cho phép lệch vài chữ / câu trích gộp)."""
    sm = difflib.SequenceMatcher(None, ft, q, autojunk=False)
    m = sm.find_longest_match(0, len(ft), 0, len(q))
    if m.size == 0:
        return 0.0
    a0, a1 = max(0, m.a - m.b - 20), min(len(ft), m.a + (len(q) - m.b) + 20)
    sm2 = difflib.SequenceMatcher(None, ft[a0:a1], q, autojunk=False)
    return sum(b.size for b in sm2.get_matching_blocks()) / len(q)


def vi_tri_trich_dan(ja, segs):
    """→ (nhãn, 'khop' | 'mot_phan' | 'khong_thay' | 'ngan'). Câu trích có '…' thì xét từng mảnh.
    Một phần: ≥ 85% ký tự khớp đoạn văn quanh chỗ khớp dài nhất."""
    q = _f(ja)
    if len(q) < 4:
        return None, "ngan"
    for lab, t in segs:
        if q in _f(t):
            return lab, "khop"
    manh = [_f(x) for x in re.split(r"…|\.\.\.|・・・", strip_marks(ja or "")) if len(_f(x)) >= 4]
    if len(manh) > 1:
        for lab, t in segs:
            if all(x in _f(t) for x in manh):
                return lab, "khop"
    best, lab_best = 0.0, None
    for lab, t in segs:
        r = _phu(q, _f(t))
        if r > best:
            best, lab_best = r, lab
    if best >= 0.85:
        return lab_best, "mot_phan"
    return None, "khong_thay"


def tim_trong_doan(ja, segs, nhan):
    seg = [(l, t) for l, t in segs if l == nhan]
    return bool(seg) and vi_tri_trich_dan(ja, seg)[1] in ("khop", "mot_phan")


# ---------------- nhãn đoạn lời giải nêu trước câu trích ----------------
NEU_NHAN_RE = re.compile(
    r"(?:đoạn|Đoạn|phần|Phần|bài|Bài|văn bản|Văn bản|trả lời của|Trả lời của|ý kiến của)\s*(?:văn\s*)?([ABCＡＢＣ])(?![A-Za-zÀ-ỹ0-9])"
    r"|(?:^|[\s\-•(])([ABCＡＢＣ])\s*(?:có câu|viết|nói|cho rằng|đề cập|nhắc)")


def _nhan_neu(window):
    ms = list(NEU_NHAN_RE.finditer(window or ""))
    return nhan_chuan(ms[-1].group(1) or ms[-1].group(2)) if ms else None


def _dich_sau(body, pos):
    """Bản dịch ngay sau câu trích: '(…)' / '（…）' (cho phép xuống dòng). → (nội dung, vị trí kết thúc) | (None, pos)."""
    m = re.match(r"[ \t]*\n?[ \t]*([(（])", body[pos:])
    if not m:
        return None, pos
    i, depth = pos + m.end() - 1, 0
    for j in range(i, len(body)):
        if body[j] in "(（":
            depth += 1
        elif body[j] in ")）":
            depth -= 1
            if depth == 0:
                return body[i + 1:j].strip(), j + 1
    return None, pos


def tach_trich_dan(body, segs=None):
    """Các câu trích 「…」 tiếng Nhật trong nhận xét của một lựa chọn.
    khoi = True: đứng thành khối (đầu dòng / sau nhãn '…:') → quotes[]; False: nằm giữa câu tiếng Việt → giữ trong analysis (bọc ⟪ ⟫)."""
    out, last_end, prev = [], 0, None
    for m in QUOTE_RE.finditer(body or ""):
        inner = m.group(0)[1:-1]
        if not co_nhat(inner) or len(_f(inner)) < 4:
            continue
        ls = body.rfind("\n", 0, m.start()) + 1
        truoc = re.sub(r"^\s*[-+•]\s*", "", body[ls:m.start()])
        khoi = truoc.strip() == "" or bool(re.search(r"[:：]\s*$", truoc))
        nghia, end = _dich_sau(body, m.end())
        window = body[last_end:m.start()]
        claim = _nhan_neu(window)
        if claim is None and prev and len(re.sub(r"[^A-Za-zÀ-ỹ]", "", re.sub(r"[(（][^)）]*[)）]", "", window))) < 15:
            claim = prev
        lab, muc = vi_tri_trich_dan(inner, segs) if segs else (None, "khong_so")
        out.append({"ja": inner, "nghia": nghia, "khoi": khoi, "nhan_neu": claim, "nhan_thay": lab, "muc": muc})
        prev, last_end = claim, (end if nghia is not None else m.end())
    return out


# ---------------- tách lời giải ----------------
def _phan_dau(lines):
    """Phần trước lựa chọn 1: câu hỏi tiếng Nhật (các dòng đầu có tiếng Nhật, không có chữ Việt, không mở bằng nháy kép) + dịch câu hỏi."""
    ne = [x for x in lines if x.strip()]
    cau, i = [], 0
    while i < len(ne) and co_nhat(ne[i]) and not co_viet(ne[i]) and (i == 0 or not re.search(r'["“]', ne[i])):
        cau.append(ne[i].strip())
        i += 1
    # dòng tiếng Nhật lặp lại câu hỏi (chỉ thêm nháy "…" / khoảng trắng – 12643_1) → bỏ khỏi nghia, ghi vào "lap"
    goc = {_f(x) for x in cau}
    lap = [x.strip() for x in ne[i:] if co_nhat(x) and not co_viet(x) and _f(x) in goc]
    con = [x.strip() for x in ne[i:] if x.strip() not in lap]
    return {"cau": "\n".join(cau) or None, "nghia": "\n".join(con) or None, "lap": lap}


def bo_dong_lap(text, ph):
    """Bỏ các dòng câu hỏi lặp (ph['dau']['lap']) khỏi text – dùng cho src_text_furi (so furigana)."""
    for x in ((ph or {}).get("dau") or {}).get("lap") or []:
        text = text.replace(x + "\n", "", 1) if x + "\n" in text else text.replace(x, "", 1)
    return text


def phan_tich_loi_giai(text, segs=None):
    lines = (text or "").split("\n")
    starts, exp = [], 1
    for i, ln in enumerate(lines):
        m = OPT_RE.match(ln)
        if m and int(unicodedata.normalize("NFKC", m.group(1))) == exp and co_nhat(m.group(2)):
            starts.append(i)
            exp += 1
            if exp > 4:
                break
    dau = _phan_dau(lines[:starts[0]] if starts else [])
    opts = []
    for k, s in enumerate(starts):
        blk = lines[s:(starts[k + 1] if k + 1 < len(starts) else len(lines))]
        nghia, kl, body, n_nghia = None, [], [], 0
        for ln in blk[1:]:
            mn, mv = NGHIA_RE.match(ln), VERDICT_RE.match(ln)
            if mn and nghia is None:
                nghia, n_nghia = mn.group(1).strip(), 1
            elif mv:
                kl.append(mv.group(1).upper() == "ĐÚNG")
            else:
                n_nghia += bool(mn)
                body.append(ln)
        b = "\n".join(body).strip()
        opts.append({"so": k + 1, "lua_chon": OPT_RE.match(blk[0]).group(2).strip(), "nghia": nghia,
                     "ket_luan": kl[-1] if kl else None, "so_ket_luan": len(kl), "nhan_xet": b,
                     "trich_dan": tach_trich_dan(b, segs), "nghia_lap": n_nghia > 1})
    t = (text or "").strip()
    if len(opts) == 4:
        khuon = "chuan"
    elif re.match(r"^\{?\s*(?:Đoạn văn|A\s*[:：])", t):
        khuon = "dich_doan_van"
    elif "Câu trả lời đúng" in t:
        khuon = "chi_dap_an"
    elif "ヒント" in t:
        khuon = "goi_y"
    else:
        khuon = "khac"
    return {"khuon": khuon, "dau": dau, "lua_chon": opts}


# ---------------- gắn cờ (GĐ0) ----------------
FLAG_TEXT = {
    "khuon_la": "Lời giải KHÔNG theo khuôn chuẩn (câu hỏi → 4 lựa chọn 'Nghĩa' / nhận xét / → ĐÚNG/SAI)",
    "dich_doan_van": "Lời giải là BẢN DỊCH đoạn văn A/B (+ dịch câu hỏi / lựa chọn), không phân tích từng lựa chọn",
    "chi_dap_an": "Lời giải chỉ dịch câu hỏi / lựa chọn + 'Câu trả lời đúng là…', không phân tích",
    "goi_y": "Lời giải chỉ có 'ヒント' (câu trích gợi ý), không phân tích",
    "khuon_khac": "Lời giải khuôn lạ khác (vd chỉ một đoạn tóm tắt / dịch), không phân tích từng lựa chọn",
    "thieu_ket_luan": "Có lựa chọn không có dòng '→ ĐÚNG/SAI' (is_match theo đáp án của đề)",
    "nhieu_dung": "Lời giải kết luận ĐÚNG cho ≠ 1 lựa chọn (nghi đáp án)",
    "lech_dap_an": "Lựa chọn được lời giải kết luận ĐÚNG khác dap_an_so của đề",
    "cau_hoi_lech": "Câu hỏi tiếng Nhật trong lời giải khác câu hỏi của đề",
    "lua_chon_lech": "Dòng lựa chọn trong lời giải viết khác lựa chọn của đề",
    "thieu_nghia_lua_chon": "Có lựa chọn không có dòng 'Nghĩa:'",
    "nghia_lap": "Có lựa chọn có 2 dòng 'Nghĩa:' (dòng sau thuộc nhận xét)",
    "trich_dan_ngoai_doan": "Có câu trích 「…」 không tìm thấy trong đoạn văn (so mờ)",
    "trich_dan_sai_nguon": "Có câu trích lời giải nói ở đoạn A nhưng thực ra nằm ở đoạn B (hoặc ngược lại)",
    "trich_dan_giua_cau": "Có câu trích nằm giữa câu tiếng Việt (giữ trong analysis, bọc ⟪ ⟫)",
    "chen_tu_nhat": "Câu tiếng Việt có chen từ tiếng Nhật ngoài 「」 – bọc ⟪ ⟫, giữ nguyên",
    "doan_khong_ab": "Đoạn văn KHÔNG có nhãn A/B (một bài đọc – nghi phân loại nhầm dạng; vẫn chạy ở dạng 13)",
    "doan_co_bang": "Đoạn văn có bảng (<table>)",
    "de_gach_chan": "Câu hỏi / lựa chọn của đề có gạch chân / { }",
    "co_furigana": "Có furigana",
    "ruby_hong": "Có ruby hỏng trong bản gốc",
    "ky_hieu_trung": "Bản gốc có sẵn ký hiệu ｜《》 (trùng ký hiệu furigana)",
    "danh_dau_rac": "Bản gốc có đoạn in đậm / gạch chân rỗng hoặc chỉ là dấu câu (đã bỏ thẻ)",
    "furigana_chu_viet": "Bản gốc có furigana gắn lên chữ tiếng Việt – Python đã bỏ",
}
CTV_FLAGS = ("khuon_la", "nhieu_dung", "lech_dap_an", "trich_dan_sai_nguon", "doan_khong_ab")


def gan_co(ph, de, segs):
    """→ (cờ, ghi chú bản gốc)."""
    co, gc = [], []
    lc_de, dap = de["lua_chon"], de["dap_an_so"]
    if ph["khuon"] != "chuan":
        co += ["khuon_la", {"dich_doan_van": "dich_doan_van", "chi_dap_an": "chi_dap_an", "goi_y": "goi_y"}.get(ph["khuon"], "khuon_khac")]
        gc.append(f"[Bản gốc VI] Lời giải không theo khuôn chuẩn ({ph['khuon']}) – thiếu phân tích các lựa chọn")
        return co, gc
    if ph["dau"]["cau"] and not eq(ph["dau"]["cau"], de["cau_hoi"]):
        co.append("cau_hoi_lech")
        gc.append(f"[Bản gốc VI] Câu hỏi trong lời giải khác đề: '{strip_marks(ph['dau']['cau'])[:70]}' ↔ đề '{de['cau_hoi'][:70]}'")
    dung = [o["so"] for o in ph["lua_chon"] if o["ket_luan"] is True]
    for o in ph["lua_chon"]:
        if not eq(o["lua_chon"], lc_de[o["so"] - 1]):
            co.append("lua_chon_lech")
            gc.append(f"[Bản gốc VI] Lựa chọn {o['so']} trong lời giải viết khác đề: '{strip_marks(o['lua_chon'])[:50]}' ↔ đề '{lc_de[o['so'] - 1][:50]}'")
        if o["ket_luan"] is None:
            co.append("thieu_ket_luan")
        if o["nghia"] is None:
            co.append("thieu_nghia_lua_chon")
        if o["nghia_lap"]:
            co.append("nghia_lap")
        for q in o["trich_dan"]:
            if not q["khoi"]:
                co.append("trich_dan_giua_cau")
            if q["muc"] == "khong_thay":
                co.append("trich_dan_ngoai_doan")
                gc.append(f"[Bản gốc VI] Lựa chọn {o['so']}: câu trích 「{strip_marks(q['ja'])[:40]}…」 không tìm thấy trong đoạn văn")
            if (q["nhan_neu"] and q["nhan_thay"] and q["nhan_neu"] != q["nhan_thay"] and len(segs) > 1
                    and not tim_trong_doan(q["ja"], segs, q["nhan_neu"])):
                co.append("trich_dan_sai_nguon")
                gc.append(f"[Bản gốc VI] Lựa chọn {o['so']}: lời giải nói câu trích ở đoạn {q['nhan_neu']} nhưng 「{strip_marks(q['ja'])[:40]}…」 nằm ở đoạn {q['nhan_thay']}")
    if len(dung) != 1:
        co.append("nhieu_dung")
        gc.append(f"[Bản gốc VI] Lời giải kết luận ĐÚNG cho {len(dung)} lựa chọn: {dung}")
    elif isinstance(dap, int) and dung[0] != dap:
        co.append("lech_dap_an")
        gc.append(f"[Bản gốc VI] Lời giải kết luận ĐÚNG lựa chọn {dung[0]}, đề dap_an_so = {dap}")
    return co, gc


def goi_y(norm):
    """Gợi ý cho tác tử KIỂM TRA: câu trích không thấy / khớp một phần / nghi sai nguồn A↔B."""
    out = []
    for o in ((norm.get("phan") or {}).get("lua_chon") or []):
        for q in o["trich_dan"]:
            if q["muc"] == "khong_thay":
                out.append(f"K-TD: lựa chọn {o['so']}: 「{strip_marks(q['ja'])[:50]}」 không có trong đoạn văn")
            elif q["muc"] == "mot_phan":
                out.append(f"K-TD: lựa chọn {o['so']}: 「{strip_marks(q['ja'])[:50]}」 chỉ khớp một phần đoạn văn" + (f" (đoạn {q['nhan_thay']})" if q["nhan_thay"] else ""))
            if q["nhan_neu"] and q["nhan_thay"] and q["nhan_neu"] != q["nhan_thay"]:
                out.append(f"K-NGUON: lựa chọn {o['so']}: lời giải nêu đoạn {q['nhan_neu']}, câu trích 「{strip_marks(q['ja'])[:30]}…」 nằm ở đoạn {q['nhan_thay']}")
    return out


# ---------------- kiểm tra JSON GĐ1 ----------------
def _v(o):
    return (o or {}).get("vi") if o else None


def kiem_tra_json(doc, norm, anh_em=()):
    """K-checks riêng dạng 13. anh_em = JSON (checked) của các câu con khác cùng đoạn văn (cho K-NQ). → (lỗi, cảnh báo)."""
    loi, cb = [], []
    de, ph = norm["de"], norm.get("phan") or {}
    khuon = ph.get("khuon")
    chuan = khuon == "chuan"
    dap = de["dap_an_so"] if isinstance(de["dap_an_so"], int) else None
    q, opts, c = doc.get("question") or {}, doc.get("options") or [], doc.get("correct") or {}
    segs = [tuple(x) for x in norm.get("doan_tach") or []]
    if [o.get("index") for o in opts] != [1, 2, 3, 4]:
        loi.append(f"K1: options phải có đủ 4 lựa chọn theo thứ tự 1–4 (đang có {[o.get('index') for o in opts]})")
    dau = ph.get("dau") or {}
    if chuan and dau.get("cau") and not eq(q.get("ja"), dau["cau"]):
        loi.append(f"K8: question.ja khác dòng câu hỏi của lời giải '{strip_marks(dau['cau'])[:60]}'")
    if chuan and (dau.get("nghia") is None) != (q.get("meaning") is None):
        loi.append("K8: question.meaning phải null khi và chỉ khi lời giải không có dòng dịch câu hỏi")
    if not chuan and not q.get("ja"):
        cb.append("K8: question.ja trống – lời giải khuôn lạ không có câu hỏi tiếng Nhật thì chép câu hỏi của đề")
    src = {o["so"]: o for o in ph.get("lua_chon") or []}
    for o in opts:
        i = o.get("index")
        if not isinstance(i, int) or not 1 <= i <= 4:
            continue
        s = src.get(i)
        if s is not None:
            if not eq(o.get("option_ja"), s["lua_chon"]):
                loi.append(f"K2: lựa chọn {i}: option_ja khác dòng lựa chọn của lời giải '{strip_marks(s['lua_chon'])[:50]}'")
            if (s["nghia"] is None) != (o.get("meaning") is None):
                loi.append(f"K3: lựa chọn {i}: meaning phải null khi và chỉ khi lời giải không có dòng 'Nghĩa:'")
            if s["ket_luan"] is not None and o.get("is_match") is not s["ket_luan"]:
                loi.append(f"K4: lựa chọn {i}: is_match phải là {s['ket_luan']} (lời giải: → {'ĐÚNG' if s['ket_luan'] else 'SAI'})")
            n_khoi = sum(1 for x in s["trich_dan"] if x["khoi"])
            if n_khoi != len(o.get("quotes") or []):
                cb.append(f"K-QN: lựa chọn {i}: lời giải có {n_khoi} câu trích đứng thành khối, JSON có {len(o.get('quotes') or [])} quotes – xem lại cách tách câu trích")
        elif not eq(o.get("option_ja"), de["lua_chon"][i - 1]):
            cb.append(f"K2: lựa chọn {i}: lời giải không có dòng lựa chọn tiếng Nhật – option_ja nên chép lựa chọn của đề")
        if (s is None or s["ket_luan"] is None) and dap and o.get("is_match") is not (i == dap):
            loi.append(f"K4: lựa chọn {i}: lời giải không kết luận ĐÚNG/SAI – is_match phải theo đáp án của đề ({i == dap})")
        for kq, qt in enumerate(o.get("quotes") or []):
            ja = qt.get("ja") or ""
            if not co_nhat(ja):
                loi.append(f"K-Q: lựa chọn {i} quotes[{kq}].ja không có tiếng Nhật")
                continue
            if ja.startswith("「") and ja.endswith("」") and QUOTE_RE.fullmatch(ja):
                cb.append(f"K-Q: lựa chọn {i} quotes[{kq}].ja còn cặp 「」 ngoài cùng – bỏ")
            if segs and vi_tri_trich_dan(ja, segs)[1] == "khong_thay":
                cb.append(f"K-TD: lựa chọn {i}: câu trích 「{strip_marks(ja)[:40]}」 không có trong đoạn văn")
    if dap is not None and c.get("index") != dap:
        loi.append(f"K6: correct.index = {c.get('index')} khác dap_an_so = {dap}")
    di = c.get("index")
    if isinstance(di, int) and 1 <= di <= len(opts) and c.get("option_ja") != opts[di - 1].get("option_ja"):
        loi.append(f"K6: correct.option_ja phải giống hệt options[{di - 1}].option_ja")
    if c.get("full_sentence") is not None:
        loi.append("K6: correct.full_sentence phải null (đọc hiểu không có câu hoàn chỉnh)")
    dung = [o.get("index") for o in opts if o.get("is_match") is True]
    if len(dung) != 1 or (dap and dung[0] != dap):
        cb.append(f"K4: is_match = true ở {dung} (đáp án {dap}) – lời giải kết luận lệch đáp án → xem quy tắc dap_an")
    for k in ("summary", "key_info"):
        if doc.get(k) is not None:
            loi.append(f"K-TR: {k} phải null (lời giải dạng 13 không có phần này)")
    ft = doc.get("full_translation")
    if ft is not None:
        if khuon != "dich_doan_van" and "dich_doan_van" not in (norm.get("co") or []):
            loi.append("K-TR: full_translation chỉ dùng khi lời giải có bản dịch đoạn văn (cờ dich_doan_van); câu này phải null")
        for b in ft:
            if b.get("label") not in (None, "A", "B", "C"):
                loi.append(f"K-TR: full_translation.label '{b.get('label')}' không hợp lệ (A / B / C / null)")
            if any(ln.get("ja") is not None for ln in b.get("lines") or []):
                loi.append("K-TR: full_translation.lines[].ja phải null (lời giải chỉ có bản dịch)")
    mine = {_f(x.get("ja")): _v(x.get("meaning")) for o in opts for x in (o.get("quotes") or []) if _v(x.get("meaning"))}
    for other in anh_em:
        for o in other.get("options") or []:
            for x in o.get("quotes") or []:
                k2, m = _f(x.get("ja")), _v(x.get("meaning"))
                if k2 in mine and m and m != mine[k2]:
                    cb.append(f"K-NQ: câu trích 「{strip_marks(x.get('ja'))[:30]}…」 được lời giải dịch khác ở câu {other.get('question_id')}_{other.get('cau_con')} (không sửa – chỉ lưu ý khi soát nghĩa)")
                    mine.pop(k2, None)
    return loi, cb


# ---------------- hiển thị (Excel CTV) ----------------
def render(d, lang, show, bold, tk_render=None):
    def t(o):
        return show((o or {}).get(lang) or "") if o else ""
    q, c = d.get("question") or {}, d.get("correct") or {}
    out = [f"{bold('【Câu hỏi】')} {show(q.get('ja') or '')}"]
    if q.get("meaning"):
        out.append(f"   Nghĩa: {t(q['meaning'])}")
    for b in d.get("full_translation") or []:
        out.append(bold("【Bản dịch đoạn văn" + (f" {b['label']}" if b.get("label") else "") + "】"))
        out += [t(ln.get("meaning")) for ln in b.get("lines") or [] if ln.get("meaning")]
    out.append(bold("【PHÂN TÍCH】"))
    for o in d.get("options") or []:
        out.append(bold(f"{o.get('index')}. ") + show(o.get("option_ja") or ""))
        if o.get("meaning"):
            out.append("   Nghĩa: " + t(o["meaning"]))
        for x in o.get("quotes") or []:
            out.append("   「" + show(x.get("ja") or "") + "」" + (f"\n   ({t(x['meaning'])})" if x.get("meaning") else ""))
        if o.get("analysis"):
            out.append("   " + t(o["analysis"]).replace("\n", "\n   "))
        out.append("   → ĐÚNG." if o.get("is_match") else "   → SAI.")
    out.append(bold("【ĐÁP ÁN】") + f" {c.get('index')}. {show(c.get('option_ja') or '')}")
    if tk_render:
        out += tk_render(d, lang, show, bold)
    return "\n".join(out)


# ---------------- nhãn cố định (bỏ khi đo độ phủ tiếng Việt) ----------------
LABELS = [r"(?m)^\s*(?:→|->|=>)\s*(?:ĐÚNG|SAI|Đúng|Sai)\s*\.?\s*$",
          r"(?im)^\s*[-+•]?\s*nghĩa\s*[:：]",
          r"(?im)^\s*[-+•]?\s*(?:trích dẫn từ đoạn văn|trích dẫn|câu gốc|giải thích|phân tích)\s*[:：]",
          r"(?im)^\s*(?:đoạn văn|câu hỏi)\s*[:：]\s*$",
          r"(?m)^\s*(?:Đoạn văn\s*)?[A-CＡ-Ｃ]\s*[:：]?\s*$",          # nhãn đoạn A / B của bản dịch đoạn văn (khuôn dich_doan_van)
          r"(?m)[A-CＡ-Ｃ](?=[｜\u3040-\u30ff\u3400-\u9fff][^\n ]*$)"]   # chữ Latin A/B dính chữ Nhật trên dòng tiếng Nhật (A社, B社…) – 12535_3


def strip_labels(text):
    for pat in LABELS:
        text = re.sub(pat, " ", text)
    return text


def chen_tu_nhat(text):
    """Dòng tiếng Việt có chen tiếng Nhật ngoài 「」."""
    t = QUOTE_RE.sub(" ", text or "")
    return [ln for ln in t.split("\n") if co_viet(ln) and JA_RE.search(strip_marks(ln))]


def k(s):
    return re.sub(r"[\s　]", "", norm_ja(s or ""))
