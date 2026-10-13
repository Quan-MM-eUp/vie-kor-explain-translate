"""[Dạng 09 – chạy song song] Gộp nhật ký từng lô (nhat_ky_lo/<tu>_<den>.md) vào NHAT_KY.md – cuộc điều phối chạy.

  python3 scripts/gop_nhat_ky.py --xem    # chỉ in những gì sẽ gộp
  python3 scripts/gop_nhat_ky.py          # gộp theo thứ tự lô, rồi chuyển file đã gộp vào nhat_ky_lo/da_gop/

File nhật ký lô dùng đúng 4 tiêu đề của NHAT_KY.md; mỗi dòng bảng ('| …') hoặc gạch đầu dòng ('- …') dưới tiêu đề
được thêm vào cuối mục tương ứng (dòng bảng lô thêm sau dòng cuối của bảng).
"""
import argparse
import glob
import os
import re

import _dang as D

MUC = ["## Bảng lô", "## Quyết định soát đã chốt", "## Cách dịch đã thống nhất (GĐ2)", "## Sửa code / sự cố"]
ap = argparse.ArgumentParser()
ap.add_argument("--xem", action="store_true")
args = ap.parse_args()

thu_muc = D.P("nhat_ky_lo")
files = sorted(glob.glob(os.path.join(thu_muc, "*.md")),
               key=lambda f: [int(x) for x in re.findall(r"\d+", os.path.basename(f))[:2]] or [0])
if not files:
    raise SystemExit("Không có nhật ký lô nào cần gộp.")

nk_path = D.P("NHAT_KY.md")
nk = open(nk_path, encoding="utf-8").read()


def tach(text):
    out, cur = {m: [] for m in MUC}, None
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("## "):
            cur = next((m for m in MUC if s.startswith(m)), None)
            continue
        if cur and (s.startswith("|") or s.startswith("- ")) and not re.match(r"^\|\s*(Lô|---)", s):
            out[cur].append(s)
    return out


def chen(nk, muc, dong):
    if not dong:
        return nk
    a = nk.index(muc)
    b = nk.find("\n## ", a + len(muc))
    b = len(nk) if b < 0 else b
    phan = nk[a:b].rstrip("\n").split("\n")
    if muc == "## Bảng lô":
        cuoi = max(i for i, l in enumerate(phan) if l.startswith("|"))
        phan = phan[:cuoi + 1] + dong + phan[cuoi + 1:]
    else:
        phan += dong
    return nk[:a] + "\n".join(phan) + "\n" + ("\n" if b < len(nk) else "") + nk[b:].lstrip("\n")


for f in files:
    parts = tach(open(f, encoding="utf-8").read())
    n = sum(len(v) for v in parts.values())
    print(f"{os.path.basename(f)}: " + ", ".join(f"{m[3:]} {len(v)}" for m, v in parts.items()))
    if n == 0:
        print("   (không có dòng nào – bỏ qua, không chuyển file)")
        continue
    if not args.xem:
        for m in MUC:
            nk = chen(nk, m, parts[m])

if not args.xem:
    open(nk_path, "w", encoding="utf-8").write(nk)
    for f in files:
        dst = os.path.join(thu_muc, "da_gop", os.path.basename(f))
        if os.path.exists(dst):
            dst = dst[:-3] + "_2.md"
        os.rename(f, dst)
    print(f"Đã gộp {len(files)} file vào NHAT_KY.md, chuyển sang nhat_ky_lo/da_gop/.")
