"""Dạng 15 – Đọc hiểu: Tìm thông tin: nội dung đầu vào cho TÁC TỬ TẠO (Claude A).

  GĐ1: STATES, FLAG_HINT, user_message(norm)                     → s1_claude_tao.py
  GĐ2: terms_text(glossary), load_tm(cfg), user_message_gd2(…)    → s2_claude_dich.py
Tác tử TẠO nhận NGỮ LIỆU đã trải bảng (chỉ để hiểu – không chép vào JSON) + đề + lời giải đã chuẩn hóa + gợi ý tách của Python.
"""
import json
import os

import _dang as D
from pipeline_chung.common import load_json

STATES = ("ĐANG_XỬ_LÝ", "LỖI_KỸ_THUẬT")

FLAG_HINT = {
    "khuon_la": "Khuôn lời giải LẠ (không phân tích đủ 4 lựa chọn với → ĐÚNG/SAI). Chép phần có được vào trường gần nhất (mục 'Khuôn lạ' của s1_chuyen_json.md); trường không có nội dung để null / []; không tự viết phân tích.",
    "co_phan_dau": "Có chữ ở phần đầu lời giải (sau câu hỏi, trước lựa chọn 1): bản dịch ngữ liệu → full_translation; tóm tắt / liệt kê thông tin ('Từ đoạn văn: - …') → summary. Chép nguyên văn, giữ \\n.",
    "co_ban_dich": "Phần đầu lời giải là BẢN DỊCH ngữ liệu (dài) → full_translation = [{label: null, lines: [{speaker: null, ja: null, meaning: {vi: <toàn bộ bản dịch, giữ \\n>}}]}].",
    "khong_cau_hoi_ja": "Lời giải KHÔNG có dòng câu hỏi tiếng Nhật ở đầu → question.ja = null (không chép câu hỏi của đề); dòng 'Câu hỏi: <tiếng Việt>' (nếu có) → question.meaning.",
    "cau_hoi_lech": "Dòng câu hỏi trong lời giải viết khác đề – question.ja vẫn chép NGUYÊN như lời giải.",
    "lua_chon_lech": "Có dòng lựa chọn trong lời giải viết khác đề – option_ja chép NGUYÊN như dòng 'k.' của lời giải (nếu dòng đó là tiếng Nhật); dòng 'k.' là tiếng Việt → option_ja = lựa chọn của đề, chữ tiếng Việt của dòng đó vào meaning (nếu là bản dịch lựa chọn) hoặc analysis.",
    "lua_chon_la_tranh": "Lựa chọn của đề chỉ là số 1–4 (chọn tranh / hình): option_ja = số của đề ('1'…'4'); mô tả tranh trong lời giải (kể cả câu tiếng Nhật) → analysis (tiếng Nhật bọc ⟪ ⟫), không vào quotes trừ khi lời giải ghi rõ là trích ngữ liệu.",
    "lua_chon_de_hong": "Lựa chọn của đề bị đổi thành ngày giờ kiểu Excel – option_ja vẫn chép như dòng 'k.' của lời giải.",
    "so_lua_chon_khac_4": "Lời giải không có đủ 4 khối lựa chọn – lựa chọn thiếu: option_ja = lựa chọn của đề, meaning = null, quotes = [], analysis = null; is_match = (index == dap_an_so).",
    "lech_dap_an": "Lời giải chấm ĐÚNG lựa chọn khác dap_an_so. is_match theo ĐÚNG lời giải nói; correct.index vẫn = dap_an_so. Không sửa – ghi vào báo cáo điểm khó.",
    "nhieu_dung": "Lời giải chấm ĐÚNG nhiều lựa chọn – is_match theo đúng lời giải; correct.index = dap_an_so.",
    "dap_an_de_loi": "dap_an_so của đề không phải 1–4 → correct.index = số lời giải chấm ĐÚNG; ghi rõ trong báo cáo điểm khó.",
    "trich_dan_ngoai_ngu_lieu": "Có câu trích tiếng Nhật Python không tìm thấy trong ngữ liệu – VẪN chép nguyên văn như lời giải vào quotes (không sửa theo ngữ liệu).",
    "trich_dan_tieng_viet": "Có 'trích dẫn' chỉ bằng tiếng Việt (từ bản dịch) – để nguyên trong analysis, KHÔNG đưa vào quotes (quotes[].ja phải là tiếng Nhật).",
    "co_tinh_toan": "Lời giải có phép tính – chép NGUYÊN các dòng tính vào analysis (giữ \\n, gạch đầu dòng, số, ×, ÷); không tự tính lại / sửa kết quả.",
    "tinh_toan_sai": "Python thấy phép tính trong lời giải sai – vẫn chép nguyên (tác tử KIỂM TRA xử lý).",
    "thieu_ngu_lieu": "Ngữ liệu RỖNG trong dữ liệu – chỉ dựa vào lời giải.",
    "ngu_lieu_anh": "Ngữ liệu có ảnh (Python không đọc được) – chỉ dựa vào lời giải.",
    "chen_tu_nhat": "Câu tiếng Việt có chen từ / câu tiếng Nhật – bọc ⟪ ⟫ (kể cả số + chữ Nhật như ⟪3回⟫, ⟪600円⟫ khi chen trong câu Việt).",
    "markdown": "Python đã bỏ ký hiệu markdown (** / #) – không thêm lại.",
    "co_furigana": "Có furigana – chép nguyên ｜chữ《cách đọc》 ở đúng chỗ (cả trong option_ja, quotes[].ja và trong ⟪ ⟫); không tự thêm, không bỏ.",
}


