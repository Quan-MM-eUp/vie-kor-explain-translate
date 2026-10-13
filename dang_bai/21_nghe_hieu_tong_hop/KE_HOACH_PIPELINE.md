# Kế hoạch dựng pipeline – dạng 21 Nghe hiểu: Nghe hiểu tổng hợp (ĐÃ DUYỆT 08/10/2026 – đã dựng, xem NHAT_KY.md mục "Quyết định đã chốt")

> Soạn 2026-10-08. Chạy **hoàn toàn bằng Claude Opus 5.5 Cowork** (tác tử TẠO = tác tử con `model: opus`, tác tử KIỂM TRA = phiên chính), **không GPT API** – theo mẫu dạng 08/09 (`pipeline_chung/CLAUDE_TAO.md`) và khung kế hoạch dạng 11/16.
> Số liệu quét từ `data/21_nghe_hieu_tong_hop.csv` (128 dòng). Dạng 21 cùng schema `reading_listening.v1` với 16 → **dùng chung tối đa với 16** (xem Q8).

## 1. Dữ liệu – khác gì so với 16 (nghe hiểu chủ đề)

| Đặc điểm | Số liệu | Hệ quả cho pipeline |
|---|---|---|
| 128 câu = **114 bài nghe**: 100 bài 1 câu hỏi + **14 bài 2 câu hỏi** (質問1 / 質問2, kiểu 3番 JLPT) | chỉ N1 64, N2 64 | Đơn vị chạy = **bài nghe** (không cắt đôi bài 2 câu hỏi, như đoạn văn 09) |
| **Bài dài**: lời thoại trung vị 562 ký tự (tối đa 1.383), lời giải trung vị **4.235 ký tự** (tối đa 8.383) – gấp ~2,5 lần dạng 16 | tổng lời giải ≈ 495k ký tự | Lô nhỏ: **5 bài ≈ 6 câu** |
| Lời thoại JA ở cột `transcript_vi` (tên cột sai); cuối lời thoại có câu hỏi + 4 lựa chọn (51 câu) | | Python cắt phần câu hỏi / lựa chọn, lấy câu hỏi làm `question.ja` khi `cau_hoi` rỗng (65 câu) |
| **Bài 2 câu hỏi: lời thoại bị chia lệch** – N2: câu con 1 rỗng, câu con 2 chứa toàn bộ; N1: câu con 1 chứa toàn bộ, câu con 2 chỉ có 質問2; 53921 câu con 2 rỗng cả lời thoại lẫn lời giải | 14 bài | s0 **gộp lời thoại theo `question_id`**; `full_translation` giống nhau ở 2 câu con |
| `doan_van` (37 câu) chỉ là lời dẫn đề "3番 まず話を聞いてください…" – không phải ngữ liệu | | Bỏ qua, không đưa vào JSON |
| `giai_thich_vi` khuôn **A** = [bản dịch VI lời thoại] + `###` + [phân tích 1–4: `Nghĩa:` / `Phân tích đoạn hội thoại:` / `Nam nói: 「…」 (dịch)` / `→ ĐÚNG/SAI` / kết luận] | **86 câu (67%)** | Ánh xạ sạch vào `options[]` như ví dụ mẫu |
| Khuôn **B** "Thông tin:" = đề cả 2 câu hỏi + đoạn thoại then chốt JA + bản dịch, đánh dấu `(i)` / `(ii)` cho câu hỏi 1 / 2; **không** phân tích từng lựa chọn | 9 câu (bài 2 câu hỏi N2) | Đoạn then chốt → `key_info` (đúng mô tả schema "khuôn Thông tin"); `options[].analysis = null` + cờ `thieu_noi_dung` |
| Khuôn **C**: chỉ có bản dịch VI lời thoại + câu hỏi + lựa chọn (10 câu N1), hoặc chỉ chép lại lời thoại JA (22 câu); 1 câu rỗng | **33 câu (26%)** | JSON từ phần có được + cờ `thieu_noi_dung` → CTV tiếng Nhật |
| Ghép dòng JA ↔ VI: số dòng bằng nhau chỉ **25/86** câu khuôn A; khớp chuỗi người nói 45/86 | | **Khác 16**: Python chỉ tự ghép khi khớp hoàn toàn; còn lại tác tử TẠO ghép (xem Q2) |
| Trích dẫn 「…」 trong phân tích: 713 câu trích – khớp nguyên văn lời thoại 90%, khớp một phần 6%, không tìm thấy 4% | | K-TD = CẢNH BÁO (so mờ) |
| **Lỗi gõ trong lời thoại JA gốc** dày: `明、月曜日` (明日), `フ降り`, `水曜日はもり` (くもり), `散っちゃんう`, `江エビ`, `お店んの` – câu trích trong phân tích thường đã viết đúng | | Xem Q5 |
| Ký hiệu `(i)` / `(ii)` trong lời thoại | 82 câu (bản dịch VI chỉ 9 câu có) | Giữ nguyên trong `ja` (như ví dụ mẫu) – xem Q4 |
| `<b>` trong lời thoại | 95 câu | Bỏ thẻ (đánh dấu dòng, không phải gạch chân) – xem Q4 |
| Lựa chọn chỉ là số (`1`…`4`, chọn theo danh sách in trên đề) | 11 câu | `option_ja` giữ nguyên, `meaning` lấy từ phân tích nếu có |
| Lỗi dữ liệu đề | 12310: 2 lựa chọn `→ ĐÚNG`; 53342, 53343: thiếu `lua_chon_4` | Cờ s0 `nhieu_dung`, `lua_chon_thieu` → gắn cờ `dap_an` / báo anh |
| Furigana: ruby trong phân tích 86 câu; lời thoại không có | | Furigana ở đâu giữ ở đó (mục 8 workflow) |
| THAM KHẢO | 2 câu (12510, 53511) | Áp quy tắc mục 11 nếu đúng là phần tham khảo |
| `giai_thich_ko` (104 câu có chữ Hàn), `transcript_ko` | | Không dùng (như 07–16) |

