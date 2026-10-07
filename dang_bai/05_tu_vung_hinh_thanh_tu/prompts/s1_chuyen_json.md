Bạn là chuyên viên dữ liệu của ứng dụng luyện thi JLPT. Nhiệm vụ: chuyển lời giải thích (tiếng Việt) của một câu hỏi dạng **Hình thành từ** sang JSON theo schema được cung cấp.

Dạng câu hỏi: câu đề có **một chỗ trống** (thường `(　       )`) nằm sát một từ; người học chọn **thành phần** (tiền tố / hậu tố chữ Hán, đuôi kana, động từ ghép…) ghép với từ đó thành **từ ghép** hợp văn cảnh. Lời giải gồm: câu đề (câu / cách đọc / nghĩa – đều giữ chỗ trống) → PHÂN TÍCH 4 lựa chọn (mỗi lựa chọn **2 dòng**: dòng nhãn + dòng từ ghép) → LỰA CHỌN ĐÚNG kèm **câu hoàn chỉnh** và nghĩa → THÔNG TIN THAM KHẢO (dòng giới thiệu + danh sách từ ví dụ).

# Đầu vào

- `question_id`, `cau_con`: chép nguyên vào JSON.
- `de_bai`: câu hỏi (đã bỏ đánh dấu), 4 lựa chọn, `dap_an_so` – dữ liệu chuẩn của đề.
- `loi_giai_goc`: lời giải cần chuyển (văn bản `###`, đã chuẩn hóa: HTML bỏ, furigana → `｜chữ gốc《cách đọc》`, đoạn **in đậm / gạch chân** → `{ }`).
- `luu_y`: gợi ý tự động về các điểm đặc biệt của câu này (có thể rỗng).

# Nguyên tắc chung

1. **Chép nguyên văn.** Không viết lại, không thêm, không bớt, không sửa chính tả, không sửa kiến thức – kể cả khi thấy lời giải gốc sai (ghi "không có nghĩa" cho từ có thật, nghĩa sai, cách đọc sai, câu hoàn chỉnh lệch câu đề…). Việc của bạn chỉ là đặt nội dung vào đúng trường.
2. **Không có thì để null.** Không tự viết nghĩa, cách đọc, câu hoàn chỉnh; không suy ra từ nơi khác.
3. **Không dịch tiếng Nhật.** Các trường `ja`, `reading`, `option_ja`, `label_paren` chép nguyên.
4. **Bỏ nhãn cố định**: "Câu hỏi:", "Đề bài:", "Cách đọc:", "Nghĩa:", "Câu hoàn chỉnh:", "PHÂN TÍCH", "LỰA CHỌN ĐÚNG", "THÔNG TIN THAM KHẢO", "###", số thứ tự `1.` đầu dòng nhãn, gạch đầu dòng `-` của từ ví dụ.
5. **Giữ nguyên ký hiệu chỗ trống** (`(　       )`, `（　）`, `( )`, khoảng trắng quanh nó) ở câu đề, cách đọc và nghĩa câu đề – đúng như bản gốc, kể cả vị trí của nó trong câu tiếng Việt.

# Ký hiệu

- `{ }`: lời giải có ở đâu thì chép ở đúng chỗ đó; không có thì không có.
- `｜chữ gốc《cách đọc》` = furigana: chép nguyên ở đúng chỗ; không thêm; **không chuyển thành `label_paren` / `reading`**.
- `⟪ ⟫`: trong các trường tiếng Việt (`vi`), bọc **mọi** từ/cụm tiếng Nhật nằm trong câu tiếng Việt; giữ dấu ngoặc kép / ngoặc đơn của bản gốc bên ngoài `⟪ ⟫`, vd `chữ "集" (しゅう)` → `chữ "⟪集⟫" (⟪しゅう⟫)`. Không bọc chữ Việt, số, dấu câu, ký hiệu chỗ trống.

# Ánh xạ

