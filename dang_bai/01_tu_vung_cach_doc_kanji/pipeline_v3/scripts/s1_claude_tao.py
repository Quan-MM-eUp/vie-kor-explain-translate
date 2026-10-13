"""[Dạng 01 – pipeline v3] Giai đoạn 1 – Bước 1.1 do tác tử TẠO Claude làm (thay GPT API). Logic chung: pipeline_chung/claude_tao.py.

  python scripts/s1_claude_tao.py --chuan-bi --tu 201 --den 210   → output/claude/tao_gd1_danh_sach.json + <id>.input.json
  (tác tử tạo theo prompts/s1_claude_tao.md ghi output/json_vi/claude_tao/<id>.json)
  python scripts/s1_claude_tao.py --nhan --tu 201 --den 210       → schema, định danh, reference_raw, meta, trạng thái
Bước tiếp theo: s1_claude_goi.py → Claude kiểm tra → s1_kiem_tra.py → s1_chot.py
"""
import _dang as D
from pipeline_chung import claude_tao as CT
from pipeline_chung import tham_khao as TK
from s1_gpt_chuyen import STATES, user_message      # cùng một nội dung đầu vào như bản GPT


def dien_tham_khao(doc, norm):
    """Dạng 01: phần tham khảo nằm ở norm['tham_khao'] (không phải norm['phan']['tham_khao'] như các dạng khác) –
    điền lại reference_raw đúng nguyên văn (không sửa code chung)."""
    return TK.dien(doc, norm.get("tham_khao"))


if __name__ == "__main__":
    CT.main_gd1(D, STATES, user_message, bo_sung=dien_tham_khao)
