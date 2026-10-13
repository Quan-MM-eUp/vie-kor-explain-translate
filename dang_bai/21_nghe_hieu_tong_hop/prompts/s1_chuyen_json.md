# Hướng dẫn chi tiết – chuyển lời giải "Nghe hiểu tổng hợp" sang JSON tiếng Việt (dạng 21) · v1

> Phiên bản `s1_chuyen_json.21.v1` (2026-10-08). Schema: `schema/reading_listening.v1.api.json` (strict – đủ mọi khóa, không có thì `null`, không thêm khóa).
> Nguyên tắc tối thượng: **chép trung thành lời giải gốc** – không thêm, không bớt, không sửa, không viết lại, không tự dịch phần lời giải không có.

## 1. Đầu vào (`yeu_cau` trong file_vao)

| Khóa | Ý nghĩa |
|---|---|
| `khuon` | `A` = [bản dịch lời thoại] ### [phân tích 1–4]; `B` = [bản dịch + đề 2 câu hỏi] ### `Thông tin:` [đoạn then chốt]; `C_vi` = chỉ có bản dịch (+ câu hỏi, lựa chọn) |
| `huong_dan_khuon` | cách điền riêng của khuôn |
| `de_bai.cau_hoi_de_xuat_ja` | câu hỏi tiếng Nhật Python tìm được (cột câu hỏi của đề, hoặc câu hỏi ở cuối lời thoại – đã bỏ nhãn 質問1 / Q：) |
| `de_bai.cac_lua_chon`, `dap_an_so` | 4 lựa chọn của đề và đáp án |
| `loi_thoai_ja` | lời thoại tiếng Nhật đã làm sạch, mỗi dòng `Jn: …` (Python đã cắt câu hỏi + danh sách lựa chọn ở cuối – xem `cau_hoi_python_da_cat_khoi_loi_thoai`) |
| `ban_dich_vi` | bản dịch tiếng Việt của lời giải (phần trước `###`), mỗi dòng `Vn: …` |
| `full_translation` = "null – Python chép…" | câu con 2 của bài 2 câu hỏi: **không** ghép lời thoại, để `full_translation: null` |
| `loi_giai_goc` | toàn bộ lời giải đã chuẩn hóa (furigana `｜漢字《かな》`) |
| `luu_y` | lưu ý riêng của câu này (theo cờ Python) |

## 2. Ánh xạ

| Lời giải / đầu vào | Trường JSON |
|---|---|
| — | `schema = "reading_listening.v1"`, `question_id`, `cau_con` như đầu vào |
| Lời thoại `Jn` + bản dịch `Vn` | `full_translation = [{"label": null, "lines": [...]}]` – mỗi **lượt thoại** một phần tử `{speaker, ja, meaning}` (mục 3) |
| `cau_hoi_de_xuat_ja` | `question.ja` (chép đúng chuỗi; `null` nếu không có) |
| dòng dịch câu hỏi (thường là dòng cuối trước `###`, hoặc `Câu hỏi: …` / `Câu 1: …` – bỏ nhãn) | `question.meaning.vi` (không có → `null`) |
| `1. …` (dòng lựa chọn của phân tích, có furigana) | `options[i].option_ja` – chép đúng dòng của **lời giải** (kể cả furigana); lời giải không có dòng đó → chép lựa chọn của đề |
| — | `options[i].reading = null` (lời giải không có dòng cách đọc riêng) |
| `Nghĩa: …` | `options[i].meaning.vi` |
| `「câu Nhật」` + `(dịch)` ngay sau | `options[i].quotes[] = {"ja": "câu Nhật (giữ furigana)", "meaning": {"vi": "dịch (bỏ ngoặc)"}}` – mỗi cặp 「」 một phần tử, theo thứ tự; không có dòng dịch → `meaning: null` |
| Nhãn dẫn trước câu trích (`Nam nói:`, `Nữ hỏi:`, `Người dẫn chương trình nói:`, `Nam còn nói:`) | **bỏ** (không chép) – chỉ khi nhãn là "<người> <động từ nói>:" thuần túy. Câu dẫn có nội dung khác (`Tuy nhiên, người đàn ông xem chương trình nói:`) → phần nội dung (`Tuy nhiên, …`) vào `analysis` |
| Nhãn `Phân tích đoạn hội thoại:` / `Phân tích:` | bỏ |
| Câu nhận xét còn lại (giữa / sau các trích dẫn, sau `→ SAI.`) | `options[i].analysis.vi` – giữ thứ tự, nối bằng `\n`; tiếng Nhật chen giữa bọc `⟪ ⟫`; không có → `null` |
| `→ ĐÚNG.` / `→ SAI.` (kết luận cuối khối) | `options[i].is_match = true / false` (dòng `→ Đúng, …` giữa khối là câu nhận xét – chép vào analysis kể cả mũi tên) |
| Khối `Thông tin:` (khuôn B) | `key_info = [{speaker, ja, meaning}]` – ghép dòng JA với dòng dịch VI tương ứng (cùng thứ tự); nhãn người nói như mục 3 |
| — | `summary = null`; `correct = {"index": dap_an_so, "option_ja": <option_ja của đáp án>, "full_sentence": null}` (Python sẽ điền lại) |

