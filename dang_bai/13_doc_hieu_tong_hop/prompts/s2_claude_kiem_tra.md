# Hướng dẫn Claude – Bước 2.4: kiểm tra bản dịch tiếng Hàn và sửa lỗi (dạng 13 – Đọc hiểu tổng hợp) · v1

> Phiên bản `s2_claude_kiem_tra.13.v1` (2026-10-08). Model: **Claude Opus 5.5** trong Cowork. Bản dịch do **tác tử TẠO (Claude A)** làm – "bản GPT" trong các công cụ / báo cáo hiểu là bản của tác tử TẠO.

> Cột "Dịch từ" trong bảng xem nhanh: **JA** = nghĩa câu hỏi (`question.meaning`), nghĩa lựa chọn (`options[i].meaning`), nghĩa câu trích (`options[i].quotes[j].meaning`) – dịch thẳng từ câu tiếng Nhật; **VI** = nhận xét (`options[i].analysis`), bản dịch đoạn văn (`full_translation`).

**Nhiệm vụ:** kiểm tra bản dịch **có đúng với ngữ cảnh không** và sửa lỗi. Ngữ cảnh: đoạn văn A / B, câu hỏi, lựa chọn, đáp án, phần tiếng Nhật trong JSON và tiếng Việt của cả lời giải.

## Làm gì

Danh sách: `output/claude/gd2_danh_sach.json`. Mỗi câu có bảng xem nhanh `output/claude/gd2/<id>.md` (xem gọn: `python3 ../../pipeline_chung/cong_cu/xem_gd2.py <id> …`). **Soát theo đoạn văn** – các câu con cùng đoạn xem liền nhau.

1. Sửa **chỉ giá trị `ko`** trong `output/json_ko/checked/<id>.json` (hoặc qua file đặc tả lô + `ghi_ly_do.py`). Không sửa `vi`, `ja`, cấu trúc.
2. Ghi `output/json_ko/checked/<id>.ly_do.json` – xong thì xóa khóa `_huong_dan`. Không có gì sửa thì `"sua": []`.
3. Câu cố định (nguồn `cau_co_dinh`): không sửa; thấy chưa hay → `[Khi dịch] Đề nghị sửa câu cố định: …` vào `ghi_chu_khi_dich`.
4. Phát hiện **JSON tiếng Việt sai** (vd nhận xét bám tiếng Việt mâu thuẫn với nghĩa câu trích dịch từ tiếng Nhật, lời giải gán nhầm A/B mà GĐ1 sót): ghi `[Lỗi JSON VI] <phần>: <vấn đề>` vào `loi_json_vi` → câu quay lại GĐ1.
5. Xong cả danh sách thì chạy `python3 scripts/s2_kiem_tra.py …` và báo kết quả.

## Phạm vi sửa

- `loai`: `sai_so_ban_goc`, `chinh_ta` (gồm trợ từ sai theo âm cuối), `khach_quan`, `chu_quan`.
- Không thêm nội dung. Phần dịch từ tiếng Việt sai vì chính tiếng Việt sai → không sửa theo ý mình, ghi `[Bản gốc VI]` / `loi_json_vi`.
- Phần bám tiếng Nhật: sửa theo **tiếng Nhật** – khác bản Việt là bình thường.

## Checklist theo ngữ cảnh

- [ ] **(JA)** nghĩa câu hỏi: đúng cách ra đề tiếng Hàn; giữ ①②, A / B.
- [ ] **(JA)** nghĩa 4 lựa chọn: đúng chủ thể A / B / cả hai, phủ định, so sánh, mức độ; lựa chọn sai vẫn dịch đúng như câu đang viết.
- [ ] **(JA)** nghĩa câu trích: sát câu Nhật, đúng mạch đoạn văn; **câu trích giống nhau dịch giống hệt** trong cùng câu (D15 cảnh báo) và giữa các câu con cùng đoạn (D4 – `output/reports/khong_nhat_quan.csv`).
- [ ] **(VI)** nhận xét: kết luận và lý do giữ đúng như tiếng Việt (ai nói gì – A hay B – không được đảo); câu dẫn "Đoạn A có câu:" dịch thống nhất; -습니다.
- [ ] **Trợ từ sau `⟪ ⟫`** theo âm cuối cách đọc tiếng Nhật (D12 cảnh báo – kiểm cả bản tạo trước khi sửa).
- [ ] Giữ nguyên `⟪ ⟫`, `{ }`, `｜…《…》`, xuống dòng, gạch đầu dòng, loại dấu nháy; tác tử TẠO gộp / tách câu làm **mất khối `⟪ ⟫`** → tách lại cho đủ.
- [ ] Không còn chữ Việt, không có tiếng Nhật ngoài ⟪ ⟫ (trừ trường dịch từ tiếng Nhật không có ⟪ ⟫).

## Mẫu file lý do

```json
{
  "sua": [{"duong_dan": "$.options[1].quotes[0].meaning", "loai": "khach_quan", "muc_do": "nhe",
           "ly_do": "(JA) Thống nhất với bản dịch cùng câu trích ở lựa chọn 4"}],
  "ghi_chu_ban_goc": [], "ghi_chu_khi_dich": [], "loi_json_vi": []
}
```
