"""Phần riêng của dạng 17 – Nghe hiểu điểm chính (dựng 2026-10-08, chạy hoàn toàn bằng Claude Opus 5.5 Cowork – không GPT API).

Dữ liệu: lời thoại TIẾNG NHẬT ở cột `transcript_vi` (tên cột gây nhầm); `giai_thich_vi` = bản dịch Việt từng dòng lời thoại
+ câu hỏi + nghĩa 4 lựa chọn, rồi tùy khuôn: A `### Thông tin` (dòng thoại then chốt Nhật + dịch) · B `### Đáp án … Vì …`
· C chỉ có bản dịch · D không có tiếng Việt (bỏ qua, chỉ liệt kê).
Schema reading_listening.v1 (không thêm trường). Python tách lượt thoại + nhãn người nói, ghép cặp gợi ý Nhật ↔ Việt và dựng
KHUNG JSON cho tác tử TẠO; kiểm tra riêng K-LT (lời thoại), K-NG (người nói), K-DV (độ phủ Việt theo thứ tự), K-LC, K-DA, K-KI.
Các script s0…s3 đều import file này.
"""
import collections  # noqa: F401
import json
import os
import re
import unicodedata
import sys

DANG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # thư mục dạng bài

try:                                   # để in tiếng Việt / Nhật / Hàn trên cửa sổ lệnh Windows
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

# Chế độ chạy thử với file test: thêm --test vào bất kỳ script nào
#   dữ liệu = config.du_lieu_test, output = config.output_test (tách riêng khỏi output/ thật)
if "--test" in sys.argv:
    sys.argv.remove("--test")
    _c = json.load(open(os.path.join(DANG, "config.json"), encoding="utf-8"))
    os.environ["PIPELINE_OUTPUT"] = _c.get("output_test", "output_test")
    os.environ["PIPELINE_DATA"] = _c.get("du_lieu_test", "data/test_17_nghe_hieu_diem_chinh.csv")


# Chọn đoạn mẫu theo thứ tự trong file dữ liệu: --tu 1 --den 50 (dùng được với mọi script có chọn phạm vi)
def _pop_int(flag):
    if flag not in sys.argv:
        return None
    i = sys.argv.index(flag)
    try:
        v = int(sys.argv[i + 1])
    except (IndexError, ValueError):
        sys.exit(f"{flag} cần một số nguyên, vd {flag} 1")
    del sys.argv[i:i + 2]
    return v


TU, DEN = _pop_int("--tu"), _pop_int("--den")
CA_NAT = "--ca-nat" in sys.argv          # tắt tạm bộ lọc nguồn đề (config.loc_nguon_de) cho lệnh này
if CA_NAT:
    sys.argv.remove("--ca-nat")
VIE_KOR = os.path.dirname(os.path.dirname(DANG))
sys.path.insert(0, VIE_KOR)

from pipeline_chung.common import (FURI_RE, LOCK_RE, get_path, iter_lang_fields, load_json, norm_ja,  # noqa: E402
                                   path_str, save_json, strip_marks)
from pipeline_chung.ctv_excel import B0, B1, bold, show  # noqa: E402
import pipeline_chung.tham_khao as TK  # noqa: E402  (quy tắc THAM KHẢO 2026-10-07)


# ---------------- cấu hình & đường dẫn ----------------
def cfg():
    return load_json(os.path.join(DANG, "config.json"))


def P(*parts):
    """Đường dẫn tính từ thư mục dạng bài."""
    return os.path.normpath(os.path.join(DANG, *parts))


def OUT(*parts):
    """Thư mục output (đổi được bằng biến môi trường PIPELINE_OUTPUT – dùng khi chạy thử giả lập)."""
    return P(os.environ.get("PIPELINE_OUTPUT") or cfg()["output"], *parts)


# ---------------- bản TẠO (bước 1.1 chuyển JSON / 2.1–2.3 dịch) – GPT (cũ) hoặc Claude tác tử tạo (từ 2026-10-08) ----------------
from pipeline_chung import claude_tao as _CT  # noqa: E402  (luồng tác tử tạo dùng chung, 2026-10-08)
THU_MUC_TAO = _CT.THU_MUC_TAO


def nguon_tao():
    """Nguồn tạo bản mới theo config.tao_ban.nguon: 'claude' (Claude Opus Cowork – tác tử tạo) | 'gpt' (GPT API cũ)."""
    return _CT.nguon_tao(cfg())


def thu_muc_tao(lop, sid):
    """Thư mục chứa bản tạo của mẫu: ưu tiên claude_tao/, không có thì gpt/."""
    return _CT.thu_muc_tao(sys.modules[__name__], lop, sid)


def ban_tao(lop, sid, ext=".json"):
    """Đường dẫn file của bản tạo (lop = 'json_vi' | 'json_ko'; ext = '.json' | '.map.json' | '.meta.json')."""
    return _CT.ban_tao(sys.modules[__name__], lop, sid, ext)


def ten_ban_tao(lop, sid):
    return _CT.ten_ban_tao(sys.modules[__name__], lop, sid)


def data_path():
    return P(os.environ.get("PIPELINE_DATA") or cfg()["du_lieu"])


def sid_of(row):
    return f"{row['question_id']}_{row['cau_con']}"


def load_norm(sid):
    return load_json(OUT("samples", "norm", sid + ".json"))


def status_path():
    return OUT("reports", "trang_thai.csv")


def read_prompt(name):
    with open(P("prompts", name), encoding="utf-8") as f:
        return f.read()


def glossary():
    """Gộp bảng thuật ngữ chung + riêng (riêng ưu tiên)."""
    g = {"thuat_ngu": {}, "cau_co_dinh": {}, "mau_cau": {}}
    for path in (os.path.join(VIE_KOR, "pipeline_chung", "glossary_ko.json"), P("glossary_ko.json")):
        if os.path.exists(path):
            d = load_json(path)
            for k in g:
                g[k].update(d.get(k) or {})
    return g


def da_duyet_path(*parts):
    """Kho mẫu đã được CTV chấp nhận (config "da_duyet", mặc định da_duyet/) – không phụ thuộc thư mục output."""
    return P(cfg().get("da_duyet", "da_duyet"), *parts)


def da_duyet_rows():
    """Các dòng của da_duyet/danh_sach.csv (sample_id → dòng)."""
    from pipeline_chung.common import read_csv
    p = da_duyet_path("danh_sach.csv")
    return {r["sample_id"]: r for r in read_csv(p)} if os.path.exists(p) else {}


def danh_dau_da_duyet(st, hash_now=None):
    """Đặt trạng thái ĐÃ_DUYỆT_CTV cho các câu có trong kho da_duyet/ (trừ câu có dữ liệu gốc đã đổi so với lúc duyệt).
    hash_now: {sample_id: hash_goc hiện tại} – mặc định lấy từ trang_thai.csv. Trả về (số câu đánh dấu, danh sách câu lệch hash)."""
    n, lech = 0, []
    for sid, k in da_duyet_rows().items():
        r = st.get(sid)
        if not r:
            continue
        h = (hash_now or {}).get(sid) or r.get("hash_goc")
        if k.get("hash_goc") and h and k["hash_goc"] != h:
            lech.append(sid)
            continue
        if r.get("trang_thai") != "ĐÃ_DUYỆT_CTV":
            st.update(sid, trang_thai="ĐÃ_DUYỆT_CTV", giai_doan_loi="", loi="",
                      canh_bao=f"Đã được CTV chấp nhận ({k.get('file_ctv')}) – xem {cfg().get('da_duyet', 'da_duyet')}/")
            n += 1
    return n, lech


