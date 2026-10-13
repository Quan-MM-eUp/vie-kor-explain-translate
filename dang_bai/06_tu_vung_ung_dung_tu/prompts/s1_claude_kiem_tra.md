# Hướng dẫn Claude – Bước 1.2: kiểm tra JSON tiếng Việt và sửa lỗi (dạng 06 – Ứng dụng từ) · v1

> Phiên bản `s1_claude_kiem_tra.v1` của dạng 06 (2026-10-07): dựng từ bản v1 của dạng 05 – **cách chia v2** (sửa định dạng / gắn cờ nội dung) + quy tắc nghi sai nội dung từ phản hồi CTV + **quy tắc riêng dạng 06** (mục 3d – đã được duyệt 07/10/2026) + **gợi ý Sudachi R1/R2** (mục 3e).
> **v1.1 (2026-10-09):** bổ sung từ phản hồi CTV tiếng Hàn file `2026-10-07-CTV-06_ung_dung_tu-v1-mau1-100 08.10.2026.xlsx` – 10/63 mẫu đã ĐẠT bị CTV trả lại vì lỗi nội dung lời giải bị soát sót: mở rộng 3d-3, 3d-4, 3d-8; thêm 3d-11 (`kien_thuc`), 3d-12 (`tu_loai`); thêm bước **phản biện từng phương án** (mục 3f).
> Model: **Claude Opus 5.5**, chạy trong Claude Cowork (không qua API). Nếu chia việc cho tác tử con thì tác tử con cũng dùng Opus 5.5.

> **Từ 2026-10-08 (mẫu 101 trở đi):** bản cần kiểm tra do **tác tử TẠO (Claude A, ngữ cảnh riêng)** tạo thay GPT – mọi chỗ "bản GPT" / "lỗi GPT" dưới đây hiểu là bản / lỗi của tác tử TẠO; cách kiểm tra không đổi. Bạn (tác tử KIỂM TRA) không tạo lại bản, chỉ soát và sửa như với bản GPT.

**Nhiệm vụ:** kiểm tra JSON tiếng Việt do GPT tạo **so với lời giải gốc** và sửa lỗi. Chuẩn so sánh là lời giải gốc đã chuẩn hóa. JSON phải thể hiện đúng và đủ lời giải gốc, không hơn, không kém.

## Làm gì

Danh sách câu: `output/claude/gd1_danh_sach_<tu>_<den>.json` (chạy song song 2026-10-12; trước đó `gd1_danh_sach.json`) (tạo bằng `python scripts/s1_claude_goi.py …`). Mỗi mục có: cờ (`co`), ghi chú bản gốc tự động, **kết quả Python chạy thử trên bản GPT** (`python_tren_ban_gpt` – gợi ý, gồm cả `[Âm Hán Việt] …`, `[Nghi dính câu/định dạng] …` và `[Từ điển Sudachi] R1/R2 …`), đường dẫn các file.

Với mỗi câu:

1. Đọc `output/samples/norm/<id>.json`: `de` (đề, 4 lựa chọn, đáp án), `dau_vao` (lời giải gốc đã chuẩn hóa – `{ }` là chỗ in đậm / gạch chân của bản gốc), `co`.
2. Mở `output/json_vi/checked/<id>.json` (đã chép sẵn từ bản GPT) và **sửa trực tiếp** nếu có lỗi. Giữ đúng schema `vocab_usage.v2`; file phải là JSON hợp lệ.
3. Ghi `output/json_vi/checked/<id>.ly_do.json` theo mẫu bên dưới – **xong thì xóa khóa `_huong_dan`**.
4. Chỉ sửa file trong `output/json_vi/checked/`.
5. Làm xong cả danh sách thì chạy `python scripts/s1_kiem_tra.py …` (cùng phạm vi) và báo kết quả.

## Phạm vi sửa – cách chia v2

Ba việc tách bạch: **sửa lỗi GPT**, **sửa lỗi ĐỊNH DẠNG của bản gốc**, **gắn cờ NGHI SAI NỘI DUNG**. Claude **không sửa nội dung** của bản gốc.

**1. Sửa lỗi của GPT:** `sai_so_ban_goc` (đặt sai trường, bỏ sót, tự thêm, viết lại, sai ký hiệu ⟪ ⟫ / { } / furigana, nhận xét nằm nhầm lựa chọn, Cách đọc / Nghĩa của câu gốc và của câu sửa bị đổi chỗ, `word.paren` / `definition_ja` / `is_correct` / `usage_ok` sai so với lời giải, tách `word.meaning` / `word.usage` sai, GPT tự sửa câu cho khớp đề, `correct.note` bỏ sót…), `chinh_ta` (lỗi GPT tạo ra), `khach_quan`. Không làm câu đổi dạng.

