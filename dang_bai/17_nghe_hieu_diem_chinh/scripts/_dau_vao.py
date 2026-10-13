"""Dạng 17 – Nghe hiểu điểm chính: nội dung đầu vào cho TÁC TỬ TẠO (Claude A).

  GĐ1: STATES, FLAG_HINT, user_message(norm)                     → s1_claude_tao.py
  GĐ2: terms_text(glossary), load_tm(cfg), user_message_gd2(…)    → s2_claude_dich.py
Tác tử TẠO GĐ1 nhận KHUNG JSON do Python dựng (lượt thoại tiếng Nhật đã tách + nhãn người nói, gợi ý ghép nghĩa Việt, 4 lựa chọn,
đáp án, key_info / analysis) cùng các dòng Việt gốc đánh số – nhiệm vụ: soát ghép cặp, sửa chỗ lệch, ghi JSON hoàn chỉnh.
"""
import json
import os

import _dang as D
from pipeline_chung.common import load_json

STATES = ("ĐANG_XỬ_LÝ", "LỖI_KỸ_THUẬT")

FLAG_HINT = {
    "lech_so_dong": "Python KHÔNG ghép được (số dòng Việt ≠ số lượt thoại): trong khung mọi meaning = null – bạn tự ghép từng dòng Việt vào đúng lượt thoại (xem mục 3 của hướng dẫn: gộp / tách lượt được, không đổi chữ).",
    "ghep_gop_dong": "Python ghép được sau khi GỘP lượt thoại (dòng thoại bị xuống dòng giữa lượt / dòng dẫn + câu hỏi) – kiểm tra lại ranh giới các lượt đã gộp.",
    "ghep_nghi_nguoi_noi": "Ghép 1–1 nhưng có dòng Việt mang nhãn ngược người nói (Nam ↔ F, Nữ ↔ M) – soát kỹ từng cặp, có thể lệch một dòng.",
    "tach_nhan_giua_dong": "Python đã tách nhãn người nói ở giữa dòng thành lượt riêng – giữ như khung.",
    "loi_thoai_co_lua_chon": "Lời thoại có 4 lựa chọn ở cuối – Python đã bỏ khỏi full_translation; KHÔNG thêm lại.",
    "loi_thoai_co_tu_vung": "Lời thoại có phần từ vựng '*** 言葉表現' ở cuối – Python đã bỏ; KHÔNG thêm vào JSON.",
    "cau_hoi_trong_loi_thoai": "Đề không có cau_hoi – question.ja trong khung lấy từ lời thoại (câu hỏi lặp lại ở cuối hoặc trong dòng dẫn); question.meaning = câu hỏi tiếng Việt tương ứng (chỉ phần câu hỏi, không chép câu dẫn tình huống).",
    "khong_tim_cau_hoi": "Không tìm được câu hỏi tiếng Nhật: question.ja = null nếu lời thoại thật sự không có câu hỏi.",
    "khong_nghia_lua_chon": "Lời giải không có nghĩa 4 lựa chọn – options[*].meaning = null; mọi dòng Việt là bản dịch lời thoại.",
    "lua_chon_lech": "4 dòng Việt cuối có thể không phải nghĩa lựa chọn (có số sai / nhãn người nói) – xác định lại: nếu là lời thoại thì đưa vào lines, options[*].meaning = null.",
    "thong_tin_khong_dich": "Phần Thông tin chỉ có tiếng Nhật – key_info[*].meaning để null (Python chép nghĩa từ dòng thoại).",
    "thong_tin_lech_so_dong": "Phần Thông tin: số dòng Nhật ≠ số dòng Việt – khung để meaning = null; bạn tự ghép nghĩa Việt của Thông tin vào đúng dòng key_info (một dòng Nhật ứng nhiều dòng Việt → nối bằng ' '; dòng Nhật không có bản Việt → null).",
    "thong_tin_co_giai_thich": "Phần Thông tin có câu giải thích (Đáp án … / Vì …) – khung đã đưa vào analysis của lựa chọn đúng; kiểm tra.",
    "thong_tin_khong_phai_tieng_viet": "Dòng dịch trong Thông tin không phải tiếng Việt – vẫn chép nguyên vào key_info.meaning.vi (tác tử KIỂM TRA xử lý).",
    "khuon_B": "Khuôn B – analysis của lựa chọn đúng = nguyên văn phần sau ###; key_info = [].",
    "khuon_C": "Khuôn C – key_info: khung đã chọn dòng có (i) nếu duy nhất (meaning null – Python chép); không có / nhiều (i) → key_info = [].",
    "co_furigana": "Có furigana – chép nguyên ｜chữ《cách đọc》 ở đúng chỗ; không tự thêm, không bỏ.",
}


