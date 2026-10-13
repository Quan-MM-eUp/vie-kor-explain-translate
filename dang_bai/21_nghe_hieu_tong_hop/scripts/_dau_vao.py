"""Dạng 21 – Nghe hiểu tổng hợp: nội dung đầu vào cho TÁC TỬ TẠO (Claude A).

  GĐ1: STATES, FLAG_HINT, user_message(norm)                     → s1_claude_tao.py
  GĐ2: terms_text(glossary), load_tm(cfg), user_message_gd2(…)    → s2_claude_dich.py
"""
import json
import os

import _dang as D
from pipeline_chung.common import load_json

STATES = ("ĐANG_XỬ_LÝ", "LỖI_KỸ_THUẬT")

KHUON_HINT = {
    "A": "Khuôn A (bản dịch lời thoại ### phân tích 1–4): ánh xạ đủ options[i].meaning / quotes / analysis / is_match theo lời giải; key_info = null.",
    "B": "Khuôn B ('Thông tin:'): KHÔNG có phân tích từng lựa chọn → options[i].meaning = nghĩa lựa chọn trong danh sách 'Câu N: … 1. … 4. …' CỦA CÂU CON NÀY (bản dịch), "
         "quotes = [], analysis = null, is_match theo dap_an_so; key_info = các dòng của khối 'Thông tin:' (ghép dòng JA ↔ dòng dịch VI tương ứng, speaker như lời thoại) – GIỐNG NHAU ở 2 câu con.",
    "C_vi": "Khuôn C_vi (chỉ có bản dịch): options[i].meaning lấy từ dòng dịch lựa chọn ở cuối bản dịch (nếu có), quotes = [], analysis = null, is_match theo dap_an_so; "
            "question.meaning = dòng 'Câu hỏi: …' (bỏ nhãn); key_info = null.",
}

FLAG_HINT = {
    "chep_loi_thoai": "full_translation = null – câu con 2: Python tự chép full_translation của câu con 1 (KHÔNG tự ghép lại).",
    "loi_thoai_trong": "Không có lời thoại tiếng Nhật dùng được: nếu có bản dịch VI thì full_translation = [{label: null, lines: [{speaker: null, ja: null, meaning: {vi: …}} …]}] (mỗi dòng dịch một phần tử); không có cả bản dịch thì full_translation = null.",
    "loi_thoai_dan_nham": "Cột lời thoại bị dán nhầm phần phân tích – không dùng; xem luu_y 'loi_thoai_trong'.",
    "nhieu_dung": "Lời giải ghi '→ ĐÚNG' ở nhiều lựa chọn – is_match vẫn chép ĐÚNG như lời giải (Python báo, tác tử KIỂM TRA gắn cờ).",
    "lech_dap_an": "Lựa chọn '→ ĐÚNG' của lời giải khác dap_an_so – is_match chép theo lời giải; correct do Python điền theo dap_an_so.",
    "thieu_ket_luan": "Có lựa chọn không có '→ ĐÚNG/SAI' – is_match = (index == dap_an_so).",
    "lua_chon_khac_de": "Có dòng lựa chọn trong phân tích viết khác đề – option_ja chép đúng dòng lựa chọn của LỜI GIẢI (kể cả furigana).",
    "co_mo_dau_phan_tich": "Có đoạn chữ trước lựa chọn 1 trong phần phân tích – schema không có chỗ riêng: đặt nguyên văn vào ĐẦU analysis.vi của lựa chọn 1 (giữ \\n) và nêu trong 'điểm khó'.",
    "trich_ngoai_loi_thoai": "Có câu trích 「…」 không khớp lời thoại (lời giải có thể đã viết đúng chỗ lời thoại gõ sai) – vẫn chép câu trích NGUYÊN như lời giải.",
    "co_furigana": "Có furigana – chép nguyên ｜chữ《cách đọc》 ở đúng chỗ (option_ja, quotes[].ja, ⟪ ⟫ trong analysis); không tự thêm, không bỏ.",
    "khong_cau_hoi": "Python không tìm được câu hỏi tiếng Nhật: nếu lời thoại / lời giải có câu hỏi tiếng Nhật thì chép vào question.ja, không có thì question.ja = null (KHÔNG tự dịch ngược).",
    "bai_2_cau_hoi": "Bài 2 câu hỏi: question / options là của CÂU CON NÀY (cau_con trong đề bài).",
}


def _dong_so(xs, tien_to):
    return [f"{tien_to}{i}: {x}" for i, x in enumerate(xs, 1)]


def user_message(norm):
    de = norm["de"]
    lt = norm.get("loi_thoai") or {}
    phan = norm.get("phan") or {}
    payload = {
        "question_id": norm["question_id"], "cau_con": norm["cau_con"], "cap_do": norm["cap_do"],
        "khuon": norm["khuon_goc"], "huong_dan_khuon": KHUON_HINT.get(norm["khuon_goc"]),
        "de_bai": {"cau_hoi_de_xuat_ja": norm.get("cau_hoi_de_xuat"),
                   "cac_lua_chon": {str(i + 1): x for i, x in enumerate(de["lua_chon"])}, "dap_an_so": de["dap_an_so"]},
    }
    if norm.get("ft_chep_tu"):
        payload["full_translation"] = f"null – Python chép từ câu con 1 ({norm['ft_chep_tu']})"
        payload["loi_thoai_ja_chi_de_hieu"] = lt.get("dong")
    else:
        payload["loi_thoai_ja"] = _dong_so(lt.get("dong") or [], "J")
        payload["ban_dich_vi"] = _dong_so(phan.get("dich_vi") or [], "V")
        payload["cau_hoi_python_da_cat_khoi_loi_thoai"] = lt.get("cau_hoi_cat")
    payload["loi_giai_goc"] = norm["dau_vao"]
    payload["luu_y"] = [FLAG_HINT[c] for c in norm["co"] if c in FLAG_HINT]
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
    ctx = {"cau_con": norm["cau_con"], "loi_thoai_ja": (norm.get("loi_thoai") or {}).get("dong"),
           "cac_lua_chon": {str(i + 1): x for i, x in enumerate(de["lua_chon"])}, "dap_an_so": de["dap_an_so"]}
    return ("NGỮ CẢNH ĐỀ (chỉ để hiểu):\n" + json.dumps(ctx, ensure_ascii=False, indent=1) +
            "\n\nJSON LỜI GIẢI (trường dịch từ tiếng Việt: {\"id\": …, \"vi\": …}; trường dịch TRỰC TIẾP từ tiếng Nhật: "
            "{\"id\": …, \"dich_tu_tieng_nhat\": true, \"nguon\": …}; trường đã điền sẵn (không dịch) giữ nguyên dạng {\"id\", \"vi\"} nhưng KHÔNG có trong danh sách id):\n"
            + json.dumps(tagged, ensure_ascii=False, indent=1) +
            "\n\nDỊCH CÁC ID SAU (chỉ các id này): " + ", ".join(todo))
