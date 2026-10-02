"""Phần riêng của dạng 01 – Cách đọc kanji: cấu hình, đường dẫn, gắn cờ, kiểm tra K1–K8 / D1–D4, hiển thị Excel.
Các script s0…s3 đều import file này.
"""
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
    os.environ["PIPELINE_DATA"] = _c.get("du_lieu_test", "data/test_01_tu_vung_cach_doc_kanji.csv")


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
from pipeline_chung.ctv_excel import B0, B1, bold  # noqa: E402,F401
from pipeline_chung.ctv_excel import show as _show  # noqa: E402

# Excel CTV: { } của dạng 01 là chỗ GẠCH CHÂN trong bản gốc → hiển thị gạch chân; nhãn 【…】 không in đậm
# (chỉ định dạng những chỗ bản gốc có định dạng)
MARK_EXCEL = "u"


def show(s):
    return _show(s, MARK_EXCEL)


def label(s):
    return s


# ---------------- cấu hình & đường dẫn ----------------
def cfg():
    return load_json(os.path.join(DANG, "config.json"))


def P(*parts):
    """Đường dẫn tính từ thư mục dạng bài."""
    return os.path.normpath(os.path.join(DANG, *parts))


def OUT(*parts):
    """Thư mục output (đổi được bằng biến môi trường PIPELINE_OUTPUT – dùng khi chạy thử giả lập)."""
    return P(os.environ.get("PIPELINE_OUTPUT") or cfg()["output"], *parts)


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
        order = [sid_of(r) for r in read_csv(data_path())]
        a, b = TU or 1, DEN or len(order)
        if a < 1 or b < a:
            sys.exit(f"Phạm vi không hợp lệ: --tu {a} --den {b} (file dữ liệu có {len(order)} mẫu, đánh số từ 1)")
        allowed = set(status.ids(*default_states))
        ids = [s for s in order[a - 1:b] if s in allowed]
        print(f"Phạm vi: mẫu {a}–{min(b, len(order))} theo thứ tự trong {os.path.basename(data_path())}"
              f" → {len(ids)}/{len(order[a - 1:b])} câu ở trạng thái phù hợp cho bước này")
        return ids
    ids = status.ids(*default_states)
    if getattr(args, "lo", None):
        ids = ids[: args.lo]
    elif not getattr(args, "tat_ca", False):
        sys.exit("Hãy chọn phạm vi: --pilot, --ids <id1,id2>, --tu <từ mẫu> --den <đến mẫu>, --lo <số câu> hoặc --tat-ca")
    return ids


# ---------------- nhãn cố định của lời giải gốc (bỏ khi đo độ phủ) ----------------
LABELS = [r"(?im)^\s*(từ|nghĩa|câu hỏi|cách đọc|thể từ điển)\s*:", r"(?im)^\s*(lựa chọn đúng|phân tích|thông tin tham khảo)\s*:?\s*$", r"(?im)thông tin tham khảo\s*:?",
          r"(?im)lựa chọn đúng\s*:?", r"(?im)phân tích\s*:?", r"(?m)^\s*###\s*$", r"Thể từ điển\s*:"]


def strip_labels(text):
    for pat in LABELS:
        text = re.sub(pat, " ", text)
    return text


# ---------------- gắn cờ (giai đoạn 0) ----------------
KHONG_TON_TAI_RE = re.compile(r"không (tồn tại|có) từ", re.I)
FLAG_TEXT = {
    "nghi_don_phan_tich": "Phân tích của một lựa chọn có thể bị viết dồn vào ô lựa chọn khác",
    "thieu_phan_tich": "Lựa chọn sai không có phân tích trong bản gốc",
    "lech_dap_an": "correct_index trong lời giải khác dap_an_so",
    "thieu_lua_chon": "Lời giải gốc có ít phân tích hơn số lựa chọn",
    "thieu_gach_chan": "Bản gốc thiếu gạch chân ở câu / cách đọc / nghĩa",
    "the_tu_dien": "Có thể từ điển",
    "tu_dien_dinh_cach_doc": "Thể từ điển viết dính vào cách đọc",
    "co_furigana": "Có furigana",
    "dang_###": "Lời giải gốc dạng ###",
    "khong_ton_tai_nhieu": "Nhiều lựa chọn ghi 'không tồn tại'",
    "ruby_hong": "Có ruby hỏng trong bản gốc",
    "ky_hieu_trung": "Bản gốc có sẵn ký hiệu ｜《》 (trùng ký hiệu furigana)",
}


