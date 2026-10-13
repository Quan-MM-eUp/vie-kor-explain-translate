# Hướng dẫn Claude – Bước 2.4: kiểm tra bản dịch tiếng Hàn và sửa lỗi (dạng 16 – Nghe hiểu chủ đề) · v1

> Phiên bản `s2_claude_kiem_tra.16.v1` (2026-10-08). Model: **Claude Opus 5.5** trong Claude Cowork (không qua API).
> Bản dịch cần kiểm tra do **tác tử TẠO (Claude A)** dịch – "bản GPT" trong công cụ / nhật ký hiểu là bản tác tử TẠO.
> Cột "Dịch từ" trong bảng xem nhanh: **JA** = dòng lời thoại, câu hỏi, câu trích, nghĩa lựa chọn chữ – dịch thẳng từ tiếng Nhật (cột cuối là bản Việt chỉ để đối chiếu); **VI** = phân tích, phân tích chung, dòng lời thoại không có tiếng Nhật.

**Nhiệm vụ:** kiểm tra bản dịch **có đúng với ngữ cảnh không** và sửa lỗi. Ngữ cảnh: lời thoại tiếng Nhật, đề, đáp án, tiếng Việt của cả lời giải.

## Làm gì

Danh sách: `output/claude/gd2_danh_sach.json` (tạo bằng `python3 scripts/s2_claude_goi.py …`). Mỗi câu có bảng xem nhanh `output/claude/gd2/<id>.md` (`python3 ../../pipeline_chung/cong_cu/xem_gd2.py <id>` in gọn Mã | Nguồn | Tiếng Hàn).

1. Sửa **chỉ giá trị `ko`** trong `output/json_ko/checked/<id>.json` (qua file đặc tả lô `"giai_doan": "2"` + `ghi_ly_do.py`). Không sửa `vi`, `ja`, cấu trúc.
2. Ghi lý do (sua / ghi_chu_khi_dich / loi_json_vi), xóa `_huong_dan`. Không có gì sửa thì `"sua": []`.
3. Thấy **chính JSON tiếng Việt sai** (bản dịch Việt của lời thoại / câu trích sai nghĩa mà GĐ1 bỏ sót, phân tích mâu thuẫn lời thoại): không sửa theo ý mình, ghi `[Lỗi JSON VI] <phần>: <vấn đề>` vào `loi_json_vi` → câu quay lại GĐ1.
4. Xong lô: `python3 scripts/s2_kiem_tra.py …` và báo kết quả.

## Phạm vi sửa

- `loai` hợp lệ: `sai_so_ban_goc`, `chinh_ta` (gồm trợ từ sai theo âm cuối), `khach_quan`, `chu_quan`.
- Phần JA sửa theo **tiếng Nhật** – khác bản Việt là bình thường. Phần VI: không sửa theo ý mình khi tiếng Việt sai → `[Bản gốc VI]`.

## Checklist theo ngữ cảnh

- [ ] **(JA) Lời thoại**: đúng nghĩa từng dòng (chủ thể, phủ định, bị động / sai khiến, thì, số liệu, giờ, giá); văn nói tự nhiên, **mức lịch sự / quan hệ đúng câu Nhật** (반말 ↔ 존댓말 không lẫn giữa các lượt của cùng một người); tên riêng, đại từ nhất quán cả bài; giữ `(i)` (D16), `{ }` đúng số cặp (D7); dòng dẫn tình huống văn viết trung tính.
- [ ] **(JA) Câu hỏi / câu trích**: trùng dòng lời thoại → giống hệt bản dịch dòng đó (D15 cảnh báo); câu trích một phần dòng → khớp phần tương ứng.
- [ ] **(JA) Nghĩa lựa chọn**: cụm ngắn đúng câu Nhật; khớp cách phân tích nhắc lại lựa chọn đó.
- [ ] **(VI) Phân tích**: đúng ý tiếng Việt, -습니다; câu trích trong phân tích (`「⟪…⟫」(…)`) dịch phần ngoặc khớp bản dịch dòng lời thoại; kết luận đúng / sai giữ đúng; tên người nói nhất quán với lời thoại (남자 / 여자 …).
- [ ] **Trợ từ sau `⟪ ⟫`** theo âm cuối cách đọc **tiếng Nhật** – Python cảnh báo D12.
- [ ] Giữ nguyên `⟪ ⟫`, `{ }`, `｜…《…》`, xuống dòng, chữ Latin.

## Mẫu file lý do

```json
{"sua": [{"duong_dan": "$.full_translation[0].lines[3].meaning", "loai": "khach_quan", "muc_do": "nhe",
          "ly_do": "(JA) Người phụ nữ nói với cấp trên bằng です/ます – đổi 반말 sang -요"}],
 "ghi_chu_ban_goc": [], "ghi_chu_khi_dich": [], "loi_json_vi": []}
```
