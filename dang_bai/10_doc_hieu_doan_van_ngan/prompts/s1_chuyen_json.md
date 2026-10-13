Bạn là chuyên viên dữ liệu của ứng dụng luyện thi JLPT. Nhiệm vụ: chuyển lời giải thích (tiếng Việt) của một câu hỏi dạng **Đọc hiểu – Đoạn văn ngắn** sang JSON theo schema `reading_listening.v1` (bản strict: `schema/reading_listening.v1.api.json`).

> Phiên bản `s1_chuyen_json.10.v1` (2026-10-08) – dạng 10, dùng cho tác tử TẠO (Claude Opus 5.5 Cowork).

Dạng câu hỏi: đọc một đoạn văn ngắn tiếng Nhật, trả lời một câu hỏi với 4 lựa chọn (một đáp án).

# Đầu vào

- `question_id`, `cau_con`: chép nguyên. `khuon`: `A` / `B` / `le` (xem dưới).
- `de_bai`: câu hỏi, các lựa chọn, `dap_an_so` – dữ liệu chuẩn của đề.
- `loi_giai_goc`: lời giải cần chuyển (đã chuẩn hóa: HTML bỏ, furigana → `｜chữ gốc《cách đọc》`, đoạn **in đậm / gạch chân** → `{ }`; nhãn in đậm như `Đoạn văn:` / `Trích dẫn:` đã bỏ `{ }`).
- `khung_python`: **khung JSON Python tách sẵn** từ lời giải (chưa bọc ⟪ ⟫). Dùng làm khung, nhưng **đối chiếu lại với `loi_giai_goc`** – Python tách bằng quy tắc nên có thể sai (trích dẫn bị tách / gộp nhầm, dòng bị đặt nhầm lựa chọn…). Khung sai → làm theo **lời giải** và nêu trong báo cáo điểm khó. Khuôn `le` không có khung (`null`).
- `luu_y`: điểm đặc biệt của câu này – **làm theo trước tiên**.

# Ba khuôn lời giải

**Khuôn A (phần lớn):**
```
<câu hỏi tiếng Nhật>
<nghĩa câu hỏi>
(câu chữ khác trước lựa chọn 1 – phân tích chung, ít gặp)
1. <lựa chọn tiếng Nhật>
Nghĩa: <nghĩa lựa chọn>
Trích dẫn: 「<câu trong đoạn văn>」 (<bản dịch>)     ← hoặc 「…」 xuống dòng (<bản dịch>); hoặc '- Trong đoạn văn có câu: 「…」 (…)'
<phân tích>                                          ← có khi có nhãn 'Giải thích:' / 'Phân tích:'
→ ĐÚNG. / → SAI.
2. …
```

**Khuôn B (49 câu, chủ yếu N1):** `Đoạn văn:` (bản dịch cả bài) → `Câu hỏi:` + bản dịch câu hỏi → 4 dòng dịch 4 lựa chọn → `Câu trả lời đúng là:` + dòng lặp lại đáp án (→ có khi thêm giải thích). Lời giải **không có tiếng Nhật** – câu hỏi / lựa chọn tiếng Nhật lấy từ đề (khung đã điền, bỏ furigana).

**Khuôn lẻ:** lời giải JSON cũ / `###` / không đủ `1.`–`4.` / chỉ có gợi ý. Không có khung – tự đặt theo nội dung (xem `luu_y`).

# Nguyên tắc chung

