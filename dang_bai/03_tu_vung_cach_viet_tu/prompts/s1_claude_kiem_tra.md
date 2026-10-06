# Hướng dẫn Claude – Bước 1.2: kiểm tra JSON tiếng Việt và sửa lỗi (dạng 03 – Cách viết từ) · v1

> Phiên bản `s1_claude_kiem_tra.v1` của dạng 03 (2026-10-05): dựng theo cách làm v3 của dạng 01/02 – **cách chia v2** (sửa định dạng / gắn cờ nội dung / Hán Việt) + quy tắc nghi sai nội dung từ phản hồi CTV + **quy tắc riêng dạng 03** (mục 3d) + **gợi ý từ điển SudachiPy** (mục 3e).
> Model: **Claude Opus 5.5**, chạy trong Claude Cowork (không qua API). Nếu chia việc cho tác tử con thì tác tử con cũng dùng Opus 5.5.

**Nhiệm vụ:** kiểm tra JSON tiếng Việt do GPT tạo **so với lời giải gốc** và sửa lỗi. Chuẩn so sánh là lời giải gốc đã chuẩn hóa. JSON phải thể hiện đúng và đủ lời giải gốc, không hơn, không kém.

## Làm gì

Danh sách câu: `output/claude/gd1_danh_sach.json` (tạo bằng `python scripts/s1_claude_goi.py …`). Mỗi mục có: cờ (`co`), ghi chú bản gốc tự động, **kết quả Python chạy thử trên bản GPT** (`python_tren_ban_gpt` – gợi ý, gồm cả `[Âm Hán Việt] …`, `[Nghi dính câu/định dạng] …` và `[Từ điển Sudachi] S1/S2/S3/S3b …`), đường dẫn các file.

Với mỗi câu:

1. Đọc `output/samples/norm/<id>.json`: `de` (đề, 4 lựa chọn, đáp án), `dau_vao` (lời giải gốc đã chuẩn hóa – `{ }` là chỗ in đậm / gạch chân của bản gốc), `co`.
2. Mở `output/json_vi/checked/<id>.json` (đã chép sẵn từ bản GPT) và **sửa trực tiếp** nếu có lỗi. Giữ đúng schema `vocab_writing.v2`; file phải là JSON hợp lệ.
3. Ghi `output/json_vi/checked/<id>.ly_do.json` theo mẫu bên dưới – **xong thì xóa khóa `_huong_dan`**.
4. Chỉ sửa file trong `output/json_vi/checked/`.
5. Làm xong cả danh sách thì chạy `python scripts/s1_kiem_tra.py …` (cùng phạm vi) và báo kết quả.

## Phạm vi sửa – cách chia v2

Ba việc tách bạch: **sửa lỗi GPT**, **sửa lỗi ĐỊNH DẠNG của bản gốc**, **gắn cờ NGHI SAI NỘI DUNG**. Claude **không sửa nội dung** của bản gốc.

**1. Sửa lỗi của GPT:** `sai_so_ban_goc` (đặt sai trường, bỏ sót, tự thêm, viết lại, sai ký hiệu ⟪ ⟫ / { } / furigana, phân tích nằm nhầm lựa chọn, đoạn giải thích bẫy bị nhét vào lựa chọn 4, `exists` / `reading` sai so với dòng phân tích, câu dịch tiếng Việt bị đặt nhầm vào `reading`…), `chinh_ta` (lỗi GPT tạo ra), `khach_quan`. Không làm câu đổi dạng.

**2. Sửa lỗi ĐỊNH DẠNG có sẵn trong bản gốc** – `loai: sua_dinh_dang` + `nhom`:

| nhom | Ví dụ |
|---|---|
| `dinh_chu` | dính câu / dính chữ: "…đồng nghĩa.Tóm lại" → "…đồng nghĩa.⏎Tóm lại" |
| `xuong_dong` | thiếu xuống dòng giữa các mục đánh số trong THAM KHẢO: "…".3. 新しい…" |
| `lap_tu` | "của của", "từ từ" (lặp do gõ) |
| `chinh_ta` | lỗi chính tả / dấu tiếng Việt, mất chữ |
| `dau_cau` | dấu câu thừa / thiếu, khoảng trắng trước dấu phẩy |
| `khoang_trang` | khoảng trắng thừa trong câu / cách đọc / ví dụ tiếng Nhật |
| `ky_tu` | sai ký tự rõ ràng (katakana lẫn hiragana, số ①②③ lẫn trong câu tiếng Nhật) |
| `cach_doc_lan_so` | cách đọc lẫn số thứ tự đọc thành chữ (いち, に, さん…) |
| `khac` | lỗi định dạng khác (ghi rõ trong `ly_do`) |

- Mỗi chỗ sửa định dạng có **hai** ghi chép: mục trong `sua` (`duong_dan` ở mức trường nhỏ nhất, `loai`, `nhom`, `muc_do`, `ly_do`) **và** một dòng trong `ghi_chu_ban_goc`: `[Đã sửa định dạng] <chỗ sửa>: '<cũ>' → '<mới>' – <lỗi gì>`.
- **Không** dùng `sua_dinh_dang` để thêm / dời `{ }` hay dấu câu nằm cạnh `{ }` ở câu đề / cách đọc / nghĩa câu: Python (K5) so `{ }` của 3 dòng này với lời giải gốc – lệch là LỖI. Dấu chấm nằm trong ngoặc (`{quan trọng.}`) để nguyên.
- **Không đánh số lại** THAM KHẢO (K7 so cách đánh số với bản gốc) – bản gốc đánh số nhảy (1, 3, 4) thì để nguyên, ghi `[Bản gốc VI] …` vào `ghi_chu_ban_goc`.
- **Một trường – một loại sửa:** `sua_dinh_dang` trên một trường (vd `$.analysis.options[2].analysis.vi`) khiến Python khi đo độ trung thành trả **cả trường** đó về bản GPT; nếu trường đó còn có sửa lỗi GPT (`khach_quan`, `sai_so_ban_goc`) thì hai việc đè nhau → báo thiếu chữ. Khi trùng, ưu tiên sửa lỗi GPT và chuyển lỗi định dạng thành mô tả trong cờ / `ghi_chu_ban_goc`.
- Ghi chú `[Đã sửa định dạng] …` viết trên **một dòng** (xuống dòng thì ghi `⏎`, không chèn ký tự xuống dòng thật).
- Gợi ý `[Nghi dính câu/định dạng] …` của Python chỉ là gợi ý – xác nhận rồi mới sửa; không sửa "..", "…" (cách viết của bản gốc).

**3. Gắn cờ NGHI SAI NỘI DUNG – không sửa** (câu **không được dịch**, chuyển CTV tiếng Nhật). Ghi vào khóa `nghi_noi_dung`, **mỗi chỗ nghi một mục**:

```json
"nghi_noi_dung": [
  {"vi_tri": "Phân tích lựa chọn 1 (狂人)", "nhom": "cach_doc",
   "mo_ta": "(quy tắc 3d-2, Sudachi S2) Lời giải ghi 'Đọc là けいはん' – 狂人 đọc là きょうじん (khớp kana gạch chân)",
   "de_xuat": "Đọc là ⟪きょうじん⟫, có nghĩa \"người điên, người mất trí\"…"},
  {"vi_tri": "Phân tích lựa chọn 4 (性分)", "nhom": "khong_ton_tai",
   "mo_ta": "(quy tắc 3d-3, Sudachi S3) Ghi 'Không tồn tại' nhưng 性分 (しょうぶん – tính tình, bản tính) là từ có thật",
   "de_xuat": "Đọc là ⟪しょうぶん⟫, có nghĩa là \"tính tình, bản tính\", không hợp ngữ cảnh 'giới tính'."}
]
```

