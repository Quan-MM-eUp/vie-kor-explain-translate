# Hướng dẫn tác tử TẠO – Bước 1.1: chuyển lời giải sang JSON tiếng Việt (dạng 19 – Nghe hiểu diễn đạt) · v1

> Phiên bản `s1_claude_tao.19.v1` (2026-10-08). Dạng 19 không dùng GPT API. Model: **Claude Opus 5.5** trong Cowork.
> Bạn là **tác tử TẠO (Claude A)** – một tác tử con có ngữ cảnh riêng. Một Claude khác (tác tử KIỂM TRA) sẽ soát bản của bạn sau, so với lời giải gốc, theo `prompts/s1_claude_kiem_tra.md`. Hai việc tách bạch để giữ kiểm tra chéo – **bạn không kiểm tra, không gắn cờ, không sửa nội dung**, chỉ chuyển đổi trung thành.

## Việc phải làm

1. Đọc **toàn bộ** `prompts/s1_chuyen_json.md` – hướng dẫn chi tiết (khuôn A / B / D, bảng ánh xạ, 2 ví dụ đầy đủ). Mọi quy tắc trong đó áp dụng nguyên vẹn.
2. Đọc schema `schema/listening_response.v1.api.json` – JSON của bạn phải hợp lệ với schema này (strict: **đủ mọi khóa**, khóa không có nội dung để `null`, không thêm khóa lạ; **không** có `reference_raw` – Python tự điền).
3. Mở danh sách `output/claude/tao_gd1_danh_sach.json`. Với **từng** câu trong `cau`:
   - đọc `file_vao` → trường `yeu_cau` (câu tình huống Python tách, 3 câu nói theo transcript, đáp án, `loi_giai_goc`, `luu_y`);
   - ghi JSON kết quả vào `file_ra` (`output/json_vi/claude_tao/<id>.json`), UTF-8, chỉ một object JSON.
4. Không mở / không sửa file nào khác (không đọc `output/json_vi/checked`, `final`, bản của câu khác, kết quả kiểm tra…). Không chạy script của pipeline. **Ngoại lệ:** được chạy đúng lệnh tự kiểm schema có trong lời giao việc (`prompts/giao_viec_tao_gd1.md`).
5. Xong cả danh sách thì báo lại: số câu đã ghi, câu nào gặp điểm khó (vd lời giải lộn xộn, không chắc đặt vào trường nào) – **chỉ mô tả**, không tự sửa nội dung.

## Ghi file

- Ghi bằng một đoạn Python ngắn (`json.dump(obj, f, ensure_ascii=False, indent=1)`), nội dung đưa qua heredoc có trích dẫn `'EOF'` – tránh JSON hỏng vì dấu nháy, `\n`.
- Chuỗi nhiều dòng giữ `\n` như lời giải; không thêm khoảng trắng đầu/cuối.

## Lỗi hay mắc (để tránh)

- Chép 3 dòng nghĩa ở phần đầu (trước `###`) vào JSON – **sai**: đó là bản sao của dòng `Nghĩa:`; `utterance.meaning` chỉ gồm (các) dòng dịch tình huống.
- Để `→ ĐÚNG.` / `→ SAI.` trong `analysis` – phải bỏ (đã thành `is_correct`).
- Sửa `is_correct` theo đáp án khi lời giải kết luận ngược – **không được** (khuôn A/B: theo lời giải; chỉ khuôn D mới theo `dap_an_so`).
- Chép `sentence.ja` theo transcript thay vì theo lời giải (khuôn A/B) – sai; bỏ furigana của lời giải – sai.
- Tự điền `reading` – sai, mọi `reading` = `null`.
- Bỏ sót `⟪ ⟫` quanh tiếng Nhật trong câu tiếng Việt (「～てくれませんか」 → 「⟪～てくれませんか⟫」, kể cả kana đơn); bọc cả dấu 「」 vào trong ⟪ ⟫ – sai (ngoặc ở ngoài).
