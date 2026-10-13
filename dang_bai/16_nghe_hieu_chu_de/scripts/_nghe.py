"""Dạng 16 – Nghe hiểu chủ đề: TÁCH / GHÉP lời thoại, bản dịch, phân tích (Python – không sửa câu chữ).

Khảo sát data/16_nghe_hieu_chu_de.csv (2026-10-08):
  - lời thoại tiếng Nhật thường ở cột `transcript_vi` (tên cột sai nghĩa); 125 câu có `doan_van` (74 câu chỉ là câu dẫn đề,
    52 câu là lời thoại thật – khi đó `transcript_vi` bị dán nhầm phân tích / bản dịch);
  - `giai_thich_vi` = [bản dịch Việt lời thoại] + `###` + [phân tích 1.–4.: câu trích 「…」(dịch), nhận xét, → ĐÚNG / → SAI];
    có câu chép cả lời thoại Nhật trước bản dịch, có câu mở đầu bằng 'Phân tích đoạn hội thoại: …', có câu không có phân tích;
  - lời thoại / bản dịch có khi kèm danh sách lựa chọn, khối từ vựng (**言葉表現 / Biểu hiện từ vựng) ở cuối.

Hàm chính: tach_cau(cot, lua_chon, dap_an_so) → các phần + cờ; goi_y_khoi(khối) → gợi ý câu trích / phân tích cho tác tử TẠO.
(File riêng của dạng 16 – pipeline_chung/nghe_hieu.py là bản của dạng 21, khác API; gộp sau khi các dạng nghe ổn định.)
"""
import re

import _dang_duong_dan  # noqa: F401  (đặt sys.path tới thư mục Vie-Kor)
from pipeline_chung.common import JA_RE, norm_ja, strip_marks
from pipeline_chung.normalize import normalize_html

# ---------------- làm sạch HTML ----------------
_ATTR_RAC_RE = re.compile(r'\\?&quot;|\\"')


def lam_sach(html):
    """HTML → văn bản chuẩn hóa (furigana ｜《》, in đậm / gạch chân → { } theo WF chung 3a). Bỏ rác thuộc tính
    (lang="\\&quot;JA\\&quot;"), &nbsp;, ký tự điều khiển. Trả (văn bản, ruby hỏng, đánh dấu rác)."""
    s = _ATTR_RAC_RE.sub("", html or "")
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", s)
    rac = []
    t, broken = normalize_html(s, "u+b", rac)
    return t, broken, rac


VERDICT_RE = re.compile(r"→\s*(ĐÚNG|SAI)\b")
JA_CHAR_RE = re.compile(r"[぀-ヿ㐀-鿿]")
VI_CHAR_RE = re.compile(r"[ăâđêôơưạảấầẩẫậắằẳẵặẹẻẽếềểễệịỉĩọỏốồổỗộớờởỡợụủứừửữựỳỷỹýàáèéìíòóùú]", re.I)


def ty_le_nhat(text):
    t = strip_marks(re.sub(r"《[^》]*》", "", text or ""))
    j, v = len(JA_CHAR_RE.findall(t)), len(VI_CHAR_RE.findall(t))
    return j / max(1, j + v)


def la_phan_tich(text):
    return bool(VERDICT_RE.search(text or ""))


def _k(s):
    """Khóa so sánh tiếng Nhật: bỏ furigana / { } / ⟪ ⟫, khoảng trắng, dấu câu."""
    return re.sub(r"[\s　。．、,，.！!？?「」『』・（）()…‥~〜～\-ー:：]", "", norm_ja(s or "").replace("{", "").replace("}", ""))


# ---------------- tách dòng + người nói ----------------
SPK_JA_RE = re.compile(r"^(\{?)\s*([^\s:：。、？！?!「」『』（）()\[\]{}…・0-9０-９][^\s:：。、？！?!「」『』（）()\[\]{}…]{0,7}?)\s*[:：]\s*")
SPK_VI_RE = re.compile(r"^(\{?)\s*((?:[A-ZÀ-ỸĐa-zà-ỹđＡ-Ｚ][A-Za-zÀ-ỹĐđ]*|[0-9０-９]+)(?:[ \t][A-Za-zÀ-ỹĐđ0-9０-９]+){0,4}"
                       r"|[^\s:：。、？！?!「」『』（）()\[\]{}…]{1,6})\s*[:：]\s*")
