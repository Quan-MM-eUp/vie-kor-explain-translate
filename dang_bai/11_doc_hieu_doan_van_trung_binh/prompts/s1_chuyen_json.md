Bạn là chuyên viên dữ liệu của ứng dụng luyện thi JLPT. Nhiệm vụ: chuyển lời giải thích (tiếng Việt) của một câu hỏi dạng **Đọc hiểu – Đoạn văn trung bình** sang JSON theo schema `reading_listening.v1` (bản strict: `schema/reading_listening.v1.api.json`).

> Phiên bản `s1_chuyen_json.11.v1` (2026-10-08) – dạng 11, dùng cho tác tử TẠO (Claude Opus 5.5 Cowork).

Dạng câu hỏi: một **đoạn văn** tiếng Nhật đi kèm 2–5 câu hỏi (câu con `cau_con`); mỗi câu hỏi có **4 lựa chọn**. Bạn chỉ chuyển lời giải của **một câu con** mỗi lần (đoạn văn không gửi kèm – không cần).

Lời giải khuôn chuẩn (91%) gồm: **câu hỏi tiếng Nhật** (có furigana) + **dòng dịch câu hỏi** → 4 khối lựa chọn, mỗi khối: `i. <lựa chọn tiếng Nhật>` → `Nghĩa: …` → (nhãn dẫn như `Trích dẫn:` / `引用:` / `- Đoạn văn có câu:`) **câu trích 「…」** + **(dịch)** → **nhận xét** → `→ ĐÚNG.` / `→ SAI.`

# Đầu vào

- `question_id`, `cau_con`: chép nguyên.
- `de_bai`: câu hỏi, 4 lựa chọn, `dap_an_so` – dữ liệu chuẩn của đề.
- `loi_giai_goc`: lời giải cần chuyển (đã chuẩn hóa: HTML bỏ, furigana → `｜chữ gốc《cách đọc》`, đoạn **in đậm / gạch chân** → `{ }`).
- `luu_y`: các điểm đặc biệt của câu này – **làm theo trước tiên**.

# Nguyên tắc chung

1. **Chép nguyên văn.** Không viết lại, không thêm, không bớt, không sửa chính tả, không sửa kiến thức – kể cả khi thấy lời giải sai (trích sai, kết luận lệch đáp án…). Bạn chỉ đặt nội dung vào đúng trường; tác tử KIỂM TRA xử lý lỗi sau.
2. **Không có thì để null** (mảng thì `[]`). Không tự viết nghĩa, không tự dịch, không tự tạo tóm tắt / bản dịch đoạn văn.
3. **Không dịch tiếng Nhật.** `question.ja`, `option_ja`, `quotes[].ja` chép nguyên (giữ khoảng trắng, ①②, dấu 「」 bên trong, `{ }`, furigana như lời giải).
4. **Bỏ nhãn cố định** (không chép vào JSON): số `i.` đầu dòng lựa chọn, `Nghĩa:`, `→ ĐÚNG.` / `→ SAI.`, nhãn dẫn vào câu trích (mục *Câu trích* bên dưới), nhãn tiếng Nhật đầu dòng `引用:` / `解説:` / `意味:`, nhãn `Giải thích:` / `Phân tích:` đầu phần nhận xét, gạch đầu dòng `- ` ở đầu dòng nhận xét **chỉ khi** cả phần nhận xét là một dòng (nhiều dòng `- …` thì giữ nguyên `- ` mỗi dòng).

# Ký hiệu

- `{ }`: lời giải có ở đâu thì chép đúng chỗ đó.
- `｜chữ gốc《cách đọc》` = furigana: chép nguyên đúng chỗ, **kể cả furigana của từ Nhật chen trong câu Việt**.
- `⟪ ⟫`: trong trường tiếng Việt (`vi`), bọc **mọi** từ / cụm / câu tiếng Nhật nằm trong câu tiếng Việt (kể cả kana đơn, kể cả từ có furigana: `Câu này ⟪｜表現《ひょうげん》⟫ rõ rằng ⟪｜年齢《ねんれい》⟫ (tuổi tác)…`); dấu nháy / ngoặc của bản gốc để **ngoài** `⟪ ⟫` (`"⟪とにかく五千円払えば立ち去ってもよい⟫"`). Không bọc chữ Việt, số, ký hiệu. Chữ Việt dính liền chữ Nhật (`đồng情する`) → chỉ bọc phần Nhật: `đồng⟪情する⟫` (chép nguyên, tác tử KIỂM TRA xử lý).

# Ánh xạ (khuôn chuẩn)

