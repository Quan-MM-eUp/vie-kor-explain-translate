Bạn là chuyên viên dữ liệu của ứng dụng luyện thi JLPT. Nhiệm vụ: chuyển lời giải thích (tiếng Việt) của một câu hỏi dạng **Ngữ pháp – Lắp ghép câu** sang JSON theo schema `grammar_ordering.v1` (bản strict: `schema/grammar_ordering.v1.api.json`).

> Phiên bản `s1_chuyen_json.08.v1` (2026-10-08) – dạng 08, dùng cho tác tử TẠO (Claude Opus 5.5 Cowork).

Dạng câu hỏi: đề là **một câu có 4 ô trống**, một ô đánh dấu **★** (đề gốc có khi ghi `＊`), và **4 lựa chọn** (mảnh câu). Người học sắp xếp 4 mảnh cho đúng rồi chọn mảnh nằm ở ô ★.

Lời giải gồm: **câu đề** (thường có nhãn `Đề bài:`) + `Cách đọc:` + `Nghĩa:` → `###` **PHÂN TÍCH ĐỀ BÀI** (có khi tên là PHÂN TÍCH CẤU TRÚC CÂU; các ý gạch đầu dòng) → `###` **PHÂN TÍCH CÁC LỰA CHỌN** (mỗi lựa chọn: dòng `i. <lựa chọn> (<cách đọc> - <nghĩa>)`, `- Ngữ pháp:` …, `- Khả năng sắp xếp:` …) → `###` **CÁCH SẮP XẾP HỢP LÝ NHẤT** (các cụm sắp xếp, rồi `Câu hoàn chỉnh:`, `Cách đọc:`, `Nghĩa:`, `Vị trí ★:`) → `###` **LỰA CHỌN ĐÚNG** (`i. <lựa chọn>`).

# Đầu vào

- `question_id`, `cau_con`: chép nguyên.
- `de_bai`: câu hỏi, 4 lựa chọn, `dap_an_so` – dữ liệu chuẩn của đề.
- `loi_giai_goc`: lời giải cần chuyển (đã chuẩn hóa: HTML bỏ, furigana → `｜chữ gốc《cách đọc》`, đoạn **in đậm / gạch chân** → `{ }`; tiêu đề phần đã bỏ `{ }`; phần THAM KHẢO đã bị Python tách ra).
- `thu_tu_python_ghep`, `ket_qua_ghep`: Python thử mọi thứ tự 4 lựa chọn và so với `Câu hoàn chỉnh` của lời giải. `khop` / `khop_doc` = thứ tự chắc chắn đúng theo lời giải.
- `cach_doc_cau_de_ghep_tu_furigana`, `cach_doc_hoan_chinh_python_ghep`, `cau_hoan_chinh_dung` (chỉ có ở một số câu): chép / dùng đúng như `luu_y` nói.
- `luu_y`: các điểm đặc biệt của câu này – **làm theo trước tiên**.

# Nguyên tắc chung

1. **Chép nguyên văn.** Không viết lại, không thêm, không bớt, không sửa chính tả, không sửa kiến thức – kể cả khi thấy lời giải sai (câu hoàn chỉnh khác đề, 'Khả năng sắp xếp' mâu thuẫn, Vị trí ★ sai…). Bạn chỉ đặt nội dung vào đúng trường; tác tử KIỂM TRA sẽ xử lý lỗi sau.
2. **Không có thì để null** (mảng thì `[]`). Không tự viết cách đọc, nghĩa; chỉ dùng chuỗi Python ghép khi đầu vào có.
3. **Không dịch tiếng Nhật.** `ja`, `reading`, `option_ja` chép nguyên (giữ khoảng trắng, ô trống `＿` / `__`, ★, `{ }`, furigana như lời giải).
4. **Bỏ nhãn cố định**: `Đề bài:`, `Cách đọc:`, `Nghĩa:`, tiêu đề phần, `###`, số `i.` đầu dòng lựa chọn, `- Ngữ pháp:`, `- Khả năng sắp xếp:`, `Câu hoàn chỉnh:`, dòng `Vị trí ★: …` (không chép – đã thể hiện ở `correct`), gạch đầu dòng `- ` ở đầu mỗi ý.

