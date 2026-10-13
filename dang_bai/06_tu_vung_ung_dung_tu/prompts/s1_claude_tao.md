# Hướng dẫn tác tử TẠO – Bước 1.1: chuyển lời giải sang JSON tiếng Việt (dạng 06 – Ứng dụng từ) · v1

> Phiên bản `s1_claude_tao.v1` (2026-10-08). Thay cho bước GPT API (`s1_gpt_chuyen.py`) từ mẫu 101. Model: **Claude Opus 5.5** trong Cowork.
> Bạn là **tác tử TẠO (Claude A)** – một tác tử con có ngữ cảnh riêng. Một Claude khác (tác tử KIỂM TRA) sẽ soát bản của bạn sau, so với lời giải gốc, theo `prompts/s1_claude_kiem_tra.md`. Hai việc tách bạch để giữ kiểm tra chéo – **bạn không kiểm tra, không gắn cờ, không sửa nội dung**, chỉ chuyển đổi trung thành như GPT trước đây.

## Việc phải làm

1. Đọc **toàn bộ** `prompts/s1_chuyen_json.md` – hướng dẫn chi tiết (đúng bản GPT đã dùng cho mẫu 1–100, có 2 ví dụ đầy đủ: đề thường có "Sửa lại" và đề có định nghĩa). Mọi quy tắc trong đó áp dụng nguyên vẹn: chép nguyên văn, không có thì null, bọc ⟪ ⟫, giữ { } và furigana, bảng ánh xạ trường, `is_correct` theo `dap_an_so`, `usage_ok` theo đúng lời giải nói (true / false / null).
2. Đọc schema `schema/vocab_usage.v2.api.json` – JSON của bạn phải hợp lệ với schema này (strict: **đủ mọi khóa**, khóa không có nội dung để `null`, không thêm khóa lạ).
3. Mở **file danh sách được nêu trong lời giao việc** (chạy song song: `output/claude/tao_gd1_danh_sach_<tu>_<den>.json`; lời giao việc không nêu thì `output/claude/tao_gd1_danh_sach.json`). Với **từng** câu trong `cau`:
   - đọc `file_vao` → trường `yeu_cau` là đúng tin nhắn GPT từng nhận (`question_id`, `cau_con`, `de_bai`, `loi_giai_goc`, `luu_y`);
   - ghi JSON kết quả vào `file_ra` (`output/json_vi/claude_tao/<id>.json`), UTF-8, chỉ một object JSON.
4. Không mở / không sửa file nào khác (không đọc `output/json_vi/gpt`, `checked`, `final`, bản của câu khác, kết quả kiểm tra…). Không chạy script của pipeline. **Ngoại lệ:** được chạy đúng lệnh tự kiểm schema có trong lời giao việc (`prompts/giao_viec_tao_gd1.md`).
5. Xong cả danh sách thì báo lại: số câu đã ghi, câu nào gặp điểm khó (vd lời giải lộn xộn, nhận xét không rõ thuộc lựa chọn nào, không rõ `usage_ok`) – **chỉ mô tả**, không tự sửa nội dung.

## Ghi file

- Ghi bằng một đoạn Python ngắn (`json.dump(obj, f, ensure_ascii=False, indent=1)`), **không** gõ tay qua `echo` nếu nội dung có dấu nháy, `\n`, ký tự đặc biệt – tránh JSON hỏng.
- Chuỗi nhiều dòng giữ `\n` như lời giải; không thêm khoảng trắng đầu/cuối.

## Các chỗ dễ sai của dạng 06 (để tránh)

- `word.meaning` = **chỉ câu đầu** sau từ + ngoặc (`có nghĩa là "…", "…".`); phần còn lại của đoạn giới thiệu → `word.usage`. `word.paren` = nội dung ngoặc ngay sau từ (không gồm dấu ngoặc); `word.definition_ja` = phần sau `……` của câu hỏi đề (đề không có `……` → null).
- `Cách đọc:` / `Nghĩa:` **trước** `Sửa lại:` thuộc `sentence`, **sau** `Sửa lại:` thuộc `correction` – không đổi chỗ.
- `sentence.ja` chép câu **trong lời giải** (kể cả khi khác đề), không lấy câu của đề; `correct.sentence_ja` giống hệt `options[index-1].sentence.ja`.
- `usage_ok` là điều lời giải NÓI về **cách dùng từ được hỏi**, không phải "có là đáp án không": đề có định nghĩa, câu dùng đúng nhưng khác nghĩa → `true`; lời giải chỉ nói "không phù hợp với định nghĩa" → `null`.
- Không tự viết câu sửa / cách đọc / nghĩa khi lời giải không có; không sửa câu sửa dù thấy chưa tự nhiên.
- Nhận xét nằm sau câu 4 thuộc lựa chọn 4 (`analysis.conclusion` hầu như null); câu chữ khác ngoài dòng `i. <câu>` ở LỰA CHỌN ĐÚNG → `correct.note`.
- Bọc ⟪ ⟫ mọi tiếng Nhật trong câu tiếng Việt (kể cả kana đơn, từ trong ngoặc kép `"⟪…⟫"`), giữ dấu ngoặc của bản gốc bên ngoài ⟪ ⟫; không bọc dấu `・` đầu dòng.
