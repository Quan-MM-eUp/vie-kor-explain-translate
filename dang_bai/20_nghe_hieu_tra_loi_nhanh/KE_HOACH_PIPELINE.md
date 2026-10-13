# Kế hoạch dựng pipeline – dạng 20 Nghe hiểu: Trả lời nhanh (ĐÃ DUYỆT 08/10/2026 – đã dựng)

> Soạn 2026-10-08. Chạy **hoàn toàn bằng Claude Opus 5.5 Cowork** (tác tử TẠO = tác tử con, tác tử KIỂM TRA = phiên chính), **không GPT API** – theo mẫu dạng 08/09 (`pipeline_chung/CLAUDE_TAO.md`).
> Số liệu dưới đây quét từ `data/20_nghe_hieu_tra_loi_nhanh.csv` (1376 câu: N1 397, N2 395, N3 246, N4 92, N5 246).

## 1. Dữ liệu – khác gì so với 07/08/09/11

| Đặc điểm | Số liệu | Hệ quả cho pipeline |
|---|---|---|
| Mỗi `question_id` = 1 câu độc lập (`cau_con` = 1), **không có đoạn văn chung** | 1376 câu / 1376 id | Lô theo câu (như 07), không cần nhóm |
| `lua_chon_1..3` chỉ là số `1` `2` `3` (đề nghe – không in lựa chọn); nội dung lựa chọn chỉ có trong **script** và **lời giải** | 1088 `1`, 35 `1)`, 13 `１` | Không so lựa chọn với cột `lua_chon_*`; so với script |
| **Script tiếng Nhật nằm ở cột `transcript_vi`** (tên cột gây nhầm): câu nói + 3 câu trả lời, có nhãn người nói `F：` / `M：` / `男：`, dòng nhãn trống cho người đáp | 1375/1376 có script | Python tách script → `utterance.ja` (xem Q1) |
| Script có biến thể: số lựa chọn `１.` / `１。` / `１ええ…` / không đánh số; ghi chú tiếng Nhật sau lựa chọn (`「説明しておいて」に対する答え`); 6 câu có `------` + bản dịch Việt; 17 câu có `れい 正答２` (câu ví dụ); 1 câu (12119) chứa nhầm lời giải | 197 câu regex đơn giản không tách được | Parser script riêng + cờ s0 `script_la` |
| `lua_chon_4 = "4"` nhưng script và lời giải chỉ có 3 lựa chọn | 51 câu (50 N1) | JSON 3 lựa chọn; ghi `bao_cao/du_lieu_goc.csv`, không gắn cờ |
| Thiếu lựa chọn trong dữ liệu gốc | 12224 (0 lựa chọn), 54035 (1 lựa chọn, lời giải chỉ có script) | Cờ s0 `du_lieu_loi` |

**Khuôn lời giải `giai_thich_vi`:**

| Khuôn | Số câu | Nội dung | Xử lý |
|---|---|---|---|
| **A – chuẩn** | 1232 (89,5%) | Phần trước `###`: dịch câu nói (có thể có nhãn `Nam:` / `F:` + dòng nhãn trống) + dịch 3 lựa chọn. Sau `###`: mỗi lựa chọn `n. câu Nhật` / `Nghĩa: …` / `→ ĐÚNG.`/`→ SAI.` / 1 dòng phân tích | Ánh xạ sạch vào `listening_response.v1` |
| **B – chuẩn nhưng thiếu `###`** (bọc `<p>`) | 6 | Chỉ có khối 3 lựa chọn, không có dòng dịch câu nói | Như A; `utterance.meaning = null` + cờ `thieu_noi_dung` |
| **C – chỉ có bản dịch** | ~137 (N1 90, N4 23, N5 19, N3 11) | Dịch câu nói + 3 lựa chọn, **không có phân tích, không chấm ĐÚNG/SAI** | Xem Q2 |
| **D – tự do** | 1 (22538) | Câu Nhật + `→ dịch` + phân tích + `→ Sai.` | Tác tử TẠO chuyển tay; phân tích câu nói → `prompt.analysis` |

