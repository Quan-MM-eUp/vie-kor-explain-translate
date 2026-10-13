"""Dạng 13: danh sách lô (theo cột 'lo' của output/thu_tu_chay.csv – lô = 4 đoạn văn, không cắt ngang đoạn) + trạng thái + lô tiếp theo.

  python3 scripts/lo.py          # bảng các lô: stt từ–đến, số đoạn / câu, trạng thái
  python3 scripts/lo.py 3        # in lệnh phạm vi của lô 3: --tu X --den Y
"""
import collections
import os
import sys

import _dang as D
from pipeline_chung.common import read_csv

XONG = ("ĐẠT", "CHỜ_DUYỆT_NỘI_DUNG", "CHỜ_XỬ_LÝ_HÁN_VIỆT", "ĐÃ_DUYỆT_CTV")


def main():
    p = D.OUT("thu_tu_chay.csv")
    if not os.path.exists(p):
        sys.exit("Chưa có output/thu_tu_chay.csv – chạy python3 scripts/s0_chuan_bi.py trước")
    tt = read_csv(p)
    stp = D.status_path()
    st = {r["sample_id"]: r for r in read_csv(stp)} if os.path.exists(stp) else {}
    lo = collections.OrderedDict()
    for x in tt:
        lo.setdefault(int(x["lo"]), []).append(x)
    if len(sys.argv) > 1:
        xs = lo[int(sys.argv[1])]
        print(f"--tu {xs[0]['stt']} --den {xs[-1]['stt']}")
        return
    tiep = None
    for k, xs in lo.items():
        c = collections.Counter((st.get(x["sample_id"]) or {}).get("trang_thai") or "CHƯA_CHẠY" for x in xs)
        xong = sum(v for s, v in c.items() if s in XONG)
        if tiep is None and xong < len(xs):
            tiep = k
        print(f"lô {k:>2}: --tu {xs[0]['stt']:>3} --den {xs[-1]['stt']:<3} · {len({x['question_id'] for x in xs})} đoạn · {len(xs):>2} câu · "
              f"{', '.join(sorted({x['kieu_doan'] for x in xs}))} · {dict(c)}")
    if tiep:
        xs = lo[tiep]
        print(f"\nLô tiếp theo: lô {tiep} (mẫu {xs[0]['stt']}–{xs[-1]['stt']})")
    else:
        print("\nĐã xong mọi lô.")


if __name__ == "__main__":
    main()
