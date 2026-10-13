# Hướng dẫn tác tử TẠO – Bước 2.2: dịch sang tiếng Hàn (dạng 13 – Đọc hiểu tổng hợp) · v1

> Phiên bản `s2_claude_dich.13.v1` (2026-10-08). Dạng 13 không dùng GPT API. Model: **Claude Opus 5.5** trong Cowork.
> Bạn là **tác tử TẠO (Claude A)** – tác tử con có ngữ cảnh riêng. Tác tử KIỂM TRA soát bản dịch của bạn sau theo `prompts/s2_claude_kiem_tra.md`, rồi Python kiểm tra (D12, D15, ⟪ ⟫, { }…). Bạn chỉ dịch – không sửa tiếng Việt, không gắn cờ.

## Việc phải làm

1. Đọc **toàn bộ** `output/claude/tao_gd2/_he_thong.md` – hướng dẫn dịch đầy đủ (đã điền bảng thuật ngữ). Đặc biệt:
   - 2 loại trường: **dịch trực tiếp từ tiếng Nhật** (`dich_tu_tieng_nhat: true` – nghĩa câu hỏi, nghĩa lựa chọn, nghĩa câu trích) và **dịch từ tiếng Việt** (nhận xét `analysis`, bản dịch đoạn văn `full_translation`);
   - ngữ cảnh có **đoạn văn A / B** – chỉ để hiểu, **không dịch**; danh sách thường gồm 2–3 câu con của cùng đoạn → câu trích giống nhau dịch **giống hệt**, thuật ngữ / tên riêng thống nhất;
   - **trợ từ sau ⟪ ⟫ theo âm cuối cách đọc tiếng Nhật** (ん → 은/이/을/과/이라는/이며/으로…, nguyên âm → 는/가/를/와/라는/며/로…) (D12);
   - giữ khối ⟪ ⟫, `{ }`, furigana, `\n`, gạch đầu dòng, loại dấu nháy như bản Việt; không thêm ý;
   - văn phong -습니다 ở `analysis`; nghĩa câu / câu trích theo mức lịch sự của câu Nhật.
2. Mở `output/claude/tao_gd2_danh_sach.json`. Với **từng** câu: đọc `file_vao` (`user` = ngữ cảnh + JSON có mã fN; `ids` = mã cần dịch); ghi `file_ra` = **một object** `{"f1": "…", …}` gồm **đúng và đủ** các mã trong `ids`.
3. Ghi file bằng Python ngắn (`json.dump(..., ensure_ascii=False, indent=1)`). Không mở / sửa file khác, không chạy script pipeline.
4. Xong thì báo lại số câu đã dịch và các điểm khó (chỉ mô tả).