**2. Sửa lỗi ĐỊNH DẠNG có sẵn trong bản gốc** – `loai: sua_dinh_dang` + `nhom`:

| nhom | Ví dụ |
|---|---|
| `dinh_chu` | dính câu / dính chữ: "…đồng nghĩa.Tóm lại" → "…đồng nghĩa.⏎Tóm lại" |
| `xuong_dong` | thiếu xuống dòng: "…phù hợp hơn.3. 小麦粉…", "Sửa lại: …浴びています。Cách đọc: …" |
| `lap_tu` | "của của", "từ từ" (lặp do gõ) |
| `chinh_ta` | lỗi chính tả / dấu tiếng Việt, mất chữ |
| `dau_cau` | dấu câu thừa / thiếu, khoảng trắng trước dấu phẩy |
| `khoang_trang` | khoảng trắng thừa trong câu / cách đọc / ví dụ tiếng Nhật |
| `ky_tu` | sai ký tự rõ ràng (katakana lẫn hiragana, số ①②③ lẫn trong câu tiếng Nhật) |
| `cach_doc_lan_so` | cách đọc lẫn số thứ tự đọc thành chữ (いち, に, さん…) |
| `furigana` | furigana lệch phạm vi rõ ràng: `｜はかる必要《ひつよう》` → `はかる｜必要《ひつよう》`; furigana gắn lên chữ Việt (`｜Câu《く》`) → bỏ |
| `khac` | lỗi định dạng khác (ghi rõ trong `ly_do`) |

- Mỗi chỗ sửa định dạng có **hai** ghi chép: mục trong `sua` (`duong_dan` ở mức trường nhỏ nhất, `loai`, `nhom`, `muc_do`, `ly_do`) **và** một dòng trong `ghi_chu_ban_goc`: `[Đã sửa định dạng] <chỗ sửa>: '<cũ>' → '<mới>' – <lỗi gì>`.
- **Không** dùng `sua_dinh_dang` để thêm / dời `{ }` ở câu của lựa chọn: Python (K5) so `{ }` với dòng câu của lời giải – lệch là LỖI.
- **Câu của lựa chọn / câu sửa / cách đọc** (`sentence.ja`, `correction.ja`, `reading`) phải chép đúng lời giải (K2, K7, K8). Lời giải viết câu khác đề, sai chữ, cách đọc sai → **gắn cờ**, không sửa (trừ lỗi định dạng rõ ràng như khoảng trắng thừa, furigana lệch phạm vi).
- **Một trường – một loại sửa:** `sua_dinh_dang` trên một trường (vd `$.analysis.options[2].analysis.vi`) khiến Python khi đo độ trung thành trả **cả trường** đó về bản GPT; nếu trường đó còn có sửa lỗi GPT (`khach_quan`, `sai_so_ban_goc`) thì hai việc đè nhau → báo thiếu chữ. Khi trùng, ưu tiên sửa lỗi GPT và chuyển lỗi định dạng thành mô tả trong cờ / `ghi_chu_ban_goc`.
- Ghi chú `[Đã sửa định dạng] …` viết trên **một dòng** (xuống dòng thì ghi `⏎`, không chèn ký tự xuống dòng thật).
- Gợi ý `[Nghi dính câu/định dạng] …` của Python chỉ là gợi ý – xác nhận rồi mới sửa; không sửa "..", "…" (cách viết của bản gốc).

**3. Gắn cờ NGHI SAI NỘI DUNG – không sửa** (câu **không được dịch**, chuyển CTV tiếng Nhật). Ghi vào khóa `nghi_noi_dung`, **mỗi chỗ nghi một mục**:

