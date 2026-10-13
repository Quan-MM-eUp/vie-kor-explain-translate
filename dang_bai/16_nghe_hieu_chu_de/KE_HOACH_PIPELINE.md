# Kế hoạch dựng pipeline – dạng 16 Nghe hiểu: Nghe hiểu chủ đề (ĐÃ DUYỆT 2026-10-08 – đã dựng, xem NHAT_KY.md)

> Soạn 2026-10-08. Chạy **hoàn toàn bằng Claude Opus 5.5 Cowork** (tác tử TẠO = tác tử con `model: opus`, tác tử KIỂM TRA = phiên chính), **không GPT API** – theo mẫu dạng 08/09 (`pipeline_chung/CLAUDE_TAO.md`) và khung kế hoạch dạng 11.
> Số liệu dưới đây quét từ `data/16_nghe_hieu_chu_de.csv` (1084 dòng).

## 1. Dữ liệu – khác gì so với 07–09 và 11

| Đặc điểm | Số liệu | Hệ quả cho pipeline |
|---|---|---|
| 1084 câu, **mỗi câu = 1 bài nghe riêng** (không có câu con, `question_id` không trùng) | N5 340, N3 228, N2 195, N1 179, N4 142 | Lô theo **câu**, không cần gom nhóm như 09/11 |
| **Lời thoại tiếng Nhật nằm ở cột `transcript_vi`** (tên cột sai nghĩa); trung vị 9 dòng / 240 ký tự, tối đa 27 dòng | 913 câu | Python lấy lời thoại JA từ cột này |
| 171 câu có `doan_van`: ở đây `doan_van` mới là lời thoại JA, còn `transcript_vi` bị dán nhầm phần phân tích (52) hoặc bản dịch Việt (46) | | s0 chọn nguồn lời thoại theo luật (cột nào là tiếng Nhật và không chứa `→ ĐÚNG/SAI`); cờ `nguon_loi_thoai` |
| 238 lời thoại có **danh sách lựa chọn** dán ở cuối (`1. 会議の資料をまとめる …`) | | Python cắt ra, không đưa vào `full_translation` |
| `giai_thich_vi` = **[bản dịch Việt lời thoại] + `###` + [phân tích 1–4]** | 1018 câu có bản dịch; 925 câu đủ khuôn phân tích | Ánh xạ sạch vào `reading_listening.v1` |
| Số đoạn `<p>` bản dịch VI = số đoạn lời thoại JA | 1041 / 1084 | **Python tự ghép từng dòng JA ↔ VI** vào `full_translation`; chỉ câu lệch dòng mới giao tác tử TẠO ghép |
| **Lựa chọn là tranh** (`lua_chon_i` = "1".."4") | **512 câu (47%)** – N5 200, N2 122, N4 107, N3 83 | `option_ja` = "1".."4", `meaning = null`; phân tích mô tả tranh **không kiểm chứng được** (không có ảnh trong dữ liệu) |
| Lựa chọn chữ: nghĩa lấy từ dòng `Nghĩa:` (44 câu) hoặc từ phần dịch danh sách lựa chọn trong bản dịch | | `options[i].meaning.vi` |
| `cau_hoi` gần như rỗng (260 câu có) | | `question.ja` = câu hỏi lặp ở cuối lời thoại (hoặc câu thứ 2 của dòng mở đầu); `meaning.vi` = dòng tương ứng trong bản dịch |
| Trích dẫn 「…」(dịch) trong phân tích: 5847 câu trích; **93% khớp nguyên văn lời thoại** | trung vị 6 trích / câu | `options[i].quotes[]`; kiểm tra khớp = CẢNH BÁO |
| **Khuôn lạ 159 câu (15%)** không có `→ ĐÚNG`: 124 chỉ có bản dịch lời thoại, 35 chỉ chép lại lời thoại JA; thêm 40 câu đủ phân tích nhưng thiếu `###` | N1 50, N4 46 | Tạo JSON từ phần có được + cờ `thieu_noi_dung` → CTV tiếng Nhật |
| Lệch đáp án: 3; số `→ SAI` ≠ 3: 4 | | Cờ s0 `lech_dap_an`, `nhieu_dung` |
| Ký hiệu `(i)` trong lời thoại | 869 câu (≈1 lần / câu); bản dịch VI có ở 271 câu | Giữ nguyên trong `ja` (như ví dụ mẫu) – xem Q4 |
| `<b>` đánh dấu câu then chốt trong lời thoại / bản dịch | 260 / 268 câu | Theo mục 3a → `{ }`; xem Q5 |
| Furigana: lời thoại JA hầu như không có (84 câu); **câu trích trong phân tích có ruby (928 câu)** | | Furigana ở đâu giữ ở đó (mục 8); lời thoại không thêm furigana |
| HTML rác: `span lang="\&quot;JA\&quot;"`, `MsoNormal`, `&nbsp;` (109 câu), dấu cách toàn góc | | `normalize.py` + bước làm sạch riêng ở s0 |
| `transcript_ko` (951 câu có) gần như rác – chỉ 63 câu có chữ Hàn; `giai_thich_ko` có đủ | | Không dùng (như 07–11) |
| THAM KHẢO | 6 câu | Áp quy tắc mục 11 (`reference_raw`) nếu đúng là phần tham khảo; không thì bỏ qua |