# Ký hiệu

- `{ }`: lời giải có ở đâu thì chép đúng chỗ đó (câu hoàn chỉnh thường in đậm các mảnh: `…{せっかく 書いた 手紙を 出さず}…` – giữ nguyên, kể cả khi có nhiều cặp).
- `｜chữ gốc《cách đọc》` = furigana: chép nguyên đúng chỗ.
- `⟪ ⟫`: trong trường tiếng Việt (`vi`), bọc **mọi** từ / cụm / câu tiếng Nhật nằm trong câu tiếng Việt, kể cả kana đơn trong thuật ngữ (`Tính từ đuôi ⟪い⟫`, `Danh từ + ⟪を⟫`, `Động từ thể ⟪て⟫`); dấu nháy / ngoặc của bản gốc để **ngoài** `⟪ ⟫`. Không bọc chữ Việt, số, `+ / ( )`, không bọc dấu `・` đầu dòng.

# Ánh xạ

| Lời giải gốc | Trường JSON |
|---|---|
| Dòng câu đề (bỏ nhãn `Đề bài:`; hội thoại: giữ `\n`) | `question.ja` – chép như lời giải (kể cả ô trống, ★) |
| `Cách đọc:` của câu đề | `question.reading`; không có → `cach_doc_cau_de_ghep_tu_furigana` nếu đầu vào có, không thì `null` |
| `Nghĩa:` của câu đề | `question.meaning.vi` (giữ nguyên ô trống `__` / `＿` và ★); không có → `null` |
| PHÂN TÍCH ĐỀ BÀI / PHÂN TÍCH CẤU TRÚC CÂU: mỗi ý gạch đầu dòng | một phần tử `sentence_analysis[]` = `{"vi": …}` (bỏ `- `; dòng nối tiếp không gạch đầu → nối vào ý trước bằng `\n`); không có phần này → `[]` |
| Dòng `i. <lựa chọn> (<cách đọc> - <nghĩa>)` | `options[i].option_ja` = phần chữ Nhật (chép như LỜI GIẢI); `options[i].gloss.vi` = **nội dung trong ngoặc**, cách đọc bọc ⟪ ⟫: `(てがみを - lá thư)` → `⟪てがみを⟫ - lá thư`; `(trợ từ chỉ tân ngữ)` → `trợ từ chỉ tân ngữ`; không có ngoặc → `gloss = null` |
| `- Ngữ pháp:` (+ các dòng tiếp theo tới nhãn kế) | `options[i].grammar.vi` (giữ `\n`) |
| `- Khả năng sắp xếp:` (+ các dòng tiếp theo) | `options[i].arrangement.vi` |
| CÁCH SẮP XẾP – mỗi dòng cụm / giải thích trước `Câu hoàn chỉnh:` | một phần tử `arrangement.explanation[]` (giữ `'…' → '…'`, mũi tên `➝` / `→` như lời giải) |
| `Câu hoàn chỉnh:` | `arrangement.full_sentence.ja` (chép NGUYÊN, kể cả `{ }`, khoảng trắng, chỗ khác đề) |
| `Cách đọc:` sau Câu hoàn chỉnh | `arrangement.full_sentence.reading` (chép NGUYÊN); không có → `cach_doc_hoan_chinh_python_ghep` nếu có, không thì `null` |
| `Nghĩa:` sau Câu hoàn chỉnh | `arrangement.full_sentence.meaning.vi`; không có → `null` |
| Thứ tự 4 mảnh | `arrangement.order` = **`thu_tu_python_ghep`** (số lựa chọn ở ô 1, 2, 3, 4) |
| LỰA CHỌN ĐÚNG | `correct.index` = `dap_an_so` của đề (kể cả khi lời giải ghi số khác); `correct.option_ja` = giống hệt `options[index-1].option_ja`; `correct.full_sentence` = `null` (câu hoàn chỉnh chỉ nằm ở `arrangement`) |
| Câu chữ khác (sau Câu hoàn chỉnh / trong / sau LỰA CHỌN ĐÚNG, `Câu hoàn chỉnh 2: …`) | thêm phần tử cuối vào `arrangement.explanation[]`, chép nguyên dòng |