def merged_into_other(notes, idx, answer):
    """Phân tích của lựa chọn idx (cách đọc answer) có nằm trong ô của lựa chọn khác không."""
    ans = strip_marks(answer).strip()
    if not ans:
        return False
    pat = re.compile(rf"(?:^|[\s\.。])({idx})\s*[\.\)]\s*{re.escape(ans)}\s*[:：]")
    return any(pat.search(n or "") for j, n in notes.items() if j != idx)


def flags_old_json(old, lua_chon, dap_an_so):
    q = old.get("question") or {}
    ans = old.get("answers") or []
    notes = {int(a.get("index")): (a.get("note") or "").strip() for a in ans if str(a.get("index", "")).isdigit()}
    correct = str(old.get("correct_index"))
    flags, ban_goc = [], []
    for i in range(1, 5):
        opt = lua_chon[i - 1] if i - 1 < len(lua_chon) else ""
        if str(i) == str(dap_an_so) or str(i) == correct:
            continue
        if not notes.get(i):
            if merged_into_other(notes, i, next((a.get("answer", "") for a in ans if str(a.get("index")) == str(i)), opt)):
                flags.append("nghi_don_phan_tich")
            else:
                flags.append("thieu_phan_tich")
                ban_goc.append(f"[Bản gốc VI] Thiếu phân tích lựa chọn {i}")
    if correct != str(dap_an_so):
        flags.append("lech_dap_an")
        ban_goc.append(f"[Bản gốc VI] correct_index trong lời giải = {correct}, khác đáp án của đề (dap_an_so = {dap_an_so})")
    if len(ans) < sum(1 for x in lua_chon if x):
        flags.append("thieu_lua_chon")
    if any("{" not in (q.get(k) or "") for k in ("text", "reading", "mean")):
        flags.append("thieu_gach_chan")
    if (q.get("kanji_jishokei") or "").strip():
        flags.append("the_tu_dien")
    if "thể từ điển" in (q.get("kanji_reading") or "").lower():
        flags.append("tu_dien_dinh_cach_doc")
    if not (q.get("kanji_mean") or "").strip():
        ban_goc.append("[Bản gốc VI] Không có nghĩa của từ")
    if sum(1 for n in notes.values() if KHONG_TON_TAI_RE.search(n)) >= 2:
        flags.append("khong_ton_tai_nhieu")
    return sorted(set(flags)), ban_goc


def vi_text_old_json(old):
    """Phần chữ tiếng Việt của JSON cũ (để đo độ phủ)."""
    q = old.get("question") or {}
    parts = [q.get("kanji_mean"), q.get("mean"), old.get("reference")]
    parts += [a.get("note") for a in old.get("answers") or []]
    return "\n".join(x for x in parts if x)


# ---------------- kiểm tra riêng giai đoạn 1: K1–K8 ----------------
READING_OK = re.compile(r"^[぀-ゟ゠-ヿー・\s/、,，]+$")


def _inner_braces(s):
    m = re.search(r"\{(.*?)\}", s or "")
    return strip_marks(m.group(1)) if m else None


