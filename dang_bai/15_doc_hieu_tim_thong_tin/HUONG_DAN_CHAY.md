# Hướng dẫn chạy – dạng 15 Đọc hiểu: Tìm thông tin

> Dạng 15 chạy **hoàn toàn bằng Claude Opus 5.5 trong Cowork** (không GPT API) – bạn không phải chạy lệnh.
> Mở một cuộc trò chuyện Cowork (liên kết máy tính có thư mục Vie-Kor) và gõ:
> **"Đọc dang_bai/15_doc_hieu_tim_thong_tin/SO_TAY_CHAY.md rồi chạy dạng 15 lô 1"**
> Mỗi lô ~10 câu, không cắt đôi ngữ liệu (35 lô – xem `output/thu_tu_chay.csv`, cột `lo`); tối đa 3 lô mỗi cuộc trò chuyện. Lô sau: "… rồi chạy dạng 15 lô tiếp theo".

- Quy trình cho Claude: `SO_TAY_CHAY.md`; lũy kế + quyết định: `NHAT_KY.md`; kế hoạch đã duyệt: `KE_HOACH_PIPELINE.md`.
- Riêng dạng 15: Python trải bảng ngữ liệu, so câu trích với ngữ liệu (`output/reports/trich_dan.csv`), tính lại phép tính (`output/reports/tinh_toan.csv`); ngữ liệu không dịch, hiện ở cột "Ngữ liệu" của Excel CTV (câu con đầu nhóm).
- Dữ liệu gốc nghi lỗi cần bạn xem: 12736_2 (đáp án), 53801_2 (đáp án), 16919_2 (lựa chọn bị đổi thành ngày giờ Excel); 21 câu ngữ liệu rỗng, 21 câu ngữ liệu là ảnh (danh sách trong NHAT_KY.md).
