"""Giai đoạn 2 – chuẩn bị cho Bước 2.4 (Claude kiểm tra bản dịch và sửa lỗi).

- Chép output/json_ko/gpt/<id>.json → output/json_ko/checked/<id>.json (Claude sửa giá trị ko trong file này)
- Tạo file lý do rỗng <id>.ly_do.json
- Tạo bảng xem nhanh output/claude/gd2/<id>.md: Mã | Vị trí | Tiếng Việt | Tiếng Hàn | Nguồn (GPT / câu cố định / bộ nhớ dịch)
- Danh sách việc: output/claude/gd2_danh_sach.json

Cách chạy:  python scripts/s2_claude_goi.py --pilot
Sau đó nói với Claude: "Kiểm tra giai đoạn 2 dạng 01 theo prompts/s2_claude_kiem_tra.md"
"""
import argparse
import os
import random
import shutil

import _dang as D
from pipeline_chung.common import get_path, load_json, parse_path, save_json, sha
from pipeline_chung.trang_thai import Status


def table(sid, doc, fmap, meta, norm, lang):
    de = norm["de"]
    lines = [f"# {sid}", "", f"**Câu hỏi:** {de['cau_hoi']}", "",
             "**Lựa chọn:** " + " / ".join(f"{i + 1}. {x}" for i, x in enumerate(de["lua_chon"])) + f" · **Đáp án:** {de['dap_an_so']}", "",
             "| Mã | Vị trí | Tiếng Việt | Tiếng Hàn | Nguồn |", "|---|---|---|---|---|"]
    for f in fmap:
        node = get_path(doc, parse_path(f["path"]))
        src = (meta.get("dien_san") or {}).get(f["id"], "GPT")
        esc = lambda s: (s or "").replace("|", "\\|").replace("\n", "<br>")  # noqa: E731
        lines.append(f"| {f['id']} | `{f['path']}` | {esc(f['vi'])} | {esc(node.get(lang))} | {src} |")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--ids")
    ap.add_argument("--lo", type=int)
    ap.add_argument("--tat-ca", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    cfg, lang = D.cfg(), D.cfg()["ngon_ngu_dich"]
    st = Status(D.status_path())
    pol = cfg["chinh_sach"]
    rng = random.Random(cfg["pilot"]["seed"] + 2)
    tasks, auto = [], 0
    for sid in D.select_ids(args, st, ("GĐ1_XONG", "LỖI_GĐ2")):
        src = D.OUT("json_ko", "gpt", sid + ".json")
        dst, why = D.OUT("json_ko", "checked", sid + ".json"), D.OUT("json_ko", "checked", sid + ".ly_do.json")
        if not os.path.exists(src):
            continue
        with open(src, encoding="utf-8") as f:
            src_hash = sha(f.read())
        if os.path.exists(dst) and not args.force:
            if os.path.exists(why) and load_json(why).get("_nguon_hash") == src_hash:
                if "_huong_dan" in load_json(why):     # đã chuẩn bị nhưng Claude chưa làm xong → vẫn giữ trong danh sách
                    tasks.append({"sample_id": sid, "co": D.load_norm(sid)["co"],
                                  "bang": os.path.relpath(D.OUT("claude", "gd2", sid + ".md"), D.DANG),
                                  "file_sua": os.path.relpath(dst, D.DANG), "file_ly_do": os.path.relpath(why, D.DANG)})
                continue          # đã có bản Claude cho đúng bản dịch GPT này
            print(f"{sid}: bản dịch GPT đã thay đổi so với bản Claude đang có → chép lại để kiểm tra")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        norm = D.load_norm(sid)
        in_scope = pol["claude_kiem_tra"] == "tat_ca" or bool(norm["co"] or st.get(sid).get("canh_bao")) or rng.random() < pol["ty_le_ngau_nhien"]
        if not in_scope:
            save_json({"sua": [], "khong_kiem_tra": True, "_nguon_hash": src_hash}, why)
            auto += 1
            continue
        save_json({"sua": [], "ghi_chu_ban_goc": [], "ghi_chu_khi_dich": [], "loi_json_vi": [], "_nguon_hash": src_hash,
                   "kiem_tra_boi": cfg["claude"]["model"], "_huong_dan": "Claude điền theo prompts/s2_claude_kiem_tra.md, xong thì xóa khóa _huong_dan"}, why)
        base = D.OUT("json_ko", "gpt", sid)
        md = table(sid, load_json(src), load_json(base + ".map.json"), load_json(base + ".meta.json"), norm, lang)
        os.makedirs(D.OUT("claude", "gd2"), exist_ok=True)
        with open(D.OUT("claude", "gd2", sid + ".md"), "w", encoding="utf-8") as f:
            f.write(md)
        tasks.append({"sample_id": sid, "co": norm["co"], "bang": os.path.relpath(D.OUT("claude", "gd2", sid + ".md"), D.DANG),
                      "file_sua": os.path.relpath(dst, D.DANG), "file_ly_do": os.path.relpath(why, D.DANG)})
    save_json(tasks, D.OUT("claude", "gd2_danh_sach.json"))
    print(f"{len(tasks)} câu cần Claude kiểm tra → output/claude/gd2_danh_sach.json" + (f" | {auto} câu ngoài phạm vi" if auto else ""))
    print('Nói với Claude: "Kiểm tra giai đoạn 2 dạng 01 theo prompts/s2_claude_kiem_tra.md"')


if __name__ == "__main__":
    main()
