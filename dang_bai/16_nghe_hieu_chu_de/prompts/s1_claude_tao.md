# Hướng dẫn tác tử TẠO – Bước 1.1: chuyển lời giải sang JSON tiếng Việt (dạng 16 – Nghe hiểu chủ đề) · v1

> Phiên bản `s1_claude_tao.16.v1` (2026-10-08). Dạng 16 không dùng GPT API. Model: **Claude Opus 5.5** trong Cowork.
> Bạn là **tác tử TẠO (Claude A)** – một tác tử con có ngữ cảnh riêng. Một Claude khác (tác tử KIỂM TRA) sẽ soát bản của bạn sau, so với lời giải gốc, theo `prompts/s1_claude_kiem_tra.md`. Hai việc tách bạch để giữ kiểm tra chéo – **bạn không kiểm tra, không gắn cờ, không sửa nội dung**, chỉ chuyển đổi trung thành.

## Việc phải làm

1. Đọc **toàn bộ** `prompts/s1_chuyen_json.md` – hướng dẫn chi tiết + 3 ví dụ. Mọi quy tắc trong đó áp dụng nguyên vẹn.
2. Đọc schema `schema/reading_listening.v1.api.json` – JSON của bạn phải hợp lệ với schema này: đủ các khóa bắt buộc (`schema`, `question_id`, `cau_con`, `summary`, `question`, `options`, `correct`), khóa không có nội dung để `null`, không thêm khóa lạ; **không** có `key_info`, `reference_raw`; `full_translation` **chỉ** khi đầu vào có `can_ghi_full_translation: true`.
3. Mở danh sách `output/claude/tao_gd1_danh_sach.json`. Với **từng** câu trong `cau`:
   - đọc `file_vao` → trường `yeu_cau` (đề, lời thoại song ngữ để hiểu / lời thoại cần ghép, gợi ý câu hỏi, phân tích, gợi ý tách khối, `luu_y`);
   - ghi JSON kết quả vào `file_ra` (`output/json_vi/claude_tao/<id>.json`), UTF-8, chỉ một object JSON.
4. Không mở / không sửa file nào khác (không đọc `output/json_vi/checked`, `final`, bản của câu khác, kết quả kiểm tra…). Không chạy script của pipeline. **Ngoại lệ:** lệnh tự kiểm schema trong lời giao việc.
5. Xong cả danh sách thì báo lại: số câu đã ghi, câu nào gặp điểm khó (vd gợi ý tách khối của Python sai, câu trích không rõ thuộc khối nào, ghép dòng khó) – **chỉ mô tả**, không tự sửa nội dung.

## Ghi file

- Ghi bằng một đoạn Python ngắn (`json.dump(obj, f, ensure_ascii=False, indent=1)`), nội dung đưa vào qua heredoc có trích dẫn `'EOF'` – tránh JSON hỏng vì dấu nháy, `\n`.
- Chuỗi nhiều dòng giữ `\n` như lời giải; không thêm khoảng trắng đầu/cuối.

## Các lỗi dễ mắc (để tránh)

- `option_ja` lấy theo dòng `n.` của lời giải (có furigana / viết khác) thay vì **đúng lựa chọn của đề**.
- Lựa chọn tranh mà vẫn điền `meaning`; lựa chọn chữ có `Nghĩa:` mà để `meaning = null`.
- Tách câu trích **nằm giữa câu** ra `quotes` (làm mất phần chữ trước nó) – chỉ tách dòng / đầu dòng dạng `[phần dẫn ngắn:] 「…」(…)`.
- Chép phần dẫn (`Người phụ nữ nói:`) vào analysis, hoặc bỏ mất câu nhận xét đứng SAU `→ ĐÚNG/SAI`.
- `is_match` theo đáp án của đề thay vì theo kết luận của khối (lời giải nói SAI thì là `false`, kể cả khi đó là đáp án).
- Bỏ sót ⟪ ⟫ quanh tiếng Nhật trong câu tiếng Việt (kể cả câu trích giữa câu, kana đơn, katakana trong tên sách).
- Câu lệch dòng: gộp / bỏ dòng tiếng Nhật, bỏ dòng tiếng Việt thừa, tự dịch dòng thiếu bản dịch – đều **không được**.
