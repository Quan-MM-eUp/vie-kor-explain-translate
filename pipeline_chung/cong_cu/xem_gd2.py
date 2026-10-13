"""Xem gọn bảng dịch GĐ2 (output/claude/gd2/<id>.md): chỉ cột Mã | Bản nguồn | Tiếng Hàn.

  python ../../pipeline_chung/cong_cu/xem_gd2.py 4812_1 5450_1
  python ../../pipeline_chung/cong_cu/xem_gd2.py --lo 91 100
"""
import os
import sys

import _chung as C

C.kiem_dang()
args = sys.argv[1:]
if args[:1] == ["--lo"]:
    ids = [s for s in C.ids_tu_den(int(args[1]), int(args[2])) if os.path.exists(C.out("claude", "gd2", s + ".md"))]
else:
    ids = args
for sid in ids:
    print("==", sid)
    with open(C.out("claude", "gd2", sid + ".md"), encoding="utf-8") as f:
        lines = f.read().splitlines()
    for ln in lines:
        if ln.startswith("**Câu đề"):
            print(ln)
        else:
            cols = ln.split("|")
            if len(cols) >= 6 and cols[1].strip()[:1] == "f" and cols[1].strip()[1:].isdigit():
                print("|".join([cols[1], cols[4], cols[5]]).strip())
