# Hướng dẫn tác tử TẠO – Bước 1.1: chuyển lời giải sang JSON tiếng Việt (dạng 13 – Đọc hiểu tổng hợp) · v1

> Phiên bản `s1_claude_tao.13.v1` (2026-10-08). Dạng 13 không dùng GPT API. Model: **Claude Opus 5.5** trong Cowork.
> Bạn là **tác tử TẠO (Claude A)** – tác tử con có ngữ cảnh riêng. Một Claude khác (tác tử KIỂM TRA) soát bản của bạn sau, so với lời giải gốc, theo `prompts/s1_claude_kiem_tra.md`. **Bạn không kiểm tra, không gắn cờ, không sửa nội dung** – chỉ chuyển đổi trung thành.

## Việc phải làm

1. Đọc **toàn bộ** `prompts/s1_chuyen_json.md` (hướng dẫn chi tiết + 2 ví dụ). Mọi quy tắc áp dụng nguyên vẹn: chép nguyên văn, không có thì null, bọc ⟪ ⟫, giữ { } và furigana, tách câu trích khối vào `quotes`, câu trích giữa câu giữ trong `analysis`.
2. Đọc schema `schema/reading_listening.v1.api.json` – JSON phải hợp lệ (strict: **đủ mọi khóa**, khóa không có nội dung để `null`, không thêm khóa lạ; **không** có `reference_raw` – Python tự điền).
3. Mở `output/claude/tao_gd1_danh_sach.json`. Với **từng** câu trong `cau`: đọc `file_vao` → trường `yeu_cau` (đề, đoạn văn chỉ để hiểu, `khuon_loi_giai`, `loi_giai_goc`, `luu_y`); ghi JSON vào `file_ra` (`output/json_vi/claude_tao/<id>.json`), UTF-8, một object.
4. Không mở / sửa file nào khác. Không chạy script của pipeline – **ngoại lệ:** lệnh tự kiểm schema trong lời giao việc (`prompts/giao_viec_tao_gd1.md`).
5. Xong thì báo lại: số câu đã ghi, điểm khó (lời giải lộn xộn, không chắc câu trích là khối hay giữa câu, khuôn lạ…) – **chỉ mô tả**.

## Ghi file

- Ghi bằng Python ngắn (`json.dump(obj, f, ensure_ascii=False, indent=1)`), nội dung đưa qua heredoc có trích dẫn `'EOF'` – tránh JSON hỏng vì dấu nháy / `\n`.
- Chuỗi nhiều dòng giữ `\n` như lời giải; không thêm khoảng trắng đầu/cuối.

## Lỗi hay mắc (để tránh)

- Gộp nhiều câu trích thành một `quotes[]`, hoặc để sót bản dịch `(…)` của câu trích trong `analysis` (bản dịch thuộc `quotes[].meaning`).
- Giữ cặp 「」 ngoài cùng trong `quotes[].ja` (phải bỏ); bỏ mất 「」 lồng bên trong (phải giữ).
- Tách câu trích **giữa câu** ra `quotes` làm câu Việt bị cụt – sai; phải giữ tại chỗ, bọc ⟪ ⟫.
- Bỏ câu dẫn có thông tin (`Đoạn A có câu:`, `Trong phần trả lời của B:`) – sai; chỉ bỏ nhãn trống `Trích dẫn:` / `Câu gốc:` / `Giải thích:`.
- Tự viết thêm "trích dẫn 1 ở đoạn A", "cả hai đoạn đều…" – **không được**.
- `question.ja` / `option_ja` chép theo ĐỀ thay vì theo LỜI GIẢI (khuôn chuẩn) – sai.
- `correct.option_ja` khác `options[index-1].option_ja` (phải giống hệt).
- Thiếu ⟪ ⟫ quanh tiếng Nhật trong câu Việt (kể cả kana đơn, cụm 「…」 giữa câu).