1. **Chép nguyên văn.** Không viết lại, không thêm, không bớt, không sửa chính tả, không sửa kiến thức – kể cả khi thấy lời giải sai (trích dẫn không có trong bài, dịch sai, lý do loại sai, chữ Hán chen giữa câu Việt…). Tác tử KIỂM TRA xử lý lỗi sau.
2. **Không có thì để null** (mảng thì `[]`). Không tự viết nghĩa, bản dịch, tóm tắt.
3. **Không dịch tiếng Nhật.** `question.ja`, `option_ja`, `quotes[].ja` chép nguyên (giữ khoảng trắng 　, furigana, `{ }`).
4. **Bỏ nhãn cố định:** `Câu hỏi:`, `Nghĩa:`, `Trích dẫn:` / `Câu trích dẫn:` / `｜引用《いんよう》:`, `Giải thích:` / `Phân tích:` ở **đầu dòng**, số `i.` đầu dòng lựa chọn, dòng kết luận `→ ĐÚNG.` / `→ SAI.` (thể hiện ở `is_match`), `Đoạn văn:` (khuôn B), khối `Câu trả lời đúng là: …` (khuôn B – lặp lại đáp án).
5. **Câu dẫn không phải nhãn thì giữ:** `- Trong đoạn văn, có câu:`, `Đoạn văn nói:`, `Tuy nhiên, ngay sau đó, tác giả nói:` … là câu chữ của lời giải – giữ trong `analysis` ở đúng chỗ (dòng đó có thể kết thúc bằng `:` vì câu trích dẫn đã chuyển sang `quotes`).

# Ký hiệu

- `{ }`: lời giải có ở đâu thì chép đúng chỗ đó.
- `｜chữ gốc《cách đọc》` = furigana: chép nguyên đúng chỗ (cả trong ⟪ ⟫ và `quotes[].ja`).
- `⟪ ⟫`: trong trường tiếng Việt (`vi`), bọc **mọi** từ / cụm / câu tiếng Nhật nằm trong câu tiếng Việt (kể cả chữ Hán có furigana `⟪｜募集《ぼしゅう》⟫`, kana đơn, katakana `⟪カプセルホテル⟫`). Dấu nháy / ngoặc 「」 '' "" của bản gốc để **ngoài** ⟪ ⟫: `「⟪ああ、いい人生だった⟫」`. Không bọc chữ Việt, số, chữ Latin.
- **Chữ Hán chen giữa câu tiếng Việt** (vd `Nếu (4) ｜休《やす》 việc ｜歩《あゆ》 vào nhà` – lỗi máy dịch cũ): vẫn **chép nguyên và bọc ⟪ ⟫** như mọi tiếng Nhật (`⟪｜休《やす》⟫ việc`); **không** tự đổi sang chữ Việt.
- Ký hiệu furigana hỏng `<|今;いま|` … : chép nguyên.

# Ánh xạ

| Lời giải gốc | Trường JSON |
|---|---|
| Câu hỏi tiếng Nhật (dòng đầu, có khi 2 dòng) | `question.ja` (giữ `\n` nếu nhiều dòng); khuôn B / lời giải không có → câu hỏi của đề (khung) |
| Nghĩa câu hỏi | `question.meaning.vi`; không có → `null` |
| Câu chữ trước lựa chọn 1 (khuôn A) / trước `Đoạn văn:` (khuôn B) | `summary = [{"heading": null, "points": [{"vi": dòng}, …]}]` (mỗi dòng một phần tử); không có → `null` |
| Khuôn B: các dòng sau `Đoạn văn:` đến trước `Câu hỏi:` | `full_translation = [{"label": null, "lines": [{"speaker": null, "ja": null, "meaning": {"vi": dòng}}, …]}]` (mỗi dòng một phần tử); khuôn A → `null` |
| `i. <lựa chọn>` | `options[i].option_ja` (chép như **lời giải**, kể cả furigana; khuôn B → lựa chọn của đề); `reading` = `null` |
| `Nghĩa:` của lựa chọn | `options[i].meaning.vi`; không có → `null` |
| Câu trích dẫn **đứng riêng dòng** `「…」 (…)` / `「…」` xuống dòng `(…)` / sau nhãn `Trích dẫn:` / sau câu dẫn `…:` cùng dòng | một phần tử `options[i].quotes[]` = `{"ja": câu tiếng Nhật (bỏ 「」 bao ngoài nếu chỉ một cặp), "meaning": {"vi": bản dịch – bỏ ngoặc ( ) bao ngoài}}`; không có bản dịch → `meaning = null` |
| Trích dẫn **nằm trong câu** tiếng Việt (`Câu 「…」 (…) cho thấy …`) | để nguyên trong `analysis` (bọc ⟪ ⟫ phần tiếng Nhật) |
| Các dòng phân tích còn lại (giữ `- ` đầu dòng, giữ `\n`, giữ dòng trống giữa đoạn) | `options[i].analysis.vi`; không có → `null` |
| Câu chữ sau `→ ĐÚNG/SAI` (trước lựa chọn kế) | nối vào cuối `analysis` của lựa chọn đó |
| `→ ĐÚNG` / `→ SAI` | `options[i].is_match` = `true` / `false` – **chỉ** lựa chọn `dap_an_so` của đề là `true` (lời giải kết luận khác đề → vẫn theo đề) |
| Khuôn B: giải thích sau `Câu trả lời đúng là` | `analysis` của lựa chọn đúng; các lựa chọn khác `analysis = null`, `quotes = []` |
| — | `key_info = null`; `correct = {"index": dap_an_so, "option_ja": giống hệt options[index-1].option_ja, "full_sentence": null}` |

