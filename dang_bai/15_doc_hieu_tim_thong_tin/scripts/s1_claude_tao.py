"""[Dạng 15] Giai đoạn 1 – Bước 1.1 do tác tử TẠO Claude làm (không GPT API). Logic chung: pipeline_chung/claude_tao.py.

  python3 scripts/s1_claude_tao.py --chuan-bi --tu 1 --den 11   → output/claude/tao_gd1_danh_sach.json + <id>.input.json
  (tác tử tạo theo prompts/s1_claude_tao.md ghi output/json_vi/claude_tao/<id>.json)
  python3 scripts/s1_claude_tao.py --nhan --tu 1 --den 11       → schema, định danh, reference_raw, meta, trạng thái
Bước tiếp theo: s1_claude_goi.py → tác tử KIỂM TRA soát → s1_kiem_tra.py → s1_chot.py
"""
import _dang as D
from pipeline_chung import claude_tao as CT
from _dau_vao import STATES, user_message

if __name__ == "__main__":
    CT.main_gd1(D, STATES, user_message)
