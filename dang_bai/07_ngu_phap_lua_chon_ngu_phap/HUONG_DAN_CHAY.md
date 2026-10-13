# Hướng dẫn chạy – dạng 07 Lựa chọn ngữ pháp

> **Từ 2026-10-08 (mẫu 61 trở đi) toàn bộ dạng 07 do Claude Opus 5.5 trong Cowork chạy – không còn bước GPT API, bạn không phải chạy lệnh.**
> Bạn chỉ cần nói với Claude: **"Chạy dạng 07 mẫu X đến Y"**. Claude tự chạy các script trên máy bạn (thư mục `dang_bai\07_ngu_phap_lua_chon_ngu_phap`) và báo cáo khi xong lô.
> Mẫu 1–60 đã làm bằng GPT trước đó giữ nguyên (bản GPT ở `output/json_vi/gpt`, `output/json_ko/gpt`); các bước sau tự nhận ra bản nào (GPT hay Claude) qua `_dang.ban_tao()`.

> **Phiên Claude mới / chạy song song:** đọc `SO_TAY_CHAY.md` (quy trình chi tiết từng lệnh) + `NHAT_KY.md` (lũy kế, quyết định đã chốt). Câu mở đầu: "Đọc dang_bai/07_ngu_phap_lua_chon_ngu_phap/SO_TAY_CHAY.md rồi chạy dạng 07 mẫu X đến Y".

## Hai tác tử tách bạch (giữ kiểm tra chéo)

- **Tác tử TẠO (Claude A)** – tác tử con, ngữ cảnh riêng: làm đúng việc GPT từng làm (chuyển JSON, dịch), theo cùng prompt chi tiết như GPT (`s1_chuyen_json.md`, `s2_dich_ko.md`) + hướng dẫn riêng (`s1_claude_tao.md`, `s2_claude_dich.md`). Không kiểm tra, không gắn cờ.
- **Tác tử KIỂM TRA (Claude phiên chính)** – không tạo bản, chỉ soát bản của tác tử TẠO so với lời giải gốc theo `s1_claude_kiem_tra.md` / `s2_claude_kiem_tra.md` (quy tắc 3d, gắn cờ, sửa định dạng…), rồi Python kiểm tra K / D như cũ.

## Các bước của một lô (Claude chạy hết)

| Bước | Ai làm | Lệnh / việc |
|---|---|---|
| 1.1a Chuẩn bị gói đầu vào | Python | `python scripts/s1_claude_tao.py --chuan-bi --tu X --den Y` |
| 1.1b Chuyển JSON tiếng Việt | **Tác tử TẠO** | theo `prompts/s1_claude_tao.md` → `output/json_vi/claude_tao/<id>.json` |
| 1.1c Nhận + kiểm tra schema, điền reference_raw | Python | `python scripts/s1_claude_tao.py --nhan --tu X --den Y` |
| 1.2–1.5 Kiểm tra, gắn cờ, chốt | **Tác tử KIỂM TRA** + Python | `s1_claude_goi` → sửa → `s1_kiem_tra` → `s1_chot` |
| 2.1 Tách trường, điền sẵn thuật ngữ / bộ nhớ dịch | Python | `python scripts/s2_claude_dich.py --chuan-bi --tu X --den Y` (chỉ mẫu không có cờ) |
| 2.2 Dịch tiếng Hàn | **Tác tử TẠO** | theo `prompts/s2_claude_dich.md` → `output/claude/tao_gd2/<id>.output.json` |
| 2.3 Ghép, kiểm tra khớp mã | Python | `python scripts/s2_claude_dich.py --nhan --tu X --den Y` → `output/json_ko/claude_tao/<id>.json` |
| 2.4–2.5 Kiểm tra bản Hàn | **Tác tử KIỂM TRA** + Python | `s2_claude_goi` → sửa → `s2_kiem_tra` |
| 3. Excel CTV tiếng Hàn (mẫu ĐẠT) | Claude | `python scripts/s3_xuat_ctv.py --tu X --den Y` |
| 3b. Excel CTV tiếng Nhật (mẫu có cờ) | Claude | `python scripts/s3b_xuat_ctv_nhat.py --tu X --den Y` |
| 10. Lưu mẫu CTV đã duyệt vào kho | Claude | `python scripts/s10_luu_da_duyet.py --file <excel CTV> …` |

Thứ tự `--tu/--den` theo `output/thu_tu_chay.csv` (100 câu đầu = 20 câu mỗi cấp N1–N5, xen kẽ). Mặc định mỗi lô 10 mẫu.

Lỗi ở 1.1c (JSON hỏng / sai schema) → mẫu thành `LỖI_KỸ_THUẬT`, Claude giao lại cho tác tử TẠO làm lại mẫu đó (`--chuan-bi --ids <id> --force`). Lỗi ghép ở 2.3 → `LỖI_GĐ2`, làm lại tương tự.

## Quay lại GPT (nếu cần)

Đặt `"tao_ban": {"nguon": "gpt"}` trong `config.json`, rồi chạy như cũ: `python scripts/s1_gpt_chuyen.py --tu X --den Y`, `python scripts/s2_dich.py --tu X --den Y` (khi `nguon = claude` hai script này chỉ chạy nếu thêm `--dung-gpt`).

Gợi ý SudachiPy (R1 cách đọc câu đề; so câu áp dụng với đề theo cách đọc) dùng ở bước 0 và 1.2.