def bo_qua_da_duyet(ids, args, buoc):
    """Bỏ các mẫu đã có trong kho đã duyệt khỏi bước gọi API (trừ khi --ca-da-duyet)."""
    if getattr(args, "ca_da_duyet", False):
        return ids
    kho = da_duyet_rows()
    bo = [s for s in ids if s in kho]
    if bo:
        print(f"Bỏ qua {len(bo)} câu đã được CTV chấp nhận (có trong {cfg().get('da_duyet', 'da_duyet')}/danh_sach.csv) ở bước {buoc}: {bo[:10]}"
              f"{' …' if len(bo) > 10 else ''}  – thêm --ca-da-duyet nếu vẫn muốn chạy")
    return [s for s in ids if s not in kho]


def mau_ngoai_jlpt():
    """Các mẫu bị loại theo config.loc_nguon_de (quyết định 2026-10-11): từ stt tu_mau (thứ tự chạy = thu_tu(),
    tức output/thu_tu_chay.csv), bỏ mẫu mà cột `cot` (thi_thu_thuoc_de – tra theo sample_id trong file dữ liệu)
    chứa một trong `bo_neu_chua` (mặc định 'Nat Test'). Trả về {sample_id: giá trị cột}."""
    lc = cfg().get("loc_nguon_de") or {}
    if CA_NAT or not lc.get("bat"):
        return {}
    from pipeline_chung.common import read_csv
    cot, tu, kw = lc.get("cot", "thi_thu_thuoc_de"), int(lc.get("tu_mau", 1)), lc.get("bo_neu_chua") or ["Nat Test"]
    gt = {sid_of(r): (r.get(cot) or "") for r in read_csv(data_path())}
    return {s: gt.get(s, "") for i, s in enumerate(thu_tu(), 1)
            if i >= tu and any(k.lower() in gt.get(s, "").lower() for k in kw)}


def _loc_jlpt(ids):
    bo = mau_ngoai_jlpt()
    loai = [s for s in ids if s in bo]
    if loai:
        print(f"Lọc nguồn đề (config.loc_nguon_de): bỏ {len(loai)} mẫu thuộc NAT-TEST (không phải đề JLPT): {loai[:10]}"
              f"{' …' if len(loai) > 10 else ''}  – thêm --ca-nat nếu vẫn muốn chạy")
    return [s for s in ids if s not in bo]


def thu_tu():
    """Thứ tự chạy --tu/--den: output/thu_tu_chay.csv (do s0_chuan_bi tạo – 100 câu đầu chia đều N1–N5) nếu có, không thì theo file dữ liệu."""
    from pipeline_chung.common import read_csv
    p = OUT("thu_tu_chay.csv")
    if os.path.exists(p):
        return [r["sample_id"] for r in read_csv(p)]
    return [sid_of(r) for r in read_csv(data_path())]


def select_ids(args, status, default_states):
    """Chọn danh sách câu theo tham số dòng lệnh: --ids, --pilot, --tu A --den B, --lo N, --tat-ca."""
    import csv
    if getattr(args, "ids", None):
        return [x.strip() for x in args.ids.split(",") if x.strip()]
    if getattr(args, "pilot", False):
        with open(OUT("pilot.csv"), encoding="utf-8-sig") as f:
            ids = [r["sample_id"] for r in csv.DictReader(f)]
        return ids
    if TU is not None or DEN is not None:
        from pipeline_chung.common import read_csv
        order = thu_tu()
        a, b = TU or 1, DEN or len(order)
        if a < 1 or b < a:
            sys.exit(f"Phạm vi không hợp lệ: --tu {a} --den {b} (file dữ liệu có {len(order)} mẫu, đánh số từ 1)")
        allowed = set(status.ids(*default_states))
        ids = [s for s in order[a - 1:b] if s in allowed]
        print(f"Phạm vi: mẫu {a}–{min(b, len(order))} theo thứ tự chạy ({'output/thu_tu_chay.csv' if os.path.exists(OUT('thu_tu_chay.csv')) else os.path.basename(data_path())})"
              f" → {len(ids)}/{len(order[a - 1:b])} câu ở trạng thái phù hợp cho bước này")
        return _loc_jlpt(ids)
    ids = _loc_jlpt(status.ids(*default_states))
    if getattr(args, "lo", None):
        ids = ids[: args.lo]
    elif not getattr(args, "tat_ca", False):
        sys.exit("Hãy chọn phạm vi: --pilot, --ids <id1,id2>, --tu <từ mẫu> --den <đến mẫu>, --lo <số câu> hoặc --tat-ca")
    return ids






# =====================================================================================================
#                                PHẦN RIÊNG DẠNG 17 – NGHE HIỂU ĐIỂM CHÍNH
# =====================================================================================================
import html as _html  # noqa: E402

from pipeline_chung.common import JA_RE, VI_DIACRITIC_RE, sha  # noqa: E402
from pipeline_chung.normalize import normalize_html  # noqa: E402

KANA_KANJI_RE = re.compile(r"[぀-ヿ㐀-䶿一-鿿々〆ヶｦ-ﾟ]")
I_RE = re.compile(r"[ \t　]*[（(][ \t　]*[iｉ][ \t　]*[)）]")          # dấu (i) – chỗ chứa đáp án trong lời thoại
SO_LUA_CHON_RE = re.compile(r"^\s*([1-4１-４])\s*(?:[.．、。:：)）]|[ \t　](?=\S))\s*")
TU_VUNG_RE = re.compile(r"^\s*(?:[*＊]{2,}|※)?\s*(?:言葉表現|ことば|語彙|単語|表現)\s*[:：]?\s*$|^\s*[*＊]{3,}")
NHAN_JA_RE = re.compile(r"^\s*([^\s：:、。「」『』（）()！？!?…・,，.．]{1,8}?)[ \t　]*[：:][ \t　]*")
NHAN_VI_RE = re.compile(r"^\s*([^:：.?!,;\n]{1,25}?)\s*[:：]\s*")
HOI_RE = re.compile(r"(か|の|かな|でしょう|ですか|ますか)?\s*[。．]?\s*[？?]?\s*$")
CAU_HOI_JA_RE = re.compile(r"(?:か[。．？?]?|[？?])\s*$")


def _sach(html):
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", html or "")
    return s


def dong(html):
    """HTML → (các dòng văn bản đã chuẩn hóa – ruby → ｜…《…》, bỏ in đậm (Q4), ruby hỏng)."""
    t, broken = normalize_html(_sach(html), "u")
    return [x.strip() for x in t.split("\n") if x.strip()], broken


def plain(html):
    t, b = normalize_html(_sach(html), "u")
    return re.sub(r"\s*\n\s*", " ", t).strip(), b


def in_dam(html):
    """Các đoạn in đậm của bản gốc (Q4: không đổi thành { } – chỉ làm gợi ý cho key_info)."""
    out = []
    for m in re.finditer(r"<(b|strong)\b[^>]*>(.*?)</\1>", _sach(html), re.I | re.S):
        t = plain(m.group(2))[0]
        if t:
            out.append(t)
    return out


def bo_i(s):
    return I_RE.sub("", s or "").strip()


def co_ja(s):
    return bool(KANA_KANJI_RE.search(strip_marks(s or "")))


def co_vi(s):
    return bool(VI_DIACRITIC_RE.search(s or ""))


def chuan_nguoi_noi(nhan):
    if nhan is None:
        return None
    n = nhan.strip()
    return (cfg().get("nguoi_noi") or {}).get("chuan_hoa", {}).get(n, n)


