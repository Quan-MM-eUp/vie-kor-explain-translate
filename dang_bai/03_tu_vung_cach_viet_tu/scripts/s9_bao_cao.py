"""Báo cáo tổng hợp – số liệu để đối chiếu với tiêu chí đạt (workflow chi tiết mục 10).

- Trạng thái các câu trong phạm vi
- Giai đoạn 1 / 2: tỷ lệ ĐẠT Python trên bản GPT và sau khi Claude sửa
- Chỗ Claude đã sửa: theo loại và mức độ (có bao nhiêu lỗi nghiêm trọng)
- Riêng nhóm nghi_don_phan_tich: bao nhiêu câu còn lỗi K3
- Token GPT (tổng, trung bình mỗi câu) ở mỗi giai đoạn
- Kết quả CTV: chưa có (sẽ bổ sung khi có script nhận file CTV)

Cách chạy:  python scripts/s9_bao_cao.py --pilot     (hoặc --ids / --tat-ca)
Kết quả:    output/reports/bao_cao_tong_hop.md
"""
import argparse
import collections
import json
import os

import _dang as D
from pipeline_chung.common import load_json
from pipeline_chung.trang_thai import Status


def usage(path, ids):
    tot, n = collections.Counter(), 0
    if os.path.exists(path):
        last = {}
        with open(path, encoding="utf-8") as f:
            for line in f:
                m = json.loads(line)
                if m.get("sample_id") in ids and m.get("usage"):
                    last[m["sample_id"]] = m["usage"]          # lần chạy gần nhất của mỗi câu
        for u in last.values():
            tot["vao"] += u.get("prompt_tokens", 0)
            tot["ra"] += u.get("completion_tokens", 0)
        n = len(last)
    return tot, n


def pass_rate(path, ids):
    if not os.path.exists(path):
        return None
    rs = [r for r in load_json(path)["results"] if r["sample_id"] in ids]
    if not rs:
        return None
    return {"n": len(rs), "gpt_dat": sum(1 for r in rs if not r["ban_gpt"]["loi"]), "cuoi_dat": sum(1 for r in rs if not r["loi"]),
            "k3": sum(1 for r in rs if any(x.startswith("K3") for x in r["loi"]))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--ids")
    ap.add_argument("--lo", type=int)
    ap.add_argument("--tat-ca", action="store_true")
    args = ap.parse_args()
    st = Status(D.status_path())
    ids = set(D.select_ids(args, st, tuple()))
    rows = [st.get(s) for s in ids if st.get(s)]
    L = [f"# Báo cáo tổng hợp – dạng 03 ({len(ids)} câu)", ""]

    L += ["## Trạng thái", "", "| Trạng thái | Số câu |", "|---|---|"]
    for k, v in collections.Counter(r.get("trang_thai") for r in rows).most_common():
        L.append(f"| {k} | {v} |")

    for gd, path in (("1 – JSON tiếng Việt", D.OUT("reports", "validate_vi.json")), ("2 – bản dịch", D.OUT("reports", "check_ko.json"))):
        pr = pass_rate(path, ids)
        L += ["", f"## Giai đoạn {gd}", ""]
        if not pr:
            L.append("Chưa có kết quả.")
            continue
        L += ["| Chỉ số | Kết quả |", "|---|---|",
              f"| Bản GPT ĐẠT Python | {pr['gpt_dat']}/{pr['n']} ({pr['gpt_dat'] / pr['n']:.0%}) |",
              f"| Sau Claude ĐẠT Python | {pr['cuoi_dat']}/{pr['n']} ({pr['cuoi_dat'] / pr['n']:.0%}) – tiêu chí ≥ 90% |"]
        if gd.startswith("1"):
            don = [s for s in ids if "nghi_don_phan_tich" in (st.get(s).get("co") or "")]
            L.append(f"| Câu nghi_don_phan_tich còn lỗi K3 (chưa tách) | {pr['k3']} / {len(don)} câu có cờ – tiêu chí 0 |")

    for gd, folder in (("1", "vi"), ("2", "ko")):
        loai, muc = collections.Counter(), collections.Counter()
        for s in ids:
            p = D.OUT("reports", "claude_sua", folder, s + ".json")
            if os.path.exists(p):
                for x in load_json(p)["sua"]:
                    loai[x.get("loai") or "(không ghi)"] += 1
                    muc[x.get("muc_do") or "(không ghi)"] += 1
        L += ["", f"## Claude đã sửa – giai đoạn {gd}", ""]
        if not loai:
            L.append("Chưa có.")
            continue
        L += ["| Loại | Số chỗ |", "|---|---|"] + [f"| {k} | {v} |" for k, v in loai.most_common()]
        L += ["", "| Mức độ | Số chỗ |", "|---|---|"] + [f"| {k} | {v} |" for k, v in muc.most_common()]
        L.append(f"\nLỗi nghiêm trọng GPT tạo ra (Claude phải sửa): **{muc.get('nghiem_trong', 0)}** – tiêu chí 0 trước khi chạy toàn bộ.")

    L += ["", "## Token GPT", "", "| Giai đoạn | Số câu | Token vào | Token ra | TB vào/câu | TB ra/câu |", "|---|---|---|---|---|---|"]
    for gd, f in (("1", "usage_gd1.jsonl"), ("2", "usage_gd2.jsonl")):
        tot, n = usage(D.OUT("reports", f), ids)
        L.append(f"| {gd} | {n} | {tot['vao']} | {tot['ra']} | {tot['vao'] // n if n else 0} | {tot['ra'] // n if n else 0} |")
    L += ["", "Chi phí = token × đơn giá của model trên gateway (điền đơn giá khi đã chọn model).",
          "", "## Kết quả CTV", "", "Chưa có – bổ sung khi nhận file CTV trả về."]
    out = D.OUT("reports", "bao_cao_tong_hop.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"\n→ {out}")


if __name__ == "__main__":
    main()
