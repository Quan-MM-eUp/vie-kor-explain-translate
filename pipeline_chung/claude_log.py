"""Nhật ký "Claude đã sửa" – mục 2b workflow tổng quát.

Python tự so bản GPT với bản Claude đã sửa để lấy đường dẫn / trước / sau.
Claude chỉ ghi lý do vào file ly_do (cùng thư mục với bản đã sửa, tên <id>.ly_do.json):
  {"sua": [{"duong_dan": "$.options[3].analysis.vi", "loai": "sai_so_ban_goc", "muc_do": "nang", "ly_do": "…"},
           {"duong_dan": "$.options[0].analysis.vi", "loai": "sua_ban_goc", "nhom": "cach_doc", "muc_do": "nang", "ly_do": "…"}],
   "ghi_chu_ban_goc": ["[Bản gốc VI] …", "[Đã sửa bản gốc] … '<cũ>' → '<mới>' – …"], "ghi_chu_khi_dich": ["[Khi dịch] …"], "loi_json_vi": ["[Lỗi JSON VI] …"]}
"""
import copy
import re

from .common import iter_strings, parse_path, path_str

LOAI = {"sai_so_ban_goc", "chinh_ta", "khach_quan", "chu_quan", "sua_ban_goc", "sua_dinh_dang", "sua_theo_ctv"}
# sua_theo_ctv (v2): sửa NỘI DUNG sau khi CTV tiếng Nhật xác nhận câu bị cờ nghi_noi_dung là sai thật –
#   bắt buộc nhom (NHOM_NOI_DUNG) + ghi chú "[Đã sửa theo CTV] <chỗ>: 'cũ' → 'mới' – <CTV nói gì>"; không tính vào Dạng 2.
# sua_dinh_dang (cách chia v2, dạng 01 – output_v2): Claude CHỈ được sửa lỗi ĐỊNH DẠNG có sẵn trong bản gốc;
#   lỗi NỘI DUNG không sửa mà gắn cờ "nghi_noi_dung" (câu bị chặn, không dịch). sua_ban_goc = cách cũ (giữ để đọc dữ liệu cũ).
NHOM_DINH_DANG = {"dinh_chu", "xuong_dong", "lap_tu", "chinh_ta", "dau_cau", "khoang_trang", "gach_chan", "ky_tu",
                  "cach_doc_lan_so", "khac"}
NOTE_DD = "[Đã sửa định dạng]"
NHOM_NOI_DUNG = {"nghia_cau", "thi_the", "tu_tha_dong_tu", "nghia_tu", "khong_ton_tai", "dong_am", "chu_han",
                 "cach_doc", "dap_an", "thieu_noi_dung", "khac"}
NOTE_ND = "[Nghi sai nội dung]"
SRC_FIX_LOAI = ("sua_ban_goc", "sua_dinh_dang", "sua_theo_ctv")
NOTE_CTV = "[Đã sửa theo CTV]"
# sua_ban_goc = Claude sửa lỗi CÓ SẴN trong lời giải gốc (workflow tổng quát mục 2a-1) → câu thuộc Dạng 2
NHOM = {"chinh_ta", "cach_doc", "kien_thuc", "khac"}
NOTE_FIX = "[Đã sửa bản gốc]"
FIX_MAX_RATIO = 0.5      # một chỗ sửa bản gốc đổi quá 50% trường → cảnh báo
FIX_MAX_WORDS = 30       # hoặc đổi quá 30 từ → cảnh báo
MUC_DO = {"nghiem_trong", "nang", "nhe"}


def _flat(doc):
    """Mọi giá trị lá (chuỗi, số, null) theo đường dẫn."""
    out = {}

    def walk(o, p):
        if isinstance(o, dict):
            if not o:
                out[path_str(p)] = {}
            for k, v in o.items():
                walk(v, p + (k,))
        elif isinstance(o, list):
            if not o:
                out[path_str(p)] = []
            for i, v in enumerate(o):
                walk(v, p + (i,))
        else:
            out[path_str(p)] = o
    walk(doc, ())
    return out


