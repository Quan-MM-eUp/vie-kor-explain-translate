"""Phần riêng của dạng 06 – Ứng dụng từ (dựng 2026-10-07 từ dạng 05): cấu hình, đường dẫn, tách phần lời giải
(đoạn giới thiệu từ → PHÂN TÍCH: mỗi lựa chọn 'i. <câu>' + Cách đọc / Nghĩa + nhận xét + Sửa lại / Cách đọc / Nghĩa → LỰA CHỌN ĐÚNG),
gắn cờ, kiểm tra K1–K17 / D1, gợi ý SudachiPy R1 (cách đọc câu) + R2 (câu sửa không thay từ đang hỏi), hiển thị Excel.
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
    os.environ["PIPELINE_DATA"] = _c.get("du_lieu_test", "data/test_06_tu_vung_ung_dung_tu.csv")


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
NGOAI_PHAN_CONG = "--ngoai-phan-cong" in sys.argv   # (chạy song song) cho phép --tu/--den không trùng lô trong phan_cong.json
if NGOAI_PHAN_CONG:
    sys.argv.remove("--ngoai-phan-cong")
VIE_KOR = os.path.dirname(os.path.dirname(DANG))
sys.path.insert(0, VIE_KOR)

from pipeline_chung.common import (FURI_RE, LOCK_RE, get_path, iter_lang_fields, load_json, norm_ja,  # noqa: E402
                                   path_str, save_json, strip_marks)
from pipeline_chung.ctv_excel import B0, B1, bold, show  # noqa: E402


# ---------------- cấu hình & đường dẫn ----------------
_CFG = {}


def cfg():
    """config.json – đọc một lần mỗi tiến trình (2026-10-12: trước đây đọc lại mỗi lần gọi OUT(), chậm khi chạy song song)."""
    if "c" not in _CFG:
        _CFG["c"] = load_json(os.path.join(DANG, "config.json"))
    return _CFG["c"]


def P(*parts):
    """Đường dẫn tính từ thư mục dạng bài."""
    return os.path.normpath(os.path.join(DANG, *parts))


def _OUT0(*parts):
    return P(os.environ.get("PIPELINE_OUTPUT") or cfg()["output"], *parts)


# ---------------- CHẠY SONG SONG nhiều cuộc trò chuyện (2026-10-12) ----------------
# 1) File danh sách việc đặt tên theo lô (tránh tác tử TẠO của cuộc này đọc danh sách của cuộc khác).
# 2) Khóa chung: mỗi script giữ khóa output/.khoa từ lúc import _dang đến lúc kết thúc → các bước Python
#    (đọc–sửa–ghi trang_thai.csv, bộ nhớ dịch…) chạy lần lượt; tác tử TẠO và phần soát vẫn song song.
#    Khóa bằng phép ĐỔI TÊN file (atomic, không cần xóa file): .khoa/MO → .khoa/GIU_<…>; nhả: đổi lại thành MO.
# 3) Phân công lô: phan_cong.json (scripts/lo_jlpt.py --phan-cong) – các bước chính chỉ chạy đúng lô đã giao.
DANH_SACH_LO = {"tao_gd1_danh_sach.json", "gd1_danh_sach.json", "tao_gd2_danh_sach.json", "gd2_danh_sach.json"}
_DA_BAO_DS = set()


def hau_to_lo():
    """Hậu tố tên file danh sách của lệnh hiện tại: _<tu>_<den> | _ids_<id đầu> | '' (không chọn phạm vi)."""
    if TU is not None or DEN is not None:
        return f"_{TU or 1}_{DEN or 'het'}"
    if "--ids" in sys.argv:
        i = sys.argv.index("--ids")
        if i + 1 < len(sys.argv):
            return "_ids_" + sys.argv[i + 1].split(",")[0].strip()
    return ""


def OUT(*parts):
    """Thư mục output (đổi được bằng biến môi trường PIPELINE_OUTPUT – dùng khi chạy thử giả lập).
    output/claude/<4 file danh sách> được đổi tên theo lô (chạy song song)."""
    if len(parts) == 2 and parts[0] == "claude" and parts[1] in DANH_SACH_LO and _ss().get("bat"):
        ten = parts[1][:-5] + hau_to_lo() + ".json"
        if ten != parts[1] and ten not in _DA_BAO_DS:
            _DA_BAO_DS.add(ten)
            import atexit
            atexit.register(print, f"[Song song] File danh sách của lô này: output/claude/{ten}  (thay cho {parts[1]})")
        return _OUT0("claude", ten)
    return _OUT0(*parts)


def _ss():
    return cfg().get("song_song") or {}


_KHOA = {}


def _lay_khoa():
    import socket
    import time
    import atexit
    ss = _ss()
    if not ss.get("bat") or os.environ.get("PIPELINE_KHONG_KHOA"):
        return
    d = _OUT0(".khoa")
    try:
        os.makedirs(os.path.dirname(d), exist_ok=True)
        os.mkdir(d)                                   # ai tạo được thư mục thì tạo token MO
        open(os.path.join(d, "MO"), "x").close()
    except FileExistsError:
        pass
    mo = os.path.join(d, "MO")
    import uuid
    toi = os.path.join(d, f"GIU_{socket.gethostname()[:20]}_{os.getpid()}_{uuid.uuid4().hex[:6]}_{os.path.basename(sys.argv[0])}")
    het_han, cho_toi_da = int(ss.get("het_han_khoa_giay", 300)), int(ss.get("cho_khoa_toi_da_giay", 150))
    t0, da_bao = time.time(), False
    while True:
        try:
            os.rename(mo, toi)
            break
        except FileNotFoundError:
            pass
        giu = [f for f in os.listdir(d) if f.startswith("GIU_")]
        for f in giu:                                  # khóa treo (script bị ngắt) → lấy lại bằng đổi tên
            fp = os.path.join(d, f)
            try:
                if time.time() - os.path.getmtime(fp) > het_han:
                    os.rename(fp, toi)
                    print(f"[Khóa] Lấy lại khóa treo quá {het_han}s: {f}")
                    break
            except FileNotFoundError:
                continue
        if os.path.exists(toi):
            break
        if not da_bao:
            print(f"[Khóa] Cuộc khác đang chạy bước Python ({', '.join(giu) or '?'}) – chờ…", flush=True)
            da_bao = True
        if time.time() - t0 > cho_toi_da:
            sys.exit(f"[Khóa] Chờ quá {cho_toi_da}s chưa lấy được khóa {d} – chạy lại lệnh sau ít phút "
                     f"(khóa treo quá {het_han}s sẽ tự được lấy lại).")
        time.sleep(1)
    try:
        os.utime(toi, None)
    except OSError:
        pass
    _KHOA["file"] = toi

    import threading
    nhip = max(5, int(ss.get("nhip_khoa_giay", 15)))

    def _giu_nhip():                                  # "còn sống": chạm file khóa định kỳ – khóa chỉ bị coi là treo khi
        while True:                                   # tiến trình chết (không chạm quá het_han_khoa_giay)
            time.sleep(nhip)
            try:
                os.utime(toi, None)
            except FileNotFoundError:
                print(f"[Khóa] Cảnh báo: khóa {os.path.basename(toi)} đã bị cuộc khác lấy lại (quá hạn) khi lệnh này còn chạy")
                return
            except OSError:
                pass
    threading.Thread(target=_giu_nhip, daemon=True).start()

    def _nha():
        try:
            os.rename(toi, mo)
        except FileNotFoundError:
            print(f"[Khóa] Không nhả được khóa (đã bị lấy lại vì quá hạn?): {toi}")
    atexit.register(_nha)


BUOC_CHINH = {"s1_claude_tao.py", "s1_claude_goi.py", "s1_kiem_tra.py", "s1_chot.py",
              "s2_claude_dich.py", "s2_claude_goi.py", "s2_kiem_tra.py"}


def _kiem_phan_cong():
    """Chạy song song: các bước chính với --tu/--den chỉ được chạy đúng một lô trong phan_cong.json."""
    if not _ss().get("bat") or NGOAI_PHAN_CONG or (TU is None and DEN is None):
        return
    if os.path.basename(sys.argv[0]) not in BUOC_CHINH:
        return
    p = P("phan_cong.json")
    lo = json.load(open(p, encoding="utf-8")).get("lo", []) if os.path.exists(p) else []
    lo_ids = [x for x in lo if x.get("ids") and x.get("tu") == TU and x.get("den") == DEN]
    if lo_ids:   # (2026-10-12) lô giao theo danh sách id – khoảng chứa cả mẫu cũ không được chạy lại
        sys.exit(f"[Song song] Lô {TU}–{DEN} được giao theo DANH SÁCH ID (đợt {lo_ids[0].get('dot')}) – chạy bằng "
                 f"--ids {','.join(lo_ids[0]['ids'])}  (không dùng --tu/--den: khoảng này có mẫu cũ không được chạy lại).")
    if not any(x.get("tu") == TU and x.get("den") == DEN for x in lo):
        sys.exit(f"[Song song] Khoảng --tu {TU} --den {DEN} không phải một lô trong phan_cong.json (xem PHAN_CONG.md). "
                 "Chỉ chạy lô được giao; cuộc điều phối cần chạy khoảng khác thì thêm --ngoai-phan-cong.")


_lay_khoa()
_kiem_phan_cong()


# ---------------- bản TẠO (bước 1.1 chuyển JSON / 2.1–2.3 dịch) – GPT (mẫu 1–100) hoặc Claude tác tử tạo (từ 2026-10-08) ----------------
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
    """Các mẫu bị loại theo config.loc_nguon_de (quyết định 2026-10-11): từ mẫu tu_mau (stt theo thứ tự file dữ liệu (= output/thu_tu_chay.csv, đúng thứ tự --tu/--den của dạng 06)),
    bỏ mẫu mà cột `cot` (thi_thu_thuoc_de) chứa một trong `bo_neu_chua` (mặc định 'Nat Test'). Trả về {sample_id: giá trị cột}."""
    lc = cfg().get("loc_nguon_de") or {}
    if CA_NAT or not lc.get("bat"):
        return {}
    from pipeline_chung.common import read_csv
    cot, tu, kw = lc.get("cot", "thi_thu_thuoc_de"), int(lc.get("tu_mau", 1)), lc.get("bo_neu_chua") or ["Nat Test"]
    gt = {sid_of(r): r.get(cot) or "" for r in read_csv(data_path())}
    nat = {x for x, v in gt.items() if any(k.lower() in v.lower() for k in kw)}
    return {x: gt.get(x, "") for i, x in enumerate([sid_of(r) for r in read_csv(data_path())], 1) if i >= tu and x in nat}


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
        order = [sid_of(r) for r in read_csv(data_path())]
        a, b = TU or 1, DEN or len(order)
        if a < 1 or b < a:
            sys.exit(f"Phạm vi không hợp lệ: --tu {a} --den {b} (file dữ liệu có {len(order)} mẫu, đánh số từ 1)")
        allowed = set(status.ids(*default_states))
        ids = [s for s in order[a - 1:b] if s in allowed]
        print(f"Phạm vi: mẫu {a}–{min(b, len(order))} theo thứ tự trong {os.path.basename(data_path())}"
              f" → {len(ids)}/{len(order[a - 1:b])} câu ở trạng thái phù hợp cho bước này")
        return _loc_jlpt(ids)
    ids = _loc_jlpt(status.ids(*default_states))
    if getattr(args, "lo", None):
        ids = ids[: args.lo]
    elif not getattr(args, "tat_ca", False):
        sys.exit("Hãy chọn phạm vi: --pilot, --ids <id1,id2>, --tu <từ mẫu> --den <đến mẫu>, --lo <số câu> hoặc --tat-ca")
    return ids


# ---------------- nhãn cố định của lời giải gốc (bỏ khi đo độ phủ) ----------------
LABELS = [r"(?im)^\s*(cách đọc|nghĩa|sửa lại)\s*:", r"(?m)PHÂN TÍCH\s*[:：]?", r"(?m)LỰA CHỌN ĐÚNG\s*[:：]?", r"#{3,}"]


def strip_labels(text):
    text = re.sub(r"(?im)^\s*cách đọc\s*[:：].*$", " ", text)    # dòng cách đọc là tiếng Nhật (có khi lẫn chữ Latin A/B của hội thoại) – không tính độ phủ tiếng Việt
    for pat in LABELS:
        text = re.sub(pat, " ", text)
    return text


# ---------------- tách lời giải ### thành các phần (giai đoạn 0) ----------------
HEADERS = {"PHÂN TÍCH": "phan_tich", "LỰA CHỌN ĐÚNG": "lua_chon_dung"}
HEADER_RE = re.compile(r"(PHÂN TÍCH|LỰA CHỌN ĐÚNG)\s*[:：]?")      # chữ HOA – không nhầm với "phân tích" trong câu
NUM_LINE_RE = re.compile(r"^\s*\{?\s*([1-4])\s*[\.．]\s*(.*)$")
LAB_RE = re.compile(r"(?i)^\s*(cách đọc|nghĩa|sửa lại|sửa thành)\s*[:：]\s*(.*)$", re.S)  # 'Sửa thành:' = 'Sửa lại:' (19818 lựa chọn 3)
# nhãn dính sau câu tiếng Nhật trên cùng một dòng ('Sửa lại: あついシャワーを浴びています。Cách đọc: …')
GLUE_LAB_RE = re.compile(r"(?<=[぀-ヿ㐀-鿿。．！？」』）)\]}》])[ \t　]*(?=(?:Cách đọc|Nghĩa|Sửa lại)\s*[:：])")
DOTS_RE = re.compile(r"\s*[…‥]{1,}\s*|\s*\.{3,}\s*")


def _eq(a, b):
    """So câu / từ: bỏ furigana, { }, dấu, khoảng trắng."""
    f = lambda s: re.sub(r"[。\.．、,，\s　!！?？「」・’'\"]", "", norm_ja(strip_marks(s or "")).replace("{", "").replace("}", "")).replace("ー", "一")  # noqa: E731
    return bool(f(a)) and f(a) == f(b)


def _eq_doc(a, b):
    """Như _eq, hoặc cùng cách đọc (lời giải viết chữ Hán, đề viết kana: 失礼します ~ しつれいします)."""
    if _eq(a, b):
        return True
    if not _tok():
        return False
    ya, yb = _seion(_yomi(a)), _seion(_yomi(b))
    return bool(ya) and ya == yb


def _doc_furi(s):
    """｜漢字《かな》 → かな (lấy cách đọc của furigana)."""
    return re.sub(r"｜([^《]*)《([^》]*)》", r"\2", s or "")


def de_tu(cau_hoi):
    """Câu hỏi của đề → (từ được hỏi, định nghĩa tiếng Nhật hoặc None). '許す……ある行為を…認める。' → ('許す', 'ある行為を…認める。')."""
    s = (cau_hoi or "").strip()
    m = DOTS_RE.search(s)
    if m and m.start() > 0 and s[m.end():].strip():
        return s[:m.start()].strip(), s[m.end():].strip()
    return s, None


def split_sections(text):
    """Văn bản ### đã chuẩn hóa → {dau, phan_tich, lua_chon_dung, sau_lcd}. Nhận tiêu đề cả khi thiếu ###."""
    t = HEADER_RE.sub(lambda m: "\n###\n" + m.group(1) + "\n", text)
    blocks = [b.strip() for b in re.split(r"#{3,}", t)]
    out = {"dau": None, "phan_tich": None, "lua_chon_dung": None, "sau_lcd": None}
    last = None
    for b in blocks:
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
        elif last == "lua_chon_dung":
            out["sau_lcd"] = b if out["sau_lcd"] is None else out["sau_lcd"] + "\n" + b
        else:
            out[last] = (out[last] or "") + "\n" + b
    return out


