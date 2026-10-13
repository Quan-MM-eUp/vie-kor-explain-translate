# Kế hoạch dựng pipeline – dạng 13 Đọc hiểu tổng hợp (ĐÃ DUYỆT 08/10/2026 – đã dựng)

> Soạn 2026-10-08. Chạy **hoàn toàn bằng Claude Opus 5.5 Cowork** (tác tử TẠO = tác tử con `model: opus`, tác tử KIỂM TRA = phiên chính), **không GPT API** – theo khung dạng 08/09 (`pipeline_chung/CLAUDE_TAO.md`) và bản kế hoạch dạng 11 (cùng schema `reading_listening.v1`).
> Số liệu quét từ `data/13_doc_hieu_tong_hop.csv` (149 câu).
> **Người dùng đồng ý mọi đề xuất (08/10/2026)** – cách triển khai thực tế và điều chỉnh (Q2 chạy phương án b, Q7 parser để trong `scripts/_doc_hieu_13.py`) ghi ở `NHAT_KY.md`.

## 1. Dữ liệu – khác gì so với dạng 11

| Đặc điểm | Số liệu | Hệ quả cho pipeline |
|---|---|---|
| 149 câu (N1 57, N2 92) = **67 đoạn văn**: 2 câu/đoạn 50, 3 câu/đoạn 16, 1 câu/đoạn 1 (12542) | `doan_van` giống hệt nhau trong một `question_id` | Ít dữ liệu → **không cần "100 câu đầu xen kẽ"**; lô theo đoạn, không cắt đoạn |
| **52 đoạn (104 câu) có cấu trúc A / B** (40 đoạn "A–B", 2 đoạn "A–B–C", 2 đoạn 相談者 + 回答者Ａ/Ｂ, có `（中略）`, 1 cặp thư A/B) | 99 câu hỏi nhắc "A và B" (`AとBで共通して…` 28 câu) | Python **tách đoạn văn theo nhãn A/B/C** → dùng cho hiển thị, kiểm tra nguồn trích dẫn, `full_translation.label` |
| **15 đoạn N2 (45 câu: 12535–12541, 12642–12649) KHÔNG có A/B** – một bài đọc dài, 3 câu hỏi (vd so sánh "A社 / B社" trong cùng bài) | | Nghi phân loại nhầm (giống dạng 12 Đoạn văn dài) → **Q1** |
| Đoạn văn: trung vị 642 ký tự (tối đa 1.024); 11 đoạn có `<table>`, 0 ảnh, 0 ruby; 11 có `注`, 18 câu hỏi có ①② gạch chân | | Làm sạch HTML trong s0; không cần cờ ảnh |
| Lời giải **dài hơn dạng 11 ~25%** (trung vị 1.986 ký tự/câu, ~4.300/đoạn); 8.243 thẻ ruby | Trung bình 3,2 câu trích 「…」/câu, có câu 11–12 trích | Lô nhỏ hơn dạng 11 (≈ 8–10 câu); GĐ2 nặng phần `quotes` |
| **129 câu (87%) khuôn chuẩn**: câu hỏi + dịch → 4 lựa chọn (`Nghĩa:` / nhận xét có `Đoạn A có câu:`, `Trong đoạn B…`, `Trích dẫn từ đoạn A:` + 「…」 (dịch)) → `→ ĐÚNG` / `→ SAI` | Đáp án theo `→ ĐÚNG` lệch `dap_an_so`: **0** | Ánh xạ sạch vào `reading_listening.v1` |
| **20 câu khuôn lạ**, tập trung ở **9 đoạn**: 8 đoạn N1 (53308, 53395, 53477, 53560, 53638, 53724, 53799, 53885) – câu con 1 = **bản dịch đầy đủ đoạn A/B** + dịch câu hỏi/lựa chọn, câu con 2 = dịch câu hỏi + lựa chọn (+ "Câu trả lời đúng là…"), không phân tích; 53990 (N2) = 1 câu tóm tắt + 1 câu chỉ có `ヒント：`; 16885_2 = tiếng Nhật chen lẫn hỏng ("…と述べているとは述べていない"), không có `→ ĐÚNG` | | Cờ `thieu_noi_dung` → CTV tiếng Nhật; **tận dụng bản dịch đầy đủ** cho `full_translation` (**Q3**) |
| 17064_2: **2 lựa chọn `→ ĐÚNG`** | | Cờ s0 `nhieu_dung` |
| Câu hỏi trong lời giải lệch `cau_hoi`: 27 (19 thuộc khuôn lạ) | | Cờ s0 `cau_hoi_lech` |
| Trích dẫn 「…」: 476 câu; khớp nguyên văn đoạn văn **84%**, khớp một phần thêm 13% | | K-TD = CẢNH BÁO (so mờ), như dạng 11 |
| **79 câu (53%) chèn từ Nhật vào câu Việt** ("…là do 二酸化炭素") | | Bọc `⟪ ⟫`, giữ nguyên (như dạng 11) |
| `transcript_vi` rỗng; `giai_thich_ko` có đủ 149 câu | | `summary`, `key_info` = `null`; `giai_thich_ko` không dùng (**Q6**) |

