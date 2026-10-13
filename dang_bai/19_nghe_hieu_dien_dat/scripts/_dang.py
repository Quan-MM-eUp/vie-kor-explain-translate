"""Phần riêng của dạng 19 – Nghe hiểu diễn đạt (発話表現) – dựng 2026-10-08 theo KE_HOACH_PIPELINE.md (đã duyệt).

Đề nghe: câu tình huống tiếng Nhật ('… 何と言いますか') + 3 câu nói – nằm trong TRANSCRIPT (cột transcript_vi), cột lua_chon_1–3 chỉ là số.
Lời giải khuôn A: dịch tình huống + 3 dòng nghĩa (bản sao) → ### → 3 khối 'i. <câu Nhật>' / 'Nghĩa: …' / '→ ĐÚNG|SAI.' / phân tích.
Khuôn B: chỉ có 3 khối (thiếu dịch tình huống). Khuôn D: chỉ dịch tình huống + 3 dòng nghĩa (không phân tích).
Khuôn C (lời giải chỉ chép transcript) và câu SAI DẠNG (即時応答 N1/N2, đề 4 lựa chọn N3) không chạy – chỉ liệt kê.
Schema listening_response.v1 (+ reference_raw); prompt.utterance.ja do Python điền từ transcript (khóa – K-TH).
Phần chung (cấu hình, đường dẫn, chọn phạm vi) giống dạng 07/08/09; phần riêng dạng 19 ở cuối file. Các script s0…s3 đều import file này.
Có thể chép sang dạng 20 (Trả lời nhanh – cùng schema): đổi phần tách transcript / lời giải.
"""
import collections
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
    os.environ["PIPELINE_DATA"] = _c.get("du_lieu_test", "data/test_19_nghe_hieu_dien_dat.csv")


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
    g = {"thuat_ngu": {}, "cau_co_dinh": {}, "mau_cau": {}, "cau_noi_co_dinh": {}}   # dạng 19: + câu nói tiếng Nhật cố định (lời chào)
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
        return ids
    ids = status.ids(*default_states)
    if getattr(args, "lo", None):
        ids = ids[: args.lo]
    elif not getattr(args, "tat_ca", False):
        sys.exit("Hãy chọn phạm vi: --pilot, --ids <id1,id2>, --tu <từ mẫu> --den <đến mẫu>, --lo <số câu> hoặc --tat-ca")
    return ids






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
# ================  DẠNG 19 – NGHE HIỂU DIỄN ĐẠT: phần riêng (dựng 2026-10-08)  ======================
# =====================================================================================================
import html as _html  # noqa: E402
from pipeline_chung.common import VI_DIACRITIC_RE  # noqa: E402

NANTO_RE = re.compile(r"(?:何|なん|ナン|どう)\s*(?:と|て)?\s*(?:言|い|聞|き)\s*(?:いますか|えば|ったら|って|きますか|ますか)")


def co_nanto(s):
    """Câu có '何と言いますか' / 'なんと聞きますか' / 'どう言いますか' … (bỏ furigana, cách đọc trong ngoặc)."""
    return bool(NANTO_RE.search(re.sub(r"[(（][぀-ゟ]+[)）]", "", strip_marks(s or ""))))
SO_DOI = str.maketrans("１２３４", "1234")


def _lines(text):
    return [x.strip() for x in (text or "").split("\n") if x.strip()]


def _k(t):
    """So chuỗi tiếng Nhật (trường JSON ↔ lời giải): bỏ furigana / ⟪ ⟫ / { } / khoảng trắng."""
    return re.sub(r"[\s　]", "", norm_ja(t or "")).replace("{", "").replace("}", "")


def _f(s):
    """So câu nói (lời giải ↔ transcript): bỏ furigana, { }, dấu câu, khoảng trắng, nhãn người nói."""
    s = strip_marks(s or "").replace("{", "").replace("}", "")
    s = norm_ja(s)
    return re.sub(r"[。\.．、,，\s　!！?？「」『』｢｣｡・’'\"…:：~〜\-－―()（）]", "", s).replace("ー", "一")


def _cover(src_text, out_text):
    from pipeline_chung.common import vi_words
    s, o = collections.Counter(vi_words(src_text or "")), collections.Counter(vi_words(out_text or ""))
    if not s:
        return 1.0, []
    return sum((s & o).values()) / sum(s.values()), [w for w, _ in (s - o).most_common(8)]


