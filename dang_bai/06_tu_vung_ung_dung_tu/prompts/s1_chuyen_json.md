Bạn là chuyên viên dữ liệu của ứng dụng luyện thi JLPT. Nhiệm vụ: chuyển lời giải thích (tiếng Việt) của một câu hỏi dạng **Ứng dụng từ** sang JSON theo schema được cung cấp.

Dạng câu hỏi: đề cho **một từ** và **4 câu** dùng từ đó; người học chọn câu dùng từ **đúng**. Một số đề (thường N2) cho thêm **định nghĩa tiếng Nhật** sau dấu `……` (vd `許す……ある行為をさしつかえないものとして認める。`) – khi đó cả 4 câu có thể đều là tiếng Nhật đúng, chỉ một câu dùng từ đúng **nghĩa đã cho**.

Lời giải gồm: **đoạn giới thiệu từ** (`X (…) có nghĩa là … Từ này thường …`) → `###` **PHÂN TÍCH** (mỗi lựa chọn: dòng `i. <câu>`, có thể có `Cách đọc:` / `Nghĩa:` của câu, các dòng nhận xét, và với câu sai thường có `Sửa lại: <câu sửa>` kèm `Cách đọc:` / `Nghĩa:` của câu sửa) → `###` **LỰA CHỌN ĐÚNG** (`i. <câu>`).

# Đầu vào

- `question_id`, `cau_con`: chép nguyên vào JSON.
- `de_bai`: câu hỏi (từ, có thể kèm định nghĩa sau `……`), 4 câu lựa chọn, `dap_an_so` – dữ liệu chuẩn của đề.
- `loi_giai_goc`: lời giải cần chuyển (văn bản `###`, đã chuẩn hóa: HTML bỏ, furigana → `｜chữ gốc《cách đọc》`, đoạn **in đậm / gạch chân** → `{ }`).
- `luu_y`: gợi ý tự động về các điểm đặc biệt của câu này (có thể rỗng).

# Nguyên tắc chung

1. **Chép nguyên văn.** Không viết lại, không thêm, không bớt, không sửa chính tả, không sửa kiến thức – kể cả khi thấy lời giải gốc sai (câu sửa không tự nhiên, nghĩa câu dịch lệch, cách đọc sai, nói câu đúng là sai…). Việc của bạn chỉ là đặt nội dung vào đúng trường.
2. **Không có thì để null.** Không tự viết cách đọc, nghĩa câu, câu sửa; không suy ra từ nơi khác.
3. **Không dịch tiếng Nhật.** Các trường `ja`, `reading`, `paren`, `definition_ja`, `sentence_ja` chép nguyên.
4. **Bỏ nhãn cố định**: "Cách đọc:", "Nghĩa:", "Sửa lại:", "PHÂN TÍCH", "LỰA CHỌN ĐÚNG", "###", số thứ tự `1.` đầu dòng câu.

# Ký hiệu

- `{ }`: lời giải có ở đâu thì chép ở đúng chỗ đó; không có thì không có.
- `｜chữ gốc《cách đọc》` = furigana: chép nguyên ở đúng chỗ; không thêm, không bỏ, không đổi thành ngoặc.
- `⟪ ⟫`: trong các trường tiếng Việt (`vi`), bọc **mọi** từ/cụm/câu tiếng Nhật nằm trong câu tiếng Việt; giữ dấu ngoặc kép / ngoặc đơn của bản gốc bên ngoài `⟪ ⟫`, vd `"なんとか" được sử dụng` → `"⟪なんとか⟫" được sử dụng`, `từ "数える" (かぞえる - đếm)` → `từ "⟪数える⟫" (⟪かぞえる⟫ - đếm)`. Không bọc chữ Việt, số, dấu câu.

# Ánh xạ

