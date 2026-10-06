# Workflow chi tiết – Dạng 02: Thay đổi cách nói

> Phiên bản: 2026-10-05 (9) · Trạng thái: **nâng cấp theo cách làm hiện tại của dạng 01 (pipeline_v3) – xem đầu `HUONG_DAN_CHAY.md`; chuẩn bị chạy thử 10 mẫu.**
> File này chỉ ghi **phần riêng của dạng 02**. Các bước, quy ước và kiểm tra chung xem ở `../../workflow/workflow_tong_quat.md` ("WF chung"). Cách làm giống dạng 01 (`../01_tu_vung_cach_doc_kanji/workflow_chi_tiet.md`), chỉ khác các mục dưới đây.
> Số liệu khảo sát: `bao_cao/van_de_du_lieu.csv` (tạo bằng `scripts/khao_sat_du_lieu.py`).

## 1. Thông tin dạng

| Mục | Giá trị |
|---|---|
| Phần | Từ vựng |
| Tên trong sheet "Format giải thích" | Thay đổi cách nói (dòng 5) |
| Giá trị `dang_bai` trong CSV | `thay đổi cách nói` |
| Số câu | 1.028 (N1: 176, N2: 193, N3: 227, N4: 215, N5: 217) |
| Schema | `vocab_synonym.v2` (`schema/vocab_synonym.v2.json` + `.api.json`), theo đúng 4 phần của format |
| Ví dụ JSON mẫu | `../../explanation_schema/examples/02_tu_vung_thay_doi_cach_noi.json` |
| Dạng câu hỏi | Chọn từ / câu có nghĩa gần nhất với phần được hỏi |

**Dạng câu hỏi:** lựa chọn có thể là từ / cụm từ, cả câu viết lại, hoặc câu đề là định nghĩa. **Không phân loại kiểu câu** (phân loại tự động không chắc chắn – vd 1636 dễ bị xếp nhầm); mọi câu dùng chung một cách chuyển.

**Đánh dấu `{ }`** – theo WF chung mục 3a: **mọi đoạn in đậm hoặc gạch chân trong lời giải gốc → `{ }`**, ở bất kỳ phần nào; không lấy từ đề (chốt 2026-09-28).

| Trường hợp (quét bằng code, cột `giai_thich_vi`) | Số câu | Xử lý |
|---|---|---|
| Phần đầu lời giải có in đậm (`<b>`, `<strong>`, `<span style="font-weight: 700">` – 125 câu dùng kiểu span, vd 21956) | 969 | → `{ }` đúng chỗ, đúng dòng |
| Lời giải có `<u>` / span underline | 21 | → `{ }`. Đúng phần được hỏi: 1314, 3472, 3473, 19555, 53445, 54471; trong phân tích: 11879 `根`, 21990 `す`, 21993 `ず` |
| – gạch chân rác (`<u>.</u>`, rỗng): 2833, 3276, 3315, 3316, 3395, 10454, 10591, 10763, 19343, 19556 | 10 | Bỏ thẻ, ghi `danh_dau_rac.csv`. 19445 `<u>g</u>` là chữ → vẫn thành `{g}`, Claude xem và ghi `[Bản gốc VI]` |
| In đậm ở PHÂN TÍCH / THAM KHẢO | 4 | → `{ }` như mọi chỗ khác |
| Phần đầu lời giải không in đậm, không gạch chân | ~57 | Không có `{ }` ở phần đầu. Câu có gạch chân trong đề (vd 10456 – gạch chân nằm ở cột `cau_hoi`, không phải lời giải) gắn cờ `de_co_gach_chan_loi_giai_khong` |
| Một dòng có ≥ 2 đoạn đánh dấu (vd 3119) | 61 | Giữ đủ các cặp |
| Nhãn in đậm (`<b>PHÂN TÍCH:</b>`…) | – | Bỏ thẻ |

**Khuôn lời giải:** 100% văn bản `###`, 4 phần theo thứ tự: câu hỏi (câu / cách đọc / nghĩa) → PHÂN TÍCH → LỰA CHỌN ĐÚNG → THÔNG TIN THAM KHẢO. Dòng phân tích có mẫu: `i. <lựa chọn> (<cách đọc>): Nghĩa là "<nghĩa>". <phân tích>`.