Kiểm tra nhanh khuôn A: đủ 3 khối `Nghĩa:` (1232/1232), đúng 1 `→ ĐÚNG` và khớp `dap_an_so` (1232/1232) – **không có câu lệch đáp án**.

Điểm cần chú ý khác:
- **Bản dịch lặp 2 lần:** dịch lựa chọn ở trước `###` và dòng `Nghĩa:` – giống nhau 3345/3405 cặp; 60 cặp khác (đa số chỉ dấu câu; một số bản trước `###` còn chen từ Nhật: `商品 này` ↔ `sản phẩm này`). → Lấy `Nghĩa:` làm nguồn; phần dịch lựa chọn trước `###` là **phần trùng lặp** (workflow tổng quát mục 8 quy tắc 8) – không đưa vào JSON, Python chỉ so sánh để cảnh báo.
- **Từ Nhật chen trong bản dịch câu nói:** 70 câu (vd `Nữ: 店 này hình như có tiếng tốt đấy.`). Đây là lỗi dịch, không phải trích dẫn → xem Q3.
- **Từ Nhật trong phân tích:** 950 lựa chọn (525 có furigana), kiểu `Câu hỏi 「大学はどこですか」…` → bọc `⟪ ⟫`, giữ nguyên, không cờ.
- Lựa chọn trong lời giải ↔ script: khớp sau chuẩn hóa 1131/1232; 101 lệch do kana/kanji (`しんせつな` ↔ `親切な`) hoặc lỗi gõ ở script (`どもう`) → chỉ CẢNH BÁO.
- Không có phần THAM KHẢO (0 câu) → không cần `reference_raw` (mục 11 workflow tổng quát không áp dụng).
- `giai_thich_ko` có sẵn 1357 câu → không dùng (như 07–09, xem Q7).

## 2. Schema và ánh xạ

Giữ `listening_response.v1` (`explanation_schema`), **không thêm trường**. id mẫu = `<question_id>_1`.

| Nguồn | Trường JSON | Ai điền |
|---|---|---|
| Câu nói trong script (bỏ nhãn `F：`/`M：`, nối nếu nhiều dòng) | `prompt.utterance.ja` | **Python** (hook `bo_sung`, như `passage` dạng 09) |
| — | `prompt.utterance.reading` = `null` (bản gốc không có dòng cách đọc) | Python |
| Dòng dịch câu nói trước `###` (bỏ nhãn người nói) | `prompt.utterance.meaning.vi` | tác tử TẠO |
| — (bản gốc không có) | `prompt.situation = null`; `prompt.analysis = []` (trừ khuôn D) | tác tử TẠO |
| `n. câu Nhật` sau `###` (có furigana) | `options[i].sentence.ja`; `reading = null` | tác tử TẠO |
| `Nghĩa: …` | `options[i].sentence.meaning.vi` | tác tử TẠO |
| `→ ĐÚNG` / `→ SAI` | `options[i].is_correct` | tác tử TẠO |
| Dòng phân tích | `options[i].analysis.vi` (từ Nhật bọc `⟪ ⟫`, furigana đi theo) | tác tử TẠO |
| `dap_an_so` + bản sao `sentence.ja` lựa chọn đúng | `correct = {index, option_ja, full_sentence: null}` | tác tử TẠO; check furigana bỏ qua `option_ja` (bản sao) |
| Khuôn C | `meaning` có được; `is_correct` theo `dap_an_so`; `analysis = null` | tác tử TẠO + cờ `thieu_noi_dung` |

> Lưu ý: ví dụ `explanation_schema/examples/20_…json` có `reading` và `prompt.analysis` – dữ liệu thật **không có** hai phần này; sẽ sửa lại ví dụ theo khuôn A thật (giữ `reading = null`, `analysis = []`).

## 3. Furigana (mục bắt buộc theo workflow tổng quát mục 8.9)

