"""Phần riêng của dạng 05 – Hình thành từ (dựng 2026-10-06 từ dạng 04): cấu hình, đường dẫn, tách phần lời giải
(PHÂN TÍCH 2 dòng / lựa chọn: nhãn 'i. X (đọc) - nghĩa gốc' + dòng từ ghép; THAM KHẢO = giới thiệu + danh sách từ), gắn cờ,
kiểm tra K1–K16 / D1, gợi ý SudachiPy W1–W3 + F1, hiển thị Excel.
Các script s0…s3 đều import file này.
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
    os.environ["PIPELINE_DATA"] = _c.get("du_lieu_test", "data/test_05_tu_vung_hinh_thanh_tu.csv")


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
LABELS = [r"(?im)^\s*(câu hỏi|đề bài|cách đọc|nghĩa|câu hoàn chỉnh)\s*:", r"(?m)PHÂN TÍCH\s*[:：]?", r"(?m)LỰA CHỌN ĐÚNG\s*[:：]?",
          r"(?m)THÔNG TIN THAM KHẢO\s*[:：]?", r"#{3,}"]


def strip_labels(text):
    for pat in LABELS:
        text = re.sub(pat, " ", text)
    return text


# ---------------- tách lời giải ### thành các phần (giai đoạn 0) ----------------
HEADERS = {"PHÂN TÍCH": "phan_tich", "LỰA CHỌN ĐÚNG": "lua_chon_dung", "THÔNG TIN THAM KHẢO": "tham_khao"}
HEADER_RE = re.compile(r"(PHÂN TÍCH|LỰA CHỌN ĐÚNG|THÔNG TIN THAM KHẢO)\s*[:：]?")   # chữ HOA – không nhầm với "phân tích" trong câu
NUM_LINE_RE = re.compile(r"^\s*\{?\s*([1-4])\s*[\.．]\s*(.*)$")
LABEL_RE = re.compile(r"^([^\n:：]*?)\s*(?:[\(（]([^()（）\n]*)[\)）])?\s*[:：]\s*(.*)$", re.S)


def _eq(a, b):
    """So lựa chọn: bỏ furigana, dấu, khoảng trắng, 。"""
    f = lambda s: re.sub(r"[。\.．、,，\s　]", "", norm_ja(s or "")).replace("ー", "一")  # noqa: E731 – đề hay gõ nhầm ー (trường âm) cho 一 (số một)
    return bool(f(a)) and f(a) == f(b)


def split_sections(text):
    """Văn bản ### đã chuẩn hóa → {dau, phan_tich, lua_chon_dung, tham_khao, tham_khao_khong_nhan}.
    Nhận tiêu đề cả khi thiếu ###; phần sau LỰA CHỌN ĐÚNG không có tiêu đề (sau ###) coi là tham khảo."""
    t = HEADER_RE.sub(lambda m: "\n###\n" + m.group(1) + "\n", text)
    blocks = [b.strip() for b in re.split(r"#{3,}", t)]
    out = {"dau": None, "phan_tich": None, "lua_chon_dung": None, "tham_khao": None, "tham_khao_khong_nhan": False}
    last = None
    for i, b in enumerate(blocks):
        m = HEADER_RE.match(b)
        if m:
            key = HEADERS[m.group(1)]
            body = b[m.end():].strip()
            out[key] = body if out[key] is None else (out[key] + "\n" + body).strip()
            last = key
        elif not b:
            continue
        elif last is None:
            out["dau"] = b if out["dau"] is None else out["dau"] + "\n" + b
        elif last == "lua_chon_dung" and out["tham_khao"] is None:
            out["tham_khao"], out["tham_khao_khong_nhan"], last = b, True, "tham_khao"
        else:
            out[last] = (out[last] or "") + "\n" + b
    return out


def head_lines(dau):
    """Phần đầu → {cau_hoi, cach_doc, nghia} (chuỗi đã bỏ nhãn, None nếu không có)."""
    res = {"cau_hoi": None, "cach_doc": None, "nghia": None}
    last = None     # dòng không nhãn ngay sau một trường → nối vào trường đó (đề hội thoại nhiều dòng A「…」/B「…」)
    for line in [x for x in (dau or "").split("\n") if x.strip()]:
        if re.match(r"(?i)^\s*cách đọc\s*[:：]", line):
            if res["cach_doc"] is None:
                res["cach_doc"] = re.sub(r"(?i)^\s*cách đọc\s*[:：]\s*", "", line); last = "cach_doc"
            else:
                last = None
        elif re.match(r"(?i)^\s*nghĩa\s*[:：]", line):
            if res["nghia"] is None:
                res["nghia"] = re.sub(r"(?i)^\s*nghĩa\s*[:：]\s*", "", line); last = "nghia"
            else:
                last = None
        elif res["cau_hoi"] is None:
            res["cau_hoi"] = re.sub(r"(?i)^\s*(câu hỏi|đề bài)\s*[:：]\s*", "", line); last = "cau_hoi"
        elif last:
            res[last] += "\n" + line
    return res


OPT_LABEL_RE = re.compile(r"^(?P<nhan>[^\s(（:：\-–—]+?)\s*(?:[（(](?P<doc>[^()（）\n]*)[)）])?\s*(?:[-–—:：]\s*(?P<gloss>.*))?$", re.S)


