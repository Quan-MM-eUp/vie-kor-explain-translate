# Kế hoạch dựng pipeline – dạng 19 Nghe hiểu: Nghe hiểu diễn đạt (ĐÃ DUYỆT 08/10/2026 – đã dựng)

> Soạn 2026-10-08. Chạy **hoàn toàn bằng Claude Opus 5.5 Cowork** (tác tử TẠO = tác tử con `model: opus`, tác tử KIỂM TRA = phiên chính), **không GPT API** – theo khung dạng 08/09 (`pipeline_chung/CLAUDE_TAO.md`).
> Số liệu quét từ `data/19_nghe_hieu_dien_dat.csv` (406 câu, mỗi `question_id` 1 câu, `cau_con` = 1).

## 1. Dữ liệu – khác gì so với 07/08/09

| Đặc điểm | Số liệu | Hệ quả cho pipeline |
|---|---|---|
| Đề "nghe": cột `lua_chon_1–3` chỉ là số `1/2/3`; câu tình huống + 3 câu nói tiếng Nhật nằm trong **`transcript_vi`** (thực chất là transcript tiếng Nhật, HTML lộn xộn: `M:`/`F：`, `<span lang>`, ruby có `<rp>`) | 319/332 transcript có "何と言いますか" | Python tách transcript → câu tình huống JA + 3 câu lựa chọn JA (đối chiếu) |
| **Khuôn A – chuẩn (330 câu, N3 134 / N4 39 / N5 157)**: phần đầu = dịch tình huống + 3 dòng nghĩa lựa chọn → `###` → 3 khối: `n. câu Nhật (furigana)` / `Nghĩa: …` / `→ ĐÚNG|SAI` / phân tích | `→ ĐÚNG` khớp `dap_an_so` 100%; mỗi câu đúng 1 chỗ ĐÚNG | Ánh xạ sạch vào `listening_response.v1` |
| **Khuôn B (2 câu: 14253, 25373)**: có 3 khối phân tích nhưng **thiếu phần dịch tình huống** | | Tạo JSON, `utterance.meaning = null` + cờ `thieu_noi_dung` |
| **Khuôn C (27 câu)**: `giai_thich_vi` chỉ **chép lại transcript tiếng Nhật** (N2 12, N3 8, N4 7) | | Không có gì để chuyển (xem Q2) |
| **Khuôn D (47 câu)**: chỉ **dịch tình huống + 3 lựa chọn**, không phân tích (N1 13, N4 15, N5 15, N3 4) | | Có nghĩa, không có phân tích (xem Q2) |
| **Sai dạng:** 25 câu N1/N2 là đề 問題4 "まず文を聞いてください。それから、それに対する返事…" = **即時応答 (dạng 20)**; 54495 là đề 4 lựa chọn kiểu 課題理解 | 26 câu – đều thuộc khuôn C/D | Đề xuất loại khỏi dạng 19 (Q1) |
| Furigana: 311 câu có ruby ở dòng lựa chọn của phần `###`; 14 câu có ruby trong transcript; **2 câu ruby hỏng kiểu Hán Việt trong câu Việt** (`<ruby>人<rt>nhân</rt></ruby><ruby>員<rt>viên</rt></ruby>` – 21395, 25368) | | Chuẩn hóa `｜…《…》` như mọi dạng; ruby Hán Việt → cờ s0 (Q4) |
| Từ Nhật chen trong câu phân tích tiếng Việt (「～ていただけないでしょうか」, 'ご飯'…) | 230 câu | Bọc `⟪ ⟫`, giữ ngoặc gốc bên ngoài (như 07) |
| Câu Nhật trong lời giải lệch transcript (kana↔kanji, gõ sai) | 24 câu (vd 12268 `おおきく` / `大きく`) | Python so theo cách đọc (Sudachi) → CẢNH BÁO |
| 3 dòng nghĩa ở phần đầu **trùng** dòng `Nghĩa:` | lệch 1 câu (21413); 23 câu tình huống nhiều dòng | Phần đầu chỉ lấy tình huống; 3 dòng nghĩa = bản sao (quy tắc 8 mục furigana) → Python đối chiếu |
| Ảnh: 7 câu có `<img>` (link data.migii.net), lời giải gần như không dựa vào tranh (3 câu nhắc "tranh/mũi tên") | | Excel CTV hiện link ảnh; không xử lý ảnh |
| Không có THAM KHẢO, không có dòng "Cách đọc" | | `reading = null` mọi chỗ; không cần `reference_raw` |
| `giai_thich_ko` có sẵn 402/406 câu | | Như 07–09: không dùng (Q6) |

