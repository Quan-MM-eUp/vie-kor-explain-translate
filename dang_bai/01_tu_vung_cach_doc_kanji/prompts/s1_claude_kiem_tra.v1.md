# Hướng dẫn Claude – Bước 1.2: kiểm tra JSON tiếng Việt và sửa lỗi (dạng 01)

> Model: **Claude Opus 5.5**, chạy trong Claude Cowork (không qua API). Nếu chia việc cho tác tử con thì tác tử con cũng dùng Opus 5.5.

**Nhiệm vụ:** kiểm tra JSON tiếng Việt do GPT tạo **so với lời giải gốc** và sửa lỗi. Chuẩn so sánh duy nhất là lời giải gốc đã chuẩn hóa. JSON phải thể hiện đúng và đủ lời giải gốc, không hơn, không kém.

## Làm gì

Danh sách câu: `output/claude/gd1_danh_sach.json` (tạo bằng `python scripts/s1_claude_goi.py …`). Mỗi mục có: cờ (`co`), ghi chú bản gốc tự động, **kết quả Python chạy thử trên bản GPT** (`python_tren_ban_gpt` – gợi ý chỗ nên xem, không phải kết luận), đường dẫn các file.

Với mỗi câu:

1. Đọc `output/samples/norm/<id>.json`: `de` (đề, 4 lựa chọn, đáp án), `dau_vao` (lời giải gốc đã chuẩn hóa), `co`.
2. Mở `output/json_vi/checked/<id>.json` (đã chép sẵn từ bản GPT) và **sửa trực tiếp** nếu có lỗi. Giữ đúng schema; file phải là JSON hợp lệ.
3. Ghi `output/json_vi/checked/<id>.ly_do.json` theo mẫu bên dưới – **xong thì xóa khóa `_huong_dan`** (còn khóa này thì Python coi như câu chưa được kiểm tra). Không có gì sửa thì để `"sua": []`.
4. Chỉ sửa file trong `output/json_vi/checked/`. Không sửa bản GPT, dữ liệu gốc hay file khác.
5. Làm xong cả danh sách thì chạy `python scripts/s1_kiem_tra.py …` (cùng phạm vi) và báo kết quả.

## Phạm vi sửa (workflow tổng quát mục 2a, 2a-1)

- **Sửa lỗi của GPT**: `sai_so_ban_goc` (GPT làm lệch bản gốc: đặt sai trường, bỏ sót, tự thêm, viết lại, sai ký hiệu), `chinh_ta` (lỗi GPT tạo ra), `khach_quan` (sai vị trí gạch chân, sai đáp án, sai cấu trúc). Giai đoạn 1 không có loại `chu_quan`.
- **Sửa lỗi có sẵn trong lời giải gốc** (workflow tổng quát mục 2a-1) – loại `sua_ban_goc`, câu sẽ vào **Dạng 2** để CTV xác nhận. Chỉ sửa khi **chắc chắn**, sửa **ít nhất có thể** (đúng chữ/cụm bị sai), và bắt buộc có `nhom`:
  - `chinh_ta`: lỗi chính tả, dấu tiếng Việt (vd "Cố gằng" → "Cố gắng").
  - `cach_doc`: cách đọc bị lẫn số ①②③ / số thứ tự (vd `いちはまべ` → `はまべ`), cách đọc sai rõ ràng (vd `ちょうむ` → `いどむ` cho 挑む).
  - `kien_thuc`: nghĩa / chữ Hán / cách đọc sai kiến thức rõ ràng (vd 人才 "thiên tài" → "nhân tài").
  - `khac`: lỗi rõ ràng khác (ghi rõ trong `ly_do`).
- **Không được**: thêm ý mới, viết lại cho hay hơn, đổi văn phong; sửa đề, lựa chọn (`option_ja`) hay đáp án; sửa khi không chắc chắn → khi đó chỉ ghi `[Bản gốc VI]` vào `ghi_chu_ban_goc`, không sửa.
- Mỗi chỗ `sua_ban_goc` phải có **hai** ghi chép: (1) mục trong `sua` (`loai`, `nhom`, `muc_do`, `ly_do`); (2) một dòng trong `ghi_chu_ban_goc`: `[Đã sửa bản gốc] <chỗ sửa>: '<cũ>' → '<mới>' – <lý do ngắn>`. Thiếu một trong hai thì Python cảnh báo. Python cũng cảnh báo nếu một chỗ sửa đổi quá 50% trường hoặc quá 30 từ.

## Checklist

