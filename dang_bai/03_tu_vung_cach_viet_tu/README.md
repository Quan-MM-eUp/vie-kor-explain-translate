# 03. Từ vựng – Cách viết từ

| Mục | Giá trị |
|---|---|
| Tên trong sheet "Format giải thích" | Cách viết từ |
| Giá trị cột `dang_bai` trong CSV | `cách viết từ` |
| Số dòng | 1633 (N1: 449, N2: 329, N3: 401, N4: 258, N5: 196) |
| Dữ liệu | `data/03_tu_vung_cach_viet_tu.csv` |
| Schema | `vocab_writing.v1` |
| Ví dụ JSON mẫu | `../../explanation_schema/examples/03_tu_vung_cach_viet_tu.json` |

Code và workflow chi tiết của dạng này đặt trong thư mục này.
Khung workflow chi tiết: xem mục 10 trong `../../workflow/workflow_tong_quat.md`.

## Pipeline (dựng 2026-10-05 theo cách làm v3 của dạng 01/02)

Chạy mọi lệnh từ thư mục này. Hướng dẫn từng bước: `HUONG_DAN_CHAY.md`.

| Thành phần | Ghi chú |
|---|---|
| Schema | `schema/vocab_writing.v2.json` (+ `.api.json` gửi GPT). Khác v1: PHÂN TÍCH trong `analysis{intro, options, conclusion}` – `conclusion` = đoạn giải thích bẫy; `options[i] = {index, option_ja, exists, reading, analysis}` – `analysis` giữ toàn bộ dòng, `reading` chép từ "Đọc là"; `reference` là một chuỗi |
| Cách chia | v2: Dạng 1 / Dạng 2 (sửa định dạng) + cờ `nghi_noi_dung` → câu có cờ không dịch, chuyển CTV tiếng Nhật |
| Gợi ý từ điển | SudachiPy (`pip install sudachipy sudachidict_core`): S1 đáp án ↔ kana gạch chân, S2 "Đọc là", S3 "không tồn tại" – chỉ gợi ý cho Claude; báo cáo toàn bộ: `output/reports/sudachi_goi_y.csv` |
| Dịch tiếng Hàn | Nghĩa câu ← tiếng Nhật; nghĩa của lựa chọn ← lựa chọn tiếng Nhật (kết hợp); dòng nghĩa câu ví dụ ← câu ví dụ tiếng Nhật; còn lại ← tiếng Việt |
| Prompt | `prompts/s1_chuyen_json.md` (GPT), `s1_claude_kiem_tra.md` (Claude, quy tắc 3d/3e riêng dạng 03), `s2_dich_ko.md` (GPT), `s2_claude_kiem_tra.md` (Claude) |
| Kho đã duyệt | `da_duyet/` |
