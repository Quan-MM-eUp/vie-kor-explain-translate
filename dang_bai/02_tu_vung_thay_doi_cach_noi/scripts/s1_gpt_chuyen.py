"""Giai đoạn 1 – Bước 1.1: GPT chuyển lời giải gốc (đã chuẩn hóa) sang JSON tiếng Việt theo schema v2 (strict).

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
    "dong_pt_dinh_lien": "Có dòng phân tích bị dính liền (vd '…\".3. 新しい (…): …') – tách phần sau về đúng lựa chọn, bỏ nhãn ở đầu.",
    "so_dong_pt_khac_4": "Phần PHÂN TÍCH không có đúng 4 dòng đánh số – lựa chọn không có phân tích để analysis: null, không tự viết.",
    "thu_tu_pt_lech": "Số thứ tự dòng phân tích không khớp thứ tự lựa chọn của đề – đặt phân tích theo nội dung nhãn, không theo số.",
    "lech_dap_an": "Số trong LỰA CHỌN ĐÚNG khác đáp án của đề – correct.index lấy theo dap_an_so của đề.",
    "thieu_phan_tich": "Thiếu phần PHÂN TÍCH – cả 4 analysis = null, intro/conclusion = null.",
    "thieu_tham_khao": "Thiếu phần THÔNG TIN THAM KHẢO – reference = null.",
    "tham_khao_khong_nhan": "Phần tham khảo không có tiêu đề (nằm sau LỰA CHỌN ĐÚNG, sau ###) – vẫn đưa vào reference.",
    "thieu_dau_phan_cach": "Có tiêu đề phần dính vào cuối phần trước (thiếu ###) – vẫn tách theo tiêu đề.",
    "thieu_cach_doc": "Không có dòng 'Cách đọc:' – question.reading = null.",
    "co_mo_dau": "PHÂN TÍCH có đoạn trước dòng '1.' – đưa vào analysis.intro.",
    "co_ket_luan": "PHÂN TÍCH có đoạn xuống dòng riêng sau dòng phân tích cuối – đưa vào analysis.conclusion.",
    "nhieu_doan_danh_dau": "Có dòng chứa từ 2 cặp { } – giữ đủ các cặp.",
    "de_co_gach_chan_loi_giai_khong": "Đề có gạch chân nhưng lời giải không đánh dấu – JSON không có { } ở câu đề.",
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
    ap.add_argument("--dry-run", action="store_true", help="in prompt câu đầu tiên, không gọi API")
    args = ap.parse_args()
    cfg = D.cfg()
    st = Status(D.status_path())
    ids = D.select_ids(args, st, STATES)
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
            doc, usage, model = call_json(cfg["gpt"], system, user_message(norm), schema, "vocab_synonym", [D.DANG])
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
