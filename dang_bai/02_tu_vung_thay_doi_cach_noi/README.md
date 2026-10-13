# 02. Từ vựng – Thay đổi cách nói

| Mục | Giá trị |
|---|---|
| Tên trong sheet "Format giải thích" | Thay đổi cách nói |
| Giá trị cột `dang_bai` trong CSV | `thay đổi cách nói` |
| Số dòng | 1028 (N1: 176, N2: 193, N3: 227, N4: 215, N5: 217) |
| Dữ liệu | `data/02_tu_vung_thay_doi_cach_noi.csv` |
| Schema | `vocab_synonym.v1` |
| Ví dụ JSON mẫu | `../../explanation_schema/examples/02_tu_vung_thay_doi_cach_noi.json` |

Code và workflow chi tiết của dạng này đặt trong thư mục này.
Khung workflow chi tiết: xem mục 10 trong `../../workflow/workflow_tong_quat.md`.

## Cập nhật 2026-10-07 – Quy tắc THAM KHẢO (leader duyệt)

Phần THÔNG TIN THAM KHẢO không gửi GPT, không kiểm tra, không sửa định dạng, không gắn cờ, không dịch, không đưa CTV duyệt. Python tách nguyên văn ở `s0_chuan_bi.py` (`norm.phan.tham_khao`; `dau_vao` / `src_text` đã bỏ phần này) và điền vào trường `reference_raw` (`s1_gpt_chuyen.py`, bù ở `s1_claude_goi.py`). Schema đổi sang `schema/vocab_synonym.v3.json` (bỏ `reference`, thêm `reference_raw`). K7 (dòng / đánh số tham khảo) thay bằng `K-TK` (reference_raw đúng nguyên văn). Quy tắc 3c-3 và 3d-5 (về Tham khảo) bỏ. Áp dụng lại: 50 câu trước bị cờ chỉ vì Tham khảo (kể cả 2610 bị cờ "thiếu tham khảo") → bỏ cờ, GĐ1_XONG, đã chốt; 24 câu còn cờ ở phần khác và 26 câu trong kho giữ nguyên. Chi tiết: `../../workflow/workflow_tong_quat.md` mục 11.
