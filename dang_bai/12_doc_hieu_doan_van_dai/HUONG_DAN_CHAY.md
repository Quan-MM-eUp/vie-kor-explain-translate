# Hướng dẫn chạy – dạng 12 Đọc hiểu: Đoạn văn dài

> Dạng 12 chạy **hoàn toàn bằng Claude Opus 5.5 trong Cowork** (không GPT API) – bạn không phải chạy lệnh.
> Mở một cuộc trò chuyện Cowork (liên kết máy tính có thư mục Vie-Kor) và gõ:
> **"Đọc dang_bai/12_doc_hieu_doan_van_dai/SO_TAY_CHAY.md rồi chạy dạng 12 lô N"** (hoặc "… lô tiếp theo"). Mỗi lô = **2 đoạn văn (6–8 câu)**, tối đa **2 lô mỗi cuộc trò chuyện**.

- Quy trình chi tiết cho Claude: `SO_TAY_CHAY.md`; lũy kế + quyết định đã chốt: `NHAT_KY.md`.
- Hai tác tử: **tác tử TẠO** (tác tử con – chuyển JSON, dịch Hàn) và **tác tử KIỂM TRA** (phiên chính – đọc đoạn văn, soát, gắn cờ, Python kiểm tra).
- Lời giải có lỗi nội dung (trích dẫn sai, phân tích trái đoạn văn, đáp án đáng ngờ, chỉ có bản dịch…) → câu bị gắn cờ, không dịch, chuyển CTV tiếng Nhật (`s3b_xuat_ctv_nhat.py`); câu ĐẠT → Excel CTV tiếng Hàn (`s3_xuat_ctv.py`).
- Riêng dạng 12: Python **so từng câu trích 「…」 với đoạn văn gốc** (khớp / khớp theo cách đọc / lệch nhẹ / khác / không tìm thấy) – `output/reports/trich_dan.csv`.
- 43 lô: lô 1–36 khuôn chuẩn (8 đoạn đầu xen kẽ N1/N3), lô 37–43 các đoạn có lời giải bất thường (chỉ bản dịch / viết tự do / dịch máy ngược) – hầu hết sẽ thành câu gắn cờ `thieu_noi_dung`.
