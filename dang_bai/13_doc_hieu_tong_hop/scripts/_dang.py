"""Phần riêng của dạng 13 – Đọc hiểu tổng hợp (dựng 2026-10-08, chạy hoàn toàn bằng Claude Opus 5.5 Cowork – không GPT API).

Khung hạ tầng (cfg / OUT / select_ids / kho đã duyệt …) chép từ dạng 09. Phần riêng dạng 13:
  - đoạn văn A / B (/ C, 相談者 – 回答者Ａ/Ｂ) tách theo nhãn (scripts/_doc_hieu_13.py), norm['doan_van'] = bản hiển thị 【A】…;
  - lời giải khuôn đọc hiểu → schema reading_listening.v1 (question / options[i]{option_ja, meaning, quotes[], analysis, is_match} / correct);
  - thứ tự chạy theo ĐOẠN VĂN, lô 4 đoạn (cột 'lo' của output/thu_tu_chay.csv); đoạn khuôn lạ dồn về lô cuối;
  - nhóm cờ nội dung mới 'trich_dan', 'phan_tich' (thêm vào claude_log.NHOM_NOI_DUNG lúc chạy – không sửa file chung).
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
    os.environ["PIPELINE_DATA"] = _c.get("du_lieu_test", "data/test_13_doc_hieu_tong_hop.csv")


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




# ---------------- dạng 13: nhóm cờ nội dung mới (bổ sung lúc chạy – không sửa pipeline_chung/claude_log.py khi đang có phiên song song) ----------------
from pipeline_chung import claude_log as _CL  # noqa: E402
_CL.NHOM_NOI_DUNG.update({"trich_dan", "phan_tich"})          # đọc hiểu: trích dẫn sai / gán nhầm đoạn A↔B; phân tích sai quan điểm A/B

import _doc_hieu_13 as DH  # noqa: E402

FLAG_TEXT = DH.FLAG_TEXT
CTV_FLAGS = DH.CTV_FLAGS
FURI_SKIP = [("correct", "option_ja")]          # correct.option_ja là bản sao của options[i].option_ja – lời giải không lặp lại
LABELS = DH.LABELS
strip_labels = DH.strip_labels


def _hira(s):
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s or "")


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




# ---------------- gợi ý cho tác tử KIỂM TRA (tên giữ như các dạng khác để s1_claude_goi gọi được) ----------------
def sudachi_hints(norm):
    """Dạng 13 không dùng Sudachi: trả gợi ý câu trích (K-TD không thấy / một phần, K-NGUON nghi gán nhầm đoạn A↔B)."""
    return DH.goi_y(norm)


def _tok():
    return False


# ---------------- làm sạch riêng dạng 13 (GĐ0 – chỉ định dạng, không đổi chữ) ----------------
NHAN_DAM_RE = re.compile(r"\{\s*((?:Đoạn văn(?:\s*[A-CＡ-Ｃ])?|Câu hỏi|Câu trả lời đúng là|Giải thích|Trích dẫn|Phân tích[^{}\n]{0,30}|[A-CＡ-Ｃ])\s*[:：]?)\s*\}")


def bo_dam_nhan(text):
    """{Đoạn văn:} / {A} / {Câu hỏi:} (nhãn in đậm của lời giải khuôn lạ) → bỏ { } – trình bày, không phải nội dung. Trả (text, số chỗ)."""
    return NHAN_DAM_RE.subn(r"\1", text)


RUBY_LA_RE = re.compile(r"<\|([^;|<>\n]+);([぀-ゟ゠-ヿー]+)\|>?")


def sua_ruby_la(text):
    """Ruby ghi kiểu lạ '<|貧;まず|しい' / '<|代;か|わり' (lỗi nhập liệu) → '｜貧《まず》しい'. Trả (text, [(cũ, mới)])."""
    doi = []
    def _r(m):
        moi = f"｜{m.group(1)}《{m.group(2)}》"
        doi.append((m.group(0), moi))
        return moi
    return RUBY_LA_RE.sub(_r, text), doi


FURI_VI_RE = re.compile(r"｜([^｜《》\n]*?[A-Za-zÀ-ỹĐđ][^｜《》\n]*?)《([^》\n]*)》")


def bo_furigana_chu_viet(text):
    """Bỏ furigana gắn lên chữ tiếng Việt / Latin – lỗi định dạng bản gốc. Trả (text, [(cũ, mới)])."""
    doi = []
    def _r(m):
        doi.append((m.group(0), m.group(1)))
        return m.group(1)
    return FURI_VI_RE.sub(_r, text), doi


# ---------------- kiểm tra riêng GĐ1 ----------------
def anh_em(norm):
    """JSON (checked, nếu có) của các câu con khác cùng đoạn văn – cho K-NQ."""
    out = []
    for sid in norm.get("cau_cung_doan") or []:
        if sid == norm["sample_id"]:
            continue
        p = OUT("json_vi", "checked", sid + ".json")
        if os.path.exists(p):
            try:
                out.append(load_json(p))
            except Exception:                                  # noqa: BLE001
                pass
    return out


def check_k(doc, norm, policy):
    loi, cb = DH.kiem_tra_json(doc, norm, anh_em(norm))
    loi += TK.kiem_tra(doc, (norm.get("phan") or {}).get("tham_khao"))
    return loi, cb


# ---------------- kiểm tra riêng GĐ2: D1 (câu cố định) ----------------
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
    """Chỉ phần nhận xét (analysis) dịch từ tiếng Việt mới xét văn phong -습니다; nghĩa câu / câu trích / bản dịch đoạn văn thì không."""
    p = path if isinstance(path, str) else path_str(path)
    return bool(re.search(r"\.analysis$", p))


# ---------------- hiển thị cho Excel CTV ----------------
def render(d, lang):
    return DH.render(d, lang, show, bold, TK.render)


# ---------------- thứ tự chạy theo đoạn văn ----------------
LO_DAU_TIEN = ("A/B N1", "A/B N2", "相談者 / 回答者", "bài đơn N2")


def tao_thu_tu_doan(recs, cfg):
    """Theo ĐOẠN VĂN (các câu con liền nhau). Lô 1 (pilot) = 1 đoạn A/B N1 + 1 đoạn A/B N2 + 1 đoạn 相談者/回答者 + 1 bài đơn N2;
    sau đó các đoạn còn lại xen kẽ N1 / N2 (ngẫu nhiên theo seed), mỗi lô `doan_moi_lo` đoạn; đoạn có lời giải khuôn lạ dồn về lô cuối."""
    import random
    tc = cfg.get("thu_tu_chay") or {}
    rng = random.Random(tc.get("seed", 2026))
    n_lo = tc.get("doan_moi_lo", 4)
    nhom, order = {}, []
    for r in recs:
        if r["question_id"] not in nhom:
            order.append(r["question_id"])
        nhom.setdefault(r["question_id"], []).append(r)
    for q in nhom:
        nhom[q].sort(key=lambda r: r["cau_con"])
    def loai(q):
        rs = nhom[q]
        segs = [x[0] for x in rs[0].get("doan_tach") or []]
        if "相談者" in segs:
            return "相談者 / 回答者"
        if not any(segs):
            return "bài đơn " + rs[0]["cap_do"]
        return "A/B " + rs[0]["cap_do"]
    la = [q for q in order if any(r["khuon_goc"] == "la" for r in nhom[q]) and
          sum(r["khuon_goc"] == "la" for r in nhom[q]) * 2 >= len(nhom[q])]          # đoạn mà ≥ nửa số câu khuôn lạ
    thuong = [q for q in order if q not in la]
    dau = []
    for kieu in LO_DAU_TIEN:
        ung = [q for q in thuong if loai(q) == kieu and q not in dau and len(nhom[q]) >= 2]
        if ung:
            dau.append(sorted(ung, key=lambda q: (len(nhom[q]), q))[0])
    con = [q for q in thuong if q not in dau]
    n1, n2 = [q for q in con if nhom[q][0]["cap_do"] == "N1"], [q for q in con if nhom[q][0]["cap_do"] != "N1"]
    rng.shuffle(n1)
    rng.shuffle(n2)
    xen = []
    while n1 or n2:
        for pool in (n1, n2):
            if pool:
                xen.append(pool.pop(0))
    doan = dau + xen + la
    rows, stt = [], 0
    for i, q in enumerate(doan):
        lo = 1 if i < len(dau) else (2 + (i - len(dau)) // n_lo if q not in la else None)
        for r in nhom[q]:
            stt += 1
            rows.append({"stt": stt, "sample_id": r["sample_id"], "question_id": r["question_id"], "cap_do": r["cap_do"],
                         "doan": i + 1, "kieu_doan": loai(q), "khuon": r["khuon"], "lo": lo})
    lo_cuoi = max(x["lo"] for x in rows if x["lo"]) + 1
    k = 0
    for q in la:                                                     # đoạn khuôn lạ: các lô cuối, mỗi lô n_lo đoạn
        for x in rows:
            if x["question_id"] == q:
                x["lo"] = lo_cuoi + k // n_lo
        k += 1
    return rows
