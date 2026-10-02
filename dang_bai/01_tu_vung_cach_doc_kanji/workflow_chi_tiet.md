# Workflow chi tiết – Dạng 01: Cách đọc kanji

> Phiên bản: 2026-09-27 · Trạng thái: **đã có code (chưa chạy GPT)** – cách chạy xem `HUONG_DAN_CHAY.md`.
> File này chỉ ghi **phần riêng của dạng 01**. Các bước, quy ước và kiểm tra chung xem ở `../../workflow/workflow_tong_quat.md` (gọi tắt là "WF chung").

## 1. Thông tin dạng

| Mục | Giá trị |
|---|---|
| Phần | Từ vựng |
| Tên trong sheet "Format giải thích" | Cách đọc kanji (dòng 2–4) |
| Giá trị `dang_bai` trong CSV | `cách đọc kanji` |
| Số câu | 1.872 (N1: 502, N2: 328, N3: 399, N4: 364, N5: 279) |
| Schema | `vocab_kanji_reading.v2` – `schema/vocab_kanji_reading.v2.json` (bản đầy đủ, Python kiểm tra) và `schema/vocab_kanji_reading.v2.api.json` (bản gửi GPT, tạo bằng `pipeline_chung/schema_tools.py`) |
| Ví dụ JSON mẫu | `../../explanation_schema/examples/01_tu_vung_cach_doc_kanji.json` |
| Dạng câu hỏi | Chọn cách đọc đúng của từ được gạch chân trong câu |

**Hiện trạng lời giải gốc** (quét ngày 2026-09-27):

| Khuôn | Số câu | Mô tả |
|---|---|---|
| JSON cũ | 1.852 | Khóa: `question{text, reading, mean, kanji, kanji_reading, kanji_mean, kanji_jishokei}`, `correct_index`, `correct_answer`, `answers[{index, answer, note}]`, `reference` (HTML) |
| `###` (HTML) | 20 | 3 phần: thông tin từ và câu / LỰA CHỌN ĐÚNG / PHÂN TÍCH, có furigana `<ruby>` |

**Đặc điểm và vấn đề của bản gốc:**

| Vấn đề | Số lượng | Xử lý |
|---|---|---|
| Phân tích của một lựa chọn bị **dồn vào ô `note` của lựa chọn khác** (vd. câu 393: ô của lựa chọn 2 chứa cả `4. やとって: …`) | 470 chỗ / 352 câu | GPT tách về đúng lựa chọn (mục 3) |
| Lựa chọn sai **thật sự không có** phân tích (vd. câu 1150) | 89 chỗ | `analysis: null` + `[Bản gốc VI] Thiếu phân tích lựa chọn X` |
| `correct_index` khác `dap_an_so` | 9 câu | Xem mục 11 (chưa chốt) |
| Số phân tích ít hơn số lựa chọn trong đề | 43 câu | Tạo đủ lựa chọn từ cột `lua_chon_1–4`, lựa chọn thiếu để `analysis: null` |
| Thiếu `<u>` ở câu / cách đọc / nghĩa | khoảng 190–250 câu | CẢNH BÁO, không tự thêm gạch chân |
| Không có nghĩa của từ (`kanji_mean` trống) | 2 câu | `[Bản gốc VI]` |
| Có thể từ điển (`kanji_jishokei`, vd. `空く(すく)`) | 299 câu | Tách thành `dictionary_form.ja` / `.reading` |
| Thể từ điển **viết dính vào cách đọc** (vd. câu 1585: `へってThể từ điển: 減る(へる)`) | 63 câu | `word.reading` = `へって`, phần sau đưa vào `dictionary_form` |
| Nhiều cách đọc trong một ô (vd. `みせ / てん`, `えきびょう, やくびょう`) | khoảng 10 câu | Giữ nguyên dấu ngăn cách |
| Có furigana `<ruby>` | khoảng 23 câu | Chuẩn hóa `｜…《…》` (WF chung mục 8) |
| Câu "không tồn tại từ có cách đọc này" | khoảng 800 lần, ≥ 6 cách viết | Câu cố định trong bảng thuật ngữ (mục 6) |

## 2. Đầu vào

| Cột CSV | Dùng cho |
|---|---|
| `question_id`, `cau_con`, `cap_do` | Định danh |
| `cau_hoi` | Đề bài, có `<u>` quanh từ đang hỏi → đối chiếu `question.ja` |
| `lua_chon_1–4` | Các lựa chọn → `options[i].option_ja` |
| `dap_an_so`, `dap_an_noi_dung` | Đáp án → `correct` |
| `giai_thich_vi` | Lời giải gốc (JSON cũ hoặc `###`) |
| `giai_thich_ko` | Không dùng (bản Hàn cũ, chỉ để tham khảo khi cần) |

File dữ liệu: `data/01_tu_vung_cach_doc_kanji.csv`.

