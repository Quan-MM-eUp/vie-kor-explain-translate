# Hướng dẫn Claude – Bước 2.4: kiểm tra bản dịch tiếng Hàn và sửa lỗi (dạng 01) · PIPELINE v3

> **v3:** `word.meaning` và `question.meaning` được dịch **TRỰC TIẾP từ tiếng Nhật** (cột "Dịch từ" = **JA** trong bảng xem nhanh) – kiểm tra theo **tiếng Nhật**, không theo tiếng Việt. Các trường còn lại vẫn kiểm tra theo tiếng Việt. Đường dẫn `output/…` là `pipeline_v3/output/…`.

> Model: **Claude Opus 5.5**, chạy trong Claude Cowork (không qua API). Nếu chia việc cho tác tử con thì tác tử con cũng dùng Opus 5.5.

**Nhiệm vụ:** kiểm tra bản dịch **có đúng với ngữ cảnh không** và sửa lỗi. Ngữ cảnh gồm: đề bài, các lựa chọn, đáp án, phần tiếng Nhật trong JSON và tiếng Việt của cả lời giải.

## Làm gì

Danh sách: `output/claude/gd2_danh_sach.json` (tạo bằng `python scripts/s2_claude_goi.py …`). Mỗi câu có bảng xem nhanh `output/claude/gd2/<id>.md` (Mã / Vị trí / Dịch từ JA|VI / Bản nguồn / Tiếng Hàn / Nguồn: GPT, câu cố định hoặc bộ nhớ dịch / Tiếng Việt chỉ để đối chiếu).

1. Sửa trực tiếp **chỉ giá trị `ko`** trong `output/json_ko/checked/<id>.json`. Không sửa `vi`, `ja`, cấu trúc. File phải là JSON hợp lệ.
2. Ghi `output/json_ko/checked/<id>.ly_do.json` – **xong thì xóa khóa `_huong_dan`**. Không có gì sửa thì để `"sua": []`.
3. **Câu cố định** (nguồn `cau_co_dinh`): không sửa trong file. Nếu thấy bản dịch cố định chưa hay/sai → ghi `[Khi dịch] Đề nghị sửa câu cố định: …` vào `ghi_chu_khi_dich` để cập nhật `glossary_ko.json` (sửa trong file sẽ bị Python báo lỗi D1).
4. Trường lấy từ **bộ nhớ dịch** vẫn kiểm tra như bản GPT (câu cũ có thể không hợp ngữ cảnh câu này).
5. Nếu phát hiện **chính JSON tiếng Việt sai** (vd phân tích nằm nhầm lựa chọn, thiếu nội dung so với bản gốc): không sửa, ghi vào `loi_json_vi` với nhãn `[Lỗi JSON VI]` → câu chuyển `CẦN_SỬA_GĐ1`.
6. Làm xong cả danh sách thì chạy `python scripts/s2_kiem_tra.py …` và báo kết quả.

## Phạm vi sửa

- Được sửa: `sai_so_ban_goc` (dịch thiếu/thừa, sai ký hiệu), `chinh_ta` (chính tả, khoảng cách, dấu câu tiếng Hàn), `khach_quan` (sai nghĩa, sai thuật ngữ, không nhất quán), `chu_quan` (thiếu tự nhiên, sai văn phong – chỉ diễn đạt lại cùng nội dung).
- Không thêm nội dung. Trường dịch từ tiếng Việt: không sửa bản dịch theo ý mình khi tiếng Việt sai → ghi `[Bản gốc VI]`.
- Trường dịch từ tiếng Nhật: sửa theo **tiếng Nhật** – bản Hàn khác bản Việt là bình thường (không phải lỗi).
- **Mâu thuẫn nội bộ:** Nghĩa từ / Nghĩa câu (bám tiếng Nhật) mâu thuẫn với phân tích hoặc tham khảo (bám tiếng Việt) – vd Nghĩa từ 吟味 = 엄선하다 nhưng tham khảo nói 시식 – nghĩa là **tiếng Việt sai nội dung**: không sửa phần tham khảo theo ý mình, ghi `[Lỗi JSON VI] <phần>: <mâu thuẫn gì>` vào `loi_json_vi` → câu quay lại GĐ1 để gắn cờ `nghi_noi_dung` (chặn dịch, chuyển CTV tiếng Nhật).

## Checklist theo ngữ cảnh

- [ ] **(JA)** `word.meaning` là nghĩa được dùng trong câu đề, **theo đúng dạng của `word.ja`** trong câu (chỉ xét phần trong `{ }` – ngữ pháp ngoài `{ }` không tính: 厳しく{処罰}される → `처벌; 형벌`, câu `{처벌}된다`): bị động / sai khiến / phủ định / thì / từ loại (催された → 개최되었다, 詳しく → 자세히, 惜しまない → 아끼지 않다); liệt kê bằng "; ", không -습니다. Python cảnh báo D6 khi nghi mất phủ định / bị động.
- [ ] **(JA)** `question.meaning` dịch đúng và đủ câu `question.ja` (thì, thể, cấu trúc ngữ pháp, từ ngoại lai, không thêm/bớt/thu hẹp ý); đúng 1 cặp `{ }` bọc phần dịch của từ đang hỏi (D7); mức lịch sự theo câu tiếng Nhật.
- [ ] **(JA)** Các mẫu có **cùng câu tiếng Nhật** (khác từ gạch chân) dùng cùng một bản dịch câu, chỉ khác vị trí `{ }` (D4 báo khi lệch).
- [ ] Nghĩa từ (JA) và tham khảo / phân tích (VI) không mâu thuẫn; mâu thuẫn → `loi_json_vi`.
- [ ] Mỗi `options[i].analysis` nói đúng về `option_ja` của nó; với mẫu "cách đọc của từ X (nghĩa)", nghĩa tiếng Hàn đúng với từ X.
- [ ] Thuật ngữ đúng bảng thuật ngữ, nhất quán trong toàn lời giải.
- [ ] Giữ nguyên `⟪ ⟫` (trợ từ viết liền sau `⟫`), `{ }`, `｜…《…》`, xuống dòng, loại dấu ngoặc.
- [ ] Văn phong -습니다 ở `analysis` và `reference`; tiếng Hàn tự nhiên.

## Mẫu file lý do

```json
{
  "sua": [{"duong_dan": "$.word.meaning", "loai": "khach_quan", "muc_do": "nang",
           "ly_do": "Nghĩa trong câu là 'tuyển mộ', GPT dịch nghĩa 'gia tăng'"}],
  "ghi_chu_ban_goc": [], "ghi_chu_khi_dich": [], "loi_json_vi": []
}
```