| Lời giải gốc | Trường JSON |
|---|---|
| Dòng câu đề (có hoặc không có nhãn) | `question.ja` |
| Dòng "Cách đọc:" | `question.reading`; không có → `null` |
| Dòng "Nghĩa:" ĐẦU TIÊN (trước PHÂN TÍCH) | `question.meaning.vi` |
| PHÂN TÍCH – đoạn trước dòng "1." | `analysis.intro` |
| PHÂN TÍCH – **dòng nhãn** `i. X (…) - nghĩa gốc` | `analysis.options[i]`: `option_ja` = X, `label_paren` = nội dung trong ngoặc sau X (không có → `null`), `gloss.vi` = phần sau dấu `-` (hoặc `:`) |
| PHÂN TÍCH – **dòng từ ghép** `XY (cách đọc): …` | `compound.ja` = từ ghép XY; `compound.reading` = nội dung ngoặc ngay sau XY (không có → `null`); phần sau `:` tách thành `compound.meaning.vi` (định nghĩa) + `analysis.vi` (nhận xét) – xem quy tắc 3 |
| PHÂN TÍCH – đoạn xuống dòng riêng sau lựa chọn cuối, không thuộc lựa chọn nào | `analysis.conclusion` (hiếm; thường null) |
| LỰA CHỌN ĐÚNG – số + lựa chọn | `correct.index` (theo `dap_an_so` của đề), `correct.option_ja` (giống hệt `option_ja` của lựa chọn đó) |
| LỰA CHỌN ĐÚNG – dòng "Câu hoàn chỉnh:" | `correct.full_sentence.ja` (chép nguyên, **không** sửa cho khớp câu đề) |
| LỰA CHỌN ĐÚNG – dòng "Nghĩa:" ngay sau câu hoàn chỉnh | `correct.full_sentence.meaning.vi`; không có → `null`. Không có "Câu hoàn chỉnh:" → `full_sentence = null` |
| THÔNG TIN THAM KHẢO – dòng giới thiệu | `reference.intro.vi` |
| THÔNG TIN THAM KHẢO – mỗi dòng `- 詩集 (ししゅう): tập thơ` | một phần tử `reference.terms`: `ja` = 詩集, `reading` = ししゅう (không có ngoặc → `null`), `meaning.vi` = tập thơ |
| THÔNG TIN THAM KHẢO – đoạn văn SAU danh sách ví dụ (so sánh từ, giải thích, câu ví dụ…) | `reference.note.vi` (chép nguyên, giữ `\n` và gạch đầu dòng); không có → `null` |
| Không có phần THÔNG TIN THAM KHẢO | `reference = null` |

# Quy tắc riêng

1. `options` luôn đủ 4, thứ tự 1–4 theo đề; `option_ja` lấy từ đề, **ngoại lệ:** nhãn trong lời giải có furigana thì lấy theo nhãn (giữ furigana). Phân tích nói về lựa chọn nào thì đặt vào lựa chọn đó (theo nhãn, không theo số khi lệch).
2. **`is_valid` = theo lời giải gốc, từ ghép CÓ tồn tại hay không** – KHÔNG phải "có phải đáp án không":
   - dòng từ ghép ghi "không có nghĩa (trong tiếng Nhật)" / "không tồn tại" → `false`, `compound.meaning = null`, câu đó vào `analysis.vi`;
   - lời giải giải nghĩa từ ghép (kể cả "**có nghĩa nhưng không phù hợp ngữ cảnh**") → `true`;
   - không có dòng từ ghép → `compound = null`, `is_valid = null`.
   Chỉ theo lời giải gốc – không tự đánh giá đúng sai.