def _v(o):
    return (o or {}).get("vi") if o else None


# ---------------- Python sửa định dạng: furigana đọc Hán Việt gắn lên chữ Hán trong câu tiếng Việt ----------------
#   '<ruby>人<rt>nhân</rt></ruby><ruby>員<rt>viên</rt></ruby> phục vụ' (21395, 25368) → 'nhân viên phục vụ'  (Q4 duyệt 08/10/2026)
_RUBY_VN = r"<ruby\b[^>]*>(?:(?!</ruby>|<rt\b).)*?<rt\b[^>]*>[^<]*?[A-Za-zÀ-ỹĐđ][^<]*?</rt>(?:\s*<rp\b[^>]*>.*?</rp>)?\s*</ruby>"
RUBY_VN_RUN_RE = re.compile(rf"(?:{_RUBY_VN})+", re.S | re.I)
_RUBY_PART_RE = re.compile(r"<ruby\b[^>]*>((?:(?!</ruby>|<rt\b).)*?)<rt\b[^>]*>([^<]*?)</rt>", re.S | re.I)


def bo_ruby_chu_viet(html):
    """Trả (html đã thay, [(chữ Hán, chữ Việt)])."""
    found = []

    def rep(m):
        parts = _RUBY_PART_RE.findall(m.group(0))
        base = "".join(re.sub(r"<rp\b.*?</rp>|<[^>]+>", "", b, flags=re.S) for b, _ in parts)
        doc = " ".join(_html.unescape(r).strip() for _, r in parts)
        found.append((base, doc))
        return doc
    return RUBY_VN_RUN_RE.sub(rep, html or ""), found


# ---------------- tách transcript: câu tình huống + các câu nói ----------------
SPK_RE = re.compile(r"^\s*(?:[MFＭＦ]|[^\s\d０-９:：、。「」？?！!]{1,4})\s*[:：]\s*")
OPT_RE = re.compile(r"^([1-4１-４])(\s*[\.．、。,，)）]\s*|\s+)?(.+)$")
BO_DONG_RE = re.compile(r"^(?:[0-9０-９]+\s*(?:番|ばん)|れい|例|問\s*[0-9０-９]+|もんだい\s*[0-9０-９]*)$")


def tach_transcript(text):
    """Transcript đã chuẩn hóa (furigana ｜《》, đã bỏ { }) → (câu tình huống | None, [câu nói], ghi chú)."""
    if not (text or "").strip():
        return None, [], "transcript rỗng"
    if VI_DIACRITIC_RE.search(strip_marks(text)) or "Nghĩa" in text:
        return None, [], "transcript không phải tiếng Nhật (chép lời giải)"
    sit, opts, sau = [], [], []
    for ln in _lines(text):
        l2 = SPK_RE.sub("", ln).strip()
        if not l2 or BO_DONG_RE.match(l2):
            continue
        m = OPT_RE.match(l2)
        if m and not sau:
            n, rest = int(m.group(1).translate(SO_DOI)), m.group(3).strip()
            if n == len(opts) + 1 and rest and (m.group(2) or (sit and not re.match(r"[0-9０-９番ばん年月日回人つ時分歳度階]", rest))):
                opts.append(SPK_RE.sub("", rest).strip())
                continue
        (sau if opts else sit).append(l2)
    gc = []
    if not opts:          # lựa chọn không đánh số: câu hỏi '何と言いますか' + đúng 3 dòng sau
        i = next((k for k, x in enumerate(sit) if co_nanto(x)), None)
        if i is not None and len(sit) - i - 1 == 3:
            opts = [(OPT_RE.match(x).group(3).strip() if OPT_RE.match(x) and OPT_RE.match(x).group(2) is not None else x) for x in sit[i + 1:]]
            opts = [re.sub(r"^[1-4１-４][\.．、]\s*", "", x) for x in opts]
            sit = sit[:i + 1]
            gc.append("lựa chọn trong transcript không đánh số")
    if sau:
        gc.append(f"transcript còn {len(sau)} dòng sau các lựa chọn")
    return ("\n".join(sit) or None), opts, "; ".join(gc)