def _nhan_ja(s):
    """Nhãn người nói đầu dòng tiếng Nhật: '女：…' → ('女', '…'); không có → (None, s)."""
    m = NHAN_JA_RE.match(s or "")
    if not m or re.fullmatch(r"[0-9０-９]+", m.group(1)) or co_vi(m.group(1)):
        return None, s
    return m.group(1).strip(), s[m.end():]


def nhan_vi(s):
    """Nhãn người nói đầu dòng tiếng Việt: 'Nam: …' / 'F:…' / 'Người phụ nữ A: …' → (nhãn, phần còn lại)."""
    m = NHAN_VI_RE.match(s or "")
    if not m or co_ja(m.group(1)) or len(m.group(1).split()) > 4 or re.search(r"\d{2}", m.group(1)):
        return None, s
    return m.group(1).strip(), s[m.end():]


# ---------------- tách lượt thoại tiếng Nhật ----------------
def tach_luot(lines):
    """Các dòng lời thoại → lượt [{nhan_goc, speaker, ja}]. Nhãn người nói ở giữa dòng ('…ますか。女：もしもし。') cũng tách
    (chỉ với nhãn đã xuất hiện ở đầu dòng trong cùng bài, cộng 男/女/M/F). Trả về (lượt, các dòng lựa chọn ở cuối lời thoại)."""
    seen = {"男", "女", "M", "F", "Ｍ", "Ｆ"}
    for x in lines:
        n, _ = _nhan_ja(x)
        if n:
            seen.add(n)
    inline = re.compile(r"(?<=[。？！?!」』…\.．)）])[ \t　]*(?=(?:" + "|".join(re.escape(x) for x in sorted(seen, key=len, reverse=True))
                        + r")[ \t　]*[：:])")
    luot, cho, tu_vung = [], None, []
    k = next((i for i, x in enumerate(lines) if TU_VUNG_RE.match(x)), None)
    if k is not None:                     # phần '*** 言葉表現' (từ vựng) cuối lời thoại – không phải lời thoại, bỏ (như quy tắc THAM KHẢO)
        lines, tu_vung = lines[:k], lines[k:]
    for x in lines:
        for seg in inline.split(x):
            seg = seg.strip()
            if not seg:
                continue
            n, rest = _nhan_ja(seg)
            if n is not None and not rest.strip():
                cho = n                     # dòng chỉ có nhãn → gắn cho dòng sau
                continue
            if n is None and cho is not None:
                n, cho = cho, None
            luot.append({"nhan_goc": n, "speaker": chuan_nguoi_noi(n), "ja": rest.strip()})
    lc = []
    while luot and luot[-1]["speaker"] is None and SO_LUA_CHON_RE.match(luot[-1]["ja"]) and len(lc) < 4:
        lc.insert(0, luot.pop()["ja"])
    return luot, lc, tu_vung


def chuoi_nguoi_noi(speakers):
    """Dãy người nói đã gộp các lượt liền nhau cùng người, bỏ None."""
    out = []
    for s in speakers:
        if s and (not out or out[-1] != s):
            out.append(s)
    return out


# ---------------- ghép cặp gợi ý Nhật ↔ Việt ----------------
VI_M = {"nam", "m", "người đàn ông", "đàn ông", "man", "anh", "chồng", "bố", "cha", "nam sinh", "nam sinh viên", "con trai"}
VI_F = {"nữ", "f", "người phụ nữ", "phụ nữ", "woman", "chị", "vợ", "mẹ", "nữ sinh", "nữ sinh viên", "con gái"}


def _hop_nguoi_noi(sp, vi):
    nv, _ = nhan_vi(vi)
    if not nv or sp not in ("M", "F"):
        return True
    nv = nv.lower()
    return not ((sp == "M" and nv in VI_F) or (sp == "F" and nv in VI_M))


def _gop_tiep_noi(luot, q=None):
    """Gộp lượt không có nhãn (không phải lượt đầu / cuối, không phải câu hỏi của đề) vào lượt có nhãn ngay trước –
    lời thoại bị xuống dòng giữa lượt."""
    out = []
    qn = re.sub(r"[\s　。．？?]", "", strip_marks(q or ""))
    for i, t in enumerate(luot):
        if out and t["speaker"] is None and 0 < i < len(luot) - 1 and out[-1]["speaker"] is not None \
                and not (qn and re.sub(r"[\s　。．？?]", "", strip_marks(t["ja"])) == qn):
            out[-1] = {**out[-1], "ja": out[-1]["ja"] + t["ja"]}
        else:
            out.append(dict(t))
    return out


def _gop_cung_nguoi(luot):
    """Gộp các lượt liền nhau của cùng một người nói (bản Việt thường gộp thành một dòng)."""
    out = []
    for t in luot:
        if out and t["speaker"] is not None and out[-1]["speaker"] == t["speaker"]:
            out[-1] = {**out[-1], "ja": out[-1]["ja"] + t["ja"]}
        else:
            out.append(dict(t))
    return out


def _gop_dau(luot):
    if len(luot) >= 2 and luot[0]["speaker"] is None and luot[1]["speaker"] is None:
        return [{**luot[0], "ja": luot[0]["ja"] + luot[1]["ja"]}] + [dict(t) for t in luot[2:]]
    return luot


def ghep_cap(luot, vi, q=None):
    """→ (các dòng gợi ý [{speaker, ja, vi}] hoặc None, cách ghép, có nghi lệch người nói)."""
    cach = [("1-1", luot)]
    l2 = _gop_tiep_noi(luot, q)
    cach.append(("gop_dong_tiep_noi", l2))
    cach.append(("gop_dong_dau", _gop_dau(l2)))
    cach.append(("gop_dong_dau_1", _gop_dau(luot)))
    l3 = _gop_cung_nguoi(l2)
    cach.append(("gop_cung_nguoi_noi", l3))
    cach.append(("gop_cung_nguoi_noi_dau", _gop_dau(l3)))
    for ten, ls in cach:
        if len(ls) == len(vi) and ls:
            nghi = any(not _hop_nguoi_noi(t["speaker"], v) for t, v in zip(ls, vi))
            return [{"speaker": t["speaker"], "ja": t["ja"], "vi": nhan_vi(v)[1].strip()} for t, v in zip(ls, vi)], ten, nghi
    return None, None, False


# ---------------- câu hỏi ----------------
def _cau(s):
    return [x for x in re.split(r"(?<=[。？?！!])", s or "") if x.strip()]


def cau_hoi_goi_y(de_cau_hoi, luot):
    """question.ja: ưu tiên cau_hoi của đề; không có thì câu hỏi lặp lại ở cuối lời thoại; không có nữa thì câu hỏi trong dòng dẫn đầu."""
    if de_cau_hoi:
        return de_cau_hoi, "de"
    if luot and luot[-1]["speaker"] is None and CAU_HOI_JA_RE.search(luot[-1]["ja"]):
        return luot[-1]["ja"], "cuoi_loi_thoai"
    if luot and luot[0]["speaker"] is None:
        cs = [c.strip() for c in _cau(luot[0]["ja"]) if CAU_HOI_JA_RE.search(c.strip())]
        if cs:
            return cs[-1], "dong_dau"
    for t in luot:
        if t["speaker"] in (None, "Q") and CAU_HOI_JA_RE.search(t["ja"]):
            return t["ja"], "khac"
    return None, None


