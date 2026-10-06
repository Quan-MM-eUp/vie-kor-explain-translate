# Kho mẫu đã được CTV chấp nhận – Dạng 01: Cách đọc kanji

Kho này nằm **tách khỏi** `output/` và `output_v2/`: chạy lại pipeline không bao giờ ghi đè lên đây.
Mỗi file JSON trong kho là **đúng bản CTV đã xem và chấp nhận** (đã kiểm tra khớp nội dung trước khi lưu).

## Cấu trúc

| Đường dẫn | Nội dung |
|---|---|
| `danh_sach.csv` | Mỗi mẫu một dòng (xem cột bên dưới) |
| `json_vi/<id>.json` | JSON tiếng Việt đã chốt |
| `json_ko/<id>.json` | JSON tiếng Hàn đã chốt (bản CTV duyệt) |
| `ly_do/<id>.gd1.ly_do.json`, `<id>.gd2.ly_do.json` | Nhật ký Claude sửa ở GĐ1 / GĐ2 (truy vết) |
| `ctv_phan_hoi/` | Bản sao file Excel CTV dùng làm căn cứ |

Cột `danh_sach.csv`: `sample_id, question_id, cau_con, cap_do, ngay_duyet, file_ctv, ket_qua_ctv, ghi_chu_ctv, goi_y_han_han, cach_chia_dang, nguon_output, hash_goc, sha256_json_vi, sha256_json_ko, model_gd1, prompt_gd1, model_gd2, prompt_gd2, ngay_luu`

- `goi_y_han_han`: `co` = CTV gợi ý bổ sung 한자음 · `khong_can` = CTV ghi không cần · `tuy_chon` = có hay không đều được · trống = CTV không ghi.
- `cach_chia_dang`: `v1` = duyệt theo cách chia dạng cũ (không phân loại lại theo v2).
- `hash_goc`: dấu vân tay dữ liệu gốc lúc duyệt – `s0_chuan_bi.py` báo nếu dữ liệu gốc đổi (mẫu cần duyệt lại).
- `sha256_json_*`: phát hiện file trong kho bị sửa nhầm.

## Quy tắc

1. **Chỉ thêm mẫu bằng script** (không chép tay):
   `python scripts/s10_luu_da_duyet.py --file <excel CTV> [--nguon output] [--chap-nhan "Đạt"] [--tat-ca-dong] [--bo-mau <id,…>] [--dry-run]`
   Script chỉ lưu khi: trạng thái ĐẠT, có JSON chốt, bản KO hiện tại khớp nội dung CTV đã xem, CTV không sửa ở cột "KO — CTV SỬA TẠI ĐÂY". Mẫu không đạt điều kiện được liệt kê kèm lý do.
2. Mẫu "Sửa nhỏ": áp dụng chỗ CTV sửa vào JSON, chạy lại bước kiểm tra, xuất lại Excel cho CTV xác nhận → rồi mới lưu.
3. Không sửa tay file trong kho. Cần thay một mẫu: chạy lại script với `--ghi-de`.
4. Trong thư mục output đang dùng, mẫu có trong kho mang trạng thái **`ĐÃ_DUYỆT_CTV`** (do `s0_chuan_bi.py` và `s10_luu_da_duyet.py` tự đặt) → mọi bước và báo cáo bỏ qua. Bước gọi API còn chặn thêm một lần nữa; thêm `--ca-da-duyet` nếu vẫn muốn chạy lại. Mẫu có dữ liệu gốc đổi so với lúc duyệt không được đánh dấu (cần duyệt lại).
5. Không xóa file trong kho.

## Lịch sử nhập

| Ngày | File CTV | Số mẫu | Ghi chú |
|---|---|---|---|
| 2026-10-01 | `2026-09-29-CTV-01_cach_doc_kanji-dang1.xlsx` | 8 (N2) | File không điền cột Kết quả – bạn xác nhận cả 8 mẫu đã được chấp nhận (`--tat-ca-dong`) |
| 2026-10-01 | `2026-10-01-CTV-01_cach_doc_kanji-dang1-N5-N1-50cau_1.xlsx` | 41 "Đạt" | 2 "Sửa nhỏ" và 7 "Không đạt" chưa lưu |
| 2026-10-05 | `2026-10-02-CTV-01_cach_doc_kanji 02.10.2026_1.xlsx` | 20 "Đạt" (N2, nguồn `output_v2`) | 660_1 chấm Đạt nhưng có góp ý Nghĩa câu → không lưu (`--bo-mau 660_1`). 6 "Sửa nhỏ" + 9 "Không đạt" + 660_1 → gắn cờ nghi sai nội dung kèm ghi chú CTV, chuyển CTV tiếng Nhật |

Tổng: **69 mẫu** – N1: 9 · N2: 36 · N3: 7 · N4: 10 · N5: 7.
