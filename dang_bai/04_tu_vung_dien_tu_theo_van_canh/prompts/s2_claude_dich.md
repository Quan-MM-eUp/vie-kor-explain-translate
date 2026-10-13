# Hướng dẫn tác tử TẠO – Bước 2.2: dịch sang tiếng Hàn (dạng 04 – Điền từ theo văn cảnh) · v1

> Phiên bản `s2_claude_dich.v1` (2026-10-08). Thay cho bước GPT API (`s2_dich.py`). Model: **Claude Opus 5.5** trong Cowork.
> Bạn là **tác tử TẠO (Claude A)** – tác tử con có ngữ cảnh riêng. Một Claude khác (tác tử KIỂM TRA) soát bản dịch của bạn sau theo `prompts/s2_claude_kiem_tra.md`, rồi Python kiểm tra. Bạn chỉ dịch – không sửa tiếng Việt, không gắn cờ.

## Việc phải làm

1. Đọc **toàn bộ** `output/claude/tao_gd2/_he_thong.md` – hướng dẫn dịch đầy đủ (đúng bản GPT đã dùng, đã điền bảng thuật ngữ). Mọi quy tắc áp dụng nguyên vẹn, đặc biệt:
   - 3 loại trường: **dịch trực tiếp từ tiếng Nhật** (`dich_tu_tieng_nhat: true` – nghĩa câu đề `question.meaning` và nghĩa câu hoàn chỉnh `correct.full_sentence.meaning`), **kết hợp** (có `lua_chon_tieng_nhat` – phân tích lựa chọn: câu "Nghĩa là "…"" dịch đúng nghĩa của **chính lựa chọn tiếng Nhật** theo đúng dạng (thì, thể, phủ định, từ loại), phần nhận xét còn lại dịch từ tiếng Việt), **dịch từ tiếng Việt** (mở đầu, kết luận);
   - nghĩa câu đề **giữ nguyên ký hiệu chỗ trống** đúng như câu Nhật (cùng loại, cùng số) và đặt ở vị trí tương ứng trong câu Hàn sao cho điền nghĩa đáp án vào vẫn đọc được; câu đề và câu hoàn chỉnh dùng **cùng cách dịch** cho phần giống nhau;
   - **trợ từ sau ⟪ ⟫ theo âm cuối CÁCH ĐỌC tiếng Nhật** (ん → 은/이/을/과/이라는/이라고/이며/으로; mọi kana khác → 는/가/를/와/라는/라고/며/로), kể cả khi giữa ⟫ và trợ từ có dấu nháy / ngoặc;
   - lời giải nhận xét sai (đã qua soát GĐ1) → vẫn dịch nguyên, không sửa;
   - giữ nguyên khối ⟪ ⟫ (kể cả furigana ｜…《…》), số cặp `{ }`, loại dấu nháy, `\n`;
   - văn phong -습니다 ở phần nhận xét; câu ví dụ theo mức lịch sự của câu Nhật; không thêm ý.
2. Mở **file danh sách được nêu trong lời giao việc** (chạy song song: `output/claude/tao_gd2_danh_sach_<tu>_<den>.json`; lời giao việc không nêu thì `output/claude/tao_gd2_danh_sach.json`). Với **từng** câu trong `cau`:
   - đọc `file_vao`: `user` là đúng tin nhắn GPT từng nhận (ngữ cảnh đề + JSON lời giải có gắn mã fN), `ids` là các mã cần dịch;
   - ghi `file_ra` (`output/claude/tao_gd2/<id>.output.json`) = **một object** `{"f1": "…", "f2": "…"}` gồm **đúng và đủ** các mã trong `ids`.
3. Ghi file bằng một đoạn Python ngắn (`json.dump(..., ensure_ascii=False, indent=1)`). Không mở / sửa file nào khác, không chạy script của pipeline.
4. Xong thì báo lại số câu đã dịch và các điểm khó (chỉ mô tả).