def _nghia_cau_hoi(vi_dong):
    """Nghĩa câu hỏi: câu kết thúc bằng '?' ở dòng Việt cuối (trước 4 lựa chọn), không có thì ở dòng đầu."""
    for v in ([vi_dong[-1]] if vi_dong else []) + ([vi_dong[0]] if vi_dong else []):
        v = nhan_vi(v)[1].strip()
        cs = [c.strip() for c in re.split(r"(?<=[.?!])\s+", v) if c.strip().endswith("?")]
        if cs:
            return cs[-1] if v != vi_dong[-1] else v
    return None


# ---------------- tách giai_thich_vi ----------------
DAU_PHAN_RE = re.compile(r"^#{3,}\s*")
TT_RE = re.compile(r"(?i)^\s*thông\s*tin\s*[:：]?\s*$")
GT_RE = re.compile(r"(?i)^\s*(đáp án|câu\s*\d|vì\b|=>|→|do\b|nên\b)")


def tach_loi_giai(lines):
    """→ dict: truoc (trước ###), sau (sau ###), khuon A/B/C/D."""
    i = next((k for k, x in enumerate(lines) if DAU_PHAN_RE.match(x)), None)
    truoc = lines if i is None else lines[:i]
    sau = [] if i is None else [DAU_PHAN_RE.sub("", x) for x in lines[i + 1:] if not DAU_PHAN_RE.fullmatch(x)]
    sau = [x for x in sau if x.strip()]
    if not any(co_vi(x) for x in truoc):
        k = "D"
    elif not sau:
        k = "C"
    elif TT_RE.match(sau[0]) or re.match(r"(?i)^\s*thông\s*tin\s*[:：]", sau[0]):
        k = "A"
    else:
        k = "B"
    return {"truoc": truoc, "sau": sau, "khuon": k}


TT_TU_VUNG_RE = re.compile(r"(?i)^\s*(?:[*＊]{2,}|※)\s*(?:cụm\s*từ|từ\s*ngữ|từ\s*vựng|言葉表現|ことば|語彙|単語|表現)")


def tach_thong_tin(sau):
    """Phần sau '### Thông tin': dòng Nhật / dòng Việt / câu giải thích thêm."""
    body = list(sau)
    if body:
        m = re.match(r"(?i)^\s*thông\s*tin\s*[:：]?\s*", body[0])
        rest = body[0][m.end():].strip() if m else body[0]
        body = ([rest] if rest else []) + body[1:]
    # phần từ vựng ('***　Cụm từ…', '**** Từ ngữ:', '**　Từ vựng', '*** 言葉表現') sau Thông tin – không phải Thông tin, bỏ
    for k, x in enumerate(body):
        if TT_TU_VUNG_RE.match(x):
            body = body[:k]
            break
    ja, vi, gt = [], [], []
    for x in body:
        if co_ja(x) and not co_vi(x):
            ja.append(x)
        elif not nhan_vi(x)[0] and GT_RE.match(x) and co_vi(x):
            gt.append(x)
        else:
            vi.append(x)
    return ja, vi, gt


# ---------------- chuẩn bị một câu (s0) ----------------
FLAG_TEXT = {
    "khuon_A": "Khuôn A – có '### Thông tin' (dòng thoại then chốt + dịch) → key_info",
    "khuon_B": "Khuôn B – '### Đáp án … Vì …' → analysis của lựa chọn đúng; key_info = []",
    "khuon_C": "Khuôn C – chỉ có bản dịch; key_info = dòng có (i) nếu duy nhất (Python chép nghĩa)",
    "khong_tieng_viet": "Khuôn D – lời giải không có tiếng Việt (chỉ chép lại lời thoại) → bỏ qua, liệt kê cho CTV",
    "thong_tin_khong_dich": "Phần Thông tin chỉ có dòng tiếng Nhật – nghĩa key_info do Python chép từ bản dịch lời thoại",
    "thong_tin_lech_so_dong": "Phần Thông tin: số dòng Nhật ≠ số dòng Việt – tác tử TẠO tự ghép",
    "thong_tin_ngoai_loi_thoai": "Có dòng Nhật trong Thông tin không tìm thấy trong lời thoại",
    "thong_tin_co_giai_thich": "Phần Thông tin có thêm câu giải thích (Đáp án … / Vì …) → analysis của lựa chọn đúng",
    "thong_tin_khong_phai_tieng_viet": "Dòng 'dịch' trong Thông tin không phải tiếng Việt (vd tiếng Anh) – nghi lỗi bản gốc",
    "lech_so_dong": "Số dòng Việt ≠ số lượt thoại Nhật – Python không ghép được, tác tử TẠO tự ghép",
    "ghep_gop_dong": "Python ghép được sau khi gộp dòng thoại bị xuống dòng giữa lượt / gộp dòng dẫn",
    "ghep_nghi_nguoi_noi": "Ghép 1–1 nhưng có dòng lệch người nói (Nam ↔ 女…) – soát kỹ thứ tự",
    "tach_nhan_giua_dong": "Lời thoại có nhãn người nói ở giữa dòng – Python đã tách thành lượt riêng",
    "loi_thoai_co_tu_vung": "Lời thoại có phần từ vựng '*** 言葉表現' ở cuối – Python bỏ (không phải lời thoại)",
    "loi_thoai_co_lua_chon": "Lời thoại có 4 lựa chọn ở cuối – Python bỏ khỏi full_translation (đã có ở options)",
    "cau_hoi_la_so_thu_tu": "cau_hoi của đề chỉ là số thứ tự ('3番', '問 7 .') – bỏ qua, lấy câu hỏi từ lời thoại",
    "cau_hoi_trong_loi_thoai": "Đề không có cau_hoi – question.ja lấy từ lời thoại",
    "khong_tim_cau_hoi": "Không tìm được câu hỏi tiếng Nhật – question.ja = null",
    "khong_nghia_lua_chon": "Lời giải không có dòng nghĩa của 4 lựa chọn – options[*].meaning = null",
    "lua_chon_lech": "4 dòng Việt cuối (nghĩa lựa chọn) không chắc là lựa chọn – soát",
    "lua_chon_co_so": "Lựa chọn của đề có số '1.' ở đầu – option_ja bỏ số",
    "dap_an_ly_do_lech": "Khuôn B: số đáp án trong lời giải khác dap_an_so",
    "co_i": "Lời thoại có dấu (i) (chỗ chứa đáp án)",
    "nhieu_i": "Lời thoại có nhiều dấu (i)",
    "in_dam": "Bản gốc in đậm dòng then chốt (Q4: bỏ in đậm, chỉ là gợi ý cho key_info)",
    "co_furigana": "Có furigana – chép nguyên ｜chữ《cách đọc》",
    "ruby_hong": "Có thẻ ruby hỏng",
}
CTV_FLAGS = ("thong_tin_ngoai_loi_thoai", "thong_tin_khong_phai_tieng_viet", "dap_an_ly_do_lech")
FURI_SKIP = []


