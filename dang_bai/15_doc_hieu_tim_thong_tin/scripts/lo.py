"""Lô chạy của dạng 15 (theo cột 'lo' của output/thu_tu_chay.csv – lô ~10 câu, không cắt đôi ngữ liệu).

  python3 scripts/lo.py            # bảng mọi lô: stt từ–đến, số câu, cấp độ, trạng thái
  python3 scripts/lo.py tiep       # lô tiếp theo cần chạy (lô đầu tiên còn câu chưa xong) → in "X Y"
  python3 scripts/lo.py 3          # stt từ–đến của lô 3 → in "X Y"
"""
import collections
import sys

import _dang as D
from pipeline_chung.common import read_csv
from pipeline_chung.trang_thai import Status

XONG = ("ĐẠT", "CHỜ_DUYỆT_NỘI_DUNG", "CHỜ_XỬ_LÝ_HÁN_VIỆT", "ĐÃ_DUYỆT_CTV")


def main():
    rows = read_csv(D.OUT("thu_tu_chay.csv"))
    st = Status(D.status_path())
    lo = collections.OrderedDict()
    for r in rows:
        lo.setdefault(int(r["lo"]), []).append(r)
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    if arg and arg.isdigit():
        g = lo[int(arg)]
        print(g[0]["stt"], g[-1]["stt"])
        return
    if arg == "tiep":
        for k, g in lo.items():
            if any((st.get(r["sample_id"]).get("trang_thai") or "") not in XONG for r in g):
                print(g[0]["stt"], g[-1]["stt"])
                print(f"(lô {k}: {len(g)} câu, {len({r['question_id'] for r in g})} ngữ liệu, cấp {sorted({r['cap_do'] for r in g})})", file=sys.stderr)
                return
        print("Đã xong mọi lô.", file=sys.stderr)
        return
    print(f"{'lô':>3} {'stt':>9} {'câu':>4} {'NL':>3}  cấp độ            trạng thái")
    for k, g in lo.items():
        tt = collections.Counter((st.get(r["sample_id"]).get("trang_thai") or "CHƯA_CHẠY") for r in g)
        print(f"{k:>3} {g[0]['stt']:>4}–{g[-1]['stt']:<4} {len(g):>4} {len({r['question_id'] for r in g}):>3}  "
              f"{','.join(sorted({r['cap_do'] for r in g})):17} {dict(tt)}")


if __name__ == "__main__":
    main()