# ---------------- tách lời giải ----------------
SPK_VI_RE = re.compile(r"^\s*(?:Nam|Nữ|Người nam|Người nữ|M|F|A|B)\s*[:：]\s*")
SPK_VI_ONLY_RE = re.compile(r"^\s*(?:Nam|Nữ|Người nam|Người nữ|M|F|A|B)\s*[:：]\s*$")
HEAD_OPT_RE = re.compile(r"^\s*(?:(?:Nam|Nữ|Người nam|Người nữ|M|F|A|B)\s*[:：]\s*)?([1-4１-４])\s*[\.．、)）]\s*(.*)$")
KHOI_RE = re.compile(r"^\s*([1-4])\s*[\.．]\s*(.*)$")
NGHIA_RE = re.compile(r"(?i)^\s*[-+•]?\s*nghĩa\s*[:：]\s*(.*)$")
KL_RE = re.compile(r"^\s*(?:→|⇒|->|=>)\s*(ĐÚNG|SAI|Đúng|Sai|đúng|sai)(?![\wÀ-ỹ])\s*[.。!]?\s*(.*)$")


def tach_khoi(body):
    """Phần sau ### (hoặc cả lời giải khuôn B) → (các khối lựa chọn, các dòng trước khối 1)."""
    khoi, truoc, cur = [], [], None
    for ln in (body or "").split("\n"):
        m = KHOI_RE.match(ln)
        if m and int(m.group(1)) == len(khoi) + 1 and (cur is None or cur["nghia"] is not None or cur["ket_luan"] is not None):
            cur = {"so": int(m.group(1)), "ja": m.group(2).strip() or None, "nghia": None, "ket_luan": None, "phan_tich": [], "nhan_lap": False}
            khoi.append(cur)
            continue
        if cur is None:
            if ln.strip():
                truoc.append(ln.strip())
            continue
        if not ln.strip():
            cur["phan_tich"].append("")
            continue
        mn, mk = NGHIA_RE.match(ln), KL_RE.match(ln)
        if cur["ja"] is None and not mn and not mk:
            cur["ja"] = ln.strip()
            continue
        if mn and cur["nghia"] is None and cur["ket_luan"] is None and not any(x.strip() for x in cur["phan_tich"]):
            cur["nghia"] = mn.group(1).strip()
            continue
        if mk and cur["ket_luan"] is None:
            cur["ket_luan"] = mk.group(1).upper() == "ĐÚNG"
            if mk.group(2).strip():
                cur["phan_tich"].append(mk.group(2).strip())
            continue
        if mn or mk:
            cur["nhan_lap"] = True
        cur["phan_tich"].append(ln.strip())
    for k in khoi:
        k["phan_tich"] = re.sub(r"\n{2,}", "\n", "\n".join(k["phan_tich"])).strip() or None
    return khoi, truoc


def tach_loi_giai(text):
    """Lời giải đã chuẩn hóa → phan = {khuon A|B|C|D, tinh_huong_vi, nghia_dau, khoi, truoc_khoi}."""
    t = text or ""
    if "###" in t:
        head, body = t.split("###", 1)
        hl = [x for x in _lines(head) if not SPK_VI_ONLY_RE.match(x)]          # dòng chỉ có nhãn người nói ('Nam:') – trình bày, bỏ
        nghia_dau = [HEAD_OPT_RE.match(x).group(2).strip() for x in hl if HEAD_OPT_RE.match(x)]
        th = [x for x in hl if not HEAD_OPT_RE.match(x)]
        if len(nghia_dau) == 2 and th and SPK_VI_RE.match(th[-1]):           # 'Nữ: Lâu rồi không gặp.' = nghĩa lựa chọn 1 không đánh số (21410)
            nghia_dau.insert(0, SPK_VI_RE.sub("", th.pop()).strip())
        khoi, truoc = tach_khoi(body)
        return {"khuon": "A", "tinh_huong_vi": "\n".join(th) or None, "nghia_dau": nghia_dau, "khoi": khoi, "truoc_khoi": truoc}
    khoi, truoc = tach_khoi(t)
    if khoi and any(k["ket_luan"] is not None for k in khoi):
        return {"khuon": "B", "tinh_huong_vi": "\n".join(truoc) or None, "nghia_dau": [], "khoi": khoi, "truoc_khoi": []}
    ls = _lines(t)
    if not VI_DIACRITIC_RE.search(strip_marks(t)):
        return {"khuon": "C", "tinh_huong_vi": None, "nghia_dau": [], "khoi": [], "truoc_khoi": []}
    th, ng = (ls[:-3], ls[-3:]) if len(ls) >= 4 else (ls[:1], ls[1:])
    ng = [re.sub(r"^\s*[1-4１-４]\s*[\.．、)）]\s*", "", x) for x in ng]
    khoi = [{"so": i + 1, "ja": None, "nghia": x, "ket_luan": None, "phan_tich": None, "nhan_lap": False} for i, x in enumerate(ng)]
    return {"khuon": "D", "tinh_huong_vi": "\n".join(th) or None, "nghia_dau": [], "khoi": khoi, "truoc_khoi": []}


