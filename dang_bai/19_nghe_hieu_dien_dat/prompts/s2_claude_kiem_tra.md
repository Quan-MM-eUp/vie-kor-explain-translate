# Hướng dẫn Claude – Bước 2.4: kiểm tra bản dịch tiếng Hàn và sửa lỗi (dạng 19 – Nghe hiểu diễn đạt) · v1

> Phiên bản 2026-10-08. Model: **Claude Opus 5.5** trong Cowork. Bản dịch cần kiểm tra do **tác tử TẠO (Claude A)** dịch – "bản GPT" trong tên trường / công cụ hiểu là bản của tác tử TẠO.
> Cột "Dịch từ" trong bảng xem nhanh: **JA** = nghĩa câu tình huống (`prompt.utterance.meaning`), nghĩa câu nói (`options[i].sentence.meaning`) – dịch thẳng từ câu tiếng Nhật; **VI** = phân tích (`options[i].analysis`) – theo tiếng Việt.

**Nhiệm vụ:** kiểm tra bản dịch **có đúng với ngữ cảnh không** và sửa lỗi. Ngữ cảnh: câu tình huống, 3 câu nói, đáp án, tiếng Việt của cả lời giải.

## Làm gì

Danh sách: `output/claude/gd2_danh_sach.json` (tạo bằng `python3 scripts/s2_claude_goi.py …`). Xem bảng: `python3 ../../pipeline_chung/cong_cu/xem_gd2.py <id> …`.

1. Sửa trực tiếp **chỉ giá trị `ko`** trong `output/json_ko/checked/<id>.json`. Không sửa `vi`, `ja`, cấu trúc.
2. Ghi kết quả bằng file đặc tả lô + `ghi_ly_do.py` (`"giai_doan": "2"`, liệt kê **mọi** câu – xem `SO_TAY_CHAY.md`). Không có gì sửa thì để `{}`.
3. Phát hiện **chính JSON tiếng Việt sai** hoặc mâu thuẫn nội bộ (nghĩa câu nói bám tiếng Nhật mâu thuẫn với phân tích bám tiếng Việt): không sửa theo ý mình, ghi `[Lỗi JSON VI] <phần>: <vấn đề>` vào `loi_json_vi` → câu quay lại GĐ1.

## Phạm vi sửa

- `loai` hợp lệ: `sai_so_ban_goc`, `chinh_ta` (gồm **trợ từ sai theo âm cuối**), `khach_quan`, `chu_quan`.
- Không thêm nội dung. Phần dịch từ tiếng Việt: tiếng Việt sai thì không sửa theo ý mình → ghi `[Bản gốc VI]`.
- Phần bám tiếng Nhật: sửa theo **tiếng Nhật** – khác bản Việt là bình thường.

## Checklist theo ngữ cảnh

- [ ] **(JA) Câu tình huống**: đúng nghĩa (ai, làm gì, với ai); `何と言いますか` → `뭐라고 말합니까?`.
- [ ] **(JA) Câu nói**: đúng nghĩa + **mức lịch sự / sắc thái** (존댓말 / 반말, -시-, 드리다), **ai làm cho ai** (あげる / くれる / もらう), xin phép / đề nghị / nhờ / rủ; lời chào cố định dùng câu tương đương tiếng Hàn (bảng câu nói cố định); câu nói SAI vẫn dịch đúng như câu đang viết (không "sửa" cho lịch sự hơn).
- [ ] Mức lịch sự trong bản Hàn **khớp với phân tích** (phân tích nói "không đủ lịch sự" thì câu Hàn tương ứng cũng không được lịch sự hóa).
- [ ] **(VI) Phân tích**: kết luận và lý do giữ đúng như tiếng Việt; nghĩa câu nói trích lại khớp bản dịch câu nói; thuật ngữ (경어, 존경어, 겸양어, 정중체, 반말…).
- [ ] **Trợ từ sau `⟪ ⟫`** theo âm cuối cách đọc tiếng Nhật (D12).
- [ ] Văn phong -습니다 ở phân tích; giữ `⟪ ⟫`, 「」, `{ }`, `\n`.
- [ ] Cùng câu Nhật → cùng bản Hàn (D15 trong câu; D4 giữa các câu – `output/reports/khong_nhat_quan.csv`): theo bản đã duyệt trước.

## Mẫu một câu trong file đặc tả lô (GĐ2)

```json
"21479_1": {"thay": [{"duong_dan": "$.options[1].sentence.meaning.ko", "cu": "…", "moi": "…"}],
            "sua": [{"duong_dan": "$.options[1].sentence.meaning", "loai": "khach_quan", "muc_do": "nhe",
                     "ly_do": "(JA) てあげませんか: người nói đề nghị làm cho người khác – không phải nhờ"}]}
```