WORD_RE = re.compile(r"^\s*(?:Từ\s+)?[\"'“「]?(?P<ja>[぀-ヿ㐀-鿿々〆ー｜《》・～〜]+)[\"'”」]?\s*(?:[（(](?P<paren>[^()（）\n]*)[)）])?\s*(?P<rest>.*)$", re.S)


def word_intro(dau):
    """Đoạn giới thiệu → {ja, paren, con_lai} (con_lai = phần tiếng Việt sau từ + ngoặc, gồm cả các dòng sau)."""
    t = (dau or "").strip()
    m = WORD_RE.match(t)
    if not t or not m or not re.search(r"[぀-ヿ㐀-鿿]", m.group("ja")):
        return {"ja": None, "paren": None, "con_lai": t}
    return {"ja": m.group("ja"), "paren": m.group("paren"), "con_lai": m.group("rest").strip()}


def _split_glued(lines, lua_chon):
    """Tách dòng dính: hai lựa chọn trên một dòng ('…phù hợp hơn.3. 小麦粉…') và nhãn dính sau câu Nhật."""
    out, glued, lab_glued = [], False, False
    for line in lines:
        cut = [0]
        for k in range(1, 5):
            for m in re.finditer(rf"(?<=[^\d\s])\s*({k})\s*[\.．]\s*", line):
                rest = line[m.end():]
                if m.start() > 0 and lua_chon and _eq(GLUE_LAB_RE.split(rest)[0], lua_chon[k - 1]):
                    cut.append(m.start() + (len(m.group(0)) - len(m.group(0).lstrip())))
        cut = sorted(set(cut))
        glued |= len(cut) > 1
        for a_, b_ in zip(cut, cut[1:] + [len(line)]):
            part = line[a_:b_].strip()
            pieces = [p.strip() for p in GLUE_LAB_RE.split(part) if p.strip()]
            lab_glued |= len(pieces) > 1
            out += pieces
    return out, glued, lab_glued