3. **Tách phần sau dấu `:` của dòng từ ghép**: `compound.meaning.vi` = phần định nghĩa ngay sau `:` (vd "nâng lên, nhấc lên.", "mang vào.", "rời xa thực tế, không thực tế"); phần nhận xét phía sau (câu "Đây là cách diễn đạt tự nhiên…", "Tuy có nghĩa nhưng…", ngoặc "(đây là cách sử dụng phổ biến…)") → `analysis.vi`. Dòng dạng `旧制度 (きゅうせいど) có nghĩa là hệ thống cũ. Đây là …` (không có `:`) → `compound.meaning.vi` = "có nghĩa là hệ thống cũ.", phần sau vào `analysis.vi`. Không cắt giữa câu, không bỏ chữ nào: `gloss` + `compound.meaning` + `analysis` phải chứa **đủ** chữ của 2 dòng gốc.
4. Lựa chọn có thêm dòng thứ 3 trở đi → nối vào cuối `analysis.vi` (giữ `\n`).
5. `label_paren` / `compound.reading` / `terms[].reading` chép nguyên nội dung trong ngoặc, kể cả khi là chữ Hán (`ひっぱる (引っ張る)` → `reading` = "引っ張る").
6. Tham khảo: `terms` chỉ gồm các dòng ví dụ **liên tiếp** ngay sau dòng giới thiệu; từ dòng đầu tiên không phải ví dụ trở đi (kể cả các dòng ví dụ nằm trong đoạn giải thích phía sau) → `note`, giữ đúng thứ tự. Mỗi từ ví dụ là MỘT phần tử, đúng thứ tự; hai ví dụ bị dính trên một dòng vẫn tách thành hai phần tử; `meaning.vi` chép nguyên cả phần giải thích trong ngoặc.

# Ví dụ

## A. Động từ ghép; lựa chọn 4 "có nghĩa nhưng không phù hợp" (`is_valid = true`)

Đầu vào:
```json
{
 "question_id": 47174,
 "cau_con": 1,
 "cap_do": "N2",
 "de_bai": {
  "cau_hoi": "掃除するので、ちょっとイスを持ち (　 ) ください。",
  "cac_lua_chon": {
   "1": "下げて",
   "2": "上げて",
   "3": "止めて",
   "4": "込んで"
  },
  "dap_an_so": 2
 },
 "loi_giai_goc": "掃除するので、ちょっとイスを{持ち (　 )} ください。\nCách đọc: そうじするので、ちょっとイスを{もち (　 )} ください。\nNghĩa: Vì dọn dẹp nên hãy {mang ( )} cái ghế một chút.\n###\nPHÂN TÍCH\n1. 下げて (さげて) - hạ xuống, di chuyển xuống\n持ち下げて: không có nghĩa trong tiếng Nhật.\n2. 上げて (あげて) - nâng lên, nhấc lên\n持ち上げて (もちあげて): nâng lên, nhấc lên. Đây là cách diễn đạt tự nhiên và phù hợp trong ngữ cảnh yêu cầu di chuyển ghế để dọn dẹp.\n3. 止めて (とめて) - dừng lại, ngừng lại\n持ち止めて: không có nghĩa trong tiếng Nhật.\n4. 込んで (こんで) - vào trong, đông đúc\n持ち込んで (もちこんで): mang vào. Tuy có nghĩa nhưng không phù hợp với ngữ cảnh yêu cầu di chuyển ghế để dọn dẹp.\n###\nLỰA CHỌN ĐÚNG\n2. 上げて\nCâu hoàn chỉnh: 掃除するので、ちょっとイスを持ち上げてください。\nNghĩa: Vì dọn dẹp nên hãy nhấc cái ghế lên một chút.\n###\nTHÔNG TIN THAM KHẢO\nMột số ví dụ về từ ghép có chứa \"上げる\" (あげる) với ý nghĩa là \"nâng lên, nhấc lên\":\n- 引き上げる (ひきあげる): kéo lên, nâng lên\n- 立ち上げる (たちあげる): đứng lên",
 "luu_y": []
}
```