## 2. Schema và ánh xạ

Giữ `reading_listening.v1`, **không thêm trường**. id mẫu = `<question_id>_<cau_con>`. Ví dụ mẫu `explanation_schema/examples/21_nghe_hieu_tong_hop.json` khớp khuôn A (sẽ chỉnh theo quyết định Q4/Q5).

| Lời giải gốc | Trường JSON | Ai điền |
|---|---|---|
| Lời thoại JA (gộp theo bài, bỏ câu hỏi / lựa chọn cuối) + bản dịch VI | `full_translation = [{label: null, lines: [{speaker, ja, meaning.vi}]}]` | Python khi khớp dòng; **tác tử TẠO** khi lệch |
| Dòng dẫn chuyện (`大学生がテレビを見て…`) | `lines[0].speaker = null` | Python / tác tử TẠO |
| Nhãn `男/女/M/F/女２/講師…` | `speaker` (giữ nguyên từ JA); nhãn `Nam:/Nữ:` bỏ khỏi `meaning.vi` | Python |
| Câu hỏi | `question.ja` (`cau_hoi` hoặc câu cuối lời thoại; `質問1` thì lấy câu đầy đủ), `question.meaning.vi` | Python đề xuất, tác tử TẠO xác nhận |
| `1. …` + `Nghĩa:` | `option_ja` (= `lua_chon_i`), `reading = null`, `meaning.vi` | Python + tác tử TẠO |
| `Nam nói: 「…」 (dịch)` | `quotes[] = {ja, meaning.vi}`; nhãn dẫn ("Nam nói:", "Nữ hỏi:") không chép (Q6) | tác tử TẠO |
| Câu nối giữa các trích dẫn + kết luận sau `→` | `analysis.vi` (từ Nhật chen giữa bọc `⟪ ⟫`) | tác tử TẠO |
| `→ ĐÚNG/SAI` | `is_match` | tác tử TẠO |
| Khuôn B "Thông tin:" | `key_info = [Line…]` (đoạn then chốt JA + dịch); bài 2 câu hỏi: câu con 1 lấy phần đến `(i)`, câu con 2 lấy phần quanh `(ii)` (Q3) | tác tử TẠO |
| Đáp án | `correct = {index: dap_an_so, option_ja, full_sentence: null}` | Python |
| — | `summary = null` | Python |

**Tiết kiệm token:** bài 2 câu hỏi chỉ ghép `full_translation` **một lần** cho câu con 1, Python chép sang câu con 2.

## 3. Quy trình (khung 08/09/16)

