"""Dạng 08 – Lắp ghép câu: nội dung đầu vào cho TÁC TỬ TẠO (Claude A) – thay cho tin nhắn GPT trước đây.

  GĐ1: STATES, FLAG_HINT, user_message(norm)                     → s1_claude_tao.py
  GĐ2: terms_text(glossary), load_tm(cfg), user_message_gd2(…)    → s2_claude_dich.py
"""
import json
import os

import _dang as D
from pipeline_chung.common import load_json

STATES = ("ĐANG_XỬ_LÝ", "LỖI_KỸ_THUẬT")

FLAG_HINT = {
    "nhan_de_bai": "Dòng câu đề có nhãn 'Đề bài:' – question.ja KHÔNG chép nhãn, chỉ chép câu tiếng Nhật (giữ nguyên ＿ ＿ ★ ＿ như lời giải).",
    "de_toan_kana": "Câu đề toàn kana, lời giải không có dòng 'Cách đọc:' – question.reading = null.",
    "khong_cach_doc": "Lời giải không có dòng 'Cách đọc:' của câu đề – question.reading = null.",
    "doc_tu_furigana": "Lời giải không có dòng 'Cách đọc:' – chép ĐÚNG chuỗi 'cach_doc_cau_de_ghep_tu_furigana' vào question.reading.",
    "khong_nghia_de": "Lời giải không có dòng 'Nghĩa:' của câu đề – question.meaning = null.",
    "hoi_thoai": "Đề hội thoại / nhiều dòng – question.ja chép đủ các dòng (giữ \\n).",
    "thieu_phan_de_bai": "Không có phần PHÂN TÍCH ĐỀ BÀI – sentence_analysis = [].",
    "phan_cau_truc_cau": "Phần phân tích đề có tiêu đề 'PHÂN TÍCH CẤU TRÚC CÂU' – đưa vào sentence_analysis như PHÂN TÍCH ĐỀ BÀI.",
    "khong_tieu_de": "Lời giải KHÔNG có tiêu đề phần – tự xác định theo nội dung: ý phân tích đề → sentence_analysis, phân tích từng lựa chọn → options, cụm sắp xếp → arrangement.explanation, Câu hoàn chỉnh → arrangement.full_sentence. Chép nguyên văn, không thêm.",
    "chi_tham_khao": "Lời giải chỉ có phần tham khảo (Python đã tách ra) – các trường phân tích = null / [] (option_ja chép lựa chọn của đề), arrangement.order theo 'thu_tu_python_ghep' nếu có, không thì [1,2,3,4]; full_sentence.ja = câu đề (giữ ô trống), reading/meaning = null.",
    "co_doan_truoc_lua_chon": "Có câu chữ trước lựa chọn '1.' trong PHÂN TÍCH CÁC LỰA CHỌN – nối vào phần tử cuối của sentence_analysis.",
    "so_lua_chon_khac_4": "PHÂN TÍCH CÁC LỰA CHỌN không đủ 4 lựa chọn – lựa chọn thiếu: option_ja chép lựa chọn của đề, gloss/grammar/arrangement = null.",
    "thu_tu_lua_chon_lech": "Số thứ tự trong PHÂN TÍCH CÁC LỰA CHỌN không khớp thứ tự lựa chọn của đề – đặt phân tích theo NỘI DUNG lựa chọn, không theo số.",
    "lua_chon_khac_de": "Có dòng lựa chọn trong lời giải viết khác đề – option_ja chép đúng như LỜI GIẢI.",
    "khong_gloss": "Có lựa chọn không có '(cách đọc - nghĩa)' ở dòng tiêu đề – gloss = null.",
    "thieu_ngu_phap": "Có lựa chọn không có '- Ngữ pháp:' – grammar = null.",
    "thieu_kha_nang_sap_xep": "Có lựa chọn không có '- Khả năng sắp xếp:' – arrangement = null.",
    "lua_chon_dong_la": "Có lựa chọn có câu chữ trước nhãn '- Ngữ pháp:' – đặt câu đó ở đầu grammar (xuống dòng rồi mới tới nội dung Ngữ pháp).",
    "khong_cau_hoan_chinh": "Không có 'Câu hoàn chỉnh' – arrangement.full_sentence.ja = câu đề (giữ ô trống), reading / meaning = null; các câu trong phần sắp xếp vào explanation.",
    "nhieu_cau_hoan_chinh": "Có nhiều 'Câu hoàn chỉnh' – full_sentence.ja = câu số 'cau_hoan_chinh_dung' (Python chọn câu ghép khớp đề); câu còn lại chép NGUYÊN dòng (kể cả nhãn 'Câu hoàn chỉnh 2:') thành một phần tử cuối của arrangement.explanation.",
    "ghep_lech_nhe": "Câu hoàn chỉnh lệch nhẹ so với đề – vẫn chép NGUYÊN như lời giải.",
    "ghep_lech_nang": "Câu hoàn chỉnh khác đề – vẫn chép NGUYÊN như lời giải, không sửa theo đề.",
    "doc_hoan_chinh_ghep": "Lời giải không có 'Cách đọc' của câu hoàn chỉnh – chép ĐÚNG chuỗi 'cach_doc_hoan_chinh_python_ghep' vào arrangement.full_sentence.reading.",
    "khong_doc_hoan_chinh": "Không có 'Cách đọc' của câu hoàn chỉnh – arrangement.full_sentence.reading = null.",
    "hoan_chinh_toan_kana": "Câu hoàn chỉnh toàn kana, không có 'Cách đọc' – arrangement.full_sentence.reading = null.",
    "doc_co_sao": "Cách đọc câu hoàn chỉnh có lẫn ★ – vẫn chép NGUYÊN (tác tử kiểm tra xử lý).",
    "khong_nghia_hoan_chinh": "Không có 'Nghĩa' của câu hoàn chỉnh – arrangement.full_sentence.meaning = null.",
    "co_doan_sau_hoan_chinh": "Có câu chữ sau Câu hoàn chỉnh / Cách đọc / Nghĩa / Vị trí ★ – chép nguyên thành phần tử cuối của arrangement.explanation.",
    "thieu_phan_sap_xep": "Không có phần CÁCH SẮP XẾP – explanation = [], full_sentence.ja = câu đề (giữ ô trống), reading / meaning = null.",
    "lech_dap_an": "LỰA CHỌN ĐÚNG ghi đáp án khác đề – correct.index theo dap_an_so của đề.",
    "lcd_go_nham_so": "LỰA CHỌN ĐÚNG gõ nhầm số – correct.index theo dap_an_so của đề.",
    "khong_so_lcd": "LỰA CHỌN ĐÚNG không ghi số – correct.index theo dap_an_so của đề.",
    "thieu_lua_chon_dung": "Thiếu phần LỰA CHỌN ĐÚNG – correct theo dap_an_so của đề.",
    "lcd_co_nhan_xet": "LỰA CHỌN ĐÚNG có thêm câu chữ – chép nguyên thành phần tử cuối của arrangement.explanation.",
    "co_doan_sau_lcd": "Có đoạn sau LỰA CHỌN ĐÚNG – chép nguyên thành phần tử cuối của arrangement.explanation.",
    "co_furigana": "Có furigana – chép nguyên ｜chữ《cách đọc》 ở đúng chỗ (cả trong câu và trong ⟪ ⟫).",
}


