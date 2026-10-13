"""Phần riêng của dạng 16 – Nghe hiểu chủ đề (dựng 2026-10-08, chạy hoàn toàn bằng Claude Opus 5.5 Cowork).

Phần chung (cấu hình, đường dẫn, kho đã duyệt, chọn phạm vi --tu/--den) chép từ dạng 09.
Phần riêng: chuẩn bị mẫu (GĐ0) dựa trên scripts/_nghe.py; JSON do Python dựng cho câu không có phân tích;
hook bổ sung full_translation; kiểm tra K1–K12 (+ K-TD, K-CH, K-TK); hiển thị Excel CTV.
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
    os.environ["PIPELINE_DATA"] = _c.get("du_lieu_test", "data/test_16_nghe_hieu_chu_de.csv")


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



# =====================================================================================
# PHẦN RIÊNG DẠNG 16
# =====================================================================================
import _nghe as NH  # noqa: E402
from pipeline_chung.common import JA_RE, iter_strings, vi_words  # noqa: E402
from pipeline_chung.normalize import mark_segments, normalize_html, paren_readings, pairs  # noqa: E402

SCHEMA_ID = "reading_listening.v1"

# ---------------- cờ (giai đoạn 0) ----------------
FLAG_TEXT = {
    "lua_chon_tranh": "Lựa chọn là tranh ('1'…'4') – option_ja = số, meaning = null; mô tả tranh trong phân tích không kiểm chứng được",
    "thieu_phan_tich": "Lời giải KHÔNG có phân tích 4 lựa chọn (chỉ bản dịch / chỉ lời thoại) – Python dựng JSON, gắn cờ thieu_noi_dung → CTV tiếng Nhật",
    "thieu_ban_dich": "Không có bản dịch Việt của lời thoại – full_translation.lines[].meaning = null",
    "thieu_loi_thoai": "Không tìm thấy lời thoại tiếng Nhật – full_translation chỉ có bản dịch (ja = null) hoặc null",
    "lech_dong": "Số dòng lời thoại Nhật ≠ số dòng bản dịch Việt – tác tử TẠO tự ghép full_translation",
    "nguoi_noi_lech": "Ghép dòng khớp số lượng nhưng có dòng một bên có nhãn người nói, bên kia không – xem lại ghép dòng",
    "nguon_loi_thoai_doan_van": "Lời thoại tiếng Nhật lấy từ cột doan_van (cột transcript_vi bị dán nhầm phân tích / bản dịch)",
    "nguon_loi_thoai_giai_thich_vi": "Lời thoại tiếng Nhật lấy từ phần đầu lời giải (cột lời thoại trống / sai)",
    "phan_tich_o_transcript": "Phần phân tích nằm ở cột transcript_vi (lời giải chỉ có bản dịch)",
    "ban_dich_o_transcript_vi": "Bản dịch Việt lấy từ cột transcript_vi",
    "ban_dich_o_doan_van": "Bản dịch Việt lấy từ cột doan_van",
    "mo_dau_phan_tich": "Có đoạn phân tích mở đầu trước khối 1. ('Phân tích đoạn hội thoại: …') → summary",
    "phu_loi_thoai": "Có khối phụ sau lời thoại (từ vựng **言葉表現 / ghi chú) → nhóm thứ 2 của full_translation",
    "so_khoi_khac_4": "Phần phân tích không có đúng 4 khối 1.–4.",
    "khong_co_dung": "Không khối nào kết luận '→ ĐÚNG'",
    "nhieu_dung": "Nhiều khối kết luận '→ ĐÚNG'",
    "lech_dap_an": "Khối '→ ĐÚNG' khác dap_an_so của đề",
    "khoi_khong_ket_luan": "Có khối không có '→ ĐÚNG/SAI'",
    "khoi_nhieu_ket_luan": "Có khối có hơn một '→ ĐÚNG/SAI'",
    "khong_cau_hoi_cuoi": "Lời thoại không kết thúc bằng câu hỏi lặp lại – question lấy từ dòng mở đầu / cột cau_hoi",
    "trich_ngoai_loi_thoai": "Có câu trích 「…」 không tìm thấy nguyên văn trong lời thoại (so bỏ furigana / dấu câu)",
    "co_furigana": "Có furigana",
    "ruby_hong": "Có ruby hỏng trong bản gốc",
    "danh_dau_rac": "Bản gốc có đoạn in đậm / gạch chân rỗng hoặc chỉ là dấu câu (đã bỏ thẻ)",
    "ky_hieu_trung": "Bản gốc có sẵn ký hiệu ｜《》 (trùng ký hiệu furigana)",
    "dap_an_de_loi": "Dữ liệu đề lỗi: dap_an_so không phải 1–4",
}
CTV_FLAGS = ("lech_dap_an", "nhieu_dung", "khong_co_dung", "thieu_phan_tich", "thieu_loi_thoai", "trich_ngoai_loi_thoai", "dap_an_de_loi")
FURI_SKIP = [("question", "ja"), ("correct", "option_ja")]   # question.ja là bản sao một dòng lời thoại, correct.option_ja là bản sao option_ja (đề có furigana – 12505_1) – không tính 2 lần khi so furigana


def plain(html):
    """Đề / lựa chọn → văn bản (furigana ｜《》, bỏ { })."""
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", html or "").replace("\\&quot;", "").replace("&quot;", "")
    return normalize_html(s)[0].replace("{", "").replace("}", "").strip()


def _dong_an(b, g):
    """Văn bản nguồn của một khối (đã bỏ phần dẫn câu trích tách được, '→ ĐÚNG/SAI', dòng lựa chọn trùng đề)."""
    out, dong, i = [], [], 0
    while i < len(b["dong"]):                                       # 'dẫn: 「ja」' + dòng '(nghĩa)' → một dòng (lô 71–80)
        a = b["dong"][i].strip()
        m2 = NH.PAREN_DONG_RE.match(b["dong"][i + 1]) if i + 1 < len(b["dong"]) else None
        if m2 and not NH.DICH_DONG_RE.match(b["dong"][i + 1]) and "「" in a and a.endswith("」") \
                and not a.startswith("「") and not NH.QUOTE_RE.search(a):
            dong.append(a + "(" + m2.group(1) + ")")
            i += 2
            continue
        dong.append(b["dong"][i])
        i += 1
    for ln in dong:
        ln2 = NH.VERDICT_DONG_RE.sub(" ", ln).strip()
        t = NH.tach_dong_trich(ln2)
        if t:
            for d in t[1]:
                ln2 = ln2.replace(d, "", 1)
        if ln2.strip() and ln2.strip() not in (g.get("dan") or []):   # dòng dẫn đứng riêng đã gộp với câu trích tách được (lô 31–40)
            out.append(ln2.strip())
    return out


def _vi_cua_khoi(g):
    """Chữ tiếng Việt của khối theo gợi ý (để đo độ phủ từng lựa chọn)."""
    return "\n".join(x for x in [g.get("nghia_lua_chon")] + [q["nghia"] for q in g["trich"]] + [g.get("phan_tich")] if x)


def chuan_bi_mau(row):
    """Một dòng CSV → bản ghi chuẩn hóa output/samples/norm/<id>.json."""
    from pipeline_chung.common import sha
    sid = sid_of(row)
    lua_chon = [plain(row.get(f"lua_chon_{i}", "")) for i in range(1, 5)]
    dap_raw = (row.get("dap_an_so") or "").strip()
    dap = int(dap_raw) if dap_raw in ("1", "2", "3", "4") else None
    rec = {"sample_id": sid, "question_id": int(row["question_id"]), "cau_con": int(row["cau_con"]), "cap_do": row["cap_do"],
           "hash_goc": sha("|".join(row.get(k, "") for k in ("giai_thich_vi", "transcript_vi", "doan_van", "cau_hoi")) + "|"
                           + "|".join(lua_chon) + "|" + dap_raw),
           "de": {"cau_hoi": plain(row.get("cau_hoi", "")), "lua_chon": lua_chon, "dap_an_so": dap if dap else dap_raw,
                  "dap_an_noi_dung": plain(row.get("dap_an_noi_dung", "")), "de_bai_chung": plain(row.get("de_bai_chung", ""))},
           "co": [], "ghi_chu_ban_goc": [], "ruby_hong": [], "danh_dau_rac": [], "phan": {"tham_khao": None}}
    cot, raw_all = {}, ""
    for k in ("doan_van", "transcript_vi", "giai_thich_vi"):
        t, br, rac = NH.lam_sach(row.get(k, ""))
        cot[k] = t
        rec["ruby_hong"] += br
        rec["danh_dau_rac"] += rac
        raw_all += row.get(k, "") or ""
    if not (cot["giai_thich_vi"].strip() or cot["transcript_vi"].strip()):
        rec.update(khuon_goc="trong", tao_bang=None, nghe=None, dau_vao=None, src_text="", src_vi_text="", src_text_furi="", marks_src=[])
        rec["ghi_chu_ban_goc"].append("[Bản gốc VI] Không có lời giải / lời thoại")
        return rec
    t = NH.tach_cau(cot, lua_chon, dap)
    co = list(t["co"])
    goi_y = [NH.goi_y_khoi(b) for b in t["khoi"]]
    # quote ngoài lời thoại
    ja_all = "\n".join(x["text"] for x in t["loi_thoai_ja"] + t["phu_ja"])
    ngoai = [q["ja"] for g in goi_y for q in g["trich"] if ja_all and not NH.trong_loi_thoai(q["ja"], ja_all)]
    if ngoai:
        co.append("trich_ngoai_loi_thoai")
    if not dap:
        co.append("dap_an_de_loi")
    if any(ch in raw_all for ch in "｜《》"):
        co.append("ky_hieu_trung")
    khuon = ("E" if "thieu_loi_thoai" in co else "A" if t["khoi"] else "C" if "thieu_ban_dich" not in co else "D")
    tao_bang = "python" if (not t["khoi"] and "lech_dong" not in co) else "tac_tu"
    # ---- văn bản nguồn cho kiểm tra ----
    ja_src = NH._chuoi(t["loi_thoai_ja"] + t["phu_ja"])
    vi_lines = [x["text"] for x in t["ban_dich_vi"] + t["phu_vi"]]
    vi_ds = list(t["ds_lua_chon_vi"].values())
    an_lines = [x for x in (t["phan_tich_mo_dau"] or "").split("\n") if x.strip()]
    for b, g in zip(t["khoi"], goi_y):
        dau = b["dau"]
        m = re.match(r"^(.*?)\s*[（(]([^()（）]*)[)）]\s*$", dau)
        dau_ja = m.group(1) if (m and g["nghia_lua_chon"] and g["nghia_lua_chon"] == m.group(2).strip()) else dau
        if dau_ja.strip() and NH._k(dau_ja) != NH._k(lua_chon[b["so"] - 1] if b["so"] <= 4 else ""):
            an_lines.append(dau_ja)                  # dòng 'n.' viết khác lựa chọn của đề → nội dung giữ trong analysis
        if m and g["nghia_lua_chon"] and g["nghia_lua_chon"] == m.group(2).strip():
            an_lines.append(g["nghia_lua_chon"])
        for x in _dong_an(b, g):                     # dòng 'Nghĩa: …' trùng bản dịch lựa chọn đã có trong vi_ds → không đếm hai lần (lô 71–80)
            mn = NH.NGHIA_RE.match(x)
            if mn and mn.group(1).strip() in [v.strip() for v in vi_ds]:
                continue
            an_lines.append(x)
    src_text = "\n".join([ja_src] + vi_lines + vi_ds + an_lines + [x for x in lua_chon if x])
    q_vi = (t["goi_y_cau_hoi"] or {}).get("vi")
    src_vi = "\n".join(vi_lines + vi_ds + an_lines + ([q_vi] if q_vi else []))
    # ---- đầu vào hiển thị cho tác tử KIỂM TRA / TẠO ----
    L = []
    L.append("【LỜI THOẠI – tiếng Nhật】 (nguồn: %s)" % (t["nguon"]["nguon_ja"] or "không có"))
    L += [f"  J{i + 1}. " + ((x["speaker"] + "：") if x["speaker"] else "") + x["text"] for i, x in enumerate(t["loi_thoai_ja"])]
    if t["phu_ja"]:
        L.append("  (khối phụ)")
        L += [f"  JP{i + 1}. " + x["text"] for i, x in enumerate(t["phu_ja"])]
    L.append("【BẢN DỊCH – tiếng Việt】 (nguồn: %s)" % (t["nguon"]["nguon_vi"] or "không có"))
    L += [f"  V{i + 1}. " + ((x["speaker"] + ": ") if x["speaker"] else "") + x["text"] for i, x in enumerate(t["ban_dich_vi"])]
    if t["phu_vi"]:
        L.append("  (khối phụ)")
        L += [f"  VP{i + 1}. " + x["text"] for i, x in enumerate(t["phu_vi"])]
    if t["ds_lua_chon_vi"]:
        L.append("【Dịch các lựa chọn trong bản dịch】 " + " | ".join(f"{k}. {v}" for k, v in t["ds_lua_chon_vi"].items()))
    if t["phan_tich_mo_dau"]:
        L.append("【PHÂN TÍCH MỞ ĐẦU】")
        L.append(t["phan_tich_mo_dau"])
    L.append("【PHÂN TÍCH】 (nguồn: %s)" % (t["nguon"]["nguon_phan_tich"] or "không có"))
    for b in t["khoi"]:
        L.append(f"{b['so']}. {b['dau']}".rstrip())
        L += b["dong"]
        L.append("")
    rec.update(khuon_goc=khuon, tao_bang=tao_bang, nghe=t, goi_y_khoi=goi_y, goi_y_tom_tat=NH.goi_y_tom_tat(t["phan_tich_mo_dau"]),
               dau_vao="\n".join(L).strip(), src_text=src_text, src_vi_text=src_vi, src_text_furi=src_text,
               marks_src=mark_segments(src_text), trich_ngoai=ngoai)
    # ---- ghi chú bản gốc tự động ----
    gc = rec["ghi_chu_ban_goc"]
    if "thieu_phan_tich" in co:
        gc.append("[Bản gốc VI] Lời giải không có phân tích các lựa chọn" + (" (chỉ có lời thoại tiếng Nhật, không có bản dịch)" if "thieu_ban_dich" in co else " (chỉ có bản dịch lời thoại)"))
    if "thieu_loi_thoai" in co:
        gc.append("[Bản gốc VI] Không tìm thấy lời thoại tiếng Nhật trong dữ liệu")
    elif "thieu_ban_dich" in co and "thieu_phan_tich" not in co:
        gc.append("[Bản gốc VI] Không có bản dịch Việt của lời thoại")
    for c, txt in (("lech_dap_an", "Khối '→ ĐÚNG' khác đáp án của đề (dap_an_so = %s)" % dap_raw), ("nhieu_dung", "Nhiều khối kết luận '→ ĐÚNG'"),
                   ("khong_co_dung", "Không khối nào kết luận '→ ĐÚNG'"), ("so_khoi_khac_4", "Phần phân tích không có đủ 4 khối"),
                   ("dap_an_de_loi", f"Dữ liệu đề lỗi: dap_an_so = '{dap_raw}'")):
        if c in co:
            gc.append("[Bản gốc VI] " + txt)
    if ngoai:
        gc.append(f"[Bản gốc VI] {len(ngoai)} câu trích không tìm thấy nguyên văn trong lời thoại: " + " | ".join(x[:40] for x in ngoai[:3]))
    if rec["ruby_hong"]:
        co.append("ruby_hong")
        gc.append(f"[Bản gốc VI] Có {len(rec['ruby_hong'])} thẻ ruby hỏng")
    if rec["danh_dau_rac"]:
        co.append("danh_dau_rac")
    if pairs(src_text):
        co.append("co_furigana")
    rec["doc_trong_ngoac"] = paren_readings(src_text)
    rec["co"] = sorted(set(co))
    return rec


# ---------------- thứ tự chạy ----------------
def tao_thu_tu(recs, cfg_):
    """100 câu đầu = 20 câu mỗi cấp N1–N5 xen kẽ; trong mỗi cấp trộn đều: câu lựa chọn tranh / chữ, có ~2 câu không phân tích."""
    import random
    tc = cfg_.get("thu_tu_chay") or {}
    rng = random.Random(tc.get("seed", 2026))
    n = tc.get("moi_cap_do", 20)
    lv = {}
    for k in ["N1", "N2", "N3", "N4", "N5"]:
        pool = [r for r in recs if r["cap_do"] == k and r["khuon_goc"] != "trong"]
        rng.shuffle(pool)
        nhom = {"tranh": [r for r in pool if "lua_chon_tranh" in r["co"] and r["tao_bang"] == "tac_tu"],
                "chu": [r for r in pool if "lua_chon_tranh" not in r["co"] and r["tao_bang"] == "tac_tu"],
                "python": [r for r in pool if r["tao_bang"] == "python"]}
        chon = nhom["python"][:2]
        i = 0
        while len(chon) < n and (nhom["tranh"] or nhom["chu"]):
            k2 = ("tranh", "chu")[i % 2]
            if nhom[k2]:
                chon.append(nhom[k2].pop(0))
            i += 1
        rng.shuffle(chon)
        lv[k] = chon
    dau = [lv[k][i] for i in range(n) for k in ["N1", "N2", "N3", "N4", "N5"] if i < len(lv[k])]
    # lô pilot (10 câu đầu) phải có: 1 câu Python dựng, 1 câu lệch dòng, 1 câu lời thoại ở doan_van, 1 câu có phân tích mở đầu
    can = [lambda r: r["tao_bang"] == "python", lambda r: "lech_dong" in r["co"],
           lambda r: "nguon_loi_thoai_doan_van" in r["co"], lambda r: "mo_dau_phan_tich" in r["co"]]
    giu = set()
    for f in can:
        if any(f(r) for r in dau[:10]):
            giu |= {i for i in range(10) if f(dau[i])}
            continue
        cand = next((r for r in recs if f(r) and r["khuon_goc"] != "trong" and r not in dau[:10]), None)
        if not cand:
            continue
        i = next((i for i in range(10) if i not in giu and dau[i]["cap_do"] == cand["cap_do"]), None)
        if i is None:
            continue
        if cand in dau:
            j = dau.index(cand)
            dau[i], dau[j] = dau[j], dau[i]
        else:
            dau[i] = cand
        giu.add(i)
    seen = {r["sample_id"] for r in dau}
    rows = dau + [r for r in recs if r["sample_id"] not in seen]
    return [{"stt": i + 1, "sample_id": r["sample_id"], "question_id": r["question_id"], "cap_do": r["cap_do"],
             "tao_bang": r["tao_bang"] or "", "lua_chon_tranh": "x" if "lua_chon_tranh" in r["co"] else "",
             "co": " ".join(c for c in r["co"] if c in ("lech_dong", "nguon_loi_thoai_doan_van", "mo_dau_phan_tich", "thieu_phan_tich"))}
            for i, r in enumerate(rows)]


# ---------------- JSON do Python dựng (câu không có phân tích) ----------------
def _T(s):
    return {"vi": s} if s and s.strip() else None


def cau_hoi_goi_y(norm):
    g = ((norm.get("nghe") or {}).get("goi_y_cau_hoi")) or {}
    ja = g.get("ja")
    if not ja:
        q = (norm["de"].get("cau_hoi") or "").strip().lstrip("？?").strip()
        ja = q if q and NH.JA_CHAR_RE.search(q) else None
    return ja, g.get("vi")


def python_json(norm):
    t, de = norm["nghe"], norm["de"]
    dap = de["dap_an_so"] if isinstance(de["dap_an_so"], int) else None
    ov = t.get("ds_lua_chon_vi") or {}
    tranh = "lua_chon_tranh" in norm["co"]
    qja, qvi = cau_hoi_goi_y(norm)
    opts = [{"index": i, "option_ja": de["lua_chon"][i - 1], "reading": None,
             "meaning": None if tranh else _T(ov.get(str(i))), "is_match": i == dap, "quotes": [], "analysis": None} for i in range(1, 5)]
    return {"schema": SCHEMA_ID, "question_id": norm["question_id"], "cau_con": norm["cau_con"],
            "full_translation": t["full_translation"], "summary": None,
            "question": {"ja": qja, "meaning": _T(qvi)}, "options": opts, "key_info": None,
            "correct": {"index": dap or 1, "option_ja": de["lua_chon"][(dap or 1) - 1], "full_sentence": None},
            "reference_raw": None}


THU_TU_KHOA = ["schema", "question_id", "cau_con", "full_translation", "summary", "question", "options", "key_info", "correct", "reference_raw"]


def bo_sung(doc, norm):
    """Hook claude_tao.gd1_nhan: Python điền full_translation (khi ghép được), key_info = null; sắp khóa theo schema."""
    if "lech_dong" not in norm["co"]:
        doc["full_translation"] = (norm.get("nghe") or {}).get("full_translation")
    doc["key_info"] = None
    doc.setdefault("reference_raw", None)
    return {k: doc.get(k) for k in THU_TU_KHOA}


def bo_truong_python(doc):
    """Hook claude_tao.gd1_nhan (trước khi so schema api): bỏ các trường Python điền (key_info, reference_raw) – để chạy lại --nhan
    trên bản đã được bo_sung không báo lỗi schema. full_translation giữ (schema api cho phép; bo_sung ghi đè khi không lệch dòng)."""
    if isinstance(doc, dict):
        for k in ("key_info", "reference_raw"):
            doc.pop(k, None)
    return doc


def kiem_them(doc, norm):
    """Hook claude_tao.gd1_nhan: lỗi riêng ngay khi nhận bản tác tử TẠO."""
    loi = []
    if "lech_dong" in norm["co"] and not doc.get("full_translation"):
        loi.append("câu lệch dòng (lech_dong) – tác tử TẠO phải ghi full_translation")
    return loi


# ---------------- nhãn bỏ khi đo độ phủ chữ tiếng Việt ----------------
LABELS = [r"→\s*(?:ĐÚNG|SAI)\s*[.。]?", r"(?im)^\s*-?\s*nghĩa\s*[:：]", r"(?im)^\s*[（(]\s*dịch\s*[:：]", r"#{3,}"]


def strip_labels(text):
    for pat in LABELS:
        text = re.sub(pat, " ", text)
    return text


def _v(o):
    return (o or {}).get("vi") if isinstance(o, dict) else None


def _cover(src_text, out_text):
    s, o = collections.Counter(vi_words(strip_labels(src_text or ""))), collections.Counter(vi_words(out_text or ""))
    if not s:
        return 1.0, []
    return sum((s & o).values()) / sum(s.values()), [w for w, _ in (s - o).most_common(8)]


def opt_text(o):
    return "\n".join(x for x in [_v(o.get("meaning"))] + [_v(q.get("meaning")) for q in o.get("quotes") or []] + [_v(o.get("analysis"))] if x)


# ---------------- kiểm tra chung (bọc check_vi) ----------------
def run_check_vi(doc, norm, cfg_, schema):
    from pipeline_chung.checks_chung import check_vi
    q = (doc.get("question") or {}).get("ja") or ""
    marks = list(norm["marks_src"]) + mark_segments(q)        # question.ja = bản sao dòng lời thoại
    return check_vi(doc, schema, norm["src_text"], norm["src_vi_text"], norm, cfg_["kiem_tra"], strip_labels,
                    marks_src=marks, furi_src_text=norm["src_text_furi"], furi_skip=FURI_SKIP)


# ---------------- kiểm tra riêng GĐ1: K1–K12 ----------------
def check_k(doc, norm, policy=None):
    loi, cb = [], []
    de, t = norm["de"], norm.get("nghe") or {}
    dap = de["dap_an_so"] if isinstance(de["dap_an_so"], int) else None
    opts = doc.get("options") or []
    tranh = "lua_chon_tranh" in norm["co"]
    goi_y = {g["so"]: g for g in norm.get("goi_y_khoi") or []}
    # K1 – 4 lựa chọn, option_ja đúng đề
    if [o.get("index") for o in opts] != [1, 2, 3, 4]:
        loi.append(f"K1: options phải có đủ 4 lựa chọn theo thứ tự 1–4 (đang có {[o.get('index') for o in opts]})")
    for o in opts:
        i = o.get("index")
        if not isinstance(i, int) or not 1 <= i <= 4:
            continue
        if (o.get("option_ja") or "") != de["lua_chon"][i - 1]:
            loi.append(f"K1: lựa chọn {i}: option_ja '{o.get('option_ja')}' phải chép đúng lựa chọn của đề '{de['lua_chon'][i - 1]}'")
        if o.get("reading") is not None:
            loi.append(f"K1: lựa chọn {i}: reading phải null")
        # K2 – is_match theo kết luận của khối
        g = goi_y.get(i)
        mong = (g["ket_luan"] == "ĐÚNG") if (g and g.get("ket_luan")) else (i == dap)
        if o.get("is_match") is not mong:
            loi.append(f"K2: lựa chọn {i}: is_match phải là {mong} (" + (f"khối {i}: → {g['ket_luan']}" if g and g.get("ket_luan") else "không có kết luận → theo đáp án") + ")")
        # K7 – nghĩa lựa chọn
        if tranh and o.get("meaning") is not None:
            cb.append(f"K7: lựa chọn {i} là tranh – meaning nên là null")
        # K6 – đủ chữ từng khối (K9 = trung thành)
        if g:
            cv, miss = _cover(_vi_cua_khoi(g), opt_text(o))
            if cv < 0.97:
                loi.append(f"K9: lựa chọn {i}: thiếu chữ so với khối {i} của lời giải: {miss}")
            if g["trich"] and not o.get("quotes") and not any("「" in (_v(o.get("analysis")) or "") for _ in [0]):
                cb.append(f"K5: lựa chọn {i}: lời giải có {len(g['trich'])} câu trích 「…」(dịch) nhưng quotes rỗng")
        elif t.get("khoi") and o.get("analysis") is not None:
            cb.append(f"K6: lựa chọn {i}: lời giải không có khối {i} nhưng analysis khác null")
        # K-TD – câu trích có trong lời thoại
        ja_all = "\n".join(x["text"] for x in t.get("loi_thoai_ja", []) + t.get("phu_ja", []))
        for q in o.get("quotes") or []:
            if ja_all and not NH.trong_loi_thoai(q.get("ja"), ja_all):
                cb.append(f"K-TD: lựa chọn {i}: câu trích không có nguyên văn trong lời thoại: '{(q.get('ja') or '')[:50]}' (xem quy tắc trich_dan)")
    # K3 – correct
    c = doc.get("correct") or {}
    if dap and c.get("index") != dap:
        loi.append(f"K3: correct.index = {c.get('index')} khác dap_an_so = {dap}")
    ci = c.get("index")
    if isinstance(ci, int) and 1 <= ci <= len(opts) and c.get("option_ja") != opts[ci - 1].get("option_ja"):
        loi.append(f"K3: correct.option_ja phải giống hệt options[{ci - 1}].option_ja")
    if c.get("full_sentence") is not None:
        loi.append("K3: correct.full_sentence phải null (dạng 16)")
    # K4 – kết luận ↔ đáp án
    dung = [o.get("index") for o in opts if o.get("is_match") is True]
    if dap and (len(dung) != 1 or dung[0] != dap):
        cb.append(f"K4: lời giải kết luận ĐÚNG ở {dung or 'không lựa chọn nào'} – đáp án của đề là {dap} → soát (nhóm dap_an)")
    # K8 / K9 – full_translation trung thành với lời thoại / bản dịch
    ft = doc.get("full_translation")
    ja_src = t.get("loi_thoai_ja", []) + t.get("phu_ja", [])
    vi_src = t.get("ban_dich_vi", []) + t.get("phu_vi", [])
    if not ja_src and not vi_src:
        if ft is not None:
            loi.append("K8: lời giải không có lời thoại / bản dịch – full_translation phải null")
    elif not ft:
        loi.append("K8: full_translation trống nhưng lời giải có lời thoại / bản dịch")
    else:
        lines = [ln for g_ in ft for ln in (g_.get("lines") or [])]
        doc_ja = [(ln.get("speaker"), ln.get("ja")) for ln in lines if ln.get("ja") is not None]
        if ja_src:
            a = [NH._k(x["text"]) for x in ja_src]
            b = [NH._k(j) for _, j in doc_ja]
            if a != b:
                k = next((i for i in range(min(len(a), len(b))) if a[i] != b[i]), min(len(a), len(b)))
                loi.append(f"K8: full_translation – dòng tiếng Nhật khác lời thoại gốc (số dòng {len(b)}/{len(a)}; lệch từ dòng {k + 1}: "
                           f"'{(ja_src[k]['text'] if k < len(ja_src) else '')[:30]}')")
            sp = [x["speaker"] for x in ja_src]
            if len(sp) == len(doc_ja) and sp != [s for s, _ in doc_ja]:
                loi.append("K8: full_translation – speaker khác nhãn người nói của lời thoại gốc (giữ nguyên nhãn tiếng Nhật)")
        if vi_src:
            cv, miss = _cover("\n".join(x["text"] for x in vi_src), "\n".join(_v(ln.get("meaning")) or "" for ln in lines))
            if cv < 0.97:
                loi.append(f"K9: full_translation thiếu chữ so với bản dịch gốc: {miss}")
        elif any(ln.get("meaning") is not None for ln in lines):
            cb.append("K9: lời giải không có bản dịch nhưng full_translation có meaning – tác tử TẠO không được tự dịch")
        if "lech_dong" not in norm["co"] and ft != t.get("full_translation"):
            cb.append("K8: full_translation khác bản Python ghép – chỉ hợp lệ khi tác tử KIỂM TRA sửa định dạng (ghi sua_dinh_dang)")
    # K10 – summary = đoạn phân tích mở đầu
    md = t.get("phan_tich_mo_dau")
    sm = doc.get("summary")
    if bool(md) != bool(sm):
        loi.append("K10: summary: lời giải " + ("có" if md else "không có") + " đoạn phân tích mở đầu nhưng summary " + ("null" if not sm else "khác null"))
    elif md:
        txt = "\n".join([_v(x.get("heading")) or "" for x in sm] + [_v(p) or "" for x in sm for p in x.get("points") or []])
        cv, miss = _cover(md, txt)
        if cv < 0.97:
            loi.append(f"K9: summary thiếu chữ so với đoạn phân tích mở đầu: {miss}")
    # K11 – key_info
    if doc.get("key_info") is not None:
        loi.append("K11: key_info phải null (dạng 16 – Python điền)")
    # K12 – câu hỏi
    q = doc.get("question") or {}
    qja, qvi = cau_hoi_goi_y(norm)
    if not q.get("ja"):
        (cb if not qja else loi).append("K12: question.ja trống" + (f" – gợi ý: '{qja}'" if qja else ""))
    else:
        nguon = "\n".join([x["text"] for x in ja_src] + [de.get("cau_hoi") or ""])
        if not NH.trong_loi_thoai(q["ja"], nguon):
            cb.append(f"K-CH: question.ja không có trong lời thoại / cột câu hỏi: '{q['ja'][:40]}'")
        if q.get("meaning") is None and qvi:
            cb.append(f"K12: question.meaning null nhưng bản dịch có dòng câu hỏi: '{qvi[:40]}'")
    loi += TK.kiem_tra(doc, None)
    return loi, cb


# ---------------- gợi ý cho tác tử KIỂM TRA ----------------
_UP = "A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬĐÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ"
_LO = "a-zàáảãạăằắẳẵặâầấẩẫậđèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ"
_HV_WORD = rf"[{_UP}]{{2,}}(?:\s+[{_UP}]{{2,}})*"
HV_SRC_RES = [
    re.compile(r"âm\s*h[áa]n\s*vi[ệe]t[^\n]{0,30}", re.I),
    re.compile(rf"ch[ữu]\s*h[áa]n\s*[\"'「]?[㐀-鿿]?[\"'」]?\s*,?\s*({_HV_WORD})\b"),
    re.compile(rf"[㐀-鿿](?:\s*[（(][^)）\n]{{0,15}}[)）])?\s*[-–—:]\s*({_HV_WORD})\b"),
]
HV_BO_QUA = {"VD", "JLPT", "TV", "OK", "DVD", "CD", "PC", "USB", "NHK", "JR", "II", "III", "IV", "SNS", "IT", "AI", "N1", "N2"}


def han_viet_src(norm):
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


FORMAT_HINT_RES = [
    ("dính câu", re.compile(rf"[{_LO}\)\]\"”'’.。:：][{_UP}][{_LO}]")),
    ("lặp từ", re.compile(rf"(?i)\b([{_LO}]{{2,}})\s+\1\b")),
    ("dấu câu thừa", re.compile(r"[ \t][,.;:](?=\s|$)|,[ \t]*\)|\([ \t]+[,.]")),
]


def format_hints(norm):
    t = "\n".join(x for x in [(norm.get("src_vi_text") or "")] if x)
    out = []
    for name, rx in FORMAT_HINT_RES:
        for m in rx.finditer(t):
            if name == "dính câu" and re.match(r"[A-Za-z]{2}", t[max(0, m.start() - 1):m.start() + 1]) \
                    and re.match(r"[A-Za-z]+\b", t[m.start() + 1:]):
                continue                      # chữ Latin viết liền kiểu PowerPoint / YouTube – không phải dính câu
            out.append(f"{name}: …{t[max(0, m.start() - 15):m.end() + 15].replace(chr(10), '⏎')}…")
    return out[:12]


def sudachi_hints(norm):
    """Dạng 16 không dùng Sudachi; trả gợi ý ghép dòng / câu trích cho tác tử KIỂM TRA."""
    out = []
    if "nguoi_noi_lech" in norm["co"]:
        out.append("GD: ghép dòng khớp số lượng nhưng nhãn người nói hai bên lệch – soát full_translation từng dòng")
    for q in norm.get("trich_ngoai") or []:
        out.append(f"TD: câu trích không có nguyên văn trong lời thoại: '{q[:50]}'")
    return out


def _tok():
    return None


# ---------------- kiểm tra riêng GĐ2 ----------------
def check_d(doc_ko, gloss, lang="ko"):
    from pipeline_chung.dich import key_norm
    loi = []
    fixed = {key_norm(k): v for k, v in gloss["cau_co_dinh"].items()}
    for fp, o in iter_lang_fields(doc_ko):
        k = key_norm(o["vi"])
        if k in fixed and o.get(lang) != fixed[k]:
            loi.append(f"D1: {path_str(fp)}: câu cố định phải dịch là '{fixed[k]}'")
    return loi, []


def is_style_field(path):
    """Văn phong -습니다 chỉ xét phần giải thích (analysis, summary) – nghĩa câu / lời thoại theo câu tiếng Nhật."""
    p = path if isinstance(path, str) else path_str(path)
    return bool(re.search(r"\.analysis$|^\$\.summary", p))


# ---------------- hiển thị cho Excel CTV ----------------
def _t(obj, lang):
    return show((obj or {}).get(lang) or "") if obj else ""


def render_loi_thoai(d, lang):
    out = []
    for gi, g in enumerate(d.get("full_translation") or []):
        if gi:
            out.append(bold("【Khối phụ】" + (f" {g.get('label')}" if g.get("label") else "")))
        for ln in g.get("lines") or []:
            sp = (ln.get("speaker") + "：") if ln.get("speaker") else ""
            if ln.get("ja") is not None:
                out.append(sp + show(ln["ja"]))
                if ln.get("meaning"):
                    out.append("   → " + _t(ln["meaning"], lang))
            else:
                out.append(sp + "(—) " + _t(ln.get("meaning"), lang))
    return "\n".join(out)


def render(d, lang):
    out = [bold("【Lời thoại】"), render_loi_thoai(d, lang) or "(không có)"]
    q = d.get("question") or {}
    out.append(f"{bold('【Câu hỏi】')} {show(q.get('ja') or '')}")
    if q.get("meaning"):
        out.append("   Nghĩa: " + _t(q["meaning"], lang))
    for s in d.get("summary") or []:
        out.append(bold("【Phân tích chung】") + (" " + _t(s.get("heading"), lang) if s.get("heading") else ""))
        out += ["   " + _t(p, lang).replace("\n", "\n   ") for p in s.get("points") or []]
    out.append(bold("【PHÂN TÍCH】"))
    for o in d.get("options") or []:
        out.append(bold(f"{o.get('index')}. ") + show(o.get("option_ja", "")) + (f"  ({_t(o['meaning'], lang)})" if o.get("meaning") else ""))
        for qq in o.get("quotes") or []:
            out.append("   「" + show(qq.get("ja") or "") + "」" + (f" ({_t(qq['meaning'], lang)})" if qq.get("meaning") else ""))
        if o.get("analysis"):
            out.append("   " + _t(o["analysis"], lang).replace("\n", "\n   "))
        out.append("   → " + ("ĐÚNG" if o.get("is_match") else "SAI"))
    c = d.get("correct") or {}
    out.append(bold("【Đáp án】") + f" {c.get('index')}. {show(c.get('option_ja', ''))}")
    out += TK.render(d, lang, show, bold)
    return "\n".join(out)


def loi_thoai_ja_text(norm):
    t = norm.get("nghe") or {}
    return "\n".join(((x["speaker"] + "：") if x["speaker"] else "") + x["text"] for x in t.get("loi_thoai_ja", []) + t.get("phu_ja", []))
