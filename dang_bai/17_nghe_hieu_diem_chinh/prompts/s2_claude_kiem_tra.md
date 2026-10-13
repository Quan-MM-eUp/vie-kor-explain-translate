# Hướng dẫn tác tử KIỂM TRA – Bước 2.4: kiểm tra bản dịch tiếng Hàn và sửa lỗi (dạng 17 – Nghe hiểu điểm chính) · v1

> Model: **Claude Opus 5.5** trong Cowork. Bản dịch do **tác tử TẠO (Claude A)** làm – "bản GPT" trong công cụ chung hiểu là bản của tác tử TẠO.

**Nhiệm vụ:** bản Hàn phải đúng với **câu tiếng Nhật** (lời thoại, câu hỏi, lựa chọn, Thông tin) và với **tiếng Việt** (lý do); sửa lỗi.

## Làm gì

- Danh sách: `output/claude/gd2_danh_sach.json`; xem nhanh: `python3 ../../pipeline_chung/cong_cu/xem_gd2.py --lo X Y` (cột Bản nguồn: `JA: người nói: câu Nhật ‖ VI: bản Việt`; `CHÉP fM` = Python chép).
- Sửa **chỉ giá trị `ko`** trong `output/json_ko/checked/<id>.json` (qua `thay` của file đặc tả lô). Mã `CHÉP` không sửa trực tiếp – sửa dòng thoại nguồn rồi sửa giống hệt ở key_info (D-KI).
- Ghi file đặc tả lô `gd2_X_Y.json` (`"giai_doan": "2"`, liệt kê **mọi** câu) → `ghi_ly_do.py` → `python3 scripts/s2_kiem_tra.py --tu X --den Y`.
- Phát hiện JSON tiếng Việt sai (vd ghép lệch dòng còn sót) → không sửa theo ý mình, ghi `[Lỗi JSON VI] <phần>: <vấn đề>` vào `loi_json_vi` → câu quay lại GĐ1.

## Checklist

- [ ] **(JA)** lời thoại: đúng nghĩa câu Nhật, nhất là số / ngày / giờ / phủ định / điều kiện / thứ tự hành động / ai làm gì; mức kính ngữ theo câu Nhật (です/ます → 존댓말, thể thường → 반말, いたします/おります → 겸양); giữ `(i)` (D-I); tên người phiên âm theo cách đọc Nhật, thống nhất trong bài.
- [ ] **(JA)** câu hỏi -ㅂ니까, giống hệt bản dịch câu hỏi lặp lại trong lời thoại; dòng dẫn văn viết.
- [ ] **(JA)** lựa chọn ngắn gọn, đúng hình thức; khớp cách nói trong lời thoại.
- [ ] **(JA)** Thông tin = bản dịch dòng thoại tương ứng (mã CHÉP – D-KI).
- [ ] **(VI)** lý do: đúng ý tiếng Việt, -습니다, giữ `⟪ ⟫`, trợ từ sau `⟫` theo âm cuối cách đọc tiếng Nhật.
- [ ] Không còn chữ Việt / chữ Nhật ngoài `⟪ ⟫` trong bản Hàn; D-SO (số thiếu) → kiểm tra.

`loai` hợp lệ: `sai_so_ban_goc`, `chinh_ta`, `khach_quan`, `chu_quan`.

## Mẫu file lý do

```json
{"sua": [{"duong_dan": "$.full_translation[0].lines[6].meaning.ko", "loai": "khach_quan", "muc_do": "nang",
          "ly_do": "(JA) '２時間までなんです' – bản Hàn mất ý 'tối đa': '2시간까지입니다'"}],
 "ghi_chu_ban_goc": [], "ghi_chu_khi_dich": [], "loi_json_vi": []}
```
