# Hướng dẫn chạy – dạng 11 Đọc hiểu: Đoạn văn trung bình

> Dạng 11 chạy **hoàn toàn bằng Claude Opus 5.5 trong Cowork** (không GPT API) – bạn không phải chạy lệnh.
> Mở một cuộc trò chuyện Cowork (liên kết máy tính có thư mục Vie-Kor) và gõ:
> **"Đọc dang_bai/11_doc_hieu_doan_van_trung_binh/SO_TAY_CHAY.md rồi chạy dạng 11 mẫu X đến Y"** (X, Y = số thứ tự trong `output/thu_tu_chay.csv`; nên ~10 mẫu mỗi lần, tối đa ~30 mẫu mỗi cuộc trò chuyện).
> Lần đầu nên chạy **mẫu 1 đến 9** (3 đoạn văn trọn vẹn, khuôn chuẩn), duyệt kết quả, rồi **mẫu 10 đến 18** (4 đoạn – có khuôn lạ, đoạn có bảng, câu trích ngoài đoạn) trước khi chạy tiếp.

- Quy trình chi tiết cho Claude: `SO_TAY_CHAY.md`; lũy kế + quyết định đã chốt: `NHAT_KY.md`; kế hoạch đã duyệt: `KE_HOACH_PIPELINE.md`.
- Hai tác tử: **tác tử TẠO** (tác tử con – chuyển JSON, dịch Hàn) và **tác tử KIỂM TRA** (phiên chính – soát theo đoạn văn, gắn cờ, Python kiểm tra).
- Lời giải có lỗi nội dung (trích sai đoạn văn, nhận xét sai, kết luận lệch đáp án, khuôn lạ thiếu phân tích) → mẫu bị gắn cờ, không dịch, chuyển CTV tiếng Nhật (`s3b_xuat_ctv_nhat.py`); mẫu ĐẠT → Excel CTV tiếng Hàn (`s3_xuat_ctv.py`).
- Riêng dạng 11: Python **dò câu trích trong đoạn văn** (`output/reports/trich_dan.csv`) và kiểm kết luận ĐÚNG/SAI ↔ đáp án; bản Hàn của cùng một câu trích phải giống nhau ở mọi câu con của đoạn.
