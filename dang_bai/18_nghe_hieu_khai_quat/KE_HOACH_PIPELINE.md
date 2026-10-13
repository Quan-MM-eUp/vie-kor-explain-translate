# Kế hoạch dựng pipeline – dạng 18 Nghe hiểu khái quát (ĐÃ DUYỆT 08/10/2026 – đã dựng)

> Soạn 2026-10-08. Chạy **hoàn toàn bằng Claude Opus 5.5 Cowork** (tác tử TẠO = tác tử con `model: opus`, tác tử KIỂM TRA = phiên chính), **không GPT API** – theo khung dạng 08/09 (`pipeline_chung/CLAUDE_TAO.md`).
> Số liệu quét từ `data/18_nghe_hieu_khai_quat.csv`. Dạng nghe đầu tiên – cùng schema `reading_listening.v1` với dạng 11 (đã có kế hoạch, chưa dựng).

## 1. Dữ liệu – khác gì so với 07/08/09/11

| Đặc điểm | Số liệu | Hệ quả cho pipeline |
|---|---|---|
| 351 câu, **mỗi câu = 1 bài nghe** (`cau_con` luôn = 1), chỉ N1 177 / N2 108 / N3 66 | | Không nhóm theo đoạn; lô theo câu |
| **Đề không có chữ**: `cau_hoi` thật chỉ 119 câu, `lua_chon_i` thật 65 câu (còn lại "1","2","3","4" / rỗng) | | Câu hỏi + 4 lựa chọn tiếng Nhật lấy từ **lời thoại** (4 dòng cuối) và từ lời giải; Python đối chiếu hai nguồn |
| **Lời thoại tiếng Nhật** ở `transcript_vi` (HTML `<p><span>`), không furigana; 311 câu có 4 dòng lựa chọn đánh số ở cuối, 33 không đánh số | trung vị 361 ký tự, tối đa 2.197 | Python tách: dòng giới thiệu / lượt thoại (người nói `男`, `女`, `女1`, `F`, `M`, `店員`…) / câu hỏi / 4 lựa chọn |
| **Lỗi nguồn lời thoại**: vài câu `transcript_vi` chứa lời giải (có chữ Việt, "Nghĩa:") trong khi lời thoại thật nằm ở `doan_van` (63 câu có `doan_van`) | | s0 chọn nguồn (`transcript_vi` → `doan_van`), cờ `nguon_loi_thoai` |
| Lời thoại có lỗi gõ / ký hiệu lạ: `えーつ`, `何ががん`, `延期さて`, `(i)` | | Chép nguyên; xem Q5 |
| Lời giải dài (trung vị 4.056 ký tự, tối đa 8.224). Khuôn: **bản dịch lời thoại (VI) + câu hỏi (VI) → `###` → 4 lựa chọn** | | |
| Khuôn A – 242 câu: `###` + `Nghĩa:` + `Phân tích đoạn hội thoại:` + trích 「…」 (dịch) + `→ ĐÚNG/SAI` + câu kết luận | | Ánh xạ sạch |
| Khuôn B – 46 câu: như A nhưng nhãn khác (`Câu thoại liên quan/then chốt:`, `Có câu:`, `Lý do:`) | | Như A |
| Khuôn C – 4 câu: không có `###`, định dạng `<p>` | | Như A sau chuẩn hóa |
| **Khuôn D – 58 câu (17%)**: chỉ bản dịch lời thoại + câu hỏi + 4 lựa chọn **bằng tiếng Việt**, không phân tích; 1 câu gần như trống | | Xem Q3 |
| `→ ĐÚNG` khớp `dap_an_so`: 292/292, không câu nào nhiều ĐÚNG | | Kiểm tra vẫn giữ (LỖI) |
| Lựa chọn trong lời giải ↔ 4 dòng cuối lời thoại: khớp 4/4: 241 · 3/4: 27 · 2/4: 11 · 0/4: 13 | | CẢNH BÁO `lua_chon_lech`, tác tử KIỂM TRA quyết |
| Trích dẫn 「…」 (1.632 câu trích): khớp nguyên văn lời thoại 90%, một phần 9%, không thấy 1% | | K-TD = CẢNH BÁO (so mờ) |
| Bản dịch lời thoại trong lời giải ↔ lời thoại Nhật: **chỉ ~1/3 câu khớp số dòng** (gộp / tách lượt, thêm "Nam:/Người đàn ông:") | | **Không ghép dòng bằng Python** – tác tử TẠO ghép; Python kiểm tra độ phủ hai phía |
| Trích dẫn kèm người nói: "Nam: 「…」", "Người đàn ông nói:" (~1.000 lần) | | `Quote` không có `speaker` – xem Q4 |
| `giai_thich_ko` có cả 351 câu; `transcript_ko` 295 câu (thực chất là lời thoại Nhật bọc 「」) | | Không dùng (Q6) |

