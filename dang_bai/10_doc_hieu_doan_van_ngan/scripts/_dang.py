"""Phần riêng của dạng 10 – Đọc hiểu: Đoạn văn ngắn (dựng 2026-10-08 trên khung dạng 08).

Phần chung kế thừa dạng 07/08 (cấu hình, đường dẫn, thứ tự chạy --tu/--den, kho đã duyệt, bản tạo Claude, Hán Việt, gợi ý định dạng).
Phần riêng dạng 10 ở cuối file: tách khuôn A (phân tích từng lựa chọn) / khuôn B (dịch cả bài) thành khung (khung_python),
tách câu trích dẫn đứng riêng dòng, so trích dẫn với đoạn văn gốc (K-TD), dò chữ Hán chèn vào câu Việt (K-KC),
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
    os.environ["PIPELINE_DATA"] = _c.get("du_lieu_test", "data/test_10_doc_hieu_doan_van_ngan.csv")


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
    """Các mẫu bị loại theo config.loc_nguon_de (quyết định 2026-10-11): từ mẫu tu_mau (stt theo thu_tu() = output/thu_tu_chay.csv (đúng thứ tự --tu/--den)),
    bỏ mẫu mà cột `cot` (thi_thu_thuoc_de) chứa một trong `bo_neu_chua` (mặc định 'Nat Test'). Trả về {sample_id: giá trị cột}."""
    lc = cfg().get("loc_nguon_de") or {}
    if CA_NAT or not lc.get("bat"):
        return {}
    from pipeline_chung.common import read_csv
    cot, tu, kw = lc.get("cot", "thi_thu_thuoc_de"), int(lc.get("tu_mau", 1)), lc.get("bo_neu_chua") or ["Nat Test"]
    gt = {sid_of(r): r.get(cot) or "" for r in read_csv(data_path())}
    nat = {x for x, v in gt.items() if any(k.lower() in v.lower() for k in kw)}
    nhom_cot, p = lc.get("nhom_theo"), OUT("thu_tu_chay.csv")
    if nhom_cot and os.path.exists(p):           # lọc trọn nhóm: không cắt đôi đoạn văn
        nhom = {}
        for r in read_csv(p):
            if r.get(nhom_cot):
                nhom.setdefault(r[nhom_cot], []).append(r["sample_id"])
        lan = [k for k, v in nhom.items() if 0 < sum(x in nat for x in v) < len(v)]
        if lan:
            sys.exit(f"Lọc nguồn đề: {len(lan)} nhóm {nhom_cot} LẪN câu NAT và câu không NAT ({lan[:5]}) – chưa có quyết định"
                     " cách xử lý (bỏ cả nhóm / giữ cả nhóm / lọc từng câu): DỪNG, hỏi người dùng. Tạm chạy cả NAT: thêm --ca-nat")

    return {x: gt.get(x, "") for i, x in enumerate(thu_tu(), 1) if i >= tu and x in nat}


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




# ---------------- nhãn cố định của lời giải gốc (bỏ khi đo độ phủ) ----------------
# ---------------- so sánh câu tiếng Nhật ----------------
# ---------------- tách lời giải ### thành các phần (giai đoạn 0) ----------------
HEAD_LAB_RE = re.compile(r"(?i)^\s*[-+•]?\s*(cách đọc|nghĩa)\s*[:：]\s*(.*)$", re.S)
FURI_VI_RE = re.compile(r"｜([^｜《》\n]*?[A-Za-zÀ-ỹĐđ][^｜《》\n]*?)《([^》\n]*)》")


def bo_furigana_chu_viet(text):
    """Bỏ furigana gắn lên chữ tiếng Việt / Latin (vd '- ｜Nhận xét《にんてい》:') – lỗi định dạng bản gốc.
    Trả (text, [(cũ, mới)])."""
    doi = []
    def _r(m):
        doi.append((m.group(0), m.group(1)))
        return m.group(1)
    return FURI_VI_RE.sub(_r, text), doi


FURI_NHAY_RE = re.compile(r"｜(['\"‘’])(?=[^｜《》\n]*《)")


def bo_dong_vi_tri_sao(text):
    """Bản so furigana: bỏ dòng 'Vị trí ★: …' (JSON dạng 08 không có trường này – furigana ở dòng đó bị tính thiếu, 54781)."""
    return re.sub(r"(?im)^[ \t]*[-+•]?[ \t]*Vị trí\s*★\s*[:：].*$", "", text or "")


def sua_furi_nhay(text):
    """'｜'声《こえ》' (dấu ｜ của furigana đặt trước dấu nháy – 54644, 54784) → ''｜声《こえ》'. Trả (text, số chỗ)."""
    return FURI_NHAY_RE.subn(r"\1｜", text)


TACH_DOC_RE = re.compile(r"(?<=[。．！？｣」])[ \t　]*(?=(?:Cách đọc|Nghĩa)\s*[:：])")


def tach_dong_cach_doc(text):
    """'…タイプだ。Cách đọc: …' (nhãn dính sau câu tiếng Nhật) → xuống dòng trước nhãn. Trả (text, số chỗ tách)."""
    return TACH_DOC_RE.subn("\n", text)


def head_part(dau):
    """Phần đầu → {cau, doc, nghia, khac}: các dòng trước nhãn đầu tiên là câu đề (hội thoại: nhiều dòng)."""
    res, cur = {"cau": [], "doc": [], "nghia": [], "khac": [], "nhan_de": []}, "cau"
    for line in (dau or "").split("\n"):
        if not line.strip():
            continue
        m = HEAD_LAB_RE.match(line)
        if m:
            cur = "doc" if m.group(1).lower() == "cách đọc" else "nghia"
            if res[cur]:                       # nhãn lặp → phần thừa
                res["khac"].append(line.strip())
                cur = "khac"
                continue
            if m.group(2).strip():             # nhãn đứng riêng dòng (hội thoại – 11189): nội dung ở các dòng sau
                res[cur].append(m.group(2).strip())
            continue
        if cur == "cau" and not res["cau"]:
            m2 = re.match(r"(?i)^\s*(đề bài|câu hỏi|đề)\s*[:：]\s*", line)
            if m2 and not line[m2.end():].strip():   # 'Đề bài:' đứng riêng dòng (11189)
                res["nhan_de"] = [m2.group(0).strip()]
                continue
            if m2 and line[m2.end():].strip():
                res["nhan_de"] = [m2.group(0).strip()]
                line = line[m2.end():]
        if cur == "cau" and res["cau"] and not re.search(r"[぀-ヿ㐀-鿿_＿]", line):
            cur = "khac"                       # dòng tiếng Việt chen giữa – không phải câu đề
        res[cur].append(line.strip())
    return {k: ("\n".join(v) if v else None) for k, v in res.items()}


def doc_tu_furigana(cau):
    """Cách đọc ghép từ furigana của câu đề: chỉ khi furigana phủ hết mọi chữ Hán (không còn chữ Hán ngoài ｜《》)."""
    if not cau or "《" not in cau:
        return None
    doc = _doc_furi(cau).replace("{", "").replace("}", "")
    return None if re.search(r"[㐀-鿿々〆]", doc) else doc


# ---------------- gắn cờ (giai đoạn 0) ----------------
# ---------------- kiểm tra riêng giai đoạn 1: K1–K13 (K8/K9 = trung thành với bản gốc: chép câu Nhật đúng lời giải / đủ chữ – Python kiểm tra trên bản đã hoàn tác chỗ sửa định dạng) ----------------
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
# ================  DẠNG 10 – ĐỌC HIỂU ĐOẠN VĂN NGẮN: phần riêng (dựng 2026-10-08)  ====================
# =====================================================================================================
# Khuôn A (~780 câu) – lời giải đã chuẩn hóa:
#   <câu hỏi tiếng Nhật>                         → question.ja
#   <nghĩa câu hỏi>                              → question.meaning
#   (câu chữ khác trước lựa chọn 1)              → summary[0].points (phân tích chung, heading = null)
#   i. <lựa chọn tiếng Nhật>                     → options[i].option_ja
#   Nghĩa: …                                     → options[i].meaning
#   Trích dẫn: 「…」 (dịch)  /  「…」\n(dịch)      → options[i].quotes[] = {ja, meaning}   (câu trích dẫn ĐỨNG RIÊNG dòng)
#   các dòng còn lại (kể cả trích dẫn nằm trong câu)→ options[i].analysis   (bỏ nhãn 'Giải thích:' / 'Phân tích:' đầu dòng)
#   → ĐÚNG / → SAI                               → options[i].is_match
# Khuôn B (49 câu, chủ yếu N1): 'Đoạn văn:' (dịch cả bài) → full_translation; 'Câu hỏi:' + dịch câu hỏi → question.meaning;
#   4 dòng dịch lựa chọn → options[i].meaning; 'Câu trả lời đúng là:' (trùng lựa chọn) → bỏ; câu chữ khác → analysis của đáp án.
#   question.ja / option_ja lấy từ ĐỀ (lời giải không có tiếng Nhật).
# Khuôn lẻ (~18 câu: không đủ '1.'–'4.', JSON / ### / văn bản trơn): không có khung – tác tử TẠO đặt theo nội dung, KIỂM TRA soát kỹ.

VI_L = "A-Za-zÀ-ỹĐđ"
JA_C = re.compile(r"[぀-ヿ㐀-鿿々〆ヶｦ-ﾟ]")


def _bare(s):
    return FURI_RE.sub(lambda m: m.group(1), s or "")


def la_tieng_nhat(s):
    """Dòng toàn tiếng Nhật (không có chữ Latin / Việt ngoài furigana)."""
    b = _bare(s).replace("{", "").replace("}", "")
    return bool(JA_C.search(b)) and not re.search(rf"[{VI_L}]{{2,}}", b)


OPT10_RE = re.compile(r"^\s*\{?\s*([1-4])\s*\}?\s*[\.．]\s*(.*)$")
NGHIA10_RE = re.compile(r"^\s*[-•*+]?\s*\{?\s*Nghĩa\s*\}?\s*[:：]\s*(.*)$", re.I)
KL_RE = re.compile(r"^\s*[-=]*\s*[→➝⇒]\s*\{?\s*(ĐÚNG|SAI|Đúng|Sai|đúng|sai)\s*\}?\s*[.。!]?\s*$")
NHAN_TRICH = (r"(?:câu\s+)?trích(?:\s+dẫn)?(?:\s+câu)?(?:\s+(?:trong\s+)?đoạn\s+văn)?"
              r"|｜引用《いんよう》|｜引用文《いんようぶん》|引用|引用文")
NHAN_TRICH_RE = re.compile(rf"^\s*[-•*+]?\s*\{{?\s*(?:{NHAN_TRICH})\s*\}}?\s*[:：]\s*(.*)$", re.I)
NHAN_GT_RE = re.compile(r"^(\s*[-•*+]?\s*)\{?\s*(?:Giải thích|Phân tích)\s*\}?\s*[:：]\s*(.*)$", re.I)
NHAN_CH_RE = re.compile(r"^\s*[-•*+]?\s*\{?\s*Câu hỏi\s*\}?\s*[:：]\s*(.*)$", re.I)
PAREN_RE = re.compile(r"^\s*[\(（](.+)[\)）]\s*[.。]?\s*$", re.S)
Q_RE = re.compile(r"^(?P<ja>(?:「[^」\n]*」\s*)+|[^()（）\n]+?)\s*(?:[\(（](?P<vi>.+)[\)）])?\s*[.。]?\s*$")
NHAN_DAM10_RE = re.compile(r"\{\s*((?:Đoạn văn|Câu hỏi|Trích dẫn|Câu trích dẫn|Giải thích|Phân tích|Nghĩa|Câu trả lời đúng là|"
                           r"Đáp án đúng|ĐÚNG|SAI|Đúng|Sai)\s*[:：.]?)\s*\}")


def bo_dam_nhan(text):
    """Bỏ { } (in đậm) quanh nhãn cố định ('{Đoạn văn:}', '{Trích dẫn:}', '→ {ĐÚNG}') – trình bày, không phải nội dung."""
    return NHAN_DAM10_RE.subn(r"\1", text)


def bo_nhan_trich_dan(text):
    """Bản dùng để KIỂM TRA (src_text): bỏ nhãn 'Trích dẫn:' / '｜引用《いんよう》:' … ở đầu dòng – JSON không chép các nhãn này
    (kể cả nhãn viết bằng chữ Hán) nên không tính là mất tiếng Nhật / furigana."""
    out = []
    for ln in (text or "").split("\n"):
        m = NHAN_TRICH_RE.match(ln)
        if m:
            pre = re.match(r"^\s*[-•*+]?\s*", ln).group(0)
            ln = (pre + m.group(1)) if m.group(1).strip() else ""
        out.append(ln)
    return "\n".join(out)


def tach_trich_dan(s):
    """Dòng (đã bỏ gạch đầu dòng / nhãn trích dẫn / câu dẫn) là câu trích dẫn đứng riêng? → (ja, vi | None) hoặc None."""
    m = Q_RE.match(s)
    if not m:
        return None
    ja, vi = m.group("ja").strip(), m.group("vi")
    if not la_tieng_nhat(ja) or len(_bare(ja)) < 3:
        return None
    if vi is not None and not re.search(rf"[{VI_L}]{{2,}}", vi):
        return None
    mm = re.fullmatch(r"「([^」]*)」", ja)
    return (mm.group(1).strip() if mm else ja), (vi.strip() if vi else None)


def tach_than(lines):
    """Thân phân tích của một lựa chọn → (quotes [{ja, vi}], analysis_lines, nhãn đã bỏ)."""
    quotes, ana, bo = [], [], []
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            ana.append("")
            i += 1
            continue
        m = NHAN_TRICH_RE.match(s)
        if m:
            bo.append(s[:len(s) - len(m.group(1))].strip())
            s = m.group(1).strip()
            if not s:
                i += 1
                continue
        bullet = re.match(r"^[-•*+]\s*", s)
        core = s[bullet.end():] if bullet else s
        lead = None
        mlead = re.match(rf"^(.*?[{VI_L}].*?[:：])\s*(「.*)$", core)
        if mlead and not la_tieng_nhat(mlead.group(1)):
            lead, core = mlead.group(1), mlead.group(2)
        q = tach_trich_dan(core)
        if q:
            ja, vi = q
            if vi is None and i + 1 < len(lines):
                pm = PAREN_RE.match(lines[i + 1].strip())
                if pm and re.search(rf"[{VI_L}]{{2,}}", pm.group(1)):
                    vi = pm.group(1).strip()
                    i += 1
            if lead:
                ana.append((bullet.group(0) if bullet else "") + lead)
            quotes.append({"ja": ja, "vi": vi})
            i += 1
            continue
        mg = NHAN_GT_RE.match(s)
        if mg:
            bo.append(s[len(mg.group(1)):len(s) - len(mg.group(2))].strip())
            s = (mg.group(1) + mg.group(2)).strip() if mg.group(2).strip() else ""
            if not s:
                i += 1
                continue
        ana.append(s)
        i += 1
    out = []
    for x in ana:
        if x == "" and (not out or out[-1] == ""):
            continue
        out.append(x)
    while out and out[-1] == "":
        out.pop()
    return quotes, out, bo


def tach_khuon_a(text):
    head, items, cur = [], [], None
    for ln in (text or "").split("\n"):
        m = OPT10_RE.match(ln)
        nxt = (items[-1]["so"] + 1) if items else 1
        if m and int(m.group(1)) == nxt and m.group(2).strip():
            cur = {"so": nxt, "tieu_de": m.group(2).strip(), "dong": []}
            items.append(cur)
            continue
        (cur["dong"] if cur else head).append(ln)
    return head, items


def phan_dau(head):
    """Phần trước lựa chọn 1 → {ja, nghia, khac[], nhan[]}: dòng tiếng Nhật đầu = câu hỏi, dòng Việt kế tiếp = nghĩa, còn lại = khac."""
    ja, vi, khac, nhan = [], [], [], []
    for ln in head:
        s = ln.strip()
        if not s:
            continue
        m = NHAN_CH_RE.match(s)
        if m and not ja:
            nhan.append("Câu hỏi:")
            s = m.group(1).strip()
            if not s:
                continue
        if la_tieng_nhat(s) and not vi and not khac:
            ja.append(s)
        elif ja and not vi and not khac:
            vi.append(s)
        else:
            khac.append(s)
    return {"ja": "\n".join(ja) or None, "nghia": "\n".join(vi) or None, "khac": khac, "nhan": nhan}


def phan_lua_chon(it):
    tieu_de = it["tieu_de"]
    nghia, ket_luan, than, sau = None, None, [], []
    mh = re.match(r"^(.*?)\s*Nghĩa\s*[:：]\s*(.*)$", tieu_de)
    if mh and la_tieng_nhat(mh.group(1)):
        tieu_de, nghia = mh.group(1).strip(), mh.group(2).strip()
    for ln in it["dong"]:
        s = ln.strip()
        if ket_luan is not None:
            if s:
                sau.append(s)
            continue
        mn = NGHIA10_RE.match(s)
        if mn and nghia is None and not any(x.strip() for x in than):
            nghia = mn.group(1).strip()
            continue
        mk = KL_RE.match(s)
        if mk:
            ket_luan = mk.group(1).upper()
            continue
        than.append(ln)
    quotes, ana, bo = tach_than(than)
    if sau:
        ana = ana + ([""] if ana else []) + sau
    return {"so": it["so"], "option_ja": tieu_de, "nghia": nghia, "ket_luan": ket_luan, "quotes": quotes,
            "analysis": "\n".join(ana) or None, "nhan_bo": bo, "co_sau_ket_luan": bool(sau)}


# ---------------- khuôn B ----------------
B_DV_RE = re.compile(r"(?im)^\s*\{?\s*Đoạn văn\s*\}?\s*[:：]\s*$")
B_CH_RE = re.compile(r"(?im)^\s*\{?\s*Câu hỏi\s*\}?\s*[:：]\s*(.*)$")
B_DA_RE = re.compile(r"(?im)^\s*\{?\s*(?:Câu trả lời đúng(?: là)?|Đáp án đúng(?: là)?)\s*\}?\s*[:：]\s*(.*)$")


def la_khuon_b(text):
    return bool(B_DV_RE.search(text or ""))


def _bo_dau_dong(s):
    s = re.sub(r"^\s*[-•*+]\s*", "", s)
    return re.sub(r"^\s*\{?[1-4]\}?\s*[\.．)]\s*", "", s).strip()


def tach_khuon_b(text):
    """→ {doan_van_dich[], cau_hoi_vi, lua_chon_vi[], dap_an_dong, giai_thich[], dau_khac[]} hoặc None nếu không tách được."""
    m = B_DV_RE.search(text)
    if not m:
        return None
    dau_khac = [x.strip() for x in text[:m.start()].split("\n") if x.strip()]
    rest = text[m.end():]
    mc = B_CH_RE.search(rest)
    if not mc:
        return None
    dv = [x.strip() for x in rest[:mc.start()].split("\n") if x.strip()]
    after = ([mc.group(1).strip()] if mc.group(1).strip() else []) + [x.strip() for x in rest[mc.end():].split("\n") if x.strip()]
    if not after:
        return None
    cau_hoi_vi, after = after[0], after[1:]
    lc, i = [], 0
    while i < len(after) and len(lc) < 4 and not B_DA_RE.match(after[i]):
        lc.append(_bo_dau_dong(after[i]))
        i += 1
    after = after[i:]
    da, gt = None, []
    j = 0
    while j < len(after):
        md = B_DA_RE.match(after[j])
        if md and da is None:
            da = md.group(1).strip()
            if not da and j + 1 < len(after):
                da = _bo_dau_dong(after[j + 1])
                j += 1
            j += 1
            continue
        gt.append(after[j])
        j += 1
    return {"doan_van_dich": dv, "cau_hoi_vi": cau_hoi_vi, "lua_chon_vi": lc, "dap_an_dong": da, "giai_thich": gt, "dau_khac": dau_khac}


# ---------------- chữ Hán chèn vào câu Việt (K-KC) ----------------
_TOKKC = r"(?:｜[^｜《》\n]+《[^《》\n]+》|[㐀-鿿々])(?:[㐀-鿿々]|｜[^｜《》\n]+《[^《》\n]+》|[ぁ-ん]{0,2})*"
KC_RE = re.compile(rf"(?<=[{VI_L}][ /])({_TOKKC})(?=[ ,.;:/)]?\s?[{VI_L}])")
_TRONG_NHAY = re.compile(r"「[^」\n]*」|『[^』\n]*』|\"[^\"\n]*\"|“[^”\n]*”|'[^'\n]*'|‘[^’\n]*’|\([^)\n]*\)|（[^）\n]*）")


def kanji_chen(text):
    """Chữ Hán (có / không furigana) nằm giữa hai chữ Việt trong câu tiếng Việt – nghi chữ Việt bị máy thay bằng chữ Hán
    (vd 'Nếu ｜休《やす》 việc ｜歩《あゆ》 vào nhà'). Bỏ qua phần trong nháy / ngoặc và tên người + さん/様/先生.
    Chỉ là GỢI Ý – tác tử KIỂM TRA quyết định: sửa định dạng (kanji_chen) / gắn cờ / ghi chú không phải lỗi."""
    out = []
    for line in (text or "").split("\n"):
        if not re.search(rf"[{VI_L}]{{2}}", _bare(line)):
            continue
        l2 = _TRONG_NHAY.sub(lambda m: "「」", line.replace("⟪", "").replace("⟫", ""))
        for m in KC_RE.finditer(l2):
            sau = l2[m.end():m.end() + 4]
            if re.match(r"\s?(?:さん|様|さま|先生|君|くん|ちゃん|氏)", sau):
                continue
            ctx = l2[max(0, m.start() - 15):m.end() + 15]
            if ctx not in out:
                out.append(ctx)
    return out


def kanji_chen_json(doc):
    """K-KC trên JSON tiếng Việt: [(đường dẫn, đoạn)] – ⟪…⟫ ngắn chỉ gồm chữ Hán nằm giữa hai chữ Việt."""
    out = []
    for fp, o in iter_lang_fields(doc):
        for x in kanji_chen(o.get("vi") or ""):
            out.append((path_str(fp), x))
    return out


# ---------------- trích dẫn ↔ đoạn văn gốc (K-TD) ----------------
_PUNCT_JA = r"[\s　。．.、，,｡､･·「」『』！？!?・…\-－―〜~:：()（）\[\]［］\"'“”‘’{}①-⑳]"


def _yomi_furi(s):
    return FURI_RE.sub(lambda m: m.group(2), s or "")


def chuan_doan_van(dv):
    """Đoạn văn gốc (đã normalize_html) → (bản chữ, bản đọc) để so trích dẫn: bỏ dấu câu / khoảng trắng; bản đọc thay 漢字（かな）→ かな."""
    s = re.sub(r"[ \t　]+", "", dv or "")
    yomi = re.sub(r"[㐀-鿿々〆ヶ]+[（(]([぀-ゟ゠-ヿー]+)[）)]", r"\1", _yomi_furi(s))
    chu = re.sub(r"[（(][぀-ゟ゠-ヿー]+[）)]", "", _bare(s))
    return re.sub(_PUNCT_JA, "", chu), re.sub(_PUNCT_JA, "", yomi)


def ty_le_trich_dan(ja, dv_chuan):
    """Tỷ lệ chữ của câu trích dẫn có mặt (theo các khối liền ≥ 3 ký tự) trong đoạn văn gốc – lấy max giữa bản chữ và bản đọc."""
    import difflib
    best = 0.0
    for q in (re.sub(_PUNCT_JA, "", _bare(ja)), re.sub(_PUNCT_JA, "", _yomi_furi(ja))):
        if not q:
            continue
        for d in dv_chuan:
            if not d:
                continue
            sm = difflib.SequenceMatcher(None, q, d, autojunk=False)
            n = sum(b.size for b in sm.get_matching_blocks() if b.size >= 3)
            best = max(best, n / len(q))
    return best


# ---------------- gắn cờ (giai đoạn 0) ----------------
FLAG_TEXT = {
    "khuon_a": "Khuôn A – phân tích từng lựa chọn (Python tách khung)",
    "khuon_b": "Khuôn B – 'Đoạn văn:' dịch cả bài + 'Câu hỏi:' + dịch lựa chọn (full_translation; question.ja / option_ja lấy từ đề)",
    "khuon_le": "Khuôn lẻ – không tách được khung (JSON cũ / ### / không đủ '1.'–'4.') – tác tử TẠO đặt theo nội dung, KIỂM TRA soát kỹ",
    "khong_ja_cau_hoi": "Lời giải không có câu hỏi tiếng Nhật ở đầu (question.ja lấy từ đề)",
    "khong_nghia_cau_hoi": "Lời giải không có nghĩa câu hỏi (question.meaning = null)",
    "co_phan_tich_chung": "Có câu chữ trước lựa chọn 1 (phân tích chung) → summary[0].points, heading = null",
    "lc_khong_nghia": "Có lựa chọn không có 'Nghĩa:' (meaning = null)",
    "lc_khong_ket_luan": "Có lựa chọn không có '→ ĐÚNG / SAI' (is_match theo đáp án)",
    "lc_khong_phan_tich": "Có lựa chọn không có phần phân tích (analysis = null)",
    "co_sau_ket_luan": "Có câu chữ sau '→ ĐÚNG/SAI' của một lựa chọn (nối vào cuối analysis của lựa chọn đó)",
    "ket_luan_lech_dap_an": "Kết luận ĐÚNG của lời giải khác dap_an_so của đề (nghi lỗi nội dung)",
    "co_trich_dan": "Có câu trích dẫn đứng riêng dòng (→ quotes[])",
    "trich_dan_khong_dich": "Có câu trích dẫn không kèm bản dịch (quotes[].meaning = null)",
    "trich_dan_lech_doan_van": "Gợi ý Python: có câu trích dẫn không tìm thấy trong đoạn văn gốc (K-TD – nghi trích sai / chép sai)",
    "kanji_chen": "Gợi ý Python: có chữ Hán chèn giữa câu tiếng Việt (K-KC – nghi chữ Việt bị máy thay bằng chữ Hán)",
    "b_khong_tach_duoc": "Khuôn B nhưng không tách được (thiếu 'Câu hỏi:' / thiếu dòng lựa chọn)",
    "b_so_lua_chon_khac_4": "Khuôn B: số dòng dịch lựa chọn khác 4",
    "b_dap_an_lech": "Khuôn B: dòng 'Câu trả lời đúng là' không trùng nghĩa của đáp án theo đề",
    "b_co_giai_thich": "Khuôn B có câu chữ giải thích (→ analysis của lựa chọn đúng)",
    "doan_van_trong": "Đề không có đoạn văn (doan_van rỗng / chỉ có hình) – không so được trích dẫn",
    "doan_van_co_hinh": "Đoạn văn có hình ảnh (<img>)",
    "doan_van_dai": "Đoạn văn dài (> lo_nho.do_dai_doan_van ký tự) – chạy lô nhỏ",
    "chung_doan_van": "Đoạn văn dùng chung với câu con khác (xếp liền nhau trong thứ tự chạy)",
    "ky_hieu_furigana_hong": "Bản gốc có ký hiệu furigana hỏng dạng '<|今;いま|' (lỗi định dạng – KIỂM TRA sửa định dạng nếu rõ, không thì giữ)",
    "danh_dau_rac": "Bản gốc có đoạn in đậm / gạch chân rỗng (đã bỏ thẻ)",
    "co_furigana": "Có furigana",
    "ruby_hong": "Có ruby hỏng trong bản gốc",
    "ky_hieu_trung": "Bản gốc có sẵn ký hiệu ｜《》",
    "furigana_chu_viet": "Furigana gắn lên chữ tiếng Việt (Python đã bỏ)",
}
CTV_FLAGS = ("ket_luan_lech_dap_an", "khuon_le", "b_dap_an_lech")
FURI_SKIP = [("correct", "option_ja")]      # correct.option_ja = bản sao options[i].option_ja (lời giải không lặp lại dòng này)


def parse_and_flag(text, lua_chon, dap_an_so, cau_hoi, doan_van):
    """Tách khung + gắn cờ + ghi chú bản gốc. Trả về (phan, co, ghi_chu, goi_y)."""
    co, gc, goi_y = [], [], []
    dap = int(dap_an_so) if str(dap_an_so).isdigit() else None
    phan = {"khuon": None}
    if la_khuon_b(text):
        b = tach_khuon_b(text)
        if not b:
            co += ["khuon_le", "b_khong_tach_duoc"]
            phan["khuon"] = "le"
        else:
            co.append("khuon_b")
            phan.update(khuon="B", b=b)
            if len(b["lua_chon_vi"]) != 4:
                co.append("b_so_lua_chon_khac_4")
            if b["dap_an_dong"] and dap and len(b["lua_chon_vi"]) >= dap and _k(b["dap_an_dong"]) != _k(b["lua_chon_vi"][dap - 1]):
                co.append("b_dap_an_lech")
                gc.append(f"[Bản gốc VI] 'Câu trả lời đúng là: {b['dap_an_dong']}' khác nghĩa lựa chọn {dap} (đáp án của đề)")
            if b["giai_thich"]:
                co.append("b_co_giai_thich")
    else:
        head, items = tach_khuon_a(text)
        def _ja_ok(it):
            t = re.split(r"\s*Nghĩa\s*[:：]", it["tieu_de"])[0]
            return la_tieng_nhat(t) or any(_k(t) == _k(x) for x in lua_chon if x)
        if len(items) != 4 or sum(not _ja_ok(it) for it in items) >= 2:
            co.append("khuon_le")
            phan["khuon"] = "le"
        else:
            co.append("khuon_a")
            hd = phan_dau(head)
            lcs = [phan_lua_chon(it) for it in items]
            phan.update(khuon="A", dau=hd, lua_chon=lcs)
            if not hd["ja"]:
                co.append("khong_ja_cau_hoi")
            if not hd["nghia"]:
                co.append("khong_nghia_cau_hoi")
            if hd["khac"]:
                co.append("co_phan_tich_chung")
            if any(x["nghia"] is None for x in lcs):
                co.append("lc_khong_nghia")
            if any(x["ket_luan"] is None for x in lcs):
                co.append("lc_khong_ket_luan")
            if any(x["analysis"] is None and not x["quotes"] for x in lcs):
                co.append("lc_khong_phan_tich")
            if any(x["co_sau_ket_luan"] for x in lcs):
                co.append("co_sau_ket_luan")
            if any(x["quotes"] for x in lcs):
                co.append("co_trich_dan")
            if any(q["vi"] is None for x in lcs for q in x["quotes"]):
                co.append("trich_dan_khong_dich")
            dung = [x["so"] for x in lcs if x["ket_luan"] == "ĐÚNG"]
            if dap and dung and dung != [dap]:
                co.append("ket_luan_lech_dap_an")
                gc.append(f"[Bản gốc VI] Lời giải kết luận ĐÚNG ở lựa chọn {dung} – đáp án của đề là {dap}")
            # K-TD: trích dẫn ↔ đoạn văn
            dvc = chuan_doan_van(doan_van) if (doan_van or "").strip() else None
            if dvc and any(dvc):
                for x in lcs:
                    for q in x["quotes"]:
                        r = ty_le_trich_dan(q["ja"], dvc)
                        if r < (cfg().get("kiem_tra") or {}).get("trich_dan_khop_doan_van_min", 0.9):
                            goi_y.append(f"TD: lựa chọn {x['so']} – trích dẫn '{_bare(q['ja'])[:40]}…' chỉ khớp {r:.0%} với đoạn văn gốc")
                if any(g.startswith("TD:") for g in goi_y):
                    co.append("trich_dan_lech_doan_van")
    kc = kanji_chen(text)
    if kc:
        co.append("kanji_chen")
        goi_y += [f"KC: …{x}…" for x in kc[:12]]
    return phan, sorted(set(co)), gc, goi_y


# ---------------- khung Python gửi tác tử TẠO ----------------
def khung_python(norm):
    """Khung JSON Python tách sẵn (chưa bọc ⟪ ⟫) – tác tử TẠO dùng làm khung, đối chiếu lại với lời giải gốc."""
    ph, de = norm.get("phan") or {}, norm["de"]
    if ph.get("khuon") == "A":
        hd = ph["dau"]
        return {"question": {"ja": hd["ja"] or de_khong_furi(de["cau_hoi"]), "meaning_vi": hd["nghia"]},
                "summary_points_vi": hd["khac"] or None,
                "options": [{"index": x["so"], "option_ja": x["option_ja"], "meaning_vi": x["nghia"],
                             "is_match": (x["ket_luan"] == "ĐÚNG") if x["ket_luan"] else (x["so"] == de["dap_an_so"]),
                             "quotes": [{"ja": q["ja"], "meaning_vi": q["vi"]} for q in x["quotes"]],
                             "analysis_vi": x["analysis"]} for x in ph["lua_chon"]]}
    if ph.get("khuon") == "B":
        b = ph["b"]
        dap = de["dap_an_so"]
        return {"full_translation_lines_vi": b["doan_van_dich"],
                "question": {"ja": de_khong_furi(de["cau_hoi"]), "meaning_vi": b["cau_hoi_vi"]},
                "summary_points_vi": b["dau_khac"] or None,
                "options": [{"index": i + 1, "option_ja": de_khong_furi(de["lua_chon"][i]),
                             "meaning_vi": b["lua_chon_vi"][i] if i < len(b["lua_chon_vi"]) else None,
                             "is_match": i + 1 == dap, "quotes": [],
                             "analysis_vi": ("\n".join(b["giai_thich"]) or None) if i + 1 == dap else None}
                            for i in range(len(de["lua_chon"]))],
                "bo_dong_cau_tra_loi_dung": b["dap_an_dong"]}
    return None


def de_khong_furi(s):
    """Câu của đề dùng trong JSON (khuôn B): bỏ furigana ｜《》 – lời giải không có, kiểm tra furigana so với lời giải."""
    return _bare(s or "").strip()


# ---------------- kiểm tra riêng giai đoạn 1 (K) ----------------
def bo_dong_tieu_de_lua_chon(text):
    """Bản đo độ phủ chữ Việt (khuôn A): bỏ dòng tiêu đề lựa chọn 'i. <tiếng Nhật>' (chép vào option_ja – không dịch; chữ Latin
    trong đó như 'a-②', 'iPhone' không tính) và phần tiếng Nhật của câu trích dẫn đứng riêng dòng (→ quotes[].ja)."""
    out = []
    for ln in (text or "").split("\n"):
        m = OPT10_RE.match(ln)
        if m:
            mh = re.match(r"^.*?(Nghĩa\s*[:：].*)$", m.group(2))
            out.append(mh.group(1) if mh else "")
            continue
        s = ln.strip()
        mt = NHAN_TRICH_RE.match(s)
        if mt:
            s = mt.group(1).strip()
        core = re.sub(r"^[-•*+]\s*", "", s)
        lead = ""
        mlead = re.match(rf"^(.*?[{VI_L}].*?[:：])\s*(「.*)$", core)
        if mlead and not la_tieng_nhat(mlead.group(1)):
            lead, core = mlead.group(1), mlead.group(2)
        q = tach_trich_dan(core)
        if q:
            out.append((lead + " " + (q[1] or "")).strip())
            continue
        out.append(ln)
    return "\n".join(out)


def strip_labels(text):
    """Bỏ nhãn cố định khi đo độ phủ chữ tiếng Việt."""
    text = re.sub(r"(?im)^\s*[-=]*\s*[→➝⇒]\s*\{?\s*(ĐÚNG|SAI)\s*\}?\s*[.。!]?\s*$", " ", text or "")
    text = re.sub(r"(?im)^\s*[-•*+]?\s*\{?\s*(Nghĩa|Câu hỏi|Đoạn văn|Giải thích|Phân tích|Câu trả lời đúng(?: là)?)\s*\}?\s*[:：]", " ", text)
    text = re.sub(rf"(?im)^\s*[-•*+]?\s*\{{?\s*(?:{NHAN_TRICH})\s*\}}?\s*[:：]", " ", text)
    text = re.sub(r"(?m)^\s*\{?[1-4]\}?\s*[\.．]\s*", " ", text)
    # chữ Latin (kg, cm…) trong câu trích dẫn tiếng Nhật 「…」 không phải chữ Việt (lô 242–251)
    text = re.sub(r"「[^「」\n]*[\u3040-\u30ff\u4e00-\u9fff][^「」\n]*」", " ", text)
    return text


def _opt_vi(o):
    xs = [_v(o.get("meaning")), _v(o.get("analysis"))] + [_v(q.get("meaning")) for q in o.get("quotes") or []]
    return "\n".join(x for x in xs if x)


def check_k(doc, norm, policy):
    loi, canh_bao = [], []
    de, ph = norm["de"], norm.get("phan") or {}
    khuon = ph.get("khuon")
    q, c = doc.get("question") or {}, doc.get("correct") or {}
    opts = doc.get("options") or []
    dap = de["dap_an_so"] if isinstance(de["dap_an_so"], int) else None
    n_lc = len([x for x in de["lua_chon"] if x.strip()])
    # K1 – lựa chọn
    if [o.get("index") for o in opts] != list(range(1, n_lc + 1)):
        loi.append(f"K1: options phải có {n_lc} lựa chọn theo thứ tự 1–{n_lc} (đang có {[o.get('index') for o in opts]})")
    # K6 – đáp án
    if str(c.get("index")) != str(de["dap_an_so"]):
        loi.append(f"K6: correct.index = {c.get('index')} khác dap_an_so = {de['dap_an_so']}")
    di = c.get("index")
    if isinstance(di, int) and 1 <= di <= len(opts) and c.get("option_ja") != opts[di - 1].get("option_ja"):
        loi.append(f"K6: correct.option_ja phải giống hệt options[{di - 1}].option_ja")
    if c.get("full_sentence") is not None:
        loi.append("K6: correct.full_sentence phải là null (dạng 10 không có câu hoàn chỉnh)")
    match = [o.get("index") for o in opts if o.get("is_match")]
    if dap and match != [dap]:
        loi.append(f"K6: is_match = true phải đúng ở MỘT lựa chọn là đáp án {dap} (đang ở {match})")
    if doc.get("key_info") is not None:
        loi.append("K10: key_info phải là null (dạng 10 không có khuôn 'Thông tin')")
    for o in opts:
        if o.get("reading") is not None:
            canh_bao.append(f"K10: lựa chọn {o.get('index')}: reading khác null – lời giải dạng 10 không có dòng cách đọc lựa chọn, xem lại")
    if khuon == "A":
        hd = ph["dau"]
        if hd["ja"] and _k(q.get("ja")) != _k(hd["ja"]):
            loi.append(f"K8: question.ja khác dòng câu hỏi của lời giải '{hd['ja'][:60]}'")
        if (hd["nghia"] is None) != (q.get("meaning") is None):
            loi.append("K8: question.meaning phải null khi và chỉ khi lời giải không có dòng nghĩa câu hỏi")
        elif hd["nghia"]:
            # nhãn 'Câu hỏi:' đầu dòng nghĩa câu hỏi bị bỏ khi chuyển JSON (s1_chuyen_json mục 4) – không tính là thiếu chữ (lô 202–211)
            cv, miss = _cover(re.sub(r"^\s*\{?\s*Câu hỏi\s*\}?\s*[:：]\s*", "", hd["nghia"]), _v(q.get("meaning")))
            if cv < 0.97:
                loi.append(f"K9: question.meaning thiếu chữ so với bản gốc: {miss}")
        sm = doc.get("summary")
        if bool(hd["khac"]) != bool(sm):
            loi.append(f"K10: summary: bản gốc {'có' if hd['khac'] else 'không có'} câu chữ trước lựa chọn 1 nhưng JSON {'không có' if not sm else 'có'} summary")
        elif hd["khac"]:
            cv, miss = _cover("\n".join(hd["khac"]), "\n".join(_v(p) or "" for s in sm for p in [s.get("heading")] + (s.get("points") or [])))
            if cv < 0.97:
                loi.append(f"K9: summary thiếu chữ so với phần phân tích chung: {miss}")
        if doc.get("full_translation") is not None:
            loi.append("K10: full_translation phải là null (khuôn A – lời giải không có bản dịch cả bài)")
        src = {x["so"]: x for x in ph["lua_chon"]}
        for o in opts:
            x = src.get(o.get("index"))
            if not x:
                continue
            i = x["so"]
            if _k(o.get("option_ja")) != _k(x["option_ja"]):
                loi.append(f"K8: lựa chọn {i}: option_ja '{(o.get('option_ja') or '')[:40]}' khác dòng lựa chọn của lời giải '{x['option_ja'][:40]}'")
            if (x["nghia"] is None) != (o.get("meaning") is None):
                loi.append(f"K12: lựa chọn {i}: meaning phải null khi và chỉ khi lời giải không có 'Nghĩa:'")
            srcv = "\n".join(y for y in [x["nghia"], x["analysis"]] + [qq["vi"] for qq in x["quotes"]] if y)
            # nhãn 'Nghĩa:' / 'Dịch:' đầu bản dịch trích dẫn ('(Nghĩa: …)') bị bỏ khi chuyển JSON – không tính là thiếu chữ (lô 81–90)
            srcv = re.sub(r"(?im)(^|[\(（]\s*)(?:Nghĩa|Dịch)\s*[:：]\s*", r"\1", srcv)
            # chữ Latin (kg, cm…) nằm trong câu trích dẫn tiếng Nhật 「…」 Python chưa tách khỏi analysis – không tính là chữ Việt (lô 242–251)
            srcv = re.sub(r"「[^「」\n]*[\u3040-\u30ff\u4e00-\u9fff][^「」\n]*」", " ", srcv)
            cv, miss = _cover(srcv, _opt_vi(o))
            if cv < 0.97:
                loi.append(f"K9: lựa chọn {i}: thiếu chữ so với bản gốc: {miss}")
            if x["ket_luan"] and bool(o.get("is_match")) != (x["ket_luan"] == "ĐÚNG") and not (dap and (i == dap) == bool(o.get("is_match"))):
                canh_bao.append(f"K12: lựa chọn {i}: is_match khác kết luận '{x['ket_luan']}' của lời giải")
            nq, nq_src = len(o.get("quotes") or []), len(x["quotes"])
            if nq != nq_src:
                canh_bao.append(f"K-TD: lựa chọn {i}: JSON có {nq} trích dẫn – Python tách được {nq_src} (xem lại: trích dẫn đứng riêng dòng → quotes, nằm trong câu → analysis)")
    elif khuon == "B":
        b = ph["b"]
        if _k(q.get("ja")) != _k(de_khong_furi(de["cau_hoi"])):
            loi.append("K8: khuôn B – question.ja phải chép câu hỏi của ĐỀ (bỏ furigana)")
        cv, miss = _cover(b["cau_hoi_vi"], _v(q.get("meaning")))
        if cv < 0.97:
            loi.append(f"K9: question.meaning thiếu chữ: {miss}")
        ft = doc.get("full_translation")
        if not ft:
            loi.append("K10: khuôn B – full_translation phải có bản dịch đoạn văn")
        else:
            cv, miss = _cover("\n".join(b["doan_van_dich"]), "\n".join(_v(ln.get("meaning")) or "" for s in ft for ln in s.get("lines") or []))
            if cv < 0.97:
                loi.append(f"K9: full_translation thiếu chữ so với 'Đoạn văn:' của lời giải: {miss}")
            if any(ln.get("ja") is not None for s in ft for ln in s.get("lines") or []):
                canh_bao.append("K10: khuôn B – full_translation.lines[].ja nên là null (lời giải chỉ có bản dịch)")
        for i, o in enumerate(opts):
            if i < len(de["lua_chon"]) and _k(o.get("option_ja")) != _k(de_khong_furi(de["lua_chon"][i])):
                loi.append(f"K8: khuôn B – lựa chọn {i + 1}: option_ja phải chép lựa chọn của ĐỀ")
            if i < len(b["lua_chon_vi"]):
                cv, miss = _cover(b["lua_chon_vi"][i], _v(o.get("meaning")))
                if cv < 0.97:
                    loi.append(f"K9: khuôn B – lựa chọn {i + 1}: meaning thiếu chữ: {miss}")
    # K-TD – trích dẫn trong JSON ↔ lời giải gốc / đoạn văn
    src_ja = _k(norm.get("src_text") or "")
    dvc = chuan_doan_van(norm.get("doan_van")) if (norm.get("doan_van") or "").strip() else None
    nguong = (cfg().get("kiem_tra") or {}).get("trich_dan_khop_doan_van_min", 0.9)
    for o in opts:
        for j, qq in enumerate(o.get("quotes") or []):
            ja = qq.get("ja") or ""
            if _k(ja).strip("「」") and _k(ja).strip("「」") not in src_ja:
                loi.append(f"K-TD: lựa chọn {o.get('index')} quotes[{j}].ja không có nguyên văn trong lời giải gốc: '{_bare(ja)[:40]}'")
            if dvc and any(dvc):
                r = ty_le_trich_dan(ja, dvc)
                if r < nguong:
                    canh_bao.append(f"K-TD: lựa chọn {o.get('index')} quotes[{j}] chỉ khớp {r:.0%} với đoạn văn gốc – nghi trích sai (gắn cờ trich_dan nếu đúng là sai)")
    # K-KC – chữ Hán chèn giữa câu Việt (s1_kiem_tra bắt buộc xử lý: sửa / cờ / ghi chú)
    for p_, x in kanji_chen_json(doc)[:10]:
        canh_bao.append(f"K-KC: {p_}: chữ Hán giữa câu Việt '…{x}…'")
    loi += TK.kiem_tra(doc, (ph or {}).get("tham_khao"))
    return loi, canh_bao


def is_style_field(path):
    """Trường câu văn giải thích (kiểm tra -습니다): chỉ analysis và summary.points; bỏ nghĩa câu / lựa chọn / trích dẫn / bản dịch cả bài / heading."""
    p = path if isinstance(path, str) else path_str(path)
    return bool(re.search(r"\.analysis$|\.points\[\d+\]$", p))


# ---------------- hiển thị cho Excel CTV ----------------
def render(d, lang):
    q, c = d.get("question") or {}, d.get("correct") or {}
    out = [bold("【CÂU HỎI】") + " " + show(q.get("ja") or "")]
    if q.get("meaning"):
        out.append(f"Nghĩa: {_t(q['meaning'], lang)}")
    if d.get("full_translation"):
        out.append(bold("【BẢN DỊCH ĐOẠN VĂN】"))
        for s in d["full_translation"]:
            if s.get("label"):
                out.append(bold(s["label"]))
            for ln in s.get("lines") or []:
                pre = f"{ln['speaker']}: " if ln.get("speaker") else ""
                if ln.get("ja"):
                    out.append(pre + show(ln["ja"]))
                if ln.get("meaning"):
                    out.append(pre + _t(ln["meaning"], lang))
    if d.get("summary"):
        out.append(bold("【PHÂN TÍCH CHUNG】"))
        for s in d["summary"]:
            if s.get("heading"):
                out.append(bold(_t(s["heading"], lang)))
            out += [_t(p_, lang) for p_ in s.get("points") or []]
    out.append(bold("【PHÂN TÍCH CÁC LỰA CHỌN】"))
    for o in d.get("options", []):
        out.append(bold(f"{o.get('index')}. ") + show(o.get("option_ja", "")))
        if o.get("meaning"):
            out.append(f"Nghĩa: {_t(o['meaning'], lang)}")
        for qq in o.get("quotes") or []:
            out.append("Trích dẫn: 「" + show(qq.get("ja", "")) + "」" + (f"\n({_t(qq['meaning'], lang)})" if qq.get("meaning") else ""))
        if o.get("analysis"):
            out.append(_t(o["analysis"], lang))
        out.append("→ ĐÚNG." if o.get("is_match") else "→ SAI.")
        out.append("")
    out.append(bold("【LỰA CHỌN ĐÚNG】"))
    out.append(f"{c.get('index')}. {show(c.get('option_ja', ''))}")
    out += TK.render(d, lang, show, bold)
    return "\n".join(out).replace("\n\n\n", "\n\n")


def sudachi_hints(norm):
    """Dạng 10: không dùng Sudachi – trả gợi ý Python của s0 (TD = trích dẫn lệch đoạn văn, KC = chữ Hán chèn câu Việt)."""
    return list(norm.get("goi_y_python") or [])
