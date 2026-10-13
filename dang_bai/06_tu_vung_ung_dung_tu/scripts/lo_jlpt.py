"""[Dạng 06] Chọn / phân công lô khi chỉ chạy mẫu thuộc đề JLPT (config.loc_nguon_de, quyết định 2026-10-11).

  python3 scripts/lo_jlpt.py                     # lô tiếp theo: khoảng --tu X --den Y chứa 10 mẫu JLPT chưa làm
  python3 scripts/lo_jlpt.py --lo 3              # 3 lô liên tiếp (chưa ghi phân công)
  python3 scripts/lo_jlpt.py --thong-ke          # thống kê từ mẫu tu_mau: JLPT / NAT, theo trạng thái
  python3 scripts/lo_jlpt.py --phan-cong 9 --nhom 3   # (CHẠY SONG SONG – cuộc điều phối) giao 9 lô kế tiếp cho
                                                 # 3 cuộc trò chuyện A/B/C → ghi phan_cong.json + PHAN_CONG.md
  python3 scripts/lo_jlpt.py --cap-nhat          # cập nhật tiến độ trong PHAN_CONG.md

Mẫu "chưa làm" = ĐANG_XỬ_LÝ / CẦN_SỬA_GĐ1 (chưa qua GĐ1). Khoảng X–Y theo số thứ tự file dữ liệu (= output/thu_tu_chay.csv);
mẫu NAT trong khoảng tự bị bỏ khi chạy --tu X --den Y. Lô bỏ qua các khoảng đã có trong phan_cong.json và
KHÔNG cắt ngang nhóm mẫu dùng chung một câu tiếng Nhật (lô được kéo dài đến hết nhóm).
"""
import argparse
import collections
import datetime
import json
import os
import re

import _dang as D
from pipeline_chung.common import read_csv

ap = argparse.ArgumentParser()
ap.add_argument("--so", type=int, default=int((D.cfg().get("thu_tu_chay") or {}).get("lo", 10)), help="số mẫu JLPT mỗi lô")
ap.add_argument("--lo", type=int, default=1, help="số lô cần gợi ý")
ap.add_argument("--thong-ke", action="store_true")
ap.add_argument("--phan-cong", type=int, metavar="K", help="giao K lô kế tiếp, ghi phan_cong.json + PHAN_CONG.md")
ap.add_argument("--nhom", type=int, default=3, help="số lô mỗi cuộc trò chuyện khi phân công (mặc định 3)")
ap.add_argument("--so-phan", type=int, help="chia đều các lô cho đúng N cuộc trò chuyện (thay cho --nhom)")
ap.add_argument("--cap-nhat", action="store_true", help="chỉ cập nhật tiến độ trong PHAN_CONG.md")
args = ap.parse_args()

lc = D.cfg().get("loc_nguon_de") or {}
tu = int(lc.get("tu_mau", 1))
st = {r["sample_id"]: r.get("trang_thai", "") for r in read_csv(D.status_path())}
order = [D.sid_of(r) for r in read_csv(D.data_path())]
bo = D.mau_ngoai_jlpt()
CHUA = ("ĐANG_XỬ_LÝ", "CẦN_SỬA_GĐ1", "")
PC_JSON, PC_MD = D.P("phan_cong.json"), D.P("PHAN_CONG.md")
pc = json.load(open(PC_JSON, encoding="utf-8")) if os.path.exists(PC_JSON) else {"lo": []}
da_giao = {k for x in pc["lo"] for k in range(x["tu"], x["den"] + 1)}

p_tt = D.OUT("thu_tu_chay.csv")
info = {r["sample_id"]: r for r in (read_csv(p_tt) if os.path.exists(p_tt) else [])}
NHOM = lc.get("nhom_theo")                          # (dạng 06) cột nhóm trong thu_tu_chay.csv – chỉ dùng cho thống kê


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


def chua_lam(k):        # k = số thứ tự (1-based)
    return order[k - 1] not in bo and st.get(order[k - 1], "") in CHUA and k not in da_giao


def cau(k):
    try:
        q = D.load_norm(order[k - 1])["de"]["cau_hoi"]
    except Exception:
        return None
    return re.sub(r"[\s{}　]", "", q or "")


