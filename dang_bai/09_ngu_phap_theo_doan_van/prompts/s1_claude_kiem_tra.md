# Hướng dẫn tác tử KIỂM TRA – Bước 1.2: kiểm tra JSON tiếng Việt và sửa lỗi (dạng 09 – Ngữ pháp theo đoạn văn) · v1

> Phiên bản `s1_claude_kiem_tra.09.v1` (2026-10-08): **bằng nguyên prompt dạng 07** (cùng khuôn lời giải, cách chia v2, quy tắc 3d-1…8) + **quy tắc riêng dạng 09 (3d-9, 3d-10)** + gợi ý Python **ĐV** (câu đề ↔ đoạn văn). Mọi ví dụ số mẫu bên dưới (5531, 4040…) là của dạng 07 – chỉ để minh họa.
> Model: **Claude Opus 5.5**, chạy trong Claude Cowork (không qua API). Nếu chia việc cho tác tử con thì tác tử con cũng dùng Opus 5.5.

> **Dạng 09:** bản cần kiểm tra do **tác tử TẠO (Claude A, ngữ cảnh riêng)** tạo thay GPT – mọi chỗ "bản GPT" / "lỗi GPT" dưới đây hiểu là bản / lỗi của tác tử TẠO; cách kiểm tra không đổi. Bạn (tác tử KIỂM TRA) không tạo lại bản, chỉ soát và sửa như với bản GPT.

**Nhiệm vụ:** kiểm tra JSON tiếng Việt do GPT tạo **so với lời giải gốc** và sửa lỗi. Chuẩn so sánh là lời giải gốc đã chuẩn hóa. JSON phải thể hiện đúng và đủ lời giải gốc, không hơn, không kém.

> **Quy tắc THAM KHẢO (leader duyệt 2026-10-07 – áp dụng mọi dạng):** phần THÔNG TIN THAM KHẢO **không** kiểm tra, **không** sửa định dạng, **không** gắn cờ nội dung, **không** dịch, **không** đưa CTV duyệt. Python đã bỏ phần này khỏi lời giải (`dau_vao`) và tự chép nguyên văn vào trường `reference_raw` – Claude **không sửa** trường này (Python báo `K-TK` nếu bị sửa). Các quy tắc / ví dụ cũ về Tham khảo đã bỏ.

## Làm gì

Xem từng câu: `python3 ../../pipeline_chung/cong_cu/xem_gd1.py <id>` (đề + lời giải gốc + gợi ý Python + JSON). Danh sách câu: `output/claude/gd1_danh_sach_<tu>_<den>.json` (chạy song song – tên in ở dòng `[Song song] …`; trước đó `gd1_danh_sach.json`) (tạo bằng `python3 scripts/s1_claude_goi.py …`). Mỗi mục có: cờ (`co`), ghi chú bản gốc tự động, **kết quả Python chạy thử trên bản GPT** (`python_tren_ban_gpt` – gợi ý, gồm cả `[Âm Hán Việt] …`, `[Nghi dính câu/định dạng] …` và `[Từ điển Sudachi] R1/A …`), đường dẫn các file.

Với mỗi câu:

1. Đọc `output/samples/norm/<id>.json`: `de` (đề, 4 lựa chọn, đáp án), `dau_vao` (lời giải gốc đã chuẩn hóa – `{ }` là chỗ in đậm / gạch chân của bản gốc), `co`.
2. Mở `output/json_vi/checked/<id>.json` (đã chép sẵn từ bản GPT) và **sửa trực tiếp** nếu có lỗi. Giữ đúng schema `grammar_choice.v2`; file phải là JSON hợp lệ.
3. Ghi `output/json_vi/checked/<id>.ly_do.json` theo mẫu bên dưới – **xong thì xóa khóa `_huong_dan`**.
4. Chỉ sửa file trong `output/json_vi/checked/`.
5. Làm xong cả danh sách thì chạy `python3 scripts/s1_kiem_tra.py …` (cùng phạm vi) và báo kết quả.

## Phạm vi sửa – cách chia v2

Ba việc tách bạch: **sửa lỗi GPT**, **sửa lỗi ĐỊNH DẠNG của bản gốc**, **gắn cờ NGHI SAI NỘI DUNG**. Claude **không sửa nội dung** của bản gốc.