**Vấn đề của bản gốc** (chi tiết + question_id trong `bao_cao/`):

| Vấn đề | Số câu | Xử lý |
|---|---|---|
| Đề đánh dấu từ đang hỏi theo 5 kiểu (`<u>`, `<span … underline>`, `<b>`, `｛ ｝`, `{ }`); lời giải đánh dấu bằng in đậm `<b>` | 206 span · 119 `｛｝` · 21 `<b>` · 6 `{}` | Chỉ dùng in đậm của lời giải → `{ }`; đề gửi GPT bỏ hết đánh dấu (mục 1, quy tắc `{ }`) |
| Đánh dấu chỉ có ở một nơi (đề hoặc lời giải) | 8 đề có gạch chân mà lời giải không in đậm | Không có `{ }` (chỉ theo lời giải); gắn cờ để nhóm biết |
| Không có dòng "Cách đọc:" | 321 | `question.reading` = `null` |
| Dòng phân tích dính liền nhau | 1 (19541) | GPT tách về đúng lựa chọn. (Khảo sát cũ đếm 41 – sai: 40 câu như 1445 thực ra xuống dòng bằng thẻ `<div>`, bước 0 đã tách đúng dòng) |
| Phần PHÂN TÍCH không đúng 4 dòng | 0 sau khi tách dòng đúng (khảo sát cũ: 34) | Kiểm tra K3; thiếu → `null` + `[Bản gốc VI]` |
| Thiếu dấu `###` (tiêu đề dính vào phần trước, vd 17164) | 26 | Bước 0 nhận tiêu đề cả khi thiếu `###` |
| Thiếu phần THAM KHẢO | 16 | `reference` = `null` |
| Lựa chọn viết cách chữ (N4–N5) / khoảng trắng gõ nhầm | 38 | So khớp bỏ khoảng trắng |
| Thứ tự phân tích lệch thứ tự lựa chọn của đề (vd 21956) | 2 | GPT đưa về đúng lựa chọn theo nội dung; `[Bản gốc VI]` |
| Thiếu cả PHÂN TÍCH và LỰA CHỌN ĐÚNG | 1 (22037) | `null` + `[Bản gốc VI]` |
| Có furigana (1 ruby hỏng – 53360) | 121 | `｜…《…》`, quy tắc riêng ở mục 3a |
| Câu "không tồn tại / không có nghĩa" | 57 | Câu cố định khi dịch |

## 2. Đầu vào

| Cột CSV | Dùng cho |
|---|---|
| `question_id`, `cau_con`, `cap_do` | Định danh |
| `cau_hoi` | Đề + vị trí đánh dấu từ đang hỏi → `question.ja` |
| `lua_chon_1–4` | `options[i].option_ja` (giữ cách viết của đề) |
| `dap_an_so` | `correct.index` |
| `giai_thich_vi` | Lời giải gốc (`###`) |

File dữ liệu: `data/02_tu_vung_thay_doi_cach_noi.csv`.

## 2a. JSON Schema – `vocab_synonym.v2`

File: `schema/vocab_synonym.v2.json` (Python kiểm tra) và `schema/vocab_synonym.v2.api.json` (gửi GPT, tạo bằng `pipeline_chung/schema_tools.py`, đã ĐẠT kiểm tra strict). Một schema cho cả 3 kiểu câu. **Mỗi trường ứng với một phần có trong format (sheet "Format giải thích", dòng 5) và chép nguyên một đoạn của lời giải gốc – không có trường suy ra thêm.**

```json
{
  "schema": "vocab_synonym.v2", "question_id": 0, "cau_con": 1,
  "question": {"ja": "田中さんは{単なる}友人です。", "reading": "たなかさんは{たんなる}ゆうじんです。",
               "meaning": {"vi": "Anh Tanaka chỉ là một người bạn {đơn thuần}."}},
  "analysis": {
    "intro": null,
    "options": [{"index": 1, "option_ja": "大切な", "reading": "たいせつな",
                 "analysis": {"vi": "Nghĩa là \"quan trọng\". Từ này mang ý nghĩa tích cực, …"}}, "… đủ 4 …"],
    "conclusion": null},
  "correct": {"index": 3, "option_ja": "ただの"},
  "reference": {"vi": "Một số từ đồng nghĩa với \"⟪単なる⟫\" (⟪たんなる⟫ - chỉ là, đơn thuần):\n1. ⟪ただの⟫ (⟪ただの⟫): …\n…"}
}
```

