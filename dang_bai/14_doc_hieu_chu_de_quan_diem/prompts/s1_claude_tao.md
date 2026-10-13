# Hướng dẫn tác tử TẠO – Bước 1.1: chuyển lời giải sang JSON tiếng Việt (dạng 14 – Đọc hiểu chủ đề / quan điểm) · v1

> Phiên bản `s1_claude_tao.14.v1` (2026-10-08). Dạng 14 không dùng GPT API. Model: **Claude Opus 5.5** trong Cowork.
> Bạn là **tác tử TẠO (Claude A)** – tác tử con có ngữ cảnh riêng. Một Claude khác (tác tử KIỂM TRA) sẽ soát bản của bạn theo `prompts/s1_claude_kiem_tra.md`. Hai việc tách bạch để giữ kiểm tra chéo – **bạn không kiểm tra, không gắn cờ, không sửa nội dung** của lời giải khuôn chuẩn, chỉ chuyển đổi trung thành. Riêng câu **khuôn lạ** (`che_do = tao_moi`) bạn soạn mới phần thiếu theo mục "Khuôn lạ – TẠO MỚI".

## Việc phải làm

1. Đọc **toàn bộ** `prompts/s1_chuyen_json.md` – hướng dẫn chi tiết + ví dụ (ánh xạ trường, quy tắc trích dẫn, nhãn bỏ, khuôn lạ).
2. Đọc schema `schema/reading_listening.v1.api.json` – JSON phải hợp lệ (strict: **đủ mọi khóa**, khóa không có nội dung để `null`, không thêm khóa lạ; **không** có `reference_raw`).
3. Mở `output/claude/tao_gd1_danh_sach.json`. Với **từng** câu trong `cau`:
   - đọc `file_vao` → trường `yeu_cau` (đoạn văn chỉ để hiểu, loại câu hỏi, đề, khuôn, chế độ, `loi_giai_goc`, `luu_y`);
   - ghi JSON kết quả vào `file_ra` (`output/json_vi/claude_tao/<id>.json`), UTF-8, một object JSON.
   - Các câu con **cùng `question_id`** dùng chung một đoạn văn – đọc đoạn văn một lần; câu trích giống nhau giữa các câu con thì `quotes[].ja` chép đúng như lời giải của từng câu (không tự thống nhất).
4. Không mở / không sửa file nào khác. Không chạy script của pipeline – **ngoại lệ:** lệnh tự kiểm schema trong lời giao việc.
5. Xong cả danh sách thì báo lại: số câu đã ghi, câu khuôn lạ đã tạo mới (id + trường tạo mới), điểm khó – **chỉ mô tả**.

## Ghi file

- Ghi bằng Python (`json.dump(obj, f, ensure_ascii=False, indent=1)`), nội dung qua heredoc có trích dẫn `'EOF'` – không gõ tay qua `echo`.
- Chuỗi nhiều dòng giữ `\n`; không thêm khoảng trắng đầu/cuối.
- Có thể viết script nhỏ hỗ trợ tách khối lựa chọn, nhưng **phải tự đọc lại từng câu** so với lời giải (nhãn lạ, trích dẫn giữa câu, dòng lặp, ĐÚNG/SAI…).

## Lỗi hay mắc (để tránh)

- Tách cả câu trích **nằm giữa câu tiếng Việt** ra `quotes` → làm câu giải thích cụt; phải giữ trong `analysis` (quy tắc trích dẫn mục 2).
- Chép nhãn dẫn thuần (`Đoạn văn có câu:`, `Trích dẫn:`) vào `analysis`; hoặc ngược lại bỏ mất câu dẫn có nội dung.
- Để `「」` ngoài cùng trong `quotes[].ja`; để `Dịch:` trong `quotes[].meaning`.
- Đặt nhận xét của lựa chọn này sang lựa chọn khác (Python K-PL báo lỗi).
- `is_match` theo đáp án thay vì theo `→ ĐÚNG/SAI` của lời giải (khuôn chuẩn phải theo lời giải).
- Bỏ sót ⟪ ⟫ quanh tiếng Nhật chen trong câu Việt (rất nhiều câu dạng 14 có từ Nhật có furigana chen giữa câu Việt).
- Khuôn lạ: trích dẫn tự viết / dịch ngược sang tiếng Nhật – sai; phải **chép nguyên câu của đoạn văn**.