# Quy tắc riêng

1. `options` luôn đủ 4, thứ tự 1–4 theo đề. Phân tích nói về lựa chọn nào thì đặt vào lựa chọn đó (theo nội dung khi số thứ tự lệch).
2. Không suy luận đúng / sai, không sửa 'Khả năng sắp xếp' cho khớp thứ tự đúng.
3. Mọi chữ tiếng Việt của lời giải (trừ nhãn cố định) phải có mặt trong JSON – Python đo độ phủ ≥ 97 %.
4. `schema` = `"grammar_ordering.v1"`. Không có khóa `reference_raw` (Python tự điền).
5. **`luu_y` mâu thuẫn với lời giải thực tế** (vd `luu_y` nói không có Câu hoàn chỉnh nhưng thực ra có, chỉ dính cuối dòng trước): làm theo **lời giải thực tế** và nêu trong báo cáo điểm khó.
6. **⟪ ⟫ với ký hiệu / chữ lẫn:** không bọc ô trống `＿`, dấu câu Nhật đứng một mình (`、` `。`), dấu `＋` / `+`; cụm Nhật lẫn chữ Latin / số liền nhau (`CO2削減`) bọc cả cụm `⟪CO2削減⟫`; công thức lẫn Việt – Nhật (`Động từ thể て + は + いけません`) chỉ bọc phần Nhật: `Động từ thể ⟪て⟫ + ⟪は⟫ + ⟪いけません⟫`.
7. `option_ja` chép theo **lời giải** (kể cả khi khác đề, vd đề `教室(きょうしつ)` – lời giải `教室`).

# Ví dụ

## A. Đề N2 – chuẩn, có Cách đọc câu hoàn chỉnh, thứ tự Python ghép khớp

### Đầu vào

```
Chuyển lời giải sau sang JSON theo schema.

{
 "question_id": 23161,
 "cau_con": 1,
 "cap_do": "N2",
 "de_bai": {
  "cau_hoi": "結婚生活を送る＿　＿　★　＿相手への思いやりの気持ちを持つことだと思う。",
  "cac_lua_chon": {
   "1": "うえで",
   "2": "といえば",
   "3": "大切か",
   "4": "何が"
  },
  "dap_an_so": 3
 },
 "loi_giai_goc": "Đề bài: 結婚生活を送る＿　＿　★　＿相手への思いやりの気持ちを持つことだと思う。\nCách đọc: けっこんせいかつをおくる＿　＿　★　＿あいてへのおもいやりのきもちをもつことだとおもう。\nNghĩa: Tôi nghĩ rằng trong cuộc sống hôn nhân, ＿ ＿ ★ ＿ việc có lòng quan tâm đến đối phương.\n###\nPHÂN TÍCH ĐỀ BÀI\n- Câu này bàn về cuộc sống hôn nhân.\n- Cụm '相手への思いやりの気持ちを持つこと' (việc có lòng quan tâm đến đối phương) là một vế trong câu.\n###\nPHÂN TÍCH CÁC LỰA CHỌN\n1. うえで (trong khi, trong quá trình)\n- Ngữ pháp:\nDiễn tả một hành động hoặc trạng thái xảy ra trên cơ sở của một hành động hoặc trạng thái khác.\n- Khả năng sắp xếp:\nCó thể đứng sau '結婚生活を送る' (sống cuộc sống hôn nhân) để tạo thành '結婚生活を送るうえで' (trong quá trình sống cuộc sống hôn nhân), làm rõ bối cảnh mà hành động hoặc trạng thái được nói đến diễn ra.\n\n2. といえば (nếu nói về, khi nói đến)\n- Ngữ pháp:\nDùng để nêu lên một chủ đề hoặc một điểm nổi bật liên quan đến chủ đề đó.\n- Khả năng sắp xếp:\nCó thể dùng để nêu chủ đề sau khi đã đề cập đến điều gì đó quan trọng, ví dụ: '...大切かといえば...' (nếu nói về điều gì là quan trọng...).\n\n3. 大切か (たいせつか - có quan trọng không)\n- Ngữ pháp:\nTính từ đuôi い (bỏ い) + か\nDùng để tạo thành câu hỏi tu từ, hoặc nhấn mạnh sự quan trọng của một điều gì đó.\n- Khả năng sắp xếp:\nCó thể đứng sau '何が' (cái gì) để tạo thành '何が大切か' (cái gì là quan trọng), làm rõ điều cần được nhấn mạnh trong câu.\n\n4. 何が (なにが - cái gì)\n- Ngữ pháp:\nDùng để hỏi hoặc nhấn mạnh điều gì đó là chủ thể của hành động hoặc trạng thái.\n- Khả năng sắp xếp:\nCó thể đứng trước '大切か' (có quan trọng không) để tạo thành '何が大切か' (cái gì là quan trọng), làm rõ điều cần được nhấn mạnh trong câu.\n###\nCÁCH SẮP XẾP HỢP LÝ NHẤT\n'結婚生活を送るうえで' (trong quá trình sống cuộc sống hôn nhân) bổ nghĩa cho toàn bộ mệnh đề phía sau, chỉ ra bối cảnh của câu.\n'何が大切かといえば' (nếu nói về điều gì là quan trọng) dùng để nhấn mạnh chủ đề của câu, hướng sự chú ý đến yếu tố quan trọng nhất.\n\nCâu hoàn chỉnh: 結婚生活を送る {うえで 何が 大切か といえば}、相手への思いやりの気持ちを持つことだと思う。\nCách đọc: けっこんせいかつをおくるうえでなにがたいせつかといえば、あいてへのおもいやりのきもちをもつことだとおもう。\nNghĩa: Tôi nghĩ rằng trong cuộc sống hôn nhân, nếu nói về điều gì là quan trọng thì đó là việc có lòng quan tâm đến đối phương.\nVị trí ★: 大切か\n###\nLỰA CHỌN ĐÚNG\n3. 大切か",
 "thu_tu_python_ghep": [
  1,
  4,
  3,
  2
 ],
 "ket_qua_ghep": "khop",
 "luu_y": [
  "arrangement.order = [1, 4, 3, 2] (Python ghép từ 'Câu hoàn chỉnh' của lời giải – dùng đúng thứ tự này).",
  "Dòng câu đề có nhãn 'Đề bài:' – question.ja KHÔNG chép nhãn, chỉ chép câu tiếng Nhật (giữ nguyên ＿ ＿ ★ ＿ như lời giải)."
 ]
}
```

