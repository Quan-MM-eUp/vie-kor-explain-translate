"""[Dạng 16] Giai đoạn 1 – Bước 1.1: tác tử TẠO Claude chuyển lời giải → JSON tiếng Việt (thay GPT API).
Câu KHÔNG có phân tích (tao_bang = python, khuôn C / D / E): Python dựng cả JSON ở bước --chuan-bi (không giao tác tử TẠO).
Logic chung: pipeline_chung/claude_tao.py.

  python3 scripts/s1_claude_tao.py --chuan-bi --tu 1 --den 10   → output/claude/tao_gd1_danh_sach.json + <id>.input.json
                                                                   (+ JSON Python cho câu không phân tích)
  (tác tử TẠO theo prompts/s1_claude_tao.md ghi output/json_vi/claude_tao/<id>.json)
  python3 scripts/s1_claude_tao.py --nhan --tu 1 --den 10       → schema, định danh, Python điền full_translation / key_info / reference_raw
Bước tiếp theo: s1_claude_goi.py → tác tử KIỂM TRA → s1_kiem_tra.py → s1_chot.py
"""
import os

import _dang as D
from pipeline_chung import claude_tao as CT
from pipeline_chung.common import load_json, save_json
from pipeline_chung.trang_thai import Status
from _dau_vao import STATES, user_message


def python_tao(args, st):
    """Câu không có phân tích → Python dựng JSON vào output/json_vi/claude_tao/<id>.json (meta nguon = python)."""
    n = 0
    for sid in D.bo_qua_da_duyet(D.select_ids(args, st, STATES), args, "1.1-python"):
        norm = D.load_norm(sid)
        if norm.get("tao_bang") != "python":
            continue
        p = CT.gd1_out(D, sid)
        if os.path.exists(p) and not args.force:
            continue
        doc = D.python_json(norm)
        for k in ("key_info", "reference_raw"):       # Python điền lại ở --nhan (bo_sung) – bản tạo theo schema api
            doc.pop(k, None)
        save_json(doc, p)
        n += 1
    if n:
        print(f"Python dựng JSON cho {n} câu không có phân tích (tao_bang = python) → output/json_vi/claude_tao/")


def sua_meta_python(args, st):
    for sid in D.select_ids(args, st, ("ĐANG_XỬ_LÝ",)):
        mp = D.OUT("json_vi", "claude_tao", sid + ".meta.json")
        if os.path.exists(mp) and D.load_norm(sid).get("tao_bang") == "python":
            m = load_json(mp)
            if m.get("nguon") != "python":
                m.update(nguon="python", model="Python (scripts/_dang.py: python_json)", prompt=D.cfg()["phien_ban_prompt"]["gd1_python"])
                save_json(m, mp)
                st.update(sid, model_gd1=m["model"], prompt_gd1=m["prompt"])
    st.save()


if __name__ == "__main__":
    args, cfg = CT._args(), D.cfg()
    st = Status(D.status_path())
    if args.chuan_bi:
        python_tao(args, st)
        CT.gd1_chuan_bi(D, args, cfg, st, STATES, user_message,
                        bo_qua=lambda norm: norm.get("khuon_goc") == "trong" or norm.get("tao_bang") == "python")
    else:
        CT.gd1_nhan(D, args, cfg, st, STATES, kiem_them=D.kiem_them, bo_sung=D.bo_sung)
        sua_meta_python(args, Status(D.status_path()))
