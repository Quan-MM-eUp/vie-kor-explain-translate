"""[PIPELINE v3] Giai đoạn 1 – thay cho Bước 1.1 với các mẫu ĐÃ CHẠY GPT ở pipeline v2: lấy lại JSON tiếng Việt do GPT tạo
(output_v2/json_vi/gpt/<id>.json + .meta.json) thay vì gọi API lại – cùng prompt GPT (s1_chuyen_json.v1), cùng schema.

Chỉ lấy khi dữ liệu gốc của mẫu KHÔNG đổi (hash_goc v3 = hash_goc v2). Mẫu trong kho đã duyệt được bỏ qua (thêm --ca-da-duyet để vẫn lấy).
Sau bước này chạy tiếp như bình thường: s1_claude_goi.py → Claude kiểm tra theo prompts/s1_claude_kiem_tra.md (quy tắc v3) → s1_kiem_tra.py …

Cách chạy (từ thư mục pipeline_v3):
  python scripts/s0_chuan_bi.py                       # nếu chưa chạy (tạo output/samples/norm + trang_thai.csv)
  python scripts/s1_lay_gpt_v2.py --tu 1 --den 130     # hoặc --ids 381_1,447_1,…
  python scripts/s1_lay_gpt_v2.py --ids … --force      # ghi đè cả mẫu đã có kết quả GPT trong v3
"""
import argparse
import os
import shutil

import _dang as D
from pipeline_chung.common import read_csv
from pipeline_chung.trang_thai import Status

STATES = ("ĐANG_XỬ_LÝ", "LỖI_KỸ_THUẬT")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids")
    ap.add_argument("--lo", type=int)
    ap.add_argument("--tat-ca", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--ca-da-duyet", action="store_true")
    args = ap.parse_args()
    cfg = D.cfg()
    v2 = D.P(cfg["output_v2_tham_chieu"])
    st = Status(D.status_path())
    st_v2 = {r["sample_id"]: r for r in read_csv(os.path.join(v2, "reports", "trang_thai.csv"))}
    ids = D.bo_qua_da_duyet(D.select_ids(args, st, STATES), args, "1.1 (lấy GPT v2)")
    lay, khong_co, lech, da_co = [], [], [], []
    for sid in ids:
        src = os.path.join(v2, "json_vi", "gpt", sid + ".json")
        dst = D.OUT("json_vi", "gpt", sid + ".json")
        if not os.path.exists(src):
            khong_co.append(sid)
            continue
        h3, h2 = (st.get(sid) or {}).get("hash_goc"), (st_v2.get(sid) or {}).get("hash_goc")
        if not h3 or h3 != h2:
            lech.append(sid)
            continue
        if os.path.exists(dst) and not args.force:
            da_co.append(sid)
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        if os.path.exists(src[:-5] + ".meta.json"):
            shutil.copy2(src[:-5] + ".meta.json", dst[:-5] + ".meta.json")
        r2 = st_v2[sid]
        st.update(sid, trang_thai="ĐANG_XỬ_LÝ", loi="", giai_doan_loi="", model_gd1=r2.get("model_gd1"),
                  prompt_gd1=r2.get("prompt_gd1"), canh_bao="[v3] JSON GPT giai đoạn 1 lấy lại từ output_v2 (không gọi API)")
        lay.append(sid)
    st.save()
    print(f"Lấy lại từ output_v2: {len(lay)} câu · chưa có GPT ở v2: {len(khong_co)} · dữ liệu gốc đổi (không lấy): {len(lech)} · đã có ở v3: {len(da_co)}")
    for name, xs in (("Chưa có GPT ở v2 (cần chạy s1_gpt_chuyen.py)", khong_co), ("Dữ liệu gốc đổi", lech)):
        if xs:
            print(f"  {name}: {xs[:15]}{' …' if len(xs) > 15 else ''}")
    print("Bước tiếp theo: python scripts/s1_claude_goi.py … rồi nhờ Claude kiểm tra (prompts/s1_claude_kiem_tra.md – quy tắc v3)")


if __name__ == "__main__":
    main()