def diff(before, after):
    a, b = _flat(before), _flat(after)
    changes = []
    for k in sorted(set(a) | set(b)):
        if a.get(k, "∅") != b.get(k, "∅"):
            changes.append({"duong_dan": k, "truoc": a.get(k), "sau": b.get(k)})
    return changes


def build_log(sid, giai_doan, before, after, reasons):
    """Ghép thay đổi thật (Python) với lý do (Claude). Trả về (nhật ký, cảnh báo)."""
    reasons = reasons or {}
    changes = diff(before, after)
    by_path = {}
    for x in reasons.get("sua", []):
        by_path.setdefault(x.get("duong_dan", ""), x)
    warn = []
    log = []
    for i, c in enumerate(changes, 1):
        # lý do có thể ghi ở đường dẫn cha (vd $.options[3].analysis thay vì …analysis.vi)
        rs = by_path.get(c["duong_dan"]) or next((v for k, v in by_path.items() if k and c["duong_dan"].startswith(k)), None)
        item = dict(stt=i, **c, loai=(rs or {}).get("loai"), muc_do=(rs or {}).get("muc_do"), ly_do=(rs or {}).get("ly_do"))
        if item["loai"] in SRC_FIX_LOAI:
            item["nhom"] = (rs or {}).get("nhom")
        if not rs:
            warn.append(f"Claude sửa nhưng không ghi lý do: {c['duong_dan']}")
        else:
            if item["loai"] not in LOAI:
                warn.append(f"{c['duong_dan']}: loại sửa không hợp lệ ({item['loai']})")
            if item["muc_do"] not in MUC_DO:
                warn.append(f"{c['duong_dan']}: mức độ không hợp lệ ({item['muc_do']})")
            if item["loai"] == "sua_ban_goc" and item.get("nhom") not in NHOM:
                warn.append(f"{c['duong_dan']}: sửa bản gốc nhưng thiếu/sai nhom ({item.get('nhom')}); cần một trong {sorted(NHOM)}")
            if item["loai"] == "sua_dinh_dang" and item.get("nhom") not in NHOM_DINH_DANG:
                warn.append(f"{c['duong_dan']}: sửa định dạng nhưng thiếu/sai nhom ({item.get('nhom')}); cần một trong {sorted(NHOM_DINH_DANG)}")
        log.append(item)
    changed = {c["duong_dan"] for c in changes}
    for k in by_path:
        if k and not any(p == k or p.startswith(k) for p in changed):
            warn.append(f"Claude ghi lý do cho chỗ không thay đổi: {k}")
    return {"sample_id": sid, "giai_doan": giai_doan, "so_cho_sua": len(log), "sua": log,
            "ghi_chu_ban_goc": reasons.get("ghi_chu_ban_goc", []),
            "ghi_chu_khi_dich": reasons.get("ghi_chu_khi_dich", []),
            "loi_json_vi": reasons.get("loi_json_vi", [])}, warn


def summary_lines(log):
    return [f"{x['duong_dan']} ({x.get('loai') or '?'}): {str(x['truoc'])[:60]!r} → {str(x['sau'])[:60]!r}" for x in log["sua"]]


# ---------- Sửa lỗi bản gốc (mục 2a-1) ----------

def src_fixes(log):
    return [x for x in log["sua"] if x.get("loai") in SRC_FIX_LOAI]


def gpt_fixes(log):
    return [x for x in log["sua"] if x.get("loai") not in SRC_FIX_LOAI]


def _set(doc, path, val):
    parts = parse_path(path)
    o = doc
    for k in parts[:-1]:
        o = o[k]
    o[parts[-1]] = val


def _get(doc, path):
    o = doc
    for k in parse_path(path):
        o = o[k]
    return o