## 2. Schema và ánh xạ

Giữ `reading_listening.v1`, **không thêm trường** (thêm `reference_raw` chỉ nếu 6 câu THAM KHẢO là thật). id mẫu = `<question_id>` (`cau_con` luôn = 1). Ví dụ mẫu: `explanation_schema/examples/16_nghe_hieu_chu_de.json` (sẽ sửa lại cho khớp quyết định Q3–Q5).

| Lời giải gốc | Trường JSON | Ai điền |
|---|---|---|
| Lời thoại JA (từng dòng, bỏ danh sách lựa chọn cuối) + bản dịch VI tương ứng | `full_translation = [{label: null, lines: [{speaker, ja, meaning.vi}]}]` | **Python** (khớp dòng); tác tử TẠO khi lệch dòng |
| Nhãn người nói `男/女/F/M/A/B/先生…` | `lines[].speaker` (lấy từ dòng JA, giữ nguyên); dòng dẫn chuyện `speaker = null`; nhãn `Nam:/Nữ:` bỏ khỏi `meaning.vi` | Python |
| Câu hỏi | `question.ja`, `question.meaning.vi` | Python đề xuất, tác tử TẠO xác nhận |
| `1. …` | `options[i].option_ja` (= `lua_chon_i`), `reading = null` | Python |
| `Nghĩa: …` / dòng dịch lựa chọn trong bản dịch | `options[i].meaning.vi`; lựa chọn tranh → `null` | tác tử TẠO |
| 「câu Nhật」(dịch) | `options[i].quotes[] = {ja, meaning.vi}` – nhãn dẫn ("Giáo viên nói:", "Tiếp theo:") không chép | tác tử TẠO |
| Phần nhận xét còn lại (kể cả mô tả tranh) | `options[i].analysis.vi`; từ Nhật chen giữa bọc `⟪ ⟫` | tác tử TẠO |
| `→ ĐÚNG` / `→ SAI` | `options[i].is_match` | tác tử TẠO |
| Đáp án | `correct = {index: dap_an_so, option_ja, full_sentence: null}` | Python |
| — | `summary = null`, `key_info = null` (không tạo nội dung mới) | Python |
| Khuôn lạ | `full_translation` từ phần có được; `options[i].quotes = []`, `analysis = null` + cờ `thieu_noi_dung` | Python + tác tử TẠO |

**Tiết kiệm token:** `full_translation` chiếm ~40% nội dung mỗi câu nhưng là ghép dòng máy móc → Python điền qua hook `bo_sung` của `claude_tao.gd1_nhan` (như `passage` dạng 09). Tác tử TẠO chỉ nhận lời thoại để đọc ngữ cảnh, chỉ trả `question` + `options`.

## 3. Quy trình (giữ nguyên khung 08/09)

**GĐ0 – Python `s0_chuan_bi.py`** (tái dùng `normalize.py`, `so_chu.py`, `tham_khao.py` của `pipeline_chung`):
- Chọn nguồn lời thoại (`transcript_vi` / `doan_van`), làm sạch HTML, ruby → `｜…《…》`, `<b>/<u>` → `{ }`.
- Tách `giai_thich_vi` thành 3 phần: bản dịch lời thoại / phân tích 1–4 / tham khảo; phân loại khuôn **A** (dịch + phân tích), **B** (phân tích, thiếu `###`), **C** (chỉ bản dịch), **D** (chỉ lời thoại JA), **F** (khác).
- Ghép dòng JA ↔ VI, tách nhãn người nói, cắt danh sách lựa chọn → `full_translation` dựng sẵn.
- `output/thu_tu_chay.csv`: 100 câu đầu xen kẽ N1–N5 (20 câu / cấp), trộn lựa chọn tranh / chữ; **lô chuẩn 10 câu**.
- Cờ gợi ý: `khuon_la`, `lech_dap_an`, `nhieu_dung`, `nguon_loi_thoai`, `lech_dong`, `lua_chon_tranh`, `trich_dan_ngoai_loi_thoai`, `chen_tu_nhat`, `ruby_hong`.
- Báo cáo `output/reports/khao_sat_s0.csv`.

