# Kế hoạch dựng pipeline – dạng 17 Nghe hiểu: Điểm chính (ĐÃ DUYỆT 08/10/2026 – đã dựng, xem SO_TAY_CHAY.md)

> Soạn 2026-10-08. Chạy **hoàn toàn bằng Claude Opus 5.5 Cowork** (tác tử TẠO = tác tử con `model: opus`, tác tử KIỂM TRA = phiên chính), **không GPT API** – theo mẫu dạng 08/09/11 (`pipeline_chung/CLAUDE_TAO.md`).
> Số liệu dưới đây quét từ `data/17_nghe_hieu_diem_chinh.csv` (1081 câu).

## 1. Dữ liệu – khác gì so với đọc hiểu (11)

| Đặc điểm | Số liệu | Hệ quả cho pipeline |
|---|---|---|
| **Mỗi câu độc lập** (1 bài nghe = 1 câu, `cau_con = 1`), không có đoạn văn chung | 1081 `question_id` khác nhau; `doan_van` chỉ là `<div><br></div>` rác (215 dòng) | Lô theo **câu**, không cần nhóm đoạn; bỏ `doan_van` |
| **Lời thoại tiếng Nhật nằm ở cột `transcript_vi`** (tên cột gây nhầm: chứa bản Nhật) | 1081/1081 có; trung vị 10 dòng, tối đa 22 dòng; ~4.300 nhãn người nói (`男`/`女` 4.000, `M`/`F`/`Ｍ`/`Ｆ` 770, `先生`, `娘`, `A`/`B`, `Q`…) | Nguồn của `full_translation[].lines[].ja` + `speaker` |
| `giai_thich_vi` = **bản dịch Việt từng dòng lời thoại** + câu hỏi + nghĩa 4 lựa chọn, rồi (tùy khuôn) `###` + phần giải thích | 4 dòng cuối là nghĩa lựa chọn: 979/989; có số `1.`…: 822 | Ghép cặp dòng Nhật ↔ dòng Việt là **việc chính** của GĐ1 (khác hẳn 11 vốn chỉ phân tích 4 lựa chọn) |
| `cau_hoi` chỉ có ở 529 câu; câu hỏi còn lại nằm trong dòng đầu / dòng cuối lời thoại | 750 lời thoại kết thúc bằng câu hỏi lặp lại | Python trích `question.ja` (ưu tiên `cau_hoi`, không có thì lấy câu hỏi trong lời thoại) |
| `(i)` đánh dấu chỗ chứa đáp án trong lời thoại | 852 lời thoại, 879 lời giải | Giữ `(i)` trong `full_translation`, bỏ trong `key_info` (như ví dụ mẫu) |
| `<b>` in đậm dòng then chốt | 354 lời thoại, 363 lời giải | Xem **Q4** |
| Furigana `<ruby>` | 26 lời thoại, 23 lời giải | Chuẩn hóa `｜…《…》`, theo quy tắc chung |
| N5/N4 viết cách chữ bằng dấu cách toàn góc | 175 lời thoại | Giữ nguyên; Python so sánh bỏ khoảng trắng |
| `giai_thich_ko`, `transcript_ko` có sẵn | 1081 / 969 | Không dùng (như 07–11) – xem **Q6** |
| Không có phần THAM KHẢO | | Không cần `reference_raw` |

### Khuôn lời giải (phân loại s0)