## 2a. JSON Schema

**`vocab_kanji_reading.v2`** (thư mục `schema/`). Thay đổi so với v1 (dùng trong pilot 5 dạng, vẫn giữ nguyên ở `explanation_schema/`):

| # | Thay đổi | Lý do |
|---|---|---|
| 1 | Mô tả các trường viết lại theo quy tắc ở mục 3: chép nguyên văn, furigana `｜…《…》`, `⟪ ⟫`, `{ }`, tách phân tích bị dồn, không có thì `null` | Ở chế độ strict, GPT đọc `description` như hướng dẫn |
| 2 | `options`: đúng 4 phần tử (`minItems`/`maxItems` = 4) | Cả 1.872 câu đều có 4 lựa chọn |
| 3 | `correct.full_sentence` chỉ nhận `null` | Dạng 01 không có câu hoàn chỉnh; tránh GPT tự tạo |
| 4 | `question.reading`: chuỗi, hoặc `null` khi bản gốc không có dòng cách đọc | 20 câu dạng `###` không có dòng "Cách đọc:" (cách đọc chỉ ghi bằng furigana) – không để GPT tự ghép |
| 5 | `word.meaning` cho phép `null` | 2 câu bản gốc không có nghĩa của từ |
| 6 | `word.reading`: "kana", cho phép nhiều cách đọc; hướng dẫn tách thể từ điển viết dính | 63 câu dính thể từ điển, khoảng 10 câu nhiều cách đọc |
| 7 | Chỉ giữ định nghĩa `T` trong `$defs`; câu đề bài dùng object riêng thay cho `Sentence` dùng chung | Gọn, đúng riêng dạng 01 |

**Bản gửi GPT** (`*.api.json`) được tạo tự động, bỏ các khóa ngoài chuẩn (`$schema`, `title`, `x-…`) và định nghĩa không dùng:

```
python pipeline_chung/schema_tools.py dang_bai/01_tu_vung_cach_doc_kanji/schema/vocab_kanji_reading.v2.json
python pipeline_chung/schema_tools.py … --bo-rang-buoc    # nếu gateway không nhận minimum/maximum/minItems/maxItems
```

Script cũng kiểm tra yêu cầu chế độ strict (mọi object có `additionalProperties: false`, `required` đủ mọi thuộc tính).

**Đã kiểm tra (2026-09-27):** 5 file JSON Opus của pilot cũ và file ví dụ `01_tu_vung_cach_doc_kanji.json` đều ĐẠT schema v2 (sau khi đổi mã `schema`). Schema bắt được: thiếu lựa chọn, `full_sentence` khác `null`, `question.reading` = `null`, thêm trường lạ, sai mã phiên bản, `index` ngoài 1–4.

Schema **không** kiểm tra được (Python kiểm tra ở mục 5): 1 cặp `{ }` mỗi câu, `option_ja` trùng đề, còn sót phân tích bị dồn, furigana khớp bản gốc.

## 3. Quy tắc chuyển sang JSON (giai đoạn 1)

**Mọi câu (cả JSON cũ lẫn `###`) đều do GPT chuyển**, rồi Claude kiểm tra và sửa, rồi Python kiểm tra lần cuối (theo WF chung mục 5). Python không tự chuyển đổi, chỉ chuẩn bị đầu vào và gắn cờ gợi ý.

**Giai đoạn 0 – Python chuẩn bị** (không sửa nội dung):

1. Chuẩn hóa: ruby → `｜…《…》`; `<u>` → `{ }`; bỏ thẻ thừa (`<div>`, `<span>`, `&nbsp;`…) nhưng giữ xuống dòng và danh sách (`<li>` → dòng bắt đầu bằng "- ").
2. Gắn cờ cho từng câu vào `trang_thai.csv` (để Claude xem kỹ ở bước 1.2):

| Cờ | Điều kiện |
|---|---|
| `nghi_don_phan_tich` | Ô `note` của một lựa chọn chứa mẫu `<số>. <cách đọc>:` của lựa chọn khác |
| `thieu_phan_tich` | Lựa chọn sai có `note` trống |
| `lech_dap_an` | `correct_index` ≠ `dap_an_so` |
| `thieu_lua_chon` | Số `answers` < số lựa chọn trong đề |
| `thieu_gach_chan` | Không có `<u>` ở `text`, `reading` hoặc `mean` |
| `the_tu_dien` | `kanji_jishokei` khác rỗng |
| `tu_dien_dinh_cach_doc` | `kanji_reading` chứa "Thể từ điển:" |
| `co_furigana` | Có `<ruby>` |
| `dang_###` | Lời giải gốc dạng `###` |

**Bảng ánh xạ** (dùng trong prompt cho GPT):

