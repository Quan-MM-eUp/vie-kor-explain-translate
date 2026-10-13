"""Dạng 09 – Ngữ pháp theo đoạn văn: nội dung đầu vào cho TÁC TỬ TẠO (Claude A) – thay cho tin nhắn GPT.

  GĐ1: STATES, FLAG_HINT, user_message(norm)                     → s1_claude_tao.py
  GĐ2: terms_text(glossary), load_tm(cfg), user_message_gd2(…)    → s2_claude_dich.py
Khác dạng 07: tác tử TẠO nhận thêm ĐOẠN VĂN (chỉ để hiểu ngữ cảnh – không chép vào JSON) và nhãn chỗ trống của câu.
"""
import json
import os

import _dang as D
from pipeline_chung.common import load_json

STATES = ("ĐANG_XỬ_LÝ", "LỖI_KỸ_THUẬT")

FLAG_HINT = {
    "doc_tu_furigana": "Lời giải không có dòng 'Cách đọc:' của câu đề – chép ĐÚNG chuỗi 'cach_doc_ghep_tu_furigana' (dưới đây) vào question.reading.",
    "khong_cach_doc": "Lời giải không có dòng 'Cách đọc:' của câu đề – question.reading = null (không tự ghép).",
    "khong_nghia_de": "Lời giải không có dòng 'Nghĩa:' của câu đề – question.meaning = null.",
    "nhan_de_bai": "Dòng câu đề trong lời giải có nhãn 'Đề bài:' ở đầu – question.ja KHÔNG chép nhãn này, chỉ chép câu tiếng Nhật.",
    "hoi_thoai": "Đề hội thoại / nhiều dòng – question.ja chép đủ các dòng (giữ \\n); applied.ja chép đúng như lời giải (có khi chỉ là dòng có chỗ trống).",
    "hai_cho_trong": "Câu có 2 chỗ trống a / b (vd '[2]−a＿＿＿ … [2]−ｂ＿＿＿'), lựa chọn dạng 'a.X／ｂ.Y' – option_ja chép nguyên như lời giải; applied.ja chép đúng như lời giải.",
    "co_cau_truc_chung": "PHÂN TÍCH có đoạn trước lựa chọn '1.' (Cấu trúc chung) – đưa nguyên vào analysis.intro, giữ \\n.",
    "y_nghia_la_nghia_cau": "Có lựa chọn ghi nghĩa của câu áp dụng bằng nhãn '- Ý nghĩa:' thứ hai (sau '- Áp dụng vào câu:') – dòng đó vào applied.meaning, không nối vào meaning.",
    "so_dong_pt_khac_4": "Phần PHÂN TÍCH không có đúng 4 lựa chọn đánh số – lựa chọn không có phân tích: option_ja chép lựa chọn của đề, các trường khác = null.",
    "thu_tu_pt_lech": "Số thứ tự trong PHÂN TÍCH không khớp thứ tự lựa chọn của đề – đặt phân tích theo nội dung lựa chọn, không theo số.",
    "lua_chon_khac_de": "Có dòng lựa chọn trong PHÂN TÍCH viết khác đề – option_ja vẫn chép đúng như LỜI GIẢI.",
    "ap_dung_lech_nhe": "Có câu 'Áp dụng vào câu' lệch 1–2 ký tự so với đề – vẫn chép NGUYÊN như lời giải (Claude xử lý sau).",
    "ap_dung_lech_nang": "Có câu 'Áp dụng vào câu' khác câu đề đã điền lựa chọn – vẫn chép NGUYÊN như lời giải, không sửa theo đề.",
    "hoan_chinh_khac_de": "'Câu hoàn chỉnh' khác câu đề – full_sentence.ja vẫn chép NGUYÊN như lời giải.",
    "thieu_danh_gia_ngu_phap": "Có lựa chọn không có dòng '+ Về ngữ pháp' – grammar_ok = null, grammar_note = null.",
    "thieu_ap_dung": "Có lựa chọn không có '- Áp dụng vào câu' – applied = null.",
    "danh_gia_khong_ro": "Có dòng 'Về ngữ pháp' / 'Về ngữ nghĩa' không có chữ Đúng/Sai/Phù hợp/Không phù hợp rõ ràng (hoặc viết ở dòng sau) – suy theo chữ đánh giá nếu có; không có thì để null và chép toàn bộ câu vào note.",
    "nhan_lap": "Có lựa chọn với nhãn lặp (2 dòng 'Nghĩa:' …) – dòng đầu vào trường, dòng thừa nối vào note của phần đang mở.",
    "lcd_go_nham_so": "LỰA CHỌN ĐÚNG ghi nhầm số (vd '5.') – correct.index theo dap_an_so của đề.",
    "lech_dap_an": "Số trong LỰA CHỌN ĐÚNG khác đáp án của đề – correct.index theo dap_an_so của đề.",
    "khong_so_lcd": "LỰA CHỌN ĐÚNG không ghi số – correct.index theo dap_an_so của đề.",
    "lcd_co_nhan_xet": "LỰA CHỌN ĐÚNG có câu chữ ngoài số / Câu hoàn chỉnh / Nghĩa – chép nguyên vào correct.note.",
    "thieu_phan_tich": "Thiếu phần PHÂN TÍCH – option_ja chép lựa chọn của đề, các trường khác của lựa chọn = null.",
    "thieu_lua_chon_dung": "Thiếu phần LỰA CHỌN ĐÚNG – correct.option_ja theo đáp án của đề, full_sentence.ja = câu áp dụng của đáp án (nếu có), meaning = null.",
    "co_doan_sau_lcd": "Có đoạn không tiêu đề sau LỰA CHỌN ĐÚNG – nối vào correct.note.",
    "thieu_dau_phan_cach": "Có tiêu đề phần dính vào cuối phần trước (thiếu ###) – vẫn tách theo tiêu đề.",
    "co_furigana": "Có furigana – chép nguyên ｜chữ《cách đọc》 ở đúng chỗ (cả trong câu và trong ⟪ ⟫); không tự thêm, không bỏ.",
}