```json
"nghi_noi_dung": [
  {"vi_tri": "Phân tích lựa chọn 2 – câu sửa", "nhom": "cau_dung_bi_sua",
   "mo_ta": "(quy tắc 3d-2) 彼は自他ともに許す財界の大物だ là thành ngữ chuẩn (自他ともに許す: được mọi người công nhận); lời giải chê 'không phổ biến' và sửa thành 認める – sai. Câu dùng 許す đúng nhưng khác nghĩa định nghĩa.",
   "de_xuat": "Bỏ 'Sửa lại'; nhận xét: '自他ともに許す' là thành ngữ, 許す ở đây nghĩa là 'công nhận', dùng đúng nhưng không mang nghĩa 'chấp nhận một hành vi là không có vấn đề' nên không phải lựa chọn đúng."},
  {"vi_tri": "Phân tích lựa chọn 2 – nhận xét", "nhom": "ly_do_loai",
   "mo_ta": "(quy tắc 3d-3) Lời giải nói わざわざ 'được sử dụng đúng', chỉ thừa と – không nêu lý do chính: không có điện thoại nên phải ra điện thoại công cộng là việc cần thiết, không phải 'cất công'.",
   "de_xuat": "わざわざ không phù hợp vì việc ra điện thoại công cộng là bắt buộc (không có điện thoại), không phải cất công làm việc không cần thiết; ngoài ra 'わざわざと' sai ngữ pháp."}
]
```

- `vi_tri`: `Giới thiệu từ`, `Giới thiệu từ – cách dùng`, `Phân tích – mở đầu`, `Phân tích lựa chọn N – câu` / `– cách đọc` / `– nghĩa câu` / `– nhận xét` / `– câu sửa` / `– cách đọc câu sửa` / `– nghĩa câu sửa`, `Lựa chọn đúng`.
- `nhom`: `nghia_cau` · `nghia_tu` · `chu_han` · `cach_doc` · `cau_dung_bi_sua` · `ly_do_loai` · `cau_sua` · `dap_an` · `cau_khac_de` · `thieu_noi_dung` · `kien_thuc` · `tu_loai` · `khac`.
  - **Tạm thời:** `kien_thuc` / `tu_loai` cần được thêm vào `NHOM_NOI_DUNG` trong `pipeline_chung/claude_log.py` (việc của cuộc trò chuyện điều phối). Khi `ghi_ly_do.py` / `s1_kiem_tra.py` còn báo "nhom không hợp lệ" → dùng `khac` và mở đầu `mo_ta` bằng `(quy tắc 3d-11 kien_thuc)` / `(quy tắc 3d-12 tu_loai)` để sau này lọc lại.
- `mo_ta`: vì sao nghi sai (ghi số quy tắc nếu tiện); `de_xuat`: cách sửa đề xuất – **không** sửa vào JSON.
- Không chắc lắm cũng gắn cờ (CTV quyết) – nhưng không gắn cờ cho cách diễn đạt chỉ "chưa hay".

**3c. Quy tắc nghi sai nội dung chung (từ phản hồi CTV tiếng Hàn 02/10/2026 – bảng ví dụ ở prompt dạng 01 mục 3c)**

1. **Nghĩa câu (tiếng Việt)** – dù bản Hàn dịch thẳng từ tiếng Nhật, JSON tiếng Việt vẫn là sản phẩm: lệch câu Nhật là phải gắn cờ `nghia_cau` (phản hồi CTV tiếng Hàn 05/10/2026, dạng 02: 2417 tự thêm 'lúc nào cũng', 2257 '{Còn} học sinh…' thiếu 'vẫn', 2728 'là xe của Nhật Bản' thay vì 'được sản xuất tại Nhật Bản'). Gồm cả: dịch sai cấu trúc ngữ pháp, tự thêm / bớt / thu hẹp ý, hiểu sai từ ngoại lai, lệch sắc thái động từ then chốt, mất thì/thể (〜てきた, 〜あろう, sai khiến, bị động).
2. **Nghĩa của từ / lựa chọn** mất bị động, sai khiến, phủ định, sai từ loại so với dạng xuất hiện; sai nghĩa hẳn.
3. **Nghĩa câu của lựa chọn / của câu sửa** dịch sai câu tiếng Nhật (xem 3d-7).
4. **Câu trong lời giải khác đề bài** (bị cụt, sai chữ, thừa chữ, furigana lặp chữ như `お｜落《お》ちて`) → gắn cờ `cau_khac_de`, ghi rõ lỗi có cả trong đề hay không (cờ tự động `cau_khac_de` + ghi chú `[Bản gốc VI] Câu N … khác đề`).

**3d. Quy tắc riêng dạng 06 – Ứng dụng từ (bắt buộc soát – đã duyệt 07/10/2026)**