| Khuôn | Số câu | Nội dung | Ánh xạ |
|---|---|---|---|
| **A – Thông tin** | 697 | Dịch lời thoại + `### Thông tin(:)` + dòng Nhật then chốt + dịch | Đầy đủ: `full_translation` + `key_info`. 649 có cả Nhật–Việt; **43 chỉ có dòng Nhật** (không dịch); 5 kèm câu giải thích thêm |
| **B – Đáp án + lý do** | 174 (+1 dạng "Câu 4 đúng.") | Dịch lời thoại + `### Đáp án đúng là câu số N. Vì …` | `full_translation` + `options[đúng].analysis.vi`; `key_info = []`. 147 câu có số đáp án – **khớp `dap_an_so` 100%** |
| **C – Chỉ dịch** | 117 | Dịch lời thoại + câu hỏi + lựa chọn, không `###` | `full_translation`, `key_info = []`, `analysis = null` |
| **D – Không có tiếng Việt** | 92 (N2: 75) | `giai_thich_vi` chỉ là bản sao lời thoại tiếng Nhật | Không có gì để chuyển – xem **Q2** |

Kiểm tra sơ bộ: dòng Nhật trong "Thông tin" tìm thấy trong lời thoại **901/909 (99%)**; số dòng Việt − số dòng Nhật: bằng nhau 529, lệch ±1–2: 174, lệch ≥ 3: 286 (chủ yếu do bản Việt có thêm câu hỏi + 4 lựa chọn, hoặc tách / gộp câu thoại dài) → cần ghép cặp có kiểm tra, không ghép máy móc theo số thứ tự. Lời thoại có lỗi gõ / OCR (vd 53926 `オリープ`, `作う`) – chỉ gắn cờ khi ảnh hưởng đáp án.

## 2. Schema và ánh xạ

Giữ `reading_listening.v1` (`explanation_schema`), **không thêm trường**. id mẫu = `<question_id>_1`.

| Lời giải gốc | Trường JSON |
|---|---|
| Lời thoại (`transcript_vi`), từng dòng; nhãn trước `：`/`:` | `full_translation = [{label: null, lines: [{speaker, ja, meaning.vi}]}]`; dòng dẫn tình huống / câu hỏi: `speaker = null` |
| Dòng Việt tương ứng trong `giai_thich_vi` (bỏ nhãn "Nam:", "Nữ:", "Sếp:"…) | `lines[i].meaning.vi`; một dòng Nhật dài ứng với nhiều dòng Việt → nối lại; **không cắt / sửa chữ** |
| `cau_hoi` (hoặc câu hỏi trong lời thoại) | `question.ja`; dòng câu hỏi Việt → `question.meaning.vi` |
| `lua_chon_1–4` | `options[i].option_ja`; `reading = null`; 4 dòng Việt cuối (bỏ `1.`) → `options[i].meaning.vi` |
| `dap_an_so` | `options[i].is_match` (đúng 1 lựa chọn `true`); `correct = {index, option_ja, full_sentence: null}`; `quotes = []` |
| Khuôn A: dòng Nhật + dịch sau "Thông tin" | `key_info[] = {speaker, ja (bỏ (i)), meaning.vi}` |
| Khuôn B: "Đáp án … Vì …" | `options[đúng].analysis.vi` (chép nguyên phần lý do) |
| `summary` | `null` (bản gốc không có, không tạo mới) |

## 3. Quy trình (giữ khung 08/09/11)

**GĐ0 – Python `s0_chuan_bi.py`** (tái dùng `normalize.py`, `so_chu.py`… của `pipeline_chung`):
- Chuẩn hóa HTML / ruby, tách dòng lời thoại + nhãn người nói; tách `giai_thich_vi` thành: phần dịch / câu hỏi / 4 lựa chọn / phần sau `###`; phân khuôn A–D.
- **Ghép cặp gợi ý** Nhật ↔ Việt (theo thứ tự + nhãn người nói + dấu hiệu `(i)`, số, tên riêng); xuất cờ `lech_so_dong` khi không ghép 1–1 được → tác tử TẠO tự ghép, tác tử KIỂM TRA soát kỹ.
- `output/thu_tu_chay.csv`: 100 câu đầu = 20 câu mỗi cấp N1–N5 xen kẽ, mỗi cấp có đủ khuôn A/B/C; **lô chuẩn 10 câu**.
- Cờ gợi ý: `khuon_B`, `khuon_C`, `khong_tieng_viet` (D), `thong_tin_khong_dich` (43), `thong_tin_ngoai_loi_thoai`, `lech_so_dong`, `cau_hoi_trong_loi_thoai`, `lua_chon_lech` (dòng Việt cuối ≠ 4), `ruby_hong`, `in_dam`.
- Báo cáo `output/reports/khao_sat_s0.csv`.