def bo_dong_nghia_dau(text):
    """Lời giải bỏ 3 dòng nghĩa ở phần đầu (bản sao của dòng 'Nghĩa:') – dùng để đo độ phủ / so furigana (WF chung mục 8, quy tắc 8)."""
    if "###" not in (text or ""):
        return text or ""
    head, body = text.split("###", 1)
    hl = [x for x in head.split("\n") if not SPK_VI_ONLY_RE.match(x)]
    th = [x for x in hl if x.strip() and not HEAD_OPT_RE.match(x)]
    n_opt = sum(1 for x in hl if HEAD_OPT_RE.match(x))
    if n_opt == 2 and th and SPK_VI_RE.match(th[-1]):
        hl = [x for x in hl if x is not th[-1]]
    head = "\n".join(x for x in hl if not HEAD_OPT_RE.match(x))
    return head + "###" + body


def so_cau(a, b):
    """So câu nói trong lời giải với transcript → (khop | khop_doc | lech_nhe | lech_nang | khong_co, chi_tiet)."""
    fa, fb = _f(a), _f(b)
    if not fa or not fb:
        return "khong_co", ""
    if fa == fb:
        return "khop", ""
    if _tok():
        try:
            if _yomi(fa) == _yomi(fb):
                return "khop_doc", ""
        except Exception:                                          # noqa: BLE001
            pass
    d = _khac(fb, fa)
    if _tok():
        def _cung_doc(x, y):
            try:
                return bool(x and y) and _yomi(x) == _yomi(y)
            except Exception:                                  # noqa: BLE001
                return False
        d = [(x, y) for x, y in d if not _cung_doc(x, y)]
    if not d:
        return "khop_doc", ""
    nchar = sum(max(len(x), len(y)) for x, y in d)
    ct = "; ".join(f"'{x}'→'{y}'" for x, y in d[:4])
    return ("lech_nhe" if nchar <= 2 else "lech_nang"), ct


# ---------------- câu sai dạng ----------------
def sai_dang(row):
    """Trả lý do nếu câu không thuộc dạng 19 (Q1 duyệt 08/10/2026), không thì None."""
    if row.get("cap_do") in ("N1", "N2") or "返事" in (row.get("doan_van") or ""):
        return "Đề 問題4 即時応答 (nghe câu rồi chọn câu đáp lại) – thuộc dạng 20 Trả lời nhanh"
    if (row.get("lua_chon_4") or "").strip():
        return "Đề 4 lựa chọn kiểu nghe hiểu nhiệm vụ / điểm chính – không phải 発話表現"
    return None


