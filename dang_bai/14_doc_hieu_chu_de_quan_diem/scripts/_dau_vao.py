"""Dạng 14 – Đọc hiểu chủ đề / quan điểm: nội dung đầu vào cho TÁC TỬ TẠO (Claude A).

  GĐ1: STATES, FLAG_HINT, user_message(norm)                     → s1_claude_tao.py
  GĐ2: terms_text(glossary), load_tm(cfg), user_message_gd2(…)    → s2_claude_dich.py
Tác tử TẠO nhận: đoạn văn (chỉ để hiểu – không chép vào JSON), loại câu hỏi, đề, khuôn lời giải, chế độ (chép / tạo mới), lời giải gốc, lưu ý.
"""
import json
import os

import _dang as D
from pipeline_chung.common import load_json

STATES = ("ĐANG_XỬ_LÝ", "LỖI_KỸ_THUẬT")

FLAG_HINT = {
    "chuan_A": "Khuôn chuẩn kiểu A: 'Nghĩa:' → options[i].meaning; 'Trích dẫn:' + 「…」 + (dịch) → options[i].quotes; 'Giải thích:' → options[i].analysis (bỏ nhãn); '→ ĐÚNG/SAI' → is_match.",
    "chuan_B": "Khuôn chuẩn kiểu B (gạch đầu dòng): '- Đoạn văn có câu: 「…」 (dịch)' → quotes (bỏ nhãn dẫn thuần); các dòng '- <nhận xét>' → analysis (bỏ '- ' đầu dòng, mỗi ý một dòng \\n).",
    "khuon_la": "KHUÔN LẠ – lời giải không có phân tích đủ 4 lựa chọn → làm theo mục 'Khuôn lạ – TẠO MỚI' của prompts/s1_chuyen_json.md.",
    "co_dich_doan": "Lời giải có bản dịch ĐOẠN VĂN ('Đoạn văn:' …) → full_translation = [{label: null, lines: [ {speaker: null, ja: null, meaning: {vi: <đoạn>}} … ]}] – mỗi đoạn văn (cách nhau dòng trống) một line, kể cả khối 'Chú thích:'; chép nguyên văn.",
    "nhieu_dung": "Lời giải chấm '→ ĐÚNG' cho số lựa chọn ≠ 1 – is_match vẫn chép ĐÚNG như lời giải (không tự sửa); correct.index theo dap_an_so.",
    "lech_dap_an": "Lựa chọn '→ ĐÚNG' của lời giải khác dap_an_so – is_match chép như lời giải; correct.index theo dap_an_so (tác tử KIỂM TRA xử lý).",
    "thieu_nghia_lc": "Có lựa chọn không có dòng 'Nghĩa:' – meaning = null (không tự dịch).",
    "lc_khac_de": "Dòng lựa chọn trong lời giải khác đề – option_ja chép đúng như LỜI GIẢI.",
    "cau_hoi_khac_de": "Dòng câu hỏi trong lời giải khác đề – question.ja chép đúng như LỜI GIẢI.",
    "trich_ngoai_doan": "Có câu trích không khớp đoạn văn – vẫn chép NGUYÊN như lời giải (không sửa theo đoạn văn).",
    "trich_khong_dich": "Có câu trích không kèm '(dịch)' – quotes[].meaning = null.",
    "chen_tu_nhat": "Câu tiếng Việt có chen từ tiếng Nhật (kể cả từ có furigana ｜…《…》 đứng giữa câu Việt) – giữ nguyên, bọc ⟪ ⟫ quanh từng cụm.",
    "dong_lap": "Lời giải có dòng lặp lại liền nhau – vẫn chép nguyên (tác tử KIỂM TRA xử lý).",
    "co_sau_dap_an": "Có chữ sau '→ ĐÚNG/SAI' của lựa chọn 4 – nối vào cuối options[3].analysis.",
    "co_furigana": "Có furigana – chép nguyên ｜chữ《cách đọc》 ở đúng chỗ (trong option_ja, quotes, question.ja và trong ⟪ ⟫); không thêm, không bỏ.",
    "furigana_chu_viet": "Python đã bỏ furigana gắn lên chữ tiếng Việt – chép như lời giải đã chuẩn hóa.",
}


def _loai(norm):
    k = norm.get("loai_cau_hoi")
    return {"ma": k, "mo_ta": D.DH.LOAI_CAU_HOI.get(k)}


def user_message(norm):
    de = norm["de"]
    la = D.la_khuon_la(norm)
    payload = {
        "question_id": norm["question_id"], "cau_con": norm["cau_con"], "cap_do": norm["cap_do"],
        "loai_cau_hoi": _loai(norm),
        "doan_van_chi_de_hieu": norm.get("doan_van"),
        "de_bai": {"cau_hoi": de["cau_hoi"], "cac_lua_chon": {str(i + 1): x for i, x in enumerate(de["lua_chon"])},
                   "dap_an_so": de["dap_an_so"]},
        "khuon_loi_giai": norm["khuon_goc"],
        "che_do": "tao_moi" if la else "chep_nguyen_van",
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
    ctx = {"doan_van_khong_dich": norm.get("doan_van"), "cau_hoi": de["cau_hoi"],
           "cac_lua_chon": {str(i + 1): x for i, x in enumerate(de["lua_chon"])}, "dap_an_so": de["dap_an_so"],
           "loai_cau_hoi": _loai(norm)}
    return ("NGỮ CẢNH ĐỀ (chỉ để hiểu – đoạn văn KHÔNG dịch):\n" + json.dumps(ctx, ensure_ascii=False, indent=1) +
            "\n\nJSON LỜI GIẢI (trường dịch từ tiếng Việt: {\"id\": …, \"vi\": …}; trường dịch TRỰC TIẾP từ tiếng Nhật: "
            "{\"id\": …, \"dich_tu_tieng_nhat\": true, \"nguon\": …}):\n" + json.dumps(tagged, ensure_ascii=False, indent=1) +
            "\n\nDỊCH CÁC ID SAU (chỉ các id này): " + ", ".join(todo))
