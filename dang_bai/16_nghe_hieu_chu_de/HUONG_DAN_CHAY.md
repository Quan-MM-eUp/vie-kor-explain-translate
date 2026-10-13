# Hướng dẫn chạy – dạng 16 Nghe hiểu chủ đề

Chạy **trong Claude Cowork** (Claude Opus 5.5), không cần API key. Mở cuộc trò chuyện mới và gõ:

> **Đọc dang_bai/16_nghe_hieu_chu_de/SO_TAY_CHAY.md rồi chạy dạng 16 mẫu 1 đến 10**

Lô tiếp theo: "… chạy dạng 16 lô tiếp theo". Mỗi cuộc trò chuyện tối đa 3 lô (30 câu).

Cấu trúc thư mục:

| Thư mục / file | Nội dung |
|---|---|
| `KE_HOACH_PIPELINE.md` | Kế hoạch đã duyệt (số liệu dữ liệu, ánh xạ, quyết định Q1–Q8) |
| `SO_TAY_CHAY.md`, `NHAT_KY.md` | Sổ tay cho phiên chạy; nhật ký từng lô |
| `config.json`, `glossary_ko.json` | Cấu hình; thuật ngữ Hàn riêng dạng 16 |
| `schema/` | `reading_listening.v1.json` (đầy đủ, Python kiểm tra) + `.api.json` (tác tử TẠO) |
| `scripts/_nghe.py` | Tách nguồn / dòng / người nói / khối phân tích / câu trích (Python, không sửa chữ) |
| `scripts/_dang.py` | Chuẩn bị mẫu, JSON Python dựng, hook, kiểm tra K1–K12, hiển thị Excel |
| `scripts/_dau_vao.py`, `_dich_v3.py` | Đầu vào tác tử TẠO GĐ1 / GĐ2; dịch từ tiếng Nhật + kiểm tra D7 / D12 / D15 / D16 |
| `scripts/s0…s10`, `xem16.py` | Các bước pipeline; công cụ xem mẫu cho tác tử KIỂM TRA |
| `prompts/` | Hướng dẫn tác tử TẠO / KIỂM TRA hai giai đoạn + lời giao việc |
| `output/` | `samples/norm` (GĐ0), `thu_tu_chay.csv`, `reports/khao_sat_s0.csv`, … kết quả các bước |
| `da_duyet/` | Kho mẫu CTV đã chấp nhận (`s10_luu_da_duyet.py`) |
