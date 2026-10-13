"""Giai đoạn 1 – Bước 1.5: bạn duyệt JSON tiếng Việt → chốt vào output/json_vi/final/.

Chép các câu GĐ1_XONG từ checked/ sang final/ và ghi "đã duyệt" vào trang_thai.csv.
Câu bạn không đồng ý: --tra-lai <id1,id2> --ly-do "…" → trạng thái CẦN_SỬA_GĐ1 (chạy lại từ bước 1.1 hoặc 1.2).

Cách chạy:
  python scripts/s1_chot.py --pilot
  python scripts/s1_chot.py --pilot --tra-lai 2610_1 --ly-do "phân tích lựa chọn 4 chưa đúng"
"""
import argparse
import datetime
import shutil

import _dang as D
from pipeline_chung.trang_thai import Status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--ids")
    ap.add_argument("--lo", type=int)
    ap.add_argument("--tat-ca", action="store_true")
    ap.add_argument("--tra-lai", default="", help="các id không duyệt, cách nhau bằng dấu phẩy")
    ap.add_argument("--ly-do", default="bạn không duyệt")
    args = ap.parse_args()
    st = Status(D.status_path())
    reject = {x.strip() for x in args.tra_lai.split(",") if x.strip()}
    ok = back = 0
    for sid in D.select_ids(args, st, ("GĐ1_XONG",)):
        if sid in reject:
            st.update(sid, trang_thai="CẦN_SỬA_GĐ1", giai_doan_loi="1", loi=f"Không duyệt: {args.ly_do}", duyet_vi="")
            back += 1
            continue
        if st.get(sid).get("trang_thai") != "GĐ1_XONG":
            continue
        D.os.makedirs(D.OUT("json_vi", "final"), exist_ok=True)
        shutil.copyfile(D.OUT("json_vi", "checked", sid + ".json"), D.OUT("json_vi", "final", sid + ".json"))
        st.update(sid, duyet_vi=f"đã duyệt {datetime.date.today().isoformat()}")
        ok += 1
    st.save()
    print(f"Đã chốt {ok} câu vào output/json_vi/final/; trả lại {back} câu (CẦN_SỬA_GĐ1).")


if __name__ == "__main__":
    main()
