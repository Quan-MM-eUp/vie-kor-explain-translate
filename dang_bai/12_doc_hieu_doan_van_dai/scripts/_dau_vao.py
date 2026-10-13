"""Dạng 12 – Đọc hiểu đoạn văn dài: nội dung đầu vào cho TÁC TỬ TẠO (Claude A).

  GĐ1: STATES, FLAG_HINT, user_message(norm)                     → s1_claude_tao.py
  GĐ2: terms_text(glossary), load_tm(cfg), user_message_gd2(…)    → s2_claude_dich.py
Tác tử TẠO nhận thêm ĐOẠN VĂN (chỉ để hiểu ngữ cảnh / đối chiếu câu trích – KHÔNG chép vào JSON).
"""
import json
import os

import _dang as D
from pipeline_chung.common import load_json

STATES = ("ĐANG_XỬ_LÝ", "LỖI_KỸ_THUẬT")

KHUON_HINT = {
    "chuan": "Khuôn CHUẨN: dòng câu hỏi tiếng Nhật + dòng nghĩa → 4 khối 'i. <lựa chọn>' (Nghĩa / Trích dẫn / Giải thích / → ĐÚNG|SAI). Làm theo mục 2 của prompts/s1_chuyen_json.md.",
    "chi_ban_dich": "Khuôn CHỈ BẢN DỊCH (mục 4a của s1_chuyen_json.md): Python đã bỏ bản dịch đoạn văn. question.ja = câu hỏi của đề; question.meaning = dòng câu hỏi tiếng Việt; "
                    "options[i].option_ja = lựa chọn i của đề, meaning = dòng tiếng Việt thứ i, is_match = (i = đáp án của đề), quotes = [], analysis = null. "
                    "Dòng 'Câu trả lời đúng là: …' KHÔNG chép (đã thể hiện bằng is_match / correct).",
    "tu_do": "Khuôn TỰ DO (mục 4b của s1_chuyen_json.md): question.ja = câu hỏi của đề, question.meaning = null; options[i].option_ja = lựa chọn i của đề, meaning = null, quotes = [], "
             "is_match = (i = đáp án của đề); TOÀN BỘ lời giải (giữ \\n, bọc tiếng Nhật trong ⟪ ⟫) vào analysis của lựa chọn đáp án; analysis các lựa chọn khác = null.",
}

