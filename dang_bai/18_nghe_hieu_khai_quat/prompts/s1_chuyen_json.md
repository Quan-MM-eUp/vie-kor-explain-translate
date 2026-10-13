# Hướng dẫn chi tiết – chuyển lời giải sang JSON tiếng Việt (dạng 18 – Nghe hiểu khái quát) · v1

> Phiên bản `s1_chuyen_json.18.v1` (2026-10-08). Đọc cùng `prompts/s1_claude_tao.md` và schema `schema/reading_listening.v1.api.json`.
> Đây là hướng dẫn cho **tác tử TẠO**: chuyển **trung thành** – không sửa nội dung, không tự dịch, không gắn cờ.

## 1. Đầu vào của mỗi câu (`yeu_cau` trong file_vao)

| Khóa | Nội dung |
|---|---|
| `loi_thoai` | Lời thoại tiếng Nhật **đã được Python tách dòng**: `[{so: "L1", speaker, ja}, …]`. `speaker` = ký hiệu người nói (`男`, `女1`, `Ｆ`, `店員` …) hoặc `null` (dòng dẫn / dòng không nhãn). **Không** gồm câu hỏi và 4 lựa chọn. |
| `cau_hoi_ja` | Câu hỏi tiếng Nhật (dòng câu hỏi ở cuối lời thoại; vài câu lấy từ cột câu hỏi của đề) |
| `lua_chon_ja` | 4 lựa chọn tiếng Nhật trong lời thoại (không furigana) – chỉ để đối chiếu, xem mục 4 |
| `dap_an_so` | Đáp án đúng của đề (1–4) |
| `khuon` | `A` / `C` (có phân tích) · `D` (chỉ bản dịch + câu hỏi + lựa chọn tiếng Việt) · `E` (không có tiếng Việt) |
| `loi_giai_goc` | Lời giải tiếng Việt đã chuẩn hóa (furigana `｜chữ《cách đọc》`): bản dịch lời thoại → câu hỏi tiếng Việt → `###` → 4 khối `n. …` |
| `luu_y` | Lưu ý riêng của câu (theo cờ Python) – **làm đúng theo lưu ý** |
| `lua_chon_tieng_viet` | (chỉ khuôn D) 4 dòng lựa chọn tiếng Việt ở cuối lời giải |

## 2. Khung JSON

```
{schema: "reading_listening.v1", question_id, cau_con: 1,
 full_translation: [{label: null, lines: [ {speaker, ja, meaning} × n ]}],   ← đúng 1 nhóm, n = số dòng loi_thoai
 summary: null,
 question: {ja, meaning},
 options: [ {index, option_ja, reading: null, meaning, is_match, quotes: [{ja, meaning}], analysis} × 4 ],
 key_info: null,
 correct: {index: dap_an_so, option_ja: <giống hệt options[dap_an_so-1].option_ja>, full_sentence: null}}
```
Mọi trường `meaning` / `analysis` là `{"vi": "…"}` hoặc `null` (không có nội dung thì `null`, **không** để chuỗi rỗng). Không có khóa `reference_raw` (Python điền).

## 3. Lời thoại → `full_translation`

1. **Mỗi dòng `Lk` của `loi_thoai` = đúng một phần tử `lines[k-1]`**, đúng thứ tự, đủ dòng: `speaker` và `ja` **chép y nguyên** từ `loi_thoai` (kể cả lỗi gõ, `(i)`, dấu câu lạ). Không gộp, không tách, không thêm dòng câu hỏi / lựa chọn. Python so từng dòng (K-LT1 – LỖI nếu lệch).
2. `meaning.vi` = câu dịch tương ứng trong **phần bản dịch** của lời giải (trước câu hỏi tiếng Việt / trước `###`):
   - **bỏ nhãn người nói** đầu dòng Việt (`Người phụ nữ:`, `Nam:`, `Nữ 1:`, `Nhân viên:` …) – người nói đã ở `speaker`;
   - dòng dẫn (`女の人と男の人が…話しています。`) ↔ câu dẫn Việt (`Một người phụ nữ và…`);
   - số dòng Việt ≠ số dòng Nhật: ghép **theo nghĩa** – một câu Việt dịch gộp 2 lượt → **cắt** câu Việt ra đúng chỗ (chỉ cắt, không viết lại, không thêm chữ); một lượt Nhật dài được dịch thành nhiều dòng Việt → nối các dòng Việt bằng `\n` vào cùng `meaning`;
   - lượt thoại **không có câu dịch** tương ứng → `meaning = null` (**không tự dịch**). Lời giải không có bản dịch (khuôn E, hoặc lưu ý `khong_ban_dich`) → mọi `meaning = null`;
   - **mọi câu chữ của bản dịch phải nằm trong một `meaning` nào đó** (Python đo độ phủ ≥ 97%).