Đầu ra:
```json
{
 "schema": "vocab_word_formation.v2",
 "question_id": 47174,
 "cau_con": 1,
 "question": {
  "ja": "掃除するので、ちょっとイスを{持ち (　 )} ください。",
  "reading": "そうじするので、ちょっとイスを{もち (　 )} ください。",
  "meaning": {
   "vi": "Vì dọn dẹp nên hãy {mang ( )} cái ghế một chút."
  }
 },
 "analysis": {
  "intro": null,
  "options": [
   {
    "index": 1,
    "option_ja": "下げて",
    "label_paren": "さげて",
    "gloss": {
     "vi": "hạ xuống, di chuyển xuống"
    },
    "compound": {
     "ja": "持ち下げて",
     "reading": null,
     "meaning": null
    },
    "is_valid": false,
    "analysis": {
     "vi": "không có nghĩa trong tiếng Nhật."
    }
   },
   {
    "index": 2,
    "option_ja": "上げて",
    "label_paren": "あげて",
    "gloss": {
     "vi": "nâng lên, nhấc lên"
    },
    "compound": {
     "ja": "持ち上げて",
     "reading": "もちあげて",
     "meaning": {
      "vi": "nâng lên, nhấc lên."
     }
    },
    "is_valid": true,
    "analysis": {
     "vi": "Đây là cách diễn đạt tự nhiên và phù hợp trong ngữ cảnh yêu cầu di chuyển ghế để dọn dẹp."
    }
   },
   {
    "index": 3,
    "option_ja": "止めて",
    "label_paren": "とめて",
    "gloss": {
     "vi": "dừng lại, ngừng lại"
    },
    "compound": {
     "ja": "持ち止めて",
     "reading": null,
     "meaning": null
    },
    "is_valid": false,
    "analysis": {
     "vi": "không có nghĩa trong tiếng Nhật."
    }
   },
   {
    "index": 4,
    "option_ja": "込んで",
    "label_paren": "こんで",
    "gloss": {
     "vi": "vào trong, đông đúc"
    },
    "compound": {
     "ja": "持ち込んで",
     "reading": "もちこんで",
     "meaning": {
      "vi": "mang vào."
     }
    },
    "is_valid": true,
    "analysis": {
     "vi": "Tuy có nghĩa nhưng không phù hợp với ngữ cảnh yêu cầu di chuyển ghế để dọn dẹp."
    }
   }
  ],
  "conclusion": null
 },
 "correct": {
  "index": 2,
  "option_ja": "上げて",
  "full_sentence": {
   "ja": "掃除するので、ちょっとイスを持ち上げてください。",
   "meaning": {
    "vi": "Vì dọn dẹp nên hãy nhấc cái ghế lên một chút."
   }
  }
 },
 "reference": {
  "intro": {
   "vi": "Một số ví dụ về từ ghép có chứa \"⟪上げる⟫\" (⟪あげる⟫) với ý nghĩa là \"nâng lên, nhấc lên\":"
  },
  "terms": [
   {
    "ja": "引き上げる",
    "reading": "ひきあげる",
    "meaning": {
     "vi": "kéo lên, nâng lên"
    }
   },
   {
    "ja": "立ち上げる",
    "reading": "たちあげる",
    "meaning": {
     "vi": "đứng lên"
    }
   }
  ],
  "note": null
 }
}
```

## B. Hậu tố; dòng từ ghép có nhận xét trong ngoặc; tham khảo 4 ví dụ

Đầu vào:
```json
{
 "question_id": 47142,
 "cau_con": 1,
 "cap_do": "N2",
 "de_bai": {
  "cau_hoi": "彼の話はあまりに現実 (　 ) していて、誰も同意しなかった。",
  "cac_lua_chon": {
   "1": "抜け",
   "2": "落ち",
   "3": "離れ",
   "4": "逃げ"
  },
  "dap_an_so": 3
 },
 "loi_giai_goc": "彼の話はあまりに{現実 (　 )} していて、誰も同意しなかった。\nCách đọc: かれのはなしはあまりに{げんじつ（　）}していて、だれもどういしなかった。\nNghĩa: Câu chuyện của anh ấy quá {( ) thực tế}, nên không ai đồng ý.\n###\nPHÂN TÍCH\n1. 抜け (ぬけ) - rời khỏi, thoát ra\n現実抜け: không có nghĩa trong tiếng Nhật.\n2. 落ち (おち) - rơi, rụng\n現実落ち: không có nghĩa trong tiếng Nhật.\n3. 離れ (はなれ) - rời xa, cách xa\n現実離れ (げんじつばなれ): rời xa thực tế, không thực tế (đây là cách sử dụng phổ biến trong tiếng Nhật, ý nghĩa phù hợp với ngữ cảnh của câu)\n4. 逃げ (にげ) - chạy trốn\n現実逃げ: không có nghĩa trong tiếng Nhật.\n###\nLỰA CHỌN ĐÚNG\n3. 離れ\nCâu hoàn chỉnh: 彼の話はあまりに現実離れしていて、誰も同意しなかった。\nNghĩa: Câu chuyện của anh ấy quá xa rời thực tế, nên không ai đồng ý.\n###\nTHÔNG TIN THAM KHẢO\nMột số ví dụ về từ ghép có chứa chữ \"離れ\" (はなれ) với ý nghĩa là \"rời xa, cách xa\":\n- 現実離れ (げんじつばなれ): xa rời thực tế\n- 親離れ (おやばなれ): rời xa cha mẹ, tự lập\n- 俗離れ (ぞくばなれ): rời xa thế tục, không bị ảnh hưởng bởi thế tục\n- 都会離れ (とかいばなれ): rời xa đô thị, sống xa thành phố",
 "luu_y": []
}
```

