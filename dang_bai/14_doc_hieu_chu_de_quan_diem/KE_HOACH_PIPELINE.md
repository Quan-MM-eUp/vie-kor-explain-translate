# Kế hoạch dựng pipeline – dạng 14 Đọc hiểu: Chủ đề / Quan điểm (đoạn văn dài) (ĐÃ DUYỆT 2026-10-08 – đã dựng)

> Soạn 2026-10-08. Chạy **hoàn toàn bằng Claude Opus 5.5 Cowork** (tác tử TẠO = tác tử con `model: opus`, tác tử KIỂM TRA = phiên chính), **không GPT API** – cùng khung với kế hoạch dạng 11 (`../11_doc_hieu_doan_van_trung_binh/KE_HOACH_PIPELINE.md`) và mẫu 08/09 (`pipeline_chung/CLAUDE_TAO.md`).
> Số liệu quét từ `data/14_doc_hieu_chu_de_quan_diem.csv` (265 dòng). Chỉ ghi những điểm **khác dạng 11**; phần nào không nhắc thì giữ như kế hoạch dạng 11.

## 1. Dữ liệu – khác gì so với dạng 11

| Đặc điểm | Số liệu dạng 14 | Hệ quả cho pipeline |
|---|---|---|
| Quy mô | **265 câu = 82 đoạn** (3 câu: 59 đoạn, 4: 21, 2: 2); chỉ **N1 (104) / N2 (161)**; 1 `question_id` = đúng 1 đoạn | Khóa nhóm = `question_id` (sạch hơn so chuỗi `doan_van`); xen kẽ chỉ 2 cấp |
| Đoạn văn dài | trung vị **1.036 ký tự** (698–1.678); 42 đoạn có `注`; 9 đoạn có `{…}` gạch chân; 2 đoạn bọc trong `<table>` + 5 đoạn có HTML Word (`mso`, `span lang`) | `<table>` ở đây là **khung viền**, không phải bảng dữ liệu → Python bóc khung, bỏ `mso/span`, giữ `①②`, `{ }`, `注` |
| Lời giải dài | trung vị **3.178 ký tự/câu** (tối đa 9.161), ~13.350 thẻ ruby | Lô nhỏ hơn dạng 11 (xem Q1); chi phí token cao hơn |
| Loại câu hỏi | Chỉ định / gạch chân 「…」とあるが… **94** · nội dung phù hợp 47 · **quan điểm tác giả 32** · điền chỗ trống ① 21 · lý do 13 · tóm tắt/chủ đề 3 · khác 55. Câu **cuối** mỗi đoạn thường là quan điểm/nội dung tổng thể | s0 gắn `loai_cau_hoi` (chỉ dùng nội bộ, không thêm vào schema) để prompt TẠO/KIỂM TRA áp tiêu chí riêng |
| Lựa chọn là **câu dài** (trung vị 23 ký tự) | 14 lựa chọn / 8 câu hỏi có HTML hoặc `{ }` | `options[i].meaning.vi` = dịch cả câu; chuẩn hóa `{ }` như câu hỏi |
| **Khuôn chuẩn: 219 câu (83%)** – 2 kiểu nhãn | Kiểu A: `Nghĩa:` / `Trích dẫn:` 「…」(dịch) / `Giải thích:` / `→ ĐÚNG/SAI`. Kiểu B: gạch đầu dòng `- Đoạn văn có câu:` / `- Trong đoạn văn có câu:` / `- Đoạn văn viết:` … + `- ` nhận xét | Parser phải nhận cả 2 kiểu + ~20 biến thể nhãn dẫn (nhãn không chép vào JSON) |
| **Khuôn lạ: 46 câu (17%) = trọn 16 đoạn** (gấp đôi tỉ lệ dạng 11) | (a) **Dịch cả đoạn văn sang Việt** + dịch câu hỏi/lựa chọn, không phân tích: 6 đoạn (dịch nằm ở câu con 1); (b) chỉ "Câu trả lời đúng là…": 3 đoạn; (c) vài câu giải thích ngắn / `ヒント：「…」` / chỉ ghi đáp án: 7 đoạn. Tất cả là HTML `<p>/<ul>` | Không có phân tích 4 lựa chọn → xem **Q2** (đề xuất mới so với dạng 11) |
| Trích dẫn | 700 câu trích: khớp nguyên văn 78%, khớp một phần 96%; 137 lựa chọn trích **≥ 2 câu**, 276 lựa chọn không trích | `quotes[]` nhiều phần tử là bình thường; K-TD vẫn chỉ CẢNH BÁO |
| Đáp án | `→ ĐÚNG` lệch `dap_an_so`: **0**; khuôn chuẩn nhưng ≠ 1 chỗ ĐÚNG: 3 | Cờ s0 `nhieu_dung` |
| Từ Nhật chen trong câu Việt | **164 câu (62%)** | Bọc `⟪ ⟫`, giữ nguyên (như Q3 dạng 11) |
| Khác | 131/265 câu thuộc đề thi thử; `giai_thich_ko` có đủ 265; không có `transcript_vi`; 1 chỗ gõ lỗi `Giải釈` | Sửa định dạng; `giai_thich_ko` không dùng (Q5) |

