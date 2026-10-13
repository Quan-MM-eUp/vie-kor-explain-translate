# 06. Từ vựng – Ứng dụng từ

| Mục | Giá trị |
|---|---|
| Tên trong sheet "Format giải thích" | Ứng dụng từ |
| Giá trị cột `dang_bai` trong CSV | `ứng dụng từ` |
| Số dòng | 676 (N1: 177, N2: 267, N3: 171, N4: 61) – 60 câu đề có định nghĩa tiếng Nhật sau '……' (N2) |
| Dữ liệu | `data/06_tu_vung_ung_dung_tu.csv` |
| Schema | `schema/vocab_usage.v2.json` (+ `.api.json` cho GPT strict) |
| Cấu hình | `config.json` |
| Cách chạy | `HUONG_DAN_CHAY.md` |

## Pipeline (dựng 2026-10-07 từ dạng 05, cách chia v2)

- **GĐ0** `s0_chuan_bi.py`: chuẩn hóa HTML (kể cả đề có thẻ bị mã hóa `&lt;p&gt;`, furigana kiểu `<翻訳:ほんやく>`, ký tự điều khiển, thẻ cụt), tách đoạn giới thiệu từ / PHÂN TÍCH (câu – Cách đọc – Nghĩa – nhận xét – Sửa lại – Cách đọc – Nghĩa) / LỰA CHỌN ĐÚNG, gắn cờ, gợi ý Sudachi.
- **Schema `vocab_usage.v2`**: `word {ja, paren, definition_ja, meaning, usage}`, `analysis {intro, options[4], conclusion}`, mỗi lựa chọn `{sentence{ja, reading, meaning}, is_correct, usage_ok, analysis, correction{ja, reading, meaning}}`, `correct {index, sentence_ja, note}`. `usage_ok` = lời giải NÓI câu dùng từ đúng (khác `is_correct` = đáp án).
- **GĐ1**: GPT chuyển JSON → Claude kiểm tra theo `prompts/s1_claude_kiem_tra.md` (quy tắc 3d đã duyệt 07/10/2026: câu đúng bị nói sai / bị "Sửa lại", lý do loại không nêu lỗi chính, câu sửa sai, đề có định nghĩa…) → Python K1–K17 + gợi ý R1/R2 → chốt. Mọi cờ nội dung chặn dịch, chuyển CTV tiếng Nhật.
- **GĐ2**: nghĩa câu 4 lựa chọn + nghĩa câu sửa dịch TRỰC TIẾP từ tiếng Nhật; `word.meaning` kết hợp theo từ tiếng Nhật; phần còn lại dịch từ tiếng Việt → Claude kiểm tra → Python (D1, D3, D4, D7, D10).
- **GĐ3**: Excel CTV tiếng Hàn (`s3_xuat_ctv.py`), Excel CTV tiếng Nhật (`s3b_xuat_ctv_nhat.py`), kho mẫu đã duyệt (`s10_luu_da_duyet.py`).

## Lịch sử

| Ngày | Việc |
|---|---|
| 2026-10-07 | Dựng pipeline (schema v2, GĐ0–GĐ3), chạy thử giả lập 676 câu (bản chuyển bằng quy tắc) – kiểm tra Python chỉ báo lỗi ở các câu có lỗi bản gốc thật |

## Cập nhật 2026-10-07 – Quy tắc THAM KHẢO (leader duyệt)

Quy tắc chung: phần tham khảo không gửi GPT, không kiểm tra, không sửa, không gắn cờ, không dịch (`../../workflow/workflow_tong_quat.md` mục 11). Dạng 06 không có phần THÔNG TIN THAM KHẢO (0/676 câu; 5 câu có chữ "tham khảo" chỉ là nghĩa của từ trong phân tích / nghĩa câu, vd 相談, 諮る) và schema `vocab_usage.v2` không có trường tham khảo → **giữ nguyên** pipeline, không câu nào cần áp dụng lại. Đoạn chữ thêm trong LỰA CHỌN ĐÚNG (2 câu, `correct.note`) không phải tham khảo – vẫn kiểm tra và dịch bình thường. `config.json` có khóa `tham_khao`.