**GĐ0 – Python `s0_chuan_bi.py`**
- Làm sạch HTML (`\&quot;JA\&quot;`, `&nbsp;`, `<b>`), ruby → `｜…《…》`; gộp lời thoại theo `question_id`; cắt câu hỏi / lựa chọn cuối lời thoại.
- Tách `giai_thich_vi` → bản dịch / phân tích 1–4 / Thông tin / tham khảo; phân loại khuôn A / B / C-vi / C-ja / rỗng.
- Thử ghép dòng JA ↔ VI (số dòng + chuỗi người nói); ghi kết quả `ghep_dong = tu_dong / can_tao`.
- `output/thu_tu_chay.csv` theo bài nghe, N1 / N2 xen kẽ, **lô chuẩn 5 bài (≈ 6 câu)**; bài 2 câu hỏi luôn đi cùng nhau.
- Cờ gợi ý: `khuon_B`, `khuon_C`, `lech_dong`, `nhieu_dung`, `lua_chon_thieu`, `trich_dan_ngoai_loi_thoai`, `loi_go_loi_thoai`, `chen_tu_nhat`, `ruby_hong`, `tham_khao`.
- Báo cáo `output/reports/khao_sat_s0.csv`.

**GĐ1 – JSON tiếng Việt**
1. `s1_claude_tao.py --chuan-bi` → gói **theo bài**: lời thoại JA đánh số dòng, bản dịch VI, (bản ghép sẵn nếu có), câu hỏi, 4 lựa chọn, đáp án, phần phân tích đã chuẩn hóa, cờ s0.
2. Tác tử TẠO chuyển JSON theo `prompts/s1_claude_tao.md` (+ ví dụ mẫu).
3. `--nhan` (Python điền `correct`, `summary`, chép `full_translation` sang câu con 2) → `s1_claude_goi.py` → tác tử KIỂM TRA soát bằng `CC/xem_gd1.py` (lời thoại song ngữ 1 lần / bài) → file đặc tả lô → `ghi_ly_do.py` → `s1_kiem_tra.py` → `s1_chot.py`.

**Python kiểm tra GĐ1** (ngoài bộ chung: schema, mất tiếng Nhật, độ phủ chữ Việt ≥ 97%, `{ }`, furigana, `⟪ ⟫`):
- LỖI: `correct.index ≠ dap_an_so`; số `is_match = true` ≠ 1 hoặc không trùng đáp án (trừ câu có cờ `dap_an`); thiếu lựa chọn; **ghép `lines[].ja` lại ≠ lời thoại gốc** (mất / thêm / sửa chữ); **ghép `lines[].meaning.vi` phủ < 97% bản dịch gốc**; 2 câu con cùng bài khác `full_translation`.
- CẢNH BÁO: K-TD `quotes[].ja` không có trong lời thoại; K-NQ nghĩa câu trích lệch hẳn dòng tương ứng; `question.ja` không có trong lời thoại / đề; `key_info.ja` không có trong lời thoại.

**Tiêu chí soát GĐ1 riêng dạng 21** (chỉ gắn cờ – không sửa nội dung):

| Gắn cờ `nghi_noi_dung` khi | `nhom` |
|---|---|
| Bản dịch lời thoại sai nghĩa / thiếu câu / nhầm người nói; ghép dòng JA ↔ VI lệch | `nghia_cau` |
| Câu trích không có trong lời thoại / không chứng minh được điều phân tích nói | `trich_dan` *(chung 11/16)* |
| Phân tích trái lời thoại, **nhất là suy luận nhiều bước** (so sánh điều kiện, loại trừ – đặc thù 統合理解) | `phan_tich` *(chung 11/16)* |
| Kết luận ĐÚNG/SAI trái đáp án; nhiều ĐÚNG (12310) | `dap_an` |
| Khuôn B / C – thiếu phân tích lựa chọn | `thieu_noi_dung` |

Sửa định dạng (`sua_dinh_dang`): lỗi gõ trong lời giải VI, nhãn dính dòng, rác HTML, `⟪ ⟫` / furigana lệch.
**Không gắn cờ:** phân tích sơ sài nhưng không sai; dịch vụng nhưng đúng ý; câu trích sửa đúng lỗi gõ của lời thoại (chỉ ghi chú).

**GĐ2 – tiếng Hàn** (như 16): gói theo bài; `full_translation` dịch văn nói (kính ngữ / 반말 theo JA), `analysis` -습니다; câu trích trùng dòng lời thoại dịch giống nhau (D4); bài 2 câu hỏi: dịch `full_translation` **một lần**, Python chép sang câu con 2; `glossary_ko.json` dùng chung bản nghe hiểu của 16 + thuật ngữ riêng (質問 → 질문, 説明会 → 설명회, コース → 코스…).

**GĐ3 – Excel CTV**: như 16 – mỗi bài một khối (lời thoại song ngữ dạng bảng, rồi từng câu hỏi); CTV tiếng Nhật nhận câu có cờ + toàn bộ khuôn B / C.

## 4. File sẽ tạo trong thư mục dạng 21

