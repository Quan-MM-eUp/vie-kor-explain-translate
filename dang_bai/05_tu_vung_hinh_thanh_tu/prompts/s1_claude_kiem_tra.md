# Hướng dẫn Claude – Bước 1.2: kiểm tra JSON tiếng Việt và sửa lỗi (dạng 05 – Hình thành từ) · v1

> Phiên bản `s1_claude_kiem_tra.v1` của dạng 05 (2026-10-06): dựng từ bản v1 của dạng 04 – **cách chia v2** (sửa định dạng / gắn cờ nội dung) + quy tắc nghi sai nội dung từ phản hồi CTV + **quy tắc riêng dạng 05** (mục 3d) + **gợi ý Sudachi W1/W2/W3/F1** (mục 3e).
> Model: **Claude Opus 5.5**, chạy trong Claude Cowork (không qua API). Nếu chia việc cho tác tử con thì tác tử con cũng dùng Opus 5.5.

**Nhiệm vụ:** kiểm tra JSON tiếng Việt do GPT tạo **so với lời giải gốc** và sửa lỗi. Chuẩn so sánh là lời giải gốc đã chuẩn hóa. JSON phải thể hiện đúng và đủ lời giải gốc, không hơn, không kém.

## Làm gì

Danh sách câu: `output/claude/gd1_danh_sach.json` (tạo bằng `python scripts/s1_claude_goi.py …`). Mỗi mục có: cờ (`co`), ghi chú bản gốc tự động, **kết quả Python chạy thử trên bản GPT** (`python_tren_ban_gpt` – gợi ý, gồm cả `[Âm Hán Việt] …`, `[Nghi dính câu/định dạng] …` và `[Từ điển Sudachi] W1/W2/W3/F1 …`), đường dẫn các file.

Với mỗi câu:

1. Đọc `output/samples/norm/<id>.json`: `de` (đề, 4 lựa chọn, đáp án), `dau_vao` (lời giải gốc đã chuẩn hóa – `{ }` là chỗ in đậm / gạch chân của bản gốc), `co`.
2. Mở `output/json_vi/checked/<id>.json` (đã chép sẵn từ bản GPT) và **sửa trực tiếp** nếu có lỗi. Giữ đúng schema `vocab_word_formation.v2`; file phải là JSON hợp lệ.
3. Ghi `output/json_vi/checked/<id>.ly_do.json` theo mẫu bên dưới – **xong thì xóa khóa `_huong_dan`**.
4. Chỉ sửa file trong `output/json_vi/checked/`.
5. Làm xong cả danh sách thì chạy `python scripts/s1_kiem_tra.py …` (cùng phạm vi) và báo kết quả.

## Phạm vi sửa – cách chia v2

Ba việc tách bạch: **sửa lỗi GPT**, **sửa lỗi ĐỊNH DẠNG của bản gốc**, **gắn cờ NGHI SAI NỘI DUNG**. Claude **không sửa nội dung** của bản gốc.