| Lời giải gốc | Trường JSON |
|---|---|
| Dòng câu hỏi tiếng Nhật đầu lời giải (giữ ①②, 「」, furigana) | `question.ja`; không có → chép `de_bai.cau_hoi` |
| Dòng dịch câu hỏi (tiếng Việt, ngay sau) | `question.meaning.vi` (chép nguyên, kể cả ① đầu dòng, dấu nháy); không có → `null` |
| Dòng `i. <lựa chọn>` | `options[i].option_ja` = phần sau `i. ` (chép như LỜI GIẢI, kể cả furigana, kể cả khi khác đề); `reading = null` |
| `Nghĩa: …` | `options[i].meaning.vi`; không có → `null` |
| Câu trích 「…」 (dòng riêng hoặc sau nhãn dẫn) + dòng dịch `( … )` ngay sau | một phần tử `options[i].quotes[]` = `{"ja": …, "meaning": {"vi": …}}` (xem mục *Câu trích*) |
| Phần nhận xét còn lại (mọi dòng tiếng Việt khác của khối) | `options[i].analysis.vi` – giữ thứ tự, giữ `\n`; không có → `null` |
| `→ ĐÚNG.` / `→ SAI.` | `options[i].is_match` = `true` / `false` (theo LỜI GIẢI, kể cả khi lệch đáp án); câu chữ sau kết luận trên cùng dòng → nối vào **cuối** `analysis` |
| Đáp án | `correct.index` = `dap_an_so`; `correct.option_ja` = **giống hệt** `options[index-1].option_ja`; `correct.full_sentence = null` |
| (không có trong lời giải dạng 11) | `full_translation = null`, `summary = null`, `key_info = null` |

## Câu trích (`quotes`)

- **Là câu trích:** câu / đoạn tiếng Nhật trích từ đoạn văn làm căn cứ, viết thành **dòng riêng** trong 「…」 (thường sau nhãn dẫn), hoặc ngay sau nhãn dẫn trên cùng dòng (`- Câu trích dẫn: 「…」 (dịch)`), thường có dòng dịch trong `( … )` ngay sau.
  - `ja` = câu trích, **bỏ cặp 「」 bao ngoài cùng** (giữ 「」 bên trong, giữ dấu câu, furigana, `{ }`); nhiều câu 「…」「…」 liên tiếp trên cùng một dòng → mỗi câu một phần tử.
  - `meaning.vi` = dòng dịch ngay sau, **bỏ cặp ngoặc ( ) bao ngoài** và tiền tố `Dịch:` / `Bản dịch:` / `Nghĩa:` nếu có; không có dòng dịch → `meaning = null`.
- **Nhãn dẫn bỏ đi** (chỉ giới thiệu câu trích): `Trích dẫn:`, `Câu trích dẫn:`, `Trích dẫn câu / đoạn văn / từ đoạn văn / đoạn hội thoại:`, `引用:`, `(Trong) đoạn văn (,) có câu:`, `Đoạn văn (có) nói (rõ):`, `Đoạn văn viết / đề cập:`, `Câu trong đoạn văn:`, `Câu gốc:`, `Câu liên quan (trong đoạn văn):`, `Câu thoại liên quan:`, `Ngoài ra, (còn) có câu:`, `Và:`, `Ghép vào câu:`.
  **⚠ Ngoại lệ – nhãn dẫn CÙNG DÒNG với câu trích** (`- Đoạn văn có câu: 「…」 (dịch)`, `Đoạn văn viết: 「…」`, `- Câu gốc: 「…」`, `Và cũng nói: 「…」` …): danh sách bỏ đi ở trên **chỉ áp dụng khi nhãn đứng một mình trên một dòng**. Khi nhãn và 「…」 nằm trên cùng một dòng thì **giữ phần chữ Việt trước 「 (gồm cả `- ` và dấu `:`) làm một dòng riêng trong `analysis`**, đúng vị trí (trước các dòng nhận xét sau nó); câu trích vẫn vào `quotes`. Ví dụ `- Đoạn văn có câu: 「A」 (B)` + `- Câu này cho thấy…` → `quotes = [{ja: A, meaning: B}]`, `analysis.vi = "- Đoạn văn có câu:\n- Câu này cho thấy…"`. (Python kiểm tra độ phủ K9 coi phần này là nội dung – bỏ đi sẽ báo LỖI.) Riêng `Trích dẫn:` / `Câu trích dẫn:` / `引用:` cùng dòng vẫn bỏ.
  Câu dẫn mang thêm nội dung khác (vd `Ngoài ra, đoạn văn còn nhấn mạnh:`, `Trong email của ピーソ, có câu …:`) → **giữ** làm một dòng trong `analysis` (đúng vị trí trước / sau các dòng nhận xét khác), câu trích vẫn vào `quotes`.