| Vị trí trong bản gốc | Số chỗ ruby | Vào trường JSON |
|---|---|---|
| Sau `###` – dòng câu Nhật của lựa chọn | phần lớn trong 7261 | `options[i].sentence.ja` |
| Sau `###` – từ Nhật trong phân tích | 525 lựa chọn | `analysis.vi` trong `⟪｜…《…》⟫` |
| Trước `###` – từ Nhật chen trong bản dịch | 280 (79 câu) | `meaning.vi` trong `⟪ ⟫` (+ Q3) |
| Khuôn không `###` | 24 | theo khuôn |
| Script (`transcript_vi`) | 22 câu | `utterance.ja`: Python chuẩn hóa `｜…《…》`, giữ như script |
| `correct.option_ja` | bản sao | bỏ qua khi check furigana |

Ruby hỏng (vd 12119 `<rt>大学</rt>` – cách đọc là chữ Hán) → giữ chữ, ghi `ruby_hong_ban_goc.csv`. Pilot có ít nhất 3 câu có furigana trong phân tích.

## 4. Quy trình (giữ nguyên khung 07/08/09)

**GĐ0 – Python `s0_chuan_bi.py`** (tái dùng `normalize.py`, `so_chu.py`… của `pipeline_chung`):
- Chuẩn hóa ruby → `｜…《…》`, `<b>/<u>` → `{ }`, bỏ `<p>/<span data-…>`; phân loại khuôn A/B/C/D.
- **Parser script**: tách nhãn người nói, câu nói, 3 lựa chọn (mọi kiểu đánh số), cắt phần ghi chú / `------` / `れい 正答`.
- `output/thu_tu_chay.csv`: 100 câu đầu = 20 câu mỗi cấp N1–N5 xen kẽ, ưu tiên đủ khuôn; sau đó theo file. **Lô chuẩn 15 câu** (Q5).
- Cờ gợi ý cho tác tử KIỂM TRA: `khuon_C`, `khuon_la`, `lua_chon_thua`, `du_lieu_loi`, `script_la`, `lech_script`, `dich_lap_lech`, `chen_tu_nhat_dich`, `ruby_hong`.
- Báo cáo `output/reports/khao_sat_s0.csv` + `script.csv` (script đã tách, để soát parser).

**GĐ1 – JSON tiếng Việt**
1. `s1_claude_tao.py --chuan-bi` → gói đầu vào mỗi câu: script đã tách (câu nói + 3 lựa chọn, chỉ để tham khảo ngữ cảnh), lời giải đã chuẩn hóa, `dap_an_so`, cờ s0.
2. Tác tử TẠO (Agent, `model: opus`) chuyển JSON theo `prompts/s1_claude_tao.md`.
3. `--nhan` (Python điền `utterance.ja/reading`) → `s1_claude_goi.py` → tác tử KIỂM TRA soát bằng `CC/xem_gd1.py` (in script + lời giải gốc + JSON) → file đặc tả lô → `ghi_ly_do.py` → `s1_kiem_tra.py` → `s1_chot.py`.

**Python kiểm tra GĐ1** (ngoài bộ chung: schema, mất tiếng Nhật, độ phủ chữ Việt ≥ 97%, `{ }`, furigana, `⟪ ⟫`):
- LỖI: `correct.index ≠ dap_an_so`; số `is_correct = true` ≠ 1 hoặc không trùng `correct.index`; số lựa chọn ≠ số khối trong lời giải; `sentence.ja` ≠ dòng câu Nhật bản gốc; `utterance.ja` bị sửa so với bản Python điền.
- CẢNH BÁO: **K-SC** `sentence.ja` lệch lựa chọn trong script (so mờ: bỏ furigana, khoảng trắng, dấu câu; kana↔kanji qua cách đọc); **K-TL** dịch lựa chọn trước `###` khác `Nghĩa:` (bỏ dấu câu); `meaning.vi` còn chữ Nhật ngoài `⟪ ⟫`.

**Tiêu chí soát GĐ1 riêng dạng 20** (tác tử KIỂM TRA, chỉ gắn cờ – không sửa nội dung):