**1. Sửa lỗi của GPT:** `sai_so_ban_goc` (đặt sai trường, bỏ sót, tự thêm, viết lại, sai ký hiệu ⟪ ⟫ / { } / furigana, nhận xét nằm nhầm lựa chọn, `meaning` (Ý nghĩa mẫu ngữ pháp) lẫn với `applied.meaning` (nghĩa câu), chữ đánh giá 'Đúng/Sai/Phù hợp…' còn sót trong note, `grammar_ok` / `semantic_ok` sai so với lời giải, GPT tự sửa câu áp dụng / câu hoàn chỉnh cho khớp đề, `correct.note` bỏ sót…), `chinh_ta` (lỗi GPT tạo ra), `khach_quan`. Không làm câu đổi dạng.

**2. Sửa lỗi ĐỊNH DẠNG có sẵn trong bản gốc** – `loai: sua_dinh_dang` + `nhom`:

| nhom | Ví dụ |
|---|---|
| `dinh_chu` | dính câu / dính chữ: "…đồng nghĩa.Tóm lại" → "…đồng nghĩa.⏎Tóm lại" |
| `xuong_dong` | thiếu xuống dòng: "…phù hợp hơn.3. 小麦粉…", "Sửa lại: …浴びています。Cách đọc: …" |
| `lap_tu` | "của của", "từ từ" (lặp do gõ) |
| `chinh_ta` | lỗi chính tả / dấu tiếng Việt, mất chữ |
| `dau_cau` | dấu câu thừa / thiếu, khoảng trắng trước dấu phẩy |
| `khoang_trang` | khoảng trắng thừa trong câu / cách đọc / ví dụ tiếng Nhật |
| `ky_tu` | sai ký tự rõ ràng (katakana lẫn hiragana, số ①②③ lẫn trong câu tiếng Nhật); **số gõ nhầm ở LỰA CHỌN ĐÚNG** (vd '5.' – nội dung đúng là đáp án; JSON đã theo `dap_an_so`, chỉ cần ghi chú) |
| `lap_tu` (câu Nhật) | **câu 'Áp dụng' / 'Câu hoàn chỉnh' lệch 1–2 ký tự do gõ** (感じ**じ**られる → 感じられる; số '8' dính cuối câu) – cờ tự động `ap_dung_lech_nhe` |
| `cach_doc_lan_so` | cách đọc lẫn số thứ tự đọc thành chữ (いち, に, さん…) |
| `furigana` | furigana lệch phạm vi rõ ràng; furigana gắn lên chữ Việt (`｜Câu《く》`, `｜文《ぶん》 ｜章《しょう》…: ` nhãn tiếng Nhật thừa) → bỏ |
| `khac` | lỗi định dạng khác (ghi rõ trong `ly_do`) |

- Mỗi chỗ sửa định dạng có **hai** ghi chép: mục trong `sua` (`duong_dan` ở mức trường nhỏ nhất, `loai`, `nhom`, `muc_do`, `ly_do`) **và** một dòng trong `ghi_chu_ban_goc`: `[Đã sửa định dạng] <chỗ sửa>: '<cũ>' → '<mới>' – <lỗi gì>`.
- **Không** dùng `sua_dinh_dang` để thêm / dời `{ }` ở câu áp dụng: Python (K5) so `{ }` với lời giải – lệch là LỖI.
- **Câu tiếng Nhật** (`question.ja`, `option_ja`, `applied.ja`, `full_sentence.ja`, `reading`) Python so với lời giải (K2, K3, K6, K8). Sửa định dạng ở các trường này (lặp ký tự do gõ…) được phép khi có mục `sua_dinh_dang` đúng đường dẫn + `[Đã sửa định dạng]`: Python so trung thành (K8/K9) trên bản đã hoàn tác chỗ đó; sửa mà không ghi mục `sua` thì K8 báo LỖI. Lời giải viết câu **khác đề về chữ / nghĩa** → **gắn cờ** `cau_khac_de`, không sửa.
- **Một trường – một loại sửa:** `sua_dinh_dang` trên một trường (vd `$.analysis.options[2].semantic_note.vi`) khiến Python khi đo độ trung thành trả **cả trường** đó về bản GPT; nếu trường đó còn có sửa lỗi GPT (`khach_quan`, `sai_so_ban_goc`) thì hai việc đè nhau → báo thiếu chữ. Khi trùng, ưu tiên sửa lỗi GPT và chuyển lỗi định dạng thành mô tả trong cờ / `ghi_chu_ban_goc`.
- Ghi chú `[Đã sửa định dạng] …` viết trên **một dòng** (xuống dòng thì ghi `⏎`, không chèn ký tự xuống dòng thật).
- Gợi ý `[Nghi dính câu/định dạng] …` của Python chỉ là gợi ý – xác nhận rồi mới sửa; không sửa "..", "…" (cách viết của bản gốc).