def analysis_items(pt, lua_chon):
    """PHÂN TÍCH → (mo_dau, [ {so, cau, lua_chon_khop, doc, nghia, sua{ja, doc, nghia}|None, nhan_xet, nhan_lap} ], glued, lab_glued)."""
    lines = [x for x in (pt or "").split("\n") if x.strip()]
    lines, glued, lab_glued = _split_glued(lines, lua_chon)
    items, mo_dau = [], []
    for line in lines:
        m = NUM_LINE_RE.match(line)
        if m:
            cau = m.group(2).strip()
            khop = next((j + 1 for j, o in enumerate(lua_chon) if _eq(cau, o)), None) or \
                next((j + 1 for j, o in enumerate(lua_chon) if _eq_doc(cau, o)), None)
            nxt = items[-1]["so"] + 1 if items else 1
            if khop or int(m.group(1)) == nxt:
                items.append({"so": int(m.group(1)), "cau": cau, "lua_chon_khop": khop, "doc": None, "nghia": None,
                              "sua": None, "nhan_xet": "", "nhan_lap": False, "_o": "goc"})
                continue
        if not items:
            mo_dau.append(line)
            continue
        it = items[-1]
        # 2026-10-12: câu gốc xuống dòng giữa câu – dòng kế chỉ có tiếng Nhật, câu chưa kết thúc (53612 lựa chọn 2)
        if (it["_o"] == "goc" and it["doc"] is None and it["nghia"] is None and not it["nhan_xet"] and it["sua"] is None
                and not re.search(r"[。．！？」』.!?]\s*$", it["cau"]) and not LAB_RE.match(line)
                and re.search(r"[぀-ヿ㐀-鿿]", line) and not re.search(r"[A-Za-zÀ-ỹĐđ]", line)):
            it["cau"] += "\n" + line.strip()
            continue
        # 'Sửa lại:' trống, câu sửa ở dòng kế tiếp (18410 lựa chọn 3)
        if it["_o"] == "sua" and it["sua"]["ja"] == "" and it["sua"]["doc"] is None and not LAB_RE.match(line):
            it["sua"]["ja"] = line.strip()
            continue
        lm = LAB_RE.match(line)
        if lm:
            lab, val = lm.group(1).lower(), lm.group(2).strip()
            if lab in ("sửa lại", "sửa thành"):
                if it["sua"] is not None:
                    it["nhan_lap"] = True
                it["sua"], it["_o"] = {"ja": val, "doc": None, "nghia": None}, "sua"
                continue
            key = "doc" if lab == "cách đọc" else "nghia"
            tgt = it["sua"] if it["_o"] == "sua" else it
            if tgt[key] is None:
                tgt[key] = val
                continue
            it["nhan_lap"] = True
        it["nhan_xet"] = (it["nhan_xet"] + "\n" + line).strip()
    for it in items:
        it.pop("_o", None)
    return "\n".join(mo_dau), items, glued, lab_glued