def parse_label(s):
    """Dòng nhãn dạng 05 'X (đọc) - nghĩa gốc' / 'X - nghĩa' / 'X: …' → (nhan, doc, gloss) hoặc None."""
    m = OPT_LABEL_RE.match((s or "").strip())
    return (m.group("nhan").strip(), m.group("doc"), (m.group("gloss") or "").strip() or None) if m else None


def analysis_lines(pt, lua_chon):
    """Phần PHÂN TÍCH → (mo_dau, [ {so, nhan, doc, gloss, noi_dung, lua_chon_khop} ], ket_luan, co_dinh_lien).
    Dạng 05: mỗi lựa chọn = dòng nhãn 'i. X (đọc) - nghĩa gốc' + (các) dòng từ ghép → noi_dung.
    Dòng dính liền ('…tiếng Nhật.3. ぱる: …') được tách theo nhãn khớp lựa chọn của đề."""
    lines = [x for x in (pt or "").split("\n") if x.strip()]
    glued = False
    split = []
    for line in lines:
        cut = [0]
        for k in range(1, 5):
            for m in re.finditer(rf"(?<=[^\d\s])\s*({k})\s*[\.．]\s*", line):
                lab = parse_label(line[m.end():].split("\n")[0])
                if m.start() > 0 and lab and _eq(lab[0], lua_chon[k - 1]):
                    cut.append(m.start() + (len(m.group(0)) - len(m.group(0).lstrip())))
        cut = sorted(set(cut))
        glued |= len(cut) > 1
        split += [line[a_:b_].strip() for a_, b_ in zip(cut, cut[1:] + [len(line)])]
    items, mo_dau = [], []
    for line in split:
        m = NUM_LINE_RE.match(line)
        lab = parse_label(m.group(2)) if m else None
        if m and lab and (any(_eq(lab[0], o) for o in lua_chon) or not items or int(m.group(1)) == items[-1]["so"] + 1):
            nhan, doc, gloss = lab
            khop = next((j + 1 for j, o in enumerate(lua_chon) if _eq(nhan, o)), None)
            items.append({"so": int(m.group(1)), "nhan": nhan, "doc": doc, "gloss": gloss, "noi_dung": "", "lua_chon_khop": khop})
        elif not items:
            mo_dau.append(line)
        else:
            items[-1]["noi_dung"] = (items[-1]["noi_dung"] + "\n" + line).strip()
    return "\n".join(mo_dau), items, "", glued


def compound_line(noi_dung):
    """Dòng từ ghép đầu tiên của một lựa chọn → (tu_ghep, ngoac, phan_sau) hoặc None.  '作品集 (さくひんしゅう): …' / '旧制度 (きゅうせいど) có nghĩa là …'"""
    first = (noi_dung or "").split("\n")[0].strip()
    m = re.match(r"^([^\s(（:：]+)\s*(?:[（(]([^()（）]*)[)）])?\s*(?:[:：]\s*)?(.*)$", first)
    if not m or not re.search(r"[぀-ゟ゠-ヿ㐀-鿿]", m.group(1)):
        return None
    return m.group(1), m.group(2), m.group(3)


TERM_RE = re.compile(r"^\s*(?:[-・•*]|\d+[\.\)])?\s*([^\s:：(（]+)\s*(?:[（(]([^)）]*)[)）])?\s*[:：]\s*(.+)$")


def ref_terms(tk):
    """Phần THAM KHẢO → (intro, [ (ja, doc, nghia) ]). Dòng dính 2 ví dụ ('…thế tục- 都会離れ (…): …') được tách."""
    lines = [x.strip() for x in (tk or "").split("\n") if x.strip()]
    lines = [p for x in lines for p in re.split(r"(?<=[^\s-])\s*(?=-\s*[぀-ゟ゠-ヿ㐀-鿿][^:：\n]{0,15}[（(][^)）]*[)）]\s*[:：])", x) if p.strip()]
    # hai ví dụ dính sau dấu chấm, không có gạch đầu dòng ('…từ Tokyo.日本発テクノロジー (…): …')
    lines = [p for x in lines for p in re.split(r"(?<=[.。])\s*(?=[぀-ゟ゠-ヿ㐀-鿿][^:：\n.。]{0,20}(?:[（(][^)）]*[)）])?\s*[:：])", x) if p.strip()]
    # câu giới thiệu dính ví dụ đầu trên cùng dòng ('…nghĩa là "gọi": 呼びかける (よびかける): …')
    lines = [p for x in lines for p in re.split(r"(?<=[:：])\s+(?=[぀-ゟ゠-ヿ㐀-鿿][^:：\n]{0,20}[（(][^)）]*[)）]\s*[:：])", x) if p.strip()]
    intro, terms, note = [], [], []
    for x in lines:
        m = TERM_RE.match(x)
        if note:
            note.append(x)
        elif m and re.search(r"[぀-ゟ゠-ヿ㐀-鿿]", m.group(1)) and (terms or not x.rstrip().endswith(":")):
            terms.append((m.group(1), m.group(2), m.group(3)))
        elif not terms:
            intro.append(x)
        else:
            note.append(x)                     # dòng đầu tiên không phải ví dụ → từ đây là đoạn ghi chú (reference.note)
    return "\n".join(intro), terms, "\n".join(note)