# ---------------- gắn cờ (giai đoạn 0) ----------------
FLAG_TEXT = {
    "khuon_B": "Lời giải KHÔNG có phần dịch tình huống (chỉ có 3 khối phân tích) – utterance.meaning = null; tác tử KIỂM TRA gắn cờ thieu_noi_dung",
    "khuon_D": "Lời giải chỉ dịch tình huống + 3 lựa chọn, KHÔNG có ĐÚNG/SAI và phân tích – sentence.ja lấy từ transcript, is_correct theo đáp án, analysis = null; gắn cờ thieu_noi_dung",
    "tinh_huong_tu_doan_van": "Câu tình huống tiếng Nhật lấy từ cột doan_van (transcript không dùng được)",
    "khong_co_tinh_huong_ja": "Không tìm được câu tình huống tiếng Nhật (transcript / đoạn văn) – utterance.ja = '' ; gắn cờ thieu_noi_dung",
    "tinh_huong_khong_nanto": "Câu tình huống trong transcript không có '何と言いますか' (vẫn dùng – Claude xem lại có tách đúng không)",
    "tinh_huong_nhieu_dong": "Câu tình huống (transcript) nhiều dòng – giữ \\n",
    "tr_khong_du_lua_chon": "Transcript không tách được đủ 3 câu nói",
    "tr_ghi_chu": "Transcript trình bày lạ (lựa chọn không đánh số / có dòng thừa) – xem norm.tr_ghi_chu",
    "lc_lech_transcript_nhe": "Câu nói trong lời giải lệch nhẹ transcript (1–2 ký tự – nghi gõ)",
    "lc_lech_transcript_nang": "Câu nói trong lời giải KHÁC transcript về chữ (nghi lỗi nội dung → Claude xem, gắn cờ cau_khac_de)",
    "nghia_dau_lech": "Dòng nghĩa ở phần đầu khác dòng 'Nghĩa:' của khối lựa chọn (JSON theo dòng 'Nghĩa:')",
    "so_khoi_khac_3": "Phần phân tích không có đúng 3 khối lựa chọn",
    "thieu_nghia": "Có khối lựa chọn không có dòng 'Nghĩa:'",
    "thieu_ket_luan": "Có khối lựa chọn không có dòng '→ ĐÚNG/SAI'",
    "thieu_phan_tich": "Có khối lựa chọn không có đoạn phân tích",
    "nhan_lap": "Có khối lựa chọn với nhãn lặp (2 dòng 'Nghĩa:' / 2 dòng '→ …')",
    "ket_luan_lech_dap_an": "'→ ĐÚNG' không nằm ở đáp án của đề hoặc số chỗ ĐÚNG ≠ 1 (nghi đáp án / lời giải)",
    "co_truoc_khoi": "Có dòng chữ giữa ### và khối lựa chọn 1",
    "ruby_han_viet": "Bản gốc có furigana đọc Hán Việt gắn lên chữ Hán trong câu tiếng Việt – Python đã đổi thành chữ Việt",
    "co_anh": "Đề có ảnh (link trong doan_van / cau_hoi) – Excel CTV hiện link",
    "co_furigana": "Có furigana",
    "ruby_hong": "Có ruby hỏng trong bản gốc",
    "ky_hieu_trung": "Bản gốc có sẵn ký hiệu ｜《》 (trùng ký hiệu furigana)",
    "danh_dau_rac": "Bản gốc có đoạn in đậm / gạch chân rỗng hoặc chỉ là dấu câu (đã bỏ thẻ)",
}
CTV_FLAGS = ("ket_luan_lech_dap_an", "lc_lech_transcript_nang", "khuon_B", "khuon_D", "khong_co_tinh_huong_ja", "tinh_huong_tu_doan_van")
# utterance.ja lấy từ transcript (furigana của transcript, không có trong lời giải); correct.option_ja = bản sao sentence.ja
FURI_SKIP = [("prompt", "utterance", "ja"), ("correct", "option_ja")]


def gan_co(phan, tr_opts, dap, ghi_chu):
    """Cờ từ kết quả tách. Ghi thêm ghi chú [Bản gốc VI] vào ghi_chu. Cập nhật phan['so_transcript']."""
    co = []
    k = phan["khuon"]
    khoi = phan["khoi"]
    if k == "B":
        co.append("khuon_B")
        ghi_chu.append("[Bản gốc VI] Lời giải không có phần dịch câu tình huống (chỉ có phân tích 3 lựa chọn)")
    if k == "D":
        co.append("khuon_D")
        ghi_chu.append("[Bản gốc VI] Lời giải chỉ dịch tình huống và 3 lựa chọn – không có kết luận ĐÚNG/SAI và phân tích")
    if k in ("A", "B"):
        if len(khoi) != 3:
            co.append("so_khoi_khac_3")
        if any(x["nghia"] is None for x in khoi):
            co.append("thieu_nghia")
        if any(x["ket_luan"] is None for x in khoi):
            co.append("thieu_ket_luan")
        if any(not x["phan_tich"] for x in khoi):
            co.append("thieu_phan_tich")
        if any(x["nhan_lap"] for x in khoi):
            co.append("nhan_lap")
        dung = [x["so"] for x in khoi if x["ket_luan"] is True]
        if dap and dung != [dap]:
            co.append("ket_luan_lech_dap_an")
            ghi_chu.append(f"[Bản gốc VI] Lời giải kết luận ĐÚNG ở lựa chọn {dung or 'không có'} – đáp án của đề là {dap}")
        if phan.get("truoc_khoi"):
            co.append("co_truoc_khoi")
    nd = phan.get("nghia_dau") or []
    if nd and len(nd) == len(khoi):
        lech = [i + 1 for i, (a, b) in enumerate(zip(nd, khoi)) if b["nghia"] is not None
                and re.sub(r"\W", "", a.lower()) != re.sub(r"\W", "", b["nghia"].lower())]
        if lech:
            co.append("nghia_dau_lech")
            ghi_chu.append(f"[Bản gốc VI] Dòng nghĩa ở phần đầu khác dòng 'Nghĩa:' của lựa chọn {lech} (JSON theo dòng 'Nghĩa:')")
    so = []
    for x in khoi:
        if x.get("ja") and x["so"] <= len(tr_opts):
            kq, ct = so_cau(x["ja"], tr_opts[x["so"] - 1])
            so.append({"so": x["so"], "ket_qua": kq, "chi_tiet": ct})
            if kq in ("lech_nhe", "lech_nang"):
                co.append("lc_lech_transcript_" + kq.split("_")[1])
                ghi_chu.append(f"[Bản gốc VI] Lựa chọn {x['so']}: câu tiếng Nhật trong lời giải {'lệch nhẹ' if kq == 'lech_nhe' else 'khác'} transcript ({ct})")
    phan["so_transcript"] = so
    return co


