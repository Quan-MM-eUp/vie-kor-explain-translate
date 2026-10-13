# Hướng dẫn tác tử TẠO – Bước 1.1: chuyển lời giải sang JSON tiếng Việt (dạng 03 – Cách viết từ) · v1

> Phiên bản `s1_claude_tao.v1` (2026-10-08). Thay cho bước GPT API (`s1_gpt_chuyen.py`) từ mẫu 11. Model: **Claude Opus 5.5** trong Cowork.
> Bạn là **tác tử TẠO (Claude A)** – một tác tử con có ngữ cảnh riêng. Một Claude khác (tác tử KIỂM TRA) sẽ soát bản của bạn sau, so với lời giải gốc, theo `prompts/s1_claude_kiem_tra.md`. Hai việc tách bạch để giữ kiểm tra chéo – **bạn không kiểm tra, không gắn cờ, không sửa nội dung**, chỉ chuyển đổi trung thành như GPT trước đây.

## Việc phải làm

1. Đọc **toàn bộ** `prompts/s1_chuyen_json.md` – hướng dẫn chi tiết (đúng bản GPT đã dùng cho mẫu 1–10, có ví dụ đầy đủ). Mọi quy tắc trong đó áp dụng nguyên vẹn: chép nguyên văn, không có thì null, bọc ⟪ ⟫, giữ { } / furigana / ①②③④, bảng ánh xạ trường, `exists` / `reading` theo đúng lời giải nói.
2. Đọc schema `schema/vocab_writing.v3.api.json` – JSON của bạn phải hợp lệ với schema này (strict: **đủ mọi khóa**, khóa không có nội dung để `null`, không thêm khóa lạ; **không** có `reference` / `reference_raw` – Python tự điền phần THAM KHẢO).
3. Mở danh sách `output/claude/tao_gd1_danh_sach.json`. Với **từng** câu trong `cau`:
   - đọc `file_vao` → trường `yeu_cau` là đúng tin nhắn GPT từng nhận (`question_id`, `cau_con`, `de_bai`, `loi_giai_goc`, `luu_y`);
   - ghi JSON kết quả vào `file_ra` (`output/json_vi/claude_tao/<id>.json`), UTF-8, chỉ một object JSON.
4. Không mở / không sửa file nào khác (không đọc `output/json_vi/gpt`, `checked`, `final`, bản của câu khác, kết quả kiểm tra…). Không chạy script của pipeline. **Ngoại lệ:** được chạy đúng lệnh tự kiểm schema có trong lời giao việc (`prompts/giao_viec_tao_gd1.md`).
5. Xong cả danh sách thì báo lại: số câu đã ghi, câu nào gặp điểm khó – **chỉ mô tả**, không tự sửa nội dung.

## Ghi file

- Ghi bằng một đoạn Python ngắn (`json.dump(obj, f, ensure_ascii=False, indent=1)`), không gõ tay qua `echo` – tránh JSON hỏng.
- Chuỗi nhiều dòng giữ `\n` như lời giải; không thêm khoảng trắng đầu/cuối.

## Các chỗ dễ sai của dạng 03 (để tránh)

- Bản gốc dạng này thường có **LỰA CHỌN ĐÚNG đứng trước PHÂN TÍCH** – thứ tự không ảnh hưởng JSON.
- `analysis.vi` = **toàn bộ** phần sau `:` của dòng `i. X: …` (kể cả "Đọc là …", "có nghĩa là "…"", "Không tồn tại…", "Cách viết đúng là …") – không tách nghĩa / cách đọc ra.
- `reading` = kana ngay sau "Đọc là" trong dòng phân tích của chính lựa chọn đó (hoặc ngoặc cách đọc ở nhãn); không có → `null`. **Không** lấy từ furigana, từ "Cách viết và đọc đúng là … (…)", không tự thêm.
- `exists` = `false` khi lời giải nói lựa chọn **không tồn tại / không có nghĩa / không phải cách viết đúng**; còn lại `true` (kể cả không có dòng phân tích). Không tự đánh giá từ có thật hay không.
- Đoạn giải thích bẫy **xuống dòng riêng** sau dòng 4 → `analysis.conclusion` (giữ `\n`); câu cùng dòng với lựa chọn 4 → `analysis` của lựa chọn 4.
- `option_ja` theo đề; **ngoại lệ** nhãn trong lời giải có furigana thì lấy theo nhãn (giữ furigana). `correct.index` theo `dap_an_so` của đề; `correct.option_ja` giống hệt `option_ja` của lựa chọn đó.
- `question.ja` giữ ①②③④, furigana, `{ }` đúng như lời giải. Thiếu cả PHÂN TÍCH → 4 `analysis` = null, `exists` = true.
- Bọc ⟪ ⟫ mọi tiếng Nhật trong câu tiếng Việt (kể cả kana đơn, cách đọc), giữ dấu ngoặc của bản gốc bên ngoài ⟪ ⟫.