**GĐ1 – JSON tiếng Việt**
1. `s1_claude_tao.py --chuan-bi` → gói mỗi câu: lời thoại đã tách dòng (đánh số), các dòng Việt (đánh số), gợi ý ghép cặp, câu hỏi, 4 lựa chọn, đáp án, phần sau `###`, cờ s0.
2. Tác tử TẠO chuyển JSON theo `prompts/s1_claude_tao.md` (+ ví dụ `explanation_schema/examples/17_…json`, bổ sung 1 ví dụ khuôn B, 1 ví dụ lệch số dòng).
3. `--nhan` → `s1_claude_goi.py` → tác tử KIỂM TRA soát bằng `CC/xem_gd1.py` (hiện lời thoại song song Nhật | Việt theo dòng) → file đặc tả lô → `ghi_ly_do.py` → `s1_kiem_tra.py` → `s1_chot.py`.

**Python kiểm tra GĐ1** (ngoài bộ chung: schema, mất tiếng Nhật, độ phủ chữ Việt ≥ 97%, furigana, `⟪ ⟫`):
- LỖI: **K-LT** ghép `full_translation[].lines[].ja` ≠ lời thoại gốc (thiếu / thừa / đảo dòng, so sau khi bỏ khoảng trắng, nhãn, thẻ); `speaker` khác nhãn gốc; dòng có tiếng Việt gốc mà `meaning.vi` rỗng; `correct.index ≠ dap_an_so`; số `is_match = true` ≠ 1; `option_ja` ≠ `lua_chon_i`.
- **Độ phủ Việt theo thứ tự (K-DV):** nối các `meaning.vi` phải phủ phần dịch gốc đúng thứ tự (bắt lỗi ghép lệch dòng / bỏ sót câu).
- CẢNH BÁO: `question.ja` lệch `cau_hoi`; **K-KI** `key_info[].ja` không có trong lời thoại; `key_info` không chứa dòng `(i)` / dòng in đậm; khuôn B số đáp án trong lý do ≠ `dap_an_so`.

**Tiêu chí soát GĐ1 riêng dạng 17** (tác tử KIỂM TRA – chỉ gắn cờ, không sửa nội dung):

| Gắn cờ `nghi_noi_dung` khi | `nhom` đề xuất |
|---|---|
| Dịch sai nghĩa dòng thoại **làm sai / che mất thông tin dẫn tới đáp án** (số, ngày, ai làm gì, phủ định…) | `nghia_cau` |
| Dòng "Thông tin" không chứng minh được đáp án, hoặc chọn sai đoạn | `thong_tin` *(mới)* |
| Lý do khuôn B sai / trái lời thoại | `phan_tich` (dùng chung với 11) |
| Đáp án đáng ngờ so với lời thoại | `dap_an` |
| Lời thoại tiếng Nhật lỗi gõ / OCR làm đổi nghĩa (vd `オリープ`, `作う`) | `loi_thoai` *(mới)* |
| Khuôn D; bản dịch thiếu cả đoạn thoại | `thieu_noi_dung` |

Sửa định dạng (`sua_dinh_dang`): ghép lệch dòng do tác tử TẠO, nhãn người nói dính vào câu, ruby hỏng, dấu thừa.
**Không gắn cờ:** dịch thoát / văn nói tự nhiên nhưng đúng ý; xưng hô (cậu/tớ, anh/em) khác nhau giữa các dòng; tên riêng phiên âm khác nhau (Yamada / Yamađa); bản dịch gộp hai câu thoại ngắn.

