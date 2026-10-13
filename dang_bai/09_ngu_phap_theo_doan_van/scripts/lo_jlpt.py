"""[Dạng 09] Chọn / phân công lô khi chỉ chạy mẫu thuộc đề JLPT (config.loc_nguon_de, quyết định 2026-10-11).

  python3 scripts/lo_jlpt.py              # lô tiếp theo: khoảng --tu X --den Y chứa 12 mẫu JLPT chưa làm
  python3 scripts/lo_jlpt.py --lo 3       # 3 lô liên tiếp
  python3 scripts/lo_jlpt.py --thong-ke   # thống kê từ mẫu tu_mau: JLPT / NAT theo trạng thái + loại tên đề
  python3 scripts/lo_jlpt.py --phan-cong 30 --so-phan 10   # (CHẠY SONG SONG – cuộc điều phối) giao 30 lô kế tiếp
                                          # cho 10 cuộc trò chuyện A–J → ghi phan_cong.json + PHAN_CONG.md
  python3 scripts/lo_jlpt.py --cap-nhat   # cập nhật tiến độ trong PHAN_CONG.md

Mẫu "chưa làm" = trạng thái ĐANG_XỬ_LÝ / CẦN_SỬA_GĐ1 (chưa qua GĐ1). Khoảng X–Y theo stt của output/thu_tu_chay.csv
(đúng thứ tự --tu/--den của dạng này); các mẫu NAT trong khoảng sẽ tự bị bỏ khi chạy với --tu X --den Y.
Lô tròn đoạn văn: 12 mẫu JLPT = 3 đoạn (cột doan), không cắt đôi đoạn; đoạn NAT trong khoảng bị bỏ trọn.
Lô bỏ qua các khoảng đã có trong phan_cong.json (chạy song song, 2026-10-13 – theo dạng 07/08).
"""
import argparse
import collections
import datetime
import json
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
ap.add_argument("--phan-cong", type=int, metavar="K", help="giao K lô kế tiếp, ghi phan_cong.json + PHAN_CONG.md")
ap.add_argument("--nhom", type=int, default=3, help="số lô mỗi cuộc trò chuyện khi phân công (mặc định 3)")
ap.add_argument("--so-phan", type=int, help="chia đều các lô cho đúng N cuộc trò chuyện (thay cho --nhom)")
ap.add_argument("--cap-nhat", action="store_true", help="chỉ cập nhật tiến độ trong PHAN_CONG.md")
args = ap.parse_args()

tu = int(lc.get("tu_mau", 1))
st = {r["sample_id"]: r.get("trang_thai", "") for r in read_csv(D.status_path())}
p_tt = D.OUT("thu_tu_chay.csv")
tt = read_csv(p_tt) if os.path.exists(p_tt) else []
order = D.thu_tu() if hasattr(D, "thu_tu") else [D.sid_of(r) for r in read_csv(D.data_path())]
info = {r["sample_id"]: r for r in tt}
bo = D.mau_ngoai_jlpt()
CHUA = ("ĐANG_XỬ_LÝ", "CẦN_SỬA_GĐ1", "")
PC_JSON, PC_MD = D.P("phan_cong.json"), D.P("PHAN_CONG.md")
pc = json.load(open(PC_JSON, encoding="utf-8")) if os.path.exists(PC_JSON) else {"lo": []}
da_giao = {k for x in pc["lo"] for k in range(x["tu"], x["den"] + 1)}


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
    u["giao"] = any(k in da_giao for k in range(u["dau"], u["cuoi"] + 1))
    u["cho"] = all(x not in bo and st.get(x, "") in CHUA for x in u["ids"]) and not u["giao"]


def tinh_lo(so_lo):
    out, j = [], 0
    while len(out) < so_lo and j < len(units):
        if units[j]["dau"] < tu or not units[j]["cho"]:
            j += 1
            continue
        nho = units[j]["nho"]
        so = (LO_NHO or args.so) if nho else args.so
        x, n, k = units[j]["dau"], 0, j
        while k < len(units) and n < so and units[k]["nho"] == nho and not units[k]["giao"]:
            if units[k]["cho"]:
                n += len(units[k]["ids"])
            k += 1
        y = units[k - 1]["cuoi"]
        out.append({"tu": x, "den": y, "so_jlpt": n, "so_nat": sum(1 for s in order[x - 1:y] if s in bo),
                    "so_ctv": sum(1 for s in order[x - 1:y] if st.get(s, "") == "ĐÃ_DUYỆT_CTV"),
                    "so_nhom": sum(1 for u in units[j:k] if u["cho"]), "lo_nho": so if nho else None})
        j = k
    return out