3. Từ tiếng Nhật chen trong câu Việt → bọc `⟪ ⟫` (giữ furigana bên trong): `các ⟪｜施《し》｜設《せつ》⟫ thu gom rác`.

## 4. Câu hỏi → `question`

- `question.ja` = `cau_hoi_ja` (chép nguyên). Không có → `null`.
- `question.meaning.vi` = dòng câu hỏi tiếng Việt (dòng cuối của phần bản dịch, kết thúc bằng `?`), bỏ nhãn `Câu hỏi:` nếu có. Không có → `null`.

## 5. Phân tích → `options` (khuôn A, C)

Mỗi khối bắt đầu bằng dòng `n. <lựa chọn tiếng Nhật>`:

| Lời giải | JSON |
|---|---|
| `n. ｜賛《さん》｜成《せい》だ` | `index = n`, `option_ja` = phần sau `n. ` **chép nguyên như lời giải** (giữ furigana; kể cả khi khác `lua_chon_ja`), `reading = null` |
| `Nghĩa: Tán thành` | `meaning.vi` (không có dòng `Nghĩa:` → `null`) |
| `Phân tích đoạn hội thoại:` / `Câu thoại liên quan:` / `Câu thoại then chốt:` / `Có câu:` (nhãn đứng riêng) | **bỏ** (không chép) |
| Dòng dẫn câu trích kết thúc bằng `:` – `Người cha nói:`, `Ví dụ, người cha nói:`, `Và:`, `Ông chỉ nói:` – và nhãn ngay trước 「 trên cùng dòng (`Nam: 「…」`) | **bỏ** (người nói tra được ở `full_translation`) |
| 「câu Nhật」 (Dịch: …) / 「câu Nhật」 (…) – câu trích **đứng riêng** (sau dòng dẫn, hoặc cả dòng là câu trích) | `quotes[] = {ja: phần trong 「 」 (bỏ cặp 「」 ngoài cùng, giữ furigana, giữ 「」 lồng bên trong), meaning.vi: phần trong ngoặc (bỏ chữ `Dịch:`)}`; không có phần dịch → `meaning = null`. Mỗi câu trích một phần tử, đúng thứ tự |
| 「…」 **nằm giữa câu tiếng Việt** (nhắc một từ / mẫu câu: `người nói dùng mẫu 「返してもらえないでしょうか」, thể hiện…`) | **không** tách thành quote – giữ trong `analysis`, bọc ⟪ ⟫ phần Nhật: `「⟪返してもらえないでしょうか⟫」` |
| `→ ĐÚNG.` / `→ SAI.` | `is_match = true / false` (chép như lời giải, kể cả khi trái `dap_an_so`); dấu `→ ĐÚNG/SAI` **không** chép vào analysis |
| Mọi câu chữ còn lại của khối (nhận xét trước và **sau** `→`, kể cả `Lý do: …`) | `analysis.vi`, giữ thứ tự, mỗi dòng nối bằng `\n`; từ Nhật chen giữa bọc ⟪ ⟫. Không còn chữ nào → `null` |

