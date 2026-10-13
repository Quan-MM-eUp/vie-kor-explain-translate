# Hướng dẫn chi tiết – chuyển lời giải dạng 17 (Nghe hiểu điểm chính) sang JSON tiếng Việt · v1

> Phiên bản `s1_chuyen_json.17.v1` (2026-10-08). Schema `reading_listening.v1` (`schema/reading_listening.v1.api.json`).

## 1. Dữ liệu gốc

- **Lời thoại tiếng Nhật** (cột `transcript_vi` – tên cột gây nhầm, nội dung là tiếng Nhật): dòng dẫn tình huống + câu hỏi, các lượt thoại `女：…` / `M：…` / `先生：…`, thường lặp lại câu hỏi ở cuối; `(i)` = chỗ chứa đáp án.
- **Lời giải** (`giai_thich_vi`): bản dịch Việt từng dòng (`Nam: …`, `F: …`, `Người phụ nữ: …`), câu hỏi tiếng Việt, nghĩa 4 lựa chọn (có / không đánh số), rồi tùy khuôn:
  - **A** `### Thông tin` + các dòng thoại then chốt tiếng Nhật + bản dịch;
  - **B** `### Đáp án đúng là câu số N. Vì …` (lý do);
  - **C** không có phần sau `###`.
  (Khuôn D – không có tiếng Việt – Python đã loại, bạn không gặp.)

## 2. Python đã làm sẵn (trong `yeu_cau`)

- `luot_thoai_tieng_nhat`: lượt thoại đã tách (J0, J1…), nhãn người nói đã chuẩn hóa (男/M/Ｍ → `M`, 女/F/Ｆ → `F`, nhãn khác giữ nguyên), đã bỏ 4 lựa chọn và phần từ vựng `*** 言葉表現` ở cuối lời thoại.
- `dong_viet_goc`: các dòng Việt gốc (V0, V1…) của lời thoại, 4 dòng nghĩa lựa chọn, phần sau `###`.
- `khung_json`: JSON gần hoàn chỉnh – lượt thoại, gợi ý ghép nghĩa Việt (`python_ghep` cho biết cách ghép; "KHÔNG ghép được" → mọi `meaning` = null), câu hỏi, 4 lựa chọn + nghĩa, `is_match`, `correct`, `key_info`, `analysis`.

## 3. Việc của bạn: soát khung và ghi JSON hoàn chỉnh

Đọc từng cặp **lượt Nhật ↔ dòng Việt** và sửa khung cho đúng lời giải gốc:

1. **`full_translation`** = `[{"label": null, "lines": [...]}]` – **một** khối. Mỗi dòng `{"speaker", "ja", "meaning": {"vi"} | null}`.
   - `ja`: chép NGUYÊN lượt thoại tiếng Nhật (kể cả `(i)`, dấu câu, khoảng trắng toàn góc, furigana `｜…《…》`), **không** có nhãn người nói. Python kiểm tra: nối mọi `ja` phải ra đúng lời thoại gốc (K-LT) – không được thêm / bớt / đổi chữ / đảo dòng.
   - Được **gộp** hai lượt liền nhau (nối `ja` liền nhau) hoặc **tách** một lượt dài thành hai dòng nếu bản Việt gộp / tách như vậy – miễn là nối lại vẫn đúng nguyên văn. Không gộp lượt của hai người nói khác nhau (K-NG so dãy người nói).
   - `speaker`: nhãn như khung (M / F / nhãn gốc); dòng dẫn tình huống, câu hỏi lặp lại cuối bài → `null`.
   - `meaning.vi`: dòng Việt tương ứng, **bỏ nhãn người nói tiếng Việt** ở đầu (`Nam:`, `Nữ:`, `F:`, `Người phụ nữ:`, `Sếp:`, `Con trai:`…), giữ nguyên phần còn lại (kể cả `(i)`, lỗi chính tả, "...", dấu lạ – tác tử KIỂM TRA xử lý định dạng). Một lượt Nhật ứng với nhiều dòng Việt → nối bằng một dấu cách. Lượt Nhật không có bản dịch → `null`. Dòng Việt không có lượt Nhật tương ứng (vd câu hỏi Việt mà lời thoại không lặp lại) → không bỏ: nối vào dòng kề phù hợp, hoặc nếu là câu hỏi thì chỉ dùng cho `question.meaning`.
   - Thứ tự `meaning` phải theo đúng thứ tự dòng Việt (K-DV: nối các `meaning` phải phủ ≥ 97% bản dịch gốc theo đúng thứ tự).
2. **`question`**: `ja` = câu hỏi tiếng Nhật như khung (ưu tiên `cau_hoi` của đề; không có thì câu hỏi trong lời thoại – chỉ phần câu hỏi, không chép câu dẫn tình huống). `meaning.vi` = câu hỏi tiếng Việt tương ứng (chỉ phần câu hỏi). Không có → `null`.
3. **`options`** (4 phần tử, `index` 1–4): `option_ja` = lựa chọn của đề (khung đã điền, đã bỏ số `1.`); `reading` = null; `meaning.vi` = dòng nghĩa lựa chọn (bỏ số `1.`); không có dòng nghĩa → `null`; `is_match` = true **chỉ** ở `dap_an_so`; `quotes` = []; `analysis` = null trừ lựa chọn đúng (xem 5).
4. **`key_info`** (dòng thoại then chốt):
   - Khuôn A: mỗi dòng Nhật của phần Thông tin → `{"speaker", "ja", "meaning"}`; `ja` bỏ nhãn người nói và **bỏ `(i)`**; `meaning.vi` = dòng Việt tương ứng của phần Thông tin, bỏ nhãn và `(i)`. Thông tin chỉ có tiếng Nhật → `meaning` = null (Python tự chép nghĩa từ dòng thoại).
   - Khuôn B: `[]`.
   - Khuôn C: như khung (dòng có `(i)` nếu duy nhất, `meaning` = null – Python chép), không thì `[]`.
