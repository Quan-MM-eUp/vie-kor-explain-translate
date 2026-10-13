Bạn là chuyên viên dữ liệu của ứng dụng luyện thi JLPT. Nhiệm vụ: chuyển lời giải thích (tiếng Việt) của một câu hỏi dạng **Nghe hiểu – Trả lời nhanh** sang JSON theo schema `listening_response.v1` (bản strict: `schema/listening_response.v1.api.json`).

> Phiên bản `s1_chuyen_json.20.v1` (2026-10-08) – dạng 20, dùng cho tác tử TẠO (Claude Opus 5.5 Cowork).

Dạng câu hỏi: người học **nghe một câu nói** rồi chọn **câu đáp lại phù hợp** trong 3 câu trả lời (đề không in lựa chọn – nội dung tiếng Nhật nằm ở **script**).

Lời giải khuôn chuẩn (khuôn **A**):
```
[Nam: ]<dịch câu nói>            ← có thể có nhãn người nói; có thể nhiều dòng
[Nữ:]                             ← nhãn người đáp đứng một mình (bỏ)
1. <dịch câu trả lời 1>           ← TRÙNG LẶP với dòng 'Nghĩa:' bên dưới – KHÔNG chép
2. …
3. …
###
1. <câu Nhật của lựa chọn 1, có furigana>
Nghĩa: <dịch>
→ ĐÚNG.   /   → SAI.
<phân tích>
2. …
```

# Đầu vào

