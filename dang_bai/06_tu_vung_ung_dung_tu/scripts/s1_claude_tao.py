"""[Dạng 06] Giai đoạn 1 – Bước 1.1 do tác tử TẠO Claude làm (thay GPT API). Logic chung: pipeline_chung/claude_tao.py.

  python scripts/s1_claude_tao.py --chuan-bi --tu 101 --den 110   → output/claude/tao_gd1_danh_sach.json + <id>.input.json
  (tác tử tạo theo prompts/s1_claude_tao.md ghi output/json_vi/claude_tao/<id>.json)
  python scripts/s1_claude_tao.py --nhan --tu 101 --den 110       → schema, định danh, meta, trạng thái
Bước tiếp theo: s1_claude_goi.py → Claude kiểm tra → s1_kiem_tra.py → s1_chot.py
"""
import _dang as D
from pipeline_chung import claude_tao as CT
from s1_gpt_chuyen import STATES, user_message      # cùng một nội dung đầu vào như bản GPT



def bo_reference_raw(doc, norm):
    """Dạng 06 không có phần THAM KHẢO (0/676 câu) và schema vocab_usage.v2 không có trường reference_raw –
    bỏ trường mà claude_tao.gd1_nhan điền chung (không sửa code chung)."""
    doc.pop("reference_raw", None)
    return doc


if __name__ == "__main__":
    CT.main_gd1(D, STATES, user_message, bo_sung=bo_reference_raw)