| # | Lỗi cần bắt | `nhom` |
|---|---|---|
| 1 | **Câu đúng bị nói là sai**: lựa chọn không phải đáp án mà thực ra là cách dùng tự nhiên. Đề **có định nghĩa** (`definition_ja`): câu dùng từ đúng nhưng khác nghĩa đã cho thì lời giải phải nói "dùng đúng nhưng khác nghĩa", không được nói "sai / không tự nhiên". | `ly_do_loai` |
| 2 | **Lời giải "Sửa lại" một câu vốn đúng** (vd 54314 自他ともに許す → 認める) – xem cảnh báo **K16** ở đề có định nghĩa. | `cau_dung_bi_sua` |
| 3 | **Lý do loại không nêu lỗi chính về cách dùng từ**: lời giải nói từ "được dùng đúng" rồi chỉ chê lỗi phụ (trợ từ, ngữ pháp…), hoặc không giải thích được vì sao câu bị loại (vd 433 lựa chọn 2 わざわざと) – xem cảnh báo **K15**. **Cả khi lý do nêu SAI hoặc TUYỆT ĐỐI HÓA**: đưa ra quy tắc chung kiểu "X không bao giờ dùng với Y", "chỉ dùng cho…", "〜できない là trạng thái tuyệt đối, không có mức độ", "không dùng để nói đồ ăn ngon" mà từ điển / thực tế có phản ví dụ → gắn cờ; `de_xuat` nêu lý do đúng dựa vào **sắc thái / ngữ cảnh của chính câu này** ("câu này không tự nhiên vì…, tự nhiên hơn là…"). Ví dụ CTV 2026-10-09: 432 (研ぐ "không dùng với làm sạch/đánh bóng" – có 鏡を研ぐ), 483 (よほど: 3 lý do đều khái quát sai), 2476 (うまい "chỉ dùng cho kỹ năng thực hành"), 10523 (見物 "không dùng để ngắm hoa" – có 桜見物; lỗi thật là 見物 với một cá thể 大きな花), 1439 (chê cả あるいは trong câu sửa vốn đúng). Lời giải đã nêu đúng lỗi chính, chỉ thêm nhận xét phụ **đúng** → **không** gắn cờ. | `ly_do_loai` |
| 4 | **Câu sửa sai / không tự nhiên / đổi nghĩa câu / sửa chỗ khác chứ không phải từ đang hỏi** (vd 433 lựa chọn 4 'わざわざではなく…') – xem gợi ý **R2**. **Sửa không đúng lỗi chính** cũng gắn cờ: vd 538 一見、あの人は日本人だとわかります – lỗi thật là thiếu して (一見して～とわかる), lời giải lại đổi わかります → 見えます và nói わかります không dùng được với 一見. Sửa thêm chỗ khác nhưng cần thiết để câu tự nhiên → không gắn cờ. | `cau_sua` |
| 5 | **Nghĩa / cách viết chữ Hán / cách đọc của từ** ở đoạn giới thiệu sai (vd chọn nhầm 計る / 測る / 量る / 図る / 諮る; nghĩa giải sai) | `nghia_tu` / `chu_han` / `cach_doc` |
| 6 | **Cách đọc** của câu / câu sửa sai so với câu tiếng Nhật – xem gợi ý **R1** | `cach_doc` |
| 7 | **Nghĩa câu** (`sentence.meaning`, `correction.meaning`) lệch câu tiếng Nhật (mục 3c-1) | `nghia_cau` |
| 8 | **Đáp án đáng ngờ**: có từ 2 câu dùng đúng (đề thường), đáp án dùng sai, nhận xét mâu thuẫn với đáp án, số ở LỰA CHỌN ĐÚNG khác đề, `correct.note` nói "không có lựa chọn nào hoàn toàn phù hợp" – xem **K6**, **K13**, **K16**. **Bắt buộc làm bước phản biện 3f**: phương án nhiễu có cách hiểu / kết hợp tự nhiên (vd 432 感覚を研ぐ – gần 感覚を研ぎ澄ます; 1374 微妙に年上 = "lớn hơn một chút"; 2476 数学がうまい hiểu được là "giỏi toán") → gắn cờ, `de_xuat` "đổi phương án nhiễu sang câu sai rõ ràng". **Chính câu đáp án không tự nhiên** cũng gắn cờ (vd 10558 塗装を塗る – 塗る đi với ペンキ／塗料; 塗装 dùng 塗装する／塗装を行う). | `dap_an` |
| 9 | Câu / cách đọc câu trong lời giải **khác đề** (cờ `cau_khac_de`) | `cau_khac_de` |
| 11 | **Sai kiến thức thực tế / ngoài ngôn ngữ** trong nghĩa câu hoặc nhận xét (vd 589 単一の通貨 giải là "ở châu Âu chỉ sử dụng một loại tiền tệ" – châu Âu còn nhiều đồng tiền khác ngoài euro; từ vựng vẫn đúng, chỉ cần sửa diễn giải). | `kien_thuc` |
| 12 | **Sai từ loại** khi lời giải dùng từ loại làm lý do (vd 701 "軽率 là tính từ" – đúng là 名詞・ナ形容詞; lý do sai thật của 軽率してはいけません là không dùng 軽率する như động từ). Phân biệt rõ イ形容詞 / ナ形容詞 / 名詞 / する動詞 / 副詞. | `tu_loai` |
| 10 | Phần PHÂN TÍCH thiếu lựa chọn, thiếu nhận xét, câu sai thiếu "Sửa lại" (cờ `thieu_sua_lai` – chỉ là thông tin, gắn cờ khi thiếu làm người học không hiểu) | `thieu_noi_dung` |