## 2. Schema và ánh xạ

Giữ `reading_listening.v1`, **không thêm trường** (trừ khi Q4 chọn khác). id mẫu = `<question_id>_1`.

| Nguồn | Trường JSON |
|---|---|
| Lời thoại Nhật (giới thiệu + lượt thoại, **không** gồm câu hỏi / lựa chọn) | `full_translation = [{label: null, lines: [{speaker, ja, meaning.vi}]}]` – `speaker` chép nguyên ký hiệu lời thoại (`男`, `女1`, `F`…; dòng giới thiệu `null`); `ja` = lượt thoại Nhật; `meaning.vi` = phần dịch tương ứng **trong lời giải** (bỏ nhãn "Nam:/Người phụ nữ:") |
| Câu hỏi: Nhật (dòng sau lời thoại / `cau_hoi`) + Việt (dòng cuối trước `###`) | `question.ja`, `question.meaning.vi` |
| `1. …` (furigana) / dòng lựa chọn lời thoại | `options[i].option_ja`; `reading = null` |
| `Nghĩa: …` | `options[i].meaning.vi` |
| 「câu Nhật」 + (Dịch: …) | `options[i].quotes[] = {ja, meaning.vi}`; nhãn dẫn ("Nam:", "Người đàn ông nói:", "Và:") không chép (Q4) |
| Phần nhận xét + câu kết luận sau `→` (kể cả "Lý do: …") | `options[i].analysis.vi` (từ Nhật chen giữa bọc `⟪ ⟫`) |
| `→ ĐÚNG / SAI` | `options[i].is_match` |
| Đáp án | `correct = {index: dap_an_so, option_ja, full_sentence: null}` |
| — | `summary = null`, `key_info = null` (lời giải không có Tóm tắt / Thông tin) |
| Khuôn D | `full_translation` + `question` + `options[i].meaning.vi` (lựa chọn tiếng Việt), `option_ja` từ lời thoại; `quotes = []`, `analysis = null`, `is_match` theo `dap_an_so` + cờ `thieu_noi_dung` |

## 3. Quy trình (giữ khung 08/09)

**GĐ0 – Python `s0_chuan_bi.py`** (tái dùng `normalize.py`, `so_chu.py`… của `pipeline_chung`):
- Làm sạch lời thoại (HTML, `&nbsp;`, `lang="\&quot;JA\&quot;"`), tách: giới thiệu / lượt thoại + người nói / câu hỏi / 4 lựa chọn → `output/reports/loi_thoai.csv`.
- Chuẩn hóa lời giải: ruby → `｜…《…》`, `<br>`/`<p>` → dòng, tách phần trước / sau `###`, phân loại khuôn A/B/C/D.
- `output/thu_tu_chay.csv`: 100 câu đầu xen kẽ N1/N2/N3 (34/33/33), sau đó theo file; **lô chuẩn 10 câu**.
- Cờ gợi ý: `khuon_D`, `nguon_loi_thoai`, `lua_chon_lech`, `cau_hoi_lech`, `trich_dan_ngoai_loi_thoai`, `so_dong_dich_lech` (số dòng dịch ≠ số lượt thoại), `lech_dap_an`, `ruby_hong`, `chen_tu_nhat` → `output/reports/khao_sat_s0.csv`.

**GĐ1 – JSON tiếng Việt**
1. `s1_claude_tao.py --chuan-bi` → gói mỗi câu: lời thoại Nhật đã tách (đánh số dòng `L1, L2…` + người nói), câu hỏi + 4 lựa chọn từ lời thoại, lời giải đã chuẩn hóa, `dap_an_so`, cờ s0.
2. Tác tử TẠO theo `prompts/s1_claude_tao.md` (+ ví dụ `explanation_schema/examples/18_…json`): **ghép mỗi lượt thoại Nhật với câu dịch Việt tương ứng** (lượt gộp / tách → chia lại theo câu Nhật; câu dịch không có → `meaning = null`, không tự dịch), rồi điền options.
3. `--nhan` → `s1_claude_goi.py` → tác tử KIỂM TRA soát bằng `CC/xem_gd1.py` (in lời thoại hai cột Nhật | Việt + lời giải gốc + JSON) → file đặc tả lô → `ghi_ly_do.py` → `s1_kiem_tra.py` → `s1_chot.py`.

