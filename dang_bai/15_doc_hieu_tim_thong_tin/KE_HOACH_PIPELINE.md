# Kế hoạch dựng pipeline – dạng 15 Đọc hiểu: Tìm thông tin (ĐÃ DUYỆT 08/10/2026 – đã dựng)

> Soạn 2026-10-08. **Anh đã đồng ý toàn bộ Q1–Q8; pipeline đã dựng cùng ngày** – module chung đặt tên `pipeline_chung/doc_hieu_chung.py` (thay cho `doc_hieu.py` trong bản đề xuất, tránh trùng tên với các phiên 10–14 đang dựng song song); chi tiết xem `NHAT_KY.md`. Chạy **hoàn toàn bằng Claude Opus 5.5 Cowork** (tác tử TẠO = tác tử con `model: opus`, tác tử KIỂM TRA = phiên chính), **không GPT API** – theo mẫu dạng 08/09 (`pipeline_chung/CLAUDE_TAO.md`) và cùng khung với kế hoạch dạng 11 (`../11_doc_hieu_doan_van_trung_binh/KE_HOACH_PIPELINE.md`).
> Số liệu quét từ `data/15_doc_hieu_tim_thong_tin.csv` (354 câu).

## 1. Dữ liệu – khác gì so với dạng 11

| Đặc điểm | Số liệu | Hệ quả cho pipeline |
|---|---|---|
| 354 câu = **198 ngữ liệu** (2 câu: 154, 1 câu: 43, 3 câu: 1). N5 gần như 1 câu / ngữ liệu | `doan_van` giống hệt trong một `question_id` | Lô theo **ngữ liệu**, không cắt đôi; lô ~10 câu ≈ 5–6 ngữ liệu |
| Ngữ liệu là **thông báo / bảng giá / lịch / phiếu giảm giá / hướng dẫn**: **166 câu có `<table>`** (N4 35/44 ngữ liệu, N5 29/42, N3 16, N2 12, N1 5), 133 có `&nbsp;`, ký hiệu ※ ■ ● ◆ 【】, ①–⑮ làm nhãn ô | HTML thô tối đa 27.487 ký tự, văn bản sạch trung vị 330–780 | Python **trải bảng thành lưới chữ** (`hàng | ô | ô`) cho gói tác tử TẠO và cho so trích dẫn; giữ nhãn ①②…, bỏ `&nbsp;` |
| **21 câu (12 ngữ liệu) `doan_van` rỗng**; **21 câu có ngữ liệu là ảnh `<img>`** (N1: 8 ngữ liệu) | | Không soát được với ngữ liệu → cờ s0 `thieu_ngu_lieu` / `ngu_lieu_anh` (xem Q3) |
| Lời giải HTML, **320 câu (90%) khuôn chuẩn**: câu hỏi + dịch → 4 lựa chọn (Nghĩa / trích dẫn / phân tích) → `→ ĐÚNG` / `→ SAI` | | Ánh xạ sạch vào `reading_listening.v1` |
| **34 câu (10%) khuôn lạ**, N1 chiếm 15: dịch toàn bộ thông báo (markdown `**…**`) + dịch câu hỏi/lựa chọn + "Lựa chọn chính xác là…" (31), `# Đáp án …` (2), khác (1) | | Không có phân tích 4 lựa chọn → JSON phần có được + cờ `thieu_noi_dung` (Q2) |
| **Tính toán** (riêng dạng 15): 32+ câu có phép tính trong lời giải (`600円 × 0.7 = 420円`, `4 + 3 + 2 = 9`), chủ yếu N3–N4 (giá, giờ, số lượng, ngày) | | Kiểm tra số học bằng Python (K-TT) + tác tử KIỂM TRA soát điều kiện áp dụng (ngày, đối tượng, giảm giá) |
| Lời giải chấm ĐÚNG lệch `dap_an_so`: **1** (12736_2: lời giải tính ra 740円 = lựa chọn 4, dữ liệu ghi 2) | | Cờ s0 `lech_dap_an` → báo người dùng sửa dữ liệu gốc |
| Trích dẫn: 1.211 câu trích 「…」; khớp nguyên văn ngữ liệu 62%, khớp một phần 17%, **~21% không tìm thấy** – có trích dẫn **tự dựng** (12735_1 「4 回 一 日 食べた後…」 không có trong bảng), có "trích dẫn từ bản dịch" chỉ tiếng Việt | Nhãn dẫn rất đa dạng: Trích dẫn (396), Câu trích dẫn, Trong đoạn văn có câu, Trong thông báo có ghi, Trong phần đọc có ghi, Câu trong bảng… | K-TD = CẢNH BÁO (so mờ trên ngữ liệu đã trải bảng); trích dẫn chỉ tiếng Việt → đưa vào `analysis`, không đưa vào `quotes` |
| Lời giải nhiều dòng con: gạch đầu dòng lồng (24 câu), các bước tính, liệt kê điều kiện | | `analysis.vi` giữ xuống dòng `\n` + gạch đầu dòng (Q6) |
| Từ Nhật chen câu Việt: **263 câu (74%)** ("Đối với 魚 (cá)…", "総数 viên: …") | ~16.200 thẻ ruby | Bọc `⟪ ⟫`, giữ nguyên |
| Lựa chọn ngắn (số tiền, giờ, ngày, ①②…): 135 câu; 1 câu chọn tranh (16911_1 "どの絵がいいですか") | | `meaning` có thể trùng `option_ja` (vd "720 yên") – hợp lệ; câu chọn tranh → cờ `ngu_lieu_anh` |
| Không có Tóm tắt / THAM KHẢO; `transcript_vi` rỗng; `giai_thich_ko` có đủ 354 câu | | `summary`, `key_info` = `null`; `giai_thich_ko` không dùng (Q7) |
| 89 câu N3 dùng đề "これを読んで…" (văn xuôi, có 3 câu kiểu ①「…」とあるが) – giống dạng 11 hơn | | Vẫn chạy trong dạng 15, cùng khuôn lời giải; ghi nhận trong NHAT_KY |

