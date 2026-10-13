"""Xem gọn một câu dạng 17 ở GĐ1 cho tác tử KIỂM TRA: đề + lời thoại SONG SONG (Nhật | Việt trong JSON) + dòng Việt gốc + phần sau ###
+ câu hỏi / lựa chọn / key_info trong JSON + gợi ý Python.

  python3 scripts/xem_17.py 13594_1 24736_1
  python3 scripts/xem_17.py --lo 1 10          # mọi câu của lô (theo thu_tu_chay) đã có bản checked
  thêm --tao để xem bản tác tử TẠO (output/json_vi/claude_tao) thay cho bản checked
Đường dẫn để ghi file lý do: dòng [k] = $.full_translation[0].lines[k] (…meaning.vi), O[i] = $.options[i], KI[k] = $.key_info[k].
"""
import os
import sys

import _dang as D
from pipeline_chung.common import load_json

args = sys.argv[1:]
tao = "--tao" in args
args = [a for a in args if a != "--tao"]
lop = ("json_vi", "claude_tao") if tao else ("json_vi", "checked")
if args[:1] == ["--lo"]:
    order = D.thu_tu()
    ids = [s for s in order[int(args[1]) - 1:int(args[2])] if os.path.exists(D.OUT(*lop, s + ".json"))]
else:
    ids = args
goi_y = {}
if os.path.exists(D.OUT("claude", "gd1_danh_sach.json")):
    for t in load_json(D.OUT("claude", "gd1_danh_sach.json")):
        goi_y[t.get("sample_id")] = t
v = lambda o: (o or {}).get("vi") if isinstance(o, dict) else None  # noqa: E731
for sid in ids:
    n = D.load_norm(sid)
    c = load_json(D.OUT(*lop, sid + ".json"))
    de = n["de"]
    print("#" * 24, sid, n["cap_do"], "khuôn", n["khuon_goc"], "| cờ:", " ".join(n["co"]))
    print("ĐỀ: cau_hoi =", de["cau_hoi"], "| lựa chọn:", " / ".join(f"{i + 1}. {x}" for i, x in enumerate(de["lua_chon"])), "| đáp án", de["dap_an_so"])
    print(f"--- LỜI THOẠI TRONG JSON (Python ghép gợi ý: {n['ghep']['cach'] or 'KHÔNG'}) ---")
    for bi, li, ln in D._lines(c):
        print(f"[{li}] {ln.get('speaker') or '-'} | {ln.get('ja')}\n      → {v(ln.get('meaning'))}")
    print("--- DÒNG VIỆT GỐC (trước 4 lựa chọn) ---")
    for i, x in enumerate(n["vi"]["dong_thoai"]):
        print(f"V{i} {x}")
    if n["vi"]["lua_chon"]:
        print("--- NGHĨA LỰA CHỌN GỐC ---", " | ".join(n["vi"]["lua_chon"]))
    if n["vi"]["sau_phan_cach"]:
        print("--- SAU ### ---")
        print("\n".join(n["vi"]["sau_phan_cach"]))
    q = c.get("question") or {}
    print("--- JSON: câu hỏi / lựa chọn / key_info ---")
    print("Q:", q.get("ja"), "→", v(q.get("meaning")))
    for i, o in enumerate(c.get("options") or []):
        print(f"O[{i}] {'✔' if o.get('is_match') else ' '} {o.get('option_ja')} → {v(o.get('meaning'))}"
              + (f"\n      analysis: {v(o.get('analysis'))}" if o.get("analysis") else ""))
    for k, x in enumerate(c.get("key_info") or []):
        print(f"KI[{k}] {x.get('speaker') or '-'} | {x.get('ja')} → {v(x.get('meaning'))}")
    print("correct:", c.get("correct"), "| summary:", c.get("summary"))
    g = goi_y.get(sid) or {}
    py = g.get("python_tren_ban_gpt") or g.get("python_tren_ban_hien_tai") or {}
    if g.get("ghi_chu_ban_goc_tu_dong") or py.get("loi") or py.get("canh_bao") or g.get("can_sua_lai"):
        print("--- GỢI Ý PYTHON (trên bản tác tử TẠO) ---")
        for k, val in (("Cần sửa lại", g.get("can_sua_lai")), ("Ghi chú tự động", g.get("ghi_chu_ban_goc_tu_dong")),
                       ("LỖI", py.get("loi")), ("Cảnh báo", py.get("canh_bao"))):
            if val:
                print(f"{k}: {val}")
    print()