**1. Sửa lỗi của GPT:** `sai_so_ban_goc` (đặt sai trường, bỏ sót, tự thêm, viết lại, sai ký hiệu ⟪ ⟫ / { } / furigana, phân tích nằm nhầm lựa chọn, `label_paren` / `compound` / `is_valid` sai so với lời giải, tách `compound.meaning` / `analysis` sai, tham khảo thiếu / gộp ví dụ, câu hoàn chỉnh / nghĩa của nó đặt sai chỗ, GPT tự sửa câu hoàn chỉnh cho khớp câu đề, mất / thêm ký hiệu chỗ trống…), `chinh_ta` (lỗi GPT tạo ra), `khach_quan`. Không làm câu đổi dạng.

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
- **Ký hiệu chỗ trống** (`________`, `（　　　）`, `( )`) ở câu đề / cách đọc / nghĩa câu đề phải giữ đúng số lượng như bản gốc (K13) – không đổi kiểu ký hiệu.
- **Câu hoàn chỉnh** (`correct.full_sentence.ja`) phải giống dòng 'Câu hoàn chỉnh:' của bản gốc (K12) – sai thì gắn cờ, không sửa.
- **Một trường – một loại sửa:** `sua_dinh_dang` trên một trường (vd `$.analysis.options[2].analysis.vi`) khiến Python khi đo độ trung thành trả **cả trường** đó về bản GPT; nếu trường đó còn có sửa lỗi GPT (`khach_quan`, `sai_so_ban_goc`) thì hai việc đè nhau → báo thiếu chữ. Khi trùng, ưu tiên sửa lỗi GPT và chuyển lỗi định dạng thành mô tả trong cờ / `ghi_chu_ban_goc`.
- Ghi chú `[Đã sửa định dạng] …` viết trên **một dòng** (xuống dòng thì ghi `⏎`, không chèn ký tự xuống dòng thật).
- Gợi ý `[Nghi dính câu/định dạng] …` của Python chỉ là gợi ý – xác nhận rồi mới sửa; không sửa "..", "…" (cách viết của bản gốc).

**3. Gắn cờ NGHI SAI NỘI DUNG – không sửa** (câu **không được dịch**, chuyển CTV tiếng Nhật). Ghi vào khóa `nghi_noi_dung`, **mỗi chỗ nghi một mục**:

```json
"nghi_noi_dung": [
  {"vi_tri": "Phân tích lựa chọn 2 (あって) – từ ghép", "nhom": "khong_ton_tai",
   "mo_ta": "(quy tắc 3d-1, W1) Lời giải ghi 'はりあって: không có nghĩa trong tiếng Nhật' – 張り合う (ganh đua, cạnh tranh) là từ thông dụng",
   "de_xuat": "はりあって (張り合って): ganh đua, cạnh tranh – có nghĩa nhưng không phù hợp với ngữ cảnh của câu."},
  {"vi_tri": "Tham khảo – 立ち上げる", "nhom": "nghia_tu",
   "mo_ta": "(quy tắc 3d-6) 立ち上げる là 'khởi động, thành lập', không phải 'đứng lên' (立ち上がる)", "de_xuat": "立ち上げる (たちあげる): khởi động, thành lập"}
]
```

- `vi_tri`: `Câu hỏi`, `Cách đọc câu`, `Nghĩa câu`, `Phân tích lựa chọn N (<lựa chọn>) – nghĩa gốc` / `– từ ghép`, `Phân tích – mở đầu / kết luận`, `Lựa chọn đúng`, `Lựa chọn đúng – Câu hoàn chỉnh`, `Lựa chọn đúng – Nghĩa câu hoàn chỉnh`, `Tham khảo – giới thiệu`, `Tham khảo – <từ ví dụ>`.
- `nhom`: `nghia_cau` · `thi_the` · `tu_tha_dong_tu` · `nghia_tu` · `khong_ton_tai` · `dong_am` · `chu_han` · `cach_doc` · `dap_an` · `thieu_noi_dung` · `khac`.
- `mo_ta`: vì sao nghi sai (ghi số quy tắc nếu tiện); `de_xuat`: cách sửa đề xuất – **không** sửa vào JSON.
- Không chắc lắm cũng gắn cờ (CTV quyết) – nhưng không gắn cờ cho cách diễn đạt chỉ "chưa hay".

**3c. Quy tắc nghi sai nội dung chung (từ phản hồi CTV tiếng Hàn 02/10/2026 – bảng ví dụ ở prompt dạng 01 mục 3c)**

