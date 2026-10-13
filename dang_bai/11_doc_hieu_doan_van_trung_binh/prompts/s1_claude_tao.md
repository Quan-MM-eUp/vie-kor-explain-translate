# Hướng dẫn tác tử TẠO – Bước 1.1: chuyển lời giải sang JSON tiếng Việt (dạng 11 – Đọc hiểu: Đoạn văn trung bình) · v1

> Phiên bản `s1_claude_tao.11.v1` (2026-10-08). Model: **Claude Opus 5.5** trong Cowork (dạng 11 không dùng GPT API).
> Bạn là **tác tử TẠO (Claude A)** – tác tử con có ngữ cảnh riêng. Một Claude khác (tác tử KIỂM TRA) sẽ soát bản của bạn so với lời giải gốc theo `prompts/s1_claude_kiem_tra.md`. Hai việc tách bạch để giữ kiểm tra chéo – **bạn không kiểm tra, không gắn cờ, không sửa nội dung**, chỉ chuyển đổi trung thành.

## Việc phải làm

1. Đọc **toàn bộ** `prompts/s1_chuyen_json.md` – hướng dẫn chi tiết + 2 ví dụ đầy đủ. Mọi quy tắc áp dụng nguyên vẹn.
2. Đọc schema `schema/reading_listening.v1.api.json` – JSON phải hợp lệ (strict: **đủ mọi khóa**, không có thì `null` / `[]`, không thêm khóa lạ, **không** có `reference_raw`).
3. Mở `output/claude/tao_gd1_danh_sach.json`. Với **từng** câu trong `cau`:
   - đọc `file_vao` → trường `yeu_cau` (đề, `loi_giai_goc`, `luu_y`);
   - ghi JSON vào `file_ra` (`output/json_vi/claude_tao/<id>.json`), UTF-8, một object.
4. Không mở / không sửa file nào khác. Không chạy script của pipeline. **Ngoại lệ:** được chạy đúng lệnh tự kiểm schema có trong lời giao việc (`prompts/giao_viec_tao_gd1.md`).
5. Xong cả danh sách thì báo lại: số câu đã ghi, câu nào gặp điểm khó – **chỉ mô tả**, không tự sửa nội dung.

## Ghi file

- Ghi bằng một đoạn Python ngắn (`json.dump(obj, f, ensure_ascii=False, indent=1)`), nội dung qua heredoc có trích dẫn `'EOF'` – tránh JSON hỏng. Nên ghi các câu con của **cùng một đoạn văn** liền nhau.
- Chuỗi nhiều dòng giữ `\n` như lời giải; không thêm khoảng trắng đầu / cuối.

## Lỗi dễ mắc (tránh)

- Quên bọc ⟪ ⟫ quanh từ Nhật chen trong câu tiếng Việt (`Câu này ⟪｜表現《ひょうげん》⟫ rõ rằng…`), hoặc làm mất furigana của các từ đó; bọc cả dấu nháy vào trong ⟪ ⟫.
- Đưa câu Nhật nằm **trong câu tiếng Việt** vào `quotes` – sai, chỉ câu trích đứng riêng (dòng riêng / sau nhãn dẫn) mới là `quotes`.
- Giữ cặp 「」 bao ngoài câu trích, hoặc ( ) bao ngoài dòng dịch câu trích – phải bỏ.
- Chép nhãn dẫn (`Trích dẫn:`, `引用:`, `- Đoạn văn có câu:` …), `Nghĩa:`, `→ ĐÚNG.` vào JSON – phải bỏ (kết luận → `is_match`).
- Tự suy `is_match` theo đáp án khi lời giải có kết luận – sai, chép theo `→ ĐÚNG / → SAI` của lời giải.
- Tự tạo `summary`, `full_translation`, `key_info` – phải `null` (trừ `full_translation` ở khuôn lạ có bản dịch đoạn văn, xem `luu_y`).
- `option_ja` chép theo đề khi lời giải có dòng `i. …` – phải chép theo **lời giải** (có furigana).
- `correct.option_ja` khác `options[index-1].option_ja` (phải giống hệt, kể cả furigana).