## 3. Ghép lời thoại (`full_translation`) – phần tốn công nhất, làm cẩn thận

- **Nguồn `ja` là `loi_thoai_ja`** (không lấy câu trích trong phân tích). Mỗi lượt thoại / câu dẫn chuyện một phần tử theo đúng thứ tự.
- `speaker` = nhãn người nói ở đầu dòng JA, **giữ nguyên** (`男`, `女２`, `店員`, `M1`, `Ｆ`…); bỏ nhãn và dấu `：` khỏi `ja`. Dòng dẫn chuyện / thông báo không nhãn → `speaker: null`.
- Dòng JA chứa **nhiều lượt** dính nhau (vd `…言っていますか。女：遅かったね。男：…`) → tách thành nhiều phần tử tại nhãn người nói; phần trước nhãn đầu tiên là dòng dẫn (speaker null). Một lượt bị xuống dòng giữa chừng (vd `…ビジネスコミュニケーション` / `がお勧めだけど`) → **gộp** thành một phần tử.
- `ja`: chép **nguyên văn** chữ của `Jn` (Python so từng chữ – chữ thừa / sửa chữ là LỖI). Không sửa lỗi gõ của lời thoại (vd `明、月曜日`, `フ降り`) – tác tử KIỂM TRA ghi chú. Giữ `(i)` / `(ii)`.
- `meaning.vi` = dòng / phần tương ứng của `ban_dich_vi`, **bỏ nhãn người nói tiếng Việt** (`Nam:`, `Nữ:`, `Người phụ nữ 2:`, `Nhân viên (nữ):`). Bản dịch gộp nhiều lượt trong một dòng → tách theo lượt; bản dịch tách một lượt thành nhiều dòng → nối bằng dấu cách. Giữ `(i)` / `(ii)` nếu bản dịch có.
- Dòng dịch **câu hỏi** và **danh sách lựa chọn** ở cuối bản dịch **không** đưa vào `full_translation` (chúng vào `question.meaning` / `options[i].meaning`). Dòng dịch thừa không ứng với lượt nào (vd câu dẫn chỉ có trong bản dịch) → phần tử `{"speaker": null, "ja": null, "meaning": {"vi": …}}` ở đúng vị trí.
- Lượt thoại không có dòng dịch tương ứng → `meaning: null` (không tự dịch).
- Không có `loi_thoai_ja` (cờ `loi_thoai_trong`) nhưng có bản dịch → mỗi dòng dịch một phần tử `{"speaker": null, "ja": null, "meaning": {...}}`. Không có cả hai → `full_translation: null`.

## 4. Ký hiệu

- **Mọi** tiếng Nhật nằm trong câu tiếng Việt (analysis, meaning…) bọc `⟪ ⟫` (kể cả kana đơn, kể cả có furigana: `⟪｜表現《ひょうげん》⟫`). Không bọc tiếng Nhật ở trường `ja` / `option_ja`.
- Furigana `｜chữ《cách đọc》`: chép nguyên đúng chỗ như lời giải; không thêm, không bỏ. Lời thoại `Jn` không có furigana – giữ nguyên.
- `{ }` (chỗ in đậm / gạch chân của lời giải) giữ nguyên nếu có.
- Chuỗi nhiều dòng giữ `\n`; không thêm khoảng trắng đầu / cuối; không có nội dung → `null` (không dùng chuỗi rỗng).

