"""Xem gọn một / nhiều mẫu dạng 16 cho tác tử KIỂM TRA (GĐ1): đề, lời giải gốc đã tách, gợi ý Python, JSON checked.

  python3 scripts/xem16.py 12099_1 12284_1
  python3 scripts/xem16.py --lo 1 10          # các mẫu stt 1–10 đang có bản checked
  thêm --gon: bỏ phần lời giải gốc;  --ban tao: xem bản tác tử TẠO thay vì bản checked
Mỗi dòng JSON in kèm ĐƯỜNG DẪN đầy đủ ($.options[1].analysis.vi …) – chép thẳng vào file đặc tả lô (ghi_ly_do.py).
"""
import json
import os
import sys

import _dang as D
from pipeline_chung.common import load_json


def p(*a):
    print(*a)


def vi(o):
    return (o or {}).get("vi") if isinstance(o, dict) else None


def main():
    args = sys.argv[1:]
    gon = "--gon" in args
    args = [a for a in args if a != "--gon"]
    lop = "checked"
    if "--ban" in args:
        i = args.index("--ban")
        lop = {"tao": "claude_tao"}.get(args[i + 1], args[i + 1])
        del args[i:i + 2]
    if args[:1] == ["--lo"]:
        order = D.thu_tu()
        ids = [s for s in order[int(args[1]) - 1:int(args[2])] if os.path.exists(D.OUT("json_vi", lop, s + ".json"))]
    else:
        ids = args
    goi_y = {}
    if os.path.exists(D.OUT("claude", "gd1_danh_sach.json")):
        for t in load_json(D.OUT("claude", "gd1_danh_sach.json")):
            goi_y[t["sample_id"]] = t
    for sid in ids:
        n = D.load_norm(sid)
        fp = D.OUT("json_vi", lop, sid + ".json")
        d = load_json(fp) if os.path.exists(fp) else None
        de = n["de"]
        p("#" * 24, sid, n["cap_do"], f"khuôn {n['khuon_goc']} · tạo bằng {n.get('tao_bang')}")
        p("CỜ:", " ".join(n["co"]))
        p("ĐỀ: câu hỏi:", de.get("cau_hoi") or "–", "| lựa chọn:", " / ".join(f"{i + 1}. {x}" for i, x in enumerate(de["lua_chon"])),
          "| đáp án:", de["dap_an_so"])
        if not gon:
            p("--- LỜI GIẢI GỐC (đã tách) ---")
            p(n.get("dau_vao"))
        g = goi_y.get(sid) or {}
        py = g.get("python_tren_ban_gpt") or g.get("python_tren_ban_hien_tai") or {}
        if g.get("ghi_chu_ban_goc_tu_dong") or py.get("loi") or py.get("canh_bao") or g.get("can_sua_lai"):
            p("--- GỢI Ý ---")
            for k, v in (("Cần sửa lại", g.get("can_sua_lai")), ("Ghi chú tự động", g.get("ghi_chu_ban_goc_tu_dong")),
                         ("Python LỖI", py.get("loi")), ("Python cảnh báo", py.get("canh_bao"))):
                if v:
                    p(f"{k}: {v}")
        if d is None:
            p("(chưa có JSON", lop, ")")
            continue
        p(f"--- JSON ({lop}) ---")
        for gi, grp in enumerate(d.get("full_translation") or []):
            p(f"$.full_translation[{gi}]  label={grp.get('label')!r}  ({len(grp.get('lines') or [])} dòng)")
            for li, ln in enumerate(grp.get("lines") or []):
                p(f"  [{li}] {ln.get('speaker') or '-'} | {ln.get('ja')} || {vi(ln.get('meaning'))}")
        if d.get("full_translation") is None:
            p("$.full_translation = null")
        q = d.get("question") or {}
        p("$.question.ja =", q.get("ja"))
        p("$.question.meaning.vi =", vi(q.get("meaning")))
        for si, s in enumerate(d.get("summary") or []):
            p(f"$.summary[{si}].heading.vi =", vi(s.get("heading")))
            for pi, pt in enumerate(s.get("points") or []):
                p(f"$.summary[{si}].points[{pi}].vi =", vi(pt))
        for oi, o in enumerate(d.get("options") or []):
            p(f"$.options[{oi}]  #{o.get('index')} option_ja={o.get('option_ja')!r}  is_match={o.get('is_match')}  reading={o.get('reading')}")
            p(f"$.options[{oi}].meaning.vi =", vi(o.get("meaning")))
            for qi, qq in enumerate(o.get("quotes") or []):
                p(f"$.options[{oi}].quotes[{qi}].ja =", qq.get("ja"))
                p(f"$.options[{oi}].quotes[{qi}].meaning.vi =", vi(qq.get("meaning")))
            a = vi(o.get("analysis"))
            p(f"$.options[{oi}].analysis.vi =", json.dumps(a, ensure_ascii=False) if a and "\n" in a else a)
        c = d.get("correct") or {}
        p("$.correct =", c.get("index"), c.get("option_ja"), "| full_sentence:", c.get("full_sentence"), "| key_info:", d.get("key_info"))


if __name__ == "__main__":
    main()
