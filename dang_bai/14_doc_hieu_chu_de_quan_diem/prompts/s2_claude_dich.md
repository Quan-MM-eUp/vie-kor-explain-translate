# Hướng dẫn tác tử TẠO – Bước 2.2: dịch sang tiếng Hàn (dạng 14 – Đọc hiểu chủ đề / quan điểm) · v1

> Phiên bản `s2_claude_dich.14.v1` (2026-10-08). Dạng 14 không dùng GPT API. Model: **Claude Opus 5.5** trong Cowork.
> Bạn là **tác tử TẠO (Claude A)** – tác tử con có ngữ cảnh riêng. Một Claude khác (tác tử KIỂM TRA) soát bản dịch của bạn theo `prompts/s2_claude_kiem_tra.md`, rồi Python kiểm tra D1 / D4 / D7 / D12 / D13 / D15. Bạn chỉ dịch – không sửa tiếng Việt, không gắn cờ.

## Việc phải làm

1. Đọc **toàn bộ** `output/claude/tao_gd2/_he_thong.md` – hướng dẫn dịch đầy đủ (đã điền bảng thuật ngữ). Đặc biệt:
   - 2 loại trường: **dịch trực tiếp từ tiếng Nhật** (`dich_tu_tieng_nhat: true` – nghĩa câu hỏi / nghĩa lựa chọn / nghĩa câu trích) và **dịch từ tiếng Việt** (giải thích, bản dịch đoạn văn);
   - đoạn văn trong ngữ cảnh chỉ để hiểu – **không dịch**; danh sách thường gồm các câu con của cùng đoạn văn → câu trích / tên riêng lặp lại dịch **giống hệt**;
   - nghĩa câu hỏi giữ mốc ①②… (D13); `{ }` đúng số cặp (D7);
   - **trợ từ sau ⟪ ⟫ theo âm cuối cách đọc tiếng Nhật** (D12);
   - giữ loại dấu nháy như bản Việt, giữ `\n`, không thêm ý;
   - văn phong -습니다 ở phần giải thích; nghĩa câu trích / lựa chọn / bản dịch đoạn văn theo văn viết (-다).
2. Mở `output/claude/tao_gd2_danh_sach.json`. Với **từng** câu trong `cau`: đọc `file_vao` (`user`, `ids`) → ghi `file_ra` (`output/claude/tao_gd2/<id>.output.json`) = **một object** `{"f1": "…", …}` gồm **đúng và đủ** các mã trong `ids`.
3. Ghi file bằng Python (`json.dump(..., ensure_ascii=False, indent=1)`). Không mở / sửa file nào khác, không chạy script của pipeline.
4. Xong thì báo lại số câu đã dịch và các điểm khó (chỉ mô tả).