def sua_goc(text):
    """(2026-10-12) Sửa định dạng hỏng của lời giải trước khi tách (gọi trong s0_chuan_bi.prepare). Trả về (text, ghi_chu).
    - nhãn 'Sửa lại' bị gắn furigana rác: '｜sửa《しゅるい》 ｜lại《らい》' (54075)
    - dấu { } (in đậm) bọc trọn cả một dòng, kể cả số thứ tự / nhãn (54146) → bỏ."""
    gc = []
    t2 = re.sub(r"(?i)｜?sửa《[^》]*》\s*｜?lại《[^》]*》", "Sửa lại", text)
    if t2 != text:
        gc.append("[Đã sửa định dạng] Nhãn 'Sửa lại' trong lời giải bị gắn furigana rác ('｜sửa《…》 ｜lại《…》') → 'Sửa lại'")
    out, n = [], 0
    for line in t2.split("\n"):
        s = line.strip()
        m = re.match(r"^\{([^{}]*)\}$", s) or re.match(r"^(Nghĩa\s*[:：]\s*)\{([^{}]*)\}$", s)
        if m:
            line, n = (m.group(1) if m.lastindex == 1 else m.group(1) + m.group(2)), n + 1
        out.append(line)
    if n:
        gc.append(f"[Đã sửa định dạng] {n} dòng lời giải bị đánh dấu {{ }} (in đậm) bọc trọn cả dòng – bỏ đánh dấu")
    return "\n".join(out), gc


def lcd_line(lcd):
    """LỰA CHỌN ĐÚNG → (số, câu, đoạn chữ khác) – dòng đánh số đầu tiên là câu đáp án; không có số thì (None, None, toàn bộ)."""
    lines = [x.strip() for x in (lcd or "").split("\n") if x.strip()]
    k = next((i for i, x in enumerate(lines) if NUM_LINE_RE.match(x)), None)
    if k is None:
        return None, None, "\n".join(lines)
    m = NUM_LINE_RE.match(lines[k])
    return int(m.group(1)), m.group(2).strip(), "\n".join(lines[:k] + lines[k + 1:])


