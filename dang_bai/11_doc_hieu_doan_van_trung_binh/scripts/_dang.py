"""Phần riêng của dạng 11 – Đọc hiểu: Đoạn văn trung bình (dựng 2026-10-08 từ khung dạng 08/09, chạy hoàn toàn bằng Claude Opus 5.5 Cowork).

Phần chung kế thừa dạng 07/08 (cấu hình, đường dẫn, thứ tự chạy --tu/--den, kho đã duyệt, bản tạo Claude, Sudachi, Hán Việt, gợi ý định dạng).
Phần riêng 11 ở cuối file: chuẩn hóa đoạn văn, tách lời giải (câu hỏi + dịch → 4 lựa chọn: Nghĩa / trích dẫn 「…」 + (dịch) / phân tích / → ĐÚNG|SAI),
phân loại khuôn (chuẩn / lạ), dò trích dẫn trong đoạn văn (K-TD), thứ tự chạy theo ĐOẠN VĂN (lô 3–4 đoạn ≈ 10 câu),
gắn cờ, kiểm tra K, hiển thị Excel. Các script s0…s3 đều import file này.
"""
import collections  # noqa: F401
import json
import os
import re
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
    os.environ["PIPELINE_DATA"] = _c.get("du_lieu_test", "data/test_11_doc_hieu_doan_van_trung_binh.csv")


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


def thu_tu():
    """Thứ tự chạy --tu/--den: output/thu_tu_chay.csv (do s0_chuan_bi tạo – 100 câu đầu chia đều N1–N5) nếu có, không thì theo file dữ liệu."""
    from pipeline_chung.common import read_csv
    p = OUT("thu_tu_chay.csv")
    if os.path.exists(p):
        return [r["sample_id"] for r in read_csv(p)]
    return [sid_of(r) for r in read_csv(data_path())]


def mau_ngoai_jlpt():
    """Các mẫu bị loại theo config.loc_nguon_de (quyết định 2026-10-11): từ stt tu_mau theo THỨ TỰ CHẠY (thu_tu() =
    output/thu_tu_chay.csv), bỏ mẫu mà cột `cot` (thi_thu_thuoc_de, tra theo sample_id trong file dữ liệu) chứa một
    trong `bo_neu_chua` (mặc định 'Nat Test'). Trả về {sample_id: giá trị cột}."""
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




# ---------------- chuẩn hóa thêm (giai đoạn 0) ----------------
FURI_VI_RE = re.compile(r"｜([^｜《》\n]*?[A-Za-zÀ-ỹĐđ][^｜《》\n]*?)《([^》\n]*)》")


def bo_furigana_chu_viet(text):
    """Bỏ furigana gắn lên chữ tiếng Việt / Latin (vd '- ｜Nhận xét《にんてい》:') – lỗi định dạng bản gốc.
    Trả (text, [(cũ, mới)])."""
    doi = []
    def _r(m):
        doi.append((m.group(0), m.group(1)))
        return m.group(1)
    return FURI_VI_RE.sub(_r, text), doi



# ---------------- tiện ích kiểm tra ----------------
def _segs(s):
    from pipeline_chung.normalize import mark_segments
    return mark_segments(s)


def _v(o):
    return (o or {}).get("vi") if o else None


def _k(t):
    return re.sub(r"[\s　]", "", norm_ja(t or ""))


def _cover(src_text, out_text):
    from pipeline_chung.common import vi_words
    s, o = collections.Counter(vi_words(src_text or "")), collections.Counter(vi_words(out_text or ""))
    if not s:
        return 1.0, []
    return sum((s & o).values()) / sum(s.values()), [w for w, _ in (s - o).most_common(8)]


# ---------------- kiểm tra riêng giai đoạn 2: D1 ----------------
def check_d(doc_ko, gloss, lang="ko"):
    from pipeline_chung.dich import key_norm
    loi, canh_bao = [], []
    fixed = {key_norm(k): v for k, v in gloss["cau_co_dinh"].items()}
    for fp, o in iter_lang_fields(doc_ko):
        k = key_norm(o["vi"])
        if k in fixed and o.get(lang) != fixed[k]:
            loi.append(f"D1: {path_str(fp)}: câu cố định phải dịch là '{fixed[k]}'")
    return loi, canh_bao


# ---------------- hiển thị cho Excel CTV (dựng lại đúng thứ tự format) ----------------
def _t(obj, lang):
    return show((obj or {}).get(lang) or "") if obj else ""


# ---------------- Cách chia v2: cờ âm Hán Việt trong lời giải gốc ----------------
_UP = "A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬĐÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ"
_HV_WORD = rf"[{_UP}]{{2,}}(?:\s+[{_UP}]{{2,}})*"
HV_SRC_RES = [
    re.compile(r"âm\s*h[áa]n\s*vi[ệe]t[^\n]{0,30}", re.I),                                   # "âm hán việt là THÁN"
    re.compile(rf"ch[ữu]\s*h[áa]n\s*[\"'「]?[㐀-鿿]?[\"'」]?\s*,?\s*({_HV_WORD})\b"),   # "chữ hán NÃO"
    re.compile(rf"[㐀-鿿](?:\s*[（(][^)）\n]{{0,15}}[)）])?\s*[-–—:]\s*({_HV_WORD})\b"),  # "選 (せん) - TUYỂN"
    re.compile(rf"\bch[ữu]\s+({_HV_WORD})\b"),                                          # "chữ TRỊ" (không có chữ 'hán')
]
HV_BO_QUA = {"VD", "JLPT", "TV", "OK", "DVD", "CD", "PC", "USB", "NHK", "JR", "II", "III", "IV", "SNS", "IT", "AI", "N1", "N2"}


def han_viet_src(norm):
    """Dò âm Hán Việt trong lời giải gốc (cách chia v2: câu có âm Hán Việt KHÔNG được dịch).
    Trả về danh sách đoạn tìm thấy (rỗng = không có)."""
    t = norm.get("src_text") or ""
    out = []
    for i, rx in enumerate(HV_SRC_RES):
        for m in rx.finditer(t):
            word = m.group(1) if m.groups() else ""
            if i > 0 and (not word or word.strip() in HV_BO_QUA):
                continue
            s = t[max(0, m.start() - 8):m.end()].replace("\n", " ").strip()
            if s not in out:
                out.append(s)
    return out


