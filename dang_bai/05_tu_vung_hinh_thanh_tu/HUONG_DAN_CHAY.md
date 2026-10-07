# Hướng dẫn chạy – dạng 05 Hình thành từ

Mở cửa sổ lệnh tại thư mục `dang_bai\05_tu_vung_hinh_thanh_tu`. Chạy tuần tự 10 mẫu một lần (thay X, Y):

| Bước | Ai chạy | Lệnh |
|---|---|---|
| 0. Chuẩn bị (đã chạy 1 lần, chạy lại khi dữ liệu đổi) | Claude | `python scripts/s0_chuan_bi.py` |
| 1.1 GPT chuyển JSON tiếng Việt | **Bạn** | `python scripts/s1_gpt_chuyen.py --tu X --den Y` |
| 1.2–1.5 Claude kiểm tra, gắn cờ, chốt | Claude | `s1_claude_goi` → sửa → `s1_kiem_tra` → `s1_chot` |
| 2.1–2.3 GPT dịch tiếng Hàn (chỉ mẫu không có cờ) | **Bạn** | `python scripts/s2_dich.py --tu X --den Y` |
| 2.4–2.5 Claude kiểm tra bản Hàn | Claude | `s2_claude_goi` → sửa → `s2_kiem_tra` |
| 3. Excel CTV tiếng Hàn (mẫu ĐẠT) | Claude | `python scripts/s3_xuat_ctv.py --tu X --den Y` |
| 3b. Excel CTV tiếng Nhật (mẫu có cờ) | Claude | `python scripts/s3b_xuat_ctv_nhat.py --tu X --den Y` |

Xem prompt GPT trước khi chạy thật (không tốn token): `python scripts/s1_gpt_chuyen.py --tu 1 --den 10 --dry-run`.

Gợi ý SudachiPy (W1/W2/W3/F1) chỉ cần trên máy Claude chạy bước 1.2 (đã cài); máy bạn không cài cũng chạy được bước 1.1 và 2.1.
