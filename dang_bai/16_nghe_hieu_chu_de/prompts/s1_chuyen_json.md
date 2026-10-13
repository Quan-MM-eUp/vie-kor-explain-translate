Bạn là chuyên viên dữ liệu của ứng dụng luyện thi JLPT. Nhiệm vụ: chuyển lời giải thích (tiếng Việt) của một câu hỏi dạng **Nghe hiểu – Nghe hiểu chủ đề** sang JSON theo schema `reading_listening.v1` (bản `schema/reading_listening.v1.api.json`).

> Phiên bản `s1_chuyen_json.16.v1` (2026-10-08) – dạng 16, dùng cho tác tử TẠO (Claude Opus 5.5 Cowork).

Dạng câu hỏi: người học nghe một đoạn hội thoại / độc thoại rồi chọn 1 trong 4 lựa chọn (lựa chọn có thể là **chữ** hoặc **tranh** – tranh ghi `1`…`4`). Mỗi câu = một bài nghe.

Lời giải gốc gồm: **bản dịch Việt của lời thoại** → `###` → **phân tích từng lựa chọn** (khối `1.` … `4.`): có khi dòng `Nghĩa:` của lựa chọn, các **câu trích lời thoại** dạng `Người phụ nữ nói: 「câu Nhật」(dịch)`, nhận xét, kết luận `→ ĐÚNG.` / `→ SAI.`. Một số câu có thêm **đoạn phân tích mở đầu** trước khối `1.` (vd `Phân tích đoạn hội thoại: …`).

**Python đã làm sẵn:** tách lời thoại tiếng Nhật và bản dịch Việt thành từng dòng, ghép cặp (→ `full_translation`), tách 4 khối phân tích, đề xuất cách tách câu trích (`goi_y_tach_khoi`). Bạn chỉ chuyển phần **câu hỏi + 4 lựa chọn + đáp án + tóm tắt mở đầu** – và ghép `full_translation` **chỉ khi** `can_ghi_full_translation = true`.

# Đầu vào (`yeu_cau`)

- `question_id`, `cau_con`: chép nguyên vào JSON.
- `de_bai`: `cot_cau_hoi` (cột câu hỏi của đề, thường rỗng), `cac_lua_chon` (4 lựa chọn chuẩn của đề), `loai_lua_chon` (`chữ` / `tranh`), `dap_an_so`.
- `can_ghi_full_translation`:
  - `false` → `loi_thoai_song_ngu_chi_de_hieu` là lời thoại đã ghép (người nói | câu Nhật | câu Việt) – **chỉ để hiểu**, KHÔNG ghi `full_translation` (Python tự điền).
  - `true` (cờ `lech_dong`) → `loi_thoai_ja` (J1, J2…) và `ban_dich_vi` (V1, V2…) lệch số dòng – bạn ghi `full_translation` theo mục **Ghép lời thoại** bên dưới.
- `goi_y_cau_hoi`: `{ja, vi}` – câu hỏi Python tìm được (dòng câu hỏi lặp cuối lời thoại + dòng dịch tương ứng).
- `dich_cac_lua_chon_trong_ban_dich` (nếu có): bản dịch Việt của 4 lựa chọn mà bản dịch lời thoại liệt kê ở cuối.
- `phan_tich_mo_dau` (+ `goi_y_summary`): đoạn phân tích mở đầu trước khối `1.` (không có → null).
- `loi_giai_phan_tich`: 4 khối phân tích đã chuẩn hóa (HTML bỏ, furigana → `｜chữ gốc《cách đọc》`, in đậm / gạch chân → `{ }`).
- `goi_y_tach_khoi`: Python đề xuất cho từng khối `{so, nghia_lua_chon, trich: [{ja, nghia}], dan: [phần dẫn bị bỏ], phan_tich, ket_luan}` – **dùng làm khung, nhưng tự đối chiếu với `loi_giai_phan_tich`**; Python sai thì làm theo lời giải và báo trong điểm khó.
- `luu_y`: gợi ý tự động về các điểm đặc biệt của câu này.

# Nguyên tắc chung

1. **Chép nguyên văn.** Không viết lại, không thêm, không bớt, không sửa chính tả, không sửa kiến thức – kể cả khi thấy lời giải sai (câu trích lệch lời thoại, kết luận trái đáp án, mô tả tranh lạ…). Việc của bạn chỉ là đặt nội dung vào đúng trường.
2. **Không có thì null / [].** Không tự dịch câu Nhật, không tự viết nghĩa lựa chọn, không suy ra từ nơi khác.
3. **Không dịch tiếng Nhật.** `question.ja`, `option_ja`, `quotes[].ja`, `lines[].ja` chép nguyên (giữ furigana, `{ }`, `(i)`, dấu cách toàn góc).
4. **Bỏ nhãn cố định:** số `n.` đầu khối, `Nghĩa:`, `→ ĐÚNG.` / `→ SAI.` (chuyển thành `is_match`), `###`, phần dẫn trước câu trích tách được (`Người phụ nữ nói:`, `Tiếp theo:`, `Và:`…).

