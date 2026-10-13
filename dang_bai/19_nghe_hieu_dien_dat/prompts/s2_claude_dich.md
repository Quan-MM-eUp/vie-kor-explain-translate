# Hướng dẫn tác tử TẠO – Bước 2.2: dịch sang tiếng Hàn (dạng 19 – Nghe hiểu diễn đạt) · v1

> Phiên bản `s2_claude_dich.19.v1` (2026-10-08). Dạng 19 không dùng GPT API. Model: **Claude Opus 5.5** trong Cowork.
> Bạn là **tác tử TẠO (Claude A)** – tác tử con có ngữ cảnh riêng. Một Claude khác (tác tử KIỂM TRA) soát bản dịch của bạn sau theo `prompts/s2_claude_kiem_tra.md`, rồi Python kiểm tra D7 / D12 / D15. Bạn chỉ dịch – không sửa tiếng Việt, không gắn cờ.

## Việc phải làm

1. Đọc **toàn bộ** `output/claude/tao_gd2/_he_thong.md` – hướng dẫn dịch đầy đủ (đã điền bảng thuật ngữ + câu nói cố định). Đặc biệt:
   - 2 loại trường: **dịch trực tiếp từ tiếng Nhật** (`dich_tu_tieng_nhat: true` – câu tình huống, câu nói) và **dịch từ tiếng Việt** (phân tích);
   - câu nói: đúng **mức lịch sự / sắc thái / ai làm cho ai** như câu Nhật; lời chào cố định → câu tương đương tiếng Hàn; câu nói SAI vẫn dịch đúng như câu đang viết;
   - `何と言いますか` → `뭐라고 말합니까?`;
   - **trợ từ sau ⟪ ⟫ theo âm cuối cách đọc tiếng Nhật** (D12); giữ ngoặc 「」, `\n`, `{ }`; văn phong -습니다 ở phân tích; không thêm ý.
2. Mở `output/claude/tao_gd2_danh_sach.json`. Với **từng** câu trong `cau`: đọc `file_vao` (`user` = ngữ cảnh + JSON có mã fN, `ids` = các mã cần dịch); ghi `file_ra` (`output/claude/tao_gd2/<id>.output.json`) = **một object** `{"f1": "…", …}` gồm **đúng và đủ** các mã trong `ids`.
3. Ghi file bằng Python (`json.dump(..., ensure_ascii=False, indent=1)`). Không mở / sửa file nào khác, không chạy script của pipeline.
4. Xong thì báo lại số câu đã dịch và các điểm khó (chỉ mô tả).
