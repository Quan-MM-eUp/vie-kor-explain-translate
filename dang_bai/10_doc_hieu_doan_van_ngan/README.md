# 10. Đọc hiểu – Đoạn văn ngắn

| Mục | Giá trị |
|---|---|
| Tên trong sheet "Format giải thích" | Đoạn văn ngắn |
| Giá trị cột `dang_bai` trong CSV | `đoạn văn ngắn` |
| Số dòng | 847 (N1: 118, N2: 237, N3: 195, N4: 171, N5: 126) |
| Dữ liệu | `data/10_doc_hieu_doan_van_ngan.csv` |
| Schema | `reading_listening.v1` (+ `reference_raw`) – `schema/reading_listening.v1.json` |
| Ví dụ JSON mẫu | `../../explanation_schema/examples/10_doc_hieu_doan_van_ngan.json` |

Code và workflow chi tiết của dạng này đặt trong thư mục này.
Khung workflow chi tiết: xem mục 10 trong `../../workflow/workflow_tong_quat.md`.

## Trạng thái (2026-10-08)

Pipeline dạng 10 đã dựng (Claude Opus 5.5 Cowork, không GPT), giai đoạn 0 đã chạy, **chưa chạy lô nào**. Chạy: xem `HUONG_DAN_CHAY.md` → `SO_TAY_CHAY.md`; tiến độ và quyết định: `NHAT_KY.md`.

| Thành phần | File |
|---|---|
| Cấu hình | `config.json` (lô 10, lô nhỏ 5 cho khuôn B / đoạn văn dài, ngưỡng K-TD 90 %) |
| Tách khung + kiểm tra K + Excel | `scripts/_dang.py` (phần riêng dạng 10 ở cuối file) |
| Đầu vào tác tử TẠO | `scripts/_dau_vao.py` (GĐ1: `khung_python` + `luu_y`; GĐ2: kèm đoạn văn tiếng Nhật) |
| Dịch GĐ2 | `scripts/_dich_v3.py` (trường kết hợp: nghĩa câu hỏi / lựa chọn / trích dẫn; D-QT, D12) |
| Prompt | `prompts/` (8 file: chuyển JSON, tác tử TẠO, kiểm tra GĐ1/GĐ2, dịch, 2 lời giao việc) |
