"""[Dạng 05 – dựng 2026-10-06 từ dạng 02/03] Giai đoạn 1 – chuẩn bị cho Bước 1.2 (Claude kiểm tra và sửa JSON tiếng Việt).

- Chép bản GPT sang output/json_vi/checked/<id>.json (Claude sửa trực tiếp file này)
- Tạo file lý do rỗng <id>.ly_do.json để Claude điền
- Chạy thử kiểm tra Python trên BẢN GPT (chỉ để đo và gợi ý – không quyết định trạng thái)
- Ghi danh sách việc cho Claude: output/claude/gd1_danh_sach.json
- Phạm vi theo config.chinh_sach.claude_kiem_tra: tat_ca | co_co_va_ngau_nhien
  (câu không nằm trong phạm vi: bản GPT được chép nguyên, ly_do ghi "khong_kiem_tra": true)

Cách chạy:  python scripts/s1_claude_goi.py --pilot      (hoặc --ids / --lo / --tat-ca)
Sau đó nói với Claude: "Kiểm tra giai đoạn 1 dạng 05 theo prompts/s1_claude_kiem_tra.md"
"""
import argparse
import os
import random
import shutil

import _dang as D
from pipeline_chung.checks_chung import check_vi
from pipeline_chung.common import load_json, save_json
from pipeline_chung.trang_thai import Status


def precheck(sid, doc, cfg, schema):
    norm = D.load_norm(sid)
    r = check_vi(doc, schema, norm["src_text"], norm["src_vi_text"], norm, cfg["kiem_tra"], D.strip_labels,
                 marks_src=norm["marks_src"], furi_src_text=norm["src_text_furi"], furi_skip=D.FURI_SKIP)
    k_loi, k_cb = D.check_k(doc, norm, cfg["chinh_sach"])
    hint = [f"[Âm Hán Việt] {x}" for x in D.han_viet_src(norm)] + [f"[Nghi dính câu/định dạng] {x}" for x in D.format_hints(norm)] + [f"[Từ điển Sudachi] {x}" for x in D.sudachi_hints(norm)]
    return norm, r["loi"] + k_loi, r["canh_bao"] + k_cb + hint


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--ids")
    ap.add_argument("--lo", type=int)
    ap.add_argument("--tat-ca", action="store_true")
    ap.add_argument("--force", action="store_true", help="chép lại bản GPT, ghi đè bản Claude đang sửa dở")
    args = ap.parse_args()
    cfg = D.cfg()
    st = Status(D.status_path())
    ids = [s for s in D.select_ids(args, st, ("ĐANG_XỬ_LÝ", "CẦN_SỬA_GĐ1")) if os.path.exists(D.OUT("json_vi", "gpt", s + ".json"))]
    schema = load_json(D.P(cfg["schema"]))
    pol = cfg["chinh_sach"]
    rng = random.Random(cfg["pilot"]["seed"])
    tasks, auto = [], 0
    for sid in ids:
        src = D.OUT("json_vi", "gpt", sid + ".json")
        dst = D.OUT("json_vi", "checked", sid + ".json")
        why = D.OUT("json_vi", "checked", sid + ".ly_do.json")
        rework = st.get(sid).get("trang_thai") == "CẦN_SỬA_GĐ1" and os.path.exists(dst) and not args.force
        if os.path.exists(dst) and not args.force and not rework:
            if os.path.exists(why) and "_huong_dan" in load_json(why):     # đã chuẩn bị nhưng Claude chưa làm xong → vẫn giữ trong danh sách
                norm, loi, cb = precheck(sid, load_json(src), cfg, schema)
                tasks.append({"sample_id": sid, "co": norm["co"], "ghi_chu_ban_goc_tu_dong": norm["ghi_chu_ban_goc"],
                              "python_tren_ban_gpt": {"loi": loi, "canh_bao": cb},
                              "dau_vao": os.path.relpath(D.OUT("samples", "norm", sid + ".json"), D.DANG),
                              "file_sua": os.path.relpath(dst, D.DANG), "file_ly_do": os.path.relpath(why, D.DANG)})
            continue
        doc = load_json(dst if rework else src)
        norm, loi, cb = precheck(sid, doc, cfg, schema)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if rework:          # sửa tiếp trên bản Claude đã sửa, giữ lý do cũ, ghi lý do bị trả lại
            old = load_json(why) if os.path.exists(why) else {}
            old.pop("khong_kiem_tra", None)
            old["_huong_dan"] = "CẦN SỬA LẠI – lý do: " + (st.get(sid).get("loi") or "") + ". Sửa tiếp file checked, thêm lý do mới vào 'sua', xong thì xóa khóa _huong_dan"
            save_json(old, why)
            tasks.append({"sample_id": sid, "can_sua_lai": st.get(sid).get("loi"), "co": norm["co"],
                          "ghi_chu_ban_goc_tu_dong": norm["ghi_chu_ban_goc"], "python_tren_ban_hien_tai": {"loi": loi, "canh_bao": cb},
                          "dau_vao": os.path.relpath(D.OUT("samples", "norm", sid + ".json"), D.DANG),
                          "file_sua": os.path.relpath(dst, D.DANG), "file_ly_do": os.path.relpath(why, D.DANG)})
            continue
        shutil.copyfile(src, dst)
        in_scope = pol["claude_kiem_tra"] == "tat_ca" or bool(norm["co"] or loi or cb) or rng.random() < pol["ty_le_ngau_nhien"]
        if not in_scope:
            save_json({"sua": [], "khong_kiem_tra": True, "ghi_chu_ban_goc": []}, why)
            auto += 1
            continue
        save_json({"sua": [], "ghi_chu_ban_goc": [], **({"nghi_noi_dung": []} if cfg.get("cach_chia_dang") == "v2" else {}),
                   "kiem_tra_boi": cfg["claude"]["model"], "_huong_dan": "Claude điền theo prompts/s1_claude_kiem_tra.md, xong thì xóa khóa _huong_dan"}, why)
        tasks.append({"sample_id": sid, "co": norm["co"], "ghi_chu_ban_goc_tu_dong": norm["ghi_chu_ban_goc"],
                      "python_tren_ban_gpt": {"loi": loi, "canh_bao": cb},
                      "dau_vao": os.path.relpath(D.OUT("samples", "norm", sid + ".json"), D.DANG),
                      "file_sua": os.path.relpath(dst, D.DANG), "file_ly_do": os.path.relpath(why, D.DANG)})
    save_json(tasks, D.OUT("claude", "gd1_danh_sach.json"))
    print(f"{len(tasks)} câu cần Claude kiểm tra → output/claude/gd1_danh_sach.json"
          + (f" | {auto} câu ngoài phạm vi (chép nguyên bản GPT)" if auto else ""))
    print('Nói với Claude: "Kiểm tra giai đoạn 1 dạng 05 theo prompts/s1_claude_kiem_tra.md"')


if __name__ == "__main__":
    main()