_KHONG_PHAI_NGUOI_NOI = {"nghĩa", "lưu ý", "chú ý", "ví dụ", "đáp án", "câu hỏi", "giải thích", "tóm tắt", "dịch", "cách đọc",
                         "note", "http", "https", "ps"}
NHAN_CAU_HOI = {"Q", "Ｑ", "質問", "問", "問題", "しつもん"}


def tach_nguoi_noi(line, ngon_ngu):
    """'{男：xxx}' → ('男', '{xxx}'); 'Nam: xxx' → ('Nam', 'xxx'); không có nhãn → (None, line)."""
    m = (SPK_JA_RE if ngon_ngu == "ja" else SPK_VI_RE).match(line)
    if not m:
        return None, line
    lab = m.group(2).strip()
    if lab.lower() in _KHONG_PHAI_NGUOI_NOI or re.fullmatch(r"[0-9０-９]+", lab) or (ngon_ngu == "vi" and len(lab.split()) > 4):
        return None, line
    rest = line[m.end():]
    if m.group(1):                       # '{' mở trước nhãn → đưa vào sau nhãn
        rest = "{" + rest
    return lab, rest


def tach_dong(text, ngon_ngu):
    out = []
    for raw in (text or "").split("\n"):
        line = raw.strip()
        if not line or not strip_marks(line).strip(" 　{}"):
            continue
        spk, rest = tach_nguoi_noi(line, ngon_ngu)
        out.append({"speaker": spk, "text": rest.strip()})
    return out


# ---------------- danh sách lựa chọn / dòng phụ ở cuối ----------------
OPT_LINE_RE = re.compile(r"^\s*\{?\s*([1-4１-４])\s*\}?\s*(?:[\.．、)）]\s*(.*)|)$")


def cat_danh_sach_lua_chon(lines, lua_chon=None):
    """Bỏ khối lựa chọn ở CUỐI: '1. … 4. …' (đếm liên tiếp từ 1; '1' trơn với lựa chọn tranh) hoặc các dòng trùng
    nguyên văn lựa chọn của đề (không đánh số). Trả (dòng còn lại, {số: chữ})."""
    i, found = len(lines), {}
    while i > 0:
        m = OPT_LINE_RE.match(lines[i - 1]["text"]) if lines[i - 1]["speaker"] is None else None
        if not m:
            break
        found[int(norm_ja(m.group(1)))] = (m.group(2) or "").strip()
        i -= 1
    if found and min(found) == 1 and len(found) >= 2 and sorted(found) == list(range(1, len(found) + 1)):
        return lines[:i], found
    if lua_chon:
        keys = [_k(x) for x in lua_chon]
        j, got = len(lines), {}
        while j > 0 and lines[j - 1]["speaker"] is None and _k(lines[j - 1]["text"]) and _k(lines[j - 1]["text"]) in keys:
            got[keys.index(_k(lines[j - 1]["text"])) + 1] = lines[j - 1]["text"]
            j -= 1
        if len(got) >= 2:
            return lines[:j], got
    return lines, {}


CAU_HOI_RE = re.compile(r"(?:か|の|ですか|ますか|でしょうか|か\s*\(i\))\s*[。．?？]?\s*\}?\s*$|[?？]\s*\}?\s*$")
PHU_RE = re.compile(r"^\{?\s*(?:\*{2,}|【?\s*(?:言葉表現|言葉と表現|表現|語彙|ことば|単語)\s*】?\s*\}?\s*$"
                    r"|(?:Biểu hiện từ vựng|Từ vựng|Từ mới|Cách diễn đạt)\b)", re.I)