# ---------------- gắn cờ (giai đoạn 0) ----------------
SAI_RE = re.compile(r"(?i)không (phù hợp|đúng|chính xác|tự nhiên|hợp lý|thích hợp)|\bsai\b(?! (lầm|sót))|chưa (phù hợp|đúng|chính xác)")
DUNG_RE = re.compile(r"(?i)(được (sử dụng|dùng) (một cách )?(đúng|chính xác|phù hợp|tự nhiên))|(cách (sử dụng|dùng) (đúng|chính xác))")
FLAG_TEXT = {
    "thieu_gioi_thieu": "Không có đoạn giới thiệu từ trước PHÂN TÍCH (word.meaning / usage = null)",
    "tu_khac_de": "Từ ở đầu đoạn giới thiệu khác từ được hỏi trong đề",
    "bien_the_dinh_nghia": "Đề có định nghĩa tiếng Nhật sau '……' (chọn câu dùng từ đúng NGHĨA đã cho)",
    "dong_pt_dinh_lien": "Các dòng phân tích bị dính liền, cần tách về đúng lựa chọn",
    "nhan_dinh_lien": "Nhãn 'Cách đọc:' / 'Nghĩa:' / 'Sửa lại:' dính sau câu tiếng Nhật trên cùng một dòng",
    "nhan_lap": "Một lựa chọn có 2 dòng 'Cách đọc:' / 'Nghĩa:' / 'Sửa lại:' cho cùng một câu",
    "so_dong_pt_khac_4": "Phần PHÂN TÍCH không có đúng 4 câu đánh số",
    "thu_tu_pt_lech": "Số thứ tự trong PHÂN TÍCH không khớp thứ tự lựa chọn của đề",
    "cau_khac_de": "Câu của lựa chọn trong lời giải khác câu của đề",
    "lech_dap_an": "Số trong LỰA CHỌN ĐÚNG khác dap_an_so của đề",
    "khong_so_lcd": "LỰA CHỌN ĐÚNG không có số thứ tự",
    "lcd_co_nhan_xet": "LỰA CHỌN ĐÚNG có thêm đoạn nhận xét ngoài câu đáp án (→ correct.note)",
    "thieu_phan_tich": "Thiếu phần PHÂN TÍCH",
    "thieu_lua_chon_dung": "Thiếu phần LỰA CHỌN ĐÚNG",
    "co_doan_sau_lcd": "Có đoạn không tiêu đề sau LỰA CHỌN ĐÚNG",
    "thieu_dau_phan_cach": "Tiêu đề phần dính vào phần trước (thiếu ###)",
    "co_mo_dau": "PHÂN TÍCH có đoạn mở đầu trước câu 1 (→ analysis.intro)",
    "thieu_sua_lai": "Có lựa chọn sai (không phải đáp án) mà không có dòng 'Sửa lại:' (đề thường)",
    "dap_an_co_sua_lai": "Đáp án đúng lại có dòng 'Sửa lại:'",
    "de_gach_chan": "Đề có gạch chân / { } ở từ được hỏi",
    "danh_dau_rac": "Bản gốc có đoạn in đậm / gạch chân rỗng hoặc chỉ là dấu câu (đã bỏ thẻ)",
    "co_furigana": "Có furigana",
    "ruby_hong": "Có ruby hỏng trong bản gốc",
    "ky_hieu_trung": "Bản gốc có sẵn ký hiệu ｜《》 (trùng ký hiệu furigana)",
}
CTV_FLAGS = ("dong_pt_dinh_lien", "thu_tu_pt_lech", "lech_dap_an", "danh_dau_rac")
FURI_SKIP = [("correct", "sentence_ja")]      # bản sao của options[i].sentence.ja


def parse_and_flag(text, raw_html, lua_chon, dap_an_so, de_html):
    """Tách phần + gắn cờ + ghi chú bản gốc. Trả về (phan, co, ghi_chu). de_html = câu hỏi + 4 lựa chọn (HTML gốc)."""
    sec = split_sections(text)
    w = word_intro(sec["dau"])
    mo, items, glued, lab_glued = analysis_items(sec["phan_tich"], lua_chon)
    so_lcd, cau_lcd, lcd_note = lcd_line(sec["lua_chon_dung"])
    co, gc = [], []
    from pipeline_chung.normalize import normalize_html
    cau_hoi = normalize_html((de_html or "").split("\x00")[0])[0].replace("{", "").replace("}", "")
    tu, dinh_nghia = de_tu(cau_hoi)
    if dinh_nghia:
        co.append("bien_the_dinh_nghia")
    if not (sec["dau"] or "").strip():
        co.append("thieu_gioi_thieu")
        gc.append("[Bản gốc VI] Không có đoạn giới thiệu từ trước PHÂN TÍCH")
    elif w["ja"] and not any(_eq_doc(x, y) for x in (w["ja"], _doc_furi(w["ja"]), w["paren"] or "") for y in (tu, _doc_furi(tu))):
        co.append("tu_khac_de")
    if glued:
        co.append("dong_pt_dinh_lien")
    if lab_glued:
        co.append("nhan_dinh_lien")
    if any(it["nhan_lap"] for it in items):
        co.append("nhan_lap")
    if sec["phan_tich"] is not None and len(items) != 4:
        co.append("so_dong_pt_khac_4")
    if any(it["lua_chon_khop"] and it["lua_chon_khop"] != it["so"] for it in items):
        co.append("thu_tu_pt_lech")
        gc.append("[Bản gốc VI] Số thứ tự trong PHÂN TÍCH không khớp thứ tự lựa chọn của đề")
    if any(not it["lua_chon_khop"] for it in items):
        co.append("cau_khac_de")
        for it in items:
            if not it["lua_chon_khop"] and 1 <= it["so"] <= 4:
                gc.append(f"[Bản gốc VI] Câu {it['so']} trong PHÂN TÍCH khác đề: '{strip_marks(it['cau'])}' ↔ đề '{lua_chon[it['so'] - 1]}'")
    for k, name in (("phan_tich", "PHÂN TÍCH"), ("lua_chon_dung", "LỰA CHỌN ĐÚNG")):
        if not (sec[k] or "").strip():
            co.append("thieu_" + k)
            gc.append(f"[Bản gốc VI] Thiếu phần {name}")
    if sec["sau_lcd"]:
        co.append("co_doan_sau_lcd")
    if lcd_note.strip():
        co.append("lcd_co_nhan_xet")
        gc.append("[Bản gốc VI] LỰA CHỌN ĐÚNG có thêm đoạn nhận xét (→ correct.note)")
    if sec["lua_chon_dung"] and so_lcd is None:
        co.append("khong_so_lcd")
    elif so_lcd is not None and str(so_lcd) != str(dap_an_so):
        co.append("lech_dap_an")
        gc.append(f"[Bản gốc VI] LỰA CHỌN ĐÚNG ghi {so_lcd}, khác đáp án của đề (dap_an_so = {dap_an_so})")
    if re.search(r"[^\n#\s]\s*(?:PHÂN TÍCH|LỰA CHỌN ĐÚNG)", re.sub(r"<[^>]+>", "", raw_html or "")):
        co.append("thieu_dau_phan_cach")
    if mo.strip():
        co.append("co_mo_dau")
    for it in items:
        j = it["lua_chon_khop"] or it["so"]
        if str(j) == str(dap_an_so):
            if it["sua"] is not None:
                co.append("dap_an_co_sua_lai")
        elif it["sua"] is None and not dinh_nghia:
            co.append("thieu_sua_lai")
    if re.search(r"<u\b|underline|｛|\{", de_html or "", re.I):
        co.append("de_gach_chan")
    phan = {"dau": sec["dau"], "tu": w, "de_tu": tu, "dinh_nghia": dinh_nghia,
            "phan_tich": {"mo_dau": mo, "dong": items}, "lua_chon_dung": sec["lua_chon_dung"], "lcd": [so_lcd, cau_lcd, lcd_note],
            "sau_lcd": sec["sau_lcd"]}
    return phan, sorted(set(co)), gc