1. **Nghĩa câu (tiếng Việt)** – dù bản Hàn dịch thẳng từ tiếng Nhật, JSON tiếng Việt vẫn là sản phẩm: lệch câu Nhật là phải gắn cờ `nghia_cau` (phản hồi CTV tiếng Hàn 05/10/2026, dạng 02: 2417 tự thêm 'lúc nào cũng', 2257 '{Còn} học sinh…' thiếu 'vẫn', 2728 'là xe của Nhật Bản' thay vì 'được sản xuất tại Nhật Bản'). Gồm cả: dịch sai cấu trúc ngữ pháp, tự thêm / bớt / thu hẹp ý, hiểu sai từ ngoại lai, lệch sắc thái động từ then chốt, mất thì/thể (〜てきた, 〜あろう, sai khiến, bị động).
2. **Nghĩa của từ / lựa chọn** mất bị động, sai khiến, phủ định, sai từ loại so với dạng xuất hiện; sai nghĩa hẳn.
3. **Câu hoàn chỉnh / nghĩa câu hoàn chỉnh**: điền sai từ, lệch câu đề, nghĩa dịch sai câu tiếng Nhật (xem 3d-7, 3d-8).
4. **Câu đề trong lời giải khác đề bài** (bị cụt, sai chữ, thừa chữ) → gắn cờ `thieu_noi_dung` / `khac`, ghi rõ lỗi có cả trong đề (`cau_hoi`) hay không.

**3d. Quy tắc riêng dạng 05 – Hình thành từ (bắt buộc soát)**

| # | Lỗi cần bắt | `nhom` |
|---|---|---|
| 1 | Lời giải ghi **"không có nghĩa / không tồn tại"** cho từ ghép **có thật, thông dụng** (vd 張り合う, 追い返す, 手つき, 作曲者) – xem gợi ý **W1**. Đề xuất ghi lại: "<từ> (<đọc>): <nghĩa> – có nghĩa nhưng không phù hợp với ngữ cảnh…" | `khong_ton_tai` |
| 2 | **Nghĩa gốc** (`gloss`) giải sai nghĩa của thành phần trong câu này (vd きって = "tem" – nhầm 切手), sai từ loại / thể | `nghia_tu` / `thi_the` |
| 3 | **Nghĩa từ ghép** sai, hoặc lý do loại / chọn sai (từ ghép thực ra hợp văn cảnh; "có nghĩa" nhưng nghĩa nêu sai) | `nghia_tu` / `dap_an` |
| 4 | Đáp án **không hợp văn cảnh**, có lựa chọn khác cũng ghép được tự nhiên, hoặc phân tích mâu thuẫn với đáp án (đáp án bị ghi "không có nghĩa", lựa chọn sai được kết luận "phù hợp") | `dap_an` |
| 5 | **Cách đọc** trong ngoặc của lựa chọn / từ ghép / từ tham khảo sai (biến âm đúng như ぶかく, ばなれ thì không tính) – xem gợi ý **W2** | `cach_doc` |
| 6 | **Tham khảo**: từ ví dụ không chứa thành phần đáp án, dùng chữ đó với **cách đọc / nghĩa khác** (vd đáp án 深く ふかく mà ví dụ 深海 しんかい; đáp án 際 さい mà ví dụ 窓際 まどぎわ), nghĩa từ ví dụ sai (vd 立ち上げる = "đứng lên") – xem gợi ý **W3** | `khac` / `nghia_tu` / `cach_doc` |
| 7 | **Câu hoàn chỉnh sai**: điền nhầm, sai / thiếu / thừa chữ so với câu đề – xem gợi ý **F1** (đáp án đổi đuôi hợp ngữ pháp như だらけだ → だらけだった thì không tính) | `khac` / `dap_an` |
| 8 | **Nghĩa câu đề / nghĩa câu hoàn chỉnh** lệch câu tiếng Nhật (mục 3c-1); chỗ trống trong Nghĩa câu đề đặt lệch chỗ so với câu Nhật | `nghia_cau` |
| 9 | Câu đề / cách đọc câu trong lời giải **khác đề bài** (sai chữ, thiếu chữ, cách đọc sai) | `cach_doc` / `khac` |
| 10 | Phần PHÂN TÍCH thiếu lựa chọn, thiếu dòng từ ghép, thiếu phần | `thieu_noi_dung` |