| Trường | Phần của format | Lấy từ | Không có thì |
|---|---|---|---|
| `question.ja` | 1 | Dòng câu đề của lời giải (có hoặc không có nhãn "Câu hỏi:"); `{ }` đúng chỗ in đậm của dòng đó | Luôn có |
| `question.reading` | 1 | Dòng "Cách đọc:" | `null` (321 câu) |
| `question.meaning.vi` | 1 | Dòng "Nghĩa:" | – |
| `analysis.options[i].option_ja` | 2 | Lựa chọn i của đề (nhãn có furigana thì theo nhãn) | Luôn đủ 4 |
| `analysis.options[i].reading` | 2 | Ngoặc cách đọc ở nhãn `i. X (đọc):` | `null` |
| `analysis.options[i].analysis.vi` | 2 | **Toàn bộ** phần sau dấu `:`, gồm cả "Nghĩa là …" | `null` |
| `analysis.intro` / `analysis.conclusion` | 2 | Đoạn trước dòng "1." (7 câu, vd 3315) / đoạn xuống dòng riêng sau dòng phân tích cuối (48 câu, vd 1513, 2610) | `null` |
| `correct.index`, `correct.option_ja` | 3 | `dap_an_so` của đề; `option_ja` giống hệt lựa chọn đó | – |
| `reference.vi` | 4 | **Nguyên cả** THÔNG TIN THAM KHẢO, giữ xuống dòng và cách đánh số | `null` (16 câu) |

| Quyết định | Lý do |
|---|---|
| Không có trường kiểu câu | Format không có; phân loại tự động không chắc chắn |
| Không tách "Nghĩa là "…"" ra trường riêng | Format viết liền một dòng; 3.876/4.074 dòng có "Nghĩa là" nhưng cách viết không đồng đều, tách dễ lệch / mất chữ |
| `reference` là một chuỗi, không tách `terms[]` | Format không có cấu trúc cố định; dữ liệu có nhiều mẫu dòng, 19 câu có đoạn kết sau danh sách, đánh số lặp (3040), mục dính dòng (1513) |
| Giữ `analysis.intro` / `conclusion` dù format không có | Là nội dung của bản gốc (55 câu); không có chỗ riêng thì GPT sẽ nhét vào lựa chọn 1 hoặc 4 |
| Thứ tự trường: PHÂN TÍCH → LỰA CHỌN ĐÚNG | Đúng thứ tự format (ngược dạng 01) |
| `options` đúng 4 (minItems = maxItems = 4) | Đề luôn 4 lựa chọn |

## 3. Quy tắc chuyển sang JSON (giai đoạn 1)

**Giai đoạn 0 – Python chuẩn bị** (không sửa nội dung):

1. Chuẩn hóa như WF chung (mục 3a: mọi in đậm / gạch chân của lời giải → `{ }`, bỏ nhãn in đậm, gộp đoạn liền nhau, bỏ đánh dấu rác). Đề: bỏ mọi đánh dấu (`<u>`, `<span … underline>`, `<b>`, `｛ ｝`, `{ }`) trước khi gửi GPT.
2. Đề gửi GPT **bỏ hết đánh dấu** (gạch chân / in đậm / `｛｝`), để GPT chỉ theo `{ }` của lời giải.
3. Gắn cờ (vào `trang_thai.csv`): `danh_dau_mot_noi`, `thieu_cach_doc`, `dong_pt_dinh_lien`, `so_dong_pt_khac_4`, `thieu_dau_phan_cach`, `thieu_tham_khao`, `thu_tu_pt_lech`, `lech_dap_an`, `thieu_phan`, `lua_chon_cach_chu`, `co_ket_luan`, `de_co_gach_chan_loi_giai_khong`, `nhieu_doan_in_dam`, `co_furigana`, `ruby_hong`.