# ---------------- gắn cờ (giai đoạn 0) ----------------
KHONG_TON_TAI_RE = re.compile(r"không (tồn tại|có nghĩa)|không phải (là )?(cách viết|từ) (đúng|chính xác)", re.I)
BLANK_RE = re.compile(r"（[\s　]*）|\([\s　]*\)|＿{2,}|_{2,}")        # ký hiệu chỗ trống của câu đề


def cau_hoan_chinh(lcd):
    """Phần LỰA CHỌN ĐÚNG → {ja: câu sau 'Câu hoàn chỉnh:', nghia: dòng 'Nghĩa:' ngay sau} (None nếu không có)."""
    lines = [x.strip() for x in (lcd or "").split("\n") if x.strip()]
    ja = nghia = None
    for k, x in enumerate(lines):
        m = re.match(r"(?i)câu hoàn chỉnh\s*[:：]\s*(.*)$", x)
        if m:
            ja = m.group(1)
            if k + 1 < len(lines) and re.match(r"(?i)nghĩa\s*[:：]", lines[k + 1]):
                nghia = re.sub(r"(?i)^nghĩa\s*[:：]\s*", "", lines[k + 1])
            break
    return {"ja": ja, "nghia": nghia}


DOC_LA_RE = re.compile(r"(?i)đọc là\s*[\"'「“‘]?\s*([぀-ゟ゠-ヿー]+)")      # "Đọc là ていこう" → ていこう (chép vào options[i].reading)
FLAG_TEXT = {
    "thieu_cach_doc": "Không có dòng 'Cách đọc:' (question.reading = null)",
    "dong_pt_dinh_lien": "Các dòng phân tích bị dính liền, cần tách về đúng lựa chọn",
    "so_dong_pt_khac_4": "Phần PHÂN TÍCH không có đúng 4 dòng đánh số",
    "thu_tu_pt_lech": "Số thứ tự dòng phân tích không khớp thứ tự lựa chọn của đề",
    "lech_dap_an": "Số trong LỰA CHỌN ĐÚNG khác dap_an_so của đề",
    "thieu_phan_tich": "Thiếu phần PHÂN TÍCH",
    "thieu_lua_chon_dung": "Thiếu phần LỰA CHỌN ĐÚNG",
    "thieu_tham_khao": "Thiếu phần THÔNG TIN THAM KHẢO",
    "tham_khao_khong_nhan": "Phần tham khảo không có tiêu đề (nằm sau LỰA CHỌN ĐÚNG)",
    "thieu_dau_phan_cach": "Tiêu đề phần dính vào phần trước (thiếu ###)",
    "co_mo_dau": "PHÂN TÍCH có đoạn mở đầu trước dòng 1 (→ analysis.intro)",
    "co_ket_luan": "PHÂN TÍCH có đoạn sau dòng phân tích cuối (→ analysis.conclusion)",
    "lua_chon_cach_chu": "Lựa chọn của đề viết cách chữ / có khoảng trắng",
    "de_co_gach_chan_loi_giai_khong": "Đề có gạch chân nhưng phần đầu lời giải không in đậm / gạch chân (JSON không có { })",
    "nhieu_doan_danh_dau": "Một dòng có từ 2 đoạn in đậm / gạch chân",
    "danh_dau_rac": "Bản gốc có đoạn in đậm / gạch chân rỗng hoặc chỉ là dấu câu (đã bỏ thẻ)",
    "co_furigana": "Có furigana",
    "ruby_hong": "Có ruby hỏng trong bản gốc",
    "thieu_cau_hoan_chinh": "LỰA CHỌN ĐÚNG không có dòng 'Câu hoàn chỉnh:' (correct.full_sentence = null)",
    "khong_co_cho_trong": "Câu đề trong lời giải không có ký hiệu chỗ trống (________ / （　） / ( ))",
    "khong_ton_tai": "Có lựa chọn được ghi 'không tồn tại / không có nghĩa / không phải cách viết đúng'",
    "tu_ghep_khong_ro": "Có lựa chọn mà dòng thứ 2 không bắt đầu bằng từ ghép tiếng Nhật (cần xem cách tách compound)",
    "ky_hieu_trung": "Bản gốc có sẵn ký hiệu ｜《》 (trùng ký hiệu furigana)",
}
CTV_FLAGS = ("dong_pt_dinh_lien", "thu_tu_pt_lech", "lech_dap_an", "de_co_gach_chan_loi_giai_khong", "danh_dau_rac")
FURI_SKIP = [("correct", "option_ja")]      # bản sao của options[i].option_ja


