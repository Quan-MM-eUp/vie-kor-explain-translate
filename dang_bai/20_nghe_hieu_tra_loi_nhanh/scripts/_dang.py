"""Phần riêng của dạng 20 – Nghe hiểu: Trả lời nhanh (dựng 2026-10-08, chạy hoàn toàn bằng Claude Opus 5.5 Cowork – không GPT API).

Phần chung kế thừa dạng 08 (cấu hình, đường dẫn, thứ tự chạy --tu/--den, kho đã duyệt, bản tạo Claude, Hán Việt, gợi ý định dạng).
Phần riêng 20 ở cuối file: tách SCRIPT nghe (cột transcript_vi – tiếng Nhật: câu nói + 3 câu trả lời), tách lời giải
(dịch câu nói + 3 lựa chọn trước ### / mỗi lựa chọn: câu Nhật – Nghĩa – → ĐÚNG/SAI – phân tích), phân loại khuôn A/B/C/D,
gắn cờ, kiểm tra K, Python điền prompt.utterance.ja/reading (x-python-dien), hiển thị Excel. Các script s0…s3 đều import file này.
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
    os.environ["PIPELINE_DATA"] = _c.get("du_lieu_test", "data/test_20_nghe_hieu_tra_loi_nhanh.csv")


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





FURI_VI_RE = re.compile(r"｜([^｜《》\n]*?[A-Za-zÀ-ỹĐđ][^｜《》\n]*?)《([^》\n]*)》")


def bo_furigana_chu_viet(text):
    """Bỏ furigana gắn lên chữ tiếng Việt / Latin (vd '- ｜Nhận xét《にんてい》:') – lỗi định dạng bản gốc.
    Trả (text, [(cũ, mới)])."""
    doi = []
    def _r(m):
        doi.append((m.group(0), m.group(1)))
        return m.group(1)
    return FURI_VI_RE.sub(_r, text), doi



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
# ================  DẠNG 20 – NGHE HIỂU: TRẢ LỜI NHANH – phần riêng (dựng 2026-10-08)  ================
# =====================================================================================================
# Đề nghe: không in lựa chọn (cột lua_chon_* chỉ là "1","2","3"). Nội dung tiếng Nhật nằm ở SCRIPT (cột transcript_vi –
# tên cột gây nhầm, thực chất là script tiếng Nhật): [nhãn người nói] câu nói + 3 câu trả lời đánh số.
# Lời giải (khuôn A – 89,5%):
#   <dịch câu nói (có thể có nhãn 'Nam:' / 'F:')>  [+ dòng nhãn người đáp trống 'Nữ:']  + dịch 3 lựa chọn  (TRÙNG LẶP với 'Nghĩa:')
#   ###
#   n. <câu Nhật có furigana>  /  Nghĩa: …  /  → ĐÚNG. | → SAI.  /  <phân tích>
# Khuôn B: khối lựa chọn nhưng không có ### (không có dòng dịch câu nói). Khuôn C: chỉ có bản dịch (không phân tích, không ĐÚNG/SAI).
# Khuôn D: tự do (tác tử TẠO chuyển theo nội dung). Ánh xạ: schema listening_response.v1 (xem prompts/s1_chuyen_json.md).

from pipeline_chung.common import JA_RE, VI_DIACRITIC_RE  # noqa: E402

KHUON_TEXT = {"A": "chuẩn (dịch + ### + khối lựa chọn)", "B": "khối lựa chọn, không có ### (không có dịch câu nói)",
              "C": "chỉ có bản dịch (không phân tích, không ĐÚNG/SAI)", "D": "tự do / không tách được", "trong": "không có lời giải"}

# ---- nhãn người nói ----
SPK_VI = (r"(?:Người\s+đàn\s+ông|Người\s+phụ\s+nữ|Người\s+nam|Người\s+nữ|Đàn\s+ông|Phụ\s+nữ|Nam|Nữ|Bạn\s+nam|Bạn\s+nữ|"
          r"M|F|A|B|Ｍ|Ｆ|男性?|女性?|男の人|女の人)(?:\s?[1-9１-９](?![\.．\d０-９]))?")   # 'Nam 1:', '男 2:' (lô 11–20, 22885)
NHAN_VI_RE = re.compile(r"^\s*\{?\s*(" + SPK_VI + r")\s*\}?\s*[:：;；]\s*(.*)$", re.S)
# nhãn tổng quát trong phần DỊCH (Cô gái:, Chàng trai:, Anh:, Ông Tanaka: …): ≤ 4 từ, viết hoa chữ đầu, không có số / dấu câu
NHAN_VI_TQ_RE = re.compile(r"^\s*\{?\s*([A-ZÀ-ỸĐ][^\s:：;；\d.,!?]{0,14}(?:\s+[^\s:：;；\d.,!?]{1,14}){0,3})\s*\}?\s*[:：]\s*(.*)$", re.S)
SPK_JA = r"(?:(?:[MFＭＦ]|男性?|女性?|男の人|女の人|[A-DＡ-Ｄ])(?:\s?[1-9１-９](?![\.．\d０-９]))?)"   # '男 1：' (22885)
NHAN_JA_RE = re.compile(r"^\s*(" + SPK_JA + r")\s*[:：;；]\s*(.*)$", re.S)

# ---- số thứ tự lựa chọn ----
_DIG = "1-4１-４"
SO_VI_RE = re.compile(rf"^\s*\{{?\s*([{_DIG}])\s*\}}?(?:\s*[\.．。、\)）:：]\s*|\s+)(.+)$", re.S)        # '1. …', '1 …', '1) …'
SO_VI_RONG_RE = re.compile(rf"^\s*\{{?\s*([{_DIG}])\s*\}}?\s*[\.．。、\)）:：]?\s*$")                          # '1.' đứng một mình (thiếu câu Nhật – 22595)
GACH_RE = re.compile(r"^\s*[-•・]\s*(.+)$", re.S)                                                            # '- câu Nhật' (18016)
SO_JA_RE = re.compile(rf"^\s*(?:{SPK_JA}\s*[:：;；]\s*)?([{_DIG}])(?:\s*[\.．。、\)）:：>＞]\s*|[\s　]+|(?=[^\d０-９\.．。、）\)]))(.+)$", re.S)
NGHIA_RE = re.compile(r"(?i)^\s*[-•]?\s*\{?\s*nghĩa\s*\}?\s*[:：]\s*(.*)$", re.S)
KL_RE = re.compile(r"(?i)^\s*\{?\s*(?:→|->|=>|➝|⇒)\s*\{?\s*(đúng|sai)\s*\}?\s*[\.。!]?\s*\}?\s*$")


def _so(c):
    return int(c.translate(str.maketrans("１２３４", "1234")))


def bo_nhan_vi(line):
    """'Nam: …' → ('Nam', '…'); không có nhãn → (None, line)."""
    m = NHAN_VI_RE.match(line or "") or NHAN_VI_TQ_RE.match(line or "")
    return (m.group(1), m.group(2).strip()) if m else (None, (line or "").strip())


def _day_so(lines, rx):
    """Tìm dãy dòng đánh số 1,2,3(,4) LIÊN TIẾP cuối cùng → (vị trí dòng '1', [nội dung]) hoặc (None, [])."""
    best = (None, [])
    for i, ln in enumerate(lines):
        m = rx.match(ln)
        if not m or _so(m.group(1)) != 1:
            continue
        run, k = [m.group(2).strip()], 2
        for ln2 in lines[i + 1:]:
            m2 = rx.match(ln2)
            if not m2 or _so(m2.group(1)) != k:
                break
            run.append(m2.group(2).strip())
            k += 1
        if len(run) >= 3 or (len(run) >= 2 and best[0] is None):
            best = (i, run)
    return best


# ---------------- SCRIPT (transcript_vi / doan_van) ----------------
def _plain(html):
    from pipeline_chung.normalize import normalize_html
    t, b = normalize_html(html or "")
    return t.replace("{", "").replace("}", ""), b


def tach_script(html, so_lc=3):
    """Script nghe → {ok, nguoi_noi, cau_noi, lua_chon[], ghi_chu[], rei, ruby_hong, hien_thi}."""
    t, broken = _plain(html)
    lines = [x.strip() for x in t.split("\n") if x.strip()]
    res = {"ok": False, "nguoi_noi": None, "cau_noi": None, "lua_chon": [], "ghi_chu": [], "rei": False,
           "ruby_hong": broken, "hien_thi": "\n".join(lines)}
    for i, ln in enumerate(lines):                                  # '------' + bản dịch Việt phía sau
        if re.match(r"^[-－ー―=＝_]{3,}\s*$", ln):
            res["ghi_chu"] += lines[i:]
            lines = lines[:i]
            break
    keep = []
    for ln in lines:
        if re.match(r"^(?:れい|例)[\s　]*(?:正答|せいとう)?[\s　]*[0-9０-９]?\s*$", ln):
            res["rei"] = True                                       # câu ví dụ của đề (れい 正答２)
            continue
        if VI_DIACRITIC_RE.search(ln) and not JA_RE.search(ln):     # dòng tiếng Việt lẫn vào script
            res["ghi_chu"].append(ln)
            continue
        keep.append(ln)
    i, run = _day_so(keep, SO_JA_RE)
    if i is not None and len(run) >= 2:
        truoc, sau = keep[:i], keep[i + len(run):]
        # 'M：１. 買い物です。' – nhãn người đáp dính dòng lựa chọn 1: đã bỏ trong SO_JA_RE
    else:
        body = [x for x in keep if not re.fullmatch(r"\s*" + SPK_JA + r"\s*[:：;；]\s*", x)]
        if len(body) == so_lc + 1:                                   # không đánh số (hoặc gạch đầu dòng <li>): câu nói + n câu trả lời
            truoc, sau = body[:1], []
            run = [re.sub(r"^[-•・]\s*", "", NHAN_JA_RE.sub(r"\2", x)).strip() for x in body[1:]]
        else:
            return res
    noi = []
    for ln in truoc:
        m = NHAN_JA_RE.match(ln)
        if m:
            if not m.group(2).strip():
                continue                                            # dòng nhãn người đáp trống 'F：'
            res["nguoi_noi"] = res["nguoi_noi"] or m.group(1)
            noi.append(re.sub(r"^[0-9０-９]{1,2}[\.．]\s*", "", m.group(2).strip()))   # số câu đề sau nhãn: '男 1: 1.大学…' (22885)
        else:
            noi.append(ln)
    res["cau_noi"] = "\n".join(noi) or None
    res["lua_chon"] = [x for x in run]
    res["ghi_chu"] = sau + res["ghi_chu"]
    res["ok"] = bool(res["cau_noi"]) and len(run) >= 2
    return res


# ---------------- lời giải ----------------
def _dau_khoi(ln):
    """Dòng mở đầu khối lựa chọn → (số | None nếu gạch đầu dòng, câu Nhật) hoặc None."""
    m = SO_VI_RE.match(ln)
    if m:
        return _so(m.group(1)), m.group(2).strip()
    m = SO_VI_RONG_RE.match(ln)
    if m:
        return _so(m.group(1)), ""
    m = GACH_RE.match(ln)
    if m and JA_RE.search(m.group(1)):
        return None, m.group(1).strip()
    return None


def _khoi(lines):
    """Các khối lựa chọn: dòng 'n. câu Nhật' (hoặc '- câu Nhật') ngay trước (≤ 3 dòng) dòng 'Nghĩa:'.
    Dòng 'Nghĩa:' đứng trước khối đầu tiên mà không có dòng mở đầu (vd 'Câu hỏi: … / Nghĩa: …' – 18016) thuộc phần mở đầu.
    → (mo_dau[], [khoi])."""
    ng = [i for i, ln in enumerate(lines) if NGHIA_RE.match(ln)]
    heads = []
    for i in ng:
        j = i - 1
        while j >= 0 and i - j <= 4 and _dau_khoi(lines[j]) is None:
            j -= 1
        if j < 0 or i - j > 4 or (heads and j <= heads[-1][1]):
            if not heads:
                continue
            return lines, []
        heads.append((j, i))
    if not heads:
        return lines, []
    out = []
    for k, (j, i) in enumerate(heads):
        end = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        so, ja0 = _dau_khoi(lines[j])
        ja = "\n".join([x for x in [ja0] + lines[j + 1:i] if x])
        nghia = NGHIA_RE.match(lines[i]).group(1).strip()
        kl, pt = None, []
        for ln in lines[i + 1:end]:
            mk = KL_RE.match(ln)
            if mk and kl is None:
                kl = mk.group(1).lower() == "đúng"
                continue
            pt.append(ln)
        out.append({"so": so if so is not None else k + 1, "ja": ja or None, "nghia": nghia or None, "ket_luan": kl,
                    "phan_tich": "\n".join(pt) or None})
    return lines[:heads[0][0]], out


def _phan_dich(lines, so_lc):
    """Phần dịch (trước ### / khuôn C) → {nhan, cau_noi_vi, lua_chon_vi[], sau_dich[], dong_nhan_trong}.
    sau_dich = câu chữ sau các dòng dịch lựa chọn (vd 'Là câu trả lời cho …' – 12195) → prompt.analysis."""
    res = {"nhan": None, "cau_noi_vi": None, "lua_chon_vi": [], "sau_dich": [], "dong_nhan_trong": 0}
    ng = [NGHIA_RE.match(x).group(1).strip() for x in lines if NGHIA_RE.match(x)]
    if ng:                                                          # 'Câu hỏi: <Nhật>' + 'Nghĩa: <dịch>' (18016)
        res["cau_noi_vi"] = ng[0] or None
        return res
    body = []
    for ln in lines:
        n, rest = bo_nhan_vi(ln)
        if n and not rest:
            res["dong_nhan_trong"] += 1                             # 'Nữ:' – nhãn người đáp đứng một mình
            continue
        if n:
            res["nhan"] = res["nhan"] or n
        body.append(rest)                                           # 'Anh: 1. Cái màu đỏ.' → '1. Cái màu đỏ.'
    i, run = _day_so(body, SO_VI_RE)
    if i is not None and len(run) == so_lc:
        truoc, lc, sau = body[:i], run, body[i + len(run):]
    elif len(body) >= so_lc + 1:
        truoc, lc, sau = body[:len(body) - so_lc], body[len(body) - so_lc:], []
    else:
        truoc, lc, sau = body, [], []
    res["cau_noi_vi"] = "\n".join(truoc) or None
    res["lua_chon_vi"], res["sau_dich"] = lc, sau
    return res


def _cmp(s):
    """So bản dịch trùng lặp: bỏ dấu câu, khoảng trắng, chữ hoa."""
    return re.sub(r"[\s\.,，。、!！?？…\"'“”‘’「」()（）:;~\-–—]", "", strip_marks(s or "").lower())


def tach_loi_giai(text, so_lc_script):
    """→ phan = {khuon, dich{…}, khoi[…], mo_dau, so_lua_chon}."""
    lines_all = [x.strip() for x in (text or "").split("\n")]
    if "###" in text:
        pre, post = text.split("###", 1)
        P = [x.strip() for x in pre.split("\n") if x.strip()]
        Q = [x.strip() for x in post.replace("###", "\n").split("\n") if x.strip()]
        mo, khoi = _khoi(Q)
        if khoi:
            dich = _phan_dich(P, len(khoi))
            return {"khuon": "A", "dich": dich, "khoi": khoi, "mo_dau": mo, "so_lua_chon": len(khoi)}
        lines = P + Q
    else:
        lines = [x for x in lines_all if x]
        mo, khoi = _khoi(lines)
        if khoi:
            dich = _phan_dich(mo, len(khoi)) if mo else {"nhan": None, "cau_noi_vi": None, "lua_chon_vi": [], "sau_dich": [], "dong_nhan_trong": 0}
            return {"khuon": "B", "dich": dich, "khoi": khoi, "mo_dau": [], "so_lua_chon": len(khoi)}
    # khuôn C: chỉ bản dịch – không có ĐÚNG/SAI, không có chữ Nhật dài, đủ câu nói + n lựa chọn
    n = so_lc_script or 3
    co_kl = any(KL_RE.match(x) or re.search(r"(?i)\b(đúng|sai)\s*[\.。]?\s*$|đáp án|câu trả lời đúng", x) for x in lines)
    ja_dai = sum(len("".join(JA_RE.findall(strip_marks(x)))) for x in lines) > 15
    if not co_kl and not ja_dai:
        dich = _phan_dich(lines, n)
        if dich["cau_noi_vi"] and len(dich["lua_chon_vi"]) == n:
            return {"khuon": "C", "dich": dich, "khoi": [], "mo_dau": [], "so_lua_chon": n}
    return {"khuon": "D", "dich": None, "khoi": [], "mo_dau": [], "so_lua_chon": n}


def _f(s):
    """Chuẩn hóa để so câu Nhật: bỏ furigana, { }, dấu câu, khoảng trắng."""
    s = strip_marks(s or "").replace("{", "").replace("}", "")
    return re.sub(r"[。\.．、,，\s　!！?？「」『』｢｣｡・’'\"…:：~〜\-－―ー]", "", s)


def _so_script(a, b):
    """'khop' | 'lech' (+ chỗ lệch)."""
    if _f(a) == _f(b):
        return "khop", ""
    d = _khac(_f(a), _f(b))
    return "lech", "; ".join(f"'{x}'→'{y}'" for x, y in d[:4])


FLAG_TEXT = {
    "khuon_A": "Khuôn chuẩn: dịch câu nói + ### + khối lựa chọn",
    "khuon_B": "Có khối lựa chọn nhưng không có ### – không có dòng dịch câu nói (utterance.meaning = null)",
    "khuon_C": "Lời giải CHỈ có bản dịch – không phân tích, không ĐÚNG/SAI (analysis = null) → gắn cờ thieu_noi_dung",
    "khuon_D": "Lời giải tự do / Python không tách được – tác tử TẠO chuyển theo nội dung, tác tử KIỂM TRA soát kỹ",
    "co_nhan_nguoi_noi": "Dòng dịch câu nói có nhãn người nói (Nam: / F: …) – meaning KHÔNG chép nhãn",
    "nhieu_dong_cau_noi": "Dịch câu nói có nhiều dòng (nối bằng \\n)",
    "khong_dich_cau_noi": "Không có dòng dịch câu nói (utterance.meaning = null)",
    "dich_lap_lech": "Bản dịch lựa chọn trước ### khác dòng 'Nghĩa:' (JSON lấy 'Nghĩa:')",
    "chen_tu_nhat_dich": "Bản dịch (câu nói / Nghĩa) còn chen từ tiếng Nhật – nghi dịch dở (gắn cờ nghia_cau – quyết định 08/10/2026)",
    "co_doan_truoc_khoi": "Có câu chữ sau ### trước lựa chọn 1",
    "co_doan_sau_dich": "Có câu chữ sau các dòng dịch lựa chọn (trước ###) – đưa vào prompt.analysis",
    "thieu_cau_nhat": "Có khối lựa chọn không có câu tiếng Nhật – sentence.ja chép câu trả lời tương ứng của script",
    "thieu_ket_luan": "Có lựa chọn không có dòng '→ ĐÚNG/SAI'",
    "nhieu_dung": "Số lựa chọn '→ ĐÚNG' khác 1",
    "lech_dap_an": "Lựa chọn '→ ĐÚNG' khác dap_an_so của đề",
    "thieu_phan_tich": "Có lựa chọn không có phân tích (analysis = null)",
    "thu_tu_lech": "Số thứ tự khối lựa chọn không phải 1, 2, 3 …",
    "lech_script": "Câu Nhật của lựa chọn trong lời giải khác script (kana/kanji, lỗi gõ… – chỉ cảnh báo; khác nội dung → cờ cau_khac_de)",
    "script_khong_tach": "Python không tách được script → utterance.ja = null; tác tử KIỂM TRA xem cột transcript_vi",
    "script_tu_doan_van": "Script lấy từ cột doan_van (cột transcript_vi lỗi)",
    "script_co_ghi_chu": "Script có ghi chú / bản dịch Việt sau các lựa chọn (không đưa vào JSON)",
    "script_vi_du": "Câu ví dụ của đề (script có 'れい 正答n')",
    "lua_chon_thua": "Cột lua_chon_4 = '4' thừa – script / lời giải chỉ có 3 lựa chọn (JSON 3 lựa chọn; báo cáo dữ liệu gốc)",
    "du_lieu_loi": "Dữ liệu đề lỗi (thiếu cột lựa chọn / đáp án ngoài số lựa chọn)",
    "so_lc_lech_script": "Số lựa chọn trong lời giải khác script",
    "furigana_phan_tich": "Có furigana trong phần phân tích",
    "co_furigana": "Có furigana",
    "ruby_hong": "Có ruby hỏng trong bản gốc",
    "ky_hieu_trung": "Bản gốc có sẵn ký hiệu ｜《》",
    "furigana_chu_viet": "Furigana gắn lên chữ tiếng Việt (Python đã bỏ)",
    "danh_dau_rac": "Bản gốc có đoạn in đậm / gạch chân rỗng (đã bỏ thẻ)",
}
CTV_FLAGS = ("khuon_C", "khuon_D", "lech_dap_an", "nhieu_dung", "chen_tu_nhat_dich", "script_khong_tach")
FURI_SKIP = [("prompt", "utterance", "ja"), ("correct", "option_ja")]   # utterance.ja: Python điền từ script; option_ja: bản sao


def parse_and_flag(text, row):
    """text = lời giải đã chuẩn hóa. → (phan, co[], ghi_chu[], src_text, src_vi_text)."""
    co, gc = [], []
    # script
    nlc_csv = sum(1 for i in range(1, 5) if (row.get(f"lua_chon_{i}") or "").strip())
    sc = tach_script(row.get("transcript_vi"))
    if not sc["ok"] and (row.get("doan_van") or "").strip():
        sc2 = tach_script(row.get("doan_van"))
        if sc2["ok"]:
            sc, _ = sc2, co.append("script_tu_doan_van")
    if not sc["ok"]:
        co.append("script_khong_tach")
        gc.append("[Bản gốc VI] Python không tách được script nghe (transcript_vi) – utterance.ja = null")
    if sc["ghi_chu"]:
        co.append("script_co_ghi_chu")
    if sc["rei"]:
        co.append("script_vi_du")
    ph = tach_loi_giai(text, len(sc["lua_chon"]) if sc["ok"] else None)
    ph["script"] = sc
    co.append("khuon_" + ph["khuon"])
    n = ph["so_lua_chon"]
    dap = int(row["dap_an_so"]) if str(row.get("dap_an_so", "")).isdigit() else None
    if nlc_csv > n and n == 3 and (row.get("lua_chon_4") or "").strip() in ("4", "４"):
        co.append("lua_chon_thua")
    if nlc_csv < n or dap is None or not (1 <= dap <= n):
        co.append("du_lieu_loi")
        gc.append(f"[Bản gốc VI] Dữ liệu đề lỗi: {nlc_csv} cột lựa chọn, dap_an_so = {row.get('dap_an_so')!r}, lời giải có {n} lựa chọn")
    if sc["ok"] and len(sc["lua_chon"]) != n:
        co.append("so_lc_lech_script")
    d = ph.get("dich") or {}
    if ph["khuon"] in ("A", "B", "C"):
        if d.get("nhan"):
            co.append("co_nhan_nguoi_noi")
        if not d.get("cau_noi_vi"):
            co.append("khong_dich_cau_noi")
        elif "\n" in d["cau_noi_vi"]:
            co.append("nhieu_dong_cau_noi")
        if d.get("sau_dich"):
            co.append("co_doan_sau_dich")
    if ph["khuon"] == "C":
        gc.append("[Bản gốc VI] Lời giải chỉ có bản dịch – không phân tích các lựa chọn (thieu_noi_dung)")
    if ph["khuon"] == "D":
        gc.append("[Bản gốc VI] Lời giải không theo khuôn chuẩn – Python không tách được")
    khoi = ph["khoi"]
    if khoi:
        if [k["so"] for k in khoi] != list(range(1, n + 1)):
            co.append("thu_tu_lech")
        if ph.get("mo_dau"):
            co.append("co_doan_truoc_khoi")
        if any(k["ket_luan"] is None for k in khoi):
            co.append("thieu_ket_luan")
        dung = [k["so"] for k in khoi if k["ket_luan"]]
        if len(dung) != 1:
            co.append("nhieu_dung")
            gc.append(f"[Bản gốc VI] Lời giải có {len(dung)} lựa chọn '→ ĐÚNG' ({dung})")
        elif dap and dung[0] != dap:
            co.append("lech_dap_an")
            gc.append(f"[Bản gốc VI] Lời giải chấm lựa chọn {dung[0]} ĐÚNG – đáp án của đề là {dap}")
        if any(not k["ja"] for k in khoi):
            co.append("thieu_cau_nhat")
            gc.append("[Bản gốc VI] Có lựa chọn thiếu câu tiếng Nhật trong lời giải – JSON chép từ script")
        if any(not k["phan_tich"] for k in khoi):
            co.append("thieu_phan_tich")
        if any("《" in (k["phan_tich"] or "") for k in khoi):
            co.append("furigana_phan_tich")
        lc_vi = d.get("lua_chon_vi") or []
        if lc_vi and len(lc_vi) == len(khoi):
            lech = [(k["so"], a, k["nghia"]) for a, k in zip(lc_vi, khoi) if _cmp(a) != _cmp(k["nghia"])]
            if lech:
                co.append("dich_lap_lech")
                ph["dich_lap_lech"] = [f"lựa chọn {s}: trước ### '{a}' ↔ Nghĩa '{b}'" for s, a, b in lech]
        if sc["ok"]:
            ph["so_script"] = []
            for k in khoi:
                j = k["so"] - 1
                if 0 <= j < len(sc["lua_chon"]):
                    kq, ct = _so_script(k["ja"], sc["lua_chon"][j])
                    ph["so_script"].append({"so": k["so"], "ket_qua": kq, "chi_tiet": ct, "script": sc["lua_chon"][j]})
            if any(x["ket_qua"] == "lech" for x in ph["so_script"]):
                co.append("lech_script")
    # từ Nhật chen trong bản dịch câu nói / Nghĩa
    chen = []
    for name, s in [("dịch câu nói", d.get("cau_noi_vi"))] + [(f"Nghĩa lựa chọn {k['so']}", k["nghia"]) for k in khoi] + \
            ([(f"dịch lựa chọn {i + 1}", x) for i, x in enumerate(d.get("lua_chon_vi") or [])] if ph["khuon"] == "C" else []):
        ja = [x for x in JA_RE.findall(strip_marks(s or "")) if x.strip("・ー")]
        if ja:
            chen.append(f"{name}: {ja[:4]}")
    if chen:
        co.append("chen_tu_nhat_dich")
        ph["chen_tu_nhat"] = chen
        gc.append("[Bản gốc VI] Bản dịch còn chen từ tiếng Nhật – " + "; ".join(chen))
    # văn bản chuẩn để kiểm tra (bỏ phần dịch trùng lặp trước ###, bỏ nhãn người nói)
    sau = "\n".join(d.get("sau_dich") or [])
    if ph["khuon"] == "A":
        src = "\n".join(x for x in [d.get("cau_noi_vi"), sau] if x) + "\n" + text.split("###", 1)[1]
    elif ph["khuon"] == "B":
        src = "\n".join(x for x in [d.get("cau_noi_vi"), sau] if x) + "\n" + "\n".join(
            f"{k['so']}. {k['ja'] or ''}\nNghĩa: {k['nghia'] or ''}\n{k['phan_tich'] or ''}" for k in khoi)
    elif ph["khuon"] == "C":
        src = "\n".join([d.get("cau_noi_vi") or ""] + d.get("lua_chon_vi", []))
    else:
        src = text
    if khoi:
        src_vi = "\n".join([d.get("cau_noi_vi") or "", sau] + [f"{k['nghia'] or ''}\n{k['phan_tich'] or ''}" for k in khoi])
    else:
        src_vi = src
    return ph, sorted(set(co)), gc, src.strip(), src_vi


LABELS = [r"(?im)^\s*[-•]?\s*\{?\s*nghĩa\s*\}?\s*[:：]", r"(?im)^\s*(?:→|->|=>|➝|⇒)\s*(?:đúng|sai)\s*[\.。!]?\s*$", r"#{3,}",
          r"(?im)^\s*" + SPK_VI + r"\s*[:：]"]


def strip_labels(text):
    """Bỏ nhãn cố định khi đo độ phủ chữ tiếng Việt."""
    for pat in LABELS:
        text = re.sub(pat, " ", text)
    return text


# ---------------- kiểm tra riêng giai đoạn 1 (K) ----------------
def _cover(src_text, out_text):
    from pipeline_chung.common import vi_words
    s = collections.Counter(vi_words(strip_labels(src_text or "")))
    o = collections.Counter(vi_words(out_text or ""))
    if not s:
        return 1.0, []
    return sum((s & o).values()) / sum(s.values()), [w for w, _ in (s - o).most_common(8)]


def check_k(doc, norm, policy):
    loi, canh_bao = [], []
    de, ph = norm["de"], norm.get("phan") or {}
    sc, d, khoi = ph.get("script") or {}, ph.get("dich") or {}, ph.get("khoi") or []
    khuon, n = ph.get("khuon"), ph.get("so_lua_chon") or 3
    p, c = doc.get("prompt") or {}, doc.get("correct") or {}
    u, opts = p.get("utterance") or {}, doc.get("options") or []
    dap = de.get("dap_an_so") if isinstance(de.get("dap_an_so"), int) else None
    # K-UT – câu nói
    if u.get("ja") != (sc.get("cau_noi") if sc.get("ok") else None):
        loi.append("K-UT: prompt.utterance.ja phải đúng câu nói Python tách từ script (Python điền khi --nhan – không sửa tay)")
    if u.get("reading") is not None:
        loi.append("K-UT: prompt.utterance.reading phải là null (bản gốc không có dòng cách đọc)")
    src_u = d.get("cau_noi_vi")
    if khuon in ("A", "B", "C"):
        if (src_u is None) != (u.get("meaning") is None):
            loi.append("K-UT: utterance.meaning phải null khi và chỉ khi lời giải không có dòng dịch câu nói")
        elif src_u:
            cv, miss = _cover(src_u, _v(u.get("meaning")))
            if cv < 0.97:
                loi.append(f"K-UT: utterance.meaning thiếu chữ so với dòng dịch câu nói: {miss}")
    if u.get("meaning") and NHAN_VI_RE.match(_v(u["meaning"]) or ""):
        canh_bao.append("K-UT: utterance.meaning còn nhãn người nói (Nam: / F: …) – bỏ nhãn (sua_dinh_dang / lỗi tác tử TẠO)")
    if p.get("situation") is not None:
        canh_bao.append("K-UT: prompt.situation khác null – dạng 20 không có tình huống")
    if p.get("analysis") and khuon != "D":
        canh_bao.append("K-UT: prompt.analysis có nội dung – lời giải khuôn chuẩn không có phân tích câu nói")
    # K1 – lựa chọn
    if [o.get("index") for o in opts] != list(range(1, n + 1)):
        loi.append(f"K1: options phải có {n} lựa chọn theo thứ tự 1–{n} (đang có {[o.get('index') for o in opts]})")
    by = {k["so"]: k for k in khoi}
    for o in opts:
        i, s = o.get("index"), o.get("sentence") or {}
        if s.get("reading") is not None:
            loi.append(f"K8: lựa chọn {i}: sentence.reading phải là null")
        k = by.get(i)
        if k:
            if _k(s.get("ja")) != _k(k["ja"]):
                loi.append(f"K8: lựa chọn {i}: sentence.ja '{s.get('ja')}' khác câu Nhật của lời giải '{k['ja']}'")
            if (k["nghia"] is None) != (s.get("meaning") is None):
                loi.append(f"K8: lựa chọn {i}: sentence.meaning phải null khi và chỉ khi lời giải không có 'Nghĩa:'")
            elif k["nghia"]:
                cv, miss = _cover(k["nghia"], _v(s.get("meaning")))
                if cv < 0.97:
                    loi.append(f"K9: lựa chọn {i}: sentence.meaning thiếu chữ: {miss}")
            if k["ket_luan"] is not None and o.get("is_correct") is not k["ket_luan"]:
                loi.append(f"K6: lựa chọn {i}: is_correct = {o.get('is_correct')} – lời giải ghi '→ {'ĐÚNG' if k['ket_luan'] else 'SAI'}'")
            if (k["phan_tich"] is None) != (o.get("analysis") is None):
                loi.append(f"K9: lựa chọn {i}: analysis phải null khi và chỉ khi lời giải không có phân tích")
            elif k["phan_tich"]:
                cv, miss = _cover(k["phan_tich"], _v(o.get("analysis")))
                if cv < 0.97:
                    loi.append(f"K9: lựa chọn {i}: analysis thiếu chữ: {miss}")
        elif khuon == "C":
            lc_vi = d.get("lua_chon_vi") or []
            if sc.get("ok") and isinstance(i, int) and 1 <= i <= len(sc["lua_chon"]) and _k(s.get("ja")) != _k(sc["lua_chon"][i - 1]):
                loi.append(f"K8: lựa chọn {i}: khuôn C – sentence.ja phải chép câu trả lời {i} của script '{sc['lua_chon'][i - 1]}'")
            if isinstance(i, int) and 1 <= i <= len(lc_vi):
                cv, miss = _cover(lc_vi[i - 1], _v(s.get("meaning")))
                if cv < 0.97:
                    loi.append(f"K9: lựa chọn {i}: sentence.meaning thiếu chữ so với bản dịch: {miss}")
            if o.get("analysis") is not None:
                loi.append(f"K9: lựa chọn {i}: khuôn C – analysis phải null (lời giải không có phân tích)")
    for x in ph.get("so_script") or []:
        if x["ket_qua"] == "lech":
            canh_bao.append(f"K-SC: lựa chọn {x['so']}: câu Nhật trong lời giải lệch script '{x['script']}' ({x['chi_tiet']}) – "
                            "kana/kanji, lỗi gõ → bỏ qua; khác nội dung → cờ cau_khac_de")
    for x in ph.get("dich_lap_lech") or []:
        canh_bao.append(f"K-TL: bản dịch trùng lặp lệch nhau – {x} (JSON theo 'Nghĩa:')")
    for x in ph.get("chen_tu_nhat") or []:
        canh_bao.append(f"K-NJ: bản dịch chen từ tiếng Nhật – {x} → gắn cờ nghia_cau (quyết định 08/10/2026)")
    # K6 – đáp án
    dung = [o.get("index") for o in opts if o.get("is_correct") is True]
    if str(c.get("index")) != str(de.get("dap_an_so")):
        loi.append(f"K6: correct.index = {c.get('index')} khác dap_an_so = {de.get('dap_an_so')}")
    if dap and dung != [dap] and khuon in ("C", "D"):
        loi.append(f"K6: khuôn {khuon}: is_correct phải true ở đúng lựa chọn {dap} (đang: {dung})")
    if len(dung) != 1 and "nhieu_dung" not in norm.get("co", []):
        loi.append(f"K6: phải có đúng 1 lựa chọn is_correct = true (đang: {dung})")
    di = c.get("index")
    if isinstance(di, int) and 1 <= di <= len(opts) and c.get("option_ja") != (opts[di - 1].get("sentence") or {}).get("ja"):
        loi.append(f"K6: correct.option_ja phải giống hệt options[{di - 1}].sentence.ja")
    if c.get("full_sentence") is not None:
        loi.append("K6: correct.full_sentence phải là null")
    loi += TK.kiem_tra(doc, None)
    return loi, canh_bao


def bo_truong_python(doc):
    """Trước khi so schema api ở --nhan: bỏ các trường Python điền (chạy lại --nhan không lỗi)."""
    u = ((doc.get("prompt") or {}).get("utterance")) if isinstance(doc, dict) else None
    if isinstance(u, dict):
        u.pop("ja", None)
        u.pop("reading", None)
    return doc


def bo_sung_utterance(doc, norm):
    """Hook cho claude_tao.gd1_nhan: Python điền prompt.utterance.ja (câu nói tách từ script) và reading = null."""
    sc = (norm.get("phan") or {}).get("script") or {}
    p = doc.get("prompt") or {}
    u = p.get("utterance") or {}
    p["utterance"] = {"ja": sc.get("cau_noi") if sc.get("ok") else None, "reading": None, "meaning": u.get("meaning")}
    doc["prompt"] = p
    return doc


def is_style_field(path):
    """Trường câu văn giải thích (kiểm tra -습니다): chỉ các phần phân tích; nghĩa câu (lời thoại) dịch theo mức lịch sự tiếng Nhật."""
    p = path if isinstance(path, str) else path_str(path)
    return bool(re.search(r"analysis", p)) and "meaning" not in p


# ---------------- hiển thị cho Excel CTV ----------------
def render(d, lang):
    p, c = d.get("prompt") or {}, d.get("correct") or {}
    u = p.get("utterance") or {}
    out = [bold("【Câu nói】") + " " + show(u.get("ja") or "")]
    if u.get("meaning"):
        out.append(f"Nghĩa: {_t(u['meaning'], lang)}")
    if p.get("situation"):
        out.append(f"Tình huống: {_t(p['situation'], lang)}")
    out += ["- " + _t(x, lang) for x in p.get("analysis") or []]
    out.append(bold("【PHÂN TÍCH CÁC LỰA CHỌN】"))
    for o in d.get("options", []):
        s = o.get("sentence") or {}
        out.append(bold(f"{o.get('index')}. ") + show(s.get("ja") or ""))
        if s.get("meaning"):
            out.append(f"Nghĩa: {_t(s['meaning'], lang)}")
        out.append("→ ĐÚNG." if o.get("is_correct") else "→ SAI.")
        if o.get("analysis"):
            out.append(_t(o["analysis"], lang))
    out.append(bold("【LỰA CHỌN ĐÚNG】"))
    out.append(f"{c.get('index')}. {show(c.get('option_ja', ''))}")
    out += TK.render(d, lang, show, bold)
    return "\n".join(out)


def ngu_lieu(norm):
    """Cột 'Ngữ liệu' của Excel CTV: script đã tách (câu nói + các câu trả lời)."""
    sc = (norm.get("phan") or {}).get("script") or {}
    if not sc.get("ok"):
        return sc.get("hien_thi")
    return "\n".join([(f"{sc['nguoi_noi']}：" if sc.get("nguoi_noi") else "") + sc["cau_noi"]]
                     + [f"{i + 1}. {x}" for i, x in enumerate(sc["lua_chon"])])


def sudachi_hints(norm):
    """Dạng 20 không dùng Sudachi (không có dòng cách đọc) – giữ hàm cho s1_claude_goi."""
    return []
