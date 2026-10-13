# Hướng dẫn tác tử TẠO – Bước 2.2: dịch sang tiếng Hàn (dạng 12 – Đọc hiểu: Đoạn văn dài) · v1

> Phiên bản `s2_claude_dich.12.v1` (2026-10-08). Dạng 12 không dùng GPT API. Model: **Claude Opus 5.5** trong Cowork.
> Bạn là **tác tử TẠO (Claude A)** – tác tử con có ngữ cảnh riêng. Một Claude khác (tác tử KIỂM TRA) soát bản dịch của bạn sau theo `prompts/s2_claude_kiem_tra.md`, rồi Python kiểm tra D7 / D12 / D15 / D4. Bạn chỉ dịch – không sửa tiếng Việt, không gắn cờ.

## Việc phải làm

1. Đọc **toàn bộ** `output/claude/tao_gd2/_he_thong.md` – hướng dẫn dịch đầy đủ (đã điền bảng thuật ngữ). Mọi quy tắc áp dụng nguyên vẹn, đặc biệt:
   - 2 loại trường: **dịch trực tiếp từ tiếng Nhật** (`dich_tu_tieng_nhat: true` – nghĩa câu hỏi / nghĩa lựa chọn / nghĩa câu trích; `vi_tham_khao` chỉ để tham khảo) và **dịch từ tiếng Việt** (`analysis`);
   - đoạn văn trong ngữ cảnh chỉ để hiểu – **không dịch**;
   - **cùng một câu trích** (giống chữ tiếng Nhật) ở các lựa chọn / câu hỏi khác nhau của cùng đoạn văn → **một bản dịch duy nhất** (làm một bảng tạm câu trích → bản dịch cho cả lô rồi dùng lại);
   - **trợ từ sau ⟪ ⟫ theo âm cuối cách đọc tiếng Nhật** (ん → 은/이/을/과/이라는/이며/으로…, nguyên âm → 는/가/를/와/라는/며/로…) (D12);
   - giữ khối ⟪ ⟫ (kể cả furigana bên trong), `{ }`, `\n`, `- `, loại dấu nháy như bản Việt; không thêm ý; văn phong -습니다 ở `analysis`.
2. Mở `output/claude/tao_gd2_danh_sach.json`. Với **từng** câu trong `cau`:
   - đọc `file_vao`: `user` = ngữ cảnh đề + JSON lời giải có gắn mã fN, `ids` = các mã cần dịch;
   - ghi `file_ra` (`output/claude/tao_gd2/<id>.output.json`) = **một object** `{"f1": "…", "f2": "…"}` gồm **đúng và đủ** các mã trong `ids`.
3. Ghi file bằng một đoạn Python ngắn (`json.dump(..., ensure_ascii=False, indent=1)`, nội dung qua heredoc `'EOF'`). **Tự dịch từng mã** (không dùng script tự động để dịch). Không mở / sửa file nào khác, không chạy script của pipeline.
4. Xong thì báo lại số câu đã dịch, số mã mỗi câu và các điểm khó (chỉ mô tả).