FLAG_HINT = {
    "can_hinh": "Câu hỏi chọn HÌNH: lựa chọn chỉ là '1'…'4' (hình không có trong dữ liệu) – option_ja chép đúng như lời giải ('1', '2'…), vẫn chuyển JSON bình thường.",
    "khong_du_4_khoi": "Lời giải KHÔNG có đủ 4 khối lựa chọn – lựa chọn thiếu khối: option_ja = lựa chọn của đề, meaning = null, quotes = [], analysis = null, is_match = (index = đáp án của đề).",
    "lua_chon_khac_de": "Có dòng lựa chọn trong lời giải viết khác đề – option_ja vẫn chép NGUYÊN như LỜI GIẢI (không sửa theo đề).",
    "cau_hoi_khac_de": "Dòng câu hỏi trong lời giải khác đề – question.ja chép NGUYÊN như LỜI GIẢI.",
    "cau_hoi_khong_tieng_nhat": "Dòng đầu lời giải là tiếng Việt (không có câu hỏi tiếng Nhật) – question.ja = câu hỏi của đề; dòng tiếng Việt đó vào question.meaning.",
    "khong_nghia_cau_hoi": "Không có dòng nghĩa của câu hỏi – question.meaning = null.",
    "co_dau_khac": "Phần đầu có hơn 2 dòng (câu hỏi lặp lại / tách dòng / có nhãn) – dòng 1 vào question.ja; MỌI dòng còn lại trước lựa chọn 1 vào question.meaning (giữ \\n, tiếng Nhật bọc ⟪ ⟫).",
    "thieu_nghia_lua_chon": "Có lựa chọn không có dòng 'Nghĩa:' – meaning của lựa chọn đó = null (không tự dịch).",
    "thieu_danh_gia": "Có khối không có '→ ĐÚNG / → SAI' – is_match của khối đó = (index = đáp án của đề).",
    "danh_gia_lap": "Một khối có 2 dòng đánh giá – is_match theo dòng CUỐI; ghi trong báo cáo điểm khó.",
    "danh_gia_lech_dap_an": "Chữ đánh giá của lời giải lệch đáp án của đề – is_match vẫn chép ĐÚNG theo chữ đánh giá của lời giải (không sửa); correct theo đáp án của đề.",
    "khong_danh_gia_dung": "Không khối nào được chấm ĐÚNG – is_match chép đúng như lời giải (đều false).",
    "trich_khong_nhan": "Có câu trích 「…」 đứng đầu dòng / đầu mục '- ' không có nhãn 'Trích dẫn' – nếu cả dòng chỉ là 「câu trích」 (+ nghĩa trong ngoặc) thì vẫn là quotes; nếu sau 」 còn câu giải thích thì là analysis.",
    "nhieu_trich_dan": "Có lựa chọn với nhiều câu trích – mỗi câu trích một phần tử quotes, theo thứ tự; câu chữ xen giữa các trích dẫn vào analysis.",
    "trich_lech_doan_van_nhe": "Có câu trích lệch nhẹ đoạn văn – vẫn chép quotes[].ja NGUYÊN như lời giải (không sửa theo đoạn văn).",
    "trich_lech_doan_van_nang": "Có câu trích khác đoạn văn – vẫn chép NGUYÊN như lời giải.",
    "trich_khong_tim_thay": "Có câu trích không tìm thấy trong đoạn văn – vẫn chép NGUYÊN như lời giải.",
    "nhan_tieng_nhat": "Lời giải có nhãn tiếng Nhật ('｜引用《いんよう》:' = Trích dẫn, '｜解説《かいせつ》:' / '｜解《かい》 ｜説《せつ》:' = Giải thích, '｜意味《いみ》:' = Nghĩa) và chữ đánh giá tiếng Nhật ('→ ｜正《ただ》しい' = ĐÚNG) – hiểu như nhãn Việt tương ứng; câu chữ còn lại chép NGUYÊN (tiếng Nhật lẫn trong câu Việt bọc ⟪ ⟫).",
    "tieng_nhat_tran": "Có từ tiếng Nhật (furigana) nằm trần giữa câu tiếng Việt – bọc ⟪ ⟫ quanh từng cụm tiếng Nhật (kể cả furigana), không sửa câu.",
    "furigana_hong": "Python đã đổi furigana kiểu lạ '<|漢字;よみ|' thành ｜漢字《よみ》 – chép như đầu vào.",
    "ky_tu_rac": "Python đã thu gọn chuỗi khoảng trắng rác – chép như đầu vào; câu chữ rác còn lại (vd '<| trích;', 'начально:') vẫn chép nguyên vào analysis.",
    "co_furigana": "Có furigana – chép nguyên ｜chữ《cách đọc》 ở đúng chỗ (trong câu Nhật và trong ⟪ ⟫); không tự thêm, không bỏ.",
    "dap_an_de_loi": "Dữ liệu đề lỗi (dap_an_so không phải 1–4): correct.index = lựa chọn được chấm ĐÚNG trong lời giải; ghi rõ trong báo cáo điểm khó.",
}


def user_message(norm):
    de = norm["de"]
    payload = {
        "question_id": norm["question_id"], "cau_con": norm["cau_con"], "cap_do": norm["cap_do"],
        "khuon_loi_giai": norm["khuon_goc"],
        "huong_dan_khuon": KHUON_HINT.get(norm["khuon_goc"]),
        "doan_van_chi_de_hieu": norm.get("doan_van"),
        "de_bai": {"cau_hoi": de["cau_hoi"], "cac_lua_chon": {str(i + 1): x for i, x in enumerate(de["lua_chon"])},
                   "dap_an_so": de["dap_an_so"]},
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
    return "\n".join(lines)


def load_tm(cfg):
    path = D.OUT(cfg["bo_nho_dich"]["file"])
    return load_json(path) if cfg["bo_nho_dich"].get("dung") and os.path.exists(path) else {}


def user_message_gd2(norm, tagged, todo):
    de = norm["de"]
    ctx = {"doan_van": norm.get("doan_van"), "cau_hoi": de["cau_hoi"],
           "cac_lua_chon": {str(i + 1): x for i, x in enumerate(de["lua_chon"])}, "dap_an_so": de["dap_an_so"]}
    return ("NGỮ CẢNH ĐỀ (chỉ để hiểu – đoạn văn KHÔNG dịch):\n" + json.dumps(ctx, ensure_ascii=False, indent=1) +
            "\n\nJSON LỜI GIẢI (trường dịch từ tiếng Việt: {\"id\": …, \"vi\": …}; trường dịch TRỰC TIẾP từ tiếng Nhật: "
            "{\"id\": …, \"dich_tu_tieng_nhat\": true, \"nguon\": …, \"vi_tham_khao\": …}):\n" + json.dumps(tagged, ensure_ascii=False, indent=1) +
            "\n\nDỊCH CÁC ID SAU (chỉ các id này): " + ", ".join(todo))
