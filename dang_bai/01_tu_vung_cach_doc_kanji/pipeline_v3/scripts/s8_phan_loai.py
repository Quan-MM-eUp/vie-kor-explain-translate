"""[Cách chia v2 – config cach_chia_dang = "v2": xem main_v2 ở cuối file]
Phân loại kết quả thành 3 dạng (chạy sau giai đoạn 2, không gọi API, không sửa dữ liệu). Định nghĩa 2026-09-29:

  dang_gd1 (xét giai đoạn 1):
    1 – Claude KHÔNG sửa lỗi có sẵn trong bản gốc (có thể GPT đổi chữ, Claude sửa lỗi của GPT, có ghi chú
        [Bản gốc VI] chưa sửa – các thông tin này vẫn ghi trong phan_loai.csv và cột "Điểm cần chú ý" của Excel CTV).
    2 – Claude CÓ sửa lỗi có sẵn trong bản gốc (loai sua_ban_goc, ghi chú [Đã sửa bản gốc] – WF chung 2a-1).
  dang (kết quả cuối):
    3 – câu (dù dang_gd1 là 1 hay 2) gặp vấn đề dịch âm Hán Việt ở giai đoạn 2 (lỗi D5).
    còn lại dang = dang_gd1 (câu ĐẠT).
  Câu lỗi khác (LỖI_GĐ2 không phải D5, LỖI_GĐ1, CẦN_SỬA_GĐ1, LỖI_KỸ_THUẬT) → "chưa phân loại – lỗi pipeline"
  (chua_phan_loai.csv; xử lý theo can_kiem_tra.csv rồi chạy lại). Câu chưa chạy xong (ĐANG_XỬ_LÝ, GĐ1_XONG) bỏ qua.
  Khi âm Hán Việt đã xử lý và dịch lại, câu Dạng 3 tự về đúng dang_gd1.

Cách chạy:  python scripts/s8_phan_loai.py --tu 1 --den 40      (hoặc --ids / --pilot / --tat-ca)
Kết quả:    output/reports/phan_loai/phan_loai.csv (câu đã phân loại), dang_1.csv, dang_2.csv, dang_3.csv,
            chua_phan_loai.csv, chi_tiet/<id>.json (Dạng 2, 3: so chữ đầy đủ + nhật ký Claude), tong_hop.md
"""
import argparse
import collections
import os

import _dang as D
from pipeline_chung.claude_log import NOTE_FIX
from pipeline_chung.common import load_json, save_json, write_csv
from pipeline_chung.so_chu import so_chu, tom_tat
from pipeline_chung.trang_thai import Status

LOI = ("LỖI_GĐ2", "LỖI_GĐ1", "CẦN_SỬA_GĐ1", "LỖI_KỸ_THUẬT")
HAN_VIET = "D5:"          # mã lỗi âm Hán Việt ở giai đoạn 2 (_dang.check_han_viet)
FIELDS = ["sample_id", "question_id", "cap_do", "dang", "dang_gd1", "ly_do_phan_loai", "trang_thai",
          "van_de_ban_goc", "so_cho_gpt_doi", "gpt_da_doi", "so_cho_claude_sua_vi",
          "so_cho_claude_sua_loi_gpt", "claude_sua_loi_gpt", "so_cho_claude_sua_ban_goc", "claude_sua_ban_goc", "da_sua_ban_goc",
          "so_cho_claude_sua_ko", "claude_da_sua_ko", "loi", "ghi_chu_khi_dich"]


def lines(s, prefix=None):
    out = [x for x in (s or "").split("\n") if x.strip()]
    return [x for x in out if x.startswith(prefix)] if prefix else out


def claude_log(folder, sid):
    p = D.OUT("reports", "claude_sua", folder, sid + ".json")
    return load_json(p) if os.path.exists(p) else {"sua": []}