def tinh_lo(so_lo):
    out, i = [], tu
    while len(out) < so_lo and i <= len(order):
        if not chua_lam(i):
            i += 1
            continue
        x, n, j, cuoi = i, 0, i, i
        while j <= len(order) and n < args.so and j not in da_giao:
            if chua_lam(j):
                n, cuoi = n + 1, j
            j += 1
        # kéo dài đến hết nhóm cùng câu tiếng Nhật
        k = cuoi + 1
        while k <= len(order) and k not in da_giao:
            if order[k - 1] in bo:
                k += 1
                continue
            if chua_lam(k) and cau(k) and cau(k) == cau(cuoi):
                n, cuoi = n + 1, k
                k += 1
                continue
            break
        y = cuoi
        out.append({"tu": x, "den": y, "so_jlpt": n, "so_nat": sum(1 for s in order[x - 1:y] if s in bo and st.get(s, "") in CHUA),
                    "so_ctv": sum(1 for s in order[x - 1:y] if st.get(s, "") == "ĐÃ_DUYỆT_CTV")})
        i = y + 1
    return out


def tien_do(x):
    ids = x.get("ids") or [s for s in order[x["tu"] - 1:x["den"]] if s not in bo and st.get(s, "") != "ĐÃ_DUYỆT_CTV"]
    c = collections.Counter(st.get(s, "") for s in ids)
    xong = sum(v for k, v in c.items() if k not in CHUA + ("GĐ1_XONG",)) if x.get("ids") else sum(v for k, v in c.items() if k not in CHUA)
    return f"{xong}/{len(ids)} xong" + (f" (ĐẠT {c['ĐẠT']}, cờ {c['CHỜ_DUYỆT_NỘI_DUNG']})" if xong else "")


def ghi_md():
    L = ["# Phân công chạy song song – dạng 06 ", "",
         "> Tạo bằng `python3 scripts/lo_jlpt.py --phan-cong K --nhom 3` (cuộc điều phối). **Không sửa tay.** "
         "Mỗi cuộc trò chuyện chỉ chạy các lô của phần mình, theo thứ tự. Tiến độ: `python3 scripts/lo_jlpt.py --cap-nhat`.", ""]
    for dot in sorted({x["dot"] for x in pc["lo"]}, reverse=True):
        L += [f"## Đợt {dot}", "", "| Phần | Lô (--tu --den) | JLPT / NAT bỏ / CTV đã duyệt | Tiến độ JLPT |", "|---|---|---|---|"]
        for x in [x for x in pc["lo"] if x["dot"] == dot]:
            lo_txt = f"{x['tu']}–{x['den']}" + (f" **--ids {','.join(x['ids'])}**" + (f" ({x['ghi_chu']})" if x.get("ghi_chu") else "") if x.get("ids") else "")
            L.append(f"| {x['phan']} | {lo_txt} | {x['so_jlpt']} / {x['so_nat']} / {x.get('so_ctv', '–')} | {tien_do(x)} |")
        L += ["", "Câu mở đầu cho từng cuộc trò chuyện:", ""]
        for ph in sorted({x["phan"] for x in pc["lo"] if x["dot"] == dot}):
            L.append(f"- **{ph}:** `Đọc dang_bai/06_tu_vung_ung_dung_tu/SO_TAY_CHAY.md rồi chạy dạng 06 phần {ph} đợt {dot}`")
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
        pc["lo"].append(x)
        print(f"Đợt {dot} – phần {x['phan']}: --tu {x['tu']} --den {x['den']}  ({x['so_jlpt']} mẫu JLPT, bỏ {x['so_nat']} NAT)")
    json.dump(pc, open(PC_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ghi_md()
    print(f"→ phan_cong.json, PHAN_CONG.md ({len(los)} lô)")
    raise SystemExit

los = tinh_lo(args.lo)
for x in los:
    print(f"Lô JLPT: --tu {x['tu']} --den {x['den']}  ({x['so_jlpt']} mẫu JLPT, bỏ {x['so_nat']} mẫu NAT trong khoảng)")
if not los:
    print("Không còn mẫu JLPT chưa làm.")
