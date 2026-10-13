# Hướng dẫn Claude – Bước 2.4: kiểm tra bản dịch tiếng Hàn và sửa lỗi (dạng 14 – Đọc hiểu chủ đề / quan điểm) · v1

> Phiên bản `s2_claude_kiem_tra.14.v1` (2026-10-08). Model: **Claude Opus 5.5** trong Cowork. Bản dịch do **tác tử TẠO (Claude A)** dịch – "bản GPT" trong các file chung hiểu là bản của tác tử TẠO.
> Cột "Dịch từ" trong bảng xem nhanh `output/claude/gd2/<id>.md`: **JA** = nghĩa câu hỏi (`question.meaning`), nghĩa lựa chọn (`options[i].meaning`), nghĩa câu trích (`options[i].quotes[j].meaning`) – dịch thẳng từ tiếng Nhật; **VI** = giải thích (`analysis`), bản dịch đoạn văn (`full_translation`).

**Nhiệm vụ:** kiểm tra bản dịch có đúng với ngữ cảnh không và sửa lỗi. Ngữ cảnh: đoạn văn, câu hỏi, lựa chọn, đáp án, phần tiếng Nhật trong JSON và tiếng Việt của cả lời giải.

## Làm gì

Danh sách: `output/claude/gd2_danh_sach.json` (`python3 scripts/s2_claude_goi.py …`). Xem nhanh: `python3 ../../pipeline_chung/cong_cu/xem_gd2.py <id> …`.

1. Sửa trực tiếp **chỉ giá trị `ko`** trong `output/json_ko/checked/<id>.json` (qua file đặc tả lô `"thay"`). Không sửa `vi`, `ja`, cấu trúc.
2. Ghi kết quả bằng file đặc tả lô `gd2_X_Y.json` + `ghi_ly_do.py` (liệt kê **mọi** câu GĐ2 của lô).
3. Câu cố định (nguồn `cau_co_dinh`): không sửa; thấy chưa hay → `[Khi dịch] Đề nghị sửa câu cố định: …` vào `ghi_chu_khi_dich`.
4. Phát hiện **JSON tiếng Việt sai** hoặc mâu thuẫn (vd nghĩa câu trích bám tiếng Nhật mâu thuẫn với cách giải thích hiểu câu đó): không sửa theo ý mình, ghi `[Lỗi JSON VI] <phần>: <vấn đề>` vào `loi_json_vi` → câu quay lại GĐ1.
5. Chạy `python3 scripts/s2_kiem_tra.py …` và báo kết quả.

## Phạm vi sửa

- `loai`: `sai_so_ban_goc`, `chinh_ta` (gồm trợ từ sai theo âm cuối), `khach_quan`, `chu_quan`.
- Không thêm nội dung. Phần dịch từ tiếng Việt: không sửa theo ý mình khi tiếng Việt sai → `[Bản gốc VI]`.
- Phần bám tiếng Nhật: sửa theo **tiếng Nhật** – khác bản Việt là bình thường.

## Checklist

- [ ] **Đoạn văn không dịch.** Các câu con cùng đoạn văn: **cùng câu trích dịch giống hệt** (D15 trong một câu, D4 giữa các câu – `output/reports/khong_nhat_quan.csv`); tên riêng / thuật ngữ thống nhất.
- [ ] **(JA) nghĩa câu hỏi**: cách ra đề JLPT tiếng Hàn (`…라고 했는데, 어떤 의미인가?`, `필자의 생각과 일치하는 것은 무엇인가?`), giữ mốc ①② (D13), cụm được hỏi trong nháy `'…'`.
- [ ] **(JA) nghĩa lựa chọn**: sát câu Nhật – chủ thể, phủ định, mức khẳng định (〜とは限らない, 〜べきだ, 〜にすぎない), bị động / sai khiến; lựa chọn sai vẫn dịch đúng như câu đang viết.
- [ ] **(JA) nghĩa câu trích**: sát câu đoạn văn, văn viết -다; `{ }` đúng số cặp (D7).
- [ ] **(VI) giải thích**: đủ ý tiếng Việt, kết luận ĐÚNG/SAI giữ nguyên; '필자', '본문'; văn phong -습니다; câu trích nằm trong giải thích: phần dịch trong ngoặc khớp bản dịch câu trích ở `quotes`.
- [ ] **(VI) bản dịch đoạn văn** (nếu có): văn viết -다, đủ ý, giữ chia đoạn.
- [ ] **Trợ từ sau `⟪ ⟫`** theo âm cuối cách đọc tiếng Nhật (D12).
- [ ] Giữ nguyên `⟪ ⟫`, `{ }`, `｜…《…》`, xuống dòng, loại dấu nháy.

## Mẫu file lý do

```json
{
  "sua": [{"duong_dan": "$.options[2].quotes[0].meaning", "loai": "khach_quan", "muc_do": "nhe",
           "ly_do": "(JA) Thống nhất với bản dịch cùng câu trích ở options[0].quotes[0] / 12709_2"}],
  "ghi_chu_ban_goc": [], "ghi_chu_khi_dich": [], "loi_json_vi": []
}
```
