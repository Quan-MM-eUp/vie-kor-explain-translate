"""Phần riêng của dạng 21 – Nghe hiểu tổng hợp (dựng 2026-10-08 theo KE_HOACH_PIPELINE.md đã duyệt).

Schema reading_listening.v1 (+ reference_raw). Lời thoại tiếng Nhật ở cột transcript_vi (tên cột sai); lời giải giai_thich_vi:
  khuôn A  = [bản dịch VI lời thoại] ### [phân tích 1–4: Nghĩa / 「trích」(dịch) / → ĐÚNG|SAI]          (86 câu)
  khuôn B  = [bản dịch VI + đề 2 câu hỏi] ### Thông tin: [đoạn then chốt JA + dịch] – bài 2 câu hỏi N2   (9 câu)
  khuôn C_vi = chỉ bản dịch VI (+ câu hỏi, lựa chọn) · C_ja = chỉ chép lại lời thoại JA · trong = rỗng
Đơn vị chạy = BÀI NGHE (question_id); bài 2 câu hỏi: lời thoại gộp theo question_id, full_translation do câu con 1 giữ,
câu con 2 Python chép. Khuôn C_ja: Python dựng cả JSON (không giao tác tử TẠO). Các script s0…s3 đều import file này.
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
    os.environ["PIPELINE_DATA"] = _c.get("du_lieu_test", "data/21_nghe_hieu_tong_hop.csv")


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
    """Thứ tự chạy --tu/--den: output/thu_tu_chay.csv (do s0_chuan_bi tạo – theo BÀI NGHE, lô 5 bài) nếu có, không thì theo file dữ liệu."""
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



# =====================================================================================================
#                                   PHẦN RIÊNG DẠNG 21
# =====================================================================================================
import collections  # noqa: E402
import copy  # noqa: E402

from pipeline_chung import nghe_hieu as NH  # noqa: E402
from pipeline_chung.common import JA_RE, vi_words  # noqa: E402

KHUON_TAO = ("A", "B", "C_vi")          # tác tử TẠO chuyển JSON
KHUON_PYTHON = ("C_ja",)                # Python dựng cả JSON (lời giải chỉ chép lại lời thoại JA – không có tiếng Việt)
KHUON_THIEU = ("B", "C_vi", "C_ja")     # thiếu phân tích từng lựa chọn → bắt buộc cờ thieu_noi_dung

FLAG_TEXT = {
    "khuon_B": "Khuôn 'Thông tin:' – chỉ có đoạn thoại then chốt (key_info), không phân tích từng lựa chọn → cờ thieu_noi_dung",
    "khuon_C_vi": "Lời giải chỉ có bản dịch lời thoại – không phân tích lựa chọn → cờ thieu_noi_dung",
    "khuon_C_ja": "Lời giải chỉ chép lại lời thoại tiếng Nhật – không có tiếng Việt, không phân tích → Python dựng JSON, cờ thieu_noi_dung",
    "bai_2_cau_hoi": "Bài nghe có 2 câu hỏi (質問1 / 質問2) – lời thoại gộp theo question_id",
    "chep_loi_thoai": "Câu con 2: full_translation do Python chép từ câu con 1 (không tự ghép)",
    "loi_thoai_trong": "Không có lời thoại tiếng Nhật dùng được (cột transcript rỗng / chỉ có câu hỏi / dán nhầm lời giải)",
    "loi_thoai_dan_nham": "Cột transcript chứa phần phân tích (→ ĐÚNG / Nghĩa:) – không dùng làm lời thoại",
    "cach_chu_nhat": "Lời thoại có khoảng trắng chen giữa chữ Nhật – Python đã bỏ",
    "lua_chon_thieu": "Dữ liệu đề thiếu lựa chọn (lua_chon_i rỗng) – cần sửa dữ liệu gốc",
    "nhieu_dung": "Lời giải ghi '→ ĐÚNG' ở nhiều hơn 1 lựa chọn",
    "lech_dap_an": "Lựa chọn '→ ĐÚNG' của lời giải khác dap_an_so",
    "thieu_ket_luan": "Có lựa chọn không có '→ ĐÚNG/SAI' trong lời giải",
    "lua_chon_khac_de": "Dòng lựa chọn trong lời giải viết khác cột lua_chon của đề",
    "co_mo_dau_phan_tich": "Có đoạn chữ trước lựa chọn 1 trong phần phân tích (schema không có chỗ riêng) – đưa vào analysis của lựa chọn 1 theo hướng dẫn",
    "trich_ngoai_loi_thoai": "Có câu trích 「…」 không tìm thấy trong lời thoại (có thể lời giải đã sửa lỗi gõ của lời thoại)",
    "co_furigana": "Lời giải có furigana",
    "ruby_hong": "Lời giải có thẻ ruby hỏng",
    "tham_khao": "Có phần THAM KHẢO – Python chép nguyên văn vào reference_raw",
    "khong_cau_hoi": "Không xác định được câu hỏi tiếng Nhật (question.ja = null nếu lời giải / lời thoại cũng không có)",
}
CTV_FLAGS = ("nhieu_dung", "lech_dap_an", "lua_chon_khac_de", "trich_ngoai_loi_thoai")
FURI_SKIP = [("correct", "option_ja")]          # bản sao option_ja của đáp án – không tính furigana hai lần
MARK = "###"


# ---------------- tách lời giải ----------------
THAM_KHAO_RE = re.compile(r"(?im)^\s*(?:THÔNG TIN THAM KHẢO|NGỮ PHÁP THAM KHẢO|THAM KHẢO)\s*[:：]?\s*$|(?im)^\s*THAM KHẢO\s*[:：]")
OPT_RE = re.compile(r"^\s*([1-4])\s*[\.．]\s*(.*)$")
KL_RE = re.compile(r"→\s*(ĐÚNG|SAI|Đúng|Sai|đúng|sai)")
QUOTE_RE = re.compile(r"「([^「」]*)」")


def ti_le_nhat(line):
    t = strip_marks(line)
    return len("".join(JA_RE.findall(t))) / max(1, len(re.sub(r"\s", "", t)))


def khuon(text):
    if not text.strip():
        return "trong"
    if len(KL_RE.findall(text)) >= 3:
        return "A"
    if re.search(r"(?im)^\s*Thông tin\s*[:：]", text):
        return "B"
    L = [x for x in text.split("\n") if x.strip()]
    ja = sum(1 for x in L if ti_le_nhat(x) > 0.3) / max(1, len(L))
    return "C_ja" if ja > 0.5 else "C_vi"


def tach_tham_khao(text):
    m = THAM_KHAO_RE.search(text)
    if not m:
        return text, None
    return text[:m.start()].rstrip(), text[m.end():].strip()


def phan_tich_A(after):
    """Phần sau ### của khuôn A → (đoạn mở đầu, [khối lựa chọn])."""
    lines = after.split("\n")
    mo, khoi, cur = [], [], None
    for ln in lines:
        m = OPT_RE.match(ln)
        if m and (cur is None or int(m.group(1)) == cur["so"] + 1):
            cur = {"so": int(m.group(1)), "lua_chon": m.group(2).strip(), "dong": []}
            khoi.append(cur)
            continue
        (cur["dong"] if cur else mo).append(ln)
    for k in khoi:
        t = "\n".join(k["dong"])
        kl = re.findall(r"→\s*(ĐÚNG|SAI)(?![a-zà-ỹ])", t) or KL_RE.findall(t)     # ưu tiên kết luận viết HOA ('→ ĐÚNG.')
        k["ket_luan"] = (kl[-1].upper() == "ĐÚNG") if kl else None
        nm = re.search(r"(?im)^\s*Nghĩa\s*[:：]\s*(.+)$", t)
        k["nghia"] = nm.group(1).strip() if nm else None
        k["trich"] = [q for q in QUOTE_RE.findall(t) if JA_RE.search(strip_marks(q)) and len(strip_marks(q)) >= 4]
        k["van_ban"] = t
    return "\n".join(mo).strip(), khoi