def fmt_sua(items):
    items = items["sua"] if isinstance(items, dict) else items
    return "\n".join(f"{x['duong_dan']} [{x.get('loai') or '?'}{'/' + x['nhom'] if x.get('nhom') else ''}]: "
                     f"{str(x['truoc'])[:80]!r} → {str(x['sau'])[:80]!r}"
                     + (f" – {x['ly_do']}" if x.get("ly_do") else "") for x in items)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--ids")
    ap.add_argument("--lo", type=int)
    ap.add_argument("--tat-ca", action="store_true")
    args = ap.parse_args()
    if D.cfg().get("cach_chia_dang") == "v2":
        return main_v2(args)
    st = Status(D.status_path())
    rows, chua_xong = [], 0
    for sid in D.select_ids(args, st, tuple()):
        r = st.get(sid)
        state = r.get("trang_thai")
        if state not in LOI and state != "ĐẠT":
            chua_xong += 1
            continue
        norm = D.load_norm(sid)
        gpt_p = D.OUT("json_vi", "gpt", sid + ".json")
        sc = so_chu(D.vi_segments_src(norm), D.vi_segments_doc(load_json(gpt_p))) if os.path.exists(gpt_p) else {"so_cho_doi": 0, "doi": []}
        lv, lk = claude_log("vi", sid), claude_log("ko", sid)
        ban_goc = lines(r.get("ghi_chu_ban_goc"), "[Bản gốc VI]")
        da_sua = lines(r.get("ghi_chu_ban_goc"), NOTE_FIX)
        fix_src = [x for x in lv["sua"] if x.get("loai") == "sua_ban_goc"]
        fix_gpt = [x for x in lv["sua"] if x.get("loai") != "sua_ban_goc"]
        loi = lines(r.get("loi"))
        dang_gd1 = 2 if fix_src else 1
        why_gd1 = (f"GĐ1: Claude sửa lỗi bản gốc {len(fix_src)} chỗ" if fix_src else "GĐ1: Claude không sửa lỗi bản gốc") + "".join(
            f"; {x}" for x in (f"{len(ban_goc)} vấn đề bản gốc chưa sửa" if ban_goc else "",
                               f"GPT đổi {sc['so_cho_doi']} chỗ" if sc["so_cho_doi"] else "",
                               f"Claude sửa lỗi GPT {len(fix_gpt)} chỗ" if fix_gpt else "") if x)
        if state == "ĐẠT":
            dang, why = dang_gd1, why_gd1 + (f"; GĐ2: Claude sửa bản dịch {len(lk['sua'])} chỗ" if lk["sua"] else "")
        elif state == "LỖI_GĐ2" and any(x.startswith(HAN_VIET) for x in loi):
            hv_paths = {x.split(":")[1].strip() for x in loi if x.startswith(HAN_VIET)}
            # lỗi khác ở cùng trường có âm Hán Việt (vd "còn chữ tiếng Việt") là hệ quả của Hán Việt, không tính riêng
            khac = [x for x in loi if not x.startswith(HAN_VIET) and x.split(":")[0].strip() not in hv_paths]
            dang = 3
            why = f"GĐ2: còn âm Hán Việt ({sum(1 for x in loi if x.startswith(HAN_VIET))} chỗ)" + (f" + {len(khac)} lỗi khác" if khac else "") + f" · {why_gd1}"
        else:
            dang, why = "", f"Chưa phân loại – lỗi pipeline ({state})"
        row = {"sample_id": sid, "question_id": r.get("question_id"), "cap_do": r.get("cap_do"), "dang": dang, "dang_gd1": dang_gd1,
               "ly_do_phan_loai": why, "trang_thai": state, "van_de_ban_goc": "\n".join(ban_goc),
               "so_cho_gpt_doi": sc["so_cho_doi"], "gpt_da_doi": tom_tat(sc) if sc["so_cho_doi"] else "",
               "so_cho_claude_sua_vi": len(lv["sua"]), "claude_da_sua_vi": fmt_sua(lv),
               "so_cho_claude_sua_loi_gpt": len(fix_gpt), "claude_sua_loi_gpt": fmt_sua(fix_gpt),
               "so_cho_claude_sua_ban_goc": len(fix_src), "claude_sua_ban_goc": fmt_sua(fix_src), "da_sua_ban_goc": "\n".join(da_sua),
               "so_cho_claude_sua_ko": len(lk["sua"]), "claude_da_sua_ko": fmt_sua(lk),
               "loi": r.get("loi") if dang != 1 and dang != 2 else "", "ghi_chu_khi_dich": "\n".join(lines(r.get("ghi_chu_ban_goc"), "[Khi dịch]"))}
        rows.append(row)
        if dang in (2, 3):
            save_json({"sample_id": sid, "dang": dang, "dang_gd1": dang_gd1, "ly_do_phan_loai": why, "trang_thai": state,
                       "van_de_ban_goc": ban_goc, "gpt_so_chu": sc, "claude_sua_vi": lv["sua"], "claude_sua_ko": lk["sua"],
                       "claude_sua_loi_gpt": fix_gpt, "claude_sua_ban_goc": fix_src, "da_sua_ban_goc": da_sua,
                       "loi": lines(r.get("loi")), "canh_bao": lines(r.get("canh_bao"))},
                      D.OUT("reports", "phan_loai", "chi_tiet", sid + ".json"))
    out = D.OUT("reports", "phan_loai")
    chua = [x for x in rows if x["dang"] == ""]
    rows = [x for x in rows if x["dang"] != ""]
    write_csv(rows, os.path.join(out, "phan_loai.csv"), FIELDS)
    for k in (1, 2, 3):
        write_csv([x for x in rows if x["dang"] == k], os.path.join(out, f"dang_{k}.csv"), FIELDS)
    write_csv(chua, os.path.join(out, "chua_phan_loai.csv"), FIELDS)
    c = collections.Counter(x["dang"] for x in rows)
    n = len(rows)
    md = [f"# Phân loại kết quả – {n} câu" + (f" ({chua_xong} câu trong phạm vi chưa chạy xong, không tính)" if chua_xong else ""), "",
          "| Dạng | Ý nghĩa | Số câu | Tỷ lệ |", "|---|---|---|---|"]
    for k, t in ((1, "GĐ1: Claude không cần sửa lỗi bản gốc; kết quả cuối ĐẠT"),
                 (2, "GĐ1: Claude đã sửa lỗi bản gốc ([Đã sửa bản gốc]); kết quả cuối ĐẠT"),
                 (3, "GĐ2: còn vấn đề dịch âm Hán Việt (lỗi D5) – câu có thể thuộc Dạng 1 hoặc 2 ở GĐ1")):
        md.append(f"| {k} | {t} | {c[k]} | {c[k] / n:.0%} |" if n else f"| {k} | {t} | 0 | – |")
    d1 = [x for x in rows if x["dang"] == 1]
    d3 = [x for x in rows if x["dang"] == 3]
    md += ["", "**Dạng 1 – thông tin thêm (không đổi dạng, vẫn hiện ở cột \"Điểm cần chú ý\" cho CTV):**", "",
           f"- Có vấn đề bản gốc chưa sửa ([Bản gốc VI]): {sum(1 for x in d1 if x['van_de_ban_goc'])} câu",
           f"- GPT đổi chữ so với bản gốc: {sum(1 for x in d1 if x['so_cho_gpt_doi'])} câu",
           f"- Claude sửa lỗi của GPT: {sum(1 for x in d1 if x['so_cho_claude_sua_loi_gpt'])} câu",
           "", f"**Dạng 3:** {', '.join(x['sample_id'] + ' (GĐ1: dạng ' + str(x['dang_gd1']) + ')' for x in d3) or 'không có'}",
           "", f"**Chưa phân loại – lỗi pipeline:** {', '.join(x['sample_id'] + ' (' + x['trang_thai'] + ')' for x in chua) or 'không có'}"
           + (" → xử lý theo can_kiem_tra.csv rồi chạy lại" if chua else "")]
    with open(os.path.join(out, "tong_hop.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("\n".join(md))
    print(f"\n→ {out}: phan_loai.csv, dang_1.csv, dang_2.csv, dang_3.csv, chua_phan_loai.csv, chi_tiet/, tong_hop.md")


# ======================= Cách chia v2 (config cach_chia_dang = "v2", output_v2) =======================
#   Dạng 1 – không sai định dạng (Claude không phải sửa định dạng ở GĐ1)
#   Dạng 2 – có sai định dạng, Claude đã sửa (loai sua_dinh_dang, ghi chú [Đã sửa định dạng] từng chỗ)
#   Hai cờ độc lập với dạng: co_nghi_noi_dung (Claude nghi sai nội dung, ghi rõ phần nào) và co_han_viet
#   (lời giải gốc có âm Hán Việt). Chỉ câu không có cờ nào mới được dịch sang tiếng Hàn.
V2_FIELDS = ["sample_id", "question_id", "cap_do", "dang", "trang_thai", "duoc_dich",
             "so_cho_sua_dinh_dang", "da_sua_dinh_dang", "da_sua_theo_ctv", "co_nghi_noi_dung", "nghi_noi_dung", "co_han_viet", "han_viet",
             "so_cho_claude_sua_loi_gpt", "claude_sua_loi_gpt", "so_cho_claude_sua_ko", "claude_da_sua_ko", "loi"]
V2_CHUA_XONG = ("ĐANG_XỬ_LÝ", "LỖI_KỸ_THUẬT", "LỖI_GĐ1", "CẦN_SỬA_GĐ1", "")


def main_v2(args):
    from pipeline_chung.claude_log import NOTE_CTV, NOTE_DD
    st = Status(D.status_path())
    rows, chua_xong, da_duyet = [], 0, 0
    for sid in D.select_ids(args, st, tuple()):
        r = st.get(sid)
        state = r.get("trang_thai", "")
        if state == "ĐÃ_DUYỆT_CTV":
            da_duyet += 1
            continue
        if state in V2_CHUA_XONG:
            chua_xong += 1
            continue
        lv, lk = claude_log("vi", sid), claude_log("ko", sid)
        dd = [x for x in lv["sua"] if x.get("loai") == "sua_dinh_dang"]
        gpt = [x for x in lv["sua"] if x.get("loai") not in ("sua_dinh_dang", "sua_ban_goc", "sua_theo_ctv")]
        nd, hv = lines(r.get("nghi_noi_dung")), lines(r.get("han_viet"))
        row = {"sample_id": sid, "question_id": r.get("question_id"), "cap_do": r.get("cap_do"), "dang": 2 if dd else 1,
               "trang_thai": state, "duoc_dich": "" if (nd or hv) else "x",
               "so_cho_sua_dinh_dang": len(dd), "da_sua_dinh_dang": "\n".join(lines(r.get("ghi_chu_ban_goc"), NOTE_DD)),
               "da_sua_theo_ctv": "\n".join(lines(r.get("ghi_chu_ban_goc"), NOTE_CTV)),
               "co_nghi_noi_dung": "x" if nd else "", "nghi_noi_dung": "\n".join(nd),
               "co_han_viet": "x" if hv else "", "han_viet": "\n".join(hv),
               "so_cho_claude_sua_loi_gpt": len(gpt), "claude_sua_loi_gpt": fmt_sua(gpt),
               "so_cho_claude_sua_ko": len(lk["sua"]), "claude_da_sua_ko": fmt_sua(lk),
               "loi": r.get("loi") if state == "LỖI_GĐ2" else ""}
        rows.append(row)
        save_json({"sample_id": sid, "dang": row["dang"], "trang_thai": state, "sua_dinh_dang": dd,
                   "da_sua_dinh_dang": lines(r.get("ghi_chu_ban_goc"), NOTE_DD),
                   "da_sua_theo_ctv": lines(r.get("ghi_chu_ban_goc"), NOTE_CTV), "nghi_noi_dung": nd, "han_viet": hv,
                   "claude_sua_loi_gpt": gpt, "claude_sua_ko": lk["sua"], "ghi_chu_ban_goc": lines(r.get("ghi_chu_ban_goc")),
                   "loi": lines(r.get("loi")), "canh_bao": lines(r.get("canh_bao"))},
                  D.OUT("reports", "phan_loai", "chi_tiet", sid + ".json"))
    out = D.OUT("reports", "phan_loai")
    write_csv(rows, os.path.join(out, "phan_loai.csv"), V2_FIELDS)
    for k in (1, 2):
        write_csv([x for x in rows if x["dang"] == k], os.path.join(out, f"dang_{k}.csv"), V2_FIELDS)
    write_csv([x for x in rows if x["co_nghi_noi_dung"]], os.path.join(out, "nghi_noi_dung.csv"), V2_FIELDS)
    write_csv([x for x in rows if x["co_han_viet"]], os.path.join(out, "han_viet.csv"), V2_FIELDS)
    n = len(rows)
    c = collections.Counter(x["dang"] for x in rows)
    pct = lambda k: f"{k / n:.0%}" if n else "–"  # noqa: E731
    nd = sum(1 for x in rows if x["co_nghi_noi_dung"]); hv = sum(1 for x in rows if x["co_han_viet"])
    ok = sum(1 for x in rows if x["duoc_dich"])
    md = [f"# Phân loại (cách chia v2) – {n} câu đã xong GĐ1" + (f" ({chua_xong} câu trong phạm vi chưa xong GĐ1, không tính)" if chua_xong else "")
          + (f" · {da_duyet} câu đã được CTV duyệt trước đó (kho da_duyet/, không tính)" if da_duyet else ""), "",
          "| Dạng | Ý nghĩa | Số câu | Tỷ lệ |", "|---|---|---|---|",
          f"| 1 | Không sai định dạng | {c[1]} | {pct(c[1])} |",
          f"| 2 | Có sai định dạng – Claude đã sửa (ghi chú từng chỗ) | {c[2]} | {pct(c[2])} |", "",
          "| Cờ | Số câu | Tỷ lệ |", "|---|---|---|",
          f"| Nghi sai nội dung (không dịch, gửi CTV tiếng Nhật) | {nd} | {pct(nd)} |",
          f"| Có âm Hán Việt (không dịch) | {hv} | {pct(hv)} |",
          f"| **Được dịch** (không có cờ nào) | {ok} | {pct(ok)} |", "",
          "| Dạng × cờ | Không cờ | Nghi nội dung | Hán Việt |", "|---|---|---|---|"]
    for k in (1, 2):
        g = [x for x in rows if x["dang"] == k]
        md.append(f"| {k} | {sum(1 for x in g if x['duoc_dich'])} | {sum(1 for x in g if x['co_nghi_noi_dung'])} | {sum(1 for x in g if x['co_han_viet'])} |")
    md += ["", f"Trạng thái: {dict(collections.Counter(x['trang_thai'] for x in rows))}"]
    with open(os.path.join(out, "tong_hop.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(md) + "\n")
    print("\n".join(md))
    print(f"\n→ {out}: phan_loai.csv, dang_1.csv, dang_2.csv, nghi_noi_dung.csv, han_viet.csv, chi_tiet/, tong_hop.md")


if __name__ == "__main__":
    main()