| Lời giải gốc (JSON cũ) | Lời giải gốc (`###`) | JSON mới |
|---|---|---|
| `question.kanji` | "Từ:" | `word.ja` |
| `question.kanji_reading` | cách đọc sau "Từ:" / trong furigana | `word.reading` |
| `question.kanji_jishokei`, vd. `空く(すく)`; hoặc phần "Thể từ điển: …" dính trong `kanji_reading` | "Thể từ điển:" | `word.dictionary_form` = `{"ja": "空く", "reading": "すく"}`; không có → `null` |
| `question.kanji_mean` | "Nghĩa:" (dòng đầu) | `word.meaning.vi` |
| `question.text` | "Câu hỏi:" | `question.ja` (từ đang hỏi trong `{ }`) |
| `question.reading` | "Cách đọc:" | `question.reading` (`{ }` quanh cách đọc tương ứng) |
| `question.mean` | "Nghĩa:" (sau câu hỏi) | `question.meaning.vi` (`{ }` quanh phần nghĩa tương ứng) |
| `correct_index`, `correct_answer` | "LỰA CHỌN ĐÚNG" | `correct.index`, `correct.option_ja`; `correct.full_sentence` = `null` |
| `answers[i].note` | "PHÂN TÍCH" – dòng `i. …:` | `options[i].analysis.vi`; trống → `null` |
| `reference` | phần giải thích thêm (nếu có) | `reference.vi`; trống → `null` |

**Quy tắc riêng cho GPT:**

1. **Phân tích bị dồn:** nếu ô của một lựa chọn chứa phân tích của lựa chọn khác (dạng `4. やとって: …`), **tách phần đó về đúng lựa chọn**, bỏ phần đánh số `4. やとって:` ở đầu, không sửa câu chữ còn lại.
2. **Không có phân tích:** để `analysis: null`, **không tự viết**. Lựa chọn đúng thường có `analysis: null` (phần giải thích nằm ở `reference`).
3. `options` luôn có **đủ số lựa chọn như đề** (lấy `option_ja` từ `lua_chon_1–4`), theo đúng thứ tự `index`.
4. Tiếng Nhật trong câu tiếng Việt (vd. `Đây là cách đọc của từ "痞え" (khó khăn)`) bọc `⟪ ⟫`: `Đây là cách đọc của từ "⟪痞え⟫" (khó khăn)`.
5. Giữ nguyên câu chữ tiếng Việt, kể cả các cách viết khác nhau của câu "không tồn tại" (việc thống nhất để ở bước dịch).
6. Không thêm gạch chân `{ }` vào chỗ bản gốc không có.

**Ví dụ – câu 393 (có phân tích bị dồn):**

Bản gốc (rút gọn):

```json
"answers": [
  {"index": 1, "answer": "いのって", "note": "Đây là cách đọc thể て của từ 祈る (cầu nguyện)."},
  {"index": 2, "answer": "したって", "note": "Đây là cách đọc thể て của từ 慕う (hâm mộ, ngưỡng mộ). 4. やとって: Đây là cách đọc thể て của từ 雇う (thuê, mướn)."},
  {"index": 3, "answer": "つのって", "note": ""},
  {"index": 4, "answer": "やとって", "note": ""}
]
```

JSON mới:

```json
"options": [
  {"index": 1, "option_ja": "いのって", "analysis": {"vi": "Đây là cách đọc thể て của từ ⟪祈る⟫ (cầu nguyện)."}},
  {"index": 2, "option_ja": "したって", "analysis": {"vi": "Đây là cách đọc thể て của từ ⟪慕う⟫ (hâm mộ, ngưỡng mộ)."}},
  {"index": 3, "option_ja": "つのって", "analysis": null},
  {"index": 4, "option_ja": "やとって", "analysis": {"vi": "Đây là cách đọc thể て của từ ⟪雇う⟫ (thuê, mướn)."}}
]
```

## 4. Claude kiểm tra JSON (bước 1.2) – điểm riêng

Ngoài checklist chung (WF chung mục 5), với dạng 01 Claude kiểm tra:

