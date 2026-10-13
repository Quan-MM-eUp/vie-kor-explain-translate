"""Dạng 13 – Đọc hiểu tổng hợp: nội dung đầu vào cho TÁC TỬ TẠO (Claude A).

  GĐ1: STATES, FLAG_HINT, user_message(norm)                     → s1_claude_tao.py
  GĐ2: terms_text(glossary), load_tm(cfg), user_message_gd2(…)    → s2_claude_dich.py
Tác tử TẠO nhận đoạn văn đã tách A/B (chỉ để hiểu – không chép vào JSON) + đề + lời giải đã chuẩn hóa + lưu ý theo cờ s0.
"""
import json
import os

import _dang as D
from pipeline_chung.common import load_json

STATES = ("ĐANG_XỬ_LÝ", "LỖI_KỸ_THUẬT")

FLAG_HINT = {
    "dich_doan_van": "Lời giải là BẢN DỊCH đoạn văn: các đoạn dịch dưới nhãn 'A' / 'B' (/ 'Đoạn văn A') → full_translation = [{label:'A', lines:[{speaker:null, ja:null, meaning:{vi:<đoạn dịch>}} …]}, {label:'B', …}] (mỗi đoạn văn / xuống dòng đôi một phần tử lines; bỏ nhãn 'Đoạn văn:'). Phần 'Câu hỏi:' + dịch → question.meaning; các dòng '1. … 4.' tiếng Việt → options[i].meaning; option_ja = lựa chọn của ĐỀ; quotes = []; analysis = null (trừ khi có câu nhận xét); is_match theo đáp án của đề.",
    "chi_dap_an": "Lời giải chỉ có dịch câu hỏi + dịch 4 lựa chọn + 'Câu trả lời đúng là:' → question.meaning = dòng dịch câu hỏi; options[i].meaning = dòng dịch lựa chọn i; option_ja = lựa chọn của ĐỀ; analysis của lựa chọn đúng = nguyên văn 'Câu trả lời đúng là:' + phần sau; các lựa chọn khác analysis = null; quotes = []; is_match theo đáp án của đề.",
    "goi_y": "Lời giải chỉ có 'ヒント：' + các câu trích (A：… / B：…) → đặt các câu trích vào quotes của lựa chọn ĐÚNG (meaning = null, nhãn 'A：' / 'B：' bỏ khỏi ja nhưng ghi analysis = 'ヒント：A / B' bọc ⟪ ⟫ như bản gốc nếu cần giữ chữ); các lựa chọn khác meaning / analysis = null; option_ja = lựa chọn của ĐỀ.",
    "khuon_khac": "Lời giải khuôn lạ (không có 4 dòng lựa chọn tiếng Nhật): đặt từng phần vào trường gần nhất – dòng dịch câu hỏi → question.meaning; dòng '1.–4.' tiếng Việt → options[i].meaning; đoạn nhận xét chung → analysis của lựa chọn ĐÚNG; dòng tiếng Nhật trùng một lựa chọn của đề → option_ja của lựa chọn đó; option_ja còn lại = lựa chọn của ĐỀ; is_match theo đáp án của đề. KHÔNG tự viết thêm.",
    "thieu_ket_luan": "Có lựa chọn không có dòng '→ ĐÚNG/SAI' – is_match của lựa chọn đó theo đáp án của đề (dap_an_so).",
    "nhieu_dung": "Lời giải kết luận ĐÚNG cho ≠ 1 lựa chọn – is_match chép ĐÚNG như lời giải nói (kể cả 2 lựa chọn true); correct.index vẫn = dap_an_so.",
    "lech_dap_an": "Lời giải kết luận ĐÚNG một lựa chọn khác đáp án – is_match chép như lời giải; correct.index = dap_an_so.",
    "cau_hoi_lech": "Câu hỏi trong lời giải khác đề – question.ja chép NGUYÊN như lời giải (không sửa theo đề).",
    "lua_chon_lech": "Có dòng lựa chọn trong lời giải viết khác đề – option_ja chép NGUYÊN như LỜI GIẢI.",
    "thieu_nghia_lua_chon": "Có lựa chọn không có dòng 'Nghĩa:' – meaning = null.",
    "nghia_lap": "Có lựa chọn có 2 dòng 'Nghĩa:' – dòng đầu vào meaning, dòng sau là chữ của analysis (chép cả nhãn).",
    "trich_dan_giua_cau": "Có câu trích 「…」 nằm GIỮA câu tiếng Việt (vd 'Câu 「ドアの数はそのまま」 (giữ nguyên số cửa) cho thấy…') – KHÔNG tách vào quotes: giữ nguyên tại chỗ trong analysis, bọc ⟪「…」⟫ (bản dịch trong ngoặc giữ nguyên sau đó).",
    "trich_dan_ngoai_doan": "Có câu trích không tìm thấy trong đoạn văn – vẫn chép NGUYÊN như lời giải.",
    "trich_dan_sai_nguon": "Lời giải có thể gán nhầm câu trích cho đoạn A/B – vẫn chép NGUYÊN câu dẫn ('Đoạn A có câu:' …) vào analysis.",
    "chen_tu_nhat": "Câu tiếng Việt có chen từ / cụm tiếng Nhật (ngoài 「」) – bọc ⟪ ⟫ từng cụm, giữ nguyên chữ (kể cả khi cụm Nhật bị gõ lẫn lộn).",
    "co_furigana": "Có furigana – chép nguyên ｜chữ《cách đọc》 ở đúng chỗ (cả trong question.ja, option_ja, quotes.ja và trong ⟪ ⟫); không tự thêm, không bỏ.",
    "de_gach_chan": "Đề có gạch chân – giữ { } đúng như LỜI GIẢI (lời giải không có { } thì không thêm).",
}


