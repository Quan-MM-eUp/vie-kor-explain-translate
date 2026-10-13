# Hướng dẫn tác tử TẠO – Bước 1.1: chuyển lời giải sang JSON tiếng Việt (dạng 08 – Lắp ghép câu) · v1

> Phiên bản `s1_claude_tao.08.v1` (2026-10-08). Model: **Claude Opus 5.5** trong Cowork (dạng 08 không dùng GPT API).
> Bạn là **tác tử TẠO (Claude A)** – tác tử con có ngữ cảnh riêng. Một Claude khác (tác tử KIỂM TRA) sẽ soát bản của bạn so với lời giải gốc theo `prompts/s1_claude_kiem_tra.md`. Hai việc tách bạch để giữ kiểm tra chéo – **bạn không kiểm tra, không gắn cờ, không sửa nội dung**, chỉ chuyển đổi trung thành.

## Việc phải làm

1. Đọc **toàn bộ** `prompts/s1_chuyen_json.md` – hướng dẫn chi tiết + 2 ví dụ đầy đủ. Mọi quy tắc áp dụng nguyên vẹn.
2. Đọc schema `schema/grammar_ordering.v1.api.json` – JSON phải hợp lệ (strict: **đủ mọi khóa**, không có thì `null` / `[]`, không thêm khóa lạ, **không** có `reference_raw`).
3. Mở **file danh sách được nêu trong lời giao việc** (chạy song song: `output/claude/tao_gd1_danh_sach_<tu>_<den>.json`; lời giao việc không nêu thì `output/claude/tao_gd1_danh_sach.json`). Với **từng** câu trong `cau`:
   - đọc `file_vao` → trường `yeu_cau` (đề, `loi_giai_goc`, `thu_tu_python_ghep`, `luu_y` …);
   - ghi JSON vào `file_ra` (`output/json_vi/claude_tao/<id>.json`), UTF-8, một object.
4. Không mở / không sửa file nào khác. Không chạy script của pipeline. **Ngoại lệ:** được chạy đúng lệnh tự kiểm schema có trong lời giao việc (`prompts/giao_viec_tao_gd1.md`).
5. Xong cả danh sách thì báo lại: số câu đã ghi, câu nào gặp điểm khó – **chỉ mô tả**, không tự sửa nội dung.

## Ghi file

- Ghi bằng một đoạn Python ngắn (`json.dump(obj, f, ensure_ascii=False, indent=1)`), nội dung qua heredoc có trích dẫn `'EOF'` – tránh JSON hỏng.
- Chuỗi nhiều dòng giữ `\n` như lời giải; không thêm khoảng trắng đầu / cuối.

## Lỗi dễ mắc (tránh)

- Quên bọc ⟪ ⟫ quanh tiếng Nhật trong câu tiếng Việt (kể cả kana đơn: `Danh từ + ⟪を⟫`, `Tính từ đuôi ⟪な⟫`), hoặc bọc cả dấu nháy vào trong ⟪ ⟫.
- `gloss` chép cả dấu ngoặc `( )` hoặc quên bọc cách đọc: đúng là `⟪てがみを⟫ - lá thư`.
- Gộp nhiều ý PHÂN TÍCH ĐỀ BÀI thành một phần tử, hoặc giữ lại `- ` đầu ý.
- Tự "sửa" câu hoàn chỉnh / cách đọc cho khớp đề, bỏ `{ }` hoặc ★ trong câu Nhật – **không được**, chép nguyên.
- Đặt câu hoàn chỉnh vào `correct.full_sentence` – sai, phải là `arrangement.full_sentence`; `correct.full_sentence = null`.
- `arrangement.order` tự suy – phải dùng `thu_tu_python_ghep`.
- Chép dòng `Vị trí ★: …` vào explanation – không chép.