| Gắn cờ `nghi_noi_dung` khi | `nhom` |
|---|---|
| Lý do loại / chọn sai: phân tích hiểu sai chức năng câu nói (lời mời, nhờ vả, khen, trách…) hoặc lập luận vì sao phản hồi hợp / không hợp là sai | `ly_do_loai` (có sẵn) |
| Đánh giá sai sắc thái: kính ngữ / khiêm nhường, ため口, quan hệ trên–dưới, sắc thái mỉa mai… | `sac_thai` *(mới, Q8)* |
| Dịch câu nói / lựa chọn sai nghĩa; bản dịch còn chen từ Nhật (theo Q3) | `nghia_cau` |
| Câu Nhật trong lời giải khác script về **nội dung** (không phải kana/kanji, lỗi gõ) | `cau_khac_de` |
| Đáp án nghi sai / nghi 2 đáp án hợp lý | `dap_an` |
| Khuôn B (thiếu dịch câu nói), khuôn C | `thieu_noi_dung` |

Sửa định dạng (`sua_dinh_dang`): lỗi gõ, nhãn `Nghĩa:` dính dòng, dấu `。` trong câu Việt, `⟪ ⟫` / furigana do tác tử TẠO làm lệch, nhãn người nói còn sót trong `meaning`.
**Không gắn cờ:** phân tích ngắn (1 câu) nhưng đúng; dịch khẩu ngữ hơi vụng nhưng đúng ý; lệch kana/kanji giữa lời giải và script.

**GĐ2 – tiếng Hàn** (chỉ câu đã chốt, không cờ): `s2_claude_dich.py --chuan-bi` → tác tử TẠO dịch → `--nhan` → soát `CC/xem_gd2.py` → `s2_kiem_tra.py`. Điểm riêng:
- **Văn phong hội thoại:** `utterance.meaning`, `sentence.meaning` dịch như lời nói, **giữ mức lịch sự theo câu Nhật**: ため口 → 반말, です/ます → 해요체, kính ngữ / khiêm nhường → 하십시오체 / 존댓말 tương ứng; `analysis` văn phong -습니다. Tác tử TẠO GĐ2 thấy câu Nhật nên không dựa vào bản Việt để đoán mức lịch sự.
- Python D4: cùng một câu Nhật lặp trong 1 câu (câu nói được trích lại trong phân tích) phải dịch thống nhất.
- `glossary_ko.json` thêm thuật ngữ nghe hiểu: 発話 → 발화, 応答 → 응답, 相づち → 맞장구, 敬語 → 경어, 謙譲語 → 겸양어, 尊敬語 → 존경어, ため口 → 반말, 皮肉 → 비꼼…

**GĐ3 – Excel CTV**: `s3_xuat_ctv.py` (ĐẠT → CTV tiếng Hàn) và `s3b_xuat_ctv_nhat.py` (có cờ → CTV tiếng Nhật). Cột "Ngữ liệu" hiện **script đã tách** (câu nói + 3 lựa chọn) vì đề không in lựa chọn.

## 5. File sẽ tạo trong thư mục dạng 20

`config.json`, `glossary_ko.json`, `schema/` (bản sao `listening_response.v1` + bản api), `scripts/` (`_dang.py`, `_dau_vao.py`, `_script.py` (parser script), `s0_chuan_bi.py`, `s1_claude_tao.py`, `s1_claude_goi.py`, `s1_kiem_tra.py`, `s1_chot.py`, `s2_claude_dich.py`, `s2_claude_goi.py`, `s2_kiem_tra.py`, `s3_xuat_ctv.py`, `s3b_xuat_ctv_nhat.py`, `s9_bao_cao.py`, `s10_luu_da_duyet.py`; `s1_gpt_chuyen.py` / `s2_dich.py` chỉ báo lỗi), `prompts/` (`s1_claude_tao.md`, `s1_claude_kiem_tra.md`, `s2_claude_dich.md`, `s2_claude_kiem_tra.md`, `giao_viec_tao_gd1.md`, `giao_viec_tao_gd2.md`), `SO_TAY_CHAY.md`, `NHAT_KY.md`, `HUONG_DAN_CHAY.md`, cập nhật `README.md`.

