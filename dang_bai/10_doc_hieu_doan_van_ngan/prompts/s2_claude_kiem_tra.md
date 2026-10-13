# Hướng dẫn tác tử KIỂM TRA – Bước 2.4: soát bản dịch tiếng Hàn (dạng 10 – Đọc hiểu đoạn văn ngắn) · v1

> Phiên bản `s2_claude_kiem_tra.10.v1` (2026-10-08). Model: **Claude Opus 5.5** trong Cowork. Bản dịch do **tác tử TẠO (Claude A)** dịch.
> `reference_raw` không dịch, không soát.

**Nhiệm vụ:** kiểm tra bản dịch **đúng với ngữ cảnh** (đoạn văn tiếng Nhật, câu hỏi, 4 lựa chọn, đáp án, tiếng Nhật trong JSON, tiếng Việt của lời giải) và sửa lỗi.

Cột "Dịch từ" trong bảng `output/claude/gd2/<id>.md` (xem gọn: `python3 ../../pipeline_chung/cong_cu/xem_gd2.py --lo X Y`; đoạn văn tiếng Nhật: `xem_gd1.py <id>`):
- **VI + JA** = nghĩa câu hỏi (`question.meaning`), nghĩa lựa chọn (`options[i].meaning`), bản dịch trích dẫn (`options[i].quotes[j].meaning`) – nghĩa theo tiếng Nhật;
- **VI** = phân tích (`analysis`), phân tích chung (`summary`), bản dịch đoạn văn khuôn B (`full_translation`).

## Làm gì

1. Sửa **chỉ giá trị `ko`** trong `output/json_ko/checked/<id>.json` – qua file đặc tả lô (`"giai_doan": "2"`, `thay` với đường dẫn tới chuỗi `….ko`) rồi `ghi_ly_do.py` (SO_TAY_CHAY mục 5). Không sửa `vi`, `ja`, cấu trúc.
2. Câu cố định (nguồn `cau_co_dinh`) không sửa trong file – thấy chưa hay → `ghi_chu_khi_dich: ["[Khi dịch] Đề nghị sửa câu cố định: …"]`.
3. JSON tiếng Việt sai / mâu thuẫn nội bộ → không sửa theo ý mình, ghi `loi_json_vi: ["[Lỗi JSON VI] <phần>: <vấn đề>"]` → câu quay lại GĐ1.
4. Chạy `python3 scripts/s2_kiem_tra.py --tu X --den Y`.

## Phạm vi sửa

- `loai`: `sai_so_ban_goc`, `chinh_ta` (gồm **trợ từ sai theo âm cuối**), `khach_quan`, `chu_quan`. Không thêm nội dung.
- Phần dịch từ tiếng Việt: không sửa theo ý mình khi tiếng Việt sai → `[Bản gốc VI] …` trong `ghi_chu_ban_goc`.
- Phần bám tiếng Nhật (VI + JA): sửa theo **tiếng Nhật** – khác bản Việt là bình thường.

## Checklist

- [ ] **(VI + JA)** nghĩa câu hỏi: đúng câu Nhật, giữ dạng câu hỏi và ký hiệu ①, [ ], （ ）.
- [ ] **(VI + JA)** nghĩa lựa chọn: đúng câu Nhật (thì, phủ định, chủ thể, mức độ, số liệu) – đây là chỗ quyết định người học hiểu đúng lựa chọn.
- [ ] **(VI + JA)** bản dịch trích dẫn: đúng câu Nhật; **cùng câu trích dẫn → cùng bản Hàn** trong mẫu (D-QT – lỗi) và giữa các câu con cùng đoạn văn (D4 – `output/reports/khong_nhat_quan.csv`).
- [ ] **(VI)** phân tích: đủ ý bản Việt, đúng ai / cái gì theo đoạn văn; kết luận đúng / sai của phân tích khớp `is_match` của lựa chọn đó; câu dẫn `…:` giữ.
- [ ] **(VI)** khuôn B – bản dịch đoạn văn: đủ ý từng dòng, tên riêng phiên âm theo đoạn văn tiếng Nhật.
- [ ] **Trợ từ sau ⟪ ⟫** theo âm cuối cách đọc tiếng Nhật (D12 – Python chỉ cảnh báo, phải tự soát cả khối có furigana và trường hợp có nháy / ngoặc giữa ⟫ và trợ từ).
- [ ] Văn phong -습니다 ở phân tích; giữ ⟪ ⟫, `{ }` (theo bản Việt), furigana, `\n`, gạch đầu dòng, loại dấu nháy.
- [ ] Thuật ngữ đọc hiểu thống nhất: 본문, 필자, 선택지, 정답, 인용문, 밑줄 친 부분, 지시어…

## Mẫu (trong file đặc tả lô GĐ2)

```json
"16645_1": {"thay": [{"duong_dan": "$.options[0].quotes[0].meaning.ko", "cu": "나쁘다고", "moi": "좋지 않다고"}],
            "sua": [{"duong_dan": "$.options[0].quotes[0].meaning", "loai": "khach_quan", "muc_do": "nhe", "ly_do": "良くない → 좋지 않다 (bám câu Nhật)"}],
            "ghi_chu_ban_goc": [], "ghi_chu_khi_dich": [], "loi_json_vi": []}
```