**Python kiểm tra GĐ1** (ngoài bộ chung: schema, mất tiếng Nhật, độ phủ chữ Việt ≥ 97%, furigana, `⟪ ⟫`):
- LỖI: `correct.index ≠ dap_an_so`; số `is_match = true` ≠ 1 hoặc không trùng `correct.index`; thiếu lựa chọn; **K-LT1** ghép `full_translation[].ja` ≠ lời thoại Nhật (sau bỏ dấu câu / khoảng trắng) – tác tử TẠO làm mất / thêm chữ Nhật; `speaker` không có trong lời thoại.
- CẢNH BÁO: **K-LT2** số dòng `meaning = null` > 0; `question.ja` / `option_ja` lệch lời thoại; **K-TD** `quotes[].ja` không tìm thấy trong lời thoại (so mờ); **K-NQ** cùng câu trích mà `meaning.vi` khác hẳn bản dịch dòng tương ứng.

**Tiêu chí soát GĐ1 riêng dạng 18** (chỉ gắn cờ – không sửa nội dung):

| Gắn cờ `nghi_noi_dung` khi | `nhom` |
|---|---|
| Câu trích không có trong lời thoại / gán sai người nói / không chứng minh được điều phân tích nói | `trich_dan` *(mới, chung với 11)* |
| Phân tích trái lời thoại, sai lập luận "ý chính / khái quát" (vd coi chi tiết phụ là ý chính) | `phan_tich` *(mới, chung với 11)* |
| Bản dịch lời thoại sai nghĩa / bỏ sót ý quan trọng | `loi_thoai` *(mới)* |
| Kết luận ĐÚNG/SAI trái đáp án; đáp án đáng ngờ | `dap_an` |
| Dịch câu hỏi / lựa chọn / câu trích sai nghĩa | `nghia_cau` |
| Khuôn D, câu dịch thiếu nhiều lượt thoại | `thieu_noi_dung` |

Sửa định dạng (`sua_dinh_dang`): lỗi gõ, nhãn dính dòng, ruby hỏng, `⟪ ⟫`, nhãn người nói sót trong `meaning.vi`.
**Không gắn cờ:** dịch thoát ý nhưng đúng; phân tích ngắn nhưng không sai; lựa chọn sai không kèm trích dẫn; câu trích chỉ lệch dấu câu / chữ Hán ↔ kana.

**GĐ2 – tiếng Hàn** (chỉ câu đã chốt, không cờ): `s2_claude_dich.py --chuan-bi` → tác tử TẠO dịch → `--nhan` → soát `CC/xem_gd2.py` → `s2_kiem_tra.py`. Điểm riêng:
- **Lời thoại, câu hỏi, lựa chọn, câu trích: dịch thẳng từ tiếng Nhật** (bản Việt chỉ tham khảo) – giữ đúng **sắc thái nói** (반말 / 존댓말 theo lời thoại Nhật, kính ngữ nhân viên – khách).
- Câu trích = bản dịch dòng lời thoại tương ứng (Python D4: cùng câu Nhật → cùng câu Hàn trong một mẫu).
- `analysis`: dịch từ Việt, văn phong -습니다; trợ từ sau `⟪kana⟫` theo âm cuối cách đọc (như 07–09).
- `glossary_ko.json` thêm: 男/女 (giữ nguyên ký hiệu), 会話 → 대화, 話の要点 → 이야기의 요점, 留守番電話 → 음성 메시지…
- Khối lượng GĐ2 lớn hơn 09 (lời thoại ~10–25 dòng / câu) → có thể phải lô 5 câu cho GĐ2 (đo ở pilot).

**GĐ3 – Excel CTV**: `s3_xuat_ctv.py` (ĐẠT → CTV tiếng Hàn), `s3b_xuat_ctv_nhat.py` (có cờ + khuôn D → CTV tiếng Nhật). Cột "Ngữ liệu" = lời thoại Nhật | Việt | Hàn theo dòng.

## 4. File sẽ tạo trong thư mục dạng 18

`config.json`, `glossary_ko.json`, `schema/` (bản sao `reading_listening.v1` + bản api), `scripts/` (`_dang.py`, `_dau_vao.py`, `_loi_thoai.py` (tách lời thoại), `s0_chuan_bi.py`, `s1_claude_tao.py`, `s1_claude_goi.py`, `s1_kiem_tra.py`, `s1_chot.py`, `s2_claude_dich.py`, `s2_claude_goi.py`, `s2_kiem_tra.py`, `s3_xuat_ctv.py`, `s3b_xuat_ctv_nhat.py`, `s9_bao_cao.py`, `s10_luu_da_duyet.py`; `s1_gpt_chuyen.py` / `s2_dich.py` chỉ báo lỗi), `prompts/` (`s1_claude_tao.md`, `s1_claude_kiem_tra.md`, `s2_claude_dich.md`, `s2_claude_kiem_tra.md`, `giao_viec_tao_gd1.md`, `giao_viec_tao_gd2.md`), `SO_TAY_CHAY.md`, `NHAT_KY.md`, `HUONG_DAN_CHAY.md`, cập nhật `README.md`. Sửa lại ví dụ `explanation_schema/examples/18_…json` cho khớp khuôn thật (speaker theo ký hiệu lời thoại).