def thong_tin_B(after):
    """Khối 'Thông tin:' → {ja: [dòng tiếng Nhật], vi: [dòng tiếng Việt]}."""
    m = re.search(r"(?im)^\s*Thông tin\s*[:：]\s*", after)
    t = after[m.end():] if m else after
    L = [x.strip() for x in t.split("\n") if x.strip()]
    return {"ja": [x for x in L if ti_le_nhat(x) > 0.3], "vi": [x for x in L if ti_le_nhat(x) <= 0.3]}


# ---------------- nhãn cố định của lời giải gốc (bỏ khi đo độ phủ) ----------------
LABELS = [r"(?m)^\s*###\s*$",
          r"(?im)^\s*Phân tích(?: đoạn hội thoại| hội thoại| đoạn văn)?\s*[:：]\s*",
          r"(?im)^\s*Nghĩa\s*[:：]\s*",
          r"(?im)^\s*Thông tin\s*[:：]\s*",
          r"(?im)^\s*Câu(?: hỏi)?\s*\d*\s*[:：]\s*",
          r"→\s*(?:ĐÚNG|SAI)\s*\.?",
          r"(?m)^[^\n:：「」]{1,45}[:：]\s*(?=「)",          # 'Nam nói: 「…」' – nhãn dẫn trích dẫn
          r"(?m)^[^\n:：「」0-9]{1,30}[:：]\s*",             # 'Nam:' – nhãn người nói
          r"(?m)^[^\n:：「」0-9]{1,25}\s?[0-9０-９][:：]\s*",  # 'Người phụ nữ 2:', 'Nam 1:', 'F2:' – nhãn người nói có số (2026-10-08 lô 1)
          r"(?<=[\u3000-\u9fff\uff01-\uff5e])\((?:i|ii|iii)\)",  # (i)/(ii) dính sau dòng tiếng Nhật – không phải chữ Việt
          r"(?m)^\s*[1-4]\s*[\.．]\s*"]