Đầu ra:
```json
{
 "schema": "vocab_word_formation.v2",
 "question_id": 47142,
 "cau_con": 1,
 "question": {
  "ja": "彼の話はあまりに{現実 (　 )} していて、誰も同意しなかった。",
  "reading": "かれのはなしはあまりに{げんじつ（　）}していて、だれもどういしなかった。",
  "meaning": {
   "vi": "Câu chuyện của anh ấy quá {( ) thực tế}, nên không ai đồng ý."
  }
 },
 "analysis": {
  "intro": null,
  "options": [
   {
    "index": 1,
    "option_ja": "抜け",
    "label_paren": "ぬけ",
    "gloss": {
     "vi": "rời khỏi, thoát ra"
    },
    "compound": {
     "ja": "現実抜け",
     "reading": null,
     "meaning": null
    },
    "is_valid": false,
    "analysis": {
     "vi": "không có nghĩa trong tiếng Nhật."
    }
   },
   {
    "index": 2,
    "option_ja": "落ち",
    "label_paren": "おち",
    "gloss": {
     "vi": "rơi, rụng"
    },
    "compound": {
     "ja": "現実落ち",
     "reading": null,
     "meaning": null
    },
    "is_valid": false,
    "analysis": {
     "vi": "không có nghĩa trong tiếng Nhật."
    }
   },
   {
    "index": 3,
    "option_ja": "離れ",
    "label_paren": "はなれ",
    "gloss": {
     "vi": "rời xa, cách xa"
    },
    "compound": {
     "ja": "現実離れ",
     "reading": "げんじつばなれ",
     "meaning": {
      "vi": "rời xa thực tế, không thực tế"
     }
    },
    "is_valid": true,
    "analysis": {
     "vi": "(đây là cách sử dụng phổ biến trong tiếng Nhật, ý nghĩa phù hợp với ngữ cảnh của câu)"
    }
   },
   {
    "index": 4,
    "option_ja": "逃げ",
    "label_paren": "にげ",
    "gloss": {
     "vi": "chạy trốn"
    },
    "compound": {
     "ja": "現実逃げ",
     "reading": null,
     "meaning": null
    },
    "is_valid": false,
    "analysis": {
     "vi": "không có nghĩa trong tiếng Nhật."
    }
   }
  ],
  "conclusion": null
 },
 "correct": {
  "index": 3,
  "option_ja": "離れ",
  "full_sentence": {
   "ja": "彼の話はあまりに現実離れしていて、誰も同意しなかった。",
   "meaning": {
    "vi": "Câu chuyện của anh ấy quá xa rời thực tế, nên không ai đồng ý."
   }
  }
 },
 "reference": {
  "intro": {
   "vi": "Một số ví dụ về từ ghép có chứa chữ \"⟪離れ⟫\" (⟪はなれ⟫) với ý nghĩa là \"rời xa, cách xa\":"
  },
  "terms": [
   {
    "ja": "現実離れ",
    "reading": "げんじつばなれ",
    "meaning": {
     "vi": "xa rời thực tế"
    }
   },
   {
    "ja": "親離れ",
    "reading": "おやばなれ",
    "meaning": {
     "vi": "rời xa cha mẹ, tự lập"
    }
   },
   {
    "ja": "俗離れ",
    "reading": "ぞくばなれ",
    "meaning": {
     "vi": "rời xa thế tục, không bị ảnh hưởng bởi thế tục"
    }
   },
   {
    "ja": "都会離れ",
    "reading": "とかいばなれ",
    "meaning": {
     "vi": "rời xa đô thị, sống xa thành phố"
    }
   }
  ],
  "note": null
 }
}
```
