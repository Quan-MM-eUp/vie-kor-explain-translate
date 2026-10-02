# Hướng dẫn dịch lời giải sang tiếng Hàn (bước 3)

Tài liệu này là **prompt giao cho tác tử Claude** (Haiku hoặc Sonnet) ở bước 3. Sửa file này và `glossary_ko.json` để tinh chỉnh bản dịch.

## Nhiệm vụ

Với mỗi file `json_vi/final/<sample_id>.json`:

1. Tìm **mọi object có khóa `"vi"`**. Đây là các trường cần dịch.
2. Thêm khóa `"ko"` **ngay cạnh** `"vi"` trong cùng object, với nội dung là bản dịch tiếng Hàn: `{"vi": "…", "ko": "…"}`.
3. **Không thay đổi bất kỳ thứ gì khác**: không sửa `vi`, không sửa trường tiếng Nhật (`ja`, `reading`, `option_ja`…), không đổi số, không thêm/bớt khóa, không đổi thứ tự.
4. Lưu kết quả vào `json_ko/<model>/<sample_id>.json`.

Ngữ cảnh để hiểu đúng ý (chỉ đọc, không dịch): câu hỏi, 4 lựa chọn, đáp án trong `samples/raw/<sample_id>.json`, và các trường tiếng Nhật trong chính file JSON.

## Quy tắc dịch

1. **Người đọc**: người Hàn Quốc đang học tiếng Nhật, luyện thi JLPT. Dịch chính xác nghĩa và thuật ngữ, câu văn tự nhiên như tài liệu học tiếng Hàn.
2. **Văn phong**: câu hoàn chỉnh kết thúc bằng **-습니다/-ㅂ니다**. Không dùng -한다/-이다. Cụm nghĩa ngắn (VD nghĩa của một từ như "ảo giác", "thu nhập") dịch thành danh từ/cụm từ, không cần đuôi câu.
3. **Nội dung trong `⟪ ⟫` là tiếng Nhật, giữ nguyên từng ký tự**, kể cả dấu `⟪ ⟫`. Được phép đổi vị trí theo ngữ pháp tiếng Hàn và thêm trợ từ sau `⟫`. VD: `"⟪段落⟫ không ⟪言及⟫ đến…"` → `"⟪段落⟫은 … ⟪言及⟫하지 않습니다."`
4. **Gạch chân `{ }`**: nếu bản tiếng Việt có 1 cặp `{ }`, bản tiếng Hàn phải có đúng 1 cặp, đặt quanh từ/cụm **tương ứng** trong câu tiếng Hàn. VD: `"Anh Tanaka chỉ là một người bạn {đơn thuần}."` → `"다나카 씨는 {단순한} 친구일 뿐입니다."`
5. **Dấu ngoặc kép, số, ký hiệu `（　）`, `★`, `[1]`** giữ nguyên.
6. **Thuật ngữ**: dùng theo `instructions/glossary_ko.json`. Thuật ngữ chưa có trong bảng thì dịch theo cách dùng phổ biến trong sách học tiếng Nhật ở Hàn Quốc.
7. **Nội dung chỉ dành cho người Việt** (âm Hán Việt, ví dụ địa danh/nhân vật Việt Nam…): vẫn dịch nguyên nghĩa, **và** ghi vào file ghi chú để xem xét bản địa hóa.
8. **Không sửa lỗi nội dung của bản gốc.** Nếu thấy bản tiếng Việt sai hoặc khó hiểu, dịch trung thành và ghi vào ghi chú.

## Ghi chú (bắt buộc)

Ghi vào `json_ko/<model>/_notes.json`:

```json
[{"sample_id": "…", "path": "$.options[2].analysis", "loai": "ban_dia_hoa | nghi_loi_ban_goc | khong_chac_thuat_ngu", "mo_ta": "…"}]
```