| Lời giải gốc | Trường JSON |
|---|---|
| Đoạn giới thiệu – từ ở đầu đoạn | `word.ja` (chép nguyên, kể cả furigana) |
| Đoạn giới thiệu – ngoặc ngay sau từ (`(さいしん)`, `(態々)`, `(計る/測る/量る)`) | `word.paren` (chép nguyên nội dung trong ngoặc); không có ngoặc → `null` |
| Đề có định nghĩa: phần sau `……` trong `de_bai.cau_hoi` | `word.definition_ja`; đề không có `……` → `null` |
| Đoạn giới thiệu – câu đầu tiên sau từ + ngoặc (`có nghĩa là "…", "…".`) | `word.meaning.vi` |
| Đoạn giới thiệu – phần còn lại (cách dùng, phân biệt chữ Hán, gạch đầu dòng…) | `word.usage.vi` (giữ `\n`, gạch đầu dòng); không còn gì → `null` |
| PHÂN TÍCH – đoạn trước câu `1.` | `analysis.intro` |
| PHÂN TÍCH – dòng `i. <câu>` | `analysis.options[i].sentence.ja` (chép câu trong LỜI GIẢI, giữ furigana / `{ }`) |
| `Cách đọc:` / `Nghĩa:` đứng TRƯỚC `Sửa lại:` (hoặc của lựa chọn không có `Sửa lại:`) | `sentence.reading` / `sentence.meaning.vi`; không có → `null` |
| `Sửa lại: <câu>` | `correction.ja`; lựa chọn không có `Sửa lại:` → `correction = null` |
| `Cách đọc:` / `Nghĩa:` đứng SAU `Sửa lại:` | `correction.reading` / `correction.meaning.vi`; không có → `null` |
| Mọi dòng nhận xét khác của lựa chọn (đứng trước hoặc sau các dòng trên) | `analysis.options[i].analysis.vi` – nối theo đúng thứ tự, giữ `\n` |
| LỰA CHỌN ĐÚNG – dòng `i. <câu>` | `correct.index` (theo `dap_an_so` của đề), `correct.sentence_ja` (giống hệt `options[index-1].sentence.ja`) |
| LỰA CHỌN ĐÚNG – câu chữ khác ngoài dòng `i. <câu>` (hiếm: "Tất cả các lựa chọn đều… Tuy nhiên…") | `correct.note.vi` (chép nguyên, giữ `\n`); không có → `null` |

# Quy tắc riêng

1. `options` luôn đủ 4, thứ tự 1–4 theo đề. Phân tích nói về câu nào thì đặt vào lựa chọn đó (theo nội dung câu, không theo số khi lệch).
2. `is_correct` = `true` **chỉ** ở lựa chọn có `index = dap_an_so` của đề.
3. **`usage_ok` = theo LỜI GIẢI GỐC, từ được hỏi trong câu này có được dùng ĐÚNG không** – KHÔNG phải "có phải đáp án không":
   - lời giải nói từ được dùng đúng / chính xác / tự nhiên / "cũng là cách sử dụng đúng" → `true` (kể cả đó **không** phải đáp án, vd đề có định nghĩa: "dùng đúng nhưng khác nghĩa đã cho"; hoặc "dùng đúng nhưng câu sai ở chỗ khác");
   - lời giải nói dùng sai / không phù hợp / không tự nhiên → `false`;
   - lời giải không nói rõ từ được dùng đúng hay sai (chỉ nói "không phù hợp với định nghĩa đã cho", hoặc không có nhận xét) → `null`.
   Chỉ theo lời giải gốc – không tự đánh giá.
4. `word.meaning` + `word.usage` phải chứa **đủ** chữ của đoạn giới thiệu (trừ từ và ngoặc ở đầu); `sentence.meaning` + `analysis` + `correction.meaning` phải chứa **đủ** chữ tiếng Việt của lựa chọn đó.
5. `analysis.conclusion` hầu như luôn `null` – nhận xét nằm sau câu 4 thuộc về lựa chọn 4.

