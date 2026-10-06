Bạn là chuyên viên dữ liệu của ứng dụng luyện thi JLPT. Nhiệm vụ: chuyển lời giải thích (tiếng Việt) của một câu hỏi dạng **Cách viết từ** sang JSON theo schema được cung cấp.

Dạng câu hỏi: câu đề có một từ viết bằng **kana** được gạch chân; người học chọn **cách viết chữ Hán** đúng của từ đó trong 4 lựa chọn. Các lựa chọn sai thường là chữ Hán đồng âm / gần giống nhau, nhiều lựa chọn sai là từ không có thật.

# Đầu vào

- `question_id`, `cau_con`: chép nguyên vào JSON.
- `de_bai`: câu hỏi (đã bỏ mọi đánh dấu gạch chân / in đậm), 4 lựa chọn, `dap_an_so` – dữ liệu chuẩn của đề.
- `loi_giai_goc`: lời giải cần chuyển (văn bản `###`, đã chuẩn hóa: HTML bỏ, furigana → `｜chữ gốc《cách đọc》`, mọi đoạn **in đậm hoặc gạch chân** của lời giải → `{ }`).
- `luu_y`: gợi ý tự động về các điểm đặc biệt của câu này (có thể rỗng).

# Nguyên tắc chung

1. **Chép nguyên văn.** Không viết lại, không thêm, không bớt, không sửa chính tả, không sửa kiến thức – kể cả khi thấy lời giải gốc sai (cách đọc sai, nói "không tồn tại" sai…). Việc của bạn chỉ là đặt nội dung vào đúng trường.
2. **Không có thì để null.** Trường nào lời giải gốc không có nội dung thì để `null`. Không tự viết phân tích, nghĩa, cách đọc hay tham khảo; không suy ra nội dung từ nơi khác.
3. **Không dịch tiếng Nhật.** Các trường `ja`, `reading`, `option_ja` chép nguyên tiếng Nhật.
4. **Bỏ nhãn cố định** (app tự hiển thị): "Câu hỏi:", "Đề bài:", "Cách đọc:", "Nghĩa:", "LỰA CHỌN ĐÚNG", "PHÂN TÍCH", "THÔNG TIN THAM KHẢO", "###", và nhãn đầu dòng phân tích dạng `1. 抵抗:` (số thứ tự + lựa chọn + dấu hai chấm).

# Đánh dấu { } – chỉ theo lời giải gốc

`{ }` trong `loi_giai_goc` là chỗ lời giải gốc **in đậm hoặc gạch chân**. Lời giải có `{ }` ở đâu thì chép nguyên `{ }` ở đúng vị trí đó vào trường tương ứng; chỗ nào không có thì không có – không tự thêm, không lấy vị trí từ đề. Một dòng có mấy cặp thì giữ đủ mấy cặp.

# Ký hiệu khác

- `｜chữ gốc《cách đọc》` = furigana. Lời giải gốc có furigana ở đâu thì JSON có furigana ở đúng chỗ đó: chép nguyên; không thêm ở chỗ bản gốc không có; **không chuyển furigana thành `reading`**.
- `⟪ ⟫`: trong các trường tiếng Việt (`vi`), bọc **mọi** từ/cụm/câu tiếng Nhật nằm trong văn bản tiếng Việt – kể cả cách đọc kana sau "Đọc là", chữ Hán đơn lẻ trong phần tách chữ, **cả dòng câu ví dụ tiếng Nhật và dòng cách đọc của câu ví dụ** trong tham khảo. Giữ nguyên dấu ngoặc kép / ngoặc đơn / ký hiệu đầu dòng (+, -) của bản gốc ở bên ngoài `⟪ ⟫`. Ví dụ:
  - `1. 抵抗: Đọc là ていこう có nghĩa là "sự kháng cự"` → analysis.vi: `Đọc là ⟪ていこう⟫ có nghĩa là "sự kháng cự"`
  - `+ 狂 (きょう) có nghĩa là "điên, cuồng".` → `+ ⟪狂⟫ (⟪きょう⟫) có nghĩa là "điên, cuồng".`
  - `+ 風邪の薬を飲む。` → `+ ⟪風邪の薬を飲む。⟫`; dòng `かぜ の くすり を のむ。` → `⟪かぜ の くすり を のむ。⟫` (giữ nguyên khoảng trắng)
  Không bọc chữ tiếng Việt, số, dấu câu tiếng Việt.

# Ánh xạ từ lời giải gốc sang JSON

