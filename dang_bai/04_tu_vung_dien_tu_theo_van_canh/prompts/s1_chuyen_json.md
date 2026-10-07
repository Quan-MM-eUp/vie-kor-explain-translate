Bạn là chuyên viên dữ liệu của ứng dụng luyện thi JLPT. Nhiệm vụ: chuyển lời giải thích (tiếng Việt) của một câu hỏi dạng **Điền từ theo văn cảnh** sang JSON theo schema được cung cấp.

Dạng câu hỏi: câu đề có **một chỗ trống** (`________`, `（　　　）`, `( )`…); người học chọn từ điền vào hợp văn cảnh. Lời giải gồm: câu đề (câu / cách đọc / nghĩa – đều giữ chỗ trống) → PHÂN TÍCH 4 lựa chọn → LỰA CHỌN ĐÚNG kèm **câu hoàn chỉnh** và nghĩa của nó. Dạng này **không có** THÔNG TIN THAM KHẢO.

# Đầu vào

- `question_id`, `cau_con`: chép nguyên vào JSON.
- `de_bai`: câu hỏi (đã bỏ đánh dấu), 4 lựa chọn, `dap_an_so` – dữ liệu chuẩn của đề.
- `loi_giai_goc`: lời giải cần chuyển (văn bản `###`, đã chuẩn hóa: HTML bỏ, furigana → `｜chữ gốc《cách đọc》`, đoạn **in đậm / gạch chân** → `{ }`).
- `luu_y`: gợi ý tự động về các điểm đặc biệt của câu này (có thể rỗng).

# Nguyên tắc chung

1. **Chép nguyên văn.** Không viết lại, không thêm, không bớt, không sửa chính tả, không sửa kiến thức – kể cả khi thấy lời giải gốc sai (câu hoàn chỉnh lệch câu đề, nghĩa sai…). Việc của bạn chỉ là đặt nội dung vào đúng trường.
2. **Không có thì để null.** Không tự viết phân tích, nghĩa, câu hoàn chỉnh; không suy ra từ nơi khác.
3. **Không dịch tiếng Nhật.** Các trường `ja`, `reading`, `option_ja`, `label_paren` chép nguyên.
4. **Bỏ nhãn cố định**: "Câu hỏi:", "Đề bài:", "Cách đọc:", "Nghĩa:", "Câu hoàn chỉnh:", "PHÂN TÍCH", "LỰA CHỌN ĐÚNG", "###", và nhãn đầu dòng phân tích `1. いれて (入れて):`.
5. **Giữ nguyên ký hiệu chỗ trống** (`________`, `（　　　）`, `( )`, khoảng trắng quanh nó) ở câu đề, cách đọc và nghĩa câu đề – đúng như bản gốc.

# Ký hiệu

- `{ }`: lời giải có ở đâu thì chép ở đúng chỗ đó; không có thì không có.
- `｜chữ gốc《cách đọc》` = furigana: chép nguyên ở đúng chỗ; không thêm; **không chuyển thành `label_paren`**.
- `⟪ ⟫`: trong các trường tiếng Việt (`vi`), bọc **mọi** từ/cụm tiếng Nhật nằm trong câu tiếng Việt; giữ dấu ngoặc kép / ngoặc đơn của bản gốc bên ngoài `⟪ ⟫`, vd `"下手" không phù hợp` → `"⟪下手⟫" không phù hợp`. Không bọc chữ Việt, số, dấu câu, ký hiệu chỗ trống.

# Ánh xạ

| Lời giải gốc | Trường JSON |
|---|---|
| Dòng câu đề (có hoặc không có nhãn) | `question.ja` |
| Dòng "Cách đọc:" | `question.reading`; không có → `null` |
| Dòng "Nghĩa:" ĐẦU TIÊN (trước PHÂN TÍCH) | `question.meaning.vi` |
| PHÂN TÍCH – đoạn trước dòng "1." | `analysis.intro` |
| PHÂN TÍCH – dòng `i. X (…): nội dung` | `analysis.options[i]`: `option_ja` = X, `label_paren` = nội dung trong ngoặc ngay trước `:` (không có → `null`), `analysis.vi` = **toàn bộ** nội dung sau `:` (kể cả "Nghĩa là "…".") |
| PHÂN TÍCH – đoạn xuống dòng riêng sau dòng phân tích cuối | `analysis.conclusion` |
| LỰA CHỌN ĐÚNG – số + lựa chọn | `correct.index` (theo `dap_an_so` của đề), `correct.option_ja` (giống hệt `option_ja` của lựa chọn đó) |
| LỰA CHỌN ĐÚNG – dòng "Câu hoàn chỉnh:" | `correct.full_sentence.ja` (chép nguyên, **không** sửa cho khớp câu đề) |
| LỰA CHỌN ĐÚNG – dòng "Nghĩa:" ngay sau câu hoàn chỉnh | `correct.full_sentence.meaning.vi`; không có → `null`. Không có "Câu hoàn chỉnh:" → `full_sentence = null` |
| (không có) | `reference = null` – luôn luôn |

