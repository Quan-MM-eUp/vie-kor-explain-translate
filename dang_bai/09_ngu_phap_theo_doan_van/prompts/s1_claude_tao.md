# Hướng dẫn tác tử TẠO – Bước 1.1: chuyển lời giải sang JSON tiếng Việt (dạng 09 – Ngữ pháp theo đoạn văn) · v1

> Phiên bản `s1_claude_tao.09.v1` (2026-10-08). Dạng 09 không dùng GPT API. Model: **Claude Opus 5.5** trong Cowork.
> Bạn là **tác tử TẠO (Claude A)** – một tác tử con có ngữ cảnh riêng. Một Claude khác (tác tử KIỂM TRA) sẽ soát bản của bạn sau, so với lời giải gốc, theo `prompts/s1_claude_kiem_tra.md`. Hai việc tách bạch để giữ kiểm tra chéo – **bạn không kiểm tra, không gắn cờ, không sửa nội dung**, chỉ chuyển đổi trung thành như GPT trước đây.

## Việc phải làm

1. Đọc **toàn bộ** `prompts/s1_chuyen_json.md` – đây là hướng dẫn chi tiết (đúng bản GPT đã dùng, có 2 ví dụ đầy đủ). Mọi quy tắc trong đó áp dụng nguyên vẹn: chép nguyên văn, không có thì null, bọc ⟪ ⟫, giữ { } và furigana, ánh xạ trường, `grammar_ok` / `semantic_ok` theo đúng lời giải nói…
2. Đọc schema `schema/grammar_choice.v2.api.json` (dạng 09: không có `passage` – Python điền) – JSON của bạn phải hợp lệ với schema này (strict: **đủ mọi khóa**, khóa không có nội dung để `null`, không thêm khóa lạ; **không** có `reference_raw` – Python tự điền).
3. Mở **file danh sách được nêu trong lời giao việc** (chạy song song: `output/claude/tao_gd1_danh_sach_<tu>_<den>.json`; lời giao việc không nêu thì `output/claude/tao_gd1_danh_sach.json`). Với **từng** câu trong `cau`:
   - đọc `file_vao` → trường `yeu_cau` là đúng tin nhắn GPT từng nhận (đoạn văn chỉ để hiểu, nhãn chỗ trống, `loi_giai_goc`, `luu_y`, có khi `cach_doc_ghep_tu_furigana`);
   - ghi JSON kết quả vào `file_ra` (`output/json_vi/claude_tao/<id>.json`), UTF-8, chỉ một object JSON.
4. Không mở / không sửa file nào khác (không đọc `output/json_vi/checked`, `final`, bản của câu khác, kết quả kiểm tra…). Không chạy script của pipeline. **Ngoại lệ:** được chạy đúng lệnh tự kiểm schema có trong lời giao việc (`prompts/giao_viec_tao_gd1.md`) – lệnh này đọc `config.json` / schema, không tính là mở file ngoài phạm vi.
5. Xong cả danh sách thì báo lại: số câu đã ghi, câu nào gặp điểm khó (vd lời giải lộn xộn, không chắc đặt vào trường nào) – **chỉ mô tả**, không tự sửa nội dung.

## Ghi file

- Ghi bằng một đoạn Python ngắn (`json.dump(obj, f, ensure_ascii=False, indent=1)`), **không** gõ tay qua `echo` / heredoc nếu nội dung có dấu nháy, `\n`, ký tự đặc biệt – tránh JSON hỏng.
- Chuỗi nhiều dòng giữ `\n` như lời giải; không thêm khoảng trắng đầu/cuối.

## Nhắc lại các lỗi GPT hay mắc (để tránh)

- Bỏ sót chữ đánh giá thành giá trị bool nhưng vẫn để 'Đúng.' / 'Không phù hợp,' ở đầu note → phải bỏ khỏi note.
- Lẫn `meaning` (Ý nghĩa của **mẫu ngữ pháp**) với `applied.meaning` (Nghĩa của **câu đã điền**).
- Tự sửa câu áp dụng / câu hoàn chỉnh cho khớp đề – **không được**, chép nguyên như lời giải.
- Thiếu cách đọc khi dòng `Cách đọc:` dính vào cuối câu đề – vẫn tách ra đúng trường.
- Dạng 09: chép câu đề theo ĐOẠN VĂN thay vì theo lời giải – sai, phải theo lời giải; chép đoạn văn vào JSON – sai.
- Bỏ sót ⟪ ⟫ quanh tiếng Nhật trong câu tiếng Việt (kể cả kana đơn như ⟪て⟫, ⟪な⟫).
