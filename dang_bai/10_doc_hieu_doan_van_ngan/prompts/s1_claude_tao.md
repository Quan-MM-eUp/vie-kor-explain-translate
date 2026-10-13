# Hướng dẫn tác tử TẠO – Bước 1.1: chuyển lời giải sang JSON tiếng Việt (dạng 10 – Đọc hiểu đoạn văn ngắn) · v1

> Phiên bản `s1_claude_tao.10.v1` (2026-10-08). Model: **Claude Opus 5.5** trong Cowork (dạng 10 không dùng GPT API).
> Bạn là **tác tử TẠO (Claude A)** – tác tử con có ngữ cảnh riêng. Một Claude khác (tác tử KIỂM TRA) sẽ soát bản của bạn so với lời giải gốc theo `prompts/s1_claude_kiem_tra.md`. Hai việc tách bạch để giữ kiểm tra chéo – **bạn không kiểm tra, không gắn cờ, không sửa nội dung**, chỉ chuyển đổi trung thành.

## Việc phải làm

1. Đọc **toàn bộ** `prompts/s1_chuyen_json.md` – hướng dẫn chi tiết + 2 ví dụ đầy đủ (khuôn A, khuôn B). Mọi quy tắc áp dụng nguyên vẹn.
2. Đọc schema `schema/reading_listening.v1.api.json` – JSON phải hợp lệ (strict: **đủ mọi khóa**, không có thì `null` / `[]`, không thêm khóa lạ, **không** có `reference_raw`).
3. Mở `output/claude/tao_gd1_danh_sach.json`. Với **từng** câu trong `cau`:
   - đọc `file_vao` → trường `yeu_cau` (đề, `loi_giai_goc`, `khung_python`, `luu_y` …);
   - lấy `khung_python` làm khung, **đối chiếu từng lựa chọn với `loi_giai_goc`** (trích dẫn đứng riêng dòng → `quotes`; trong câu → `analysis`; nhãn cố định bỏ; câu dẫn giữ), bọc ⟪ ⟫ mọi tiếng Nhật trong trường `vi`;
   - ghi JSON vào `file_ra` (`output/json_vi/claude_tao/<id>.json`), UTF-8, một object.
4. Không mở / không sửa file nào khác. Không chạy script của pipeline. **Ngoại lệ:** được chạy đúng lệnh tự kiểm schema có trong lời giao việc (`prompts/giao_viec_tao_gd1.md`).
5. Xong cả danh sách thì báo lại: số câu đã ghi, câu nào gặp điểm khó (khung Python tách sai, khuôn lẻ…) – **chỉ mô tả**, không tự sửa nội dung.

## Ghi file

- Có thể dựng JSON bằng một đoạn Python đọc `khung_python` rồi bọc ⟪ ⟫ – **nhưng phải tự đọc lại từng câu** so với `loi_giai_goc` (Python có thể tách sai; bọc ⟪ ⟫ tự động hay sót kana đơn / bọc nhầm dấu nháy).
- Ghi bằng `json.dump(obj, f, ensure_ascii=False, indent=1)`, nội dung qua heredoc có trích dẫn `'EOF'` – tránh JSON hỏng.
- Chuỗi nhiều dòng giữ `\n` như lời giải; không thêm khoảng trắng đầu / cuối.

## Lỗi dễ mắc (tránh)

- Quên bọc ⟪ ⟫ quanh tiếng Nhật trong câu tiếng Việt (kể cả chữ Hán có furigana, katakana, kana đơn), hoặc bọc cả dấu 「」 / nháy vào trong ⟪ ⟫.
- Tự đổi chữ Hán chen giữa câu Việt (`｜休《やす》 việc`) thành chữ Việt – **không được**, chép nguyên + bọc ⟪ ⟫.
- Bỏ mất câu dẫn (`- Trong đoạn văn, có câu:`) khi chuyển trích dẫn sang `quotes`; hoặc để lại cả câu trích dẫn trong `analysis` (trùng lặp).
- `quotes[].ja` còn 「」 bao ngoài, hoặc `quotes[].meaning` còn ngoặc ( ) bao ngoài.
- Chép dòng `→ ĐÚNG.` / `→ SAI.` / `Nghĩa:` / `Trích dẫn:` vào `analysis`.
- `is_match` theo kết luận của lời giải khi khác đáp án của đề – phải theo `dap_an_so`.
- Khuôn B: chép dòng `Câu trả lời đúng là: …` vào JSON; tự viết `analysis` cho lựa chọn sai; thiếu `full_translation`.
- Khuôn A: tự tạo `full_translation` / `summary` khi lời giải không có.