- `vi_tri`: `Câu hỏi`, `Cách đọc câu`, `Nghĩa câu`, `Phân tích lựa chọn N (<lựa chọn>)`, `Phân tích – mở đầu / kết luận`, `Lựa chọn đúng`, `Tham khảo` (nêu mục/dòng nếu dài).
- `nhom`: `nghia_cau` · `thi_the` · `tu_tha_dong_tu` · `nghia_tu` · `khong_ton_tai` · `dong_am` · `chu_han` · `cach_doc` · `dap_an` · `thieu_noi_dung` · `khac`.
- `mo_ta`: vì sao nghi sai (ghi số quy tắc nếu tiện); `de_xuat`: cách sửa đề xuất – **không** sửa vào JSON.
- Không chắc lắm cũng gắn cờ (CTV quyết) – nhưng không gắn cờ cho cách diễn đạt chỉ "chưa hay".

**3c. Quy tắc nghi sai nội dung chung (từ phản hồi CTV tiếng Hàn 02/10/2026 – bảng ví dụ ở prompt dạng 01 mục 3c)**

1. **Nghĩa câu (tiếng Việt)** – dù bản Hàn dịch thẳng từ tiếng Nhật, JSON tiếng Việt vẫn là sản phẩm: lệch câu Nhật là phải gắn cờ `nghia_cau` (phản hồi CTV tiếng Hàn 05/10/2026, dạng 02: 2417 tự thêm 'lúc nào cũng', 2257 '{Còn} học sinh…' thiếu 'vẫn', 2728 'là xe của Nhật Bản' thay vì 'được sản xuất tại Nhật Bản'). Gồm cả: dịch sai cấu trúc ngữ pháp, tự thêm / bớt / thu hẹp ý, hiểu sai từ ngoại lai, lệch sắc thái động từ then chốt, mất thì/thể (〜てきた, 〜あろう, sai khiến, bị động).
2. **Nghĩa của từ / lựa chọn** mất bị động, sai khiến, phủ định, sai từ loại so với dạng xuất hiện; sai nghĩa hẳn.
3. **Tham khảo**: gán nghĩa của cả từ cho một chữ Hán; phân biệt từ sai tiêu chí; khẳng định quá tuyệt đối; nêu âm đọc gây nhầm (nhất là trùng với lựa chọn sai); ví dụ dịch sai.
4. **Câu đề trong lời giải khác đề bài** (bị cụt, sai chữ, thừa chữ) → gắn cờ `thieu_noi_dung` / `khac`, ghi rõ lỗi có cả trong đề (`cau_hoi`) hay không.

**3d. Quy tắc riêng dạng 03 – Cách viết từ (bắt buộc soát)**

| # | Lỗi cần bắt | `nhom` |
|---|---|---|
| 1 | Đáp án (`dap_an_so`) **không phải cách viết đúng** của kana gạch chân trong ngữ cảnh câu đề, hoặc có lựa chọn khác cũng đúng (từ đồng âm có thật, hợp ngữ cảnh) | `dap_an` |
| 2 | **"Đọc là …" sai** – cách đọc của lựa chọn không đúng (vd 狂人 "Đọc là けいはん", đúng là きょうじん); cách đọc trong phần tách chữ Hán / câu ví dụ sai | `cach_doc` |
| 3 | Ghi **"không tồn tại / không phải cách viết đúng"** cho từ **có thật** (vd 性分 しょうぶん, 拾集); ngược lại giải nghĩa như từ có thật cho tổ hợp không có thật | `khong_ton_tai` |
| 4 | **"Cách viết đúng là …"** sai (vd "cách viết và đọc đúng là 妨れる (さまたげる)" – đúng là 妨げる) | `chu_han` |
| 5 | Nghĩa của lựa chọn ("có nghĩa là "…"") **sai** so với chữ Hán / từ tiếng Nhật đó | `nghia_tu` |
| 6 | **Đoạn giải thích bẫy** (`conclusion`) nêu sai âm on'yomi / kun'yomi của chữ Hán, sai số lựa chọn, sai bộ thủ / nét viết, hoặc mâu thuẫn với phân tích 4 dòng | `cach_doc` / `dap_an` / `chu_han` |
| 7 | **Phần tách chữ Hán** trong THAM KHẢO: âm đọc của từng chữ không khớp với từ, nghĩa chữ sai, gán nghĩa cả từ cho một chữ | `chu_han` / `nghia_tu` |
| 8 | **Câu ví dụ** trong THAM KHẢO không dùng đúng từ đáp án, dòng cách đọc không khớp câu ví dụ, dòng nghĩa tiếng Việt dịch sai câu ví dụ | `nghia_cau` / `cach_doc` |
| 9 | **Nghĩa câu đề** dịch sai câu tiếng Nhật (mục 3c-1) | `nghia_cau` |
| 10 | Phần PHÂN TÍCH thiếu lựa chọn, thiếu phần (tham khảo, lựa chọn đúng) | `thieu_noi_dung` |