def _la_cau_hoi(x):
    return (x["speaker"] is None or x["speaker"] in NHAN_CAU_HOI) and bool(CAU_HOI_RE.search(strip_marks(x["text"])))


def cat_cuoi(lines, lua_chon=None):
    """Dòng thoại → (dòng thoại đến hết câu hỏi lặp cuối, {số: lựa chọn} dán cuối, [dòng phụ sau đó]).
    Dòng phụ: khối từ vựng (**言葉表現 / Biểu hiện từ vựng …) hoặc các dòng không nhãn sau câu hỏi lặp cuối."""
    phu = []
    for i, x in enumerate(lines):
        if i > 0 and PHU_RE.search(((x["speaker"] + "：") if x["speaker"] else "") + x["text"]):
            phu = [{"speaker": None, "text": (y["speaker"] + "：" + y["text"]) if y["speaker"] else y["text"]} for y in lines[i:]]
            lines = lines[:i]
            break
    lines, ds = cat_danh_sach_lua_chon(lines, lua_chon)
    qi = next((i for i in range(len(lines) - 1, -1, -1) if _la_cau_hoi(lines[i])), None)
    if qi is not None and qi < len(lines) - 1 and qi >= len(lines) - 8 and all(x["speaker"] is None for x in lines[qi + 1:]):
        rest = lines[qi + 1:]
        rest2, ds2 = cat_danh_sach_lua_chon(rest, lua_chon)
        if not rest2 and ds2:
            ds = ds or ds2
        else:
            phu = rest + phu
        lines = lines[:qi + 1]
    return lines, ds, phu


def tach_cau_hoi(lines):
    """Vị trí dòng câu hỏi lặp ở CUỐI lời thoại (không nhãn / nhãn 'Q:', kết thúc bằng か / ？) hoặc None."""
    return len(lines) - 1 if lines and _la_cau_hoi(lines[-1]) else None


def cau_hoi_tu_dong_dau(text):
    """Dòng mở đầu 'Bối cảnh。Câu hỏi？' → câu hỏi (câu cuối kết thúc bằng か / ？)."""
    parts = [p for p in re.split(r"(?<=[。．！？?])", (text or "").strip()) if p.strip()]
    if len(parts) >= 2 and CAU_HOI_RE.search(strip_marks(parts[-1])):
        return parts[-1].strip()
    return None


def ghep_dong(ja, vi):
    """Ghép từng dòng khi số dòng bằng nhau; người nói lấy theo dòng tiếng Nhật. Lệch số dòng → None."""
    if len(ja) != len(vi) or not ja:
        return None
    return [{"speaker": a["speaker"], "ja": a["text"], "meaning": {"vi": b["text"]} if b["text"].strip() else None}
            for a, b in zip(ja, vi)]


def lech_nguoi_noi(ja, vi):
    return sum(1 for a, b in zip(ja, vi) if (a["speaker"] is None) != (b["speaker"] is None))


# ---------------- khối phân tích 1.–4. ----------------
BLOCK_RE = re.compile(r"^\s*\{?\s*([1-4１-４])\s*\}?\s*[\.．、]\s*(.*)$")


def tach_phan_tich(text):
    """Văn bản phân tích → (mở đầu, [{so, dau, dong, ket_luan, so_ket_luan}]). Khối mới khi gặp 'n.' với n = khối trước + 1."""
    mo, blocks, cur = [], [], None
    for ln in (text or "").split("\n"):
        m = BLOCK_RE.match(ln)
        n = int(norm_ja(m.group(1))) if m else None
        if m and n == (cur["so"] + 1 if cur else 1):
            cur = {"so": n, "dau": m.group(2).strip(), "dong": []}
            blocks.append(cur)
        elif cur is None:
            if ln.strip():
                mo.append(ln.strip())
        elif ln.strip():
            cur["dong"].append(ln.strip())
    for b in blocks:
        v = VERDICT_RE.findall(" ".join([b["dau"]] + b["dong"]))
        b["ket_luan"] = v[-1] if v else None
        b["so_ket_luan"] = len(v)
    return "\n".join(mo), blocks