def goi_y_tach(norm):
    """Gợi ý tách của Python (để tác tử TẠO đối chiếu – lời giải gốc mới là chuẩn)."""
    ph = norm.get("phan") or {}
    return {"khuon": ph.get("khuon"), "cau_hoi_ja": ph.get("cau_hoi_ja"), "cau_hoi_vi": ph.get("cau_hoi_vi"),
            "co_phan_dau": bool((ph.get("dau_khac") or "").strip()),
            "lua_chon": [{"so": o["so"], "dong_lua_chon": o.get("dong_so"), "la_tieng_nhat": o.get("ja") is not None,
                          "ket_luan": {True: "ĐÚNG", False: "SAI", None: None}[o.get("ket_luan")]} for o in ph.get("lua_chon") or []],
            "chu_sau_ket_luan_cuoi": ph.get("sau") or None}


def user_message(norm):
    de = norm["de"]
    payload = {
        "question_id": norm["question_id"], "cau_con": norm["cau_con"], "cap_do": norm["cap_do"],
        "ngu_lieu_chi_de_hieu": D.ngu_lieu_text(norm, 12000),
        "de_bai": {"cau_hoi": de["cau_hoi"], "cac_lua_chon": {str(i + 1): x for i, x in enumerate(de["lua_chon"])}, "dap_an_so": de["dap_an_so"]},
        "loi_giai_goc": norm["dau_vao"],
        "goi_y_tach_cua_python": goi_y_tach(norm),
        "luu_y": [FLAG_HINT[c] for c in norm["co"] if c in FLAG_HINT],
    }
    return "Chuyển lời giải sau sang JSON theo schema reading_listening.v1.\n\n" + json.dumps(payload, ensure_ascii=False, indent=1)


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
    ctx = {"ngu_lieu_khong_dich": D.ngu_lieu_text(norm, 8000), "cau_hoi": de["cau_hoi"],
           "cac_lua_chon": {str(i + 1): x for i, x in enumerate(de["lua_chon"])}, "dap_an_so": de["dap_an_so"]}
    return ("NGỮ CẢNH ĐỀ (chỉ để hiểu – ngữ liệu KHÔNG dịch):\n" + json.dumps(ctx, ensure_ascii=False, indent=1) +
            "\n\nJSON LỜI GIẢI (trường dịch từ tiếng Việt: {\"id\": …, \"vi\": …}; trường dịch TRỰC TIẾP từ tiếng Nhật: "
            "{\"id\": …, \"dich_tu_tieng_nhat\": true, \"cau_tieng_nhat\": …, \"ban_viet_tham_khao\": …, \"luu_y\": …}):\n"
            + json.dumps(tagged, ensure_ascii=False, indent=1) + "\n\nDỊCH CÁC ID SAU (chỉ các id này): " + ", ".join(todo))