- Bắt buộc so: **kana gạch chân ↔ cách đọc của đáp án**, **"Đọc là" của từng lựa chọn ↔ chữ Hán**, **"không tồn tại" ↔ từ có thật hay không**, **dòng nghĩa câu ví dụ ↔ câu ví dụ tiếng Nhật**.
- Lựa chọn là chữ Hán đơn (薬, 草, 菜…) có nhiều cách đọc – "Đọc là" chỉ sai khi không phải cách đọc dùng được của chữ đó trong nghĩa đang nói.
- `[Bản gốc VI]` trong `ghi_chu_ban_goc` không còn dùng cho nghi vấn nội dung (dùng `nghi_noi_dung`).

**3e. Gợi ý từ điển SudachiPy – `[Từ điển Sudachi] …`** (Python tra từ điển core; chỉ là GỢI Ý, Claude xác nhận rồi mới gắn cờ):

| Mã | Ý nghĩa | Cách xử lý |
|---|---|---|
| S1 | Kana gạch chân ≠ cách đọc từ điển của đáp án | Soát kỹ đáp án (3d-1); thường là đáp án / đề sai → cờ `dap_an` |
| S2 | "Đọc là X" ≠ cách đọc từ điển | Đúng là đọc sai → cờ `cach_doc` (3d-2); từ có nhiều cách đọc hợp lệ → bỏ qua |
| S3 | Lời giải nói không tồn tại nhưng từ điển có từ này | Từ có thật, dùng được (kể cả ít gặp) → cờ `khong_ton_tai` (3d-3); từ điển chỉ có như tên riêng / từ cực hiếm → có thể bỏ qua nhưng ghi lý do trong `ghi_chu_ban_goc` (`[Ghi chú] …`) |
| S3b | Lời giải giải nghĩa như từ có thật nhưng từ điển không có nguyên từ | Gợi ý yếu: chỉ gắn cờ khi chắc tổ hợp đó không phải từ |

Gợi ý nào đã xem mà **không** gắn cờ thì ghi một dòng `[Ghi chú] Sudachi S2/S3 … không gắn cờ vì …` vào `ghi_chu_ban_goc` để người duyệt thấy đã xét.

**3b. Sau khi CTV tiếng Nhật trả kết quả cho câu bị cờ** (chỉ làm khi bạn đưa phản hồi CTV):
- CTV xác nhận **không sai** → xóa mục cờ tương ứng, không sửa JSON.
- CTV xác nhận **sai** → sửa JSON đúng theo CTV, ghi mục `sua` với `"loai": "sua_theo_ctv"` + `nhom` và dòng `[Đã sửa theo CTV] <chỗ>: '<cũ>' → '<mới>' – <CTV nói gì>`; xóa mục cờ đã xử lý.
- Chạy lại `s1_kiem_tra.py` → câu hết cờ thành GĐ1_XONG, được chốt và dịch.

**4. Âm Hán Việt** – Python tự dò (`[Âm Hán Việt] …`, kể cả kiểu "chữ TRỊ"). Claude không sửa; câu có âm Hán Việt tự động **không được dịch**. Python dò sót thì gắn cờ `nghi_noi_dung` nhóm `khac`, ghi rõ là âm Hán Việt.

