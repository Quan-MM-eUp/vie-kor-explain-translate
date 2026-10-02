# Hướng dẫn Claude – Bước 1.2: kiểm tra JSON tiếng Việt và sửa lỗi (dạng 02 – Thay đổi cách nói)

> Model: **Claude Opus 5.5**, chạy trong Claude Cowork (không qua API). Nếu chia việc cho tác tử con thì tác tử con cũng dùng Opus 5.5.

**Nhiệm vụ:** kiểm tra JSON tiếng Việt do GPT tạo **so với lời giải gốc** và sửa lỗi. Chuẩn so sánh duy nhất là lời giải gốc đã chuẩn hóa. JSON phải thể hiện đúng và đủ lời giải gốc, không hơn, không kém.

## Làm gì

Danh sách câu: `output/claude/gd1_danh_sach.json` (tạo bằng `python scripts/s1_claude_goi.py …`). Mỗi mục có: cờ (`co`), ghi chú bản gốc tự động, **kết quả Python chạy thử trên bản GPT** (`python_tren_ban_gpt` – gợi ý chỗ nên xem, không phải kết luận), đường dẫn các file.

Với mỗi câu:

1. Đọc `output/samples/norm/<id>.json`: `de` (đề, 4 lựa chọn, đáp án), `dau_vao` (lời giải gốc đã chuẩn hóa – `{ }` là chỗ in đậm / gạch chân của bản gốc), `co`.
2. Mở `output/json_vi/checked/<id>.json` (đã chép sẵn từ bản GPT) và **sửa trực tiếp** nếu có lỗi. Giữ đúng schema `vocab_synonym.v2`; file phải là JSON hợp lệ.
3. Ghi `output/json_vi/checked/<id>.ly_do.json` theo mẫu bên dưới – **xong thì xóa khóa `_huong_dan`** (còn khóa này thì Python coi như câu chưa được kiểm tra). Không có gì sửa thì để `"sua": []`.
4. Chỉ sửa file trong `output/json_vi/checked/`. Không sửa bản GPT, dữ liệu gốc hay file khác.
5. Làm xong cả danh sách thì chạy `python scripts/s1_kiem_tra.py …` (cùng phạm vi) và báo kết quả.

## Phạm vi sửa (workflow tổng quát mục 2a, 2a-1)

- **Sửa lỗi của GPT**: `sai_so_ban_goc` (GPT làm lệch bản gốc: đặt sai trường, bỏ sót, tự thêm, viết lại, sai ký hiệu), `chinh_ta` (lỗi GPT tạo ra), `khach_quan` (sai vị trí `{ }`, sai đáp án, sai cấu trúc). Giai đoạn 1 không có loại `chu_quan`.
- **Sửa lỗi có sẵn trong lời giải gốc** (workflow tổng quát mục 2a-1) – loại `sua_ban_goc`, câu sẽ vào **Dạng 2** để CTV xác nhận. Chỉ sửa khi **chắc chắn**, sửa **ít nhất có thể** (đúng chữ/cụm bị sai), và bắt buộc có `nhom`:
  - `chinh_ta`: lỗi chính tả, dấu tiếng Việt (vd "Cố gằng" → "Cố gắng").
  - `cach_doc`: cách đọc bị lẫn số ①②③ / số thứ tự (vd `いちはまべ` → `はまべ`), cách đọc sai rõ ràng (vd `ちょうむ` → `いどむ` cho 挑む).
  - `kien_thuc`: nghĩa / chữ Hán / cách đọc sai kiến thức rõ ràng (vd 人才 "thiên tài" → "nhân tài").
  - `khac`: lỗi rõ ràng khác (ghi rõ trong `ly_do`).
- **Không được**: thêm ý mới, viết lại cho hay hơn, đổi văn phong; sửa đề, lựa chọn (`option_ja`) hay đáp án; sửa khi không chắc chắn → khi đó chỉ ghi `[Bản gốc VI]` vào `ghi_chu_ban_goc`, không sửa.
- Mỗi chỗ `sua_ban_goc` phải có **hai** ghi chép: (1) mục trong `sua` (`loai`, `nhom`, `muc_do`, `ly_do`); (2) một dòng trong `ghi_chu_ban_goc`: `[Đã sửa bản gốc] <chỗ sửa>: '<cũ>' → '<mới>' – <lý do ngắn>`. Thiếu một trong hai thì Python cảnh báo. Python cũng cảnh báo nếu một chỗ sửa đổi quá 50% trường hoặc quá 30 từ.

## Checklist

