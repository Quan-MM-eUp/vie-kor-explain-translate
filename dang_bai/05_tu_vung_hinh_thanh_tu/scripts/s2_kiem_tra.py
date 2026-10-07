"""[PIPELINE v3] Giai đoạn 2 – Bước 2.5 + 2.6: Python kiểm tra lần cuối bản dịch (đã qua Claude) và gắn trạng thái.

- Kiểm tra chung (check_ko) + riêng D1–D2; D3 (số { }) nằm trong kiểm tra chung
- v3: trường dịch từ tiếng Nhật bỏ các phép so với bản Việt (⟪ ⟫, furigana, tỷ lệ độ dài, câu cố định);
  thêm D6 (cảnh báo: nghĩa từ mất phủ định / bị động) và D7 (lỗi: số { } của Nghĩa câu khác câu tiếng Nhật);
  không đưa trường dịch từ tiếng Nhật vào bộ nhớ dịch; D4 so Nghĩa câu theo câu tiếng Nhật
- Nhật ký "Claude đã sửa" giai đoạn 2 → output/reports/claude_sua/ko/<id>.json
- Cảnh báo nếu bản Claude dài hơn bản GPT quá ngưỡng (có thể đã thêm nội dung)
- Claude ghi [Lỗi JSON VI] → trạng thái CẦN_SỬA_GĐ1 (quay lại giai đoạn 1)
- Trạng thái: LỖI → LỖI_GĐ2; không lỗi → ĐẠT, chép sang output/json_ko/final/, cập nhật bộ nhớ dịch
- D4: báo cáo không nhất quán giữa các câu (cùng vi, khác ko) → output/reports/khong_nhat_quan.csv

Cách chạy:  python scripts/s2_kiem_tra.py --pilot
"""
import argparse
import collections
import glob
import os
import shutil

import _dang as D
from pipeline_chung.checks_chung import check_ko
from pipeline_chung.claude_log import build_log, summary_lines
from pipeline_chung.common import iter_lang_fields, load_json, path_str, save_json, strip_marks, write_csv
from pipeline_chung.dich import key_norm
from pipeline_chung.trang_thai import Status
from _dich_v3 import d4_key, kiem_tra_v3, loc_kiem_tra


def run(doc, vi, schema, cfg, g, lang, fmap):
    r = check_ko(doc, vi, schema, lang, cfg["kiem_tra"], D.is_style_field)
    l2, c2 = D.check_d(doc, g, lang)
    r["loi"] = loc_kiem_tra(r["loi"] + l2, fmap)
    r["canh_bao"] = loc_kiem_tra(r["canh_bao"] + c2, fmap)
    l3, c3 = kiem_tra_v3(doc, lang)
    r["loi"] += l3
    r["canh_bao"] += c3
    return r


