# Hướng dẫn tác tử KIỂM TRA – Bước 1.2: kiểm tra JSON tiếng Việt và sửa lỗi (dạng 17 – Nghe hiểu điểm chính) · v1

> Phiên bản `s1_claude_kiem_tra.17.v1` (2026-10-08). Model: **Claude Opus 5.5** trong Cowork. Cách chia **v2** (như 07–09).
> Bản cần kiểm tra do **tác tử TẠO (Claude A)** làm từ khung JSON của Python – "bản GPT" / "lỗi GPT" trong các công cụ chung hiểu là bản / lỗi của tác tử TẠO. Bạn không tạo lại bản, chỉ soát và sửa.

**Nhiệm vụ:** JSON phải thể hiện **đúng và đủ** lời giải gốc (lời thoại tiếng Nhật + bản dịch Việt + câu hỏi + lựa chọn + Thông tin / lý do), không hơn, không kém; và bản dịch phải **đúng nghĩa tiếng Nhật ở những chỗ quyết định đáp án**.

## Làm gì

- Xem từng câu: `python3 scripts/xem_17.py <id> …` hoặc `--lo X Y` – in đề, lời thoại SONG SONG `[k] người nói | tiếng Nhật → nghĩa Việt` của JSON, các dòng Việt gốc `V…`, phần sau `###`, câu hỏi / lựa chọn / key_info, gợi ý Python (lỗi / cảnh báo trên bản tác tử TẠO).
- Lỗi của tác tử TẠO / định dạng → sửa trực tiếp `output/json_vi/checked/<id>.json` (qua `thay` của file đặc tả lô, hoặc python read-modify-write khi đổi cấu trúc: gộp / tách dòng, đổi null).
- Ghi kết quả bằng **file đặc tả lô** + `ghi_ly_do.py` (SO_TAY_CHAY mục 4.3). Xong chạy `python3 scripts/s1_kiem_tra.py --tu X --den Y`.

## 1. Sửa lỗi của tác tử TẠO (`loai`: `sai_so_ban_goc` | `chinh_ta` | `khach_quan`)

- **Ghép lệch dòng** (nghĩa của lượt này gán cho lượt khác) – soát **từng cặp**, nhất là câu có cờ `lech_so_dong`, `ghep_gop_dong`, `ghep_nghi_nguoi_noi`, cảnh báo `K-NV` (người nói ngược nhãn Việt), `K-DV`. Sửa: đặt lại `meaning` đúng lượt, `duong_dan` = các trường `…lines[k].meaning.vi` bị đổi.
- Sót nhãn người nói Việt đầu `meaning.vi` (`K-NV … còn nhãn`), sót `(i)` trong key_info, `speaker` sai, câu dẫn lọt vào `question.meaning`, nghĩa lựa chọn đặt nhầm, `analysis` sai lựa chọn, thiếu `⟪ ⟫` quanh tiếng Nhật trong câu Việt.
- Dòng Việt bị bỏ sót / thêm chữ không có trong bản gốc → sửa về đúng bản gốc.

## 2. Sửa lỗi ĐỊNH DẠNG có sẵn trong bản gốc – `loai: sua_dinh_dang` + `nhom`

| nhom | Ví dụ dạng 17 |
|---|---|
| `dinh_chu` | dính câu "…nhé.Vậy thì" |
| `lap_tu` / `chinh_ta` | "của của", "Người đang ông" → "Người đàn ông" |
| `dau_cau` / `ky_tu` | `???` → `?`, ký tự lạ đầu câu (`❔`, `??` trước câu hỏi), khoảng trắng toàn góc thừa trong câu Việt |
| `khac` | nhãn người nói tiếng Việt / tiếng Anh dính trong câu (`Man:`), ghi rõ |

- Mỗi chỗ: mục trong `sua` (`duong_dan` mức trường nhỏ nhất, `loai`, `nhom`, `muc_do`, `ly_do`) **và** một dòng `[Đã sửa định dạng] <chỗ>: '<cũ>' → '<mới>' – <lỗi gì>` trong `ghi_chu_ban_goc` (một dòng, xuống dòng ghi `⏎`).
- **Không** sửa chữ tiếng Nhật của lời thoại (`ja`) – K-LT so nguyên văn với lời thoại gốc. Lời thoại gõ sai → gắn cờ (mục 3) hoặc bỏ qua.
- Một trường – một loại sửa (như dạng 07–09).

## 3. Gắn cờ NGHI SAI NỘI DUNG – không sửa (câu không dịch, chuyển CTV tiếng Nhật)

| Gắn cờ khi | `nhom` |
|---|---|
| Dịch sai nghĩa dòng thoại **làm sai / che mất thông tin dẫn tới đáp án** (số, ngày giờ, ai làm gì, phủ định, thứ tự hành động "まず / その前に", điều kiện…) – so với câu tiếng Nhật | `nghia_cau` |
| Dòng "Thông tin" (key_info) **không chứng minh được đáp án**, chọn sai đoạn, hoặc bản "dịch" của Thông tin không phải tiếng Việt / sai hẳn | `thong_tin` |
| Lý do (khuôn B / câu giải thích) sai hoặc trái lời thoại | `phan_tich` |
| Đáp án (`dap_an_so`) đáng ngờ khi đọc lời thoại; lý do ghi số đáp án khác đề (`dap_an_ly_do_lech`) | `dap_an` |
| Lời thoại tiếng Nhật gõ sai / lỗi OCR **làm đổi nghĩa hoặc ảnh hưởng đáp án** (vd `オリープ`, `作う`, `もし訳ございません`) – Q8 | `loi_thoai` |
| Bản dịch thiếu cả đoạn / nhiều lượt thoại; dòng then chốt (có `(i)`) không có bản dịch; câu hỏi / nghĩa lựa chọn bị thiếu khiến người học không hiểu | `thieu_noi_dung` |
| Khác | `khac` |

