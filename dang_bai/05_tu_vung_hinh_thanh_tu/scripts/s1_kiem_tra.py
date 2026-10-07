"""[Cách chia v2 + quy tắc v3 – nâng cấp 2026-10-05 theo dạng 01/pipeline_v3] Giai đoạn 1 – Bước 1.3 + 1.4: Python kiểm tra lần cuối JSON tiếng Việt (đã qua Claude) và gắn trạng thái.

- Kiểm tra chung (pipeline_chung.checks_chung.check_vi) + kiểm tra riêng K1–K10 (_dang.check_k)
- Nhật ký "Claude đã sửa": Python so bản GPT với bản Claude, ghép lý do Claude ghi → output/reports/claude_sua/vi/<id>.json
- Chỗ Claude sửa lỗi bản gốc (loai=sua_ban_goc, WF chung 2a-1): kiểm tra trung thành trên bản đã hoàn tác chỗ đó,
  cảnh báo nếu sửa quá nhiều / thiếu nhom / thiếu ghi chú [Đã sửa bản gốc]
- Cảnh báo nếu Claude có dấu hiệu thêm nội dung (tỷ lệ từ thừa tăng so với bản GPT)
- Chạy thêm kiểm tra trên bản GPT (chỉ để đo: GPT sai bao nhiêu, Claude sửa được bao nhiêu, có làm phát sinh lỗi không)
- Trạng thái: có LỖI → LỖI_GĐ1 (dừng); không → GĐ1_XONG (chờ bạn duyệt bằng s1_chot.py)
- Cách chia v2 (config cach_chia_dang = "v2"): Claude chỉ sửa định dạng (loai sua_dinh_dang + ghi chú [Đã sửa định dạng]);
  cờ nghi sai nội dung (ly_do.nghi_noi_dung) → CHỜ_DUYỆT_NỘI_DUNG; có âm Hán Việt trong lời giải → CHỜ_XỬ_LÝ_HÁN_VIỆT.
  Hai trạng thái này không được chốt/dịch.

Cách chạy:  python scripts/s1_kiem_tra.py --pilot   (hoặc --ids / --lo / --tat-ca)
Kết quả:    output/reports/validate_vi.json, trang_thai.csv
"""
import argparse
import collections
import os

import _dang as D
from pipeline_chung.checks_chung import check_vi
from pipeline_chung.claude_log import (build_log, content_flags, format_fix_warnings, gpt_fixes, merge_checks,
                                        revert_src_fixes, src_fix_warnings, src_fixes, summary_lines)
from pipeline_chung.common import load_json, save_json
from pipeline_chung.trang_thai import Status


