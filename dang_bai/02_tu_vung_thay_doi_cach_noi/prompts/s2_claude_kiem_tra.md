# Hướng dẫn Claude – Bước 2.4: kiểm tra bản dịch tiếng Hàn và sửa lỗi (dạng 02 – Thay đổi cách nói)

> Model: **Claude Opus 5.5**, chạy trong Claude Cowork (không qua API). Nếu chia việc cho tác tử con thì tác tử con cũng dùng Opus 5.5.

**Nhiệm vụ:** kiểm tra bản dịch **có đúng với ngữ cảnh không** và sửa lỗi. Ngữ cảnh gồm: đề bài, các lựa chọn, đáp án, phần tiếng Nhật trong JSON và tiếng Việt của cả lời giải.

## Làm gì

Danh sách: `output/claude/gd2_danh_sach.json` (tạo bằng `python scripts/s2_claude_goi.py …`). Mỗi câu có bảng xem nhanh `output/claude/gd2/<id>.md` (Mã / Vị trí / Tiếng Việt / Tiếng Hàn / Nguồn: GPT, câu cố định hoặc bộ nhớ dịch).

1. Sửa trực tiếp **chỉ giá trị `ko`** trong `output/json_ko/checked/<id>.json`. Không sửa `vi`, `ja`, cấu trúc. File phải là JSON hợp lệ.
2. Ghi `output/json_ko/checked/<id>.ly_do.json` – **xong thì xóa khóa `_huong_dan`**. Không có gì sửa thì để `"sua": []`.
3. **Câu cố định** (nguồn `cau_co_dinh`): không sửa trong file. Nếu thấy bản dịch cố định chưa hay/sai → ghi `[Khi dịch] Đề nghị sửa câu cố định: …` vào `ghi_chu_khi_dich` để cập nhật `glossary_ko.json` (sửa trong file sẽ bị Python báo lỗi D1).
4. Trường lấy từ **bộ nhớ dịch** vẫn kiểm tra như bản GPT (câu cũ có thể không hợp ngữ cảnh câu này).
5. Nếu phát hiện **chính JSON tiếng Việt sai** (vd phân tích nằm nhầm lựa chọn, kết luận bị nhét vào lựa chọn, `{ }` khác chỗ in đậm / gạch chân của bản gốc): không sửa, ghi vào `loi_json_vi` với nhãn `[Lỗi JSON VI]` → câu chuyển `CẦN_SỬA_GĐ1`.
6. Làm xong cả danh sách thì chạy `python scripts/s2_kiem_tra.py …` và báo kết quả.

## Phạm vi sửa

- Được sửa: `sai_so_ban_goc` (dịch thiếu/thừa, sai ký hiệu), `chinh_ta` (chính tả, khoảng cách, dấu câu tiếng Hàn), `khach_quan` (sai nghĩa, sai thuật ngữ, không nhất quán), `chu_quan` (thiếu tự nhiên, sai văn phong – chỉ diễn đạt lại cùng nội dung).
- Không thêm nội dung. Không sửa bản dịch theo ý mình khi tiếng Việt sai → ghi `[Bản gốc VI]`.

## Checklist theo ngữ cảnh

- [ ] `question.meaning` dịch đúng câu `question.ja`; mức lịch sự theo câu tiếng Nhật. Có `{ }` thì bọc đúng phần dịch của phần được hỏi; tiếng Việt không có `{ }` thì bản dịch cũng không có.
- [ ] Mỗi `analysis.options[i].analysis`: phần "Nghĩa là "…"" dịch đúng nghĩa của **`option_ja` của chính lựa chọn đó** trong ngữ cảnh câu đề (với lựa chọn là câu: dịch đúng cả câu tiếng Nhật đó); phần phân tích nói đúng về lựa chọn đó.
- [ ] Kết luận đồng nghĩa / không đồng nghĩa giữ đúng như tiếng Việt và khớp đáp án; `analysis.conclusion` dịch đúng số lựa chọn.
- [ ] `reference`: đủ dòng, giữ đánh số và xuống dòng; nghĩa của từng từ trong danh sách đúng với từ tiếng Nhật đứng trước.
- [ ] Thuật ngữ đồng nghĩa / gần nghĩa / câu gốc đúng bảng thuật ngữ, nhất quán trong toàn lời giải.
- [ ] Giữ nguyên `⟪ ⟫` (trợ từ viết liền sau `⟫`), `{ }`, `｜…《…》`, xuống dòng, loại dấu ngoặc.
- [ ] Văn phong -습니다 ở phân tích, kết luận, câu văn tham khảo; tiếng Hàn tự nhiên.

## Mẫu file lý do

```json
{
  "sua": [{"duong_dan": "$.analysis.options[0].analysis", "loai": "khach_quan", "muc_do": "nang",
           "ly_do": "'大切な' nghĩa là 'quan trọng', GPT dịch thành '소중히 하다' (động từ) – sửa thành '중요한'"}],
  "ghi_chu_ban_goc": [], "ghi_chu_khi_dich": [], "loi_json_vi": []
}
```