def parse_and_flag(text, raw_html, lua_chon, dap_an_so, de_html):
    """Tách phần + gắn cờ + ghi chú bản gốc. Trả về (phan, co, ghi_chu)."""
    sec = split_sections(text)
    hl = head_lines(sec["dau"])
    mo, items, kl, glued = analysis_lines(sec["phan_tich"], lua_chon)
    co, gc = [], []
    if hl["cach_doc"] is None:
        co.append("thieu_cach_doc")
    if glued:
        co.append("dong_pt_dinh_lien")
    if sec["phan_tich"] is not None and len(items) != 4:
        co.append("so_dong_pt_khac_4")
    if any(it["lua_chon_khop"] and it["lua_chon_khop"] != it["so"] for it in items):
        co.append("thu_tu_pt_lech")
        gc.append("[Bản gốc VI] Số thứ tự trong PHÂN TÍCH không khớp thứ tự lựa chọn của đề")
    for k, name in (("phan_tich", "PHÂN TÍCH"), ("lua_chon_dung", "LỰA CHỌN ĐÚNG"), ("tham_khao", "THÔNG TIN THAM KHẢO")):
        if not (sec[k] or "").strip():
            co.append("thieu_" + {"phan_tich": "phan_tich", "lua_chon_dung": "lua_chon_dung", "tham_khao": "tham_khao"}[k])
            gc.append(f"[Bản gốc VI] Thiếu phần {name}")
    if sec["tham_khao_khong_nhan"]:
        co.append("tham_khao_khong_nhan")
    m = re.match(r"\s*(\d)", sec["lua_chon_dung"] or "")
    if m and str(m.group(1)) != str(dap_an_so):
        co.append("lech_dap_an")
        gc.append(f"[Bản gốc VI] LỰA CHỌN ĐÚNG ghi {m.group(1)}, khác đáp án của đề (dap_an_so = {dap_an_so})")
    if re.search(r"[^\n#\s]\s*(?:PHÂN TÍCH|LỰA CHỌN ĐÚNG|THÔNG TIN THAM KHẢO)", re.sub(r"<[^>]+>", "", raw_html or "")):
        co.append("thieu_dau_phan_cach")
    if sec["lua_chon_dung"] and cau_hoan_chinh(sec["lua_chon_dung"])["ja"] is None:
        co.append("thieu_cau_hoan_chinh")
    if not BLANK_RE.search(hl["cau_hoi"] or ""):
        co.append("khong_co_cho_trong")
    if mo.strip():
        co.append("co_mo_dau")
    if kl.strip():
        co.append("co_ket_luan")
    if any(re.search(r"[\s　]", o or "") for o in lua_chon):
        co.append("lua_chon_cach_chu")
    head_has = any("{" in (hl[k] or "") for k in hl)
    if not head_has and re.search(r"<u\b|underline|｛|\{", de_html or "", re.I):
        co.append("de_co_gach_chan_loi_giai_khong")
    if any((hl[k] or "").count("{") > 1 for k in hl):
        co.append("nhieu_doan_danh_dau")
    # dạng 05: 'không có nghĩa trong tiếng Nhật' là cách loại lựa chọn bình thường → KHÔNG gắn cờ khong_ton_tai (W1 – Sudachi – kiểm tra thay)
    if any(it["noi_dung"] and compound_line(it["noi_dung"]) is None for it in items):
        co.append("tu_ghep_khong_ro")
    phan = {"dau": hl, "phan_tich": {"mo_dau": mo, "dong": items, "ket_luan": kl}, "lua_chon_dung": sec["lua_chon_dung"],
            "tham_khao": sec["tham_khao"]}
    return phan, co, gc


def text_without_lcd(text):
    """Văn bản lời giải bỏ dòng nhãn đáp án trong LỰA CHỌN ĐÚNG (bản lặp của nhãn lựa chọn – không tính khi so furigana / { }).
    Dạng 05: GIỮ các dòng 'Câu hoàn chỉnh:' / 'Nghĩa:' (→ correct.full_sentence)."""
    sec = split_sections(text)
    lcd = [x for x in (sec["lua_chon_dung"] or "").split("\n") if x.strip()]
    giu = "\n".join(x for x in lcd if re.match(r"(?i)\s*(câu hoàn chỉnh|nghĩa)\s*[:：]", x))
    return "\n".join(x for x in (sec["dau"], sec["phan_tich"], giu, sec["tham_khao"]) if x)


# ---------------- kiểm tra riêng giai đoạn 1: K1–K10 ----------------
READING_OK = re.compile(r"^[぀-ゟ゠-ヿー・\s/、,，。]+$")


def _segs(s):
    from pipeline_chung.normalize import mark_segments
    return mark_segments(s)


def opt_text(o, gloss=True):
    """Toàn bộ chữ tiếng Việt của một lựa chọn: gloss + compound.meaning + analysis."""
    cp = o.get("compound") or {}
    parts = ([(o.get("gloss") or {}).get("vi")] if gloss else []) + [(cp.get("meaning") or {}).get("vi"), (o.get("analysis") or {}).get("vi")]
    return "\n".join(x for x in parts if x)