`config.json` (`thu_tu_chay.lo` theo bài = 5), `glossary_ko.json`, `schema/` (bản sao + bản api – bản api **giữ** `full_translation` vì tác tử TẠO ghép phần lệch dòng), `scripts/` (bộ như 16: `_dang.py`, `_dau_vao.py`, `s0…s10`; `s1_gpt_chuyen.py` / `s2_dich.py` chỉ báo lỗi), `prompts/` (6 file như 09), `SO_TAY_CHAY.md`, `NHAT_KY.md`, `HUONG_DAN_CHAY.md`, cập nhật `README.md`.

**Phụ thuộc code chung** (làm ở cuộc trò chuyện điều phối, không ở phiên chạy dạng): nhóm cờ `trich_dan`, `phan_tich` trong `claude_log.NHOM_NOI_DUNG`; `checks_chung` / `schema_tools` duyệt `Line` / `Quote`; `xem_gd1.py` / `xem_gd2.py` hiện hội thoại dạng bảng + gom theo bài; `pipeline_chung/nghe_hieu.py` (đề xuất ở 16 Q7). **Nếu 16 chưa dựng**, các phần này làm luôn khi dựng 21.

## 5. Lộ trình

| Bước | Việc | Đầu ra để duyệt |
|---|---|---|
| 1 | s0 + khảo sát (khuôn, ghép dòng, gộp bài 2 câu hỏi, lỗi gõ lời thoại) | `khao_sat_s0.csv`, tóm tắt |
| 2 | Prompt + script GĐ1, pilot **lô 1 = 5 bài**: 2 bài N1 + 2 bài N2 khuôn A (≥ 1 lệch dòng), 1 bài 2 câu hỏi khuôn B | JSON VI + file lý do + bảng cờ |
| 3 | Anh duyệt pilot → chỉnh prompt / tiêu chí | `NHAT_KY.md` |
| 4 | GĐ2 pilot + Excel CTV mẫu | Excel 2 file |
| 5 | `SO_TAY_CHAY.md`; chạy lô thường, tối đa 3 lô / cuộc trò chuyện | ≈ 23 lô |

Ước tính token tác tử TẠO: **≈ 250–350k / lô (6 câu) GĐ1** (ghép dòng chiếm phần lớn khi lệch), **≈ 250–350k GĐ2**; đo lại ở pilot. Toàn dạng ≈ 23 lô × 2 giai đoạn.

## 6. Cần anh duyệt

- **Q1 – Lô:** theo bài nghe, 5 bài (~6 câu) / lô, N1 / N2 xen kẽ, bài 2 câu hỏi không tách?
- **Q2 – Ghép dòng JA ↔ VI:** Python ghép khi khớp (≈ 25–45 / 86 câu), còn lại tác tử TẠO ghép; Python bắt buộc ghép lại = nguyên văn lời thoại?
- **Q3 – Khuôn B "Thông tin:" (9 câu):** đưa đoạn then chốt vào `key_info`, chia theo `(i)` / `(ii)` cho từng câu con, + cờ `thieu_noi_dung`? Khuôn C (33 câu): JSON từ phần có được + cờ; riêng **22 câu chỉ có lời thoại JA** – tác tử TẠO **dịch mới** lời thoại hay để `meaning = null`?
- **Q4 – `(i)` / `(ii)` và `<b>` trong lời thoại:** giữ `(i)` trong `ja` (như ví dụ mẫu), bỏ `<b>`? (Theo quyết định 16 nếu đã có.)
- **Q5 – Lỗi gõ trong lời thoại JA gốc** (`フ降り`, `もり`, `江エビ`…): giữ nguyên + ghi chú CTV, hay `sua_dinh_dang` (nhóm `chinh_ta`) khi câu trích trong lời giải đã có bản đúng?
- **Q6 – Nhãn người nói trong trích dẫn** ("Nam nói:", "Nữ hỏi:"): `Quote` không có trường người nói → bỏ, hay đưa vào đầu `analysis` (vd "Nam nói ⟪…⟫")? Bỏ thì mất thông tin ai nói – quan trọng ở bài nhiều người.
- **Q7 – 53921 câu con 2** (rỗng lời thoại + lời giải) và **53342/53343 thiếu `lua_chon_4`**: bỏ qua + báo, hay anh sửa dữ liệu gốc trước?
- **Q8 – Dùng chung với 16:** dựng 21 **sau** 16 và dùng lại `nghe_hieu.py`, `glossary_ko`, `xem_gd*` (đề xuất), hay dựng 21 độc lập ngay?
- **Q9 – `giai_thich_ko`:** không dùng (như 07–16)?
