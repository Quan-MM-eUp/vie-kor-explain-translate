"""Dạng 16 – Nghe hiểu chủ đề: nội dung đầu vào cho TÁC TỬ TẠO (Claude A).

  GĐ1: STATES, FLAG_HINT, user_message(norm)                     → s1_claude_tao.py
  GĐ2: terms_text(glossary), load_tm(cfg), user_message_gd2(…)    → s2_claude_dich.py
Tác tử TẠO KHÔNG ghi full_translation (Python điền) – trừ câu có cờ lech_dong (lời thoại Nhật và bản dịch Việt lệch số dòng).
"""
import json
import os

import _dang as D
from pipeline_chung.common import load_json

STATES = ("ĐANG_XỬ_LÝ", "LỖI_KỸ_THUẬT")

FLAG_HINT = {
    "lua_chon_tranh": "Lựa chọn là TRANH: option_ja = '1'…'4' (chép đúng đề), meaning = null; mô tả tranh trong phân tích chép nguyên vào analysis.",
    "lech_dong": "LỆCH DÒNG: số dòng lời thoại Nhật ≠ số dòng bản dịch Việt → BẠN phải ghi full_translation: giữ ĐỦ và ĐÚNG THỨ TỰ mọi dòng tiếng Nhật "
                 "(ja chép nguyên dòng J…, speaker = nhãn của dòng J đó, không có → null); gán dòng Việt tương ứng vào meaning.vi (một dòng Nhật ứng với "
                 "nhiều dòng Việt → nối bằng ' '; dòng Nhật không có bản dịch → meaning = null); dòng Việt không ứng với dòng Nhật nào → thêm line "
                 "{speaker: null, ja: null, meaning} đúng vị trí. Không bỏ, không sửa chữ nào. Khối phụ (JP / VP) → nhóm thứ 2 {label: null, lines}.",
    "mo_dau_phan_tich": "Có PHÂN TÍCH MỞ ĐẦU (trước khối 1.) → summary = [{heading, points}] theo goi_y_summary (heading = dòng tiêu đề ngắn, points = từng dòng còn lại, "
                        "giữ câu trích trong dòng, bọc ⟪ ⟫ tiếng Nhật).",
    "so_khoi_khac_4": "Phân tích không đủ 4 khối – lựa chọn không có khối: quotes = [], analysis = null, meaning theo bản dịch (nếu có), is_match = (index = đáp án).",
    "khoi_khong_ket_luan": "Có khối không có '→ ĐÚNG/SAI' – is_match của khối đó = (index = đáp án của đề).",
    "khoi_nhieu_ket_luan": "Có khối có nhiều '→ ĐÚNG/SAI' – is_match theo kết luận CUỐI của khối; chép đủ chữ còn lại vào analysis.",
    "lech_dap_an": "Khối '→ ĐÚNG' khác đáp án của đề – is_match vẫn chép theo lời giải; correct.index = dap_an_so của đề.",
    "nhieu_dung": "Nhiều khối '→ ĐÚNG' – is_match chép theo lời giải; correct.index = dap_an_so.",
    "khong_co_dung": "Không khối nào '→ ĐÚNG' – is_match chép theo lời giải (đều false); correct.index = dap_an_so.",
    "khong_cau_hoi_cuoi": "Lời thoại không kết thúc bằng câu hỏi lặp – question.ja = câu hỏi trong dòng mở đầu (goi_y_cau_hoi) hoặc cột câu hỏi của đề; "
                          "meaning = phần dịch tương ứng trong bản dịch (không có → null).",
    "thieu_ban_dich": "Không có bản dịch lời thoại – question.meaning = null nếu lời giải không dịch câu hỏi; không tự dịch.",
    "thieu_loi_thoai": "Không có lời thoại tiếng Nhật – question.ja lấy theo cột câu hỏi của đề nếu có, không thì null.",
    "phan_tich_o_transcript": "Phần phân tích lấy từ cột transcript_vi (chép như mọi câu khác).",
    "trich_ngoai_loi_thoai": "Có câu trích không khớp nguyên văn lời thoại – vẫn chép NGUYÊN như lời giải (không sửa theo lời thoại).",
    "co_furigana": "Có furigana – chép nguyên ｜chữ《cách đọc》 ở đúng chỗ (cả trong câu trích và trong ⟪ ⟫); không tự thêm, không bỏ.",
}