## 2. Schema và ánh xạ

Giữ `reading_listening.v1`, **không thêm trường**. id mẫu = `<question_id>_<cau_con>`.

| Lời giải gốc | Trường JSON |
|---|---|
| Dòng câu hỏi tiếng Nhật | `question.ja` (khớp `cau_hoi` sau khi bỏ ruby / khoảng trắng) |
| Dòng dịch câu hỏi | `question.meaning.vi` |
| `1. …` | `options[i].option_ja`; `reading = null` |
| `Nghĩa: …` | `options[i].meaning.vi` |
| Nhãn dẫn + 「câu Nhật」 + (dịch) | `options[i].quotes[] = {ja, meaning.vi}`; nhãn không chép; `ja` có dạng `| ô | ô` của bảng thì chép đúng như lời giải |
| Trích dẫn chỉ tiếng Việt ("Trích dẫn từ bản dịch: …") | giữ trong `analysis.vi` |
| Phân tích, các bước tính, kết luận | `options[i].analysis.vi` (giữ xuống dòng; từ Nhật bọc `⟪ ⟫`) |
| `→ ĐÚNG` / `→ SAI` | `options[i].is_match` |
| Đáp án | `correct = {index: dap_an_so, option_ja, full_sentence: null}` |
| Khuôn lạ: bản dịch thông báo ở đầu lời giải | `full_translation = [{label: null, lines: [...]}]` (chỉ phần dịch có sẵn, không tạo mới) + các trường lựa chọn chỉ có `meaning` + cờ `thieu_noi_dung` |

## 3. Quy trình (khung 08/09, bổ sung phần riêng dạng 15)