# ---------------- chọn nguồn ----------------
PHAN_TICH_DONG_RE = re.compile(r"「[^」]*[぀-ヿ㐀-鿿][^」]*」|→|^\s*phân tích", re.I)


def _dong_phan_tich(line):
    return bool(PHAN_TICH_DONG_RE.search(line))


def _tach_gt(gt):
    """Lời giải → (phần trước, phần phân tích). Có '###': tách ở '###' đầu; không có: tách ở dòng '1.' cuối cùng đứng trước
    dòng → ĐÚNG/SAI đầu tiên."""
    if "###" in gt:
        a, b = gt.split("###", 1)
        return a.strip(), re.sub(r"(?m)^\s*#{3,}\s*$", "", b).strip()
    if not VERDICT_RE.search(gt):
        return gt.strip(), ""
    lines = gt.split("\n")
    first = next(i for i, l in enumerate(lines) if VERDICT_RE.search(l))
    start = next((i for i in range(first, -1, -1) if BLOCK_RE.match(lines[i]) and norm_ja(BLOCK_RE.match(lines[i]).group(1)) == "1"), None)
    if start is None:
        return "", gt.strip()
    return "\n".join(lines[:start]).strip(), "\n".join(lines[start:]).strip()


def _la_mo_dau_phan_tich(text):
    ds = [l for l in text.split("\n") if l.strip()]
    return bool(ds) and sum(_dong_phan_tich(l) for l in ds) >= max(1, 0.3 * len(ds))


def _dong_ngon_ngu(text, ngon_ngu):
    out = []
    for l in (text or "").split("\n"):
        if strip_marks(l).strip() and (ty_le_nhat(l) >= 0.5) == (ngon_ngu == "ja"):
            out.append(l)
    return "\n".join(out).strip()


def chon_nguon(cot):
    """cot = {'doan_van', 'transcript_vi', 'giai_thich_vi'} (đã lam_sach) → ja / vi / phan_tich / mo_dau_phan_tich + cột nguồn."""
    dv, tr, gt = (cot.get(k) or "" for k in ("doan_van", "transcript_vi", "giai_thich_vi"))
    gt_pre, gt_post = _tach_gt(gt)
    out = {"ja": None, "nguon_ja": None, "vi": None, "nguon_vi": None, "phan_tich": None, "nguon_phan_tich": None,
           "mo_dau_phan_tich": None}
    if gt_post and VERDICT_RE.search(gt_post):
        out["phan_tich"], out["nguon_phan_tich"] = gt_post, "giai_thich_vi"
    elif la_phan_tich(tr):
        out["phan_tich"], out["nguon_phan_tich"] = (_tach_gt(tr)[1] or tr), "transcript_vi"
    if gt_pre and _la_mo_dau_phan_tich(gt_pre):           # 'Phân tích đoạn hội thoại: …' trước khối 1.
        vi_l = [l for l in gt_pre.split("\n") if l.strip() and ty_le_nhat(l) < 0.5]
        if sum(_dong_phan_tich(l) for l in vi_l) >= 0.3 * max(1, len(vi_l)):
            out["mo_dau_phan_tich"], gt_pre = gt_pre, ""
    ung = [(len([x for x in t.split("\n") if x.strip()]), name == "transcript_vi", name, t)
           for name, t in (("doan_van", dv), ("transcript_vi", tr)) if t.strip() and not la_phan_tich(t) and ty_le_nhat(t) > 0.6]
    if ung:                               # doan_van có khi chỉ là câu dẫn đề → lấy cột nhiều dòng hơn
        _, _, out["nguon_ja"], out["ja"] = max(ung)
    else:
        j = _dong_ngon_ngu(gt_pre, "ja")
        if len([x for x in j.split("\n") if x.strip()]) >= 2:
            out["ja"], out["nguon_ja"] = j, "giai_thich_vi"
    v = _dong_ngon_ngu(gt_pre, "vi")
    if len(strip_marks(v)) > 20:
        out["vi"], out["nguon_vi"] = v, "giai_thich_vi"
    else:
        for name, t in (("transcript_vi", tr), ("doan_van", dv)):
            if t.strip() and not la_phan_tich(t) and ty_le_nhat(t) < 0.3 and not _la_mo_dau_phan_tich(t):
                out["vi"], out["nguon_vi"] = t, name
                break
    return out


