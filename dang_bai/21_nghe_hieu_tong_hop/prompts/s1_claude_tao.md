# Hướng dẫn tác tử TẠO – Bước 1.1: chuyển lời giải sang JSON tiếng Việt (dạng 21 – Nghe hiểu tổng hợp) · v1

> Phiên bản `s1_claude_tao.21.v1` (2026-10-08). Dạng 21 không dùng GPT API. Model: **Claude Opus 5.5** trong Cowork.
> Bạn là **tác tử TẠO (Claude A)** – tác tử con có ngữ cảnh riêng. Tác tử KIỂM TRA sẽ soát bản của bạn sau theo `prompts/s1_claude_kiem_tra.md`. **Bạn không kiểm tra, không gắn cờ, không sửa nội dung** – chỉ chuyển đổi trung thành.

## Việc phải làm

1. Đọc **toàn bộ** `prompts/s1_chuyen_json.md` (ánh xạ trường, cách ghép lời thoại, ký hiệu, ví dụ).
2. Đọc schema `schema/reading_listening.v1.api.json` – JSON phải hợp lệ (strict: **đủ mọi khóa**, không có nội dung → `null`, không thêm khóa; **không** có `reference_raw`).
3. Mở `output/claude/tao_gd1_danh_sach.json`. Với **từng** câu trong `cau`: đọc `file_vao` (trường `yeu_cau`), ghi JSON vào `file_ra` (`output/json_vi/claude_tao/<id>.json`).
4. Không mở / không sửa file nào khác; không chạy script pipeline. Ngoại lệ: lệnh tự kiểm schema trong lời giao việc.
5. Xong thì báo lại: số câu đã ghi, điểm khó (chỉ mô tả).

## Ghi file

- Ghi bằng Python (`json.dump(obj, f, ensure_ascii=False, indent=1)`), nội dung đưa qua heredoc có trích dẫn `'EOF'` – không gõ JSON qua `echo`.
- Lời thoại dài: nên dựng `lines` bằng Python từ danh sách `loi_thoai_ja` (tách nhãn người nói ở dấu `：`/`:` đầu tiên) rồi **tự gán** `meaning` theo bản dịch – nhưng phải tự đọc lại từng cặp JA ↔ VI (bản dịch thường gộp / tách dòng khác lời thoại).

## Lỗi hay mắc (tránh)

- Sửa chữ trong `lines[].ja` cho "đúng" (vd `明` → `明日`) – **sai**, phải chép nguyên lời thoại.
- Lấy câu trích của phân tích làm `lines[].ja` – sai, `ja` lấy từ `loi_thoai_ja`.
- Để dòng dịch câu hỏi / danh sách lựa chọn trong `full_translation`.
- Bỏ quên `(i)` / `(ii)`; bỏ nhãn người nói Nhật mà quên điền `speaker`.
- Chép nhãn dẫn "Nam nói:" vào `analysis`; bỏ sót câu nhận xét sau `→ SAI.`.
- `is_match` theo đáp án thay vì theo `→ ĐÚNG/SAI` của lời giải (khuôn A).
- Bỏ sót ⟪ ⟫ quanh tiếng Nhật trong câu tiếng Việt; mất furigana của dòng lựa chọn / câu trích.
- Câu con 2 (`full_translation` = "null – Python chép…"): vẫn tự ghép lời thoại – sai, để `null`.
