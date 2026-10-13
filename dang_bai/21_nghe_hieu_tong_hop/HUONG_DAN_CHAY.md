# Hướng dẫn chạy – dạng 21 Nghe hiểu tổng hợp

> Dạng 21 chạy **hoàn toàn bằng Claude Opus 5.5 trong Cowork** (không GPT API) – bạn không phải chạy lệnh.
> Mở một cuộc trò chuyện Cowork (liên kết máy tính có thư mục Vie-Kor) và gõ:
> **"Đọc dang_bai/21_nghe_hieu_tong_hop/SO_TAY_CHAY.md rồi chạy dạng 21 mẫu 1 đến 6"** (lô 1 – pilot)
> Mỗi lô = 5 bài nghe (≈ 6 câu; bài 2 câu hỏi không tách); tối đa 3 lô mỗi cuộc trò chuyện. Không nhớ lô tiếp theo: "… rồi chạy dạng 21 lô tiếp theo".

- Quy trình cho Claude: `SO_TAY_CHAY.md`; lũy kế + quyết định: `NHAT_KY.md`; kế hoạch đã duyệt: `KE_HOACH_PIPELINE.md`.
- Khoảng mẫu từng lô: `output/lo_chay.csv` (hoặc nhờ Claude chạy `python3 scripts/lo.py`).
- 41 câu khuôn B / C (lời giải không phân tích lựa chọn) tự động gắn cờ, không dịch – xuất cho CTV tiếng Nhật bằng `s3b_xuat_ctv_nhat.py`.
- Dữ liệu gốc cần sửa: 53921_2 (không có lời thoại / lời giải), 53342_1 và 53343_1 (thiếu `lua_chon_4`).