- Khối không có `→ ĐÚNG/SAI` → `is_match = (index == dap_an_so)`. Có nhiều `→` → theo kết luận **cuối**.
- Có đoạn chữ sau `###` trước khối 1 → nối vào **đầu** `options[0].analysis` (giữ `\n`).
- Câu trích chứa chữ **Việt** trong 「 」 (lời giải trích nhầm bản dịch) → giữ trong `analysis` như văn bản Việt, không đưa vào `quotes`.

## 6. Khuôn D, E (không phân tích)

- **D:** `options[i].option_ja` = `lua_chon_ja[i]`; `meaning.vi` = dòng `lua_chon_tieng_viet[i]` (bỏ số thứ tự đầu dòng nếu có); `quotes = []`; `analysis = null`; `is_match = (index == dap_an_so)`. `full_translation` / `question` như mục 3–4.
- **E:** như D nhưng mọi `meaning = null` (lời giải không có tiếng Việt – **không tự dịch**).

## 7. `correct`

`{"index": dap_an_so, "option_ja": <giống hệt options[dap_an_so-1].option_ja>, "full_sentence": null}` – luôn theo `dap_an_so`, kể cả khi lời giải ghi `→ ĐÚNG` chỗ khác.

## 8. Ví dụ (12136_1, khuôn A – `full_translation` chỉ in 4/12 dòng cho gọn; bản thật phải đủ 12 dòng)