## 2. Schema và ánh xạ

Giữ `reading_listening.v1`. id mẫu = `<question_id>_<cau_con>`.

| Lời giải gốc | Trường JSON |
|---|---|
| Dòng câu hỏi tiếng Nhật / dòng dịch | `question.ja` (khớp `cau_hoi` sau bỏ furigana) / `question.meaning.vi` |
| `1. …` / `Nghĩa: …` | `options[i].option_ja` (`reading = null`) / `options[i].meaning.vi` |
| Nhãn dẫn `Đoạn A có câu:` / `Trong đoạn B, có câu` / `Trích dẫn từ đoạn A:` + 「câu Nhật」 + (dịch) | `options[i].quotes[] = {ja, meaning.vi}`; **nguồn A/B** → xem **Q2** |
| Phần nhận xét còn lại (kể cả "Đoạn A nói…, còn đoạn B…") | `options[i].analysis.vi` – chép nguyên, **không tự thêm câu "trích dẫn 1 ở đoạn A"** như ví dụ mẫu `explanation_schema/examples/13_…json` (sẽ sửa ví dụ cho khớp quy tắc không thêm nội dung) |
| `→ ĐÚNG` / `→ SAI` | `options[i].is_match` |
| Đáp án | `correct = {index: dap_an_so, option_ja, full_sentence: null}` |
| Bản dịch đầy đủ A/B (chỉ 8 đoạn N1 khuôn lạ) | `full_translation = [{label:"A", lines:[{speaker:null, ja:null, meaning.vi}]}, {label:"B", …}]` – chỉ ở câu con 1 (**Q3**) |
| Khuôn lạ còn lại | Chép phần có được vào trường gần nhất, trường thiếu `null` / `[]` + cờ `thieu_noi_dung` |

## 3. Quy trình (khung 08/09/11, chỉnh cho A/B)

**GĐ0 – Python `s0_chuan_bi.py`** (tái dùng `normalize.py`, `so_chu.py`… của `pipeline_chung`):
- Chuẩn hóa ruby → `｜…《…》`, gạch chân `<u>`/span underline → `{ }`, phân loại khuôn (chuẩn / dịch-đầy-đủ / chỉ-đáp-án / tóm-tắt / hỏng).
- **Tách đoạn văn theo nhãn** (`A`, `B`, `C`, `回答者：Ａ`, `相談者`, thư A/B) → `output/reports/doan_van_tach.csv` (đoạn, nhãn, văn bản). Đoạn không tách được (15 đoạn N2 đơn) → nhãn `null`.
- `output/thu_tu_chay.csv` theo đoạn, N1/N2 xen kẽ; **9 đoạn khuôn lạ dồn về lô cuối** (gần như chắc chắn gắn cờ, soát nhanh một lần). Lô chuẩn **4 đoạn ≈ 8–10 câu** → ≈ 15–16 lô (tùy Q1).
- Cờ gợi ý cho tác tử KIỂM TRA: `khuon_la`, `nhieu_dung`, `cau_hoi_lech`, `lua_chon_lech`, `trich_dan_ngoai_doan`, **`trich_dan_sai_nguon`** (lời giải nói "đoạn A" nhưng câu trích nằm ở B), `chen_tu_nhat`, `ruby_hong`, `doan_khong_ab`.
- Báo cáo `output/reports/khao_sat_s0.csv`.

**GĐ1 – JSON tiếng Việt**
1. `s1_claude_tao.py --chuan-bi` → gói đầu vào **theo đoạn**: đoạn văn đã tách A/B (giữ ①② và `{ }`), mỗi câu con: câu hỏi, 4 lựa chọn, đáp án, lời giải đã chuẩn hóa, cờ s0.
2. Tác tử TẠO chuyển JSON theo `prompts/s1_claude_tao.md` (lỗi hay mắc riêng: tách nhãn dẫn A/B khỏi câu trích, không gộp 2 câu trích làm 1, không tự viết thêm "điểm chung").
3. `--nhan` (hook `bo_sung`: Python điền `full_translation` cho 8 đoạn N1 và nguồn trích dẫn nếu Q2 duyệt) → `s1_claude_goi.py` → tác tử KIỂM TRA soát bằng `cong_cu/xem_gd1.py` (in đoạn A và B một lần, rồi các câu con) → `ghi_ly_do.py` → `s1_kiem_tra.py` → `s1_chot.py`.

