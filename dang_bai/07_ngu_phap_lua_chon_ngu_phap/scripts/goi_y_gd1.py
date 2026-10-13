"""[Dạng 07 – chạy song song] In phần GỢI Ý của Python cho các mẫu GĐ1 của lô (từ output/claude/gd1_danh_sach_<tu>_<den>.json).
CC/xem_gd1.py chỉ đọc file tên cũ gd1_danh_sach.json nên từ 2026-10-12 không còn in khối GỢI Ý – chạy thêm lệnh này:
  cd scripts && python3 goi_y_gd1.py --tu X --den Y
"""
import json
import os

import _dang as D

p = D.OUT("claude", "gd1_danh_sach.json")          # tự đổi thành gd1_danh_sach_<tu>_<den>.json
if not os.path.exists(p):
    raise SystemExit(f"Chưa có {os.path.relpath(p, D.DANG)} – chạy s1_claude_goi.py với cùng --tu/--den trước.")
ds = json.load(open(p, encoding="utf-8"))
co = 0
for g in (ds.get("cau", []) if isinstance(ds, dict) else ds):
    py = g.get("python_tren_ban_gpt") or g.get("python_tren_ban_hien_tai") or {}
    muc = [(k, v) for k, v in (("Cờ", g.get("co")), ("Cần sửa lại", g.get("can_sua_lai")),
                               ("Ghi chú tự động", g.get("ghi_chu_ban_goc_tu_dong")),
                               ("Python LỖI", py.get("loi")), ("Python cảnh báo", py.get("canh_bao"))) if v]
    if muc:
        co += 1
        print("#" * 10, g.get("sample_id"))
        for k, v in muc:
            print(f"  {k}: {v}")
print(f"({co} mẫu có gợi ý)")