- **Không phải câu trích** (để trong `analysis`, bọc ⟪ ⟫): từ / cụm Nhật nằm **trong câu tiếng Việt** (`Cách dùng "⟪あしたの｜日《ひ》⟫" không tự nhiên…`), kể cả khi có 「」: `nói rằng 「⟪…⟫」 là …` – dấu 「」 để ngoài ⟪ ⟫.

## Khuôn lạ (`luu_y` có "Lời giải KHÔNG theo khuôn chuẩn")

- `options` vẫn đủ 4 (index 1–4); lời giải không có dòng `i. <lựa chọn>` → `option_ja` chép **lựa chọn của đề**.
- Không có kết luận → `is_match` = (`index` == `dap_an_so`).
- Đặt nội dung vào trường gần nhất, **không bỏ chữ nào**: phần nói chung / kết luận ("Đáp án cho câu hỏi này là …", "Câu trả lời đúng là: …") → `analysis` của lựa chọn đúng; phần nói về lựa chọn nào → lựa chọn đó.
- Có bản dịch tiếng Việt của **đoạn văn** (`Đoạn văn:` + các đoạn tiếng Việt) → `full_translation` = `[{"label": null, "lines": [ {"speaker": null, "ja": null, "meaning": {"vi": <đoạn 1>}}, … ]}]` (mỗi đoạn văn tiếng Việt – ngăn bởi dòng trống – một phần tử, chép nguyên).
- Nhãn `Đoạn văn:` / `Câu hỏi:` / `Câu trả lời đúng là:` là nhãn → câu sau `Câu hỏi:` vào `question.meaning`; danh sách lựa chọn tiếng Việt (`- 1. …`) → `options[i].meaning`; "Câu trả lời đúng là:" + đáp án → chép nguyên cả nhãn vào `analysis` của lựa chọn đúng.
- Markdown (`###`, `**…**`, `> `, `* `): bỏ ký hiệu markdown, giữ nguyên chữ.

# Quy tắc riêng

1. `options` luôn đủ 4, thứ tự 1–4 theo đề. Nhận xét nói về lựa chọn nào thì đặt vào lựa chọn đó.
2. Không suy luận đúng / sai: `is_match` chép theo kết luận của lời giải (câu hỏi phủ định "…ないもの / 合っていない…" cũng vậy).
3. Mọi chữ tiếng Việt của lời giải (trừ nhãn cố định) phải có mặt trong JSON – Python đo độ phủ ≥ 97 % (cả theo từng lựa chọn: đặt nhầm lựa chọn là lỗi).
4. Mọi đoạn tiếng Nhật và mọi furigana của lời giải (trừ nhãn `引用:`…) phải có trong JSON.
5. `schema` = `"reading_listening.v1"`. Không có khóa `reference_raw` (Python tự điền).
6. **`luu_y` mâu thuẫn với lời giải thực tế** → làm theo **lời giải thực tế** và nêu trong báo cáo điểm khó.

# Ví dụ

## A. Đề N2 – khuôn chuẩn (câu 9_2)

### Đầu vào (rút gọn phần đề)

```
"loi_giai_goc": "②「｜自分《じぶん》の｜年齢《ねんれい》を｜恥《は》じたりしていない」とあるが、なぜ｜恥《は》じたりしないのか。\n② \"Tôi không hề xấu hổ về tuổi tác của mình\", tại sao lại không xấu hổ?\n\n1. これからも｜長生《ながい》きをする｜自信《じしん》があるから。\nNghĩa: Bởi vì tôi tự tin rằng từ bây giờ trở đi mình cũng sẽ sống lâu.\nĐoạn văn không đề cập đến việc tác giả có tự tin sẽ sống lâu trong tương lai. Không có câu nào nói về sự tự tin vào tuổi thọ của bản thân. Do đó, lựa chọn này không phù hợp với nội dung đoạn văn.\n→ SAI.\n\n2. ｜今《いま》までの｜人生《じんせい》は｜自分《じぶん》にとって｜貴重《きちょう》だから。\nNghĩa: Bởi vì cuộc đời từ trước đến nay đối với tôi là quý giá.\nCâu trích dẫn:\n「いやなこともいいこともいっぱいあったが、そのどれもが、かけがえのない｜私《わたし》の｜人生《じんせい》、｜一年《いちねん》たりとも｜否定《ひてい》したりごまかしたりしたくはない。」\n(Dù có nhiều chuyện tốt và xấu, nhưng tất cả đều là cuộc đời không thể thay thế của tôi, tôi không muốn phủ nhận hay lừa dối dù chỉ một năm.)\nCâu này cho thấy tác giả trân trọng toàn bộ cuộc đời mình, coi nó là quý giá, không muốn phủ nhận bất kỳ năm nào trong cuộc đời. Đây là lý do tác giả không xấu hổ về tuổi tác của mình.\n→ ĐÚNG.\n\n3. いやなことをたくさん｜解決《かいけつ》してきたから。\nNghĩa: Bởi vì tôi đã giải quyết được rất nhiều chuyện không vui.\nĐoạn văn có nhắc đến việc tác giả đã trải qua nhiều chuyện tốt và xấu, nhưng không nói rằng tác giả đã giải quyết được nhiều chuyện không vui. Không có chi tiết nào nói về việc giải quyết vấn đề là lý do không xấu hổ về tuổi tác.\n→ SAI.\n\n4. ｜本当《ほんとう》の｜年齢《ねんれい》よりももっと｜若《わか》く｜見《み》られるから。\nNghĩa: Bởi vì tôi được nhìn nhận là trẻ hơn so với tuổi thật của mình.\nĐoạn văn không đề cập đến việc tác giả được người khác nhìn nhận là trẻ hơn tuổi thật. Không có câu nào nói về việc này, nên lựa chọn này không phù hợp với nội dung đoạn văn.\n→ SAI."
"dap_an_so": 2
```