# ---------------- thứ tự chạy ----------------
def tao_thu_tu(recs, cfg):
    """12 câu đầu = lô pilot (4 N3 / 4 N4 / 4 N5: 1 khuôn B, 1 khuôn D, 1 câu có ảnh, ưu tiên câu có furigana); tới câu 100 xen kẽ N3/N4/N5 khuôn A;
    sau đó các câu còn lại theo file dữ liệu. Chỉ gồm câu chạy được (khuôn A / B / D)."""
    import random
    tc = cfg.get("thu_tu_chay") or {}
    rng = random.Random(tc.get("seed", 2026))
    chay = [r for r in recs if r["khuon_goc"] in ("A", "B", "D")]
    lv = ["N3", "N4", "N5"]
    pilot = {k: [] for k in lv}
    dung = set()

    def lay(pool, k):
        pool = [r for r in pool if r["sample_id"] not in dung]
        if pool:
            r = rng.choice(pool)
            pilot[k].append(r)
            dung.add(r["sample_id"])

    b = [r for r in chay if r["khuon_goc"] == "B"]
    if b:
        lay(b[:1], b[0]["cap_do"])
    lay([r for r in chay if r["khuon_goc"] == "D" and r["cap_do"] == "N4"], "N4")
    anh = [r for r in chay if "co_anh" in r["co"] and r["sample_id"] not in dung]
    if anh and not any("co_anh" in r["co"] for k in lv for r in pilot[k]):
        r0 = rng.choice(anh)
        lay([r0], r0["cap_do"])
    for k in lv:
        while len(pilot[k]) < 4:
            a = [r for r in chay if r["cap_do"] == k and r["khuon_goc"] == "A" and r["sample_id"] not in dung]
            fu = [r for r in a if "co_furigana" in r["co"]]
            if not a:
                break
            lay(fu if fu and len(pilot[k]) % 2 == 0 else a, k)
    dau = [pilot[k][i] for i in range(4) for k in lv if i < len(pilot[k])]
    n = int(tc.get("dau_tien", 100))
    pools = {k: [r for r in chay if r["cap_do"] == k and r["khuon_goc"] == "A" and r["sample_id"] not in dung] for k in lv}
    for k in lv:
        rng.shuffle(pools[k])
    while len(dau) < n and any(pools.values()):
        for k in lv:
            if pools[k] and len(dau) < n:
                r = pools[k].pop()
                dau.append(r)
                dung.add(r["sample_id"])
    rows = dau + [r for r in chay if r["sample_id"] not in dung]
    return [{"stt": i + 1, "sample_id": r["sample_id"], "question_id": r["question_id"], "cap_do": r["cap_do"], "khuon": r["khuon_goc"]}
            for i, r in enumerate(rows)]


# ---------------- nhãn cố định của lời giải gốc (bỏ khi đo độ phủ) ----------------
LABELS = [r"(?im)^\s*[-+•]?\s*nghĩa\s*[:：]", r"(?m)^\s*(?:→|⇒|->|=>)\s*(?:ĐÚNG|SAI|Đúng|Sai|đúng|sai)(?![\wÀ-ỹ])\s*[.。!]?", r"#{3,}"]


