# 15. Đọc hiểu – Tìm thông tin

| Mục | Giá trị |
|---|---|
| Tên trong sheet "Format giải thích" | Tìm thông tin |
| Giá trị cột `dang_bai` trong CSV | `tìm thông tin` |
| Số dòng | 354 (N1: 58, N2: 76, N3: 89, N4: 88, N5: 43) |
| Dữ liệu | `data/15_doc_hieu_tim_thong_tin.csv` |
| Schema | `reading_listening.v1` (+ `reference_raw`) – bản sao ở `schema/` |
| Ví dụ JSON mẫu | `../../explanation_schema/examples/15_doc_hieu_tim_thong_tin.json` |

Code và workflow chi tiết của dạng này đặt trong thư mục này.
Khung workflow chi tiết: xem mục 10 trong `../../workflow/workflow_tong_quat.md`.

## Trạng thái (2026-10-08)

Pipeline dạng 15 đã dựng theo `KE_HOACH_PIPELINE.md` (đã duyệt) – Claude Opus 5.5 Cowork, không GPT; phần đọc hiểu dùng chung ở `../../pipeline_chung/doc_hieu_chung.py`. Đã chạy s0 (toàn bộ 354 câu, thứ tự chạy 35 lô), chưa chạy lô nào. Chạy: `HUONG_DAN_CHAY.md` → `SO_TAY_CHAY.md`; tiến độ: `NHAT_KY.md`.