5. **`analysis`** của **lựa chọn đúng** (`options[dap_an_so − 1].analysis.vi`): khuôn B = nguyên văn phần sau `###` (giữ `\n`); khuôn A có câu giải thích sau Thông tin ("Đáp án … / Vì …") = nguyên văn các câu đó. Các lựa chọn khác `analysis` = null.
6. `correct` = `{"index": dap_an_so, "option_ja": lựa chọn đúng của đề, "full_sentence": null}`; `summary` = null; `schema` = "reading_listening.v1"; `question_id`, `cau_con` như đề.
7. **Tiếng Nhật trong câu tiếng Việt** (thường ở lý do khuôn B, vd "Vì người phụ nữ nói 毎日"): bọc `⟪ ⟫` (`⟪毎日⟫`). Không bọc dấu `・` đứng riêng.
8. **Không** sửa nội dung, kể cả khi thấy dịch sai / lời thoại gõ sai – chép nguyên, chỉ ghi vào phần "điểm khó" khi báo cáo. Không thêm khóa lạ, không có `reference_raw`.

## 4. Ví dụ (13594_1 – khuôn A, Python ghép 1–1)

Lời thoại: `女の人が図書館で本を借ります。女の人は何冊まで、何週間借りることができますか。` / `女：あの、本を借りたいんですが。` / … / `男：それだと、すみませんが、3冊までなんです。ただ3週間まで借りられます。 (i)` / `女の人は何冊まで、何週間借りることができますか。`
Lời giải: `Cô gái đang mượn sách ở thư viện. …?` / `Nữ: Em muốn mượn sách` / … / `Nam: À thế thì 3 cuốn thôi, nhưng được 3 tuần (i)` / `Cô gái có thể mượn tối đa …?` / `1. 3 cuốn 2 tuần` … / `###` / `Thông tin:` / `男：それだと、…借りられます。` / `Nam: À thế thì 3 cuốn thôi, nhưng được 3 tuần`

```json
{"schema": "reading_listening.v1", "question_id": 13594, "cau_con": 1,
 "full_translation": [{"label": null, "lines": [
   {"speaker": null, "ja": "女の人が図書館で本を借ります。女の人は何冊まで、何週間借りることができますか。", "meaning": {"vi": "Cô gái đang mượn sách ở thư viện. Cô gái có thể mượn tối đa mấy cuốn sách và trong thời gian bao lâu?"}},
   {"speaker": "F", "ja": "あの、本を借りたいんですが。", "meaning": {"vi": "Em muốn mượn sách"}},
   {"speaker": "M", "ja": "それだと、すみませんが、3冊までなんです。ただ3週間まで借りられます。 (i)", "meaning": {"vi": "À thế thì 3 cuốn thôi, nhưng được 3 tuần (i)"}},
   {"speaker": null, "ja": "女の人は何冊まで、何週間借りることができますか。", "meaning": {"vi": "Cô gái có thể mượn tối đa mấy cuốn sách và trong thời gian bao lâu?"}}]}],
 "summary": null,
 "question": {"ja": "女の人は何冊まで、何週間借りることができますか。", "meaning": {"vi": "Cô gái có thể mượn tối đa mấy cuốn sách và trong thời gian bao lâu?"}},
 "options": [
   {"index": 1, "option_ja": "3冊2週間です。", "reading": null, "meaning": {"vi": "3 cuốn 2 tuần"}, "is_match": false, "quotes": [], "analysis": null},
   {"index": 2, "option_ja": "3冊3週間です。", "reading": null, "meaning": {"vi": "3 cuốn 3 tuần"}, "is_match": true, "quotes": [], "analysis": null},
   {"index": 3, "option_ja": "10冊2週間です。", "reading": null, "meaning": {"vi": "10 cuốn 2 tuần"}, "is_match": false, "quotes": [], "analysis": null},
   {"index": 4, "option_ja": "10冊3週間です。", "reading": null, "meaning": {"vi": "10 cuốn 3 tuần"}, "is_match": false, "quotes": [], "analysis": null}],
 "key_info": [{"speaker": "M", "ja": "それだと、すみませんが、3冊までなんです。ただ3週間まで借りられます。", "meaning": {"vi": "À thế thì 3 cuốn thôi, nhưng được 3 tuần"}}],
 "correct": {"index": 2, "option_ja": "3冊3週間です。", "full_sentence": null}}
```
(Ví dụ rút gọn – thực tế `lines` có đủ mọi lượt thoại.)

**Khuôn B** (24736_1): `options[3].analysis.vi` = `"Đáp án 4. 40 bản. Vì có 30 người tham gia họp nhưng theo trưởng phòng nói chuẩn bị nhiều hơn 10 bản."`, `key_info` = [].

**Không ghép được** (vd 12288_1: lời thoại có 2 lượt `M` liền nhau `もし訳ございません…` / `木曜日の夜に帰国いたしますが。。。。`, bản Việt gộp thành một dòng): gộp hai lượt `M` thành một dòng (nối `ja`) và gán dòng Việt `Người đàn ông: Tôi xin lỗi. Takahashi đang đi công tác…` (bỏ nhãn).