- Ghi vào `nghi_noi_dung`: `{"vi_tri": "Lời thoại dòng 6" | "Câu hỏi – nghĩa" | "Lựa chọn 3 – nghĩa" | "Thông tin" | "Lý do (lựa chọn đúng)" | "Đáp án", "nhom", "mo_ta": "vì sao nghi", "de_xuat": "cách sửa đề xuất"}` – **không** sửa vào JSON.
- **Không gắn cờ:** dịch thoát / văn nói tự nhiên nhưng đúng ý; xưng hô (cậu/tớ, anh/em, tôi/mình) không thống nhất; tên riêng phiên âm khác nhau (Yamada / Yamađa); bản dịch gộp hai câu thoại ngắn; lỗi gõ nhẹ của lời thoại không đổi nghĩa (Q8); dòng thoại phụ (chào hỏi, "Vâng") dịch sơ sài; lựa chọn sai không có phân tích (dạng 17 vốn không phân tích 4 lựa chọn). Cách diễn đạt chỉ "chưa hay" → không gắn cờ.
- **Phải đọc dòng có `(i)` và dòng in đậm** (gợi ý `[In đậm …]`) để xác nhận đáp án và Thông tin.

## 4. Gợi ý / cảnh báo Python

| Mã | Ý nghĩa → việc làm |
|---|---|
| K-LT (LỖI) | `ja` của lời thoại khác nguyên văn → lỗi tác tử TẠO khi gộp / tách / chép: sửa về đúng lời thoại (chép từ `luot` trong `output/samples/norm/<id>.json`) |
| K-NG (LỖI) | dãy người nói / nhãn sai, còn nhãn trong `ja` → sửa `speaker` |
| K-DV (LỖI / cảnh báo) | bản dịch không phủ ≥ 97% bản gốc theo thứ tự / dòng thoại không có nghĩa → ghép lại; bản gốc thật sự không dịch dòng then chốt → cờ `thieu_noi_dung` |
| K-NV (cảnh báo) | dòng Việt gốc mang nhãn ngược người nói → kiểm tra ghép; bản gốc ghi nhầm nhãn (ghép đúng) → `[Ghi chú] … không sửa` |
| K-LC, K-DA (LỖI) | lựa chọn / `is_match` / `correct` sai → sửa (lỗi tác tử TẠO) |
| K-CH (cảnh báo) | `question.ja` khác `cau_hoi` / không có trong lời thoại; `question.meaning` null → xem lại |
| K-KI (cảnh báo / LỖI) | key_info không có nguyên văn trong lời thoại / số dòng ≠ Thông tin / không chứa dòng `(i)` / chưa có nghĩa / còn `(i)` → xem 3 (`thong_tin`) hoặc sửa |
| Độ phủ / Từ thừa / Mất tiếng Nhật / Furigana | như các dạng trước: sửa về đúng bản gốc |

`[Âm Hán Việt]` (hiếm ở dạng 17) → câu tự động không dịch.

## Checklist

- [ ] Từng cặp lượt Nhật ↔ nghĩa Việt đúng thứ tự, đúng người nói; không sót dòng Việt.
- [ ] `question` đúng câu hỏi (không có câu dẫn); 4 lựa chọn đúng đề + nghĩa; chỉ đáp án `is_match`; `correct` đúng.
- [ ] `key_info` đúng phần Thông tin (khuôn A) / dòng `(i)` (khuôn C) / `[]` (khuôn B); bỏ `(i)`.
- [ ] Lý do khuôn B ở `analysis` của lựa chọn đúng, tiếng Nhật bọc `⟪ ⟫`.
- [ ] Soát nghĩa các dòng then chốt so với tiếng Nhật; gắn cờ theo mục 3.

## Mẫu file lý do (từng câu – do `ghi_ly_do.py` ghi)

```json
{"sua": [{"duong_dan": "$.full_translation[0].lines[4].meaning.vi", "loai": "sai_so_ban_goc", "muc_do": "nang",
          "ly_do": "tác tử TẠO ghép lệch: dòng 4 mang nghĩa của dòng 5"}],
 "ghi_chu_ban_goc": [],
 "nghi_noi_dung": [{"vi_tri": "Lời thoại dòng 7", "nhom": "nghia_cau",
                    "mo_ta": "'２時間までなんです' = 'chỉ được tối đa 2 tiếng', bản Việt dịch 'mượn được 2 tiếng' – mất ý giới hạn, đúng chỗ quyết định đáp án",
                    "de_xuat": "Nếu chỉ có sinh viên thì chỉ được dùng tối đa 2 tiếng thôi."}]}
```