def user_message(norm):
    de = norm["de"]
    payload = {
        "question_id": norm["question_id"], "cau_con": norm["cau_con"], "cap_do": norm["cap_do"],
        "doan_van_chi_de_hieu": norm.get("doan_van"),
        "de_bai": {"cau_hoi": de["cau_hoi"], "cac_lua_chon": {str(i + 1): x for i, x in enumerate(de["lua_chon"])},
                   "dap_an_so": de["dap_an_so"]},
        "khuon_loi_giai": norm.get("khuon"),
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
        lines += ["", "Mẫu câu (X, A, B, … là phần thay đổi):"] + [f"- {k} → {v}" for k, v in g["mau_cau"].items()]
    return "\n".join(lines)


def load_tm(cfg):
    path = D.OUT(cfg["bo_nho_dich"]["file"])
    return load_json(path) if cfg["bo_nho_dich"].get("dung") and os.path.exists(path) else {}


def user_message_gd2(norm, tagged, todo):
    de = norm["de"]
    ctx = {"doan_van_A_B": norm.get("doan_van"), "cau_hoi": de["cau_hoi"],
           "cac_lua_chon": {str(i + 1): x for i, x in enumerate(de["lua_chon"])}, "dap_an_so": de["dap_an_so"]}
    return ("NGỮ CẢNH ĐỀ (chỉ để hiểu – đoạn văn KHÔNG dịch):\n" + json.dumps(ctx, ensure_ascii=False, indent=1) +
            "\n\nJSON LỜI GIẢI (trường dịch từ tiếng Việt: {\"id\": …, \"vi\": …}; trường dịch TRỰC TIẾP từ tiếng Nhật: "
            "{\"id\": …, \"dich_tu_tieng_nhat\": true, \"nguon\": …}):\n" + json.dumps(tagged, ensure_ascii=False, indent=1) +
            "\n\nDỊCH CÁC ID SAU (chỉ các id này): " + ", ".join(todo))