def text_without_lcd(text):
    """Văn bản lời giải bỏ dòng câu đáp án trong LỰA CHỌN ĐÚNG (bản lặp của câu lựa chọn – không tính khi so độ phủ / furigana / { }),
    giữ đoạn chữ khác của phần đó (→ correct.note)."""
    sec = split_sections(text)
    note = lcd_line(sec["lua_chon_dung"])[2]
    return "\n".join(x for x in (sec["dau"], sec["phan_tich"], note, sec["sau_lcd"]) if x)


# ---------------- kiểm tra riêng giai đoạn 1: K1–K17 ----------------
READING_OK = re.compile(r"^[぀-ゟ゠-ヿー・\s/、,，。．！？!?「」『』（）()0-9０-９~〜…\-－―]+$")


def _segs(s):
    from pipeline_chung.normalize import mark_segments
    return mark_segments(s)


def _v(o):
    return (o or {}).get("vi") if o else None


def opt_text(o):
    """Toàn bộ chữ tiếng Việt của một lựa chọn: nghĩa câu + nhận xét + nghĩa câu sửa."""
    s, c = o.get("sentence") or {}, o.get("correction") or {}
    return "\n".join(x for x in (_v(s.get("meaning")), _v(o.get("analysis")), _v(c.get("meaning"))) if x)


def _k(t):
    return re.sub(r"[\s　]", "", norm_ja(t or ""))


