"""[Dạng 10] Gợi ý lô tiếp theo khi chỉ chạy mẫu thuộc đề JLPT (config.loc_nguon_de, quyết định 2026-10-11).

  python3 scripts/lo_jlpt.py              # lô tiếp theo: khoảng --tu X --den Y chứa 10 (lô nhỏ 5 với mẫu có lo_nho) mẫu JLPT chưa làm
  python3 scripts/lo_jlpt.py --lo 3       # 3 lô liên tiếp
  python3 scripts/lo_jlpt.py --thong-ke   # thống kê từ mẫu tu_mau: JLPT / NAT theo trạng thái + loại tên đề

Mẫu "chưa làm" = trạng thái ĐANG_XỬ_LÝ / CẦN_SỬA_GĐ1 (chưa qua GĐ1). Khoảng X–Y theo stt của output/thu_tu_chay.csv
(đúng thứ tự --tu/--den của dạng này); các mẫu NAT trong khoảng sẽ tự bị bỏ khi chạy với --tu X --den Y.
Lô không cắt đôi nhóm chung đoạn văn (cột nhom_doan_van) – có thể dư 1–2 mẫu; mẫu có lo_nho (khuôn B) chạy lô 5 và không gộp chung lô với mẫu thường.
"""
import argparse
import collections
import os
import re

import _dang as D
from pipeline_chung.common import read_csv

C = D.cfg()
lc = C.get("loc_nguon_de") or {}
NHOM = lc.get("nhom_theo")                          # cột nhóm trong thu_tu_chay.csv – không cắt đôi nhóm
LO_NHO = int((C.get("lo_nho") or {}).get("so_cau", 0)) or None   # mẫu có cột lo_nho → lô nhỏ

ap = argparse.ArgumentParser()
ap.add_argument("--so", type=int, default=int((C.get("thu_tu_chay") or {}).get("lo", 10)),
                help="số mẫu JLPT mỗi lô (mặc định theo config.thu_tu_chay.lo)")
ap.add_argument("--lo", type=int, default=1, help="số lô cần gợi ý")
ap.add_argument("--thong-ke", action="store_true")
args = ap.parse_args()

tu = int(lc.get("tu_mau", 1))
st = {r["sample_id"]: r.get("trang_thai", "") for r in read_csv(D.status_path())}
p_tt = D.OUT("thu_tu_chay.csv")
tt = read_csv(p_tt) if os.path.exists(p_tt) else []
order = D.thu_tu() if hasattr(D, "thu_tu") else [D.sid_of(r) for r in read_csv(D.data_path())]
info = {r["sample_id"]: r for r in tt}
bo = D.mau_ngoai_jlpt()
CHUA = ("ĐANG_XỬ_LÝ", "CẦN_SỬA_GĐ1", "")


def loai_ten_de(rows, cot):
    c, vd = collections.Counter(), {}
    for r in rows:
        v = (r.get(cot) or "").strip()
        if not v:
            c["(trống)"] += 1
            continue
        for x in (y.strip() for y in v.split("|")):
            if x:
                m = re.match(r"^(.*?)\s*\d", x)
                t = (m.group(1) if m else x).strip()
                c[t] += 1
                vd.setdefault(t, x)
    return c, vd


if args.thong_ke:
    c = collections.Counter(("NAT (bỏ)" if s in bo else "JLPT", st.get(s, "")) for s in order[tu - 1:])
    print(f"Từ mẫu {tu} đến {len(order)} ({len(order) - tu + 1} mẫu):")
    for k in ("JLPT", "NAT (bỏ)"):
        print(f"  {k}: {sum(v for (g, _), v in c.items() if g == k)}  "
              + str({t: v for (g, t), v in sorted(c.items()) if g == k}))
    if NHOM:
        g = collections.OrderedDict()
        for s in order[tu - 1:]:
            g.setdefault((info.get(s) or {}).get(NHOM) or s, []).append(s)
        print(f"  Nhóm `{NHOM}` từ mẫu {tu}: {sum(all(x not in bo for x in v) for v in g.values())} nhóm JLPT · "
              f"{sum(all(x in bo for x in v) for v in g.values())} nhóm NAT · "
              f"{sum(0 < sum(x in bo for x in v) < len(v) for v in g.values())} nhóm lẫn")
    cot = lc.get("cot", "thi_thu_thuoc_de")
    rows = read_csv(D.data_path())
    pos = {s: i for i, s in enumerate(order, 1)}
    for nhan, rr in (("toàn bộ file dữ liệu", rows), (f"từ mẫu {tu}", [r for r in rows if pos.get(D.sid_of(r), 0) >= tu])):
        cc, vd = loai_ten_de(rr, cot)
        print(f"Loại tên đề trong cột {cot} ({nhan}; lượt, tách theo '|'):")
        for t, v in cc.most_common():
            print(f"  {t!r}: {v}" + (f"   vd: {vd[t]}" if t in vd else ""))
    BIET = {"(trống)", "Test", "Nat Test", "Reading Test", "Vocabulary Test", "Mock Full Exam", "Listening Test"}
    la = [t for t in loai_ten_de(rows, cot)[0] if t not in BIET]
    if la:
        print(f"!! CÓ LOẠI TÊN ĐỀ MỚI chưa có quyết định giữ/bỏ: {la} – DỪNG, hỏi người dùng trước khi chạy lô.")
    raise SystemExit

# đơn vị = nhóm liền nhau (cùng giá trị cột nhom_theo); không có nhom_theo → mỗi mẫu một đơn vị
units = []
for i, s in enumerate(order, 1):
    k = (info.get(s) or {}).get(NHOM) if NHOM else None
    if units and k and units[-1]["k"] == k:
        units[-1]["ids"].append(s)
    else:
        units.append({"k": k, "dau": i, "ids": [s], "nho": bool((info.get(s) or {}).get("lo_nho"))})
for u in units:
    u["cuoi"] = u["dau"] + len(u["ids"]) - 1
    u["cho"] = all(x not in bo and st.get(x, "") in CHUA for x in u["ids"])

ra, j = 0, 0
while ra < args.lo and j < len(units):
    if units[j]["dau"] < tu or not units[j]["cho"]:
        j += 1
        continue
    nho = units[j]["nho"]
    so = (LO_NHO or args.so) if nho else args.so
    x, n, k = units[j]["dau"], 0, j
    while k < len(units) and n < so and units[k]["nho"] == nho:
        if units[k]["cho"]:
            n += len(units[k]["ids"])
        k += 1
    y = units[k - 1]["cuoi"]
    nat = sum(1 for s in order[x - 1:y] if s in bo)
    them = f", lô nhỏ {so}" if nho else ""
    if NHOM:
        them += f", {sum(1 for u in units[j:k] if u['cho'])} nhóm `{NHOM}` trọn"
    print(f"Lô JLPT: --tu {x} --den {y}  ({n} mẫu JLPT, bỏ {nat} mẫu NAT trong khoảng{them})")
    ra, j = ra + 1, k
if ra == 0:
    print("Không còn mẫu JLPT chưa làm.")