**3. Gắn cờ NGHI SAI NỘI DUNG – không sửa** (câu **không được dịch**, chuyển CTV tiếng Nhật). Ghi vào khóa `nghi_noi_dung`, **mỗi chỗ nghi một mục**:

```json
"nghi_noi_dung": [
  {"vi_tri": "Phân tích lựa chọn 4 – về ngữ pháp", "nhom": "danh_gia_ngu_phap",
   "mo_ta": "(quy tắc 3d-1) 'きのう えいがを見るから どう しましたか' đúng ngữ pháp (thể thường + から); lỗi thật là nghĩa/thì: 見るから = 'vì sẽ xem', không hợp với câu hỏi về hôm qua. Lời giải chấm 'Sai' ngữ pháp với lý do câu dùng しました (thể lịch sự) – sai.",
   "de_xuat": "+ Về ngữ pháp: Đúng. + Về ngữ nghĩa: Không phù hợp – '見るから' chỉ lý do / hành động chưa xảy ra, không diễn tả 'sau khi xem phim hôm qua'."},
  {"vi_tri": "Lựa chọn đúng – câu hoàn chỉnh", "nhom": "cau_khac_de",
   "mo_ta": "(quy tắc 3d-5) Câu hoàn chỉnh viết 'あなたなりの考えが…' trong khi đề là 'あなた ____ お考えが…' – mất お.",
   "de_xuat": "この問題については、あなたなりのお考えがおありでしょうが、ここのところは私の言うとおりにしてください。"}
]
```

- `vi_tri`: `Câu đề`, `Câu đề – cách đọc`, `Câu đề – nghĩa`, `Phân tích – cấu trúc chung`, `Phân tích lựa chọn N – ý nghĩa` / `– cấu trúc` / `– câu áp dụng` / `– về ngữ pháp` / `– nghĩa câu` / `– về ngữ nghĩa`, `Lựa chọn đúng`, `Lựa chọn đúng – câu hoàn chỉnh`, `Lựa chọn đúng – nghĩa`.
- `nhom`: `nghia_cau` · `danh_gia_ngu_phap` · `ly_do_loai` · `y_nghia_cau_truc` · `cach_doc` · `cau_khac_de` · `dap_an` · `thieu_noi_dung` · `khac`.
- `mo_ta`: vì sao nghi sai (ghi số quy tắc nếu tiện); `de_xuat`: cách sửa đề xuất – **không** sửa vào JSON.
- Không chắc lắm cũng gắn cờ (CTV quyết) – nhưng không gắn cờ cho cách diễn đạt chỉ "chưa hay".

**3c. Quy tắc nghi sai nội dung chung (từ phản hồi CTV tiếng Hàn – bảng ví dụ ở prompt dạng 01 mục 3c)**

1. **Nghĩa câu (tiếng Việt)** – dù bản Hàn dịch thẳng từ tiếng Nhật, JSON tiếng Việt vẫn là sản phẩm: lệch câu Nhật là phải gắn cờ `nghia_cau` (phản hồi CTV 05/10/2026: tự thêm 'lúc nào cũng', thiếu 'vẫn', đổi 'được sản xuất tại Nhật' thành 'là xe của Nhật'). Gồm cả: dịch sai cấu trúc ngữ pháp, tự thêm / bớt / thu hẹp ý, hiểu sai từ ngoại lai, lệch sắc thái động từ then chốt, mất thì/thể (〜てきた, 〜あろう, sai khiến, bị động, phủ định).
2. **Ý nghĩa của mẫu ngữ pháp** mất bị động, sai khiến, phủ định, khả năng; sai nghĩa hẳn (xem 3d-3).
3. **Câu trong lời giải khác đề bài** (thiếu / thừa / sai chữ, chép nhầm câu của lựa chọn khác) → `cau_khac_de` (xem 3d-5).

**3d. Quy tắc riêng dạng 07 – Lựa chọn ngữ pháp (bắt buộc soát – đã duyệt 07/10/2026)**

