# 04. Từ vựng – Điền từ theo văn cảnh

| Mục | Giá trị |
|---|---|
| Tên trong sheet "Format giải thích" | Điền từ theo văn cảnh |
| Giá trị cột `dang_bai` trong CSV | `điền từ theo văn cảnh` |
| Số dòng | 1187 (N1: 208, N2: 311, N3: 248, N4: 215, N5: 205) |
| Dữ liệu | `data/04_tu_vung_dien_tu_theo_van_canh.csv` |
| Schema | `vocab_context_fill.v1` |
| Ví dụ JSON mẫu | `../../explanation_schema/examples/04_tu_vung_dien_tu_theo_van_canh.json` |

Code và workflow chi tiết của dạng này đặt trong thư mục này.
Khung workflow chi tiết: xem mục 10 trong `../../workflow/workflow_tong_quat.md`.

## Pipeline (dựng 2026-10-06 theo cách làm v3 của dạng 02/03)

Chạy mọi lệnh từ thư mục này. Hướng dẫn từng bước: `HUONG_DAN_CHAY.md`.

| Thành phần | Ghi chú |
|---|---|
| Schema | `schema/vocab_context_fill.v2.json` (+ `.api.json`). PHÂN TÍCH trong `analysis{intro, options, conclusion}`; `options[i] = {index, option_ja, label_paren, analysis}` – `label_paren` chép nguyên ngoặc ở nhãn (chữ Hán hoặc cách đọc); `correct.full_sentence {ja, meaning}` = "Câu hoàn chỉnh" + "Nghĩa"; `reference` luôn null (dạng này không có tham khảo) |
| Cách chia | v2: Dạng 1 / Dạng 2 (sửa định dạng) + cờ `nghi_noi_dung` → câu có cờ không dịch, chuyển CTV tiếng Nhật |
| Kiểm tra riêng | K12 câu hoàn chỉnh chép đúng; K13 giữ số chỗ trống; D8 bản Hàn giữ chỗ trống; F1 (SudachiPy) câu hoàn chỉnh ≠ câu đề + đáp án – gợi ý, báo cáo toàn bộ: `output/reports/sudachi_goi_y.csv` |
| Dịch tiếng Hàn | Nghĩa câu đề + nghĩa câu hoàn chỉnh ← tiếng Nhật; câu "Nghĩa là" của lựa chọn ← lựa chọn tiếng Nhật (kết hợp); còn lại ← tiếng Việt |
| Kho đã duyệt | `da_duyet/` |