def strip_labels(text):
    for pat in LABELS:
        text = re.sub(pat, " ", text)
    return text


# ---------------- hook cho claude_tao.gd1_nhan: Python điền prompt.utterance.ja ----------------
def bo_sung(doc, norm):
    pr = doc.get("prompt")
    if isinstance(pr, dict) and isinstance(pr.get("utterance"), dict):
        pr["utterance"]["ja"] = norm.get("tinh_huong_ja") or ""
    return doc


# ---------------- kiểm tra riêng giai đoạn 1 ----------------
def check_k(doc, norm, policy):
    loi, cb = [], []
    ph = norm.get("phan") or {}
    dap = norm["de"]["dap_an_so"]
    tr = norm.get("tr_lua_chon") or []
    pr, c = doc.get("prompt") or {}, doc.get("correct") or {}
    ut = pr.get("utterance") or {}
    # K-TH – câu tình huống (Python điền)
    if (ut.get("ja") or "") != (norm.get("tinh_huong_ja") or ""):
        loi.append("K-TH: prompt.utterance.ja phải đúng câu tình huống Python tách từ transcript (Python điền khi --nhan – không sửa tay)")
    if ut.get("reading") is not None:
        loi.append("K-TH: prompt.utterance.reading phải là null (lời giải không có dòng cách đọc)")
    if pr.get("situation") is not None:
        loi.append("K-TH: prompt.situation phải là null (dạng 19)")
    if pr.get("analysis") != []:
        loi.append("K-TH: prompt.analysis phải là [] (lời giải không phân tích câu tình huống)")
    th = ph.get("tinh_huong_vi")
    if (th is None) != (ut.get("meaning") is None):
        loi.append("K8: prompt.utterance.meaning phải null khi và chỉ khi lời giải không có phần dịch tình huống")
    elif th:
        cv, miss = _cover(th, _v(ut.get("meaning")))
        if cv < 0.97:
            loi.append(f"K9: prompt.utterance.meaning thiếu chữ so với phần dịch tình huống: {miss}")
    # K1 – các lựa chọn
    khoi = ph.get("khoi") or []
    opts = doc.get("options") or []
    n = len(khoi) or len(tr) or 3
    if [o.get("index") for o in opts] != list(range(1, n + 1)):
        loi.append(f"K1: options phải có đủ {n} lựa chọn theo thứ tự 1–{n} (đang có {[o.get('index') for o in opts]})")
    for o in opts:
        i = o.get("index")
        if not isinstance(i, int) or not 1 <= i <= n:
            continue
        k = khoi[i - 1] if i <= len(khoi) else None
        s = o.get("sentence") or {}
        ja_src, nguon = (k["ja"], "dòng 'i.' của lời giải") if k and k.get("ja") else ((tr[i - 1], "transcript (khuôn D)") if i <= len(tr) else (None, ""))
        if ja_src and _k(s.get("ja")) != _k(ja_src):
            loi.append(f"K8: lựa chọn {i}: sentence.ja '{s.get('ja')}' khác {nguon} '{ja_src}'")
        if s.get("reading") is not None:
            loi.append(f"K8: lựa chọn {i}: sentence.reading phải là null")
        if k is None:
            continue
        if (k["nghia"] is None) != (s.get("meaning") is None):
            loi.append(f"K4: lựa chọn {i}: sentence.meaning phải null khi và chỉ khi lời giải không có dòng 'Nghĩa:'")
        elif k["nghia"]:
            cv, miss = _cover(k["nghia"], _v(s.get("meaning")))
            if cv < 0.97:
                loi.append(f"K9: lựa chọn {i}: sentence.meaning thiếu chữ so với dòng 'Nghĩa:': {miss}")
        if k["ket_luan"] is not None and o.get("is_correct") is not k["ket_luan"]:
            loi.append(f"K7: lựa chọn {i}: is_correct phải là {k['ket_luan']} (lời giải: → {'ĐÚNG' if k['ket_luan'] else 'SAI'})")
        if k["ket_luan"] is None and o.get("is_correct") is not (i == dap):
            loi.append(f"K7: lựa chọn {i}: lời giải không có '→ ĐÚNG/SAI' – is_correct theo đáp án của đề ({i == dap})")
        if (not k["phan_tich"]) != (o.get("analysis") is None):
            loi.append(f"K12: lựa chọn {i}: analysis phải null khi và chỉ khi lời giải không có đoạn phân tích")
        elif k["phan_tich"]:
            cv, miss = _cover(k["phan_tich"], _v(o.get("analysis")))
            if cv < 0.97:
                loi.append(f"K9: lựa chọn {i}: analysis thiếu chữ so với bản gốc: {miss}")
    # K6 – đáp án
    if str(c.get("index")) != str(dap):
        loi.append(f"K6: correct.index = {c.get('index')} khác dap_an_so = {dap}")
    elif isinstance(dap, int) and 1 <= dap <= len(opts):
        if c.get("option_ja") != (opts[dap - 1].get("sentence") or {}).get("ja"):
            loi.append(f"K6: correct.option_ja phải giống hệt options[{dap - 1}].sentence.ja")
    if c.get("full_sentence") is not None:
        loi.append("K6: correct.full_sentence phải là null (dạng 19)")
    dung = [o.get("index") for o in opts if o.get("is_correct") is True]
    if dung != [dap]:
        cb.append(f"K11: lời giải kết luận ĐÚNG ở {dung or 'không lựa chọn nào'} – đáp án của đề là {dap} (quy tắc 3d-5: gắn cờ dap_an)")
    loi += TK.kiem_tra(doc, None)
    # cảnh báo theo cờ s0
    co = set(norm.get("co") or [])
    for x in ph.get("so_transcript") or []:
        if x["ket_qua"] in ("lech_nhe", "lech_nang"):
            cb.append(f"K-LC: lựa chọn {x['so']}: câu trong lời giải {'lệch nhẹ' if x['ket_qua'] == 'lech_nhe' else 'khác'} transcript ({x['chi_tiet']}) – "
                      + ("xác định bên sai: lời giải → sửa định dạng; transcript → [Ghi chú]" if x["ket_qua"] == "lech_nhe" else "khác chữ → gắn cờ cau_khac_de (3d-4)"))
    if co & {"khuon_B", "khuon_D", "khong_co_tinh_huong_ja"}:
        cb.append("K-ND: lời giải thiếu phần dịch tình huống / phân tích / câu tình huống – gắn cờ thieu_noi_dung (quy tắc 3d-6)")
    return loi, cb


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