def check_k(doc, norm, policy):
    from pipeline_chung.common import vi_words
    loi, canh_bao = [], []
    de, phan = norm["de"], norm.get("phan") or {}
    an, wd, c = doc.get("analysis") or {}, doc.get("word") or {}, doc.get("correct") or {}
    opts = an.get("options") or []
    dap = int(de["dap_an_so"]) if str(de["dap_an_so"]).isdigit() else None
    # K1
    if [o.get("index") for o in opts] != [1, 2, 3, 4]:
        loi.append(f"K1: analysis.options phải có đủ 4 lựa chọn theo thứ tự 1–4 (đang có {[o.get('index') for o in opts]})")
    src = {}
    for it in (phan.get("phan_tich") or {}).get("dong", []):
        src.setdefault(it["lua_chon_khop"] or it["so"], it)
    for o in opts:
        i = o.get("index")
        s, cr, it = o.get("sentence") or {}, o.get("correction"), src.get(o.get("index"))
        if not isinstance(i, int) or not 1 <= i <= 4:
            continue
        # K2 – câu chép đúng dòng 'i. <câu>' của lời giải
        if it is not None and _k(s.get("ja")) != _k(it["cau"]):
            loi.append(f"K2: lựa chọn {i}: sentence.ja '{s.get('ja')}' khác dòng câu của lời giải '{it['cau']}'")
        elif it is None and not _eq(s.get("ja"), de["lua_chon"][i - 1]):
            loi.append(f"K2: lựa chọn {i}: lời giải không có câu này – sentence.ja phải chép đúng câu của đề '{de['lua_chon'][i - 1]}'")
        if it is not None:
            # K5 – { } đúng như dòng câu của lời giải
            if _segs(s.get("ja") or "") != _segs(it["cau"]):
                loi.append(f"K5: lựa chọn {i}: đánh dấu {{ }} của sentence.ja {_segs(s.get('ja') or '')} khác lời giải {_segs(it['cau'])}")
            # K8 – cách đọc / nghĩa của câu gốc
            for key, name in (("doc", "reading"), ("nghia", "meaning")):
                got = s.get(name)
                if (it[key] is None) != (got is None):
                    loi.append(f"K8: lựa chọn {i}: sentence.{name} phải null khi và chỉ khi lời giải không có dòng "
                               f"'{'Cách đọc' if key == 'doc' else 'Nghĩa'}:' của câu gốc (trước 'Sửa lại:')")
            if it["doc"] is not None and s.get("reading") is not None and _k(s["reading"]) != _k(it["doc"]):
                loi.append(f"K8: lựa chọn {i}: sentence.reading khác dòng 'Cách đọc:' của lời giải")
            # K7 – câu sửa
            if (it["sua"] is None) != (cr is None):
                loi.append(f"K7: lựa chọn {i}: correction phải null khi và chỉ khi lời giải không có dòng 'Sửa lại:'")
            elif cr is not None:
                if _k(cr.get("ja")) != _k(it["sua"]["ja"]):
                    loi.append(f"K7: lựa chọn {i}: correction.ja khác dòng 'Sửa lại:' của lời giải '{it['sua']['ja']}'")
                for key, name in (("doc", "reading"), ("nghia", "meaning")):
                    if (it["sua"][key] is None) != (cr.get(name) is None):
                        loi.append(f"K7: lựa chọn {i}: correction.{name} phải null khi và chỉ khi không có dòng "
                                   f"'{'Cách đọc' if key == 'doc' else 'Nghĩa'}:' sau 'Sửa lại:'")
                if it["sua"]["doc"] is not None and cr.get("reading") is not None and _k(cr["reading"]) != _k(it["sua"]["doc"]):
                    loi.append(f"K7: lựa chọn {i}: correction.reading khác dòng 'Cách đọc:' sau 'Sửa lại:'")
                if _eq(cr.get("ja"), s.get("ja")):
                    canh_bao.append(f"K17: lựa chọn {i}: câu sửa giống hệt câu gốc")
            # K3 / K9 – nhận xét: đủ chữ, không null khi bản gốc có
            if it["nhan_xet"].strip() and o.get("analysis") is None:
                loi.append(f"K3: lựa chọn {i}: bản gốc có nhận xét nhưng analysis = null")
            srcw = collections.Counter(vi_words("\n".join(x for x in (it["nghia"], it["nhan_xet"], (it["sua"] or {}).get("nghia")) if x)))
            outw = collections.Counter(vi_words(opt_text(o)))
            if srcw and sum((srcw & outw).values()) / sum(srcw.values()) < 0.97 and "dong_pt_dinh_lien" not in norm["co"]:
                loi.append(f"K9: lựa chọn {i}: thiếu chữ so với bản gốc: {[w for w, _ in (srcw - outw).most_common(8)]}")
        for name, val in (("sentence.reading", s.get("reading")), ("correction.reading", (cr or {}).get("reading"))):
            if val and not READING_OK.match(strip_marks(val).replace("{", "").replace("}", "")):
                canh_bao.append(f"K8: lựa chọn {i}: {name} có ký tự không phải kana – xem lại (lời giải có thể ghi chữ Hán)")
        # K14 – is_correct
        if o.get("is_correct") is not (i == dap):
            loi.append(f"K14: lựa chọn {i}: is_correct phải là {i == dap} (đáp án của đề = {dap})")
        # K15 / K16 – usage_ok
        uo = o.get("usage_ok")
        if i == dap and uo is False:
            canh_bao.append(f"K16: đáp án (lựa chọn {i}) bị lời giải nói dùng từ SAI – nghi lỗi nội dung")
        if i != dap and uo is True and not phan.get("dinh_nghia"):
            canh_bao.append(f"K15: lựa chọn {i} (không phải đáp án, đề thường) bị lời giải nói dùng từ ĐÚNG – xem lý do loại (quy tắc 3d-3)")
        if i != dap and phan.get("dinh_nghia") and cr is not None:
            canh_bao.append(f"K16: đề có định nghĩa – lựa chọn {i} có 'Sửa lại:' – xem câu gốc có thật sự sai không (quy tắc 3d-2)")
        txt = strip_marks(_v(o.get("analysis")) or "")
        if uo is True and SAI_RE.search(txt) and not DUNG_RE.search(txt):
            canh_bao.append(f"K15: lựa chọn {i}: usage_ok = true nhưng nhận xét chỉ thấy ý 'không phù hợp / sai' – xem lại")
        if uo is False and DUNG_RE.search(txt) and not SAI_RE.search(txt):
            canh_bao.append(f"K15: lựa chọn {i}: usage_ok = false nhưng nhận xét nói 'được dùng đúng' – xem lại")
    # K6 – đáp án
    if str(c.get("index")) != str(de["dap_an_so"]):
        loi.append(f"K6: correct.index = {c.get('index')} khác dap_an_so = {de['dap_an_so']}")
    elif {"lech_dap_an", "khong_so_lcd"} & set(norm["co"]):
        canh_bao.append(f"K6: lời giải gốc ghi đáp án khác đề / không ghi số – JSON đã theo dap_an_so = {de['dap_an_so']}")
    di = c.get("index")
    if isinstance(di, int) and 1 <= di <= len(opts) and c.get("sentence_ja") != (opts[di - 1].get("sentence") or {}).get("ja"):
        loi.append(f"K6: correct.sentence_ja phải giống hệt options[{di - 1}].sentence.ja")
    # K13 – đoạn chữ khác trong LỰA CHỌN ĐÚNG
    lcd_note = ((phan.get("lcd") or [None, None, ""]) + [""])[2] or ""
    if bool(lcd_note.strip()) != (c.get("note") is not None):
        loi.append("K13: correct.note phải null khi và chỉ khi LỰA CHỌN ĐÚNG không có đoạn chữ nào ngoài dòng câu đáp án")
    elif lcd_note.strip():
        cs_, co2 = collections.Counter(vi_words(lcd_note)), collections.Counter(vi_words(_v(c.get("note")) or ""))
        if cs_ and sum((cs_ & co2).values()) / sum(cs_.values()) < 0.97:
            loi.append(f"K13: correct.note thiếu chữ so với bản gốc: {[x for x, _ in (cs_ - co2).most_common(8)]}")
    # K11 – từ, định nghĩa
    w = phan.get("tu") or {}
    # 2026-10-12 (phần E đợt 1, điều phối chỉnh): so token đầu, bỏ furigana nhưng GIỮ chữ gốc ('もと ｜元《もと》' ↔ 'もと'; ｜元《もと》 ≠ ｜本《もと》)
    _kf = lambda t: _k(re.sub(r"《[^》]*》|｜", "", ((t or "").split() or [""])[0]))  # noqa: E731
    if w.get("ja") and _kf(wd.get("ja")) != _kf(w["ja"]):
        loi.append(f"K11: word.ja '{wd.get('ja')}' khác từ ở đầu đoạn giới thiệu '{w['ja']}'")
    if (w.get("paren") or None) != (wd.get("paren") or None) and not (w.get("paren") and wd.get("paren") and _k(w["paren"]) == _k(wd["paren"])):
        loi.append(f"K11: word.paren '{wd.get('paren')}' phải chép đúng ngoặc sau từ ở đoạn giới thiệu: '{w.get('paren')}'")
    dn = phan.get("dinh_nghia")
    if (dn is None) != (wd.get("definition_ja") is None):
        loi.append("K11: word.definition_ja phải null khi và chỉ khi câu hỏi của đề không có định nghĩa sau '……'")
    elif dn and _k(wd.get("definition_ja")) != _k(dn):
        loi.append(f"K11: word.definition_ja khác định nghĩa trong đề '{dn}'")
    # K12 – đoạn giới thiệu đủ chữ
    con_lai = w.get("con_lai") or ""
    if con_lai.strip() and wd.get("meaning") is None and wd.get("usage") is None:
        loi.append("K12: bản gốc có đoạn giới thiệu nhưng word.meaning và word.usage đều null")
    cs = collections.Counter(vi_words(con_lai))
    co_ = collections.Counter(vi_words("\n".join(x for x in (_v(wd.get("meaning")), _v(wd.get("usage"))) if x)))
    if cs and sum((cs & co_).values()) / sum(cs.values()) < 0.97:
        loi.append(f"K12: word.meaning + word.usage thiếu chữ so với đoạn giới thiệu: {[x for x, _ in (cs - co_).most_common(8)]}")
    # K10 – mở đầu / kết luận
    if ("co_mo_dau" in norm["co"]) != (an.get("intro") is not None):
        canh_bao.append(f"K10: analysis.intro: bản gốc {'có' if 'co_mo_dau' in norm['co'] else 'không có'} đoạn mở đầu nhưng JSON "
                        f"{'null' if an.get('intro') is None else 'có'}")
    if an.get("conclusion") is not None:
        canh_bao.append("K10: analysis.conclusion khác null – dạng 06 thường không có đoạn kết luận, xem lại có lấy nhầm nhận xét của lựa chọn 4 không")
    return loi, canh_bao


