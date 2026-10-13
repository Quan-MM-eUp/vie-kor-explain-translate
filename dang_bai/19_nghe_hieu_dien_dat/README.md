# 19. Nghe hiểu – Nghe hiểu diễn đạt

| Mục | Giá trị |
|---|---|
| Tên trong sheet "Format giải thích" | Nghe hiểu diễn đạt |
| Giá trị cột `dang_bai` trong CSV | `nghe hiểu diễn đạt` |
| Số dòng | 406 (N1: 13, N2: 12, N3: 147, N4: 61, N5: 173) |
| Dữ liệu | `data/19_nghe_hieu_dien_dat.csv` |
| Schema | `listening_response.v1` (+ `reference_raw`) – `schema/listening_response.v1.json` |
| Ví dụ JSON mẫu | `../../explanation_schema/examples/19_nghe_hieu_dien_dat.json` |

Code và workflow chi tiết của dạng này đặt trong thư mục này.
Khung workflow chi tiết: xem mục 10 trong `../../workflow/workflow_tong_quat.md`.

## Trạng thái (2026-10-08)

Pipeline dạng 19 đã dựng (Claude Opus 5.5 Cowork, không GPT) theo `KE_HOACH_PIPELINE.md` (đã duyệt), s0 đã chạy, chưa chạy lô nào.
Chạy: `HUONG_DAN_CHAY.md` → `SO_TAY_CHAY.md`; tiến độ: `NHAT_KY.md`. 366 câu chạy được; 31 câu sai dạng + 9 câu không có lời giải chỉ liệt kê (`output/reports/`).