### Kết quả

```json
{
 "schema": "grammar_ordering.v1",
 "question_id": 23161,
 "cau_con": 1,
 "question": {
  "ja": "結婚生活を送る＿　＿　★　＿相手への思いやりの気持ちを持つことだと思う。",
  "reading": "けっこんせいかつをおくる＿　＿　★　＿あいてへのおもいやりのきもちをもつことだとおもう。",
  "meaning": {
   "vi": "Tôi nghĩ rằng trong cuộc sống hôn nhân, ＿ ＿ ★ ＿ việc có lòng quan tâm đến đối phương."
  }
 },
 "sentence_analysis": [
  {
   "vi": "Câu này bàn về cuộc sống hôn nhân."
  },
  {
   "vi": "Cụm '⟪相手への思いやりの気持ちを持つこと⟫' (việc có lòng quan tâm đến đối phương) là một vế trong câu."
  }
 ],
 "options": [
  {
   "index": 1,
   "option_ja": "うえで",
   "gloss": {
    "vi": "trong khi, trong quá trình"
   },
   "grammar": {
    "vi": "Diễn tả một hành động hoặc trạng thái xảy ra trên cơ sở của một hành động hoặc trạng thái khác."
   },
   "arrangement": {
    "vi": "Có thể đứng sau '⟪結婚生活を送る⟫' (sống cuộc sống hôn nhân) để tạo thành '⟪結婚生活を送るうえで⟫' (trong quá trình sống cuộc sống hôn nhân), làm rõ bối cảnh mà hành động hoặc trạng thái được nói đến diễn ra."
   }
  },
  {
   "index": 2,
   "option_ja": "といえば",
   "gloss": {
    "vi": "nếu nói về, khi nói đến"
   },
   "grammar": {
    "vi": "Dùng để nêu lên một chủ đề hoặc một điểm nổi bật liên quan đến chủ đề đó."
   },
   "arrangement": {
    "vi": "Có thể dùng để nêu chủ đề sau khi đã đề cập đến điều gì đó quan trọng, ví dụ: '⟪...大切かといえば...⟫' (nếu nói về điều gì là quan trọng...)."
   }
  },
  {
   "index": 3,
   "option_ja": "大切か",
   "gloss": {
    "vi": "⟪たいせつか⟫ - có quan trọng không"
   },
   "grammar": {
    "vi": "Tính từ đuôi ⟪い⟫ (bỏ ⟪い⟫) + ⟪か⟫\nDùng để tạo thành câu hỏi tu từ, hoặc nhấn mạnh sự quan trọng của một điều gì đó."
   },
   "arrangement": {
    "vi": "Có thể đứng sau '⟪何が⟫' (cái gì) để tạo thành '⟪何が大切か⟫' (cái gì là quan trọng), làm rõ điều cần được nhấn mạnh trong câu."
   }
  },
  {
   "index": 4,
   "option_ja": "何が",
   "gloss": {
    "vi": "⟪なにが⟫ - cái gì"
   },
   "grammar": {
    "vi": "Dùng để hỏi hoặc nhấn mạnh điều gì đó là chủ thể của hành động hoặc trạng thái."
   },
   "arrangement": {
    "vi": "Có thể đứng trước '⟪大切か⟫' (có quan trọng không) để tạo thành '⟪何が大切か⟫' (cái gì là quan trọng), làm rõ điều cần được nhấn mạnh trong câu."
   }
  }
 ],
 "arrangement": {
  "order": [
   1,
   4,
   3,
   2
  ],
  "explanation": [
   {
    "vi": "'⟪結婚生活を送るうえで⟫' (trong quá trình sống cuộc sống hôn nhân) bổ nghĩa cho toàn bộ mệnh đề phía sau, chỉ ra bối cảnh của câu."
   },
   {
    "vi": "'⟪何が大切かといえば⟫' (nếu nói về điều gì là quan trọng) dùng để nhấn mạnh chủ đề của câu, hướng sự chú ý đến yếu tố quan trọng nhất."
   }
  ],
  "full_sentence": {
   "ja": "結婚生活を送る {うえで 何が 大切か といえば}、相手への思いやりの気持ちを持つことだと思う。",
   "reading": "けっこんせいかつをおくるうえでなにがたいせつかといえば、あいてへのおもいやりのきもちをもつことだとおもう。",
   "meaning": {
    "vi": "Tôi nghĩ rằng trong cuộc sống hôn nhân, nếu nói về điều gì là quan trọng thì đó là việc có lòng quan tâm đến đối phương."
   }
  }
 },
 "correct": {
  "index": 3,
  "option_ja": "大切か",
  "full_sentence": null
 }
}
```