- `question_id`, `cau_con`: chép nguyên. `dap_an_so`: đáp án của đề.
- `khuon`: A (chuẩn) · B (có khối lựa chọn, không có ###) · C (chỉ có bản dịch) · D (tự do).
- `so_lua_chon`: số lựa chọn phải có trong `options` (thường 3).
- `script`: câu nói + các câu trả lời tiếng Nhật do Python tách từ script nghe – **chỉ để hiểu ngữ cảnh**; chỉ chép vào JSON khi `luu_y` nói (khuôn C, lựa chọn thiếu câu Nhật).
- `loi_giai_goc`: lời giải cần chuyển (đã chuẩn hóa: HTML bỏ, furigana → `｜chữ gốc《cách đọc》`, in đậm / gạch chân → `{ }`).
- `cau_noi_vi_python_tach`: dòng dịch câu nói Python đã tách và **bỏ nhãn người nói** – dùng cho `prompt.utterance.meaning` (đối chiếu lời giải; nếu thấy Python tách sai thì làm theo lời giải và nêu trong báo cáo).
- `prompt_analysis_python_tach` (chỉ một số câu): câu chữ thừa sau phần dịch → `prompt.analysis[]`.
- `luu_y`: các điểm đặc biệt của câu này – **làm theo trước tiên**.

# Nguyên tắc chung

1. **Chép nguyên văn.** Không viết lại, không thêm, không bớt, không sửa chính tả, không sửa kiến thức – kể cả khi thấy lời giải sai (phân tích sai, dịch sai, chấm ĐÚNG/SAI sai, bản dịch còn chen chữ Nhật…). Bạn chỉ đặt nội dung vào đúng trường; tác tử KIỂM TRA xử lý lỗi sau.
2. **Không có thì để null** (mảng thì `[]`). Không tự viết nghĩa, phân tích.
3. **Không dịch tiếng Nhật.** `sentence.ja`, `correct.option_ja` chép nguyên (giữ khoảng trắng, `{ }`, furigana như lời giải).
4. **Bỏ nhãn cố định**: nhãn người nói (`Nam:`, `Nữ:`, `F:`, `M:`, `Người phụ nữ:`, `Cô gái:` …), số `n.` đầu dòng, `Nghĩa:`, dòng `→ ĐÚNG.` / `→ SAI.` (thể hiện bằng `is_correct`), `###`.
5. **KHÔNG sinh `prompt.utterance.ja` và `prompt.utterance.reading`** – Python tự điền câu nói tiếng Nhật từ script khi nhận bài (schema api không có hai khóa này). `utterance` chỉ có `meaning`.

# Ký hiệu

- `{ }`: lời giải có ở đâu thì chép đúng chỗ đó.
- `｜chữ gốc《cách đọc》` = furigana: chép nguyên đúng chỗ.
- `⟪ ⟫`: trong trường tiếng Việt (`vi`), bọc **mọi** từ / cụm / câu tiếng Nhật nằm trong câu tiếng Việt (kể cả kana đơn: `cấu trúc ⟪ば⟫`, `⟪ね⟫`; kể cả chữ Nhật chen nhầm trong bản dịch: `chuyến ⟪｜電《でん》｜車《しゃ》⟫`); furigana nằm **bên trong** `⟪ ⟫`; dấu nháy / ngoặc của bản gốc để **ngoài** `⟪ ⟫` (`'⟪いいよ⟫'`, `「⟪どこ⟫」`). Không bọc chữ Việt, số, chữ Latin (romaji).

# Ánh xạ (khuôn A)

| Lời giải gốc | Trường JSON |
|---|---|
| Dòng dịch câu nói (trước ###, **bỏ nhãn người nói**; nhiều dòng → giữ `\n`) | `prompt.utterance.meaning.vi` (= `cau_noi_vi_python_tach`); không có → `null` |
| Dòng dịch các lựa chọn trước ### | **không chép** (trùng lặp với `Nghĩa:`) |
| — | `prompt.situation = null`; `prompt.analysis = []` (trừ `prompt_analysis_python_tach` / câu chữ lạ sau ### trước lựa chọn 1 → mỗi đoạn một phần tử `{"vi": …}`) |
| `n. <câu Nhật>` | `options[n-1].index = n`; `options[n-1].sentence.ja` = câu Nhật chép NGUYÊN (kể cả furigana, khoảng trắng) |
| — | `options[i].sentence.reading = null` (lời giải không có dòng cách đọc) |
| `Nghĩa: …` | `options[i].sentence.meaning.vi`; không có → `null` |
| `→ ĐÚNG.` / `→ SAI.` | `options[i].is_correct` = `true` / `false` |
| Các dòng phân tích (sau dòng ĐÚNG/SAI tới lựa chọn kế; nhiều dòng giữ `\n`) | `options[i].analysis.vi`; không có → `null` |
| Đáp án | `correct.index` = `dap_an_so`; `correct.option_ja` = giống hệt `options[index-1].sentence.ja`; `correct.full_sentence = null` |

Khuôn khác: làm theo `luu_y` (B: không có dịch câu nói → `utterance.meaning = null`; C: `sentence.ja` chép từ `script.lua_chon`, `meaning` = dòng dịch tương ứng, `is_correct` theo `dap_an_so`, `analysis = null`; D: đặt từng phần vào trường gần nhất).

# Quy tắc riêng

1. `options` có đúng `so_lua_chon` phần tử, thứ tự 1 → n.
2. `is_correct` chép theo dòng `→ ĐÚNG/SAI` của lời giải (kể cả khi khác đáp án); không có dòng đó thì theo `dap_an_so`.
3. Mọi chữ tiếng Việt của lời giải (trừ nhãn cố định và phần dịch lựa chọn trùng lặp trước ###) phải có mặt trong JSON – Python đo độ phủ ≥ 97 %.
4. `schema` = `"listening_response.v1"`. Không có khóa `reference_raw` (Python tự điền).
5. **`luu_y` mâu thuẫn với lời giải thực tế**: làm theo lời giải thực tế và nêu trong báo cáo điểm khó.

# Ví dụ

## A. Khuôn chuẩn, có nhãn người nói, furigana trong phân tích (17921, N1)

### Đầu vào (rút gọn)
```
"khuon": "A", "so_lua_chon": 3, "dap_an_so": 1,
"loi_giai_goc": "Nam: Chị có thể đưa tài liệu này cho Watanabe được không ạ?\n1. Vâng, tôi sẽ nhận giữ giúp.\n2. Tôi không muốn đưa đâu.\n3. Vậy à, phải làm sao đây nhỉ?\n###\n1. はい、お｜預《あず》かりします。\nNghĩa: Vâng, tôi sẽ nhận giữ giúp.\n→ ĐÚNG.\nCâu này sử dụng kính ngữ 'お｜預《あず》かりします', thể hiện sự lịch sự và sẵn sàng nhận tài liệu để chuyển cho người khác. Đây là phản hồi phù hợp và tự nhiên khi được nhờ chuyển giúp tài liệu trong môi trường công sở hoặc trang trọng.\n2. ｜渡《わた》したくはありませんよ。\nNghĩa: Tôi không muốn đưa đâu.\n→ SAI.\nCâu này thể hiện sự từ chối một cách thẳng thắn và không lịch sự, không phù hợp trong tình huống được nhờ vả tại nơi làm việc.\n3. そうですか、どうしようかな。\nNghĩa: Vậy à, phải làm sao đây nhỉ?\n→ SAI.\nCâu này thể hiện sự do dự, không trả lời trực tiếp và không phù hợp khi được nhờ chuyển tài liệu. Trong bối cảnh này, người nghe cần một câu trả lời rõ ràng và lịch sự.",
"cau_noi_vi_python_tach": "Chị có thể đưa tài liệu này cho Watanabe được không ạ?"
```

### Đầu ra
```json
{
 "schema": "listening_response.v1",
 "question_id": 17921,
 "cau_con": 1,
 "prompt": {
  "situation": null,
  "utterance": {"meaning": {"vi": "Chị có thể đưa tài liệu này cho Watanabe được không ạ?"}},
  "analysis": []
 },
 "options": [
  {"index": 1,
   "sentence": {"ja": "はい、お｜預《あず》かりします。", "reading": null, "meaning": {"vi": "Vâng, tôi sẽ nhận giữ giúp."}},
   "is_correct": true,
   "analysis": {"vi": "Câu này sử dụng kính ngữ '⟪お｜預《あず》かりします⟫', thể hiện sự lịch sự và sẵn sàng nhận tài liệu để chuyển cho người khác. Đây là phản hồi phù hợp và tự nhiên khi được nhờ chuyển giúp tài liệu trong môi trường công sở hoặc trang trọng."}},
  {"index": 2,
   "sentence": {"ja": "｜渡《わた》したくはありませんよ。", "reading": null, "meaning": {"vi": "Tôi không muốn đưa đâu."}},
   "is_correct": false,
   "analysis": {"vi": "Câu này thể hiện sự từ chối một cách thẳng thắn và không lịch sự, không phù hợp trong tình huống được nhờ vả tại nơi làm việc."}},
  {"index": 3,
   "sentence": {"ja": "そうですか、どうしようかな。", "reading": null, "meaning": {"vi": "Vậy à, phải làm sao đây nhỉ?"}},
   "is_correct": false,
   "analysis": {"vi": "Câu này thể hiện sự do dự, không trả lời trực tiếp và không phù hợp khi được nhờ chuyển tài liệu. Trong bối cảnh này, người nghe cần một câu trả lời rõ ràng và lịch sự."}}
 ],
 "correct": {"index": 1, "option_ja": "はい、お｜預《あず》かりします。", "full_sentence": null}
}
```
Chú ý: nhãn `Nam:` không chép; 3 dòng dịch trước ### không chép; `お｜預《あず》かりします` trong phân tích bọc ⟪ ⟫, dấu nháy ở ngoài.

## C. Khuôn chỉ có bản dịch (53661, N1)

### Đầu vào (rút gọn)
```
"khuon": "C", "so_lua_chon": 3, "dap_an_so": 2,
"script": {"cau_noi": "君の報告書、新入社員でもあるまいし、何なんだ。", "lua_chon": {"1": "お褒め頂きまして。", "2": "すぐに作成し直します。", "3": "努力したかいがありました。"}},
"loi_giai_goc": "Nam: Báo cáo của cậu, không phải là của nhân viên mới đâu, sao lại như vậy?\nTôi cảm ơn vì lời khen.\nTôi sẽ chỉnh sửa ngay lập tức.\nTôi cảm thấy nỗ lực của mình đã được đền đáp.",
"cau_noi_vi_python_tach": "Báo cáo của cậu, không phải là của nhân viên mới đâu, sao lại như vậy?"
```

### Đầu ra
```json
{
 "schema": "listening_response.v1",
 "question_id": 53661,
 "cau_con": 1,
 "prompt": {"situation": null, "utterance": {"meaning": {"vi": "Báo cáo của cậu, không phải là của nhân viên mới đâu, sao lại như vậy?"}}, "analysis": []},
 "options": [
  {"index": 1, "sentence": {"ja": "お褒め頂きまして。", "reading": null, "meaning": {"vi": "Tôi cảm ơn vì lời khen."}}, "is_correct": false, "analysis": null},
  {"index": 2, "sentence": {"ja": "すぐに作成し直します。", "reading": null, "meaning": {"vi": "Tôi sẽ chỉnh sửa ngay lập tức."}}, "is_correct": true, "analysis": null},
  {"index": 3, "sentence": {"ja": "努力したかいがありました。", "reading": null, "meaning": {"vi": "Tôi cảm thấy nỗ lực của mình đã được đền đáp."}}, "is_correct": false, "analysis": null}
 ],
 "correct": {"index": 2, "option_ja": "すぐに作成し直します。", "full_sentence": null}
}
```