def chuan_bi(row):
    """Một dòng CSV → bản ghi norm (output/samples/norm/<id>.json)."""
    sid = sid_of(row)
    dap = int(row["dap_an_so"]) if str(row["dap_an_so"]).strip().isdigit() else row["dap_an_so"]
    lc_raw = [plain(row.get(f"lua_chon_{i}", ""))[0] for i in range(1, 5)]
    lc = [SO_LUA_CHON_RE.sub("", x, count=1) for x in lc_raw]
    cau_hoi = plain(row.get("cau_hoi", ""))[0]
    cau_hoi_so = None
    if re.fullmatch(r"\s*(?:問|もんだい)?\s*[0-9０-９]+\s*(?:番|ばん|ばんめ|\.|．)?\s*[.．]?\s*", cau_hoi or ""):
        cau_hoi_so, cau_hoi = cau_hoi, ""          # cau_hoi chỉ là số thứ tự câu ('3番', '問 7 .') – không phải câu hỏi
    tr_lines, b1 = dong(row.get("transcript_vi"))
    gt_lines, b2 = dong(row.get("giai_thich_vi"))
    co, gc = [], []
    rec = {"sample_id": sid, "question_id": int(row["question_id"]), "cau_con": int(row["cau_con"]), "cap_do": row["cap_do"],
           "hash_goc": sha((row.get("transcript_vi") or "") + "|" + (row.get("giai_thich_vi") or "") + "|" + (row.get("cau_hoi") or "")
                           + "|" + "|".join(lc_raw) + "|" + str(row["dap_an_so"])),
           "de": {"cau_hoi": cau_hoi or None, "lua_chon": lc, "dap_an_so": dap, "dap_an_noi_dung": plain(row.get("dap_an_noi_dung", ""))[0]},
           "ruby_hong": b1 + b2, "phan": None, "marks_src": []}
    if lc != lc_raw:
        co.append("lua_chon_co_so")
    if cau_hoi_so:
        co.append("cau_hoi_la_so_thu_tu")
        rec["de"]["cau_hoi_goc"] = cau_hoi_so
    luot, lc_tr, tu_vung = tach_luot(tr_lines)
    if not lc_tr and len(luot) >= 5 and all(t["speaker"] is None for t in luot[-4:]):
        # 4 lựa chọn KHÔNG đánh số ở cuối lời thoại (khuôn C, N1/N3) – nhận khi ≥ 3/4 khớp lựa chọn của đề (2026-10-08, lô 1–10)
        _nn = lambda z: re.sub(r"[\s　。．.、,]", "", unicodedata.normalize("NFKC", z or ""))
        if sum(_nn(t["ja"]) == _nn(b) for t, b in zip(luot[-4:], lc)) >= 3:
            lc_tr = [t["ja"] for t in luot[-4:]]
            luot = luot[:-4]
    rec["tu_vung_loi_thoai"] = tu_vung
    if tu_vung:
        co.append("loi_thoai_co_tu_vung")
        gc.append("[Bản gốc VI] Lời thoại có phần từ vựng '*** 言葉表現' ở cuối – không phải lời thoại, Python bỏ khỏi JSON (như quy tắc THAM KHẢO)")
    if len(luot) > len(tr_lines) - len(tu_vung):
        co.append("tach_nhan_giua_dong")
    if lc_tr:
        co.append("loi_thoai_co_lua_chon")
    rec["loi_thoai_goc"] = tr_lines
    rec["luot"] = luot
    rec["lua_chon_trong_loi_thoai"] = lc_tr
    rec["in_dam"] = in_dam(row.get("transcript_vi")) + [x for x in in_dam(row.get("giai_thich_vi")) if co_ja(x)]
    if rec["in_dam"]:
        co.append("in_dam")
    n_i = sum(1 for t in luot if I_RE.search(t["ja"]))
    if n_i:
        co.append("co_i" if n_i == 1 else "nhieu_i")
    lg = tach_loi_giai(gt_lines)
    rec["khuon_goc"] = lg["khuon"]
    rec["loi_giai_goc"] = gt_lines
    if lg["khuon"] == "D":
        co.append("khong_tieng_viet")
        gc.append("[Bản gốc VI] Khuôn D – lời giải không có tiếng Việt (chỉ chép lại lời thoại tiếng Nhật): bỏ qua, chuyển CTV dịch bổ sung")
        rec.update(co=sorted(set(co)), ghi_chu_ban_goc=gc, dau_vao=None, src_text="", src_vi_text="", src_text_furi="", khung=None)
        return rec
    co.append("khuon_" + lg["khuon"])
    truoc = lg["truoc"]
    if len(truoc) >= 5 and not any(nhan_vi(x)[0] and not SO_LUA_CHON_RE.match(x) for x in truoc[-4:]):
        vi_lc, vi_dong = truoc[-4:], truoc[:-4]
        so = [SO_LUA_CHON_RE.match(x) for x in vi_lc]
        if any(co_ja(x) or nhan_vi(x)[0] for x in vi_lc) or (any(so) and [m.group(1) if m else None for m in so] != ["1", "2", "3", "4"]
                                                             and [m.group(1) if m else None for m in so] != ["１", "２", "３", "４"]):
            co.append("lua_chon_lech")
    else:
        vi_lc, vi_dong = [], truoc
        co.append("khong_nghia_lua_chon")
        gc.append("[Bản gốc VI] Lời giải không có nghĩa 4 lựa chọn – options[*].meaning = null")
    rec["vi"] = {"dong_thoai": vi_dong, "lua_chon": vi_lc, "sau_phan_cach": lg["sau"]}
    q_ja, q_nguon = cau_hoi_goi_y(cau_hoi, luot)
    goi_y, cach, nghi = ghep_cap(luot, vi_dong, q_ja)
    rec["ghep"] = {"cach": cach, "dong": goi_y}
    if goi_y is None:
        co.append("lech_so_dong")
    elif cach != "1-1":
        co.append("ghep_gop_dong")
    if nghi:
        co.append("ghep_nghi_nguoi_noi")
    if q_nguon and q_nguon != "de":
        co.append("cau_hoi_trong_loi_thoai")
    if not q_ja:
        co.append("khong_tim_cau_hoi")
    q_vi = _nghia_cau_hoi(vi_dong)
    # Thông tin / lý do
    key_info, analysis = [], None
    tt = {"ja": [], "vi": [], "giai_thich": []}
    T = norm_ja("".join(bo_i(t["ja"]) for t in luot))
    if lg["khuon"] == "A":
        ja_l, vi_l, gt_l = tach_thong_tin(lg["sau"])
        tt = {"ja": ja_l, "vi": vi_l, "giai_thich": gt_l}
        if gt_l:
            co.append("thong_tin_co_giai_thich")
            analysis = "\n".join(gt_l)
        if not vi_l:
            co.append("thong_tin_khong_dich")
            gc.append("[Bản gốc VI] Phần Thông tin chỉ có tiếng Nhật – nghĩa key_info do Python chép từ bản dịch lời thoại (Q3)")
        elif len(vi_l) != len(ja_l):
            co.append("thong_tin_lech_so_dong")
        if any(not co_vi(x) for x in vi_l):
            co.append("thong_tin_khong_phai_tieng_viet")
        for k, x in enumerate(ja_l):
            n, rest = _nhan_ja(x)
            if norm_ja(bo_i(rest))[:20] not in T:
                co.append("thong_tin_ngoai_loi_thoai")
            v = vi_l[k] if len(vi_l) == len(ja_l) else None
            key_info.append({"speaker": chuan_nguoi_noi(n), "ja": bo_i(rest),
                             "meaning": {"vi": bo_i(nhan_vi(v)[1])} if v else None})
    elif lg["khuon"] == "B":
        analysis = "\n".join(lg["sau"])
        m = re.search(r"(?i)(?:đáp án|câu)\D{0,20}?([1-4])", " ".join(lg["sau"][:2]))
        if m and str(m.group(1)) != str(dap):
            co.append("dap_an_ly_do_lech")
            gc.append(f"[Bản gốc VI] Lý do ghi đáp án {m.group(1)} nhưng dap_an_so = {dap}")
    else:   # C
        i_luot = [t for t in luot if I_RE.search(t["ja"])]
        if len(i_luot) == 1:
            key_info = [{"speaker": i_luot[0]["speaker"], "ja": bo_i(i_luot[0]["ja"]), "meaning": None}]
            gc.append("[Bản gốc VI] Khuôn C (chỉ có bản dịch) – key_info = dòng thoại có (i), nghĩa do Python chép (Q3)")
    rec["thong_tin"] = tt
    # khung JSON cho tác tử TẠO
    lines = [{"speaker": t["speaker"], "ja": t["ja"], "meaning": {"vi": t["vi"]} if t.get("vi") else None} for t in (goi_y or
             [dict(x, vi=None) for x in luot])]
    opts = []
    for i in range(4):
        v = SO_LUA_CHON_RE.sub("", nhan_vi(vi_lc[i])[1] if i < len(vi_lc) else "", count=1).strip() if vi_lc else ""
        opts.append({"index": i + 1, "option_ja": lc[i], "reading": None, "meaning": {"vi": v} if v else None,
                     "is_match": (i + 1) == dap, "quotes": [], "analysis": {"vi": analysis} if (analysis and (i + 1) == dap) else None})
    rec["khung"] = {"schema": "reading_listening.v1", "question_id": rec["question_id"], "cau_con": rec["cau_con"],
                    "full_translation": [{"label": None, "lines": lines}], "summary": None,
                    "question": {"ja": q_ja, "meaning": {"vi": q_vi} if q_vi else None},
                    "options": opts, "key_info": key_info,
                    "correct": {"index": dap, "option_ja": lc[dap - 1] if isinstance(dap, int) and 1 <= dap <= 4 else "", "full_sentence": None}}
    # chuẩn so sánh của Python
    src_ja = [t["ja"] for t in luot] + tt["ja"] + ([cau_hoi] if cau_hoi else []) + lc
    rec["src_text"] = "\n".join(_nhan_ja(x)[1] for x in src_ja)
    rec["src_text_furi"] = "\n".join([t["ja"] for t in luot] + [_nhan_ja(x)[1] for x in tt["ja"]])
    vi_src = vi_dong + vi_lc + (tt["vi"] + tt["giai_thich"] if lg["khuon"] == "A" else lg["sau"] if lg["khuon"] == "B" else [])
    # bản sao có chủ ý (không tính là 'từ thừa'): question.meaning = dòng câu hỏi Việt; key_info chép nghĩa dòng thoại (khuôn C / Thông tin chỉ tiếng Nhật)
    # q_vi chỉ là bản sao khi khung có dòng thoại mang đúng câu hỏi đó (lời thoại không có dòng câu hỏi → không sao)
    sao = [q_vi] if q_vi and any((l.get("meaning") or {}).get("vi") == q_vi for l in lines) else []
    for x in key_info:
        # khuôn A có Thông tin tiếng Việt (kể cả lệch số dòng) → nghĩa key_info lấy từ Thông tin, đã có trong vi_src
        if x.get("meaning") is None and goi_y and not (lg["khuon"] == "A" and tt["vi"]):
            sao += [t["vi"] for t in goi_y if t.get("vi") and _n(bo_i(t["ja"])) == _n(x["ja"])]
    rec["src_vi_text"] = "\n".join(x for x in vi_src + sao if not (co_ja(x) and not co_vi(x)))
    rec["dau_vao"] = ("LỜI THOẠI (transcript_vi):\n" + "\n".join(tr_lines) + "\n\nLỜI GIẢI (giai_thich_vi):\n" + "\n".join(gt_lines))
    if furigana_pairs(rec["dau_vao"]):
        co.append("co_furigana")
    if rec["ruby_hong"]:
        co.append("ruby_hong")
        gc.append(f"[Bản gốc VI] Có {len(rec['ruby_hong'])} thẻ ruby hỏng")
    rec["co"] = sorted(set(co))
    rec["ghi_chu_ban_goc"] = gc
    return rec


