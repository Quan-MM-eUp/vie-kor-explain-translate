# Hướng dẫn chạy – dạng 08 Lắp ghép câu

> Dạng 08 chạy **hoàn toàn bằng Claude Opus 5.5 trong Cowork** (không GPT API) – bạn không phải chạy lệnh.
> Mở một cuộc trò chuyện Cowork (liên kết máy tính có thư mục Vie-Kor) và gõ:
> **"Đọc dang_bai/08_ngu_phap_lap_ghep_cau/SO_TAY_CHAY.md rồi chạy dạng 08 mẫu X đến Y"** (mỗi lô 10 mẫu, tối đa 3 lô mỗi cuộc trò chuyện).

- Quy trình chi tiết cho Claude: `SO_TAY_CHAY.md`; lũy kế + quyết định đã chốt: `NHAT_KY.md`.
- Hai tác tử: **tác tử TẠO** (tác tử con – chuyển JSON, dịch Hàn) và **tác tử KIỂM TRA** (phiên chính – soát, gắn cờ, Python kiểm tra).
- Lời giải có lỗi nội dung → mẫu bị gắn cờ, không dịch, chuyển CTV tiếng Nhật (`s3b_xuat_ctv_nhat.py`); mẫu ĐẠT → Excel CTV tiếng Hàn (`s3_xuat_ctv.py`).
- Riêng dạng 08: Python **ghép câu tự động** (thử mọi thứ tự 4 lựa chọn so với "Câu hoàn chỉnh") để kiểm thứ tự đúng và ô ★ = đáp án – `output/reports/ghep_cau.csv`.
