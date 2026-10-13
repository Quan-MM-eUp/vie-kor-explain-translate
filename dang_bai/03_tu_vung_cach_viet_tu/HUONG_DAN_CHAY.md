# Hướng dẫn chạy – dạng 03 Cách viết từ

> **Từ 2026-10-08 (mẫu 11 trở đi) toàn bộ pipeline chạy bằng Claude Opus 5.5 trong Cowork – không gọi GPT API.**
> Mở một cuộc trò chuyện Cowork mới và gõ: **"Đọc dang_bai/03_tu_vung_cach_viet_tu/SO_TAY_CHAY.md rồi chạy dạng 03 mẫu 11 đến 20"** (lô sau: 21–30, …; tối đa 3 lô mỗi cuộc trò chuyện).
> Claude tự chạy tác tử TẠO + tác tử KIỂM TRA + Python kiểm tra; cuối lô báo cáo và cập nhật `NHAT_KY.md`. Excel CTV: nhắn "Tạo file Excel gửi CTV tiếng Hàn cho dạng 03 mẫu X đến Y".
> `s1_gpt_chuyen.py` / `s2_dich.py` đã bị chặn (muốn quay lại GPT: `config.tao_ban.nguon = "gpt"` hoặc `--dung-gpt`).
>
> Phần dưới là hướng dẫn cũ (luồng GPT, pilot mẫu 1–10) – giữ để tham khảo.

---

Mở cửa sổ lệnh tại thư mục `dang_bai\03_tu_vung_cach_viet_tu`. Chạy tuần tự 10 mẫu một lần (thay X, Y):

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

Gợi ý từ điển SudachiPy chỉ cần trên máy Claude chạy bước 1.2 (đã cài); máy bạn không cài cũng chạy được bước 1.1 và 2.1.