**GĐ0 – Python `s0_chuan_bi.py`** (dùng `normalize.py`, `so_chu.py`… của `pipeline_chung`):
- Chuẩn hóa ruby → `｜…《…》`, `<u>` → `{ }`, markdown `**`/`#` → bỏ ký hiệu, giữ dòng; phân loại khuôn A (chuẩn) / B (dịch thông báo + đáp án) / C (khác).
- **Trải bảng ngữ liệu**: `<table>` → lưới chữ có `|`, ô gộp lặp lại, `&nbsp;` → khoảng trắng; xuất `output/reports/ngu_lieu.csv` (ngữ liệu sạch theo `question_id`) dùng cho gói TẠO, `xem_gd1.py` và Excel CTV.
- `output/thu_tu_chay.csv` theo **ngữ liệu**: 100 câu đầu xen kẽ N1–N5 (~10 ngữ liệu mỗi cấp, N5 1 câu/ngữ liệu nên lấy nhiều ngữ liệu hơn); **lô chuẩn ~10 câu** (tròn ngữ liệu, `config.thu_tu_chay.lo = 10`).
- Cờ gợi ý: `khuon_la`, `lech_dap_an`, `nhieu_dung`, `cau_hoi_lech`, `lua_chon_lech`, `trich_dan_ngoai_ngu_lieu`, `trich_dan_tieng_viet`, `co_tinh_toan`, `tinh_toan_sai`, `thieu_ngu_lieu`, `ngu_lieu_anh`, `chen_tu_nhat`, `ruby_hong`.
- Báo cáo `output/reports/khao_sat_s0.csv`.

**GĐ1 – JSON tiếng Việt**
1. `s1_claude_tao.py --chuan-bi` → gói **theo ngữ liệu**: ngữ liệu đã trải bảng (một lần), `de_bai_chung`, mỗi câu con: câu hỏi, 4 lựa chọn, đáp án, lời giải đã chuẩn hóa, cờ s0.
2. Tác tử TẠO chuyển JSON theo `prompts/s1_claude_tao.md` (+ ví dụ `explanation_schema/examples/15_…json` – sửa lại theo khuôn thật, thêm 1 ví dụ có tính toán và 1 ví dụ khuôn B). "Lỗi hay mắc" riêng: tự sửa phép tính / trích dẫn cho đúng (cấm – chép nguyên), gộp nhiều trích dẫn thành một, đưa trích dẫn tiếng Việt vào `quotes`, làm mất dòng con.
3. `--nhan` (Python điền / so `correct`) → `s1_claude_goi.py` → soát bằng `CC/xem_gd1.py` (in ngữ liệu đã trải bảng một lần mỗi nhóm) → file đặc tả lô → `ghi_ly_do.py` → `s1_kiem_tra.py` → `s1_chot.py`.

**Python kiểm tra GĐ1** (ngoài bộ chung: schema, mất tiếng Nhật, độ phủ chữ Việt ≥ 97%, `{ }`, furigana, `⟪ ⟫`):
- LỖI: `correct.index ≠ dap_an_so`; số `is_match = true` ≠ 1 hoặc lệch `correct.index` (trừ câu có cờ `dap_an`); thiếu lựa chọn (trừ khuôn B).
- CẢNH BÁO: `question.ja` / `option_ja` lệch đề; **K-TD** `quotes[].ja` không có trong ngữ liệu (so mờ: bỏ ruby, dấu câu, khoảng trắng, số toàn/bán độ rộng, `|`); **K-NQ** cùng câu trích trong một ngữ liệu mà nghĩa khác nhau giữa các câu con.
- **K-TT (mới):** tìm biểu thức `a ⊕ b … = c` trong `analysis` (+ − × ÷ x *, %, 円, phút/giờ), tính lại → sai số học = CẢNH BÁO `tinh_toan_sai`; với lựa chọn `is_match = true` dạng số, kết quả cuối của phép tính phải bằng số trong `option_ja`.

**Tiêu chí soát GĐ1 riêng dạng 15** (tác tử KIỂM TRA – chỉ gắn cờ, không sửa nội dung):

| Gắn cờ `nghi_noi_dung` khi | `nhom` |
|---|---|
| Phép tính sai, hoặc áp sai điều kiện (sai ngày áp dụng, sai đối tượng/hạng vé, quên phí cộng thêm, sai số lượng tối đa) | `tinh_toan` *(mới)* |
| Trích dẫn tiếng Nhật không có trong ngữ liệu / tự dựng / trích sai hàng của bảng / không chứng minh được điều phân tích nói | `trich_dan` *(mới, chung với 11)* |
| Phân tích trái ngữ liệu (nói "không đề cập" nhưng có, đọc sai bảng, bỏ sót điều kiện ※) | `phan_tich` *(mới, chung với 11)* |
| Kết luận ĐÚNG/SAI trái đáp án; dữ liệu `dap_an_so` sai (12736_2) | `dap_an` |
| Dịch câu hỏi / lựa chọn / câu trích sai nghĩa (kể cả sai số, ngày, giờ) | `nghia_cau` |
| Khuôn lạ – thiếu phân tích lựa chọn; ngữ liệu rỗng / là ảnh nên không xác minh được | `thieu_noi_dung` |

