# 14. Đọc hiểu – Đọc hiểu quan điểm (đoạn văn dài)

| Mục | Giá trị |
|---|---|
| Tên trong sheet "Format giải thích" | Đọc hiểu quan điểm (đoạn văn dài) |
| Giá trị cột `dang_bai` trong CSV | `đọc hiểu chủ đề` |
| Số dòng | 265 (N1: 104, N2: 161) |
| Dữ liệu | `data/14_doc_hieu_chu_de_quan_diem.csv` |
| Schema | `reading_listening.v1` (+ `reference_raw`) – `schema/reading_listening.v1.json` |
| Ví dụ JSON mẫu | `../../explanation_schema/examples/14_doc_hieu_chu_de_quan_diem.json` (12709_3 – câu hỏi tác giả, khuôn B; cập nhật 2026-10-08) |

Code và workflow chi tiết của dạng này đặt trong thư mục này.
Khung workflow chi tiết: xem mục 10 trong `../../workflow/workflow_tong_quat.md`.

## Trạng thái (2026-10-08)

Pipeline dạng 14 đã dựng (Claude Opus 5.5 Cowork, không GPT) theo `KE_HOACH_PIPELINE.md` (đã duyệt), chưa chạy lô nào.
Chạy: `HUONG_DAN_CHAY.md` → `SO_TAY_CHAY.md`; tiến độ: `NHAT_KY.md`. Phần đọc hiểu: `scripts/_doc_hieu_14.py`.
