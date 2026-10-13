"""Dạng 20 – Nghe hiểu: Trả lời nhanh: nội dung đầu vào cho TÁC TỬ TẠO (Claude A).

  GĐ1: STATES, FLAG_HINT, user_message(norm)                     → s1_claude_tao.py
  GĐ2: terms_text(glossary), load_tm(cfg), user_message_gd2(…)    → s2_claude_dich.py
Tác tử TẠO nhận: script đã tách (câu nói + các câu trả lời – để hiểu ngữ cảnh; khuôn C thì chép câu trả lời vào sentence.ja),
lời giải đã chuẩn hóa, dap_an_so, dòng dịch câu nói Python đã bỏ nhãn người nói, các lưu ý theo cờ s0.
prompt.utterance.ja / reading do Python điền khi --nhan – tác tử TẠO KHÔNG sinh.
"""
import json
import os

import _dang as D
from pipeline_chung.common import load_json

STATES = ("ĐANG_XỬ_LÝ", "LỖI_KỸ_THUẬT")

FLAG_HINT = {
    "khuon_A": "Khuôn chuẩn: phần trước ### = dịch câu nói + dịch các lựa chọn (TRÙNG LẶP với 'Nghĩa:' – KHÔNG chép phần dịch lựa chọn này); sau ### = khối từng lựa chọn.",
    "khuon_B": "Không có ###: chỉ có khối từng lựa chọn – không có dòng dịch câu nói → prompt.utterance.meaning = null (trừ khi có dòng 'Nghĩa:' của câu hỏi trước lựa chọn 1 – khi đó dùng dòng đó).",
    "khuon_C": "Lời giải CHỈ có bản dịch: dòng đầu = dịch câu nói, các dòng sau = dịch từng câu trả lời. sentence.ja = câu trả lời tương ứng trong 'script.lua_chon' (chép nguyên), sentence.meaning = dòng dịch tương ứng, is_correct = true ở lựa chọn dap_an_so (false ở các lựa chọn khác), analysis = null.",
    "khuon_D": "Lời giải không theo khuôn chuẩn – đọc kỹ, đặt từng phần vào trường gần nhất: dịch câu nói → utterance.meaning; nhận xét về câu nói → prompt.analysis[]; mỗi lựa chọn: câu Nhật → sentence.ja (lời giải không có thì chép từ script), dịch → sentence.meaning, Đúng/Sai → is_correct, phần còn lại → analysis. Chép nguyên văn, không thêm.",
    "co_nhan_nguoi_noi": "Dòng dịch câu nói có nhãn người nói ('Nam:', 'Nữ:', 'F:', 'Người phụ nữ:' …) – utterance.meaning KHÔNG chép nhãn (dùng 'cau_noi_vi_python_tach').",
    "nhieu_dong_cau_noi": "Câu nói được dịch thành nhiều dòng – utterance.meaning giữ nguyên các dòng, nối bằng \\n.",
    "khong_dich_cau_noi": "Lời giải không có dòng dịch câu nói – utterance.meaning = null.",
    "dich_lap_lech": "Bản dịch lựa chọn ở phần trước ### khác dòng 'Nghĩa:' – sentence.meaning chép theo dòng 'Nghĩa:' (bỏ qua phần trước ###).",
    "chen_tu_nhat_dich": "Bản dịch còn chen chữ Nhật (vd '店 này') – chép NGUYÊN, bọc ⟪ ⟫ quanh chữ Nhật (kể cả furigana); KHÔNG tự dịch thay.",
    "co_doan_sau_dich": "Phần trước ### có câu chữ sau các dòng dịch lựa chọn – chép nguyên thành phần tử của prompt.analysis[] (mỗi dòng một phần tử).",
    "co_doan_truoc_khoi": "Sau ### có câu chữ trước lựa chọn 1 – chép nguyên thành phần tử của prompt.analysis[].",
    "thieu_ket_luan": "Có lựa chọn không có dòng '→ ĐÚNG/SAI' – is_correct theo dap_an_so (đúng ở lựa chọn dap_an_so).",
    "nhieu_dung": "Lời giải chấm số lựa chọn ĐÚNG khác 1 – is_correct chép đúng như lời giải (tác tử KIỂM TRA xử lý).",
    "lech_dap_an": "Lời giải chấm ĐÚNG ở lựa chọn khác dap_an_so – is_correct chép như lời giải; correct.index = dap_an_so.",
    "thieu_phan_tich": "Có lựa chọn không có phân tích – analysis = null.",
    "thieu_cau_nhat": "Có khối lựa chọn không có câu tiếng Nhật (chỉ '1.') – sentence.ja = câu trả lời tương ứng trong 'script.lua_chon'; script không có thì \"\".",
    "lech_script": "Câu Nhật trong lời giải hơi khác script – sentence.ja chép theo LỜI GIẢI (không sửa theo script).",
    "script_khong_tach": "Python không tách được script – không cần utterance.ja (Python điền null).",
    "lua_chon_thua": "Đề ghi 4 cột lựa chọn nhưng thực tế chỉ có 3 – options gồm 3 lựa chọn.",
    "furigana_phan_tich": "Phân tích có chữ Nhật kèm furigana – bọc ⟪ ⟫ quanh cả cụm, giữ ｜chữ《cách đọc》 bên trong.",
    "co_furigana": "Có furigana – chép nguyên ｜chữ《cách đọc》 ở đúng chỗ (câu Nhật của lựa chọn, và trong ⟪ ⟫ ở câu Việt).",
}


def user_message(norm):
    ph = norm.get("phan") or {}
    sc, d = ph.get("script") or {}, ph.get("dich") or {}
    payload = {
        "question_id": norm["question_id"], "cau_con": norm["cau_con"], "cap_do": norm["cap_do"],
        "khuon": ph.get("khuon"), "so_lua_chon": ph.get("so_lua_chon"), "dap_an_so": norm["de"]["dap_an_so"],
        "script": {"cau_noi": sc.get("cau_noi"), "lua_chon": {str(i + 1): x for i, x in enumerate(sc.get("lua_chon") or [])}}
        if sc.get("ok") else None,
        "loi_giai_goc": norm["dau_vao"],
        "cau_noi_vi_python_tach": d.get("cau_noi_vi"),
        "luu_y": [FLAG_HINT[c] for c in ["khuon_" + str(ph.get("khuon"))] + norm["co"] if c in FLAG_HINT],
    }
    if d.get("sau_dich"):
        payload["prompt_analysis_python_tach"] = d["sau_dich"]
    payload["luu_y"] = list(dict.fromkeys(payload["luu_y"]))
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
    ctx = {"cau_noi": de.get("cau_hoi"), "cac_cau_tra_loi": {str(i + 1): x for i, x in enumerate(de.get("lua_chon") or [])},
           "dap_an_so": de["dap_an_so"]}
    return ("NGỮ CẢNH ĐỀ NGHE (script – chỉ để hiểu):\n" + json.dumps(ctx, ensure_ascii=False, indent=1) +
            "\n\nJSON LỜI GIẢI (trường dịch từ tiếng Việt: {\"id\": …, \"vi\": …}; trường dịch TRỰC TIẾP từ tiếng Nhật – lời thoại: "
            "{\"id\": …, \"dich_tu_tieng_nhat\": true, \"nguon\": …}):\n"
            + json.dumps(tagged, ensure_ascii=False, indent=1) +
            "\n\nDỊCH CÁC ID SAU (chỉ các id này): " + ", ".join(todo))
