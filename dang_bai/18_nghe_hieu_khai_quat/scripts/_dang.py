"""Phần riêng của dạng 18 – Nghe hiểu khái quát (dựng 2026-10-08, khung hạ tầng chép từ dạng 09; Claude Opus 5.5 Cowork – không GPT).

Mỗi câu = 1 bài nghe (cau_con = 1). Lời thoại Nhật ở transcript_vi (hoặc doan_van) – Python tách thành dòng L1…Ln + câu hỏi + 4 lựa chọn
(scripts/_loi_thoai.py); lời giải = bản dịch VI + câu hỏi VI + '###' + phân tích 4 lựa chọn. Schema reading_listening.v1.
Tác tử TẠO ghép từng dòng L1…Ln với câu dịch Việt, điền options; Python kiểm tra K-LT (lời thoại), K-CH (câu hỏi), K-LC (lựa chọn),
K-DA (đáp án), K-TD (câu trích có trong lời thoại – cảnh báo), K9 (đủ chữ). Các script s0…s3 đều import file này.
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
    os.environ["PIPELINE_DATA"] = _c.get("du_lieu_test", "data/test_18_nghe_hieu_khai_quat.csv")


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
    """Thứ tự chạy --tu/--den: output/thu_tu_chay.csv (do s0_chuan_bi tạo – 100 câu đầu xen kẽ N1–N3) nếu có, không thì theo file dữ liệu."""
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
# ---------------- PHẦN RIÊNG DẠNG 18 – NGHE HIỂU KHÁI QUÁT ----------------
# =====================================================================================================
import _loi_thoai as LT  # noqa: E402

from pipeline_chung.common import JA_RE, VI_DIACRITIC_RE, sha, vi_words  # noqa: E402
from pipeline_chung.normalize import pairs as _pairs  # noqa: E402


def strip_labels(text):
    """src_vi_text đã bỏ nhãn ở s0 (nhãn người nói, Nghĩa:, Phân tích…, dòng dẫn câu trích, Dịch:) – chỉ bỏ thêm '→ ĐÚNG/SAI'."""
    return LT.VERD_RE.sub(" ", text or "")


FLAG_TEXT = {
    "khuon_C": "Lời giải có phân tích 4 lựa chọn nhưng không có dòng '###' (Python tách ở dòng '1.')",
    "khuon_D": "Lời giải CHỈ có bản dịch lời thoại + câu hỏi + 4 lựa chọn tiếng Việt – không phân tích (quotes = [], analysis = null → cờ thieu_noi_dung)",
    "khuon_E": "Lời giải KHÔNG có tiếng Việt (chỉ chép lời thoại Nhật) – mọi meaning = null, không phân tích (→ cờ thieu_noi_dung)",
    "nguon_doan_van": "transcript_vi bị dán nhầm lời giải – lời thoại Nhật lấy từ cột doan_van",
    "khong_loi_thoai": "Không tìm thấy lời thoại tiếng Nhật (transcript_vi / doan_van đều rỗng hoặc là tiếng Việt)",
    "bo_cau_dan_de": "Đầu lời thoại có câu dẫn đề '問題… 問題用紙…' – Python bỏ (không đưa vào JSON)",
    "loi_thoai_khong_cau_hoi": "Lời thoại không chép câu hỏi + 4 lựa chọn ở cuối – lấy câu hỏi / lựa chọn từ cột cau_hoi / lua_chon_i (hoặc lời giải)",
    "lua_chon_khong_so": "4 lựa chọn ở cuối lời thoại không đánh số (Python lấy 4 dòng cuối sau câu hỏi)",
    "sau_lua_chon": "Lời thoại có dòng sau 4 lựa chọn (ghi chú / đáp án) – không đưa vào JSON",
    "lua_chon_lech": "Dòng lựa chọn trong lời giải khác lựa chọn trong lời thoại (option_ja vẫn chép theo LỜI GIẢI)",
    "khong_ban_dich": "Lời giải không có bản dịch lời thoại – mọi full_translation…meaning = null",
    "so_dong_dich_lech": "Số dòng bản dịch Việt ≠ số dòng lời thoại Nhật (gộp / tách lượt) – tác tử TẠO ghép theo nghĩa",
    "cau_hoi_vi_la": "Không tìm thấy dòng câu hỏi tiếng Việt (dòng cuối trước ### kết thúc bằng '?')",
    "nhan_cau_hoi_vi": "Dòng câu hỏi tiếng Việt có nhãn 'Câu hỏi:' (question.meaning không chép nhãn)",
    "tach_lua_chon_la": "Phân tích không tách được đủ 4 khối 'n. …' + 'Nghĩa:' (Python chỉ cảnh báo K-LC – Claude soát kỹ)",
    "thieu_ket_luan": "Có lựa chọn không có '→ ĐÚNG / → SAI' (is_match theo dap_an_so)",
    "nhieu_ket_luan": "Có lựa chọn ghi nhiều '→ ĐÚNG/SAI'",
    "lech_dap_an": "Lựa chọn được ghi '→ ĐÚNG' khác dap_an_so của đề",
    "nhieu_dung": "Lời giải ghi '→ ĐÚNG' cho nhiều lựa chọn",
    "trich_dan_ngoai_loi_thoai": "Có câu trích 「…」 không tìm thấy trong lời thoại (so mờ)",
    "chen_tu_nhat": "Câu tiếng Việt có chen từ tiếng Nhật ngoài 「 」 – bọc ⟪ ⟫",
    "co_mo_dau_phan_tich": "Có đoạn chữ sau ### trước lựa chọn 1 – schema không có chỗ: nối vào đầu analysis của lựa chọn 1",
    "co_furigana": "Có furigana",
    "ruby_hong": "Có ruby hỏng trong bản gốc",
}
CTV_FLAGS = ("khuon_D", "khuon_E", "lua_chon_lech", "lech_dap_an", "nhieu_dung", "trich_dan_ngoai_loi_thoai", "nguon_doan_van",
             "loi_thoai_khong_cau_hoi")
FURI_SKIP = [("correct", "option_ja")]        # correct.option_ja = bản sao options[i].option_ja – không đếm furigana 2 lần
_CO_JA = re.compile(r"[぀-ヿ㐀-鿿]")


def _cot_ja(row, col):
    t = LT.lam_sach(row.get(col), giu_furigana=False)[0].replace("{", "").replace("}", "").strip()
    return t if _CO_JA.search(t) and len(LT._k(t)) >= 2 else None


def trong_loi_thoai(q, lt_text):
    """'khop' (nguyên văn hoặc ≥ 85% ký tự khớp theo thứ tự – lệch chữ Hán / kana, lỗi gõ nhỏ) | 'mot_phan' | 'khong'."""
    import difflib
    a, b = LT._k(q), LT._k(lt_text)
    if not a or a in b:
        return "khop"
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    n = sum(x.size for x in sm.get_matching_blocks())
    if n / len(a) >= 0.85:
        return "khop"
    if len(a) >= 8 and (a[:6] in b or a[-6:] in b or n / len(a) >= 0.5):
        return "mot_phan"
    return "khong"


def loi_thoai_text(norm):
    lt = norm.get("loi_thoai") or {}
    return "\n".join([d["ja"] for d in lt.get("dong", [])] + [lt.get("cau_hoi") or ""] + list(lt.get("lua_chon") or []))


def chuan_bi_mau(row):
    """Một dòng CSV → bản chuẩn hóa output/samples/norm/<id>.json (s0)."""
    sid = sid_of(row)
    g = (row.get("giai_thich_vi") or "").strip()
    dap = int(row["dap_an_so"]) if str(row.get("dap_an_so", "")).isdigit() else row.get("dap_an_so")
    lt = LT.tach_loi_thoai(row)
    lg = LT.tach_loi_giai(g)
    co, gc = [], []
    # 2026-10-11 (lô 247): dòng thuần tiếng Nhật trong khối bản dịch (lời giải chép xen Nhật–Việt, hoặc viết lại bằng tiếng Nhật)
    # không phải bản dịch → bỏ khỏi bản dịch và khỏi văn bản so furigana / tiếng Nhật
    def _dong_nhat(x):
        y = re.sub(r"《[^》]*》|｜", "", x)
        n_ja = len(re.findall(r"[\u3040-\u30ff\u4e00-\u9fff]", y))
        n_la = len(re.findall(r"[A-Za-zÀ-ỹ]", y))
        return not LT._vi(x) and n_ja > 0 and n_la < 0.2 * (n_ja + n_la)
    _ja_dich = [x for x in lg["dich"] if _dong_nhat(x)]
    text_kt = lg["text"]
    if _ja_dich:
        lg["dich"] = [x for x in lg["dich"] if x not in _ja_dich]
        _bo = set(_ja_dich)
        text_kt = "\n".join(l for l in lg["text"].split("\n") if l not in _bo)
        co.append("dich_dong_nhat")
        gc.append(f"[Bản gốc VI] Khối bản dịch có {len(_ja_dich)} dòng tiếng Nhật (chép lại / viết lại lời thoại) – không tính là bản dịch")
    # ---- câu hỏi + 4 lựa chọn tiếng Nhật
    cau_hoi, nguon_ch = lt["cau_hoi"], "loi_thoai"
    if not cau_hoi:
        cau_hoi, nguon_ch = _cot_ja(row, "cau_hoi"), "cot_cau_hoi"
        if cau_hoi:
            co.append("loi_thoai_khong_cau_hoi")
    if not cau_hoi:
        nguon_ch = None
    khoi = [b for b in lg["khoi"] if b["so"]]
    lua_chon, nguon_lc = lt["lua_chon"], "loi_thoai"
    if not lua_chon:
        cot = [_cot_ja(row, f"lua_chon_{i}") for i in range(1, 5)]
        if all(cot):
            lua_chon, nguon_lc = cot, "cot_lua_chon"
        elif len(khoi) == 4:
            lua_chon, nguon_lc = [FURI_RE.sub(lambda m: m.group(1), b["lua_chon"]) for b in khoi], "loi_giai"
        else:
            lua_chon, nguon_lc = [None] * 4, None
        if "loi_thoai_khong_cau_hoi" not in co:
            co.append("loi_thoai_khong_cau_hoi")
    if lt["kieu"] == "khong_so":
        co.append("lua_chon_khong_so")
    if lt["sau_lua_chon"]:
        co.append("sau_lua_chon")
        gc.append("[Bản gốc VI] Lời thoại có dòng sau 4 lựa chọn (không đưa vào JSON): " + " / ".join(lt["sau_lua_chon"])[:200])
    if lt["bo_dau"]:
        co.append("bo_cau_dan_de")
    if lt["nguon"] == "doan_van":
        co.append("nguon_doan_van")
        gc.append("[Bản gốc VI] Cột transcript_vi chứa lời giải (dán nhầm) – lời thoại Nhật lấy từ cột doan_van")
    if not lt["nguon"]:
        co.append("khong_loi_thoai")
        gc.append("[Bản gốc VI] Không có lời thoại tiếng Nhật")
    # ---- khuôn lời giải
    kh = lg["khuon"]
    if kh in ("C", "D", "E"):
        co.append("khuon_" + kh)
    if kh in ("D", "E"):
        gc.append("[Bản gốc VI] Lời giải " + ("chỉ có bản dịch + câu hỏi + lựa chọn tiếng Việt, không phân tích 4 lựa chọn" if kh == "D"
                                            else "không có tiếng Việt (chỉ chép lời thoại Nhật)"))
    if kh in ("A", "C", "D"):
        if not lg["dich"]:
            co.append("khong_ban_dich")
        elif len(lg["dich"]) != len(lt["dong"]):
            co.append("so_dong_dich_lech")
        if not lg["cau_hoi_vi"]:
            co.append("cau_hoi_vi_la")
        if lg["dong_nhan_cau_hoi"]:
            co.append("nhan_cau_hoi_vi")
    if kh in ("A", "C"):
        if len(khoi) != 4 or any(b["nghia"] is None for b in khoi) or any(LT._vi(b["lua_chon"]) for b in khoi):
            co.append("tach_lua_chon_la")
        if any(not b["ket_luan"] for b in khoi):
            co.append("thieu_ket_luan")
        if any(len(b["ket_luan"]) > 1 for b in khoi):
            co.append("nhieu_ket_luan")
        dung = [b["so"] for b in khoi if b["ket_luan"] and b["ket_luan"][-1] == "ĐÚNG"]
        if len(dung) > 1:
            co.append("nhieu_dung")
        if dung and isinstance(dap, int) and dap not in dung:
            co.append("lech_dap_an")
            gc.append(f"[Bản gốc VI] Lời giải ghi '→ ĐÚNG' ở lựa chọn {dung} nhưng dap_an_so = {dap}")
        if lt["lua_chon"]:
            lech = [b["so"] for b in khoi if 1 <= b["so"] <= 4 and LT._k(b["lua_chon"]) != LT._k(lt["lua_chon"][b["so"] - 1])]
            if lech:
                co.append("lua_chon_lech")
                gc.append("[Bản gốc VI] Lựa chọn trong lời giải khác lời thoại: " + "; ".join(
                    f"{i}. '{FURI_RE.sub(lambda m: m.group(1), khoi[i - 1]['lua_chon'])}' ↔ '{lt['lua_chon'][i - 1]}'" for i in lech if i <= len(khoi)))
        if any(b["so"] == 0 and b["dong"] for b in lg["khoi"]):
            co.append("co_mo_dau_phan_tich")
    # ---- câu trích có trong lời thoại không
    ltt = "\n".join([d["ja"] for d in lt["dong"]])
    ngoai = [q for b in khoi for q in b["trich"] if trong_loi_thoai(q, ltt) == "khong"]
    if ngoai:
        co.append("trich_dan_ngoai_loi_thoai")
    # ---- chữ Nhật chen trong câu Việt
    vi_lines = lg["dich"] + ([lg["cau_hoi_vi"]] if lg["cau_hoi_vi"] else []) + [l for b in khoi for l in b["dong"] if LT._vi(l)]
    if any(JA_RE.search(strip_marks(LT.QUOTE_RE.sub("", l))) for l in vi_lines if LT._vi(l)):
        co.append("chen_tu_nhat")
    if _pairs(lg["text"]):
        co.append("co_furigana")
    if lg["broken"]:
        co.append("ruby_hong")
        gc.append(f"[Bản gốc VI] Có {len(lg['broken'])} thẻ ruby hỏng")
    # ---- văn bản nguồn cho kiểm tra chung
    dong_ja = "\n".join(d["ja"] for d in lt["dong"])
    if kh in ("A", "C", "D"):
        src_text = "\n".join(x for x in (text_kt, dong_ja, cau_hoi or "") if x)
        furi = text_kt
    else:
        src_text = "\n".join(x for x in (dong_ja, cau_hoi or "") if x)
        furi = ""
    if kh in ("D", "E"):
        src_text += "\n" + "\n".join(x for x in lua_chon if x)
    vi_src = []
    if kh in ("A", "C", "D"):
        vi_src.append(LT.vi_dong_dich(lg["dich"]))
        if lg["cau_hoi_vi"]:
            vi_src.append(lg["cau_hoi_vi"])
        if kh == "D" and lg["lua_chon_vi"]:
            vi_src += lg["lua_chon_vi"]
        vi_src += [LT.vi_lua_chon(b) for b in lg["khoi"] if b["so"] or b["dong"]]
    hash_goc = sha(g + "|" + (row.get("transcript_vi") or "") + "|" + (row.get("doan_van") or "") + "|" + str(row.get("dap_an_so")))
    return {"sample_id": sid, "question_id": int(row["question_id"]), "cau_con": int(row["cau_con"]), "cap_do": row["cap_do"],
            "hash_goc": hash_goc, "khuon_goc": kh if g else "trong",
            "de": {"cau_hoi": cau_hoi, "lua_chon": lua_chon, "dap_an_so": dap, "nguon_cau_hoi": nguon_ch, "nguon_lua_chon": nguon_lc},
            "loi_thoai": lt, "doan_van": LT.hien_thi_loi_thoai(lt), "nhan_doan_van": "LỜI THOẠI TIẾNG NHẬT (Python tách: Lk [người nói] …)",
            "dau_vao": lg["text"] or None, "src_text": src_text, "src_vi_text": "\n".join(vi_src), "src_text_furi": furi, "marks_src": [],
            "phan": {"tham_khao": None, "dich": lg["dich"], "cau_hoi_vi": lg["cau_hoi_vi"], "lua_chon_vi": lg["lua_chon_vi"],
                     "khoi": khoi, "mo_dau": "\n".join(l for b in lg["khoi"] if b["so"] == 0 for l in b["dong"]) or None,
                     "trich_ngoai": ngoai},
            "co": sorted(set(co)), "ghi_chu_ban_goc": gc, "ruby_hong": lg["broken"], "danh_dau_rac": []}


def mong_doi_lua_chon(norm, i):
    """(option_ja mong đợi, nguồn) cho lựa chọn i (1–4)."""
    kh, khoi = norm["khuon_goc"], (norm.get("phan") or {}).get("khoi") or []
    b = next((x for x in khoi if x["so"] == i), None)
    if kh in ("A", "C") and b and b["lua_chon"]:
        return b["lua_chon"], "lời giải"
    lc = (norm["de"].get("lua_chon") or [None] * 4)[i - 1]
    return lc, "lời thoại / đề"


def tao_thu_tu(recs, cfg):
    """100 câu đầu xen kẽ N1/N2/N3 (ngẫu nhiên theo seed, bỏ câu không có lời giải); sau đó các câu còn lại theo file dữ liệu."""
    import random
    tc = cfg.get("thu_tu_chay") or {}
    rng = random.Random(tc.get("seed", 2026))
    cap = tc.get("cap_do", ["N1", "N2", "N3"])
    n = tc.get("dau_tien", 100)
    pools = {}
    for k in cap:
        p = [r for r in recs if r["cap_do"] == k and r["khuon_goc"] != "trong"]
        rng.shuffle(p)
        pools[k] = p
    dau = []
    while len(dau) < n and any(pools.values()):
        for k in cap:
            if pools[k] and len(dau) < n:
                dau.append(pools[k].pop(0))
    seen = {r["sample_id"] for r in dau}
    rows = dau + [r for r in recs if r["sample_id"] not in seen]
    return [{"stt": i + 1, "sample_id": r["sample_id"], "question_id": r["question_id"], "cap_do": r["cap_do"],
             "khuon": r["khuon_goc"]} for i, r in enumerate(rows)]


# ---------------- kiểm tra riêng giai đoạn 1 ----------------
def _v(o):
    return (o or {}).get("vi") if isinstance(o, dict) else None


def _cover(src_text, out_text):
    s, o = collections.Counter(vi_words(src_text or "")), collections.Counter(vi_words(out_text or ""))
    if not s:
        return 1.0, []
    return sum((s & o).values()) / sum(s.values()), [w for w, _ in (s - o).most_common(8)]


def opt_text(o):
    """Chữ của một lựa chọn trong JSON (kể cả option_ja / câu trích – chữ Latin như 'Wi-Fi' nằm trong câu Nhật)."""
    q = [_v(x.get("meaning")) for x in o.get("quotes") or []] + [x.get("ja") for x in o.get("quotes") or []]
    return "\n".join(x for x in [o.get("option_ja"), _v(o.get("meaning"))] + q + [_v(o.get("analysis"))] if x)


def check_k(doc, norm, policy):
    loi, cb = [], []
    de, phan, lt = norm["de"], norm.get("phan") or {}, norm.get("loi_thoai") or {}
    kh, co = norm["khuon_goc"], set(norm.get("co") or [])
    dap = de.get("dap_an_so")
    # K-LT – lời thoại
    ft = doc.get("full_translation")
    dong = lt.get("dong") or []
    if not isinstance(ft, list) or len(ft) != 1 or (ft[0] or {}).get("label") is not None:
        loi.append("K-LT1: full_translation phải là đúng 1 nhóm {label: null, lines: […]}")
    else:
        lines = ft[0].get("lines") or []
        if len(lines) != len(dong):
            loi.append(f"K-LT1: full_translation có {len(lines)} dòng ≠ {len(dong)} dòng lời thoại (L1…L{len(dong)}) – mỗi dòng Lk một phần tử, đúng thứ tự")
        else:
            for k, (a, b) in enumerate(zip(lines, dong), 1):
                if LT._k(a.get("ja")) != LT._k(b["ja"]):
                    loi.append(f"K-LT1: L{k}: ja khác lời thoại '{b['ja'][:50]}'")
                if (a.get("speaker") or None) != (b["speaker"] or None):
                    loi.append(f"K-LT1: L{k}: speaker = {a.get('speaker')!r} ≠ {b['speaker']!r} (chép đúng ký hiệu Python tách)")
        n_null = sum(1 for a in lines if not a.get("meaning"))
        if kh in ("E",) or "khong_ban_dich" in co:
            if n_null != len(lines):
                loi.append("K-LT2: lời giải không có bản dịch lời thoại – mọi meaning phải null (không tự dịch)")
        elif lines and n_null:
            ty = n_null / len(lines)
            msg = f"K-LT2: {n_null}/{len(lines)} dòng lời thoại meaning = null"
            nguong = (cfg().get("kiem_tra") or {}).get("dong_thoai_khong_dich_toi_da", 0.3)
            cb.append(msg + (" – vượt ngưỡng, xem có nên gắn cờ thieu_noi_dung" if ty > nguong else ""))
        dv = phan.get("dich") or []
        if dv:
            cv, miss = _cover(LT.vi_dong_dich(dv), "\n".join(_v(a.get("meaning")) or "" for a in lines))
            if cv < 0.97:
                loi.append(f"K9: bản dịch lời thoại thiếu chữ so với lời giải: {miss}")
    if doc.get("summary") is not None or doc.get("key_info") is not None:
        loi.append("K-NULL: summary và key_info phải là null (dạng 18)")
    # K-CH – câu hỏi
    q = doc.get("question") or {}
    if de.get("cau_hoi"):
        if LT._k(q.get("ja")) != LT._k(de["cau_hoi"]):
            loi.append(f"K-CH: question.ja khác câu hỏi trong {'lời thoại' if de.get('nguon_cau_hoi') == 'loi_thoai' else 'cột cau_hoi'}: '{de['cau_hoi']}'")
    elif q.get("ja"):
        cb.append("K-CH: không có câu hỏi tiếng Nhật trong dữ liệu nhưng question.ja khác null – xem lấy từ đâu")
    qv = phan.get("cau_hoi_vi")
    if (qv is None) != (q.get("meaning") is None):
        (loi if kh in ("A", "C", "D") and qv else cb).append(
            "K-CH: question.meaning phải null khi và chỉ khi lời giải không có dòng câu hỏi tiếng Việt" + (f" ('{qv[:60]}')" if qv else ""))
    elif qv:
        cv, miss = _cover(qv, _v(q.get("meaning")))
        if cv < 0.97:
            loi.append(f"K9: question.meaning thiếu chữ: {miss}")
    # K-LC – lựa chọn
    opts = doc.get("options") or []
    if [o.get("index") for o in opts] != [1, 2, 3, 4]:
        loi.append(f"K-LC: options phải có đủ 4 lựa chọn index 1–4 theo thứ tự (đang có {[o.get('index') for o in opts]})")
    khoi = {b["so"]: b for b in phan.get("khoi") or []}
    la = "tach_lua_chon_la" in co
    for o in opts:
        i = o.get("index")
        if not isinstance(i, int) or not 1 <= i <= 4:
            continue
        mong, nguon = mong_doi_lua_chon(norm, i)
        if mong and LT._k(o.get("option_ja")) != LT._k(mong):
            (cb if la else loi).append(f"K-LC: lựa chọn {i}: option_ja '{o.get('option_ja')}' khác dòng lựa chọn của {nguon} '{mong}'")
        if o.get("reading") is not None:
            loi.append(f"K-LC: lựa chọn {i}: reading phải null")
        b = khoi.get(i)
        if kh in ("A", "C"):
            if b is None:
                cb.append(f"K-LC: lựa chọn {i}: Python không tách được khối phân tích – soát tay")
                continue
            if (b["nghia"] is None) != (o.get("meaning") is None) and not la:
                loi.append(f"K-LC: lựa chọn {i}: meaning phải null khi và chỉ khi khối không có dòng 'Nghĩa:'")
            kl = b["ket_luan"][-1] if b["ket_luan"] else None
            if kl and o.get("is_match") is not (kl == "ĐÚNG"):
                loi.append(f"K-DA: lựa chọn {i}: is_match phải là {kl == 'ĐÚNG'} (lời giải: → {kl})")
            if len(b["ket_luan"]) > 1:
                cb.append(f"K-DA: lựa chọn {i}: lời giải ghi {len(b['ket_luan'])} lần → ĐÚNG/SAI ({b['ket_luan']}) – is_match theo kết luận cuối")
            cv, miss = _cover(LT.vi_lua_chon(b), opt_text(o))
            if cv < 0.97:
                loi.append(f"K9: lựa chọn {i}: thiếu chữ so với lời giải: {miss}")
            khoi_txt = "\n".join(b["dong"])
            for j, x in enumerate(o.get("quotes") or []):
                if LT._k(x.get("ja")) not in LT._k(khoi_txt):
                    loi.append(f"K-QT: lựa chọn {i}: quotes[{j}].ja '{(x.get('ja') or '')[:40]}' không có trong khối phân tích của lựa chọn này")
                kq = trong_loi_thoai(x.get("ja") or "", loi_thoai_text(norm))
                if kq != "khop":
                    cb.append(f"K-TD: lựa chọn {i}: câu trích '{(x.get('ja') or '')[:40]}' {'chỉ khớp một phần' if kq == 'mot_phan' else 'không có'} trong lời thoại")
        else:
            if o.get("quotes") or o.get("analysis") is not None:
                loi.append(f"K-LC: lựa chọn {i}: khuôn {kh} không có phân tích – quotes = [], analysis = null")
            mv = (phan.get("lua_chon_vi") or [None] * 4)[i - 1] if kh == "D" else None
            if (mv is None) != (o.get("meaning") is None):
                loi.append(f"K-LC: lựa chọn {i}: meaning " + (f"phải chép dòng lựa chọn tiếng Việt '{mv}'" if mv else "phải null (lời giải không có nghĩa lựa chọn)"))
            elif mv:
                cv, miss = _cover(mv, _v(o.get("meaning")))
                if cv < 0.97:
                    loi.append(f"K9: lựa chọn {i}: meaning thiếu chữ: {miss}")
            if isinstance(dap, int) and o.get("is_match") is not (i == dap):
                loi.append(f"K-DA: lựa chọn {i}: khuôn {kh} không có kết luận – is_match = (index == dap_an_so = {dap})")
    # K-NQ – cùng câu trích, nghĩa khác nhau
    seen = {}
    for o in opts:
        for x in o.get("quotes") or []:
            k, m = LT._k(x.get("ja")), _v(x.get("meaning"))
            if k and m:
                if k in seen and seen[k] != m:
                    cb.append(f"K-NQ: câu trích '{(x.get('ja') or '')[:30]}' có 2 cách dịch khác nhau giữa các lựa chọn (theo lời giải – chỉ lưu ý)")
                seen.setdefault(k, m)
    # K-DA – đáp án
    c = doc.get("correct") or {}
    if str(c.get("index")) != str(dap):
        loi.append(f"K-DA: correct.index = {c.get('index')} khác dap_an_so = {dap}")
    di = c.get("index")
    if isinstance(di, int) and 1 <= di <= len(opts) and c.get("option_ja") != opts[di - 1].get("option_ja"):
        loi.append(f"K-DA: correct.option_ja phải giống hệt options[{di - 1}].option_ja")
    if c.get("full_sentence") is not None:
        loi.append("K-DA: correct.full_sentence phải null (dạng 18)")
    dung = [o.get("index") for o in opts if o.get("is_match") is True]
    if dung != [dap]:
        (cb if co & {"lech_dap_an", "nhieu_dung", "thieu_ket_luan"} else loi).append(
            f"K-DA: lựa chọn is_match = true là {dung}, phải đúng 1 và trùng dap_an_so = {dap}")
    loi += TK.kiem_tra(doc, None)
    return loi, cb


# ---------------- kiểm tra riêng giai đoạn 2 ----------------
def check_d(doc_ko, gloss, lang="ko"):
    from pipeline_chung.dich import key_norm
    loi, cb = [], []
    fixed = {key_norm(k): v for k, v in gloss["cau_co_dinh"].items()}
    for fp, o in iter_lang_fields(doc_ko):
        k = key_norm(o["vi"])
        if k in fixed and o.get(lang) != fixed[k]:
            loi.append(f"D1: {path_str(fp)}: câu cố định phải dịch là '{fixed[k]}'")
    return loi, cb


def is_style_field(path):
    """Chỉ phần phân tích (analysis – dịch từ tiếng Việt) xét văn phong -습니다; lời thoại / câu hỏi / lựa chọn / câu trích theo câu Nhật."""
    p = path if isinstance(path, str) else path_str(path)
    return bool(re.search(r"\.analysis(\.|$)", p))


# ---------------- hiển thị cho Excel CTV ----------------
def _t(obj, lang):
    return show((obj or {}).get(lang) or "") if obj else ""


def render(d, lang):
    out = [bold("【LỜI THOẠI】")]
    for g in d.get("full_translation") or []:
        if g.get("label"):
            out.append(bold(f"[{g['label']}]"))
        for ln in g.get("lines") or []:
            out.append((f"{ln['speaker']}：" if ln.get("speaker") else "") + show(ln.get("ja") or ""))
            if ln.get("meaning"):
                out.append("   → " + _t(ln["meaning"], lang))
    q = d.get("question") or {}
    out.append(f"{bold('【Câu hỏi】')} {show(q.get('ja') or '')}")
    if q.get("meaning"):
        out.append(f"   Nghĩa: {_t(q['meaning'], lang)}")
    out.append(bold("【PHÂN TÍCH】"))
    for o in d.get("options") or []:
        out.append(bold(f"{o.get('index')}. ") + show(o.get("option_ja") or ""))
        if o.get("meaning"):
            out.append("   Nghĩa: " + _t(o["meaning"], lang))
        for x in o.get("quotes") or []:
            out.append("   Trích: 「" + show(x.get("ja") or "") + "」" + (f" ({_t(x['meaning'], lang)})" if x.get("meaning") else ""))
        if o.get("analysis"):
            out.append("   " + _t(o["analysis"], lang).replace("\n", "\n   "))
        out.append("   → " + ("ĐÚNG" if o.get("is_match") else "SAI"))
    c = d.get("correct") or {}
    out.append(f"{bold('【ĐÁP ÁN】')} {c.get('index')}. {show(c.get('option_ja') or '')}")
    out += TK.render(d, lang, show, bold)
    return "\n".join(out)


# ---------------- Cách chia v2: âm Hán Việt, gợi ý định dạng (chép từ dạng 09, chạy trên lời giải gốc) ----------------
_UP = "A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬĐÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ"
_HV_WORD = rf"[{_UP}]{{2,}}(?:\s+[{_UP}]{{2,}})*"
HV_SRC_RES = [
    re.compile(r"âm\s*h[áa]n\s*vi[ệe]t[^\n]{0,30}", re.I),
    re.compile(rf"ch[ữu]\s*h[áa]n\s*[\"'「]?[㐀-鿿]?[\"'」]?\s*,?\s*({_HV_WORD})\b"),
    re.compile(rf"[㐀-鿿](?:\s*[（(][^)）\n]{{0,15}}[)）])?\s*[-–—:]\s*({_HV_WORD})\b"),
    re.compile(rf"\bch[ữu]\s+({_HV_WORD})\b"),
]
HV_BO_QUA = {"VD", "JLPT", "TV", "OK", "DVD", "CD", "PC", "USB", "NHK", "JR", "II", "III", "IV", "SNS", "IT", "AI", "N1", "N2", "N3",
             "NGO", "CEO", "SAI", "ĐÚNG"}


def han_viet_src(norm):
    t = norm.get("dau_vao") or ""
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


_LO = "a-zàáảãạăằắẳẵặâầấẩẫậđèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ"
FORMAT_HINT_RES = [
    ("dính câu", re.compile(rf"[{_LO}\)\]\"”'’.。:：][{_UP}][{_LO}]")),
    ("lặp từ", re.compile(rf"(?i)\b([{_LO}]{{2,}})\s+\1\b")),
    ("dấu câu thừa", re.compile(r"[ \t][,.;:](?=\s|$)|,[ \t]*\)|\([ \t]+[,.]")),
]


def format_hints(norm):
    t = norm.get("dau_vao") or ""
    out = []
    for name, rx in FORMAT_HINT_RES:
        for m in rx.finditer(t):
            out.append(f"{name}: …{t[max(0, m.start() - 15):m.end() + 15].replace(chr(10), '⏎')}…")
    return out[:12]


def _tok():
    return None          # dạng 18 không dùng SudachiPy


def sudachi_hints(norm):
    return []