**Cần sửa code chung** (làm ở cuộc trò chuyện điều phối): thêm `sac_thai` vào `claude_log.NHOM_NOI_DUNG` (nếu duyệt Q8); kiểm tra `checks_chung` / `schema_tools` duyệt đúng `Sentence` lồng trong `prompt.utterance` / `options[].sentence`; cập nhật `pipeline_chung/CLAUDE_TAO.md` mục "Các dạng đã chuyển"; sửa ví dụ `explanation_schema/examples/20_…json`.

**Tái dùng cho dạng 19** (Nghe hiểu diễn đạt, 406 câu, cùng schema `listening_response.v1`): sau khi 20 chạy ổn, dạng 19 dùng lại parser + prompt, chỉ khảo sát khác biệt (có tranh / `situation`).

## 6. Lộ trình

| Bước | Việc | Đầu ra để duyệt |
|---|---|---|
| 1 | Dựng s0 + parser script + báo cáo khảo sát | `khao_sat_s0.csv`, `script.csv`, tóm tắt số liệu |
| 2 | Viết prompt + script GĐ1, chạy pilot **lô 1 (15 câu: 3 mỗi cấp, có 2 câu khuôn C, 1 câu chen từ Nhật, 3 câu có furigana trong phân tích, 1 câu `lua_chon_4` thừa)** | JSON VI + file lý do + bảng cờ |
| 3 | Anh duyệt pilot GĐ1 → chỉnh prompt / tiêu chí | ghi `NHAT_KY.md` |
| 4 | GĐ2 pilot + Excel CTV mẫu | Excel 2 file |
| 5 | Viết `SO_TAY_CHAY.md`, chạy lô thường: tối đa 3 lô / cuộc trò chuyện | — |

Ước tính chi phí tác tử TẠO: lời giải dạng 20 ngắn hơn dạng 07 (3 lựa chọn, phân tích 1 dòng) → **≈ 120–150k token mỗi giai đoạn cho lô 15 câu** (dạng 07: ≈ 120k / 10 mẫu); đo lại ở pilot.

## 7. Cần anh duyệt (đã duyệt toàn bộ đề xuất Q1–Q8 ngày 08/10/2026)

- **Q1 – `utterance.ja` lấy từ script** (`transcript_vi`) do Python điền, vì lời giải không chép câu nói tiếng Nhật; bỏ nhãn người nói (`F：`/`Nam:`) ở cả `ja` và `meaning` (schema không có trường người nói)?
- **Q2 – Khuôn C (~137 câu, 10%; 90 câu N1):** tạo JSON phần dịch + `is_correct` theo đáp án, `analysis = null`, cờ `thieu_noi_dung` → CTV tiếng Nhật viết phân tích? (Hay chỉ liệt kê, không chạy.)
- **Q3 – Từ Nhật chen trong bản dịch câu nói (70 câu):** gắn cờ `nghia_cau` (CTV dịch lại) – hay cho tác tử KIỂM TRA thay bằng nghĩa Việt khi dòng `Nghĩa:` / ngữ cảnh đã có sẵn nghĩa đó (`sua_dinh_dang`)?
- **Q4 – `lua_chon_4 = "4"` thừa (51 câu):** JSON 3 lựa chọn, chỉ báo cáo dữ liệu gốc, không gắn cờ?
- **Q5 – Lô 15 câu** (100 câu đầu 20 câu mỗi cấp xen kẽ)? Hay giữ 10 như 07/08.
- **Q6 – `reading = null`** cho mọi câu (bản gốc không có dòng cách đọc; không tự sinh từ furigana)?
- **Q7 – `giai_thich_ko` có sẵn:** không dùng (như 07–09)?
- **Q8 – Nhóm cờ mới `sac_thai`** (đánh giá sai kính ngữ / mức lịch sự / sắc thái) – hay gộp vào `ly_do_loai`?

> Cập nhật 08/10/2026: lô đổi từ 15 → **10 câu** (2 câu mỗi cấp) theo yêu cầu người dùng – tránh tràn ngữ cảnh. Lô pilot = mẫu 1–10.