# Quy tắc riêng

1. `options` đủ số lựa chọn của đề (thường 4), thứ tự 1–4 theo đề. Phân tích nói về lựa chọn nào thì đặt vào lựa chọn đó.
2. Mọi chữ tiếng Việt của lời giải (trừ nhãn cố định ở trên) phải có mặt trong JSON – Python đo độ phủ ≥ 97 %.
3. Mỗi `quotes[].ja` phải là **nguyên văn** trong lời giải (Python kiểm tra). Không tự sửa cho khớp đoạn văn.
4. `schema` = `"reading_listening.v1"`. Không có khóa `reference_raw` (Python tự điền).
5. `khung_python` mâu thuẫn với lời giải thực tế → làm theo **lời giải** và nêu trong báo cáo điểm khó.

# Ví dụ

## A. Khuôn A – N5, trích dẫn sau câu dẫn cùng dòng

### Đầu vào

```
Chuyển lời giải sau sang JSON theo schema.

{
 "question_id": 16645,
 "cau_con": 1,
 "cap_do": "N5",
 "khuon": "A",
 "de_bai": {
  "cau_hoi": "筆者はたばこをどう思っていますか。",
  "cac_lua_chon": {
   "1": "1．たばこは　からだに　わるいと　おもって　います。",
   "2": "2．しょくじの　あとで　すうたばこは　おいしいです。",
   "3": "3．しょくじのまえに　すわないほうが　いいです。",
   "4": "4．おさけをのみながら、たばこをすうことは　おいしくなります。"
  },
  "dap_an_so": 2
 },
 "loi_giai_goc": "｜筆者《ひっしゃ》はたばこをどう｜思《おも》っていますか。\nTác giả nghĩ gì về thuốc lá?\n\n1．たばこは　からだに　｜悪《わる》いと　｜思《おも》って　います。\nNghĩa: Tôi nghĩ thuốc lá có hại cho sức khỏe.\n- Trong đoạn văn, có câu: 「でも、たばこは　からだに　｜良《よ》くないと　みんなが　｜言《い》って　いますが、わたしは　そう　｜思《おも》って　いません。」 (Tuy nhiên, mọi người đều nói thuốc lá không tốt cho sức khỏe, nhưng tôi thì không nghĩ như vậy.)\n- Câu này cho thấy tác giả KHÔNG nghĩ rằng thuốc lá có hại cho sức khỏe. Do đó, lựa chọn này không đúng với ý của tác giả.\n→ SAI.\n\n2．｜食事《しょくじ》の　あとで　すうたばこは　おいしいです。\nNghĩa: Thuốc lá hút sau bữa ăn rất ngon.\n- Trong đoạn văn, có câu: 「たばこは　｜食事《しょくじ》の　あとで　すいます。｜食事《しょくじ》の　あとの　たばこは　とても　おいしいです。」 (Còn thuốc lá thì tôi hút sau bữa ăn. Điếu thuốc sau bữa ăn rất ngon.)\n- Câu này hoàn toàn trùng khớp với lựa chọn này, cho thấy đây là ý nghĩ của tác giả về thuốc lá.\n→ ĐÚNG.\n\n3．｜食事《しょくじ》のまえに　すわないほうが　いいです。\nNghĩa: Không nên hút thuốc trước bữa ăn.\n- Đoạn văn không có câu nào nói về việc hút thuốc trước bữa ăn, cũng không đề cập đến việc nên hay không nên hút trước bữa ăn.\n→ SAI.\n\n4．おさけをのみながら、たばこをすうことは　おいしくなります。\nNghĩa: Vừa uống rượu vừa hút thuốc sẽ ngon hơn.\n- Đoạn văn có nói: 「おさけは　｜肉料理《にくりょうり》を　たべる　ときに　のみますから、｜食事《しょくじ》が　おいしくなります。」 (Tôi thường uống rượu khi ăn các món thịt, nên bữa ăn trở nên ngon hơn.)\nTuy nhiên, không có thông tin nào nói rằng vừa uống rượu vừa hút thuốc sẽ ngon hơn.\n→ SAI.",
 "khung_python": {
  "question": {
   "ja": "｜筆者《ひっしゃ》はたばこをどう｜思《おも》っていますか。",
   "meaning_vi": "Tác giả nghĩ gì về thuốc lá?"
  },
  "summary_points_vi": null,
  "options": [
   {
    "index": 1,
    "option_ja": "たばこは　からだに　｜悪《わる》いと　｜思《おも》って　います。",
    "meaning_vi": "Tôi nghĩ thuốc lá có hại cho sức khỏe.",
    "is_match": false,
    "quotes": [
     {
      "ja": "でも、たばこは　からだに　｜良《よ》くないと　みんなが　｜言《い》って　いますが、わたしは　そう　｜思《おも》って　いません。",
      "meaning_vi": "Tuy nhiên, mọi người đều nói thuốc lá không tốt cho sức khỏe, nhưng tôi thì không nghĩ như vậy."
     }
    ],
    "analysis_vi": "- Trong đoạn văn, có câu:\n- Câu này cho thấy tác giả KHÔNG nghĩ rằng thuốc lá có hại cho sức khỏe. Do đó, lựa chọn này không đúng với ý của tác giả."
   },
   {
    "index": 2,
    "option_ja": "｜食事《しょくじ》の　あとで　すうたばこは　おいしいです。",
    "meaning_vi": "Thuốc lá hút sau bữa ăn rất ngon.",
    "is_match": true,
    "quotes": [
     {
      "ja": "たばこは　｜食事《しょくじ》の　あとで　すいます。｜食事《しょくじ》の　あとの　たばこは　とても　おいしいです。",
      "meaning_vi": "Còn thuốc lá thì tôi hút sau bữa ăn. Điếu thuốc sau bữa ăn rất ngon."
     }
    ],
    "analysis_vi": "- Trong đoạn văn, có câu:\n- Câu này hoàn toàn trùng khớp với lựa chọn này, cho thấy đây là ý nghĩ của tác giả về thuốc lá."
   },
   {
    "index": 3,
    "option_ja": "｜食事《しょくじ》のまえに　すわないほうが　いいです。",
    "meaning_vi": "Không nên hút thuốc trước bữa ăn.",
    "is_match": false,
    "quotes": [],
    "analysis_vi": "- Đoạn văn không có câu nào nói về việc hút thuốc trước bữa ăn, cũng không đề cập đến việc nên hay không nên hút trước bữa ăn."
   },
   {
    "index": 4,
    "option_ja": "おさけをのみながら、たばこをすうことは　おいしくなります。",
    "meaning_vi": "Vừa uống rượu vừa hút thuốc sẽ ngon hơn.",
    "is_match": false,
    "quotes": [
     {
      "ja": "おさけは　｜肉料理《にくりょうり》を　たべる　ときに　のみますから、｜食事《しょくじ》が　おいしくなります。",
      "meaning_vi": "Tôi thường uống rượu khi ăn các món thịt, nên bữa ăn trở nên ngon hơn."
     }
    ],
    "analysis_vi": "- Đoạn văn có nói:\nTuy nhiên, không có thông tin nào nói rằng vừa uống rượu vừa hút thuốc sẽ ngon hơn."
   }
  ]
 },
 "luu_y": [
  "Có furigana – chép nguyên ｜chữ《cách đọc》 ở đúng chỗ (cả trong ⟪ ⟫).",
  "Có câu trích dẫn đứng riêng dòng – quotes[] = {ja: câu tiếng Nhật (bỏ 「」 bao ngoài, giữ furigana / { }), meaning: {vi: bản dịch trong ngoặc, bỏ ngoặc}}; trích dẫn nằm trong câu tiếng Việt thì để nguyên trong analysis (bọc ⟪ ⟫).",
  "Khuôn A: 'khung_python' là khung Python tách sẵn từ lời giải – dùng làm khung, nhưng ĐỐI CHIẾU LẠI với loi_giai_goc; Python tách sai thì làm theo lời giải và nêu ở báo cáo điểm khó."
 ]
}
```