def check_k(doc, norm, policy):
    from pipeline_chung.common import vi_words
    loi, canh_bao = [], []
    de, phan = norm["de"], norm.get("phan") or {}
    an = doc.get("analysis") or {}
    opts = an.get("options") or []
    # K1
    if [o.get("index") for o in opts] != [1, 2, 3, 4]:
        loi.append(f"K1: analysis.options phải có đủ 4 lựa chọn theo thứ tự 1–4 (đang có {[o.get('index') for o in opts]})")
    # K2
    for o in opts:
        i = o.get("index")
        if isinstance(i, int) and 1 <= i <= 4 and not _eq(o.get("option_ja"), de["lua_chon"][i - 1]):
            loi.append(f"K2: lựa chọn {i}: option_ja '{o.get('option_ja')}' khác đề '{de['lua_chon'][i - 1]}'")
    # K3 – còn dính phân tích của lựa chọn khác / bản gốc có mà JSON null
    for o in opts:
        a = strip_marks(opt_text(o))
        for other in opts:
            if other is o:
                continue
            for m in re.finditer(rf"(?<=[^\d])\s*{other.get('index')}\s*[\.．]\s*", a):
                lab = parse_label(a[m.end():].split("\n")[0])
                if lab and _eq(lab[0], other.get("option_ja")):
                    loi.append(f"K3: phân tích lựa chọn {o.get('index')} còn chứa phân tích của lựa chọn {other.get('index')} (chưa tách)")
    src_line = {}
    for it in (phan.get("phan_tich") or {}).get("dong", []):
        j = it["lua_chon_khop"] or it["so"]
        src_line.setdefault(j, it)
    for j, it in src_line.items():
        if 1 <= j <= len(opts) and (it["noi_dung"] or it["gloss"]) and not opt_text(opts[j - 1]).strip():
            loi.append(f"K3: bản gốc có phân tích lựa chọn {j} nhưng JSON để trống (gloss / compound / analysis đều null)")
    # K5 – { } ở phần đầu nằm đúng trường
    q = doc.get("question") or {}
    hl = phan.get("dau") or {}
    for name, key, val in (("question.ja", "cau_hoi", q.get("ja")), ("question.reading", "cach_doc", q.get("reading")),
                           ("question.meaning.vi", "nghia", (q.get("meaning") or {}).get("vi"))):
        if _segs(val or "") != _segs(hl.get(key) or ""):
            loi.append(f"K5: {name}: đánh dấu {{ }} {_segs(val or '')} khác dòng tương ứng của lời giải {_segs(hl.get(key) or '')}")
    if (hl.get("cach_doc") is None) != (q.get("reading") is None):
        loi.append("K5: question.reading phải là null khi và chỉ khi lời giải không có dòng 'Cách đọc:'")
    # K6
    c = doc.get("correct") or {}
    if str(c.get("index")) != str(de["dap_an_so"]):
        loi.append(f"K6: correct.index = {c.get('index')} khác dap_an_so = {de['dap_an_so']}")
    elif "lech_dap_an" in norm["co"]:
        canh_bao.append(f"K6: lời giải gốc ghi đáp án khác đề – JSON đã theo dap_an_so = {de['dap_an_so']}")
    di = c.get("index")
    if isinstance(di, int) and 1 <= di <= len(opts) and c.get("option_ja") != opts[di - 1].get("option_ja"):
        loi.append(f"K6: correct.option_ja '{c.get('option_ja')}' phải giống hệt options[{di - 1}].option_ja")
    # K7 – tham khảo: đủ số ví dụ, đúng thứ tự, chép đúng từ tiếng Nhật
    ref_src, ref = phan.get("tham_khao"), doc.get("reference")
    if bool((ref_src or "").strip()) != (ref is not None):
        loi.append("K7: reference phải null khi và chỉ khi bản gốc không có phần THÔNG TIN THAM KHẢO")
    elif ref is not None:
        intro_src, terms_src, note_src = ref_terms(ref_src)
        terms = ref.get("terms") or []
        if len(terms) != len(terms_src):
            loi.append(f"K7: reference.terms có {len(terms)} ví dụ, bản gốc có {len(terms_src)} dòng ví dụ")
        else:
            for k, (t, (ja, doc_, _)) in enumerate(zip(terms, terms_src)):
                if norm_ja(strip_marks(t.get("ja") or "")) != norm_ja(strip_marks(ja)) and not (norm_ja(strip_marks(t.get("ja") or "")) in norm_ja(strip_marks(ja))):
                    loi.append(f"K7: reference.terms[{k}].ja '{t.get('ja')}' khác bản gốc '{ja}'")
                if (doc_ or None) != (t.get("reading") or None) and not (doc_ and t.get("reading") and norm_ja(doc_) == norm_ja(t["reading"])):
                    loi.append(f"K7: reference.terms[{k}].reading '{t.get('reading')}' phải chép đúng ngoặc của bản gốc: '{doc_}'")
        if bool(note_src.strip()) != (ref.get("note") is not None):
            loi.append("K7: reference.note phải null khi và chỉ khi bản gốc không có đoạn văn sau danh sách ví dụ")
        elif note_src.strip():
            cs, co_ = collections.Counter(vi_words(note_src)), collections.Counter(vi_words((ref.get("note") or {}).get("vi") or ""))
            if cs and sum((cs & co_).values()) / sum(cs.values()) < 0.97:
                loi.append(f"K7: reference.note thiếu chữ so với bản gốc: {[w for w, _ in (cs - co_).most_common(8)]}")
        if bool(intro_src.strip()) != (ref.get("intro") is not None):
            loi.append("K7: reference.intro phải null khi và chỉ khi bản gốc không có dòng giới thiệu trước các ví dụ")
    # K8 – label_paren chép đúng ngoặc ở nhãn dòng phân tích
    for o in opts:
        it = src_line.get(o.get("index"))
        if it is not None:
            want, got = it["doc"] or None, o.get("label_paren") or None
            if want != got and not (want and got and norm_ja(want) == norm_ja(got)):
                loi.append(f"K8: lựa chọn {o.get('index')}: label_paren '{got}' phải chép đúng ngoặc ở nhãn dòng phân tích: '{want}'")
    # K12 – câu hoàn chỉnh (correct.full_sentence) theo dòng 'Câu hoàn chỉnh:' / 'Nghĩa:' trong LỰA CHỌN ĐÚNG
    fs_src = cau_hoan_chinh(phan.get("lua_chon_dung"))
    fs = c.get("full_sentence")
    if (fs_src["ja"] is None) != (fs is None):
        loi.append("K12: correct.full_sentence phải null khi và chỉ khi LỰA CHỌN ĐÚNG không có dòng 'Câu hoàn chỉnh:'")
    elif fs is not None:
        k_ = lambda t: re.sub(r"[\s　]", "", norm_ja(t or ""))  # noqa: E731
        if k_(fs.get("ja")) != k_(fs_src["ja"]):
            loi.append(f"K12: full_sentence.ja khác dòng 'Câu hoàn chỉnh:' của bản gốc: '{fs_src['ja']}'")
        if (fs_src["nghia"] is None) != (fs.get("meaning") is None):
            loi.append("K12: full_sentence.meaning phải null khi và chỉ khi không có dòng 'Nghĩa:' sau 'Câu hoàn chỉnh:'")
    # K13 – giữ nguyên số chỗ trống ở câu đề / cách đọc / nghĩa
    for name, key, val in (("question.ja", "cau_hoi", q.get("ja")), ("question.reading", "cach_doc", q.get("reading")),
                           ("question.meaning.vi", "nghia", (q.get("meaning") or {}).get("vi"))):
        if val is not None and hl.get(key) is not None and len(BLANK_RE.findall(val)) != len(BLANK_RE.findall(hl[key])):
            loi.append(f"K13: {name}: số chỗ trống {len(BLANK_RE.findall(val))} khác bản gốc {len(BLANK_RE.findall(hl[key]))} – phải giữ nguyên ký hiệu chỗ trống")
    # K9 – độ phủ chữ Việt theo từng lựa chọn (gloss + compound.meaning + analysis so với dòng nhãn + dòng từ ghép)
    pass  # collections đã import đầu file
    for j, it in src_line.items():
        if not (1 <= j <= len(opts)):
            continue
        src = collections.Counter(vi_words((it["gloss"] or "") + "\n" + (it["noi_dung"] or "")))
        o_ = opts[j - 1]
        out = collections.Counter(vi_words(opt_text(o_) + "\n" + (o_.get("label_paren") or "") + "\n" + ((o_.get("compound") or {}).get("reading") or "")))   # ngoặc có thể là chữ Việt ('Thể từ điển là こむ')
        if src and sum((src & out).values()) / sum(src.values()) < 0.97 and "dong_pt_dinh_lien" not in norm["co"]:
            loi.append(f"K9: phân tích lựa chọn {j} thiếu chữ so với bản gốc: {[w for w, _ in (src - out).most_common(8)]}")
    # K14 – is_valid khớp lời giải; K15 – từ ghép chứa lựa chọn; K16 – đáp án phải là từ ghép có nghĩa
    for o in opts:
        i, cp = o.get("index"), o.get("compound")
        txt = strip_marks(opt_text(o, gloss=False))
        if cp is None:
            if o.get("is_valid") is not None:
                loi.append(f"K14: lựa chọn {i}: không có compound thì is_valid phải null")
            continue
        neg = bool(KHONG_TON_TAI_RE.search(txt))
        if o.get("is_valid") is None:
            loi.append(f"K14: lựa chọn {i}: có compound thì is_valid phải true/false")
        elif o.get("is_valid") == neg:
            loi.append(f"K14: lựa chọn {i}: is_valid = {o.get('is_valid')} nhưng lời giải {'ghi' if neg else 'không ghi'} 'không có nghĩa / không tồn tại' "
                       "(is_valid = lời giải nói từ ghép CÓ tồn tại)")
        if neg and (cp.get("meaning") or None) is not None:
            canh_bao.append(f"K14: lựa chọn {i}: lời giải ghi 'không có nghĩa' nhưng compound.meaning không null – xem lại cách tách")
        core = re.sub(r"(だ|です)$", "", norm_ja(strip_marks(o.get("option_ja") or "")))
        if core and core not in norm_ja(strip_marks(cp.get("ja") or "")) + norm_ja(strip_marks(cp.get("reading") or "")):
            canh_bao.append(f"K15: lựa chọn {i}: từ ghép '{cp.get('ja')}' không chứa lựa chọn '{o.get('option_ja')}'")
    if isinstance(di, int) and 1 <= di <= len(opts) and opts[di - 1].get("is_valid") is False:
        canh_bao.append(f"K16: đáp án (lựa chọn {di}) bị lời giải ghi 'không có nghĩa' – nghi lỗi nội dung")
    # K10
    for key, flag, name in (("intro", "co_mo_dau", "mở đầu"), ("conclusion", "co_ket_luan", "kết luận")):
        if (flag in norm["co"]) != (an.get(key) is not None):
            canh_bao.append(f"K10: analysis.{key}: bản gốc {'có' if flag in norm['co'] else 'không có'} đoạn {name} nhưng JSON {'null' if an.get(key) is None else 'có'}")
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
    ref = doc_ko.get("reference") or {}
    if ref.get("vi") is not None and isinstance(ref.get(lang), str):
        lines = lambda t: [x for x in t.split("\n") if x.strip()]  # noqa: E731
        nums = lambda t: re.findall(r"(?m)^\s*(\d+)\s*[\.．\)]", t)  # noqa: E731
        if len(lines(ref["vi"])) != len(lines(ref[lang])) or nums(ref["vi"]) != nums(ref[lang]):
            loi.append("D2: reference: số dòng / cách đánh số của bản dịch khác tiếng Việt")
    return loi, canh_bao