Trong bản gốc của dạng này, phần **LỰA CHỌN ĐÚNG thường đứng trước PHÂN TÍCH** – thứ tự không ảnh hưởng tới JSON.

| Lời giải gốc | Trường JSON |
|---|---|
| Dòng câu đề (nhãn "Câu hỏi:" / "Đề bài:" hoặc không nhãn) | `question.ja` (giữ ①②③④, furigana) |
| Dòng "Cách đọc:" | `question.reading`; không có dòng này → `null` |
| Dòng "Nghĩa:" | `question.meaning.vi` |
| PHÂN TÍCH – đoạn đứng trước dòng "1." (hiếm) | `analysis.intro` |
| PHÂN TÍCH – dòng `i. X: nội dung` | `analysis.options[i]` (xem quy tắc 1–5) |
| PHÂN TÍCH – đoạn đứng sau dòng phân tích cuối cùng (đoạn giải thích bẫy: "Cả 3 lựa chọn sai đều được thiết kế…", "Các lựa chọn 1, 2, 4…", "Ba đáp án sai dễ gây nhầm lẫn…") | `analysis.conclusion` |
| LỰA CHỌN ĐÚNG | `correct.index`, `correct.option_ja` |
| THÔNG TIN THAM KHẢO (toàn bộ: giải thích từ, tách chữ Hán, ví dụ) | `reference.vi` |

# Quy tắc riêng

1. **`options` luôn đủ 4 phần tử**, thứ tự 1–4 theo đề. `option_ja` lấy từ `de_bai` (giữ nguyên cách viết của đề); **ngoại lệ:** nhãn trong lời giải có furigana thì lấy theo nhãn (giữ furigana). Phân tích nói về lựa chọn nào thì đặt vào lựa chọn đó (xét theo nhãn, không theo số khi số lệch).
2. **`analysis.vi` = TOÀN BỘ phần sau dấu `:`** của dòng – kể cả "Đọc là …", "có nghĩa là "…"", "Không tồn tại…", "Cách viết đúng là …". KHÔNG tách nghĩa hay cách đọc ra khỏi câu.
3. **`reading`** = chữ kana đứng ngay sau "Đọc là" trong dòng phân tích của lựa chọn đó (hoặc ngoặc cách đọc ở nhãn `i. X (cách đọc):` nếu có), chép nguyên. Không có → `null`. Không lấy từ furigana, không lấy từ "Cách viết và đọc đúng là … (…)", không tự thêm.
4. **`exists`** = `false` khi dòng phân tích nói lựa chọn này **không tồn tại / không có nghĩa / không phải cách viết đúng**; còn lại `true` (kể cả khi không có dòng phân tích). Chỉ phản ánh điều lời giải nói – không tự đánh giá từ có thật hay không.
5. Đoạn giải thích bẫy **xuống dòng riêng** sau dòng 4 → `conclusion` (nhiều dòng thì giữ `\n`); câu nằm **trên cùng dòng** với phân tích lựa chọn cuối thì vẫn thuộc `analysis` của lựa chọn đó. Lựa chọn không có dòng phân tích → `analysis: null`.
6. **`correct.index` lấy theo `dap_an_so` của đề**; `correct.option_ja` giống hệt `option_ja` của lựa chọn đó.
7. **`reference.vi`**: chép nguyên cả phần THÔNG TIN THAM KHẢO trong một chuỗi, giữ xuống dòng (\n), ký hiệu đầu dòng (+, -), cách đánh số và thứ tự như bản gốc – không tách, không gộp dòng, không đánh số lại. Không có phần này → `null`.
8. Thiếu dấu `###` (tiêu đề dính vào cuối phần trước): vẫn nhận theo tiêu đề. Thiếu cả phần PHÂN TÍCH → cả 4 `analysis` = `null`, `exists` = `true`, `intro`/`conclusion` = `null`.

# Ví dụ

## A. Lựa chọn chữ Hán đơn, không có dòng "Cách đọc", có câu ví dụ kèm dòng cách đọc

Đầu vào `de_bai`: {"cau_hoi": "このくすりはようじのひふアレルギーにこうかがある。", "lua_chon": ["楽", "草", "薬", "菜"], "dap_an_so": 3, "dap_an_noi_dung": "薬"}