def strip_labels(text):
    for p in LABELS:
        text = re.sub(p, " ", text or "")
    return text


# ---------------- chuẩn bị (s0) ----------------
def _plain(html):
    from pipeline_chung.normalize import normalize_html
    t, _ = normalize_html(NH.furigana_lua_chon(html or ""))
    return t.replace("{", "").replace("}", "").strip()


def chuan_bi_bai(rows):
    """Các dòng CSV của MỘT question_id → danh sách norm (theo cau_con). Dùng ở s0_chuan_bi."""
    from pipeline_chung.common import sha
    from pipeline_chung.normalize import normalize_html, pairs
    rows = sorted(rows, key=lambda r: int(r["cau_con"]))
    lua_chon_all = [_plain(r.get(f"lua_chon_{i}", "")) for r in rows for i in range(1, 5)]
    # lời thoại của bài: lấy bản dài nhất trong các câu con (không dùng bản dán nhầm lời giải)
    cands, dan_nham, cach = [], False, 0
    for r in rows:
        dong, n = NH.loi_thoai_dong(r.get("transcript_vi"))
        if re.search(r"→\s*(?:ĐÚNG|SAI)|(?m)^Nghĩa\s*:", "\n".join(dong)):
            dan_nham = True
            continue
        cands.append((dong, n, r))
    dong, cach, nguon = (max(cands, key=lambda x: len("".join(x[0]))) if cands else ([], 0, None))
    loi_thoai, cau_hoi_cat, dau_cat = NH.cat_loi_thoai(dong, lua_chon_all)
    # câu hỏi bị cắt ở cuối của các câu con KHÁC (câu con 2 của N1 chỉ chứa '質問2 …')
    q_all = list(cau_hoi_cat)
    for r in rows:
        if nguon is not None and r is nguon:
            continue
        d2, _ = NH.loi_thoai_dong(r.get("transcript_vi"))
        if not d2 or len(d2) > 8:
            continue
        _, q2, _ = NH.cat_loi_thoai(d2, lua_chon_all)
        q2 = q2 or [x for x in d2 if NH.Q_LABEL_RE.match(x) and NH.Q_LABEL_RE.sub("", x) != x.strip()][:1]
        q_all += [x for x in q2 if x not in q_all]
    if loi_thoai and all(NH.la_cau_hoi(x) or NH.Q_LABEL_RE.match(x) for x in loi_thoai):   # chỉ có câu hỏi (53930…)
        q_all += [x for x in loi_thoai if x not in q_all]
        loi_thoai = []
    out = []
    chu_bai = None
    for r in rows:
        sid = sid_of(r)
        g = (r.get("giai_thich_vi") or "").strip()
        lua_chon = [_plain(r.get(f"lua_chon_{i}", "")) for i in range(1, 5)]
        cau_hoi = _plain(r.get("cau_hoi", ""))
        rec = {"sample_id": sid, "question_id": int(r["question_id"]), "cau_con": int(r["cau_con"]), "cap_do": r["cap_do"],
               "hash_goc": sha(g + "|" + (r.get("transcript_vi") or "") + "|" + r.get("cau_hoi", "") + "|" + "|".join(lua_chon) + "|" + r["dap_an_so"]),
               "de": {"cau_hoi": cau_hoi, "lua_chon": lua_chon,
                      "dap_an_so": int(r["dap_an_so"]) if r["dap_an_so"].isdigit() else r["dap_an_so"],
                      "dap_an_noi_dung": _plain(r.get("dap_an_noi_dung", ""))},
               "co": [], "ghi_chu_ban_goc": [], "ruby_hong": [], "danh_dau_rac": [],
               "bai": {"cac_cau": [sid_of(x) for x in rows], "so_cau_hoi": len(rows)},
               "loi_thoai": {"dong": loi_thoai, "nguon": sid_of(nguon) if nguon else None, "cau_hoi_cat": q_all, "dau_cat": dau_cat},
               "doan_van": "\n".join(loi_thoai) or None}
        if len(rows) > 1:
            rec["co"].append("bai_2_cau_hoi")
        if dan_nham:
            rec["co"].append("loi_thoai_dan_nham")
        if not loi_thoai:
            rec["co"].append("loi_thoai_trong")
        if cach:
            rec["co"].append("cach_chu_nhat")
            rec["ghi_chu_ban_goc"].append("[Python sửa định dạng] Lời thoại: bỏ khoảng trắng chen giữa chữ Nhật ('話 し て い ま す' → '話しています')")
        if any(not x for x in lua_chon):
            rec["co"].append("lua_chon_thieu")
        # câu hỏi đề xuất
        q = None
        ch = NH.bo_cach_chu_nhat(cau_hoi)
        rac_de = (not ch or re.fullmatch(r"\s*(?:質問|問題)?\s*[0-9０-９一二三]*\s*番?\s*[:：]?\s*", ch) or "まず話を" in ch
                  or "問題用紙" in ch or len(ch) > 150 or NH.tach_nguoi_noi(ch)[0] is not None)
        if not rac_de:
            q = NH.bo_nhan_cau_hoi(ch)
        else:
            cc = int(r["cau_con"])
            so = [x for x in q_all if NH.so_cau_hoi(x) == cc]
            if not so and len(q_all) >= cc and len(rows) > 1:
                so = [q_all[cc - 1]]
            if not so and len(rows) == 1 and q_all:
                so = q_all[:1]          # một câu con mà lời thoại có 2 câu hỏi: lấy câu số cc, không có số thì câu đầu
            q = NH.bo_nhan_cau_hoi(so[0]) if so else None
        rec["cau_hoi_de_xuat"] = q
        if not q:
            rec["co"].append("khong_cau_hoi")
        # lời giải
        if not g:
            rec.update(khuon_goc="trong", dau_vao=None, src_text="", src_vi_text="", src_text_furi="", marks_src=[], phan=None)
            rec["ghi_chu_ban_goc"].append("[Bản gốc VI] Không có lời giải")
            out.append(rec)
            continue
        rac = []
        text, broken = normalize_html(g.replace("&nbsp;", " "), "u+b", rac)
        text = re.sub(r"\n?\s*###\s*\n?", "\n###\n", text, count=1) if MARK in text else text
        text, tk = tach_tham_khao(text)
        kh = khuon(text)
        pre, after = (text.split(MARK, 1) + [""])[:2] if MARK in text else ((text, "") if kh in ("C_vi", "C_ja") else ("", text))
        phan = {"tham_khao": tk, "dich_vi": [x.strip() for x in pre.split("\n") if x.strip()] if kh != "C_ja" else [],
                "phan_tich": None, "mo_dau": None, "thong_tin": None}
        if kh == "A":
            phan["mo_dau"], phan["phan_tich"] = phan_tich_A(after)
            dung = [k["so"] for k in phan["phan_tich"] if k["ket_luan"]]
            if len(dung) > 1:
                rec["co"].append("nhieu_dung")
            elif dung and str(dung[0]) != str(rec["de"]["dap_an_so"]):
                rec["co"].append("lech_dap_an")
            if any(k["ket_luan"] is None for k in phan["phan_tich"]):
                rec["co"].append("thieu_ket_luan")
            if phan["mo_dau"]:
                rec["co"].append("co_mo_dau_phan_tich")
            for k in phan["phan_tich"]:
                if 1 <= k["so"] <= 4 and NH._k(k["lua_chon"]) != NH._k(lua_chon[k["so"] - 1]):
                    rec["co"].append("lua_chon_khac_de")
                for qq in k["trich"]:
                    if loi_thoai and NH.tim_trich(qq, "".join(loi_thoai)) == "khong":
                        rec["co"].append("trich_ngoai_loi_thoai")
        elif kh == "B":
            phan["thong_tin"] = thong_tin_B(after)
        if kh in ("B", "C_vi", "C_ja"):
            rec["co"].append("khuon_" + kh)
        if tk:
            rec["co"].append("tham_khao")
        if pairs(text):
            rec["co"].append("co_furigana")
        if broken:
            rec["co"].append("ruby_hong")
            rec["ghi_chu_ban_goc"].append(f"[Bản gốc VI] Có {len(broken)} thẻ ruby hỏng")
        src = "" if kh == "C_ja" else text
        if len(rows) > 1 and src:      # bài 2 câu hỏi: bỏ danh sách 'Câu 1/2: … 1.–4.' của bản dịch khỏi phép đo độ phủ (mỗi câu con chỉ chép phần của mình)
            pre_s, sep, aft = src.partition(MARK)
            pre_s = "\n".join(x for x in pre_s.split("\n") if not re.match(r"^\s*(?:Câu(?:\s*hỏi)?\s*\d*\s*[:：]|[1-4]\s*[\.．])", x))
            src = pre_s + sep + aft
        rec.update(khuon_goc=kh, dau_vao=text, src_text=src, src_vi_text=src, src_text_furi=src,
                   marks_src=[], phan=phan, ruby_hong=broken, danh_dau_rac=rac)
        if chu_bai is None and kh != "trong":
            chu_bai = sid
        out.append(rec)
    for rec in out:
        rec["bai"]["chu_bai"] = chu_bai
        rec["ft_chep_tu"] = chu_bai if (chu_bai and rec["sample_id"] != chu_bai) else None
        if rec["ft_chep_tu"]:
            rec["co"].append("chep_loi_thoai")
            ph = rec.get("phan") or {}
            # câu con 2: full_translation không tính ở câu này → đo độ phủ trên phần sau ### (hoặc cả lời giải nếu không có bản dịch)
            if rec.get("dau_vao") and MARK in rec["dau_vao"]:
                rec["src_text"] = rec["src_vi_text"] = rec["src_text_furi"] = rec["dau_vao"].split(MARK, 1)[1]
            ph["dich_vi_cau_con_1"] = True            # bản dịch (nếu có) dùng ở câu con 1
        rec["co"] = sorted(set(rec["co"]))
    return out


