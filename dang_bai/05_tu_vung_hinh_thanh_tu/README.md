# 05. Từ vựng – Hình thành từ

| Mục | Giá trị |
|---|---|
| Tên trong sheet "Format giải thích" | Hình thành từ |
| Giá trị cột `dang_bai` trong CSV | `hình thành từ` |
| Số dòng | 209 (N2: 209) |
| Dữ liệu | `data/05_tu_vung_hinh_thanh_tu.csv` |
| Schema | `vocab_word_formation.v2` (pipeline) – bản v1: ví dụ mẫu bên dưới |
| Ví dụ JSON mẫu | `../../explanation_schema/examples/05_tu_vung_hinh_thanh_tu.json` |

Code và workflow chi tiết của dạng này đặt trong thư mục này.
Khung workflow chi tiết: xem mục 10 trong `../../workflow/workflow_tong_quat.md`.

## Pipeline (dựng 2026-10-06 từ dạng 04)

Chạy mọi lệnh từ thư mục này. Hướng dẫn từng bước: `HUONG_DAN_CHAY.md`.

| Thành phần | Ghi chú |
|---|---|
| Schema | `schema/vocab_word_formation.v2.json` (+ `.api.json`). PHÂN TÍCH trong `analysis{intro, options, conclusion}`; `options[i] = {index, option_ja, label_paren, gloss, compound{ja, reading, meaning}, is_valid, analysis}`; **`is_valid` = lời giải nói từ ghép CÓ tồn tại** (không phải "là đáp án"); `correct.full_sentence {ja, meaning}`; `reference {intro, terms[{ja, reading, meaning}]}` hoặc null |
| Cách chia | v2: Dạng 1 / Dạng 2 (sửa định dạng) + cờ `nghi_noi_dung` → câu có cờ không dịch, chuyển CTV tiếng Nhật |
| Kiểm tra riêng | K7 tham khảo (đủ ví dụ, chép đúng từ / cách đọc); K12 câu hoàn chỉnh chép đúng; K13 giữ số chỗ trống; K14 `is_valid` khớp lời giải; K15 từ ghép chứa lựa chọn (cảnh báo); K16 đáp án bị ghi "không có nghĩa" (cảnh báo); D8 bản Hàn giữ chỗ trống. Không dùng cờ `khong_ton_tai` (câu "không có nghĩa" là cách loại bình thường của dạng này) |
| Gợi ý SudachiPy | W1 từ ghép bị ghi "không có nghĩa" nhưng từ điển có · W2 cách đọc trong ngoặc khác từ điển · W3 ví dụ tham khảo không chứa / đọc khác thành phần đáp án · F1 câu hoàn chỉnh ≠ câu đề + đáp án. **Chỉ là gợi ý** – Claude xác nhận rồi mới gắn cờ. Báo cáo toàn bộ: `output/reports/sudachi_goi_y.csv` |
| Dịch tiếng Hàn | Nghĩa câu đề + nghĩa câu hoàn chỉnh ← tiếng Nhật; nghĩa gốc lựa chọn / nghĩa từ ghép / nghĩa từ tham khảo ← kết hợp theo từ tiếng Nhật; nhận xét + câu giới thiệu tham khảo ← tiếng Việt; câu "không có nghĩa trong tiếng Nhật." là câu cố định |
| Kho đã duyệt | `da_duyet/` |
