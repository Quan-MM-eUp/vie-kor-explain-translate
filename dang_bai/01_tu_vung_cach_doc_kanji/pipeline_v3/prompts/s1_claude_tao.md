# Hướng dẫn tác tử TẠO – Bước 1.1: chuyển lời giải sang JSON tiếng Việt (dạng 01 – Cách đọc kanji (pipeline v3)) · v1

> Phiên bản `s1_claude_tao.v1` (2026-10-08). Thay cho bước GPT API (`s1_gpt_chuyen.py`) từ mẫu 201. Model: **Claude Opus 5.5** trong Cowork.
> Bạn là **tác tử TẠO (Claude A)** – một tác tử con có ngữ cảnh riêng. Một Claude khác (tác tử KIỂM TRA) sẽ soát bản của bạn sau, so với lời giải gốc, theo `prompts/s1_claude_kiem_tra.md`. Hai việc tách bạch để giữ kiểm tra chéo – **bạn không kiểm tra, không gắn cờ, không sửa nội dung**, chỉ chuyển đổi trung thành như GPT trước đây.

## Việc phải làm

1. Đọc **toàn bộ** `prompts/s1_chuyen_json.md` – hướng dẫn chi tiết (đúng bản GPT đã dùng cho mẫu 1–200, có ví dụ đầy đủ). Mọi quy tắc trong đó áp dụng nguyên vẹn: chép nguyên văn, không có thì null, bọc ⟪ ⟫, giữ { } / furigana, bảng ánh xạ trường (JSON cũ hoặc văn bản ###), phân tích bị dồn tách về đúng lựa chọn.
2. Đọc schema `../schema/vocab_kanji_reading.v3.api.json` – JSON của bạn phải hợp lệ với schema này (strict: **đủ mọi khóa**, khóa không có nội dung để `null`, không thêm khóa lạ; **không** có `reference` / `reference_raw` – Python tự điền phần THAM KHẢO).
3. Mở **file danh sách được nêu trong lời giao việc** (chạy song song: `output/claude/tao_gd1_danh_sach_<tu>_<den>.json`; lời giao việc không nêu thì `output/claude/tao_gd1_danh_sach.json`). Với **từng** câu trong `cau`:
   - đọc `file_vao` → trường `yeu_cau` là đúng tin nhắn GPT từng nhận (`question_id`, `cau_con`, `de_bai`, `loi_giai_goc`, `luu_y`);
   - ghi JSON kết quả vào `file_ra` (`output/json_vi/claude_tao/<id>.json`), UTF-8, chỉ một object JSON.
4. Không mở / không sửa file nào khác (không đọc `output/json_vi/gpt`, `checked`, `final`, bản của câu khác, kết quả kiểm tra…). Không chạy script của pipeline. **Ngoại lệ:** được chạy đúng lệnh tự kiểm schema có trong lời giao việc (`prompts/giao_viec_tao_gd1.md`).
5. Xong cả danh sách thì báo lại: số câu đã ghi, câu nào gặp điểm khó – **chỉ mô tả**, không tự sửa nội dung.

## Ghi file

- Ghi bằng một đoạn Python ngắn (`json.dump(obj, f, ensure_ascii=False, indent=1)`), không gõ tay qua `echo` – tránh JSON hỏng.
- Chuỗi nhiều dòng giữ `\n` như lời giải; không thêm khoảng trắng đầu/cuối.

## Các chỗ dễ sai của dạng 01 (để tránh)

- Lời giải gốc có **hai khuôn**: JSON cũ (`question.kanji`, `kanji_reading`, `kanji_jishokei`, `kanji_mean`, `text`, `mean`, `answers[i].note`…) hoặc văn bản `###` (Từ: / Thể từ điển: / Nghĩa: / Câu hỏi: / Cách đọc: / Nghĩa: / PHÂN TÍCH / LỰA CHỌN ĐÚNG) – xem bảng ánh xạ trong `s1_chuyen_json.md`.
- `word.reading` = furigana của "Từ:" (không có thì nội dung đáp án đúng); **Thể từ điển dính vào cách đọc** (`へってThể từ điển: 減る(へる)`) → `word.reading` = `へって`, `word.dictionary_form` = `{"ja": "減る", "reading": "へる"}`; không có thể từ điển → `null`.
- `word.meaning` = dòng "Nghĩa:" ngay sau "Từ:"; `question.meaning` = dòng "Nghĩa:" ngay sau "Câu hỏi:" – không lẫn hai dòng này.
- `options` đủ 4, `option_ja` đúng nội dung lựa chọn của đề; `correct.index` theo `dap_an_so`; `correct.full_sentence = null`.
- **Phân tích bị dồn** (ô của lựa chọn này chứa `4. やとって: …`) → tách về đúng lựa chọn, bỏ nhãn đầu. Lựa chọn (kể cả đáp án) không có phân tích → `analysis: null`.
- Nhiều cách đọc trong một ô (`みせ / てん`) giữ nguyên dấu ngăn cách; giữ nguyên các cách viết khác nhau của câu "Không tồn tại từ … có cách đọc này".
- Bọc ⟪ ⟫ mọi tiếng Nhật trong câu tiếng Việt (kể cả kana đơn, cách đọc), giữ dấu ngoặc của bản gốc bên ngoài ⟪ ⟫.
