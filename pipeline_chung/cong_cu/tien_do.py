"""Tiến độ của dạng: đếm trạng thái theo thứ tự chạy, mẫu tiếp theo cần làm.

  python ../../pipeline_chung/cong_cu/tien_do.py            # toàn bộ
  python ../../pipeline_chung/cong_cu/tien_do.py 91 100     # một lô: trạng thái + bước đã qua của từng mẫu (tạo / soát / chốt VI, tạo / soát KO)
"""
import collections
import sys

import _chung as C

C.kiem_dang()
tt, st = C.thu_tu(), C.trang_thai()
CHUA = "CHƯA_CHẠY"


def tt_of(sid):
    return (st.get(sid) or {}).get("trang_thai") or CHUA


def buoc(sid):
    """Bước đã qua của mẫu (dựa vào file): tạo VI → soát VI → chốt VI → tạo KO → soát KO."""
    import os
    ex = lambda *p: os.path.exists(C.out(*p))  # noqa: E731

    def soat(lop):
        p = C.out(lop, "checked", sid + ".ly_do.json")
        if not os.path.exists(p):
            return "–"
        return "dở (còn _huong_dan)" if "_huong_dan" in C.lj(p) else "xong"
    tao_vi = ex("json_vi", "claude_tao", sid + ".json") or ex("json_vi", "gpt", sid + ".json")
    tao_ko = ex("json_ko", "claude_tao", sid + ".json") or ex("json_ko", "gpt", sid + ".json")
    return (f"tạo VI {'✓' if tao_vi else '–'} | soát VI {soat('json_vi')} | chốt VI {'✓' if ex('json_vi', 'final', sid + '.json') else '–'}"
            f" | tạo KO {'✓' if tao_ko else '–'} | soát KO {soat('json_ko')}")


if len(sys.argv) == 3:
    tu, den = int(sys.argv[1]), int(sys.argv[2])
    for stt, sid in tt:
        if tu <= stt <= den:
            print(f"{stt:5d}  {sid:10s}  {tt_of(sid):20s} {buoc(sid)}")
    c = collections.Counter(tt_of(sid) for stt, sid in tt if tu <= stt <= den)
    print("Lô:", dict(c))
else:
    c = collections.Counter(tt_of(sid) for _, sid in tt)
    print(f"Tổng {len(tt)} mẫu theo thứ tự chạy:", dict(c))
    xong = ("ĐẠT", "CHỜ_DUYỆT_NỘI_DUNG", "CHỜ_XỬ_LÝ_HÁN_VIỆT")
    chua = [stt for stt, sid in tt if tt_of(sid) not in xong]
    tiep = chua[0] if chua else None
    print(f"Đã xong {len(tt) - len(chua)} mẫu. Mẫu chưa xong đầu tiên: stt {tiep}"
          + (f" ({tt[tiep - 1][1]}, {tt_of(tt[tiep - 1][1])})" if tiep else ""))
    if tiep:
        import csv
        with open(C.out("thu_tu_chay.csv"), encoding="utf-8-sig") as f:
            cot_lo = {int(r["stt"]): r.get("lo") for r in csv.DictReader(f)}
        if cot_lo.get(tiep):           # dạng 15 (đọc hiểu): thu_tu_chay.csv có cột 'lo' – lô tròn ngữ liệu, cỡ lô thay đổi
            cung = [s for s, l in cot_lo.items() if l == cot_lo[tiep] and s >= tiep]
            print(f"Lô tiếp theo gợi ý: {tiep} đến {max(cung)} (lô {cot_lo[tiep]} theo cột 'lo' của thu_tu_chay.csv)")
        else:
            lo = int((C.cfg().get("thu_tu_chay") or {}).get("lo", 10))     # dạng 09: lô 12 câu = 3 đoạn văn
            print(f"Lô tiếp theo gợi ý: {tiep} đến {tiep + lo - 1}")
