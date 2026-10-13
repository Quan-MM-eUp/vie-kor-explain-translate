"""Dạng 10 – Đọc hiểu đoạn văn ngắn: nội dung đầu vào cho TÁC TỬ TẠO (Claude A).

  GĐ1: STATES, FLAG_HINT, user_message(norm)                     → s1_claude_tao.py
  GĐ2: terms_text(glossary), load_tm(cfg), user_message_gd2(…)    → s2_claude_dich.py
"""
import json
import os

import _dang as D
from pipeline_chung.common import load_json

STATES = ("ĐANG_XỬ_LÝ", "LỖI_KỸ_THUẬT")

FLAG_HINT = {
    "khuon_a": "Khuôn A: 'khung_python' là khung Python tách sẵn từ lời giải – dùng làm khung, nhưng ĐỐI CHIẾU LẠI với loi_giai_goc; Python tách sai thì làm theo lời giải và nêu ở báo cáo điểm khó.",
    "khuon_b": "Khuôn B: full_translation = [{label: null, lines: mỗi dòng của 'Đoạn văn:' một phần tử {speaker: null, ja: null, meaning: {vi}}}]; question.ja / option_ja chép từ khung (câu của ĐỀ, đã bỏ furigana); options[i].meaning = dòng dịch lựa chọn i; quotes = []; analysis = null (trừ lựa chọn đúng nếu khung có analysis_vi); dòng 'Câu trả lời đúng là: …' KHÔNG chép (lặp lại nghĩa đáp án).",
    "khuon_le": "Khuôn lẻ – Python KHÔNG tách được khung: tự đặt theo nội dung. question.ja = câu hỏi tiếng Nhật trong lời giải (không có thì câu hỏi của đề, bỏ furigana); mỗi lựa chọn: option_ja = dòng tiếng Nhật của lời giải (không có thì lựa chọn của đề), meaning = dòng nghĩa, analysis = phân tích; câu chữ không thuộc lựa chọn nào → summary[0].points (heading null). Lựa chọn lời giải không nói tới: meaning / analysis = null, quotes = []. Chép nguyên văn, không thêm.",
    "khong_ja_cau_hoi": "Lời giải không có câu hỏi tiếng Nhật – question.ja = câu hỏi của đề (khung đã điền).",
    "khong_nghia_cau_hoi": "Lời giải không có nghĩa câu hỏi – question.meaning = null.",
    "co_phan_tich_chung": "Có câu chữ trước lựa chọn 1 (phân tích chung) – summary = [{heading: null, points: [mỗi dòng một phần tử]}], chép nguyên.",
    "lc_khong_nghia": "Có lựa chọn không có 'Nghĩa:' – meaning = null.",
    "lc_khong_ket_luan": "Có lựa chọn không có '→ ĐÚNG/SAI' – is_match theo đáp án của đề.",
    "lc_khong_phan_tich": "Có lựa chọn không có phân tích – analysis = null.",
    "co_sau_ket_luan": "Có câu chữ sau '→ ĐÚNG/SAI' của một lựa chọn – nối vào cuối analysis của lựa chọn đó (khung đã nối).",
    "ket_luan_lech_dap_an": "Lời giải kết luận ĐÚNG ở lựa chọn khác đáp án của đề – is_match và correct vẫn theo dap_an_so của ĐỀ.",
    "co_trich_dan": "Có câu trích dẫn đứng riêng dòng – quotes[] = {ja: câu tiếng Nhật (bỏ 「」 bao ngoài, giữ furigana / { }), meaning: {vi: bản dịch trong ngoặc, bỏ ngoặc}}; trích dẫn nằm trong câu tiếng Việt thì để nguyên trong analysis (bọc ⟪ ⟫).",
    "trich_dan_khong_dich": "Có câu trích dẫn không kèm bản dịch – quotes[].meaning = null.",
    "b_co_giai_thich": "Khuôn B có câu chữ giải thích – đặt vào analysis của lựa chọn đúng (khung đã đặt).",
    "kanji_chen": "Lời giải có chữ Hán chen giữa câu tiếng Việt (lỗi máy dịch cũ) – vẫn CHÉP NGUYÊN (bọc ⟪ ⟫ như mọi tiếng Nhật), KHÔNG tự đổi sang chữ Việt; tác tử KIỂM TRA xử lý.",
    "ky_hieu_furigana_hong": "Lời giải có ký hiệu furigana hỏng dạng '<|今;いま|' – chép NGUYÊN, không sửa.",
    "co_furigana": "Có furigana – chép nguyên ｜chữ《cách đọc》 ở đúng chỗ (cả trong ⟪ ⟫).",
}


def user_message(norm):
    de = norm["de"]
    payload = {
        "question_id": norm["question_id"], "cau_con": norm["cau_con"], "cap_do": norm["cap_do"],
        "khuon": norm.get("khuon_goc"),
        "de_bai": {"cau_hoi": de["cau_hoi"], "cac_lua_chon": {str(i + 1): x for i, x in enumerate(de["lua_chon"]) if x},
                   "dap_an_so": de["dap_an_so"]},
        "loi_giai_goc": norm["dau_vao"],
        "khung_python": D.khung_python(norm),
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
    return "\n".join(lines)


def load_tm(cfg):
    path = D.OUT(cfg["bo_nho_dich"]["file"])
    return load_json(path) if cfg["bo_nho_dich"].get("dung") and os.path.exists(path) else {}


def user_message_gd2(norm, tagged, todo):
    de = norm["de"]
    ctx = {"doan_van_tieng_nhat": norm.get("doan_van"), "cau_hoi": de["cau_hoi"],
           "cac_lua_chon": {str(i + 1): x for i, x in enumerate(de["lua_chon"]) if x}, "dap_an_so": de["dap_an_so"]}
    return ("NGỮ CẢNH ĐỀ (chỉ để hiểu – đoạn văn tiếng Nhật, câu hỏi, lựa chọn, đáp án):\n" + json.dumps(ctx, ensure_ascii=False, indent=1) +
            "\n\nJSON LỜI GIẢI (trường dịch từ tiếng Việt: {\"id\": …, \"vi\": …}; trường KẾT HỢP – nghĩa phải đúng với TIẾNG NHẬT: "
            "{\"id\", \"vi\", \"tu_tieng_nhat\", \"loai\", \"luu_y\"}):\n"
            + json.dumps(tagged, ensure_ascii=False, indent=1) +
            "\n\nDỊCH CÁC ID SAU (chỉ các id này): " + ", ".join(todo))
