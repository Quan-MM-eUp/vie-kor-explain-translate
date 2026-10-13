# Hướng dẫn chạy – dạng 10 Đọc hiểu: Đoạn văn ngắn

> Dạng 10 chạy **hoàn toàn bằng Claude Opus 5.5 trong Cowork** (không GPT API) – bạn không phải chạy lệnh.
> Mở một cuộc trò chuyện Cowork (liên kết máy tính có thư mục Vie-Kor) và gõ:
> **"Đọc dang_bai/10_doc_hieu_doan_van_ngan/SO_TAY_CHAY.md rồi chạy dạng 10 mẫu X đến Y"** (mỗi lô 10 mẫu – khuôn B 5 mẫu; tối đa 2 lô mỗi cuộc trò chuyện).

- Quy trình chi tiết cho Claude: `SO_TAY_CHAY.md`; lũy kế + quyết định đã chốt: `NHAT_KY.md`.
- Hai tác tử: **tác tử TẠO** (tác tử con – chuyển JSON, dịch Hàn) và **tác tử KIỂM TRA** (phiên chính – soát, gắn cờ, Python kiểm tra).
- Lời giải có lỗi nội dung → mẫu bị gắn cờ, không dịch, chuyển CTV tiếng Nhật (`s3b_xuat_ctv_nhat.py`); mẫu ĐẠT → Excel CTV tiếng Hàn (`s3_xuat_ctv.py`, có cột đoạn văn tiếng Nhật).
- Riêng dạng 10: Python **tách khung** lời giải (khuôn A / B / lẻ) cho tác tử TẠO, **so trích dẫn với đoạn văn gốc** (K-TD – `output/reports/trich_dan_lech.csv`) và **dò chữ Hán chèn giữa câu Việt** (K-KC – `output/reports/kanji_chen_cau_viet.csv`).
- Giai đoạn 0 đã chạy (2026-10-08): `python3 scripts/s0_chuan_bi.py`. Chạy lại khi dữ liệu gốc đổi (giữ thứ tự chạy; chỉ thêm `--tao-lai-thu-tu` khi muốn xếp lại).