**Python kiểm tra GĐ1** (ngoài bộ chung: schema, mất tiếng Nhật, độ phủ chữ Việt ≥ 97%, `{ }`, furigana, `⟪ ⟫`):
- LỖI: `correct.index ≠ dap_an_so`; số `is_match = true` ≠ 1 hoặc lệch `correct.index` (trừ câu có cờ); thiếu lựa chọn; `full_translation` có label ngoài A/B/C.
- CẢNH BÁO: `question.ja` lệch `cau_hoi`; `option_ja` lệch `lua_chon_i`; **K-TD** câu trích không có trong đoạn văn (so mờ); **K-NGUON** câu trích không nằm trong đoạn A/B mà lời giải nêu; **K-NQ** cùng một câu trích trong một đoạn mà nghĩa khác nhau giữa các câu con.

**Tiêu chí soát GĐ1 riêng dạng 13** (tác tử KIỂM TRA chỉ gắn cờ, không sửa nội dung):

| Gắn cờ `nghi_noi_dung` khi | `nhom` |
|---|---|
| Trích dẫn không có trong đoạn văn, **gán nhầm đoạn A ↔ B**, hoặc không chứng minh được điều phân tích nói | `trich_dan` *(mới, chung với dạng 11)* |
| Phân tích sai quan điểm của A hoặc B (nói "cả A và B đều…" nhưng chỉ một bên nói; đảo quan điểm A/B; nói "không đề cập" nhưng có) | `phan_tich` *(mới, chung với dạng 11)* |
| Kết luận ĐÚNG/SAI trái đáp án, nhiều lựa chọn ĐÚNG | `dap_an` |
| Dịch câu hỏi / lựa chọn / câu trích sai nghĩa (đặc biệt "A も B も" / "A は…が、B は…") | `nghia_cau` |
| Khuôn lạ – thiếu phân tích các lựa chọn | `thieu_noi_dung` |

Sửa định dạng (`sua_dinh_dang`): lỗi gõ, nhãn dính dòng, dấu thừa, `⟪ ⟫`/furigana lệch. **Không gắn cờ:** phân tích sơ sài nhưng đúng; lựa chọn sai không kèm trích dẫn; dịch vụng nhưng đúng ý.

**GĐ2 – tiếng Hàn** (chỉ câu đã chốt, không cờ): gói theo đoạn, các câu con cùng đoạn dịch cùng lúc; câu trích giống nhau dịch giống nhau (D4 theo đoạn); `⟪ ⟫` + trợ từ Hàn theo âm cuối cách đọc Nhật (như 08); `analysis` văn phong -습니다.
- `glossary_ko.json` thêm: 筆者 → 필자, 相談者 → 상담자, 回答者 → 답변자, 共通 → 공통, 本文 → 본문, 下線部 → 밑줄 친 부분, "đoạn A / đoạn B" → "A 글 / B 글" (giữ chữ Latin A/B như đề).
- `full_translation` (8 đoạn) dịch như văn xuôi, giữ chia dòng.

**GĐ3 – Excel CTV**: `s3_xuat_ctv.py` (ĐẠT → CTV tiếng Hàn), `s3b_xuat_ctv_nhat.py` (có cờ → CTV tiếng Nhật); **nhóm theo đoạn**, cột "Ngữ liệu" hiện **A và B tách khối** một lần ở đầu nhóm, rồi từng câu con.

## 4. File sẽ tạo trong thư mục dạng 13

`config.json`, `glossary_ko.json`, `schema/` (bản sao `reading_listening.v1` + bản api), `scripts/` (`_dang.py`, `_dau_vao.py`, `s0_chuan_bi.py`, `s1_claude_tao.py`, `s1_claude_goi.py`, `s1_kiem_tra.py`, `s1_chot.py`, `s2_claude_dich.py`, `s2_claude_goi.py`, `s2_kiem_tra.py`, `s3_xuat_ctv.py`, `s3b_xuat_ctv_nhat.py`, `s9_bao_cao.py`, `s10_luu_da_duyet.py`; `s1_gpt_chuyen.py` / `s2_dich.py` chỉ báo lỗi), `prompts/` (`s1_claude_tao.md`, `s1_claude_kiem_tra.md`, `s2_claude_dich.md`, `s2_claude_kiem_tra.md`, `giao_viec_tao_gd1.md`, `giao_viec_tao_gd2.md`), `SO_TAY_CHAY.md`, `NHAT_KY.md`, `HUONG_DAN_CHAY.md`, cập nhật `README.md`.