## 2. Schema và ánh xạ

Giữ `reading_listening.v1`, **không thêm trường**; id mẫu `<question_id>_<cau_con>`. Ánh xạ khuôn chuẩn như dạng 11, bổ sung:

| Lời giải gốc | Trường JSON |
|---|---|
| Kiểu B: `- Đoạn văn có câu: 「…」 (dịch)` | `options[i].quotes[]` (giống `Trích dẫn:`) |
| Kiểu B: các gạch `- ` nhận xét còn lại | gộp vào `options[i].analysis.vi` (bỏ dấu `- ` đầu dòng, giữ xuống dòng) |
| Câu hỏi nhiều dòng (vd `文中の①～⑦の問いに…` + `①「自分」とはだれか。`) | `question.ja` giữ cả hai dòng như `cau_hoi` |
| Khuôn lạ (a): bản dịch đoạn văn tiếng Việt | `full_translation.vi` (xem Q3) |
| Khuôn lạ (b)/(c) | theo phương án Q2 |
| `summary`, `key_info` | `null` (không có trong nguồn) |

## 3. Quy trình (khung 08/09/11 – chỉ ghi điểm riêng)

**GĐ0 – `s0_chuan_bi.py`**
- Bóc khung `<table>`/`mso` trong đoạn văn; ruby → `｜…《…》`; `<b>/<u>` → `{ }`.
- Phân khuôn: `chuan_A`, `chuan_B`, `la_dich_doan`, `la_chi_dap_an`, `la_ngan`; phân `loai_cau_hoi` (A–G ở mục 1).
- `output/thu_tu_chay.csv` theo đoạn: N1/N2 xen kẽ; **16 đoạn khuôn lạ xếp riêng cuối danh sách** (chạy theo phương án Q2).
- Cờ gợi ý (ngoài bộ dạng 11): `cum_hoi_khong_trong_doan` (cụm 「…」 trong câu hỏi gạch chân không tìm thấy trong đoạn văn), `thieu_moc_doan` (câu hỏi nhắc ①② mà đoạn văn không có mốc), `doan_khung_html`.
- Báo cáo `output/reports/khao_sat_s0.csv`.

**GĐ1 – JSON tiếng Việt**: như dạng 11 (gói theo đoạn → tác tử TẠO → `--nhan` → KIỂM TRA bằng `xem_gd1.py` → `ghi_ly_do.py` → `s1_kiem_tra.py` → `s1_chot.py`). Gói đầu vào thêm `loai_cau_hoi` từng câu con. Ví dụ mẫu: sửa `explanation_schema/examples/14_…json` (hiện là câu điền liên từ – ít gặp ở dạng 14) thành **1 câu quan điểm tác giả + 1 câu gạch chân**, lấy từ dữ liệu thật.

**Python kiểm tra GĐ1**: toàn bộ kiểm tra dạng 11 (LỖI đáp án/`is_match`; CẢNH BÁO `question.ja`, `option_ja`, K-TD, K-NQ) + **K-GC**: câu loại B (gạch chân) mà không lựa chọn nào có `quotes` chứa cụm được hỏi → CẢNH BÁO.

**Tiêu chí soát GĐ1 riêng dạng 14** (chỉ gắn cờ, không sửa nội dung):

| Gắn cờ `nghi_noi_dung` khi | `nhom` |
|---|---|
| **Câu quan điểm tác giả**: lời giải lấy ý của **người khác / ví dụ / quan điểm bị phản bác** trong bài làm ý của tác giả, hoặc bỏ qua đoạn kết luận | `quan_diem` *(mới)* |
| Câu gạch chân / chỉ định: giải thích sai cái mà cụm được hỏi chỉ tới (sai phạm vi, sai chủ thể) | `phan_tich` |
| Trích dẫn không có trong bài / không chứng minh được nhận định | `trich_dan` |
| Kết luận ĐÚNG/SAI trái đáp án, nhiều ĐÚNG | `dap_an` |
| Dịch câu hỏi / lựa chọn / câu trích sai nghĩa | `nghia_cau` |
| Khuôn lạ còn thiếu phân tích (nếu Q2 chọn phương án giữ nguyên) | `thieu_noi_dung` |

Không gắn cờ: phân tích sơ sài nhưng đúng; lựa chọn sai không kèm trích dẫn; dịch vụng nhưng đúng ý; trích nhiều câu dài hơn cần thiết.