# ---------------- Python dựng JSON cho khuôn C_ja ----------------
def dung_ft_python(norm, co_nghia=False):
    dong = (norm.get("loi_thoai") or {}).get("dong") or []
    if not dong:
        return None
    lines = []
    for x in dong:
        sp, ja = NH.tach_nguoi_noi(x)
        lines.append({"speaker": sp, "ja": ja, "meaning": None})
    return [{"label": None, "lines": lines}]


def dung_json_python(norm):
    de = norm["de"]
    dap = de["dap_an_so"] if isinstance(de["dap_an_so"], int) else None
    opts = [{"index": i + 1, "option_ja": x, "reading": None, "meaning": None, "is_match": dap == i + 1,
             "quotes": [], "analysis": None} for i, x in enumerate(de["lua_chon"])]
    doc = {"schema": "reading_listening.v1", "question_id": norm["question_id"], "cau_con": norm["cau_con"],
           "full_translation": None if norm.get("ft_chep_tu") else dung_ft_python(norm), "summary": None,
           "question": {"ja": norm.get("cau_hoi_de_xuat"), "meaning": None}, "options": opts, "key_info": None,
           "correct": {"index": dap or 1, "option_ja": de["lua_chon"][dap - 1] if dap else "", "full_sentence": None}}
    return doc


