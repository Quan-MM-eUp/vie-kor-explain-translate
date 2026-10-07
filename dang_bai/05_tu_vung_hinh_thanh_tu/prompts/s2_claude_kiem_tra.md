# Hướng dẫn Claude – Bước 2.4: kiểm tra bản dịch tiếng Hàn và sửa lỗi (dạng 05 – Hình thành từ) · v1

> **v1 (2026-10-06):** cột "Dịch từ" trong bảng xem nhanh: **JA** = `question.meaning` (câu đề có chỗ trống) và `correct.full_sentence.meaning` (câu hoàn chỉnh) dịch thẳng từ câu tiếng Nhật; **VI + JA** = nghĩa gốc của lựa chọn (`gloss` – theo `option_ja`), nghĩa từ ghép (`compound.meaning` – theo `compound.ja`), nghĩa từ tham khảo (`reference.terms[j].meaning` – theo `terms[j].ja`); **VI** = phần nhận xét (`analysis`), câu giới thiệu tham khảo – theo tiếng Việt.

> Model: **Claude Opus 5.5**, chạy trong Claude Cowork (không qua API). Nếu chia việc cho tác tử con thì tác tử con cũng dùng Opus 5.5.

**Nhiệm vụ:** kiểm tra bản dịch **có đúng với ngữ cảnh không** và sửa lỗi. Ngữ cảnh gồm: đề bài, các lựa chọn, đáp án, phần tiếng Nhật trong JSON và tiếng Việt của cả lời giải.

## Làm gì

Danh sách: `output/claude/gd2_danh_sach.json` (tạo bằng `python scripts/s2_claude_goi.py …`). Mỗi câu có bảng xem nhanh `output/claude/gd2/<id>.md`.

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

- [ ] **(JA)** `question.meaning` dịch đúng câu `question.ja`; **giữ đúng ký hiệu và số chỗ trống** (D8), đặt **sát từ tiếng Hàn tương ứng với từ đang được ghép**; câu vẫn hợp lý khi điền đáp án; `{ }` đúng số cặp (D7).
- [ ] **(JA)** `correct.full_sentence.meaning` dịch đúng câu hoàn chỉnh; phần giống câu đề dùng **cùng cách dịch** với `question.meaning`; cùng câu tiếng Nhật ở mẫu khác thì cùng bản dịch (D4).
- [ ] **(VI + JA)** `gloss` là nghĩa của **chính `option_ja`** (đúng dạng – Python cảnh báo D6); `compound.meaning` là nghĩa của **chính `compound.ja`**; `terms[j].meaning` là nghĩa của **chính `terms[j].ja`**; đều là cụm nghĩa ngắn (không đuôi -습니다), giữ số nghĩa / dấu câu như bản Việt; từ ghép đáp án dịch giống nhau ở nghĩa từ ghép, câu hoàn chỉnh và tham khảo.
- [ ] **(VI)** `reference.intro`: nghĩa trong ngoặc kép (nhắc lại nghĩa gốc của đáp án) dùng **đúng nguyên văn** bản dịch `gloss` của đáp án – Python cảnh báo D9 khi lệch.
- [ ] **(VI)** `analysis`: kết luận "không có nghĩa / có nghĩa nhưng không phù hợp / phù hợp" giữ đúng như tiếng Việt (câu cố định "Không có nghĩa trong tiếng Nhật." dùng bản dịch trong bảng thuật ngữ).
- [ ] **Trợ từ sau `⟪ ⟫`** theo âm cuối của cách đọc tiếng Nhật: ん → 과/은/을/이라는/이라고; nguyên âm → 와/는/를/라는/라고.
- [ ] Văn phong -습니다 ở phần nhận xét và câu giới thiệu tham khảo; tiếng Hàn tự nhiên; giữ nguyên `⟪ ⟫`, `{ }`, `｜…《…》`, xuống dòng, loại dấu ngoặc.

## Mẫu file lý do

```json
{
  "sua": [{"duong_dan": "$.correct.full_sentence.meaning", "loai": "khach_quan", "muc_do": "nhe",
           "ly_do": "(JA) Thống nhất phần giống câu đề với question.meaning"}],
  "ghi_chu_ban_goc": [], "ghi_chu_khi_dich": [], "loi_json_vi": []
}
```