**GĐ2 – tiếng Hàn**: như dạng 11 (dịch cả đoạn cùng lúc, câu trích giống nhau dịch giống nhau, `⟪ ⟫` giữ nguyên, `analysis` văn phong -습니다). `glossary_ko.json` thêm: 筆者 → 필자, 主張 → 주장, 要旨 → 요지, 下線部 → 밑줄 친 부분, 本文 → 본문, 引用 → 인용, 「〜とあるが」 → '~'라고 했는데. Nếu có `full_translation` (Q3) thì dịch luôn sang Hàn.

**GĐ3 – Excel CTV**: như dạng 11 – nhóm theo đoạn văn (đoạn hiện một lần, sau đó các câu con); đoạn khuôn lạ ra file CTV tiếng Nhật riêng hoặc chung tùy Q2.

## 4. Dùng lại code – đề xuất gom phần đọc hiểu chung

Dạng 11 và 14 trùng ~80% (parser lựa chọn/trích dẫn, làm sạch đoạn văn, K-TD/K-NQ, Excel nhóm theo đoạn) và dạng 10, 12, 13, 15 sau này cũng cần. Đề xuất tạo **`pipeline_chung/doc_hieu.py`** (parser kiểu A/B, làm sạch đoạn văn, so mờ trích dẫn, xuất Excel theo đoạn); `_dang.py` dạng 14 chỉ chứa phần riêng (khuôn lạ, `loai_cau_hoi`, K-GC). File trong thư mục dạng 14: giống danh sách mục 4 kế hoạch dạng 11.

Sửa code chung (ở phiên điều phối): thêm `trich_dan`, `phan_tich`, `quan_diem` vào `claude_log.NHOM_NOI_DUNG`; cập nhật `CLAUDE_TAO.md` mục "Các dạng đã chuyển".

## 5. Lộ trình

| Bước | Việc | Đầu ra để duyệt |
|---|---|---|
| 1 | s0 + báo cáo khảo sát | `khao_sat_s0.csv` |
| 2 | Prompt + script GĐ1; pilot **lô 1 = 3 đoạn (~10 câu)**: 1 đoạn N1 kiểu A, 1 đoạn N2 kiểu B có câu quan điểm, 1 đoạn khuôn lạ (a) | JSON VI + file lý do + bảng cờ |
| 3 | Anh duyệt pilot → chỉnh prompt / tiêu chí, ghi `NHAT_KY.md` | — |
| 4 | GĐ2 pilot + Excel CTV mẫu | 2 file Excel |
| 5 | `SO_TAY_CHAY.md`, chạy lô thường (tối đa 3 lô / cuộc trò chuyện) | — |

Ước tính: lời giải dài gấp ~1,5 lần dạng 11 → **≈ 300–400k token / giai đoạn / lô ~8 câu**; cả dạng ≈ 33 lô × 2 giai đoạn. Đo lại ở pilot.

## 6. Quyết định (anh đã duyệt 2026-10-08 – "đồng ý với các đề xuất")

> Đã chọn: Q1 lô 3 đoạn; **Q2 = (B) tác tử TẠO soạn mới + bắt buộc CTV tiếng Nhật duyệt**; Q3 = `full_translation` của đúng câu con có bản dịch; Q4 thêm `quan_diem`; Q5 không dùng `giai_thich_ko`; Q6 = làm dạng 14 trước, phần đọc hiểu đặt ở `scripts/_doc_hieu_14.py` (không dùng `pipeline_chung/doc_hieu.py` vì phiên dạng 15 đang phát triển file đó song song – gộp sau). Chi tiết thực hiện: `NHAT_KY.md`.


- **Q1 – Lô:** theo đoạn, **2–3 đoạn (~8 câu)** mỗi lô (nhỏ hơn dạng 11 vì lời giải dài), N1/N2 xen kẽ?
- **Q2 – Khuôn lạ (46 câu / 16 đoạn, 17%):** (A) như dạng 11 – chép phần có được + cờ `thieu_noi_dung` → CTV tiếng Nhật viết lại; hay (B) **tác tử TẠO soạn mới** phân tích 4 lựa chọn + trích dẫn từ đoạn văn theo đúng khuôn chuẩn, gắn nhãn `tao_moi` và **bắt buộc qua CTV tiếng Nhật duyệt**? (B tiết kiệm công CTV nhưng phá nguyên tắc "không tạo nội dung mới".)
- **Q3 – Bản dịch đoạn văn có sẵn (6 đoạn):** đưa vào `full_translation` (chỉ câu con 1 hay mọi câu con của đoạn?), hay bỏ vì sheet Format nói bản dịch đầy đủ nằm riêng trên admin?
- **Q4 – Nhóm cờ mới `quan_diem`** (cùng `trich_dan`, `phan_tich` của dạng 11)?
- **Q5 – `giai_thich_ko` có sẵn:** không dùng (như 07–09)?
- **Q6 – Thứ tự làm:** dựng `pipeline_chung/doc_hieu.py` rồi làm dạng 11 trước, dạng 14 theo sau (dùng lại); hay làm dạng 14 trước vì nhỏ hơn (265 câu) để thử nghiệm khung đọc hiểu?
