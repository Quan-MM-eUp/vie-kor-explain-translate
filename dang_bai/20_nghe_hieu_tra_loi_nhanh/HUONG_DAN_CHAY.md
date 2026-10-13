# Hướng dẫn chạy – dạng 20 Nghe hiểu: Trả lời nhanh

> Dạng 20 chạy **hoàn toàn bằng Claude Opus 5.5 trong Cowork** (không GPT API) – bạn không phải chạy lệnh.
> Mở một cuộc trò chuyện Cowork (liên kết máy tính có thư mục Vie-Kor) và gõ:
> **"Đọc dang_bai/20_nghe_hieu_tra_loi_nhanh/SO_TAY_CHAY.md rồi chạy dạng 20 mẫu 1 đến 10"**
> Mỗi lô 10 câu (1–10, 11–20 …); tối đa 3 lô mỗi cuộc trò chuyện. Không nhớ lô tiếp theo: "… rồi chạy dạng 20 lô tiếp theo".

- Quy trình cho Claude: `SO_TAY_CHAY.md`; lũy kế + quyết định: `NHAT_KY.md`; kế hoạch đã duyệt: `KE_HOACH_PIPELINE.md`.
- Lô 1–10 là lô pilot (đủ N1–N5, 3 câu khuôn C, 1 câu chen từ Nhật, furigana trong phân tích, 1 câu thừa cột lua_chon_4) – nên xem kỹ kết quả trước khi chạy tiếp.
- Riêng dạng 20: câu nói tiếng Nhật lấy từ script (cột `transcript_vi`); Excel CTV có cột "Ngữ liệu" = script đã tách.
- Dữ liệu gốc cần nhóm sửa: `output/reports/du_lieu_goc.csv` (cột lua_chon_4 thừa, thiếu cột lựa chọn, script lỗi, ruby hỏng).