**GĐ2 – tiếng Hàn** (chỉ câu đã chốt, không cờ): `s2_claude_dich.py --chuan-bi` → tác tử TẠO dịch → `--nhan` → soát `CC/xem_gd2.py` → `s2_kiem_tra.py`. Điểm riêng:
- **Dịch lời thoại từ tiếng Nhật** (bản Việt chỉ để tham khảo ý), giữ số dòng, `speaker`, `(i)`; văn phong hội thoại tự nhiên, **giữ mức kính ngữ của bản Nhật** (です/ます → 존댓말, thể thường → 반말); dòng dẫn / câu hỏi → văn viết -ㅂ니까 / -습니다; `analysis` → -습니다.
- Python D-check riêng: số dòng KO = số dòng; `key_info[].meaning.ko` phải **trùng** bản Hàn của dòng tương ứng trong `full_translation` (dịch một lần, Python chép sang – tiết kiệm token); số / giờ / ngày trong `ja` phải xuất hiện trong `ko`.
- `glossary_ko.json` thêm: nhãn người nói hay gặp nếu cần hiển thị (男 → 남자, 女 → 여자, 先生 → 선생님…), 聴解 → 청해, ポイント → 포인트.

**GĐ3 – Excel CTV**: `s3_xuat_ctv.py` (ĐẠT → CTV tiếng Hàn) và `s3b_xuat_ctv_nhat.py` (có cờ → CTV tiếng Nhật). Cột "Ngữ liệu" = lời thoại dạng bảng 3 cột **Người nói | Nhật | Việt/Hàn**, dòng `key_info` tô nền; sau đó câu hỏi, 4 lựa chọn, đáp án, lý do.

## 4. File sẽ tạo trong thư mục dạng 17

`config.json`, `glossary_ko.json`, `schema/` (bản sao `reading_listening.v1` + bản api), `scripts/` (`_dang.py`, `_dau_vao.py`, `s0_chuan_bi.py`, `s1_claude_tao.py`, `s1_claude_goi.py`, `s1_kiem_tra.py`, `s1_chot.py`, `s2_claude_dich.py`, `s2_claude_goi.py`, `s2_kiem_tra.py`, `s3_xuat_ctv.py`, `s3b_xuat_ctv_nhat.py`, `s9_bao_cao.py`, `s10_luu_da_duyet.py`; `s1_gpt_chuyen.py` / `s2_dich.py` chỉ báo lỗi "dạng 17 không dùng GPT"), `prompts/` (`s1_claude_tao.md`, `s1_claude_kiem_tra.md`, `s2_claude_dich.md`, `s2_claude_kiem_tra.md`, `giao_viec_tao_gd1.md`, `giao_viec_tao_gd2.md`), `SO_TAY_CHAY.md`, `NHAT_KY.md`, `HUONG_DAN_CHAY.md`, cập nhật `README.md`.

**Phần dùng chung với dạng 11 / 16 / 18–21** (cùng `reading_listening.v1`): bộ tách lời thoại + ghép cặp + K-LT / K-DV viết thành module có thể chuyển sang `pipeline_chung/` sau khi pilot ổn, để dạng 16, 18–21 tái dùng.

**Cần sửa code chung** (làm ở cuộc trò chuyện điều phối): thêm `thong_tin`, `loi_thoai` (và `phan_tich` nếu 11 chưa thêm) vào `claude_log.NHOM_NOI_DUNG`; `checks_chung` / `schema_tools` duyệt đúng `Line` / `full_translation`; `CC/xem_gd1.py`, `xem_gd2.py` hiện lời thoại song song; cập nhật `pipeline_chung/CLAUDE_TAO.md`.

## 5. Lộ trình

