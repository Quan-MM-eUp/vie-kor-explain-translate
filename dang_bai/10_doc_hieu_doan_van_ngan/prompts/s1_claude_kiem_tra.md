# Hướng dẫn tác tử KIỂM TRA – Bước 1.2: soát JSON tiếng Việt (dạng 10 – Đọc hiểu đoạn văn ngắn) · v1

> Phiên bản `s1_claude_kiem_tra.10.v1` (2026-10-08): khung **cách chia v2** của dạng 07/08 (sửa định dạng / gắn cờ nội dung) + **quy tắc riêng dạng 10 (mục 3d)** + **chữ Hán chèn câu Việt (mục 3e)** + **gợi ý Python (mục 3f)**.
> Model: **Claude Opus 5.5** trong Cowork. Bản cần soát do **tác tử TẠO (Claude A, ngữ cảnh riêng)** tạo – bạn không tạo lại bản, chỉ soát và sửa.
> Quyết định đã duyệt (08/10/2026): `full_translation` / `summary` chỉ có khi lời giải có (không tự tạo); chữ Hán chèn câu Việt → khôi phục chữ Việt khi nghĩa rõ, không chắc thì gắn cờ; khuôn B không có phân tích → `analysis = null`, **không** gắn cờ.

**Nhiệm vụ:** so JSON với **lời giải gốc** (`output/samples/norm/<id>.json` → `dau_vao`) và **đoạn văn gốc** (`doan_van`): JSON phải thể hiện đúng và đủ lời giải, không hơn, không kém; đồng thời phát hiện chỗ lời giải gốc **sai nội dung** để gắn cờ.

## Làm gì

1. Xem từng câu bằng `python3 ../../pipeline_chung/cong_cu/xem_gd1.py --lo X Y` (đề + **đoạn văn** + lời giải gốc + gợi ý Python + JSON phẳng). Câu dài: truyền từng id.
2. Sửa lỗi của tác tử TẠO / lỗi định dạng (mục 1–2), gắn cờ nội dung (mục 3), xử lý chữ Hán chèn câu Việt (3e) – ghi tất cả vào **một file đặc tả lô** rồi chạy `ghi_ly_do.py` (`SO_TAY_CHAY.md` mục 4.3). Sửa cấu trúc (chuyển trích dẫn giữa `quotes` ↔ `analysis`, bool, mảng) thì sửa thẳng `output/json_vi/checked/<id>.json` bằng python read-modify-write và ghi lý do vào `sua`.
3. Chạy `python3 scripts/s1_kiem_tra.py --tu X --den Y`, xử lý lỗi K.

## Phạm vi sửa – cách chia v2

Ba việc tách bạch: **sửa lỗi tác tử TẠO**, **sửa lỗi ĐỊNH DẠNG của bản gốc**, **gắn cờ NGHI SAI NỘI DUNG**. Không sửa nội dung của bản gốc.

**1. Sửa lỗi tác tử TẠO** – `loai`: `sai_so_ban_goc` (đặt sai trường / sai lựa chọn, bỏ sót, tự thêm, viết lại, thiếu / thừa ⟪ ⟫, mất `{ }` / furigana, trích dẫn đứng riêng dòng để trong `analysis` hoặc trích dẫn trong câu bị tách ra `quotes`, bỏ mất câu dẫn, `quotes[].ja` còn 「」 / `meaning` còn ( ), chép nhãn `Nghĩa:` / `→ SAI.` vào `analysis`, `is_match` sai, tự tạo `summary` / `full_translation`, khuôn B chép dòng 'Câu trả lời đúng là'), `chinh_ta` (lỗi do tác tử TẠO), `khach_quan`.

**2. Sửa lỗi ĐỊNH DẠNG có sẵn trong bản gốc** – `loai: sua_dinh_dang` + `nhom` (`dinh_chu`, `xuong_dong`, `lap_tu`, `chinh_ta`, `dau_cau`, `khoang_trang`, `ky_tu`, `furigana`, `kanji_chen`, `khac`). Dạng 10 hay gặp:

| Trường hợp | Cách xử lý |
|---|---|
| **Chữ Hán chèn câu Việt, nghĩa rõ** (`Nếu (4) ⟪｜休《やす》⟫ việc ⟪｜歩《あゆ》⟫ vào nhà` → `nghỉ việc bước vào nhà`; `cần phải ⟪｜補《おぎな》⟫ sung` → `bổ sung`) | khôi phục chữ Việt – `nhom: kanji_chen` (mục 3e) |
| Ký hiệu furigana hỏng `<|今;いま|` (cờ `ky_hieu_furigana_hong`) khi rõ chữ + cách đọc | `｜今《いま》` – `nhom: furigana`; không rõ → giữ, ghi `[Ghi chú]` |
| Nhãn bị gõ dính / lặp (`trích dẫndẫn:`), dấu câu thừa, lặp chữ | `nhom: lap_tu` / `dau_cau` / `chinh_ta` |
| Dòng dính nhau (`…さようならNghĩa: Tạm biệt.`) | tách đúng trường – `nhom: dinh_chu` |

- Mỗi chỗ sửa định dạng có **hai** ghi chép: mục trong `sua` (`duong_dan` mức trường nhỏ nhất, `loai`, `nhom`, `muc_do`, `ly_do`) **và** một dòng `[Đã sửa định dạng] <chỗ>: '<cũ>' → '<mới>' – <lỗi gì>` (một dòng, xuống dòng ghi `⏎`). Không có thay đổi JSON → dùng `[Ghi chú] …`.
- **Một trường – một loại sửa** (sửa định dạng làm Python trả cả trường về bản tạo khi đo độ phủ / furigana / tiếng Nhật).
- Câu tiếng Nhật (`question.ja`, `option_ja`, `quotes[].ja`) Python so với lời giải (K8 / K-TD): sửa mà không có mục `sua` đúng đường dẫn → LỖI.

**3. Gắn cờ NGHI SAI NỘI DUNG – không sửa** (câu không được dịch, chuyển CTV tiếng Nhật). Khóa `nghi_noi_dung`, mỗi chỗ một mục:

```json
{"vi_tri": "Lựa chọn 1 – trích dẫn", "nhom": "nghia_cau",
 "mo_ta": "(3d-2) 変わっていることも大好きだ dịch 'tôi cũng thích việc nó thay đổi như vậy' – đúng là 'cũng rất thích những thứ khác người'.",
 "de_xuat": "(Người nhóm máu B … nhưng cũng rất thích những điều khác thường.)"}
```

- `vi_tri`: `Câu hỏi – nghĩa`, `Bản dịch đoạn văn`, `Phân tích chung`, `Lựa chọn N – nghĩa`, `Lựa chọn N – trích dẫn`, `Lựa chọn N – phân tích`, `Lựa chọn N – kết luận`, `Đáp án`.
- `nhom`: `trich_dan` · `nghia_cau` · `phan_tich` · `dap_an` · `kanji_chen` · `thieu_noi_dung` · `khac`.

**3c. Quy tắc chung (phản hồi CTV các dạng trước)** – nghĩa tiếng Việt lệch câu Nhật (thêm / bớt ý, mất phủ định / bị động / sai khiến / thì, sai chủ thể) → `nghia_cau`; lời giải nói điều trái sự thật → cờ.

**3d. Quy tắc riêng dạng 10 – Đọc hiểu đoạn văn ngắn**