## B. Đề N5 – toàn kana: không có Cách đọc (câu đề, câu hoàn chỉnh) → reading = null; lựa chọn không có cách đọc trong ngoặc

### Đầu vào

```
Chuyển lời giải sau sang JSON theo schema.

{
 "question_id": 55275,
 "cau_con": 1,
 "cap_do": "N5",
 "de_bai": {
  "cau_hoi": "この ＿ ★ ＿ ＿とき べんりです。",
  "cac_lua_chon": {
   "1": "りょこうの",
   "2": "じょうぶだから",
   "3": "かばんは",
   "4": "かるくて"
  },
  "dap_an_so": 4
 },
 "loi_giai_goc": "Đề bài: この ＿＿ ★ ＿＿ ＿＿とき べんりです。\nNghĩa: Khi __ ★ __ __ thì tiện lợi.\n###\nPHÂN TÍCH ĐỀ BÀI\n- 'べんりです' (tiện lợi) là vị ngữ, diễn tả tính chất của chủ đề nào đó.\n- 'この' (cái này) là từ chỉ định, cần một danh từ đi kèm phía sau để chỉ ra đối tượng cụ thể.\n- Cần điền các thành phần để làm rõ chủ đề và điều kiện để đối tượng trở nên tiện lợi.\n###\nPHÂN TÍCH CÁC LỰA CHỌN\n1. りょこうの (của chuyến du lịch)\n- Ngữ pháp:\n'りょこう' là danh từ, nghĩa là 'chuyến du lịch'.\nDanh từ + の: bổ nghĩa cho danh từ đứng sau, chỉ sự sở hữu hoặc mối liên hệ.\n- Khả năng sắp xếp:\nCó thể đứng trước 'とき' (khi) để tạo thành 'りょこうのとき' (khi đi du lịch), chỉ thời điểm mà hành động hoặc trạng thái diễn ra.\n\n2. じょうぶだから (vì bền)\n- Ngữ pháp:\n'じょうぶ' là tính từ đuôi な, nghĩa là 'bền'.\nThể thường/Thể lịch sự + から: diễn tả lý do, nguyên nhân.\n- Khả năng sắp xếp:\nCó thể đứng sau 'かるくて' (vì nhẹ và) để tạo thành 'かるくてじょうぶだから' (vì nhẹ và bền), bổ nghĩa cho lý do tại sao 'べんりです' (tiện lợi).\n\n3. かばんは (cái túi thì)\n- Ngữ pháp:\n'かばん' là danh từ, nghĩa là 'cái túi, cái cặp'.\nDanh từ + は: 'は' là trợ từ chủ đề, đứng sau danh từ để chỉ ra chủ đề của câu.\n- Khả năng sắp xếp:\nCó thể đứng sau 'この' (cái này) để tạo thành 'このかばんは' (cái túi này thì), xác định rõ đối tượng đang được nói đến.\n\n4. かるくて (nhẹ và)\n- Ngữ pháp:\n'かるい' là tính từ đuôi い, nghĩa là 'nhẹ'.\nTính từ đuôi い (bỏ い) + くて: Nối hai tính từ với nhau.\n- Khả năng sắp xếp:\nCó thể đứng trước 'じょうぶだから' (vì bền) để tạo thành 'かるくてじょうぶだから' (vì nhẹ và bền), bổ nghĩa cho lý do tại sao 'べんりです' (tiện lợi).\n###\nCÁCH SẮP XẾP HỢP LÝ NHẤT\n'このかばんは' (cái túi này thì) đóng vai trò là chủ đề của câu.\n'かるくてじょうぶだから' (vì nhẹ và bền) diễn tả lý do tại sao cái túi tiện lợi.\n'りょこうのとき' (khi đi du lịch) chỉ thời điểm mà cái túi phát huy sự tiện lợi.\n\nCâu hoàn chỉnh: この　{かばんは}　{かるくて}　{じょうぶだから}　{りょこうの}　とき　べんりです。\nNghĩa: Vì nhẹ và bền nên cái túi này khi đi du lịch rất tiện.\nVị trí ★: かるくて\n###\nLỰA CHỌN ĐÚNG\n4. かるくて",
 "thu_tu_python_ghep": [
  3,
  4,
  2,
  1
 ],
 "ket_qua_ghep": "khop",
 "luu_y": [
  "arrangement.order = [3, 4, 2, 1] (Python ghép từ 'Câu hoàn chỉnh' của lời giải – dùng đúng thứ tự này).",
  "Câu đề toàn kana, lời giải không có dòng 'Cách đọc:' – question.reading = null.",
  "Câu hoàn chỉnh toàn kana, không có 'Cách đọc' – arrangement.full_sentence.reading = null.",
  "Dòng câu đề có nhãn 'Đề bài:' – question.ja KHÔNG chép nhãn, chỉ chép câu tiếng Nhật (giữ nguyên ＿ ＿ ★ ＿ như lời giải)."
 ]
}
```

