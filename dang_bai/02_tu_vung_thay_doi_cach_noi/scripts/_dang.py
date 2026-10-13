"""Phần riêng của dạng 02 – Thay đổi cách nói: cấu hình, đường dẫn, tách phần lời giải, gắn cờ, kiểm tra K1–K10 / D1–D2, hiển thị Excel.
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
    os.environ["PIPELINE_DATA"] = _c.get("du_lieu_test", "data/test_02_tu_vung_thay_doi_cach_noi.csv")


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
    """Các mẫu bị loại theo config.loc_nguon_de (quyết định 2026-10-11): từ mẫu tu_mau, bỏ mẫu mà cột `cot`
    (thi_thu_thuoc_de) chứa một trong `bo_neu_chua` (mặc định 'Nat Test'). Trả về {sample_id: giá trị cột}."""
    lc = cfg().get("loc_nguon_de") or {}
    if CA_NAT or not lc.get("bat"):
        return {}
    from pipeline_chung.common import read_csv
    cot, tu, kw = lc.get("cot", "thi_thu_thuoc_de"), int(lc.get("tu_mau", 1)), lc.get("bo_neu_chua") or ["Nat Test"]
    return {sid_of(r): r.get(cot, "") for i, r in enumerate(read_csv(data_path()), 1)
            if i >= tu and any(k.lower() in (r.get(cot) or "").lower() for k in kw)}


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
LABELS = [r"(?im)^\s*(câu hỏi|cách đọc|nghĩa)\s*:", r"(?m)PHÂN TÍCH\s*[:：]?", r"(?m)LỰA CHỌN ĐÚNG\s*[:：]?",
          r"(?m)THÔNG TIN THAM KHẢO\s*[:：]?", r"#{3,}",
          r"(?m)^\s*[AB]\s*[:：]"]   # 2026-10-12: nhãn người nói hội thoại A:/B: lặp ở câu hỏi / cách đọc / nghĩa (19375, 22017) – không tính độ phủ


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
    f = lambda s: re.sub(r"[。\.．、,，\s　]", "", norm_ja(re.sub(r"<([^<>:]+):[^<>]+>", r"\1", s or "")))  # noqa: E731 – 2026-10-12: đề có furigana dạng <漢字:かな> (54756–54760)
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
            res["cau_hoi"] = re.sub(r"(?i)^\s*câu hỏi\s*[:：]\s*", "", line); last = "cau_hoi"
        elif last == "cach_doc" and res["nghia"] is None and not re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", line):
            res["nghia"] = line; last = "nghia"     # 2026-10-12: dòng nghĩa tiếng Việt không nhãn 'Nghĩa:' ngay sau 'Cách đọc:' (21986)
        elif last:
            res[last] += "\n" + line
    return res


def analysis_lines(pt, lua_chon):
    """Phần PHÂN TÍCH → (mo_dau, [ {so, nhan, doc, noi_dung, lua_chon_khop} ], ket_luan, co_dinh_lien).
    Dòng dính liền ('…".3. 新しい (…): …') được tách theo nhãn khớp lựa chọn của đề."""
    lines = [x for x in (pt or "").split("\n") if x.strip()]
    glued = False
    split = []
    for line in lines:
        cut = [0]
        for k in range(1, 5):
            for m in re.finditer(rf"(?<=[^\d\s])\s*({k})\s*[\.．]\s*", line):
                lab = LABEL_RE.match(line[m.end():])
                if m.start() > 0 and lab and _eq(lab.group(1), lua_chon[k - 1]):
                    cut.append(m.start() + (len(m.group(0)) - len(m.group(0).lstrip())))
        cut = sorted(set(cut))
        glued |= len(cut) > 1
        split += [line[a:b].strip() for a, b in zip(cut, cut[1:] + [len(line)])]
    items, mo_dau, tail = [], [], []
    for line in split:
        m = NUM_LINE_RE.match(line)
        if m:
            if tail and items:                     # dòng không đánh số nằm giữa hai dòng phân tích → thuộc dòng trước
                items[-1]["noi_dung"] = (items[-1]["noi_dung"] + "\n" + "\n".join(tail)).strip()
            tail = []
            lab = LABEL_RE.match(m.group(2))
            nhan, doc, nd = (lab.group(1), lab.group(2), lab.group(3)) if lab else (m.group(2), None, "")
            khop = next((j + 1 for j, o in enumerate(lua_chon) if _eq(nhan, o)), None)
            items.append({"so": int(m.group(1)), "nhan": nhan.strip(), "doc": doc, "noi_dung": nd.strip(), "lua_chon_khop": khop})
        elif not items:
            mo_dau.append(line)
        else:
            tail.append(line)
    ket_luan = tail
    return "\n".join(mo_dau), items, "\n".join(ket_luan), glued


# ---------------- gắn cờ (giai đoạn 0) ----------------
KHONG_TON_TAI_RE = re.compile(r"không (tồn tại|có nghĩa)", re.I)
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
    "co_ket_luan": "PHÂN TÍCH có đoạn sau dòng cuối (→ analysis.conclusion)",
    "lua_chon_cach_chu": "Lựa chọn của đề viết cách chữ / có khoảng trắng",
    "de_co_gach_chan_loi_giai_khong": "Đề có gạch chân nhưng phần đầu lời giải không in đậm / gạch chân (JSON không có { })",
    "nhieu_doan_danh_dau": "Một dòng có từ 2 đoạn in đậm / gạch chân",
    "danh_dau_rac": "Bản gốc có đoạn in đậm / gạch chân rỗng hoặc chỉ là dấu câu (đã bỏ thẻ)",
    "co_furigana": "Có furigana",
    "ruby_hong": "Có ruby hỏng trong bản gốc",
    "khong_ton_tai": "Có câu 'không tồn tại / không có nghĩa'",
    "ky_hieu_trung": "Bản gốc có sẵn ký hiệu ｜《》 (trùng ký hiệu furigana)",
}
CTV_FLAGS = ("dong_pt_dinh_lien", "thu_tu_pt_lech", "lech_dap_an", "de_co_gach_chan_loi_giai_khong", "danh_dau_rac")
FURI_SKIP = [("correct", "option_ja")]      # bản sao của options[i].option_ja – WF dạng 02 mục 3a quy tắc 5


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
    if len([it for it in items if KHONG_TON_TAI_RE.search(it["noi_dung"])]) >= 1:
        co.append("khong_ton_tai")
    phan = {"dau": hl, "phan_tich": {"mo_dau": mo, "dong": items, "ket_luan": kl}, "lua_chon_dung": sec["lua_chon_dung"],
            "tham_khao": sec["tham_khao"]}
    return phan, co, gc


def text_without_lcd(text):
    """Văn bản lời giải bỏ phần LỰA CHỌN ĐÚNG (bản lặp của nhãn lựa chọn – không tính khi so furigana / { })."""
    sec = split_sections(text)
    return "\n".join(x for x in (sec["dau"], sec["phan_tich"]) if x)


def text_without_ref(text):
    """Quy tắc THAM KHẢO (2026-10-07): lời giải bỏ phần THÔNG TIN THAM KHẢO (cả đoạn không tiêu đề sau LỰA CHỌN ĐÚNG)
    – dùng làm đầu vào GPT và làm chuẩn kiểm tra (độ phủ, tiếng Nhật, furigana, { }, âm Hán Việt, gợi ý)."""
    sec = split_sections(text)
    parts = [sec["dau"]] if sec["dau"] else []
    if sec["phan_tich"] is not None:
        parts.append("###\nPHÂN TÍCH\n" + sec["phan_tich"])
    if sec["lua_chon_dung"] is not None:
        parts.append("###\nLỰA CHỌN ĐÚNG\n" + sec["lua_chon_dung"])
    return "\n".join(parts)


# ---------------- kiểm tra riêng giai đoạn 1: K1–K10 ----------------
READING_OK = re.compile(r"^[぀-ゟ゠-ヿー・\s/、,，。]+$")


def _segs(s):
    from pipeline_chung.normalize import mark_segments
    return mark_segments(s)


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
        a = strip_marks((o.get("analysis") or {}).get("vi", ""))
        for other in opts:
            if other is o:
                continue
            for m in re.finditer(rf"(?<=[^\d])\s*{other.get('index')}\s*[\.．]\s*", a):
                lab = LABEL_RE.match(a[m.end():])
                if lab and _eq(lab.group(1), other.get("option_ja")):
                    loi.append(f"K3: phân tích lựa chọn {o.get('index')} còn chứa phân tích của lựa chọn {other.get('index')} (chưa tách)")
    src_line = {}
    for it in (phan.get("phan_tich") or {}).get("dong", []):
        j = it["lua_chon_khop"] or it["so"]
        src_line.setdefault(j, it)
    for j, it in src_line.items():
        if 1 <= j <= len(opts) and it["noi_dung"] and opts[j - 1].get("analysis") is None:
            loi.append(f"K3: bản gốc có phân tích lựa chọn {j} nhưng JSON để null")
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
    # K7 – quy tắc THAM KHẢO 2026-10-07: reference_raw = nguyên văn (Python điền); không kiểm tra nội dung tham khảo
    loi += TK.kiem_tra(doc, phan.get("tham_khao"))
    # K8
    for o in opts:
        r_ = o.get("reading")
        if r_ is not None and not READING_OK.match(strip_marks(r_)):
            canh_bao.append(f"K8: lựa chọn {o.get('index')}: reading '{r_}' không chỉ gồm kana")
        it = src_line.get(o.get("index"))
        if it is not None and (it["doc"] or None) != (r_ or None) and not (it["doc"] and r_ and norm_ja(it["doc"]) == norm_ja(r_)):
            canh_bao.append(f"K8: lựa chọn {o.get('index')}: reading '{r_}' khác ngoặc cách đọc ở nhãn '{it['doc']}'")
    # K9 – độ phủ chữ Việt theo từng lựa chọn
    import collections
    for j, it in src_line.items():
        if not (1 <= j <= len(opts)) or not it["noi_dung"]:
            continue
        src = collections.Counter(vi_words(it["noi_dung"]))
        out = collections.Counter(vi_words(((opts[j - 1].get("analysis") or {}).get("vi")) or ""))
        if src and sum((src & out).values()) / sum(src.values()) < 0.97 and "dong_pt_dinh_lien" not in norm["co"]:
            loi.append(f"K9: phân tích lựa chọn {j} thiếu chữ so với dòng gốc: {[w for w, _ in (src - out).most_common(8)]}")
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
        lab = show(o.get("option_ja", "")) + (f" ({o['reading']})" if o.get("reading") else "")
        out.append(f"{bold(str(o['index']) + '. ' + lab + ':')} {_t(o.get('analysis'), lang)}")
    if an.get("conclusion"):
        out.append(_t(an["conclusion"], lang))
    out.append(f"{bold('【LỰA CHỌN ĐÚNG】')} {c.get('index')}. {show(c.get('option_ja', ''))}")
    if isinstance(d.get("reference"), dict):            # dữ liệu cũ (trước quy tắc THAM KHẢO 2026-10-07): tham khảo đã tách / dịch
        out.append(bold("【THÔNG TIN THAM KHẢO】"))
        out.append(_t(d["reference"], lang))
    out += TK.render(d, lang, show, bold)               # quy tắc mới: nguyên văn, chỉ hiện ở bản Việt, không dịch
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
