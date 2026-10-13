# 07. Ngữ pháp – Lựa chọn ngữ pháp

| Mục | Giá trị |
|---|---|
| Tên trong sheet "Format giải thích" | Lựa chọn ngữ pháp |
| Giá trị cột `dang_bai` trong CSV | `lựa chọn ngữ pháp` |
| Số dòng | 2564 (N1: 433, N2: 461, N3: 552, N4: 567, N5: 551) |
| Dữ liệu | `data/07_ngu_phap_lua_chon_ngu_phap.csv` |
| Schema | `schema/grammar_choice.v2.json` (+ `.api.json` cho GPT strict) – thay `grammar_choice.v1` |
| Cấu hình | `config.json` |
| Cách chạy | `HUONG_DAN_CHAY.md` |
| README gốc | `README_goc.md` |

## Pipeline (dựng 2026-10-07 từ dạng 06, cách chia v2 – kế hoạch đã duyệt 07/10/2026)

- **GĐ0** `s0_chuan_bi.py`: chuẩn hóa HTML (ruby → `｜chữ《cách đọc》`), tách câu đề (+ Cách đọc / Nghĩa; hội thoại nhiều dòng; bỏ nhãn 'Đề bài:') / PHÂN TÍCH (Cấu trúc chung + mỗi lựa chọn: Ý nghĩa – Cấu trúc – Áp dụng vào câu – Về ngữ pháp – Nghĩa – Về ngữ nghĩa) / LỰA CHỌN ĐÚNG (số – Câu hoàn chỉnh – Nghĩa). Gắn cờ, ghép cách đọc câu đề từ furigana (khi thiếu dòng Cách đọc và furigana phủ hết chữ Hán), **so câu 'Áp dụng' với câu đề đã điền lựa chọn** (theo cách đọc Sudachi; hiểu hội thoại / 2 chỗ trống): lệch nhẹ (≤ 2 ký tự) → sửa định dạng, lệch nặng / chép nhầm lựa chọn khác → Claude gắn cờ `cau_khac_de`. Tạo `output/thu_tu_chay.csv`: 100 câu đầu = 20 câu mỗi cấp N1–N5, xen kẽ.
- **Schema `grammar_choice.v2`**: `question {ja, reading, meaning}`, `question_note`, `analysis {intro (Cấu trúc chung), options[4], conclusion}`, mỗi lựa chọn `{option_ja, meaning (Ý nghĩa), structure (Cấu trúc), applied {ja, meaning}, grammar_ok, grammar_note, semantic_ok, semantic_note, other}`, `correct {index, option_ja, full_sentence {ja, meaning}, note}`.
- **GĐ1**: GPT chuyển JSON → Claude kiểm tra theo `prompts/s1_claude_kiem_tra.md` (quy tắc 3d đã duyệt: đánh giá ngữ pháp sai rõ ràng, lý do loại không nêu lỗi chính, ý nghĩa / cấu trúc sai kiến thức, nghĩa câu lệch, câu khác đề, đáp án đáng ngờ, cách đọc, thiếu nội dung) → Python K1–K13 (K8/K9 = trung thành) + gợi ý R1 / A → chốt. Mọi cờ nội dung chặn dịch, chuyển CTV tiếng Nhật.
- **GĐ2**: nghĩa câu đề, nghĩa câu áp dụng, nghĩa câu hoàn chỉnh dịch TRỰC TIẾP từ tiếng Nhật; Ý nghĩa mẫu ngữ pháp kết hợp theo lựa chọn tiếng Nhật; phần còn lại dịch từ tiếng Việt (glossary thuật ngữ ngữ pháp tiếng Hàn) → Claude kiểm tra → Python (D1, D3, D4, D7, D12 trợ từ, D13 chỗ trống, D14 câu hoàn chỉnh = câu áp dụng của đáp án).
- **GĐ3**: Excel CTV tiếng Hàn (`s3_xuat_ctv.py`), Excel CTV tiếng Nhật (`s3b_xuat_ctv_nhat.py`), kho mẫu đã duyệt (`s10_luu_da_duyet.py`).

## Số liệu GĐ0 (2564 câu)

Cách đọc ghép từ furigana 403 · không có cách đọc 238 · Cấu trúc chung 347 · hội thoại 155 · 2 chỗ trống 38 · câu áp dụng lệch nhẹ 37 / lệch nặng 88 · câu hoàn chỉnh khác đề 52 · số LỰA CHỌN ĐÚNG gõ nhầm 46 · đáp án bị chấm không đạt 15.

## Lịch sử

| Ngày | Việc |
|---|---|
| 2026-10-07 | Dựng pipeline (schema v2, GĐ0–GĐ3); chạy thử giả lập end-to-end trên 2 câu ví dụ (thư mục `output_test/`) |

## Cập nhật 2026-10-07 – Quy tắc THAM KHẢO (leader duyệt, trước khi chạy thật)

Phần THÔNG TIN THAM KHẢO / NGỮ PHÁP THAM KHẢO (chỉ 1 câu: 4059) không gửi GPT, không kiểm tra, không sửa, không gắn cờ, không dịch, không đưa CTV duyệt. `split_sections` nhận thêm 2 tiêu đề này; `s0_chuan_bi.py` bỏ phần tham khảo khỏi `dau_vao` / `src_text` (cờ `co_tham_khao`); Python điền nguyên văn vào `reference_raw` (schema `grammar_choice.v2` thêm trường này, đánh dấu `x-python-dien` nên không có trong bản gửi GPT); kiểm tra `K-TK`. Chi tiết: `../../workflow/workflow_tong_quat.md` mục 11.

## Cập nhật 2026-10-08 – Chuyển bước GPT sang Claude Opus Cowork (từ mẫu 61)

Bước 1.1 (chuyển JSON) và 2.1–2.3 (dịch) do **tác tử TẠO** (Claude Opus 5.5, tác tử con ngữ cảnh riêng) làm thay GPT API; **tác tử KIỂM TRA** (phiên Claude chính) vẫn soát như cũ → giữ kiểm tra chéo hai bên + toàn bộ check Python K / D. Script mới: `s1_claude_tao.py`, `s2_claude_dich.py` (`--chuan-bi` / `--nhan`); prompt mới: `prompts/s1_claude_tao.md`, `prompts/s2_claude_dich.md` (dùng lại nguyên `s1_chuyen_json.md`, `s2_dich_ko.md`). Bản tạo mới ở `output/json_vi/claude_tao`, `output/json_ko/claude_tao`; mẫu 1–60 giữ bản GPT. `_dang.ban_tao()` chọn đúng bản cho `s1_claude_goi`, `s1_kiem_tra`, `s2_claude_goi`, `s2_kiem_tra`; Excel CTV ghi rõ bản do GPT hay Claude tạo. Cấu hình: `config.tao_ban.nguon = "claude"` (đặt `"gpt"` để quay lại). Các dạng 01–06 chưa đổi.