from pipeline_chung.common import furigana_pairs  # noqa: E402


# ---------------- thứ tự chạy ----------------
def tao_thu_tu(recs, cfg_):
    """100 câu đầu: 20 câu mỗi cấp N1–N5 xen kẽ (mỗi cấp ưu tiên ≥ 3 câu khuôn B, ≥ 2 câu khuôn C); rồi các câu còn lại theo file;
    câu khuôn D xếp cuối."""
    import random
    tc = cfg_.get("thu_tu_chay") or {}
    rng = random.Random(tc.get("seed", 2026))
    n = tc.get("moi_cap_do", 20)
    lv = {}
    for k in ["N1", "N2", "N3", "N4", "N5"]:
        pool = [r for r in recs if r["cap_do"] == k and r["khuon_goc"] in "ABC"]
        rng.shuffle(pool)
        chon = [r for r in pool if r["khuon_goc"] == "B"][:3] + [r for r in pool if r["khuon_goc"] == "C"][:2]
        chon += [r for r in pool if r not in chon][: n - len(chon)]
        rng.shuffle(chon)
        lv[k] = chon
    dau = [lv[k][i] for i in range(n) for k in ["N1", "N2", "N3", "N4", "N5"] if i < len(lv[k])]
    seen = {r["sample_id"] for r in dau}
    rows = dau + [r for r in recs if r["sample_id"] not in seen and r["khuon_goc"] != "D"] + [r for r in recs if r["khuon_goc"] == "D"]
    return [{"stt": i + 1, "sample_id": r["sample_id"], "question_id": r["question_id"], "cap_do": r["cap_do"], "khuon": r["khuon_goc"]}
            for i, r in enumerate(rows)]


# ---------------- nhãn cố định (bỏ khi đo độ phủ) ----------------
def strip_labels(text):
    out = []
    for x in (text or "").split("\n"):
        x = DAU_PHAN_RE.sub("", x)
        if TT_RE.match(x):
            continue
        x = re.sub(r"(?i)^\s*thông\s*tin\s*[:：]\s*", "", x)
        x = nhan_vi(x)[1]
        x = SO_LUA_CHON_RE.sub("", x, count=1)
        out.append(x)
    return "\n".join(out)


# ---------------- kiểm tra riêng GĐ1 ----------------
def _n(s):
    """So lời thoại: bỏ furigana, ⟪ ⟫ { }, mọi khoảng trắng."""
    return re.sub(r"[\s　]+", "", strip_marks(s or ""))


def _vi_tokens(s):
    return re.findall(r"[0-9a-zà-ỹđ]+", strip_marks(s or "").lower())


def do_phu_theo_thu_tu(src_lines, out_lines):
    import difflib
    a = [w for x in src_lines for w in _vi_tokens(nhan_vi(x)[1])]
    b = [w for x in out_lines for w in _vi_tokens(x)]
    if not a:
        return None, []
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    khop = sum(bl.size for bl in sm.get_matching_blocks())
    thieu = [" ".join(a[i1:i2]) for op, i1, i2, j1, j2 in sm.get_opcodes() if op in ("delete", "replace") and i2 - i1 >= 3]
    return khop / len(a), thieu


def _lines(doc):
    out = []
    for bi, blk in enumerate(doc.get("full_translation") or []):
        for li, ln in enumerate((blk or {}).get("lines") or []):
            out.append((bi, li, ln))
    return out


