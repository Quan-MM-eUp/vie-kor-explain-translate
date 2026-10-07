# Kho mẫu đã được CTV chấp nhận – Dạng 04: Thay đổi cách nói

Cùng quy tắc với kho dạng 01 (`../../01_tu_vung_cach_doc_kanji/da_duyet/README.md`):

- Chỉ thêm mẫu bằng script: `python scripts/s10_luu_da_duyet.py --file <excel CTV> [--chap-nhan "Đạt"] [--bo-mau <id,…>] [--dry-run]`.
- Mẫu trong kho mang trạng thái `ĐÃ_DUYỆT_CTV` trong `output/` → mọi bước bỏ qua (thêm `--ca-da-duyet` nếu vẫn muốn chạy lại).
- Không sửa tay, không xóa file trong kho.

## Lịch sử nhập

| Ngày | File CTV | Số mẫu | Ghi chú |
|---|---|---|---|
| – | – | 0 | Kho mới tạo 2026-10-05 |
| 2026-10-06 | 2026-10-06-CTV-04_dien_tu_theo_van_canh-v1-mau1-100 06.10.2026.xlsx | 79 (Đạt 76 + Sửa nhỏ 3) | Mẫu 1–100. CTV ghi bản sửa ở Ghi chú (không sửa cột vàng); Claude áp dụng trước khi lưu (sua_theo_ctv, s10 --da-sua-theo-ctv): 416, 468 sửa phân tích lựa chọn ở cả VI và KO (lỗi kiến thức của lời giải gốc); 477 sửa Nghĩa câu đề + Nghĩa câu hoàn chỉnh tiếng Hàn (〜てもらう → 받았습니다) |
