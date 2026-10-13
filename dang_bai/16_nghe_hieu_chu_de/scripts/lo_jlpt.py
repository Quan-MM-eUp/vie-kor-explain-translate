"""[Dạng 16] Gợi ý lô tiếp theo khi chỉ chạy mẫu thuộc đề JLPT (config.loc_nguon_de, quyết định 2026-10-11).

  python3 scripts/lo_jlpt.py            # lô tiếp theo: khoảng --tu X --den Y chứa đủ N mẫu JLPT chưa làm (N = config.thu_tu_chay.lo)
  python3 scripts/lo_jlpt.py --lo 3     # 3 lô liên tiếp
  python3 scripts/lo_jlpt.py --so 10 --lo 3
  python3 scripts/lo_jlpt.py --thong-ke # thống kê từ mẫu tu_mau: JLPT / NAT theo trạng thái + loại tên đề

Mẫu "chưa làm" = trạng thái ĐANG_XỬ_LÝ / CẦN_SỬA_GĐ1 (chưa qua GĐ1). Khoảng X–Y = stt trong output/thu_tu_chay.csv
(thứ tự chạy của --tu/--den – KHÁC thứ tự file dữ liệu); giá trị thi_thu_thuoc_de tra theo sample_id trong file dữ liệu.
Các mẫu NAT trong khoảng sẽ tự bị bỏ khi chạy với --tu X --den Y.
"""
import argparse
import collections
import re

import _dang as D
from pipeline_chung.common import read_csv

ap = argparse.ArgumentParser()
ap.add_argument("--so", type=int, default=int((D.cfg().get("thu_tu_chay") or {}).get("lo", 10)), help="số mẫu JLPT mỗi lô")
ap.add_argument("--lo", type=int, default=1, help="số lô cần gợi ý")
ap.add_argument("--thong-ke", action="store_true")
args = ap.parse_args()

lc = D.cfg().get("loc_nguon_de") or {}
tu = int(lc.get("tu_mau", 1))
cot = lc.get("cot", "thi_thu_thuoc_de")
st = {r["sample_id"]: r.get("trang_thai", "") for r in read_csv(D.status_path())}
order = D.thu_tu()                      # stt theo output/thu_tu_chay.csv
bo = D.mau_ngoai_jlpt()
CHUA = ("ĐANG_XỬ_LÝ", "CẦN_SỬA_GĐ1", "")

if args.thong_ke:
    c = collections.Counter(("NAT (bỏ)" if s in bo else "JLPT", st.get(s, "")) for s in order[tu - 1:])
    print(f"Từ stt {tu} đến {len(order)} ({len(order) - tu + 1} mẫu, theo output/thu_tu_chay.csv):")
    for k in ("JLPT", "NAT (bỏ)"):
        print(f"  {k}: {sum(v for (g, _), v in c.items() if g == k)}  "
              + str({t: v for (g, t), v in sorted(c.items()) if g == k}))
    gt = {D.sid_of(r): (r.get(cot) or "") for r in read_csv(D.data_path())}
    ten, mau = collections.Counter(), collections.defaultdict(set)
    for s in order:
        for p in gt.get(s, "").split("|"):
            p = p.strip()
            if p:
                m = re.match(r"^(.*?)\s*\d", p)
                t = (m.group(1) if m else p).strip()
                ten[t] += 1
                mau[t].add(s)
    trong = sum(1 for s in order if not gt.get(s, "").strip())
    print(f"Loại tên đề trong cột {cot} (toàn bộ {len(order)} mẫu thứ tự chạy): "
          + ", ".join(f"{t}: {n} lượt / {len(mau[t])} mẫu" for t, n in ten.most_common()) + f"; ô trống: {trong} mẫu")
    raise SystemExit

i, ra = tu, 0
while ra < args.lo and i <= len(order):
    if not (order[i - 1] not in bo and st.get(order[i - 1], "") in CHUA):
        i += 1
        continue
    x, n, j = i, 0, i
    while j <= len(order) and n < args.so:
        if order[j - 1] not in bo and st.get(order[j - 1], "") in CHUA:
            n += 1
        j += 1
    y = j - 1
    nat = sum(1 for s in order[x - 1:y] if s in bo)
    print(f"Lô JLPT: --tu {x} --den {y}  ({n} mẫu JLPT, bỏ {nat} mẫu NAT trong khoảng)")
    ra, i = ra + 1, y + 1
if ra == 0:
    print("Không còn mẫu JLPT chưa làm.")