def _dong(lines, tien_to, khoa_text):
    return [{"dong": f"{tien_to}{i + 1}", "nguoi_noi": x["speaker"], khoa_text: x["text"]} for i, x in enumerate(lines)]


def user_message(norm):
    de, t = norm["de"], norm["nghe"]
    tranh = "lua_chon_tranh" in norm["co"]
    payload = {
        "question_id": norm["question_id"], "cau_con": norm["cau_con"], "cap_do": norm["cap_do"],
        "de_bai": {"cot_cau_hoi": de.get("cau_hoi") or None,
                   "cac_lua_chon": {str(i + 1): x for i, x in enumerate(de["lua_chon"])},
                   "loai_lua_chon": "tranh (option_ja = số, meaning = null)" if tranh else "chữ",
                   "dap_an_so": de["dap_an_so"]},
    }
    if "lech_dong" in norm["co"]:
        payload["can_ghi_full_translation"] = True
        payload["loi_thoai_ja"] = _dong(t["loi_thoai_ja"], "J", "ja")
        payload["ban_dich_vi"] = _dong(t["ban_dich_vi"], "V", "vi")
        if t["phu_ja"] or t["phu_vi"]:
            payload["khoi_phu_ja"] = _dong(t["phu_ja"], "JP", "ja")
            payload["khoi_phu_vi"] = _dong(t["phu_vi"], "VP", "vi")
    else:
        payload["can_ghi_full_translation"] = False
        payload["loi_thoai_song_ngu_chi_de_hieu"] = [
            {"nguoi_noi": ln["speaker"], "ja": ln["ja"], "vi": (ln.get("meaning") or {}).get("vi")}
            for g in (t["full_translation"] or []) for ln in g["lines"]]
    payload["goi_y_cau_hoi"] = t["goi_y_cau_hoi"]
    if t["ds_lua_chon_vi"]:
        payload["dich_cac_lua_chon_trong_ban_dich"] = t["ds_lua_chon_vi"]
    payload["phan_tich_mo_dau"] = t["phan_tich_mo_dau"]
    if t["phan_tich_mo_dau"]:
        payload["goi_y_summary"] = norm.get("goi_y_tom_tat")
    payload["loi_giai_phan_tich"] = "\n".join(
        "\n".join([f"{b['so']}. {b['dau']}".rstrip()] + b["dong"]) for b in t["khoi"])
    payload["goi_y_tach_khoi"] = [{k: g[k] for k in ("so", "nghia_lua_chon", "trich", "dan", "phan_tich", "ket_luan")}
                                  for g in norm.get("goi_y_khoi") or []]
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
    ctx = {"cac_lua_chon": {str(i + 1): x for i, x in enumerate(de["lua_chon"])},
           "loai_lua_chon": "tranh" if "lua_chon_tranh" in norm["co"] else "chữ", "dap_an_so": de["dap_an_so"]}
    return ("NGỮ CẢNH ĐỀ (chỉ để hiểu):\n" + json.dumps(ctx, ensure_ascii=False, indent=1) +
            "\n\nJSON LỜI GIẢI (trường dịch từ tiếng Việt: {\"id\": …, \"vi\": …}; trường dịch TRỰC TIẾP từ tiếng Nhật: "
            "{\"id\": …, \"dich_tu_tieng_nhat\": true, \"nguon\": …}):\n" + json.dumps(tagged, ensure_ascii=False, indent=1) +
            "\n\nDỊCH CÁC ID SAU (chỉ các id này): " + ", ".join(todo))