## 2. Schema và ánh xạ

Giữ `listening_response.v1` (`explanation_schema`), **không thêm trường**. id mẫu = `<question_id>_1`.

| Nguồn | Trường JSON | Ai điền |
|---|---|---|
| Câu tình huống + "何と言いますか" trong **transcript** (bỏ nhãn `M:`/`F:`, bỏ 3 dòng lựa chọn, giữ furigana) | `prompt.utterance.ja` | **Python** (khóa như `passage` dạng 09; tác tử TẠO không sửa) |
| Phần trước `###` – các dòng tình huống (nhiều dòng → nối `\n`) | `prompt.utterance.meaning.vi` | Tác tử TẠO |
| — | `prompt.situation = null`, `prompt.analysis = []`, `utterance.reading = null` | Python/TẠO |
| `n. câu Nhật` (furigana → `｜…《…》`) | `options[i].sentence.ja`; `reading = null` | TẠO |
| `Nghĩa: …` | `options[i].sentence.meaning.vi` | TẠO |
| `→ ĐÚNG` / `→ SAI` | `options[i].is_correct` | TẠO |
| Đoạn phân tích (Nhật chen giữa bọc `⟪ ⟫`) | `options[i].analysis.vi` | TẠO |
| Đáp án | `correct = {index: dap_an_so, option_ja: options[đúng].sentence.ja, full_sentence: null}` | TẠO (Python đối chiếu) |
| 3 dòng nghĩa ở phần đầu | không lưu (bản sao) – chỉ dùng để Python so với `Nghĩa:` | Python |

## 3. Quy trình (giữ nguyên khung 08/09)

**GĐ0 – `s0_chuan_bi.py`** (dùng `normalize.py`, `so_chu.py`… của `pipeline_chung`):
- Chuẩn hóa ruby, tách transcript, phân loại khuôn A/B/C/D, đánh dấu `sai_dang`.
- `output/thu_tu_chay.csv`: 100 câu đầu xen kẽ N3/N4/N5 (≈ 34/33/33, ưu tiên khuôn A, có vài câu B/D và câu có furigana/ảnh); sau đó theo file. **Lô chuẩn 12 câu** (câu ngắn: 3 lựa chọn, ~1.000 ký tự).
- Cờ gợi ý: `khuon_b`, `khuon_c`, `khuon_d`, `sai_dang`, `tinh_huong_khong_tach_duoc` (44 transcript không có 何と言いますか), `lc_lech_transcript`, `nghia_dau_lech`, `ruby_han_viet`, `co_anh`, `nhan_speaker`.
- Báo cáo `output/reports/khao_sat_s0.csv`, `sai_dang.csv`, `khong_co_loi_giai.csv`.

**GĐ1 – JSON tiếng Việt** (như 09): `s1_claude_tao.py --chuan-bi` (gói: đề chung, transcript đã làm sạch, lời giải đã chuẩn hóa, đáp án, cờ s0) → tác tử TẠO theo `prompts/s1_claude_tao.md` + `s1_chuyen_json.md` (viết mới cho dạng 19, ví dụ lấy từ câu thật 12111, 12138, 12268) → `--nhan` (Python điền `utterance.ja`) → `s1_claude_goi.py` → soát `CC/xem_gd1.py` (in transcript + lời giải gốc + JSON) → file đặc tả lô → `ghi_ly_do.py` → `s1_kiem_tra.py` → `s1_chot.py`.

**Python kiểm tra GĐ1** (ngoài bộ chung: schema, mất tiếng Nhật, độ phủ chữ Việt ≥ 97%, furigana, `⟪ ⟫`):
- LỖI: `correct.index ≠ dap_an_so`; số `is_correct = true` ≠ 1 hoặc ≠ `correct.index`; số lựa chọn ≠ 3 (4 với câu có `lua_chon_4`); `correct.option_ja` ≠ `sentence.ja` của lựa chọn đúng; `utterance.ja` khác bản Python điền.
- CẢNH BÁO: `sentence.ja` lệch câu tương ứng trong transcript (so cách đọc, chữ Hán ↔ kana không tính); `Nghĩa:` lệch dòng nghĩa ở phần đầu; tình huống VI rỗng.