- Bắt buộc so: **dòng từ ghép "không có nghĩa" ↔ gợi ý W1 / hiểu biết tiếng Nhật**, **nghĩa gốc ↔ `option_ja`**, **nghĩa từ ghép ↔ `compound.ja`**, **ví dụ tham khảo ↔ thành phần đáp án**, **câu hoàn chỉnh ↔ câu đề + đáp án**, **nghĩa câu đề và nghĩa câu hoàn chỉnh ↔ câu tiếng Nhật**.
- Từ ghép **rất hiếm / cổ / không dùng cho nghĩa này** (từ điển có nhưng người học N2 không gặp) mà lời giải ghi "không có nghĩa" → **không** gắn cờ; ghi `[Ghi chú] W1 … không gắn cờ vì …` vào `ghi_chu_ban_goc`.
- `[Bản gốc VI]` trong `ghi_chu_ban_goc` không còn dùng cho nghi vấn nội dung (dùng `nghi_noi_dung`).

**3e. Gợi ý Sudachi – `[Từ điển Sudachi] …`** (chỉ là gợi ý; Claude xác nhận rồi mới gắn cờ – gợi ý nào bỏ qua thì ghi lý do vào `ghi_chu_ban_goc` dạng `[Ghi chú] W1/W2/W3/F1 … không gắn cờ vì …`):
- **W1** – từ ghép bị ghi "không có nghĩa" nhưng từ điển có (đã đưa dạng chia về thể từ điển). Từ thông dụng → gắn cờ 3d-1; báo nhầm (tách sai, từ điển đoán ghép, từ cổ / hiếm) → không gắn cờ.
- **W2** – cách đọc trong ngoặc khác cách đọc từ điển. Lệch thật → 3d-5; chữ nhiều âm đúng ngữ cảnh (日本 にほん/にっぽん, 市場 いちば/しじょう, 見出す みいだす) → không gắn cờ.
- **W3** – từ tham khảo không chứa thành phần đáp án / dùng chữ đó với cách đọc khác. Làm người học hiểu sai thành phần đáp án → 3d-6; hợp lý (cùng nghĩa, chỉ khác âm do biến âm / âm ngắt) → không gắn cờ.
- **F1** – câu hoàn chỉnh ≠ câu đề + đáp án (so cách đọc). Lệch thật → 3d-7.

**3b. Sau khi CTV tiếng Nhật trả kết quả cho câu bị cờ** (chỉ làm khi bạn đưa phản hồi CTV):
- CTV xác nhận **không sai** → xóa mục cờ tương ứng, không sửa JSON.
- CTV xác nhận **sai** → sửa JSON đúng theo CTV, ghi mục `sua` với `"loai": "sua_theo_ctv"` + `nhom` và dòng `[Đã sửa theo CTV] <chỗ>: '<cũ>' → '<mới>' – <CTV nói gì>`; xóa mục cờ đã xử lý.
- Chạy lại `s1_kiem_tra.py` → câu hết cờ thành GĐ1_XONG, được chốt và dịch.

**4. Âm Hán Việt** (dạng 05: nghĩa gốc như "tập hợp", "tổng" là nghĩa tiếng Việt bình thường, KHÔNG phải âm Hán Việt; chỉ tính khi lời giải ghi âm Hán Việt như cách đọc, vd '集 - TẬP') – Python tự dò (`[Âm Hán Việt] …`, kể cả kiểu "chữ TRỊ"). Claude không sửa; câu có âm Hán Việt tự động **không được dịch**. Python dò sót thì gắn cờ `nghi_noi_dung` nhóm `khac`, ghi rõ là âm Hán Việt.