def check_k(doc, norm, policy):
    loi, canh_bao = [], []
    de = norm["de"]
    opts = doc.get("options") or []
    # K1
    if [o.get("index") for o in opts] != [1, 2, 3, 4]:
        loi.append(f"K1: options phải có đủ 4 lựa chọn theo thứ tự 1–4 (đang có {[o.get('index') for o in opts]})")
    # K2
    for o in opts:
        i = o.get("index")
        if isinstance(i, int) and 1 <= i <= 4 and norm_ja(o.get("option_ja")) != norm_ja(de["lua_chon"][i - 1]):
            loi.append(f"K2: lựa chọn {i}: option_ja '{o.get('option_ja')}' khác đề '{de['lua_chon'][i - 1]}'")
    # K3
    for o in opts:
        a = (o.get("analysis") or {}).get("vi", "")
        for other in opts:
            if other is o:
                continue
            ans = strip_marks(other.get("option_ja", "")).strip()
            if ans and re.search(rf"(?:^|[\s\.。])({other.get('index')})\s*[\.\)]\s*{re.escape(ans)}\s*[:：]", strip_marks(a)):
                loi.append(f"K3: phân tích lựa chọn {o.get('index')} còn chứa phân tích của lựa chọn {other.get('index')} (chưa tách)")
    # K4
    w = doc.get("word") or {}
    reads = [("word.reading", w.get("reading"))]
    if w.get("dictionary_form"):
        reads.append(("dictionary_form.reading", w["dictionary_form"].get("reading")))
    for name, r in reads:
        r2 = strip_marks(r or "")
        if not r2.strip() or not READING_OK.match(r2) or "thể từ điển" in r2.lower():
            loi.append(f"K4: {name} '{r}' không phải cách đọc kana hợp lệ")
    # K5
    q = doc.get("question") or {}
    inner = _inner_braces(q.get("ja"))
    wj = strip_marks(w.get("ja", "")).strip()
    if inner is not None and wj and wj not in inner and inner not in wj:
        canh_bao.append(f"K5: từ đang hỏi '{wj}' không trùng phần gạch chân '{inner}' trong câu")
    # K6
    mean_vi = (q.get("meaning") or {}).get("vi")
    for name, s in (("question.ja", q.get("ja")), ("question.reading", q.get("reading")), ("question.meaning.vi", mean_vi)):
        if s is None:
            continue
        if s.count("{") != 1 or s.count("}") != 1:
            msg = f"K6: {name} không có đúng 1 cặp {{ }}"
            (canh_bao if "thieu_gach_chan" in norm["co"] else loi).append(msg)
    # K7
    c = doc.get("correct") or {}
    if str(c.get("index")) != str(de["dap_an_so"]):
        msg = f"K7: correct.index = {c.get('index')} khác dap_an_so = {de['dap_an_so']}"
        (loi if policy.get("lech_dap_an") == "loi" or "lech_dap_an" not in norm["co"] else canh_bao).append(msg)
    elif "lech_dap_an" in norm["co"]:
        msg = f"K7: lời giải gốc ghi đáp án khác đề (correct_index ≠ dap_an_so = {de['dap_an_so']}) – JSON đã theo dap_an_so"
        (loi if policy.get("lech_dap_an") == "loi" else canh_bao).append(msg)
    di = c.get("index")
    if isinstance(di, int) and 1 <= di <= 4 and norm_ja(c.get("option_ja")) != norm_ja(de["lua_chon"][di - 1]):
        loi.append(f"K7: correct.option_ja '{c.get('option_ja')}' khác lựa chọn {di} của đề")
    # K9 – giữ nguyên danh sách đánh số của phần tham khảo (GPT hay đổi "1." thành "- ")
    if norm["khuon_goc"] == "json" and isinstance(norm["dau_vao"].get("reference"), str):
        num = lambda t: len(re.findall(r"(?m)^\s*\d+\s*[\.\)]", strip_marks(t or "")))  # noqa: E731
        a, b = num(norm["dau_vao"]["reference"]), num(((doc.get("reference") or {}).get("vi")))
        if a != b:
            canh_bao.append(f"K9: phần tham khảo có {a} dòng đánh số trong bản gốc nhưng JSON có {b} – kiểm tra GPT có đổi cách đánh số không")
    # K8
    if norm["khuon_goc"] == "json":
        for a in norm["dau_vao"].get("answers") or []:
            i = a.get("index")
            note = strip_marks(a.get("note") or "").strip()
            only_other = re.match(r"^\d\s*[\.\)]\s*\S+?\s*[:：]", note)   # ô chỉ chứa phân tích của lựa chọn khác
            if note and not only_other and isinstance(i, int) and 1 <= i <= len(opts) and opts[i - 1].get("analysis") is None:
                loi.append(f"K8: bản gốc có phân tích ở ô lựa chọn {i} nhưng JSON để null")
    return loi, canh_bao