| # | Lỗi cần bắt | `nhom` |
|---|---|---|
| 1 | **Trích dẫn không có trong đoạn văn** (bịa, chép câu khác, dịch ngược từ tiếng Việt – gợi ý **TD**, cảnh báo **K-TD** < 90 %), hoặc trích nhầm đoạn không liên quan đến lựa chọn. Chỉ khác kana / kanji, khoảng trắng, dấu câu, chú thích 注 → không cờ (ghi `[Ghi chú]` nếu K-TD báo). | `trich_dan` |
| 2 | **Dịch sai nghĩa**: bản dịch câu trích dẫn / nghĩa lựa chọn / nghĩa câu hỏi / bản dịch đoạn văn (khuôn B) lệch câu Nhật (vd 16715 変わっていることも大好きだ). Dịch thoáng nhưng đúng ý → không cờ. | `nghia_cau` |
| 3 | **Phân tích sai**: lý do chọn / loại trái với đoạn văn, sai chủ thể (ai làm gì – vd 15 ① やる là 妻), tự mâu thuẫn, kết luận của phân tích ngược với `→ ĐÚNG/SAI`, hoặc chỉ ghi chung chung không nêu căn cứ ở **lựa chọn đúng**. | `phan_tich` |
| 4 | **Đáp án đáng ngờ**: lời giải kết luận ĐÚNG khác đáp án đề (`ket_luan_lech_dap_an`); khuôn B 'Câu trả lời đúng là' khác đáp án (`b_dap_an_lech` – xem kỹ: chỉ khác số thứ tự '1. ' → không cờ); theo đoạn văn đáp án của đề sai rõ. | `dap_an` |
| 5 | **Chữ Hán chèn câu Việt không đoán chắc được chữ Việt gốc** (3e). | `kanji_chen` |
| 6 | **Thiếu nội dung làm người học không hiểu**: khuôn lẻ chỉ có gợi ý / một câu (vd 53982, 54695); khuôn A không có phân tích cho **lựa chọn đúng**. Khuôn B không có phân tích → **không** cờ (đã duyệt). | `thieu_noi_dung` |

- Bắt buộc so: **trích dẫn ↔ đoạn văn**, **bản dịch trích dẫn ↔ câu Nhật**, **nghĩa lựa chọn ↔ lựa chọn**, **phân tích ↔ đoạn văn + kết luận**, **is_match ↔ đáp án**.
- **Không gắn cờ:** diễn đạt chỉ "chưa hay"; câu dẫn kết thúc bằng `:` sau khi trích dẫn đã chuyển sang `quotes`; phân tích ngắn nhưng đúng; dịch thoáng đúng ý.

**3e. Chữ Hán chèn câu Việt (K-KC)** – lỗi máy dịch cũ thay chữ Việt bằng chữ Hán (~150 câu). Python liệt kê (gợi ý **KC**, cảnh báo **K-KC**); **mẫu nào còn K-KC thì `s1_kiem_tra` báo LỖI cho đến khi xử lý xong**, theo một trong ba cách:
- **Nghĩa rõ → khôi phục chữ Việt** (`sua_dinh_dang`, `nhom: kanji_chen`): thay cả khối `⟪…⟫` bằng chữ Việt đúng ngữ cảnh (`⟪｜補《おぎな》⟫ sung` → `bổ sung`; `có thể ⟪｜実《じつ》｜行《こう》⟫` → `có thể thực hiện`). Một dòng `[Đã sửa định dạng]` có thể gộp nhiều chỗ của **cùng một trường**.
- **Không chắc** chữ Việt gốc → gắn cờ `kanji_chen` (mô tả chỗ, đề xuất nếu có).
- **Không phải lỗi** (tên người / địa danh / thuật ngữ / từ của đề – lựa chọn được lời giải cố ý nhắc bằng tiếng Nhật: `⟪｜田中《たなか》⟫さん`, `từ ⟪｜募集《ぼしゅう》⟫ (tuyển dụng)`, `chủ ngữ là ⟪｜妻《つま》⟫` khi lựa chọn ghi ①:妻) → ghi **một** dòng `[Ghi chú] kanji_chen: <các chỗ> – không phải lỗi (…)`.
- Mẫu vừa sửa vừa còn chỗ "không phải lỗi" → cần cả `[Đã sửa định dạng]` và dòng `[Ghi chú] kanji_chen: …`.