# ---------------- Python điền sau tác tử TẠO (hook bo_sung) ----------------
def ban_moi_nhat_vi(sid):
    for p in (OUT("json_vi", "checked", sid + ".json"), OUT("json_vi", "final", sid + ".json"),
              OUT("json_vi", "claude_tao", sid + ".json"), OUT("json_vi", "gpt", sid + ".json")):
        if os.path.exists(p):
            return load_json(p)
    return None


def bo_sung(doc, norm):
    """Python điền: summary = null; correct theo dap_an_so; câu con 2: chép full_translation của câu con 1."""
    doc["summary"] = None
    dap = norm["de"]["dap_an_so"]
    opts = doc.get("options") or []
    if isinstance(dap, int) and 1 <= dap <= len(opts):
        doc["correct"] = {"index": dap, "option_ja": opts[dap - 1].get("option_ja"), "full_sentence": None}
    if norm.get("ft_chep_tu"):
        c1 = ban_moi_nhat_vi(norm["ft_chep_tu"])
        doc["full_translation"] = copy.deepcopy((c1 or {}).get("full_translation"))
    return doc


def dong_bo_ft(doc, norm, lop="json_vi"):
    """Câu con 2: lấy full_translation của câu con 1 (bản checked/final mới nhất) – trả về True nếu đã đổi."""
    if not norm.get("ft_chep_tu"):
        return False
    c1 = None
    for p in (OUT(lop, "checked", norm["ft_chep_tu"] + ".json"), OUT(lop, "final", norm["ft_chep_tu"] + ".json")):
        if os.path.exists(p):
            c1 = load_json(p)
            break
    if c1 is None:
        return False
    if doc.get("full_translation") != c1.get("full_translation"):
        doc["full_translation"] = copy.deepcopy(c1.get("full_translation"))
        return True
    return False


# ---------------- kiểm tra riêng GĐ1 (K-…) ----------------
def _v(o):
    return (o or {}).get("vi") if o else None


