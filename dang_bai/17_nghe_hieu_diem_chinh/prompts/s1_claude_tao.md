# Hướng dẫn tác tử TẠO – Bước 1.1: chuyển lời giải sang JSON tiếng Việt (dạng 17 – Nghe hiểu điểm chính) · v1

> Phiên bản `s1_claude_tao.17.v1` (2026-10-08). Dạng 17 không dùng GPT API. Model: **Claude Opus 5.5** trong Cowork.
> Bạn là **tác tử TẠO (Claude A)** – tác tử con có ngữ cảnh riêng. Một Claude khác (tác tử KIỂM TRA) soát bản của bạn sau theo `prompts/s1_claude_kiem_tra.md`. **Bạn không gắn cờ, không sửa nội dung** – chỉ chuyển đổi trung thành.

## Việc phải làm

1. Đọc **toàn bộ** `prompts/s1_chuyen_json.md` (quy tắc + ví dụ) và schema `schema/reading_listening.v1.api.json` (strict: đủ mọi khóa, không có nội dung thì `null`, không khóa lạ, không có `reference_raw`).
2. Mở `output/claude/tao_gd1_danh_sach.json`. Với **từng** câu trong `cau`:
   - đọc `file_vao` → trường `yeu_cau` (đề, lượt thoại Nhật J0…, dòng Việt gốc V0…, `khung_json`, `luu_y`);
   - so **từng cặp** J ↔ V trong khung (Python ghép theo thứ tự – có thể lệch khi bản Việt gộp / tách / bỏ dòng); sửa những chỗ lệch, điền chỗ `null` theo mục 3 của `s1_chuyen_json.md`;
   - ghi JSON hoàn chỉnh vào `file_ra` (`output/json_vi/claude_tao/<id>.json`).
3. Không mở / sửa file nào khác (không đọc `checked`, `final`, bản của câu khác, kết quả kiểm tra…). Không chạy script của pipeline, **trừ** lệnh tự kiểm có trong lời giao việc.
4. Xong cả danh sách thì báo lại: số câu đã ghi, câu nào gặp điểm khó (lời thoại / bản Việt lệch nhiều, nghi dịch sai, Thông tin không khớp…) – **chỉ mô tả**.

## Ghi file

- Dùng Python ngắn: đọc `khung_json` từ `file_vao`, sửa bằng code (gán theo chỉ số dòng) rồi `json.dump(obj, f, ensure_ascii=False, indent=1)` – tránh gõ lại cả lời thoại tiếng Nhật bằng tay (dễ sai chữ → K-LT báo lỗi).
- Chuỗi giữ `\n` như lời giải; không thêm khoảng trắng đầu / cuối.

## Lỗi hay gặp (tránh)

- Ghép lệch một dòng (nghĩa của lượt sau gán cho lượt trước) – nhất là khi bản Việt bỏ dòng dẫn, gộp câu hỏi vào dòng đầu, hoặc gộp 2 lượt liền nhau.
- Để sót nhãn người nói tiếng Việt (`Nam:`, `F:`) đầu `meaning.vi`; để sót `(i)` trong `key_info`.
- Đổi chữ tiếng Nhật khi gộp / tách lượt (mất `。`, mất khoảng trắng toàn góc của N5 vẫn được – Python bỏ khoảng trắng khi so, nhưng không được mất chữ).
- Đưa câu dẫn tình huống vào `question.meaning`; thêm 4 lựa chọn vào `full_translation`.
