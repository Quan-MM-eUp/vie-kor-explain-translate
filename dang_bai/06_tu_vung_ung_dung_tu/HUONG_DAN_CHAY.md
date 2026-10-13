# Hướng dẫn chạy – dạng 06 Ứng dụng từ

> **Từ 2026-10-08 (mẫu 101 trở đi) toàn bộ pipeline chạy bằng Claude Opus 5.5 trong Cowork – không gọi GPT API.**
> Bạn chỉ cần mở một cuộc trò chuyện Cowork mới và gõ:
> **"Đọc dang_bai/06_tu_vung_ung_dung_tu/SO_TAY_CHAY.md rồi chạy dạng 06 mẫu 101 đến 110"** (lô sau: 111–120, …; tối đa 3 lô mỗi cuộc trò chuyện).
> Claude tự chạy: tác tử TẠO (chuyển JSON tiếng Việt, dịch tiếng Hàn) + tác tử KIỂM TRA (soát, gắn cờ, chốt) + Python kiểm tra; cuối lô báo cáo và cập nhật `NHAT_KY.md`.
> Excel CTV: nhắn "Tạo file Excel gửi CTV tiếng Hàn cho dạng 06 mẫu X đến Y" (hoặc CTV tiếng Nhật cho câu bị cờ).
> `s1_gpt_chuyen.py` / `s2_dich.py` đã bị chặn (muốn quay lại GPT: `config.tao_ban.nguon = "gpt"` hoặc thêm `--dung-gpt`).
>
> Phần dưới là hướng dẫn cũ (luồng GPT, dùng cho mẫu 1–100) – giữ để tham khảo.

---

Mở cửa sổ lệnh tại thư mục `dang_bai\06_tu_vung_ung_dung_tu`.

**Chạy thử (pilot) trước** – 13 câu đại diện (ví dụ trong prompt, đề có định nghĩa, ruby hỏng, gạch chân HTML, câu sửa sai, mỗi cấp độ N1–N4):

| Bước | Ai chạy | Lệnh |
|---|---|---|
| 1.1 GPT chuyển JSON tiếng Việt | **Bạn** | `python scripts/s1_gpt_chuyen.py --pilot` |
| 1.2–1.5 Claude kiểm tra, gắn cờ, chốt | Claude | `s1_claude_goi --pilot` → sửa → `s1_kiem_tra` → `s1_chot` |
| 2.1–2.3 GPT dịch tiếng Hàn (chỉ mẫu không có cờ) | **Bạn** | `python scripts/s2_dich.py --pilot` |
| 2.4–2.5 Claude kiểm tra bản Hàn | Claude | `s2_claude_goi --pilot` → sửa → `s2_kiem_tra` |

**Chạy thật** – tuần tự 10 mẫu một lần (thay X, Y; mẫu đã chạy ở pilot tự bỏ qua):

| Bước | Ai chạy | Lệnh |
|---|---|---|
| 0. Chuẩn bị (đã chạy, chạy lại khi dữ liệu đổi) | Claude | `python scripts/s0_chuan_bi.py` |
| 1.1 GPT chuyển JSON tiếng Việt | **Bạn** | `python scripts/s1_gpt_chuyen.py --tu X --den Y` |
| 1.2–1.5 Claude kiểm tra, gắn cờ, chốt | Claude | `s1_claude_goi` → sửa → `s1_kiem_tra` → `s1_chot` |
| 2.1–2.3 GPT dịch tiếng Hàn (chỉ mẫu không có cờ) | **Bạn** | `python scripts/s2_dich.py --tu X --den Y` |
| 2.4–2.5 Claude kiểm tra bản Hàn | Claude | `s2_claude_goi` → sửa → `s2_kiem_tra` |
| 3. Excel CTV tiếng Hàn (mẫu ĐẠT) | Claude | `python scripts/s3_xuat_ctv.py --tu X --den Y` |
| 3b. Excel CTV tiếng Nhật (mẫu có cờ) | Claude | `python scripts/s3b_xuat_ctv_nhat.py --tu X --den Y` |
| 10. Lưu mẫu CTV đã duyệt vào kho | Claude | `python scripts/s10_luu_da_duyet.py --file <excel CTV> …` |

Xem prompt GPT trước khi chạy thật (không tốn token): `python scripts/s1_gpt_chuyen.py --pilot --dry-run`.

Gợi ý SudachiPy (R1 cách đọc câu, R2 câu sửa không thay từ đang hỏi) chỉ cần trên máy Claude chạy bước 1.2 (đã cài); máy bạn không cài cũng chạy được bước 1.1 và 2.1.