def run_checks(doc, norm, cfg, schema):
    r = check_vi(doc, schema, norm["src_text"], norm["src_vi_text"], norm, cfg["kiem_tra"], D.strip_labels,
                 marks_src=norm["marks_src"], furi_src_text=norm["src_text_furi"], furi_skip=D.FURI_SKIP)
    k_loi, k_cb = D.check_k(doc, norm, cfg["chinh_sach"])
    r["loi"] += k_loi
    r["canh_bao"] += k_cb
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--ids")
    ap.add_argument("--lo", type=int)
    ap.add_argument("--tat-ca", action="store_true")
    args = ap.parse_args()
    cfg = D.cfg()
    st = Status(D.status_path())
    schema = load_json(D.P(cfg["schema"]))
    v2 = cfg.get("cach_chia_dang") == "v2"
    ids = D.select_ids(args, st, ("ĐANG_XỬ_LÝ", "CẦN_SỬA_GĐ1", "LỖI_GĐ1", "GĐ1_XONG", "CHỜ_DUYỆT_NỘI_DUNG", "CHỜ_XỬ_LÝ_HÁN_VIỆT"))
    results, count, not_ready = [], collections.Counter(), []
    gpt_fail = final_fail = fixed_by_claude = broke_by_claude = 0
    for sid in ids:
        gpt_p, chk_p = D.OUT("json_vi", "gpt", sid + ".json"), D.OUT("json_vi", "checked", sid + ".json")
        why_p = D.OUT("json_vi", "checked", sid + ".ly_do.json")
        if not os.path.exists(chk_p) or not os.path.exists(why_p):
            not_ready.append(sid)
            continue
        norm, gpt_doc, doc, why = D.load_norm(sid), load_json(gpt_p), load_json(chk_p), __import__('pipeline_chung.claude_log', fromlist=['x']).chuan_hoa_duong_dan(load_json(why_p))
        if "_huong_dan" in why:
            not_ready.append(sid)          # Claude chưa kiểm tra xong câu này
            continue
        log, warn = build_log(sid, 1, gpt_doc, doc, why)
        r = run_checks(doc, norm, cfg, schema)
        if src_fixes(log):
            # WF chung mục 2a-1: chỗ Claude sửa lỗi bản gốc không tính là "không trung thành" –
            # kiểm tra trung thành trên bản đã trả các chỗ đó về giá trị GPT, còn cấu trúc/K… trên bản cuối
            r = merge_checks(r, run_checks(revert_src_fixes(gpt_doc, doc, log, why), norm, cfg, schema))
            if not v2:
                warn += src_fix_warnings(log, why.get("ghi_chu_ban_goc", []))
        elif why.get("ghi_chu_ban_goc") and not v2:
            warn += src_fix_warnings(log, why.get("ghi_chu_ban_goc", []))
        nd_lines, hv = [], []
        if v2:
            # Cách chia v2: chỉ sửa định dạng (có ghi chú từng chỗ); nội dung → cờ, chặn dịch; âm Hán Việt → cờ, chặn dịch
            warn += format_fix_warnings(log, why.get("ghi_chu_ban_goc", []))
            nd_lines, bad = content_flags(why)
            warn += bad
            hv = D.han_viet_src(norm)
        r_gpt = run_checks(gpt_doc, norm, cfg, schema)
        r["canh_bao"] += warn
        ex_c, ex_g = r["so_lieu"].get("tu_thua_vi"), r_gpt["so_lieu"].get("tu_thua_vi")
        if ex_c is not None and ex_g is not None and ex_c - ex_g > cfg["kiem_tra"]["claude_them_noi_dung_tang_toi_da"] + 1e-9:
            new = [w for w in r["so_lieu"]["tu_moi"] if w not in r_gpt["so_lieu"]["tu_moi"]]
            r["canh_bao"].append(f"Claude có thể đã thêm nội dung (từ thừa {ex_g:.1%} → {ex_c:.1%}; từ mới: {new[:10]})")
        save_json(log, D.OUT("reports", "claude_sua", "vi", sid + ".json"))
        gpt_fail += bool(r_gpt["loi"]); final_fail += bool(r["loi"])
        fixed_by_claude += bool(r_gpt["loi"] and not r["loi"]); broke_by_claude += bool(r["loi"] and not r_gpt["loi"])
        state = ("LỖI_GĐ1" if r["loi"] else "CHỜ_DUYỆT_NỘI_DUNG" if nd_lines
                 else "CHỜ_XỬ_LÝ_HÁN_VIỆT" if hv else "GĐ1_XONG")
        count[state] += 1
        notes = norm["ghi_chu_ban_goc"] + [x for x in why.get("ghi_chu_ban_goc", []) if x not in norm["ghi_chu_ban_goc"]]
        st.update(sid, trang_thai=state, giai_doan_loi="1" if r["loi"] else "", loi=r["loi"], canh_bao=r["canh_bao"],
                  so_cho_claude_sua_vi=log["so_cho_sua"], claude_da_sua_vi=summary_lines(log), ghi_chu_ban_goc=notes,
                  so_cho_sua_loi_gpt=len(gpt_fixes(log)), so_cho_sua_ban_goc=len(src_fixes(log)),
                  so_cho_sua_dinh_dang=sum(1 for x in log["sua"] if x.get("loai") == "sua_dinh_dang"),
                  co_nghi_noi_dung="x" if nd_lines else "", nghi_noi_dung=nd_lines,
                  co_han_viet="x" if hv else "", han_viet=[f"[Âm Hán Việt] {x}" for x in hv])
        results.append({"sample_id": sid, "trang_thai": state, "loi": r["loi"], "canh_bao": r["canh_bao"],
                        "so_lieu": r["so_lieu"], "ban_gpt": {"loi": r_gpt["loi"], "canh_bao": r_gpt["canh_bao"]},
                        "claude_khong_kiem_tra": bool(why.get("khong_kiem_tra"))})
        print(f"{state:9} {sid}" + "".join(f"\n   ✗ {x}" for x in r["loi"]) + "".join(f"\n   ! {x}" for x in r["canh_bao"])
              + "".join(f"\n   ? {x}" for x in nd_lines) + "".join(f"\n   ~ [Âm Hán Việt] {x}" for x in hv))
    st.save()
    save_json({"results": results}, D.OUT("reports", "validate_vi.json"))
    n = len(results)
    print(f"\nTổng {n} câu: {dict(count)}")
    if n:
        print(f"Đo chất lượng: bản GPT có LỖI {gpt_fail}/{n} câu → sau Claude còn {final_fail}/{n}"
              f" (Claude sửa hết lỗi ở {fixed_by_claude} câu, làm phát sinh lỗi ở {broke_by_claude} câu)")
    if not_ready:
        print(f"Chưa kiểm tra được {len(not_ready)} câu (Claude chưa làm xong / chưa có file): {not_ready[:10]}")
    if v2 and (count["CHỜ_DUYỆT_NỘI_DUNG"] or count["CHỜ_XỬ_LÝ_HÁN_VIỆT"]):
        print(f"Không dịch: {count['CHỜ_DUYỆT_NỘI_DUNG']} câu nghi sai nội dung (?) → CTV tiếng Nhật (s3b_xuat_ctv_nhat.py), "
              f"{count['CHỜ_XỬ_LÝ_HÁN_VIỆT']} câu có âm Hán Việt (~) – xem output/reports/can_kiem_tra.csv")
    print("Bước tiếp theo: bạn duyệt rồi chạy python scripts/s1_chot.py … (chỉ chốt các câu GĐ1_XONG)")


if __name__ == "__main__":
    main()