Sửa định dạng: lỗi gõ, nhãn dính dòng, markdown sót, dấu thừa, số toàn/bán độ rộng lẫn lộn, `⟪ ⟫` / furigana lệch.
**Không gắn cờ:** phân tích ngắn nhưng đúng; lựa chọn SAI không kèm trích dẫn; lặp lại cùng phép tính ở nhiều lựa chọn; trích dẫn khớp ý nhưng khác khoảng trắng/dấu câu so với bảng.

**GĐ2 – tiếng Hàn** (chỉ câu đã chốt, không cờ): `s2_claude_dich.py --chuan-bi` (gói theo ngữ liệu) → tác tử TẠO dịch → `--nhan` → soát `CC/xem_gd2.py` → `s2_kiem_tra.py`. Điểm riêng:
- **Giữ nguyên mọi con số, phép tính, đơn vị**: 円 → 엔, 5月5日 → 5월 5일, 13:00〜14:00 giữ nguyên, 30%引き → 30% 할인; Python **D-SO (mới)**: tập số trong bản ko phải trùng tập số trong bản vi (cảnh báo nếu lệch).
- Các câu con cùng ngữ liệu dịch cùng lúc, câu trích / tên mục giống nhau dịch giống nhau (D4 theo ngữ liệu).
- `⟪từ Nhật⟫` giữ nguyên, trợ từ Hàn theo âm cuối cách đọc (như 08/09).
- `glossary_ko.json` thêm thuật ngữ thông báo: 申込/申し込み → 신청, 締め切り → 마감, 料金 → 요금, 割引/〜引き → 할인, 会員 → 회원, 予約 → 예약, 受付 → 접수, 対象 → 대상, 助成 → 지원(조성), 税込 → 세금 포함, 定員 → 정원, 本文 → 본문…

**GĐ3 – Excel CTV**: `s3_xuat_ctv.py` (ĐẠT → CTV tiếng Hàn), `s3b_xuat_ctv_nhat.py` (có cờ → CTV tiếng Nhật); **nhóm theo ngữ liệu**: ngữ liệu hiện một lần (bản trải bảng; ngữ liệu ảnh ghi "[ảnh – xem trên admin, question_id …]"), sau đó từng câu con.

## 4. Đề xuất dùng chung với dạng 11 (và 10, 12–14)

Dạng 10–15 cùng schema `reading_listening.v1` và cùng khuôn lời giải 4 lựa chọn. Đề xuất viết **một parser đọc hiểu dùng chung** `pipeline_chung/doc_hieu.py` (tách lời giải, nhãn dẫn, trích dẫn, K-TD, K-NQ, nhóm theo ngữ liệu, `xem_gd1` in ngữ liệu) ở cuộc trò chuyện điều phối; mỗi dạng chỉ giữ phần riêng trong `_dang.py`. Dạng 15 thêm: trải bảng, K-TT, D-SO, cờ ảnh/rỗng. Nếu anh muốn làm 15 độc lập trước 11 thì vẫn được – sau này gom lại.

## 5. File sẽ tạo trong thư mục dạng 15

`config.json`, `glossary_ko.json`, `schema/` (bản sao `reading_listening.v1` + bản api), `scripts/` (`_dang.py`, `_dau_vao.py`, `s0_chuan_bi.py`, `s1_claude_tao.py`, `s1_claude_goi.py`, `s1_kiem_tra.py`, `s1_chot.py`, `s2_claude_dich.py`, `s2_claude_goi.py`, `s2_kiem_tra.py`, `s3_xuat_ctv.py`, `s3b_xuat_ctv_nhat.py`, `s9_bao_cao.py`, `s10_luu_da_duyet.py`; `s1_gpt_chuyen.py` / `s2_dich.py` chỉ báo lỗi), `prompts/` (`s1_claude_tao.md`, `s1_claude_kiem_tra.md`, `s2_claude_dich.md`, `s2_claude_kiem_tra.md`, `giao_viec_tao_gd1.md`, `giao_viec_tao_gd2.md`), `SO_TAY_CHAY.md`, `NHAT_KY.md`, `HUONG_DAN_CHAY.md`, cập nhật `README.md`.