`loi_giai_goc`:
```
Đề bài: この{くすり}はようじのひふアレルギーにこうかがある。
Nghĩa: {Thuốc} này có hiệu quả trong việc điều trị dị ứng da ở trẻ nhỏ.
###
LỰA CHỌN ĐÚNG:
3. 薬
###
PHÂN TÍCH:
1. 楽: Đọc là らく, có nghĩa là "vui vẻ, thoải mái".
2. 草: Đọc là くさ, có nghĩa là "cỏ".
3. 薬: Đọc là くすり, có nghĩa là "thuốc", là từ chính xác và phù hợp với ngữ cảnh của câu.
4. 菜: Đọc là な, có nghĩa là "rau".
###
THÔNG TIN THAM KHẢO:
Từ 薬 (くすり) trong tiếng Nhật có nghĩa là "thuốc", chỉ các loại thuốc dùng để chữa bệnh hoặc cải thiện sức khỏe. Từ này được sử dụng rộng rãi trong các ngữ cảnh liên quan đến y tế, sức khỏe, và dược phẩm. Nó có thể chỉ các loại thuốc uống, thuốc bôi, hoặc bất kỳ dạng thuốc nào khác.
Ví dụ:
+ 風邪の薬を飲む。
かぜ の くすり を のむ。
Uống thuốc cảm.
+ この薬は一日三回飲んでください。
この くすり は いちにち さんかい のんで ください。
Hãy uống thuốc này ba lần một ngày.
```
Kết quả:
```json
{
 "schema": "vocab_writing.v2",
 "question_id": 2170,
 "cau_con": 1,
 "question": {
  "ja": "この{くすり}はようじのひふアレルギーにこうかがある。",
  "reading": null,
  "meaning": {
   "vi": "{Thuốc} này có hiệu quả trong việc điều trị dị ứng da ở trẻ nhỏ."
  }
 },
 "analysis": {
  "intro": null,
  "options": [
   {
    "index": 1,
    "option_ja": "楽",
    "exists": true,
    "reading": "らく",
    "analysis": {
     "vi": "Đọc là ⟪らく⟫, có nghĩa là \"vui vẻ, thoải mái\"."
    }
   },
   {
    "index": 2,
    "option_ja": "草",
    "exists": true,
    "reading": "くさ",
    "analysis": {
     "vi": "Đọc là ⟪くさ⟫, có nghĩa là \"cỏ\"."
    }
   },
   {
    "index": 3,
    "option_ja": "薬",
    "exists": true,
    "reading": "くすり",
    "analysis": {
     "vi": "Đọc là ⟪くすり⟫, có nghĩa là \"thuốc\", là từ chính xác và phù hợp với ngữ cảnh của câu."
    }
   },
   {
    "index": 4,
    "option_ja": "菜",
    "exists": true,
    "reading": "な",
    "analysis": {
     "vi": "Đọc là ⟪な⟫, có nghĩa là \"rau\"."
    }
   }
  ],
  "conclusion": null
 },
 "correct": {
  "index": 3,
  "option_ja": "薬"
 },
 "reference": {
  "vi": "Từ ⟪薬⟫ (⟪くすり⟫) trong tiếng Nhật có nghĩa là \"thuốc\", chỉ các loại thuốc dùng để chữa bệnh hoặc cải thiện sức khỏe. Từ này được sử dụng rộng rãi trong các ngữ cảnh liên quan đến y tế, sức khỏe, và dược phẩm. Nó có thể chỉ các loại thuốc uống, thuốc bôi, hoặc bất kỳ dạng thuốc nào khác.\nVí dụ:\n+ ⟪風邪の薬を飲む。⟫\n⟪かぜ の くすり を のむ。⟫\nUống thuốc cảm.\n+ ⟪この薬は一日三回飲んでください。⟫\n⟪この くすり は いちにち さんかい のんで ください。⟫\nHãy uống thuốc này ba lần một ngày."
 }
}
```

## B. Lựa chọn có furigana ở nhãn, không có "Đọc là", có đoạn giải thích bẫy

Đầu vào `de_bai`: {"cau_hoi": "けいやく", "lua_chon": ["計約", "係約", "契約", "継約"], "dap_an_so": 3, "dap_an_noi_dung": "契約"}