def tien_do(x):
    ids = x.get("ids") or [s for s in order[x["tu"] - 1:x["den"]] if s not in bo and st.get(s, "") != "ĐÃ_DUYỆT_CTV"]
    c = collections.Counter(st.get(s, "") for s in ids)
    xong = sum(v for k, v in c.items() if k not in CHUA + ("GĐ1_XONG",)) if x.get("ids") else sum(v for k, v in c.items() if k not in CHUA)
    return f"{xong}/{len(ids)} xong" + (f" (ĐẠT {c['ĐẠT']}, cờ {c['CHỜ_DUYỆT_NỘI_DUNG']})" if xong else "")


def ghi_md():
    L = ["# Phân công chạy song song – dạng 09 ", "",
         "> Tạo bằng `python3 scripts/lo_jlpt.py --phan-cong K --so-phan N` (cuộc điều phối). **Không sửa tay.** "
         "Mỗi cuộc trò chuyện chỉ chạy các lô của phần mình, theo thứ tự. Tiến độ: `python3 scripts/lo_jlpt.py --cap-nhat`.", ""]
    for dot in sorted({x["dot"] for x in pc["lo"]}, reverse=True):
        L += [f"## Đợt {dot}", "", "| Phần | Lô (--tu --den) | JLPT / NAT bỏ / CTV đã duyệt | Tiến độ JLPT |", "|---|---|---|---|"]
        for x in [x for x in pc["lo"] if x["dot"] == dot]:
            lo_txt = f"{x['tu']}–{x['den']}" + (f" **--ids {','.join(x['ids'])}**" + (f" ({x['ghi_chu']})" if x.get("ghi_chu") else "") if x.get("ids") else "")
            L.append(f"| {x['phan']} | {lo_txt} | {x['so_jlpt']} / {x['so_nat']} / {x.get('so_ctv', '–')} | {tien_do(x)} |")
        L += ["", "Câu mở đầu cho từng cuộc trò chuyện:", ""]
        for ph in sorted({x["phan"] for x in pc["lo"] if x["dot"] == dot}):
            L.append(f"- **{ph}:** `Đọc dang_bai/09_ngu_phap_theo_doan_van/SO_TAY_CHAY.md rồi chạy dạng 09 phần {ph} đợt {dot}`")
        L.append("")
    open(PC_MD, "w", encoding="utf-8").write("\n".join(L))


if args.cap_nhat:
    ghi_md()
    print(f"Đã cập nhật {os.path.relpath(PC_MD, D.DANG)}")
    raise SystemExit

if args.phan_cong:
    los = tinh_lo(args.phan_cong)
    dot = max([x["dot"] for x in pc["lo"]] or [0]) + 1
    ngay = datetime.date.today().isoformat()
    if args.so_phan:
        q, r = divmod(len(los), args.so_phan)
        nhan = [chr(ord("A") + k) for k in range(args.so_phan) for _ in range(q + (1 if k < r else 0))]
    else:
        nhan = [chr(ord("A") + n // args.nhom) for n in range(len(los))]
    for n, x in enumerate(los):
        x.update(dot=dot, phan=nhan[n], ngay=ngay)
        x.pop("so_nhom", None), x.pop("lo_nho", None)
        pc["lo"].append(x)
        print(f"Đợt {dot} – phần {x['phan']}: --tu {x['tu']} --den {x['den']}  ({x['so_jlpt']} mẫu JLPT, bỏ {x['so_nat']} NAT)")
    json.dump(pc, open(PC_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ghi_md()
    print(f"→ phan_cong.json, PHAN_CONG.md ({len(los)} lô)")
    raise SystemExit

los = tinh_lo(args.lo)
for x in los:
    them = (f", lô nhỏ {x['lo_nho']}" if x["lo_nho"] else "") + (f", {x['so_nhom']} nhóm `{NHOM}` trọn" if NHOM else "")
    print(f"Lô JLPT: --tu {x['tu']} --den {x['den']}  ({x['so_jlpt']} mẫu JLPT, bỏ {x['so_nat']} mẫu NAT trong khoảng{them})")
if not los:
    print("Không còn mẫu JLPT chưa làm.")
