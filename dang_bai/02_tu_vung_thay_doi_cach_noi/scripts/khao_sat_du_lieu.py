"""Khảo sát vấn đề dữ liệu dạng 02 – Thay đổi cách nói.

Quét data/02_tu_vung_thay_doi_cach_noi.csv, phát hiện từng loại vấn đề và ghi:
  bao_cao/van_de_du_lieu.csv       – mỗi dòng: van_de, mo_ta, so_cau, question_id (cách nhau bằng dấu phẩy)
  bao_cao/van_de_theo_cau.csv      – mỗi dòng 1 câu: question_id, cau_con, cap_do, danh sách vấn đề
Cách chạy (từ thư mục dạng bài):  python scripts/khao_sat_du_lieu.py
"""
import collections
import os
import re
import sys

DANG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(DANG)))
from pipeline_chung.common import read_csv, write_csv  # noqa: E402
from pipeline_chung.normalize import normalize_html  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

MO_TA = {
    "gach_chan_span": "Đề đánh dấu gạch chân bằng <span style=\"text-decoration: underline\"> thay vì <u>",
    "gach_chan_b": "Đề đánh dấu từ đang hỏi bằng in đậm <b> thay vì gạch chân",
    "gach_chan_ngoac": "Đề viết sẵn dấu { } thay cho thẻ gạch chân",
    "gach_chan_ngoac_toan_goc": "Đề viết sẵn dấu ｛ ｝ toàn góc (chữ Nhật) thay cho thẻ gạch chân",
    "de_khong_danh_dau": "Đề không đánh dấu từ đang hỏi (nếu lời giải có in đậm thì vẫn lấy lại được)",
    "khong_danh_dau_ca_hai": "Kiểu câu định nghĩa (cả câu là nghĩa cần tìm từ): cả đề lẫn lời giải không đánh dấu – không phải lỗi",
    "loi_giai_khong_in_dam": "Đề có đánh dấu nhưng phần đầu lời giải (câu hỏi / cách đọc / nghĩa) không in đậm từ đang hỏi",
    "thieu_phan_phan_tich": "Lời giải thiếu phần PHÂN TÍCH",
    "thieu_phan_lua_chon_dung": "Lời giải thiếu phần LỰA CHỌN ĐÚNG",
    "thieu_phan_tham_khao": "Lời giải thiếu phần THÔNG TIN THAM KHẢO",
    "phan_rong": "Lời giải có phần rỗng (### liền nhau)",
    "thieu_dau_phan_cach": "Có tiêu đề PHÂN TÍCH / LỰA CHỌN ĐÚNG / THAM KHẢO nhưng thiếu dấu ### nên dính vào phần trước",
    "thieu_nhan_cau_hoi": "Phần đầu không có nhãn \"Câu hỏi:\"",
    "thieu_cach_doc": "Phần đầu không có dòng \"Cách đọc:\"",
    "so_dong_phan_tich_khac_4": "Phần PHÂN TÍCH không có đúng 4 dòng đánh số",
    "dong_phan_tich_dinh_lien": "Các dòng phân tích bị dính liền, không xuống dòng (vd \"…đồng nghĩa.2. 小さい…\")",
    "lech_dap_an": "Số thứ tự trong LỰA CHỌN ĐÚNG khác dap_an_so của đề",
    "thu_tu_phan_tich_lech": "Số thứ tự trong PHÂN TÍCH không khớp thứ tự lựa chọn của đề (vd dòng \"1.\" lại phân tích lựa chọn 4)",
    "lua_chon_khoang_trang_thua": "Lựa chọn viết cách chữ (kiểu N4–N5 hoặc lỗi gõ) nên khác cách viết trong lời giải",
    "co_furigana": "Lời giải có furigana (<ruby>)",
    "ruby_hong": "Lời giải có thẻ ruby hỏng",
    "khong_ton_tai": "Có câu \"không tồn tại / không có nghĩa\"",
    "nhac_han_viet": "Lời giải nhắc tới âm Hán Việt",
}
JA = "぀-ヿ㐀-䶿一-鿿々〆ヶ"


def sections(text):
    parts = [p.strip() for p in re.split(r"(?m)^\s*###\s*$", text)]
    return parts


