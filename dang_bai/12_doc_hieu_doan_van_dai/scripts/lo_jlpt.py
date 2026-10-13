"""[Dạng 12] Gợi ý lô tiếp theo khi chỉ chạy mẫu thuộc đề JLPT (config.loc_nguon_de, quyết định 2026-10-11).

  python3 scripts/lo_jlpt.py              # lô JLPT tiếp theo (theo cột 'lo' của output/thu_tu_chay.csv)
  python3 scripts/lo_jlpt.py --lo 3       # 3 lô JLPT liên tiếp
  python3 scripts/lo_jlpt.py --thong-ke   # thống kê từ stt tu_mau: JLPT / NAT theo trạng thái, đoạn, lô, loại tên đề

Lô giữ nguyên cột 'lo' (không đánh lại số, không sửa thu_tu_chay.csv). Mỗi lô in khoảng stt --tu X --den Y (phần
từ tu_mau trở đi); khi chạy với --tu X --den Y, _dang.select_ids tự bỏ mẫu NAT trong khoảng. Chỉ đếm mẫu JLPT CHƯA
xong (trạng thái không thuộc XONG); lô toàn NAT hoặc đã xong bị bỏ qua. Dùng script này thay cho gợi ý lô của
CC/tien_do.py (công cụ chung vẫn đếm mẫu NAT là ĐANG_XỬ_LÝ).
"""
import argparse
import collections
import re

import _dang as D
from pipeline_chung.common import read_csv

XONG = ("ĐẠT", "CHỜ_DUYỆT_NỘI_DUNG", "CHỜ_XỬ_LÝ_HÁN_VIỆT", "ĐÃ_DUYỆT_CTV")

ap = argparse.ArgumentParser()
ap.add_argument("--lo", type=int, default=1, help="số lô cần gợi ý")
ap.add_argument("--thong-ke", action="store_true")
args = ap.parse_args()

lc = D.cfg().get("loc_nguon_de") or {}
tu = int(lc.get("tu_mau", 1))
cot = lc.get("cot", "thi_thu_thuoc_de")
tt = read_csv(D.OUT("thu_tu_chay.csv"))
st = {r["sample_id"]: r.get("trang_thai", "") for r in read_csv(D.status_path())}
bo = D.mau_ngoai_jlpt()
if not lc.get("bat"):
    print("⚠ config.loc_nguon_de.bat = false → không lọc mẫu NAT.")
KHOA = "doan" if tt and "doan" in tt[0] else "question_id"

lo = collections.OrderedDict()
for r in tt:
    if int(r["stt"]) >= tu:
        lo.setdefault(int(r["lo"]), []).append(r)


def chua_xong(r):
    return (st.get(r["sample_id"]) or "") not in XONG


if args.thong_ke:
    gt = {D.sid_of(r): (r.get(cot) or "") for r in read_csv(D.data_path())}
    sau = [r for r in tt if int(r["stt"]) >= tu]
    c = collections.Counter(("NAT (bỏ)" if r["sample_id"] in bo else "JLPT", st.get(r["sample_id"], "")) for r in sau)
    print(f"Từ stt {tu} đến {len(tt)} ({len(sau)} mẫu, theo output/thu_tu_chay.csv):")
    for k in ("JLPT", "NAT (bỏ)"):
        print(f"  {k}: {sum(v for (g, _), v in c.items() if g == k)}  "
              + str({t: v for (g, t), v in sorted(c.items()) if g == k}))
    doan = collections.OrderedDict()
    for r in sau:
        doan.setdefault(r[KHOA], []).append(r["sample_id"] in bo)
    lan = [k for k, v in doan.items() if any(v) and not all(v)]
    print(f"  Đoạn văn (cột {KHOA}): {len(doan)} · toàn NAT {sum(all(v) for v in doan.values())} · lẫn NAT/JLPT {len(lan)}"
          + (f" ⚠ {lan[:10]}" if lan else ""))
    print(f"  Lô (cột lo): {len(lo)} · toàn NAT (bỏ hẳn) {sum(all(r['sample_id'] in bo for r in g) for g in lo.values())}"
          f" · còn mẫu JLPT chưa xong {sum(any(r['sample_id'] not in bo and chua_xong(r) for r in g) for g in lo.values())}")
    for ten, ds in (("toàn file dữ liệu", list(gt.values())), (f"từ stt {tu}", [gt.get(r["sample_id"], "") for r in sau])):
        de = collections.Counter()
        for v in ds:
            for p in v.split("|"):
                p = p.strip()
                if p:
                    m = re.match(r"^(.*?)\s*\d", p)
                    de[(m.group(1) if m else p).strip()] += 1
        print(f"  Loại tên đề ({ten}, số lượt): {dict(de.most_common())} · ô trống {sum(1 for v in ds if not v.strip())}")
    raise SystemExit

ra = 0
for n, g in lo.items():
    jl = [r for r in g if r["sample_id"] not in bo and chua_xong(r)]
    nat = [r for r in g if r["sample_id"] in bo]
    if not jl:
        if nat and len(nat) == len(g):
            print(f"  (bỏ qua lô {n}: stt {g[0]['stt']}–{g[-1]['stt']} toàn NAT, {len(nat)} mẫu)")
        continue
    print(f"Lô {n}: --tu {g[0]['stt']} --den {g[-1]['stt']} ({len(jl)} mẫu JLPT, bỏ {len(nat)} mẫu NAT)")
    ra += 1
    if ra >= args.lo:
        break
if ra == 0:
    print("Không còn mẫu JLPT chưa xong.")