- [ ] **Mỗi phân tích nằm đúng lựa chọn của nó:** nội dung `analysis` nói về đúng `option_ja` bên cạnh. Câu có cờ `nghi_don_phan_tich` phải xem kỹ: phần bị dồn đã tách hết chưa, có bị tách nhầm không.
- [ ] **Lựa chọn đúng:** `correct.index` và `correct.option_ja` khớp đề; phần giải thích lựa chọn đúng nằm ở `reference`, không bị đưa vào `analysis` của lựa chọn khác.
- [ ] **Gạch chân nhất quán ở 3 dòng:** `{ }` bọc đúng từ đang hỏi trong `question.ja`, cách đọc tương ứng trong `question.reading`, và phần nghĩa tương ứng trong `question.meaning.vi`.
- [ ] **Từ đang hỏi:** `word.ja` / `word.reading` đúng như bản gốc; thể từ điển tách đúng `ja` và `reading`.
- [ ] **Sửa lỗi có sẵn trong bản gốc** (WF chung mục 2a-1, thêm 2026-09-29): chỉ khi **chắc chắn**, sửa đúng chỗ sai, `loai: sua_ban_goc` + `nhom` + dòng `[Đã sửa bản gốc] <chỗ>: '<cũ>' → '<mới>' – <lý do>`. Câu có sửa bản gốc → **Dạng 2**. Hay gặp ở dạng này:
  - `cach_doc`: cách đọc câu lẫn số ①②③ (`いち{はまべ}…` → `{はまべ}…`, `にかだん` → `かだん`, 丘 `いっきゅう` → `おか`), đọc sai rõ ràng (挑む `ちょうむ` → `いどむ`, 貝殻 `がいがら` → `かいがら`).
  - `chinh_ta`: "Cố gằng" → "Cố gắng", "toàn câu" → "toàn cầu", "dạt đến" → "đạt đến".
  - `kien_thuc`: 人才 "thiên tài" → "nhân tài", 地形 `じぎょう` → `ちけい`, 挙行 "lễ kỉ niệm" → "cử hành".
- [ ] **Không sửa**, chỉ ghi `[Bản gốc VI]`: nghi sai nhưng không chắc (vd. "không tồn tại" với だまして – có thể là 騙して; nghĩa câu "chưa sát"); thiếu phân tích / thiếu đoạn (không tự thêm); lỗi ở đề, lựa chọn, đáp án (vd. 2 đáp án đúng, ベっそ trong đề).
- [ ] **89 chỗ thiếu phân tích và 43 câu thiếu lựa chọn:** GPT để `null`, không tự viết thêm.

## 5. Python kiểm tra JSON (bước 1.3) – kiểm tra thêm

Ngoài 7 kiểm tra chung (WF chung mục 5):

| # | Kiểm tra | Mức |
|---|---|---|
| K1 | Số phần tử `options` = số lựa chọn trong đề; `index` đủ và đúng thứ tự | LỖI |
| K2 | `options[i].option_ja` trùng `lua_chon_i` (sau khi chuẩn hóa) | LỖI |
| K3 | `analysis` của một lựa chọn **không chứa** mẫu `<số>. <option_ja của lựa chọn khác>:` (còn sót phần bị dồn) | LỖI |
| K4 | `word.reading` và `dictionary_form.reading` chỉ gồm kana (cho phép khoảng trắng, `/`, `、`, `,` ngăn cách nhiều cách đọc); không còn chữ "Thể từ điển" | LỖI |
| K5 | `word.ja` nằm trong cặp `{ }` của `question.ja` (có thể là dạng chia của từ) | CẢNH BÁO |
| K6 | `question.ja`, `question.reading`, `question.meaning.vi` đều có đúng 1 cặp `{ }`. Câu có cờ `thieu_gach_chan` thì chỉ CẢNH BÁO | LỖI / CẢNH BÁO |
| K7 | `correct.index` = `dap_an_so` (CSV) | Xem mục 11 |
| K8 | Lựa chọn có `note` khác rỗng trong bản gốc thì `analysis` không được `null` | LỖI |
| K9 | Số dòng đánh số ("1.", "2.") trong phần tham khảo bằng bản gốc (GPT hay đổi thành "- ") | CẢNH BÁO |

Kiểm tra độ phủ chữ Việt (kiểm tra chung số 4) vẫn đúng khi tách lại phân tích, vì nội dung chỉ đổi chỗ.

## 6. Quy tắc dịch riêng (giai đoạn 2)

**Các trường cần dịch** (thường 4–8 trường mỗi câu):

| Trường | Nội dung | Ghi chú |
|---|---|---|
| `word.meaning` | Nghĩa của từ, vd. "khuyến khích; động viên; khích lệ" | Giữ dạng liệt kê, ngăn cách bằng `;`; dùng dạng từ điển (-다), **không** dùng -습니다 |
| `question.meaning` | Bản dịch câu ví dụ | Giữ đúng 1 cặp `{ }` quanh phần tương ứng |
| `options[i].analysis` | Phân tích lựa chọn sai | Văn phong -습니다 |
| `reference` | Giải thích thêm về từ | Văn phong -습니다; giữ xuống dòng và dòng "- " |

**Bảng thuật ngữ riêng** (`glossary_ko.json` trong thư mục này, gộp với bảng chung khi chạy):

- **Câu cố định:** mọi biến thể "không tồn tại / không có từ nào … có cách đọc này" → `이 읽는 법을 가진 단어는 존재하지 않습니다.` Python điền trực tiếp ở bước 2.1, không gửi GPT.
- **Mẫu câu:** "Đây là cách đọc của từ X (nghĩa)." → `X(의미)의 읽는 법입니다.`; "Đây là cách đọc thể て của từ X (nghĩa)." → `X(의미)의 て형 읽는 법입니다.` (GPT dịch theo mẫu, Claude kiểm tra).
- **Thuật ngữ:** cách đọc → 읽는 법; âm On → 음독; âm Kun → 훈독; thể từ điển → 사전형; thể て → て형; biến âm → 음 변화.
- **Bản địa hóa:** "âm Hán Việt" không có ý nghĩa với người Hàn → xem mục 11.

