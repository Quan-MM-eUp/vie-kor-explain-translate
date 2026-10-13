"""Phần riêng của dạng 09 – Ngữ pháp theo đoạn văn (dựng 2026-10-08 từ dạng 07 – cùng khuôn lời giải).

Khác dạng 07: câu đề là đoạn TRÍCH từ đoạn văn (4 chỗ trống / đoạn, 4 câu con); nhãn 'Về mặt ngữ pháp' / '{ĐỀ BÀI}:' / 'NGHĨA:';
chỗ trống dạng [1] / （1） / (1) / [1-a]…; lời giải viết liền một dòng (Python tách); K-ĐV: so câu đề trong lời giải với đoạn văn gốc;
thứ tự chạy theo ĐOẠN VĂN (4 câu liền nhau, lô 12 câu = 3 đoạn); passage {blank_label, lines=[]} do Python điền.
Phần riêng 09 ở cuối file. Các script s0…s3 đều import file này.
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
    os.environ["PIPELINE_DATA"] = _c.get("du_lieu_test", "data/test_09_ngu_phap_theo_doan_van.csv")


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
VERDICT_NP = r"(?:Không đúng|Không chính xác|Chính xác|Đúng|Sai)"
VERDICT_NN = r"(?:Không phù hợp|Không hợp lý|Không tự nhiên|Chưa phù hợp|Không đúng|Phù hợp|Hợp lý|Tự nhiên|Đúng|Sai)"
LABELS = [r"(?im)^\s*[-+•]?\s*về (?:mặt )?ngữ pháp\s*[:：]?\s*" + VERDICT_NP + r"?[\s.,;:!]*",
          r"(?im)^\s*[-+•]?\s*về (?:mặt )?ngữ nghĩa\s*[:：]?\s*" + VERDICT_NN + r"?[\s.,;:!]*",
          r"(?im)^\s*[-+•]?\s*(ý nghĩa|cấu trúc|áp dụng vào câu|áp dụng|nhận xét|nghĩa|câu hoàn chỉnh)\s*[:：]",
          r"(?m)PHÂN TÍCH\s*[:：]?", r"(?m)LỰA CHỌN ĐÚNG\s*[:：]?", r"#{3,}"]


def strip_labels(text):
    text = re.sub(r"(?im)^\s*[-+•]?\s*cách đọc\s*[:：].*$", " ", text)   # dòng cách đọc là tiếng Nhật – không tính độ phủ tiếng Việt
    text = re.sub(r"(?m)^\s*[A-ZＡ-Ｚ]\s*(?=[｢「『])", " ", text)   # nhãn người nói (A / B) trước câu tiếng Nhật của đề hội thoại – không phải chữ tiếng Việt
    for pat in LABELS:
        text = re.sub(pat, " ", text)
    return text


# ---------------- so sánh câu tiếng Nhật ----------------
def _eq(a, b):
    """So câu / lựa chọn: bỏ furigana, { }, dấu, khoảng trắng."""
    f = lambda s: re.sub(r"[。\.．、,，\s　!！?？「」『』｢｣｡・’'\"…:：①-⑳]", "", norm_ja(strip_marks(s or "")).replace("{", "").replace("}", "")).replace("ー", "一")  # noqa: E731
    return bool(f(a)) and f(a) == f(b)


def _eq_doc(a, b):
    """Như _eq, hoặc cùng cách đọc (lời giải viết chữ Hán, đề viết kana: 限る ~ かぎる)."""
    if _eq(a, b):
        return True
    if not _tok():
        return False
    ya, yb = _yomi(a), _yomi(b)
    return bool(ya) and ya == yb


def _doc_furi(s):
    """｜漢字《かな》 → かな (lấy cách đọc của furigana)."""
    return re.sub(r"｜([^《]*)《([^》]*)》", r"\2", s or "")


BLANK_RE = re.compile(r"_{2,}|＿{2,}|[（(][\s　]*[)）]|[\[［（(「]\s*[1-4１-４]\s*(?:[-－]\s*[abａｂ])?\s*[\]］）)」]")   # dạng 09: [1] （1） (1) [1-a] 「１」


def dien(cau, lua_chon):
    """Điền lựa chọn vào chỗ trống của câu. Lựa chọn 'X/Y' (hoặc 'X／Y') với câu 2 chỗ trống → điền lần lượt."""
    cau, lc = cau or "", strip_marks(lua_chon or "").strip()
    n = len(BLANK_RE.findall(cau))
    parts = [p.strip() for p in re.split(r"[/／]", lc)] if n >= 2 and re.search(r"[/／]", lc) else [lc]
    parts = [re.sub(r"^[abａｂ]\s*(?=[^\sA-Za-z])", "", p) for p in parts]   # dạng 09: 'aからして／b表すことだ'
    out = cau
    for p in parts:
        out = BLANK_RE.sub(p.replace("\\", r"\\"), out, count=1)
    return out


def cau_ap_dung_mong_doi(cau, lua_chon):
    """Các câu 'áp dụng' chấp nhận được: cả câu đã điền + (đề hội thoại) riêng dòng có chỗ trống đã điền."""
    full = dien(cau, lua_chon)
    out = [full]
    lines = [x for x in re.split(r"\n|(?<=[」｣』])[\s　]+|[\s　]+(?=[①-⑳]|[A-ZＡ-Ｚ]\s*[:：])", cau or "") if x and x.strip()]
    if len(lines) > 1:
        out += [dien(x, lua_chon) for x in lines if BLANK_RE.search(x)]
        out.append("".join(dien(x, lua_chon) for x in lines))
    # bỏ nhãn người nói 'A:' / 'B:' / '男:' ở đầu dòng khi so
    return [re.sub(r"(?m)^\s*(?:[A-ZＡ-Ｚ]|[男女]の?人?|[^\s:：]{1,6})\s*[:：]\s*", "", x) for x in out] + out


def so_ap_dung(ap_dung, cau, lua_chon, cac_lua_chon=()):
    """Phân loại câu 'Áp dụng vào câu' so với câu đề đã điền lựa chọn:
    khop · kanji_kana (chỉ khác chữ Hán ↔ kana) · nhe (lệch ≤ 2 ký tự – lỗi gõ) · chep_nham (giống câu của lựa chọn khác) · nang."""
    if not ap_dung:
        return "khong_co", ""
    cands = cau_ap_dung_mong_doi(cau, lua_chon)
    if any(_eq(ap_dung, c) for c in cands):
        return "khop", ""
    if any(_eq_doc(ap_dung, c) for c in cands):
        return "kanji_kana", ""
    for lc in cac_lua_chon:
        if lc != lua_chon and any(_eq(ap_dung, c) for c in cau_ap_dung_mong_doi(cau, lc)):
            return "chep_nham", lc
    clean = lambda s: re.sub(r"[。\.．、,，\s　!！?？「」『』｢｣｡・…:：{}①-⑳]", "", strip_marks(s or ""))  # noqa: E731
    a, b = clean(cands[0]), clean(ap_dung)
    if _tok():
        a, b = _yomi(cands[0]) or a, _yomi(ap_dung) or b
    d = _khac(a, b)
    n = sum(max(len(x), len(y)) for x, y in d)
    return ("nhe" if n <= 2 else "nang"), "; ".join(f"'{x}'→'{y}'" for x, y in d[:3])


# ---------------- tách lời giải ### thành các phần (giai đoạn 0) ----------------
HEADERS = {"PHÂN TÍCH": "phan_tich", "LỰA CHỌN ĐÚNG": "lua_chon_dung", "THÔNG TIN THAM KHẢO": "tham_khao", "NGỮ PHÁP THAM KHẢO": "tham_khao"}
HEADER_RE = re.compile(r"(PHÂN TÍCH|LỰA CHỌN ĐÚNG|THÔNG TIN THAM KHẢO|NGỮ PHÁP THAM KHẢO)\s*[:：]?")      # chữ HOA – không nhầm với "phân tích" trong câu
NUM_LINE_RE = re.compile(r"^\s*\{?\s*([1-4])\s*\}?\s*[\.．]\s*(.*)$")
LCD_NUM_RE = re.compile(r"^\s*\{?\s*(\d)\s*\}?\s*[\.．]\s*(.*)$")
HEAD_LAB_RE = re.compile(r"(?i)^\s*[-+•]?\s*(cách đọc|nghĩa)\s*[:：]\s*(.*)$", re.S)
OPT_LAB_RE = re.compile(r"(?i)^\s*[-+•]{0,2}\s*(ý nghĩa|cấu trúc|áp dụng vào câu|áp dụng|nhận xét|về ngữ pháp|về ngữ nghĩa|nghĩa|cách đọc)\s*[:：]?\s*(.*)$", re.S)
LCD_LAB_RE = re.compile(r"(?i)^\s*[-+•]?\s*(câu hoàn chỉnh|nghĩa|cách đọc)\s*[:：]\s*(.*)$", re.S)
NP_RE = re.compile(r"(?i)^\s*(" + VERDICT_NP + r")(?![\wÀ-ỹ])[\s.,;:!。、]*(.*)$", re.S)
NN_RE = re.compile(r"(?i)^\s*(" + VERDICT_NN + r")(?![\wÀ-ỹ])[\s.,;:!。、]*(.*)$", re.S)
LAB_KEY = {"ý nghĩa": "y_nghia", "cấu trúc": "cau_truc", "áp dụng vào câu": "ap_dung", "áp dụng": "ap_dung", "nhận xét": "nhan_xet",
           "về ngữ pháp": "np", "về ngữ nghĩa": "nn", "nghĩa": "nghia", "cách đọc": "doc_ap_dung"}


def split_sections(text):
    """Văn bản ### đã chuẩn hóa → {dau, phan_tich, lua_chon_dung, sau_lcd}. Nhận tiêu đề cả khi thiếu ###;
    '###' chèn giữa các lựa chọn trong PHÂN TÍCH được gộp lại vào PHÂN TÍCH."""
    t = HEADER_RE.sub(lambda m: "\n###\n" + m.group(1) + "\n", text)
    blocks = [b.strip() for b in re.split(r"#{3,}", t)]
    out = {"dau": None, "phan_tich": None, "lua_chon_dung": None, "sau_lcd": None, "tham_khao": None}
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


FURI_VI_RE = re.compile(r"｜([^｜《》\n]*?[A-Za-zÀ-ỹĐđ][^｜《》\n]*?)《([^》\n]*)》")


def bo_furigana_chu_viet(text):
    """Bỏ furigana gắn lên chữ tiếng Việt / Latin (vd '- ｜Nhận xét《にんてい》:') – lỗi định dạng bản gốc.
    Trả (text, [(cũ, mới)])."""
    doi = []
    def _r(m):
        doi.append((m.group(0), m.group(1)))
        return m.group(1)
    return FURI_VI_RE.sub(_r, text), doi


TACH_DOC_RE = re.compile(r"(?<=[。．！？｣」])[ \t　]*(?=(?:Cách đọc|Nghĩa)\s*[:：])")


def tach_dong_cach_doc(text):
    """'…タイプだ。Cách đọc: …' (nhãn dính sau câu tiếng Nhật) → xuống dòng trước nhãn. Trả (text, số chỗ tách)."""
    return TACH_DOC_RE.subn("\n", text)


def text_without_ref(text):
    """Quy tắc THAM KHẢO (2026-10-07): lời giải bỏ phần THÔNG TIN / NGỮ PHÁP THAM KHẢO – dùng làm đầu vào GPT và chuẩn kiểm tra."""
    sec = split_sections(text)
    if sec["tham_khao"] is None:
        return text
    parts = [sec["dau"]] if sec["dau"] else []
    if sec["phan_tich"] is not None:
        parts.append("###\nPHÂN TÍCH\n" + sec["phan_tich"])
    if sec["lua_chon_dung"] is not None:
        parts.append("###\nLỰA CHỌN ĐÚNG\n" + sec["lua_chon_dung"])
    if sec["sau_lcd"]:
        parts.append("###\n" + sec["sau_lcd"])
    return "\n".join(parts)


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
            res[cur].append(m.group(2).strip())
            continue
        if cur == "cau" and not res["cau"]:
            m2 = re.match(r"(?i)^\s*(?:đề\s+)?(đề bài|câu hỏi|đề)\s*[·・]?\s*[:：]\s*", line)   # 12094_4: 'ĐỀ BÀI·:'; 13345_2: 'Đề Đề bài:'
            if m2 and line[m2.end():].strip():
                res["nhan_de"] = [m2.group(0).strip()]
                line = line[m2.end():]
        if cur == "cau" and res["cau"] and not re.search(r"[぀-ヿ㐀-鿿_＿]", line):
            cur = "khac"                       # dòng tiếng Việt chen giữa – không phải câu đề
        res[cur].append(line.strip())
    return {k: ("\n".join(v) if v else None) for k, v in res.items()}


def _new_item(so, lc, khop):
    return {"so": so, "lua_chon": lc, "lua_chon_khop": khop, "y_nghia": None, "cau_truc": None, "ap_dung": None, "nghia": None,
            "np": None, "np_note": None, "nn": None, "nn_note": None, "nhan_xet": None, "khac": None, "nhan_lap": False}


def _add(it, key, val):
    val = (val or "").strip()
    if not val:
        if it.get(key) is None and key in ("ap_dung", "nhan_xet"):
            it[key] = ""
        return
    it[key] = val if not it.get(key) else it[key] + "\n" + val


SPK_VI_RE = re.compile(r"^\s*[A-ZＡ-Ｚ]\s*[:：]")


def analysis_items(pt, lua_chon):
    """PHÂN TÍCH → (mo_dau, [item], ket_luan). item = {so, lua_chon, lua_chon_khop, y_nghia, cau_truc, ap_dung, nghia,
    np (True/False/None), np_note, nn, nn_note, nhan_xet, khac, nhan_lap}."""
    lines = [x for x in (pt or "").split("\n") if x.strip()]
    items, mo_dau, cur, prev = [], [], None, None
    for line in lines:
        line = re.sub(r"(?i)^(\s*[-+•]?\s*về) mặt (ngữ pháp|ngữ nghĩa)", r"\1 \2", line)   # dạng 09: 'Về mặt ngữ pháp'
        m = NUM_LINE_RE.match(line)
        if m:
            lc = m.group(2).strip()
            khop = next((j + 1 for j, o in enumerate(lua_chon) if _eq(lc, o)), None) or \
                next((j + 1 for j, o in enumerate(lua_chon) if _eq_doc(lc, o)), None)
            nxt = items[-1]["so"] + 1 if items else 1
            if khop or int(m.group(1)) == nxt:
                items.append(_new_item(int(m.group(1)), lc, khop))
                cur = prev = None
                continue
        if not items:
            mo_dau.append(line)
            continue
        it = items[-1]
        lm = OPT_LAB_RE.match(line)
        if lm and (":" in line[:lm.start(2)] or "：" in line[:lm.start(2)] or lm.group(1).lower() in ("về ngữ pháp", "về ngữ nghĩa")):
            key, val = LAB_KEY[lm.group(1).lower()], lm.group(2)
            # nhãn '+ Về ngữ pháp:' lặp lần 2 nhưng chữ đánh giá là kiểu ngữ nghĩa (Phù hợp / Không phù hợp…) → thực chất là '+ Về ngữ nghĩa:' (gõ nhầm nhãn – 4044)
            if key == "np" and it["np"] is not None and it["nn"] is None and re.match(r"(?i)\s*(không phù hợp|chưa phù hợp|phù hợp|không hợp lý|hợp lý|không tự nhiên|tự nhiên)\b", val or ""):
                key = "nn"
                it["nhan_np_la_nn"] = True
            if key == "y_nghia" and it["y_nghia"] and it["ap_dung"] is not None and it["nghia"] is None:
                key = "nghia"                       # '- Ý nghĩa:' thứ hai sau câu áp dụng = nghĩa của câu áp dụng
                it["y_nghia_la_nghia_cau"] = True
            if key == "np":
                v = NP_RE.match(val or "")
                if it["np"] is not None or it["np_note"]:
                    it["nhan_lap"] = True
                it["np"] = None if not v else not v.group(1).lower().startswith(("sai", "không"))
                _add(it, "np_note", v.group(2) if v else val)
                if not v and not (val or "").strip():
                    it["np_note"] = None
            elif key == "nn":
                v = NN_RE.match(val or "")
                if it["nn"] is not None or it["nn_note"]:
                    it["nhan_lap"] = True
                it["nn"] = None if not v else not v.group(1).lower().startswith(("không", "chưa", "sai"))
                _add(it, "nn_note", v.group(2) if v else val)
                if not v and not (val or "").strip():
                    it["nn_note"] = None
            elif key == "nghia":
                if it["nghia"] is not None:
                    it["nhan_lap"] = True
                    _add(it, {"np": "np_note", "nn": "nn_note"}.get(cur, cur) or "khac", line)
                    continue
                _add(it, "nghia", val)
                it["_nghia_rong"] = not (val or "").strip()      # 'Nghĩa:' để trống, nghĩa viết ở các dòng sau (đề hội thoại A: … / B: …)
                prev, cur = cur, "nghia"
                continue
            else:
                if it.get(key) and key not in ("nhan_xet",):
                    it["nhan_lap"] = True
                _add(it, key, val)
            prev, cur = cur, key
            continue
        # đánh giá viết ở dòng sau nhãn ('+ Về ngữ nghĩa:' ⏎ 'Sai. …')
        if cur in ("np", "nn") and it[cur] is None and not (it[cur + "_note"] or "").strip():
            v = (NP_RE if cur == "np" else NN_RE).match(line)
            if v:
                it[cur] = not v.group(1).lower().startswith(("sai", "không", "chưa"))
                it[cur + "_note"] = None
                _add(it, cur + "_note", v.group(2))
                continue
        # 'Nghĩa:' để trống → các dòng người nói (A: … / B: …) – hoặc dòng đầu tiên – là nghĩa câu
        if cur == "nghia" and it.get("_nghia_rong") and (SPK_VI_RE.match(line) or not (it["nghia"] or "").strip()):
            _add(it, "nghia", line)
            continue
        # dòng tiếng Nhật thuần sau 'Ý nghĩa/Cấu trúc' khi thiếu nhãn 'Áp dụng vào câu' → coi là câu áp dụng (09)
        if (it["ap_dung"] is None and cur in ("y_nghia", "cau_truc")
                and re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", line)
                and not re.search(r"[À-ỹa-zA-Z]", line)):
            _add(it, "ap_dung", line)
            prev, cur = cur, "ap_dung"
            continue
        # dòng không nhãn: nối vào nhãn đang mở (sau 'Nghĩa:' thì trở lại nhãn trước đó)
        tgt = cur
        if cur == "nghia":
            tgt = prev if prev not in (None, "nghia") else "khac"
            cur = tgt
        tgt = {"np": "np_note", "nn": "nn_note"}.get(tgt, tgt)
        _add(it, tgt or "khac", line)
    for it in items:
        it.pop("_nghia_rong", None)
    return "\n".join(mo_dau), items


def lcd_part(lcd):
    """LỰA CHỌN ĐÚNG → {so, lua_chon, hoan_chinh, nghia, khac}."""
    res = {"so": None, "lua_chon": None, "hoan_chinh": None, "nghia": None, "khac": None}
    cur = None
    for line in [x for x in (lcd or "").split("\n") if x.strip()]:
        m = LCD_NUM_RE.match(line)
        if m and res["so"] is None and not LCD_LAB_RE.match(line):
            res["so"], res["lua_chon"] = int(m.group(1)), m.group(2).strip()
            cur = None
            continue
        lm = LCD_LAB_RE.match(line)
        if lm:
            key = {"câu hoàn chỉnh": "hoan_chinh", "nghĩa": "nghia", "cách đọc": "khac"}[lm.group(1).lower()]
            if res[key] is None:
                res[key] = lm.group(2).strip()
                cur = key
                continue
        if cur == "hoan_chinh" and re.search(r"[぀-ヿ㐀-鿿]", line) and not re.search(r"[À-ỹ]", line):
            res["hoan_chinh"] += "\n" + line.strip()
            continue
        if cur == "nghia" and not re.search(r"[぀-ヿ㐀-鿿]", line) and re.match(r"^\s*\S{1,10}\s*[:：]", line):
            res["nghia"] += "\n" + line.strip()
            continue
        res["khac"] = line.strip() if not res["khac"] else res["khac"] + "\n" + line.strip()
        cur = "khac"
    return res


def doc_tu_furigana(cau):
    """Cách đọc ghép từ furigana của câu đề: chỉ khi furigana phủ hết mọi chữ Hán (không còn chữ Hán ngoài ｜《》)."""
    if not cau or "《" not in cau:
        return None
    doc = _doc_furi(cau).replace("{", "").replace("}", "")
    return None if re.search(r"[㐀-鿿々〆]", doc) else doc


# ---------------- gắn cờ (giai đoạn 0) ----------------
FLAG_TEXT = {
    "doc_tu_furigana": "Không có dòng 'Cách đọc:' – Python ghép cách đọc câu đề từ furigana (phủ hết chữ Hán)",
    "khong_cach_doc": "Không có dòng 'Cách đọc:' và không ghép được từ furigana (question.reading = null)",
    "khong_nghia_de": "Không có dòng 'Nghĩa:' của câu đề",
    "hoi_thoai": "Đề hội thoại / nhiều dòng",
    "hai_cho_trong": "Đề có 2 chỗ trống (lựa chọn dạng 'X/Y')",
    "co_cau_truc_chung": "PHÂN TÍCH có đoạn trước lựa chọn 1 (Cấu trúc chung → analysis.intro)",
    "co_tham_khao": "Có phần THÔNG TIN / NGỮ PHÁP THAM KHẢO – Python tách nguyên văn vào reference_raw (quy tắc 2026-10-07: không gửi GPT, không kiểm tra, không dịch)",
    "nhan_de_bai": "Câu đề trong lời giải có nhãn 'Đề bài:' ở đầu (question.ja không chép nhãn)",
    "y_nghia_la_nghia_cau": "Có lựa chọn ghi nghĩa câu áp dụng bằng nhãn '- Ý nghĩa:' thứ hai (→ applied.meaning)",
    "so_dong_pt_khac_4": "Phần PHÂN TÍCH không có đúng 4 lựa chọn đánh số",
    "thu_tu_pt_lech": "Số thứ tự trong PHÂN TÍCH không khớp thứ tự lựa chọn của đề",
    "lua_chon_khac_de": "Dòng lựa chọn trong PHÂN TÍCH viết khác lựa chọn của đề",
    "ap_dung_lech_nhe": "Câu 'Áp dụng vào câu' lệch 1–2 ký tự so với câu đề đã điền lựa chọn (nghi lỗi gõ → sửa định dạng)",
    "ap_dung_lech_nang": "Câu 'Áp dụng vào câu' khác câu đề đã điền lựa chọn (nghi lỗi nội dung → Claude xem, gắn cờ cau_khac_de)",
    "thieu_ap_dung": "Có lựa chọn không có 'Áp dụng vào câu'",
    "thieu_danh_gia_ngu_phap": "Có lựa chọn không có dòng 'Về ngữ pháp'",
    "danh_gia_khong_ro": "Có dòng 'Về ngữ pháp' / 'Về ngữ nghĩa' không bắt đầu bằng Đúng/Sai/Phù hợp/Không phù hợp",
    "nhan_lap": "Một lựa chọn có nhãn lặp (2 dòng 'Nghĩa:' / 'Về ngữ pháp' …)",
    "dap_an_khong_dat": "Lời giải KHÔNG chấm đáp án là 'Đúng' + 'Phù hợp' (nghi đáp án / lời giải)",
    "lua_chon_sai_ca_hai_dung": "Có lựa chọn không phải đáp án được chấm cả 'Đúng' + 'Phù hợp' (nghi 2 đáp án)",
    "hoan_chinh_khac_de": "'Câu hoàn chỉnh' khác câu đề đã điền đáp án",
    "lcd_go_nham_so": "Số trong LỰA CHỌN ĐÚNG gõ nhầm (vd '5.') nhưng nội dung đúng là đáp án của đề (→ sửa định dạng)",
    "lech_dap_an": "LỰA CHỌN ĐÚNG ghi đáp án khác dap_an_so của đề",
    "khong_so_lcd": "LỰA CHỌN ĐÚNG không có số thứ tự",
    "lcd_co_nhan_xet": "LỰA CHỌN ĐÚNG có thêm câu chữ ngoài số / Câu hoàn chỉnh / Nghĩa (→ correct.note)",
    "thieu_phan_tich": "Thiếu phần PHÂN TÍCH",
    "thieu_lua_chon_dung": "Thiếu phần LỰA CHỌN ĐÚNG",
    "co_doan_sau_lcd": "Có đoạn không tiêu đề sau LỰA CHỌN ĐÚNG",
    "thieu_dau_phan_cach": "Tiêu đề phần dính vào phần trước (thiếu ###)",
    "de_gach_chan": "Đề có gạch chân / { }",
    "danh_dau_rac": "Bản gốc có đoạn in đậm / gạch chân rỗng hoặc chỉ là dấu câu (đã bỏ thẻ)",
    "co_furigana": "Có furigana",
    "ruby_hong": "Có ruby hỏng trong bản gốc",
    "ky_hieu_trung": "Bản gốc có sẵn ký hiệu ｜《》 (trùng ký hiệu furigana)",
}
CTV_FLAGS = ("thu_tu_pt_lech", "lech_dap_an", "danh_dau_rac", "dap_an_khong_dat", "lua_chon_sai_ca_hai_dung")
FURI_SKIP = []


def parse_and_flag(text, raw_html, lua_chon, dap_an_so, de_html):
    """Tách phần + gắn cờ + ghi chú bản gốc. Trả về (phan, co, ghi_chu)."""
    sec = split_sections(text)
    hd = head_part(sec["dau"])
    mo, items = analysis_items(sec["phan_tich"], lua_chon)
    lcd = lcd_part(sec["lua_chon_dung"])
    co, gc = [], []
    from pipeline_chung.normalize import normalize_html
    cau_de = normalize_html((de_html or "").split("\x00")[0])[0].replace("{", "").replace("}", "")
    cau = hd["cau"] or cau_de
    dap = int(dap_an_so) if str(dap_an_so).isdigit() else None
    # cách đọc câu đề
    doc_furi = None
    if hd["doc"] is None:
        doc_furi = doc_tu_furigana(hd["cau"])
        co.append("doc_tu_furigana" if doc_furi else "khong_cach_doc")
        if doc_furi:
            gc.append("[Cách đọc ghép từ furigana] Lời giải gốc không có dòng 'Cách đọc:' – cách đọc câu đề do Python ghép từ furigana của bản gốc")
    if hd["nghia"] is None:
        co.append("khong_nghia_de")
    if "\n" in (hd["cau"] or "") or re.search(r"(?m)^\s*[A-ZＡ-Ｚ]\s*[:：]", hd["cau"] or ""):
        co.append("hoi_thoai")
    if len(BLANK_RE.findall(cau)) >= 2 or any(re.search(r"[/／]", x) for x in lua_chon):
        co.append("hai_cho_trong")
    if hd.get("nhan_de"):
        co.append("nhan_de_bai")
        gc.append(f"[Bản gốc VI] Câu đề trong lời giải có nhãn '{hd['nhan_de']}' ở đầu (đã bỏ khi so – question.ja không chép nhãn này)")
    if any(it.get("y_nghia_la_nghia_cau") for it in items):
        co.append("y_nghia_la_nghia_cau")
    if mo.strip():
        co.append("co_cau_truc_chung")
    if sec["phan_tich"] is not None and len(items) != 4:
        co.append("so_dong_pt_khac_4")
    if any(it["lua_chon_khop"] and it["lua_chon_khop"] != it["so"] for it in items):
        co.append("thu_tu_pt_lech")
        gc.append("[Bản gốc VI] Số thứ tự trong PHÂN TÍCH không khớp thứ tự lựa chọn của đề")
    for it in items:
        j = it["lua_chon_khop"] or it["so"]
        if not it["lua_chon_khop"] and 1 <= it["so"] <= 4:
            co.append("lua_chon_khac_de")
            gc.append(f"[Bản gốc VI] Lựa chọn {it['so']} trong PHÂN TÍCH viết khác đề: '{strip_marks(it['lua_chon'])}' ↔ đề '{lua_chon[it['so'] - 1]}'")
        if it["ap_dung"] is None:
            co.append("thieu_ap_dung")
        elif 1 <= j <= 4:
            kq, ct = so_ap_dung(it["ap_dung"], cau, lua_chon[j - 1], lua_chon)
            it["so_de"] = kq
            if kq == "nhe":
                co.append("ap_dung_lech_nhe")
                gc.append(f"[Bản gốc VI] Lựa chọn {j}: câu 'Áp dụng' lệch nhẹ so với đề ({ct}) – nghi lỗi gõ")
            elif kq in ("nang", "chep_nham"):
                co.append("ap_dung_lech_nang")
                gc.append(f"[Bản gốc VI] Lựa chọn {j}: câu 'Áp dụng' khác câu đề đã điền lựa chọn"
                          + (f" – giống câu của lựa chọn '{ct}'" if kq == "chep_nham" else f" ({ct})"))
        if it["np"] is None and it["np_note"] is None:
            co.append("thieu_danh_gia_ngu_phap")
        if (it["np_note"] is not None and it["np"] is None) or (it["nn_note"] is not None and it["nn"] is None):
            co.append("danh_gia_khong_ro")
        if it["nhan_lap"]:
            co.append("nhan_lap")
        if dap and j == dap and not (it["np"] in (True, None) and it["nn"] is True):
            co.append("dap_an_khong_dat")
        if dap and j != dap and it["np"] is True and it["nn"] is True:
            co.append("lua_chon_sai_ca_hai_dung")
    for k, name in (("phan_tich", "PHÂN TÍCH"), ("lua_chon_dung", "LỰA CHỌN ĐÚNG")):
        if not (sec[k] or "").strip():
            co.append("thieu_" + k)
            gc.append(f"[Bản gốc VI] Thiếu phần {name}")
    if sec["sau_lcd"]:
        co.append("co_doan_sau_lcd")
    if lcd["khac"]:
        co.append("lcd_co_nhan_xet")
    if sec["lua_chon_dung"] and lcd["so"] is None:
        co.append("khong_so_lcd")
    elif lcd["so"] is not None and dap and lcd["so"] != dap:
        if lcd["lua_chon"] and _eq_doc(lcd["lua_chon"], lua_chon[dap - 1]):
            co.append("lcd_go_nham_so")
            gc.append(f"[Bản gốc VI] LỰA CHỌN ĐÚNG ghi số {lcd['so']} nhưng nội dung là đáp án {dap} – nghi gõ nhầm số")
        else:
            co.append("lech_dap_an")
            gc.append(f"[Bản gốc VI] LỰA CHỌN ĐÚNG ghi {lcd['so']}. {lcd['lua_chon']}, khác đáp án của đề (dap_an_so = {dap_an_so})")
    if lcd["hoan_chinh"] and dap:
        kq, ct = so_ap_dung(lcd["hoan_chinh"], cau, lua_chon[dap - 1], lua_chon)
        if kq not in ("khop", "kanji_kana"):
            co.append("hoan_chinh_khac_de")
            gc.append(f"[Bản gốc VI] 'Câu hoàn chỉnh' khác câu đề đã điền đáp án ({ct or kq})")
    if re.search(r"[^\n#\s]\s*(?:PHÂN TÍCH|LỰA CHỌN ĐÚNG)", re.sub(r"<[^>]+>", "", raw_html or "")):
        co.append("thieu_dau_phan_cach")
    if re.search(r"<u\b|underline|｛|\{", de_html or "", re.I):
        co.append("de_gach_chan")
    if sec["tham_khao"]:
        co.append("co_tham_khao")
    phan = {"tham_khao": sec["tham_khao"], "dau": hd, "cau_de": cau_de, "doc_furigana": doc_furi, "phan_tich": {"mo_dau": mo, "dong": items},
            "lcd": lcd, "sau_lcd": sec["sau_lcd"]}
    return phan, sorted(set(co)), gc


# ---------------- kiểm tra riêng giai đoạn 1: K1–K13 (K8/K9 = trung thành với bản gốc: chép câu Nhật đúng lời giải / đủ chữ – Python kiểm tra trên bản đã hoàn tác chỗ sửa định dạng) ----------------
READING_OK = re.compile(r"^[぀-ゟ゠-ヿー・\s/、,，。．！？!?「」『』（）()0-9０-９~〜…\-－―_＿　:：A-Za-zＡ-Ｚ]+$")


def _segs(s):
    from pipeline_chung.normalize import mark_segments
    return mark_segments(s)


def _v(o):
    return (o or {}).get("vi") if o else None


def opt_text(o):
    """Toàn bộ chữ tiếng Việt của một lựa chọn."""
    a = o.get("applied") or {}
    return "\n".join(x for x in (_v(o.get("meaning")), _v(o.get("structure")), _v(a.get("meaning")), _v(o.get("grammar_note")),
                                 _v(o.get("semantic_note")), _v(o.get("other"))) if x)


def _k(t):
    return re.sub(r"[\s　]", "", norm_ja(t or ""))


def _cover(src_text, out_text):
    from pipeline_chung.common import vi_words
    s, o = collections.Counter(vi_words(src_text or "")), collections.Counter(vi_words(out_text or ""))
    if not s:
        return 1.0, []
    return sum((s & o).values()) / sum(s.values()), [w for w, _ in (s - o).most_common(8)]


def check_k(doc, norm, policy):
    loi, canh_bao = [], []
    de, phan = norm["de"], norm.get("phan") or {}
    an, q, c = doc.get("analysis") or {}, doc.get("question") or {}, doc.get("correct") or {}
    opts = an.get("options") or []
    dap = int(de["dap_an_so"]) if str(de["dap_an_so"]).isdigit() else None
    hd = phan.get("dau") or {}
    # K8 – câu đề / cách đọc / nghĩa
    if hd.get("cau") and _k(q.get("ja")) != _k(hd["cau"]):
        loi.append(f"K8: question.ja khác dòng câu đề của lời giải '{hd['cau'][:60]}'")
    doc_mong = hd.get("doc") or phan.get("doc_furigana")
    if (doc_mong is None) != (q.get("reading") is None):
        loi.append("K8: question.reading phải null khi và chỉ khi lời giải không có dòng 'Cách đọc:' và không ghép được từ furigana"
                   + (f" (cách đọc ghép từ furigana: '{phan['doc_furigana']}')" if phan.get("doc_furigana") else ""))
    elif doc_mong and _k(q.get("reading")) != _k(doc_mong):
        loi.append(f"K8: question.reading khác {'dòng Cách đọc' if hd.get('doc') else 'cách đọc ghép từ furigana'}: '{doc_mong[:60]}'")
    if (hd.get("nghia") is None) != (q.get("meaning") is None):
        loi.append("K8: question.meaning phải null khi và chỉ khi lời giải không có dòng 'Nghĩa:' của câu đề")
    elif hd.get("nghia"):
        cv, miss = _cover(hd["nghia"], _v(q.get("meaning")))
        if cv < 0.97:
            loi.append(f"K8: question.meaning thiếu chữ so với bản gốc: {miss}")
        nb = len(BLANK_RE.findall(hd["nghia"]))
        if nb and len(BLANK_RE.findall(_v(q.get("meaning")) or "")) != nb:
            loi.append("K8: question.meaning phải giữ nguyên chỗ trống như bản gốc")
    if (hd.get("khac") is None) != (doc.get("question_note") is None):
        canh_bao.append("K8: question_note: bản gốc " + ("có" if hd.get("khac") else "không có") + " câu chữ khác ở phần đầu nhưng JSON "
                        + ("null" if doc.get("question_note") is None else "có"))
    # K1
    if [o.get("index") for o in opts] != [1, 2, 3, 4]:
        loi.append(f"K1: analysis.options phải có đủ 4 lựa chọn theo thứ tự 1–4 (đang có {[o.get('index') for o in opts]})")
    src = {}
    for it in (phan.get("phan_tich") or {}).get("dong", []):
        src.setdefault(it["lua_chon_khop"] or it["so"], it)
    for o in opts:
        i = o.get("index")
        if not isinstance(i, int) or not 1 <= i <= 4:
            continue
        it, ap = src.get(i), o.get("applied")
        # K2 – lựa chọn chép đúng dòng 'i. …' của lời giải
        if it is not None and _k(o.get("option_ja")) != _k(it["lua_chon"]):
            loi.append(f"K8: lựa chọn {i}: option_ja '{o.get('option_ja')}' khác dòng lựa chọn của lời giải '{it['lua_chon']}'")
        elif it is None and not _eq(o.get("option_ja"), de["lua_chon"][i - 1]):
            loi.append(f"K2: lựa chọn {i}: lời giải không có lựa chọn này – option_ja phải chép đúng lựa chọn của đề '{de['lua_chon'][i - 1]}'")
        if it is None:
            continue
        # K3 – câu áp dụng
        if (it["ap_dung"] is None) != (ap is None):
            loi.append(f"K3: lựa chọn {i}: applied phải null khi và chỉ khi lời giải không có '- Áp dụng vào câu:'")
        elif ap is not None:
            if it["ap_dung"] and _k(ap.get("ja")) != _k(it["ap_dung"]):
                loi.append(f"K8: lựa chọn {i}: applied.ja khác câu 'Áp dụng vào câu' của lời giải '{it['ap_dung'][:60]}'")
            if _segs(ap.get("ja") or "") != _segs(it["ap_dung"] or ""):
                loi.append(f"K5: lựa chọn {i}: đánh dấu {{ }} của applied.ja khác lời giải")
            if (it["nghia"] is None) != (ap.get("meaning") is None):
                loi.append(f"K4: lựa chọn {i}: applied.meaning phải null khi và chỉ khi lựa chọn không có dòng 'Nghĩa:'")
        elif it["nghia"] is not None:
            loi.append(f"K4: lựa chọn {i}: bản gốc có dòng 'Nghĩa:' nhưng applied = null")
        # K7 – đánh giá ngữ pháp / ngữ nghĩa
        if it["np"] is not None and o.get("grammar_ok") is not it["np"]:
            loi.append(f"K7: lựa chọn {i}: grammar_ok phải là {it['np']} (lời giải: Về ngữ pháp: {'Đúng' if it['np'] else 'Sai'})")
        if it["np"] is None and it["np_note"] is None and o.get("grammar_ok") is not None:
            loi.append(f"K7: lựa chọn {i}: lời giải không có dòng 'Về ngữ pháp' – grammar_ok phải là null")
        if it["nn"] is not None and o.get("semantic_ok") is not it["nn"]:
            loi.append(f"K7: lựa chọn {i}: semantic_ok phải là {it['nn']} (lời giải: Về ngữ nghĩa: {'Phù hợp' if it['nn'] else 'Không phù hợp'})")
        if it["nn"] is None and it["nn_note"] is None and o.get("semantic_ok") is not None:
            loi.append(f"K7: lựa chọn {i}: lời giải không có dòng 'Về ngữ nghĩa' – semantic_ok phải là null")
        # K12 – các trường chữ: có trong bản gốc thì không null
        for key, name, lab in (("y_nghia", "meaning", "Ý nghĩa"), ("cau_truc", "structure", "Cấu trúc"),
                               ("np_note", "grammar_note", "Về ngữ pháp (phần giải thích)"), ("nn_note", "semantic_note", "Về ngữ nghĩa (phần giải thích)")):
            if it[key] and o.get(name) is None:
                loi.append(f"K12: lựa chọn {i}: bản gốc có '{lab}' nhưng {name} = null")
            if not it[key] and o.get(name) is not None and key in ("y_nghia", "cau_truc"):
                loi.append(f"K12: lựa chọn {i}: bản gốc không có '{lab}' nhưng {name} khác null")
        # K9 – đủ chữ
        srcv = "\n".join(x for x in (it["y_nghia"], it["cau_truc"], it["nghia"], it["np_note"], it["nn_note"], it["nhan_xet"], it["khac"]) if x)
        cv, miss = _cover(srcv, opt_text(o))
        if cv < 0.97:
            loi.append(f"K9: lựa chọn {i}: thiếu chữ so với bản gốc: {miss}")
    # K11 – đáp án theo đánh giá của lời giải
    if dap and 1 <= dap <= len(opts):
        od = opts[dap - 1]
        if od.get("grammar_ok") is False or od.get("semantic_ok") is False:
            canh_bao.append(f"K11: đáp án (lựa chọn {dap}) bị lời giải chấm Sai / Không phù hợp – nghi lỗi nội dung (quy tắc 3d-6)")
        for o in opts:
            if o.get("index") != dap and o.get("grammar_ok") is True and o.get("semantic_ok") is True:
                canh_bao.append(f"K11: lựa chọn {o.get('index')} (không phải đáp án) được chấm 'Đúng' + 'Phù hợp' – nghi 2 đáp án (quy tắc 3d-6)")
    # K6 – LỰA CHỌN ĐÚNG
    lcd = phan.get("lcd") or {}
    if str(c.get("index")) != str(de["dap_an_so"]):
        loi.append(f"K6: correct.index = {c.get('index')} khác dap_an_so = {de['dap_an_so']}")
    elif {"lech_dap_an", "khong_so_lcd", "lcd_go_nham_so"} & set(norm["co"]):
        canh_bao.append(f"K6: lời giải gốc ghi số đáp án khác đề / không ghi số – JSON đã theo dap_an_so = {de['dap_an_so']}")
    di = c.get("index")
    if isinstance(di, int) and 1 <= di <= len(opts) and c.get("option_ja") != opts[di - 1].get("option_ja"):
        loi.append(f"K6: correct.option_ja phải giống hệt options[{di - 1}].option_ja")
    fs = c.get("full_sentence") or {}
    if lcd.get("hoan_chinh") is not None and _k(fs.get("ja")) != _k(lcd["hoan_chinh"]):
        loi.append(f"K8: correct.full_sentence.ja khác 'Câu hoàn chỉnh' của lời giải '{lcd['hoan_chinh'][:60]}'")
    if lcd.get("hoan_chinh") is None and lcd and (phan.get("lcd") or {}).get("so") is not None:
        canh_bao.append("K6: lời giải không có 'Câu hoàn chỉnh' – xem full_sentence.ja lấy từ đâu (phải là câu áp dụng của đáp án)")
    if (lcd.get("nghia") is None) != (fs.get("meaning") is None):
        loi.append("K6: correct.full_sentence.meaning phải null khi và chỉ khi LỰA CHỌN ĐÚNG không có dòng 'Nghĩa:'")
    elif lcd.get("nghia"):
        cv, miss = _cover(lcd["nghia"], _v(fs.get("meaning")))
        if cv < 0.97:
            loi.append(f"K9: correct.full_sentence.meaning thiếu chữ: {miss}")
    # K13 – đoạn chữ khác trong LỰA CHỌN ĐÚNG
    note = "\n".join(x for x in (lcd.get("khac"), phan.get("sau_lcd")) if x)
    if bool(note.strip()) != (c.get("note") is not None or an.get("conclusion") is not None):
        canh_bao.append("K13: correct.note / analysis.conclusion: bản gốc " + ("có" if note.strip() else "không có")
                        + " đoạn chữ khác trong / sau LỰA CHỌN ĐÚNG – xem lại")
    # K-TK – quy tắc THAM KHẢO 2026-10-07: reference_raw = nguyên văn (Python điền)
    loi += TK.kiem_tra(doc, phan.get("tham_khao"))
    # K10 – Cấu trúc chung
    mo = (phan.get("phan_tich") or {}).get("mo_dau") or ""
    if bool(mo.strip()) != (an.get("intro") is not None):
        loi.append(f"K10: analysis.intro: bản gốc {'có' if mo.strip() else 'không có'} đoạn trước lựa chọn 1 nhưng JSON "
                   f"{'null' if an.get('intro') is None else 'có'}")
    elif mo.strip():
        cv, miss = _cover(mo, _v(an.get("intro")))
        if cv < 0.97:
            loi.append(f"K9: analysis.intro thiếu chữ: {miss}")
    return loi, canh_bao


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


def is_style_field(path):
    """Trường dịch từ tiếng Việt (giải thích) – kiểm tra văn phong; nghĩa câu (dịch từ tiếng Nhật) thì không."""
    p = path if isinstance(path, str) else path_str(path)
    # structure = công thức ('명사 + ⟪を⟫ + 타동사') – không phải câu văn, không kiểm tra -습니다
    return not re.search(r"question\.meaning|applied\.meaning|full_sentence\.meaning|\.structure", p)


# ---------------- hiển thị cho Excel CTV (dựng lại đúng thứ tự format) ----------------
def _t(obj, lang):
    return show((obj or {}).get(lang) or "") if obj else ""


def render(d, lang):
    q, an, c = d.get("question") or {}, d.get("analysis") or {}, d.get("correct") or {}
    out = [f"{bold('【Câu hỏi】')} {show(q.get('ja', ''))}"]
    if q.get("reading"):
        out.append(f"   Cách đọc: {show(q['reading'])}")
    if q.get("meaning"):
        out.append(f"   Nghĩa: {_t(q['meaning'], lang)}")
    if d.get("question_note"):
        out.append(_t(d["question_note"], lang))
    out.append(bold("【PHÂN TÍCH】"))
    if an.get("intro"):
        out.append(f"{bold('【Cấu trúc chung】')} " + _t(an["intro"], lang))
    for o in an.get("options", []):
        out.append(bold(f"{o.get('index')}. ") + show(o.get("option_ja", "")))
        if o.get("other"):
            out.append("   " + _t(o["other"], lang).replace("\n", "\n   "))
        if o.get("meaning"):
            out.append("   - Ý nghĩa: " + _t(o["meaning"], lang).replace("\n", "\n   "))
        if o.get("structure"):
            out.append("   - Cấu trúc: " + _t(o["structure"], lang).replace("\n", "\n   "))
        ap = o.get("applied")
        if ap:
            out.append("   - Áp dụng vào câu: " + show(ap.get("ja", "")))
        if o.get("grammar_ok") is not None or o.get("grammar_note"):
            v = {True: "Đúng.", False: "Sai.", None: ""}[o.get("grammar_ok")]
            out.append(("   + Về ngữ pháp: " + v + " " + _t(o.get("grammar_note"), lang).replace("\n", "\n   ")).rstrip())
        if ap and ap.get("meaning"):
            out.append("   Nghĩa: " + _t(ap["meaning"], lang))
        if o.get("semantic_ok") is not None or o.get("semantic_note"):
            v = {True: "Phù hợp.", False: "Không phù hợp.", None: ""}[o.get("semantic_ok")]
            out.append(("   + Về ngữ nghĩa: " + v + " " + _t(o.get("semantic_note"), lang).replace("\n", "\n   ")).rstrip())
    if an.get("conclusion"):
        out.append(_t(an["conclusion"], lang))
    out.append(bold("【LỰA CHỌN ĐÚNG】"))
    out.append(f"{c.get('index')}. {show(c.get('option_ja', ''))}")
    fs = c.get("full_sentence") or {}
    if fs.get("ja"):
        out.append(f"Câu hoàn chỉnh: {show(fs['ja'])}")
    if fs.get("meaning"):
        out.append(f"Nghĩa: {_t(fs['meaning'], lang)}")
    if c.get("note"):
        out.append(_t(c["note"], lang))
    out += TK.render(d, lang, show, bold)               # quy tắc THAM KHẢO: nguyên văn, chỉ hiện ở bản Việt, không dịch
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




def sudachi_hints(norm):
    """Gợi ý cho bước 1.2 (Claude xác nhận rồi mới gắn cờ):
    R1 – dòng 'Cách đọc:' của câu đề khác cách đọc từ điển của câu tiếng Nhật (bỏ qua câu có số / chữ Latin, cách đọc ghép từ furigana).
    A  – câu 'Áp dụng vào câu' / 'Câu hoàn chỉnh' lệch câu đề đã điền lựa chọn (phân loại nhẹ / nặng)."""
    if not norm.get("phan"):
        return []
    ph = norm["phan"]
    hd = ph.get("dau") or {}
    out = []
    ja, doc = hd.get("cau"), hd.get("doc")
    if _tok() and ja and doc and not re.search(r"[㐀-鿿]", strip_marks(doc)) \
            and not re.search(r"[0-9０-９A-Za-zＡ-Ｚａ-ｚ]", strip_marks(ja) + doc):
        a = _seion(_yomi(BLANK_RE.sub("", ja)))
        b = _seion(_yomi_kana(BLANK_RE.sub("", doc)))
        if a and b and a != b:
            diff = _khac(a, b)
            n = sum(len(x) + len(y) for x, y in diff)
            if n >= 2:
                out.append("R1: câu đề – cách đọc lệch từ điển ở: " + "; ".join(f"'{x}'→'{y}'" for x, y in diff[:3]) if n <= 12
                           else "R1: câu đề – cách đọc lệch nhiều so với câu tiếng Nhật (xem lại cả dòng)")
    for x in norm.get("ghi_chu_ban_goc") or []:
        if "câu 'Áp dụng'" in x or "Câu hoàn chỉnh" in x:
            out.append("A: " + x.replace("[Bản gốc VI] ", ""))
    return out


# =====================================================================================================
# ================  DẠNG 09 – NGỮ PHÁP THEO ĐOẠN VĂN: phần riêng (dựng 2026-10-08)  ===================
# =====================================================================================================
NHAN_DAM_09_RE = re.compile(r"\{\s*((?:ĐỀ BÀI|Đề bài|NGHĨA|Nghĩa|CÁCH ĐỌC|Cách đọc|PHÂN TÍCH|LỰA CHỌN ĐÚNG)\s*[:：]?)\s*\}?")


def bo_dam_nhan(text):
    """Bỏ { } (in đậm) quanh nhãn '{ĐỀ BÀI}:' / '{NGHĨA}:' / '{PHÂN TÍCH}' … – trình bày, không phải nội dung. Trả (text, số chỗ)."""
    return NHAN_DAM_09_RE.subn(r"\1", text)


LIEN_DONG_RE = re.compile(
    r"[ \t]*(?=(?:Cách đọc|CÁCH ĐỌC|Nghĩa|NGHĨA)\s*[:：])"
    r"|[ \t]*(?=###)|(?<=###)[ \t]*"
    r"|[ \t]*(?=(?:PHÂN TÍCH|LỰA CHỌN ĐÚNG)(?![a-zà-ỹ]))"
    r"|(?<=PHÂN TÍCH)[ \t]*(?=\d)|(?<=LỰA CHỌN ĐÚNG)[ \t]*(?=\d)"
    r"|[ \t]*(?=[-+]\s*(?:Ý nghĩa|Cấu trúc|Áp dụng vào câu|Nhận xét|Về (?:mặt )?ngữ pháp|Về (?:mặt )?ngữ nghĩa)\s*[:：])"
    r"|(?<=[。.!?！？])[ \t]*(?=[2-4][\.．]\s*\S)"
    r"|[ \t]*(?=Câu hoàn chỉnh\s*[:：])")


LIEN_DONG_DINH_RE = re.compile(r"###[ \t]*(?:PHÂN TÍCH|LỰA CHỌN)|PHÂN TÍCH[ \t]*1[\.．]|LỰA CHỌN ĐÚNG[ \t]*[1-4][\.．]")


def tach_dong_lien(text):
    """Lời giải viết liền một dòng (vd 12673: 'Đề bài: …Cách đọc: …###PHÂN TÍCH1. …- Ý nghĩa: …') → xuống dòng trước nhãn.
    Chỉ áp dụng khi lời giải có rất ít dòng. Trả (text, số chỗ)."""
    if text.count("\n") >= 8 and not LIEN_DONG_DINH_RE.search(text):   # nhiều dòng nhưng vẫn dính '###PHÂN TÍCH1.' (12687_1) → vẫn tách
        return text, 0
    out, n = LIEN_DONG_RE.subn("\n", text)
    out = re.sub(r"\n{2,}", "\n", out)
    return out.strip(), n


CHU_THICH_RE = r"[(（]\s*注\s*[0-9０-９]*\s*[)）]|※\s*[0-9０-９]*"


# ---------------- K-ĐV: câu đề trong lời giải ↔ đoạn văn gốc ----------------
def _fdv(s):
    s = strip_marks(s or "").replace("{", "").replace("}", "")
    s = O_RE.sub("", s)
    s = re.sub(r"[(（][぀-ゟ゠-ヿー]+[)）]", "", s)           # cách đọc trong ngoặc: 会社(かいしゃ)
    s = re.sub(CHU_THICH_RE, "", s)                         # ký hiệu chú thích (注2)
    s = norm_ja(s)
    return re.sub(r"[。\.．、,，\s　!！?？「」『』｢｣｡・’'\"…:：~〜\-－―]", "", s).replace("ー", "一")


def so_doan_van(cau, doan_van):
    """So câu đề (đoạn trích) trong lời giải với đoạn văn gốc.
    → (khop | khop_doc | lech_nhe | lech_nang | khong_tim_thay | khong_co, chi_tiet)."""
    import difflib
    fc, fp = _fdv(cau), _fdv(doan_van)
    if not fc or not fp:
        return "khong_co", ""
    if fc in fp:
        return "khop", ""
    sm = difflib.SequenceMatcher(None, fp, fc, autojunk=False)
    m = sm.find_longest_match(0, len(fp), 0, len(fc))
    if m.size < 3:
        return "khong_tim_thay", ""
    a0 = max(0, m.a - m.b - 10)
    a1 = min(len(fp), m.a - m.b + len(fc) + 10)
    win = fp[a0:a1]
    sm2 = difflib.SequenceMatcher(None, win, fc, autojunk=False)
    bl = [b for b in sm2.get_matching_blocks() if b.size]
    if not bl:
        return "khong_tim_thay", ""
    win = win[bl[0].a - bl[0].b if bl[0].a >= bl[0].b else 0: bl[-1].a + bl[-1].size + (len(fc) - bl[-1].b - bl[-1].size)]
    if _tok():
        try:
            if _yomi(win) == _yomi(fc):
                return "khop_doc", ""
        except Exception:                                          # noqa: BLE001
            pass
    d = _khac(win, fc)
    if _tok():                                   # chữ Hán ↔ kana cùng cách đọc (方 ↔ ほう) không tính là lệch
        def _cung_doc(x, y):
            try:
                return bool(x and y) and _yomi(x) == _yomi(y)
            except Exception:                                  # noqa: BLE001
                return False
        d = [(x, y) for x, y in d if not _cung_doc(x, y)]
    if not d:
        return "khop_doc", ""
    nchar = sum(max(len(x), len(y)) for x, y in d)
    ct = "; ".join(f"'{x}'→'{y}'" for x, y in d[:4])
    kana_only = all(re.fullmatch(r"[぀-ゟ゠-ヿー]*", x + y) for x, y in d)
    if nchar <= 3 and kana_only:
        return "lech_nhe", ct
    return "lech_nang", ct


# ---------------- thứ tự chạy theo đoạn văn ----------------
def tao_thu_tu_doan(recs, cfg):
    """25 đoạn đầu = 5 đoạn ngẫu nhiên mỗi cấp N1–N5 (xen kẽ), rồi các đoạn còn lại theo file dữ liệu; 4 câu của một đoạn liền nhau."""
    import random
    tc = cfg.get("thu_tu_chay") or {}
    rng = random.Random(tc.get("seed", 2026))
    n = tc.get("moi_cap_do_doan", 5)
    nhom, thu_tu_qid = {}, []
    for r in recs:
        if r["question_id"] not in nhom:
            thu_tu_qid.append(r["question_id"])
        nhom.setdefault(r["question_id"], []).append(r)
    for q in nhom:
        nhom[q].sort(key=lambda r: r["cau_con"])
    lv = {}
    for k in ["N1", "N2", "N3", "N4", "N5"]:
        pool = [q for q in thu_tu_qid if nhom[q][0]["cap_do"] == k and all(r["khuon_goc"] != "trong" for r in nhom[q])]
        rng.shuffle(pool)
        lv[k] = pool[:n]
    dau = [lv[k][i] for i in range(n) for k in ["N1", "N2", "N3", "N4", "N5"] if i < len(lv[k])]
    con = [q for q in thu_tu_qid if q not in set(dau)]
    rows = [r for q in dau + con for r in nhom[q]]
    return [{"stt": i + 1, "sample_id": r["sample_id"], "question_id": r["question_id"], "cap_do": r["cap_do"],
             "doan": (dau + con).index(r["question_id"]) + 1} for i, r in enumerate(rows)]


# ---------------- gắn cờ: bổ sung cho parse_and_flag của dạng 07 ----------------
FLAG_TEXT.update({
    "dap_an_de_loi": "Dữ liệu đề lỗi: dap_an_so không phải 1–4 (vd 53467_3: '33') – báo người dùng sửa dữ liệu gốc",
    "lien_dong": "Lời giải viết liền một dòng – Python đã xuống dòng trước các nhãn",
    "nhan_in_dam": "Nhãn in đậm ({ĐỀ BÀI} / {NGHĨA}…) – Python bỏ { }",
    "de_khop_doan_van": "Câu đề trong lời giải khớp đoạn văn gốc",
    "de_lech_doan_van_nhe": "Câu đề trong lời giải lệch nhẹ đoạn văn gốc (kana / ruby hỏng – nghi lỗi gõ → sửa định dạng)",
    "de_lech_doan_van_nang": "Câu đề trong lời giải KHÁC đoạn văn gốc (mất / khác chữ – nghi lỗi nội dung → gắn cờ cau_khac_de)",
    "de_khong_tim_thay_doan_van": "Không tìm thấy câu đề trong đoạn văn gốc (Claude đối chiếu tay)",
})
_parse_and_flag_07 = parse_and_flag


def parse_and_flag(text, raw_html, lua_chon, dap_an_so, de_html, doan_van=None):
    dap_hl = str(dap_an_so).strip() in ("1", "2", "3", "4")
    phan, co, gc = _parse_and_flag_07(text, raw_html, lua_chon, dap_an_so if dap_hl else "", de_html)
    if not dap_hl:
        co.append("dap_an_de_loi")
        gc.append(f"[Bản gốc VI] Dữ liệu đề lỗi: dap_an_so = '{dap_an_so}' (không phải 1–4) – cần sửa dữ liệu gốc trước khi chạy")
    cau = (phan.get("dau") or {}).get("cau")
    kq, ct = so_doan_van(cau, doan_van) if (cau and doan_van) else ("khong_co", "")
    phan["doan_van"] = {"ket_qua": kq, "chi_tiet": ct}
    if kq in ("lech_nhe", "lech_nang"):
        co.append("de_lech_doan_van_" + kq.split("_")[1])
        gc.append(f"[Bản gốc VI] Câu đề trong lời giải {'lệch nhẹ' if kq == 'lech_nhe' else 'khác'} đoạn văn gốc ({ct})")
    elif kq == "khong_tim_thay":
        co.append("de_khong_tim_thay_doan_van")
    # 'hoan_chinh_khac_de' của dạng 07 so với câu đề TRONG lời giải – dạng 09 vẫn dùng như vậy
    return phan, sorted(set(co)), gc


CTV_FLAGS = tuple(CTV_FLAGS) + ("de_lech_doan_van_nang",)
_sudachi_hints_07 = sudachi_hints


def sudachi_hints(norm):
    out = _sudachi_hints_07(norm)
    dv = (norm.get("phan") or {}).get("doan_van") or {}
    if dv.get("ket_qua") in ("lech_nhe", "lech_nang", "khong_tim_thay"):
        out.append(f"ĐV: câu đề ↔ đoạn văn gốc: {dv['ket_qua']}" + (f" – {dv['chi_tiet']}" if dv.get("chi_tiet") else ""))
    return out


_check_k_07 = check_k


def check_k(doc, norm, policy):
    loi, canh_bao = _check_k_07(doc, norm, policy)
    dv = (norm.get("phan") or {}).get("doan_van") or {}
    if dv.get("ket_qua") == "lech_nang":
        canh_bao.append(f"K-ĐV: câu đề trong lời giải khác đoạn văn gốc ({dv.get('chi_tiet')}) – mất / khác chữ → gắn cờ cau_khac_de (quy tắc 3d-9)")
    elif dv.get("ket_qua") == "lech_nhe":
        canh_bao.append(f"K-ĐV: câu đề lệch nhẹ đoạn văn ({dv.get('chi_tiet')}) – lỗi gõ / ruby hỏng → sửa định dạng")
    ps = doc.get("passage")
    mong = nhan_cho_trong(norm)
    if ps is None or ps.get("lines") != [] or ps.get("blank_label") != mong:
        loi.append(f"K-PS: passage phải là {{'blank_label': {mong!r}, 'lines': []}} (Python điền khi --nhan)")
    return loi, canh_bao


def nhan_cho_trong(norm):
    """Nhãn chỗ trống của câu: lấy từ câu hỏi của đề ('[1]', '（1）', '1' → '[1]')."""
    q = strip_marks((norm.get("de") or {}).get("cau_hoi") or "").strip()
    m = re.search(r"[0-9０-９]+(?:\s*[-－]\s*[abａｂ])?", q)   # nhiều chữ số: '21' → [21] (sửa lô 49–60)
    return f"[{norm_ja(m.group(0)).replace(' ', '')}]" if m else (f"[{norm.get('cau_con')}]" if norm.get("cau_con") else None)


def bo_sung_passage(doc, norm):
    """Hook cho claude_tao.gd1_nhan: Python điền passage (x-python-dien)."""
    out = {}
    for k, v in doc.items():
        out[k] = v
        if k == "cau_con":
            out["passage"] = {"blank_label": nhan_cho_trong(norm), "lines": []}
    if "passage" not in out:
        out["passage"] = {"blank_label": nhan_cho_trong(norm), "lines": []}
    return out


# ---------------- dạng 09: điền / so câu áp dụng theo ĐÚNG chỗ trống của câu con ----------------
SO_O_RE = re.compile(r"(?:[\[［（(「【]\s*([1-9１-９][0-9０-９]?)\s*(?:[-－−]\s*([abａｂ]))?\s*[\]］）)」】]|([⑴-⑷]))(?:\s*[-－−]\s*([abａｂ]))?")
# một ô = nhãn số ([1] （1） 【42】 ⑴ [2]−a …) hoặc gạch dưới, kể cả '[1]＿＿＿' / '[1] ____' (nhãn + gạch dưới = một ô)
O_RE = re.compile(r"(?:" + SO_O_RE.pattern + r"|_{2,}|＿{2,}|[（(][\s　]*[)）])(?:[\s　]*(?:_{2,}|＿{2,}|＿+))?")
_CAU_CON = {"so": None}


def _so(m):
    """Số của ô (nhóm 1: chữ số; nhóm 3: ⑴–⑷)."""
    if m.group(1):
        return int(norm_ja(m.group(1)))
    if m.group(3):
        return ord(m.group(3)) - 0x2473
    return None


def dien(cau, lua_chon):
    """Điền lựa chọn vào ĐÚNG chỗ trống của câu con (số = cau_con hoặc số cuối của nhãn 41–44); 2 chỗ a/b với 'aX／bY'.
    Chỗ trống của câu con khác giữ nguyên (khi so sẽ bị bỏ qua)."""
    cau, lc = cau or "", strip_marks(lua_chon or "").strip()
    toks = list(O_RE.finditer(cau))
    if not toks:
        return cau
    so = _CAU_CON.get("so")
    def la_cua_minh(m):
        n = _so(m)
        return n is None or so is None or n == so or (n > 9 and n % 10 == so)
    mine = [m for m in toks if la_cua_minh(m)] or toks[:1]
    parts = [p.strip() for p in re.split(r"[/／]", lc)] if len(mine) >= 2 and re.search(r"[/／]", lc) else [lc]
    parts = [re.sub(r"^[abａｂ]\s*[.．]?\s*(?=[^\sA-Za-z])", "", p) for p in parts]   # 'a.市民／ｂ.お年寄り'
    out, last = [], 0
    for i, m in enumerate(mine[:len(parts)] if len(parts) > 1 else mine[:1]):
        out.append(cau[last:m.start()])
        out.append(parts[i] if i < len(parts) else parts[-1])
        last = m.end()
    out.append(cau[last:])
    return "".join(out)


def cau_ap_dung_mong_doi(cau, lua_chon):
    """Câu áp dụng chấp nhận được: cả đoạn trích đã điền + riêng câu (。！？/xuống dòng) chứa chỗ trống đã điền + ghép liên tiếp."""
    full = dien(cau, lua_chon)
    out = [full]
    sents = [x for x in re.split(r"(?<=[。！？!?])|\n", cau or "") if x and x.strip()]
    if len(sents) > 1:
        idx = [i for i, x in enumerate(sents) if O_RE.search(x)]
        for i in idx:
            out.append(dien(sents[i], lua_chon))
            for j in range(i + 1, len(sents) + 1):
                for k in range(0, i + 1):
                    out.append(dien("".join(sents[k:j]), lua_chon))
    return out


def _eq(a, b):
    """So câu / lựa chọn: bỏ furigana, { }, cách đọc trong ngoặc, các chỗ trống còn lại, dấu, khoảng trắng."""
    def f(s):
        s = strip_marks(s or "").replace("{", "").replace("}", "")
        s = O_RE.sub("", s)
        s = re.sub(r"[(（][぀-ゟ゠-ヿー]+[)）]", "", s)
        s = re.sub(CHU_THICH_RE, "", s)                     # ký hiệu chú thích (注2) – không tính
        s = norm_ja(s)
        return re.sub(r"[。\.．、,，\s　!！?？「」『』｢｣｡・’'\"…:：①-⑳]", "", s).replace("ー", "一")
    return bool(f(a)) and f(a) == f(b)


_parse_and_flag_09 = parse_and_flag


def parse_and_flag(text, raw_html, lua_chon, dap_an_so, de_html, doan_van=None, cau_con=None):
    _CAU_CON["so"] = int(cau_con) if cau_con else None
    try:
        phan, co, gc = _parse_and_flag_09(text, raw_html, lua_chon, dap_an_so, de_html, doan_van=doan_van)
        if "hai_cho_trong" in co and not any(re.search(r"[/／]", x or "") for x in lua_chon) \
                and not re.search(r"[-－]\s*[abａｂ]\s*[\]］）)]", (phan.get("dau") or {}).get("cau") or ""):
            co = [c for c in co if c != "hai_cho_trong"]   # dạng 09: đoạn trích có chỗ trống của câu khác – không phải 2 chỗ trống
        return phan, co, gc
    finally:
        _CAU_CON["so"] = None


# nhãn thêm của dạng 09 (bỏ khi đo độ phủ chữ tiếng Việt): 'Đề bài:' / 'ĐỀ BÀI:', tiền tố a / b của lựa chọn 2 chỗ trống, nhãn chỗ trống [1-a]
LABELS += [r"(?im)^\s*\{?\s*đề\s+bài\s*\}?\s*[:：]",
           r"(?m)(?<![A-Za-zÀ-ỹ])[abａｂ]\s*[.．]?(?=\s*[぀-ヿ㐀-鿿])",
           r"[\[［（(]\s*[1-9１-９][0-9０-９]?\s*[-－−]\s*[abａｂ]\s*[\]］）)]|[-－−]\s*[abａｂ](?=＿)"]