def revert_src_fixes(before, after, log, reasons=None):
    """Bản 'after' nhưng các chỗ sua_ban_goc trả về giá trị GPT (để kiểm tra trung thành với bản gốc).
    Trả về theo đường dẫn Claude ghi trong lý do (vd $.options[3].analysis) để xử lý cả khi đổi kiểu
    (chuỗi → null), rồi theo từng đường dẫn lá trong nhật ký."""
    out = copy.deepcopy(after)
    for x in src_fixes(log):
        try:
            _set(out, x["duong_dan"], copy.deepcopy(x["truoc"]))
        except (KeyError, IndexError, TypeError):
            pass     # đường dẫn không có ở bản GPT (thêm/bớt phần tử) – cảnh báo ở src_fix_warnings
    for x in (reasons or {}).get("sua", []):      # sau cùng: theo đường dẫn trong lý do (đè lên các lá ở trên)
        if x.get("loai") in SRC_FIX_LOAI and x.get("duong_dan"):
            try:
                _set(out, x["duong_dan"], copy.deepcopy(_get(before, x["duong_dan"])))
            except (KeyError, IndexError, TypeError):
                pass
    return out


def _words(s):
    """Từ tiếng Việt theo khoảng trắng; tiếng Nhật (kana/kanji) tính mỗi chữ là một đơn vị (không có khoảng trắng)."""
    return re.findall(r"[\u3040-\u30ff\u3400-\u9fff]|[^\W\u3040-\u30ff\u3400-\u9fff]+", str(s or ""))


def src_fix_warnings(log, notes):
    """Cảnh báo kiểm soát cho các chỗ Claude sửa lỗi bản gốc."""
    import difflib
    warn = []
    fixes = src_fixes(log)
    for x in fixes:
        a, b = _words(x["truoc"]), _words(x["sau"])
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        changed = sum(max(i2 - i1, j2 - j1) for t, i1, i2, j1, j2 in sm.get_opcodes() if t != "equal")
        base = max(len(a), 1)
        if x["truoc"] is None and x["sau"] is None:
            continue          # thay đổi cấu trúc (vd analysis → null) – đã tính ở đường dẫn lá
        if not isinstance(x["truoc"], str) and isinstance(x["sau"], str):
            warn.append(f"{x['duong_dan']}: sửa bản gốc ở chỗ bản GPT không có chuỗi (có thể là thêm nội dung mới)")
        elif changed > FIX_MAX_WORDS or changed / base > FIX_MAX_RATIO:
            warn.append(f"{x['duong_dan']}: sửa bản gốc quá nhiều ({changed} từ / {len(a)} từ) – kiểm tra có viết lại nội dung không")
    if fixes and not any(str(n).startswith(NOTE_FIX) for n in notes or []):
        warn.append(f"Có {len(fixes)} chỗ sửa bản gốc nhưng thiếu ghi chú '{NOTE_FIX} …' trong ghi_chu_ban_goc")
    if not fixes and any(str(n).startswith(NOTE_FIX) for n in notes or []):
        warn.append(f"Có ghi chú '{NOTE_FIX}' nhưng không có chỗ sửa nào loai=sua_ban_goc")
    return warn


# Lỗi/cảnh báo "trung thành với bản gốc" – khi có sua_ban_goc thì lấy từ bản đã hoàn tác chỗ sửa bản gốc
FIDELITY_PREFIX = ("Mất ", "Độ phủ", "Từ thừa", "Furigana bị", "Furigana thừa", "Đánh dấu {", "K8:", "K9:")


def _is_fid(msg):
    return str(msg).startswith(FIDELITY_PREFIX)


def merge_checks(r_final, r_rev):
    """Cấu trúc/schema/K… lấy từ bản cuối; trung thành (độ phủ, tiếng Nhật, furigana, { }) lấy từ bản hoàn tác."""
    return {"loi": [e for e in r_final["loi"] if not _is_fid(e)] + [e for e in r_rev["loi"] if _is_fid(e)],
            "canh_bao": [e for e in r_final["canh_bao"] if not _is_fid(e)] + [e for e in r_rev["canh_bao"] if _is_fid(e)],
            "so_lieu": r_rev["so_lieu"]}