**Code chung cần sửa** (làm ở cuộc trò chuyện điều phối): thêm `trich_dan`, `phan_tich` vào `claude_log.NHOM_NOI_DUNG` (nếu dạng 11 chưa thêm); `cong_cu/xem_gd1.py` / `xem_gd2.py` in đoạn văn theo nhãn A/B; kiểm tra `checks_chung` / `schema_tools` duyệt đúng `Quote` / `Line` / `full_translation`; cập nhật `pipeline_chung/CLAUDE_TAO.md`. Đề xuất đặt bộ parser lời giải đọc hiểu (khuôn `Nghĩa` / trích dẫn / `→ ĐÚNG`) vào `pipeline_chung/doc_hieu.py` để dạng 10–15 dùng chung (**Q7**).

## 5. Lộ trình

| Bước | Việc | Đầu ra để duyệt |
|---|---|---|
| 1 | s0 + tách A/B + báo cáo khảo sát | `khao_sat_s0.csv`, `doan_van_tach.csv`, tóm tắt số liệu |
| 2 | Prompt + script GĐ1, pilot **lô 1 = 4 đoạn (~9 câu)**: 1 đoạn N1 A/B, 1 đoạn N2 A/B, 1 đoạn 相談者/回答者, 1 đoạn N2 không A/B (nếu giữ theo Q1) | JSON VI + file lý do + bảng cờ |
| 3 | Anh duyệt pilot GĐ1 → chỉnh prompt / tiêu chí | ghi `NHAT_KY.md` |
| 4 | GĐ2 pilot + Excel CTV mẫu | 2 file Excel |
| 5 | `SO_TAY_CHAY.md`, chạy lô thường (tối đa 3 lô / cuộc trò chuyện); lô khuôn lạ chạy cuối | — |

Ước tính tác tử TẠO: lời giải dài hơn dạng 11 ~25%, nhiều câu trích hơn → **≈ 250–350k token mỗi giai đoạn cho một lô ~9 câu**; toàn dạng ≈ 15–16 lô × 2 giai đoạn ≈ 8–10M token. Đo lại ở pilot.

## 6. Cần anh duyệt

- **Q1 – 15 đoạn N2 không có A/B (45 câu):** giữ ở dạng 13 và chạy chung (nhãn đoạn `null`), hay chuyển sang dạng 12 Đoạn văn dài (sửa `dang_bai` trong dữ liệu)? *Đề xuất: giữ ở 13 để không chờ, ghi chú phân loại nghi nhầm trong `NHAT_KY.md`.*
- **Q2 – Nguồn trích dẫn A/B:** (a) thêm trường tùy chọn `quotes[].source` ("A"/"B"/null, Python điền từ vị trí câu trích – cần báo dev app), hay (b) giữ schema, nguồn chỉ thể hiện trong `analysis` như lời giải gốc? *Đề xuất (a) nếu dev đồng ý; nếu chưa trả lời được thì chạy (b) và Python vẫn kiểm tra K-NGUON.*
- **Q3 – 8 đoạn N1 khuôn lạ có bản dịch đầy đủ A/B:** đưa vào `full_translation` (label A/B) + cờ `thieu_noi_dung` cho phần phân tích thiếu, hay bỏ qua bản dịch?
- **Q4 – Lô:** 4 đoạn (~8–10 câu), N1/N2 xen kẽ, đoạn khuôn lạ dồn lô cuối?
- **Q5 – Hai nhóm cờ mới** `trich_dan`, `phan_tich` (dùng chung với dạng 11) – trong `trich_dan` tính cả "gán nhầm đoạn A ↔ B"?
- **Q6 – `giai_thich_ko` có sẵn:** không dùng (như 07–09), hay đưa làm tham khảo thuật ngữ cho GĐ2?
- **Q7 – Code chung:** gom parser đọc hiểu vào `pipeline_chung/doc_hieu.py` cho 10–15 (làm dạng 13 trước vì nhỏ – 149 câu – để thử khuôn), hay dựng riêng trong thư mục dạng 13?