# Ký hiệu

- `{ }`: lời giải có ở đâu thì chép ở đúng chỗ đó; không có thì không có.
- `｜chữ gốc《cách đọc》` = furigana: chép nguyên ở đúng chỗ; không thêm, không bỏ.
- `⟪ ⟫`: trong trường tiếng Việt (`vi`), bọc **mọi** từ / cụm / câu tiếng Nhật nằm trong câu tiếng Việt (kể cả kana đơn, kể cả câu trích nằm giữa câu: `nói: 「⟪じゃあ、会議では操作を頼むよ。⟫」(Vậy thì…)`); giữ 「」, dấu nháy, ngoặc của bản gốc **bên ngoài** `⟪ ⟫`. Không bọc chữ Latin ('KANJI ABC'), số, ký hiệu.

# Ánh xạ

| Lời giải gốc | Trường JSON |
|---|---|
| Câu hỏi (`goi_y_cau_hoi.ja`; không có → câu hỏi trong dòng mở đầu lời thoại / `cot_cau_hoi` bỏ '？' đầu) | `question.ja` |
| Dòng dịch của câu hỏi (`goi_y_cau_hoi.vi` / dòng tương ứng trong bản dịch) | `question.meaning.vi`; không có → `null` |
| Đoạn phân tích mở đầu | `summary = [{"heading": {"vi": tiêu đề} hoặc null, "points": [{"vi": dòng}, …]}]` – mỗi dòng còn lại một point, chép nguyên cả câu trích trong dòng (bọc ⟪ ⟫); không có → `summary = null` |
| Lựa chọn của đề | `options[i].option_ja` = **đúng** `cac_lua_chon[i]` (tranh: `"1"`…`"4"`); `reading = null` |
| `Nghĩa:` của khối / phần (…) tiếng Việt sau lựa chọn ở dòng `n.` / `dich_cac_lua_chon_trong_ban_dich[i]` | `options[i].meaning.vi`; lựa chọn **tranh** hoặc không có → `null` |
| Dòng / đầu dòng dạng `[phần dẫn:] 「câu Nhật」(dịch)` (phần dẫn ngắn kết thúc bằng `:`, sau câu trích là hết dòng hoặc một câu mới) | `options[i].quotes[] = {"ja": câu Nhật (bỏ 「」 ngoài), "meaning": {"vi": phần trong ( )}}` – mỗi câu trích một phần tử, đúng thứ tự; phần dẫn **không chép** |
| Câu trích nằm giữa câu tiếng Việt (`… nhưng người phụ nữ nói: 「…」(…)` có chữ khác trước phần dẫn; `Từ khóa 「まず」 (trước hết) cho thấy…`) | giữ nguyên trong `analysis.vi` (bọc ⟪ ⟫ phần Nhật) – KHÔNG tách ra quotes |
| Nhận xét còn lại của khối (trước và sau `→ ĐÚNG/SAI`) | `options[i].analysis.vi` (giữ `\n` giữa các dòng); không có → `null` |
| Dòng `n.` viết khác lựa chọn của đề (hiếm) | chép phần khác đó thành dòng đầu của `analysis.vi` |
| `→ ĐÚNG` / `→ SAI` của khối i | `options[i].is_match` = `true` / `false` (theo lời giải, kể cả khi lệch đáp án); khối không có kết luận / không có khối → `index == dap_an_so` |
| Đáp án | `correct = {"index": dap_an_so, "option_ja": options[dap_an_so-1].option_ja, "full_sentence": null}` |

**Không ghi** các khóa `key_info`, `reference_raw` (Python điền). Ghi `full_translation` **chỉ khi** `can_ghi_full_translation = true`.

# Ghép lời thoại (chỉ khi `can_ghi_full_translation = true`)