FLAG_HINT.update({
    "lien_dong": "Lời giải gốc viết liền một dòng – Python đã xuống dòng trước các nhãn; vẫn chép nội dung nguyên văn.",
    "nhan_in_dam": "Nhãn in đậm ({ĐỀ BÀI} / {NGHĨA}) đã được Python bỏ { } – không chép nhãn.",
    "de_lech_doan_van_nhe": "Câu đề trong lời giải lệch nhẹ đoạn văn gốc – vẫn chép question.ja NGUYÊN như lời giải (không sửa theo đoạn văn).",
    "de_lech_doan_van_nang": "Câu đề trong lời giải khác đoạn văn gốc – vẫn chép question.ja NGUYÊN như lời giải (không sửa theo đoạn văn).",
    "de_khong_tim_thay_doan_van": "Không tìm thấy câu đề trong đoạn văn – vẫn chép question.ja nguyên như lời giải.",
    "dap_an_de_loi": "NGOẠI LỆ với quy tắc correct.index = dap_an_so: dữ liệu đề lỗi (dap_an_so không phải 1–4) → correct.index = số ở LỰA CHỌN ĐÚNG của lời giải; ghi rõ trong báo cáo điểm khó.",
})


def user_message(norm):
    de = norm["de"]
    payload = {
        "question_id": norm["question_id"], "cau_con": norm["cau_con"], "cap_do": norm["cap_do"],
        "doan_van_chi_de_hieu": norm.get("doan_van"),
        "de_bai": {"cho_trong_cua_cau_nay": D.nhan_cho_trong(norm),
                   "cac_lua_chon": {str(i + 1): x for i, x in enumerate(de["lua_chon"])},
                   "dap_an_so": de["dap_an_so"]},
        "loi_giai_goc": norm["dau_vao"],
        "luu_y": [FLAG_HINT[c] for c in norm["co"] if c in FLAG_HINT],
    }
    if (norm.get("phan") or {}).get("doc_furigana"):
        payload["cach_doc_ghep_tu_furigana"] = norm["phan"]["doc_furigana"]
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
    ctx = {"doan_van": norm.get("doan_van"), "cho_trong_cua_cau_nay": D.nhan_cho_trong(norm),
           "cac_lua_chon": {str(i + 1): x for i, x in enumerate(de["lua_chon"])}, "dap_an_so": de["dap_an_so"]}
    return ("NGỮ CẢNH ĐỀ (chỉ để hiểu – đoạn văn KHÔNG dịch):\n" + json.dumps(ctx, ensure_ascii=False, indent=1) +
            "\n\nJSON LỜI GIẢI (trường dịch từ tiếng Việt: {\"id\": …, \"vi\": …}; trường dịch TRỰC TIẾP từ tiếng Nhật: "
            "{\"id\": …, \"dich_tu_tieng_nhat\": true, \"nguon\": …}):\n" + json.dumps(tagged, ensure_ascii=False, indent=1) +
            "\n\nDỊCH CÁC ID SAU (chỉ các id này): " + ", ".join(todo))