**GĐ1 – JSON tiếng Việt**
1. `s1_claude_tao.py --chuan-bi` → gói đầu vào mỗi câu: lời thoại JA đã làm sạch (đánh số dòng), bản dịch VI, câu hỏi, 4 lựa chọn (đánh dấu tranh/chữ), đáp án, phần phân tích đã chuẩn hóa, cờ s0.
2. Tác tử TẠO chuyển JSON theo `prompts/s1_claude_tao.md` (+ ví dụ mẫu đã sửa).
3. `--nhan` (Python điền `full_translation`, `correct`, `summary/key_info = null`) → `s1_claude_goi.py` → tác tử KIỂM TRA soát bằng `CC/xem_gd1.py` (hiện lời thoại song ngữ 1 lần + 4 lựa chọn) → file đặc tả lô → `ghi_ly_do.py` → `s1_kiem_tra.py` → `s1_chot.py`.

**Python kiểm tra GĐ1** (ngoài bộ chung: schema, mất tiếng Nhật, độ phủ chữ Việt ≥ 97%, `{ }`, furigana, `⟪ ⟫`):
- LỖI: `correct.index ≠ dap_an_so`; số `is_match = true` ≠ 1 hoặc không trùng `correct.index` (trừ câu có cờ `dap_an`); thiếu lựa chọn; `full_translation` mất dòng so với lời thoại gốc; `lines[].ja` khác nguyên văn lời thoại.
- CẢNH BÁO: **K-TD** `quotes[].ja` không có trong lời thoại (so mờ, bỏ furigana / dấu câu / khoảng trắng); **K-NQ** nghĩa câu trích lệch hẳn nghĩa dòng tương ứng trong `full_translation`; `question.ja` không có trong lời thoại; lựa chọn tranh mà `meaning ≠ null`.

**Tiêu chí soát GĐ1 riêng dạng 16** (tác tử KIỂM TRA, chỉ gắn cờ – không sửa nội dung):

| Gắn cờ `nghi_noi_dung` khi | `nhom` đề xuất |
|---|---|
| Bản dịch lời thoại sai nghĩa / thiếu câu / dịch nhầm người nói | `nghia_cau` |
| Câu trích không có trong lời thoại, hoặc không chứng minh được điều phân tích nói | `trich_dan` *(dùng chung với 11)* |
| Phân tích trái nội dung lời thoại (vd nói "không nhắc đến" nhưng có) | `phan_tich` *(dùng chung với 11)* |
| Kết luận ĐÚNG/SAI trái đáp án, nhiều lựa chọn ĐÚNG | `dap_an` |
| Khuôn lạ C/D – thiếu phân tích các lựa chọn | `thieu_noi_dung` |

Sửa định dạng (`sua_dinh_dang`): lỗi gõ, nhãn dính dòng, rác HTML/`&nbsp;` còn sót, `⟪ ⟫` / furigana lệch.
**Không gắn cờ:** mô tả tranh (không kiểm chứng được) trừ khi tự mâu thuẫn với lời thoại; phân tích sơ sài nhưng không sai; dịch vụng nhưng đúng ý; lỗi gõ trong lời thoại JA gốc (vd `わかしました`) – chỉ ghi chú, xem Q6.

**GĐ2 – tiếng Hàn** (chỉ câu đã chốt, không cờ): `s2_claude_dich.py --chuan-bi` → tác tử TẠO dịch → `--nhan` → soát `CC/xem_gd2.py` → `s2_kiem_tra.py`. Điểm riêng:
- `full_translation.lines[].meaning`: **văn nói hội thoại** (giữ quan hệ trên–dưới: kính ngữ/반말 theo lời thoại JA), không ép -습니다; `analysis`: văn phong -습니다.
- Câu trích giống nhau / trùng dòng lời thoại phải dịch giống nhau (Python D4 so `quotes.meaning.ko` với dòng tương ứng).
- `speaker` không dịch; `⟪ ⟫` giữ nguyên, trợ từ Hàn theo âm cuối cách đọc tiếng Nhật (như 08).
- `glossary_ko.json` thêm thuật ngữ nghe hiểu: 会話/話 → 대화/이야기, 男の人/女の人 → 남자/여자, 店員 → 점원, 課長 → 과장, 選択肢 → 선택지…

**GĐ3 – Excel CTV**: `s3_xuat_ctv.py` (ĐẠT → CTV tiếng Hàn) và `s3b_xuat_ctv_nhat.py` (có cờ → CTV tiếng Nhật). Mỗi câu một khối: lời thoại song ngữ dạng bảng (người nói | JA | VI/KO), rồi câu hỏi, 4 lựa chọn (lựa chọn tranh ghi "【Tranh – xem trên app】"), đáp án.

## 4. File sẽ tạo trong thư mục dạng 16

