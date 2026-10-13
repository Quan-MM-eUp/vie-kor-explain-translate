"""Lô chạy dạng 21 (theo BÀI NGHE – 5 bài / lô, bài 2 câu hỏi không tách). Đọc output/lo_chay.csv + trạng thái.

  python3 scripts/lo.py           # bảng mọi lô: khoảng mẫu (--tu/--den), bài, khuôn, trạng thái
  python3 scripts/lo.py tiep      # lô tiếp theo cần chạy (lô đầu tiên còn câu chưa xong)
  python3 scripts/lo.py 3         # khoảng mẫu của lô 3
"""
import collections
import sys

import _dang as D
from pipeline_chung.common import read_csv
from pipeline_chung.trang_thai import Status

XONG = ("ĐẠT", "CHỜ_DUYỆT_NỘI_DUNG", "CHỜ_XỬ_LÝ_HÁN_VIỆT", "ĐÃ_DUYỆT_CTV", "LỖI_GĐ1")
lo = read_csv(D.OUT("lo_chay.csv"))
tt = read_csv(D.OUT("thu_tu_chay.csv"))
st = Status(D.status_path())


def trang_thai(x):
    ids = [r["sample_id"] for r in tt if r["lo"] == x["lo"]]
    return collections.Counter(st.get(s).get("trang_thai") or "CHƯA_CHẠY" for s in ids), ids


arg = sys.argv[1] if len(sys.argv) > 1 else ""
if arg == "tiep":
    for x in lo:
        c, ids = trang_thai(x)
        chua = [s for s in ids if (st.get(s).get("trang_thai") or "") not in XONG]
        if chua:
            print(f"Lô tiếp theo: {x['lo']} → --tu {x['tu']} --den {x['den']} · {x['so_bai']} bài {x['bai']} · {x['so_cau']} câu · khuôn {x['khuon']} · {dict(c)}")
            print(f'Câu lệnh cho người dùng: "Chạy dạng 21 mẫu {x["tu"]} đến {x["den"]}"')
            break
    else:
        print("Đã chạy hết các lô.")
elif arg.isdigit():
    x = next(x for x in lo if x["lo"] == arg)
    print(f"Lô {arg}: --tu {x['tu']} --den {x['den']} · bài {x['bai']} · khuôn {x['khuon']}")
else:
    for x in lo:
        c, _ = trang_thai(x)
        print(f"Lô {x['lo']:>2}: mẫu {x['tu']:>3}–{x['den']:<3} · {x['so_bai']} bài / {x['so_cau']} câu · {x['khuon']:<22} · {dict(c)}")