| Bước | Việc | Đầu ra để duyệt |
|---|---|---|
| 1 | Dựng s0: tách dòng, ghép cặp gợi ý, phân khuôn, cờ | `khao_sat_s0.csv` + tỷ lệ ghép 1–1 thành công |
| 2 | Prompt + script GĐ1, pilot **lô 1 = 10 câu** (đủ N1–N5, ≥ 2 khuôn B, 1 khuôn C, 1 câu lệch số dòng, 1 câu khuôn D) | JSON VI + file lý do + bảng cờ |
| 3 | Anh duyệt pilot GĐ1 → chỉnh prompt / tiêu chí | ghi `NHAT_KY.md` |
| 4 | GĐ2 pilot + Excel CTV mẫu (2 file) | Excel |
| 5 | Viết `SO_TAY_CHAY.md`, chạy lô thường, tối đa 3 lô / cuộc trò chuyện | — |

Ước tính chi phí tác tử TẠO: một câu ≈ lời thoại 10–15 dòng × (Nhật + Việt) → JSON dài gấp ~2 dạng 08; **≈ 200–300k token mỗi giai đoạn cho lô 10 câu** (đo lại ở pilot). Nếu quá nặng: hạ lô xuống 8 câu, hoặc để Python ghép sẵn các câu khớp 1–1 và tác tử TẠO chỉ xử lý phần còn lại.

## 6. Cần anh duyệt

- **Q1 – Lô:** 10 câu / lô, 100 câu đầu xen kẽ 20 câu mỗi cấp N1–N5?
- **Q2 – Khuôn D (92 câu, không có tiếng Việt):** (a) tạo JSON chỉ có tiếng Nhật, `meaning.vi = null`, gắn cờ `thieu_noi_dung` → CTV tiếng Nhật dịch bổ sung; hay (b) bỏ hẳn, chỉ liệt kê danh sách? *Đề xuất: (b) – chuyển thẳng danh sách cho CTV, không tốn tác tử.*
- **Q3 – "Thông tin" chỉ có dòng Nhật (43 câu) và khuôn C (117 câu, không có Thông tin):** cho Python lấy `meaning.vi` của dòng tương ứng trong `full_translation` (chép nội dung gốc, không tạo mới) để điền `key_info`? Riêng khuôn C có cho tác tử TẠO chọn dòng then chốt (dòng `(i)` / in đậm) làm `key_info` không, hay để `[]`? *Đề xuất: 43 câu → Python chép; khuôn C → chỉ lấy dòng có `(i)` nếu duy nhất, còn lại `[]`, không gắn cờ.*
- **Q4 – In đậm `<b>` (≈360 câu):** trong nghe hiểu, in đậm = đánh dấu dòng then chốt (trùng chức năng `(i)` / Thông tin). Áp quy tắc chung 3a (đổi thành `{ }`) hay **bỏ in đậm** và chỉ dùng làm gợi ý cho `key_info`? *Đề xuất: bỏ, chỉ dùng làm gợi ý.*
- **Q5 – Nhãn người nói:** giữ nguyên nhãn gốc (`男`, `女`, `上司`, `M`, `Ｆ`) hay chuẩn hóa (`男/M/Ｍ` → `M`, `女/F/Ｆ` → `F` như ví dụ mẫu 13594, nhãn khác giữ)? Bản Việt "Nam/Nữ/Sếp" bỏ.
- **Q6 – `transcript_ko` / `giai_thich_ko` có sẵn:** không dùng (như các dạng trước), hay đưa làm tham khảo cho tác tử TẠO GĐ2 (nhất là tên riêng, cách xưng hô)?
- **Q7 – Hai nhóm cờ mới** `thong_tin`, `loi_thoai` (sửa `pipeline_chung/claude_log.py`).
- **Q8 – Lỗi gõ / OCR trong lời thoại Nhật:** chỉ gắn cờ `loi_thoai` khi ảnh hưởng đáp án, còn lỗi nhẹ bỏ qua (không sửa văn bản đề)?