Bảng hiện là **bản nháp**, cần CTV tiếng Hàn duyệt trước khi chạy thật.

## 7. Claude kiểm tra bản dịch (bước 2.4) – điểm riêng

- [ ] **Nghĩa của từ đúng nghĩa trong câu:** `word.meaning` (tiếng Hàn) phải có nghĩa được dùng trong `question.ja`. Nếu từ nhiều nghĩa, không được chỉ giữ nghĩa khác.
- [ ] **Nghĩa trong câu phân tích:** với mẫu "cách đọc của từ X (nghĩa)", nghĩa tiếng Hàn phải đúng với từ X (tiếng Nhật), không chỉ đúng với chữ tiếng Việt.
- [ ] **`{ }` trong `question.meaning`** bọc đúng phần dịch của từ đang hỏi.
- [ ] **Câu cố định** dùng đúng bản trong bảng thuật ngữ; các câu "không tồn tại" giống hệt nhau trên mọi câu hỏi.
- [ ] **Văn phong:** `word.meaning` dạng từ điển; các trường còn lại -습니다.

## 8. Python kiểm tra bản dịch (bước 2.5) – kiểm tra thêm

| # | Kiểm tra | Mức |
|---|---|---|
| D1 | Câu `vi` thuộc danh sách câu cố định thì `ko` phải đúng bản dịch trong bảng | LỖI |
| D2 | `word.meaning.ko` không kết thúc bằng -습니다/-ㅂ니다 | CẢNH BÁO |
| D3 | `question.meaning.ko` có đúng 1 cặp `{ }` nếu `question.meaning.vi` có | LỖI |
| D4 | Báo cáo **nhất quán giữa các câu:** cùng một `vi` nhưng khác `ko` | CẢNH BÁO (tổng hợp) |

**D5 – còn âm Hán Việt** (thêm 2026-09-29): trường tiếng Việt có "âm Hán Việt" hoặc bản dịch có 베트남 한자음 / 한월음 → LỖI. Bắt cả âm không dấu (vd 446 LANG) mà kiểm tra "còn chữ tiếng Việt" bỏ sót. Bỏ / đổi khi đã chốt cách xử lý âm Hán Việt (mục 11).

### Phân loại kết quả (bước 2.7 – `scripts/s8_phan_loai.py`)

Định nghĩa từ 2026-09-29 (thay định nghĩa cũ). Mỗi câu có `dang_gd1` (xét giai đoạn 1) và `dang` (kết quả cuối):

| Dạng | Điều kiện | Nội dung báo cáo |
|---|---|---|
| 1 | `ĐẠT`; ở GĐ1 Claude **không** sửa lỗi có sẵn trong bản gốc. GPT đổi chữ, Claude sửa lỗi GPT, ghi chú `[Bản gốc VI]` chưa sửa, Claude sửa bản dịch KO – đều vẫn là Dạng 1 (thông tin ghi trong `phan_loai.csv`; `[Bản gốc VI]` hiện ở cột "Điểm cần chú ý" của Excel CTV) | Ghi chú bản gốc chưa sửa, GPT đổi gì, Claude sửa gì |
| 2 | `ĐẠT`; ở GĐ1 Claude **có** sửa lỗi có sẵn trong bản gốc (`loai: sua_ban_goc`, ghi chú `[Đã sửa bản gốc]` – WF chung 2a-1) | Claude sửa lỗi bản gốc (nhóm, cũ → mới, lý do) + các thông tin như Dạng 1 |
| 3 | `LỖI_GĐ2` có lỗi D5 (còn âm Hán Việt) – câu có thể là Dạng 1 hoặc 2 ở GĐ1 (`dang_gd1`); lỗi khác ở cùng trường (vd "còn chữ tiếng Việt") coi là hệ quả của Hán Việt | Lỗi, `dang_gd1`, ghi chú khi dịch. Khi đã chốt cách xử lý Hán Việt và dịch lại → câu tự về `dang_gd1` |
| chưa phân loại | Lỗi pipeline khác: `LỖI_GĐ2` không có D5, `LỖI_GĐ1`, `CẦN_SỬA_GĐ1`, `LỖI_KỸ_THUẬT` → `chua_phan_loai.csv`; xử lý theo `can_kiem_tra.csv` rồi chạy lại | – |

Câu chưa chạy xong (`ĐANG_XỬ_LÝ`, `GĐ1_XONG`) không được phân loại.