**Cần sửa code chung** (ở cuộc trò chuyện điều phối): thêm `trich_dan`, `phan_tich`, `tinh_toan` vào `claude_log.NHOM_NOI_DUNG`; kiểm tra `checks_chung` / `schema_tools` duyệt `Quote` / `Line` và giữ `\n` trong `T.vi`; (tùy Q5) `pipeline_chung/doc_hieu.py`; cập nhật `CLAUDE_TAO.md` mục "Các dạng đã chuyển".

## 6. Lộ trình

| Bước | Việc | Đầu ra để duyệt |
|---|---|---|
| 1 | s0: trải bảng, phân khuôn, K-TT, cờ | `khao_sat_s0.csv`, `ngu_lieu.csv`, tóm tắt số liệu |
| 2 | Prompt + script GĐ1, pilot **lô 1 (~10 câu, đủ N1–N5)**: có 1 bảng tính tiền (12736 – lệch đáp án), 1 khuôn B N1 (53310), 1 ngữ liệu rỗng (54384), 1 ngữ liệu văn xuôi N3 | JSON VI + file lý do + bảng cờ |
| 3 | Anh duyệt pilot GĐ1 → chỉnh prompt / tiêu chí | `NHAT_KY.md` |
| 4 | GĐ2 pilot + Excel CTV mẫu (kiểm tra hiển thị bảng) | 2 file Excel |
| 5 | `SO_TAY_CHAY.md`, chạy lô thường: tối đa 3 lô / cuộc trò chuyện (~36 lô ≈ 12 cuộc trò chuyện) | — |

Ước tính tác tử TẠO: ngữ liệu bảng dài + lời giải trung vị 2.760 ký tự (gấp ~1,5 dạng 11) → **≈ 250–350k token mỗi giai đoạn cho lô ~10 câu**; đo lại ở pilot.

## 7. Cần anh duyệt

- **Q1 – Lô:** theo ngữ liệu, ~10 câu (5–6 ngữ liệu, N5 nhiều ngữ liệu hơn), 100 câu đầu xen kẽ cấp độ?
- **Q2 – Khuôn lạ (34 câu, phần lớn N1):** đưa bản dịch thông báo có sẵn vào `full_translation`, lựa chọn chỉ có `meaning`, gắn cờ `thieu_noi_dung` → CTV tiếng Nhật viết lại phân tích? (Hay chỉ liệt kê, không tạo JSON.)
- **Q3 – Ngữ liệu rỗng (21 câu) / ảnh (21 câu):** vẫn tạo JSON từ lời giải nhưng luôn gắn cờ `thieu_noi_dung` (không xác minh được)? Hay anh bổ sung ngữ liệu (ảnh) để tác tử KIỂM TRA xem ảnh?
- **Q4 – Tính toán:** thêm nhóm cờ `tinh_toan`; Python K-TT chỉ CẢNH BÁO, tác tử KIỂM TRA quyết định gắn cờ?
- **Q5 – Code chung:** viết parser đọc hiểu dùng chung `pipeline_chung/doc_hieu.py` cho 10–15 (đề xuất), hay dựng 15 riêng như 09?
- **Q6 – Lời giải nhiều dòng:** giữ `\n` + gạch đầu dòng trong `analysis.vi` (app hiển thị xuống dòng)?
- **Q7 – `giai_thich_ko` có sẵn:** không dùng (như 07–09), dịch lại từ JSON VI?
- **Q8 – Dữ liệu gốc:** 12736_2 `dap_an_so = 2` nhưng lời giải tính ra lựa chọn 4 (740円) – gắn cờ `dap_an` + báo anh sửa dữ liệu gốc?
