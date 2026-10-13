"""[Dạng 07 – Lựa chọn ngữ pháp] Giai đoạn 1 – Bước 1.1: GPT chuyển lời giải gốc (đã chuẩn hóa) sang JSON tiếng Việt theo schema grammar_choice.v2 (strict).

Cách chạy (từ thư mục dạng bài):
  python scripts/s1_gpt_chuyen.py --pilot --dry-run      # in prompt của câu đầu tiên, KHÔNG gọi API
  python scripts/s1_gpt_chuyen.py --pilot                # chạy các câu pilot
  python scripts/s1_gpt_chuyen.py --lo 200               # chạy 200 câu tiếp theo (trạng thái ĐANG_XỬ_LÝ / LỖI_KỸ_THUẬT)
  python scripts/s1_gpt_chuyen.py --ids 2610_1,54417_1 --force
Đầu ra: output/json_vi/gpt/<id>.json (+ <id>.meta.json: model, token, thời gian), output/reports/usage_gd1.jsonl
"""
import argparse
import datetime
import json
import os

import _dang as D
from pipeline_chung.common import load_json, save_json  # noqa: F401
from pipeline_chung.gpt_client import GPTError, call_json
from pipeline_chung.trang_thai import Status
import pipeline_chung.tham_khao as TK

STATES = ("ĐANG_XỬ_LÝ", "LỖI_KỸ_THUẬT")   # CẦN_SỬA_GĐ1 quay về bước 1.2 (s1_claude_goi), không gọi lại GPT – muốn gọi lại thì dùng --ids … --force
FLAG_HINT = {
    "doc_tu_furigana": "Lời giải không có dòng 'Cách đọc:' của câu đề – chép ĐÚNG chuỗi 'cach_doc_ghep_tu_furigana' (dưới đây) vào question.reading.",
    "khong_cach_doc": "Lời giải không có dòng 'Cách đọc:' của câu đề – question.reading = null (không tự ghép).",
    "khong_nghia_de": "Lời giải không có dòng 'Nghĩa:' của câu đề – question.meaning = null.",
    "nhan_de_bai": "Dòng câu đề trong lời giải có nhãn 'Đề bài:' ở đầu – question.ja KHÔNG chép nhãn này, chỉ chép câu tiếng Nhật.",
    "hoi_thoai": "Đề hội thoại / nhiều dòng – question.ja chép đủ các dòng (giữ \\n); applied.ja chép đúng như lời giải (có khi chỉ là dòng có chỗ trống).",
    "hai_cho_trong": "Đề có 2 chỗ trống, lựa chọn dạng 'X/Y' – option_ja chép nguyên 'X/Y'; applied.ja chép đúng như lời giải.",
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


def system_prompt(cfg):
    return D.read_prompt("s1_chuyen_json.md")        # ví dụ đầy đủ đã nằm sẵn trong prompt


def user_message(norm):
    de = norm["de"]
    payload = {
        "question_id": norm["question_id"], "cau_con": norm["cau_con"], "cap_do": norm["cap_do"],
        "de_bai": {"cau_hoi": de["cau_hoi"],
                   "cac_lua_chon": {str(i + 1): x for i, x in enumerate(de["lua_chon"])},
                   "dap_an_so": de["dap_an_so"]},
        "loi_giai_goc": norm["dau_vao"],
        "luu_y": [FLAG_HINT[c] for c in norm["co"] if c in FLAG_HINT],
    }
    if (norm.get("phan") or {}).get("doc_furigana"):
        payload["cach_doc_ghep_tu_furigana"] = norm["phan"]["doc_furigana"]
    return "Chuyển lời giải sau sang JSON theo schema.\n\n" + json.dumps(payload, ensure_ascii=False, indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--ids")
    ap.add_argument("--lo", type=int)
    ap.add_argument("--tat-ca", action="store_true")
    ap.add_argument("--force", action="store_true", help="chạy lại cả câu đã có kết quả")
    ap.add_argument("--ca-da-duyet", action="store_true", help="vẫn chạy cả mẫu đã có trong kho da_duyet/")
    ap.add_argument("--dung-gpt", action="store_true", help="vẫn gọi GPT API dù config.tao_ban.nguon = claude")
    ap.add_argument("--dry-run", action="store_true", help="in prompt câu đầu tiên, không gọi API")
    args = ap.parse_args()
    if D.nguon_tao() == "claude" and not args.dung_gpt and not args.dry_run:
        raise SystemExit("Dạng 07 đã chuyển sang Claude Opus Cowork làm bước này (config.tao_ban.nguon = claude) – "
                         "dùng scripts/s1_claude_tao.py / s2_claude_dich.py (Claude tự chạy). Muốn vẫn gọi GPT: thêm --dung-gpt.")
    cfg = D.cfg()
    st = Status(D.status_path())
    ids = D.bo_qua_da_duyet(D.select_ids(args, st, STATES), args, "1.1")
    schema = load_json(D.P(cfg["schema_api"]))
    system = system_prompt(cfg)

    if args.dry_run:
        norm = D.load_norm(ids[0])
        print("=== SYSTEM ===\n" + system + "\n\n=== USER ===\n" + user_message(norm))
        print(f"\n(model: {cfg['gpt']['model']} | {len(ids)} câu trong phạm vi)")
        return

    tot = {"prompt_tokens": 0, "completion_tokens": 0}
    done = err = skip = 0
    for sid in ids:
        out = D.OUT("json_vi", "gpt", sid + ".json")
        if os.path.exists(out) and not args.force:
            skip += 1
            continue
        norm = D.load_norm(sid)
        if norm["khuon_goc"] == "trong":
            continue
        t0 = datetime.datetime.now()
        try:
            doc, usage, model = call_json(cfg["gpt"], system, user_message(norm), schema, "grammar_choice", [D.DANG])
        except GPTError as e:
            if e.kind == "cau_hinh":
                st.save()
                raise SystemExit(f"Dừng: lỗi cấu hình – {e}")
            st.update(sid, trang_thai="LỖI_KỸ_THUẬT", giai_doan_loi="1", loi=f"GPT: {e}")
            err += 1
            print(f"LỖI_KỸ_THUẬT {sid}: {e}")
            continue
        TK.dien(doc, (norm.get("phan") or {}).get("tham_khao"))     # quy tắc THAM KHẢO: Python chép nguyên văn
        save_json(doc, out)
        meta = {"sample_id": sid, "model": model, "usage": usage, "prompt": cfg["phien_ban_prompt"]["gd1"],
                "thoi_gian_giay": (datetime.datetime.now() - t0).total_seconds(), "luc": t0.isoformat(timespec="seconds")}
        save_json(meta, D.OUT("json_vi", "gpt", sid + ".meta.json"))
        with open(D.OUT("reports", "usage_gd1.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(meta, ensure_ascii=False) + "\n")
        st.update(sid, trang_thai="ĐANG_XỬ_LÝ", loi="", model_gd1=model, prompt_gd1=cfg["phien_ban_prompt"]["gd1"])
        for k in tot:
            tot[k] += usage.get(k, 0)
        done += 1
        print(f"xong {sid}  token vào/ra: {usage.get('prompt_tokens')}/{usage.get('completion_tokens')}")
        if done % 20 == 0:
            st.save()
    st.save()
    print(f"Xong {done} câu, lỗi kỹ thuật {err}, bỏ qua (đã có) {skip}. Token lần này: {tot}")
    print("Bước tiếp theo: python scripts/s1_claude_goi.py … rồi nhờ Claude kiểm tra (prompts/s1_claude_kiem_tra.md)")


if __name__ == "__main__":
    main()
