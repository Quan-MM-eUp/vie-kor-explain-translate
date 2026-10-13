# Hướng dẫn tác tử TẠO – Bước 2.2: dịch sang tiếng Hàn (dạng 18 – Nghe hiểu khái quát) · v1

> Phiên bản `s2_claude_dich.18.v1` (2026-10-08). Dạng 18 không dùng GPT API. Model: **Claude Opus 5.5** trong Cowork.
> Bạn là **tác tử TẠO (Claude A)** – tác tử con có ngữ cảnh riêng. Tác tử KIỂM TRA soát bản dịch của bạn theo `prompts/s2_claude_kiem_tra.md`, rồi Python kiểm tra D12 / D15 / D16. Bạn chỉ dịch – không sửa tiếng Việt, không gắn cờ.

## Việc phải làm

1. Đọc **toàn bộ** `output/claude/tao_gd2/_he_thong.md` – hướng dẫn dịch đầy đủ (đã điền bảng thuật ngữ). Đặc biệt:
   - 2 loại trường: **dịch trực tiếp từ tiếng Nhật** (`dich_tu_tieng_nhat: true` – lời thoại, câu hỏi, lựa chọn, câu trích) và **dịch từ tiếng Việt** (`analysis`);
   - lời thoại giữ **sắc thái nói** (반말 / 해요체 / 하십시오체 theo câu Nhật, cùng người nói cùng mức lịch sự);
   - câu trích **dịch giống hệt** dòng lời thoại tương ứng; câu trích lặp ở nhiều lựa chọn dịch giống nhau;
   - **trợ từ sau ⟪ ⟫ theo âm cuối cách đọc tiếng Nhật**; giữ ⟪ ⟫, furigana, `\n`, loại dấu nháy như bản Việt; không thêm ý;
   - `analysis` văn phong -습니다; nghĩa câu thoại / lựa chọn nhắc lại trong `analysis` dùng đúng bản dịch đã chọn.
2. Mở `output/claude/tao_gd2_danh_sach.json`. Với **từng** câu trong `cau`: đọc `file_vao` (`user` = ngữ cảnh + JSON có mã fN, `ids` = mã cần dịch); ghi `file_ra` (`output/claude/tao_gd2/<id>.output.json`) = **một object** `{"f1": "…", …}` gồm **đúng và đủ** các mã trong `ids`.
3. Gợi ý thứ tự: dịch **toàn bộ lời thoại trước** (thống nhất sắc thái), rồi câu hỏi, lựa chọn, câu trích (chép lại bản dịch dòng tương ứng), cuối cùng `analysis`.
4. Ghi file bằng Python (`json.dump(..., ensure_ascii=False, indent=1)`, heredoc `'EOF'`). Không mở / sửa file nào khác, không chạy script của pipeline.
5. Xong thì báo lại số câu đã dịch, số mã mỗi câu, điểm khó (chỉ mô tả).