def user_message(norm):
    de = norm["de"]
    payload = {
        "question_id": norm["question_id"], "cau_con": norm["cau_con"], "cap_do": norm["cap_do"], "khuon": norm["khuon_goc"],
        "de_bai": {"cau_hoi": de["cau_hoi"], "cac_lua_chon": {str(i + 1): x for i, x in enumerate(de["lua_chon"])}, "dap_an_so": de["dap_an_so"]},
        "luot_thoai_tieng_nhat": [f"J{i}  {(t['speaker'] + ': ') if t['speaker'] else ''}{t['ja']}" for i, t in enumerate(norm["luot"])],
        "dong_viet_goc": {
            "loi_thoai": [f"V{i}  {x}" for i, x in enumerate(norm["vi"]["dong_thoai"])],
            "nghia_lua_chon": norm["vi"]["lua_chon"],
            "sau_###": norm["vi"]["sau_phan_cach"],
        },
        "python_ghep": norm["ghep"]["cach"] or "KHÔNG ghép được – tự ghép",
        "khung_json": norm["khung"],
        "luu_y": [FLAG_HINT[c] for c in norm["co"] if c in FLAG_HINT],
    }
    return ("Soát và hoàn thiện khung JSON dưới đây theo lời giải gốc rồi ghi JSON hoàn chỉnh (schema reading_listening.v1).\n\n"
            + json.dumps(payload, ensure_ascii=False, indent=1))


# ---------------- GĐ2 ----------------
def terms_text(g):
    lines = ["Thuật ngữ (Việt → Hàn):"] + [f"- {k} → {v}" for k, v in g["thuat_ngu"].items()]
    if g["cau_co_dinh"]:
        lines += ["", "Câu cố định:"] + [f"- {vi} → {ko}" for vi, ko in g["cau_co_dinh"].items()]
    if g["mau_cau"]:
        lines += ["", "Mẫu câu:"] + [f"- {k} → {v}" for k, v in g["mau_cau"].items()]
    return "\n".join(lines)


def load_tm(cfg):
    path = D.OUT(cfg["bo_nho_dich"]["file"])
    return load_json(path) if cfg["bo_nho_dich"].get("dung") and os.path.exists(path) else {}


def _sao_chep_ids(tagged):
    out = []

    def walk(o):
        if isinstance(o, dict):
            if "sao_chep_tu" in o and "id" in o:
                out.append(o["id"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(tagged)
    return out


def user_message_gd2(norm, tagged, todo):
    de = norm["de"]
    ctx = {"cau_hoi_de": de["cau_hoi"], "cac_lua_chon": {str(i + 1): x for i, x in enumerate(de["lua_chon"])}, "dap_an_so": de["dap_an_so"]}
    sc = set(_sao_chep_ids(tagged))
    dich = [i for i in todo if i not in sc]
    return ("NGỮ CẢNH ĐỀ (chỉ để hiểu):\n" + json.dumps(ctx, ensure_ascii=False, indent=1) +
            "\n\nJSON LỜI GIẢI. Trường dịch TRỰC TIẾP từ tiếng Nhật: {\"id\", \"dich_tu_tieng_nhat\": true, \"nguoi_noi\", \"ja\", \"vi_tham_khao\"}; "
            "trường dịch từ tiếng Việt: {\"id\", \"vi\"}; trường {\"id\", \"sao_chep_tu\"}: Python tự chép bản dịch của mã kia – KHÔNG dịch, KHÔNG ghi vào output:\n"
            + json.dumps(tagged, ensure_ascii=False, indent=1) +
            "\n\nDỊCH CÁC ID SAU (chỉ các id này): " + ", ".join(dich))
