"""Xem gọn một mẫu ở GĐ1 cho tác tử KIỂM TRA: đề + lời giải gốc (dau_vao) + JSON checked dạng phẳng.

  python ../../pipeline_chung/cong_cu/xem_gd1.py 4812_1 5450_1
  python ../../pipeline_chung/cong_cu/xem_gd1.py --lo 91 100      # mọi mẫu của lô đang có bản checked
Thêm --gon để bỏ phần dau_vao (chỉ xem JSON).
"""
import os
import sys

import _chung as C

C.kiem_dang()


def flat(o, p="$"):
    if isinstance(o, dict):
        if "vi" in o and set(o) <= {"vi", "ko"}:
            yield p, o["vi"]
            return
        for k, v in o.items():
            yield from flat(v, f"{p}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from flat(v, f"{p}[{i}]")
    elif o is not None:
        yield p, o


args = sys.argv[1:]
gon = "--gon" in args
args = [a for a in args if a != "--gon"]
if args[:1] == ["--lo"]:
    ids = [s for s in C.ids_tu_den(int(args[1]), int(args[2])) if os.path.exists(C.out("json_vi", "checked", s + ".json"))]
else:
    ids = args
goi_y = {}
if os.path.exists(C.out("claude", "gd1_danh_sach.json")):
    _ds = C.lj(C.out("claude", "gd1_danh_sach.json"))
    for t in (_ds.get("cau", []) if isinstance(_ds, dict) else _ds):
        goi_y[t.get("sample_id")] = t
da_in_dv = set()
for sid in ids:
    n = C.lj(C.out("samples", "norm", sid + ".json"))
    c = C.lj(C.out("json_vi", "checked", sid + ".json"))
    for k in ("reference_raw", "schema", "question_id", "cau_con"):
        c.pop(k, None)
    de = n.get("de") or {}
    print("#" * 20, sid, n.get("co"), "| ĐỀ:", de.get("cau_hoi"), de.get("lua_chon"), "| đáp án", de.get("dap_an_so"))
    if n.get("doan_van") and n.get("question_id") not in da_in_dv and not gon:   # dạng 09: in đoạn văn một lần cho mỗi nhóm
        da_in_dv.add(n.get("question_id"))
        print("--- ĐOẠN VĂN (chung cho các câu con) ---")
        print(n["doan_van"])
    if ((n.get("phan") or {}).get("script") or {}).get("hien_thi") and not gon:   # dạng 20: script nghe
        sc = n["phan"]["script"]
        print("--- SCRIPT NGHE (đã tách) ---" if sc.get("ok") else "--- SCRIPT NGHE (Python KHÔNG tách được – bản gốc) ---")
        print((f"{sc.get('nguoi_noi')}：" if sc.get("nguoi_noi") else "") + (sc.get("cau_noi") or "") + "".join(
            f"\n  {i + 1}. {x}" for i, x in enumerate(sc.get("lua_chon") or [])) if sc.get("ok") else sc.get("hien_thi"))
        if sc.get("ghi_chu"):
            print("  (ghi chú trong script:", sc["ghi_chu"], ")")
    if not gon:
        print("--- LỜI GIẢI GỐC ---")
        print(n.get("dau_vao"))
    g = goi_y.get(sid) or {}
    py = g.get("python_tren_ban_gpt") or g.get("python_tren_ban_hien_tai") or {}
    if g.get("ghi_chu_ban_goc_tu_dong") or py.get("loi") or py.get("canh_bao") or g.get("can_sua_lai"):
        print("--- GỢI Ý (gd1_danh_sach) ---")
        for k, v in (("Cần sửa lại", g.get("can_sua_lai")), ("Ghi chú tự động", g.get("ghi_chu_ban_goc_tu_dong")),
                     ("Python LỖI", py.get("loi")), ("Python cảnh báo", py.get("canh_bao"))):
            if v:
                print(f"{k}: {v}")
    print("--- JSON ---")
    for p, v in flat(c):
        if p.endswith(".index"):
            continue
        print(p.replace("$.analysis.options", "O").replace("$.", ""), "=", repr(v) if isinstance(v, str) and "\n" in v else v)