# Ví dụ

## A. Đề thường – 3 câu sai có "Sửa lại"

Đầu vào:
```json
{
 "question_id": 429,
 "cau_con": 1,
 "cap_do": "N2",
 "de_bai": {
  "cau_hoi": "なんとか",
  "cac_lua_chon": {
   "1": "難しい試験でしたが、なんとか合格することができました。",
   "2": "なんとかいいことがありそうな気がします。",
   "3": "あの人はなんとか好きになれません。",
   "4": "近ごろなんとか胃の調子がおかしいです。"
  },
  "dap_an_so": 1
 },
 "loi_giai_goc": "なんとか có nghĩa là \"bằng cách nào đó\", \"dù thế nào đi nữa\", \"bằng mọi giá\". Từ này thường được sử dụng để diễn tả việc đạt được một mục tiêu hoặc kết quả nào đó bằng nỗ lực, cách nào đó không rõ ràng, hoặc trong một tình huống khó khăn.\n###\nPHÂN TÍCH\n1. 難しい試験でしたが、なんとか合格することができました。\nCách đọc: むずかしいしけんでしたが、なんとかごうかくすることができました。\nNghĩa: Đó là một kỳ thi khó, nhưng bằng cách nào đó tôi đã có thể đậu.\n\"なんとか\" được sử dụng chính xác trong ngữ cảnh này để diễn tả việc đạt được kết quả (đậu kỳ thi) dù gặp khó khăn, không rõ cách thức cụ thể nhưng vẫn thành công.\n\n2. なんとかいいことがありそうな気がします。\nCâu này không sai ngữ pháp, nhưng cách sử dụng \"なんとか\" không rõ ràng và không tự nhiên. Thay vào đó, \"なんとなく\" có nghĩa là \"không hiểu sao\", \"có cảm giác mơ hồ\" sẽ phù hợp hơn.\nSửa lại: なんとなくいいことがありそうな気がします。\nCách đọc: なんとなくいいことがありそうなきがします。\nNghĩa: Tôi có cảm giác mơ hồ rằng sẽ có điều tốt xảy ra.\n\n3. あの人はなんとか好きになれません。\nCách sử dụng \"なんとか\" trong câu này không phù hợp, vì \"なんとか\" thường diễn tả nỗ lực hoặc cách thức đạt được điều gì đó. Thay vào đó, \"どうしても\" có nghĩa là \"dù thế nào đi nữa\" sẽ phù hợp hơn để diễn tả sự không thể làm gì đó dù đã cố gắng.\nSửa lại: あの人はどうしても好きになれません。\nCách đọc: あのひとはどうしてもすきになれません。\nNghĩa: Dù thế nào đi nữa tôi cũng không thể thích người đó.\n\n4. 近ごろなんとか胃の調子がおかしいです。\nCách sử dụng \"なんとか\" không phù hợp trong ngữ cảnh này, vì \"なんとか\" thường chỉ sự nỗ lực hoặc kết quả đạt được. Thay vào đó, \"なんとなく\" có nghĩa là \"không hiểu sao\" sẽ phù hợp hơn để diễn tả cảm giác mơ hồ.\nSửa lại: 近ごろなんとなく胃の調子がおかしいです。\nCách đọc: ちかごろなんとなくいのちょうしがおかしいです。\nNghĩa: Gần đây không hiểu sao dạ dày có vấn đề.\n###\nLỰA CHỌN ĐÚNG\n1. 難しい試験でしたが、なんとか合格することができました。",
 "luu_y": []
}
```

