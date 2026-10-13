# Kho mẫu đã được CTV chấp nhận – Dạng 05: Hình thành từ

Cùng quy tắc với kho dạng 01 (`../../01_tu_vung_cach_doc_kanji/da_duyet/README.md`):

- Chỉ thêm mẫu bằng script: `python scripts/s10_luu_da_duyet.py --file <excel CTV> [--chap-nhan "Đạt"] [--da-sua-theo-ctv <id,…>] [--bo-mau <id,…>] [--dry-run]`.
- Mẫu trong kho mang trạng thái `ĐÃ_DUYỆT_CTV` trong `output/` → mọi bước bỏ qua (thêm `--ca-da-duyet` nếu vẫn muốn chạy lại).
- Không sửa tay, không xóa file trong kho.

## Lịch sử nhập

| Ngày | File CTV | Số mẫu | Ghi chú |
|---|---|---|---|
| 2026-10-07 | 2026-10-06-CTV-05_hinh_thanh_tu-v1-mau1-100 07.10.2026.xlsx | 56 (Đạt 54 + Sửa nhỏ 2) | Mẫu 1–100. CTV không sửa cột tiếng Hàn. 47149 (nhận xét lựa chọn 4: 当段階 có thể mang nghĩa "giai đoạn đó", nhưng câu cần 現段階) và 47162 (Tham khảo: 出産率 → 出生率 しゅっしょうりつ – tỷ lệ sinh): đã sửa cả VI và KO theo góp ý CTV (sua_theo_ctv) trước khi lưu |