def is_style_field(path):
    return "analysis" in path or "reference" in path


# ---------------- hiển thị cho Excel CTV (dựng lại đúng thứ tự format) ----------------
def _t(obj, lang):
    return show((obj or {}).get(lang) or "") if obj else ""


def render(d, lang):
    q, an, c = d.get("question") or {}, d.get("analysis") or {}, d.get("correct") or {}
    out = [f"{bold('【Câu hỏi】')} {show(q.get('ja', ''))}"]
    if q.get("reading"):
        out.append(f"{bold('【Cách đọc】')} {show(q['reading'])}")
    out.append(f"{bold('【Nghĩa】')} {_t(q.get('meaning'), lang)}")
    out.append(bold("【PHÂN TÍCH】"))
    if an.get("intro"):
        out.append(_t(an["intro"], lang))
    for o in an.get("options", []):
        lab = show(o.get("option_ja", "")) + (f" ({o['label_paren']})" if o.get("label_paren") else "")
        out.append(f"{bold(str(o['index']) + '. ' + lab)}" + (f" - {_t(o.get('gloss'), lang)}" if o.get("gloss") else ""))
        cp = o.get("compound")
        if cp:
            head = show(cp.get("ja", "")) + (f" ({show(cp['reading'])})" if cp.get("reading") else "")
            body = " ".join(x for x in (_t(cp.get("meaning"), lang), _t(o.get("analysis"), lang)) if x)
            out.append(f"   {head}: {body}")
        elif o.get("analysis"):
            out.append(f"   {_t(o.get('analysis'), lang)}")
    if an.get("conclusion"):
        out.append(_t(an["conclusion"], lang))
    out.append(f"{bold('【LỰA CHỌN ĐÚNG】')} {c.get('index')}. {show(c.get('option_ja', ''))}")
    fs = c.get("full_sentence")
    if fs:
        out.append(f"{bold('Câu hoàn chỉnh:')} {show(fs.get('ja', ''))}")
        if fs.get("meaning"):
            out.append(f"{bold('Nghĩa:')} {_t(fs['meaning'], lang)}")
    ref = d.get("reference")
    if ref:
        out.append(bold("【THÔNG TIN THAM KHẢO】"))
        if ref.get("intro"):
            out.append(_t(ref["intro"], lang))
        for t in ref.get("terms") or []:
            out.append(f"- {show(t.get('ja', ''))}" + (f" ({show(t['reading'])})" if t.get("reading") else "") + f": {_t(t.get('meaning'), lang)}")
        if ref.get("note"):
            out.append(_t(ref["note"], lang))
    return "\n".join(out)


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