**So chữ** (`pipeline_chung/so_chu.py`): so theo từng từ / dấu câu phần chữ tiếng Việt của lời giải gốc (theo thứ tự trường của JSON) với các trường `vi` của bản GPT; bỏ qua ⟪ ⟫, { }, furigana, khoảng trắng và nhãn cố định. Chạy thử 40 câu: chỉ 393 khác (bỏ nhãn `4. やとって:` khi tách phân tích bị dồn – đúng quy tắc).

### Cách chia dạng v2 (từ 2026-10-01 – thư mục `output_v2/`)

Bật bằng `config.json`: `"output": "output_v2"`, `"cach_chia_dang": "v2"`. Kết quả cũ ở `output/` giữ nguyên, không phân loại lại. Chi tiết và lưu ý: `output_v2/CHU_Y_TRIEN_KHAI.md`.

| | Điều kiện |
|---|---|
| Dạng 1 | Lời giải gốc không sai định dạng (`so_cho_sua_dinh_dang = 0`) |
| Dạng 2 | Claude có sửa định dạng (`loai: sua_dinh_dang`, mỗi chỗ một dòng `[Đã sửa định dạng] <chỗ>: 'cũ' → 'mới' – lý do`) |
| Cờ `nghi_noi_dung` | Claude nghi sai nội dung (nghĩa câu/thì, tự–tha động từ, cách đọc…) – chỉ gắn cờ với `vi_tri`, `nhom`, `mo_ta`, `de_xuat`; không sửa → trạng thái `CHỜ_DUYỆT_NỘI_DUNG` |
| Cờ `han_viet` | Python phát hiện âm Hán Việt trong lời giải gốc (`_dang.han_viet_src`) → `CHỜ_XỬ_LÝ_HÁN_VIỆT` |

**Chỉ câu không có cả 2 cờ mới được dịch** (`s2_dich.py` tự bỏ qua câu có cờ). Cách đọc lẫn số ①②③ là lỗi định dạng (`cach_doc_lan_so`); cách đọc sai khác là lỗi nội dung. Báo cáo `s8_phan_loai.py`: `phan_loai.csv`, `dang_1.csv`, `dang_2.csv`, `nghi_noi_dung.csv`, `han_viet.csv`. CTV tiếng Nhật (`s3b`) xem câu Dạng 2 và câu có cờ `nghi_noi_dung`.

### Kho mẫu đã được CTV chấp nhận (`da_duyet/`, từ 2026-10-01)

Mẫu CTV chấp nhận được lưu bằng `scripts/s10_luu_da_duyet.py` vào `da_duyet/` (tách khỏi mọi thư mục output): `json_vi/`, `json_ko/`, `ly_do/`, `ctv_phan_hoi/`, `danh_sach.csv` (cấp độ, ngày duyệt, file CTV, ghi chú CTV, gợi ý 한자음, cách chia dạng, `hash_goc`, sha256, model/prompt). Script chỉ lưu khi bản KO hiện tại khớp nội dung CTV đã xem. Bước 1.1/2.1 tự bỏ qua mẫu trong kho; `s0` báo khi dữ liệu gốc của mẫu trong kho thay đổi. Chi tiết: `da_duyet/README.md`.

## 9. Hiển thị trong Excel cho CTV

- Dùng lại cách hiển thị `vocab_kanji_reading` của `export_ctv_xlsx.py` (pilot 5 dạng): nhãn 【Từ】【Cách đọc】【Thể từ điển】【Nghĩa】【Câu hỏi】… giữ tiếng Việt ở cả hai cột; `{ }` hiển thị in đậm; furigana `漢字《かな》` (ẩn `｜`).
- Lựa chọn có `analysis: null` hiển thị dòng lựa chọn, không có phân tích.
- Thêm **sheet chi tiết theo trường** (Mã / Vị trí / Tiếng Việt / Tiếng Hàn / Bản sửa CTV) để đưa bản sửa của CTV ngược vào JSON.
- Cột "Điểm cần chú ý": thêm các cờ ở mục 3 (vd. `[Bản gốc VI] Thiếu phân tích lựa chọn 2`, `[Claude – JSON VI] Đã tách phân tích lựa chọn 4 khỏi lựa chọn 2`).

## 10. Mẫu test và tiêu chí đạt

**Pilot: 30 câu**, chọn có chủ đích (seed cố định):

| Nhóm | Số câu |
|---|---|
| Trải đều N1–N5, câu thông thường (gồm 5 câu pilot cũ + 1 câu mỗi cấp độ) | 10 |
| `nghi_don_phan_tich` | 5 |
| `thieu_phan_tich` / `thieu_lua_chon` | 3 |
| `lech_dap_an` | 2 |
| `thieu_gach_chan` | 2 |
| `the_tu_dien` / `tu_dien_dinh_cach_doc` | 3 |
| `dang_###` (có furigana) | 3 |
| Câu có "không tồn tại" ở ≥ 2 lựa chọn | 2 |