**Dạng của câu:** có ít nhất một `sua_dinh_dang` → **Dạng 2**; không → **Dạng 1**. Chỉ câu **không có** `nghi_noi_dung` **và không có** âm Hán Việt mới được chốt và dịch.

## Checklist cấu trúc

- [ ] Nội dung đặt đúng trường; không thiếu ý, thừa ý, không bị viết lại; đã bỏ nhãn cố định (số `i.` đầu dòng nhãn, gạch `-` đầu dòng ví dụ).
- [ ] `question.ja` lấy từ dòng câu hỏi của **lời giải**; `question.reading` = `null` khi lời giải không có dòng "Cách đọc:".
- [ ] **Mỗi lựa chọn**: `option_ja` đúng đề; `label_paren` = ngoặc ở dòng nhãn; `gloss` = phần sau `-`; `compound.ja` / `compound.reading` = từ ghép + ngoặc ở dòng thứ 2; `compound.meaning` = phần định nghĩa; `analysis` = phần nhận xét (+ các dòng thêm). Không chữ nào bị mất hoặc nằm nhầm lựa chọn.
- [ ] **`is_valid`** theo lời giải: "không có nghĩa / không tồn tại" → `false` (+ `compound.meaning = null`); có giải nghĩa (kể cả "có nghĩa nhưng không phù hợp") → `true`; không có dòng từ ghép → `compound = null`, `is_valid = null`.
- [ ] `correct.index` = `dap_an_so`; `correct.option_ja` giống hệt `option_ja` của lựa chọn đó; `full_sentence` = dòng "Câu hoàn chỉnh:" (chép nguyên) + "Nghĩa:" đi kèm.
- [ ] `reference`: `intro` = dòng giới thiệu; `terms` đủ từng dòng ví dụ, đúng thứ tự, `ja` / `reading` / `meaning` chép nguyên; không có phần tham khảo → `reference = null`.
- [ ] Ký hiệu chỗ trống ở câu đề / cách đọc / nghĩa câu đề giữ đúng như bản gốc.
- [ ] `{ }` đúng số cặp, đúng chỗ in đậm / gạch chân của lời giải gốc; GPT tự thêm / bỏ sót thì sửa (lỗi GPT).
- [ ] Mọi tiếng Nhật trong câu tiếng Việt được bọc `⟪ ⟫`; furigana `｜…《…》` đúng như bản gốc.
- [ ] Soát đủ **3c**, **3d** và mọi gợi ý **3e**; gắn cờ `nghi_noi_dung` cho mọi chỗ nghi sai nội dung.

## Mẫu file lý do

```json
{
  "sua": [
    {"duong_dan": "$.analysis.options[3].is_valid", "loai": "sai_so_ban_goc", "muc_do": "nang",
     "ly_do": "lời giải nói 持ち込んで có nghĩa ('mang vào') nhưng không phù hợp – is_valid phải true, GPT để false"},
    {"duong_dan": "$.reference.terms[3].meaning.vi", "loai": "sua_dinh_dang", "nhom": "chinh_ta", "muc_do": "nhe",
     "ly_do": "lỗi chính tả 'thàng phố' → 'thành phố'"}
  ],
  "ghi_chu_ban_goc": ["[Đã sửa định dạng] Tham khảo – 都会離れ: 'thàng phố' → 'thành phố' – lỗi chính tả"],
  "nghi_noi_dung": []
}
```

- `loai`: `sai_so_ban_goc` | `chinh_ta` | `khach_quan` | `chu_quan` (lỗi GPT) | `sua_dinh_dang` (lỗi định dạng bản gốc – bắt buộc `nhom` + dòng `[Đã sửa định dạng]`) | `sua_theo_ctv` (sau CTV). `muc_do`: `nghiem_trong` | `nang` | `nhe`. Không dùng `sua_ban_goc` nữa.
- Không có gì thì để `"sua": []`, `"nghi_noi_dung": []`. Xong thì xóa khóa `_huong_dan`.
