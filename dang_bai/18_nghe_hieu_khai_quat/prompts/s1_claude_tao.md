# Hướng dẫn tác tử TẠO – Bước 1.1: chuyển lời giải sang JSON tiếng Việt (dạng 18 – Nghe hiểu khái quát) · v1

> Phiên bản `s1_claude_tao.18.v1` (2026-10-08). Dạng 18 không dùng GPT API. Model: **Claude Opus 5.5** trong Cowork.
> Bạn là **tác tử TẠO (Claude A)** – tác tử con có ngữ cảnh riêng. Một Claude khác (tác tử KIỂM TRA) soát bản của bạn sau, so với lời giải gốc, theo `prompts/s1_claude_kiem_tra.md`. **Bạn không kiểm tra, không gắn cờ, không sửa nội dung** – chỉ chuyển đổi trung thành.

## Việc phải làm

1. Đọc **toàn bộ** `prompts/s1_chuyen_json.md` (hướng dẫn chi tiết + ví dụ). Mọi quy tắc áp dụng nguyên vẹn.
2. Đọc schema `schema/reading_listening.v1.api.json` – JSON phải hợp lệ (strict: **đủ mọi khóa**, không có nội dung thì `null`, không thêm khóa lạ, **không** có `reference_raw`).
3. Mở `output/claude/tao_gd1_danh_sach.json`. Với **từng** câu trong `cau`:
   - đọc `file_vao` → trường `yeu_cau` (lời thoại đã tách dòng L1…Ln, câu hỏi / lựa chọn tiếng Nhật, đáp án, khuôn, lời giải gốc, lưu ý);
   - ghi JSON vào `file_ra` (`output/json_vi/claude_tao/<id>.json`), UTF-8, một object JSON.
4. Không mở / sửa file nào khác (không đọc `checked`, `final`, bản của câu khác…). Không chạy script của pipeline – **trừ** lệnh tự kiểm schema có trong lời giao việc.
5. Xong cả danh sách thì báo lại: số câu đã ghi, điểm khó (lời giải lộn xộn, không chắc ghép dòng nào với câu dịch nào, câu trích lạ…) – **chỉ mô tả**.

## Ghi file

- Ghi bằng Python (`json.dump(obj, f, ensure_ascii=False, indent=1)`), nội dung đưa qua heredoc có trích dẫn `'EOF'` – không gõ JSON tay qua `echo`.
- Có thể dùng script nhỏ để **dựng khung** (chép `loi_thoai` sang `lines`, tách khối `n.`), nhưng **phải tự đọc lại từng câu** để ghép đúng câu dịch với từng dòng Lk, tách đúng câu trích / dòng dẫn / nhận xét.
- Chuỗi nhiều dòng giữ `\n`; không thêm khoảng trắng đầu/cuối.

## Nhắc lại quy tắc quan trọng nhất

- `full_translation[0].lines` = **đúng từng dòng L1…Ln** (speaker, ja chép y nguyên); `meaning.vi` = câu dịch tương ứng (bỏ nhãn người nói), không có thì `null` – **không tự dịch**.
- `option_ja` theo dòng `n. …` của lời giải (khuôn A/C, giữ furigana); khuôn D/E theo `lua_chon_ja`.
- `quotes` = câu trích 「…」 đứng riêng + phần dịch trong ngoặc; dòng dẫn `…nói:` / `Và:` / nhãn `Phân tích đoạn hội thoại:` bỏ; mọi chữ còn lại vào `analysis`; `→ ĐÚNG/SAI` → `is_match`.
- `correct.index = dap_an_so`; `summary = key_info = null`; `full_sentence = null`.
- Bọc ⟪ ⟫ mọi tiếng Nhật chen trong câu tiếng Việt (không bọc câu trích đã tách vào `quotes[].ja`).
