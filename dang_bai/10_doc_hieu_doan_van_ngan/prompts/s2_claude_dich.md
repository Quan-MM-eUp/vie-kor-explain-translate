# Hướng dẫn tác tử TẠO – Bước 2.2: dịch sang tiếng Hàn (dạng 10 – Đọc hiểu đoạn văn ngắn) · v1

> Phiên bản `s2_claude_dich.10.v1` (2026-10-08). Model: **Claude Opus 5.5** trong Cowork (dạng 10 không dùng GPT API).
> Bạn là **tác tử TẠO (Claude A)** – tác tử con có ngữ cảnh riêng. Tác tử KIỂM TRA soát bản dịch của bạn sau theo `prompts/s2_claude_kiem_tra.md`, rồi Python kiểm tra (⟪ ⟫, { }, furigana, D-QT, D12). Bạn chỉ dịch – không sửa tiếng Việt, không gắn cờ.

## Việc phải làm

1. Đọc **toàn bộ** `output/claude/tao_gd2/_he_thong.md` – hướng dẫn dịch đầy đủ + bảng thuật ngữ. Trọng tâm:
   - 2 loại trường: **kết hợp** (nghĩa câu hỏi, nghĩa lựa chọn, bản dịch câu trích dẫn – nghĩa theo **tiếng Nhật**), **dịch từ tiếng Việt** (phân tích, phân tích chung, bản dịch đoạn văn khuôn B);
   - ngữ cảnh luôn có **đoạn văn tiếng Nhật** – dùng để chọn từ đúng (tên riêng, thuật ngữ, ai làm gì);
   - **trợ từ sau ⟪ ⟫ theo âm cuối cách đọc tiếng Nhật** (D12);
   - cùng một câu trích dẫn lặp lại → dịch giống hệt (D-QT);
   - giữ `\n`, `{ }`, gạch đầu dòng, loại dấu nháy; không thêm ý; văn phong -습니다 ở phần phân tích.
2. Mở `output/claude/tao_gd2_danh_sach.json`. Với **từng** câu trong `cau`: đọc `file_vao` (`user` = ngữ cảnh + JSON có mã fN; `ids` = mã cần dịch); ghi `file_ra` (`output/claude/tao_gd2/<id>.output.json`) = **một object** `{"fN": "…"}` gồm **đúng và đủ** các mã trong `ids`.
3. Ghi file bằng một đoạn Python ngắn (`json.dump(..., ensure_ascii=False, indent=1)`). Không mở / sửa file nào khác, không chạy script của pipeline.
4. Xong thì báo lại số câu đã dịch và điểm khó (chỉ mô tả).