- Bắt buộc so: **nhận xét ↔ câu tiếng Nhật** (lý do loại đúng chưa), **câu sửa ↔ câu gốc** (sửa đúng chỗ, câu sửa tự nhiên), **`usage_ok` ↔ nhận xét**, **đề có định nghĩa: từng câu dùng nghĩa nào**, **nghĩa câu / cách đọc ↔ câu tiếng Nhật**, **đoạn giới thiệu ↔ từ**.
- **`usage_ok`** là điều lời giải NÓI (GPT điền theo lời giải). Thấy GPT điền sai so với lời giải → sửa (lỗi GPT, `sai_so_ban_goc`). Lời giải nói sai sự thật → giữ `usage_ok` theo lời giải và gắn cờ.
- `[Bản gốc VI]` trong `ghi_chu_ban_goc` không còn dùng cho nghi vấn nội dung (dùng `nghi_noi_dung`).

**3f. Phản biện từng phương án (bắt buộc – thêm 2026-10-09)**
Với **mỗi** lựa chọn, trước khi kết luận "không gắn cờ", tự trả lời 3 câu và chỉ gắn cờ khi có câu trả lời "có" chắc chắn hoặc khá chắc:
1. Phương án nhiễu này có ngữ cảnh / kết hợp từ nào khiến câu **tự nhiên** không (nghĩa mở rộng, nghĩa bóng, kết hợp cố định trong từ điển)? → 3d-1 / 3d-8.
2. Lý do loại có phải là **quy tắc chung** dễ bị phản ví dụ không, hay chỉ nói về câu này? Lý do có đúng **từ loại**, đúng **thực tế** không? → 3d-3 / 3d-11 / 3d-12.
3. Câu sửa (và chính câu đáp án) có thật **tự nhiên** và sửa **đúng lỗi chính** không? → 3d-4 / 3d-8.
Không chắc → vẫn gắn cờ (CTV quyết), `mo_ta` ghi rõ mức chắc chắn. Lô 1–100: Claude cho ĐẠT 63 mẫu, CTV trả lại 10 (16%) – đều thuộc các câu hỏi này.

**3e. Gợi ý Sudachi – `[Từ điển Sudachi] …`** (chỉ là gợi ý; Claude xác nhận rồi mới gắn cờ – gợi ý nào bỏ qua thì ghi lý do vào `ghi_chu_ban_goc` dạng `[Ghi chú] R1/R2 … không gắn cờ vì …`):
- **R1** – dòng "Cách đọc:" (câu gốc / câu sửa) lệch cách đọc từ điển của câu tiếng Nhật. Lệch thật (thiếu chữ, sai âm, sai thì) → 3d-6; chữ nhiều âm đúng ngữ cảnh (何 なに/なん, 今日 きょう/こんにち, 行う おこなう / 行く いく do từ điển đoán sai, 人 ひと/にん) → không gắn cờ.
- **R2** – câu "Sửa lại" giữ nguyên từ đang hỏi và chỉ đổi chỗ khác, hoặc giống hệt câu gốc. Xem lời giải có đang ngầm nói từ dùng đúng không (→ 3d-3), câu sửa có đổi nghĩa không (→ 3d-4); đổi chỗ khác nhưng hợp lý (kèm thay từ) → không gắn cờ.

**3b. Sau khi CTV tiếng Nhật trả kết quả cho câu bị cờ** (chỉ làm khi bạn đưa phản hồi CTV):
- CTV xác nhận **không sai** → xóa mục cờ tương ứng, không sửa JSON.
- CTV xác nhận **sai** → sửa JSON đúng theo CTV, ghi mục `sua` với `"loai": "sua_theo_ctv"` + `nhom` và dòng `[Đã sửa theo CTV] <chỗ>: '<cũ>' → '<mới>' – <CTV nói gì>`; xóa mục cờ đã xử lý.
- Chạy lại `s1_kiem_tra.py` → câu hết cờ thành GĐ1_XONG, được chốt và dịch.