def check_k(doc, norm, policy, cfg_kt=None):
    loi, cb = [], []
    cfg_kt = cfg_kt or {}
    de, phan, kh = norm["de"], norm.get("phan") or {}, norm.get("khuon_goc")
    opts = doc.get("options") or []
    dap = de["dap_an_so"] if isinstance(de["dap_an_so"], int) else None
    # K-LC: 4 lựa chọn, option_ja = dòng lựa chọn của lời giải (khuôn A) hoặc cột lua_chon của đề
    if [o.get("index") for o in opts] != [1, 2, 3, 4]:
        loi.append(f"K-LC: options phải có đủ 4 lựa chọn theo thứ tự 1–4 (đang có {[o.get('index') for o in opts]})")
    khoi = {k["so"]: k for k in (phan.get("phan_tich") or [])}
    for o in opts:
        i = o.get("index")
        if not isinstance(i, int) or not 1 <= i <= 4:
            continue
        hop_le = [x for x in (de["lua_chon"][i - 1], (khoi.get(i) or {}).get("lua_chon")) if x]
        if not any(NH._k(o.get("option_ja")) == NH._k(x) for x in hop_le):
            loi.append(f"K-LC: lựa chọn {i}: option_ja '{o.get('option_ja')}' khác cả đề '{de['lua_chon'][i - 1]}' lẫn dòng lựa chọn của lời giải")
        if o.get("reading") is not None:
            loi.append(f"K-LC: lựa chọn {i}: reading phải null (lời giải không có dòng cách đọc riêng)")
        k = khoi.get(i)
        if kh == "A" and k:
            if k["ket_luan"] is not None and o.get("is_match") is not k["ket_luan"]:
                loi.append(f"K-IM: lựa chọn {i}: is_match phải là {k['ket_luan']} (lời giải: → {'ĐÚNG' if k['ket_luan'] else 'SAI'})")
            if (k["nghia"] is None) != (o.get("meaning") is None) and k["nghia"] is not None:
                loi.append(f"K-NG: lựa chọn {i}: lời giải có dòng 'Nghĩa:' nhưng meaning = null")
            nq = len(o.get("quotes") or [])
            if nq != len(k["trich"]):
                cb.append(f"K-QT: lựa chọn {i}: JSON có {nq} câu trích, lời giải có {len(k['trich'])} đoạn 「…」 tiếng Nhật – xem có sót / tách gộp sai không")
            if k["van_ban"].strip() and o.get("analysis") is None and len(vi_words(strip_labels(QUOTE_RE.sub('', k['van_ban'])))) > 12:
                cb.append(f"K-AN: lựa chọn {i}: lời giải có phần nhận xét nhưng analysis = null")
        elif kh in KHUON_THIEU:
            if dap and o.get("is_match") is not (i == dap):
                loi.append(f"K-IM: lựa chọn {i}: khuôn {kh} không có kết luận ĐÚNG/SAI – is_match phải theo dap_an_so ({i == dap})")
            if o.get("quotes") or o.get("analysis") is not None:
                cb.append(f"K-AN: lựa chọn {i}: khuôn {kh} không có phân tích – quotes = [], analysis = null")
        # K-TD: câu trích có trong lời thoại
        goc = "".join((norm.get("loi_thoai") or {}).get("dong") or [])
        for j, qt in enumerate(o.get("quotes") or []):
            if goc and NH.tim_trich(qt.get("ja"), goc) == "khong":
                cb.append(f"K-TD: lựa chọn {i} câu trích {j + 1} không tìm thấy trong lời thoại: '{(qt.get('ja') or '')[:40]}'")
    # K-DA: đáp án
    nm = [o.get("index") for o in opts if o.get("is_match") is True]
    if "nhieu_dung" not in norm["co"] and dap and nm != [dap]:
        loi.append(f"K-DA: is_match = true phải đúng 1 lựa chọn là đáp án {dap} (đang: {nm})")
    elif "nhieu_dung" in norm["co"]:
        cb.append(f"K-DA: lời giải ghi ĐÚNG ở nhiều lựa chọn ({nm}) – gắn cờ dap_an (quy tắc 3d-4)")
    c = doc.get("correct") or {}
    if dap and c.get("index") != dap:
        loi.append(f"K-DA: correct.index = {c.get('index')} khác dap_an_so = {dap}")
    if dap and 1 <= dap <= len(opts) and c.get("option_ja") != opts[dap - 1].get("option_ja"):
        loi.append("K-DA: correct.option_ja phải giống hệt option_ja của đáp án")
    if c.get("full_sentence") is not None or doc.get("summary") is not None:
        loi.append("K-DA: correct.full_sentence và summary phải null (dạng 21)")
    # K-Q: câu hỏi
    q = doc.get("question") or {}
    if norm.get("cau_hoi_de_xuat") and NH._k(q.get("ja")) != NH._k(norm["cau_hoi_de_xuat"]):
        cb.append(f"K-Q: question.ja khác câu hỏi Python đề xuất '{norm['cau_hoi_de_xuat']}' – xem lại")
    if not q.get("ja") and norm.get("cau_hoi_de_xuat"):
        loi.append("K-Q: question.ja = null trong khi đề có câu hỏi")
    # K-KI: key_info
    ki = doc.get("key_info")
    if kh == "B":
        if not ki:
            loi.append("K-KI: khuôn 'Thông tin:' – key_info phải có các dòng của đoạn Thông tin")
        else:
            tt = "".join((phan.get("thong_tin") or {}).get("ja") or [])
            for j, ln in enumerate(ki):
                if ln.get("ja") and NH.tim_trich(ln["ja"], tt) == "khong":
                    loi.append(f"K-KI: key_info[{j}].ja không có trong đoạn 'Thông tin:' của lời giải")
    elif ki is not None:
        loi.append("K-KI: key_info chỉ dùng cho khuôn 'Thông tin:' – phải null")
    # K-FT: lời thoại
    loi_, cb_ = check_ft(doc, norm, cfg_kt)
    loi += loi_
    cb += cb_
    # K-TK
    loi += TK.kiem_tra(doc, phan.get("tham_khao"))
    return loi, cb