def format_hints(norm):
    """Các chỗ nghi lỗi định dạng trong lời giải gốc (chỉ là gợi ý cho Claude, không quyết định trạng thái)."""
    t = norm.get("src_text") or ""
    out = []
    for name, rx in FORMAT_HINT_RES:
        for m in rx.finditer(t):
            out.append(f"{name}: …{t[max(0, m.start() - 15):m.end() + 15].replace(chr(10), '⏎')}…")
    return out[:12]


# ---------------- Dạng 05: gợi ý từ điển SudachiPy (F1) – chỉ GỢI Ý cho Claude, không quyết định trạng thái ----------------
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


def tu_dien(word):
    """Tra từ ghép (có thể đang ở dạng chia: はりあって, 持ち上げて, 泥だらけだ) → (dictionary_form, POS) nếu từ điển có MỘT từ (sau khi bỏ trợ từ / trợ động từ ở đuôi), không thì None."""
    t = _tok()
    if not t:
        return None
    from sudachipy import SplitMode
    w = re.sub(r"[。．.、\s　「」'\"“”‘’]", "", strip_marks(word or ""))
    if not w:
        return None
    ms = [m for m in t.tokenize(w, SplitMode.C) if m.part_of_speech()[0] != "補助記号"]
    while len(ms) > 1 and ms[-1].part_of_speech()[0] in ("助詞", "助動詞"):
        ms = ms[:-1]
    if (len(ms) == 1 and not ms[0].is_oov() and ms[0].part_of_speech()[1] != "固有名詞" and len(ms[0].surface()) >= 2
            and len(ms[0].surface()) >= len(re.sub(r"(ます|ました|ません|て|で|た|だ|る)$", "", w)) - 1):
        return ms[0].dictionary_form(), ms[0].part_of_speech()[0], _hira(ms[0].reading_form())
    return None