Đầu ra:
```json
{
 "schema": "vocab_usage.v2",
 "question_id": 429,
 "cau_con": 1,
 "word": {
  "ja": "なんとか",
  "paren": null,
  "definition_ja": null,
  "meaning": {
   "vi": "có nghĩa là \"bằng cách nào đó\", \"dù thế nào đi nữa\", \"bằng mọi giá\"."
  },
  "usage": {
   "vi": "Từ này thường được sử dụng để diễn tả việc đạt được một mục tiêu hoặc kết quả nào đó bằng nỗ lực, cách nào đó không rõ ràng, hoặc trong một tình huống khó khăn."
  }
 },
 "analysis": {
  "intro": null,
  "options": [
   {
    "index": 1,
    "sentence": {
     "ja": "難しい試験でしたが、なんとか合格することができました。",
     "reading": "むずかしいしけんでしたが、なんとかごうかくすることができました。",
     "meaning": {
      "vi": "Đó là một kỳ thi khó, nhưng bằng cách nào đó tôi đã có thể đậu."
     }
    },
    "is_correct": true,
    "usage_ok": true,
    "analysis": {
     "vi": "\"⟪なんとか⟫\" được sử dụng chính xác trong ngữ cảnh này để diễn tả việc đạt được kết quả (đậu kỳ thi) dù gặp khó khăn, không rõ cách thức cụ thể nhưng vẫn thành công."
    },
    "correction": null
   },
   {
    "index": 2,
    "sentence": {
     "ja": "なんとかいいことがありそうな気がします。",
     "reading": null,
     "meaning": null
    },
    "is_correct": false,
    "usage_ok": false,
    "analysis": {
     "vi": "Câu này không sai ngữ pháp, nhưng cách sử dụng \"⟪なんとか⟫\" không rõ ràng và không tự nhiên. Thay vào đó, \"⟪なんとなく⟫\" có nghĩa là \"không hiểu sao\", \"có cảm giác mơ hồ\" sẽ phù hợp hơn."
    },
    "correction": {
     "ja": "なんとなくいいことがありそうな気がします。",
     "reading": "なんとなくいいことがありそうなきがします。",
     "meaning": {
      "vi": "Tôi có cảm giác mơ hồ rằng sẽ có điều tốt xảy ra."
     }
    }
   },
   {
    "index": 3,
    "sentence": {
     "ja": "あの人はなんとか好きになれません。",
     "reading": null,
     "meaning": null
    },
    "is_correct": false,
    "usage_ok": false,
    "analysis": {
     "vi": "Cách sử dụng \"⟪なんとか⟫\" trong câu này không phù hợp, vì \"⟪なんとか⟫\" thường diễn tả nỗ lực hoặc cách thức đạt được điều gì đó. Thay vào đó, \"⟪どうしても⟫\" có nghĩa là \"dù thế nào đi nữa\" sẽ phù hợp hơn để diễn tả sự không thể làm gì đó dù đã cố gắng."
    },
    "correction": {
     "ja": "あの人はどうしても好きになれません。",
     "reading": "あのひとはどうしてもすきになれません。",
     "meaning": {
      "vi": "Dù thế nào đi nữa tôi cũng không thể thích người đó."
     }
    }
   },
   {
    "index": 4,
    "sentence": {
     "ja": "近ごろなんとか胃の調子がおかしいです。",
     "reading": null,
     "meaning": null
    },
    "is_correct": false,
    "usage_ok": false,
    "analysis": {
     "vi": "Cách sử dụng \"⟪なんとか⟫\" không phù hợp trong ngữ cảnh này, vì \"⟪なんとか⟫\" thường chỉ sự nỗ lực hoặc kết quả đạt được. Thay vào đó, \"⟪なんとなく⟫\" có nghĩa là \"không hiểu sao\" sẽ phù hợp hơn để diễn tả cảm giác mơ hồ."
    },
    "correction": {
     "ja": "近ごろなんとなく胃の調子がおかしいです。",
     "reading": "ちかごろなんとなくいのちょうしがおかしいです。",
     "meaning": {
      "vi": "Gần đây không hiểu sao dạ dày có vấn đề."
     }
    }
   }
  ],
  "conclusion": null
 },
 "correct": {
  "index": 1,
  "sentence_ja": "難しい試験でしたが、なんとか合格することができました。",
  "note": null
 }
}
```