`loi_giai_goc`:
```
Câu hỏi: ｜製品《せいひん》のかかくをいじするために{けいやく}をむすんだ。
Nghĩa: Họ đã ký {hợp đồng} để duy trì giá cả của sản phẩm.
###
LỰA CHỌN ĐÚNG:
3. ｜契約《けいやく》
###
PHÂN TÍCH:
1. ｜計約《けいやく》: có nghĩa là 'ước tính', không liên quan đến nghĩa của từ được đề cập.
2. ｜係約《けいやく》: Không tồn tại trong tiếng Nhật.
3. ｜契約《けいやく》: Có nghĩa là 'hợp đồng, thỏa thuận'.
4. ｜継約《けいやく》: Không tồn tại trong tiếng Nhật.
Các lựa chọn 1, 2, 4 được thiết kế để gây nhầm lẫn với đáp án đúng. ｜計《けい》, ｜係《けい》, ｜継《けい》 đều có cách đọc là けい, khi ghép với ｜約《やく》 có cách đọc giống đáp án đúng là ｜契約《けいやく》 nhưng không tạo thành từ có nghĩa trong tiếng Nhật hoặc từ mang nghĩa khác không phù hợp ngữ cảnh.
###
THÔNG TIN THAM KHẢO:
｜契約《けいやく》 trong tiếng Nhật có nghĩa là 'hợp đồng', chỉ một thỏa thuận chính thức giữa hai hoặc nhiều bên, thường liên quan đến việc trao đổi hàng hóa, dịch vụ hoặc quyền lợi. Từ này thường được sử dụng trong các lĩnh vực kinh doanh, pháp lý và thương mại.
- Ví dụ:
+ ｜新《あたら》しい｜契約《けいやく》を｜結《むす》ぶ。
Ký kết hợp đồng mới.
+ ｜契約《けいやく》｜内容《ないよう》を｜確認《かくにん》する。
Xác nhận nội dung hợp đồng.
```
Kết quả:
```json
{
 "schema": "vocab_writing.v2",
 "question_id": 54346,
 "cau_con": 1,
 "question": {
  "ja": "｜製品《せいひん》のかかくをいじするために{けいやく}をむすんだ。",
  "reading": null,
  "meaning": {
   "vi": "Họ đã ký {hợp đồng} để duy trì giá cả của sản phẩm."
  }
 },
 "analysis": {
  "intro": null,
  "options": [
   {
    "index": 1,
    "option_ja": "｜計約《けいやく》",
    "exists": true,
    "reading": null,
    "analysis": {
     "vi": "có nghĩa là 'ước tính', không liên quan đến nghĩa của từ được đề cập."
    }
   },
   {
    "index": 2,
    "option_ja": "｜係約《けいやく》",
    "exists": false,
    "reading": null,
    "analysis": {
     "vi": "Không tồn tại trong tiếng Nhật."
    }
   },
   {
    "index": 3,
    "option_ja": "｜契約《けいやく》",
    "exists": true,
    "reading": null,
    "analysis": {
     "vi": "Có nghĩa là 'hợp đồng, thỏa thuận'."
    }
   },
   {
    "index": 4,
    "option_ja": "｜継約《けいやく》",
    "exists": false,
    "reading": null,
    "analysis": {
     "vi": "Không tồn tại trong tiếng Nhật."
    }
   }
  ],
  "conclusion": {
   "vi": "Các lựa chọn 1, 2, 4 được thiết kế để gây nhầm lẫn với đáp án đúng. ⟪｜計《けい》⟫, ⟪｜係《けい》⟫, ⟪｜継《けい》⟫ đều có cách đọc là ⟪けい⟫, khi ghép với ⟪｜約《やく》⟫ có cách đọc giống đáp án đúng là ⟪｜契約《けいやく》⟫ nhưng không tạo thành từ có nghĩa trong tiếng Nhật hoặc từ mang nghĩa khác không phù hợp ngữ cảnh."
  }
 },
 "correct": {
  "index": 3,
  "option_ja": "｜契約《けいやく》"
 },
 "reference": {
  "vi": "⟪｜契約《けいやく》⟫ trong tiếng Nhật có nghĩa là 'hợp đồng', chỉ một thỏa thuận chính thức giữa hai hoặc nhiều bên, thường liên quan đến việc trao đổi hàng hóa, dịch vụ hoặc quyền lợi. Từ này thường được sử dụng trong các lĩnh vực kinh doanh, pháp lý và thương mại.\n- Ví dụ:\n+ ⟪｜新《あたら》しい｜契約《けいやく》を｜結《むす》ぶ。⟫\nKý kết hợp đồng mới.\n+ ⟪｜契約《けいやく》｜内容《ないよう》を｜確認《かくにん》する。⟫\nXác nhận nội dung hợp đồng."
 }
}
```

Chỉ trả về JSON theo schema, không giải thích.
