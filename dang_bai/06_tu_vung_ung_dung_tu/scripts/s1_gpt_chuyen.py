"""[Dạng 06 – Ứng dụng từ] Giai đoạn 1 – Bước 1.1: GPT chuyển lời giải gốc (đã chuẩn hóa) sang JSON tiếng Việt theo schema vocab_usage.v2 (strict).

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

STATES = ("ĐANG_XỬ_LÝ", "LỖI_KỸ_THUẬT")   # CẦN_SỬA_GĐ1 quay về bước 1.2 (s1_claude_goi), không gọi lại GPT – muốn gọi lại thì dùng --ids … --force
FLAG_HINT = {
    "bien_the_dinh_nghia": "Đề có định nghĩa tiếng Nhật sau '……' – word.definition_ja chép phần sau '……' của de_bai.cau_hoi; câu dùng từ đúng nhưng khác nghĩa định nghĩa: usage_ok = true theo lời giải, is_correct = false.",
    "dong_pt_dinh_lien": "Có dòng phân tích bị dính liền (vd '…phù hợp hơn.3. 小麦粉…') – tách phần sau về đúng lựa chọn, bỏ số thứ tự ở đầu.",
    "nhan_dinh_lien": "Có nhãn 'Cách đọc:' / 'Nghĩa:' / 'Sửa lại:' dính sau câu tiếng Nhật trên cùng một dòng – vẫn tách vào đúng trường.",
    "nhan_lap": "Có lựa chọn với 2 dòng 'Cách đọc:' / 'Nghĩa:' cho cùng một câu – dòng đầu vào trường, dòng thừa nối vào analysis.",
    "so_dong_pt_khac_4": "Phần PHÂN TÍCH không có đúng 4 câu đánh số – lựa chọn không có phân tích: sentence.ja chép câu của đề, reading / meaning / analysis / correction = null, usage_ok = null.",
    "thu_tu_pt_lech": "Số thứ tự trong PHÂN TÍCH không khớp thứ tự lựa chọn của đề – đặt phân tích theo nội dung câu, không theo số.",
    "cau_khac_de": "Có câu trong PHÂN TÍCH viết khác câu của đề – sentence.ja vẫn chép đúng câu trong LỜI GIẢI, không sửa theo đề.",
    "lech_dap_an": "Số trong LỰA CHỌN ĐÚNG khác đáp án của đề – correct.index và is_correct theo dap_an_so của đề.",
    "khong_so_lcd": "LỰA CHỌN ĐÚNG không ghi số – correct.index theo dap_an_so của đề.",
    "lcd_co_nhan_xet": "LỰA CHỌN ĐÚNG có thêm đoạn chữ ngoài dòng câu đáp án – chép nguyên vào correct.note.",
    "thieu_phan_tich": "Thiếu phần PHÂN TÍCH – sentence.ja chép câu của đề, các trường khác của lựa chọn = null.",
    "co_doan_sau_lcd": "Có đoạn không tiêu đề sau LỰA CHỌN ĐÚNG – nếu là nhận xét thì nối vào analysis.conclusion.",
    "thieu_dau_phan_cach": "Có tiêu đề phần dính vào cuối phần trước (thiếu ###) – vẫn tách theo tiêu đề.",
    "thieu_gioi_thieu": "Không có đoạn giới thiệu từ – word.ja lấy theo từ của đề (phần trước '……' nếu có), paren / meaning / usage = null.",
    "co_mo_dau": "PHÂN TÍCH có đoạn trước câu '1.' – đưa nguyên vào analysis.intro.",
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
    return "Chuyển lời giải sau sang JSON theo schema.\n\n" + json.dumps(payload, ensure_ascii=False, indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--ids")
    ap.add_argument("--lo", type=int)
    ap.add_argument("--tat-ca", action="store_true")
    ap.add_argument("--force", action="store_true", help="chạy lại cả câu đã có kết quả")
    ap.add_argument("--ca-da-duyet", action="store_true", help="vẫn chạy cả mẫu đã có trong kho da_duyet/")
    ap.add_argument("--dry-run", action="store_true", help="in prompt câu đầu tiên, không gọi API")
    ap.add_argument("--dung-gpt", action="store_true", help="vẫn gọi GPT API dù config.tao_ban.nguon = claude")
    args = ap.parse_args()
    if D.nguon_tao() == "claude" and not args.dung_gpt and not args.dry_run:
        raise SystemExit("Dạng 06 đã chuyển sang Claude Opus Cowork làm bước này (config.tao_ban.nguon = claude) – "
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
            doc, usage, model = call_json(cfg["gpt"], system, user_message(norm), schema, "vocab_usage", [D.DANG])
        except GPTError as e:
            if e.kind == "cau_hinh":
                st.save()
                raise SystemExit(f"Dừng: lỗi cấu hình – {e}")
            st.update(sid, trang_thai="LỖI_KỸ_THUẬT", giai_doan_loi="1", loi=f"GPT: {e}")
            err += 1
            print(f"LỖI_KỸ_THUẬT {sid}: {e}")
            continue
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
