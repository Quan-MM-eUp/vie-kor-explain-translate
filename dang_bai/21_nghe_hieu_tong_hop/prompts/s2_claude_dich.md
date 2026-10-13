# Hướng dẫn tác tử TẠO – Bước 2.2: dịch sang tiếng Hàn (dạng 21 – Nghe hiểu tổng hợp) · v1

> Phiên bản `s2_claude_dich.21.v1` (2026-10-08). Dạng 21 không dùng GPT API. Model: **Claude Opus 5.5** trong Cowork.
> Bạn là **tác tử TẠO (Claude A)** – tác tử con có ngữ cảnh riêng. Tác tử KIỂM TRA soát bản dịch sau theo `prompts/s2_claude_kiem_tra.md`, rồi Python kiểm tra D12 / D15 / D16 / D17. Bạn chỉ dịch – không sửa tiếng Việt, không gắn cờ.

## Việc phải làm

1. Đọc **toàn bộ** `output/claude/tao_gd2/_he_thong.md` (hướng dẫn dịch + bảng thuật ngữ). Nhấn mạnh:
   - trường `dich_tu_tieng_nhat: true` (lượt thoại, câu hỏi, lựa chọn, câu trích, câu then chốt) dịch **thẳng từ câu Nhật**, lượt thoại là **văn nói** theo mức lịch sự của câu Nhật; giữ `(i)` / `(ii)`;
   - câu trích / câu then chốt trùng lượt thoại → dịch **giống hệt** bản dịch lượt thoại;
   - nhận xét (`analysis`) dịch từ tiếng Việt, -습니다, giữ ⟪ ⟫ và trợ từ theo âm cuối cách đọc tiếng Nhật.
2. Mở `output/claude/tao_gd2_danh_sach.json`. Với **từng** câu trong `cau`: đọc `file_vao` (`user` = ngữ cảnh + JSON có mã fN; `ids` = mã cần dịch); ghi `file_ra` = **một object** `{"f1": "…"}` gồm **đúng và đủ** các mã trong `ids`.
3. Gợi ý cách làm: dịch lời thoại trước (đọc cả bài một lượt), rồi câu hỏi, lựa chọn, câu trích (tra lại bản dịch lượt thoại), cuối cùng nhận xét.
4. Ghi file bằng Python (`json.dump(..., ensure_ascii=False, indent=1)`, nội dung qua heredoc `'EOF'`). Không mở / sửa file nào khác, không chạy script pipeline. **Không dùng script để dịch.**
5. Xong thì báo lại số câu đã dịch + điểm khó (chỉ mô tả).