**Tiêu chí soát GĐ1 riêng dạng 19** (chỉ gắn cờ, không sửa nội dung; **dùng nhóm cờ có sẵn – không phải sửa code chung**):

| Gắn cờ `nghi_noi_dung` khi | `nhom` |
|---|---|
| Lý do chọn/loại sai về **cách diễn đạt**: kính ngữ / khiêm nhường, あげる–くれる–もらう, ～ましょうか / ～ませんか / ～てもいいですか (ai làm cho ai), lời chào theo tình huống (trước/sau, trên/dưới) | `ly_do_loai` |
| Giải thích mẫu câu / sắc thái sai kiến thức | `y_nghia_cau_truc` |
| Dịch tình huống hoặc `Nghĩa:` sai nghĩa, sai chủ thể (ai nói với ai) | `nghia_cau` |
| Câu Nhật trong lời giải khác transcript về chữ (không phải chỉ kana↔kanji) | `cau_khac_de` |
| Lời giải ĐÚNG/SAI trái đáp án, đáp án đáng ngờ theo tình huống | `dap_an` |
| Khuôn B/D – thiếu phân tích hoặc thiếu dịch tình huống | `thieu_noi_dung` |

Sửa định dạng (`sua_dinh_dang`): lỗi gõ, dính dòng, ruby hỏng, ruby Hán Việt trong câu Việt (Q4), `⟪ ⟫` / furigana tác tử TẠO làm lệch.
**Không gắn cờ:** phân tích ngắn nhưng đúng; lời giải khác transcript chỉ ở dấu câu / kana↔kanji / dấu `、` – ghi `[Ghi chú]`.

**GĐ2 – tiếng Hàn** (chỉ câu đã chốt, không cờ): `s2_claude_dich.py --chuan-bi` → tác tử TẠO dịch → `--nhan` → soát `CC/xem_gd2.py` → `s2_kiem_tra.py`. Điểm riêng:
- `utterance.meaning`, `options[*].sentence.meaning` **dịch thẳng từ tiếng Nhật** (tham chiếu bản Việt) như 07 – câu nói tình huống cần lời Hàn tự nhiên, đúng mức lịch sự (vd いただきます → 잘 먹겠습니다, ごちそうさまでした → 잘 먹었습니다; "Bạn sẽ nói gì?" → "뭐라고 말합니까?").
- `analysis`: văn phong -습니다; trợ từ sau `⟪kana⟫` theo âm cuối cách đọc (D12).
- **D4 theo câu Nhật:** cùng câu lựa chọn/lời chào xuất hiện ở nhiều câu (rất nhiều ở N5) → bản Hàn giống nhau; bộ nhớ dịch khóa theo `sentence.ja`.
- `glossary_ko.json`: 敬語 경어, 尊敬語 존경어, 謙譲語 겸양어, 丁寧語 정중어, "thể lịch sự" 정중체, "thân mật" 반말/친근한 표현, "nhờ vả" 부탁, "xin phép" 허락을 구하다, "mời rủ" 권유…

**GĐ3 – Excel CTV**: `s3_xuat_ctv.py` (ĐẠT → CTV tiếng Hàn), `s3b_xuat_ctv_nhat.py` (có cờ → CTV tiếng Nhật). Cột "Ngữ liệu" = transcript sạch (tình huống + 3 câu nói) + link ảnh nếu có.

## 4. File sẽ tạo trong thư mục dạng 19

`config.json`, `glossary_ko.json`, `schema/` (bản sao `listening_response.v1` + bản api), `scripts/` (`_dang.py`, `_dau_vao.py`, `s0_chuan_bi.py`, `s1_claude_tao.py`, `s1_claude_goi.py`, `s1_kiem_tra.py`, `s1_chot.py`, `s2_claude_dich.py`, `s2_claude_goi.py`, `s2_kiem_tra.py`, `s3_xuat_ctv.py`, `s3b_xuat_ctv_nhat.py`, `s9_bao_cao.py`, `s10_luu_da_duyet.py`; `s1_gpt_chuyen.py` / `s2_dich.py` chỉ báo lỗi), `prompts/` (`s1_chuyen_json.md`, `s1_claude_tao.md`, `s1_claude_kiem_tra.md`, `s2_claude_dich.md`, `s2_claude_kiem_tra.md`, `giao_viec_tao_gd1.md`, `giao_viec_tao_gd2.md`), `SO_TAY_CHAY.md`, `NHAT_KY.md`, `HUONG_DAN_CHAY.md`, cập nhật `README.md`.