`config.json` (`thu_tu_chay.lo = 10`), `glossary_ko.json`, `schema/` (bản sao `reading_listening.v1` + bản api, bản api bỏ `full_translation`/`summary`/`key_info` vì Python điền), `scripts/` (`_dang.py`, `_dau_vao.py`, `s0_chuan_bi.py`, `s1_claude_tao.py`, `s1_claude_goi.py`, `s1_kiem_tra.py`, `s1_chot.py`, `s2_claude_dich.py`, `s2_claude_goi.py`, `s2_kiem_tra.py`, `s3_xuat_ctv.py`, `s3b_xuat_ctv_nhat.py`, `s9_bao_cao.py`, `s10_luu_da_duyet.py`; `s1_gpt_chuyen.py` / `s2_dich.py` chỉ báo lỗi), `prompts/` (`s1_claude_tao.md`, `s1_claude_kiem_tra.md`, `s2_claude_dich.md`, `s2_claude_kiem_tra.md`, `giao_viec_tao_gd1.md`, `giao_viec_tao_gd2.md`), `SO_TAY_CHAY.md`, `NHAT_KY.md`, `HUONG_DAN_CHAY.md`, cập nhật `README.md`.

**Cần sửa code chung** (làm ở cuộc trò chuyện điều phối): thêm `trich_dan`, `phan_tich` vào `claude_log.NHOM_NOI_DUNG` (nếu dạng 11 chưa thêm); `checks_chung` / `schema_tools` duyệt đúng `Line` / `Quote` của `reading_listening`; `cong_cu/xem_gd1.py`, `xem_gd2.py` hiện `full_translation` dạng bảng hội thoại; cập nhật `CLAUDE_TAO.md`.
**Đề xuất:** đặt phần đọc lời thoại / ghép dòng / tách người nói thành `pipeline_chung/nghe_hieu.py` để dạng 17, 18, 21 (cùng schema) dùng lại – xem Q7.

## 5. Lộ trình

| Bước | Việc | Đầu ra để duyệt |
|---|---|---|
| 1 | Dựng s0 + báo cáo khảo sát (khuôn A–F, nguồn lời thoại, ghép dòng, cờ) | `khao_sat_s0.csv`, tóm tắt số liệu |
| 2 | Viết prompt + script GĐ1, chạy pilot **lô 1 (10 câu: 2 câu / cấp, ≥ 4 câu lựa chọn tranh, 1 câu khuôn C, 1 câu nguồn `doan_van`)** | JSON VI + file lý do + bảng cờ |
| 3 | Anh duyệt pilot GĐ1 → chỉnh prompt / tiêu chí | ghi `NHAT_KY.md` |
| 4 | GĐ2 pilot + Excel CTV mẫu | Excel 2 file |
| 5 | Viết `SO_TAY_CHAY.md`, chạy lô thường: tối đa 3 lô / cuộc trò chuyện | — |

Ước tính chi phí tác tử TẠO: lời giải trung vị 1.650 ký tự (gần dạng 11) nhưng `full_translation` do Python điền → **≈ 150–220k token GĐ1, 200–280k token GĐ2 (phải dịch cả lời thoại) mỗi lô 10 câu**; đo lại ở pilot. Toàn dạng ≈ 109 lô.

## 6. Cần anh duyệt

- **Q1 – Lô:** 10 câu / lô, 100 câu đầu xen kẽ cấp độ và trộn lựa chọn tranh / chữ?
- **Q2 – `full_translation` do Python ghép** (tác tử TẠO chỉ làm câu lệch dòng), tác tử KIỂM TRA vẫn soát nghĩa từng dòng?
- **Q3 – Khuôn lạ C/D (159 câu):** tạo JSON từ phần có được + cờ `thieu_noi_dung` → CTV tiếng Nhật viết phân tích? Riêng 35 câu khuôn D (không có cả bản dịch): có cho tác tử TẠO **dịch mới** lời thoại không, hay để `meaning = null`?
- **Q4 – Ký hiệu `(i)`:** giữ nguyên trong `ja` và `meaning` (như ví dụ mẫu), hay xóa? (Cần biết `(i)` dùng làm gì trên app.)
- **Q5 – `<b>` trong lời thoại (260 câu):** đổi `{ }` theo mục 3a, hay bỏ (vì đánh dấu cả dòng, không phải chỗ gạch chân)? Có dùng để điền `key_info` không, hay để `null`?
- **Q6 – Lỗi gõ trong lời thoại JA gốc** (vd `わかしました` ← わかりました, `準備はん済んでいます`): giữ nguyên + ghi chú cho CTV, hay sửa theo `sua_ban_goc` (mục 2a-1)?
- **Q7 – Code dùng chung nghe hiểu** (`pipeline_chung/nghe_hieu.py`) để tái dùng cho 17/18/21?
- **Q8 – `giai_thich_ko` có sẵn:** không dùng (như 07–11)?