**Đầu vào gửi GPT:** `question_id`, `cau_con`, `cap_do`, `de_bai` (câu hỏi đã bỏ đánh dấu, 4 lựa chọn, `dap_an_so`), `loi_giai_goc` (đã chuẩn hóa), `luu_y` (gợi ý từ cờ).

**Prompt:** `prompts/s1_chuyen_json.md`. Ánh xạ và quy tắc đầy đủ nằm trong prompt; tóm tắt:

| Lời giải gốc | Trường JSON |
|---|---|
| Dòng câu đề (có hoặc không có nhãn "Câu hỏi:") | `question.ja` |
| "Cách đọc:" | `question.reading`; không có → `null` |
| "Nghĩa:" | `question.meaning.vi` |
| PHÂN TÍCH – đoạn trước dòng "1." | `analysis.intro` |
| PHÂN TÍCH – dòng `i. X (đọc): nội dung` | `analysis.options[i]`: `reading` = đọc, `analysis` = toàn bộ nội dung |
| PHÂN TÍCH – đoạn xuống dòng riêng sau dòng cuối | `analysis.conclusion` |
| LỰA CHỌN ĐÚNG | `correct` (index theo `dap_an_so` của đề) |
| THÔNG TIN THAM KHẢO (toàn bộ) | `reference.vi` |

**Quy tắc `{ }`** (WF chung mục 3a): `{ }` trong lời giải đã chuẩn hóa (chỗ in đậm / gạch chân của bản gốc) nằm ở đâu thì chép nguyên vào đúng trường đó, đủ số cặp; chỗ không có thì không có. Không lấy từ đề, không tự đoán phần được hỏi.

**Quy tắc riêng khác:**

1. `options` đủ 4, thứ tự 1–4; `option_ja` lấy từ đề (nhãn có furigana thì theo nhãn). Phân tích nào nói về lựa chọn nào thì đặt vào lựa chọn đó (theo nội dung nhãn – vd 21956).
2. **Dòng dính liền** (`…".3. 新しい…`) → tách về đúng lựa chọn, bỏ nhãn `3. 新しい (…):` ở đầu.
3. **Không tách "Nghĩa là"**: `analysis` giữ nguyên cả dòng sau dấu `:`. Câu kết luận nằm cùng dòng với lựa chọn 4 (vd 54417 "Tóm lại, …") thuộc `analysis` lựa chọn 4; chỉ đoạn xuống dòng riêng mới vào `conclusion`.
4. `reading` của lựa chọn: chỉ ngoặc đứng ngay trước `:` của nhãn; ngoặc giữa câu (`大変(たいへん)でも`) là một phần lựa chọn. Không có → `null`; không lấy từ furigana.
5. `reference.vi`: chép nguyên cả phần, kể cả đánh số lặp / mục dính liền; phần tham khảo thiếu tiêu đề nhưng nằm sau LỰA CHỌN ĐÚNG (vd 2724) vẫn là `reference`.
6. Chép nguyên văn, không có thì `null`, `⟪ ⟫` theo WF chung; furigana theo mục 3a.

**Ví dụ đầy đủ** (trong prompt, đã kiểm tra khớp schema): A – mẫu sheet (lựa chọn là từ), B – 2610 (lựa chọn là câu, lời giải in đậm, có kết luận, thiếu tham khảo), C – 54417 (câu định nghĩa, không in đậm, furigana), D – 2260 (lựa chọn là câu, không in đậm).

## 3a. Furigana

Theo WF chung mục 8 (`｜chữ gốc《cách đọc》`, chép nguyên, không thêm, không bớt, không sửa), cộng các điểm riêng của dạng 02.

**Hiện trạng** (121 câu có furigana, hầu hết ở lời giải; đề chỉ 4 câu, lựa chọn 0 câu):