# ---------------- kiểm tra riêng giai đoạn 2: D1 (D3 nằm trong kiểm tra chung, D4 tổng hợp nhiều câu) ----------------
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
    return "analysis" in path or "usage" in path


# ---------------- hiển thị cho Excel CTV (dựng lại đúng thứ tự format) ----------------
def _t(obj, lang):
    return show((obj or {}).get(lang) or "") if obj else ""


def render(d, lang):
    w, an, c = d.get("word") or {}, d.get("analysis") or {}, d.get("correct") or {}
    head = show(w.get("ja", "")) + (f" ({show(w['paren'])})" if w.get("paren") else "")
    mean = _t(w.get("meaning"), lang)
    sep = "" if re.match(r"^(는|은)\s", mean) else " "          # bản Hàn: trợ từ 는/은 viết liền sau từ / ngoặc
    out = [f"{bold('【Từ】')} {head}{sep}{mean}".rstrip()]
    if w.get("usage"):
        out.append(_t(w["usage"], lang))
    if w.get("definition_ja"):
        out.append(f"{bold('【Định nghĩa trong đề】')} {show(w['definition_ja'])}")
    out.append(bold("【PHÂN TÍCH】"))
    if an.get("intro"):
        out.append(_t(an["intro"], lang))
    for o in an.get("options", []):
        s, cr = o.get("sentence") or {}, o.get("correction")
        out.append(bold(f"{o.get('index')}. ") + show(s.get("ja", "")))
        if s.get("reading"):
            out.append(f"   Cách đọc: {show(s['reading'])}")
        if s.get("meaning"):
            out.append(f"   Nghĩa: {_t(s['meaning'], lang)}")
        if o.get("analysis"):
            out.append("   " + _t(o["analysis"], lang).replace("\n", "\n   "))
        if cr:
            out.append(f"   {bold('Sửa lại:')} {show(cr.get('ja', ''))}")
            if cr.get("reading"):
                out.append(f"   Cách đọc: {show(cr['reading'])}")
            if cr.get("meaning"):
                out.append(f"   Nghĩa: {_t(cr['meaning'], lang)}")
    if an.get("conclusion"):
        out.append(_t(an["conclusion"], lang))
    out.append(bold("【LỰA CHỌN ĐÚNG】"))
    if c.get("note"):
        out.append(_t(c["note"], lang))
    out.append(f"{c.get('index')}. {show(c.get('sentence_ja', ''))}")
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


# ---------------- Dạng 06: gợi ý từ điển SudachiPy (R1, R2) – chỉ GỢI Ý cho Claude, không quyết định trạng thái ----------------
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


def sudachi_hints(norm):
    """Gợi ý cho bước 1.2 (Claude xác nhận rồi mới gắn cờ):
    R1 – dòng 'Cách đọc:' (câu gốc / câu sửa) khác cách đọc từ điển của câu tiếng Nhật;
    R2 – câu 'Sửa lại' không thay đổi ở chỗ có từ được hỏi (sửa chỗ khác của câu) hoặc giống hệt câu gốc."""
    if not norm.get("phan"):
        return []
    ph = norm["phan"]
    items = (ph.get("phan_tich") or {}).get("dong") or []
    out = []
    loi = _tu_loi(ph.get("de_tu") or "")
    for it in items:
        so = it["lua_chon_khop"] or it["so"]
        if _tok():
            for ten, ja, doc in (("câu", it["cau"], it["doc"]), ("câu sửa", (it["sua"] or {}).get("ja"), (it["sua"] or {}).get("doc"))):
                if not ja or not doc or re.search(r"[㐀-鿿]", strip_marks(doc)):
                    continue
                if re.search(r"[0-9０-９A-Za-zＡ-Ｚａ-ｚ]", strip_marks(ja) + doc):
                    continue                      # số / chữ Latin: từ điển đọc khác cách ghi của lời giải (17 → じゅうなな) – bỏ qua
                y, d = _seion(_yomi(ja)), _seion(_yomi_kana(doc))
                if y and d and y != d:
                    diff = _khac(y, d)
                    if sum(len(a) + len(b) for a, b in diff) < 2:
                        continue
                    if sum(len(a) + len(b) for a, b in diff) <= 12:
                        out.append(f"R1: lựa chọn {so} – cách đọc {ten} lệch từ điển ở: " + "; ".join(f"'{a}'→'{b}'" for a, b in diff[:3]))
                    elif diff:
                        out.append(f"R1: lựa chọn {so} – cách đọc {ten} lệch nhiều so với câu tiếng Nhật (xem lại cả dòng)")
        if it["sua"] and loi:
            a, b = strip_marks(it["cau"]).replace("{", "").replace("}", ""), strip_marks(it["sua"]["ja"]).replace("{", "").replace("}", "")
            if _eq(a, b):
                out.append(f"R2: lựa chọn {so} – câu 'Sửa lại' giống hệt câu gốc")
                continue
            import difflib
            sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
            pos = [m.start() for m in re.finditer(re.escape(loi), a)]
            def cham(i1, i2, p):            # đoạn sửa [i1, i2) có chạm vào từ đang hỏi [p, p+len) không (chèn sát bên cạnh thì không tính)
                han = bool(re.fullmatch(r"[㐀-鿿々]+", loi))     # từ chữ Hán: đổi okurigana ngay sau chữ Hán (汚し→汚れ, 著しい→著名な) vẫn là đổi từ
                if i1 == i2:
                    return p < i1 < p + len(loi) or (han and i1 == p + len(loi))
                return i1 < p + len(loi) + (1 if han else 0) and i2 > p
            sua_tu = any(op != "equal" and any(cham(i1, i2, p) for p in pos) for op, i1, i2, j1, j2 in sm.get_opcodes())
            if pos and not sua_tu:
                ch = "; ".join(f"'{x}'→'{y}'" for x, y in _khac(a, b)[:3])
                out.append(f"R2: lựa chọn {so} – câu 'Sửa lại' giữ nguyên '{loi}', chỉ đổi chỗ khác: {ch}")
    return out