# ---------------- ghép tất cả ----------------
TRANH_RE = re.compile(r"^\s*[1-4１-４]\s*$")


def la_lua_chon_tranh(lua_chon):
    return all(TRANH_RE.match(strip_marks(x or "")) or not strip_marks(x or "").strip() for x in lua_chon)


def _chuoi(lines):
    return "\n".join(((x["speaker"] + "：") if x["speaker"] else "") + x["text"] for x in lines)


def tach_cau(cot, lua_chon, dap_an_so):
    n = chon_nguon(cot)
    co = []
    ja, oj, pj = cat_cuoi(tach_dong(n["ja"] or "", "ja"), lua_chon)
    vi, ov, pv = cat_cuoi(tach_dong(n["vi"] or "", "vi"), None)
    tranh = la_lua_chon_tranh(lua_chon)
    if pv and not ov and not pj and oj and len(pv) == len(oj):          # bản dịch các lựa chọn (không đánh số) sau câu hỏi
        ov, pv = {k: x["text"] for k, x in zip(sorted(oj), pv)}, []
    if pv and not ov and not pj and len(pv) == 4 and all(x["speaker"] is None for x in pv) and not tranh:
        ov, pv = {i + 1: x["text"] for i, x in enumerate(pv)}, []
    ghep = ghep_dong(ja, vi) if (n["ja"] and n["vi"]) else None
    ghep_phu = ghep_dong(pj, pv) if (pj and pv) else ([] if not (pj or pv) else None)
    full = None
    if ghep is not None and ghep_phu is not None:
        full = [{"label": None, "lines": ghep}] + ([{"label": None, "lines": ghep_phu}] if ghep_phu else [])
    elif n["ja"] and not n["vi"]:
        full = [{"label": None, "lines": [{"speaker": x["speaker"], "ja": x["text"], "meaning": None} for x in ja]}]
        if pj:
            full.append({"label": None, "lines": [{"speaker": None, "ja": x["text"], "meaning": None} for x in pj]})
    elif n["vi"] and not n["ja"]:
        full = [{"label": None, "lines": [{"speaker": x["speaker"], "ja": None, "meaning": {"vi": x["text"]}} for x in vi]}]
        if pv:
            full.append({"label": None, "lines": [{"speaker": None, "ja": None, "meaning": {"vi": x["text"]}} for x in pv]})
    qi = tach_cau_hoi(ja)
    goi_y_q = {"ja": None, "vi": None}
    if qi is not None:
        goi_y_q["ja"] = ja[qi]["text"]
        if ghep is not None:
            goi_y_q["vi"] = vi[qi]["text"]
    elif ja:
        goi_y_q["ja"] = cau_hoi_tu_dong_dau(ja[0]["text"])
    mo, blocks = tach_phan_tich(n["phan_tich"] or "")
    mo_dau = "\n".join(x for x in (n["mo_dau_phan_tich"], mo) if x and x.strip()) or None
    if not n["ja"]:
        co.append("thieu_loi_thoai")
    if not n["vi"]:
        co.append("thieu_ban_dich")
    if not n["phan_tich"]:
        co.append("thieu_phan_tich")
    if n["ja"] and n["vi"] and full is None:
        co.append("lech_dong")
    if ghep is not None and lech_nguoi_noi(ja, vi):
        co.append("nguoi_noi_lech")
    if n["nguon_ja"] and n["nguon_ja"] != "transcript_vi":
        co.append("nguon_loi_thoai_" + n["nguon_ja"])
    if n["nguon_phan_tich"] == "transcript_vi":
        co.append("phan_tich_o_transcript")
    if n["nguon_vi"] and n["nguon_vi"] != "giai_thich_vi":
        co.append("ban_dich_o_" + n["nguon_vi"])
    if mo_dau:
        co.append("mo_dau_phan_tich")
    if pj or pv:
        co.append("phu_loi_thoai")
    if tranh:
        co.append("lua_chon_tranh")
    if n["phan_tich"]:
        if len(blocks) != 4:
            co.append("so_khoi_khac_4")
        dung = [b["so"] for b in blocks if b["ket_luan"] == "ĐÚNG"]
        if not dung:
            co.append("khong_co_dung")
        elif len(dung) > 1:
            co.append("nhieu_dung")
        elif str(dung[0]) != str(dap_an_so):
            co.append("lech_dap_an")
        if any(b["ket_luan"] is None for b in blocks):
            co.append("khoi_khong_ket_luan")
        if any(b["so_ket_luan"] > 1 for b in blocks):
            co.append("khoi_nhieu_ket_luan")
    if qi is None:
        co.append("khong_cau_hoi_cuoi")
    return {"nguon": {k: n[k] for k in ("nguon_ja", "nguon_vi", "nguon_phan_tich")},
            "loi_thoai_ja": ja, "ban_dich_vi": vi, "phu_ja": pj, "phu_vi": pv,
            "ds_lua_chon_ja": {str(k): v for k, v in oj.items()}, "ds_lua_chon_vi": {str(k): v for k, v in ov.items()},
            "full_translation": full, "goi_y_cau_hoi": goi_y_q,
            "mo_dau_ngoai": n["mo_dau_phan_tich"], "phan_tich_mo_dau": mo_dau, "khoi": blocks,
            "lua_chon_tranh": tranh, "co": co}


