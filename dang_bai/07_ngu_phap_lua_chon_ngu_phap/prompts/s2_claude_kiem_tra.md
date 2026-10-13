# Hướng dẫn Claude – Bước 2.4: kiểm tra bản dịch tiếng Hàn và sửa lỗi (dạng 07 – Lựa chọn ngữ pháp) · v1

> **Quy tắc THAM KHẢO (2026-10-07):** phần THÔNG TIN THAM KHẢO **không dịch** – JSON chỉ còn trường `reference_raw` (nguyên văn tiếng Việt, không có khóa `ko`, không nằm trong danh sách id cần dịch). Các hướng dẫn cũ về dịch / kiểm tra tham khảo bên dưới không còn áp dụng.

> **v1 (2026-10-07):** cột "Dịch từ" trong bảng xem nhanh: **JA** = nghĩa câu đề (`question.meaning`), nghĩa câu áp dụng (`analysis.options[i].applied.meaning`), nghĩa câu hoàn chỉnh (`correct.full_sentence.meaning`) – dịch thẳng từ câu tiếng Nhật; **VI + JA** = 'Ý nghĩa' của mẫu ngữ pháp (`analysis.options[i].meaning` – theo `option_ja`); **VI** = cấu trúc, nhận xét ngữ pháp / ngữ nghĩa, cấu trúc chung, ghi chú – theo tiếng Việt.

> Model: **Claude Opus 5.5**, chạy trong Claude Cowork (không qua API). Nếu chia việc cho tác tử con thì tác tử con cũng dùng Opus 5.5.

> **Từ 2026-10-08 (mẫu 61 trở đi):** bản dịch cần kiểm tra do **tác tử TẠO (Claude A, ngữ cảnh riêng)** dịch thay GPT – "bản GPT" dưới đây hiểu là bản của tác tử TẠO; cách kiểm tra không đổi.

**Nhiệm vụ:** kiểm tra bản dịch **có đúng với ngữ cảnh không** và sửa lỗi. Ngữ cảnh gồm: đề bài, các lựa chọn, đáp án, phần tiếng Nhật trong JSON và tiếng Việt của cả lời giải.

## Làm gì

Danh sách: `output/claude/gd2_danh_sach_<tu>_<den>.json` (chạy song song 2026-10-12; trước đó `gd2_danh_sach.json`) (tạo bằng `python scripts/s2_claude_goi.py …`). Mỗi câu có bảng xem nhanh `output/claude/gd2/<id>.md`.

1. Sửa trực tiếp **chỉ giá trị `ko`** trong `output/json_ko/checked/<id>.json`. Không sửa `vi`, `ja`, cấu trúc. File phải là JSON hợp lệ.
2. Ghi `output/json_ko/checked/<id>.ly_do.json` – **xong thì xóa khóa `_huong_dan`**. Không có gì sửa thì để `"sua": []`.
3. **Câu cố định** (nguồn `cau_co_dinh`): không sửa trong file; thấy chưa hay → ghi `[Khi dịch] Đề nghị sửa câu cố định: …` vào `ghi_chu_khi_dich`.
4. Phát hiện **chính JSON tiếng Việt sai** hoặc **mâu thuẫn nội bộ** (nghĩa câu bám tiếng Nhật mâu thuẫn với nhận xét bám tiếng Việt): không sửa theo ý mình, ghi `[Lỗi JSON VI] <phần>: <vấn đề>` vào `loi_json_vi` → câu quay lại GĐ1.
5. Làm xong cả danh sách thì chạy `python scripts/s2_kiem_tra.py …` và báo kết quả.

## Phạm vi sửa

- `loai` hợp lệ: `sai_so_ban_goc`, `chinh_ta` (gồm **trợ từ sai theo âm cuối**), `khach_quan`, `chu_quan`.
- Không thêm nội dung. Phần dịch từ tiếng Việt: không sửa theo ý mình khi tiếng Việt sai → ghi `[Bản gốc VI]`.
- Phần bám tiếng Nhật: sửa theo **tiếng Nhật** – khác bản Việt là bình thường.

## Checklist theo ngữ cảnh

- [ ] **(JA)** nghĩa câu đề giữ đủ chỗ trống, không tự điền (D13).
- [ ] **(JA)** nghĩa câu áp dụng của 4 lựa chọn dịch đúng câu tiếng Nhật (thì, thể, phủ định, bị động, sai khiến, khả năng, chủ thể); lựa chọn sai vẫn dịch đúng như câu đang viết; phần giống nhau giữa các câu áp dụng dịch giống nhau; `{ }` đúng số cặp (D7).
- [ ] **(JA)** nghĩa câu hoàn chỉnh giống hệt bản dịch nghĩa câu áp dụng của đáp án khi câu Nhật giống nhau (D14).
- [ ] **(VI + JA)** 'Ý nghĩa' mẫu ngữ pháp: giữ cấu trúc câu Việt, mỗi nghĩa trong nháy đúng với chính mẫu tiếng Nhật, cách giải thích chuẩn của sách ngữ pháp tiếng Hàn.
- [ ] **(VI)** cấu trúc: thuật ngữ ngữ pháp tiếng Hàn chuẩn (동사 て형, 명사, い형용사, 보통형, 정중형…), giữ `+ / ( )` và khối `⟪ ⟫`; nhận xét: kết luận Đúng / Sai / Phù hợp / Không phù hợp và lý do giữ đúng như tiếng Việt.
- [ ] **Trợ từ sau `⟪ ⟫`** theo âm cuối của cách đọc **tiếng Nhật** (không theo âm Hán Hàn): ん → 과/은/을/이/이라는/이라고/이며/으로; nguyên âm → 와/는/를/가/라는/라고/며/로 – Python cảnh báo D12 (kiểm tra cả bản GPT trước khi sửa).
- [ ] Văn phong -습니다 ở phần ý nghĩa / nhận xét / cấu trúc chung; tiếng Hàn tự nhiên; giữ nguyên `⟪ ⟫`, `{ }`, `｜…《…》`, xuống dòng, gạch đầu dòng, loại dấu ngoặc.
- [ ] GPT gộp / tách câu làm **mất một khối `⟪ ⟫`** so với bản Việt → tách lại cho đủ (Python báo "nội dung ⟪ ⟫ khác bản tiếng Việt").

## Mẫu file lý do

```json
{
  "sua": [{"duong_dan": "$.analysis.options[1].applied.meaning", "loai": "khach_quan", "muc_do": "nhe",
           "ly_do": "(JA) Thống nhất phần ngoài chỗ điền với nghĩa câu áp dụng của lựa chọn 1"}],
  "ghi_chu_ban_goc": [], "ghi_chu_khi_dich": [], "loi_json_vi": []
}
```
