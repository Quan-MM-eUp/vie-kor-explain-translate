# Hướng dẫn tác tử TẠO – Bước 1.1: chuyển lời giải sang JSON tiếng Việt (dạng 12 – Đọc hiểu: Đoạn văn dài) · v1

> Phiên bản `s1_claude_tao.12.v1` (2026-10-08). Dạng 12 không dùng GPT API. Model: **Claude Opus 5.5** trong Cowork.
> Bạn là **tác tử TẠO (Claude A)** – một tác tử con có ngữ cảnh riêng. Một Claude khác (tác tử KIỂM TRA) sẽ soát bản của bạn sau, so với lời giải gốc và đoạn văn, theo `prompts/s1_claude_kiem_tra.md`. Hai việc tách bạch để giữ kiểm tra chéo – **bạn không kiểm tra, không gắn cờ, không sửa nội dung**, chỉ chuyển đổi trung thành.

## Việc phải làm

1. Đọc **toàn bộ** `prompts/s1_chuyen_json.md` – hướng dẫn chi tiết (ánh xạ, câu trích, khuôn bất thường, 4 ví dụ). Mọi quy tắc trong đó áp dụng nguyên vẹn.
2. Đọc schema `schema/reading_listening.v1.api.json` – JSON của bạn phải hợp lệ với schema này (strict: **đủ mọi khóa**, khóa không có nội dung để `null` / `[]`, không thêm khóa lạ; **không** có `reference_raw` – Python tự điền).
3. Mở danh sách `output/claude/tao_gd1_danh_sach.json`. Với **từng** câu trong `cau`:
   - đọc `file_vao` → trường `yeu_cau` (khuôn lời giải, đoạn văn chỉ để hiểu, đề, `loi_giai_goc`, `luu_y`);
   - ghi JSON kết quả vào `file_ra` (`output/json_vi/claude_tao/<id>.json`), UTF-8, chỉ một object JSON.
   - Các câu của **cùng một đoạn văn** thường nằm liền nhau – đọc đoạn văn một lần, dùng cho các câu đó.
4. Không mở / không sửa file nào khác (không đọc `output/json_vi/checked`, `final`, bản của lô khác, kết quả kiểm tra…). Không chạy script của pipeline. **Ngoại lệ:** được chạy đúng lệnh tự kiểm schema có trong lời giao việc (`prompts/giao_viec_tao_gd1.md`).
5. Xong cả danh sách thì báo lại: số câu đã ghi, câu nào gặp điểm khó (lời giải lộn xộn, không chắc đâu là câu trích / đâu là nhận xét, khối thiếu…) – **chỉ mô tả**, không tự sửa nội dung.

## Ghi file

- Ghi bằng một đoạn Python ngắn (`json.dump(obj, f, ensure_ascii=False, indent=1)`), nội dung đưa vào qua heredoc có trích dẫn `'EOF'` – **không** gõ JSON qua `echo`.
- Chuỗi nhiều dòng giữ `\n` như lời giải; không thêm khoảng trắng đầu/cuối.
- Câu tiếng Nhật dài, nhiều furigana: chép **nguyên** từ `loi_giai_goc` (có thể dùng Python cắt chuỗi từ đầu vào thay vì gõ lại để tránh sai ký tự) – nhưng PHẢI tự đọc lại từng câu so với lời giải để chắc đúng trường.

## Nhắc lại các lỗi hay mắc (để tránh)

- Sửa câu trích theo đoạn văn / sửa lựa chọn theo đề – **không được**, chép như lời giải.
- Để nguyên 「」 bao ngoài câu trích, hoặc ( ) bao ngoài phần dịch câu trích.
- Coi câu giải thích bắt đầu bằng 「từ」 là câu trích (vd `「しかし」 (Tuy nhiên) là từ dùng để…`).
- `is_match` theo đáp án của đề thay vì theo `→ ĐÚNG / → SAI` của lời giải.
- Bỏ sót ⟪ ⟫ quanh tiếng Nhật trong câu tiếng Việt (kể cả từ có furigana, kana đơn).
- Khuôn chỉ bản dịch: chép dòng "Câu trả lời đúng là: …" (không chép); khuôn tự do: chia lời giải ra nhiều lựa chọn (toàn bộ vào lựa chọn đáp án).