def issues(r):
    out = []
    q, g = r.get("cau_hoi") or "", r.get("giai_thich_vi") or ""
    if re.search(r"text-decoration(?:-line)?:\s*underline", q):
        out.append("gach_chan_span")
    if re.search(r"<b\b", q):
        out.append("gach_chan_b")
    if "{" in q:
        out.append("gach_chan_ngoac")
    if "｛" in q:
        out.append("gach_chan_ngoac_toan_goc")
    marked = bool(re.search(r"<u\b|text-decoration(?:-line)?:\s*underline|<b\b|[\{｛]", q))
    opts = [normalize_html(r.get(f"lua_chon_{i}", ""))[0] for i in range(1, 5)]
    # dạng này lời giải đánh dấu từ đang hỏi bằng IN ĐẬM ở phần đầu (bỏ qua nhãn in đậm "Câu hỏi:", "Nghĩa:"…)
    head = re.split(r"###", g)[0]
    head_body = re.sub(r"<(b|strong)[^>]*>\s*(Câu hỏi|Cách đọc|Nghĩa)\s*:?\s*</\1>", "", head, flags=re.I)
    head_marked = bool(re.search(r"<(b|strong)\b[^>]*>", head_body, re.I) or
                       re.search(r"<u\b|text-decoration(?:-line)?:\s*underline|[\{｛]", head))
    if not marked:
        out.append("de_khong_danh_dau")
        if not head_marked and sum(len(o) for o in opts) / 4 <= 10:
            out.append("khong_danh_dau_ca_hai")
    elif not head_marked:
        out.append("loi_giai_khong_in_dam")
    t, broken = normalize_html(g)
    parts = sections(t)
    if any(not p for p in parts[1:]):
        out.append("phan_rong")
    parts = [p for p in parts if p]
    up = [p.upper() for p in parts]
    def find(head):
        """Phần bắt đầu bằng tiêu đề; nếu thiếu ### thì tìm tiêu đề ở đầu một dòng bất kỳ."""
        sec = next((p for p in parts if p.upper().startswith(head)), None)
        if sec:
            return sec, False
        m = re.search(rf"(?im)^\s*{head}\s*:?.*", t, re.S)
        return (m.group(0) if m else None), bool(m)
    pt, pt_glued = find("PHÂN TÍCH")
    lc, lc_glued = find("LỰA CHỌN ĐÚNG")
    tk, tk_glued = find("THÔNG TIN THAM KHẢO")
    if not tk and any(u.startswith("MỘT SỐ TỪ") for u in up):
        tk = True
    if not pt:
        out.append("thieu_phan_phan_tich")
    if not lc:
        out.append("thieu_phan_lua_chon_dung")
    if not tk:
        out.append("thieu_phan_tham_khao")
    if pt_glued or lc_glued or tk_glued:
        out.append("thieu_dau_phan_cach")
    head = parts[0] if parts else ""
    if not re.search(r"(?im)^\s*câu hỏi\s*:", head):
        out.append("thieu_nhan_cau_hoi")
    if not re.search(r"(?im)cách đọc\s*:", head):
        out.append("thieu_cach_doc")
    if pt:
        body = re.sub(r"(?i)^\s*phân tích\s*:?", "", pt).strip()
        body = re.split(r"(?im)^\s*(lựa chọn đúng|thông tin tham khảo)", body)[0]
        n_lines = len(re.findall(r"(?m)^\s*[1-5]\s*[\.\)]", body))
        n_all = len(re.findall(rf"(?:^|(?<=[\s\.。」\"”]))([1-5])\s*[\.\)]\s*[{JA}]", body))
        if n_lines != 4:
            out.append("so_dong_phan_tich_khac_4")
        if n_all > n_lines:
            out.append("dong_phan_tich_dinh_lien")
        # dòng "i. X" phải phân tích đúng lựa chọn i của đề
        squash = lambda x: re.sub(r"\s+", "", x or "")  # noqa: E731
        lech = False
        for m in re.finditer(rf"(?:^|(?<=[\s\.。」\"”]))([1-4])\s*[\.\)]\s*([{JA}ー〜～・0-9０-９、]+)", body):
            i, x = int(m.group(1)), squash(m.group(2))
            own = squash(opts[i - 1])
            others = [squash(o) for k, o in enumerate(opts) if k != i - 1]
            if x and not (own.startswith(x) or x.startswith(own)) and any(o and (o.startswith(x) or x.startswith(o)) for o in others):
                lech = True
        if lech:
            out.append("thu_tu_phan_tich_lech")
    if lc:
        m = re.search(r"([1-4])\s*[\.\)]", lc)
        if m and m.group(1) != (r.get("dap_an_so") or "").strip():
            out.append("lech_dap_an")
    if any(re.search(rf"[{JA}] +[{JA}]", o) for o in opts):
        out.append("lua_chon_khoang_trang_thua")
    if "<ruby" in g:
        out.append("co_furigana")
    if broken:
        out.append("ruby_hong")
    if re.search(r"không (tồn tại|có) (từ|nghĩa)", t, re.I):
        out.append("khong_ton_tai")
    if re.search(r"hán[\s-]*việt", t, re.I):
        out.append("nhac_han_viet")
    return out


def main():
    rows = read_csv(os.path.join(DANG, "data", "02_tu_vung_thay_doi_cach_noi.csv"))
    by_issue = collections.defaultdict(list)
    per_row = []
    for r in rows:
        iss = issues(r)
        for i in iss:
            by_issue[i].append(r["question_id"])
        per_row.append({"question_id": r["question_id"], "cau_con": r["cau_con"], "cap_do": r["cap_do"],
                        "so_van_de": len(iss), "van_de": " ".join(iss)})
    summary = [{"van_de": k, "mo_ta": MO_TA[k], "so_cau": len(by_issue.get(k, [])),
                "question_id": ", ".join(by_issue.get(k, []))} for k in MO_TA]
    write_csv(summary, os.path.join(DANG, "bao_cao", "van_de_du_lieu.csv"), ["van_de", "mo_ta", "so_cau", "question_id"])
    write_csv(per_row, os.path.join(DANG, "bao_cao", "van_de_theo_cau.csv"))
    print(f"{len(rows)} câu")
    for s in summary:
        print(f"{s['so_cau']:5}  {s['van_de']:28} vd: {s['question_id'][:60]}")


if __name__ == "__main__":
    main()