def is_style_field(path):
    """Phân tích (dịch từ tiếng Việt) – kiểm tra văn phong -습니다; nghĩa câu (dịch từ tiếng Nhật) thì không."""
    p = path if isinstance(path, str) else path_str(path)
    return not re.search(r"utterance\.meaning|sentence\.meaning", p)


def sudachi_hints(norm):
    """Gợi ý cho bước 1.2: câu nói trong lời giải ↔ transcript (đã so theo cách đọc)."""
    out = []
    for x in (norm.get("phan") or {}).get("so_transcript") or []:
        if x["ket_qua"] in ("lech_nhe", "lech_nang"):
            out.append(f"LC: lựa chọn {x['so']} – lời giải ↔ transcript: {x['ket_qua']} ({x['chi_tiet']})")
    return out


# ---------------- hiển thị cho Excel CTV ----------------
def _t(obj, lang):
    return show((obj or {}).get(lang) or "") if obj else ""


def render(d, lang):
    pr, c = d.get("prompt") or {}, d.get("correct") or {}
    ut = pr.get("utterance") or {}
    out = [f"{bold('【Tình huống】')} {show(ut.get('ja', ''))}"]
    if ut.get("meaning"):
        out.append(f"   Nghĩa: {_t(ut['meaning'], lang)}")
    out.append(bold("【PHÂN TÍCH】"))
    for o in d.get("options", []):
        s = o.get("sentence") or {}
        out.append(bold(f"{o.get('index')}. ") + show(s.get("ja", "")))
        if s.get("meaning"):
            out.append("   Nghĩa: " + _t(s["meaning"], lang))
        out.append("   → " + ("ĐÚNG." if o.get("is_correct") else "SAI."))
        if o.get("analysis"):
            out.append("   " + _t(o["analysis"], lang).replace("\n", "\n   "))
    out.append(bold("【LỰA CHỌN ĐÚNG】") + f" {c.get('index')}. {show(c.get('option_ja', ''))}")
    out += TK.render(d, lang, show, bold)
    return "\n".join(out)
