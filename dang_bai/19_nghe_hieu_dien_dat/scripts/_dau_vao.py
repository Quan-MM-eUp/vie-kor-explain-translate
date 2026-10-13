"""Dạng 19 – Nghe hiểu diễn đạt: nội dung đầu vào cho TÁC TỬ TẠO (Claude A).

  GĐ1: STATES, FLAG_HINT, user_message(norm), bo_qua(norm)        → s1_claude_tao.py
  GĐ2: terms_text(glossary), load_tm(cfg), user_message_gd2(…)    → s2_claude_dich.py
"""
import json
import os

import _dang as D
from pipeline_chung.common import load_json

STATES = ("ĐANG_XỬ_LÝ", "LỖI_KỸ_THUẬT")


def bo_qua(norm):
    """Không giao cho tác tử TẠO: câu sai dạng, khuôn C, không có lời giải."""
    return norm.get("khuon_goc") not in ("A", "B", "D")


FLAG_HINT = {
    "khuon_B": "Lời giải KHÔNG có phần dịch tình huống (bắt đầu ngay bằng '1. …') – prompt.utterance.meaning = null; các khối lựa chọn chuyển như bình thường.",
    "khuon_D": "Lời giải CHỈ có dòng dịch tình huống + 3 dòng nghĩa (không có '→ ĐÚNG/SAI', không phân tích): utterance.meaning = dòng tình huống; "
               "options[i].sentence.ja = câu thứ i trong 'cau_noi_transcript' (chép nguyên); sentence.meaning = dòng nghĩa thứ i; "
               "is_correct = (i == dap_an_so); analysis = null.",
    "khong_co_tinh_huong_ja": "Không có câu tình huống tiếng Nhật – vẫn để prompt.utterance.ja = chuỗi rỗng \"\" (Python điền).",
    "nghia_dau_lech": "Dòng nghĩa ở phần đầu khác dòng 'Nghĩa:' trong khối – sentence.meaning lấy theo dòng 'Nghĩa:' của khối.",
    "lc_lech_transcript_nhe": "Câu Nhật trong lời giải hơi khác transcript – vẫn chép sentence.ja NGUYÊN như lời giải (không sửa theo transcript).",
    "lc_lech_transcript_nang": "Câu Nhật trong lời giải khác transcript – vẫn chép sentence.ja NGUYÊN như lời giải (không sửa theo transcript).",
    "ket_luan_lech_dap_an": "Kết luận '→ ĐÚNG' của lời giải không khớp đáp án của đề – is_correct vẫn theo đúng lời giải; correct.index = dap_an_so.",
    "nhan_lap": "Có khối với nhãn lặp (2 dòng 'Nghĩa:' / 2 dòng '→ …') – dòng đầu vào trường, dòng thừa nối vào analysis.",
    "thieu_phan_tich": "Có khối không có đoạn phân tích – analysis = null.",
    "thieu_nghia": "Có khối không có dòng 'Nghĩa:' – sentence.meaning = null.",
    "co_truoc_khoi": "Có dòng chữ giữa ### và khối '1.' – báo trong điểm khó (không có trường riêng; không tự bỏ, không tự đặt chỗ khác).",
    "co_furigana": "Có furigana – chép nguyên ｜chữ《cách đọc》 ở đúng chỗ (cả trong câu Nhật và trong ⟪ ⟫); không tự thêm, không bỏ.",
}


def user_message(norm):
    de = norm["de"]
    payload = {
        "question_id": norm["question_id"], "cau_con": norm["cau_con"], "cap_do": norm["cap_do"], "khuon": norm["khuon_goc"],
        "cau_tinh_huong_ja": norm.get("tinh_huong_ja") or "",
        "cau_noi_transcript": {str(i + 1): x for i, x in enumerate(norm.get("tr_lua_chon") or [])},
        "dap_an_so": de["dap_an_so"],
        "loi_giai_goc": norm["dau_vao"],
        "luu_y": [FLAG_HINT[c] for c in norm["co"] if c in FLAG_HINT],
    }
    return "Chuyển lời giải sau sang JSON theo schema.\n\n" + json.dumps(payload, ensure_ascii=False, indent=1)


# ---------------- GĐ2 ----------------
def terms_text(g):
    lines = ["Thuật ngữ (Việt → Hàn):"] + [f"- {k} → {v}" for k, v in g["thuat_ngu"].items()]
    if g["cau_co_dinh"]:
        by_ko = {}
        for vi, ko in g["cau_co_dinh"].items():
            by_ko.setdefault(ko, []).append(vi)
        lines += ["", "Câu cố định (mọi cách viết tiếng Việt bên trái đều dịch đúng một câu bên phải):"]
        lines += [f"- {' | '.join(v)} → {ko}" for ko, v in by_ko.items()]
    if g["mau_cau"]:
        lines += ["", "Mẫu câu (X, A, B là phần thay đổi):"] + [f"- {k} → {v}" for k, v in g["mau_cau"].items()]
    if g.get("cau_noi_co_dinh"):
        lines += ["", "Câu nói tiếng Nhật cố định (lời chào / câu giao tiếp – nghĩa tiếng Hàn tương đương):"]
        lines += [f"- {k} → {v}" for k, v in g["cau_noi_co_dinh"].items()]
    return "\n".join(lines)


def load_tm(cfg):
    path = D.OUT(cfg["bo_nho_dich"]["file"])
    return load_json(path) if cfg["bo_nho_dich"].get("dung") and os.path.exists(path) else {}


def user_message_gd2(norm, tagged, todo):
    ctx = {"cau_tinh_huong_ja": norm.get("tinh_huong_ja"), "cau_noi_transcript": norm.get("tr_lua_chon"),
           "dap_an_so": norm["de"]["dap_an_so"]}
    return ("NGỮ CẢNH ĐỀ (chỉ để hiểu):\n" + json.dumps(ctx, ensure_ascii=False, indent=1) +
            "\n\nJSON LỜI GIẢI (trường dịch từ tiếng Việt: {\"id\": …, \"vi\": …}; trường dịch TRỰC TIẾP từ tiếng Nhật: "
            "{\"id\": …, \"dich_tu_tieng_nhat\": true, \"nguon\": …}):\n" + json.dumps(tagged, ensure_ascii=False, indent=1) +
            "\n\nDỊCH CÁC ID SAU (chỉ các id này): " + ", ".join(todo))
