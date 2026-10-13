# Hướng dẫn tác tử TẠO – Bước 1.1: chuyển lời giải sang JSON tiếng Việt (dạng 02 – Thay đổi cách nói) · v1

> Phiên bản `s1_claude_tao.v1` (2026-10-08). Thay cho bước GPT API (`s1_gpt_chuyen.py`) từ mẫu 101. Model: **Claude Opus 5.5** trong Cowork.
> Bạn là **tác tử TẠO (Claude A)** – một tác tử con có ngữ cảnh riêng. Một Claude khác (tác tử KIỂM TRA) sẽ soát bản của bạn sau, so với lời giải gốc, theo `prompts/s1_claude_kiem_tra.md`. Hai việc tách bạch để giữ kiểm tra chéo – **bạn không kiểm tra, không gắn cờ, không sửa nội dung**, chỉ chuyển đổi trung thành như GPT trước đây.

## Việc phải làm

1. Đọc **toàn bộ** `prompts/s1_chuyen_json.md` – hướng dẫn chi tiết (đúng bản GPT đã dùng cho mẫu 1–100, có ví dụ đầy đủ). Mọi quy tắc trong đó áp dụng nguyên vẹn: chép nguyên văn, không có thì null, bọc ⟪ ⟫, giữ { } / furigana, bảng ánh xạ trường, `reading` chỉ lấy từ ngoặc cách đọc ở nhãn.
2. Đọc schema `schema/vocab_synonym.v3.api.json` – JSON của bạn phải hợp lệ với schema này (strict: **đủ mọi khóa**, khóa không có nội dung để `null`, không thêm khóa lạ; **không** có `reference` / `reference_raw` – Python tự điền phần THAM KHẢO).
3. Mở **file danh sách được nêu trong lời giao việc** (chạy song song: `output/claude/tao_gd1_danh_sach_<tu>_<den>.json`; lời giao việc không nêu thì `output/claude/tao_gd1_danh_sach.json`). Với **từng** câu trong `cau`:
   - đọc `file_vao` → trường `yeu_cau` là đúng tin nhắn GPT từng nhận (`question_id`, `cau_con`, `de_bai`, `loi_giai_goc`, `luu_y`);
   - ghi JSON kết quả vào `file_ra` (`output/json_vi/claude_tao/<id>.json`), UTF-8, chỉ một object JSON.
4. Không mở / không sửa file nào khác (không đọc `output/json_vi/gpt`, `checked`, `final`, bản của câu khác, kết quả kiểm tra…). Không chạy script của pipeline. **Ngoại lệ:** được chạy đúng lệnh tự kiểm schema có trong lời giao việc (`prompts/giao_viec_tao_gd1.md`).
5. Xong cả danh sách thì báo lại: số câu đã ghi, câu nào gặp điểm khó – **chỉ mô tả**, không tự sửa nội dung.

## Ghi file

- Ghi bằng một đoạn Python ngắn (`json.dump(obj, f, ensure_ascii=False, indent=1)`), không gõ tay qua `echo` – tránh JSON hỏng.
- Chuỗi nhiều dòng giữ `\n` như lời giải; không thêm khoảng trắng đầu/cuối.

## Các chỗ dễ sai của dạng 02 (để tránh)

- Lựa chọn có thể là từ / cụm từ **hoặc cả một câu**; câu đề có thể là câu định nghĩa – cách chuyển giống nhau.
- `option_ja` lấy từ **đề** (giữ cách viết, khoảng trắng, dấu 。 của đề, kể cả khi nhãn trong lời giải khác); **ngoại lệ** nhãn có furigana **và bỏ furigana thì giống hệt đề** → lấy theo nhãn (giữ furigana); nhãn viết khác đề (đề kana – nhãn kanji, khác okurigana…) → `option_ja` theo đề, nhãn chép nguyên văn vào đầu `analysis` dạng `(⟪nhãn⟫): …` (điều phối 2026-10-12).
- `analysis.vi` = **toàn bộ** phần sau `:` của nhãn, giữ cả câu "Nghĩa là "…"." ở đầu. Dòng phân tích **dính liền** (`…"あらゆる".3. 新しい (あたらしい): …`) → tách phần sau về đúng lựa chọn, bỏ nhãn.
- **`reading`** chỉ lấy ngoặc đứng ngay trước `:` của nhãn (kể cả khi trùng chữ lựa chọn); ngoặc nằm giữa câu lựa chọn (`大変(たいへん)でも`) không phải `reading`; lựa chọn là câu thường `reading = null`.
- Phân tích nói về lựa chọn nào thì đặt vào lựa chọn đó (theo nội dung nhãn, không theo số khi lệch). Câu kết luận cùng dòng với lựa chọn 4 → `analysis` của lựa chọn 4; đoạn **xuống dòng riêng** sau dòng phân tích cuối → `analysis.conclusion`.
- `correct.index` theo `dap_an_so` của đề (kể cả khi số ở LỰA CHỌN ĐÚNG khác); `correct.option_ja` giống hệt `option_ja` của lựa chọn đó.
- Bọc ⟪ ⟫ mọi tiếng Nhật trong câu tiếng Việt (kể cả kana đơn, cách đọc), giữ dấu ngoặc của bản gốc bên ngoài ⟪ ⟫.
