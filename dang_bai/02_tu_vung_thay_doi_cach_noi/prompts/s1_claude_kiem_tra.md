# Hướng dẫn Claude – Bước 1.2: kiểm tra JSON tiếng Việt và sửa lỗi (dạng 02 – Thay đổi cách nói) · v3

> Phiên bản `s1_claude_kiem_tra.v3` (2026-10-05): theo cách làm hiện tại của dạng 01 (`../../01_tu_vung_cach_doc_kanji/pipeline_v3/prompts/s1_claude_kiem_tra.md`) – **cách chia v2** (sửa định dạng / gắn cờ nội dung / Hán Việt) + quy tắc nghi sai nội dung từ phản hồi CTV tiếng Hàn + quy tắc riêng dạng 02.
> Model: **Claude Opus 5.5**, chạy trong Claude Cowork (không qua API). Nếu chia việc cho tác tử con thì tác tử con cũng dùng Opus 5.5.

**Nhiệm vụ:** kiểm tra JSON tiếng Việt do GPT tạo **so với lời giải gốc** và sửa lỗi. Chuẩn so sánh là lời giải gốc đã chuẩn hóa. JSON phải thể hiện đúng và đủ lời giải gốc, không hơn, không kém.

## Làm gì

Danh sách câu: `output/claude/gd1_danh_sach.json` (tạo bằng `python scripts/s1_claude_goi.py …`). Mỗi mục có: cờ (`co`), ghi chú bản gốc tự động, **kết quả Python chạy thử trên bản GPT** (`python_tren_ban_gpt` – gợi ý, gồm cả `[Âm Hán Việt] …` và `[Nghi dính câu/định dạng] …`), đường dẫn các file.

Với mỗi câu:

1. Đọc `output/samples/norm/<id>.json`: `de` (đề, 4 lựa chọn, đáp án), `dau_vao` (lời giải gốc đã chuẩn hóa – `{ }` là chỗ in đậm / gạch chân của bản gốc), `co`.
2. Mở `output/json_vi/checked/<id>.json` (đã chép sẵn từ bản GPT) và **sửa trực tiếp** nếu có lỗi. Giữ đúng schema `vocab_synonym.v2`; file phải là JSON hợp lệ.
3. Ghi `output/json_vi/checked/<id>.ly_do.json` theo mẫu bên dưới – **xong thì xóa khóa `_huong_dan`**.
4. Chỉ sửa file trong `output/json_vi/checked/`.
5. Làm xong cả danh sách thì chạy `python scripts/s1_kiem_tra.py …` (cùng phạm vi) và báo kết quả.

## Phạm vi sửa – cách chia v2

Ba việc tách bạch: **sửa lỗi GPT**, **sửa lỗi ĐỊNH DẠNG của bản gốc**, **gắn cờ NGHI SAI NỘI DUNG**. Claude **không sửa nội dung** của bản gốc.

**1. Sửa lỗi của GPT:** `sai_so_ban_goc` (đặt sai trường, bỏ sót, tự thêm, viết lại, sai ký hiệu ⟪ ⟫ / { } / furigana, phân tích nằm nhầm lựa chọn, kết luận bị nhét vào lựa chọn…), `chinh_ta` (lỗi GPT tạo ra), `khach_quan`. Không làm câu đổi dạng.

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
- **Không** dùng `sua_dinh_dang` để thêm `{ }`: dạng 02 chỉ có `{ }` ở chỗ lời giải gốc in đậm / gạch chân (WF dạng 02 mục 1).
- Gợi ý `[Nghi dính câu/định dạng] …` của Python chỉ là gợi ý – xác nhận rồi mới sửa; không sửa "..", "…" (cách viết của bản gốc).

**3. Gắn cờ NGHI SAI NỘI DUNG – không sửa** (câu **không được dịch**, chuyển CTV tiếng Nhật). Ghi vào khóa `nghi_noi_dung`, **mỗi chỗ nghi một mục**:

```json
"nghi_noi_dung": [
  {"vi_tri": "Phân tích lựa chọn 2 (一生の)", "nhom": "dap_an",
   "mo_ta": "(quy tắc 3d-2) Phân tích kết luận '一生の đồng nghĩa với 単なる' – mâu thuẫn đáp án 3",
   "de_xuat": "Từ này không đồng nghĩa với ⟪単なる⟫."}
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

**3d. Quy tắc riêng dạng 02 – Thay đổi cách nói (bắt buộc soát)**

| # | Lỗi cần bắt | `nhom` |
|---|---|---|
| 1 | Đáp án (LỰA CHỌN ĐÚNG / `dap_an_so`) **không thật sự đồng nghĩa** với phần được hỏi trong ngữ cảnh câu đề, hoặc có lựa chọn khác cũng đúng | `dap_an` |
| 2 | Phân tích **mâu thuẫn với đáp án**: lựa chọn sai bị kết luận "đồng nghĩa", lựa chọn đúng bị kết luận "không đồng nghĩa", kết luận ghi nhầm số lựa chọn | `dap_an` |
| 3 | "Nghĩa là "…"" giải **sai nghĩa của lựa chọn tiếng Nhật**, mất bị động / phủ định / kính ngữ / thì, sai từ loại | `nghia_tu` / `thi_the` |
| 4 | "Nghĩa là" của lựa chọn là **câu** nhưng dịch lệch câu tiếng Nhật (thêm / bớt ý, đổi chủ thể) | `nghia_cau` |
| 5 | Danh sách đồng nghĩa trong THAM KHẢO có từ **không đồng nghĩa** (hoặc khác hẳn sắc thái) mà không ghi chú | `nghia_tu` |
| 6 | Phân biệt sắc thái các từ gần nghĩa sai tiêu chí | `nghia_tu` |
| 7 | Cách đọc ở nhãn lựa chọn / trong tham khảo sai (không do lẫn số) | `cach_doc` |
| 8 | Ghi "không tồn tại / không có nghĩa" cho từ / cách nói có thật | `khong_ton_tai` |
| 9 | Phần PHÂN TÍCH thiếu lựa chọn, thiếu phần | `thieu_noi_dung` |

- Bắt buộc so **Nghĩa câu với câu tiếng Nhật**, **"Nghĩa là" của từng lựa chọn với `option_ja`**, và **kết luận đồng nghĩa với đáp án**.
- `[Bản gốc VI]` trong `ghi_chu_ban_goc` không còn dùng cho nghi vấn nội dung (dùng `nghi_noi_dung`).

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
- [ ] `analysis.vi` giữ nguyên câu "Nghĩa là "…"." ở đầu và toàn bộ phần còn lại của dòng.
- [ ] Đoạn trước dòng "1." → `analysis.intro`; đoạn **xuống dòng riêng** sau dòng phân tích cuối → `analysis.conclusion`.
- [ ] `options` đủ 4, `option_ja` đúng đề; `reading` chỉ lấy từ ngoặc cách đọc ở nhãn, không có → `null`.
- [ ] `correct.index` = `dap_an_so`; `correct.option_ja` giống hệt `option_ja` của lựa chọn đó.
- [ ] `reference.vi` chứa **nguyên cả** phần tham khảo (đủ dòng, giữ xuống dòng, đánh số); không có → `null`.
- [ ] `{ }` đúng số cặp, đúng chỗ in đậm / gạch chân của lời giải gốc ở mọi trường; GPT tự thêm / bỏ sót thì sửa (lỗi GPT).
- [ ] Mọi tiếng Nhật trong câu tiếng Việt được bọc `⟪ ⟫`; furigana `｜…《…》` đúng như bản gốc.
- [ ] Soát đủ **3c** và **3d**; gắn cờ `nghi_noi_dung` cho mọi chỗ nghi sai nội dung.

## Mẫu file lý do

```json
{
  "sua": [
    {"duong_dan": "$.analysis.conclusion", "loai": "sai_so_ban_goc", "muc_do": "nang",
     "ly_do": "GPT gộp câu kết luận (dòng riêng trong bản gốc) vào phân tích lựa chọn 4"},
    {"duong_dan": "$.reference.vi", "loai": "sua_dinh_dang", "nhom": "xuong_dong", "muc_do": "nhe",
     "ly_do": "Dính mục '….3. 新しい', thiếu xuống dòng"}
  ],
  "ghi_chu_ban_goc": ["[Đã sửa định dạng] Tham khảo: '….3. 新しい' → '….⏎3. 新しい' – dính mục, thiếu xuống dòng"],
  "nghi_noi_dung": []
}
```

- `loai`: `sai_so_ban_goc` | `chinh_ta` | `khach_quan` (lỗi GPT) | `sua_dinh_dang` (lỗi định dạng bản gốc – bắt buộc `nhom` + dòng `[Đã sửa định dạng]`) | `sua_theo_ctv` (sau CTV). `muc_do`: `nghiem_trong` | `nang` | `nhe`. Không dùng `sua_ban_goc` nữa.
- Không có gì thì để `"sua": []`, `"nghi_noi_dung": []`. Xong thì xóa khóa `_huong_dan`.