# ---------------- câu trích 「…」(dịch) + gợi ý tách khối ----------------
QUOTE_RE = re.compile(r"「((?:[^「」]|「[^「」]*」)+)」\s*[（(]([^()（）]*(?:[（(][^()（）]*[)）][^()（）]*)*)[)）]")
DAN_RE = re.compile(r"^[^「」\n,，;；.。]{1,40}[:：]$")       # phần dẫn ngắn: "Giáo viên nói:", "Tiếp theo:", "Nữ 2 trả lời:"
NGHIA_RE = re.compile(r"^\s*(?:-\s*)?Nghĩa\s*[:：]\s*(.*)$", re.I)
VERDICT_DONG_RE = re.compile(r"\s*→\s*(?:ĐÚNG|SAI)\s*[.。]?\s*")
_CAU_MOI_RE = re.compile(r"^[\s.,;:。、]*([A-ZÀ-ỸĐ\"“'‘(]|$)")


def tach_dong_trich(line):
    """Dòng bắt đầu bằng [dẫn:] 「ja」(nghĩa) [lặp] → (câu trích, phần dẫn, phần còn lại) hoặc None.
    Phần còn lại phải là câu mới (chữ hoa / hết dòng); không thì câu trích nằm giữa câu → giữ cả dòng trong phân tích."""
    pos, trich, dan = 0, [], []
    while True:
        m = QUOTE_RE.search(line, pos)
        if not m or not JA_RE.search(strip_marks(m.group(1))):
            break
        lead = line[pos:m.start()].strip()
        if lead and not (DAN_RE.match(lead) and len(lead.split()) <= 7):
            break
        trich.append({"ja": m.group(1).strip(), "nghia": m.group(2).strip()})
        if lead:
            dan.append(lead)
        pos = m.end()
    if not trich:
        return None
    rest = line[pos:]
    if rest.strip() and not _CAU_MOI_RE.match(rest):
        return None
    return trich, dan, re.sub(r"^[\s.,;:。、]+", "", rest).strip()