| Vị trí furigana trong lời giải | Số câu | Ví dụ (câu 53272) |
|---|---|---|
| Phần đầu (câu hỏi / cách đọc / nghĩa) | 110 | `Câu hỏi: ｜自分《じぶん》の｜尺度《しゃくど》を｜持《も》ったほうがいい.` |
| Nhãn lựa chọn ở đầu dòng phân tích | 82 | `1. ｜理想《りそう》: Nghĩa là 'lý tưởng'.…` |
| Trong nội dung phân tích | 52 | `…không đồng nghĩa với '｜尺度《しゃくど》' (thước đo).` |
| LỰA CHỌN ĐÚNG | 73 | `3. ｜基準《きじゅん》` |
| THÔNG TIN THAM KHẢO | 111 | `1. ｜無駄《むだ》な (むだな): Vô ích…` |

**Quy tắc:**

1. **Giữ furigana tại chỗ trong mọi trường**: `question.ja`, `option_ja`, và tiếng Nhật trong câu tiếng Việt – phân tích, kết luận, tham khảo (bên trong `⟪ ⟫`, vd `'⟪｜尺度《しゃくど》⟫'`).
2. `question.ja` lấy **từ dòng câu hỏi của lời giải** (có furigana); đề chỉ dùng để xác định vị trí `{ }`. Furigana nằm bên trong `{ }` (vd `{｜尺度《しゃくど》}`).
3. `option_ja`: lấy theo nhãn trong dòng phân tích nếu nhãn có furigana (`｜理想《りそう》`), nếu không thì lấy từ đề. Khi so với đề, Python bỏ furigana (chỉ so chữ gốc).
4. **Không chuyển furigana thành `reading`**: `reading` chỉ lấy khi bản gốc ghi cách đọc bằng chữ trong ngoặc ở nhãn (`不要 (ふよう)`); nhãn chỉ có furigana → `reading` = `null`. Lý do: giữ đúng bản gốc, không tự ghép cách đọc (giống quy tắc `question.reading` của dạng 01).
5. `correct.option_ja` = đúng `option_ja` của lựa chọn đó (cùng furigana). Furigana ở phần LỰA CHỌN ĐÚNG là bản lặp của nhãn lựa chọn nên không tính riêng.
6. Đề có gạch chân nằm **trong** thẻ ruby (vd 10661: `<ruby><span style="text-decoration-line: underline;">逆</span><rt>ぎゃく</rt></ruby>`) → bước 0 đổi gạch chân trước, `{ }` đưa ra ngoài furigana: `{｜逆《ぎゃく》}`.
7. Ruby hỏng (53360) → không đổi sang `《》`, giữ phần chữ, ghi `ruby_hong_ban_goc.csv`; không làm câu bị lỗi.
8. Excel cho CTV hiển thị `漢字《かな》` (ẩn `｜`); khi dịch, furigana nằm trong `⟪ ⟫` được chép nguyên.

## 4. Claude kiểm tra JSON (bước 1.2) – điểm riêng

Prompt: `prompts/s1_claude_kiem_tra.md`. Điểm riêng so với checklist chung:

- [ ] `question.ja` lấy từ dòng câu hỏi của lời giải; `question.reading` = `null` khi không có dòng "Cách đọc:".
- [ ] Mỗi phân tích nằm đúng lựa chọn của nó; câu có cờ `dong_pt_dinh_lien` / `thu_tu_pt_lech` xem kỹ.
- [ ] `analysis` giữ nguyên cả dòng (gồm "Nghĩa là …"); `intro` / `conclusion` đúng chỗ, không bị nhét vào lựa chọn.
- [ ] `{ }` đúng số cặp, đúng vị trí như chỗ in đậm / gạch chân của lời giải gốc ở mọi trường; chỗ bản gốc không đánh dấu thì không có.
- [ ] `reference.vi` đủ nguyên phần tham khảo, giữ đánh số và xuống dòng.
- [ ] Furigana giữ đúng chỗ như bản gốc; không bị chuyển thành `reading`, không tự thêm.
- [ ] Phân tích nghi sai kiến thức → không sửa, ghi `[Bản gốc VI]`.

## 5. Python kiểm tra JSON (bước 1.3) – kiểm tra thêm

