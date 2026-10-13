"""Phần riêng của dạng 08 – Ngữ pháp: Lắp ghép câu (dựng 2026-10-08 từ dạng 07).

Phần chung kế thừa dạng 07 (cấu hình, đường dẫn, thứ tự chạy --tu/--den, kho đã duyệt, bản tạo Claude, Sudachi, Hán Việt, gợi ý định dạng).
Phần riêng 08 ở cuối file: tách 4 phần lời giải (PHÂN TÍCH ĐỀ BÀI / PHÂN TÍCH CÁC LỰA CHỌN / CÁCH SẮP XẾP HỢP LÝ NHẤT / LỰA CHỌN ĐÚNG),
GHÉP CÂU tự động (thử mọi thứ tự 4 lựa chọn so với 'Câu hoàn chỉnh' → thứ tự đúng, ô ★ = đáp án), ghép cách đọc câu hoàn chỉnh khi thiếu,
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
    os.environ["PIPELINE_DATA"] = _c.get("du_lieu_test", "data/test_08_ngu_phap_lap_ghep_cau.csv")


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
import pipeline_chung.tham_khao as TK  # noqa: E402  (quy tắc THAM KHẢO 2026-10-07)


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
    if lo_ids:   # (2026-10-13) lô giao theo danh sách id – khoảng chứa cả mẫu cũ không được chạy lại
        sys.exit(f"[Song song] Lô {TU}–{DEN} được giao theo DANH SÁCH ID (đợt {lo_ids[0].get('dot')}) – chạy bằng "
                 f"--ids {','.join(lo_ids[0]['ids'])}  (không dùng --tu/--den: khoảng này có mẫu cũ không được chạy lại).")
    if not any(x.get("tu") == TU and x.get("den") == DEN for x in lo):
        sys.exit(f"[Song song] Khoảng --tu {TU} --den {DEN} không phải một lô trong phan_cong.json (xem PHAN_CONG.md). "
                 "Chỉ chạy lô được giao; cuộc điều phối cần chạy khoảng khác thì thêm --ngoai-phan-cong.")


_lay_khoa()
_kiem_phan_cong()


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
# ================  DẠNG 08 – LẮP GHÉP CÂU: phần riêng (dựng 2026-10-08)  ============================
# =====================================================================================================
# Lời giải gốc (### ngăn phần, tiêu đề in đậm → { } sau chuẩn hóa – Python bỏ { } quanh tiêu đề / nhãn):
#   Đề bài: <câu có ＿ ＿ ★ ＿>  /  Cách đọc: …  /  Nghĩa: …
#   PHÂN TÍCH ĐỀ BÀI (hoặc PHÂN TÍCH CẤU TRÚC CÂU)   - ý 1 / - ý 2 …              → sentence_analysis[]
#   PHÂN TÍCH CÁC LỰA CHỌN   i. <lựa chọn> (<cách đọc> - <nghĩa>)                 → options[i].option_ja / gloss
#                            - Ngữ pháp: …                                         → options[i].grammar
#                            - Khả năng sắp xếp: …                                 → options[i].arrangement
#   CÁCH SẮP XẾP HỢP LÝ NHẤT  các cụm '…' → '…'                                    → arrangement.explanation[]
#                            Câu hoàn chỉnh / Cách đọc / Nghĩa                     → arrangement.full_sentence
#                            Vị trí ★: <lựa chọn>                                  → (đối chiếu correct.option_ja)
#   LỰA CHỌN ĐÚNG            i. <lựa chọn>                                         → correct.index / option_ja

SLOT_RE = re.compile(r"[＿_]+|★|＊")                 # một ô trống (kể cả ô ★)
BLANK_RE = SLOT_RE                                    # tương thích tên cũ (đếm ô trống trong nghĩa câu đề)
SAO_RE = re.compile(r"★|＊")

HEADERS = {"PHÂN TÍCH ĐỀ BÀI": "de_bai", "PHÂN TÍCH CẤU TRÚC CÂU": "de_bai", "PHÂN TÍCH CÁC LỰA CHỌN": "lua_chon",
           "CÁCH SẮP XẾP HỢP LÝ NHẤT": "sap_xep", "LỰA CHỌN ĐÚNG": "lua_chon_dung",
           "THÔNG TIN THAM KHẢO": "tham_khao", "NGỮ PHÁP THAM KHẢO": "tham_khao"}
_HNAMES = "|".join(sorted(HEADERS, key=len, reverse=True))
HEADER_RE = re.compile(r"\{?[ \t]*(" + _HNAMES + r")[ \t]*[:：]?[ \t]*\}?")
OPT_HEAD_RE = re.compile(r"^\s*\{?\s*([1-4])\s*\}?\s*[\.．]\s*(.+)$")
LCD_NUM_RE = re.compile(r"^\s*\{?\s*(\d)\s*\}?\s*[\.．]\s*(.*)$")
OPT_LAB_RE = re.compile(r"(?i)^\s*[-+•]?\s*\{?\s*(ngữ pháp|khả năng sắp xếp)\s*\}?\s*(?:[:：]\s*(.*)|()\s*)$", re.S)   # nhãn thiếu ':' đứng riêng dòng (17187)
SX_LAB_RE = re.compile(r"(?i)^\s*[-+•]?\s*\{?\s*(câu hoàn chỉnh(?:\s*\d)?|cách đọc|nghĩa|vị trí\s*★)\s*\}?\s*[:：]\s*(.*)$", re.S)
NHAN_DAM_RE = re.compile(r"\{\s*((?:" + _HNAMES + r"|ĐỀ BÀI|Đề bài)\s*[:：]?)\s*\}")

LABELS = [r"(?im)^\s*[-+•]?\s*(đề bài|nghĩa|ngữ pháp|khả năng sắp xếp|câu hoàn chỉnh(?:\s*\d)?)\s*[:：]",
          r"(?m)(" + _HNAMES + r")\s*[:：]?", r"#{3,}",
          r"(?<![A-Za-zÀ-ỹ])[ABab](?=\s*[:：「『'\"])"]   # 2026-10-13: chữ A/B người nói (17314)


TACH_SX_RE = re.compile(r"(?<=[.。．!?！？)）'’」])[ \t　]*(?=(?:Câu hoàn chỉnh(?:\s*\d)?|Vị trí\s*★)\s*[:：])")


def tach_dong_sap_xep(text):
    """'…(đã đi qua).Câu hoàn chỉnh: …' (nhãn dính cuối dòng giải thích – 11100) → xuống dòng trước nhãn. Trả (text, số chỗ)."""
    return TACH_SX_RE.subn("\n", text)


def bo_dam_nhan(text):
    """Bỏ { } (in đậm) quanh tiêu đề phần / nhãn 'Đề bài' – định dạng trình bày, không phải nội dung. Trả (text, số chỗ)."""
    return NHAN_DAM_RE.subn(r"\1", text)


def strip_labels(text):
    """Bỏ nhãn cố định + các dòng tiếng Nhật thuần (Cách đọc, Vị trí ★) khi đo độ phủ chữ tiếng Việt."""
    text = re.sub(r"(?im)^\s*[-+•]?\s*(cách đọc|vị trí\s*★)\s*[:：].*$", " ", text)
    for pat in LABELS:
        text = re.sub(pat, " ", text)
    return text


# ---------------- so sánh câu tiếng Nhật ----------------
def _f(s):
    """Chuẩn hóa để ghép / so câu: bỏ furigana, { }, ô trống, ★, dấu câu, khoảng trắng."""
    s = strip_marks(s or "").replace("{", "").replace("}", "")
    s = re.sub(r"[(（][぀-ゟ゠-ヿー]+[)）]", "", s)          # cách đọc trong ngoặc ở đề: 一ヶ月(げつ)
    s = norm_ja(s)
    return re.sub(r"[。\.．、,，\s　!！?？「」『』｢｣｡・’'\"…:：★＊_＿~〜]", "", s).replace("ー", "一")


def _doc_furi(s):
    return re.sub(r"｜([^《]*)《([^》]*)》", r"\2", s or "")


def _eq(a, b):
    return bool(_f(a)) and _f(a) == _f(b)


def _eq_doc(a, b):
    if _eq(a, b):
        return True
    if not _tok():
        return False
    ya, yb = _yomi(a), _yomi(b)
    return bool(ya) and ya == yb


# ---------------- tách phần ----------------
def split_sections(text):
    """→ {dau, de_bai, lua_chon, sap_xep, lua_chon_dung, sau_lcd, tham_khao, ten_de_bai, lap}."""
    t = HEADER_RE.sub(lambda m: "\n###\n" + m.group(1) + "\n", text)
    blocks = [b.strip() for b in re.split(r"#{3,}", t)]
    out = {"dau": None, "de_bai": None, "lua_chon": None, "sap_xep": None, "lua_chon_dung": None, "sau_lcd": None,
           "tham_khao": None, "ten_de_bai": None, "lap": [], "co_tieu_de": False}
    last, seen = None, []
    for b in blocks:
        m = HEADER_RE.match(b)
        if m and m.start() == 0:
            out["co_tieu_de"] = True
            key = HEADERS[m.group(1)]
            if key == "de_bai":
                out["ten_de_bai"] = m.group(1)
            if key in seen and key != "tham_khao":
                out["lap"].append(m.group(1))
            seen.append(key)
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


def text_without_ref(text):
    """Quy tắc THAM KHẢO: bỏ phần THÔNG TIN / NGỮ PHÁP THAM KHẢO khỏi đầu vào của tác tử TẠO và chuẩn kiểm tra."""
    m = re.search(r"(?m)^[ \t]*(?:###[ \t]*\n[ \t]*)?\{?[ \t]*(?:THÔNG TIN THAM KHẢO|NGỮ PHÁP THAM KHẢO)", text)
    if not m:
        return text
    # phần tham khảo kéo đến tiêu đề phần kế tiếp (nếu có) hoặc hết bài
    rest = text[m.end():]
    n = HEADER_RE.search(rest)
    nxt = None
    while n:
        if HEADERS[n.group(1)] != "tham_khao":
            nxt = n
            break
        n = HEADER_RE.search(rest, n.end())
    tail = ("\n###\n" + rest[nxt.start():]) if nxt else ""
    return (text[:m.start()].rstrip("#\n \t") + tail).strip()


def bullet_items(body):
    """Các ý gạch đầu dòng ('- …' / '• …' / '+ …'); dòng không gạch đầu nối vào ý trước. Không có gạch đầu → mỗi dòng một ý."""
    lines = [x.strip() for x in (body or "").split("\n") if x.strip()]
    if not lines:
        return []
    if not any(re.match(r"^[-•+・]\s*", x) for x in lines):
        return lines
    out = []
    for x in lines:
        m = re.match(r"^[-•+・]\s*(.*)$", x)
        if m or not out:
            out.append(m.group(1) if m else x)
        else:
            out[-1] += "\n" + x
    return out


def _khop_lua_chon(rest, lua_chon):
    """Dòng tiêu đề 'X (cách đọc - nghĩa)' → (số lựa chọn khớp, phần chữ Nhật, phần trong ngoặc / phần còn lại)."""
    rest = rest.strip()
    best = None
    for j, o in enumerate(lua_chon):
        fo = _f(o)
        if not fo:
            continue
        # lấy tiền tố dài nhất của rest mà _f(tiền tố) == _f(o)
        for k in range(len(rest), 0, -1):
            if _f(rest[:k]) == fo and (best is None or k > best[1]):
                # 'X (cách đọc)' – _f bỏ cách đọc trong ngoặc nên tiền tố dài nhất nuốt cả ngoặc → cắt ngoặc ra làm gloss (8416)
                m2 = re.match(r"^(.*?\S)\s+[（(][^()（）]*[)）]\s*$", rest[:k], re.S)
                if m2 and not re.search(r"[（(]", o) and _f(m2.group(1)) == fo:
                    k = len(m2.group(1))
                best = (j + 1, k)
                break
    m = re.match(r"^(.*?)\s*[（(](.*)[)）]\s*$", rest, re.S)
    if best:
        ja, du = rest[:best[1]].strip(), rest[best[1]:].strip()
    elif m:
        ja, du = m.group(1).strip(), "(" + m.group(2) + ")"
    else:
        ja, du = rest, ""
    gloss = du
    mm = re.match(r"^[（(](.*)[)）]$", du, re.S)
    if mm:
        gloss = mm.group(1).strip()
    return (best[0] if best else None), ja, (gloss or None)


def option_items(body, lua_chon):
    """PHÂN TÍCH CÁC LỰA CHỌN → (mo_dau, [item]). item = {so, lua_chon, lua_chon_khop, gloss, ngu_phap, sap_xep, khac, nhan_lap}."""
    items, mo_dau, cur = [], [], None
    for line in [x for x in (body or "").split("\n") if x.strip()]:
        m = OPT_HEAD_RE.match(line)
        if m:
            so = int(m.group(1))
            khop, ja, gl = _khop_lua_chon(m.group(2), lua_chon)
            nxt = items[-1]["so"] + 1 if items else 1
            if khop or so == nxt:
                items.append({"so": so, "lua_chon": ja, "lua_chon_khop": khop, "gloss": gl, "dong_tieu_de": m.group(2).strip(),
                              "ngu_phap": None, "sap_xep": None, "khac": None, "nhan_lap": False})
                cur = None
                continue
        if not items:
            mo_dau.append(line.strip())
            continue
        it = items[-1]
        lm = OPT_LAB_RE.match(line)
        if lm:
            key = "ngu_phap" if lm.group(1).lower() == "ngữ pháp" else "sap_xep"
            if it[key] is not None:
                it["nhan_lap"] = True
            val = (lm.group(2) or "").strip()
            it[key] = (it[key] + "\n" + val if it[key] else val) if val else (it[key] or "")
            cur = key
            continue
        tgt = cur or "khac"
        it[tgt] = (it[tgt] + "\n" + line.strip()) if it[tgt] else line.strip()
    return "\n".join(mo_dau), items


SUA_V1 = True                                       # (2026-10-13 điều phối đợt 1) – đặt False để so tác động
QUOTE_DAU_RE = re.compile(r"^\s*[「『'\"“‘]")
NGUOI_NOI_RE = re.compile(r"^\s*[^\s「『:：]{1,12}\s*[「『:：]")   # đầu lượt hội thoại: A「 / B: / ｜山田《やまだ》「


def sap_xep_part(body):
    """CÁCH SẮP XẾP HỢP LÝ NHẤT → {giai_thich[], hoan_chinh[], doc, nghia, vi_tri_sao, khac}."""
    res = {"giai_thich": [], "hoan_chinh": [], "doc": None, "nghia": None, "vi_tri_sao": None, "khac": []}
    cur, nhieu_dong = None, None             # nhieu_dong: nhãn đứng riêng dòng → các dòng sau là nội dung (11189)
    for line in [x for x in (body or "").split("\n") if x.strip()]:
        lm = SX_LAB_RE.match(line)
        # 2026-10-13: thiếu nhãn 'Nghĩa:' – sau 'Cách đọc:' nhiều dòng là các dòng tiếng Việt (không kana/kanji) = nghĩa (17314)
        if SUA_V1 and not lm and nhieu_dong == "doc" and res["nghia"] is None and not re.search(r"[぀-ヿ㐀-鿿]", line):
            nhieu_dong, res["nghia"], cur = "nghia", line.strip(), "nghia"
            continue
        if not lm and nhieu_dong:
            if nhieu_dong == "hoan_chinh":
                res["hoan_chinh"][-1] = (res["hoan_chinh"][-1] + "\n" + line.strip()).strip("\n")
            else:
                res[nhieu_dong] = ((res[nhieu_dong] or "") + "\n" + line.strip()).strip("\n")
            continue
        nhieu_dong = None
        if lm:
            lab, val = lm.group(1).lower(), lm.group(2).strip()
            if not val and (lab.startswith("câu hoàn chỉnh") or (lab in ("cách đọc", "nghĩa") and res["hoan_chinh"])):
                nhieu_dong = "hoan_chinh" if lab.startswith("câu hoàn chỉnh") else ("doc" if lab == "cách đọc" else "nghia")
            if lab.startswith("câu hoàn chỉnh"):
                res["hoan_chinh"].append(val)
                cur = "hoan_chinh"
            elif lab == "cách đọc" and res["hoan_chinh"]:
                if res["doc"] is None:
                    res["doc"], cur = val, "doc"
                else:
                    res["khac"].append(line.strip())
                    cur = "khac"
            elif lab == "nghĩa" and res["hoan_chinh"]:
                if res["nghia"] is None:
                    res["nghia"], cur = val, "nghia"
                else:
                    res["khac"].append(line.strip())
                    cur = "khac"
            elif lab.startswith("vị trí"):
                res["vi_tri_sao"], cur = val, "vi_tri_sao"
            else:                                   # 'Cách đọc:' / 'Nghĩa:' trước câu hoàn chỉnh = phần giải thích
                res["giai_thich"].append(line.strip())
                cur = "giai_thich"
            continue
        if res["hoan_chinh"] and cur in ("hoan_chinh", "doc", "nghia"):
            # hội thoại: 'Câu hoàn chỉnh: A「…」' rồi dòng 'B「…」' (tương tự Cách đọc / Nghĩa 'B: …') → nối vào trường (11056)
            gt = res["hoan_chinh"][-1] if cur == "hoan_chinh" else res[cur]
            if gt and ((NGUOI_NOI_RE.match(gt.split("\n")[0]) and NGUOI_NOI_RE.match(line.strip()))
                       or (SUA_V1 and QUOTE_DAU_RE.match(gt.split("\n")[0]) and QUOTE_DAU_RE.match(line.strip()))):   # 2026-10-13: lượt thoại không tên người nói, bắt đầu bằng 「 / ' (9269)
                if cur == "hoan_chinh":
                    res["hoan_chinh"][-1] = res["hoan_chinh"][-1] + "\n" + line.strip()
                else:
                    res[cur] = res[cur] + "\n" + line.strip()
                continue
        if not res["hoan_chinh"]:
            m = re.match(r"^[-•+・]\s*(.*)$", line.strip())
            res["giai_thich"].append(m.group(1) if m else line.strip())
            cur = "giai_thich"
        else:
            res["khac"].append(line.strip())
            cur = "khac"
    return res


def lcd_part(lcd):
    res = {"so": None, "lua_chon": None, "khac": None}
    for line in [x for x in (lcd or "").split("\n") if x.strip()]:
        m = LCD_NUM_RE.match(line)
        if m and res["so"] is None:
            res["so"], res["lua_chon"] = int(m.group(1)), m.group(2).strip()
            continue
        res["khac"] = line.strip() if not res["khac"] else res["khac"] + "\n" + line.strip()
    return res


# ---------------- ghép câu (lõi kiểm tra tự động của dạng 08) ----------------
def o_trong(cau):
    """Câu đề → (các đoạn chữ giữa ô [5], vị trí ô ★ 0..3 hoặc None, số ô)."""
    cau = re.sub(r"(?<=[\s　＿_])\*(?=[\s　＿_])", "★", cau or "")   # ô ★ gõ bằng '*' ASCII trong đề (23144, 54781)
    parts = SLOT_RE.split(cau)
    slots = SLOT_RE.findall(cau)
    sao = next((i for i, s in enumerate(slots) if s in "★＊"), None)
    return parts, sao, len(slots)


def ghep_cau(cau_de, lua_chon, hoan_chinh_list, dap):
    """Thử mọi thứ tự 4 lựa chọn, so với 'Câu hoàn chỉnh' của lời giải.
    → {trang_thai: khop | khop_doc | lech_nhe | lech_nang | khong_ghep_duoc, order: [số lựa chọn ở ô 1..4], so_o_sao, sao_dung_dap_an,
       chon: chỉ số câu hoàn chỉnh dùng, chi_tiet}"""
    import itertools
    import difflib
    parts, sao, n = o_trong(cau_de)
    res = {"trang_thai": "khong_ghep_duoc", "order": None, "so_o_sao": None, "sao_dung_dap_an": None, "chon": None, "chi_tiet": ""}
    if n != 4 or len(lua_chon) != 4:
        res["chi_tiet"] = f"đề có {n} ô trống (cần 4)"
        return res
    if not hoan_chinh_list:
        res["chi_tiet"] = "lời giải không có 'Câu hoàn chỉnh'"
        return res
    fp, fo = [_f(p) for p in parts], [_f(o) for o in lua_chon]

    def ghep(p):
        return "".join(fp[i] + fo[p[i]] for i in range(4)) + fp[4]
    perms = list(itertools.permutations(range(4)))
    best = None
    for ci, hc in enumerate(hoan_chinh_list):
        fh = _f(hc)
        for p in perms:
            if ghep(p) == fh:
                best = ("khop", p, ci, "")
                break
        if best:
            break
    if not best and _tok():
        for ci, hc in enumerate(hoan_chinh_list):
            yh = _yomi(hc)
            for p in perms:
                s = "".join(parts[i] + lua_chon[p[i]] for i in range(4)) + parts[4]
                if yh and _yomi(s) == yh:
                    best = ("khop_doc", p, ci, "")
                    break
            if best:
                break
    if not best:
        sc = []
        for ci, hc in enumerate(hoan_chinh_list):
            fh = _f(hc)
            for p in perms:
                g = ghep(p)
                sc.append((difflib.SequenceMatcher(a=g, b=fh, autojunk=False).ratio(), ci, p, g, fh))
        sc.sort(key=lambda x: -x[0])
        r, ci, p, g, fh = sc[0]
        d = _khac(g, fh)
        nchar = sum(max(len(x), len(y)) for x, y in d)
        # lệch nhẹ = ≤ 2 ký tự và chỉ là kana / ký hiệu (イ↔ィ…); khác chữ Hán / số → lệch nặng (vd 千→万)
        nang = nchar > 2 or any(re.search(r"[㐀-鿿々0-9０-９]", x + y) for x, y in d)
        best = ("lech_nang" if nang else "lech_nhe", p, ci, "; ".join(f"'{x}'→'{y}'" for x, y in d[:4]))
    tt, p, ci, ct = best
    order = [p[i] + 1 for i in range(4)]
    res.update(trang_thai=tt, order=order, chon=ci, chi_tiet=ct)
    if sao is not None:
        res["so_o_sao"] = order[sao]
        res["sao_dung_dap_an"] = (dap is not None and order[sao] == dap)
    return res


def doc_lua_chon(item, lua_chon_de):
    """Cách đọc của một lựa chọn: phần trước ' - ' trong ngoặc tiêu đề nếu toàn kana; lựa chọn toàn kana thì là chính nó."""
    s = strip_marks(lua_chon_de or "")
    if re.fullmatch(r"[぀-ゟ゠-ヿー\s]+", s or "x"):
        return _hira(s.strip())
    gl = (item or {}).get("gloss") or ""
    m = re.match(r"^\s*([぀-ゟ゠-ヿー・\s]+?)\s*[-–—:：]", gl)
    if m and m.group(1).strip():
        return m.group(1).strip()
    return None


def ghep_cach_doc(doc_de, order, items_by_so, lua_chon):
    """Quyết định 08/10/2026: lời giải thiếu 'Cách đọc' của câu hoàn chỉnh → Python ghép = cách đọc câu đề + cách đọc từng lựa chọn theo thứ tự đúng.
    Chỉ ghép khi câu đề có 'Cách đọc' đủ 4 ô và đọc được cả 4 lựa chọn; không thì None."""
    if not doc_de or not order:
        return None
    parts, _, n = o_trong(doc_de)
    if n != 4:
        return None
    docs = [doc_lua_chon(items_by_so.get(k), lua_chon[k - 1]) for k in order]
    if any(not d for d in docs):
        return None
    out = parts[0].strip()
    for i in range(4):
        out += " " + docs[i]
        if parts[i + 1].strip():
            out += " " + parts[i + 1].strip()
    out = re.sub(r"[ \t　]+", " ", out).strip()
    return None if re.search(r"[㐀-鿿々]", out) else out


VITRI_RE = re.compile(r"(?:đứng|đặt|nằm|đi)\s*(trước|sau)\s*(?:[^'‘’\"\n]{0,25})?['‘’\"]([^'‘’\"\n]{1,30})['‘’\"]")


def kiem_kha_nang_sap_xep(items, order, hoan_chinh, cau_de):
    """Gợi ý (độ chính xác cao): 'Khả năng sắp xếp' nói lựa chọn đứng TRƯỚC 'X' nhưng câu hoàn chỉnh có X đứng ngay trước lựa chọn
    (hoặc ngược lại) – mâu thuẫn rõ với cách sắp xếp đúng (vd 19634). Câu nói chung chung / không liền kề thì bỏ qua."""
    out = []
    if not hoan_chinh:
        return out
    fh = _f(hoan_chinh)
    for it in items:
        txt, me = it.get("sap_xep") or "", _f(it.get("lua_chon"))
        if not me or fh.count(me) != 1:
            continue
        for m in VITRI_RE.finditer(txt):
            huong, x = m.group(1), _f(m.group(2))
            if not x or me in x or x in me or fh.count(x) != 1:
                continue
            truoc, sau = (me + x) in fh, (x + me) in fh
            if (huong == "trước" and sau and not truoc) or (huong == "sau" and truoc and not sau):
                out.append(f"Lựa chọn {it['so']} '{it.get('lua_chon')}': 'Khả năng sắp xếp' nói đứng {huong} '{m.group(2)}' – "
                           f"nhưng trong câu hoàn chỉnh nó đứng {'sau' if huong == 'trước' else 'trước'} '{m.group(2)}' (nghi lỗi nội dung)")
    return out


# ---------------- gắn cờ (giai đoạn 0) ----------------
FLAG_TEXT = {
    "nhan_de_bai": "Câu đề trong lời giải có nhãn 'Đề bài:' (question.ja không chép nhãn)",
    "khong_cach_doc": "Không có dòng 'Cách đọc:' của câu đề (question.reading = null, trừ khi ghép được từ furigana)",
    "de_toan_kana": "Câu đề toàn kana, lời giải không ghi 'Cách đọc' (question.reading = null – không cần)",
    "hoan_chinh_toan_kana": "Câu hoàn chỉnh toàn kana, lời giải không ghi 'Cách đọc' (reading = null – không cần)",
    "doc_tu_furigana": "Không có dòng 'Cách đọc:' – Python ghép cách đọc câu đề từ furigana",
    "khong_nghia_de": "Không có dòng 'Nghĩa:' của câu đề",
    "hoi_thoai": "Đề hội thoại / nhiều dòng",
    "de_khong_du_o": "Câu đề không có đúng 4 ô trống (không ghép được)",
    "de_khong_sao": "Câu đề không có ô ★",
    "thieu_phan_de_bai": "Không có phần PHÂN TÍCH ĐỀ BÀI (sentence_analysis = [])",
    "phan_cau_truc_cau": "Phần phân tích đề có tiêu đề 'PHÂN TÍCH CẤU TRÚC CÂU' (→ sentence_analysis như PHÂN TÍCH ĐỀ BÀI)",
    "thieu_phan_lua_chon": "Không có phần PHÂN TÍCH CÁC LỰA CHỌN",
    "thieu_phan_sap_xep": "Không có phần CÁCH SẮP XẾP HỢP LÝ NHẤT",
    "thieu_lua_chon_dung": "Không có phần LỰA CHỌN ĐÚNG",
    "khong_tieu_de": "Lời giải không có tiêu đề phần nào (không tách được – tác tử TẠO tự đặt theo nội dung, Claude kiểm tra soát kỹ)",
    "chi_tham_khao": "Lời giải chỉ có phần NGỮ PHÁP / THÔNG TIN THAM KHẢO – thiếu lời giải chính",
    "lap_phan": "Một phần xuất hiện 2 lần (gộp theo thứ tự)",
    "co_doan_truoc_lua_chon": "PHÂN TÍCH CÁC LỰA CHỌN có câu chữ trước lựa chọn 1",
    "so_lua_chon_khac_4": "PHÂN TÍCH CÁC LỰA CHỌN không có đúng 4 lựa chọn",
    "thu_tu_lua_chon_lech": "Số thứ tự trong PHÂN TÍCH CÁC LỰA CHỌN không khớp thứ tự lựa chọn của đề",
    "lua_chon_khac_de": "Dòng lựa chọn trong lời giải viết khác lựa chọn của đề",
    "khong_gloss": "Có lựa chọn không có phần '(cách đọc - nghĩa)' ở dòng tiêu đề (gloss = null)",
    "thieu_ngu_phap": "Có lựa chọn không có '- Ngữ pháp:'",
    "thieu_kha_nang_sap_xep": "Có lựa chọn không có '- Khả năng sắp xếp:'",
    "lua_chon_dong_la": "Có lựa chọn có câu chữ trước nhãn '- Ngữ pháp:' (không thuộc nhãn nào)",
    "nhan_lap": "Một lựa chọn có nhãn lặp",
    "khong_cau_hoan_chinh": "Không có 'Câu hoàn chỉnh'",
    "nhieu_cau_hoan_chinh": "Có nhiều 'Câu hoàn chỉnh' (1 / 2 …) – dùng câu ghép khớp đề, câu còn lại vào explanation + gắn cờ (quyết định 08/10/2026)",
    "ghep_lech_nhe": "Câu hoàn chỉnh lệch 1–2 ký tự so với đề + lựa chọn (nghi lỗi gõ / dấu câu → sửa định dạng nếu đúng là lỗi gõ)",
    "ghep_lech_nang": "Câu hoàn chỉnh khác chữ so với đề + lựa chọn (nghi lỗi nội dung → gắn cờ cau_khac_de)",
    "khong_ghep_duoc": "Không ghép được câu (thiếu câu hoàn chỉnh / đề không đủ 4 ô)",
    "sao_lech_dap_an": "Theo câu hoàn chỉnh của lời giải, ô ★ là lựa chọn KHÁC đáp án của đề (nghi lỗi nội dung)",
    "vi_tri_sao_lech": "Dòng 'Vị trí ★' ghi lựa chọn khác đáp án của đề",
    "thieu_vi_tri_sao": "Không có dòng 'Vị trí ★'",
    "doc_hoan_chinh_ghep": "Không có 'Cách đọc' của câu hoàn chỉnh – Python ghép từ cách đọc câu đề + cách đọc 4 lựa chọn (quyết định 08/10/2026)",
    "khong_doc_hoan_chinh": "Không có 'Cách đọc' của câu hoàn chỉnh và Python không ghép được (reading = null)",
    "doc_co_sao": "Cách đọc câu hoàn chỉnh có lẫn ★ (lỗi định dạng)",
    "khong_nghia_hoan_chinh": "Không có 'Nghĩa' của câu hoàn chỉnh",
    "co_doan_sau_hoan_chinh": "Có câu chữ sau Câu hoàn chỉnh / Cách đọc / Nghĩa trong phần sắp xếp",
    "kha_nang_sap_xep_lech": "Gợi ý Python: 'Khả năng sắp xếp' của một lựa chọn mâu thuẫn với câu hoàn chỉnh",
    "lech_dap_an": "LỰA CHỌN ĐÚNG ghi đáp án khác dap_an_so của đề",
    "lcd_go_nham_so": "Số trong LỰA CHỌN ĐÚNG gõ nhầm nhưng nội dung đúng đáp án",
    "khong_so_lcd": "LỰA CHỌN ĐÚNG không có số",
    "lcd_co_nhan_xet": "LỰA CHỌN ĐÚNG có thêm câu chữ",
    "co_doan_sau_lcd": "Có đoạn sau LỰA CHỌN ĐÚNG",
    "co_tham_khao": "Có phần THAM KHẢO – Python chép nguyên văn vào reference_raw",
    "danh_dau_rac": "Bản gốc có đoạn in đậm / gạch chân rỗng (đã bỏ thẻ)",
    "co_furigana": "Có furigana",
    "ruby_hong": "Có ruby hỏng trong bản gốc",
    "ky_hieu_trung": "Bản gốc có sẵn ký hiệu ｜《》",
    "furigana_chu_viet": "Furigana gắn lên chữ tiếng Việt (Python đã bỏ)",
}
CTV_FLAGS = ("sao_lech_dap_an", "lech_dap_an", "ghep_lech_nang", "chi_tham_khao", "khong_tieu_de")
FURI_SKIP = []


def parse_and_flag(text, raw_html, lua_chon, dap_an_so, de_html):
    """Tách phần + ghép câu + gắn cờ + ghi chú bản gốc. Trả về (phan, co, ghi_chu)."""
    from pipeline_chung.normalize import normalize_html
    sec = split_sections(text)
    hd = head_part(sec["dau"])
    mo, items = option_items(sec["lua_chon"], lua_chon)
    sx = sap_xep_part(sec["sap_xep"])
    lcd = lcd_part(sec["lua_chon_dung"])
    co, gc, goi_y = [], [], []
    cau_de = normalize_html((de_html or "").split("\x00")[0])[0].replace("{", "").replace("}", "")
    cau_de = cau_de.replace("＊", "★")
    cau = hd["cau"] or cau_de
    dap = int(dap_an_so) if str(dap_an_so).isdigit() else None
    if hd.get("nhan_de"):
        co.append("nhan_de_bai")
    doc_furi = None
    co_han = lambda t: bool(re.search(r"[㐀-鿿々〆]", strip_marks(t or "")))  # noqa: E731
    if hd["doc"] is None:
        doc_furi = doc_tu_furigana(hd["cau"])
        co.append("doc_tu_furigana" if doc_furi else ("khong_cach_doc" if co_han(hd["cau"] or cau_de) else "de_toan_kana"))
    if hd["nghia"] is None:
        co.append("khong_nghia_de")
    if "\n" in (hd["cau"] or "") or re.search(r"[｢「].*[」｣]", hd["cau"] or ""):
        co.append("hoi_thoai")
    _, sao, n = o_trong(cau_de)
    if n != 4:
        co.append("de_khong_du_o")
    if sao is None:
        co.append("de_khong_sao")
    if not sec["co_tieu_de"]:
        co.append("khong_tieu_de")
        gc.append("[Bản gốc VI] Lời giải không có tiêu đề phần (PHÂN TÍCH ĐỀ BÀI / CÁC LỰA CHỌN / CÁCH SẮP XẾP / LỰA CHỌN ĐÚNG)")
    elif sec["tham_khao"] and not (sec["lua_chon"] or sec["sap_xep"]):
        co.append("chi_tham_khao")
        gc.append("[Bản gốc VI] Lời giải chỉ có phần tham khảo – thiếu phân tích các lựa chọn và cách sắp xếp")
    if sec["co_tieu_de"]:
        if sec["de_bai"] is None:
            co.append("thieu_phan_de_bai")
        elif sec["ten_de_bai"] == "PHÂN TÍCH CẤU TRÚC CÂU":
            co.append("phan_cau_truc_cau")
        if sec["lua_chon"] is None:
            co.append("thieu_phan_lua_chon")
        if sec["sap_xep"] is None:
            co.append("thieu_phan_sap_xep")
        if sec["lua_chon_dung"] is None:
            co.append("thieu_lua_chon_dung")
    if sec["lap"]:
        co.append("lap_phan")
        gc.append(f"[Bản gốc VI] Phần lặp lại: {', '.join(sec['lap'])}")
    if mo.strip():
        co.append("co_doan_truoc_lua_chon")
    if sec["lua_chon"] is not None and len(items) != 4:
        co.append("so_lua_chon_khac_4")
    for it in items:
        if it["lua_chon_khop"] and it["lua_chon_khop"] != it["so"]:
            co.append("thu_tu_lua_chon_lech")
        if not it["lua_chon_khop"] and 1 <= it["so"] <= 4:
            co.append("lua_chon_khac_de")
            gc.append(f"[Bản gốc VI] Lựa chọn {it['so']} trong lời giải viết khác đề: '{strip_marks(it['lua_chon'])}' ↔ đề '{lua_chon[it['so'] - 1]}'")
        if not it["gloss"]:
            co.append("khong_gloss")
        if it["ngu_phap"] is None:
            co.append("thieu_ngu_phap")
        if it["sap_xep"] is None:
            co.append("thieu_kha_nang_sap_xep")
        if it["khac"]:
            co.append("lua_chon_dong_la")
        if it["nhan_lap"]:
            co.append("nhan_lap")
    # câu hoàn chỉnh + ghép
    hcs = sx["hoan_chinh"]
    if sec["sap_xep"] is not None and not hcs:
        co.append("khong_cau_hoan_chinh")
    if len(hcs) > 1:
        co.append("nhieu_cau_hoan_chinh")
    g = ghep_cau(cau_de, lua_chon, hcs, dap)
    if g["trang_thai"] == "khong_ghep_duoc":
        co.append("khong_ghep_duoc")
    elif g["trang_thai"] == "lech_nhe":
        co.append("ghep_lech_nhe")
        gc.append(f"[Bản gốc VI] Câu hoàn chỉnh lệch nhẹ so với đề + lựa chọn ({g['chi_tiet']}) – nghi lỗi gõ")
    elif g["trang_thai"] == "lech_nang":
        co.append("ghep_lech_nang")
        gc.append(f"[Bản gốc VI] Câu hoàn chỉnh khác đề + lựa chọn ({g['chi_tiet']})")
    if g["sao_dung_dap_an"] is False:
        co.append("sao_lech_dap_an")
        gc.append(f"[Bản gốc VI] Theo câu hoàn chỉnh, ô ★ là lựa chọn {g['so_o_sao']} – khác đáp án {dap}")
    if sec["sap_xep"] is not None:
        if sx["vi_tri_sao"] is None:
            co.append("thieu_vi_tri_sao")
        elif dap and not _eq_doc(sx["vi_tri_sao"], lua_chon[dap - 1]):
            co.append("vi_tri_sao_lech")
            gc.append(f"[Bản gốc VI] 'Vị trí ★' ghi '{sx['vi_tri_sao']}' – đáp án của đề là '{lua_chon[dap - 1]}'")
    doc_hc_ghep = None
    if hcs:
        if sx["doc"] is None:
            by_so = {(it["lua_chon_khop"] or it["so"]): it for it in items}
            doc_de = hd["doc"] or doc_furi or (None if co_han(hd["cau"] or cau_de) else (hd["cau"] or cau_de))
            doc_hc_ghep = None if not co_han(hcs[g["chon"] or 0]) else ghep_cach_doc(doc_de, g["order"] if g["trang_thai"] in ("khop", "khop_doc") else None, by_so, lua_chon)
            co.append("doc_hoan_chinh_ghep" if doc_hc_ghep else ("khong_doc_hoan_chinh" if co_han(hcs[g["chon"] or 0]) else "hoan_chinh_toan_kana"))
            if doc_hc_ghep:
                gc.append("[Cách đọc ghép] Lời giải không có 'Cách đọc' của câu hoàn chỉnh – Python ghép từ cách đọc câu đề + cách đọc các lựa chọn")
        elif "★" in sx["doc"] or "＊" in sx["doc"]:
            co.append("doc_co_sao")
        if sx["nghia"] is None:
            co.append("khong_nghia_hoan_chinh")
        if sx["khac"]:
            co.append("co_doan_sau_hoan_chinh")
    if g["order"] and hcs:
        goi_y += kiem_kha_nang_sap_xep(items, g["order"], hcs[g["chon"] or 0], cau_de)
        if goi_y:
            co.append("kha_nang_sap_xep_lech")
    # LỰA CHỌN ĐÚNG
    if sec["lua_chon_dung"] is not None:
        if lcd["so"] is None:
            co.append("khong_so_lcd")
        elif dap and lcd["so"] != dap:
            if lcd["lua_chon"] and _eq_doc(lcd["lua_chon"], lua_chon[dap - 1]):
                co.append("lcd_go_nham_so")
                gc.append(f"[Bản gốc VI] LỰA CHỌN ĐÚNG ghi số {lcd['so']} nhưng nội dung là đáp án {dap} – nghi gõ nhầm số")
            else:
                co.append("lech_dap_an")
                gc.append(f"[Bản gốc VI] LỰA CHỌN ĐÚNG ghi {lcd['so']}. {lcd['lua_chon']}, khác đáp án của đề (dap_an_so = {dap_an_so})")
        if lcd["khac"]:
            co.append("lcd_co_nhan_xet")
    if sec["sau_lcd"]:
        co.append("co_doan_sau_lcd")
    if sec["tham_khao"]:
        co.append("co_tham_khao")
    phan = {"tham_khao": sec["tham_khao"], "dau": hd, "cau_de": cau_de, "doc_furigana": doc_furi,
            "de_bai": bullet_items(sec["de_bai"]), "ten_de_bai": sec["ten_de_bai"],
            "lua_chon": {"mo_dau": mo, "dong": items}, "sap_xep": sx, "doc_hoan_chinh_ghep": doc_hc_ghep,
            "ghep": g, "lcd": lcd, "sau_lcd": sec["sau_lcd"], "goi_y_python": goi_y}
    return phan, sorted(set(co)), gc


# ---------------- kiểm tra riêng giai đoạn 1 (K) ----------------
READING_OK = re.compile(r"^[぀-ゟ゠-ヿー・\s/、,，。．！？!?「」『』（）()0-9０-９~〜…\-－―_＿★　:：A-Za-zＡ-Ｚ{}]+$")


def opt_text(o):
    return "\n".join(x for x in (_v(o.get("gloss")), _v(o.get("grammar")), _v(o.get("arrangement"))) if x)


def check_k(doc, norm, policy):
    loi, canh_bao = [], []
    de, phan = norm["de"], norm.get("phan") or {}
    q, ar, c = doc.get("question") or {}, doc.get("arrangement") or {}, doc.get("correct") or {}
    opts = doc.get("options") or []
    dap = int(de["dap_an_so"]) if str(de["dap_an_so"]).isdigit() else None
    hd = phan.get("dau") or {}
    # K8 – câu đề
    dong_dau_khong_o = bool(hd.get("cau")) and o_trong(hd["cau"])[2] == 0 and _k(q.get("ja")) == _k(de["cau_hoi"])
    if hd.get("cau") and _k(q.get("ja")) != _k(hd["cau"]) and not dong_dau_khong_o:   # dòng đầu không có ô trống = không phải câu đề (18266)
        loi.append(f"K8: question.ja khác dòng câu đề của lời giải '{hd['cau'][:60]}'")
    doc_mong = hd.get("doc") or phan.get("doc_furigana")
    if (doc_mong is None) != (q.get("reading") is None):
        loi.append("K8: question.reading phải null khi và chỉ khi lời giải không có dòng 'Cách đọc:' (và không ghép được từ furigana)")
    elif doc_mong and _k(q.get("reading")) != _k(doc_mong):
        loi.append(f"K8: question.reading khác dòng Cách đọc của lời giải: '{doc_mong[:60]}'")
    if (hd.get("nghia") is None) != (q.get("meaning") is None):
        loi.append("K8: question.meaning phải null khi và chỉ khi lời giải không có dòng 'Nghĩa:' của câu đề")
    elif hd.get("nghia"):
        cv, miss = _cover(hd["nghia"], _v(q.get("meaning")))
        if cv < 0.97:
            loi.append(f"K8: question.meaning thiếu chữ so với bản gốc: {miss}")
        nb = len(SLOT_RE.findall(hd["nghia"]))
        if len(SLOT_RE.findall(_v(q.get("meaning")) or "")) != nb:
            loi.append(f"K8: question.meaning phải giữ {nb} ô trống / ★ như bản gốc")
    # K-SA – PHÂN TÍCH ĐỀ BÀI
    sa_src = phan.get("de_bai") or []
    sa = doc.get("sentence_analysis") or []
    if bool(sa_src) != bool(sa):
        loi.append(f"K10: sentence_analysis: bản gốc {'có' if sa_src else 'không có'} phần phân tích đề nhưng JSON {'rỗng' if not sa else 'có'}")
    elif sa_src:
        cv, miss = _cover("\n".join(sa_src), "\n".join(_v(x) or "" for x in sa))
        if cv < 0.97:
            loi.append(f"K9: sentence_analysis thiếu chữ: {miss}")
        if len(sa) != len(sa_src):
            canh_bao.append(f"K10: sentence_analysis có {len(sa)} ý – bản gốc có {len(sa_src)} gạch đầu dòng")
    # K1 / K2 / K12 / K9 – lựa chọn
    if [o.get("index") for o in opts] != [1, 2, 3, 4]:
        loi.append(f"K1: options phải có đủ 4 lựa chọn theo thứ tự 1–4 (đang có {[o.get('index') for o in opts]})")
    src = {}
    for it in (phan.get("lua_chon") or {}).get("dong", []):
        src.setdefault(it["lua_chon_khop"] or it["so"], it)
    for o in opts:
        i = o.get("index")
        if not isinstance(i, int) or not 1 <= i <= 4:
            continue
        it = src.get(i)
        if it is not None and _k(o.get("option_ja")) != _k(it["lua_chon"]):
            loi.append(f"K8: lựa chọn {i}: option_ja '{o.get('option_ja')}' khác dòng lựa chọn của lời giải '{it['lua_chon']}'")
        elif it is None and not _eq(o.get("option_ja"), de["lua_chon"][i - 1]):
            loi.append(f"K2: lựa chọn {i}: option_ja phải chép đúng lựa chọn của đề '{de['lua_chon'][i - 1]}'")
        if it is None:
            for name in ("gloss", "grammar", "arrangement"):
                if o.get(name) is not None:
                    canh_bao.append(f"K12: lựa chọn {i}: lời giải không phân tích lựa chọn này nhưng {name} khác null")
            continue
        for key, name, lab in (("gloss", "gloss", "(cách đọc - nghĩa) ở dòng tiêu đề"), ("ngu_phap", "grammar", "Ngữ pháp"),
                               ("sap_xep", "arrangement", "Khả năng sắp xếp")):
            if it[key] and o.get(name) is None:
                loi.append(f"K12: lựa chọn {i}: bản gốc có '{lab}' nhưng {name} = null")
            if not it[key] and o.get(name) is not None and not (key == "ngu_phap" and it.get("khac")):
                loi.append(f"K12: lựa chọn {i}: bản gốc không có '{lab}' nhưng {name} khác null")
        srcv = "\n".join(x for x in (it["gloss"], it["ngu_phap"], it["sap_xep"], it["khac"]) if x)
        cv, miss = _cover(srcv, opt_text(o))
        if cv < 0.97:
            loi.append(f"K9: lựa chọn {i}: thiếu chữ so với bản gốc: {miss}")
    # K-AR – CÁCH SẮP XẾP
    sx = phan.get("sap_xep") or {}
    g = phan.get("ghep") or {}
    fs = ar.get("full_sentence") or {}
    hcs = sx.get("hoan_chinh") or []
    chon = g.get("chon") or 0
    ex_src = list(sx.get("giai_thich") or []) + [x for i, x in enumerate(hcs) if i != chon] + list(sx.get("khac") or [])
    ex = ar.get("explanation") or []
    if ex_src:
        cv, miss = _cover("\n".join(ex_src), "\n".join(_v(x) or "" for x in ex))
        if cv < 0.97:
            loi.append(f"K9: arrangement.explanation thiếu chữ: {miss}")
    elif ex:
        canh_bao.append("K10: arrangement.explanation có nội dung nhưng bản gốc không có phần giải thích trước 'Câu hoàn chỉnh'")
    if hcs:
        if _k(fs.get("ja")) != _k(hcs[chon]):
            loi.append(f"K8: arrangement.full_sentence.ja khác 'Câu hoàn chỉnh' của lời giải '{hcs[chon][:60]}'")
        doc_hc = sx.get("doc") or phan.get("doc_hoan_chinh_ghep")
        if (doc_hc is None) != (fs.get("reading") is None):
            loi.append("K8: arrangement.full_sentence.reading phải null khi và chỉ khi lời giải không có 'Cách đọc' câu hoàn chỉnh và Python không ghép được"
                       + (f" (Python ghép: '{phan['doc_hoan_chinh_ghep']}')" if phan.get("doc_hoan_chinh_ghep") else ""))
        elif doc_hc and _k(fs.get("reading")).replace("★", "") != _k(doc_hc).replace("★", ""):
            loi.append(f"K8: arrangement.full_sentence.reading khác {'Cách đọc của lời giải' if sx.get('doc') else 'cách đọc Python ghép'}: '{doc_hc[:60]}'")
        if "★" in (fs.get("reading") or ""):
            canh_bao.append("K-DOC: full_sentence.reading còn ★ – lỗi định dạng bản gốc, bỏ ★ (sua_dinh_dang)")
        if (sx.get("nghia") is None) != (fs.get("meaning") is None):
            loi.append("K8: arrangement.full_sentence.meaning phải null khi và chỉ khi lời giải không có 'Nghĩa' của câu hoàn chỉnh")
        elif sx.get("nghia"):
            cv, miss = _cover(sx["nghia"], _v(fs.get("meaning")))
            if cv < 0.97:
                loi.append(f"K9: arrangement.full_sentence.meaning thiếu chữ: {miss}")
    for name, s_ in (("question.reading", q.get("reading")), ("arrangement.full_sentence.reading", fs.get("reading"))):
        if s_ and not READING_OK.match(strip_marks(s_)):
            canh_bao.append(f"K-DOC: {name} có chữ Hán / ký tự lạ – xem lại")
    # K-ORD – thứ tự
    order = ar.get("order")
    if sorted(order or []) != [1, 2, 3, 4]:
        loi.append(f"K-ORD: arrangement.order phải là hoán vị của 1–4 (đang là {order})")
    elif g.get("trang_thai") in ("khop", "khop_doc") and order != g.get("order"):
        loi.append(f"K-ORD: arrangement.order = {order} khác thứ tự Python ghép từ câu hoàn chỉnh {g.get('order')}")
    elif g.get("order") and order != g.get("order"):
        canh_bao.append(f"K-ORD: arrangement.order = {order} – Python ghép gần nhất được {g.get('order')} (câu hoàn chỉnh lệch đề)")
    # K6 – đáp án / ô ★
    if str(c.get("index")) != str(de["dap_an_so"]):
        loi.append(f"K6: correct.index = {c.get('index')} khác dap_an_so = {de['dap_an_so']}")
    di = c.get("index")
    if isinstance(di, int) and 1 <= di <= len(opts) and c.get("option_ja") != opts[di - 1].get("option_ja"):
        loi.append(f"K6: correct.option_ja phải giống hệt options[{di - 1}].option_ja")
    if c.get("full_sentence") is not None:
        loi.append("K6: correct.full_sentence phải là null (câu hoàn chỉnh nằm ở arrangement.full_sentence)")
    if g.get("sao_dung_dap_an") is False:
        canh_bao.append(f"K11: theo câu hoàn chỉnh của lời giải, ô ★ là lựa chọn {g.get('so_o_sao')} ≠ đáp án {dap} – nghi lỗi nội dung (gắn cờ)")
    if g.get("trang_thai") == "lech_nang":
        canh_bao.append(f"K11: câu hoàn chỉnh khác đề + lựa chọn ({g.get('chi_tiet')}) – nghi lỗi nội dung (gắn cờ cau_khac_de)")
    elif g.get("trang_thai") == "lech_nhe":
        canh_bao.append(f"K11: câu hoàn chỉnh lệch nhẹ đề ({g.get('chi_tiet')}) – lỗi gõ thì sửa định dạng, khác chữ thì gắn cờ")
    for x in phan.get("goi_y_python") or []:
        canh_bao.append("K-SX: " + x)
    loi += TK.kiem_tra(doc, phan.get("tham_khao"))
    return loi, canh_bao


def is_style_field(path):
    """Trường câu văn giải thích (kiểm tra -습니다); bỏ nghĩa câu (dịch từ tiếng Nhật), gloss ('⟪…⟫ - nghĩa') và các cụm '… → …'."""
    p = path if isinstance(path, str) else path_str(path)
    return not re.search(r"question\.meaning|full_sentence\.meaning|\.gloss|arrangement\.explanation", p)


# ---------------- hiển thị cho Excel CTV ----------------
def render(d, lang):
    q, ar, c = d.get("question") or {}, d.get("arrangement") or {}, d.get("correct") or {}
    out = [f"{bold('Đề bài:')} {show(q.get('ja', ''))}"]
    if q.get("reading"):
        out.append(f"Cách đọc: {show(q['reading'])}")
    if q.get("meaning"):
        out.append(f"Nghĩa: {_t(q['meaning'], lang)}")
    if d.get("sentence_analysis"):
        out.append(bold("【PHÂN TÍCH ĐỀ BÀI】"))
        out += ["- " + _t(x, lang).replace("\n", "\n  ") for x in d["sentence_analysis"]]
    out.append(bold("【PHÂN TÍCH CÁC LỰA CHỌN】"))
    for o in d.get("options", []):
        head = bold(f"{o.get('index')}. ") + show(o.get("option_ja", ""))
        if o.get("gloss"):
            head += f" ({_t(o['gloss'], lang)})"
        out.append(head)
        if o.get("grammar"):
            out.append("- Ngữ pháp:\n" + _t(o["grammar"], lang))
        if o.get("arrangement"):
            out.append("- Khả năng sắp xếp:\n" + _t(o["arrangement"], lang))
    out.append(bold("【CÁCH SẮP XẾP HỢP LÝ NHẤT】"))
    out += [_t(x, lang) for x in ar.get("explanation") or []]
    fs = ar.get("full_sentence") or {}
    if fs.get("ja"):
        out.append(f"Câu hoàn chỉnh: {show(fs['ja'])}")
    if fs.get("reading"):
        out.append(f"Cách đọc: {show(fs['reading'])}")
    if fs.get("meaning"):
        out.append(f"Nghĩa: {_t(fs['meaning'], lang)}")
    if ar.get("order"):
        out.append(f"Thứ tự: {' → '.join(str(x) for x in ar['order'])}")
    out.append(bold("【LỰA CHỌN ĐÚNG】"))
    out.append(f"{c.get('index')}. {show(c.get('option_ja', ''))}")
    out += TK.render(d, lang, show, bold)
    return "\n".join(out)


def sudachi_hints(norm):
    """Gợi ý cho bước 1.2: R1 – cách đọc câu đề lệch từ điển; A – kết quả ghép câu; SX – khả năng sắp xếp mâu thuẫn."""
    if not norm.get("phan"):
        return []
    ph = norm["phan"]
    hd = ph.get("dau") or {}
    out = []
    ja, doc = hd.get("cau"), hd.get("doc")
    if _tok() and ja and doc and not re.search(r"[㐀-鿿]", strip_marks(doc)) \
            and not re.search(r"[0-9０-９A-Za-zＡ-Ｚａ-ｚ]", strip_marks(ja) + doc):
        a = _seion(_yomi(SLOT_RE.sub("", ja)))
        b = _seion(_yomi_kana(SLOT_RE.sub("", doc)))
        if a and b and a != b:
            diff = _khac(a, b)
            n = sum(len(x) + len(y) for x, y in diff)
            if n >= 2:
                out.append("R1: câu đề – cách đọc lệch từ điển ở: " + "; ".join(f"'{x}'→'{y}'" for x, y in diff[:3]) if n <= 12
                           else "R1: câu đề – cách đọc lệch nhiều so với câu tiếng Nhật (xem lại cả dòng)")
    g = ph.get("ghep") or {}
    if g.get("trang_thai") not in (None, "khop", "khop_doc"):
        out.append(f"A: ghép câu {g['trang_thai']}" + (f" – {g['chi_tiet']}" if g.get("chi_tiet") else ""))
    if g.get("sao_dung_dap_an") is False:
        out.append(f"A: ô ★ theo câu hoàn chỉnh là lựa chọn {g.get('so_o_sao')} – khác đáp án")
    out += ["SX: " + x for x in ph.get("goi_y_python") or []]
    return out