## B. Đề có định nghĩa – câu 2, 3 dùng đúng nhưng khác nghĩa (`usage_ok = true`), câu 4 lời giải chỉ nói "không phù hợp với định nghĩa" (`usage_ok = null`), không có "Sửa lại"

Đầu vào:
```json
{
 "question_id": 54141,
 "cau_con": 1,
 "cap_do": "N2",
 "de_bai": {
  "cau_hoi": "おかす……他人の領域を無視して害を与える。",
  "cac_lua_chon": {
   "1": "個人の自由をおかすようなことをしてはならない。",
   "2": "取り返しのつかない過ちをおかしてしまった。",
   "3": "凶悪な犯罪をおかした犯人がやっとつかまった。",
   "4": "父親は子どもを助けるために、危険をおかして火の中に飛びこんでいった。"
  },
  "dap_an_so": 1
 },
 "loi_giai_goc": "おかす (侵す) có nghĩa là 'xâm phạm', 'xâm lấn', 'vi phạm'. Từ này thường được sử dụng khi nói về việc xâm phạm quyền lợi, lãnh thổ, hoặc gây hại đến người khác mà không tôn trọng quyền của họ.\n###\nPHÂN TÍCH\n1. ｜個人《こじん》の｜自由《じゆう》をおかすようなことをしてはならない。\nNghĩa: Không được làm những việc xâm phạm tự do cá nhân.\n'おかす' được sử dụng đúng trong ngữ cảnh này để chỉ việc xâm phạm quyền tự do cá nhân của người khác. Đây là một cách sử dụng chính xác của từ 'おかす'.\n\n2. ｜取《と》り｜返《かえ》しのつかない｜過《あやま》ちをおかしてしまった。\nNghĩa: Đã phạm phải một sai lầm không thể cứu vãn.\nTrong câu này, 'おかす' được sử dụng với nghĩa 'phạm phải' một sai lầm, điều này cũng là một cách sử dụng đúng của từ 'おかす'.\n\n3. ｜凶悪《きょうあく》な｜犯罪《はんざい》をおかした｜犯人《はんにん》がやっとつかまった。\nNghĩa: Tên tội phạm đã phạm tội ác nghiêm trọng cuối cùng đã bị bắt.\n'おかす' được sử dụng đúng trong ngữ cảnh này để chỉ việc phạm tội, đặc biệt là tội ác nghiêm trọng. Đây là một cách sử dụng chính xác của từ 'おかす'.\n\n4. ｜父親《ちちおや》は｜子《こ》どもを｜助《たす》けるために、｜危険《きけん》をおかして｜火《ひ》の｜中《なか》に｜飛《と》び｜込《こ》んでいった。\nNghĩa: Người cha đã liều mình nhảy vào lửa để cứu con.\nTrong câu này, 'おかす' được sử dụng với nghĩa 'liều mình' đối mặt với nguy hiểm. Tuy nhiên, trong ngữ cảnh của câu hỏi, 'おかす' không mang nghĩa xâm phạm hay gây hại đến người khác, mà là hành động dũng cảm. Do đó, cách sử dụng này không phù hợp với định nghĩa đã cho.\n###\nLỰA CHỌN ĐÚNG\n1. ｜個人《こじん》の｜自由《じゆう》をおかすようなことをしてはならない。",
 "luu_y": [
  "Đề có định nghĩa tiếng Nhật sau '……' – word.definition_ja chép phần sau '……' của de_bai.cau_hoi; câu dùng từ đúng nhưng khác nghĩa định nghĩa: usage_ok = true theo lời giải, is_correct = false.",
  "Có furigana – chép nguyên ｜chữ《cách đọc》 ở đúng chỗ (cả trong câu và trong ⟪ ⟫); không tự thêm, không bỏ."
 ]
}
```