Gồm cả 5 câu pilot cũ (1097, 15284, 3285, 54564, 54733) để so sánh với bản Opus.

**Tiêu chí để chạy toàn bộ 1.872 câu:**

- Giai đoạn 1: ≥ 90% câu ĐẠT Python; 100% câu `nghi_don_phan_tich` được tách đúng (Claude xác nhận); không có lỗi mức nghiêm trọng.
- Giai đoạn 2: ≥ 90% câu ĐẠT Python; ≥ 80% câu CTV chấm "Đạt"; không có lỗi nghiêm trọng.
- Đo và báo cáo: token / chi phí thật mỗi câu, số chỗ Claude sửa theo loại.

**Chạy toàn bộ:** theo lô 200 câu, theo dõi qua `trang_thai.csv`; sau mỗi lô xem nhanh tỷ lệ LỖI / CẢNH BÁO trước khi chạy lô tiếp.

## 11. Việc cần chốt

- [ ] **Áp dụng quy tắc chung mới (WF chung mục 3a, 2026-09-28): in đậm cũng → `{ }`.** Dạng 01 có 135 câu (đều dạng JSON cũ) in đậm trong lời giải, chủ yếu để nhấn mạnh ở phần tham khảo (vd 379 `chủ thể bị tiêu diệ`, 544 `hoành tráng`) → các câu này sẽ có thêm `{ }` ngoài câu đề. Cần sửa: `normalize.py`, K6 (bỏ giới hạn 1 cặp ngoài `question`), chạy lại GĐ1 cho 5 câu test (379 bị ảnh hưởng).

- [ ] **9 câu lệch đáp án** (`correct_index` ≠ `dap_an_so`): đề xuất lấy `dap_an_so` (CSV) làm chuẩn + ghi `[Bản gốc VI]`; hoặc gắn `LỖI_GĐ1`.
- [ ] **Phạm vi Claude kiểm tra khi chạy 1.872 câu:** tất cả, hay câu có cờ/cảnh báo + khoảng 10% ngẫu nhiên.
- [ ] **"Âm Hán Việt" trong `reference`:** dịch nguyên kèm ghi chú, bỏ đi, hay thay bằng 한자음 (đụng quy tắc "không thêm nội dung").
- [ ] CTV duyệt bảng thuật ngữ và các câu cố định.
- [ ] Model GPT và các tính năng gateway (strict schema, Batch, temperature).

## 12. Cấu trúc thư mục

```
01_tu_vung_cach_doc_kanji/
├── README.md, workflow_chi_tiet.md, HUONG_DAN_CHAY.md
├── config.json               ← model, pilot, chính sách (lệch đáp án, phạm vi Claude), ngưỡng kiểm tra
├── glossary_ko.json          ← thuật ngữ + câu cố định + mẫu câu riêng dạng 01 (bản nháp)
├── data/                     ← 01_tu_vung_cach_doc_kanji.csv
├── schema/                   ← vocab_kanji_reading.v2.json (+ .api.json)
├── prompts/
│   ├── s1_chuyen_json.md     ← prompt GPT giai đoạn 1
│   ├── s1_claude_kiem_tra.md ← hướng dẫn Claude bước 1.2
│   ├── s2_dich_ko.md         ← prompt GPT giai đoạn 2
│   └── s2_claude_kiem_tra.md ← hướng dẫn Claude bước 2.4
├── scripts/
│   ├── _dang.py              ← phần riêng: gắn cờ, K1–K8, D1–D2, hiển thị Excel
│   ├── s0_chuan_bi.py        ← chuẩn hóa + gắn cờ + chọn pilot
│   ├── s1_gpt_chuyen.py      ← bước 1.1
│   ├── s1_claude_goi.py      ← chuẩn bị bước 1.2
│   ├── s1_kiem_tra.py        ← bước 1.3–1.4
│   ├── s1_chot.py            ← bước 1.5 (bạn duyệt)
│   ├── s2_dich.py            ← bước 2.1–2.3
│   ├── s2_claude_goi.py      ← chuẩn bị bước 2.4
│   ├── s2_kiem_tra.py        ← bước 2.5–2.6 + D4
│   ├── s3_xuat_ctv.py        ← giai đoạn 3
│   └── s9_bao_cao.py         ← số liệu so với tiêu chí đạt (mục 10)
└── output/                   ← samples/norm, json_vi/, json_ko/, claude/, reports/
```

Phần dùng chung đặt ở `../../pipeline_chung/`: `common.py`, `normalize.py` (furigana, gạch chân, HTML), `gpt_client.py`, `trang_thai.py`, `checks_chung.py`, `dich.py` (tách/ghép, câu cố định, bộ nhớ dịch), `claude_log.py`, `ctv_excel.py`, `schema_tools.py`, `glossary_ko.json` (thuật ngữ chung).