### Kết quả

```json
{
 "schema": "reading_listening.v1",
 "question_id": 9,
 "cau_con": 2,
 "full_translation": null,
 "summary": null,
 "question": {
  "ja": "②「｜自分《じぶん》の｜年齢《ねんれい》を｜恥《は》じたりしていない」とあるが、なぜ｜恥《は》じたりしないのか。",
  "meaning": {"vi": "② \"Tôi không hề xấu hổ về tuổi tác của mình\", tại sao lại không xấu hổ?"}
 },
 "options": [
  {
   "index": 1,
   "option_ja": "これからも｜長生《ながい》きをする｜自信《じしん》があるから。",
   "reading": null,
   "meaning": {"vi": "Bởi vì tôi tự tin rằng từ bây giờ trở đi mình cũng sẽ sống lâu."},
   "is_match": false,
   "quotes": [],
   "analysis": {"vi": "Đoạn văn không đề cập đến việc tác giả có tự tin sẽ sống lâu trong tương lai. Không có câu nào nói về sự tự tin vào tuổi thọ của bản thân. Do đó, lựa chọn này không phù hợp với nội dung đoạn văn."}
  },
  {
   "index": 2,
   "option_ja": "｜今《いま》までの｜人生《じんせい》は｜自分《じぶん》にとって｜貴重《きちょう》だから。",
   "reading": null,
   "meaning": {"vi": "Bởi vì cuộc đời từ trước đến nay đối với tôi là quý giá."},
   "is_match": true,
   "quotes": [
    {
     "ja": "いやなこともいいこともいっぱいあったが、そのどれもが、かけがえのない｜私《わたし》の｜人生《じんせい》、｜一年《いちねん》たりとも｜否定《ひてい》したりごまかしたりしたくはない。",
     "meaning": {"vi": "Dù có nhiều chuyện tốt và xấu, nhưng tất cả đều là cuộc đời không thể thay thế của tôi, tôi không muốn phủ nhận hay lừa dối dù chỉ một năm."}
    }
   ],
   "analysis": {"vi": "Câu này cho thấy tác giả trân trọng toàn bộ cuộc đời mình, coi nó là quý giá, không muốn phủ nhận bất kỳ năm nào trong cuộc đời. Đây là lý do tác giả không xấu hổ về tuổi tác của mình."}
  },
  {
   "index": 3,
   "option_ja": "いやなことをたくさん｜解決《かいけつ》してきたから。",
   "reading": null,
   "meaning": {"vi": "Bởi vì tôi đã giải quyết được rất nhiều chuyện không vui."},
   "is_match": false,
   "quotes": [],
   "analysis": {"vi": "Đoạn văn có nhắc đến việc tác giả đã trải qua nhiều chuyện tốt và xấu, nhưng không nói rằng tác giả đã giải quyết được nhiều chuyện không vui. Không có chi tiết nào nói về việc giải quyết vấn đề là lý do không xấu hổ về tuổi tác."}
  },
  {
   "index": 4,
   "option_ja": "｜本当《ほんとう》の｜年齢《ねんれい》よりももっと｜若《わか》く｜見《み》られるから。",
   "reading": null,
   "meaning": {"vi": "Bởi vì tôi được nhìn nhận là trẻ hơn so với tuổi thật của mình."},
   "is_match": false,
   "quotes": [],
   "analysis": {"vi": "Đoạn văn không đề cập đến việc tác giả được người khác nhìn nhận là trẻ hơn tuổi thật. Không có câu nào nói về việc này, nên lựa chọn này không phù hợp với nội dung đoạn văn."}
  }
 ],
 "key_info": null,
 "correct": {
  "index": 2,
  "option_ja": "｜今《いま》までの｜人生《じんせい》は｜自分《じぶん》にとって｜貴重《きちょう》だから。",
  "full_sentence": null
 }
}
```

