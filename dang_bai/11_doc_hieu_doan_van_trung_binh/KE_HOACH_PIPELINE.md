# Kế hoạch dựng pipeline – dạng 11 Đọc hiểu: Đoạn văn trung bình (ĐÃ DUYỆT 2026-10-08 – đã dựng, xem NHAT_KY.md)

> Soạn 2026-10-08. Chạy **hoàn toàn bằng Claude Opus 5.5 Cowork** (tác tử TẠO = tác tử con, tác tử KIỂM TRA = phiên chính), **không GPT API** – theo mẫu dạng 08/09 (`pipeline_chung/CLAUDE_TAO.md`).
> Số liệu dưới đây quét từ `data/11_doc_hieu_doan_van_trung_binh.csv`.

## 1. Dữ liệu – khác gì so với 07/08/09

| Đặc điểm | Số liệu | Hệ quả cho pipeline |
|---|---|---|
| 1151 câu = **395 đoạn văn** × 2–5 câu con (3 câu: 252 đoạn, 2: 86, 4: 54) | `doan_van` giống hệt nhau trong một đoạn | Thứ tự chạy + lô theo **đoạn văn**, không cắt đôi đoạn (như 09) |
| Đoạn văn: trung vị 590 ký tự, tối đa 4.574; có `①{<b>…</b>}` đánh dấu chỗ hỏi, chú thích `注1…`, 50 đoạn có `<table>`, 5 có `<img>` | | Python làm sạch đoạn văn đưa vào gói tác tử TẠO; đoạn có ảnh → cờ s0 |
| Lời giải HTML, **1043 câu (91%) khuôn chuẩn**: câu hỏi + dịch → 4 lựa chọn (Nghĩa / 引用·Trích dẫn 「…」 + (dịch) / phân tích) → `→ ĐÚNG` / `→ SAI` | 889 câu có trích dẫn | Ánh xạ sạch vào `reading_listening.v1` |
| **108 câu (9%) khuôn lạ**: chỉ dịch đoạn văn + "Câu trả lời đúng là…" (36), chỉ vài câu giải thích ngắn (56), markdown `###` (1), khác (15) | | Không có phân tích 4 lựa chọn → gắn cờ `thieu_noi_dung`, chuyển CTV tiếng Nhật |
| Furigana: ~45.000 thẻ ruby; **~430 câu (38%) chèn từ Nhật vào câu Việt** ("Câu này ｜表現《ひょうげん》 rõ rằng…") – bản Hàn cũ cũng giữ kiểu này | | Bọc `⟪｜表現《ひょうげん》⟫`, giữ nguyên; xem quyết định Q3 |
| Câu `→ ĐÚNG` lệch `dap_an_so`: 13; có ≠ 1 chỗ `→ ĐÚNG`: 11 | | Cờ s0 `lech_dap_an`, `nhieu_dung` |
| Trích dẫn 「…」 khớp nguyên văn đoạn văn: 70%; khớp một phần: 95% | | Kiểm tra trích dẫn = **CẢNH BÁO** (so mờ), không phải LỖI |
| Không có Bản dịch đầy đủ / Tóm tắt / THAM KHẢO (sheet Format nói bản dịch đầy đủ nằm riêng trên admin) | `transcript_vi` rỗng | `full_translation`, `summary`, `key_info` = `null`; không tạo nội dung mới; không cần `reference_raw` |
| `giai_thich_ko` có sẵn cả 1151 câu | | Như các dạng trước: **không dùng**, dịch lại từ JSON VI (xem Q5) |

## 2. Schema và ánh xạ

Giữ `reading_listening.v1` (`explanation_schema`), **không thêm trường**. id mẫu = `<question_id>_<cau_con>`.

| Lời giải gốc | Trường JSON |
|---|---|
| Dòng câu hỏi tiếng Nhật (có furigana) | `question.ja` (phải khớp `cau_hoi` sau khi bỏ furigana / thẻ) |
| Dòng dịch câu hỏi | `question.meaning.vi` |
| `1. …` (lựa chọn, có furigana) | `options[i].option_ja`; `reading = null` (lời giải không có dòng cách đọc riêng) |
| `Nghĩa: …` | `options[i].meaning.vi` |
| `引用:` / `Trích dẫn:` / `Đoạn văn có câu:` … + 「câu Nhật」 + (dịch) | `options[i].quotes[] = {ja, meaning.vi}` – mỗi câu trích một phần tử; nhãn dẫn không chép |
| Phần nhận xét còn lại | `options[i].analysis.vi` (từ Nhật chen giữa bọc `⟪ ⟫`) |
| `→ ĐÚNG` / `→ SAI` | `options[i].is_match` (true/false) |
| Đáp án | `correct = {index: dap_an_so, option_ja, full_sentence: null}` |
| Khuôn lạ (dịch đoạn văn, giải thích ngắn) | Chép phần có được vào trường gần nhất (`analysis` của lựa chọn đúng / `full_translation` cho bản dịch đoạn văn), các trường thiếu để `null` / `[]` + cờ `thieu_noi_dung` |