**Nội dung và vị trí**
- [ ] Nội dung đặt đúng trường; không thiếu ý, thừa ý, không bị viết lại so với bản gốc; đã bỏ các nhãn cố định (kể cả nhãn `i. X (đọc):` ở đầu dòng phân tích).
- [ ] `question.ja` lấy từ dòng câu hỏi của **lời giải** (khi lời giải viết khác đề, vd 2610, vẫn theo lời giải); `question.reading` = `null` khi lời giải không có dòng "Cách đọc:".
- [ ] **Mỗi phân tích nằm đúng lựa chọn của nó** (theo nội dung nhãn). Câu có cờ `dong_pt_dinh_lien` / `thu_tu_pt_lech`: đã tách hết, không tách nhầm.
- [ ] `analysis.vi` giữ nguyên câu "Nghĩa là "…"." ở đầu và toàn bộ phần còn lại của dòng.
- [ ] Đoạn đứng trước dòng "1." → `analysis.intro`; đoạn **xuống dòng riêng** sau dòng phân tích cuối → `analysis.conclusion`; không bị nhét vào lựa chọn 1 hoặc 4. Câu kết luận nằm cùng dòng với lựa chọn 4 thì để trong `analysis` của lựa chọn 4.
- [ ] `options` đủ 4, `option_ja` đúng đề (nhãn có furigana thì theo nhãn); `reading` chỉ lấy từ ngoặc cách đọc ở nhãn, không có → `null`.
- [ ] `correct.index` = `dap_an_so`; `correct.option_ja` giống hệt `option_ja` của lựa chọn đó.
- [ ] `reference.vi` chứa **nguyên cả** phần tham khảo: đủ các dòng, giữ xuống dòng và cách đánh số của bản gốc (kể cả đánh số lặp, mục dính liền); không có phần này → `null`.

**Đánh dấu `{ }`** (chỉ theo chỗ in đậm / gạch chân của lời giải gốc)
- [ ] `{ }` đúng số cặp và đúng vị trí như lời giải gốc đã chuẩn hóa, ở mọi trường (câu đề, phân tích, kết luận, tham khảo); chỗ gốc không có thì JSON không có. GPT tự thêm (vd lấy theo đề, hoặc đoán phần được hỏi) hay bỏ sót thì sửa lại.
- [ ] `{ }` bọc chữ vô nghĩa do lỗi định dạng của bản gốc (vd `{g}`) → không sửa, ghi `[Bản gốc VI]`.

**Ký hiệu**
- [ ] Mọi tiếng Nhật trong câu tiếng Việt được bọc `⟪ ⟫`; không bọc chữ tiếng Việt; dấu ngoặc của bản gốc giữ ở ngoài `⟪ ⟫`.
- [ ] Furigana `｜…《…》`: chỗ bản gốc có thì JSON có đúng như vậy (phần đầu, nhãn lựa chọn, nội dung phân tích, tham khảo); chỗ bản gốc không có thì JSON không có; không bị chuyển thành `reading`.

**Ghi chú bản gốc**
- [ ] Lựa chọn thiếu phân tích, thiếu phần, số trong LỰA CHỌN ĐÚNG khác `dap_an_so` → không sửa (không thêm nội dung, không sửa đáp án), ghi `[Bản gốc VI]` (nếu chưa có trong ghi chú tự động).
- [ ] Lỗi chính tả, cách đọc bị lẫn số ①②③, lỗi kiến thức **rõ ràng** trong phân tích/tham khảo → sửa (`loai: sua_ban_goc` + `nhom`) và ghi dòng `[Đã sửa bản gốc]`; nghi sai nhưng không chắc → chỉ ghi `[Bản gốc VI]`.

## Mẫu file lý do

```json
{
  "sua": [
    {"duong_dan": "$.analysis.conclusion", "loai": "sai_so_ban_goc", "muc_do": "nang",
     "ly_do": "GPT gộp câu 'Do đó, lựa chọn hợp lý nhất là lựa chọn 4.' vào phân tích lựa chọn 4; bản gốc là dòng riêng"},
    {"duong_dan": "$.question.ja", "loai": "khach_quan", "muc_do": "nang",
     "ly_do": "Lời giải gốc không in đậm nhưng GPT tự bọc { } quanh 伝記"},
    {"duong_dan": "$.analysis.options[1].analysis.vi", "loai": "sua_ban_goc", "nhom": "chinh_ta", "muc_do": "nhe",
     "ly_do": "Bản gốc viết sai chính tả 'Cố gằng'"}
  ],
  "ghi_chu_ban_goc": ["[Bản gốc VI] Thiếu phần THÔNG TIN THAM KHẢO",
                      "[Đã sửa bản gốc] Phân tích lựa chọn 2: 'Cố gằng' → 'Cố gắng' – lỗi chính tả"]
}
```

- `duong_dan`: vị trí đã sửa, có thể ghi ở mức trường (vd `$.analysis.options[3].analysis`). Python tự so bản GPT với bản đã sửa để lấy nội dung trước/sau; chỗ thay đổi nào không có lý do sẽ bị cảnh báo.
- `loai`: `sai_so_ban_goc` | `chinh_ta` | `khach_quan` (sửa lỗi GPT) | `sua_ban_goc` (sửa lỗi có sẵn trong bản gốc – bắt buộc thêm `nhom`: `chinh_ta` | `cach_doc` | `kien_thuc` | `khac`). `muc_do`: `nghiem_trong` | `nang` | `nhe`.
- `chinh_ta` (loai) = lỗi chính tả **GPT tạo ra**; lỗi chính tả **có sẵn trong bản gốc** là `loai: sua_ban_goc, nhom: chinh_ta`.
- Python kiểm tra "trung thành với bản gốc" trên bản đã trả các chỗ `sua_ban_goc` về giá trị GPT, nên chỗ sửa bản gốc không bị báo lỗi độ phủ / mất tiếng Nhật. Vì vậy **chỉ** gắn `sua_ban_goc` cho đúng chỗ sửa bản gốc, không gộp cả chỗ sửa lỗi GPT vào (ghi `duong_dan` ở mức trường nhỏ nhất, vd `…analysis.vi`).