def check_k(doc, norm, policy=None):
    """Kiểm tra riêng dạng 17. Trả về (lỗi, cảnh báo)."""
    loi, cb = [], []
    de = norm["de"]
    ft = doc.get("full_translation")
    if not isinstance(ft, list) or len(ft) != 1:
        loi.append("K-LT: full_translation phải là mảng 1 khối {label: null, lines: […]}")
    lines = _lines(doc)
    # K-LT: ghép ja các dòng = lời thoại gốc
    want = _n("".join(t["ja"] for t in norm["luot"]))
    got = _n("".join((ln.get("ja") or "") for _, _, ln in lines))
    if want != got:
        import difflib
        sm = difflib.SequenceMatcher(None, want, got, autojunk=False)
        d = [f"{op}: '{want[i1:i2][:25]}' → '{got[j1:j2][:25]}'" for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal"][:4]
        loi.append(f"K-LT: lời thoại tiếng Nhật trong full_translation khác lời thoại gốc (thiếu / thừa / đổi chữ / đảo dòng): {d}")
    # K-NG: người nói
    if chuoi_nguoi_noi([ln.get("speaker") for _, _, ln in lines]) != chuoi_nguoi_noi([t["speaker"] for t in norm["luot"]]):
        loi.append(f"K-NG: dãy người nói khác lời thoại gốc: {chuoi_nguoi_noi([ln.get('speaker') for _, _, ln in lines])[:12]} ≠ "
                   f"{chuoi_nguoi_noi([t['speaker'] for t in norm['luot']])[:12]}")
    hop_le = {t["speaker"] for t in norm["luot"]} | {None}
    la = sorted({str(ln.get("speaker")) for _, _, ln in lines if ln.get("speaker") not in hop_le})
    if la:
        loi.append(f"K-NG: nhãn người nói không có trong lời thoại gốc: {la}")
    for bi, li, ln in lines:
        if ln.get("ja") and nhan_vi(ln["ja"])[0] is None and _nhan_ja(ln["ja"])[0] and ln.get("speaker") is None and \
                _nhan_ja(ln["ja"])[0] in {t["nhan_goc"] for t in norm["luot"] if t["nhan_goc"]}:
            loi.append(f"K-NG: $.full_translation[{bi}].lines[{li}].ja còn nhãn người nói '{_nhan_ja(ln['ja'])[0]}' – tách vào speaker")
        m = ln.get("meaning")
        if isinstance(m, dict) and nhan_vi(m.get("vi") or "")[0] and (nhan_vi(m["vi"])[0].lower() in VI_M | VI_F or len(nhan_vi(m["vi"])[0]) <= 2):
            cb.append(f"K-NV: $.full_translation[{bi}].lines[{li}].meaning.vi còn nhãn người nói '{nhan_vi(m['vi'])[0]}:' – bỏ nhãn")
    # K-NV: nghĩa của dòng lấy từ dòng Việt có nhãn người nói ngược giới (Nam ↔ F, Nữ ↔ M) → nghi ghép lệch dòng
    nguon_vi = [nhan_vi(x) for x in (norm.get("vi") or {}).get("dong_thoai") or []]
    for bi, li, ln in lines:
        v = ((ln.get("meaning") or {}).get("vi") or "").strip()
        nv = next((a for a, b in nguon_vi if a and b.strip() == v), None) if v else None
        if nv and ((ln.get("speaker") == "M" and nv.lower() in VI_F) or (ln.get("speaker") == "F" and nv.lower() in VI_M)):
            cb.append(f"K-NV: $.full_translation[{bi}].lines[{li}]: người nói {ln.get('speaker')} nhưng dòng Việt gốc ghi '{nv}:' – nghi ghép lệch dòng")
    # K-DV: dòng có tiếng Việt gốc mà không có nghĩa / độ phủ theo thứ tự
    khong_nghia = [f"[{li}]" for _, li, ln in lines if ln.get("ja") and not ln.get("meaning")]
    if khong_nghia:
        cb.append(f"K-DV: {len(khong_nghia)} dòng thoại không có meaning: {khong_nghia[:8]} – bản gốc không dịch dòng này? (thiếu thật → cờ thieu_noi_dung)")
    vi_dong = (norm.get("vi") or {}).get("dong_thoai") or []
    out = [((ln.get("meaning") or {}).get("vi") or "") for _, _, ln in lines]
    qv = ((doc.get("question") or {}).get("meaning") or {}).get("vi") or ""
    src = [x for x in vi_dong if not (qv and _vi_tokens(nhan_vi(x)[1]) == _vi_tokens(qv) and not any(_vi_tokens(qv) == _vi_tokens(o) for o in out))]
    tl, thieu = do_phu_theo_thu_tu(src, out)
    nguong = (cfg().get("kiem_tra") or {}).get("loi_thoai_do_phu_vi_theo_thu_tu_min", 0.97)
    if tl is not None and tl < nguong:
        loi.append(f"K-DV: bản dịch lời thoại chỉ phủ {tl:.1%} bản gốc theo đúng thứ tự (ghép lệch dòng / bỏ sót / đảo câu): thiếu {thieu[:4]}")
    # K-LC / K-DA
    opts = doc.get("options") or []
    if [o.get("index") for o in opts] != [1, 2, 3, 4]:
        loi.append("K-LC: options phải có đủ 4 lựa chọn index 1–4 theo thứ tự")
    for k, o in enumerate(opts[:4]):
        if _n(o.get("option_ja")) != _n(de["lua_chon"][k]):
            loi.append(f"K-LC: options[{k}].option_ja '{o.get('option_ja')}' ≠ lựa chọn {k + 1} của đề '{de['lua_chon'][k]}'")
        if o.get("reading") is not None:
            loi.append(f"K-LC: options[{k}].reading phải null (lời giải không có cách đọc lựa chọn)")
        if o.get("quotes"):
            loi.append(f"K-LC: options[{k}].quotes phải [] (dạng 17 không dùng trích dẫn)")
        if o.get("analysis") and (k + 1) != de["dap_an_so"]:
            cb.append(f"K-LC: options[{k}].analysis có nội dung nhưng không phải lựa chọn đúng – xem lại")
    dung = [o.get("index") for o in opts if o.get("is_match")]
    c = doc.get("correct") or {}
    if dung != [de["dap_an_so"]]:
        loi.append(f"K-DA: is_match = true phải đúng 1 lựa chọn = dap_an_so {de['dap_an_so']} (đang: {dung})")
    if c.get("index") != de["dap_an_so"]:
        loi.append(f"K-DA: correct.index = {c.get('index')} ≠ dap_an_so {de['dap_an_so']}")
    elif _n(c.get("option_ja")) != _n(de["lua_chon"][de["dap_an_so"] - 1]):
        loi.append("K-DA: correct.option_ja khác lựa chọn đúng của đề")
    if c.get("full_sentence") is not None:
        loi.append("K-DA: correct.full_sentence phải null")
    if doc.get("summary") is not None:
        loi.append("K-SM: summary phải null (bản gốc không có tóm tắt)")
    # câu hỏi
    q = doc.get("question") or {}
    if de.get("cau_hoi"):
        if _n(q.get("ja")) != _n(de["cau_hoi"]):
            cb.append(f"K-CH: question.ja khác cau_hoi của đề ('{de['cau_hoi']}')")
    elif q.get("ja") and _n(q["ja"]) not in want:
        cb.append("K-CH: question.ja không tìm thấy trong lời thoại")
    if not q.get("meaning"):
        cb.append("K-CH: question.meaning = null")
    # key_info
    ki = doc.get("key_info") or []
    for k, x in enumerate(ki):
        if _n(bo_i(x.get("ja")))[:40] not in want.replace("(i)", "").replace("（i）", ""):
            cb.append(f"K-KI: key_info[{k}].ja không có nguyên văn trong lời thoại")
        if I_RE.search(x.get("ja") or "") or I_RE.search(((x.get("meaning") or {}).get("vi")) or ""):
            loi.append(f"K-KI: key_info[{k}] còn dấu (i) – bỏ (i) trong key_info")
    if norm["khuon_goc"] == "A" and len(ki) != len(norm["thong_tin"]["ja"]):
        cb.append(f"K-KI: key_info có {len(ki)} dòng, phần Thông tin có {len(norm['thong_tin']['ja'])} dòng tiếng Nhật")
    if norm["khuon_goc"] == "B" and ki:
        cb.append("K-KI: khuôn B – key_info phải [] (Q3)")
    i_ja = [_n(bo_i(t["ja"])) for t in norm["luot"] if I_RE.search(t["ja"])]
    if ki and i_ja and not any(_n(bo_i(x.get("ja")))[:15] in j or j[:15] in _n(bo_i(x.get("ja"))) for x in ki for j in i_ja):
        cb.append("K-KI: key_info không chứa dòng thoại có dấu (i) – xem lại có chọn đúng dòng then chốt không")
    if any((k.get("meaning") is None) for k in ki):
        cb.append("K-KI: có key_info chưa có meaning (không tìm thấy dòng thoại trùng để Python chép)")
    return loi, cb


def furi_skip(doc, norm):
    """So furigana chỉ trên lời thoại (+ key_info lấy từ phần Thông tin): câu hỏi / lựa chọn là bản sao của đề / lời thoại; key_info khuôn C
    (hoặc Thông tin chỉ tiếng Nhật) là bản sao dòng thoại → không tính furigana 2 lần."""
    out = [("question", "ja"), ("correct", "option_ja")] + [("options", k, "option_ja") for k in range(len(doc.get("options") or []))]
    if norm["khuon_goc"] == "A" and norm["thong_tin"]["ja"]:
        return out
    return out + [("key_info", k, "ja") for k in range(len(doc.get("key_info") or []))]


def chay_check_vi(doc, norm, cfg_, schema):
    from pipeline_chung.checks_chung import check_vi
    r = check_vi(doc, schema, norm["src_text"], norm["src_vi_text"], norm, cfg_["kiem_tra"], strip_labels,
                 marks_src=[], furi_src_text=norm["src_text_furi"], furi_skip=furi_skip(doc, norm))
    k_loi, k_cb = check_k(doc, norm, cfg_["chinh_sach"])
    r["loi"] += k_loi
    r["canh_bao"] += k_cb
    return r


def bo_sung(doc, norm):
    """Hook --nhan GĐ1: bỏ reference_raw (schema reading_listening không có); key_info chưa có nghĩa (Thông tin chỉ tiếng Nhật /
    khuôn C) → chép meaning của dòng thoại có cùng câu tiếng Nhật (Q3)."""
    doc.pop("reference_raw", None)
    lines = [ln for _, _, ln in _lines(doc)]
    for x in doc.get("key_info") or []:
        if x.get("meaning") is None:
            k = _n(bo_i(x.get("ja")))
            ln = next((l for l in lines if l.get("meaning") and _n(bo_i(l.get("ja"))) == k), None)
            if ln:
                x["meaning"] = {"vi": bo_i(ln["meaning"]["vi"])}
    return doc


# ---------------- gợi ý cho tác tử KIỂM TRA ----------------
def han_viet_src(norm):
    t = norm.get("src_vi_text") or ""
    return [m.group(0) for m in re.finditer(r"âm\s*h[áa]n\s*vi[ệe]t[^\n]{0,30}", t, re.I)]


_UP = "A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬĐÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ"
_LO = "a-zàáảãạăằắẳẵặâầấẩẫậđèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ"
FORMAT_HINT_RES = [
    ("dính câu", re.compile(rf"[{_LO}][.?!][{_UP}][{_LO}]")),
    ("lặp từ", re.compile(rf"(?i)\b([{_LO}]{{2,}})\s+\1\b")),
    ("dấu câu thừa", re.compile(r"[ \t][,.;:](?=\s|$)|,[ \t]*\)|\([ \t]+[,.]")),
    ("ký tự lạ", re.compile(r"\?\?|�")),
]


def format_hints(norm):
    t = norm.get("src_vi_text") or ""
    out = []
    for name, rx in FORMAT_HINT_RES:
        for m in rx.finditer(t):
            out.append(f"{name}: …{t[max(0, m.start() - 15):m.end() + 15].replace(chr(10), '⏎')}…")
    return out[:12]


def goi_y(norm):
    """Gợi ý ngắn cho tác tử KIỂM TRA (đặt trong gd1_danh_sach)."""
    out = [f"[Định dạng] {x}" for x in format_hints(norm)]
    if norm.get("in_dam"):
        out.append(f"[In đậm – gợi ý dòng then chốt] {norm['in_dam'][:3]}")
    return out


# ---------------- GĐ2 ----------------
def is_style_field(path):
    """Chỉ phần lý do (options[*].analysis – dịch từ tiếng Việt) dùng văn phong -습니다; lời thoại / câu hỏi / lựa chọn theo câu Nhật."""
    p = path if isinstance(path, str) else path_str(path)
    return bool(re.search(r"\.analysis", p))


def check_d(doc_ko, gloss, lang="ko"):
    from pipeline_chung.dich import key_norm
    loi = []
    fixed = {key_norm(k): v for k, v in gloss["cau_co_dinh"].items()}
    for fp, o in iter_lang_fields(doc_ko):
        k = key_norm(o["vi"])
        if k in fixed and o.get(lang) != fixed[k]:
            loi.append(f"D1: {path_str(fp)}: câu cố định phải dịch là '{fixed[k]}'")
    return loi, []


# ---------------- hiển thị (Excel CTV) ----------------
def _t(obj, lang):
    return show((obj or {}).get(lang) or "") if obj else ""


def loi_thoai_text(norm):
    """Lời thoại tiếng Nhật cho cột 'Ngữ liệu'."""
    return "\n".join((f"{t['speaker']}: " if t["speaker"] else "") + show(t["ja"]) for t in norm.get("luot") or [])


def render(d, lang):
    out = [bold("【Lời thoại】")]
    ki = {_n(bo_i(x.get("ja"))) for x in d.get("key_info") or []}
    for _, _, ln in _lines(d):
        sp = f"{ln['speaker']}: " if ln.get("speaker") else ""
        ja = show(ln.get("ja") or "")
        out.append(bold(sp + ja) if _n(bo_i(ln.get("ja"))) in ki else sp + ja)
        if ln.get("meaning"):
            out.append("   → " + _t(ln["meaning"], lang))
    q = d.get("question") or {}
    out.append(f"{bold('【Câu hỏi】')} {show(q.get('ja') or '')}")
    if q.get("meaning"):
        out.append("   → " + _t(q["meaning"], lang))
    out.append(bold("【Lựa chọn】"))
    for o in d.get("options") or []:
        dau = "✔ " if o.get("is_match") else ""
        out.append(f"{dau}{o.get('index')}. {show(o.get('option_ja') or '')}" + (f" – {_t(o['meaning'], lang)}" if o.get("meaning") else ""))
        if o.get("analysis"):
            out.append("   " + _t(o["analysis"], lang).replace("\n", "\n   "))
    if d.get("key_info"):
        out.append(bold("【Thông tin】"))
        for x in d["key_info"]:
            out.append((f"{x['speaker']}: " if x.get("speaker") else "") + show(x.get("ja") or ""))
            if x.get("meaning"):
                out.append("   → " + _t(x["meaning"], lang))
    c = d.get("correct") or {}
    out.append(f"{bold('【Đáp án】')} {c.get('index')}. {show(c.get('option_ja') or '')}")
    return "\n".join(out)
