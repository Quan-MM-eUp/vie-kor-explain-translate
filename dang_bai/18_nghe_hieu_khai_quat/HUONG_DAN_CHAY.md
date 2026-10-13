# Hướng dẫn chạy – dạng 18 Nghe hiểu khái quát

> Dạng 18 chạy **hoàn toàn bằng Claude Opus 5.5 trong Cowork** (không GPT API) – bạn không phải chạy lệnh.
> Mở một cuộc trò chuyện Cowork (liên kết máy tính có thư mục Vie-Kor) và gõ:
> **"Đọc dang_bai/18_nghe_hieu_khai_quat/SO_TAY_CHAY.md rồi chạy dạng 18 mẫu 1 đến 10"**
> Mỗi lô 10 câu (1–10, 11–20 …); tối đa 3 lô mỗi cuộc trò chuyện. Không nhớ lô tiếp theo: "… rồi chạy dạng 18 lô tiếp theo".

- Quy trình cho Claude: `SO_TAY_CHAY.md`; lũy kế + quyết định: `NHAT_KY.md`; kế hoạch đã duyệt: `KE_HOACH_PIPELINE.md`.
- Riêng dạng 18: Python tách lời thoại Nhật thành dòng L1…Ln (+ người nói, câu hỏi, 4 lựa chọn); tác tử TẠO ghép từng dòng với bản dịch Việt của lời giải.
- 59 câu khuôn D/E (lời giải không phân tích 4 lựa chọn) luôn bị gắn cờ `thieu_noi_dung` → file CTV tiếng Nhật (`s3b_xuat_ctv_nhat.py`).
- Muốn chạy lại bước chuẩn bị (sau khi dữ liệu gốc đổi): `python3 scripts/s0_chuan_bi.py` (giữ thứ tự chạy cũ).
