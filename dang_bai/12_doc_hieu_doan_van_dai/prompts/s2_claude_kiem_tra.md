# Hướng dẫn Claude – Bước 2.4: kiểm tra bản dịch tiếng Hàn và sửa lỗi (dạng 12 – Đọc hiểu: Đoạn văn dài) · v1

> Phiên bản `s2_claude_kiem_tra.12.v1` (2026-10-08). Model: **Claude Opus 5.5**, chạy trong Claude Cowork (không qua API).
> Bản dịch cần kiểm tra do **tác tử TẠO (Claude A, ngữ cảnh riêng)** dịch – mọi chỗ "bản GPT" trong công cụ / nhật ký hiểu là bản của tác tử TẠO.

> Cột "Dịch từ" trong bảng xem nhanh: **JA** = nghĩa câu hỏi (`question.meaning`), nghĩa lựa chọn (`options[i].meaning`), nghĩa câu trích (`options[i].quotes[j].meaning`) – dịch thẳng từ câu tiếng Nhật; **VI** = `options[i].analysis` – theo tiếng Việt.

**Nhiệm vụ:** kiểm tra bản dịch **có đúng với ngữ cảnh không** và sửa lỗi. Ngữ cảnh gồm: đoạn văn, câu hỏi, các lựa chọn, đáp án, phần tiếng Nhật trong JSON và tiếng Việt của cả lời giải.

## Làm gì

Danh sách: `output/claude/gd2_danh_sach.json` (tạo bằng `python3 scripts/s2_claude_goi.py …`). Xem nhanh: `python3 ../../pipeline_chung/cong_cu/xem_gd2.py <id> …` (Mã | Bản nguồn | Tiếng Hàn); bảng đầy đủ `output/claude/gd2/<id>.md`.

1. Sửa **chỉ giá trị `ko`** trong `output/json_ko/checked/<id>.json` – bằng file đặc tả lô + `ghi_ly_do.py` (khóa `thay`, `duong_dan` tới `….ko`) hoặc python read-modify-write. Không sửa `vi`, `ja`, cấu trúc.
2. Ghi lý do: file đặc tả lô `output/claude/ly_do_lo/gd2_X_Y.json` (`"giai_doan": "2"`, liệt kê **mọi** mẫu GĐ2 của lô, kể cả không sửa) → `python3 ../../pipeline_chung/cong_cu/ghi_ly_do.py <file>`.
3. **Câu cố định** (nguồn `cau_co_dinh`): không sửa trong file; thấy chưa hay → `[Khi dịch] Đề nghị sửa câu cố định: …` vào `ghi_chu_khi_dich`.
4. Phát hiện **chính JSON tiếng Việt sai** (vd câu trích đặt nhầm lựa chọn, nghĩa câu trích Việt ≠ câu Nhật mà GĐ1 bỏ sót) hoặc **mâu thuẫn nội bộ**: không sửa theo ý mình, ghi `[Lỗi JSON VI] <phần>: <vấn đề>` vào `loi_json_vi` → câu quay lại GĐ1.
5. Làm xong cả lô thì chạy `python3 scripts/s2_kiem_tra.py --tu X --den Y` và xử lý lỗi / cảnh báo.

## Phạm vi sửa

- `loai` hợp lệ: `sai_so_ban_goc`, `chinh_ta` (gồm **trợ từ sai theo âm cuối**), `khach_quan`, `chu_quan`.
- Không thêm nội dung. Phần dịch từ tiếng Việt: không sửa theo ý mình khi tiếng Việt sai → ghi `[Bản gốc VI]`.
- Phần bám tiếng Nhật: sửa theo **tiếng Nhật** – khác bản Việt là bình thường (vd bản Việt dịch câu trích thiếu ý, bản Hàn dịch đủ).

## Checklist theo ngữ cảnh

- [ ] **(JA)** nghĩa câu hỏi: câu hỏi tiếng Hàn tự nhiên, đúng loại câu hỏi (lý do / chỉ thị từ / nội dung phù hợp / không phù hợp – **giữ phủ định** của câu hỏi "…違うもの / 合わないもの"); giữ ①②, `{ }` (D7).
- [ ] **(JA)** nghĩa lựa chọn: sát câu Nhật; lựa chọn sai vẫn dịch đúng như câu đang viết.
- [ ] **(JA)** nghĩa câu trích: đủ ý, sát câu Nhật (không lấy ý của nhận xét); **cùng câu trích → cùng bản dịch** trong cả câu (D15) và giữa các câu của cùng đoạn văn (đối chiếu bảng của cả lô; D4 → `output/reports/khong_nhat_quan.csv`).
- [ ] **(VI)** analysis: đúng và đủ ý tiếng Việt; kết luận "phù hợp / không phù hợp / không đề cập" giữ đúng; 'đoạn văn' → 본문, 'tác giả' → 필자; câu trích lại trong nhận xét khớp bản dịch câu trích.
- [ ] **Trợ từ sau `⟪ ⟫`** theo âm cuối của cách đọc tiếng Nhật (không theo âm Hán Hàn) – Python cảnh báo D12 (soát cả khi có nháy / ngoặc giữa ⟫ và trợ từ).
- [ ] Văn phong -습니다 ở `analysis`; giữ nguyên `⟪ ⟫` (kể cả furigana bên trong), `{ }`, xuống dòng, `- `, loại dấu nháy.
- [ ] Tác tử TẠO gộp / tách câu làm **mất một khối `⟪ ⟫`** so với bản Việt → tách lại cho đủ (Python báo "nội dung ⟪ ⟫ khác bản tiếng Việt").

## Mẫu file đặc tả lô (GĐ2)

```json
{"giai_doan": "2",
 "cau": {
  "16447_1": {},
  "16447_2": {"thay": [{"duong_dan": "$.options[0].quotes[0].meaning.ko", "cu": "잊어버리기 쉽다", "moi": "잊기 쉽습니다"}],
              "sua": [{"duong_dan": "$.options[0].quotes[0].meaning", "loai": "khach_quan", "muc_do": "nhe",
                       "ly_do": "(JA) Thống nhất với bản dịch cùng câu trích ở 16447_1 lựa chọn 1"}]}
 }}
```