Lời giải gốc (trích khối 1):
```
1. ｜賛《さん》｜成《せい》だ
Nghĩa: Tán thành
Phân tích đoạn hội thoại:
Không có câu nào thể hiện người cha tán thành với ý định của con trai.
Ví dụ, người cha nói:
「そうか・・・。｜真《ま》｜面《じ》なやつだから、｜何《なに》ががん｜考《かんが》えてるんだろうけど。」 (Vậy à... Nó là đứa nghiêm túc, chắc nó cũng đang suy nghĩ gì đó, nhưng...)
Và:
「とにかく、｜話《はな》しを｜聞《き》いてみないと。」 (Dù sao thì cũng phải thử nghe nó nói đã.)
Những câu này cho thấy ông chưa đưa ra ý kiến tán thành.
→ SAI.
Lựa chọn này không phù hợp vì người cha chưa thể hiện sự đồng ý.
```
JSON:
```json
{
 "schema": "reading_listening.v1",
 "question_id": 12136,
 "cau_con": 1,
 "full_translation": [
  {
   "label": null,
   "lines": [
    {
     "speaker": null,
     "ja": "女の人と男の人が息子について話しています。",
     "meaning": {
      "vi": "Một người phụ nữ và một người đàn ông đang nói chuyện về con trai."
     }
    },
    {
     "speaker": "Ｆ",
     "ja": "最近、たけしと話した？",
     "meaning": {
      "vi": "Gần đây anh có nói chuyện với Takeshi không?"
     }
    },
    {
     "speaker": "Ｍ",
     "ja": "いや、どうかしたの？",
     "meaning": {
      "vi": "Không, có chuyện gì à?"
     }
    },
    {
     "speaker": "Ｆ",
     "ja": "せっかく大学に合格したのに、行かないって言うのよ。",
     "meaning": {
      "vi": "Dù đã vất vả thi đỗ đại học, nhưng nó lại nói là không đi học."
     }
    }
   ]
  }
 ],
 "summary": null,
 "question": {
  "ja": "父親は息子の考えについて、どう思っていますか。",
  "meaning": {
   "vi": "Người cha nghĩ thế nào về suy nghĩ của con trai?"
  }
 },
 "options": [
  {
   "index": 1,
   "option_ja": "｜賛《さん》｜成《せい》だ",
   "reading": null,
   "meaning": {
    "vi": "Tán thành"
   },
   "is_match": false,
   "quotes": [
    {
     "ja": "そうか・・・。｜真《ま》｜面《じ》なやつだから、｜何《なに》ががん｜考《かんが》えてるんだろうけど。",
     "meaning": {
      "vi": "Vậy à... Nó là đứa nghiêm túc, chắc nó cũng đang suy nghĩ gì đó, nhưng..."
     }
    },
    {
     "ja": "とにかく、｜話《はな》しを｜聞《き》いてみないと。",
     "meaning": {
      "vi": "Dù sao thì cũng phải thử nghe nó nói đã."
     }
    }
   ],
   "analysis": {
    "vi": "Không có câu nào thể hiện người cha tán thành với ý định của con trai.\nNhững câu này cho thấy ông chưa đưa ra ý kiến tán thành.\nLựa chọn này không phù hợp vì người cha chưa thể hiện sự đồng ý."
   }
  },
  {
   "index": 2,
   "option_ja": "｜反《はん》｜対《たい》だ",
   "reading": null,
   "meaning": {
    "vi": "Phản đối"
   },
   "is_match": false,
   "quotes": [
    {
     "ja": "とにかく、｜話《はな》しを｜聞《き》いてみないと。",
     "meaning": {
      "vi": "Dù sao thì cũng phải thử nghe nó nói đã."
     }
    }
   ],
   "analysis": {
    "vi": "Người cha không nói rõ là phản đối.\nÔng chưa đưa ra ý kiến phản đối, mà muốn nghe con trai giải thích trước.\nKhông có dấu hiệu rõ ràng về sự phản đối trong lời nói của người cha."
   }
  },
  {
   "index": 3,
   "option_ja": "まだわからない",
   "reading": null,
   "meaning": {
    "vi": "Vẫn chưa biết"
   },
   "is_match": true,
   "quotes": [
    {
     "ja": "とにかく、｜話《はな》しを｜聞《き》いてみないと。",
     "meaning": {
      "vi": "Dù sao thì cũng phải thử nghe nó nói đã."
     }
    }
   ],
   "analysis": {
    "vi": "Điều này cho thấy ông chưa quyết định gì, muốn nghe con trai giải thích trước khi đưa ra ý kiến.\nLựa chọn này phù hợp nhất với nội dung hội thoại, vì người cha chưa đưa ra ý kiến mà muốn nghe thêm."
   }
  },
  {
   "index": 4,
   "option_ja": "まじめだ",
   "reading": null,
   "meaning": {
    "vi": "Nghiêm túc"
   },
   "is_match": false,
   "quotes": [
    {
     "ja": "｜真《ま》｜面《じ》なやつだから、｜何《なに》ががん｜考《かんが》えてるんだろうけど。",
     "meaning": {
      "vi": "Nó là đứa nghiêm túc, chắc nó cũng đang suy nghĩ gì đó, nhưng..."
     }
    }
   ],
   "analysis": {
    "vi": "Tuy nhiên, đây chỉ là nhận xét về tính cách của con trai, không phải là ý kiến về suy nghĩ của con trai.\nLựa chọn này không trả lời đúng câu hỏi về ý kiến của người cha đối với suy nghĩ của con trai."
   }
  }
 ],
 "key_info": null,
 "correct": {
  "index": 3,
  "option_ja": "まだわからない",
  "full_sentence": null
 }
}
```

## 9. Lỗi hay mắc (tránh)

- Gộp / tách dòng lời thoại, bỏ dòng dẫn L1, thêm câu hỏi / lựa chọn vào `full_translation`, sửa `ja` hay `speaker` cho "đúng hơn".
- Để sót nhãn `Người phụ nữ:` / `Nam:` trong `meaning.vi`; bỏ sót câu dịch (độ phủ < 97%); **tự dịch** dòng không có bản dịch.
- Chép `option_ja` theo `lua_chon_ja` thay vì theo dòng `n. …` của lời giải (khuôn A/C); bỏ furigana.
- Để lại `→ SAI.` trong `analysis`; bỏ mất câu kết luận sau `→`; chép `Dịch:` vào `quotes[].meaning`.
- Tách 「từ」 nằm giữa câu Việt thành quote; quên ⟪ ⟫ quanh tiếng Nhật trong câu Việt.
- `correct.index` theo `→ ĐÚNG` thay vì `dap_an_so`.
