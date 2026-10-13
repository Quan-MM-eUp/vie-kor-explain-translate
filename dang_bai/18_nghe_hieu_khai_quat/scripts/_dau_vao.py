"""Dạng 18 – Nghe hiểu khái quát: nội dung đầu vào cho TÁC TỬ TẠO (Claude A).

  GĐ1: STATES, FLAG_HINT, user_message(norm)                     → s1_claude_tao.py
  GĐ2: terms_text(glossary), load_tm(cfg), user_message_gd2(…)    → s2_claude_dich.py
Tác tử TẠO nhận lời thoại đã tách dòng (L1…Ln + người nói), câu hỏi + 4 lựa chọn tiếng Nhật, lời giải gốc đã chuẩn hóa và lưu ý theo cờ s0.
"""
import json
import os

import _dang as D
from pipeline_chung.common import load_json

STATES = ("ĐANG_XỬ_LÝ", "LỖI_KỸ_THUẬT")

FLAG_HINT = {
    "khuon_C": "Lời giải không có dòng '###' – phần trước dòng '1.' là bản dịch + câu hỏi tiếng Việt, từ dòng '1.' là phân tích.",
    "khuon_D": "KHUÔN D – lời giải chỉ có bản dịch lời thoại + câu hỏi + 4 lựa chọn tiếng Việt (4 dòng cuối), KHÔNG phân tích: "
               "options[i].option_ja = lựa chọn tiếng Nhật trong 'lua_chon_ja'; meaning.vi = dòng lựa chọn tiếng Việt thứ i ('lua_chon_tieng_viet'); "
               "quotes = [], analysis = null, is_match = (index == dap_an_so).",
    "khuon_E": "KHUÔN E – lời giải KHÔNG có tiếng Việt (chỉ chép lại lời thoại Nhật): mọi meaning = null (full_translation, question, options); "
               "option_ja theo 'lua_chon_ja'; quotes = [], analysis = null, is_match = (index == dap_an_so). KHÔNG tự dịch.",
    "khong_ban_dich": "Lời giải không có bản dịch lời thoại – mọi full_translation[0].lines[k].meaning = null (không tự dịch).",
    "so_dong_dich_lech": "Số dòng bản dịch Việt khác số dòng lời thoại – ghép THEO NGHĨA: một câu dịch gộp 2 lượt thoại thì tách câu Việt ra đúng chỗ "
                         "(chỉ cắt, không viết lại); lượt thoại không có câu dịch tương ứng → meaning = null; câu dịch thừa không ứng với dòng nào → "
                         "ghép vào dòng gần nhất có cùng nội dung (ghi trong báo cáo điểm khó).",
    "cau_hoi_vi_la": "Không tìm thấy dòng câu hỏi tiếng Việt rõ ràng ở cuối phần dịch – tìm trong lời giải; không có thì question.meaning = null.",
    "nhan_cau_hoi_vi": "Dòng câu hỏi tiếng Việt có nhãn 'Câu hỏi:' – question.meaning không chép nhãn.",
    "loi_thoai_khong_cau_hoi": "Lời thoại không chép câu hỏi + lựa chọn – question.ja = 'cau_hoi_ja' (lấy từ cột câu hỏi của đề).",
    "lua_chon_lech": "Dòng lựa chọn trong lời giải khác lựa chọn trong lời thoại – option_ja vẫn chép theo dòng 'n. …' của LỜI GIẢI (giữ furigana).",
    "tach_lua_chon_la": "Phân tích có dòng đánh số lạ (vd '4.5 …' trong nội dung) – xác định đúng 4 khối lựa chọn theo nội dung, không theo mọi dòng có số.",
    "thieu_ket_luan": "Có lựa chọn không ghi '→ ĐÚNG / → SAI' – is_match = (index == dap_an_so).",
    "nhieu_ket_luan": "Có lựa chọn ghi '→ ĐÚNG/SAI' nhiều lần – is_match theo kết luận CUỐI; mọi câu chữ khác vẫn vào analysis.",
    "lech_dap_an": "Lời giải ghi '→ ĐÚNG' ở lựa chọn khác dap_an_so – is_match vẫn chép đúng như LỜI GIẢI (→ ĐÚNG = true); correct.index = dap_an_so. Ghi vào báo cáo điểm khó.",
    "nhieu_dung": "Lời giải ghi '→ ĐÚNG' ở nhiều lựa chọn – is_match chép đúng như lời giải; correct.index = dap_an_so. Ghi vào báo cáo điểm khó.",
    "chen_tu_nhat": "Câu tiếng Việt có chen từ / câu tiếng Nhật (ngoài câu trích 「 」 đứng riêng) – bọc ⟪ ⟫, giữ furigana bên trong ⟪ ⟫.",
    "co_mo_dau_phan_tich": "Có đoạn chữ sau ### trước lựa chọn 1 – nối vào ĐẦU options[0].analysis (giữ \\n).",
    "sau_lua_chon": "Lời thoại có dòng sau 4 lựa chọn – KHÔNG đưa vào JSON.",
    "nguon_doan_van": "Lời thoại lấy từ cột doan_van (transcript_vi dán nhầm) – vẫn dùng đúng L1…Ln ở đây.",
    "co_furigana": "Có furigana – chép nguyên ｜chữ《cách đọc》 ở đúng chỗ (option_ja, quotes[].ja, ⟪ ⟫); không tự thêm, không bỏ.",
}


def user_message(norm):
    de, ph = norm["de"], norm.get("phan") or {}
    payload = {
        "question_id": norm["question_id"], "cau_con": norm["cau_con"], "cap_do": norm["cap_do"], "khuon": norm["khuon_goc"],
        "loi_thoai": [{"so": d["so"], "speaker": d["speaker"], "ja": d["ja"]} for d in norm["loi_thoai"]["dong"]],
        "cau_hoi_ja": de.get("cau_hoi"),
        "lua_chon_ja": {str(i + 1): x for i, x in enumerate(de.get("lua_chon") or [])},
        "dap_an_so": de["dap_an_so"],
        "loi_giai_goc": norm.get("dau_vao"),
        "luu_y": [FLAG_HINT[c] for c in norm["co"] if c in FLAG_HINT],
    }
    if norm["khuon_goc"] == "D" and ph.get("lua_chon_vi"):
        payload["lua_chon_tieng_viet"] = {str(i + 1): x for i, x in enumerate(ph["lua_chon_vi"])}
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
    ctx = {"loi_thoai_tieng_nhat": norm.get("doan_van"), "dap_an_so": de["dap_an_so"]}
    return ("NGỮ CẢNH (lời thoại đầy đủ – để hiểu quan hệ người nói / sắc thái; KHÔNG dịch ngữ cảnh, chỉ dịch các id):\n"
            + json.dumps(ctx, ensure_ascii=False, indent=1) +
            "\n\nJSON LỜI GIẢI (trường dịch từ tiếng Việt: {\"id\": …, \"vi\": …}; trường dịch TRỰC TIẾP từ tiếng Nhật: "
            "{\"id\": …, \"dich_tu_tieng_nhat\": true, \"nguon\": …}):\n" + json.dumps(tagged, ensure_ascii=False, indent=1) +
            "\n\nDỊCH CÁC ID SAU (chỉ các id này): " + ", ".join(todo))