def load_fmap(sid):
    p = D.OUT("json_ko", "gpt", sid + ".map.json")
    return load_json(p) if os.path.exists(p) else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--ids")
    ap.add_argument("--lo", type=int)
    ap.add_argument("--tat-ca", action="store_true")
    args = ap.parse_args()
    cfg, lang = D.cfg(), D.cfg()["ngon_ngu_dich"]
    st = Status(D.status_path())
    schema = load_json(D.P(cfg["schema"]))
    g = D.glossary()
    tm_path = D.OUT(cfg["bo_nho_dich"]["file"])
    tm = load_json(tm_path) if os.path.exists(tm_path) else {}
    fixed = {key_norm(k) for k in g["cau_co_dinh"]}
    count, results, not_ready = collections.Counter(), [], []
    gpt_fail = final_fail = 0
    for sid in D.select_ids(args, st, ("GĐ1_XONG", "LỖI_GĐ2", "ĐẠT")):
        chk_p, why_p, gpt_p = (D.OUT("json_ko", "checked", sid + ".json"), D.OUT("json_ko", "checked", sid + ".ly_do.json"),
                               D.OUT("json_ko", "gpt", sid + ".json"))
        if not all(os.path.exists(x) for x in (chk_p, why_p, gpt_p)):
            not_ready.append(sid)
            continue
        why = __import__('pipeline_chung.claude_log', fromlist=['x']).chuan_hoa_duong_dan(load_json(why_p))
        if "_huong_dan" in why:
            not_ready.append(sid)
            continue
        vi = load_json(D.OUT("json_vi", "final", sid + ".json"))
        doc, gpt_doc = load_json(chk_p), load_json(gpt_p)
        fmap = load_fmap(sid)
        ja_p = {f["path"] for f in fmap if f.get("nguon_dich") in ("ja", "vi_vd", "ket_hop")}   # không đưa vào bộ nhớ dịch (ket_hop: cùng bản Việt nhưng khác từ tiếng Nhật)
        r, r_gpt = run(doc, vi, schema, cfg, g, lang, fmap), run(gpt_doc, vi, schema, cfg, g, lang, fmap)
        log, warn = build_log(sid, 2, gpt_doc, doc, why)
        r["canh_bao"] += warn
        gko = {path_str(p): o.get(lang, "") for p, o in iter_lang_fields(gpt_doc)}
        for p, o in iter_lang_fields(doc):
            a, b = len(strip_marks(gko.get(path_str(p), ""))), len(strip_marks(o.get(lang, "")))
            if a and (b - a) / a > cfg["kiem_tra"]["claude_ko_dai_hon_gpt_toi_da"]:
                r["canh_bao"].append(f"{path_str(p)}: bản Claude dài hơn bản GPT {(b - a) / a:.0%} – xem lại có thêm nội dung không")
        save_json(log, D.OUT("reports", "claude_sua", "ko", sid + ".json"))
        gpt_fail += bool(r_gpt["loi"]); final_fail += bool(r["loi"])
        if why.get("loi_json_vi"):
            state = "CẦN_SỬA_GĐ1"
            r["loi"] += why["loi_json_vi"]
        else:
            state = "LỖI_GĐ2" if r["loi"] else "ĐẠT"
        count[state] += 1
        old = st.get(sid)
        notes = [x for x in (old.get("ghi_chu_ban_goc") or "").split("\n") if x]
        notes += [x for x in why.get("ghi_chu_ban_goc", []) + why.get("ghi_chu_khi_dich", []) if x not in notes]
        cb_all = [x for x in (old.get("canh_bao") or "").split("\n") if x and not x.startswith("[GĐ2]")] + [f"[GĐ2] {x}" for x in r["canh_bao"]]
        st.update(sid, trang_thai=state, giai_doan_loi={"ĐẠT": "", "LỖI_GĐ2": "2", "CẦN_SỬA_GĐ1": "1"}[state],
                  loi=r["loi"], canh_bao=cb_all, so_cho_claude_sua_ko=log["so_cho_sua"],
                  claude_da_sua_ko=summary_lines(log), ghi_chu_ban_goc=notes)
        if state == "CẦN_SỬA_GĐ1":
            st.update(sid, duyet_vi="")
        if state == "ĐẠT":
            os.makedirs(D.OUT("json_ko", "final"), exist_ok=True)
            shutil.copyfile(chk_p, D.OUT("json_ko", "final", sid + ".json"))
            for p, o in iter_lang_fields(doc):
                k = key_norm(o["vi"])
                if path_str(p) in ja_p:          # v3: trường dịch từ tiếng Nhật không vào bộ nhớ dịch (khóa theo tiếng Việt)
                    continue
                if k not in fixed:
                    tm[k] = {"ko": o[lang], "nguon": sid}
        results.append({"sample_id": sid, "trang_thai": state, "loi": r["loi"], "canh_bao": r["canh_bao"],
                        "ban_gpt": {"loi": r_gpt["loi"], "canh_bao": r_gpt["canh_bao"]}})
        print(f"{state:11} {sid}" + "".join(f"\n   ✗ {x}" for x in r["loi"]) + "".join(f"\n   ! {x}" for x in r["canh_bao"]))
    st.save()
    if cfg["bo_nho_dich"].get("dung"):
        save_json(tm, tm_path)
    save_json({"results": results}, D.OUT("reports", "check_ko.json"))

    # D4 – nhất quán giữa các câu
    seen = collections.defaultdict(lambda: collections.defaultdict(list))
    for f in glob.glob(D.OUT("json_ko", "final", "*.json")):
        sid = os.path.basename(f)[:-5]
        d = load_json(f)
        by_path = {x["path"]: x for x in load_fmap(sid)}
        for p, o in iter_lang_fields(d):
            fx = by_path.get(path_str(p)) or {"path": path_str(p)}
            if fx.get("nguon_dich") == "ja":
                k = d4_key(fx, d)
                if k:
                    seen[k][strip_marks(o.get(lang, ""))].append(f"{sid}:{path_str(p)}")
                continue
            seen[key_norm(o["vi"])][o.get(lang, "")].append(f"{sid}:{path_str(p)}")
    rows = [{"vi": vi, "so_cach_dich": len(v), "cac_ban_dich": "\n".join(f"{ko} ← {', '.join(locs[:5])}" for ko, locs in v.items())}
            for vi, v in seen.items() if len(v) > 1]
    write_csv(rows, D.OUT("reports", "khong_nhat_quan.csv"), ["vi", "so_cach_dich", "cac_ban_dich"])

    n = len(results)
    print(f"\nTổng {n} câu: {dict(count)}")
    if n:
        print(f"Đo chất lượng: bản GPT có LỖI {gpt_fail}/{n} → sau Claude còn {final_fail}/{n}")
    print(f"D4: {len(rows)} câu tiếng Việt có nhiều cách dịch khác nhau → output/reports/khong_nhat_quan.csv")
    if not_ready:
        print(f"Chưa kiểm tra được {len(not_ready)} câu: {not_ready[:10]}")
    print("Bước tiếp theo: python scripts/s3_xuat_ctv.py …")


if __name__ == "__main__":
    main()