DICH_DONG_RE = re.compile(r"^\s*[（(]\s*Dịch\s*[:：]\s*(.*?)\s*[)）]\s*$")
PAREN_DONG_RE = re.compile(r"^\s*[（(]\s*([^()（）]*[A-Za-zÀ-ỹ][^()（）]*?)\s*[)）]\s*$")   # dòng chỉ có (nghĩa) sau dòng 「ja」 (lô 71–80)


def gop_trich_nhieu_dong(dong):
    """Câu trích viết trên nhiều dòng: [dẫn:] / 「ja」 / (Dịch: nghĩa) → một dòng '[dẫn:] 「ja」(nghĩa)' (2026-10-08, lô pilot)."""
    ra, i = [], 0
    while i < len(dong):
        a = dong[i].strip()
        j, dan = i, None
        if DAN_RE.match(a) and len(a.split()) <= 7 and i + 1 < len(dong):
            dan, j = a, i + 1
        q = dong[j].strip() if j < len(dong) else ""
        m = (DICH_DONG_RE.match(dong[j + 1]) or PAREN_DONG_RE.match(dong[j + 1])) if j + 1 < len(dong) else None
        if q.startswith("「") and q.endswith("」") and m:
            ra.append(((dan + " ") if dan else "") + q + "(" + m.group(1) + ")")
            i = j + 2
            continue
        # dẫn cùng dòng 'Người phụ nữ nói: 「ja」' + dòng sau '(nghĩa)' (2026-10-08, lô 71–80)
        m2 = (DICH_DONG_RE.match(dong[i + 1]) or PAREN_DONG_RE.match(dong[i + 1])) if i + 1 < len(dong) else None
        if dan is None and m2 and "「" in a and a.endswith("」") and not QUOTE_RE.search(a):
            ra.append(a + "(" + m2.group(1) + ")")
            i += 2
            continue
        if dan and q.startswith("「") and QUOTE_RE.match(q):          # dẫn đứng riêng một dòng + dòng 「ja」(nghĩa) (2026-10-08, lô 21–30)
            ra.append(dan + " " + q)
            i = j + 1
            continue
        ra.append(dong[i])
        i += 1
    return ra


def goi_y_khoi(b):
    """Khối 'n.' → {so, dau, nghia_lua_chon, trich: [{ja, nghia}], dan: [..], phan_tich, ket_luan} (gợi ý)."""
    nghia, trich, dan, con = None, [], [], []
    m = re.match(r"^(.*?)\s*[（(]([^()（）]*[A-Za-zÀ-ỹ][^()（）]*)[)）]\s*$", b["dau"])
    if m and JA_RE.search(strip_marks(m.group(1))) and not JA_RE.search(m.group(2)):
        nghia = m.group(2).strip()
    for ln in gop_trich_nhieu_dong(b["dong"]):
        ln2 = VERDICT_DONG_RE.sub(" ", ln).strip()
        if not ln2:
            continue
        mn = NGHIA_RE.match(ln2)
        if mn and nghia is None and not trich and not con:
            nghia = mn.group(1).strip()
            continue
        t = tach_dong_trich(ln2)
        if t:
            trich += t[0]
            dan += t[1]
            if t[2]:
                con.append(t[2])
            continue
        con.append(ln2)
    return {"so": b["so"], "dau": b["dau"], "nghia_lua_chon": nghia, "trich": trich, "dan": dan,
            "phan_tich": "\n".join(con) or None, "ket_luan": b["ket_luan"]}


def goi_y_tom_tat(mo_dau):
    """Đoạn phân tích mở đầu → gợi ý summary [{heading, points}] (heading = dòng đầu ngắn kết thúc bằng ':')."""
    if not mo_dau:
        return None
    ds = [x.strip() for x in mo_dau.split("\n") if x.strip()]
    head = None
    if ds and len(ds[0]) <= 60 and re.search(r"[:：]\s*$", ds[0]) and not JA_RE.search(strip_marks(ds[0])):
        head = ds.pop(0)
    return [{"heading": head, "points": ds}]


def trong_loi_thoai(quote_ja, loi_thoai_text):
    q = _k(quote_ja)
    return (not q) or q in _k(loi_thoai_text)