| # | Kiểm tra | Mức |
|---|---|---|
| K1 | `analysis.options` đủ 4, `index` 1–4 đúng thứ tự | LỖI |
| K2 | `option_ja` trùng lựa chọn của đề (so sau khi bỏ khoảng trắng và furigana) | LỖI |
| K3 | Lựa chọn có phân tích trong bản gốc thì `analysis` không `null`; `analysis` không chứa mẫu `<số>. <lựa chọn khác>` (còn dính) | LỖI |
| K4 | `{ }`: kiểm tra chung số 5 (danh sách đoạn trong `{ }` trùng danh sách đoạn in đậm / gạch chân của lời giải, theo thứ tự) | LỖI |
| K5 | Đoạn `{ }` ở phần đầu lời giải nằm đúng trường (`question.ja` / `reading` / `meaning`) của dòng tương ứng | LỖI |
| K6 | `correct.index` = `dap_an_so`; `correct.option_ja` = `option_ja` của lựa chọn đó | LỖI |
| K7 | `reference.vi` giữ đủ số dòng và số dòng đánh số như phần THAM KHẢO của bản gốc | LỖI |
| K8 | `options[].reading` chỉ gồm kana (cho phép khoảng trắng, dấu câu) | CẢNH BÁO |
| K9 | Độ phủ chữ Việt tính riêng cho từng lựa chọn: `analysis` phủ đủ chữ của dòng phân tích gốc | LỖI |
| K10 | Bản gốc có đoạn trước dòng "1." / sau dòng cuối (cờ `co_ket_luan`) thì `intro` / `conclusion` không `null` | CẢNH BÁO |
| K11 | Furigana: cặp (chữ gốc, cách đọc) trong JSON trùng bản gốc (kiểm tra chung số 7), **không tính** phần LỰA CHỌN ĐÚNG của bản gốc và `correct.option_ja` của JSON (bản lặp – mục 3a quy tắc 5) | LỖI |

## 6. Quy tắc dịch riêng (giai đoạn 2)

Prompt: `prompts/s2_dich_ko.md`.

**Trường cần dịch:** 6–8 trường mỗi câu (`question.meaning`, 4 × `analysis`, `reference`, và `intro` / `conclusion` nếu có) – ít hơn bản đề xuất cũ nên không lo giới hạn số trường của schema strict.

| Trường | Văn phong |
|---|---|
| `question.meaning` | Theo mức lịch sự của câu tiếng Nhật (thể thường → -다; です/ます → -습니다) |
| `analysis.options[].analysis`, `analysis.intro`, `analysis.conclusion` | -습니다/-ㅂ니다; câu "Nghĩa là "N"." → `"N"이라는 뜻입니다.` |
| `reference` | Câu văn -습니다; phần nghĩa ngắn trong danh sách từ giữ dạng cụm từ như tiếng Việt |

**Câu cố định** (bổ sung vào `glossary_ko.json` riêng của dạng, CTV duyệt): "Không đồng nghĩa." (25 lần), "Không đồng nghĩa với câu gốc." (11), "Không đồng nghĩa với câu hỏi." (8), "Đây là lựa chọn đúng." (26), "Đây là lựa chọn đồng nghĩa chính xác." (7). **Mẫu câu:** "Một số từ (cụm từ) đồng nghĩa (hoặc) gần nghĩa với "X" (có thể) bao gồm:" – ≥ 5 cách viết. **Thuật ngữ:** đồng nghĩa → 동의어 / 같은 의미, gần nghĩa → 유의어 / 비슷한 의미, câu gốc → 원래 문장.

## 7. Claude kiểm tra bản dịch (bước 2.4) – điểm riêng

Prompt: `prompts/s2_claude_kiem_tra.md`.

- [ ] Phần "Nghĩa là "…"" trong mỗi phân tích dịch đúng nghĩa của **lựa chọn tiếng Nhật đó**, đúng với ngữ cảnh câu đề.
- [ ] Phân tích và kết luận giữ đúng ý đồng nghĩa / không đồng nghĩa như tiếng Việt, khớp đáp án.
- [ ] `question.meaning`: `{ }` chỉ có khi tiếng Việt có, bọc đúng phần dịch của phần được hỏi.
- [ ] `reference` đủ dòng, giữ đánh số; thuật ngữ đồng nghĩa / gần nghĩa nhất quán trong toàn lời giải và giữa các câu.

