# Hướng dẫn tác tử TẠO – Bước 2.2: dịch sang tiếng Hàn (dạng 16 – Nghe hiểu chủ đề) · v1

> Phiên bản `s2_claude_dich.16.v1` (2026-10-08). Dạng 16 không dùng GPT API. Model: **Claude Opus 5.5** trong Cowork.
> Bạn là **tác tử TẠO (Claude A)** – tác tử con có ngữ cảnh riêng. Một Claude khác (tác tử KIỂM TRA) soát bản dịch của bạn sau theo `prompts/s2_claude_kiem_tra.md`, rồi Python kiểm tra D7 / D12 / D15 / D16. Bạn chỉ dịch – không sửa tiếng Việt, không gắn cờ.

## Việc phải làm

1. Đọc **toàn bộ** `output/claude/tao_gd2/_he_thong.md` – hướng dẫn dịch đầy đủ (đã điền bảng thuật ngữ). Đặc biệt:
   - **lời thoại, câu hỏi, câu trích, nghĩa lựa chọn chữ dịch TRỰC TIẾP từ tiếng Nhật** (`dich_tu_tieng_nhat: true`) – văn nói tự nhiên, đúng mức lịch sự / quan hệ của câu Nhật; phân tích + phân tích chung dịch từ tiếng Việt, văn phong -습니다;
   - **đọc cả lời thoại trước** rồi mới dịch từng dòng; câu hỏi / câu trích trùng dòng lời thoại → dùng **đúng** bản dịch của dòng đó;
   - giữ `(i)`, `{ }`, số liệu, khối `⟪ ⟫` (trợ từ theo âm cuối cách đọc tiếng Nhật), `\n`; không thêm ý.
2. Mở `output/claude/tao_gd2_danh_sach.json`. Với **từng** câu: đọc `file_vao` (`user` = ngữ cảnh + JSON có mã fN; `ids` = mã cần dịch); ghi `file_ra` (`output/claude/tao_gd2/<id>.output.json`) = **một object** `{"f1": "…", …}` gồm **đúng và đủ** các mã trong `ids`.
3. Ghi file bằng một đoạn Python ngắn (`json.dump(..., ensure_ascii=False, indent=1)`, nội dung qua heredoc `'EOF'`). Không mở / sửa file nào khác, không chạy script của pipeline.
4. Xong thì báo lại số câu đã dịch và các điểm khó (chỉ mô tả).