**4. Âm Hán Việt** (chỉ tính khi lời giải ghi âm Hán Việt như cách đọc, vd '細心 - TẾ TÂM') – Python tự dò (`[Âm Hán Việt] …`, kể cả kiểu "chữ TRỊ"). Claude không sửa; câu có âm Hán Việt tự động **không được dịch**. Python dò sót thì gắn cờ `nghi_noi_dung` nhóm `khac`, ghi rõ là âm Hán Việt.

**Dạng của câu:** có ít nhất một `sua_dinh_dang` → **Dạng 2**; không → **Dạng 1**. Chỉ câu **không có** `nghi_noi_dung` **và không có** âm Hán Việt mới được chốt và dịch.

## Checklist cấu trúc

- [ ] Nội dung đặt đúng trường; không thiếu ý, thừa ý, không bị viết lại; đã bỏ nhãn cố định (số `i.`, "Cách đọc:", "Nghĩa:", "Sửa lại:").
- [ ] `word.ja` / `word.paren` = từ + ngoặc ở đầu đoạn giới thiệu; `word.meaning` = câu nghĩa đầu tiên; `word.usage` = phần còn lại; `word.definition_ja` = phần sau `……` của đề (đề thường → `null`).
- [ ] **Mỗi lựa chọn**: `sentence.ja` = dòng câu của lời giải; Cách đọc / Nghĩa **trước** "Sửa lại" → `sentence`, **sau** "Sửa lại" → `correction`; mọi dòng nhận xét → `analysis` (đúng thứ tự); không có "Sửa lại" → `correction = null`.
- [ ] `is_correct` chỉ đúng ở đáp án; `usage_ok` đúng như lời giải nói (true / false / null).
- [ ] `correct.index` = `dap_an_so`; `correct.sentence_ja` giống hệt câu của lựa chọn đó; `correct.note` = đoạn chữ khác trong LỰA CHỌN ĐÚNG (nếu có).
- [ ] `{ }` đúng số cặp, đúng chỗ in đậm / gạch chân của lời giải gốc; GPT tự thêm / bỏ sót thì sửa (lỗi GPT).
- [ ] Mọi tiếng Nhật trong câu tiếng Việt được bọc `⟪ ⟫`; furigana `｜…《…》` đúng như bản gốc.
- [ ] Đã làm bước **phản biện 3f** cho cả 4 lựa chọn (phương án nhiễu có dùng được không, lý do loại có tuyệt đối hóa / sai từ loại / sai thực tế không, câu sửa và câu đáp án có tự nhiên không).
- [ ] Soát đủ **3c**, **3d** và mọi gợi ý **3e**, cảnh báo **K15 / K16 / K17**; gắn cờ `nghi_noi_dung` cho mọi chỗ nghi sai nội dung.

## Mẫu file lý do

```json
{
  "sua": [
    {"duong_dan": "$.analysis.options[1].usage_ok", "loai": "sai_so_ban_goc", "muc_do": "nang",
     "ly_do": "lời giải nói câu 2 'cũng là một cách sử dụng đúng' của おかす – usage_ok phải true, GPT để null"},
    {"duong_dan": "$.analysis.options[2].analysis.vi", "loai": "sua_dinh_dang", "nhom": "chinh_ta", "muc_do": "nhe",
     "ly_do": "lỗi chính tả 'chính xát' → 'chính xác'"}
  ],
  "ghi_chu_ban_goc": ["[Đã sửa định dạng] Phân tích lựa chọn 3 – nhận xét: 'chính xát' → 'chính xác' – lỗi chính tả"],
  "nghi_noi_dung": []
}
```

- `loai`: `sai_so_ban_goc` | `chinh_ta` | `khach_quan` | `chu_quan` (lỗi GPT) | `sua_dinh_dang` (lỗi định dạng bản gốc – bắt buộc `nhom` + dòng `[Đã sửa định dạng]`) | `sua_theo_ctv` (sau CTV). `muc_do`: `nghiem_trong` | `nang` | `nhe`. Không dùng `sua_ban_goc` nữa.
- Không có gì thì để `"sua": []`, `"nghi_noi_dung": []`. Xong thì xóa khóa `_huong_dan`.
