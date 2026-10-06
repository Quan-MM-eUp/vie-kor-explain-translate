# Hướng dẫn Claude – Bước 2.4: kiểm tra bản dịch tiếng Hàn và sửa lỗi (dạng 03 – Cách viết từ) · v1

> **v1 (2026-10-05):** cột "Dịch từ" trong bảng xem nhanh: **JA** = `question.meaning` dịch thẳng từ câu tiếng Nhật; **VI + JA** = phân tích lựa chọn – nghĩa trong "có nghĩa là "…"" kiểm tra theo `option_ja`, phần còn lại theo tiếng Việt; **VI + VD** = tham khảo – dòng nghĩa của câu ví dụ kiểm tra theo câu ví dụ tiếng Nhật ngay phía trên, phần còn lại theo tiếng Việt; **VI** = theo tiếng Việt.

> Model: **Claude Opus 5.5**, chạy trong Claude Cowork (không qua API). Nếu chia việc cho tác tử con thì tác tử con cũng dùng Opus 5.5.

**Nhiệm vụ:** kiểm tra bản dịch **có đúng với ngữ cảnh không** và sửa lỗi. Ngữ cảnh gồm: đề bài, các lựa chọn, đáp án, phần tiếng Nhật trong JSON và tiếng Việt của cả lời giải.

## Làm gì

Danh sách: `output/claude/gd2_danh_sach.json` (tạo bằng `python scripts/s2_claude_goi.py …`). Mỗi câu có bảng xem nhanh `output/claude/gd2/<id>.md`.

1. Sửa trực tiếp **chỉ giá trị `ko`** trong `output/json_ko/checked/<id>.json`. Không sửa `vi`, `ja`, cấu trúc. File phải là JSON hợp lệ.
2. Ghi `output/json_ko/checked/<id>.ly_do.json` – **xong thì xóa khóa `_huong_dan`**. Không có gì sửa thì để `"sua": []`.
3. **Câu cố định** (nguồn `cau_co_dinh`, vd "존재하지 않는 단어입니다."): không sửa trong file. Thấy chưa hay/sai → ghi `[Khi dịch] Đề nghị sửa câu cố định: …` vào `ghi_chu_khi_dich`.
4. Trường lấy từ **bộ nhớ dịch** vẫn kiểm tra như bản GPT.
5. Phát hiện **chính JSON tiếng Việt sai** (phân tích nằm nhầm lựa chọn, đoạn bẫy bị nhét vào lựa chọn 4, `{ }` sai chỗ…) hoặc **mâu thuẫn nội bộ** (nghĩa lựa chọn bám tiếng Nhật mâu thuẫn với phần bám tiếng Việt): không sửa theo ý mình, ghi `[Lỗi JSON VI] <phần>: <vấn đề>` vào `loi_json_vi` → câu quay lại GĐ1.
6. Làm xong cả danh sách thì chạy `python scripts/s2_kiem_tra.py …` và báo kết quả.

## Phạm vi sửa

- `loai` hợp lệ: `sai_so_ban_goc` (dịch thiếu/thừa, sai ký hiệu), `chinh_ta` (chính tả, khoảng cách, dấu câu, **trợ từ sai theo âm cuối**), `khach_quan` (sai nghĩa, sai thuật ngữ, không nhất quán), `chu_quan` (thiếu tự nhiên, sai văn phong – chỉ diễn đạt lại cùng nội dung).
- Không thêm nội dung. Phần dịch từ tiếng Việt: không sửa theo ý mình khi tiếng Việt sai → ghi `[Bản gốc VI]`.
- Phần bám tiếng Nhật (nghĩa câu đề, nghĩa của lựa chọn, dòng nghĩa câu ví dụ): sửa theo **tiếng Nhật** – khác bản Việt là bình thường.

## Checklist theo ngữ cảnh

- [ ] **(JA)** `question.meaning` dịch đúng và đủ câu `question.ja`; số cặp `{ }` bằng câu Nhật, bọc đúng phần tương ứng (D7); không còn ①②③④ / furigana; cùng câu Nhật thì cùng bản dịch (D4).
- [ ] **(VI + JA)** Nghĩa trong "có nghĩa là "…"" là nghĩa của **chính `option_ja`** (đúng từ loại); "Đọc là ⟪X⟫" → `⟪X⟫라고 읽으며…`; lựa chọn không tồn tại dùng đúng câu cố định / không bị thêm nghĩa.
- [ ] **(VI + VD)** Dòng nghĩa của từng câu ví dụ dịch đúng câu ví dụ tiếng Nhật ngay phía trên; dòng câu ví dụ và dòng cách đọc giữ nguyên `⟪ ⟫`; đủ dòng, đúng thứ tự, giữ +/- và đánh số (D2).
- [ ] Đoạn giải thích bẫy (`analysis.conclusion`) giữ đúng số lựa chọn, chữ Hán, âm đọc; on'yomi / kun'yomi → 음독 / 훈독.
- [ ] **Trợ từ sau `⟪ ⟫`** theo âm cuối của cách đọc tiếng Nhật: ん → 과/은/을/이라는/이라고; nguyên âm → 와/는/를/라는/라고.
- [ ] Văn phong -습니다 ở mọi câu văn (không đuôi -음/-ㅁ, không cụt "…라는 뜻."); câu dùng "저는 …" thống nhất với câu đề khi có chủ ngữ ngôi 1.
- [ ] Giữ nguyên `⟪ ⟫`, `{ }`, `｜…《…》`, xuống dòng, loại dấu ngoặc.

## Mẫu file lý do

```json
{
  "sua": [{"duong_dan": "$.analysis.options[0].analysis", "loai": "khach_quan", "muc_do": "nang",
           "ly_do": "(VI+JA) 抵抗 nghĩa là 'kháng cự' – GPT dịch '저항하다' (động từ) trong khi lựa chọn là danh từ → '저항'"},
          {"duong_dan": "$.reference", "loai": "chinh_ta", "muc_do": "nhe",
           "ly_do": "Tiểu từ theo âm đọc: けいやく kết thúc bằng nguyên âm → 와"}],
  "ghi_chu_ban_goc": [], "ghi_chu_khi_dich": [], "loi_json_vi": []
}
```