# ---------------- kiểm tra riêng giai đoạn 2: D1–D2 (D3 nằm trong kiểm tra chung, D4 tổng hợp nhiều câu) ----------------
def check_d(doc_ko, gloss, lang="ko"):
    from pipeline_chung.dich import key_norm
    loi, canh_bao = [], []
    fixed = {key_norm(k): v for k, v in gloss["cau_co_dinh"].items()}
    for fp, o in iter_lang_fields(doc_ko):
        k = key_norm(o["vi"])
        if k in fixed and o.get(lang) != fixed[k]:
            loi.append(f"D1: {path_str(fp)}: câu cố định phải dịch là '{fixed[k]}'")
    loi += check_han_viet(doc_ko, lang)
    wm = ((doc_ko.get("word") or {}).get("meaning") or {}).get(lang, "")
    if re.search(r"(니다|니까)[\.。]?\s*$", wm or ""):
        canh_bao.append("D2: word.meaning nên dùng dạng từ điển, không dùng -습니다")
    return loi, canh_bao


HAN_VIET_VI_RE = re.compile(r"âm\s*h[áa]n\s*vi[ệe]t", re.I)
HAN_VIET_KO_RE = re.compile(r"베트남\s*한자음|한월음|한월\s*음|베트남\s*한자\s*음")


def check_han_viet(doc_ko, lang="ko"):
    """D5 – còn âm Hán Việt (chưa chốt cách xử lý, workflow chi tiết mục 11) → LỖI để vào nhóm cần xử lý.
    Bắt cả trường hợp âm không có dấu (vd LANG) mà kiểm tra 'còn chữ tiếng Việt' không phát hiện được."""
    out = []
    for fp, o in iter_lang_fields(doc_ko):
        if HAN_VIET_VI_RE.search(o.get("vi") or "") or HAN_VIET_KO_RE.search(o.get(lang) or ""):
            out.append(f"D5: {path_str(fp)}: còn âm Hán Việt – chờ chốt cách xử lý (workflow chi tiết mục 11)")
    return out


# ---------------- so chữ bản gốc ↔ JSON GPT (s8_phan_loai) ----------------
PT_LABEL_RE = re.compile(r"(?m)^\s*[1-4]\s*[\.．]\s*[^:：\n]{1,40}[:：]\s*")


def vi_segments_src(norm):
    """Phần chữ tiếng Việt của lời giải gốc, theo đúng thứ tự trường của JSON mới."""
    g = norm.get("dau_vao")
    if norm.get("khuon_goc") == "json":
        q = g.get("question") or {}
        notes = sorted((a for a in g.get("answers") or [] if isinstance(a.get("index"), int)), key=lambda a: a["index"])
        return [q.get("kanji_mean") or "", q.get("mean") or ""] + [a.get("note") or "" for a in notes] + [g.get("reference") or ""]
    return [PT_LABEL_RE.sub(" ", strip_labels(g or ""))]


def vi_segments_doc(doc):
    t = lambda o: (o or {}).get("vi") or ""  # noqa: E731
    w, q = doc.get("word") or {}, doc.get("question") or {}
    return [t(w.get("meaning")), t(q.get("meaning"))] + [t(o.get("analysis")) for o in doc.get("options") or []] + [t(doc.get("reference"))]


def is_style_field(path):
    return "analysis" in path or "reference" in path


