"""[Dạng 18] Giai đoạn 1 – Bước 1.1 do tác tử TẠO Claude làm. Logic chung: pipeline_chung/claude_tao.py.

  python scripts/s1_claude_tao.py --chuan-bi --tu 1 --den 10   → output/claude/tao_gd1_danh_sach.json + <id>.input.json
  (tác tử tạo theo prompts/s1_claude_tao.md ghi output/json_vi/claude_tao/<id>.json)
  python scripts/s1_claude_tao.py --nhan --tu 1 --den 10       → schema, định danh, reference_raw (= null), meta, trạng thái
Bước tiếp theo: s1_claude_goi.py → Claude kiểm tra → s1_kiem_tra.py → s1_chot.py
"""
import _dang as D
from pipeline_chung import claude_tao as CT
from _dau_vao import STATES, user_message


def bo_qua(norm):
    return norm.get("khuon_goc") == "trong" or not (norm.get("loi_thoai") or {}).get("nguon")


if __name__ == "__main__":
    CT.main_gd1(D, STATES, user_message, bo_qua=bo_qua)