- [ ] Nội dung đặt đúng trường; không thiếu ý, thừa ý, không bị viết lại so với bản gốc; đã bỏ các nhãn cố định.
- [ ] **Mỗi phân tích nằm đúng lựa chọn của nó.** Câu có cờ `nghi_don_phan_tich`: phần bị dồn đã tách hết về đúng lựa chọn chưa, có tách nhầm không.
- [ ] `options` đủ 4, `option_ja` đúng đề; `correct.index` = `dap_an_so`; lựa chọn đúng: có phân tích trong bản gốc thì phải chép, không có thì `null`.
- [ ] `{ }` bọc đúng từ đang hỏi ở `question.ja`, cách đọc tương ứng ở `question.reading`, phần nghĩa tương ứng ở `question.meaning.vi` – chỉ ở chỗ bản gốc có gạch chân.
- [ ] `word.ja`, `word.reading` đúng như bản gốc; thể từ điển tách đúng (kể cả trường hợp viết dính vào cách đọc).
- [ ] `question.reading` chép từ bản gốc; bản gốc không có dòng cách đọc (dạng ###) thì `null`, không tự ghép từ furigana.
- [ ] Mọi tiếng Nhật trong câu tiếng Việt được bọc `⟪ ⟫`; không bọc chữ tiếng Việt.
- [ ] Furigana `｜…《…》`: chỗ bản gốc có thì JSON có đúng như vậy; chỗ bản gốc không có thì JSON không có.
- [ ] Lựa chọn thiếu phân tích trong bản gốc → `null` + ghi `[Bản gốc VI] Thiếu phân tích lựa chọn X` (nếu chưa có trong ghi chú tự động).
- [ ] Cách đọc bị lẫn số ①②③ (vd `いちはまべ`, `にかいさい`) hoặc sai rõ ràng → sửa, `loai: sua_ban_goc, nhom: cach_doc` + dòng `[Đã sửa bản gốc]`.
- [ ] Lỗi chính tả / kiến thức rõ ràng trong bản gốc → sửa (`sua_ban_goc`, `nhom` tương ứng) + dòng `[Đã sửa bản gốc]`.
- [ ] Câu "không tồn tại" hoặc nghi sai nhưng **không chắc** (vd だまして có thể là 騙して) → không sửa, ghi `[Bản gốc VI]`.

## Mẫu file lý do

```json
{
  "sua": [
    {"duong_dan": "$.options[3].analysis", "loai": "sai_so_ban_goc", "muc_do": "nang",
     "ly_do": "GPT chưa tách phân tích lựa chọn 4 khỏi ô lựa chọn 2"},
    {"duong_dan": "$.options[0].analysis.vi", "loai": "sua_ban_goc", "nhom": "cach_doc", "muc_do": "nang",
     "ly_do": "Bản gốc ghi cách đọc lẫn số thứ tự lựa chọn: いちはまべ → はまべ"}
  ],
  "ghi_chu_ban_goc": ["[Bản gốc VI] Thiếu phân tích lựa chọn 1",
                      "[Đã sửa bản gốc] Lựa chọn 1 – cách đọc: 'いちはまべ' → 'はまべ' – lẫn số ① vào cách đọc"]
}
```

- `duong_dan`: vị trí đã sửa, có thể ghi ở mức trường (vd `$.options[3].analysis`). Python tự so bản GPT với bản đã sửa để lấy nội dung trước/sau; chỗ thay đổi nào không có lý do sẽ bị cảnh báo.
- `loai`: `sai_so_ban_goc` | `chinh_ta` | `khach_quan` (sửa lỗi GPT) | `sua_ban_goc` (sửa lỗi có sẵn trong bản gốc – bắt buộc thêm `nhom`: `chinh_ta` | `cach_doc` | `kien_thuc` | `khac`). `muc_do`: `nghiem_trong` | `nang` | `nhe`.
- `chinh_ta` (loai) = lỗi chính tả **GPT tạo ra**; lỗi chính tả **có sẵn trong bản gốc** là `loai: sua_ban_goc, nhom: chinh_ta`.
- Python kiểm tra "trung thành với bản gốc" trên bản đã trả các chỗ `sua_ban_goc` về giá trị GPT, nên chỗ sửa bản gốc không bị báo lỗi độ phủ / mất tiếng Nhật. Vì vậy **chỉ** gắn `sua_ban_goc` cho đúng chỗ sửa bản gốc, không gộp cả chỗ sửa lỗi GPT vào (ghi `duong_dan` ở mức trường nhỏ nhất, vd `…analysis.vi`).