def check_ft(doc, norm, cfg_kt=None):
    loi, cb = [], []
    ft = doc.get("full_translation")
    dong = (norm.get("loi_thoai") or {}).get("dong") or []
    if norm.get("ft_chep_tu"):
        c1 = ban_moi_nhat_vi(norm["ft_chep_tu"])
        if c1 is not None and ft != c1.get("full_translation"):
            loi.append(f"K-FT: câu con 2 – full_translation phải giống hệt câu con 1 ({norm['ft_chep_tu']}); sửa ở câu con 1 rồi chạy lại")
        return loi, cb
    co_dich = bool((norm.get("phan") or {}).get("dich_vi"))
    if not dong and not co_dich:
        if ft:
            cb.append("K-FT: không có lời thoại / bản dịch gốc nhưng full_translation có nội dung")
        return loi, cb
    if not ft:
        loi.append("K-FT: có lời thoại / bản dịch nhưng full_translation = null")
        return loi, cb
    lines = [ln for blk in ft for ln in (blk.get("lines") or [])]
    if dong:
        thua, thieu, tl = NH.so_loi_thoai(lines, dong)
        thua = [x for x in thua if x.strip()]
        if thua:
            loi.append(f"K-FT: lines[].ja có chữ KHÔNG có trong lời thoại gốc (sửa / thêm chữ?): {thua[:5]}")
        if tl > (cfg_kt or {}).get("loi_thoai_thieu_toi_da", 0.02):
            cb.append(f"K-FT: thiếu {tl:.1%} chữ lời thoại gốc trong lines[].ja: {[x[:30] for x in thieu][:5]} – nếu là câu hỏi / lựa chọn / lời dẫn đề Python cắt sót thì bỏ qua")
        for j, ln in enumerate(lines):
            if ln.get("ja") and co_dich and ln.get("meaning") is None:
                cb.append(f"K-FT: lines[{j}] có ja nhưng meaning = null (lời giải có bản dịch)")
    if not co_dich and any(ln.get("meaning") for ln in lines):
        loi.append("K-FT: lời giải không có bản dịch lời thoại – meaning phải null (không tự dịch)")
    return loi, cb


def kiem_tra_gd1(doc, norm, cfg, schema):
    """Kiểm tra chung + riêng GĐ1 (dùng ở s1_claude_goi và s1_kiem_tra)."""
    from pipeline_chung.checks_chung import check_vi
    d = copy.deepcopy(doc)
    if norm.get("ft_chep_tu"):
        d["full_translation"] = None          # câu con 2: lời thoại kiểm ở câu con 1
    r = check_vi(d, schema, norm["src_text"], norm["src_vi_text"], norm, cfg["kiem_tra"], strip_labels,
                 marks_src=norm["marks_src"], furi_src_text=norm["src_text_furi"], furi_skip=FURI_SKIP)
    if norm.get("ft_chep_tu"):          # schema kiểm trên bản đầy đủ
        from pipeline_chung.checks_chung import schema_errors
        r["loi"] = [x for x in r["loi"] if not x.startswith("Schema:")] + schema_errors(doc, schema)
    k_loi, k_cb = check_k(doc, norm, cfg["chinh_sach"], cfg["kiem_tra"])
    r["loi"] += k_loi
    r["canh_bao"] += k_cb
    return r


# ---------------- âm Hán Việt / gợi ý định dạng (giữ như các dạng trước) ----------------
_UP = "A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬĐÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ"
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


_LO = "a-zàáảãạăằắẳẵặâầấẩẫậđèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ"
FORMAT_HINT_RES = [
    ("dính câu", re.compile(rf"[{_LO}\)\]\"”'’.。:：][{_UP}][{_LO}]")),
    ("lặp từ", re.compile(rf"(?i)\b([{_LO}]{{2,}})\s+\1\b")),
    ("dấu câu thừa", re.compile(r"[ \t][,.;:](?=\s|$)|,[ \t]*\)|\([ \t]+[,.]")),
]


def format_hints(norm):
    t = norm.get("src_text") or ""
    out = []
    for name, rx in FORMAT_HINT_RES:
        for m in rx.finditer(t):
            out.append(f"{name}: …{t[max(0, m.start() - 15):m.end() + 15].replace(chr(10), '⏎')}…")
    return out[:12]


def sudachi_hints(norm):
    return []


# ---------------- kiểm tra riêng GĐ2: D1 ----------------
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
    """Chỉ phần nhận xét (analysis – dịch từ tiếng Việt) kiểm tra văn phong -습니다."""
    p = path if isinstance(path, str) else path_str(path)
    return bool(re.search(r"\.analysis$|\.analysis\.", p))


# ---------------- hiển thị cho Excel CTV ----------------
def _t(obj, lang):
    return show((obj or {}).get(lang) or "") if obj else ""