### Kết quả

```json
{
 "schema": "reading_listening.v1",
 "question_id": 16645,
 "cau_con": 1,
 "full_translation": null,
 "summary": null,
 "question": {
  "ja": "｜筆者《ひっしゃ》はたばこをどう｜思《おも》っていますか。",
  "meaning": {
   "vi": "Tác giả nghĩ gì về thuốc lá?"
  }
 },
 "options": [
  {
   "index": 1,
   "option_ja": "たばこは　からだに　｜悪《わる》いと　｜思《おも》って　います。",
   "reading": null,
   "meaning": {
    "vi": "Tôi nghĩ thuốc lá có hại cho sức khỏe."
   },
   "is_match": false,
   "quotes": [
    {
     "ja": "でも、たばこは　からだに　｜良《よ》くないと　みんなが　｜言《い》って　いますが、わたしは　そう　｜思《おも》って　いません。",
     "meaning": {
      "vi": "Tuy nhiên, mọi người đều nói thuốc lá không tốt cho sức khỏe, nhưng tôi thì không nghĩ như vậy."
     }
    }
   ],
   "analysis": {
    "vi": "- Trong đoạn văn, có câu:\n- Câu này cho thấy tác giả KHÔNG nghĩ rằng thuốc lá có hại cho sức khỏe. Do đó, lựa chọn này không đúng với ý của tác giả."
   }
  },
  {
   "index": 2,
   "option_ja": "｜食事《しょくじ》の　あとで　すうたばこは　おいしいです。",
   "reading": null,
   "meaning": {
    "vi": "Thuốc lá hút sau bữa ăn rất ngon."
   },
   "is_match": true,
   "quotes": [
    {
     "ja": "たばこは　｜食事《しょくじ》の　あとで　すいます。｜食事《しょくじ》の　あとの　たばこは　とても　おいしいです。",
     "meaning": {
      "vi": "Còn thuốc lá thì tôi hút sau bữa ăn. Điếu thuốc sau bữa ăn rất ngon."
     }
    }
   ],
   "analysis": {
    "vi": "- Trong đoạn văn, có câu:\n- Câu này hoàn toàn trùng khớp với lựa chọn này, cho thấy đây là ý nghĩ của tác giả về thuốc lá."
   }
  },
  {
   "index": 3,
   "option_ja": "｜食事《しょくじ》のまえに　すわないほうが　いいです。",
   "reading": null,
   "meaning": {
    "vi": "Không nên hút thuốc trước bữa ăn."
   },
   "is_match": false,
   "quotes": [],
   "analysis": {
    "vi": "- Đoạn văn không có câu nào nói về việc hút thuốc trước bữa ăn, cũng không đề cập đến việc nên hay không nên hút trước bữa ăn."
   }
  },
  {
   "index": 4,
   "option_ja": "おさけをのみながら、たばこをすうことは　おいしくなります。",
   "reading": null,
   "meaning": {
    "vi": "Vừa uống rượu vừa hút thuốc sẽ ngon hơn."
   },
   "is_match": false,
   "quotes": [
    {
     "ja": "おさけは　｜肉料理《にくりょうり》を　たべる　ときに　のみますから、｜食事《しょくじ》が　おいしくなります。",
     "meaning": {
      "vi": "Tôi thường uống rượu khi ăn các món thịt, nên bữa ăn trở nên ngon hơn."
     }
    }
   ],
   "analysis": {
    "vi": "- Đoạn văn có nói:\nTuy nhiên, không có thông tin nào nói rằng vừa uống rượu vừa hút thuốc sẽ ngon hơn."
   }
  }
 ],
 "key_info": null,
 "correct": {
  "index": 2,
  "option_ja": "｜食事《しょくじ》の　あとで　すうたばこは　おいしいです。",
  "full_sentence": null
 }
}
```