def user_message(norm):
    de, ph = norm["de"], norm.get("phan") or {}
    g = ph.get("ghep") or {}
    payload = {
        "question_id": norm["question_id"], "cau_con": norm["cau_con"], "cap_do": norm["cap_do"],
        "de_bai": {"cau_hoi": de["cau_hoi"], "cac_lua_chon": {str(i + 1): x for i, x in enumerate(de["lua_chon"])},
                   "dap_an_so": de["dap_an_so"]},
        "loi_giai_goc": norm["dau_vao"],
        "thu_tu_python_ghep": g.get("order"),
        "ket_qua_ghep": g.get("trang_thai"),
        "luu_y": [FLAG_HINT[c] for c in norm["co"] if c in FLAG_HINT],
    }
    if g.get("trang_thai") in ("khop", "khop_doc"):
        payload["luu_y"].insert(0, f"arrangement.order = {g['order']} (Python ghép từ 'Câu hoàn chỉnh' của lời giải – dùng đúng thứ tự này).")
    elif g.get("order"):
        payload["luu_y"].insert(0, f"Câu hoàn chỉnh của lời giải lệch đề – arrangement.order = {g['order']} (thứ tự gần nhất Python ghép được).")
    else:
        payload["luu_y"].insert(0, "Python không ghép được câu – arrangement.order theo cụm trong phần CÁCH SẮP XẾP nếu xác định được, không thì [1, 2, 3, 4].")
    if len((ph.get("sap_xep") or {}).get("hoan_chinh") or []) > 1:
        payload["cau_hoan_chinh_dung"] = (g.get("chon") or 0) + 1
    if ph.get("doc_furigana"):
        payload["cach_doc_cau_de_ghep_tu_furigana"] = ph["doc_furigana"]
    if ph.get("doc_hoan_chinh_ghep"):
        payload["cach_doc_hoan_chinh_python_ghep"] = ph["doc_hoan_chinh_ghep"]
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
    ctx = {"cau_hoi": de["cau_hoi"], "cac_lua_chon": {str(i + 1): x for i, x in enumerate(de["lua_chon"])},
           "dap_an_so": de["dap_an_so"]}
    return ("NGỮ CẢNH ĐỀ (chỉ để hiểu):\n" + json.dumps(ctx, ensure_ascii=False, indent=1) +
            "\n\nJSON LỜI GIẢI (trường dịch từ tiếng Việt: {\"id\": …, \"vi\": …}; trường dịch TRỰC TIẾP từ tiếng Nhật: "
            "{\"id\": …, \"dich_tu_tieng_nhat\": true, \"nguon\": …}; trường KẾT HỢP: {\"id\", \"vi\", \"tu_tieng_nhat\", \"luu_y\"}):\n"
            + json.dumps(tagged, ensure_ascii=False, indent=1) +
            "\n\nDỊCH CÁC ID SAU (chỉ các id này): " + ", ".join(todo))
