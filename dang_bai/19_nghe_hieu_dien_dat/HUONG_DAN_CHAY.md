# Hướng dẫn chạy – dạng 19 Nghe hiểu diễn đạt

> Dạng 19 chạy **hoàn toàn bằng Claude Opus 5.5 trong Cowork** (không GPT API) – bạn không phải chạy lệnh.
> Mở một cuộc trò chuyện Cowork (liên kết máy tính có thư mục Vie-Kor) và gõ:
> **"Đọc dang_bai/19_nghe_hieu_dien_dat/SO_TAY_CHAY.md rồi chạy dạng 19 mẫu 1 đến 12"**
> Mỗi lô 12 câu (1–12 là lô pilot, 13–24, 25–36 …); tối đa 3 lô mỗi cuộc trò chuyện. Không nhớ lô tiếp theo: "… rồi chạy dạng 19 lô tiếp theo".

- Quy trình cho Claude: `SO_TAY_CHAY.md`; lũy kế + quyết định: `NHAT_KY.md`; kế hoạch đã duyệt: `KE_HOACH_PIPELINE.md`.
- 366/406 câu được chạy. Câu không chạy: `output/reports/sai_dang.csv` (31 câu sai dạng – 25 câu nên chuyển sang dạng 20), `output/reports/khong_co_loi_giai.csv` (9 câu lời giải chỉ chép transcript).
- Excel CTV: câu ĐẠT → CTV tiếng Hàn (`s3_xuat_ctv.py`); câu bị cờ (gồm 36 câu khuôn B/D thiếu phân tích) → CTV tiếng Nhật (`s3b_xuat_ctv_nhat.py`). Nói với Claude "xuất Excel CTV dạng 19 mẫu A đến B".
- Bảng thuật ngữ / câu nói cố định tiếng Hàn: `glossary_ko.json` (bản nháp – nên nhờ CTV tiếng Hàn duyệt trước khi chạy GĐ2 nhiều lô).