def sudachi_hints(norm):
    """Gợi ý cho bước 1.2 (Claude xác nhận rồi mới gắn cờ):
    W1 – từ ghép bị ghi 'không có nghĩa' nhưng từ điển có;
    W2 – cách đọc trong ngoặc của từ ghép / từ tham khảo khác cách đọc từ điển;
    W3 – từ tham khảo không chứa thành phần đáp án, hoặc chứa nhưng đọc khác hẳn;
    F1 – câu hoàn chỉnh ≠ câu đề + đáp án (cho phép đổi đuôi だ → だった…)."""
    if not _tok() or not norm.get("phan"):
        return []
    de, ph = norm["de"], norm["phan"]
    out = []
    items = (ph.get("phan_tich") or {}).get("dong") or []
    for it in items:
        cl = compound_line(it["noi_dung"])
        if not cl:
            continue
        w, paren, rest = cl
        r = tu_dien(w)
        if KHONG_TON_TAI_RE.search(rest or "") and r:
            out.append(f"W1: lựa chọn {it['so']} – '{w}' bị ghi 'không có nghĩa' nhưng từ điển có từ {r[0]} ({r[1]}, đọc {r[2]})")
        if paren and re.fullmatch(r"[぀-ゟー]+", paren) and r and _seion(r[2]) != _seion(paren) and _seion(_yomi(w)) != _seion(paren):
            out.append(f"W2: lựa chọn {it['so']} – cách đọc '{paren}' của '{w}' khác từ điển '{_yomi(w)}'")
    try:
        da = int(de["dap_an_so"])
    except (TypeError, ValueError):
        da = 0
    if ph.get("tham_khao") and 1 <= da <= 4:
        _, terms, _ = ref_terms(ph["tham_khao"])
        it = next((x for x in items if (x["lua_chon_khop"] or x["so"]) == da), None)
        opt = strip_marks(de["lua_chon"][da - 1])
        kanji = "".join(re.findall(r"[㐀-鿿]", opt))
        okuri = re.sub(r"^[㐀-鿿]+", "", opt) if kanji and opt.startswith(kanji) else ""
        doc_opt = (it or {}).get("doc") if it and re.fullmatch(r"[぀-ゟー]+", (it or {}).get("doc") or "") else None
        if doc_opt and okuri and doc_opt.endswith(okuri):
            doc_opt = doc_opt[: -len(okuri)]                       # 深く (ふかく) → ふか: chỉ phần đọc của chữ Hán
        kana_core = _seion(re.sub(r"[てでただっ]+$", "", opt))[:1] if not kanji else ""
        for ja, doc_, _ in terms:
            if not doc_:
                continue
            if re.fullmatch(r"[぀-ゟー・\s/]+", doc_):
                y = _yomi(ja)
                if y and _seion(y) != _seion(doc_):
                    out.append(f"W2: tham khảo '{ja}' – cách đọc '{doc_}' khác từ điển '{y}'")
            if kanji and kanji not in ja:
                out.append(f"W3: tham khảo '{ja}' không chứa chữ '{kanji}' của đáp án '{opt}'")
            elif not kanji and kana_core and kana_core not in _seion(doc_ if re.fullmatch(r"[぀-ゟー]+", doc_) else _yomi(ja)):
                out.append(f"W3: tham khảo '{ja} ({doc_})' không chứa thành phần đáp án '{opt}'")
            elif doc_opt and len(kanji) == 1 and re.fullmatch(r"[぀-ゟー]+", doc_):
                v = {_seion(doc_opt), _seion(doc_opt[:-1] + "つ") if doc_opt[-1] in "くきつち" else _seion(doc_opt)}
                if not any(x in _seion(doc_) for x in v):
                    out.append(f"W3: tham khảo '{ja} ({doc_})' – chữ '{kanji}' đọc khác cách đọc ở đáp án '{(it or {}).get('doc')}'")
    out += _f1(de, ph, da)
    return out


def _f1(de, ph, da):
    fs = cau_hoan_chinh(ph.get("lua_chon_dung"))["ja"]
    cau = (ph.get("dau") or {}).get("cau_hoi") or ""
    if not fs or not (1 <= da <= 4) or not BLANK_RE.search(cau):
        return []
    opt = de["lua_chon"][da - 1]
    yfs = _yomi(fs)
    for o in (opt, re.sub(r"(だ|です)$", "", opt)):
        g = BLANK_RE.sub(lambda m: o, cau, count=1)
        if _yomi(g) == yfs:
            return []
        pre = BLANK_RE.split(cau, maxsplit=1)[0] + o
        if o != opt and yfs.startswith(_yomi(pre)) and abs(len(yfs) - len(_yomi(g))) <= 3:
            return []                                    # đáp án đổi đuôi trong câu hoàn chỉnh (だらけだ → だらけだった)
    ghep = BLANK_RE.sub(lambda m: opt, cau, count=1)
    return [f"F1: câu hoàn chỉnh khác câu đề + đáp án {da} '{opt}' – câu ghép: '{strip_marks(ghep).replace(chr(10), ' ')}' | câu hoàn chỉnh: '{strip_marks(fs)}'"]