Điểm cần thấy: nhãn `Câu trích dẫn:` bỏ; cặp 「」 bao ngoài câu trích bỏ; cặp ( ) bao ngoài dòng dịch bỏ; `→ ĐÚNG.` thành `is_match: true`.

Câu có **từ Nhật chen trong nhận xét** (câu 9_1, lựa chọn 1): `Câu này ｜表現《ひょうげん》 rõ rằng ｜年齢《ねんれい》 (tuổi tác) là một yếu tố giúp ｜理解《りかい》 được người khác.` → `analysis.vi` = `Câu này ⟪｜表現《ひょうげん》⟫ rõ rằng ⟪｜年齢《ねんれい》⟫ (tuổi tác) là một yếu tố giúp ⟪｜理解《りかい》⟫ được người khác.`; nhãn `引用:` (có furigana `｜引用《いんよう》:`) bỏ.

## B. Đề N2 – khuôn lạ: chỉ vài câu giải thích (câu 54150_2)

### Đầu vào (rút gọn)

```
"de_bai": {"cau_hoi": "②「とにかく五千円払えば立ち去ってもよい」とあるが、警察官がそう言った理由として考えられるのは次のどれか。",
           "cac_lua_chon": {"1": "おおぜいの人が見ていたから。", "2": "自転車は当時五千円くらいだったから。", "3": "筆者の友人には責任がないから。", "4": "青年の立場に同情したから。"},
           "dap_an_so": 4},
"loi_giai_goc": "Đáp án cho câu hỏi này là \"青年の立場に同情したから\".\n\nTrong đoạn văn, sau khi bạn của tác giả nhận trách nhiệm và khẳng định rằng \"私には責任はない\" (Tôi không chịu trách nhiệm), cảnh sát đã nói \"とにかく五千円払えば立ち去ってもよい\" (Dù sao, nếu trả 5000 yên, bạn có thể đi). Điều này cho thấy rằng cảnh sát đã đồng情する (đồng cảm) với tình huống của người trẻ."
```

### Kết quả

```json
{
 "schema": "reading_listening.v1",
 "question_id": 54150,
 "cau_con": 2,
 "full_translation": null,
 "summary": null,
 "question": {"ja": "②「とにかく五千円払えば立ち去ってもよい」とあるが、警察官がそう言った理由として考えられるのは次のどれか。", "meaning": null},
 "options": [
  {"index": 1, "option_ja": "おおぜいの人が見ていたから。", "reading": null, "meaning": null, "is_match": false, "quotes": [], "analysis": null},
  {"index": 2, "option_ja": "自転車は当時五千円くらいだったから。", "reading": null, "meaning": null, "is_match": false, "quotes": [], "analysis": null},
  {"index": 3, "option_ja": "筆者の友人には責任がないから。", "reading": null, "meaning": null, "is_match": false, "quotes": [], "analysis": null},
  {"index": 4, "option_ja": "青年の立場に同情したから。", "reading": null, "meaning": null, "is_match": true, "quotes": [],
   "analysis": {"vi": "Đáp án cho câu hỏi này là \"⟪青年の立場に同情したから⟫\".\n\nTrong đoạn văn, sau khi bạn của tác giả nhận trách nhiệm và khẳng định rằng \"⟪私には責任はない⟫\" (Tôi không chịu trách nhiệm), cảnh sát đã nói \"⟪とにかく五千円払えば立ち去ってもよい⟫\" (Dù sao, nếu trả 5000 yên, bạn có thể đi). Điều này cho thấy rằng cảnh sát đã đồng⟪情する⟫ (đồng cảm) với tình huống của người trẻ."}}
 ],
 "key_info": null,
 "correct": {"index": 4, "option_ja": "青年の立場に同情したから。", "full_sentence": null}
}
```

Điểm cần thấy: các câu Nhật nằm **trong câu tiếng Việt** (có dấu nháy, không đứng riêng dòng) → để trong `analysis`, bọc ⟪ ⟫ – không đưa vào `quotes`; không có kết luận → `is_match` theo `dap_an_so`.
