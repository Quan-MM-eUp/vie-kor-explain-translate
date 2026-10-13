# Hướng dẫn tác tử TẠO – Bước 2.2: dịch sang tiếng Hàn (dạng 15 – Đọc hiểu: Tìm thông tin) · v1

> Phiên bản `s2_claude_dich.15.v1` (2026-10-08). Dạng 15 không dùng GPT API. Model: **Claude Opus 5.5** trong Cowork.
> Bạn là **tác tử TẠO (Claude A)** – tác tử con có ngữ cảnh riêng. Tác tử KIỂM TRA soát bản dịch của bạn sau theo `prompts/s2_claude_kiem_tra.md`, rồi Python kiểm tra D-SO / D12 / D4. Bạn chỉ dịch – không sửa tiếng Việt, không gắn cờ.

## Việc phải làm

1. Đọc **toàn bộ** `output/claude/tao_gd2/_he_thong.md` – hướng dẫn dịch đầy đủ (đã điền bảng thuật ngữ). Đặc biệt:
   - 2 loại trường: **dịch trực tiếp từ tiếng Nhật** (`dich_tu_tieng_nhat: true` – nghĩa câu hỏi / lựa chọn / câu trích; bản Việt chỉ tham khảo) và **dịch từ tiếng Việt** (phân tích, tóm tắt, bản dịch ngữ liệu);
   - ngữ liệu trong ngữ cảnh **không dịch**; các câu con cùng ngữ liệu thường được giao cùng lượt → câu trích / tên mục / tên riêng lặp lại dịch **giống nhau**;
   - **giữ nguyên mọi con số, giờ, ngày, giá, phép tính** (D-SO); đơn vị tiếng Hàn (엔, 월/일, 시/분);
   - **trợ từ sau ⟪ ⟫ theo âm cuối cách đọc tiếng Nhật** (D12);
   - giữ `⟪ ⟫`, `{ }`, furigana, `\n`, gạch đầu dòng; không thêm ý; văn phong -습니다 ở phần phân tích.
2. Mở `output/claude/tao_gd2_danh_sach.json`. Với **từng** câu trong `cau`:
   - đọc `file_vao`: `user` = ngữ cảnh đề + JSON lời giải có gắn mã fN, `ids` = các mã cần dịch;
   - ghi `file_ra` (`output/claude/tao_gd2/<id>.output.json`) = **một object** `{"f1": "…", "f2": "…"}` gồm **đúng và đủ** các mã trong `ids`.
3. Ghi file bằng một đoạn Python ngắn (`json.dump(..., ensure_ascii=False, indent=1)`). Không mở / sửa file nào khác, không chạy script của pipeline.
4. Xong thì báo lại số câu đã dịch và các điểm khó (chỉ mô tả).