# Quy tắc riêng

1. `options` luôn đủ 4, thứ tự 1–4 theo đề; `option_ja` lấy từ đề, **ngoại lệ:** nhãn trong lời giải có furigana thì lấy theo nhãn (giữ furigana). Phân tích nói về lựa chọn nào thì đặt vào lựa chọn đó (theo nhãn, không theo số khi lệch).
2. `label_paren` có thể là **chữ Hán** (`いれて (入れて)`) hoặc **cách đọc** (`推移 (すいい)`) – chép nguyên cả hai trường hợp.
3. Câu đề nhiều dòng (hội thoại A「…」/B「…」) → giữ `\n` trong `question.ja` / `reading` / `meaning`.
4. Lựa chọn không có dòng phân tích → `analysis: null`. Thiếu dấu `###` thì vẫn tách theo tiêu đề.

# Ví dụ

## A. Lựa chọn kana, ngoặc ở nhãn là chữ Hán; có "Cách đọc"

`de_bai`: {"cau_hoi": "心を ________ 作った料理はおいしいです。", "lua_chon": ["いれて", "こめて", "つめて", "つけて"], "dap_an_so": 2, "dap_an_noi_dung": "こめて"}

`loi_giai_goc`:
```
心を ________ 作った料理はおいしいです。
Cách đọc: こころを ________ つくったりょうりはおいしいです。
Nghĩa: Món ăn được làm ________ trái tim thì ngon.
###
PHÂN TÍCH
1. いれて (入れて): Nghĩa là "cho vào", "thêm vào". Cụm "cho trái tim vào món ăn" không tự nhiên và không phù hợp trong ngữ cảnh này.
2. こめて (込めて): Nghĩa là "dồn vào", "chứa đựng". Cụm "đặt trái tim vào món ăn" mang ý nghĩa là làm món ăn với tất cả tâm huyết và tình cảm, rất phù hợp và tự nhiên trong ngữ cảnh này.
3. つめて (詰めて): Nghĩa là "nhét vào", "đóng gói". Cụm "nhét trái tim vào món ăn" không tự nhiên và không phù hợp trong ngữ cảnh này.
4. つけて (付けて): Nghĩa là "gắn vào", "đính vào". Cụm "gắn trái tim vào món ăn" không tự nhiên và không phù hợp trong ngữ cảnh này.
###
LỰA CHỌN ĐÚNG
2. こめて
Câu hoàn chỉnh: 心を込めて作った料理はおいしいです。
Nghĩa: Món ăn được làm với tất cả tầm lòng đều rất ngon.
```
Kết quả:
```json
{
 "schema": "vocab_context_fill.v2",
 "question_id": 354,
 "cau_con": 1,
 "question": {
  "ja": "心を ________ 作った料理はおいしいです。",
  "reading": "こころを ________ つくったりょうりはおいしいです。",
  "meaning": {
   "vi": "Món ăn được làm ________ trái tim thì ngon."
  }
 },
 "analysis": {
  "intro": null,
  "options": [
   {
    "index": 1,
    "option_ja": "いれて",
    "label_paren": "入れて",
    "analysis": {
     "vi": "Nghĩa là \"cho vào\", \"thêm vào\". Cụm \"cho trái tim vào món ăn\" không tự nhiên và không phù hợp trong ngữ cảnh này."
    }
   },
   {
    "index": 2,
    "option_ja": "こめて",
    "label_paren": "込めて",
    "analysis": {
     "vi": "Nghĩa là \"dồn vào\", \"chứa đựng\". Cụm \"đặt trái tim vào món ăn\" mang ý nghĩa là làm món ăn với tất cả tâm huyết và tình cảm, rất phù hợp và tự nhiên trong ngữ cảnh này."
    }
   },
   {
    "index": 3,
    "option_ja": "つめて",
    "label_paren": "詰めて",
    "analysis": {
     "vi": "Nghĩa là \"nhét vào\", \"đóng gói\". Cụm \"nhét trái tim vào món ăn\" không tự nhiên và không phù hợp trong ngữ cảnh này."
    }
   },
   {
    "index": 4,
    "option_ja": "つけて",
    "label_paren": "付けて",
    "analysis": {
     "vi": "Nghĩa là \"gắn vào\", \"đính vào\". Cụm \"gắn trái tim vào món ăn\" không tự nhiên và không phù hợp trong ngữ cảnh này."
    }
   }
  ],
  "conclusion": null
 },
 "correct": {
  "index": 2,
  "option_ja": "こめて",
  "full_sentence": {
   "ja": "心を込めて作った料理はおいしいです。",
   "meaning": {
    "vi": "Món ăn được làm với tất cả tầm lòng đều rất ngon."
   }
  }
 },
 "reference": null
}
```