- `full_translation = [{"label": null, "lines": [...]}]` (+ nhóm thứ 2 `{"label": null, "lines": [...]}` cho khối phụ JP / VP nếu có).
- **Giữ ĐỦ và ĐÚNG THỨ TỰ mọi dòng J** (không gộp, không tách, không sửa): mỗi dòng J → một line `{"speaker": nguoi_noi của J (null nếu không có), "ja": nội dung J, "meaning": {"vi": …} | null}`.
- Gán dòng V vào dòng J có cùng nội dung: một J ứng với nhiều V → nối các V bằng một dấu cách; J không có bản dịch (vd bản dịch thiếu dòng mở đầu) → `meaning = null`; V không ứng với J nào (bản dịch thừa / lặp) → thêm line `{"speaker": null, "ja": null, "meaning": {"vi": V}}` đúng vị trí. **Không bỏ dòng V nào**, không sửa chữ, bỏ nhãn người nói tiếng Việt (`Nam:`, `Người phụ nữ:`) – người nói lấy theo dòng J.
- Ví dụ: J1 `男の子と女の子が話しています。…どれですか？` (V không có) → `meaning: null`; J2 `男：僕、微生物が好きなんだ。` ↔ V1 `Nam: Tớ thích vi sinh vật.` → `{"speaker": "男", "ja": "僕、微生物が好きなんだ。", "meaning": {"vi": "Tớ thích vi sinh vật."}}`.

# Ví dụ A – N3, lựa chọn chữ, có `Nghĩa:`, câu trích tách được và câu trích giữa câu (12125_1)

Đầu vào (rút gọn): `cac_lua_chon` = `{"1": "駅", "2": "会社", "3": "レストラン", "4": "自分の家"}`, `dap_an_so` = 4, `can_ghi_full_translation` = false, `goi_y_cau_hoi` = `{"ja": "男の人はまずどこへ行きますか。", "vi": "Người đàn ông sẽ đi đâu trước?"}`,

```
1. ｜駅《えき》
Nghĩa: Nhà ga
Người đàn ông nói: 「うん、でも、ワイン｜飲《の》みたいから、｜今日《きょう》はうちに｜置《お》いてから｜行《い》くよ。」(Ừ, nhưng vì muốn uống rượu vang nên hôm nay tôi sẽ để xe ở nhà rồi đi.)
Câu này cho thấy anh ấy sẽ về nhà trước để gửi xe máy rồi mới đi tiếp. Sau đó sẽ hẹn gặp mọi người tại cửa soát vé của nhà ga.
→ SAI.
2. ｜会社《かいしゃ》
Nghĩa: Công ty
Đoạn hội thoại bắt đầu ở công ty, nhưng người phụ nữ nói: 「｜私《わたし》たちはも、これから｜会《かい》｜社《しゃ》｜出《で》るところだけど、｜川《かわ》｜島《しま》は？」(Chúng tôi cũng sắp rời công ty rồi, còn anh Kawashima thì sao?)
Người đàn ông trả lời là sẽ làm xong việc rồi đi, không nói sẽ ở lại công ty.
→ SAI.
3. レストラン
Nghĩa: Nhà hàng
Người phụ nữ hỏi: 「じゃあ、お｜店《みせ》に｜直《ちょく》｜接《せつ》｜行《い》く？」(Vậy anh sẽ đi thẳng đến nhà hàng à?)
Người đàn ông trả lời: 「いや、｜改《かい》｜札《さつ》で｜待《ま》ってるよ。」(Không, tôi sẽ đợi ở cửa soát vé.)
Không phải đi thẳng đến nhà hàng.
→ SAI.
4. ｜自分《じぶん》の｜家《いえ》
Nghĩa: Nhà của mình
Người đàn ông nói rõ: 「｜今日《きょう》はうちに｜置《お》いてから｜行《い》くよ。」(Hôm nay tôi sẽ để xe ở nhà rồi đi.)
Điều này xác nhận anh ấy sẽ về nhà trước.
→ ĐÚNG.
```

Kết quả:

