"""Phần riêng của dạng 14 – Đọc hiểu chủ đề / quan điểm (đoạn văn dài) – dựng 2026-10-08 (Claude Opus 5.5 Cowork, không GPT API).

Schema reading_listening.v1 (+ reference_raw). Phần đọc hiểu dùng chung (làm sạch đoạn văn, tách lời giải kiểu A/B, so trích dẫn,
phân loại câu hỏi, render) ở pipeline_chung/doc_hieu.py; file này chỉ chứa phần riêng: cờ s0, kiểm tra K…, thứ tự chạy theo đoạn văn,
khuôn lạ → TẠO MỚI (bắt buộc CTV tiếng Nhật duyệt). Kế hoạch đã duyệt: KE_HOACH_PIPELINE.md.
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
    os.environ["PIPELINE_DATA"] = _c.get("du_lieu_test", "data/test_14_doc_hieu_chu_de_quan_diem.csv")


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
    """Thứ tự chạy --tu/--den: output/thu_tu_chay.csv (do s0_chuan_bi tạo – đoạn văn N1/N2 xen kẽ, khuôn lạ cuối) nếu có, không thì theo file dữ liệu."""
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




import _doc_hieu_14 as DH  # noqa: E402  (phần đọc hiểu của dạng 14)


# ---------------- nhãn cố định của lời giải gốc (bỏ khi đo độ phủ) ----------------
def strip_labels(text):
    return DH.strip_labels(text)


def text_without_ref(text):
    """Dạng 14 không có phần THAM KHẢO – trả nguyên văn."""
    return text


# ---------------- cờ s0 ----------------
FLAG_TEXT = {
    "chuan_A": "Khuôn chuẩn kiểu A (Nghĩa / Trích dẫn / Giải thích / → ĐÚNG|SAI)",
    "chuan_B": "Khuôn chuẩn kiểu B (trích dẫn + nhận xét viết thành gạch đầu dòng '- …')",
    "khuon_la": "Lời giải KHUÔN LẠ – không có phân tích đủ 4 lựa chọn (chỉ dịch đoạn văn / chỉ ghi đáp án / vài câu giải thích)",
    "tao_moi": "Khuôn lạ → tác tử TẠO soạn mới phần thiếu – BẮT BUỘC CTV tiếng Nhật duyệt trước khi dịch (Q2, 2026-10-08)",
    "co_dich_doan": "Lời giải có bản dịch ĐOẠN VĂN tiếng Việt ('Đoạn văn:') → full_translation của câu này",
    "nhieu_dung": "Khuôn chuẩn nhưng số lựa chọn '→ ĐÚNG' khác 1",
    "lech_dap_an": "Lựa chọn '→ ĐÚNG' của lời giải khác dap_an_so của đề",
    "thieu_nghia_lc": "Có lựa chọn không có dòng 'Nghĩa:'",
    "lc_khac_de": "Dòng lựa chọn trong lời giải viết khác lựa chọn của đề",
    "cau_hoi_khac_de": "Dòng câu hỏi trong lời giải viết khác câu hỏi của đề",
    "trich_ngoai_doan": "Có câu trích 「…」 không tìm thấy trong đoạn văn (so mờ, bỏ furigana / dấu câu / 注)",
    "trich_khong_dich": "Có câu trích không kèm bản dịch '(…)'",
    "cum_hoi_khong_trong_doan": "Cụm 「…」 trong câu hỏi không tìm thấy trong đoạn văn",
    "thieu_moc_doan": "Câu hỏi nhắc mốc ①②… mà đoạn văn không có mốc đó",
    "chen_tu_nhat": "Câu tiếng Việt có chen từ / cụm tiếng Nhật (giữ nguyên, bọc ⟪ ⟫)",
    "dong_lap": "Lời giải có dòng lặp lại liền nhau (nghi lỗi trình bày)",
    "doan_khung_html": "Đoạn văn có khung <table> / HTML Word (Python đã bóc)",
    "co_sau_dap_an": "Có đoạn chữ sau '→ ĐÚNG/SAI' của lựa chọn 4",
    "co_furigana": "Có furigana",
    "ruby_hong": "Có ruby hỏng trong bản gốc",
    "ky_hieu_trung": "Bản gốc có sẵn ký hiệu ｜《》 (trùng ký hiệu furigana)",
}
for _k, _v in DH.LOAI_CAU_HOI.items():
    FLAG_TEXT["hoi_" + _k] = "Loại câu hỏi: " + _v
CTV_FLAGS = ("tao_moi", "lech_dap_an", "nhieu_dung", "trich_ngoai_doan", "cum_hoi_khong_trong_doan")
FURI_SKIP = [("correct", "option_ja")]      # correct.option_ja là bản sao của options[i].option_ja – không đếm furigana 2 lần
KHUON_LA = ("la_dich_doan", "la_chi_dap_an", "la_ngan")


def la_khuon_la(norm):
    return (norm or {}).get("khuon_goc") in KHUON_LA


def parse_and_flag(text, lua_chon, dap_an_so, cau_hoi, doan_van):
    """Tách lời giải + gắn cờ + ghi chú bản gốc. Trả về (phan, co, ghi_chu)."""
    phan = DH.tach_loi_giai(text, lua_chon)
    co, gc = [phan["khuon"]] if phan["khuon"].startswith("chuan") else ["khuon_la", "tao_moi"], []
    dap = int(dap_an_so) if str(dap_an_so).isdigit() else None
    if re.search(r"(?m)^\s*Đoạn văn\s*[:：]", text):
        co.append("co_dich_doan")
    if phan["khuon"].startswith("chuan"):
        dung = [b["so"] for b in phan["lua_chon"] if b["ket_luan"]]
        if len(dung) != 1:
            co.append("nhieu_dung")
            gc.append(f"[Bản gốc VI] Lời giải chấm '→ ĐÚNG' cho {len(dung)} lựa chọn: {dung}")
        elif dap and dung[0] != dap:
            co.append("lech_dap_an")
            gc.append(f"[Bản gốc VI] Lời giải chấm ĐÚNG lựa chọn {dung[0]}, khác đáp án của đề (dap_an_so = {dap})")
        for b in phan["lua_chon"]:
            if b["nghia"] is None:
                co.append("thieu_nghia_lc")
            if DH._giong(b["dong"], lua_chon[b["so"] - 1]) < 0.9:
                co.append("lc_khac_de")
                gc.append(f"[Bản gốc VI] Lựa chọn {b['so']} trong lời giải viết khác đề: '{strip_marks(b['dong'])}' ↔ đề '{strip_marks(lua_chon[b['so'] - 1])}'")
            for q in b["trich"]:
                kq, tl = DH.so_trich_dan(q["ja"], doan_van)
                q["so_doan_van"] = kq
                if kq == "khong":
                    co.append("trich_ngoai_doan")
                    gc.append(f"[Bản gốc VI] Lựa chọn {b['so']}: câu trích không tìm thấy trong đoạn văn (khớp {tl:.0%}): 「{strip_marks(q['ja'])[:50]}…」")
                if q["vi"] is None:
                    co.append("trich_khong_dich")
        if phan["sau"]:
            co.append("co_sau_dap_an")
        if phan["dau"]["ja"] and DH._giong(phan["dau"]["ja"], cau_hoi) < 0.8:
            co.append("cau_hoi_khac_de")
            gc.append(f"[Bản gốc VI] Dòng câu hỏi trong lời giải khác câu hỏi của đề: '{strip_marks(phan['dau']['ja'])[:60]}'")
    else:
        gc.append(f"[Bản gốc VI] Lời giải khuôn lạ ({phan['khuon']}) – không có phân tích đủ 4 lựa chọn; tác tử TẠO soạn mới phần thiếu, CTV tiếng Nhật duyệt")
    for c in DH.cum_hoi(cau_hoi):
        if DH.so_trich_dan(c, doan_van)[0] == "khong":
            co.append("cum_hoi_khong_trong_doan")
            gc.append(f"[Bản gốc VI] Cụm được hỏi 「{c}」 không tìm thấy trong đoạn văn")
    for mk in DH.moc_hoi(cau_hoi):
        if mk not in doan_van:
            co.append("thieu_moc_doan")
    lines = [x.strip() for x in text.split("\n") if x.strip()]
    if any(a == b and len(a) > 15 for a, b in zip(lines, lines[1:])):
        co.append("dong_lap")
    if any(DH.co_tieng_viet(x) and re.search(r"[｜《》]|[ぁ-んァ-ン一-鿿]{2,}", re.sub(r"「[^」]*」|\"[^\"]*\"|“[^”]*”", "", x))
           for x in lines if not x.startswith(("「", "(")) and not DH.LUA_CHON_RE.match(x)):
        co.append("chen_tu_nhat")
    return phan, sorted(set(co)), gc


# ---------------- thứ tự chạy theo ĐOẠN VĂN ----------------
def tao_thu_tu_doan(recs, cfg):
    """Nhóm theo question_id (= đoạn văn). 3 đoạn PILOT đầu (theo KE_HOACH): 1 đoạn N1 khuôn chuẩn kiểu A, 1 đoạn N2 khuôn chuẩn kiểu B
    có câu quan điểm, 1 đoạn khuôn lạ có bản dịch đoạn văn; sau đó các đoạn khuôn chuẩn N1/N2 xen kẽ (ngẫu nhiên theo seed),
    cuối cùng các đoạn khuôn lạ. Câu con của một đoạn luôn liền nhau. Trả về (thu_tu, lo_chay)."""
    import random
    tc = cfg.get("thu_tu_chay") or {}
    rng = random.Random(tc.get("seed", 2026))
    nhom = {}
    for r in recs:
        nhom.setdefault(r["question_id"], []).append(r)
    for v in nhom.values():
        v.sort(key=lambda r: r["cau_con"])

    def la(q):
        return any(r["khuon_goc"] in KHUON_LA for r in nhom[q])

    def kieu(q, k):
        return sum(r["khuon_goc"] == k for r in nhom[q]) >= len(nhom[q]) / 2

    qs = list(nhom)
    pilot = []
    for cond in (lambda q: not la(q) and nhom[q][0]["cap_do"] == "N1" and kieu(q, "chuan_A"),
                 lambda q: not la(q) and nhom[q][0]["cap_do"] == "N2" and kieu(q, "chuan_B") and any(r["loai_cau_hoi"] == "quan_diem" for r in nhom[q]),
                 lambda q: la(q) and any("co_dich_doan" in r["co"] for r in nhom[q])):
        q = next((q for q in qs if q not in pilot and cond(q)), None)
        if q is not None:
            pilot.append(q)
    con = [q for q in qs if q not in pilot]
    chuan = {lv: [q for q in con if not la(q) and nhom[q][0]["cap_do"] == lv] for lv in ("N1", "N2")}
    lam = {lv: [q for q in con if la(q) and nhom[q][0]["cap_do"] == lv] for lv in ("N1", "N2")}
    for d in (chuan, lam):
        for v in d.values():
            rng.shuffle(v)

    def xen(d):
        out, a, b = [], d["N1"], d["N2"]
        for i in range(max(len(a), len(b))):
            out += ([a[i]] if i < len(a) else []) + ([b[i]] if i < len(b) else [])
        return out
    order = pilot + xen(chuan) + xen(lam)
    rows, lo_rows, stt = [], [], 0
    n_lo = int(tc.get("doan_moi_lo", 3))
    for i in range(0, len(order), n_lo):
        grp = order[i:i + n_lo]
        tu = stt + 1
        for q in grp:
            for r in nhom[q]:
                stt += 1
                rows.append({"stt": stt, "sample_id": r["sample_id"], "question_id": q, "cap_do": r["cap_do"],
                             "khuon": r["khuon_goc"], "lo": len(lo_rows) + 1})
        lo_rows.append({"lo": len(lo_rows) + 1, "tu": tu, "den": stt, "so_cau": stt - tu + 1,
                        "doan": " ".join(str(q) for q in grp), "cap_do": " ".join(nhom[q][0]["cap_do"] for q in grp),
                        "khuon_la": sum(la(q) for q in grp), "ghi_chu": "PILOT" if i == 0 else ""})
    return rows, lo_rows


# ---------------- tiện ích ----------------
def _v(o):
    return (o or {}).get("vi") if o else None


def _kj(s):
    """So tiếng Nhật: bỏ furigana / ⟪⟫ / { } / khoảng trắng / 「」 ngoài cùng."""
    s = re.sub(r"[\s　]", "", norm_ja(s or ""))
    return s[1:-1] if s.startswith("「") and s.endswith("」") else s


def vi_lua_chon(o):
    """Toàn bộ chữ tiếng Việt của một lựa chọn trong JSON."""
    return "\n".join(x for x in [_v(o.get("meaning"))] + [_v(q.get("meaning")) for q in o.get("quotes") or []]
                     + [_v(o.get("analysis"))] if x)


def _cover(src, out):
    from pipeline_chung.common import vi_words
    import collections as _c
    s, o = _c.Counter(vi_words(strip_labels(src or ""))), _c.Counter(vi_words(out or ""))
    if not s:
        return 1.0, []
    return sum((s & o).values()) / sum(s.values()), [w for w, _ in (s - o).most_common(8)]


def anh_em(norm, lop=("checked", "final")):
    """JSON tiếng Việt của các câu con khác cùng đoạn văn (đã có bản checked / final)."""
    out = {}
    for sid in [f"{norm['question_id']}_{k}" for k in range(1, 7)]:
        if sid == norm["sample_id"]:
            continue
        for l in lop:
            p = OUT("json_vi", l, sid + ".json")
            if os.path.exists(p):
                out[sid] = load_json(p)
                break
    return out


def truong_tao_moi(doc, norm, nguong=0.5):
    """Các trường tiếng Việt mà phần lớn chữ KHÔNG có trong lời giải gốc (= tác tử TẠO soạn mới) – cho câu khuôn lạ."""
    from pipeline_chung.common import vi_words
    src = set(vi_words(norm.get("src_vi_text") or ""))
    out = []
    for fp, o in iter_lang_fields(doc):
        w = vi_words(o["vi"])
        if w and sum(x in src for x in w) / len(w) < nguong:
            out.append(path_str(fp))
    return out


# ---------------- kiểm tra riêng GĐ1 (K…) ----------------
def check_k(doc, norm, policy):
    loi, cb = [], []
    de, phan, co = norm["de"], norm.get("phan") or {}, set(norm.get("co") or [])
    dap = int(de["dap_an_so"]) if str(de["dap_an_so"]).isdigit() else None
    opts, q, c = doc.get("options") or [], doc.get("question") or {}, doc.get("correct") or {}
    chuan = str(phan.get("khuon") or "").startswith("chuan")
    # K1 – đáp án
    if dap and c.get("index") != dap:
        loi.append(f"K1: correct.index = {c.get('index')} ≠ dap_an_so {dap}")
    if isinstance(c.get("index"), int) and 1 <= c["index"] <= len(opts) and c.get("option_ja") != opts[c["index"] - 1].get("option_ja"):
        loi.append("K1: correct.option_ja phải giống hệt options[index-1].option_ja")
    if c.get("full_sentence") is not None:
        loi.append("K1: correct.full_sentence phải null (dạng 14 không có câu hoàn chỉnh)")
    # K2 – cấu trúc lựa chọn
    if [o.get("index") for o in opts] != [1, 2, 3, 4]:
        loi.append(f"K2: options phải đủ 4 lựa chọn, index 1–4 theo thứ tự (đang {[o.get('index') for o in opts]})")
    for o in opts:
        if o.get("reading") is not None:
            loi.append(f"K2: options[{o.get('index')}].reading phải null (lời giải không có dòng cách đọc)")
    # K3 – is_match
    dung = [o.get("index") for o in opts if o.get("is_match")]
    if dung != ([dap] if dap else dung):
        (cb if co & {"nhieu_dung", "lech_dap_an"} else loi).append(
            f"K3: is_match = true ở {dung} – phải đúng một lựa chọn và trùng đáp án {dap}")
    # K-FT / null
    if doc.get("summary") is not None or doc.get("key_info") is not None:
        loi.append("K-FT: summary và key_info phải null (lời giải dạng 14 không có)")
    if ("co_dich_doan" in co) != (doc.get("full_translation") is not None):
        loi.append("K-FT: full_translation " + ("phải chứa bản dịch đoạn văn có trong lời giải ('Đoạn văn:')" if "co_dich_doan" in co
                                              else "phải null (lời giải câu này không có bản dịch đoạn văn)"))
    loi += TK.kiem_tra(doc, None)
    dv = norm.get("doan_van") or ""
    if chuan:
        # K5 – câu hỏi, K6 – lựa chọn: chép đúng lời giải
        if phan["dau"].get("ja") and _kj(q.get("ja")) != _kj(phan["dau"]["ja"]):
            loi.append(f"K5: question.ja khác dòng câu hỏi của lời giải: '{strip_marks(phan['dau']['ja'])[:60]}'")
        if (phan["dau"].get("vi") is None) != (q.get("meaning") is None):
            loi.append("K5: question.meaning phải null khi và chỉ khi lời giải không có dòng dịch câu hỏi")
        for b in phan["lua_chon"]:
            i = b["so"] - 1
            if i >= len(opts):
                continue
            o = opts[i]
            if _kj(o.get("option_ja")) != _kj(b["dong"]):
                loi.append(f"K6: options[{i}].option_ja khác dòng lựa chọn {b['so']} của lời giải: '{strip_marks(b['dong'])[:50]}'")
            # K4 – ĐÚNG/SAI theo lời giải
            if b["ket_luan"] is not None and bool(o.get("is_match")) != b["ket_luan"]:
                loi.append(f"K4: options[{i}].is_match = {o.get('is_match')} nhưng lời giải ghi '→ {'ĐÚNG' if b['ket_luan'] else 'SAI'}'")
            if (b["nghia"] is None) != (o.get("meaning") is None):
                loi.append(f"K6: options[{i}].meaning phải null khi và chỉ khi lời giải không có dòng 'Nghĩa:' của lựa chọn {b['so']}")
            # K7 – trích dẫn phải có trong khối lời giải của lựa chọn đó
            than = _kj(b["than"])
            for j, qt in enumerate(o.get("quotes") or []):
                if _kj(qt.get("ja")) not in than:
                    loi.append(f"K7: options[{i}].quotes[{j}].ja không có trong lời giải của lựa chọn {b['so']} (chép nhầm lựa chọn / tự thêm?)")
                elif DH.so_trich_dan(qt.get("ja"), dv)[0] == "khong":
                    cb.append(f"K-TD: options[{i}].quotes[{j}] không tìm thấy trong đoạn văn (so mờ) – xem có trích sai / chép sai không")
            # K-PL – chữ Việt của lựa chọn nằm đúng lựa chọn
            cv, miss = _cover(b["than"], vi_lua_chon(o))
            if cv < (policy.get("phu_lua_chon_min") or 0.95):
                loi.append(f"K-PL: lựa chọn {b['so']} chỉ phủ {cv:.0%} chữ Việt của khối lời giải tương ứng (thiếu: {miss}) – nhận xét đặt nhầm lựa chọn / bỏ sót?")
        # K-GC – câu hỏi về cụm gạch chân: có lựa chọn nào trích cụm đó không
        if norm.get("loai_cau_hoi") == "chi_dinh":
            for cum in DH.cum_hoi(de["cau_hoi"]):
                if not any(DH._k(cum) in DH._k(qt.get("ja")) for o in opts for qt in o.get("quotes") or []):
                    cb.append(f"K-GC: câu hỏi về 「{cum}」 nhưng không lựa chọn nào trích câu chứa cụm này – soát lời giải có giải thích đúng cái cụm chỉ tới không")
    else:
        # khuôn lạ – TẠO MỚI: đủ phần, trích dẫn phải lấy từ đoạn văn
        for o in opts:
            if o.get("meaning") is None or o.get("analysis") is None:
                loi.append(f"K-TM: khuôn lạ – options[{o.get('index', '?') - 1 if isinstance(o.get('index'), int) else '?'}] thiếu meaning / analysis (phải soạn đủ)")
            for j, qt in enumerate(o.get("quotes") or []):
                if DH.so_trich_dan(qt.get("ja"), dv)[0] == "khong":
                    loi.append(f"K-TM: options[{o.get('index')}].quotes[{j}] không có trong đoạn văn – trích dẫn tạo mới phải chép NGUYÊN câu của đoạn văn")
        if dap and 1 <= dap <= len(opts) and not opts[dap - 1].get("quotes"):
            cb.append("K-TM: lựa chọn đúng chưa có trích dẫn từ đoạn văn")
    # K-NQ – cùng câu trích trong một đoạn văn: nghĩa phải thống nhất giữa các câu con
    mine = {_kj(qt.get("ja")): _v(qt.get("meaning")) for o in opts for qt in o.get("quotes") or [] if _v(qt.get("meaning"))}
    for sid2, d2 in anh_em(norm).items():
        for o in d2.get("options") or []:
            for qt in o.get("quotes") or []:
                k, m = _kj(qt.get("ja")), _v(qt.get("meaning"))
                if k in mine and m and m != mine[k]:
                    cb.append(f"K-NQ: câu trích 「{strip_marks(qt.get('ja'))[:30]}…」 được dịch khác ở {sid2} – nghĩa câu trích nên giống nhau (chỉ ghi chú, không tự sửa nếu đúng như bản gốc)")
                    mine.pop(k, None)
    return loi, cb


# ---------------- kiểm tra riêng GĐ2: D1 ----------------
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
    """Kiểm tra văn phong -습니다 chỉ ở phần nhận xét (analysis); nghĩa câu / trích dẫn / bản dịch đoạn văn theo văn của câu gốc."""
    p = path if isinstance(path, str) else path_str(path)
    return bool(re.search(r"\.analysis$", p))


# ---------------- hiển thị cho Excel CTV ----------------
def render(d, lang):
    return DH.render(d, lang, show, bold, TK.render)


def nhan_cau_hoi(norm):
    return norm["de"]["cau_hoi"]


# ---------------- Cách chia v2: cờ âm Hán Việt trong lời giải gốc (như dạng 07/09) ----------------
_UP = "A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬĐÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ"
_HV_WORD = rf"[{_UP}]{{2,}}(?:\s+[{_UP}]{{2,}})*"
HV_SRC_RES = [
    re.compile(r"âm\s*h[áa]n\s*vi[ệe]t[^\n]{0,30}", re.I),
    re.compile(rf"ch[ữu]\s*h[áa]n\s*[\"'「]?[㐀-鿿]?[\"'」]?\s*,?\s*({_HV_WORD})\b"),
    re.compile(rf"[㐀-鿿](?:\s*[（(][^)）\n]{{0,15}}[)）])?\s*[-–—:]\s*({_HV_WORD})\b"),
    re.compile(rf"\bch[ữu]\s+({_HV_WORD})\b"),
]
HV_BO_QUA = {"VD", "JLPT", "TV", "OK", "DVD", "CD", "PC", "USB", "NHK", "JR", "II", "III", "IV", "SNS", "IT", "AI", "N1", "N2",
             "SAI", "ĐÚNG"}


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


# ---------------- Cách chia v2: gợi ý lỗi định dạng (Python dò, Claude xác nhận và sửa) ----------------
_LO = "a-zàáảãạăằắẳẵặâầấẩẫậđèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ"
FORMAT_HINT_RES = [
    ("dính câu", re.compile(rf"[{_LO}\)\]\"”'’.。:：][{_UP}][{_LO}]")),
    ("dính mục đánh số", re.compile(r"[^\s\d][.。][ \t]?\d{1,2}[.．][ \t]")),
    ("lặp từ", re.compile(rf"(?i)\b([{_LO}]{{2,}})\s+\1\b")),
    ("dấu câu thừa", re.compile(r"[ \t][,.;:](?=\s|$)|,[ \t]*\)|\([ \t]+[,.]")),
]
FURI_LECH_RE = re.compile(r"｜([぀-ゟ]+)([㐀-鿿々]+)《([^》]*)》")


def _hira(s):
    return "".join(chr(ord(ch) - 0x60) if "ァ" <= ch <= "ヶ" else ch for ch in s or "")


def format_hints(norm):
    t = norm.get("src_text") or ""
    out = []
    for name, rx in FORMAT_HINT_RES:
        for m in rx.finditer(t):
            out.append(f"{name}: …{t[max(0, m.start() - 15):m.end() + 15].replace(chr(10), '⏎')}…")
    for m in FURI_LECH_RE.finditer(t):
        if not _hira(m.group(3)).startswith(m.group(1)):
            out.append(f"furigana lệch phạm vi: '{m.group(0)}' → nên là '{m.group(1)}｜{m.group(2)}《{m.group(3)}》'")
    lines = [x.strip() for x in t.split("\n") if x.strip()]
    for a, b in zip(lines, lines[1:]):
        if a == b and len(a) > 15:
            out.append(f"dòng lặp: '{a[:40]}…'")
    return out[:12]


def sudachi_hints(norm):
    """Dạng 14 không dùng gợi ý Sudachi (không có dòng cách đọc)."""
    return []


def _tok():
    return None


# ---------------- furigana gắn lên chữ Việt (lỗi định dạng bản gốc – Python tự bỏ, như dạng 09) ----------------
FURI_VI_RE = re.compile(r"｜([^｜《》\n]*?[A-Za-zÀ-ỹĐđ][^｜《》\n]*?)《([^》\n]*)》")


def bo_furigana_chu_viet(text):
    """'｜Nhận xét《にんてい》' → 'Nhận xét'. Trả về (văn bản, danh sách (cũ, mới))."""
    doi = []

    def f(m):
        doi.append((m.group(0), m.group(1)))
        return m.group(1)
    return FURI_VI_RE.sub(f, text or ""), doi