**3f. Gợi ý Python** (trong `xem_gd1.py` / `gd1_danh_sach.json` – chỉ là gợi ý, xác nhận rồi mới gắn cờ; bỏ qua gợi ý nào thì ghi `[Ghi chú] … không gắn cờ vì …`):
- **TD** / **K-TD** – trích dẫn khớp < 90 % đoạn văn gốc.
- **KC** / **K-KC** – chữ Hán chèn câu Việt (3e).
- **RAC** – ký hiệu furigana hỏng `<|…`.
- **K-TD số trích dẫn** – JSON có số trích dẫn khác Python tách: xem lại đúng / sai (đứng riêng dòng → `quotes`, trong câu → `analysis`).

**3b. Sau khi CTV tiếng Nhật trả kết quả** (chỉ khi người dùng đưa phản hồi): CTV xác nhận không sai → xóa cờ; sai → sửa theo CTV (`loai: sua_theo_ctv` + `nhom` + dòng `[Đã sửa theo CTV] …`), xóa cờ, chạy lại `s1_kiem_tra.py`.

**4. Âm Hán Việt** – Python tự dò (câu có âm Hán Việt không được dịch). Python dò sót → cờ nhóm `khac`. (Chữ Hán chèn câu Việt **không** phải âm Hán Việt – xử lý theo 3e.)

## Checklist cấu trúc

- [ ] `question.ja` = câu hỏi tiếng Nhật của lời giải (khuôn B / không có → câu hỏi của đề, bỏ furigana); `question.meaning` = dòng nghĩa.
- [ ] Khuôn A: `full_translation = null`; `summary` chỉ khi có câu chữ trước lựa chọn 1. Khuôn B: `full_translation` đủ các dòng 'Đoạn văn:'; `option_ja` = lựa chọn của đề.
- [ ] Mỗi lựa chọn: `option_ja` = dòng `i.` của lời giải; `meaning` = `Nghĩa:`; `quotes` = trích dẫn đứng riêng dòng (ja không 「」, meaning không ( )); `analysis` = phần còn lại (giữ câu dẫn, `- `, `\n`; không có nhãn / kết luận); `reading = null`.
- [ ] `is_match` chỉ đúng ở `dap_an_so`; `correct.index` = `dap_an_so`; `correct.option_ja` = lựa chọn đó; `correct.full_sentence = null`; `key_info = null`.
- [ ] ⟪ ⟫ quanh mọi tiếng Nhật trong câu Việt (dấu 「」 / nháy ở ngoài); `{ }`, furigana đúng như lời giải.
- [ ] Soát đủ 3c, 3d, 3e, 3f.

## Mẫu lý do (một mẫu trong file đặc tả lô)

```json
"15_1": {
  "thay": [{"duong_dan": "$.options[0].analysis.vi", "cu": "Nếu (4) ⟪｜休《やす》⟫ việc ⟪｜歩《あゆ》⟫ vào nhà", "moi": "Nếu (4) nghỉ việc bước vào nhà"}],
  "sua": [{"duong_dan": "$.options[0].analysis", "loai": "sua_dinh_dang", "nhom": "kanji_chen", "muc_do": "nhe", "ly_do": "chữ Việt 'nghỉ', 'bước' bị máy thay bằng 休, 歩"}],
  "ghi_chu_ban_goc": ["[Đã sửa định dạng] Lựa chọn 1 – phân tích: '｜休《やす》 việc ｜歩《あゆ》 vào nhà' → 'nghỉ việc bước vào nhà' – chữ Việt bị thay bằng chữ Hán",
                      "[Ghi chú] kanji_chen: ｜妻《つま》 / ｜夫《おっと》 (người vợ / người chồng – lời giải cố ý dùng từ của đề) – không phải lỗi"],
  "nghi_noi_dung": []
}
```
- `loai`: `sai_so_ban_goc` | `chinh_ta` | `khach_quan` | `chu_quan` | `sua_dinh_dang` (bắt buộc `nhom` + dòng `[Đã sửa định dạng]`) | `sua_theo_ctv`. `muc_do`: `nghiem_trong` | `nang` | `nhe`.
