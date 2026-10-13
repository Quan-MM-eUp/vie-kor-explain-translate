# Hướng dẫn Claude – Bước 2.4: kiểm tra bản dịch tiếng Hàn và sửa lỗi (dạng 06 – Ứng dụng từ) · v1

> **v1 (2026-10-07):** cột "Dịch từ" trong bảng xem nhanh: **JA** = nghĩa câu của lựa chọn (`analysis.options[i].sentence.meaning`) và nghĩa câu sửa (`analysis.options[i].correction.meaning`) dịch thẳng từ câu tiếng Nhật; **VI + JA** = câu nghĩa của từ được hỏi (`word.meaning` – theo `word.ja`); **VI** = cách dùng (`word.usage`), mở đầu, nhận xét từng lựa chọn, `correct.note` – theo tiếng Việt.

> Model: **Claude Opus 5.5**, chạy trong Claude Cowork (không qua API). Nếu chia việc cho tác tử con thì tác tử con cũng dùng Opus 5.5.

> **Từ 2026-10-08 (mẫu 101 trở đi):** bản dịch cần kiểm tra do **tác tử TẠO (Claude A, ngữ cảnh riêng)** dịch thay GPT – mọi chỗ "bản GPT" / "lỗi GPT" / "GPT dịch" dưới đây hiểu là bản / lỗi của tác tử TẠO; cách kiểm tra không đổi. Bạn (tác tử KIỂM TRA) không tạo lại bản, chỉ soát và sửa như với bản GPT.

**Nhiệm vụ:** kiểm tra bản dịch **có đúng với ngữ cảnh không** và sửa lỗi. Ngữ cảnh gồm: đề bài, các lựa chọn, đáp án, phần tiếng Nhật trong JSON và tiếng Việt của cả lời giải.

## Làm gì

Danh sách: `output/claude/gd2_danh_sach_<tu>_<den>.json` (chạy song song 2026-10-12; trước đó `gd2_danh_sach.json`) (tạo bằng `python scripts/s2_claude_goi.py …`). Mỗi câu có bảng xem nhanh `output/claude/gd2/<id>.md`.

1. Sửa trực tiếp **chỉ giá trị `ko`** trong `output/json_ko/checked/<id>.json`. Không sửa `vi`, `ja`, cấu trúc. File phải là JSON hợp lệ.
2. Ghi `output/json_ko/checked/<id>.ly_do.json` – **xong thì xóa khóa `_huong_dan`**. Không có gì sửa thì để `"sua": []`.
3. **Câu cố định** (nguồn `cau_co_dinh`): không sửa trong file; thấy chưa hay → ghi `[Khi dịch] Đề nghị sửa câu cố định: …` vào `ghi_chu_khi_dich`.
4. Phát hiện **chính JSON tiếng Việt sai** hoặc **mâu thuẫn nội bộ** (nghĩa bám tiếng Nhật mâu thuẫn với phần nhận xét bám tiếng Việt): không sửa theo ý mình, ghi `[Lỗi JSON VI] <phần>: <vấn đề>` vào `loi_json_vi` → câu quay lại GĐ1.
5. Làm xong cả danh sách thì chạy `python scripts/s2_kiem_tra.py …` và báo kết quả.

## Phạm vi sửa

- `loai` hợp lệ: `sai_so_ban_goc`, `chinh_ta` (gồm **trợ từ sai theo âm cuối**), `khach_quan`, `chu_quan`.
- Không thêm nội dung. Phần dịch từ tiếng Việt: không sửa theo ý mình khi tiếng Việt sai → ghi `[Bản gốc VI]`.
- Phần bám tiếng Nhật: sửa theo **tiếng Nhật** – khác bản Việt là bình thường.

## Checklist theo ngữ cảnh

- [ ] **(JA)** nghĩa câu của 4 lựa chọn dịch đúng câu tiếng Nhật (thì, thể, chủ thể, phủ định); câu dùng sai từ vẫn dịch đúng như câu đang viết, không tự sửa cho hợp lý; `{ }` đúng số cặp (D7).
- [ ] **(JA)** nghĩa câu sửa dịch đúng câu sửa; phần giống câu gốc dùng **cùng cách dịch** với nghĩa câu gốc, chỉ khác ở chỗ được sửa (D10 cảnh báo khi hai bản dịch trùng hệt dù câu Nhật khác); cùng câu tiếng Nhật ở mẫu khác thì cùng bản dịch (D4).
- [ ] **(VI + JA)** `word.meaning`: bắt đầu bằng trợ từ `는`/`은` (theo âm cuối cách đọc của từ – trường đứng ngay sau từ tiếng Nhật); giữ cấu trúc câu Việt, mỗi nghĩa trong ngoặc kép đúng với chính `word.ja` (cụm ngắn tiếng Hàn).
- [ ] **(VI)** nhận xét: kết luận "dùng đúng / không phù hợp / không tự nhiên / dùng đúng nhưng khác nghĩa định nghĩa" giữ đúng như tiếng Việt; từ thay thế và nghĩa của nó dịch đúng; nghĩa của từ được hỏi khi nhắc lại dùng cùng cách dịch với `word.meaning`.
- [ ] **Trợ từ sau `⟪ ⟫`** theo âm cuối của cách đọc **tiếng Nhật** (không theo âm Hán Hàn: `不足(ふそく)며`, không phải `이며`): ん → 과/은/을/이/이라는/이라고/이며/으로; nguyên âm → 와/는/를/가/라는/라고/며/로 – Python cảnh báo D12.
- [ ] Văn phong -습니다 ở phần nhận xét / cách dùng / mở đầu; tiếng Hàn tự nhiên; giữ nguyên `⟪ ⟫`, `{ }`, `｜…《…》`, xuống dòng, gạch đầu dòng, loại dấu ngoặc.

## Mẫu file lý do

```json
{
  "sua": [{"duong_dan": "$.analysis.options[1].correction.meaning", "loai": "khach_quan", "muc_do": "nhe",
           "ly_do": "(JA) Thống nhất phần giống câu gốc với nghĩa câu gốc của lựa chọn 2"}],
  "ghi_chu_ban_goc": [], "ghi_chu_khi_dich": [], "loi_json_vi": []
}
```
