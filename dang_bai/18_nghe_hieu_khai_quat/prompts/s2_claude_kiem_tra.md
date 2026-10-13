# Hướng dẫn Claude – Bước 2.4: kiểm tra bản dịch tiếng Hàn và sửa lỗi (dạng 18 – Nghe hiểu khái quát) · v1

> Phiên bản `s2_claude_kiem_tra.18.v1` (2026-10-08). Model: **Claude Opus 5.5**, chạy trong Claude Cowork (không qua API).
> Bản dịch cần kiểm tra do **tác tử TẠO (Claude A)** dịch – "bản GPT" trong nhật ký / cảnh báo Python hiểu là bản của tác tử TẠO.
> Cột "Dịch từ" trong bảng xem nhanh `output/claude/gd2/<id>.md`: **JA** = dòng lời thoại, câu hỏi, nghĩa lựa chọn, nghĩa câu trích – dịch thẳng từ tiếng Nhật (cột cuối là bản Việt để đối chiếu); **VI** = nhận xét phân tích (`analysis`).

**Nhiệm vụ:** kiểm tra bản dịch **có đúng với ngữ cảnh không** (lời thoại, câu hỏi, lựa chọn, đáp án, tiếng Việt của lời giải) và sửa lỗi.

## Làm gì

Danh sách: `output/claude/gd2_danh_sach.json` (tạo bằng `python3 scripts/s2_claude_goi.py …`). Xem nhanh: `python3 ../../pipeline_chung/cong_cu/xem_gd2.py <id>`.
1. Sửa trực tiếp **chỉ giá trị `ko`** trong `output/json_ko/checked/<id>.json` (không sửa `vi`, `ja`, `speaker`, cấu trúc). JSON hợp lệ.
2. Ghi kết quả bằng file đặc tả lô `output/claude/ly_do_lo/gd2_X_Y.json` (`"giai_doan": "2"`, liệt kê **mọi** câu) → `python3 ../../pipeline_chung/cong_cu/ghi_ly_do.py …`. Không có gì sửa thì để `{}`.
3. **Câu cố định** (nguồn `cau_co_dinh`): không sửa; thấy chưa hay → `[Khi dịch] Đề nghị sửa câu cố định: …` vào `ghi_chu_khi_dich`.
4. Phát hiện **JSON tiếng Việt sai** hoặc **mâu thuẫn** (nhận xét bám tiếng Việt mâu thuẫn với lời thoại bám tiếng Nhật): không sửa theo ý mình, ghi `[Lỗi JSON VI] <phần>: <vấn đề>` vào `loi_json_vi` → câu quay lại GĐ1.
5. Làm xong cả lô thì chạy `python3 scripts/s2_kiem_tra.py …` và báo kết quả.

## Phạm vi sửa

- `loai`: `sai_so_ban_goc`, `chinh_ta` (gồm **trợ từ sai theo âm cuối**), `khach_quan`, `chu_quan`. Không thêm nội dung.
- Phần bám tiếng Nhật: sửa theo **tiếng Nhật** – khác bản Việt là bình thường. Phần `analysis`: bám tiếng Việt; tiếng Việt sai → ghi `[Bản gốc VI]`, không tự sửa.

## Checklist theo ngữ cảnh

- [ ] **(JA) Lời thoại:** từng dòng đúng nghĩa câu Nhật (thì, phủ định, bị động, sai khiến, điều kiện, chủ thể); **sắc thái nói** đúng quan hệ người nói (bạn bè / gia đình → 반말; です・ます → 해요체; nhân viên ↔ khách, thông báo, tin nhắn công việc → 하십시오체 / 해요체 lịch sự), cùng người nói cùng mức; dòng dẫn theo văn sách JLPT (`…이야기하고 있습니다.`); tên người phiên âm chuẩn; không thêm nhãn người nói; giữ `(i)`.
- [ ] **(JA) Câu hỏi:** văn phong đề thi (`…습니까?`), đúng nghĩa câu Nhật.
- [ ] **(JA) Lựa chọn:** dịch sát, giữ hình thức cụm / câu; từ then chốt đúng (vì lựa chọn quyết định đáp án).
- [ ] **(JA) Câu trích:** giống hệt bản dịch dòng lời thoại tương ứng (Python **D15**); cùng câu trích ở nhiều lựa chọn dịch giống nhau (**D16**).
- [ ] **(VI) analysis:** đủ ý, đúng kết luận / lý do như tiếng Việt; nghĩa câu thoại / lựa chọn nhắc lại dùng đúng bản dịch đã chọn; văn phong -습니다; giữ nguyên `⟪ ⟫`, `｜…《…》`, `\n`, loại dấu nháy.
- [ ] **Trợ từ sau `⟪ ⟫`** theo âm cuối cách đọc tiếng Nhật (ん → 과/은/을/이/이라는/이라고/이며/으로; nguyên âm → 와/는/를/가/라는/라고/며/로) – Python cảnh báo **D12**.
- [ ] Bản tác tử TẠO gộp / tách câu làm **mất một khối `⟪ ⟫`** → tách lại cho đủ (Python báo "nội dung ⟪ ⟫ khác bản tiếng Việt").

## Mẫu đặc tả lô (GĐ2)

```json
{"giai_doan": "2",
 "cau": {
  "12136_1": {"thay": [{"duong_dan": "$.full_translation[0].lines[2].meaning.ko", "cu": "아뇨, 무슨 일 있어요?", "moi": "아니, 무슨 일 있어?"}],
              "sua": [{"duong_dan": "$.full_translation[0].lines[2].meaning.ko", "loai": "khach_quan", "muc_do": "nhe",
                       "ly_do": "(JA) L3 vợ chồng nói thể thường (いや、どうかしたの？) → 반말, thống nhất với các dòng khác của 男"}]},
  "17747_1": {}
 }}
```
