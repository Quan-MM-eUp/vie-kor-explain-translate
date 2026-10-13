# Hướng dẫn tác tử KIỂM TRA – Bước 2.4: kiểm tra bản dịch tiếng Hàn và sửa lỗi (dạng 15 – Đọc hiểu: Tìm thông tin) · v1

> Phiên bản `s2_claude_kiem_tra.15.v1` (2026-10-08). Model: **Claude Opus 5.5** trong Cowork. Bản dịch do **tác tử TẠO (Claude A)** làm – "bản GPT" trong công cụ hiểu là bản của tác tử TẠO.
> Cột "Dịch từ" trong bảng xem nhanh (`output/claude/gd2/<id>.md`, xem gọn bằng `xem_gd2.py`): **JA** = nghĩa câu hỏi / lựa chọn / câu trích – dịch thẳng từ tiếng Nhật (bản Việt ở cột cuối chỉ để đối chiếu); **VI** = phân tích, tóm tắt, bản dịch ngữ liệu – dịch từ tiếng Việt.

**Nhiệm vụ:** kiểm tra bản dịch **có đúng với ngữ cảnh không** (ngữ liệu, câu hỏi, lựa chọn, đáp án, tiếng Nhật, tiếng Việt của cả lời giải) và sửa lỗi.

## Làm gì

1. Sửa trực tiếp **chỉ giá trị `ko`** trong `output/json_ko/checked/<id>.json`. Không sửa `vi`, `ja`, cấu trúc. File phải là JSON hợp lệ.
2. Ghi kết quả cả lô bằng file đặc tả `gd2_X_Y.json` + `ghi_ly_do.py` (SO_TAY_CHAY.md mục 4.3), liệt kê **mọi** câu.
3. **Câu cố định** (nguồn `cau_co_dinh`): không sửa; thấy chưa hay → `[Khi dịch] Đề nghị sửa câu cố định: …` vào `ghi_chu_khi_dich`.
4. Phát hiện **chính JSON tiếng Việt sai** (phép tính, trích dẫn, phân tích…) hoặc mâu thuẫn nội bộ: không sửa theo ý mình, ghi `[Lỗi JSON VI] <phần>: <vấn đề>` vào `loi_json_vi` → câu quay lại GĐ1.
5. Xong cả lô thì chạy `python3 scripts/s2_kiem_tra.py …` và báo kết quả.

## Phạm vi sửa

- `loai` hợp lệ: `sai_so_ban_goc`, `chinh_ta` (gồm **trợ từ sai theo âm cuối**), `khach_quan`, `chu_quan`.
- Không thêm nội dung. Phần dịch từ tiếng Việt: không sửa theo ý mình khi tiếng Việt sai → ghi `[Lỗi JSON VI]`.
- Phần dịch từ tiếng Nhật: sửa theo **tiếng Nhật** – khác bản Việt là bình thường.

## Checklist theo ngữ cảnh

- [ ] **Số**: mọi con số, giờ, ngày, giá, phần trăm, phép tính giữ đúng (cảnh báo **D-SO**); đơn vị tiếng Hàn đúng (엔, 월/일, 요일, 시/분, 만 엔).
- [ ] **(JA)** nghĩa câu hỏi đúng chủ thể / điều kiện; nghĩa lựa chọn dịch sát (lựa chọn sai vẫn dịch như đang viết); nghĩa câu trích sát ngữ liệu.
- [ ] Câu trích giống nhau (giữa lựa chọn / câu con cùng ngữ liệu) dịch giống hệt – xem bảng của cả nhóm (**D4** → `output/reports/khong_nhat_quan.csv`).
- [ ] **(VI)** phân tích: kết luận và lý do giữ đúng như tiếng Việt, phép tính giữ nguyên; tên mục / thuật ngữ theo bảng thuật ngữ (본문, 지문, 선택지, 요금, 할인, 신청, 마감…).
- [ ] **Trợ từ sau `⟪ ⟫`** theo âm cuối cách đọc tiếng Nhật – cảnh báo **D12**.
- [ ] Văn phong -습니다 ở phần phân tích; tiếng Hàn tự nhiên; giữ `⟪ ⟫`, `{ }`, `｜…《…》`, `\n`, gạch đầu dòng.
- [ ] Ngữ liệu không dịch.

## Mẫu file lý do

```json
{
  "sua": [{"duong_dan": "$.options[1].quotes[0].meaning", "loai": "khach_quan", "muc_do": "nang",
           "ly_do": "(JA) Bản dịch mất giờ '18：30～20：30' của câu trích"}],
  "ghi_chu_ban_goc": [], "ghi_chu_khi_dich": [], "loi_json_vi": []
}
```
