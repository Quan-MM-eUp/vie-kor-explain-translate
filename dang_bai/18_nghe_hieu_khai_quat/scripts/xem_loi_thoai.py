"""Dạng 18 – xem gọn phần LỜI THOẠI của một mẫu cho tác tử KIỂM TRA: bản dịch Việt trong lời giải (V1…Vm) và cách JSON ghép
từng dòng lời thoại Nhật L1…Ln với câu dịch (Lk [người nói] Nhật ‖ Việt). Dùng kèm ../../pipeline_chung/cong_cu/xem_gd1.py.

  python3 scripts/xem_loi_thoai.py 12136_1 17747_1          # bản checked (output/json_vi/checked)
  python3 scripts/xem_loi_thoai.py --tao 12136_1            # bản tác tử TẠO (output/json_vi/claude_tao)
  python3 scripts/xem_loi_thoai.py --lo 1 10                # mọi mẫu stt 1–10 đã có bản checked
"""
import os
import sys

import _dang as D
from pipeline_chung.common import load_json

args = sys.argv[1:]
lop = "claude_tao" if "--tao" in args else "checked"
args = [a for a in args if a != "--tao"]
if args[:1] == ["--lo"]:
    order = D.thu_tu()
    ids = [s for s in order[int(args[1]) - 1:int(args[2])] if os.path.exists(D.OUT("json_vi", lop, s + ".json"))]
else:
    ids = args
for sid in ids:
    n = D.load_norm(sid)
    p = D.OUT("json_vi", lop, sid + ".json")
    print("#" * 20, sid, n["cap_do"], "| khuôn", n["khuon_goc"], "| đáp án", n["de"]["dap_an_so"], "|", " ".join(n["co"]))
    print("--- BẢN DỊCH TRONG LỜI GIẢI (V1…Vm, nguyên văn) ---")
    for i, x in enumerate((n.get("phan") or {}).get("dich") or [], 1):
        print(f"V{i}: {x}")
    print("câu hỏi VI:", (n.get("phan") or {}).get("cau_hoi_vi"))
    if not os.path.exists(p):
        print(f"(chưa có {os.path.relpath(p, D.DANG)})")
        continue
    d = load_json(p)
    print(f"--- JSON ({lop}): Lk [người nói] Nhật ‖ Việt ---")
    dong = n["loi_thoai"]["dong"]
    lines = ((d.get("full_translation") or [{}])[0] or {}).get("lines") or []
    for k in range(max(len(lines), len(dong))):
        a = lines[k] if k < len(lines) else {}
        b = dong[k] if k < len(dong) else {}
        m = (a.get("meaning") or {}).get("vi") if a.get("meaning") else "∅ (null)"
        lech = "" if (b and a and D.LT._k(a.get("ja")) == D.LT._k(b.get("ja")) and (a.get("speaker") or None) == (b.get("speaker") or None)) else "   ⚠ KHÁC lời thoại Python tách"
        print(f"L{k + 1} [{a.get('speaker') or '-'}] {a.get('ja')} ‖ {m}{lech}")
    q = d.get("question") or {}
    print("câu hỏi JSON:", q.get("ja"), "‖", (q.get("meaning") or {}).get("vi") if q.get("meaning") else None)