| # | Lỗi cần bắt | `nhom` |
|---|---|---|
| 1 | **Đánh giá ngữ pháp sai rõ ràng**: lời giải chấm "Về ngữ pháp: Sai" cho câu đúng ngữ pháp mà lỗi thật ở nghĩa / thì / ngữ cảnh (vd 5531 lựa chọn 4 「見るから」); hoặc chấm "Đúng" cho tổ hợp không thể ghép được. Lời giải gộp lỗi ngữ pháp với lỗi nghĩa nhưng **kết luận loại vẫn đúng** → **không** gắn cờ. | `danh_gia_ngu_phap` |
| 2 | **Lý do loại không nêu lỗi chính hoặc tự mâu thuẫn** (nói 'Đúng' ngữ pháp rồi giải thích như lỗi ngữ pháp; lý do không liên quan tới lựa chọn; nhận xét trái với chính phần Ý nghĩa). Đã nêu đúng lỗi chính, chỉ thêm nhận xét phụ → không gắn cờ. | `ly_do_loai` |
| 3 | **Ý nghĩa / cấu trúc của mẫu ngữ pháp giải thích sai kiến thức** (nghĩa sai, cách nối sai). Nội dung chỉ **đặt nhầm dòng** (vd ý nghĩa nằm ở dòng 'Cấu trúc:' – 4040) là lỗi định dạng: GPT/Claude đặt đúng trường theo nội dung, ghi `sai_so_ban_goc` hoặc `[Đã sửa định dạng]`, không gắn cờ. | `y_nghia_cau_truc` |
| 4 | **Nghĩa câu** (`question.meaning`, `applied.meaning`, `full_sentence.meaning`) lệch câu tiếng Nhật: sai cấu trúc, mất phủ định / bị động / sai khiến / khả năng, thêm bớt ý (3c-1). Câu sai ngữ pháp được dịch **sát chữ, gượng** (vd 3890 'suy nghĩ tùy thuộc vào') là chủ ý của lời giải → **không** gắn cờ. Nghĩa câu đề bỏ trống đúng chỗ trống → bình thường. | `nghia_cau` |
| 5 | **Câu tiếng Nhật khác đề**: câu 'Áp dụng vào câu' / 'Câu hoàn chỉnh' khác câu đề đã điền lựa chọn về **chữ hoặc nghĩa** (cờ tự động `ap_dung_lech_nang`, `hoan_chinh_khac_de`; gợi ý `A:`), chép nhầm câu của lựa chọn khác (11048, 53289), câu đề trong lời giải khác đề (7772 律法 → 方法), lựa chọn trong PHÂN TÍCH viết khác đề (`lua_chon_khac_de`). **Không** tính: chữ Hán ↔ kana (限る / かぎる), đề hội thoại chỉ áp dụng dòng có chỗ trống, đề 2 chỗ trống, khác dấu câu / khoảng trắng / ①② – Python đã bỏ qua. Lệch 1–2 ký tự do gõ (`ap_dung_lech_nhe`) → **sửa định dạng** (mục 2), không gắn cờ. | `cau_khac_de` |
| 6 | **Đáp án đáng ngờ**: đáp án bị chấm Sai / Không phù hợp (cờ `dap_an_khong_dat`, K11); lựa chọn sai được chấm cả 'Đúng' + 'Phù hợp' (cờ `lua_chon_sai_ca_hai_dung`, K11 – có thể 2 đáp án); số ở LỰA CHỌN ĐÚNG khác đề mà nội dung cũng khác (`lech_dap_an`). Số gõ nhầm nhưng nội dung đúng đáp án (`lcd_go_nham_so`) → chỉ ghi `[Đã sửa định dạng]` (JSON đã theo `dap_an_so`). | `dap_an` |
| 7 | **Cách đọc câu đề** sai so với câu tiếng Nhật – xem gợi ý **R1** | `cach_doc` |
| 8 | Thiếu phân tích lựa chọn / thiếu Áp dụng / thiếu Nhận xét **làm người học không hiểu vì sao loại** (lựa chọn chỉ có 'Ý nghĩa: … không tồn tại trong tiếng Nhật' là đủ – không gắn cờ) | `thieu_noi_dung` |

**3d (dạng 09 – thêm, duyệt 08/10/2026)**

