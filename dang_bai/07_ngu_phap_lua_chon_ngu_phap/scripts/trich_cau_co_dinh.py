"""[Dạng 07 – chạy song song] Trích "Cách dịch đã thống nhất (GĐ2)" của NHAT_KY.md + các nhat_ky_lo/*.md chưa gộp
ra một file cho tác tử TẠO GĐ2 đọc (thay cho dán thẳng vào lời giao việc – mục này đã dài):
  cd scripts && python3 trich_cau_co_dinh.py --tu X --den Y   → output/claude/cau_co_dinh_X_Y.md
"""
import glob
import os
import re

import _dang as D

MUC = "## Cách dịch đã thống nhất (GĐ2)"


def lay(text):
    a = text.find(MUC)
    if a < 0:
        return []
    b = text.find("\n## ", a + len(MUC))
    return [l for l in text[a + len(MUC):b if b > 0 else None].splitlines() if l.strip().startswith("- ")]


dong = lay(open(D.P("NHAT_KY.md"), encoding="utf-8").read())
for f in sorted(glob.glob(D.P("nhat_ky_lo", "*.md"))):
    dong += lay(open(f, encoding="utf-8").read())
out = D.OUT("claude", f"cau_co_dinh{D.hau_to_lo()}.md")
open(out, "w", encoding="utf-8").write(MUC + "\n" + "\n".join(dong) + "\n")
print(f"{len(dong)} dòng → {os.path.relpath(out, D.DANG)}")