# ---------- Cách chia v2 (dạng 01): sửa định dạng + cờ nghi sai nội dung ----------

def format_fix_warnings(log, notes):
    """Mỗi chỗ sua_dinh_dang phải có dòng ghi chú '[Đã sửa định dạng] <chỗ>: '<cũ>' → '<mới>' – <lý do>'."""
    warn = []
    dd = [x for x in log["sua"] if x.get("loai") == "sua_dinh_dang"]
    n_note = sum(1 for n in notes or [] if str(n).startswith(NOTE_DD))
    if dd and not n_note:
        warn.append(f"Có {len(dd)} chỗ sửa định dạng nhưng thiếu ghi chú '{NOTE_DD} <chỗ>: …' trong ghi_chu_ban_goc")
    if n_note and not dd:
        warn.append(f"Có ghi chú '{NOTE_DD}' nhưng không có chỗ sửa nào loai=sua_dinh_dang")
    ctv = [x for x in log["sua"] if x.get("loai") == "sua_theo_ctv"]
    n_ctv = sum(1 for n in notes or [] if str(n).startswith(NOTE_CTV))
    if ctv and not n_ctv:
        warn.append(f"Có {len(ctv)} chỗ sửa theo CTV nhưng thiếu ghi chú '{NOTE_CTV} <chỗ>: …' trong ghi_chu_ban_goc")
    for x in ctv:
        if x.get("nhom") not in NHOM_NOI_DUNG:
            warn.append(f"{x['duong_dan']}: sua_theo_ctv thiếu/sai nhom (dùng nhóm của nghi_noi_dung: {sorted(NHOM_NOI_DUNG)})")
    for x in log["sua"]:
        if x.get("loai") == "sua_ban_goc":
            warn.append(f"{x['duong_dan']}: dùng loai cũ 'sua_ban_goc' – cách chia v2 chỉ cho 'sua_dinh_dang'; "
                        f"lỗi nội dung phải ghi vào 'nghi_noi_dung' (chưa CTV duyệt) hoặc 'sua_theo_ctv' (CTV đã xác nhận)")
    return warn


def content_flags(why):
    """Đọc cờ nghi sai nội dung trong file lý do. Trả về (danh sách dòng hiển thị, lỗi định dạng của cờ)."""
    lines, bad = [], []
    for i, f in enumerate((why or {}).get("nghi_noi_dung") or [], 1):
        if not isinstance(f, dict):
            bad.append(f"nghi_noi_dung[{i}] phải là object {{vi_tri, nhom, mo_ta, de_xuat}}")
            continue
        vt, nh, mt = (f.get("vi_tri") or "").strip(), f.get("nhom"), (f.get("mo_ta") or "").strip()
        if not vt:
            bad.append(f"nghi_noi_dung[{i}]: thiếu 'vi_tri' (nghi sai ở phần nào, vd 'Nghĩa câu', 'Phân tích lựa chọn 2', 'Tham khảo')")
        if nh not in NHOM_NOI_DUNG:
            bad.append(f"nghi_noi_dung[{i}]: nhom '{nh}' không hợp lệ; cần một trong {sorted(NHOM_NOI_DUNG)}")
        if not mt:
            bad.append(f"nghi_noi_dung[{i}]: thiếu 'mo_ta'")
        de = (f.get("de_xuat") or "").strip()
        lines.append(f"{NOTE_ND} {vt} ({nh}): {mt}" + (f" – đề xuất: {de}" if de else ""))
    return lines, bad


def chuan_hoa_duong_dan(why):
    """Chấp nhận duong_dan viết thiếu '$.' (vd 'reference.vi' → '$.reference.vi')."""
    for x in (why or {}).get("sua") or []:
        d = x.get("duong_dan")
        if isinstance(d, str) and d and not d.startswith("$"):
            x["duong_dan"] = "$." + d.lstrip(".")
    return why