```json
{"schema": "reading_listening.v1", "question_id": 12125, "cau_con": 1,
 "summary": null,
 "question": {"ja": "男の人はまずどこへ行きますか。", "meaning": {"vi": "Người đàn ông sẽ đi đâu trước?"}},
 "options": [
  {"index": 1, "option_ja": "駅", "reading": null, "meaning": {"vi": "Nhà ga"}, "is_match": false,
   "quotes": [{"ja": "うん、でも、ワイン｜飲《の》みたいから、｜今日《きょう》はうちに｜置《お》いてから｜行《い》くよ。",
               "meaning": {"vi": "Ừ, nhưng vì muốn uống rượu vang nên hôm nay tôi sẽ để xe ở nhà rồi đi."}}],
   "analysis": {"vi": "Câu này cho thấy anh ấy sẽ về nhà trước để gửi xe máy rồi mới đi tiếp. Sau đó sẽ hẹn gặp mọi người tại cửa soát vé của nhà ga."}},
  {"index": 2, "option_ja": "会社", "reading": null, "meaning": {"vi": "Công ty"}, "is_match": false, "quotes": [],
   "analysis": {"vi": "Đoạn hội thoại bắt đầu ở công ty, nhưng người phụ nữ nói: 「⟪｜私《わたし》たちはも、これから｜会《かい》｜社《しゃ》｜出《で》るところだけど、｜川《かわ》｜島《しま》は？⟫」(Chúng tôi cũng sắp rời công ty rồi, còn anh Kawashima thì sao?)\nNgười đàn ông trả lời là sẽ làm xong việc rồi đi, không nói sẽ ở lại công ty."}},
  {"index": 3, "option_ja": "レストラン", "reading": null, "meaning": {"vi": "Nhà hàng"}, "is_match": false,
   "quotes": [{"ja": "じゃあ、お｜店《みせ》に｜直《ちょく》｜接《せつ》｜行《い》く？", "meaning": {"vi": "Vậy anh sẽ đi thẳng đến nhà hàng à?"}},
              {"ja": "いや、｜改《かい》｜札《さつ》で｜待《ま》ってるよ。", "meaning": {"vi": "Không, tôi sẽ đợi ở cửa soát vé."}}],
   "analysis": {"vi": "Không phải đi thẳng đến nhà hàng."}},
  {"index": 4, "option_ja": "自分の家", "reading": null, "meaning": {"vi": "Nhà của mình"}, "is_match": true,
   "quotes": [{"ja": "｜今日《きょう》はうちに｜置《お》いてから｜行《い》くよ。", "meaning": {"vi": "Hôm nay tôi sẽ để xe ở nhà rồi đi."}}],
   "analysis": {"vi": "Điều này xác nhận anh ấy sẽ về nhà trước."}}
 ],
 "correct": {"index": 4, "option_ja": "自分の家", "full_sentence": null}}
```

Ghi chú: `option_ja` theo đề (`駅`, không lấy `｜駅《えき》` ở dòng `1.`); khối 2 có chữ trước phần dẫn (`Đoạn hội thoại bắt đầu ở công ty, nhưng…`) nên câu trích **giữ trong analysis**.

# Ví dụ B – N5, lựa chọn tranh, chữ Latin trong nhận xét (12099_1, rút gọn khối 3)

```
3.
Giáo viên nói: 「その　｜本《ほん》は　｜練《れん》｜習《しゅう》に　｜使《つか》う　｜本《ほん》です。うちで　｜使《つか》って　ください。」(Quyển sách đó là sách dùng để luyện tập. Hãy dùng ở nhà nhé.)
Đáp án này có 'NIHONGO' và 'JAPANESE WORK BOOK れんしゅうノート' (sách luyện tập).
→ SAI.
Sách luyện tập được yêu cầu dùng ở nhà, không mang đến lớp.
```

```json
{"index": 3, "option_ja": "3", "reading": null, "meaning": null, "is_match": false,
 "quotes": [{"ja": "その　｜本《ほん》は　｜練《れん》｜習《しゅう》に　｜使《つか》う　｜本《ほん》です。うちで　｜使《つか》って　ください。",
             "meaning": {"vi": "Quyển sách đó là sách dùng để luyện tập. Hãy dùng ở nhà nhé."}}],
 "analysis": {"vi": "Đáp án này có 'NIHONGO' và 'JAPANESE WORK BOOK ⟪れんしゅうノート⟫' (sách luyện tập).\nSách luyện tập được yêu cầu dùng ở nhà, không mang đến lớp."}}
```

# Ví dụ C – đoạn phân tích mở đầu (12256_1, rút gọn)

`phan_tich_mo_dau`:
```
Phân tích đoạn hội thoại:
Giáo viên nói: 「｜家《か》｜族《ぞく》を｜紹《しょう》｜介《かい》する｜作《さく》｜文《ぶん》を｜書《か》いて、｜持《も》ってきてください。」(Hãy viết một đoạn văn giới thiệu về gia đình và mang đến.)
→ Vì vậy bắt buộc phải mang theo bài văn.
```
→ `"summary": [{"heading": {"vi": "Phân tích đoạn hội thoại:"}, "points": [{"vi": "Giáo viên nói: 「⟪｜家《か》｜族《ぞく》を｜紹《しょう》｜介《かい》する｜作《さく》｜文《ぶん》を｜書《か》いて、｜持《も》ってきてください。⟫」(Hãy viết một đoạn văn giới thiệu về gia đình và mang đến.)"}, {"vi": "→ Vì vậy bắt buộc phải mang theo bài văn."}]}]` (trong summary giữ nguyên cả phần dẫn và câu trích; chỉ bọc ⟪ ⟫).