**Code chung:** dự kiến **không phải sửa** (dùng nhóm cờ có sẵn). Chỉ kiểm tra `schema_tools` / `dich.build_map` duyệt đúng `options[*].sentence` của `listening_response`; nếu thiếu thì sửa ở cuộc trò chuyện điều phối. Cập nhật `pipeline_chung/CLAUDE_TAO.md` mục "Các dạng đã chuyển".
**Tái dùng cho dạng 20 (1.376 câu, cùng schema):** viết phần tách transcript / ánh xạ trong `_dang.py` theo hàm tách riêng để dạng 20 chép sang và chỉ đổi phần khác (lời thoại người nói, `prompt.analysis`).

## 5. Lộ trình

| Bước | Việc | Đầu ra để duyệt |
|---|---|---|
| 1 | Dựng s0 + báo cáo khảo sát | `khao_sat_s0.csv`, `sai_dang.csv`, tóm tắt số liệu |
| 2 | Prompt + script GĐ1, pilot **lô 1–12** (N3/N4/N5, có câu furigana, 1 câu khuôn B/D, 1 câu có ảnh) | JSON VI + file lý do + bảng cờ |
| 3 | Anh duyệt pilot GĐ1 → chỉnh prompt / tiêu chí | ghi `NHAT_KY.md` |
| 4 | GĐ2 pilot + 2 file Excel CTV mẫu | Excel |
| 5 | Viết `SO_TAY_CHAY.md`, chạy lô thường (tối đa 3 lô = 36 câu / cuộc trò chuyện) | — |

Ước tính tác tử TẠO (suy từ dạng 07 ≈ 120k token / 10 câu / giai đoạn; lời giải dạng 19 ngắn hơn): **≈ 110–150k token mỗi giai đoạn cho lô 12 câu**, ~2–3 phút; đo lại ở pilot. Toàn dạng (~380 câu) ≈ 32 lô.

## 6. Cần anh duyệt

- **Q1 – Sai dạng (26 câu):** 25 câu N1/N2 (即時応答) + 54495 → loại khỏi dạng 19, ghi `reports/sai_dang.csv` để chuyển dạng 20 / phân loại lại (không sửa dữ liệu gốc)?
- **Q2 – Không có phân tích (sau Q1 còn 48 câu: khuôn D 34, khuôn C 14):** đề xuất khuôn D → tạo JSON từ phần có (tình huống + nghĩa) + cờ `thieu_noi_dung` → CTV tiếng Nhật; khuôn C (chỉ chép transcript) → không tạo JSON, chỉ liệt kê. Hay anh muốn Claude **viết lời giải mới** cho nhóm này (ngoài nguyên tắc "không thêm nội dung" – sẽ đi luồng riêng, CTV Nhật duyệt)?
- **Q3 – `utterance.ja` lấy từ transcript** (lời giải không có câu tình huống tiếng Nhật), Python điền và khóa, giữ furigana của transcript?
- **Q4 – Ruby Hán Việt trong câu Việt (21395, 25368):** sửa định dạng thành chữ Việt thường ("nhân viên") hay gắn cờ?
- **Q5 – Lô 12 câu**, 100 câu đầu xen kẽ N3/N4/N5?
- **Q6 – `giai_thich_ko` có sẵn:** không dùng (như 07–09), hay cho tác tử TẠO GĐ2 tham khảo cách nói lời chào cố định?
- **Q7 – Nghĩa câu (tình huống, lựa chọn) tiếng Hàn dịch thẳng từ tiếng Nhật** như dạng 07?

## 7. Kết quả duyệt và triển khai (2026-10-08)

- Người dùng đồng ý toàn bộ đề xuất Q1–Q7. Pipeline đã dựng; s0 đã chạy trên dữ liệu thật.
- Số liệu sau s0 (khác ước tính ở mục 1): **sai dạng 31 câu** (25 N1/N2 即時応答 + 6 N3 đề 4 lựa chọn 54495–54500), **khuôn C 9 câu**, khuôn D 34, khuôn B 2, khuôn A 330 → **366 câu chạy**.
- Phát hiện thêm khi dựng: phần đầu lời giải có nhãn người nói (`Nam:` / `Nữ:` – 20 câu) → không chép; một số lệch lời giải ↔ transcript là lỗi gõ **trong transcript** (21473, 21400) → chỉ ghi chú.