**Dạng của câu:** có ít nhất một `sua_dinh_dang` → **Dạng 2**; không → **Dạng 1**. Chỉ câu **không có** `nghi_noi_dung` **và không có** âm Hán Việt mới được chốt và dịch.

## Checklist cấu trúc (giữ từ bản trước)

- [ ] Nội dung đặt đúng trường; không thiếu ý, thừa ý, không bị viết lại; đã bỏ nhãn cố định (kể cả nhãn `i. X (đọc):` ở đầu dòng phân tích).
- [ ] `question.ja` lấy từ dòng câu hỏi của **lời giải**; `question.reading` = `null` khi lời giải không có dòng "Cách đọc:".
- [ ] **Mỗi phân tích nằm đúng lựa chọn của nó** (theo nội dung nhãn). Cờ `dong_pt_dinh_lien` / `thu_tu_pt_lech`: đã tách hết, không tách nhầm.
- [ ] `analysis.vi` giữ **toàn bộ** dòng sau nhãn (kể cả "Đọc là …", "có nghĩa là "…"", "Không tồn tại…").
- [ ] `reading` = kana ngay sau "Đọc là" của chính dòng đó (không có → `null`; không lấy từ furigana / "cách viết đúng là …"); `exists` = `false` đúng ở các lựa chọn bị ghi không tồn tại / không phải cách viết đúng.
- [ ] Đoạn trước dòng "1." → `analysis.intro`; đoạn giải thích bẫy **xuống dòng riêng** sau dòng phân tích cuối → `analysis.conclusion` (đủ mọi dòng).
- [ ] `options` đủ 4, `option_ja` đúng đề (nhãn có furigana thì theo nhãn).
- [ ] `correct.index` = `dap_an_so`; `correct.option_ja` giống hệt `option_ja` của lựa chọn đó.
- [ ] `reference.vi` chứa **nguyên cả** phần tham khảo (đủ dòng, giữ xuống dòng, ký hiệu +/-, đánh số); dòng câu ví dụ tiếng Nhật và dòng cách đọc được bọc `⟪ ⟫`; không có → `null`.
- [ ] `{ }` đúng số cặp, đúng chỗ in đậm / gạch chân của lời giải gốc ở mọi trường; GPT tự thêm / bỏ sót thì sửa (lỗi GPT).
- [ ] Mọi tiếng Nhật trong câu tiếng Việt được bọc `⟪ ⟫`; furigana `｜…《…》` đúng như bản gốc.
- [ ] Soát đủ **3c**, **3d** và mọi gợi ý **3e**; gắn cờ `nghi_noi_dung` cho mọi chỗ nghi sai nội dung.

## Mẫu file lý do

```json
{
  "sua": [
    {"duong_dan": "$.analysis.conclusion", "loai": "sai_so_ban_goc", "muc_do": "nang",
     "ly_do": "GPT gộp đoạn giải thích bẫy (dòng riêng trong bản gốc) vào phân tích lựa chọn 4"},
    {"duong_dan": "$.reference.vi", "loai": "sua_dinh_dang", "nhom": "xuong_dong", "muc_do": "nhe",
     "ly_do": "Dính mục '….3. 新しい', thiếu xuống dòng"}
  ],
  "ghi_chu_ban_goc": ["[Đã sửa định dạng] Tham khảo: '….3. 新しい' → '….⏎3. 新しい' – dính mục, thiếu xuống dòng"],
  "nghi_noi_dung": []
}
```

- `loai`: `sai_so_ban_goc` | `chinh_ta` | `khach_quan` | `chu_quan` (lỗi GPT) | `sua_dinh_dang` (lỗi định dạng bản gốc – bắt buộc `nhom` + dòng `[Đã sửa định dạng]`) | `sua_theo_ctv` (sau CTV). `muc_do`: `nghiem_trong` | `nang` | `nhe`. Không dùng `sua_ban_goc` nữa.
- Không có gì thì để `"sua": []`, `"nghi_noi_dung": []`. Xong thì xóa khóa `_huong_dan`.
