# 13. Đọc hiểu – Đọc hiểu tổng hợp

| Mục | Giá trị |
|---|---|
| Tên trong sheet "Format giải thích" | Đọc hiểu tổng hợp |
| Giá trị cột `dang_bai` trong CSV | `đọc hiểu tổng hợp` |
| Số dòng | 149 (N1: 57, N2: 92) = 67 đoạn văn |
| Dữ liệu | `data/13_doc_hieu_tong_hop.csv` |
| Schema | `reading_listening.v1` (không thêm trường) + `reference_raw` – duyệt 08/10/2026 |
| Ví dụ JSON mẫu | `../../explanation_schema/examples/13_doc_hieu_tong_hop.json` (đã sửa 08/10/2026 theo quy tắc không thêm nội dung) |

Code và workflow chi tiết của dạng này đặt trong thư mục này.
Khung workflow chi tiết: xem mục 10 trong `../../workflow/workflow_tong_quat.md`.

## Trạng thái (2026-10-08)

Pipeline dạng 13 đã dựng (Claude Opus 5.5 Cowork, không GPT), đã chạy s0 (`output/thu_tu_chay.csv`, 18 lô), chưa chạy lô nào.
Chạy: `HUONG_DAN_CHAY.md` → `SO_TAY_CHAY.md`; tiến độ: `NHAT_KY.md`; kế hoạch đã duyệt: `KE_HOACH_PIPELINE.md`.
