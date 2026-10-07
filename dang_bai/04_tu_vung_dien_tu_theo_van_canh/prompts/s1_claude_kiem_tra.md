# Hướng dẫn Claude – Bước 1.2: kiểm tra JSON tiếng Việt và sửa lỗi (dạng 04 – Điền từ theo văn cảnh) · v1

> Phiên bản `s1_claude_kiem_tra.v1` của dạng 04 (2026-10-06): dựng theo cách làm v3 của dạng 02/03 – **cách chia v2** (sửa định dạng / gắn cờ nội dung) + quy tắc nghi sai nội dung từ phản hồi CTV + **quy tắc riêng dạng 04** (mục 3d) + **gợi ý F1** (mục 3e: câu hoàn chỉnh ≠ câu đề + đáp án).
> Model: **Claude Opus 5.5**, chạy trong Claude Cowork (không qua API). Nếu chia việc cho tác tử con thì tác tử con cũng dùng Opus 5.5.

**Nhiệm vụ:** kiểm tra JSON tiếng Việt do GPT tạo **so với lời giải gốc** và sửa lỗi. Chuẩn so sánh là lời giải gốc đã chuẩn hóa. JSON phải thể hiện đúng và đủ lời giải gốc, không hơn, không kém.

## Làm gì

Danh sách câu: `output/claude/gd1_danh_sach.json` (tạo bằng `python scripts/s1_claude_goi.py …`). Mỗi mục có: cờ (`co`), ghi chú bản gốc tự động, **kết quả Python chạy thử trên bản GPT** (`python_tren_ban_gpt` – gợi ý, gồm cả `[Âm Hán Việt] …`, `[Nghi dính câu/định dạng] …` và `[Từ điển Sudachi] F1 …`), đường dẫn các file.

Với mỗi câu:

1. Đọc `output/samples/norm/<id>.json`: `de` (đề, 4 lựa chọn, đáp án), `dau_vao` (lời giải gốc đã chuẩn hóa – `{ }` là chỗ in đậm / gạch chân của bản gốc), `co`.
2. Mở `output/json_vi/checked/<id>.json` (đã chép sẵn từ bản GPT) và **sửa trực tiếp** nếu có lỗi. Giữ đúng schema `vocab_context_fill.v2`; file phải là JSON hợp lệ.
3. Ghi `output/json_vi/checked/<id>.ly_do.json` theo mẫu bên dưới – **xong thì xóa khóa `_huong_dan`**.
4. Chỉ sửa file trong `output/json_vi/checked/`.
5. Làm xong cả danh sách thì chạy `python scripts/s1_kiem_tra.py …` (cùng phạm vi) và báo kết quả.

## Phạm vi sửa – cách chia v2

Ba việc tách bạch: **sửa lỗi GPT**, **sửa lỗi ĐỊNH DẠNG của bản gốc**, **gắn cờ NGHI SAI NỘI DUNG**. Claude **không sửa nội dung** của bản gốc.

