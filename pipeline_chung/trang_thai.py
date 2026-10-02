"""File theo dõi trạng thái: output/reports/trang_thai.csv (mỗi câu một dòng) – mục 7 workflow tổng quát.

Mỗi lần lưu trạng thái, tự tạo lại output/reports/can_kiem_tra.csv: danh sách câu cần người xem
(lỗi pipeline, chờ duyệt, vấn đề bản gốc) kèm việc cần làm."""
import os

from .common import read_csv, write_csv

FIELDS = ["sample_id", "question_id", "cau_con", "cap_do", "khuon_goc", "co", "hash_goc",
          "trang_thai", "giai_doan_loi", "loi", "canh_bao",
          "so_cho_claude_sua_vi", "claude_da_sua_vi", "so_cho_sua_loi_gpt", "so_cho_sua_ban_goc", "so_cho_sua_dinh_dang",
          "co_nghi_noi_dung", "nghi_noi_dung", "co_han_viet", "han_viet",
          "so_cho_claude_sua_ko", "claude_da_sua_ko",
          "ghi_chu_ban_goc", "duyet_vi", "model_gd1", "prompt_gd1", "model_gd2", "prompt_gd2", "cap_nhat"]

# ĐANG_XỬ_LÝ → (GĐ1) LỖI_GĐ1 | LỖI_KỸ_THUẬT | CẦN_SỬA_GĐ1 | GĐ1_XONG → (GĐ2) LỖI_GĐ2 | ĐẠT
TRANG_THAI = ["ĐANG_XỬ_LÝ", "LỖI_KỸ_THUẬT", "LỖI_GĐ1", "CẦN_SỬA_GĐ1", "GĐ1_XONG", "LỖI_GĐ2", "ĐẠT",
              "CHỜ_DUYỆT_NỘI_DUNG", "CHỜ_XỬ_LÝ_HÁN_VIỆT", "ĐÃ_DUYỆT_CTV"]
# ĐÃ_DUYỆT_CTV: câu đã có trong kho da_duyet/ (CTV tiếng Hàn đã chấp nhận) – mọi bước bỏ qua, không chạy lại.
# Cách chia v2 (dạng 01): sau GĐ1, câu có cờ nghi sai nội dung → CHỜ_DUYỆT_NỘI_DUNG; câu có âm Hán Việt → CHỜ_XỬ_LÝ_HÁN_VIỆT.
# Hai trạng thái này KHÔNG được chốt (s1_chot) và KHÔNG được dịch (s2_dich).


class Status:
    def __init__(self, path):
        self.path = path
        self.rows = {r["sample_id"]: r for r in read_csv(path)} if os.path.exists(path) else {}

    def get(self, sid):
        return self.rows.get(sid, {})

    def update(self, sid, **kw):
        import datetime
        r = self.rows.setdefault(sid, {f: "" for f in FIELDS})
        r["sample_id"] = sid
        for k, v in kw.items():
            if isinstance(v, (list, tuple)):
                v = "\n".join(str(x) for x in v)
            r[k] = "" if v is None else str(v)
        r["cap_nhat"] = datetime.datetime.now().isoformat(timespec="seconds")

    def ids(self, *states):
        return [sid for sid, r in self.rows.items() if not states or r.get("trang_thai") in states]

    def save(self):
        write_csv(list(self.rows.values()), self.path, FIELDS)
        write_csv(can_kiem_tra(self.rows.values()), os.path.join(os.path.dirname(self.path), "can_kiem_tra.csv"), CKT_FIELDS)


VIEC_CAN_LAM = {
    "LỖI_KỸ_THUẬT": ("1 – lỗi pipeline", "Lỗi gọi GPT: chạy lại bước 1.1 (s1_gpt_chuyen.py – tự lấy các câu này)"),
    "LỖI_GĐ1": ("1 – lỗi pipeline", "Xem cột loi: sửa prompt rồi chạy lại (s1_gpt_chuyen.py --ids … --force), hoặc gửi nhóm sửa dữ liệu gốc"),
    "CẦN_SỬA_GĐ1": ("1 – lỗi pipeline", "Bị trả lại / Claude phát hiện lỗi JSON VI: chạy s1_claude_goi.py → Claude sửa → s1_kiem_tra.py → s1_chot.py"),
    "CHỜ_DUYỆT_NỘI_DUNG": ("2 – chờ duyệt", "Claude nghi sai nội dung (cột nghi_noi_dung) – không dịch; gửi CTV tiếng Nhật (s3b_xuat_ctv_nhat.py) xác nhận/sửa rồi mới chạy tiếp"),
    "CHỜ_XỬ_LÝ_HÁN_VIỆT": ("2 – chờ duyệt", "Lời giải có âm Hán Việt (cột han_viet) – không dịch cho đến khi chốt cách xử lý âm Hán Việt"),
    "LỖI_GĐ2": ("1 – lỗi pipeline", "Xem cột loi: lỗi ghép / GPT → chạy lại s2_dich.py; lỗi kiểm tra → Claude sửa (s2_claude_goi.py) hoặc s2_dich.py --force"),
}
CKT_FIELDS = ["sample_id", "question_id", "cap_do", "nhom", "trang_thai", "giai_doan_loi", "viec_can_lam",
              "loi", "canh_bao", "nghi_noi_dung", "han_viet", "ghi_chu_ban_goc", "cap_nhat"]


def can_kiem_tra(rows):
    """Câu cần người xem: lỗi pipeline → chờ bạn duyệt GĐ1 → đã xong nhưng có vấn đề bản gốc."""
    out = []
    for r in rows:
        st = r.get("trang_thai", "")
        if st == "ĐÃ_DUYỆT_CTV":
            continue
        if st in VIEC_CAN_LAM:
            nhom, viec = VIEC_CAN_LAM[st]
        elif st == "GĐ1_XONG" and not r.get("duyet_vi"):
            nhom, viec = "2 – chờ duyệt", "Bạn duyệt JSON tiếng Việt: s1_chot.py (câu không đồng ý: --tra-lai … --ly-do …)"
        elif (r.get("ghi_chu_ban_goc") or "").strip():
            nhom, viec = "3 – vấn đề bản gốc", "Không chặn pipeline; gửi nhóm dữ liệu xem các ghi chú [Bản gốc VI] (chưa sửa) và [Đã sửa bản gốc] (Claude đã sửa – cần xác nhận)"
        else:
            continue
        out.append({**{k: r.get(k, "") for k in CKT_FIELDS}, "nhom": nhom, "viec_can_lam": viec})
    return sorted(out, key=lambda x: (x["nhom"], int(x["question_id"] or 0) if str(x["question_id"]).isdigit() else 0))
