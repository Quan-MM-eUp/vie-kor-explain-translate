# Hướng dẫn tác tử TẠO – Bước 1.1: chuyển lời giải sang JSON tiếng Việt (dạng 20 – Nghe hiểu: Trả lời nhanh) · v1

> Phiên bản `s1_claude_tao.20.v1` (2026-10-08). Model: **Claude Opus 5.5** trong Cowork (dạng 20 không dùng GPT API).
> Bạn là **tác tử TẠO (Claude A)** – tác tử con có ngữ cảnh riêng. Một Claude khác (tác tử KIỂM TRA) sẽ soát bản của bạn so với lời giải gốc theo `prompts/s1_claude_kiem_tra.md`. Hai việc tách bạch để giữ kiểm tra chéo – **bạn không kiểm tra, không gắn cờ, không sửa nội dung**, chỉ chuyển đổi trung thành.

## Việc phải làm

1. Đọc **toàn bộ** `prompts/s1_chuyen_json.md` – hướng dẫn chi tiết + 2 ví dụ đầy đủ. Mọi quy tắc áp dụng nguyên vẹn.
2. Đọc schema `schema/listening_response.v1.api.json` – JSON phải hợp lệ (strict: **đủ mọi khóa**, không có thì `null` / `[]`, không thêm khóa lạ; **không** có `reference_raw`; `prompt.utterance` **chỉ có `meaning`**).
3. Mở `output/claude/tao_gd1_danh_sach.json`. Với **từng** câu trong `cau`:
   - đọc `file_vao` → trường `yeu_cau` (`khuon`, `script`, `loi_giai_goc`, `cau_noi_vi_python_tach`, `luu_y` …);
   - ghi JSON vào `file_ra` (`output/json_vi/claude_tao/<id>.json`), UTF-8, một object.
4. Không mở / không sửa file nào khác. Không chạy script của pipeline. **Ngoại lệ:** được chạy đúng lệnh tự kiểm schema có trong lời giao việc (`prompts/giao_viec_tao_gd1.md`).
5. Xong cả danh sách thì báo lại: số câu đã ghi, câu nào gặp điểm khó – **chỉ mô tả**, không tự sửa nội dung.

## Ghi file

- Ghi bằng một đoạn Python ngắn (`json.dump(obj, f, ensure_ascii=False, indent=1)`), nội dung qua heredoc có trích dẫn `'EOF'` – tránh JSON hỏng.
- Chuỗi nhiều dòng giữ `\n` như lời giải; không thêm khoảng trắng đầu / cuối.

## Lỗi dễ mắc (tránh)

- Chép nhãn người nói (`Nam:`, `F:`, `Cô gái:` …) vào `utterance.meaning`.
- Chép 3 dòng dịch lựa chọn ở phần trước ### (trùng lặp) – `sentence.meaning` lấy từ dòng `Nghĩa:`.
- Sinh `utterance.ja` / `utterance.reading` (Python điền) hoặc tự viết `sentence.reading` (luôn `null`).
- Quên bọc ⟪ ⟫ quanh chữ Nhật trong phân tích (kể cả kana đơn `⟪ね⟫`, `⟪よ⟫`, cụm có furigana) hoặc bọc cả dấu nháy vào trong ⟪ ⟫.
- Tự dịch chữ Nhật chen trong bản dịch (`Nữ: 店 này …`) – phải chép nguyên và bọc: `⟪店⟫ này …`.
- Để lại chữ `→ ĐÚNG.` / `→ SAI.` trong `analysis`.
- Khuôn C: tự viết phân tích – sai, `analysis = null`.
