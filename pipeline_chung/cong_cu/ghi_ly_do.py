"""Ghi kết quả soát của tác tử KIỂM TRA cho cả lô từ MỘT file đặc tả JSON (thay cho việc viết script riêng mỗi lô).

  python ../../pipeline_chung/cong_cu/ghi_ly_do.py output/claude/ly_do_lo/gd1_91_100.json

File đặc tả:
{
  "giai_doan": "1",                     # "1" → output/json_vi/checked ; "2" → output/json_ko/checked
  "cau": {
    "4517_1": {
      "thay": [                         # sửa chuỗi trong file checked (tùy chọn): đường dẫn tới CHUỖI (…​.vi hoặc …​.ko)
        {"duong_dan": "$.analysis.options[1].meaning.vi", "cu": ";à cách", "moi": "là cách"}
      ],
      "sua": [...], "ghi_chu_ban_goc": [...], "nghi_noi_dung": [...],      # GĐ1
      "ghi_chu_khi_dich": [...], "loi_json_vi": [...]                        # GĐ2
    },
    "4812_1": {}                        # không có gì: vẫn liệt kê để xóa _huong_dan, đặt các danh sách rỗng
  }
}
- "cu" phải xuất hiện đúng 1 lần trong chuỗi, không thì dừng (không sửa gì của mẫu đó); đã thay rồi (chỉ còn "moi") thì bỏ qua → chạy lại an toàn.
- Các khóa danh sách được GHI ĐÈ (không cộng dồn); khóa không nêu → đặt [] nếu chưa có.
- Luôn xóa "_huong_dan". Chỉ sửa file của các mẫu có trong đặc tả.
"""
import os
import sys

import _chung as C

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from pipeline_chung.common import get_path, parse_path  # noqa: E402

C.kiem_dang()
spec = C.lj(sys.argv[1])
gd = str(spec.get("giai_doan"))
lop = {"1": "json_vi", "2": "json_ko"}[gd]
KHOA = {"1": ("sua", "ghi_chu_ban_goc", "nghi_noi_dung"), "2": ("sua", "ghi_chu_ban_goc", "ghi_chu_khi_dich", "loi_json_vi")}[gd]
loi = 0
for sid, v in spec["cau"].items():
    pj, pl = C.out(lop, "checked", sid + ".json"), C.out(lop, "checked", sid + ".ly_do.json")
    if not (os.path.exists(pj) and os.path.exists(pl)):
        print(f"BỎ QUA {sid}: chưa có {os.path.relpath(pj)} / .ly_do.json (đã chạy s{gd}_claude_goi chưa?)")
        loi += 1
        continue
    doc, ly = C.lj(pj), C.lj(pl)
    ok = True
    for t in v.get("thay", []):
        path = parse_path(t["duong_dan"])
        try:
            parent, key = get_path(doc, path[:-1]), path[-1]
            s = parent[key]
        except (KeyError, IndexError, TypeError):
            print(f"LỖI {sid}: không có đường dẫn {t['duong_dan']}")
            ok = False
            break
        if isinstance(s, str) and t["cu"] not in s and t["moi"] in s:
            print(f"   {sid}: {t['duong_dan']} đã thay từ lần chạy trước – bỏ qua")
            continue
        if not isinstance(s, str) or s.count(t["cu"]) != 1:
            print(f"LỖI {sid}: '{t['cu']}' xuất hiện {s.count(t['cu']) if isinstance(s, str) else 0} lần ở {t['duong_dan']}")
            ok = False
            break
        parent[key] = s.replace(t["cu"], t["moi"])
    if not ok:
        loi += 1
        continue
    for k in KHOA:
        if k in v:
            ly[k] = v[k]
        else:
            ly.setdefault(k, [])
    ly.pop("_huong_dan", None)
    if v.get("thay"):
        C.sj(pj, doc)
    C.sj(pl, ly)
    print(f"OK {sid}: thay {len(v.get('thay', []))}, " + ", ".join(f"{k} {len(ly[k])}" for k in KHOA))
print("Xong." if not loi else f"Có {loi} mẫu lỗi – sửa đặc tả rồi chạy lại (các mẫu OK chạy lại vẫn an toàn).")