# ---------------- hiển thị cho Excel CTV ----------------
KANJI_LABELS = ["Câu hỏi", "Cách đọc câu", "Nghĩa câu", "Từ", "Cách đọc từ", "Nghĩa từ", "Thể từ điển", "Đáp án đúng"]


def _t(obj, lang):
    return show((obj or {}).get(lang) or "") if obj else ""


def render(d, lang):
    w, q, c = d.get("word") or {}, d.get("question") or {}, d.get("correct") or {}
    dic = w.get("dictionary_form")
    vals = [show(q.get("ja", "")), show(q.get("reading") or ""), _t(q.get("meaning"), lang),
            show(w.get("ja", "")), show(w.get("reading", "")), _t(w.get("meaning"), lang),
            f"{show(dic['ja'])} ({dic['reading']})" if dic else "", f"{c.get('index')}. {show(c.get('option_ja', ''))}"]
    out = [f"【{lab}】 {v}" for lab, v in zip(KANJI_LABELS, vals)]
    for o in d.get("options", []):
        out.append(f"{'【Lựa chọn ' + str(o['index']) + ': ' + show(o.get('option_ja', '')) + '】'} {_t(o.get('analysis'), lang)}")
    out.append("【Tham khảo】" + " ")
    out.append(_t(d.get("reference"), lang))
    return "\n".join(out)


def furi_src_text(norm):
    """Bản gốc dùng để so furigana: với dạng ###, furigana ở dòng "Từ:" được tách thành word.ja + word.reading
    (bảng ánh xạ mục 3) nên không tính dòng đó; dạng JSON cũ giữ nguyên."""
    t = norm["src_text"]
    if norm.get("khuon_goc") == "###":
        t = "\n".join(l for l in t.split("\n") if not re.match(r"^\s*Từ\s*:", l))
    return t


def src_text_for_check(norm):
    """Bản gốc dùng để kiểm tra 'mất tiếng Nhật': bỏ các dòng nhãn lựa chọn của lời giải gốc không có trong đề
    (câu lệch đáp án / nhãn lựa chọn ghi sai – JSON lấy option_ja theo đề, K2/K7 đã kiểm tra riêng)."""
    dv = norm.get("dau_vao")
    if not isinstance(dv, dict):
        return norm["src_text"]
    de = set(norm["de"]["lua_chon"])
    bad = {(a.get("answer") or "").strip() for a in dv.get("answers") or []} - de - {""}
    if not bad:
        return norm["src_text"]
    return "\n".join(l for l in norm["src_text"].split("\n") if l.strip() not in bad)


# ---------------- Cách chia v2: cờ âm Hán Việt trong lời giải gốc ----------------
_UP = "A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬĐÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ"
_HV_WORD = rf"[{_UP}]{{2,}}(?:\s+[{_UP}]{{2,}})*"
HV_SRC_RES = [
    re.compile(r"âm\s*h[áa]n\s*vi[ệe]t[^\n]{0,30}", re.I),                                   # "âm hán việt là THÁN"
    re.compile(rf"ch[ữu]\s*h[áa]n\s*[\"'「]?[㐀-鿿]?[\"'」]?\s*,?\s*({_HV_WORD})\b"),   # "chữ hán NÃO"
    re.compile(rf"[㐀-鿿](?:\s*[（(][^)）\n]{{0,15}}[)）])?\s*[-–—:]\s*({_HV_WORD})\b"),  # "選 (せん) - TUYỂN"
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


def format_hints(norm):
    """Các chỗ nghi lỗi định dạng trong lời giải gốc (chỉ là gợi ý cho Claude, không quyết định trạng thái)."""
    t = norm.get("src_text") or ""
    out = []
    for name, rx in FORMAT_HINT_RES:
        for m in rx.finditer(t):
            out.append(f"{name}: …{t[max(0, m.start() - 15):m.end() + 15].replace(chr(10), '⏎')}…")
    return out[:12]
