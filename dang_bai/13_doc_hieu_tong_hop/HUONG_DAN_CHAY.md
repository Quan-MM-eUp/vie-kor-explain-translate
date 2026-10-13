# Hướng dẫn chạy – dạng 13 Đọc hiểu tổng hợp

> Dạng 13 chạy **hoàn toàn bằng Claude Opus 5.5 trong Cowork** (không GPT API) – bạn không phải chạy lệnh.
> Mở một cuộc trò chuyện Cowork (liên kết máy tính có thư mục Vie-Kor) và gõ:
> **"Đọc dang_bai/13_doc_hieu_tong_hop/SO_TAY_CHAY.md rồi chạy dạng 13 lô 1"** (lô 1 = pilot 4 đoạn, 9 câu – Claude dừng sau GĐ1 để bạn duyệt).
> Các lần sau: **"… rồi chạy dạng 13 lô tiếp theo"**. Mỗi lô = 4 đoạn văn (8–11 câu); tối đa 3 lô mỗi cuộc trò chuyện.

- Quy trình cho Claude: `SO_TAY_CHAY.md`; lũy kế + quyết định: `NHAT_KY.md`; kế hoạch đã duyệt: `KE_HOACH_PIPELINE.md`.
- Danh sách lô: `python3 scripts/lo.py` (18 lô; lô 16–18 là 9 đoạn lời giải khuôn lạ – gần như toàn bộ sẽ gắn cờ `thieu_noi_dung`).
- Khảo sát dữ liệu: `output/reports/khao_sat_s0.csv`, `doan_van_tach.csv`, `trich_dan.csv`.