## 8. Python kiểm tra bản dịch (bước 2.5) – kiểm tra thêm

| # | Kiểm tra | Mức |
|---|---|---|
| D1 | Câu cố định dịch đúng bảng thuật ngữ | LỖI |
| D2 | `reference.ko` giữ đủ số dòng và số dòng đánh số như `reference.vi` | LỖI |
| D3 | `{ }` trong `question.meaning.ko` đúng số cặp như tiếng Việt | LỖI (kiểm tra chung) |
| D4 | Nhất quán giữa các câu (cùng vi, khác ko) | CẢNH BÁO (tổng hợp) |

## 9. Hiển thị trong Excel cho CTV

Dựng lại đúng thứ tự format: câu đề / cách đọc / nghĩa → PHÂN TÍCH (`intro`, 4 dòng `i. option_ja (reading): analysis` – ghép lại nhãn từ `option_ja` + `reading`, `conclusion`) → LỰA CHỌN ĐÚNG (`index. option_ja`) → THÔNG TIN THAM KHẢO. `{ }` hiển thị in đậm (đúng chỗ bản gốc in đậm / gạch chân); furigana `漢字《かな》` (ẩn `｜`).

## 10. Mẫu test và tiêu chí đạt

**Pilot: 30 câu** (seed cố định):

| Nhóm | Số câu |
|---|---|
| Thông thường, trải đều N1–N5 (lựa chọn là từ) | 8 |
| Lựa chọn là câu (2 có in đậm – gồm 2610; 2 không in đậm) + 1636 | 5 |
| Câu định nghĩa | 2 |
| Nhiều đoạn in đậm trên một dòng (vd 3119) / đề có gạch chân mà lời giải không in đậm | 2 |
| In đậm lỗi định dạng ở PHÂN TÍCH / THAM KHẢO | 2 |
| `dong_pt_dinh_lien` / `so_dong_pt_khac_4` / `thu_tu_pt_lech` | 4 |
| `thieu_dau_phan_cach` / `thieu_tham_khao` | 3 |
| Có furigana (ở nhãn lựa chọn, tham khảo; 1 câu gạch chân trong ruby – 10661) | 3 |
| Câu pilot cũ (so với bản Opus) | 1 |

**Tiêu chí chạy toàn bộ:** như dạng 01 – GĐ1 ≥ 90% ĐẠT Python, 100% câu dính dòng được tách đúng, không lỗi nghiêm trọng; GĐ2 ≥ 90% ĐẠT Python, ≥ 80% CTV chấm "Đạt".

## 11. Việc cần chốt

- [x] ~~Tách "Nghĩa là" ra trường riêng~~ → chốt 2026-09-28: không tách (schema theo đúng format).
- [x] ~~Schema~~ → chốt `vocab_synonym.v2` (mục 2a).
- [ ] Mở rộng `pipeline_chung/normalize.py`: span underline, `<b>` ở phần đầu lời giải → `{ }` (gộp đoạn liền nhau, bỏ nhãn in đậm, bỏ in đậm ở phần khác), bỏ đánh dấu trong đề gửi GPT.
- [ ] CTV duyệt câu cố định và thuật ngữ đồng nghĩa / gần nghĩa.
- [ ] Các điểm chung còn mở từ dạng 01: âm Hán Việt, phạm vi Claude kiểm tra khi chạy toàn bộ.

## 12. Cấu trúc thư mục dự kiến

```
02_tu_vung_thay_doi_cach_noi/
├── README.md, workflow_chi_tiet.md
├── config.json, glossary_ko.json
├── data/                     ← 02_tu_vung_thay_doi_cach_noi.csv
├── bao_cao/                  ← van_de_du_lieu.csv, van_de_theo_cau.csv (khảo sát)
├── schema/                   ← vocab_synonym.v2.json (+ .api.json)
├── prompts/                  ← s1_chuyen_json.md, s1_claude_kiem_tra.md, s2_dich_ko.md, s2_claude_kiem_tra.md
├── scripts/                  ← khao_sat_du_lieu.py, _dang.py, s0…s3, s9 (cùng khung dạng 01)
└── output/
```

## 13. Lịch sử thay đổi

