"""[Dạng 21] Giai đoạn 1 – Bước 1.1 do tác tử TẠO Claude làm (không GPT API). Logic chung: pipeline_chung/claude_tao.py.

  python3 scripts/s1_claude_tao.py --chuan-bi --tu 1 --den 6   → output/claude/tao_gd1_danh_sach.json + <id>.input.json
        (khuôn C_ja: Python dựng JSON ngay – output/json_vi/claude_tao/<id>.json – không giao tác tử TẠO)
  (tác tử tạo theo prompts/s1_claude_tao.md ghi output/json_vi/claude_tao/<id>.json)
  python3 scripts/s1_claude_tao.py --nhan --tu 1 --den 6       → schema, định danh, Python điền correct / summary / full_translation câu con 2
Bước tiếp theo: s1_claude_goi.py → tác tử KIỂM TRA → s1_kiem_tra.py → s1_chot.py
"""
import os

import _dang as D
from pipeline_chung import claude_tao as CT
from pipeline_chung.common import save_json
from pipeline_chung.trang_thai import Status
from _dau_vao import STATES, user_message


def bo_qua(norm):
    return norm.get("khuon_goc") not in D.KHUON_TAO or "lua_chon_thieu" in norm["co"]


def dung_python(args, st):
    n = 0
    for sid in D.select_ids(args, st, STATES):
        norm = D.load_norm(sid)
        if norm.get("khuon_goc") not in D.KHUON_PYTHON or "lua_chon_thieu" in norm["co"]:
            continue
        p = CT.gd1_out(D, sid)
        if os.path.exists(p) and not args.force:
            continue
        save_json(D.dung_json_python(norm), p)
        n += 1
    if n:
        print(f"Python dựng sẵn JSON cho {n} câu khuôn C_ja (lời giải chỉ chép lại lời thoại JA) → output/json_vi/claude_tao/")


if __name__ == "__main__":
    args, cfg = CT._args(), D.cfg()
    st = Status(D.status_path())
    if args.chuan_bi:
        dung_python(args, st)
        CT.gd1_chuan_bi(D, args, cfg, st, STATES, user_message, bo_qua=bo_qua)
    else:
        CT.gd1_nhan(D, args, cfg, st, STATES, bo_sung=D.bo_sung)
