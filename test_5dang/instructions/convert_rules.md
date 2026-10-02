# Hướng dẫn chuyển lời giải tiếng Việt sang JSON (bước 2)

Tài liệu này là **prompt giao cho tác tử Claude** (Haiku hoặc Sonnet) ở bước 2. Sửa file này để tinh chỉnh cách chuyển đổi; lần chạy sau sẽ dùng bản mới.

## Nhiệm vụ

Với mỗi file `samples/raw/<sample_id>.json`, đọc cột `giai_thich_vi` (lời giải tiếng Việt gốc) và tạo **một file JSON** theo đúng schema ghi ở trường `schema` của mẫu, lưu vào `json_vi/<model>/<sample_id>.json`.

Tài liệu tham khảo bắt buộc đọc trước:

- Schema: `../explanation_schema/explanation_schemas_v1.json` (mục tương ứng với `schema` của mẫu)
- Ví dụ chuẩn của từng dạng: `../explanation_schema/examples/01…05_*.json`

## Quy tắc bắt buộc

1. **Chép nguyên văn, không viết lại.** Câu tiếng Việt và tiếng Nhật phải giữ đúng từng chữ như bản gốc. Không sửa lỗi chính tả, không diễn đạt lại, không thêm, không bớt ý. Nếu thấy bản gốc có lỗi, **vẫn chép nguyên** và ghi vào file ghi chú (mục "Ghi chú" bên dưới).
2. **Chỉ bỏ những thứ sau:**
   - Nhãn cố định, vì app tự hiển thị: "Câu hỏi:", "Đề bài:", "Từ:", "Cách đọc:", "Nghĩa:", "Thể từ điển:", "PHÂN TÍCH", "LỰA CHỌN ĐÚNG", "THÔNG TIN THAM KHẢO", "Câu hoàn chỉnh:", "→ ĐÚNG/SAI", dấu `###`.
   - Thẻ HTML và furigana (`<ruby>`, `<rt>`, `<b>`, `<span …>`, `<br>`, `&nbsp;`…). Trường `ja` lưu chữ Nhật thường, không kèm furigana.
3. **Tách tiếng Nhật ra trường riêng** (`ja`, `reading`, `option_ja`…) ở mọi chỗ schema có. Tiếng Nhật **không tách ra được** khỏi câu tiếng Việt thì bọc trong `⟪ ⟫`. Ví dụ: `"vi": "Đây là cách đọc của từ \"⟪冷凍⟫\" (làm lạnh)."`
4. **Gạch chân:** phần được gạch chân hoặc bôi đậm trong đề (thẻ `<u>`, `<b>` trong câu hỏi hoặc câu đề) đặt trong `{ }` ở cả 3 trường `ja`, `reading`, `meaning.vi`. Mỗi câu tối đa 1 cặp. Ví dụ: `"ja": "田中さんは{単なる}友人です。"`, `"reading": "たなかさんは{たんなる}ゆうじんです。"`, `"meaning": {"vi": "Anh Tanaka chỉ là một người bạn {đơn thuần}."}`. Nếu bản gốc không có cách đọc thì `reading` = `null`.
5. **Trường không có trong bản gốc thì để `null`** (hoặc `[]` với danh sách). Không tự viết thêm nội dung cho đủ trường.
6. **Đáp án:** `correct.index` phải bằng `dap_an_so`; `correct.option_ja` là lựa chọn đúng (bỏ thẻ HTML).
7. **`question_id` và `cau_con`** lấy từ file mẫu (kiểu số nguyên). Trường `schema` ghi dạng `"<schema>.v1"`.
8. **Chỉ trả về JSON hợp lệ.** Không thêm khóa ngoài schema, không kèm chú thích trong JSON.

## Gợi ý ánh xạ theo dạng bài

| Dạng | Phần trong bản gốc → trường JSON |
|---|---|
| Cách đọc kanji (JSON cũ) | `question.text/reading/mean` → `question.ja/reading/meaning.vi`; `kanji`, `kanji_reading`, `kanji_mean` → `word.ja/reading/meaning.vi`; `kanji_jishokei` → `word.dictionary_form`; `answers[].note` → `options[].analysis.vi` (lựa chọn đúng: `null`); `reference` → `reference.vi`. Thẻ `<u>` trong `text/reading/mean` → `{ }` |
| Thay đổi cách nói | Câu đề → `question`; mỗi dòng "n. 語 (よみ): Nghĩa là "…". …" trong PHÂN TÍCH → `options[]` (`option_ja`, `reading`, `meaning` = phần trong "Nghĩa là", `analysis` = phần còn lại); THÔNG TIN THAM KHẢO → `reference.intro` + `reference.terms[]` |
| Cách viết từ | Câu đề → `question` (phần hiragana gạch chân đặt trong `{ }`); PHÂN TÍCH → `options[]` (`exists` = false nếu "không tồn tại"); THÔNG TIN THAM KHẢO → `reference.text` (+ `examples[]` nếu có ví dụ dạng câu/cách đọc/nghĩa) |
| Điền từ theo văn cảnh | Câu đề (giữ `（　）`) → `question`; PHÂN TÍCH → `options[]`; LỰA CHỌN ĐÚNG + Câu hoàn chỉnh + Nghĩa → `correct.full_sentence` |
| Hình thành từ | Câu đề → `question` (ô trống + phần liền kề đặt trong `{ }` nếu bản gốc bôi đậm); mỗi lựa chọn: chữ, cách đọc, nghĩa → `option_ja/reading/gloss`; từ ghép → `compound`; "không có nghĩa trong tiếng Nhật" → `is_valid` = false; LỰA CHỌN ĐÚNG → `correct` (+ `full_sentence`); THÔNG TIN THAM KHẢO → `reference` |

## Ghi chú (bắt buộc)

Ghi tất cả vấn đề phát hiện được vào `json_vi/<model>/_notes.json`, dạng danh sách:

```json
[{"sample_id": "…", "loai": "loi_ban_goc | khong_chac_anh_xa | thieu_thong_tin", "mo_ta": "…"}]
```

Ví dụ: bản gốc ghi lời giải của lựa chọn 2 vào `note` của lựa chọn 1; lựa chọn gốc có furigana dính vào chữ; không chắc một đoạn thuộc `analysis` hay `reference`.