**1. Sửa lỗi của GPT:** `sai_so_ban_goc` (đặt sai trường, bỏ sót, tự thêm, viết lại, sai ký hiệu ⟪ ⟫ / { } / furigana, phân tích nằm nhầm lựa chọn, `label_paren` sai so với ngoặc ở nhãn, câu hoàn chỉnh / nghĩa của nó đặt sai chỗ, GPT tự sửa câu hoàn chỉnh cho khớp câu đề, mất / thêm ký hiệu chỗ trống…), `chinh_ta` (lỗi GPT tạo ra), `khach_quan`. Không làm câu đổi dạng.

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
  {"vi_tri": "Lựa chọn đúng – Câu hoàn chỉnh", "nhom": "dap_an",
   "mo_ta": "(quy tắc 3d-5, F1) Câu hoàn chỉnh điền いそがしい, nhưng đáp án là くだらない",
   "de_xuat": "くだらない理由で、彼は会議を欠席した。"},
  {"vi_tri": "Phân tích lựa chọn 4 (つけて)", "nhom": "nghia_tu",
   "mo_ta": "(quy tắc 3d-3) …", "de_xuat": "…"}
]
```

- `vi_tri`: `Câu hỏi`, `Cách đọc câu`, `Nghĩa câu`, `Phân tích lựa chọn N (<lựa chọn>)`, `Phân tích – mở đầu / kết luận`, `Lựa chọn đúng`, `Lựa chọn đúng – Câu hoàn chỉnh`, `Lựa chọn đúng – Nghĩa câu hoàn chỉnh`.
- `nhom`: `nghia_cau` · `thi_the` · `tu_tha_dong_tu` · `nghia_tu` · `khong_ton_tai` · `dong_am` · `chu_han` · `cach_doc` · `dap_an` · `thieu_noi_dung` · `khac`.
- `mo_ta`: vì sao nghi sai (ghi số quy tắc nếu tiện); `de_xuat`: cách sửa đề xuất – **không** sửa vào JSON.
- Không chắc lắm cũng gắn cờ (CTV quyết) – nhưng không gắn cờ cho cách diễn đạt chỉ "chưa hay".

**3c. Quy tắc nghi sai nội dung chung (từ phản hồi CTV tiếng Hàn 02/10/2026 – bảng ví dụ ở prompt dạng 01 mục 3c)**

1. **Nghĩa câu (tiếng Việt)** – dù bản Hàn dịch thẳng từ tiếng Nhật, JSON tiếng Việt vẫn là sản phẩm: lệch câu Nhật là phải gắn cờ `nghia_cau` (phản hồi CTV tiếng Hàn 05/10/2026, dạng 02: 2417 tự thêm 'lúc nào cũng', 2257 '{Còn} học sinh…' thiếu 'vẫn', 2728 'là xe của Nhật Bản' thay vì 'được sản xuất tại Nhật Bản'). Gồm cả: dịch sai cấu trúc ngữ pháp, tự thêm / bớt / thu hẹp ý, hiểu sai từ ngoại lai, lệch sắc thái động từ then chốt, mất thì/thể (〜てきた, 〜あろう, sai khiến, bị động).
2. **Nghĩa của từ / lựa chọn** mất bị động, sai khiến, phủ định, sai từ loại so với dạng xuất hiện; sai nghĩa hẳn.
3. **Câu hoàn chỉnh / nghĩa câu hoàn chỉnh**: điền sai từ, lệch câu đề, nghĩa dịch sai câu tiếng Nhật (xem 3d-5, 3d-6).
4. **Câu đề trong lời giải khác đề bài** (bị cụt, sai chữ, thừa chữ) → gắn cờ `thieu_noi_dung` / `khac`, ghi rõ lỗi có cả trong đề (`cau_hoi`) hay không.

**3d. Quy tắc riêng dạng 04 – Điền từ theo văn cảnh (bắt buộc soát)**

| # | Lỗi cần bắt | `nhom` |
|---|---|---|
| 1 | Đáp án (`dap_an_so`) **không hợp văn cảnh** câu đề, hoặc có lựa chọn khác cũng điền được tự nhiên | `dap_an` |
| 2 | Phân tích **mâu thuẫn với đáp án** (lựa chọn sai bị kết luận "phù hợp", lựa chọn đúng bị kết luận "không phù hợp") | `dap_an` |
| 3 | "Nghĩa là "…"" giải **sai nghĩa của lựa chọn tiếng Nhật**, sai từ loại / thể (bị động, phủ định, thì) | `nghia_tu` / `thi_the` |
| 4 | Lý do loại lựa chọn sai **không đúng**: nói "không kết hợp được" với cụm thực ra tự nhiên, sai sắc thái / cách dùng, ví dụ cụm tiếng Việt dịch lệch | `nghia_tu` / `khac` |
| 5 | **Câu hoàn chỉnh sai**: điền nhầm từ khác đáp án, sai / thiếu / thừa chữ so với câu đề, lỗi gõ (ののイメージ, をを), furigana lẫn vào câu, bị cụt – xem gợi ý **F1** | `khac` / `dap_an` |
| 6 | **Nghĩa câu hoàn chỉnh** dịch lệch câu tiếng Nhật (thêm / bớt ý, sai chủ thể, sai thì) | `nghia_cau` |
| 7 | **Nghĩa câu đề** (có chỗ trống) dịch lệch câu tiếng Nhật – vẫn phải gắn cờ dù bản Hàn dịch thẳng từ tiếng Nhật (mục 3c-1) | `nghia_cau` |
| 8 | Ngoặc ở nhãn (`label_paren`) ghi **sai chữ Hán / sai cách đọc** của lựa chọn | `chu_han` / `cach_doc` |
| 9 | Câu đề / cách đọc câu trong lời giải **khác đề bài** (sai chữ, thiếu chữ, cách đọc sai) | `cach_doc` / `khac` |
| 10 | Phần PHÂN TÍCH thiếu lựa chọn, thiếu phần | `thieu_noi_dung` |

- Bắt buộc so: **"Nghĩa là" của từng lựa chọn ↔ `option_ja`**, **câu hoàn chỉnh ↔ câu đề + đáp án**, **nghĩa câu đề và nghĩa câu hoàn chỉnh ↔ câu tiếng Nhật**.
- `[Bản gốc VI]` trong `ghi_chu_ban_goc` không còn dùng cho nghi vấn nội dung (dùng `nghi_noi_dung`).

**3e. Gợi ý F1 – `[Từ điển Sudachi] F1: …`**: Python ghép đáp án vào chỗ trống của câu đề rồi so **cách đọc** với dòng "Câu hoàn chỉnh" (bỏ qua khác biệt kana / kanji, furigana, khoảng trắng). Lệch → soát quy tắc 3d-5: lệch thật (điền sai từ, lỗi gõ, cụt, thừa câu) → gắn cờ; lệch do từ điển đọc khác (chữ nhiều âm, số đếm) → không gắn cờ, ghi `[Ghi chú] F1 … không gắn cờ vì …` vào `ghi_chu_ban_goc`.

**3b. Sau khi CTV tiếng Nhật trả kết quả cho câu bị cờ** (chỉ làm khi bạn đưa phản hồi CTV):
- CTV xác nhận **không sai** → xóa mục cờ tương ứng, không sửa JSON.
- CTV xác nhận **sai** → sửa JSON đúng theo CTV, ghi mục `sua` với `"loai": "sua_theo_ctv"` + `nhom` và dòng `[Đã sửa theo CTV] <chỗ>: '<cũ>' → '<mới>' – <CTV nói gì>`; xóa mục cờ đã xử lý.
- Chạy lại `s1_kiem_tra.py` → câu hết cờ thành GĐ1_XONG, được chốt và dịch.

**4. Âm Hán Việt** (dạng 04 gần như không có) – Python tự dò (`[Âm Hán Việt] …`, kể cả kiểu "chữ TRỊ"). Claude không sửa; câu có âm Hán Việt tự động **không được dịch**. Python dò sót thì gắn cờ `nghi_noi_dung` nhóm `khac`, ghi rõ là âm Hán Việt.

**Dạng của câu:** có ít nhất một `sua_dinh_dang` → **Dạng 2**; không → **Dạng 1**. Chỉ câu **không có** `nghi_noi_dung` **và không có** âm Hán Việt mới được chốt và dịch.

## Checklist cấu trúc (giữ từ bản trước)

- [ ] Nội dung đặt đúng trường; không thiếu ý, thừa ý, không bị viết lại; đã bỏ nhãn cố định (kể cả nhãn `i. X (đọc):` ở đầu dòng phân tích).
- [ ] `question.ja` lấy từ dòng câu hỏi của **lời giải**; `question.reading` = `null` khi lời giải không có dòng "Cách đọc:".
- [ ] **Mỗi phân tích nằm đúng lựa chọn của nó** (theo nội dung nhãn). Cờ `dong_pt_dinh_lien` / `thu_tu_pt_lech`: đã tách hết, không tách nhầm.
- [ ] `analysis.vi` giữ **toàn bộ** dòng sau nhãn, kể cả câu "Nghĩa là "…"." ở đầu.
- [ ] `label_paren` = nội dung trong ngoặc ở nhãn (chữ Hán hoặc cách đọc), không có → `null`.
- [ ] Đoạn trước dòng "1." → `analysis.intro`; đoạn **xuống dòng riêng** sau dòng phân tích cuối → `analysis.conclusion`.
- [ ] `options` đủ 4, `option_ja` đúng đề (nhãn có furigana thì theo nhãn).
- [ ] `correct.index` = `dap_an_so`; `correct.option_ja` giống hệt `option_ja` của lựa chọn đó.
- [ ] `correct.full_sentence` = dòng "Câu hoàn chỉnh:" (chép nguyên) + dòng "Nghĩa:" đi kèm; không có → `null`. `reference` luôn `null`.
- [ ] Ký hiệu chỗ trống ở câu đề / cách đọc / nghĩa câu đề giữ đúng như bản gốc.
- [ ] `{ }` đúng số cặp, đúng chỗ in đậm / gạch chân của lời giải gốc ở mọi trường; GPT tự thêm / bỏ sót thì sửa (lỗi GPT).
- [ ] Mọi tiếng Nhật trong câu tiếng Việt được bọc `⟪ ⟫`; furigana `｜…《…》` đúng như bản gốc.
- [ ] Soát đủ **3c**, **3d** và mọi gợi ý **3e**; gắn cờ `nghi_noi_dung` cho mọi chỗ nghi sai nội dung.

## Mẫu file lý do

```json
{
  "sua": [
    {"duong_dan": "$.correct.full_sentence.meaning", "loai": "sai_so_ban_goc", "muc_do": "nang",
     "ly_do": "GPT đưa dòng 'Nghĩa:' của câu hoàn chỉnh vào question.meaning"},
    {"duong_dan": "$.analysis.options[2].analysis.vi", "loai": "sua_dinh_dang", "nhom": "chinh_ta", "muc_do": "nhe",
     "ly_do": "lỗi chính tả 'tầm lòng' → 'tấm lòng'"}
  ],
  "ghi_chu_ban_goc": ["[Đã sửa định dạng] Phân tích lựa chọn 3: 'tầm lòng' → 'tấm lòng' – lỗi chính tả"],
  "nghi_noi_dung": []
}
```

- `loai`: `sai_so_ban_goc` | `chinh_ta` | `khach_quan` | `chu_quan` (lỗi GPT) | `sua_dinh_dang` (lỗi định dạng bản gốc – bắt buộc `nhom` + dòng `[Đã sửa định dạng]`) | `sua_theo_ctv` (sau CTV). `muc_do`: `nghiem_trong` | `nang` | `nhe`. Không dùng `sua_ban_goc` nữa.
- Không có gì thì để `"sua": []`, `"nghi_noi_dung": []`. Xong thì xóa khóa `_huong_dan`.
