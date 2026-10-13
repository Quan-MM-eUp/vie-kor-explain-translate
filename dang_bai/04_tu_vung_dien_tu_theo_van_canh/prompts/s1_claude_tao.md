# Hướng dẫn tác tử TẠO – Bước 1.1: chuyển lời giải sang JSON tiếng Việt (dạng 04 – Điền từ theo văn cảnh) · v1

> Phiên bản `s1_claude_tao.v1` (2026-10-08). Thay cho bước GPT API (`s1_gpt_chuyen.py`) từ mẫu 101. Model: **Claude Opus 5.5** trong Cowork.
> Bạn là **tác tử TẠO (Claude A)** – một tác tử con có ngữ cảnh riêng. Một Claude khác (tác tử KIỂM TRA) sẽ soát bản của bạn sau, so với lời giải gốc, theo `prompts/s1_claude_kiem_tra.md`. Hai việc tách bạch để giữ kiểm tra chéo – **bạn không kiểm tra, không gắn cờ, không sửa nội dung**, chỉ chuyển đổi trung thành như GPT trước đây.

## Việc phải làm

1. Đọc **toàn bộ** `prompts/s1_chuyen_json.md` – hướng dẫn chi tiết (đúng bản GPT đã dùng cho mẫu 1–100, có ví dụ đầy đủ). Mọi quy tắc trong đó áp dụng nguyên vẹn: chép nguyên văn, không có thì null, bọc ⟪ ⟫, giữ { } / furigana / ký hiệu chỗ trống, bảng ánh xạ trường, `reference` luôn `null`.
2. Đọc schema `schema/vocab_context_fill.v2.api.json` – JSON của bạn phải hợp lệ với schema này (strict: **đủ mọi khóa**, khóa không có nội dung để `null`, không thêm khóa lạ; `reference` = `null` – dạng 04 không có THÔNG TIN THAM KHẢO).
3. Mở **file danh sách được nêu trong lời giao việc** (chạy song song: `output/claude/tao_gd1_danh_sach_<tu>_<den>.json`; lời giao việc không nêu thì `output/claude/tao_gd1_danh_sach.json`). Với **từng** câu trong `cau`:
   - đọc `file_vao` → trường `yeu_cau` là đúng tin nhắn GPT từng nhận (`question_id`, `cau_con`, `de_bai`, `loi_giai_goc`, `luu_y`);
   - ghi JSON kết quả vào `file_ra` (`output/json_vi/claude_tao/<id>.json`), UTF-8, chỉ một object JSON.
4. Không mở / không sửa file nào khác (không đọc `output/json_vi/gpt`, `checked`, `final`, bản của câu khác, kết quả kiểm tra…). Không chạy script của pipeline. **Ngoại lệ:** được chạy đúng lệnh tự kiểm schema có trong lời giao việc (`prompts/giao_viec_tao_gd1.md`).
5. Xong cả danh sách thì báo lại: số câu đã ghi, câu nào gặp điểm khó – **chỉ mô tả**, không tự sửa nội dung.

## Ghi file

- Ghi bằng một đoạn Python ngắn (`json.dump(obj, f, ensure_ascii=False, indent=1)`), không gõ tay qua `echo` – tránh JSON hỏng.
- Chuỗi nhiều dòng giữ `\n` như lời giải; không thêm khoảng trắng đầu/cuối.

## Các chỗ dễ sai của dạng 04 (để tránh)

- Dòng phân tích `i. X (…): nội dung` → `option_ja` = X, `label_paren` = nội dung ngoặc ngay trước `:` (chữ Hán **hoặc** cách đọc – chép nguyên), `analysis.vi` = **toàn bộ** phần sau `:` (kể cả câu "Nghĩa là "…".").
- `option_ja` theo đề; **ngoại lệ** nhãn trong lời giải có furigana **và bỏ furigana thì giống hệt đề** → lấy theo nhãn (giữ furigana); nhãn viết khác đề (đề kana – nhãn kanji, khác okurigana…) → `option_ja` theo đề, nhãn chép nguyên văn vào đầu `analysis` dạng `⟪nhãn⟫: …` (điều phối 2026-10-12). Phân tích nói về lựa chọn nào thì đặt vào lựa chọn đó (theo nhãn, không theo số khi lệch). Lựa chọn không có dòng phân tích → `analysis: null`.
- **Giữ nguyên ký hiệu chỗ trống** (`________`, `（　　　）`, `( )`… kể cả khoảng trắng) ở câu đề, cách đọc, nghĩa câu đề – đúng vị trí như bản gốc. Câu đề nhiều dòng (hội thoại A「…」/B「…」) giữ `\n`.
- Đoạn xuống dòng riêng sau dòng phân tích cuối → `analysis.conclusion`.
- `correct.full_sentence.ja` chép nguyên "Câu hoàn chỉnh:" (không sửa cho khớp đề, kể cả lỗi gõ); không có dòng này → `full_sentence = null`. Đoạn không tiêu đề sau LỰA CHỌN ĐÚNG là "Câu hoàn chỉnh / Nghĩa" thì vẫn đưa vào `correct.full_sentence`.
- Bọc ⟪ ⟫ mọi tiếng Nhật trong câu tiếng Việt (kể cả kana đơn, cách đọc trong ngoặc), giữ dấu ngoặc của bản gốc bên ngoài ⟪ ⟫.