## 3. Quy trình (giữ nguyên khung 08/09)

**GĐ0 – Python `s0_chuan_bi.py`** (tái dùng `normalize.py`, `so_chu.py`, `tham_khao.py`… của `pipeline_chung`):
- Chuẩn hóa ruby → `｜…《…》`, `<b>/<u>` → `{ }`, phân loại khuôn A/B/C/D/F.
- `output/thu_tu_chay.csv` theo **đoạn văn**: 100 câu đầu ≈ 35 đoạn, 7 đoạn mỗi cấp N1–N5 xen kẽ; lô chuẩn **3–4 đoạn ≈ 10 câu** (không cắt đoạn).
- Cờ gợi ý cho tác tử KIỂM TRA: `khuon_la`, `lech_dap_an`, `nhieu_dung`, `cau_hoi_lech`, `lua_chon_lech`, `trich_dan_ngoai_doan`, `chen_tu_nhat`, `doan_co_anh`, `ruby_hong`.
- Báo cáo `output/reports/khao_sat_s0.csv` (khuôn, cờ theo từng câu).

**GĐ1 – JSON tiếng Việt**
1. `s1_claude_tao.py --chuan-bi` → gói đầu vào **theo đoạn**: đoạn văn đã làm sạch (giữ ①②③ và `{ }`), `de_bai_chung`, mỗi câu con: câu hỏi, 4 lựa chọn, đáp án, lời giải đã chuẩn hóa, cờ s0.
2. Tác tử TẠO (Agent, `model: opus`) chuyển JSON theo `prompts/s1_claude_tao.md` (+ ví dụ `explanation_schema/examples/11_…json`, sửa lại theo khuôn thật).
3. `--nhan` → `s1_claude_goi.py` → tác tử KIỂM TRA soát bằng `CC/xem_gd1.py` (hiện đoạn văn 1 lần + các câu con) → file đặc tả lô → `ghi_ly_do.py` → `s1_kiem_tra.py` → `s1_chot.py`.

**Python kiểm tra GĐ1** (ngoài bộ chung: schema, mất tiếng Nhật, độ phủ chữ Việt ≥ 97%, `{ }`, furigana, `⟪ ⟫`):
- LỖI: `correct.index ≠ dap_an_so`; số `is_match = true` ≠ 1 hoặc không trùng `correct.index` (trừ câu có cờ `dap_an`); thiếu lựa chọn.
- CẢNH BÁO: `question.ja` lệch `cau_hoi`; `option_ja` lệch `lua_chon_i`; **K-TD** `quotes[].ja` không tìm thấy trong đoạn văn (so mờ, bỏ furigana / dấu câu / 注); **K-NQ** cùng một câu trích trong một đoạn mà `meaning.vi` khác nhau giữa các câu con.

**Tiêu chí soát GĐ1 riêng dạng 11** (tác tử KIỂM TRA, chỉ gắn cờ – không sửa nội dung):

| Gắn cờ `nghi_noi_dung` khi | `nhom` đề xuất |
|---|---|
| Trích dẫn không có trong đoạn văn, trích sai chỗ, hoặc câu trích không chứng minh được điều phân tích nói | `trich_dan` *(mới)* |
| Phân tích lựa chọn trái nội dung đoạn văn / lập luận sai (vd nói "đoạn văn không đề cập" nhưng có) | `phan_tich` *(mới)* |
| Kết luận ĐÚNG/SAI trái đáp án, nhiều lựa chọn ĐÚNG | `dap_an` |
| Dịch câu hỏi / lựa chọn / câu trích sai nghĩa | `nghia_cau` |
| Khuôn lạ – thiếu phân tích các lựa chọn | `thieu_noi_dung` |

Sửa định dạng (`sua_dinh_dang`): lỗi gõ, nhãn dính dòng, dấu thừa, `⟪ ⟫` / furigana do tác tử TẠO làm lệch.
**Không gắn cờ:** phân tích sơ sài nhưng không sai; lựa chọn sai không kèm trích dẫn; dịch vụng nhưng đúng ý.

**GĐ2 – tiếng Hàn** (chỉ câu đã chốt, không cờ): `s2_claude_dich.py --chuan-bi` (gói theo đoạn) → tác tử TẠO dịch → `--nhan` → soát `CC/xem_gd2.py` → `s2_kiem_tra.py`. Điểm riêng:
- **Các câu con cùng đoạn dịch cùng lúc**; câu trích giống nhau phải dịch giống nhau (Python D4 theo đoạn).
- Câu Việt có `⟪từ Nhật⟫` chen giữa: giữ `⟪ ⟫`, trợ từ Hàn theo âm cuối cách đọc tiếng Nhật (như 08).
- `question.meaning`, `options.meaning`, `quotes.meaning`: dịch câu tự nhiên; `analysis`: văn phong -습니다.
- `glossary_ko.json` thêm thuật ngữ đọc hiểu: 本文/段落 → 본문/단락, 筆者 → 필자, 下線部 → 밑줄 친 부분, 引用 → 인용…