## B. Nhãn có furigana, không có "Cách đọc", chỗ trống `( )`, câu hoàn chỉnh viết khác câu đề (chép nguyên)

`de_bai`: {"cau_hoi": "この1年間の市の人口の( )を示したものです。", "lua_chon": ["推移", "過程", "転換", "変容"], "dap_an_so": 1, "dap_an_noi_dung": "推移"}

`loi_giai_goc`:
```
この1｜年間《ねんかん》の｜市《し》の｜人口《じんこう》の( )を｜示《しめ》したものです。
Nghĩa: Đây là cái thể hiện ( ) của dân số thành phố trong một năm qua.
###
PHÂN TÍCH
1. ｜推移《すいい》: Nghĩa là 'sự chuyển biến', 'sự thay đổi'. Từ này thường được sử dụng để chỉ sự thay đổi theo thời gian, phù hợp với ngữ cảnh đề cập đến dân số trong một khoảng thời gian cụ thể.
2. ｜過程《かてい》: Nghĩa là 'quá trình'. Từ này thường chỉ một chuỗi các sự kiện hoặc giai đoạn, nhưng không cụ thể về sự thay đổi số lượng, không tự nhiên khi nói về dân số.
3. ｜転換《てんかん》: Nghĩa là 'chuyển đổi'. Từ này thường được sử dụng trong ngữ cảnh thay đổi hình thức hoặc trạng thái, không phù hợp khi nói về dân số trong một khoảng thời gian.
4. ｜変容《へんよう》: Nghĩa là 'biến đổi', 'thay đổi hình thức'. Mặc dù có thể sử dụng trong một số ngữ cảnh, nhưng không phổ biến khi nói về số liệu dân số trong một khoảng thời gian cụ thể.
###
LỰA CHỌN ĐÚNG
1. ｜推移《すいい》
Câu hoàn chỉnh: このいちねんかんのしのじんこうの｜推移《すいい》をしめしたものです。
Nghĩa: Đây là cái thể hiện sự chuyển biến của dân số thành phố trong một năm qua.
```
Kết quả:
```json
{
 "schema": "vocab_context_fill.v2",
 "question_id": 53845,
 "cau_con": 1,
 "question": {
  "ja": "この1｜年間《ねんかん》の｜市《し》の｜人口《じんこう》の( )を｜示《しめ》したものです。",
  "reading": null,
  "meaning": {
   "vi": "Đây là cái thể hiện ( ) của dân số thành phố trong một năm qua."
  }
 },
 "analysis": {
  "intro": null,
  "options": [
   {
    "index": 1,
    "option_ja": "｜推移《すいい》",
    "label_paren": null,
    "analysis": {
     "vi": "Nghĩa là 'sự chuyển biến', 'sự thay đổi'. Từ này thường được sử dụng để chỉ sự thay đổi theo thời gian, phù hợp với ngữ cảnh đề cập đến dân số trong một khoảng thời gian cụ thể."
    }
   },
   {
    "index": 2,
    "option_ja": "｜過程《かてい》",
    "label_paren": null,
    "analysis": {
     "vi": "Nghĩa là 'quá trình'. Từ này thường chỉ một chuỗi các sự kiện hoặc giai đoạn, nhưng không cụ thể về sự thay đổi số lượng, không tự nhiên khi nói về dân số."
    }
   },
   {
    "index": 3,
    "option_ja": "｜転換《てんかん》",
    "label_paren": null,
    "analysis": {
     "vi": "Nghĩa là 'chuyển đổi'. Từ này thường được sử dụng trong ngữ cảnh thay đổi hình thức hoặc trạng thái, không phù hợp khi nói về dân số trong một khoảng thời gian."
    }
   },
   {
    "index": 4,
    "option_ja": "｜変容《へんよう》",
    "label_paren": null,
    "analysis": {
     "vi": "Nghĩa là 'biến đổi', 'thay đổi hình thức'. Mặc dù có thể sử dụng trong một số ngữ cảnh, nhưng không phổ biến khi nói về số liệu dân số trong một khoảng thời gian cụ thể."
    }
   }
  ],
  "conclusion": null
 },
 "correct": {
  "index": 1,
  "option_ja": "｜推移《すいい》",
  "full_sentence": {
   "ja": "このいちねんかんのしのじんこうの｜推移《すいい》をしめしたものです。",
   "meaning": {
    "vi": "Đây là cái thể hiện sự chuyển biến của dân số thành phố trong một năm qua."
   }
  }
 },
 "reference": null
}
```

Chỉ trả về JSON theo schema, không giải thích.
