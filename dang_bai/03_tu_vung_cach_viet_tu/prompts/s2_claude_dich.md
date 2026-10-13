# Hướng dẫn tác tử TẠO – Bước 2.2: dịch sang tiếng Hàn (dạng 03 – Cách viết từ) · v1

> Phiên bản `s2_claude_dich.v1` (2026-10-08). Thay cho bước GPT API (`s2_dich.py`). Model: **Claude Opus 5.5** trong Cowork.
> Bạn là **tác tử TẠO (Claude A)** – tác tử con có ngữ cảnh riêng. Một Claude khác (tác tử KIỂM TRA) soát bản dịch của bạn sau theo `prompts/s2_claude_kiem_tra.md`, rồi Python kiểm tra. Bạn chỉ dịch – không sửa tiếng Việt, không gắn cờ.

## Việc phải làm

1. Đọc **toàn bộ** `output/claude/tao_gd2/_he_thong.md` – hướng dẫn dịch đầy đủ (đúng bản GPT đã dùng, đã điền bảng thuật ngữ). Mọi quy tắc áp dụng nguyên vẹn, đặc biệt:
   - 3 loại trường: **dịch trực tiếp từ tiếng Nhật** (`dich_tu_tieng_nhat: true` – nghĩa câu đề `question.meaning`, giữ đúng số cặp `{ }` bọc phần tương ứng với từ gạch chân), **kết hợp** (có `lua_chon_tieng_nhat` – phân tích lựa chọn: nghĩa trong `có nghĩa là "…"` là nghĩa của **chính lựa chọn tiếng Nhật** (đọc theo `cach_doc`), đúng từ loại / dạng, kể cả khi bản Việt lệch; phần còn lại dịch từ tiếng Việt), **dịch từ tiếng Việt** (mở đầu, đoạn giải thích bẫy `conclusion`);
   - lựa chọn bị lời giải nói "không tồn tại": dịch nguyên nhận xét, không tự thêm nghĩa;
   - **trợ từ sau ⟪ ⟫ theo âm cuối CÁCH ĐỌC tiếng Nhật** (ん → 은/이/을/과/이라는/이라고/이며/으로; mọi kana khác → 는/가/를/와/라는/라고/며/로), kể cả khi giữa ⟫ và trợ từ có dấu nháy / ngoặc;
   - giữ nguyên khối ⟪ ⟫ (kể cả furigana ｜…《…》), số cặp `{ }`, loại dấu nháy, `\n`;
   - văn phong -습니다 ở phần nhận xét; câu ví dụ theo mức lịch sự của câu Nhật; không thêm ý.
2. Mở `output/claude/tao_gd2_danh_sach.json`. Với **từng** câu trong `cau`:
   - đọc `file_vao`: `user` là đúng tin nhắn GPT từng nhận (ngữ cảnh đề + JSON lời giải có gắn mã fN), `ids` là các mã cần dịch;
   - ghi `file_ra` (`output/claude/tao_gd2/<id>.output.json`) = **một object** `{"f1": "…", "f2": "…"}` gồm **đúng và đủ** các mã trong `ids`.
3. Ghi file bằng một đoạn Python ngắn (`json.dump(..., ensure_ascii=False, indent=1)`). Không mở / sửa file nào khác, không chạy script của pipeline.
4. Xong thì báo lại số câu đã dịch và các điểm khó (chỉ mô tả).