**GĐ3 – Excel CTV**: `s3_xuat_ctv.py` (ĐẠT → CTV tiếng Hàn) và `s3b_xuat_ctv_nhat.py` (có cờ → CTV tiếng Nhật), **nhóm theo đoạn văn**: đoạn văn hiện một lần ở đầu nhóm, sau đó từng câu con.

## 4. File sẽ tạo trong thư mục dạng 11

`config.json`, `glossary_ko.json`, `schema/` (bản sao `reading_listening.v1` + bản api), `scripts/` (`_dang.py`, `_dau_vao.py`, `s0_chuan_bi.py`, `s1_claude_tao.py`, `s1_claude_goi.py`, `s1_kiem_tra.py`, `s1_chot.py`, `s2_claude_dich.py`, `s2_claude_goi.py`, `s2_kiem_tra.py`, `s3_xuat_ctv.py`, `s3b_xuat_ctv_nhat.py`, `s9_bao_cao.py`, `s10_luu_da_duyet.py`; `s1_gpt_chuyen.py` / `s2_dich.py` chỉ báo lỗi), `prompts/` (`s1_claude_tao.md`, `s1_claude_kiem_tra.md`, `s2_claude_dich.md`, `s2_claude_kiem_tra.md`, `giao_viec_tao_gd1.md`, `giao_viec_tao_gd2.md`), `SO_TAY_CHAY.md`, `NHAT_KY.md`, `HUONG_DAN_CHAY.md`, cập nhật `README.md`.

**Cần sửa code chung** (làm ở cuộc trò chuyện điều phối, không ở phiên chạy dạng): thêm `trich_dan`, `phan_tich` vào `claude_log.NHOM_NOI_DUNG`; kiểm tra `checks_chung` / `schema_tools` duyệt đúng `Quote` / `Line` của `reading_listening`; cập nhật `pipeline_chung/CLAUDE_TAO.md` mục "Các dạng đã chuyển".

## 5. Lộ trình

| Bước | Việc | Đầu ra để duyệt |
|---|---|---|
| 1 | Dựng s0 + báo cáo khảo sát (khuôn, cờ, furigana) | `khao_sat_s0.csv`, tóm tắt số liệu |
| 2 | Viết prompt + script GĐ1, chạy pilot **lô 1 (~10 câu / 3–4 đoạn, đủ N1–N5, có 1 đoạn khuôn lạ, 1 đoạn có bảng)** | JSON VI + file lý do + bảng cờ |
| 3 | Anh duyệt pilot GĐ1 → chỉnh prompt / tiêu chí | ghi `NHAT_KY.md` |
| 4 | GĐ2 pilot + Excel CTV mẫu | Excel 2 file |
| 5 | Viết `SO_TAY_CHAY.md`, chạy lô thường: tối đa 3 lô / cuộc trò chuyện | — |

Ước tính chi phí tác tử TẠO (suy từ dạng 08 ≈ 130k token / 10 câu / giai đoạn, nhân hệ số đoạn văn + lời giải dài hơn): **≈ 200–280k token mỗi giai đoạn cho một lô ~10 câu**; sẽ đo lại ở pilot.

## 6. Cần anh duyệt

- **Q1 – Lô:** theo đoạn văn, 3–4 đoạn (~10 câu) mỗi lô, 100 câu đầu xen kẽ cấp độ?
- **Q2 – Khuôn lạ (108 câu):** vẫn tạo JSON từ phần có được + cờ `thieu_noi_dung` → CTV tiếng Nhật viết lại? (Hay bỏ qua hẳn, chỉ liệt kê.)
- **Q3 – Từ Nhật chen trong câu Việt (~430 câu):** giữ nguyên, bọc `⟪ ⟫` (không gắn cờ)? Trường hợp lỗi rõ như `đồng情する` → sửa định dạng hay gắn cờ?
- **Q4 – Trích dẫn không khớp đoạn văn:** Python chỉ CẢNH BÁO, tác tử KIỂM TRA quyết định gắn cờ `trich_dan` khi sai thật?
- **Q5 – `giai_thich_ko` có sẵn:** không dùng (như 07–09), hay đưa làm tham khảo thuật ngữ cho tác tử TẠO GĐ2?
- **Q6 – Hai nhóm cờ mới** `trich_dan`, `phan_tich` (sửa `pipeline_chung/claude_log.py`).
