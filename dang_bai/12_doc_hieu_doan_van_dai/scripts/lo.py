"""Dạng 12 – lô chạy theo đoạn văn (cột 'lo' của output/thu_tu_chay.csv; mỗi lô = 2 đoạn văn = 6–8 câu).

  python3 scripts/lo.py          # lô tiếp theo chưa xong + khoảng stt (--tu/--den) để dùng cho mọi lệnh
  python3 scripts/lo.py 5        # khoảng stt của lô 5
  python3 scripts/lo.py --tat-ca # bảng mọi lô: stt, đoạn, cấp độ, khuôn, trạng thái
"""
import collections
import sys

import _dang as D
from pipeline_chung.common import read_csv
from pipeline_chung.trang_thai import Status

XONG = ("ĐẠT", "CHỜ_DUYỆT_NỘI_DUNG", "CHỜ_XỬ_LÝ_HÁN_VIỆT", "ĐÃ_DUYỆT_CTV")


def main():
    tt = read_csv(D.OUT("thu_tu_chay.csv"))
    st = Status(D.status_path())
    lo = collections.OrderedDict()
    for r in tt:
        lo.setdefault(int(r["lo"]), []).append(r)

    def mo_ta(n):
        rs = lo[n]
        a, b = int(rs[0]["stt"]), int(rs[-1]["stt"])
        qids = list(dict.fromkeys(r["question_id"] for r in rs))
        tts = collections.Counter(st.get(r["sample_id"]).get("trang_thai") or "CHƯA_CHẠY" for r in rs)
        khuon = collections.Counter(r["khuon_goc"] for r in rs)
        return (f"Lô {n}: --tu {a} --den {b} ({len(rs)} câu; đoạn {', '.join(qids)}; {rs[0]['cap_do']}"
                + (f"/{rs[-1]['cap_do']}" if rs[-1]["cap_do"] != rs[0]["cap_do"] else "")
                + f"; khuôn {dict(khuon)}; trạng thái {dict(tts)})")

    args = sys.argv[1:]
    if args[:1] == ["--tat-ca"]:
        for n in lo:
            print(mo_ta(n))
        return
    if args:
        print(mo_ta(int(args[0])))
        return
    for n, rs in lo.items():
        if any((st.get(r["sample_id"]).get("trang_thai") or "") not in XONG for r in rs):
            print("Lô tiếp theo – " + mo_ta(n))
            return
    print("Đã xong mọi lô.")


if __name__ == "__main__":
    main()