| Ngày | Thay đổi |
|---|---|
| 2026-09-28 (8) | Viết script pipeline (`scripts/_dang.py`, s0–s3, s9; dùng chung `pipeline_chung/`), `config.json`, `glossary_ko.json` (nháp), `HUONG_DAN_CHAY.md`, file test 5 câu; chạy bước 0 cho 1.028 câu. `normalize.py` thêm chế độ đánh dấu `u+b` (mục 3a) và nhận `<div>`/`<p>` mở đầu là xuống dòng → số dòng dính liền thật chỉ còn 1 |
| 2026-09-28 (7) | Theo quy tắc chung mới (WF chung mục 3a): in đậm **và** gạch chân trong lời giải đều → `{ }`, ở mọi phần; thống kê 21 câu có `<u>` trong lời giải (10 câu gạch chân rác); cập nhật K4–K5, prompt |
| 2026-09-28 (6) | Đếm lại in đậm (bản trước đếm sai do biểu thức `<b…>` khớp nhầm `<br>` và bỏ sót `<span style="font-weight: 700">`): 969 có / 59 không; chỉ 8 câu đề có gạch chân mà lời giải không in đậm; 61 câu nhiều đoạn in đậm; 4 câu in đậm ngoài phần đầu |
| 2026-09-28 (5) | **Bỏ phân loại kiểu câu** (`kieu_cau`, `co_danh_dau`) vì tự động không chắc chắn; `{ }` chỉ theo chỗ in đậm ở phần đầu lời giải gốc (không lấy từ đề, cho phép nhiều cặp mỗi dòng); đề gửi GPT bỏ đánh dấu; sửa K4–K5, prompt, schema; xóa `kieu_cau.csv`, `chon_cau_co_danh_dau.csv` |
| 2026-09-28 (4) | Sửa cách xác định `kieu_cau` (theo việc lựa chọn có lặp lại ngữ cảnh trước chỗ đánh dấu, không theo độ dài – 1636 là `thay_tu`); số câu mới 762 / 238 / 28; `co_danh_dau` tính cả dòng nghĩa; xuất `bao_cao/kieu_cau.csv`, `chon_cau_co_danh_dau.csv` |
| 2026-09-28 (3) | Chốt schema `vocab_synonym.v2` theo đúng 4 phần của format (không `kieu_cau` trong JSON, không tách "Nghĩa là", `reference` một chuỗi, giữ `analysis.intro/conclusion`); tạo file schema + bản API (ĐẠT strict); thêm cờ `co_danh_dau` quyết định `{ }` (chon_cau vẫn có thể có đánh dấu – 282/304); tạo 4 prompt; cập nhật mục 1, 2a, 3, 3a, 4–7, 9–11 |
| 2026-09-28 (2) | Thêm mục 3a – quy tắc furigana riêng dạng 02 (giữ tại chỗ, không chuyển thành reading, LỰA CHỌN ĐÚNG là bản lặp); kiểm tra K11; mẫu "Nghĩa là" nhận cả ngoặc đơn |
| 2026-09-28 | Tạo workflow chi tiết dạng 02 từ khảo sát dữ liệu: 3 kiểu câu (`kieu_cau`), schema `vocab_synonym.v2` (dự kiến) thêm `analysis_intro/conclusion`, chuẩn hóa 5 kiểu đánh dấu từ đang hỏi, kiểm tra K1–K10, D1–D4 |
| 2026-10-05 (9) | Nâng cấp theo dạng 01/pipeline_v3: cách chia v2 (sửa định dạng / cờ nghi sai nội dung / cờ Hán Việt, chặn dịch câu có cờ), kho `da_duyet/`, Excel CTV tiếng Nhật (`s3b`), `s10_luu_da_duyet`; GĐ2 dịch `question.meaning` trực tiếp từ tiếng Nhật, câu 'Nghĩa là' của lựa chọn theo lựa chọn tiếng Nhật (`scripts/_dich_v3.py`); prompt GĐ1 v3 thêm quy tắc 3c (chung) + 3d (riêng dạng 02); kiểm tra D6/D7; chạy thử 10 mẫu thay cho pilot 30 |