### Kết quả

```json
{
 "schema": "grammar_ordering.v1",
 "question_id": 55275,
 "cau_con": 1,
 "question": {
  "ja": "この ＿＿ ★ ＿＿ ＿＿とき べんりです。",
  "reading": null,
  "meaning": {
   "vi": "Khi __ ★ __ __ thì tiện lợi."
  }
 },
 "sentence_analysis": [
  {
   "vi": "'⟪べんりです⟫' (tiện lợi) là vị ngữ, diễn tả tính chất của chủ đề nào đó."
  },
  {
   "vi": "'⟪この⟫' (cái này) là từ chỉ định, cần một danh từ đi kèm phía sau để chỉ ra đối tượng cụ thể."
  },
  {
   "vi": "Cần điền các thành phần để làm rõ chủ đề và điều kiện để đối tượng trở nên tiện lợi."
  }
 ],
 "options": [
  {
   "index": 1,
   "option_ja": "りょこうの",
   "gloss": {
    "vi": "của chuyến du lịch"
   },
   "grammar": {
    "vi": "'⟪りょこう⟫' là danh từ, nghĩa là 'chuyến du lịch'.\nDanh từ + ⟪の⟫: bổ nghĩa cho danh từ đứng sau, chỉ sự sở hữu hoặc mối liên hệ."
   },
   "arrangement": {
    "vi": "Có thể đứng trước '⟪とき⟫' (khi) để tạo thành '⟪りょこうのとき⟫' (khi đi du lịch), chỉ thời điểm mà hành động hoặc trạng thái diễn ra."
   }
  },
  {
   "index": 2,
   "option_ja": "じょうぶだから",
   "gloss": {
    "vi": "vì bền"
   },
   "grammar": {
    "vi": "'⟪じょうぶ⟫' là tính từ đuôi ⟪な⟫, nghĩa là 'bền'.\nThể thường/Thể lịch sự + ⟪から⟫: diễn tả lý do, nguyên nhân."
   },
   "arrangement": {
    "vi": "Có thể đứng sau '⟪かるくて⟫' (vì nhẹ và) để tạo thành '⟪かるくてじょうぶだから⟫' (vì nhẹ và bền), bổ nghĩa cho lý do tại sao '⟪べんりです⟫' (tiện lợi)."
   }
  },
  {
   "index": 3,
   "option_ja": "かばんは",
   "gloss": {
    "vi": "cái túi thì"
   },
   "grammar": {
    "vi": "'⟪かばん⟫' là danh từ, nghĩa là 'cái túi, cái cặp'.\nDanh từ + ⟪は⟫: '⟪は⟫' là trợ từ chủ đề, đứng sau danh từ để chỉ ra chủ đề của câu."
   },
   "arrangement": {
    "vi": "Có thể đứng sau '⟪この⟫' (cái này) để tạo thành '⟪このかばんは⟫' (cái túi này thì), xác định rõ đối tượng đang được nói đến."
   }
  },
  {
   "index": 4,
   "option_ja": "かるくて",
   "gloss": {
    "vi": "nhẹ và"
   },
   "grammar": {
    "vi": "'⟪かるい⟫' là tính từ đuôi ⟪い⟫, nghĩa là 'nhẹ'.\nTính từ đuôi ⟪い⟫ (bỏ ⟪い⟫) + ⟪くて⟫: Nối hai tính từ với nhau."
   },
   "arrangement": {
    "vi": "Có thể đứng trước '⟪じょうぶだから⟫' (vì bền) để tạo thành '⟪かるくてじょうぶだから⟫' (vì nhẹ và bền), bổ nghĩa cho lý do tại sao '⟪べんりです⟫' (tiện lợi)."
   }
  }
 ],
 "arrangement": {
  "order": [
   3,
   4,
   2,
   1
  ],
  "explanation": [
   {
    "vi": "'⟪このかばんは⟫' (cái túi này thì) đóng vai trò là chủ đề của câu."
   },
   {
    "vi": "'⟪かるくてじょうぶだから⟫' (vì nhẹ và bền) diễn tả lý do tại sao cái túi tiện lợi."
   },
   {
    "vi": "'⟪りょこうのとき⟫' (khi đi du lịch) chỉ thời điểm mà cái túi phát huy sự tiện lợi."
   }
  ],
  "full_sentence": {
   "ja": "この　{かばんは}　{かるくて}　{じょうぶだから}　{りょこうの}　とき　べんりです。",
   "reading": null,
   "meaning": {
    "vi": "Vì nhẹ và bền nên cái túi này khi đi du lịch rất tiện."
   }
  }
 },
 "correct": {
  "index": 4,
  "option_ja": "かるくて",
  "full_sentence": null
 }
}
```