| # | Lỗi cần bắt | `nhom` |
|---|---|---|
| 9 | **Câu đề trong lời giải chép lệch đoạn văn gốc** (cờ `de_lech_doan_van_nang`, gợi ý `ĐV:`, cảnh báo `K-ĐV`): mất / thêm / khác chữ so với câu tương ứng trong đoạn văn (vd 11194_1 mất 'はっきり'). Lệch chỉ do gõ kana / ruby hỏng (`de_lech_doan_van_nhe`, vd 'もう少すこし') → **sửa định dạng** `question.ja` theo đoạn văn (mục 2). Chữ Hán ↔ kana cùng cách đọc, cách đọc trong ngoặc của đoạn văn, nhãn chỗ trống khác kiểu → không tính. | `cau_khac_de` |
| 10 | **Lý do chọn / loại trái với mạch văn của cả đoạn**: lựa chọn (thường là liên từ, từ nối, thì / thể) được phân tích chỉ theo câu trích mà kết luận sai khi đọc câu trước / sau trong đoạn văn; hoặc nghĩa câu đề / câu áp dụng hiểu sai vì không xét đoạn văn. **Phải đọc đoạn văn** (cột `doan_van` trong `output/samples/norm/<id>.json`, hoặc `xem_gd1.py`) khi soát lựa chọn đúng và lý do loại. | `ly_do_loai` / `nghia_cau` |

- Dạng 09: `question.ja` = câu đề TRONG LỜI GIẢI (không phải câu trong đoạn văn) – Python K8 so với lời giải; chỉ sửa theo đoạn văn khi là lỗi định dạng (3d-9) và ghi `sua_dinh_dang`.
- **Ruby hỏng** (`少すこし`, `一番いちばん`, `聞きき`) ở bất kỳ trường tiếng Nhật nào → `sua_dinh_dang` `nhom: furigana` (bỏ kana lặp, hoặc khôi phục furigana đúng như chỗ khác trong cùng câu), kể cả khi Python báo `ap_dung_lech_nang` / `hoan_chinh_khac_de`. Câu áp dụng bị cụt cuối → cờ `thieu_noi_dung`.
- **Không tính là khác đề:** thêm / bỏ ký hiệu chú thích `(注n)`; câu áp dụng chỉ trích mệnh đề / ngoặc 「」 chứa chỗ trống mà phần trích đúng chữ đề → `[Ghi chú] … không gắn cờ`.
- `passage` do Python điền (`{"blank_label": "[n]", "lines": []}`) – không sửa (K-PS).
- `dap_an_de_loi` (vd 53467_3: `dap_an_so = 33`) → gắn cờ `dap_an`, báo người dùng sửa dữ liệu gốc.

- Bắt buộc so: **câu áp dụng ↔ câu đề + lựa chọn**, **đánh giá ngữ pháp / ngữ nghĩa ↔ câu áp dụng**, **lý do ↔ ý nghĩa mẫu ngữ pháp**, **nghĩa câu ↔ câu tiếng Nhật**, **câu hoàn chỉnh ↔ đề + đáp án**.
- **`grammar_ok` / `semantic_ok`** là điều lời giải NÓI (GPT điền theo lời giải). GPT điền sai so với lời giải → sửa (lỗi GPT, `sai_so_ban_goc`). Lời giải nói sai sự thật → giữ theo lời giải và gắn cờ (3d-1 / 3d-6).
- **Cách đọc ghép từ furigana** (cờ `doc_tu_furigana`, ghi chú `[Cách đọc ghép từ furigana]`): `question.reading` phải đúng chuỗi Python ghép (K8) – không sửa, không gắn cờ trừ khi furigana gốc sai.

**3e. Gợi ý Python – `[Từ điển Sudachi] …`** (chỉ là gợi ý; Claude xác nhận rồi mới gắn cờ – gợi ý nào bỏ qua thì ghi lý do vào `ghi_chu_ban_goc` dạng `[Ghi chú] R1/A … không gắn cờ vì …`):
- **R1** – dòng "Cách đọc:" của câu đề lệch cách đọc từ điển. Lệch thật → 3d-7; chữ nhiều âm đúng ngữ cảnh (何 なに/なん, 今日 きょう/こんにち, 人 ひと/にん, 何時 なんじ/いつ) → không gắn cờ.
- **A** – câu 'Áp dụng' / 'Câu hoàn chỉnh' lệch câu đề đã điền lựa chọn (kèm chỗ lệch theo cách đọc). Xem 3d-5: lệch về chữ / nghĩa → cờ; lệch gõ → sửa định dạng; lệch do câu đề trong lời giải khác đề (vd câu đề lặp chữ '外国外国へ') → xử lý ở câu đề (sửa định dạng nếu là lỗi gõ, gắn cờ nếu khác chữ).
- Cảnh báo **K11** (đáp án / 2 đáp án) → 3d-6.

