# Hướng dẫn tác tử KIỂM TRA – Bước 2.4: kiểm tra bản dịch tiếng Hàn (dạng 21 – Nghe hiểu tổng hợp) · v1

> Phiên bản 2026-10-08. Bản dịch do **tác tử TẠO (Claude A)** dịch – "bản GPT" trong báo cáo hiểu là bản của tác tử TẠO. **THAM KHẢO** không dịch.
> Cột "Dịch từ" trong bảng `output/claude/gd2/<id>.md`: **JA** = lượt thoại, câu then chốt, câu hỏi, lựa chọn, câu trích (dịch thẳng từ tiếng Nhật); **VI** = nhận xét (analysis).

## Làm gì

1. Danh sách `output/claude/gd2_danh_sach.json`; xem bảng gọn `python3 ../../pipeline_chung/cong_cu/xem_gd2.py <id> …` (cột Mã | Bản nguồn | Tiếng Hàn); lời thoại JA đầy đủ ở dòng đầu file `output/claude/gd2/<id>.md`.
2. Sửa **chỉ giá trị `ko`** trong `output/json_ko/checked/<id>.json` (không sửa `vi`, `ja`, cấu trúc). Ghi lý do bằng file đặc tả lô `gd2_X_Y.json` + `ghi_ly_do.py`.
3. JSON tiếng Việt sai / mâu thuẫn → `loi_json_vi`: `[Lỗi JSON VI] <phần>: <vấn đề>` → câu quay lại GĐ1.
4. **Câu con 2** của bài 2 câu hỏi: lời thoại là bản của câu con 1 – sửa lời thoại ở **câu con 1**; `s2_kiem_tra` tự đồng bộ (D16).
5. Xong chạy `python3 scripts/s2_kiem_tra.py …`.

`loai` hợp lệ: `sai_so_ban_goc`, `chinh_ta` (gồm trợ từ sai theo âm cuối), `khach_quan`, `chu_quan`.

## Checklist

- [ ] **(JA) Lượt thoại**: đúng nghĩa câu Nhật (chủ thể, phủ định, thời gian, số, giá, đổi ý やっぱり / じゃあ), văn nói tự nhiên, mức lịch sự đúng quan hệ (bạn bè / vợ chồng 반말; khách – nhân viên 존댓말), giữ `(i)` / `(ii)` (D17 LỖI nếu mất), không thêm nhãn người nói.
- [ ] **(JA) Câu trích / câu then chốt** trùng lượt thoại → giống hệt bản dịch lượt thoại (D15).
- [ ] **(JA) Câu hỏi** dạng câu hỏi đề thi; **lựa chọn** ngắn gọn, bám chữ Nhật, 4 lựa chọn song song về cấu trúc.
- [ ] **(VI) Nhận xét**: đủ ý tiếng Việt, kết luận / lý do giữ nguyên, -습니다, thuật ngữ đúng bảng, tên người nói (남자 / 여자 / 점원…) nhất quán với lời thoại.
- [ ] Trợ từ sau `⟪ ⟫` theo âm cuối cách đọc tiếng Nhật (D12 cảnh báo – kiểm tra cả bản tác tử TẠO).
- [ ] Giữ nguyên `⟪ ⟫`, `{ }`, `｜…《…》`, xuống dòng, loại dấu nháy; không còn chữ Việt / tiếng Nhật ngoài ⟪ ⟫ trong phần nhận xét.

## Mẫu file lý do (qua đặc tả lô)

```json
{"giai_doan": "2", "cau": {"12309_1": {"sua": [{"duong_dan": "$.full_translation[0].lines[6].meaning.ko", "loai": "khach_quan", "muc_do": "nhe",
  "ly_do": "(JA) 女：じゃあ、寒いのを我慢するしかないか – bạn bè nói chuyện → 반말: '그럼 추운 건 참을 수밖에 없나…'"}],
  "ghi_chu_ban_goc": [], "ghi_chu_khi_dich": [], "loi_json_vi": []}}}
```
