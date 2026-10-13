# Hướng dẫn tác tử TẠO – Bước 2.2: dịch sang tiếng Hàn (dạng 09 – Ngữ pháp theo đoạn văn) · v1

> Phiên bản `s2_claude_dich.09.v1` (2026-10-08). Dạng 09 không dùng GPT API. Model: **Claude Opus 5.5** trong Cowork.
> Bạn là **tác tử TẠO (Claude A)** – tác tử con có ngữ cảnh riêng. Một Claude khác (tác tử KIỂM TRA) soát bản dịch của bạn sau theo `prompts/s2_claude_kiem_tra.md`, rồi Python kiểm tra D7 / D12 / D13 / D14. Bạn chỉ dịch – không sửa tiếng Việt, không gắn cờ.

## Việc phải làm

1. Đọc **toàn bộ** `output/claude/tao_gd2/_he_thong.md` – hướng dẫn dịch đầy đủ (đúng bản GPT đã dùng, đã điền bảng thuật ngữ). Mọi quy tắc áp dụng nguyên vẹn, đặc biệt:
   - 3 loại trường: **dịch trực tiếp từ tiếng Nhật** (`dich_tu_tieng_nhat: true` – nghĩa câu đề / câu áp dụng / câu hoàn chỉnh), **kết hợp** (Ý nghĩa mẫu ngữ pháp, theo `tu_tieng_nhat`), **dịch từ tiếng Việt**;
   - **dạng 09:** ngữ cảnh có đoạn văn – chỉ để hiểu, **không dịch**; danh sách thường gồm 4 câu của cùng đoạn văn → câu / cụm lặp lại giữa các câu dịch **giống nhau**;
   - nghĩa câu đề giữ đúng ký hiệu chỗ trống (`[1]`, `（1）`, `[1-a]`…) như **bản tiếng Việt của nghĩa câu đề** (Python D13 so số chỗ trống với bản Việt – nếu lời giải Việt đã điền sẵn chỗ trống thì bản Hàn cũng điền);
   - nghĩa câu hoàn chỉnh **giống hệt** bản dịch nghĩa câu áp dụng của đáp án khi câu Nhật giống nhau (D14);
   - **trợ từ sau ⟪ ⟫ theo âm cuối cách đọc tiếng Nhật** (ん → 은/이/을/과/이라는/이며/으로…, nguyên âm → 는/가/를/와/라는/며/로…) (D12);
   - thuật ngữ có kana giữ khối ⟪ ⟫ như bản Việt: `Tính từ đuôi ⟪な⟫` → `⟪な⟫형용사`, `Động từ thể ⟪て⟫` → `동사 ⟪て⟫형`;
   - giữ loại dấu nháy như bản Việt (`'…'` không đổi thành `‘…’`), giữ `\n`, `{ }`, `+ / ( )`, không thêm ý (vd không tự thêm '만', 'chỉ', 'chắc chắn');
   - văn phong -습니다 ở phần giải thích; câu ví dụ theo mức lịch sự của câu Nhật.
2. Mở **file danh sách được nêu trong lời giao việc** (chạy song song: `output/claude/tao_gd2_danh_sach_<tu>_<den>.json`; lời giao việc không nêu thì `output/claude/tao_gd2_danh_sach.json`). Với **từng** câu trong `cau`:
   - đọc `file_vao`: `user` là đúng tin nhắn GPT từng nhận (ngữ cảnh đề + JSON lời giải có gắn mã fN), `ids` là các mã cần dịch;
   - ghi `file_ra` (`output/claude/tao_gd2/<id>.output.json`) = **một object** `{"f1": "…", "f2": "…"}` gồm **đúng và đủ** các mã trong `ids` (không thêm mã khác, không bỏ mã nào).
3. Ghi file bằng một đoạn Python ngắn (`json.dump(..., ensure_ascii=False, indent=1)`). Không mở / sửa file nào khác, không chạy script của pipeline.
4. Xong thì báo lại số câu đã dịch và các điểm khó (chỉ mô tả).