**3b. Sau khi CTV tiếng Nhật trả kết quả cho câu bị cờ** (chỉ làm khi bạn đưa phản hồi CTV):
- CTV xác nhận **không sai** → xóa mục cờ tương ứng, không sửa JSON.
- CTV xác nhận **sai** → sửa JSON đúng theo CTV, ghi mục `sua` với `"loai": "sua_theo_ctv"` + `nhom` và dòng `[Đã sửa theo CTV] <chỗ>: '<cũ>' → '<mới>' – <CTV nói gì>`; xóa mục cờ đã xử lý.
- Chạy lại `s1_kiem_tra.py` → câu hết cờ thành GĐ1_XONG, được chốt và dịch.

**4. Âm Hán Việt** (chỉ tính khi lời giải ghi âm Hán Việt như cách đọc) – Python tự dò (`[Âm Hán Việt] …`). Claude không sửa; câu có âm Hán Việt tự động **không được dịch**. Python dò sót thì gắn cờ `nghi_noi_dung` nhóm `khac`, ghi rõ là âm Hán Việt.

**Dạng của câu:** có ít nhất một `sua_dinh_dang` → **Dạng 2**; không → **Dạng 1**. Chỉ câu **không có** `nghi_noi_dung` **và không có** âm Hán Việt mới được chốt và dịch.

## Checklist cấu trúc

- [ ] `question.ja` = dòng câu đề của lời giải (không nhãn 'Đề bài:'); `reading` = dòng Cách đọc hoặc chuỗi ghép từ furigana; `meaning` = dòng Nghĩa (giữ chỗ trống).
- [ ] `analysis.intro` = đoạn Cấu trúc chung (nếu có).
- [ ] **Mỗi lựa chọn**: `option_ja` = dòng `i.` của lời giải; Ý nghĩa → `meaning`; Cấu trúc → `structure`; câu Áp dụng → `applied.ja` (chép nguyên); `Nghĩa:` → `applied.meaning`; đánh giá → `grammar_ok` / `semantic_ok`, phần giải thích → `grammar_note` / `semantic_note` (không còn chữ 'Đúng.' / 'Sai.' / 'Phù hợp.' ở đầu); dòng lẻ → `other`.
- [ ] `correct.index` = `dap_an_so`; `correct.option_ja` giống hệt lựa chọn đó; `full_sentence` = Câu hoàn chỉnh + Nghĩa; `note` = câu chữ khác (nếu có).
- [ ] `{ }` đúng số cặp, đúng chỗ; mọi tiếng Nhật trong câu tiếng Việt được bọc `⟪ ⟫`; furigana `｜…《…》` đúng như bản gốc.
- [ ] Soát đủ **3c**, **3d** và mọi gợi ý **3e**, cảnh báo **K11**; gắn cờ `nghi_noi_dung` cho mọi chỗ nghi sai nội dung.

## Mẫu file lý do

```json
{
  "sua": [
    {"duong_dan": "$.analysis.options[1].semantic_note.vi", "loai": "sai_so_ban_goc", "muc_do": "nhe",
     "ly_do": "GPT để sót chữ đánh giá 'Không phù hợp.' ở đầu semantic_note – bỏ (đã thể hiện bằng semantic_ok = false)"},
    {"duong_dan": "$.analysis.options[0].applied.ja", "loai": "sua_dinh_dang", "nhom": "lap_tu", "muc_do": "nhe",
     "ly_do": "lặp ký tự do gõ: '感じじられる' → '感じられる'"}
  ],
  "ghi_chu_ban_goc": ["[Đã sửa định dạng] Phân tích lựa chọn 1 – câu áp dụng: '…品が感じじられる。' → '…品が感じられる。' – lặp ký tự do gõ"],
  "nghi_noi_dung": []
}
```

- `loai`: `sai_so_ban_goc` | `chinh_ta` | `khach_quan` | `chu_quan` (lỗi GPT) | `sua_dinh_dang` (lỗi định dạng bản gốc – bắt buộc `nhom` + dòng `[Đã sửa định dạng]`) | `sua_theo_ctv` (sau CTV). `muc_do`: `nghiem_trong` | `nang` | `nhe`. Không dùng `sua_ban_goc` nữa.
- Không có gì thì để `"sua": []`, `"nghi_noi_dung": []`. Xong thì xóa khóa `_huong_dan`.