**Mặc định đang dùng cho 2 điểm chưa chốt** (đổi trong `config.json` → `chinh_sach`): lệch đáp án = lấy `dap_an_so` làm chuẩn + `[Bản gốc VI]`, chỉ CẢNH BÁO; Claude kiểm tra = tất cả câu.

## 13. Lịch sử thay đổi

| Ngày | Thay đổi |
|---|---|
| 2026-10-01 | Thêm kho `da_duyet/` + `s10_luu_da_duyet.py`; nhập 49 mẫu CTV đã chấp nhận (8 mẫu file 29/09 + 41 mẫu "Đạt" file 50 câu); bước 1.1/2.1 bỏ qua mẫu trong kho (`--ca-da-duyet` để chạy lại) |
| 2026-10-01 | Cách chia dạng v2 (mục 8): Dạng 1 = không sai định dạng, Dạng 2 = Claude sửa định dạng (`sua_dinh_dang`, ghi `[Đã sửa định dạng]`); cờ `nghi_noi_dung` (Claude chỉ gắn cờ, ghi rõ vị trí) và cờ `han_viet`; chỉ dịch câu không cờ; trạng thái `CHỜ_DUYỆT_NỘI_DUNG`, `CHỜ_XỬ_LÝ_HÁN_VIỆT`; chạy ở `output_v2/`; prompt `s1_claude_kiem_tra.md` viết lại (bản cũ `.v1.md`) |
| 2026-09-29 | Thêm D5 (còn âm Hán Việt → LỖI), bước so chữ bản gốc ↔ GPT và bước 2.7 phân loại 3 dạng (`s8_phan_loai.py`) |
| 2026-09-29 | Định nghĩa lại 3 dạng: 1 = GĐ1 không sửa lỗi bản gốc · 2 = GĐ1 có sửa lỗi bản gốc · 3 = GĐ2 còn âm Hán Việt (giữ `dang_gd1`); lỗi pipeline khác → chưa phân loại |
| 2026-09-29 | Mục 4: Claude được sửa lỗi có sẵn trong bản gốc (chính tả / cách đọc lẫn ①②③ / kiến thức) theo WF chung 2a-1, ghi `[Đã sửa bản gốc]`; `s1_kiem_tra` kiểm tra trung thành trên bản đã hoàn tác chỗ sửa bản gốc; `s8` và cột GĐ1 của Excel CTV tách "sửa lỗi GPT" / "sửa lỗi bản gốc" |
| 2026-09-27 (7) | Sau chạy thật 5 câu test: GPT đổi danh sách đánh số trong tham khảo thành "- " (2/5 câu) → sửa quy tắc 8 của prompt, thêm kiểm tra K9 |
| 2026-09-27 (6) | Chốt model: GPT = `gpt-5.6-sol` (reasoning_effort high) qua gateway; Claude = Opus 5.5 trong Cowork cho bước 1.2 và 2.4 (ghi trong config.json → claude, và vào file lý do `kiem_tra_boi`) |
| 2026-09-27 (5) | Rà soát script theo workflow: pilot đúng 30 câu (5 câu pilot cũ tính vào nhóm thông thường); tên cờ `the_tu_dien` thống nhất; câu `CẦN_SỬA_GĐ1` quay về bước 1.2 (không gọi lại GPT), bỏ dấu đã duyệt khi có `[Lỗi JSON VI]`; bước 2.1/2.4 tự nhận ra dữ liệu đã đổi để làm lại; ghi token giai đoạn 2; thêm `s9_bao_cao.py` |
| 2026-09-27 (4) | Rà soát prompt: bổ sung nhãn THÔNG TIN THAM KHẢO, bỏ tiền tố "1. いがい:", giữ phân tích của lựa chọn đúng nếu có, `question.reading` = null cho dạng ### (sửa schema), đưa câu cố định vào prompt dịch, quy tắc mức lịch sự của câu ví dụ, nhắc Claude xóa `_huong_dan`; sửa chính sách lệch đáp án = "loi" có hiệu lực; cờ thiếu gạch chân cho dạng ### |
| 2026-09-27 (3) | Viết code pipeline (pipeline_chung + scripts s0–s3 + prompts + config + glossary riêng); chạy s0 thật trên 1.872 câu; chạy thử giả lập toàn luồng; pilot gồm 35 câu (30 + 5 câu pilot cũ) |
| 2026-09-27 (2) | Thêm schema `vocab_kanji_reading.v2` (mục 2a) và `pipeline_chung/schema_tools.py`; bổ sung trường hợp thể từ điển dính vào cách đọc (63 câu), nhiều cách đọc; cờ `tu_dien_dinh_cach_doc`; sửa K4 |
| 2026-09-27 | Tạo workflow chi tiết dạng 01: GPT chuyển cả 1.872 câu; Python chỉ chuẩn hóa và gắn cờ; quy tắc tách phân tích bị dồn; kiểm tra K1–K8, D1–D4; kế hoạch pilot 30 câu |