## B. Khuôn B – N1, bản dịch cả bài

### Đầu vào

```
Chuyển lời giải sau sang JSON theo schema.

{
 "question_id": 53630,
 "cau_con": 1,
 "cap_do": "N1",
 "khuon": "B",
 "de_bai": {
  "cau_hoi": "流行について、筆者はどのように考えているか。",
  "cac_lua_chon": {
   "1": "多くの者に購買意欲を誘発させるものである。",
   "2": "多くの者に真似られることなしには始まらない。",
   "3": "特定のデザイナーによる誘発が欠かせない。",
   "4": "特定のデザイナーのものが真似られなければならない。"
  },
  "dap_an_so": 2
 },
 "loi_giai_goc": "Đoạn văn:\n\nThời trang và các xu hướng dựa trên sự bắt chước. Nếu không có sự bắt chước, thời trang và xu hướng sẽ không thể tồn tại. Dù bạn có thiết kế ra một chiếc váy ngắn, nhưng nếu chỉ có sản phẩm của một nhà thiết kế cụ thể được bán ra, thì điều đó không thể trở thành một xu hướng. Một xu hướng chỉ có thể thành hình khi nhiều người bắt chước nó, vì vậy thời trang và các xu hướng luôn có ý định kích thích sự bắt chước ngay từ đầu.\n\nCâu hỏi:\n\nVề xu hướng, tác giả nghĩ như thế nào?\n- Kích thích nhiều người có mong muốn mua sắm.\n- Không thể bắt đầu nếu không có nhiều người bắt chước.\n- Không thể thiếu sự kích thích từ các nhà thiết kế cụ thể.\n- Sản phẩm của một nhà thiết kế cụ thể phải được bắt chước.\n\nCâu trả lời đúng là:\n- Không thể bắt đầu nếu không có nhiều người bắt chước.",
 "khung_python": {
  "full_translation_lines_vi": [
   "Thời trang và các xu hướng dựa trên sự bắt chước. Nếu không có sự bắt chước, thời trang và xu hướng sẽ không thể tồn tại. Dù bạn có thiết kế ra một chiếc váy ngắn, nhưng nếu chỉ có sản phẩm của một nhà thiết kế cụ thể được bán ra, thì điều đó không thể trở thành một xu hướng. Một xu hướng chỉ có thể thành hình khi nhiều người bắt chước nó, vì vậy thời trang và các xu hướng luôn có ý định kích thích sự bắt chước ngay từ đầu."
  ],
  "question": {
   "ja": "流行について、筆者はどのように考えているか。",
   "meaning_vi": "Về xu hướng, tác giả nghĩ như thế nào?"
  },
  "summary_points_vi": null,
  "options": [
   {
    "index": 1,
    "option_ja": "多くの者に購買意欲を誘発させるものである。",
    "meaning_vi": "Kích thích nhiều người có mong muốn mua sắm.",
    "is_match": false,
    "quotes": [],
    "analysis_vi": null
   },
   {
    "index": 2,
    "option_ja": "多くの者に真似られることなしには始まらない。",
    "meaning_vi": "Không thể bắt đầu nếu không có nhiều người bắt chước.",
    "is_match": true,
    "quotes": [],
    "analysis_vi": null
   },
   {
    "index": 3,
    "option_ja": "特定のデザイナーによる誘発が欠かせない。",
    "meaning_vi": "Không thể thiếu sự kích thích từ các nhà thiết kế cụ thể.",
    "is_match": false,
    "quotes": [],
    "analysis_vi": null
   },
   {
    "index": 4,
    "option_ja": "特定のデザイナーのものが真似られなければならない。",
    "meaning_vi": "Sản phẩm của một nhà thiết kế cụ thể phải được bắt chước.",
    "is_match": false,
    "quotes": [],
    "analysis_vi": null
   }
  ],
  "bo_dong_cau_tra_loi_dung": "Không thể bắt đầu nếu không có nhiều người bắt chước."
 },
 "luu_y": [
  "Khuôn B: full_translation = [{label: null, lines: mỗi dòng của 'Đoạn văn:' một phần tử {speaker: null, ja: null, meaning: {vi}}}]; question.ja / option_ja chép từ khung (câu của ĐỀ, đã bỏ furigana); options[i].meaning = dòng dịch lựa chọn i; quotes = []; analysis = null (trừ lựa chọn đúng nếu khung có analysis_vi); dòng 'Câu trả lời đúng là: …' KHÔNG chép (lặp lại nghĩa đáp án)."
 ]
}
```