# ---------------- Cách chia v2: gợi ý lỗi định dạng (Python dò, Claude xác nhận và sửa) ----------------
_LO = "a-zàáảãạăằắẳẵặâầấẩẫậđèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ"
FORMAT_HINT_RES = [
    ("dính câu", re.compile(rf"[{_LO}\)\]\"”'’.。:：][{_UP}][{_LO}]")),            # "phía sauMột", ")Ví dụ", "…'.Phân biệt"
    ("dính mục đánh số", re.compile(r"[^\s\d][.。][ \t]?\d{1,2}[.．][ \t]")),            # "…từ bỏ\".3. 物"
    ("lặp từ", re.compile(rf"(?i)\b([{_LO}]{{2,}})\s+\1\b")),                        # "này này", "chữ chữ"
    ("dấu câu thừa", re.compile(r"[ \t][,.;:](?=\s|$)|,[ \t]*\)|\([ \t]+[,.]")),  # " ,"  ", )"  ('..' thay cho '...' là cách viết của bản gốc – không tính)
]


FURI_LECH_RE = re.compile(r"｜([぀-ゟ]+)([㐀-鿿々]+)《([^》]*)》")


def format_hints(norm):
    """Các chỗ nghi lỗi định dạng trong lời giải gốc (chỉ là gợi ý cho Claude, không quyết định trạng thái)."""
    t = norm.get("src_text") or ""
    out = []
    for name, rx in FORMAT_HINT_RES:
        for m in rx.finditer(t):
            out.append(f"{name}: …{t[max(0, m.start() - 15):m.end() + 15].replace(chr(10), '⏎')}…")
    # dạng 06: furigana phủ cả phần kana đứng trước chữ Hán ('｜はかる必要《ひつよう》' → 'はかる｜必要《ひつよう》')
    for m in FURI_LECH_RE.finditer(t):
        if not _hira(m.group(3)).startswith(m.group(1)):
            out.append(f"furigana lệch phạm vi: '{m.group(0)}' → nên là '{m.group(1)}｜{m.group(2)}《{m.group(3)}》'")
    return out[:12]


# ---------------- Dạng 07: gợi ý từ điển SudachiPy (R1) + so câu theo cách đọc – chỉ GỢI Ý cho Claude, không quyết định trạng thái ----------------
_TOK = None


def _tok():
    """Tokenizer SudachiPy (từ điển core); không cài thư viện thì trả về False (bỏ qua gợi ý)."""
    global _TOK
    if _TOK is None:
        try:
            from sudachipy import Dictionary
            d = Dictionary(dict=(cfg().get("sudachi") or {}).get("dict", "core"))
            _TOK = d.tokenizer() if hasattr(d, "tokenizer") else d.create()
        except Exception:                                          # noqa: BLE001
            _TOK = False
    return _TOK


def _hira(s):
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s or "")


def tra_tu(word):
    """→ {'tu': bool (từ điển có nguyên chuỗi là MỘT từ), 'doc': cách đọc hiragana, 'tach': [các mảnh]} hoặc None nếu không có thư viện."""
    t = _tok()
    if not t:
        return None
    from sudachipy import SplitMode
    w = re.sub(r"[。．.、\s　]", "", strip_marks(word or ""))
    if not w:
        return None
    ms = list(t.tokenize(w, SplitMode.C))
    rieng = len(ms) == 1 and ms[0].part_of_speech()[1] == "固有名詞"      # tên riêng (người, địa danh) – không tính là "có từ"
    return {"tu": len(ms) == 1 and not ms[0].is_oov() and not rieng, "doc": _hira("".join(m.reading_form() for m in ms)),
            "tach": [m.surface() for m in ms]}


def _yomi(t):
    """Cách đọc (hiragana) của cả câu – bỏ furigana, { }, khoảng trắng, dấu câu (để so câu viết kana / kanji khác nhau)."""
    from sudachipy import SplitMode
    t = re.sub(r"[\s　。．.、，,｡､･·「」『』！？!?・…\-－―〜~:：]", "", strip_marks(t or "").replace("{", "").replace("}", ""))
    return _hira("".join(m.reading_form() for m in _tok().tokenize(t, SplitMode.C))) if t else ""


_DAKU = str.maketrans("がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ", "かきくけこさしすせそたちつてとはひふへほはひふへほ")


def _seion(s):
    """Bỏ biến âm (rendaku) để so cách đọc: ぶかく ~ ふかく, ばなれ ~ はなれ."""
    return _hira(s or "").translate(_DAKU).replace("っ", "つ")


def _yomi_kana(s):
    """Dòng 'Cách đọc:' → hiragana liền, bỏ dấu câu / khoảng trắng / furigana / { }."""
    s = strip_marks(s or "").replace("{", "").replace("}", "")
    return _hira(re.sub(r"[\s　。．.、，,｡､･·「」『』！？!?・…\-－―〜~:：()（）]", "", s))


def _tu_loi(word):
    """Phần cốt của từ được hỏi để dò trong câu: chữ Hán liền đầu (細心, 許) hoặc kana bỏ đuôi chia (はかる → はか, わざわざ)."""
    w = strip_marks(word or "")
    k = re.match(r"[㐀-鿿々]+", w)
    if k:
        return k.group(0)
    w = re.sub(r"[るうくすつぬぶむぐいだな]$", "", w) if len(w) >= 3 else w
    return w