def render(d, lang, co_loi_thoai=True):
    out = []
    ft = d.get("full_translation") or []
    if ft and co_loi_thoai:
        out.append(bold("【Lời thoại】"))
        for blk in ft:
            if blk.get("label"):
                out.append(bold(f"[{blk['label']}]"))
            for ln in blk.get("lines") or []:
                sp = f"{ln['speaker']}：" if ln.get("speaker") else ""
                if ln.get("ja"):
                    out.append(sp + show(ln["ja"]))
                if ln.get("meaning"):
                    out.append("   → " + _t(ln["meaning"], lang))
    q = d.get("question") or {}
    out.append(f"{bold('【Câu hỏi】')} {show(q.get('ja') or '')}")
    if q.get("meaning"):
        out.append("   Nghĩa: " + _t(q["meaning"], lang))
    out.append(bold("【Phân tích】"))
    for o in d.get("options") or []:
        out.append(bold(f"{o.get('index')}. ") + show(o.get("option_ja") or ""))
        if o.get("meaning"):
            out.append("   Nghĩa: " + _t(o["meaning"], lang))
        for qt in o.get("quotes") or []:
            out.append("   「" + show(qt.get("ja") or "") + "」")
            if qt.get("meaning"):
                out.append("   (" + _t(qt["meaning"], lang) + ")")
        if o.get("analysis"):
            out.append("   " + _t(o["analysis"], lang).replace("\n", "\n   "))
        out.append("   → " + ("ĐÚNG" if o.get("is_match") else "SAI")
                   + ("" if (o.get("quotes") or o.get("analysis")) else " (theo đáp án – lời giải gốc không phân tích)"))
    if d.get("key_info"):
        out.append(bold("【Thông tin】"))
        for ln in d["key_info"]:
            sp = f"{ln['speaker']}：" if ln.get("speaker") else ""
            if ln.get("ja"):
                out.append(sp + show(ln["ja"]))
            if ln.get("meaning"):
                out.append("   → " + _t(ln["meaning"], lang))
    c = d.get("correct") or {}
    out.append(bold("【Đáp án】") + f" {c.get('index')}. {show(c.get('option_ja') or '')}")
    out += TK.render(d, lang, show, bold)
    return "\n".join(out)


# ---------------- thứ tự chạy theo BÀI NGHE ----------------
def tao_thu_tu_bai(recs, cfg):
    """Lô 1 (pilot) = 2 bài N1 + 2 bài N2 khuôn A (≥ 1 bài lời thoại lệch dòng với bản dịch) + 1 bài 2 câu hỏi khuôn B;
    sau đó N1 / N2 xen kẽ theo thứ tự file dữ liệu. Trả về (thu_tu, lo_chay)."""
    tc = cfg.get("thu_tu_chay") or {}
    n_lo = int(tc.get("bai_moi_lo", 5))
    bai = collections.OrderedDict()
    for r in recs:
        bai.setdefault(r["question_id"], []).append(r)
    info = {q: {"cap": v[0]["cap_do"], "khuon": v[0]["khuon_goc"], "n": len(v),
                "lech": abs(len((v[0].get("phan") or {}).get("dich_vi") or []) - len((v[0].get("loi_thoai") or {}).get("dong") or [])) > 1}
            for q, v in bai.items()}
    ok = lambda q: all(r["khuon_goc"] != "trong" and "lua_chon_thieu" not in r["co"] for r in bai[q])  # noqa: E731
    pilot = []
    for cap in ("N1", "N2"):
        a = [q for q, x in info.items() if x["cap"] == cap and x["khuon"] == "A" and x["n"] == 1 and ok(q)]
        lech = [q for q in a if info[q]["lech"]]
        chon = (lech[:1] + [q for q in a if q not in lech[:1]])[:2]
        pilot += chon
    b = [q for q, x in info.items() if x["khuon"] == "B" and x["n"] == 2]
    pilot += b[:1]
    rest = [q for q in bai if q not in pilot]
    n1 = [q for q in rest if info[q]["cap"] == "N1"]
    n2 = [q for q in rest if info[q]["cap"] != "N1"]
    xen = [x for pair in zip(n1, n2) for x in pair] + n1[len(n2):] + n2[len(n1):]
    order = pilot + xen
    tt, lo, stt = [], [], 0
    for i, q in enumerate(order):
        so_lo = i // n_lo + 1
        for r in sorted(bai[q], key=lambda r: r["cau_con"]):
            stt += 1
            tt.append({"stt": stt, "sample_id": r["sample_id"], "question_id": q, "cap_do": r["cap_do"],
                       "khuon": r["khuon_goc"], "bai": i + 1, "lo": so_lo})
    for so_lo in sorted({x["lo"] for x in tt}):
        xs = [x for x in tt if x["lo"] == so_lo]
        lo.append({"lo": so_lo, "tu": xs[0]["stt"], "den": xs[-1]["stt"], "so_bai": len({x["question_id"] for x in xs}),
                   "so_cau": len(xs), "bai": " ".join(str(x) for x in dict.fromkeys(x["question_id"] for x in xs)),
                   "khuon": " ".join(x["khuon"] for x in xs)})
    return tt, lo