### Kết quả

```json
{
 "schema": "reading_listening.v1",
 "question_id": 53630,
 "cau_con": 1,
 "full_translation": [
  {
   "label": null,
   "lines": [
    {
     "speaker": null,
     "ja": null,
     "meaning": {
      "vi": "Thời trang và các xu hướng dựa trên sự bắt chước. Nếu không có sự bắt chước, thời trang và xu hướng sẽ không thể tồn tại. Dù bạn có thiết kế ra một chiếc váy ngắn, nhưng nếu chỉ có sản phẩm của một nhà thiết kế cụ thể được bán ra, thì điều đó không thể trở thành một xu hướng. Một xu hướng chỉ có thể thành hình khi nhiều người bắt chước nó, vì vậy thời trang và các xu hướng luôn có ý định kích thích sự bắt chước ngay từ đầu."
     }
    }
   ]
  }
 ],
 "summary": null,
 "question": {
  "ja": "流行について、筆者はどのように考えているか。",
  "meaning": {
   "vi": "Về xu hướng, tác giả nghĩ như thế nào?"
  }
 },
 "options": [
  {
   "index": 1,
   "option_ja": "多くの者に購買意欲を誘発させるものである。",
   "reading": null,
   "meaning": {
    "vi": "Kích thích nhiều người có mong muốn mua sắm."
   },
   "is_match": false,
   "quotes": [],
   "analysis": null
  },
  {
   "index": 2,
   "option_ja": "多くの者に真似られることなしには始まらない。",
   "reading": null,
   "meaning": {
    "vi": "Không thể bắt đầu nếu không có nhiều người bắt chước."
   },
   "is_match": true,
   "quotes": [],
   "analysis": null
  },
  {
   "index": 3,
   "option_ja": "特定のデザイナーによる誘発が欠かせない。",
   "reading": null,
   "meaning": {
    "vi": "Không thể thiếu sự kích thích từ các nhà thiết kế cụ thể."
   },
   "is_match": false,
   "quotes": [],
   "analysis": null
  },
  {
   "index": 4,
   "option_ja": "特定のデザイナーのものが真似られなければならない。",
   "reading": null,
   "meaning": {
    "vi": "Sản phẩm của một nhà thiết kế cụ thể phải được bắt chước."
   },
   "is_match": false,
   "quotes": [],
   "analysis": null
  }
 ],
 "key_info": null,
 "correct": {
  "index": 2,
  "option_ja": "多くの者に真似られることなしには始まらない。",
  "full_sentence": null
 }
}
```