def _khac(a, b):
    """Các đoạn khác nhau giữa hai chuỗi: [(cũ, mới)]."""
    import difflib
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    return [(a[i1:i2], b[j1:j2]) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal"]


# =====================================================================================================
# ================  DẠNG 11 – ĐỌC HIỂU: ĐOẠN VĂN TRUNG BÌNH – phần riêng (dựng 2026-10-08)  ==========
# =====================================================================================================
# Lời giải gốc (HTML, 91% khuôn chuẩn – sau chuẩn hóa):
#   <câu hỏi tiếng Nhật (có furigana)>                                  → question.ja
#   <dịch câu hỏi>                                                       → question.meaning
#   i. <lựa chọn tiếng Nhật (có furigana)>                               → options[i].option_ja
#   Nghĩa: …                                                             → options[i].meaning
#   [Trích dẫn: / 引用: / - Đoạn văn có câu: …]  「câu trích」 (dịch)     → options[i].quotes[] = {ja, meaning}
#   <nhận xét>                                                           → options[i].analysis
#   → ĐÚNG. / → SAI.                                                     → options[i].is_match
# Không có BẢN DỊCH ĐẦY ĐỦ / TÓM TẮT / Thông tin → full_translation = summary = key_info = null (trừ khuôn lạ có bản dịch đoạn văn).
# Khuôn lạ (~9%): chỉ dịch đoạn văn + "Câu trả lời đúng là…", vài câu giải thích, markdown ### → cờ khuon_la (tác tử KIỂM TRA gắn thieu_noi_dung).

VI_DAU_RE = re.compile(r"[ăâđêôơưàáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ]", re.I)
JA_CH_RE = re.compile(r"[぀-ヿ㐀-䶿一-鿿ｦ-ﾟ々〆ヶ]")
OPT_RE = re.compile(r"^\s*\{?\s*([1-4１-４])\s*\}?\s*[\.．、:：)）]\s*(.*)$")
NGHIA_RE = re.compile(r"(?i)^\s*[-•]?\s*\{?\s*(nghĩa|dịch|意味)\s*\}?\s*[:：]\s*(.*)$")
KET_LUAN_RE = re.compile(r"^\s*[-•]?\s*(?:→|=>|⇒|->|➡|➔)\s*\{?\s*(ĐÚNG|SAI|Đúng|Sai)\b\s*\}?\s*\.?\s*(.*)$")
KET_LUAN_TOKEN_RE = re.compile(r"(?:→|=>|⇒|->|➡|➔)\s*\{?\s*(?:ĐÚNG|SAI|Đúng|Sai)\b\s*\}?\s*\.?")
# nhãn tiếng Nhật đầu dòng (引用: / 解説: …) – nhãn trình bày, không phải nội dung → bỏ khỏi chuẩn kiểm tra (furigana / mất tiếng Nhật)
NHAN_NHAT_RE = re.compile(r"(?m)^([ \t]*[-•]?[ \t]*)(?:｜(?:引用|解説|意味|解釈|説明|分析)《[^》\n]*》|引用|解\s?説|意味|解釈|説明|分析)[ \t]*[:：][ \t]*")
# dòng dẫn vào câu trích (chỉ giới thiệu câu trích – tác tử TẠO bỏ, Python bỏ khi đo độ phủ)
_DAN_TRICH = (
    r"(?:câu\s+)?tr[íi]ch\w*\s*d[ẫa]n(?:\s+(?:câu|từ|đoạn|liên quan|trong)[^:：\n]{0,30})?"
    r"|c[âa]u\s+(?:trong\s+(?:đoạn văn|bài(?: đọc)?)|gốc|liên quan(?: trong đoạn văn)?|thoại liên quan|trích)"
    r"|(?:ngoài ra,?\s*)?(?:trong\s+)?(?:đoạn văn|bài(?: đọc)?|đoạn hội thoại)(?:,)?\s*(?:cũng|còn)?\s*(?:có\s+)?(?:câu|nói(?: rõ)?|viết|đề cập|có nói(?: rõ)?|kết luận(?: như sau)?)"
    r"|(?:ngoài ra,?\s*)?(?:còn\s+)?có\s+câu|và(?: tiếp theo)?|tríchdẫntrích dẫn|ghép vào câu"
    r"|｜?(?:引用|解\s?説|意味|解釈|説明|分析)(?:《[^》\n]*》)?")
DAN_TRICH_RE = re.compile(r"(?im)^[ \t]*[-•]?[ \t]*(?:" + _DAN_TRICH + r")[ \t]*[:：][ \t]*$")
DAN_TRICH_DAU_RE = re.compile(r"(?i)^[ \t]*[-•]?[ \t]*(?:" + _DAN_TRICH + r")[ \t]*[:：][ \t]*(?=[「『])")    # nhãn dẫn + câu trích cùng dòng
# 2026-10-10 (11693_1): cho phép "(" trước nhãn – dòng dịch dạng "(Nghĩa: …)"
NHAN_TIEN_TO_RE = re.compile(r"(?im)^([ \t]*[-•(（]?[ \t]*)(?:nghĩa|dịch|bản dịch|giải thích|phân tích|câu hỏi|(?:câu\s+)?tr[íi]ch\w*\s*d[ẫa]n[^:：\n]{0,25})[ \t]*[:：]")
QUOTE_RE = re.compile(r"[「『]((?:[^「」『』]|[「『][^「」『』]*[」』])*)[」』]")
PHU_DINH_RE = re.compile(r"ないもの|ないのは(?:次の)?どれ|ないのはどちら|違うもの|違っているもの|合わない|合っていない|正しくない|ただしくない|"
                         r"間違って|間違い|ではないもの|でないもの|当てはまらない|あてはまらない|合致しない|述べていない|一致しない")


def de_html(html):
    """Đề / đoạn văn: bỏ ký tự điều khiển lạc, thẻ cụt ở cuối (kế thừa dạng 06/09)."""
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", html or "")
    return re.sub(r"</?[a-zA-Z]*$", "", s.rstrip())


def plain(html):
    """Chuẩn hóa và bỏ { } (đề / lựa chọn)."""
    from pipeline_chung.normalize import normalize_html
    t, b = normalize_html(de_html(html))
    return t.replace("{", "").replace("}", ""), b


def chuan_doan_van(html):
    """Đoạn văn (chung cho các câu con): chuẩn hóa HTML, giữ ①②③ và { } (chỗ được hỏi in đậm)."""
    from pipeline_chung.normalize import normalize_html
    return normalize_html(de_html(html))[0]


def ja_line(s):
    """Dòng chủ yếu là tiếng Nhật (không có dấu tiếng Việt)."""
    t = strip_marks(s or "")
    if VI_DAU_RE.search(t):
        return False
    j = len(JA_CH_RE.findall(t))
    return j >= 1 and j >= len(re.findall(r"[A-Za-z]", t))


def bo_dam_nhan(text):
    """'{Đoạn văn:}', '{Câu hỏi:}' (nhãn in đậm đứng riêng dòng) → bỏ { }. Trả (text, số chỗ)."""
    return re.subn(r"(?m)^([ \t]*)\{([^{}\n]{1,40}[:：])\}[ \t]*$", r"\1\2", text)


def bo_nhan_nhat(text):
    """Chuẩn kiểm tra: bỏ nhãn tiếng Nhật đầu dòng (引用: / 解説: …) – tác tử TẠO không chép nhãn."""
    t = NHAN_NHAT_RE.sub(r"\1", text or "")
    t = re.sub(r"Phân\s?析", "Phân tích", t)      # nhãn 'Phân tích:' hỏng thành 'Phân析:' – 193_3 (2026-10-08)
    # dòng tiếng Nhật lặp lại câu hỏi (đầu lời giải, viết "…" thay 「…」) – tác tử TẠO không chép bản lặp – 193_2 (2026-10-08)
    lines = t.split("\n")
    def _q(x):
        return re.sub(r"[「」『』\"“”\s　]", "", x)
    if lines and _q(lines[0]):
        q0, out = _q(lines[0]), [lines[0]]
        for i, ln in enumerate(lines[1:], 1):
            if i <= 4 and _q(ln) == q0:
                continue
            out.append(ln)
        t = "\n".join(out)
    return t


def strip_labels(text):
    """Bỏ nhãn cố định khi đo độ phủ chữ tiếng Việt: dòng dẫn vào câu trích, '→ ĐÚNG/SAI', tiền tố 'Nghĩa:', 'Trích dẫn:', 'Giải thích:'…"""
    text = DAN_TRICH_RE.sub(" ", text or "")
    text = KET_LUAN_TOKEN_RE.sub(" ", text)
    text = NHAN_TIEN_TO_RE.sub(r"\1 ", text)
    # chữ Latin hoa đứng riêng dính chữ Nhật trên dòng tiếng Nhật (Aさん, B社…) không phải từ Việt – 13519_2/_3 (2026-10-08)
    text = LATIN_DINH_NHAT_RE.sub(" ", text)
    return text


# 2026-10-10 (261_2): cho phép dấu hai chấm / khoảng trắng / ⟪ giữa chữ hoa và chữ Nhật (A と B は, A:｜冷蔵庫, A: ⟪…⟫)
LATIN_DINH_NHAT_RE = re.compile(r"(?<![A-Za-zÀ-ỹđĐ])[A-ZＡ-Ｚ](?=[:：]?[ 　]*[⟪｜\u3040-\u30ff\u3400-\u9fff])")


def text_without_ref(text):
    """Dạng 11 không có phần THAM KHẢO (khảo sát 2026-10-08: 'Tham khảo:' duy nhất ở 55282_2 là câu trích đoạn văn – nội dung)."""
    return text


def _k11(s):
    """Chuẩn hóa để so câu Nhật: bỏ furigana / ký hiệu / dấu câu / khoảng trắng; số toàn góc → ASCII."""
    s = norm_ja(strip_marks(s or "").replace("{", "").replace("}", ""))
    s = re.sub(r"[\s　。．.、，,「」『』（）()!?！？…・\-~〜\"“”'’:：;；]", "", s)
    return s.translate(str.maketrans("０１２３４５６７８９ＡＢＣＤ", "0123456789ABCD"))


def giong(a, b):
    import difflib
    a, b = _k11(a), _k11(b)
    if not a or not b:
        return 0.0
    return 1.0 if a == b else difflib.SequenceMatcher(a=a, b=b, autojunk=False).ratio()


def _dv(s):
    """Chuẩn hóa để dò câu trích trong đoạn văn: như _k11 + bỏ 注n, số khoanh ①…⑳, cách đọc trong ngoặc."""
    s = re.sub(r"注\s*[0-9０-９]+", "", strip_marks(s or ""))
    s = re.sub(r"[（(][぀-ゟ゠-ヿー]+[)）]", "", s)
    s = re.sub(r"[①-⑳]", "", s)
    return _k11(s)


def so_doan_van(quote, doan_van):
    """Câu trích ↔ đoạn văn → 'khop' (mọi mảnh có nguyên văn) | 'mot_phan' (đầu / cuối mảnh có) | 'khong'."""
    dv = _dv(doan_van)
    if not dv:
        return "khong_co_doan"
    manh = [_dv(x) for x in re.split(r"…+|\.{3,}|・・・|（略）|\(略\)", quote or "")]
    manh = [m for m in manh if len(m) >= 4]
    if not manh:
        return "khop"
    if all(m in dv for m in manh):
        return "khop"
    if any(m[:8] in dv or m[-8:] in dv for m in manh):
        return "mot_phan"
    return "khong"


def trich_trong(s):
    """Các câu trích 「…」 tiếng Nhật trong một dòng (≥ 6 chữ, không có chữ Việt)."""
    out = []
    for m in QUOTE_RE.finditer(s or ""):
        q = m.group(1)
        if ja_line(q) and len(_k11(q)) >= 6:
            out.append(q)
    return out


def parse_loi_giai(text, lua_chon, dap):
    """Tách lời giải (đã chuẩn hóa) → {dau: {cau, dich}, lua_chon: [...], so_lua_chon}.
    Dòng tiêu đề lựa chọn: 'i. <tiếng Nhật>' theo thứ tự 1→4 (không cần khớp chữ với đề – lời giải hay viết khác đề)."""
    L = (text or "").split("\n")
    hs, want = [], 1
    for i, line in enumerate(L):
        m = OPT_RE.match(line)
        if not m:
            continue
        n = int(m.group(1).translate(str.maketrans("１２３４", "1234")))
        rest = m.group(2)
        if n == want and rest.strip() and not VI_DAU_RE.search(strip_marks(rest)) and \
                (ja_line(rest) or giong(rest, lua_chon[n - 1]) >= 0.6):
            hs.append(i)
            want += 1
            if want > 4:
                break
    so_cua = list(range(1, len(hs) + 1))
    if len(hs) < 4:      # lời giải giải thích lựa chọn KHÁC thứ tự (vd 2-1-3-4 – 298_2): nhận khi tìm đủ 4 dòng, mỗi số một lần, khớp đề
        hs2, seen = [], set()
        for i, line in enumerate(L):
            m = OPT_RE.match(line)
            if not m:
                continue
            n = int(m.group(1).translate(str.maketrans("１２３４", "1234")))
            rest = m.group(2)
            if 1 <= n <= 4 and n not in seen and rest.strip() and not VI_DAU_RE.search(strip_marks(rest)) and \
                    giong(rest, lua_chon[n - 1]) >= 0.6:
                hs2.append((i, n))
                seen.add(n)
        if len(hs2) == 4:
            hs, so_cua = [i for i, _ in hs2], [n for _, n in hs2]
    dau = [x.strip() for x in (L[:hs[0]] if hs else L) if x.strip()]
    for k, x in enumerate(dau):          # khối lựa chọn thừa trước khối 1 (vd '2. ことば' – 330_2) không phải phần câu hỏi
        mo = OPT_RE.match(x)
        if len(hs) == 4 and k and mo and mo.group(1) in "1234１２３４" and \
                giong(mo.group(2), lua_chon[int(mo.group(1).translate(str.maketrans("１２３４", "1234"))) - 1]) >= 0.6:
            dau = dau[:k]
            break
    ky_hieu = lambda x: re.fullmatch(r"[\u2460-\u2473\u30a2-\u30f3（）()\s]+", x) is not None   # dòng chỉ là ①② / ア イ
    cau = [x for x in dau if ja_line(x) or ky_hieu(x)]
    dich = [x for x in dau if not (ja_line(x) or ky_hieu(x))]
    items = []
    for j, i in enumerate(hs):
        end = hs[j + 1] if j + 1 < len(hs) else len(L)
        n = so_cua[j]
        it = {"so": n, "dong": OPT_RE.match(L[i]).group(2).strip(), "nghia": None, "ket_luan": None, "sau_ket_luan": [],
              "trich": [], "trich_rieng": [], "dong_vi": []}
        it["giong_de"] = round(giong(it["dong"], lua_chon[n - 1]), 2)
        for line in L[i + 1:end]:
            s = line.strip()
            if not s:
                continue
            mn = NGHIA_RE.match(s)
            if mn and it["nghia"] is None and not it["trich"] and not it["dong_vi"]:
                it["nghia"] = mn.group(2).strip()
                continue
            mk = KET_LUAN_RE.match(s)
            if mk:
                it["ket_luan"] = "ĐÚNG" if mk.group(1).upper() == "ĐÚNG" else "SAI"
                if mk.group(2).strip():
                    it["sau_ket_luan"].append(mk.group(2).strip())
                continue
            q = trich_trong(s)
            if q:
                it["trich"] += q
                if (re.fullmatch(r"[「『].*[」』][。.]?", s) and ja_line(s)) or DAN_TRICH_DAU_RE.match(s):
                    it["trich_rieng"] += q          # câu trích đứng riêng / sau nhãn dẫn → quotes (dùng cho K-TR)
            if not ja_line(s):
                it["dong_vi"].append(s)
        items.append(it)
    items.sort(key=lambda it: it["so"])
    return {"dau": {"cau": "\n".join(cau) or None, "dich": "\n".join(dich) or None}, "lua_chon": items, "so_lua_chon": len(hs)}


def khuon_la(text):
    """Phân loại khuôn lạ (không đủ 4 lựa chọn): dịch đoạn văn / markdown / ngắn / khác."""
    if re.search(r"(?im)^\s*\{?\s*Đoạn văn\s*:?\s*\}?\s*:?\s*$", text) or "Câu trả lời đúng là" in text:
        return "dich_doan_van"
    if re.search(r"(?m)^\s*#{2,}|\*\*", text):
        return "markdown"
    if len(strip_marks(text)) < 800:
        return "ngan"
    return "khac"


FLAG_TEXT = {
    "khuon_la": "Lời giải KHÔNG theo khuôn chuẩn (không đủ phân tích 4 lựa chọn) – chép phần có được, trường thiếu null / [], gắn cờ thieu_noi_dung",
    "khuon_dich_doan_van": "Khuôn lạ: lời giải chủ yếu là bản dịch đoạn văn + 'Câu trả lời đúng là…' (bản dịch đoạn văn → full_translation)",
    "khuon_markdown": "Khuôn lạ: lời giải viết kiểu markdown (###, **, >)",
    "khuon_ngan": "Khuôn lạ: lời giải chỉ vài câu giải thích",
    "khuon_khac": "Khuôn lạ: khác",
    "thieu_cau_hoi": "Phần đầu lời giải không có dòng câu hỏi tiếng Nhật (question.ja chép câu hỏi của đề)",
    "thieu_dich_cau_hoi": "Phần đầu lời giải không có bản dịch câu hỏi (question.meaning = null)",
    "cau_hoi_lech": "Câu hỏi trong lời giải viết khác câu hỏi của đề – thường chỉ khác cách viết kana / kanji (question.ja vẫn chép theo lời giải; khác nội dung thật → cờ khac)",
    "lua_chon_lech": "Có dòng lựa chọn trong lời giải viết khác lựa chọn của đề – thường chỉ khác cách viết (option_ja vẫn chép theo lời giải; khác nội dung thật → cờ khac)",
    "thieu_nghia_lua_chon": "Có lựa chọn không có dòng 'Nghĩa:' (meaning = null)",
    "thieu_ket_luan": "Có lựa chọn không có kết luận '→ ĐÚNG / → SAI' (is_match theo đáp án của đề)",
    "co_sau_ket_luan": "Có câu chữ sau '→ ĐÚNG / SAI' trên cùng dòng (chép vào cuối analysis)",
    "cau_hoi_phu_dinh": "Câu hỏi phủ định (…ないもの / 合わない / 正しくない …): '→ ĐÚNG' có thể nghĩa là 'phù hợp đoạn văn' (không phải đáp án)",
    "ket_luan_lech_dap_an": "Kết luận ĐÚNG / SAI của lời giải không khớp đáp án của đề (nghi lỗi nội dung → cờ dap_an)",
    "nhieu_dung": "Lời giải kết luận '→ ĐÚNG' cho nhiều lựa chọn (câu hỏi không phủ định)",
    "co_trich_dan": "Có câu trích dẫn 「…」",
    "trich_mot_phan": "Có câu trích chỉ khớp một phần đoạn văn (lược bớt / gõ khác – xem K-TD)",
    "trich_ngoai_doan": "Có câu trích KHÔNG tìm thấy trong đoạn văn (nghi trích sai / bịa → xem kỹ, cờ trich_dan nếu sai thật)",
    "chen_tu_nhat": "Câu tiếng Việt có chen từ tiếng Nhật (bọc ⟪ ⟫, giữ furigana)",
    "doan_co_anh": "Đoạn văn có hình ảnh (<img>) – CTV xem trên app",
    "doan_co_bang": "Đoạn văn có bảng (<table>)",
    "nhan_in_dam": "Nhãn in đậm đứng riêng dòng ({Đoạn văn:}) – Python bỏ { }",
    "co_furigana": "Có furigana",
    "ruby_hong": "Có ruby hỏng trong bản gốc",
    "ky_hieu_trung": "Bản gốc có sẵn ký hiệu ｜《》",
    "furigana_chu_viet": "Furigana gắn lên chữ tiếng Việt (Python đã bỏ)",
    "danh_dau_rac": "Bản gốc có đoạn in đậm / gạch chân rỗng (đã bỏ thẻ)",
}
CTV_FLAGS = ("khuon_la", "ket_luan_lech_dap_an", "nhieu_dung", "trich_ngoai_doan", "doan_co_anh")
FURI_SKIP = [("correct", "option_ja")]        # correct.option_ja = bản sao options[i].option_ja (lời giải không có mục LỰA CHỌN ĐÚNG)


def parse_and_flag(text, lua_chon, dap_an_so, cau_hoi, doan_van, doan_van_html=""):
    """Tách lời giải + gắn cờ + ghi chú bản gốc. Trả (phan, co, ghi_chu)."""
    dap = int(dap_an_so) if str(dap_an_so).strip() in ("1", "2", "3", "4") else None
    ph = parse_loi_giai(text, lua_chon, dap)
    co, gc, goi_y = [], [], []
    if ph["so_lua_chon"] != 4:
        k = khuon_la(text)
        co += ["khuon_la", "khuon_" + k]
        gc.append(f"[Bản gốc VI] Lời giải không theo khuôn chuẩn ({FLAG_TEXT['khuon_' + k].split(': ', 1)[-1]}) – không đủ phân tích 4 lựa chọn")
    hd = ph["dau"]
    if not hd["cau"]:
        co.append("thieu_cau_hoi")
    elif ph["so_lua_chon"] == 4 and giong(hd["cau"].split("\n")[0], cau_hoi) < 0.8 and giong(hd["cau"], cau_hoi) < 0.8:
        co.append("cau_hoi_lech")          # thường chỉ khác cách viết kana / kanji – gợi ý, không phải lỗi
    if not hd["dich"]:
        co.append("thieu_dich_cau_hoi")
    phu_dinh = bool(PHU_DINH_RE.search(cau_hoi or ""))
    if phu_dinh:
        co.append("cau_hoi_phu_dinh")
    items = ph["lua_chon"]
    if len(items) == 4:
        for it in items:
            if it["giong_de"] < 0.6:
                co.append("lua_chon_lech")      # gợi ý (thường khác cách viết kana / kanji, số toàn góc…)
                goi_y.append(f"LC: lựa chọn {it['so']} trong lời giải viết khác đề: '{strip_marks(it['dong'])[:50]}' ↔ đề '{lua_chon[it['so'] - 1][:50]}'")
            if it["nghia"] is None:
                co.append("thieu_nghia_lua_chon")
            if it["ket_luan"] is None:
                co.append("thieu_ket_luan")
            if it["sau_ket_luan"]:
                co.append("co_sau_ket_luan")
        kl = [it["ket_luan"] for it in items]
        if all(kl) and dap:
            dung = {it["so"] for it in items if it["ket_luan"] == "ĐÚNG"}
            hop_le = dung == {dap} or (phu_dinh and dung == {1, 2, 3, 4} - {dap})
            if not hop_le:
                co.append("ket_luan_lech_dap_an")
                gc.append(f"[Bản gốc VI] Lời giải kết luận ĐÚNG ở lựa chọn {sorted(dung) or 'không có'} – đáp án của đề là {dap}"
                          + (" (câu hỏi phủ định)" if phu_dinh else ""))
                goi_y.append(f"KL: kết luận ĐÚNG ở {sorted(dung) or '—'} ≠ đáp án {dap}" + (" (câu hỏi phủ định)" if phu_dinh else "") + " – xem có phải lỗi nội dung (cờ dap_an)")
                if len(dung) > 1 and not phu_dinh:
                    co.append("nhieu_dung")
    # trích dẫn ↔ đoạn văn
    kq_trich = []
    for it in items:
        for q in it["trich"]:
            kq = so_doan_van(q, doan_van)
            kq_trich.append({"so": it["so"], "trich": q, "ket_qua": kq})
            if kq == "khong":
                goi_y.append(f"TD: lựa chọn {it['so']} – câu trích không tìm thấy trong đoạn văn: '{strip_marks(q)[:50]}…'")
    if kq_trich:
        co.append("co_trich_dan")
    if any(x["ket_qua"] == "mot_phan" for x in kq_trich):
        co.append("trich_mot_phan")
    if any(x["ket_qua"] == "khong" for x in kq_trich):
        co.append("trich_ngoai_doan")
    # từ Nhật chen trong câu Việt (ngoài 「」)
    for line in text.split("\n"):
        if VI_DAU_RE.search(line) and JA_CH_RE.search(strip_marks(QUOTE_RE.sub("", line))):
            co.append("chen_tu_nhat")
            break
    if "<img" in (doan_van_html or "").lower():
        co.append("doan_co_anh")
    if "<table" in (doan_van_html or "").lower():
        co.append("doan_co_bang")
    ph.update({"phu_dinh": phu_dinh, "trich_dan": kq_trich, "goi_y_python": goi_y, "tham_khao": None})
    return ph, sorted(set(co)), gc


def opt_vi_src(it):
    """Chữ tiếng Việt của một lựa chọn trong lời giải gốc (để đo độ phủ theo từng lựa chọn)."""
    return "\n".join([it.get("nghia") or ""] + it.get("dong_vi", []) + it.get("sau_ket_luan", []))


def opt_vi_json(o):
    parts = [_v(o.get("meaning")) or "", _v(o.get("analysis")) or ""]
    parts += [_v(q.get("meaning")) or "" for q in o.get("quotes") or []]
    return "\n".join(parts)


# ---------------- kiểm tra riêng giai đoạn 1 (K) ----------------
def check_k(doc, norm, policy):
    loi, canh_bao = [], []
    de, ph = norm["de"], norm.get("phan") or {}
    q, c = doc.get("question") or {}, doc.get("correct") or {}
    opts = doc.get("options") or []
    dap = int(de["dap_an_so"]) if str(de["dap_an_so"]).isdigit() else None
    co = set(norm.get("co") or [])
    # K1 – đủ 4 lựa chọn
    if [o.get("index") for o in opts] != [1, 2, 3, 4]:
        loi.append(f"K1: options phải có đủ 4 lựa chọn theo thứ tự 1–4 (đang có {[o.get('index') for o in opts]})")
    # K6 – đáp án
    if str(c.get("index")) != str(de["dap_an_so"]):
        loi.append(f"K6: correct.index = {c.get('index')} khác dap_an_so = {de['dap_an_so']}")
    di = c.get("index")
    if isinstance(di, int) and 1 <= di <= len(opts) and c.get("option_ja") != opts[di - 1].get("option_ja"):
        loi.append(f"K6: correct.option_ja phải giống hệt options[{di - 1}].option_ja")
    if c.get("full_sentence") is not None:
        loi.append("K6: correct.full_sentence phải là null (dạng 11 không có câu hoàn chỉnh)")
    # K-NULL – trường lời giải dạng 11 không có
    for name in ("summary", "key_info"):
        if doc.get(name) is not None:
            loi.append(f"K-NULL: {name} phải là null (lời giải dạng 11 không có phần này – không tự tạo)")
    if doc.get("full_translation") is not None and "khuon_dich_doan_van" not in co:
        loi.append("K-NULL: full_translation phải là null (chỉ dùng cho khuôn lạ có bản dịch đoạn văn)")
    # K8 – câu hỏi
    hd = ph.get("dau") or {}
    if hd.get("cau") and _k11(q.get("ja")) != _k11(hd["cau"]) and _k11(q.get("ja")) != _k11(hd["cau"].split("\n")[0]):
        canh_bao.append(f"K8: question.ja khác dòng câu hỏi của lời giải '{strip_marks(hd['cau'])[:60]}'")
    if not hd.get("cau") and giong(q.get("ja"), de["cau_hoi"]) < 0.9:
        canh_bao.append("K8: lời giải không có dòng câu hỏi – question.ja nên chép câu hỏi của đề")
    if hd.get("dich") and len(ph.get("lua_chon") or []) == 4:      # khuôn lạ: phần đầu = cả lời giải – không so
        if q.get("meaning") is None:
            loi.append("K8: lời giải có dòng dịch câu hỏi nhưng question.meaning = null")
        else:
            cv, miss = _cover(strip_labels(hd["dich"]), _v(q.get("meaning")))
            if cv < 0.97:
                canh_bao.append(f"K9: question.meaning thiếu chữ so với dòng dịch câu hỏi: {miss}")
    # K2 / K9 / K-KL – từng lựa chọn
    items = {it["so"]: it for it in ph.get("lua_chon") or []}
    chuan = len(items) == 4
    for o in opts:
        i = o.get("index")
        if not isinstance(i, int) or not 1 <= i <= 4:
            continue
        it = items.get(i)
        if it:
            if _k11(o.get("option_ja")) != _k11(it["dong"]):
                canh_bao.append(f"K8: lựa chọn {i}: option_ja '{strip_marks(o.get('option_ja'))[:40]}' khác dòng lựa chọn của lời giải '{strip_marks(it['dong'])[:40]}'")
            if it["nghia"] is not None and o.get("meaning") is None:
                loi.append(f"K12: lựa chọn {i}: lời giải có 'Nghĩa:' nhưng meaning = null")
            if it["nghia"] is None and o.get("meaning") is not None:
                canh_bao.append(f"K12: lựa chọn {i}: lời giải không có 'Nghĩa:' nhưng meaning khác null – xem lại có đặt nhầm câu khác vào không")
            if it["ket_luan"] and o.get("is_match") is not (it["ket_luan"] == "ĐÚNG"):
                loi.append(f"K-KL: lựa chọn {i}: lời giải kết luận '→ {it['ket_luan']}' nhưng is_match = {o.get('is_match')}")
            cv, miss = _cover(strip_labels(opt_vi_src(it)), opt_vi_json(o))
            if cv < 0.97:
                loi.append(f"K9: lựa chọn {i}: thiếu chữ so với phần phân tích lựa chọn này trong lời giải (đặt nhầm lựa chọn / bỏ sót?): {miss}")
            if len(o.get("quotes") or []) != len(it.get("trich_rieng", it["trich"])):
                canh_bao.append(f"K-TR: lựa chọn {i}: JSON có {len(o.get('quotes') or [])} câu trích – lời giải có {len(it.get('trich_rieng', []))} câu 「…」 đứng riêng / sau nhãn dẫn "
                                "(xem tác tử TẠO có tách / gộp / bỏ sót câu trích không)")
        if not (it and it["ket_luan"]) and dap and o.get("is_match") is not (i == dap):
            (canh_bao if chuan else loi).append(f"K-KL: lựa chọn {i}: lời giải không có kết luận – is_match phải = {i == dap} (theo đáp án của đề)")
        if o.get("reading") is not None:
            canh_bao.append(f"K12: lựa chọn {i}: reading khác null – lời giải dạng 11 không có dòng cách đọc lựa chọn")
        for j, qt in enumerate(o.get("quotes") or []):
            if VI_DAU_RE.search(strip_marks(qt.get("ja") or "")):
                loi.append(f"K-TR: options[{i - 1}].quotes[{j}].ja có chữ tiếng Việt – câu trích chỉ gồm tiếng Nhật")
                continue
            kq = so_doan_van(qt.get("ja"), norm.get("doan_van") or "")
            if kq == "khong":
                canh_bao.append(f"K-TD: options[{i - 1}].quotes[{j}] không tìm thấy trong đoạn văn: '{strip_marks(qt.get('ja'))[:50]}' – trích sai / bịa? (cờ trich_dan nếu sai thật)")
    if chuan:
        n_true = [o.get("index") for o in opts if o.get("is_match")]
        if not n_true:
            canh_bao.append("K-KL: không lựa chọn nào is_match = true")
    for x in ph.get("goi_y_python") or []:
        if x.startswith("KL:"):
            canh_bao.append("K-KL (gợi ý): " + x[4:])
    loi += TK.kiem_tra(doc, None)
    return loi, canh_bao


def is_style_field(path):
    """Trường câu văn giải thích (kiểm tra -습니다): chỉ analysis; bỏ nghĩa câu hỏi / lựa chọn / câu trích (dịch câu)."""
    p = path if isinstance(path, str) else path_str(path)
    return bool(re.search(r"\.analysis$", p))


# ---------------- hiển thị cho Excel CTV ----------------
def render(d, lang):
    q, c = d.get("question") or {}, d.get("correct") or {}
    out = [f"{bold('Câu hỏi:')} {show(q.get('ja') or '')}"]
    if q.get("meaning"):
        out.append(f"Nghĩa: {_t(q['meaning'], lang)}")
    for blk in d.get("full_translation") or []:
        out.append(bold("【BẢN DỊCH ĐOẠN VĂN】") + (f" {blk.get('label')}" if blk.get("label") else ""))
        for ln in blk.get("lines") or []:
            if ln.get("ja"):
                out.append(show(ln["ja"]))
            if ln.get("meaning"):
                out.append(_t(ln["meaning"], lang))
    out.append(bold("【PHÂN TÍCH CÁC LỰA CHỌN】"))
    for o in d.get("options", []):
        out.append(bold(f"{o.get('index')}. ") + show(o.get("option_ja", "")))
        if o.get("reading"):
            out.append(f"Cách đọc: {show(o['reading'])}")
        if o.get("meaning"):
            out.append(f"Nghĩa: {_t(o['meaning'], lang)}")
        for qt in o.get("quotes") or []:
            out.append("Trích dẫn: 「" + show(qt.get("ja") or "") + "」")
            if qt.get("meaning"):
                out.append("(" + _t(qt["meaning"], lang) + ")")
        if o.get("analysis"):
            out.append(_t(o["analysis"], lang))
        out.append("→ ĐÚNG." if o.get("is_match") else "→ SAI.")
        out.append("")
    out.append(bold("【LỰA CHỌN ĐÚNG】"))
    out.append(f"{c.get('index')}. {show(c.get('option_ja', ''))}")
    out += TK.render(d, lang, show, bold)
    return "\n".join(out)


def sudachi_hints(norm):
    """Gợi ý cho bước 1.2 (dạng 11 không dùng Sudachi): KL – kết luận lệch đáp án; TD – câu trích không có trong đoạn văn."""
    return list((norm.get("phan") or {}).get("goi_y_python") or [])


# ---------------- thứ tự chạy theo ĐOẠN VĂN ----------------
def tao_thu_tu_doan(recs, cfg):
    """Đoạn đầu = N đoạn ngẫu nhiên mỗi cấp N1–N5 (xen kẽ), rồi các đoạn còn lại theo file dữ liệu; các câu con của một đoạn liền nhau.
    Chia lô: gom đoạn liền nhau đến khi đủ ≥ lo_toi_thieu câu (không vượt lo_toi_da trừ khi một đoạn đã quá) – không cắt đôi đoạn."""
    import random
    tc = cfg.get("thu_tu_chay") or {}
    rng = random.Random(tc.get("seed", 2026))
    n = tc.get("moi_cap_do_doan", 7)
    lo_min, lo_max = tc.get("lo_toi_thieu", 9), tc.get("lo_toi_da", 12)
    nhom, thu_tu_qid = {}, []
    for r in recs:
        if r["question_id"] not in nhom:
            thu_tu_qid.append(r["question_id"])
        nhom.setdefault(r["question_id"], []).append(r)
    for k in nhom:
        nhom[k].sort(key=lambda r: r["cau_con"])
    lv = {}
    for k in ["N1", "N2", "N3", "N4", "N5"]:
        pool = [x for x in thu_tu_qid if nhom[x][0]["cap_do"] == k and all(r["khuon_goc"] != "trong" for r in nhom[x])]
        rng.shuffle(pool)
        lv[k] = pool[:n]
    dau = [lv[k][i] for i in range(n) for k in ["N1", "N2", "N3", "N4", "N5"] if i < len(lv[k])]
    sd = set(dau)
    doan = dau + [x for x in thu_tu_qid if x not in sd]
    rows, lo, dem = [], 1, 0
    for d_i, x in enumerate(doan, 1):
        if dem and (dem >= lo_min or dem + len(nhom[x]) > lo_max):
            lo, dem = lo + 1, 0
        for r in nhom[x]:
            rows.append({"stt": len(rows) + 1, "sample_id": r["sample_id"], "question_id": r["question_id"], "cap_do": r["cap_do"],
                         "doan": d_i, "lo": lo})
        dem += len(nhom[x])
    return rows


# ---------------- gợi ý định dạng: chỉnh cho dạng 11 (bớt báo nhầm) ----------------
FORMAT_HINT_RES = [
    ("dính câu", re.compile(rf"[{_LO}\)\]\.。][{_UP}][{_LO}]")),                    # "phía sauMột", ")Ví dụ" – bỏ trường hợp sau dấu nháy mở ("Bạn…)
    ("dính mục đánh số", re.compile(r"[^\s\d][.。][ \t]?\d{1,2}[.．][ \t]")),
    ("lặp từ", re.compile(rf"(?i)\b([{_LO}]{{2,}})\s+\1\b")),
    ("dấu câu thừa", re.compile(r"[ \t][,.;](?=\s|$)|,[ \t]*\)|\([ \t]+[,.]")),     # bỏ ' :' (nhãn 'Trích dẫn :' – không phải lỗi nội dung)
]
LAP_HOP_LE = {"dần", "chằm", "từ", "ngày", "hỏi", "nhiều", "đâu", "ai", "gì", "người", "nhà", "năm", "tháng", "lần", "rất", "càng",
              "khác", "đều", "mỗi", "nhè", "lâu", "xa", "thường", "chầm", "rõ", "đó"}
_format_hints_chung = format_hints


def format_hints(norm):
    out = []
    for x in _format_hints_chung(norm):
        if x.startswith("lặp từ"):
            m = re.search(rf"(?i)\b([{_LO}]{{2,}})\s+\1\b", x)
            if m and m.group(1).lower() in LAP_HOP_LE:
                continue
        out.append(x)
    return out


def ngu_lieu(norm, da_in):
    """Cột 'Ngữ liệu' của Excel CTV: đoạn văn đầy đủ ở câu con đầu tiên của mỗi đoạn trong file, các câu sau ghi tham chiếu."""
    q = norm.get("question_id")
    if q in da_in:
        return f"(Đoạn văn chung của question_id {q} – xem ở câu con đầu tiên của đoạn này trong file)"
    da_in.add(q)
    return norm.get("doan_van")
