"""[Dạng 11] Giai đoạn 2 – Bước 2.1–2.3 do tác tử TẠO Claude dịch (thay GPT API). Logic chung: pipeline_chung/claude_tao.py.

  python scripts/s2_claude_dich.py --chuan-bi --tu 61 --den 70  → map, request, _he_thong.md, tao_gd2_danh_sach.json
  (tác tử tạo theo prompts/s2_claude_dich.md ghi output/claude/tao_gd2/<id>.output.json = {"fN": "…"})
  python scripts/s2_claude_dich.py --nhan --tu 61 --den 70      → ghép → output/json_ko/claude_tao/<id>.json; lỗi → LỖI_GĐ2
Bước tiếp theo: s2_claude_goi.py → Claude kiểm tra → s2_kiem_tra.py
"""
import _dang as D
from pipeline_chung import claude_tao as CT
from _dich_v3 import danh_dau, prefill_v3, tagged_copy_v3
from _dau_vao import load_tm, terms_text, user_message_gd2 as user_message

HOOK = CT.HookGD2(user_message=user_message, load_tm=load_tm, terms_text=terms_text,
                  danh_dau=danh_dau, prefill=prefill_v3, tagged=tagged_copy_v3)

if __name__ == "__main__":
    CT.main_gd2(D, HOOK)