**Cần sửa code chung** (ở cuộc trò chuyện điều phối): `claude_log.NHOM_NOI_DUNG` thêm `trich_dan`, `phan_tich`, `loi_thoai`; `checks_chung` / `schema_tools` duyệt `Line` / `Quote` của `reading_listening`; `cong_cu/xem_gd1.py`, `xem_gd2.py` in lời thoại hai / ba cột; cập nhật `CLAUDE_TAO.md`. **Làm chung một lần cho 11 và 18** (và 16, 17, 21 sau này).

## 5. Lộ trình

| Bước | Việc | Đầu ra để duyệt |
|---|---|---|
| 1 | s0 + tách lời thoại + khảo sát | `khao_sat_s0.csv`, `loi_thoai.csv`, tóm tắt số liệu |
| 2 | Prompt + script GĐ1, pilot **lô 1 = 10 câu** (N1/N2/N3; ≥ 1 khuôn B, 1 khuôn D, 1 lời thoại lấy từ `doan_van`, 1 có `女1/女2`) | JSON VI + file lý do + bảng cờ |
| 3 | Anh duyệt pilot GĐ1 → chỉnh prompt / tiêu chí | `NHAT_KY.md` |
| 4 | GĐ2 pilot + Excel CTV mẫu | 2 file Excel |
| 5 | `SO_TAY_CHAY.md`, chạy lô thường: tối đa 3 lô / cuộc trò chuyện | — |

Ước tính tác tử TẠO: **≈ 250–350k token / lô 10 câu cho GĐ1**, GĐ2 cao hơn (dịch cả lời thoại); đo lại ở pilot. Toàn dạng ≈ 35 lô.

## 6. Cần anh duyệt

- **Q1 – Lô:** 10 câu / lô, 100 câu đầu xen kẽ N1/N2/N3? (GĐ2 có thể giảm 5 câu nếu pilot cho thấy quá dài.)
- **Q2 – Bản dịch lời thoại:** để tác tử TẠO ghép từng lượt Nhật ↔ câu Việt trong lời giải; lượt không có bản dịch → `meaning = null` + cảnh báo (không tự dịch)? Hay cho phép tác tử TẠO dịch bù và ghi `[Đã bổ sung]`?
- **Q3 – Khuôn D (58 câu, không phân tích):** tạo JSON phần có được + cờ `thieu_noi_dung` → CTV tiếng Nhật viết phân tích? Hay bỏ hẳn khỏi pipeline, chỉ liệt kê?
- **Q4 – Người nói của câu trích:** bỏ nhãn "Nam: / Người đàn ông nói:" (giữ schema, người nói tra được trong `full_translation`)? Hay thêm `speaker` (nullable) vào `Quote` – đổi schema chung `reading_listening`, ảnh hưởng cả dạng 11?
- **Q5 – Lỗi gõ trong lời thoại Nhật** (`えーつ`, `何ががん`, `延期さて`, `(i)`): chép nguyên + chỉ ghi chú? Hay sửa định dạng khi chắc chắn (vd lời giải trích đúng chữ)?
- **Q6 – `giai_thich_ko` / `transcript_ko`:** không dùng (như 07–09)?
- **Q7 – Nhóm cờ mới** `trich_dan`, `phan_tich`, `loi_thoai` (sửa `pipeline_chung/claude_log.py`).
- **Q8 – Thứ tự với dạng 11:** dựng phần chung `reading_listening` cùng lúc khi làm 18 (18 chạy trước), hay chờ 11 dựng xong rồi 18 kế thừa?

## 7. Kết quả duyệt và điều chỉnh khi dựng (08/10/2026)

- Q1–Q8: duyệt theo đề xuất (phương án đầu của mỗi câu hỏi).
- Điều chỉnh: các phiên khác đang dựng dạng 10–21 song song và đã sửa `pipeline_chung` (thêm `trich_dan`, `phan_tich`; tạo `nghe_hieu.py`). Để tránh ghi đè, dạng 18 **không sửa code chung**: bản dịch lời thoại sai gắn cờ nhóm `nghia_cau` (thay cho nhóm mới `loi_thoai`); công cụ xem lời thoại hai cột là `scripts/xem_loi_thoai.py` của dạng 18. Chi tiết: `NHAT_KY.md`.
