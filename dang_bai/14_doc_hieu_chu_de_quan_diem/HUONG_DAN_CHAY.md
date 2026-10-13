# Hướng dẫn chạy – dạng 14 Đọc hiểu chủ đề / quan điểm

> Dạng 14 chạy **hoàn toàn bằng Claude Opus 5.5 trong Cowork** (không GPT API) – bạn không phải chạy lệnh.
> Mở một cuộc trò chuyện Cowork (liên kết máy tính có thư mục Vie-Kor) và gõ:
> **"Đọc dang_bai/14_doc_hieu_chu_de_quan_diem/SO_TAY_CHAY.md rồi chạy dạng 14 lô 1"**
> Mỗi lô = 3 đoạn văn (~9–11 câu, xem `output/lo_chay.csv`); tối đa 3 lô mỗi cuộc trò chuyện. Lô 1 là PILOT – duyệt kết quả GĐ1 trước khi chạy tiếp. Không nhớ lô tiếp theo: "… rồi chạy dạng 14 lô tiếp theo".

- Quy trình cho Claude: `SO_TAY_CHAY.md`; lũy kế + quyết định: `NHAT_KY.md`; kế hoạch đã duyệt: `KE_HOACH_PIPELINE.md`.
- Riêng dạng 14: 46 câu khuôn lạ được Claude **soạn mới** phần giải thích – luôn chuyển CTV tiếng Nhật duyệt (`s3b_xuat_ctv_nhat.py`) trước khi dịch.
- Đoạn văn không dịch, hiển thị ở cột "Ngữ liệu" của Excel CTV (dòng câu con đầu của mỗi đoạn).
