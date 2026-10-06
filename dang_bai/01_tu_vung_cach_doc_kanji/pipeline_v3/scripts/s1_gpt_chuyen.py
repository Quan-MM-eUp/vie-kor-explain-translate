"""Giai đoạn 1 – Bước 1.1: GPT chuyển lời giải gốc (đã chuẩn hóa) sang JSON tiếng Việt theo schema v2 (strict).

Cách chạy (từ thư mục dạng bài):
  python scripts/s1_gpt_chuyen.py --pilot --dry-run      # in prompt của câu đầu tiên, KHÔNG gọi API
  python scripts/s1_gpt_chuyen.py --pilot                # chạy các câu pilot
  python scripts/s1_gpt_chuyen.py --lo 200               # chạy 200 câu tiếp theo (trạng thái ĐANG_XỬ_LÝ / LỖI_KỸ_THUẬT)
  python scripts/s1_gpt_chuyen.py --ids 393_1,1150_1 --force
Đầu ra: output/json_vi/gpt/<id>.json (+ <id>.meta.json: model, token, thời gian), output/reports/usage_gd1.jsonl
"""
import argparse
import datetime
import json
import os

import _dang as D
from pipeline_chung.common import load_json, save_json
from pipeline_chung.gpt_client import GPTError, call_json
from pipeline_chung.trang_thai import Status

STATES = ("ĐANG_XỬ_LÝ", "LỖI_KỸ_THUẬT")   # CẦN_SỬA_GĐ1 quay về bước 1.2 (s1_claude_goi), không gọi lại GPT – muốn gọi lại thì dùng --ids … --force
FLAG_HINT = {
    "nghi_don_phan_tich": "Ô phân tích của một lựa chọn có thể chứa cả phân tích của lựa chọn khác – hãy tách về đúng lựa chọn.",
    "thieu_phan_tich": "Có lựa chọn sai không có phân tích – để analysis: null, không tự viết.",
    "thieu_lua_chon": "Lời giải gốc có ít phân tích hơn số lựa chọn – options vẫn đủ 4, lựa chọn thiếu để analysis: null.",
    "lech_dap_an": "correct_index trong lời giải khác đáp án của đề – correct.index lấy theo dap_an_so của đề.",
    "tu_dien_dinh_cach_doc": "Thể từ điển bị viết dính vào cách đọc – tách ra dictionary_form.",
    "thieu_gach_chan": "Bản gốc thiếu gạch chân ở một số dòng – không tự thêm { }.",
}


def system_prompt(cfg):
    ex = load_json(D.P(cfg["vi_du_json"]))
    ex["schema"] = cfg["schema_id"]
    return D.read_prompt("s1_chuyen_json.md").replace("{{VI_DU_JSON}}", "```json\n" + json.dumps(ex, ensure_ascii=False, indent=1) + "\n```")


def user_message(norm):
    de = norm["de"]
    payload = {
        "question_id": norm["question_id"], "cau_con": norm["cau_con"], "cap_do": norm["cap_do"],
        "de_bai": {"cau_hoi": de["cau_hoi"],
                   "cac_lua_chon": {str(i + 1): x for i, x in enumerate(de["lua_chon"])},
                   "dap_an_so": de["dap_an_so"]},
        "khuon_loi_giai_goc": "JSON cũ" if norm["khuon_goc"] == "json" else "văn bản ###",
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
    args = ap.parse_args()
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
            doc, usage, model = call_json(cfg["gpt"], system, user_message(norm), schema, "vocab_kanji_reading", [D.DANG])
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