## 5. Ví dụ (rút gọn) – khuôn A, 12309_1

Lời giải (trích):
```
Sinh viên đại học đang xem tivi và nói chuyện với nhau.
Nam: Sau đây là thời tiết của tuần tới. Cơn mưa hiện tại này, ngày mai, thứ Hai cũng sẽ tiếp tục rơi suốt cả ngày.
…
Khi nào họ đi ngắm hoa anh đào?
###
1. ｜月《げつ》｜曜《よう》｜日《び》
Nghĩa: Thứ Hai
Phân tích đoạn hội thoại:
Nam nói: 「｜今降《いまふ》っているこの｜雨《あめ》は｜明《あ》、｜月《げつ》｜曜《よう》｜日《び》も一日中降り｜続《つづ》くでしょう。」
(Cơn mưa hiện tại này, ngày mai, thứ Hai cũng sẽ tiếp tục rơi suốt cả ngày.)
…
→ SAI.
Thứ Hai trời mưa cả ngày, họ đã quyết định không đi vào ngày này.
```
JSON (trích):
```json
{"schema": "reading_listening.v1", "question_id": 12309, "cau_con": 1,
 "full_translation": [{"label": null, "lines": [
   {"speaker": null, "ja": "大学生がテレビを見て話しています。", "meaning": {"vi": "Sinh viên đại học đang xem tivi và nói chuyện với nhau."}},
   {"speaker": "男", "ja": "それでは来週の天気です。今降っているこの雨は明、月曜日も一日中フ降り続くでしょう。…", "meaning": {"vi": "Sau đây là thời tiết của tuần tới. Cơn mưa hiện tại này, ngày mai, thứ Hai cũng sẽ tiếp tục rơi suốt cả ngày. …"}}]}],
 "summary": null,
 "question": {"ja": "いつ花見に行きますか。", "meaning": {"vi": "Khi nào họ đi ngắm hoa anh đào?"}},
 "options": [
  {"index": 1, "option_ja": "｜月《げつ》｜曜《よう》｜日《び》", "reading": null, "meaning": {"vi": "Thứ Hai"}, "is_match": false,
   "quotes": [{"ja": "｜今降《いまふ》っているこの｜雨《あめ》は｜明《あ》、｜月《げつ》｜曜《よう》｜日《び》も一日中降り｜続《つづ》くでしょう。",
               "meaning": {"vi": "Cơn mưa hiện tại này, ngày mai, thứ Hai cũng sẽ tiếp tục rơi suốt cả ngày."}}, "…"],
   "analysis": {"vi": "Thứ Hai trời mưa cả ngày, họ đã quyết định không đi vào ngày này."}}, "…"],
 "key_info": null,
 "correct": {"index": 2, "option_ja": "｜火《か》｜曜《よう》｜日《び》", "full_sentence": null}}
```
(Lời thoại gốc dòng 2 có `男：` → `speaker: "男"`; lỗi gõ `明`, `フ降り` giữ nguyên trong `ja`; câu trích giữ đúng chữ của lời giải.)

## 6. Khuôn B / C_vi (thiếu phân tích – Python và tác tử KIỂM TRA sẽ gắn cờ, bạn chỉ chép phần có)

- **B** (bài 2 câu hỏi): `question` / `options` là của câu con này; `options[i].meaning` lấy từ danh sách `Câu N: … 1. … 4. …` của **câu con này** trong bản dịch; `quotes = []`, `analysis = null`, `is_match = (index == dap_an_so)`; `key_info` = toàn bộ khối `Thông tin:` (dòng JA ghép với dòng dịch cùng thứ tự; giữ `(i)` / `(ii)`), **giống nhau ở cả 2 câu con**.
- **C_vi**: `question.meaning` = dòng `Câu hỏi: …` (bỏ nhãn); `options[i].meaning` = dòng dịch lựa chọn tương ứng ở cuối bản dịch (theo thứ tự); `quotes = []`, `analysis = null`, `is_match = (index == dap_an_so)`; `key_info = null`.
