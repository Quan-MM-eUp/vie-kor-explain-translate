"""[Dạng 17] Giai đoạn 2 – Bước 2.1–2.3 do tác tử TẠO Claude dịch (không GPT). Logic chung: pipeline_chung/claude_tao.py.

  python3 scripts/s2_claude_dich.py --chuan-bi --tu 1 --den 10  → map, request, _he_thong.md, tao_gd2_danh_sach.json
  (tác tử tạo theo prompts/s2_claude_dich.md ghi output/claude/tao_gd2/<id>.output.json = {"fN": "…"} – TRỪ các mã sao chép)
  python3 scripts/s2_claude_dich.py --nhan --tu 1 --den 10      → Python chép bản Hàn cho key_info trùng dòng thoại (mã sao chép),
                                                                  ghép → output/json_ko/claude_tao/<id>.json; lỗi → LỖI_GĐ2
Bước tiếp theo: s2_claude_goi.py → soát → s2_kiem_tra.py
"""
import os

import _dang as D
from pipeline_chung import claude_tao as CT
from pipeline_chung.common import load_json, save_json
from pipeline_chung.trang_thai import Status
from _dich_17 import danh_dau, prefill_17, sao_chep_ids, tagged_copy_17
from _dau_vao import load_tm, terms_text, user_message_gd2 as user_message

HOOK = CT.HookGD2(user_message=user_message, load_tm=load_tm, terms_text=terms_text,
                  danh_dau=danh_dau, prefill=prefill_17, tagged=tagged_copy_17)


def sau_chuan_bi(tasks):
    """Ghi bảng mã sao chép vào từng request + danh sách (số mã cần dịch thật)."""
    for t in tasks:
        req_p = os.path.join(D.DANG, t["file_vao"])
        req = load_json(req_p)
        fmap = load_json(D.OUT(*CT.GD2_DIR, t["sample_id"] + ".map.json"))
        sc = {k: v for k, v in sao_chep_ids(fmap).items() if k in req["ids"]}
        req["sao_chep"] = sc
        save_json(req, req_p)
        t["so_ma"] = len([i for i in req["ids"] if i not in sc])
        t["so_ma_sao_chep"] = len(sc)
    p = D.OUT("claude", "tao_gd2_danh_sach.json")
    ds = load_json(p)
    ds["cau"] = tasks
    ds["ghi_chu"] = "file_ra gồm ĐÚNG các mã trong ids TRỪ các mã trong request.sao_chep (Python tự chép khi --nhan)."
    save_json(ds, p)


def truoc_nhan(ids):
    """Điền các mã sao chép (key_info trùng dòng thoại) = bản Hàn của dòng thoại, bỏ (i)."""
    for sid in ids:
        req_p, out_p = D.OUT("claude", "tao_gd2", sid + ".request.json"), D.OUT("claude", "tao_gd2", sid + ".output.json")
        if not (os.path.exists(req_p) and os.path.exists(out_p)):
            continue
        req = load_json(req_p)
        try:
            out = load_json(out_p)
        except Exception:          # noqa: BLE001 – để gd2_nhan báo lỗi JSON
            continue
        sc = req.get("sao_chep") or {}
        if not sc:
            continue
        for k, src in sc.items():
            if isinstance(out.get(src), str):
                out[k] = D.bo_i(out[src])
        save_json(out, out_p)


if __name__ == "__main__":
    args, cfg = CT._args(), D.cfg()
    st = Status(D.status_path())
    if args.chuan_bi:
        sau_chuan_bi(CT.gd2_chuan_bi(D, HOOK, args, cfg, st))
    else:
        truoc_nhan(CT._chon(D, HOOK, args, cfg, st))
        CT.gd2_nhan(D, HOOK, args, cfg, st)
