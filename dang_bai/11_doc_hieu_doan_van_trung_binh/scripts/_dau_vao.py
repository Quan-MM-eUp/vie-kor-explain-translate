"""Dạng 11 – Đọc hiểu: Đoạn văn trung bình: nội dung đầu vào cho TÁC TỬ TẠO (Claude A).

  GĐ1: STATES, FLAG_HINT, user_message(norm)                     → s1_claude_tao.py
  GĐ2: terms_text(glossary), load_tm(cfg), user_message_gd2(…)    → s2_claude_dich.py
GĐ1 không gửi đoạn văn (chỉ chép lời giải – tiết kiệm token); GĐ2 gửi đoạn văn làm ngữ cảnh dịch câu hỏi / lựa chọn / câu trích.
"""
import json
import os

import _dang as D
from pipeline_chung.common import load_json

STATES = ("ĐANG_XỬ_LÝ", "LỖI_KỸ_THUẬT")

FLAG_HINT = {
    "khuon_la": "Lời giải KHÔNG theo khuôn chuẩn (không đủ phân tích 4 lựa chọn). Chép phần có được vào trường gần nhất (mục 'Khuôn lạ' của s1_chuyen_json.md); "
                "options đủ 4 (option_ja chép lựa chọn của đề nếu lời giải không có dòng lựa chọn), trường thiếu = null / []; "
                "is_match = (index == dap_an_so) khi lời giải không kết luận.",
    "khuon_dich_doan_van": "Lời giải có bản dịch tiếng Việt của đoạn văn (sau nhãn 'Đoạn văn:') → full_translation = [{\"label\": null, \"lines\": [mỗi đoạn (dòng) dịch một phần tử "
                           "{\"speaker\": null, \"ja\": null, \"meaning\": {\"vi\": …}}]}]; 'Câu hỏi:' + câu dịch → question.meaning; danh sách lựa chọn tiếng Việt → options[i].meaning; "
                           "'Câu trả lời đúng là: …' (cả nhãn) → analysis của lựa chọn đúng.",
    "khuon_markdown": "Lời giải viết kiểu markdown (###, **, >, *): bỏ ký hiệu markdown (### đầu dòng, ** in đậm, > trích, * gạch đầu dòng) nhưng giữ NGUYÊN chữ; "
                      "câu trích 「…」 → quotes của lựa chọn đúng; phần còn lại → analysis của lựa chọn đúng.",
    "khuon_ngan": "Lời giải chỉ có vài câu giải thích chung (không tách theo lựa chọn) → đặt toàn bộ vào analysis của lựa chọn đúng (dap_an_so); "
                  "các lựa chọn khác meaning / analysis = null, quotes = [].",
    "khuon_khac": "Khuôn khác thường – đặt nội dung theo đúng lựa chọn mà nó nói tới; nội dung chung → analysis của lựa chọn đúng.",
    "thieu_cau_hoi": "Phần đầu lời giải không có dòng câu hỏi tiếng Nhật → question.ja = câu hỏi của đề (de_bai.cau_hoi), chép nguyên.",
    "thieu_dich_cau_hoi": "Phần đầu lời giải không có bản dịch câu hỏi → question.meaning = null (nếu có câu tiếng Việt khác ở phần đầu thì vẫn đưa vào question.meaning).",
    "cau_hoi_lech": "Câu hỏi trong lời giải viết khác đề → question.ja chép theo LỜI GIẢI.",
    "lua_chon_lech": "Có dòng lựa chọn trong lời giải viết khác đề → option_ja chép theo LỜI GIẢI.",
    "thieu_nghia_lua_chon": "Có lựa chọn không có dòng 'Nghĩa:' → meaning = null cho lựa chọn đó.",
    "thieu_ket_luan": "Có lựa chọn không có '→ ĐÚNG / → SAI' → is_match của lựa chọn đó = (index == dap_an_so).",
    "co_sau_ket_luan": "Có câu chữ sau '→ ĐÚNG / SAI' trên cùng dòng → chép câu chữ đó vào CUỐI analysis của lựa chọn (xuống dòng).",
    "cau_hoi_phu_dinh": "Câu hỏi phủ định: is_match vẫn chép theo kết luận của lời giải (→ ĐÚNG = true, → SAI = false), không suy theo đáp án.",
    "ket_luan_lech_dap_an": "Kết luận ĐÚNG / SAI lệch đáp án của đề → vẫn chép is_match theo lời giải; correct.index = dap_an_so.",
    "nhieu_dung": "Nhiều lựa chọn '→ ĐÚNG' → vẫn chép is_match theo lời giải.",
    "chen_tu_nhat": "Câu tiếng Việt có chen từ tiếng Nhật (vd 'Câu này ｜表現《ひょうげん》 rõ rằng…') → bọc ⟪ ⟫ quanh từng cụm Nhật, giữ furigana bên trong: '⟪｜表現《ひょうげん》⟫'.",
    "co_furigana": "Có furigana – chép nguyên ｜chữ《cách đọc》 ở đúng chỗ (câu hỏi, lựa chọn, câu trích, cả trong ⟪ ⟫).",
}


def user_message(norm):
    de = norm["de"]
    payload = {
        "question_id": norm["question_id"], "cau_con": norm["cau_con"], "cap_do": norm["cap_do"],
        "de_bai": {"cau_hoi": de["cau_hoi"], "cac_lua_chon": {str(i + 1): x for i, x in enumerate(de["lua_chon"])},
                   "dap_an_so": de["dap_an_so"]},
        "loi_giai_goc": norm["dau_vao"],
        "luu_y": [h for c, h in FLAG_HINT.items() if c in norm["co"]],
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
    return ("NGỮ CẢNH ĐỀ (chỉ để hiểu – đoạn văn chung cho các câu con của cùng question_id):\n" + json.dumps(ctx, ensure_ascii=False, indent=1) +
            "\n\nJSON LỜI GIẢI (trường dịch từ tiếng Việt: {\"id\": …, \"vi\": …}; trường dịch TRỰC TIẾP từ tiếng Nhật: "
            "{\"id\": …, \"dich_tu_tieng_nhat\": true, \"nguon\": …}):\n"
            + json.dumps(tagged, ensure_ascii=False, indent=1) +
            "\n\nDỊCH CÁC ID SAU (chỉ các id này): " + ", ".join(todo))