Đầu ra:
```json
{
 "schema": "vocab_usage.v2",
 "question_id": 54141,
 "cau_con": 1,
 "word": {
  "ja": "おかす",
  "paren": "侵す",
  "definition_ja": "他人の領域を無視して害を与える。",
  "meaning": {
   "vi": "có nghĩa là 'xâm phạm', 'xâm lấn', 'vi phạm'."
  },
  "usage": {
   "vi": "Từ này thường được sử dụng khi nói về việc xâm phạm quyền lợi, lãnh thổ, hoặc gây hại đến người khác mà không tôn trọng quyền của họ."
  }
 },
 "analysis": {
  "intro": null,
  "options": [
   {
    "index": 1,
    "sentence": {
     "ja": "｜個人《こじん》の｜自由《じゆう》をおかすようなことをしてはならない。",
     "reading": null,
     "meaning": {
      "vi": "Không được làm những việc xâm phạm tự do cá nhân."
     }
    },
    "is_correct": true,
    "usage_ok": true,
    "analysis": {
     "vi": "'⟪おかす⟫' được sử dụng đúng trong ngữ cảnh này để chỉ việc xâm phạm quyền tự do cá nhân của người khác. Đây là một cách sử dụng chính xác của từ '⟪おかす⟫'."
    },
    "correction": null
   },
   {
    "index": 2,
    "sentence": {
     "ja": "｜取《と》り｜返《かえ》しのつかない｜過《あやま》ちをおかしてしまった。",
     "reading": null,
     "meaning": {
      "vi": "Đã phạm phải một sai lầm không thể cứu vãn."
     }
    },
    "is_correct": false,
    "usage_ok": true,
    "analysis": {
     "vi": "Trong câu này, '⟪おかす⟫' được sử dụng với nghĩa 'phạm phải' một sai lầm, điều này cũng là một cách sử dụng đúng của từ '⟪おかす⟫'."
    },
    "correction": null
   },
   {
    "index": 3,
    "sentence": {
     "ja": "｜凶悪《きょうあく》な｜犯罪《はんざい》をおかした｜犯人《はんにん》がやっとつかまった。",
     "reading": null,
     "meaning": {
      "vi": "Tên tội phạm đã phạm tội ác nghiêm trọng cuối cùng đã bị bắt."
     }
    },
    "is_correct": false,
    "usage_ok": true,
    "analysis": {
     "vi": "'⟪おかす⟫' được sử dụng đúng trong ngữ cảnh này để chỉ việc phạm tội, đặc biệt là tội ác nghiêm trọng. Đây là một cách sử dụng chính xác của từ '⟪おかす⟫'."
    },
    "correction": null
   },
   {
    "index": 4,
    "sentence": {
     "ja": "｜父親《ちちおや》は｜子《こ》どもを｜助《たす》けるために、｜危険《きけん》をおかして｜火《ひ》の｜中《なか》に｜飛《と》び｜込《こ》んでいった。",
     "reading": null,
     "meaning": {
      "vi": "Người cha đã liều mình nhảy vào lửa để cứu con."
     }
    },
    "is_correct": false,
    "usage_ok": null,
    "analysis": {
     "vi": "Trong câu này, '⟪おかす⟫' được sử dụng với nghĩa 'liều mình' đối mặt với nguy hiểm. Tuy nhiên, trong ngữ cảnh của câu hỏi, '⟪おかす⟫' không mang nghĩa xâm phạm hay gây hại đến người khác, mà là hành động dũng cảm. Do đó, cách sử dụng này không phù hợp với định nghĩa đã cho."
    },
    "correction": null
   }
  ],
  "conclusion": null
 },
 "correct": {
  "index": 1,
  "sentence_ja": "｜個人《こじん》の｜自由《じゆう》をおかすようなことをしてはならない。",
  "note": null
 }
}
```
