# Hướng dẫn tác tử KIỂM TRA – Bước 1.2: kiểm tra JSON tiếng Việt (dạng 21 – Nghe hiểu tổng hợp) · v1

> Phiên bản `s1_claude_kiem_tra.21.v1` (2026-10-08). Khung = dạng 07/09 (cách chia v2) + tiêu chí riêng nghe hiểu. Model: **Claude Opus 5.5** (Cowork).
> Bản cần kiểm tra do **tác tử TẠO (Claude A)** tạo (mọi chỗ "bản GPT" trong công cụ / báo cáo hiểu là bản tác tử TẠO); khuôn **C_ja** do **Python** dựng. Bạn không tạo lại bản, chỉ soát và sửa.
> **THAM KHẢO** (quy tắc 2026-10-07): không kiểm tra, không sửa `reference_raw`.

**Nhiệm vụ:** JSON phải thể hiện **đúng và đủ** lời giải gốc (không hơn, không kém) và **lời giải phải đúng với lời thoại**. Sửa lỗi của tác tử TẠO + lỗi định dạng; lỗi nội dung của lời giải chỉ **gắn cờ**.

## Làm gì

Xem: `python3 ../../pipeline_chung/cong_cu/xem_gd1.py <id> …` – in **lời thoại JA một lần cho mỗi bài** (khối "ĐOẠN VĂN"), lời giải gốc, gợi ý Python (`gd1_danh_sach.json`), JSON phẳng. Dữ liệu đầy đủ: `output/samples/norm/<id>.json` (`loi_thoai.dong`, `phan.dich_vi`, `phan.phan_tich`, `phan.thong_tin`, `cau_hoi_de_xuat`).
Sửa file `output/json_vi/checked/<id>.json`; ghi lý do bằng **file đặc tả lô + `ghi_ly_do.py`** (SO_TAY mục 4.3). Xong chạy `s1_kiem_tra.py`.

## 1. Sửa lỗi của tác tử TẠO (`sai_so_ban_goc` / `khach_quan` / `chinh_ta`)

- Ghép lời thoại sai: nghĩa gán nhầm lượt, tách / gộp lượt sai, `speaker` sai / thiếu, dòng dịch câu hỏi / lựa chọn lọt vào `full_translation`, mất `(i)` / `(ii)`, `ja` khác lời thoại gốc (K-FT LỖI "chữ KHÔNG có trong lời thoại").
- Ánh xạ sai: nhận xét đặt nhầm lựa chọn, câu trích thiếu / tách gộp sai (K-QT), `meaning` của câu trích lẫn vào `analysis`, nhãn dẫn "Nam nói:" còn trong `analysis`, `is_match` sai so với `→ ĐÚNG/SAI` (K-IM), `option_ja` mất furigana, thiếu ⟪ ⟫.
- Bỏ sót / tự thêm / viết lại câu chữ.

## 2. Sửa lỗi ĐỊNH DẠNG của bản gốc – `loai: sua_dinh_dang` + `nhom` (bảng nhóm như dạng 07: `dinh_chu`, `xuong_dong`, `lap_tu`, `chinh_ta`, `dau_cau`, `khoang_trang`, `ky_tu`, `furigana`, `khac`)

- Mỗi chỗ: mục `sua` (đường dẫn trường nhỏ nhất) **và** dòng `[Đã sửa định dạng] <chỗ>: '<cũ>' → '<mới>' – <lỗi gì>` (một dòng).
- Ví dụ: dính câu / thiếu xuống dòng trong analysis, lặp chữ do gõ, `. . .` thừa dấu cách.
- **Lời thoại tiếng Nhật gốc gõ sai** (`明、月曜日` ← 明日, `フ降り`, `水曜日はもり` ← くもり, `散っちゃんう`, `江エビ`): **KHÔNG sửa** `lines[].ja` (quyết định Q5) – ghi `[Ghi chú] Lời thoại gõ sai: '<cũ>' (nên là '<mới>') – giữ nguyên` vào `ghi_chu_ban_goc` (CTV xem). Câu trích của lời giải viết đúng chỗ lời thoại gõ sai → bình thường (K-TD cảnh báo – bỏ qua).

## 3. Gắn cờ NGHI SAI NỘI DUNG – không sửa (`nghi_noi_dung`, mỗi chỗ một mục `{vi_tri, nhom, mo_ta, de_xuat}`; câu **không được dịch**, chuyển CTV tiếng Nhật)

`vi_tri`: `Lời thoại – lượt N`, `Câu hỏi – nghĩa`, `Lựa chọn N – nghĩa`, `Lựa chọn N – trích dẫn`, `Lựa chọn N – phân tích`, `Lựa chọn N – kết luận`, `Thông tin`, `Đáp án`, `Toàn câu`.

| # | Lỗi | `nhom` |
|---|---|---|
| 1 | **Khuôn B / C (thiếu phân tích từng lựa chọn)** – BẮT BUỘC; `s1_claude_goi` đã **điền sẵn** mục này trong `.ly_do.json` (giữ nguyên; đặc tả lô ghi `nghi_noi_dung` thì chép lại mục này – Python báo LỖI nếu thiếu): `{"vi_tri": "Toàn câu", "nhom": "thieu_noi_dung", "mo_ta": "Lời giải gốc chỉ có <bản dịch lời thoại / đoạn Thông tin / chép lại lời thoại JA> – không phân tích 4 lựa chọn", "de_xuat": "CTV viết phân tích từng lựa chọn"}` | `thieu_noi_dung` |
| 2 | Bản dịch lời thoại / câu hỏi / lựa chọn / câu trích **sai nghĩa** so với tiếng Nhật: sai chủ thể (ai nói, ai làm), mất phủ định, sai thời gian / số / ngày, đảo ý. Dịch thoát nhưng đúng ý → **không** gắn cờ. | `nghia_cau` |
| 3 | Câu trích **không có** trong lời thoại (K-TD) mà cũng không phải sửa lỗi gõ; trích **sai chỗ** (câu của người khác / đoạn khác); câu trích **không chứng minh** được điều phân tích nói. | `trich_dan` |
| 4 | Phân tích **trái lời thoại** hoặc lập luận sai – **đặc biệt suy luận nhiều bước** của nghe hiểu tổng hợp: so điều kiện (giá, ngày, giờ, khoảng cách), loại trừ dần, người nói đổi ý giữa chừng (やっぱり…, じゃあ…にする). Phải **tự đọc lời thoại và tự giải** câu hỏi, đối chiếu với kết luận. Vd lời giải nói "người đàn ông không nhắc đến X" nhưng có; chọn lựa chọn theo ý định ban đầu mà bỏ qua lần đổi ý cuối. | `phan_tich` |
| 5 | Kết luận ĐÚNG / SAI trái đáp án (`lech_dap_an`), nhiều lựa chọn ĐÚNG (`nhieu_dung`), hoặc **tự giải thấy đáp án của đề sai**. | `dap_an` |
| 6 | Câu hỏi tiếng Nhật (`question.ja`) không khớp lời thoại / đề (vd câu con 2 nhận nhầm câu hỏi 1) – kiểm tra lại `cau_hoi_de_xuat`; sai do Python đề xuất nhầm → **sửa** `question.ja` (lỗi tác tử TẠO / Python, `sai_so_ban_goc`), không gắn cờ. | — |
| 7 | Phân tích một lựa chọn chỉ có trích dẫn, không có lý do / chỉ một câu chung chung **làm người học không hiểu vì sao loại** | `thieu_noi_dung` |

- `mo_ta` nêu bằng chứng từ lời thoại (trích câu JA); `de_xuat`: cách sửa – **không** sửa vào JSON.
- **Không gắn cờ:** phân tích sơ sài nhưng đúng; lựa chọn sai không kèm trích dẫn; diễn đạt vụng; lỗi gõ của lời thoại (mục 2); câu trích bỏ bớt đầu / cuối câu mà phần trích đúng chữ.

## 4. Gợi ý / cảnh báo Python (đọc trong `gd1_danh_sach.json` và kết quả `s1_kiem_tra`)

| Mã | Ý nghĩa | Xử lý |
|---|---|---|
| K-FT LỖI chữ thừa | `lines[].ja` có chữ không có trong lời thoại | sửa `ja` về đúng lời thoại (lỗi tác tử TẠO) |
| K-FT cảnh báo thiếu | còn đoạn lời thoại chưa vào `lines` | nếu là câu hỏi / lựa chọn / lời dẫn đề ("1番", "まず話を聞いてください") Python cắt sót → bỏ qua, ghi `[Ghi chú]`; nếu là lượt thoại → thêm vào (lỗi tác tử TẠO) |
| K-FT câu con 2 | full_translation phải giống câu con 1 | sửa ở **câu con 1**; `s1_claude_goi` / `s1_kiem_tra` tự đồng bộ câu con 2 |
| K-IM / K-LC / K-DA / K-KI | sai ánh xạ | sửa |
| K-QT, K-AN | số câu trích / analysis khác lời giải | xem lại – thường là lỗi tác tử TẠO |
| K-TD | câu trích không thấy trong lời thoại | mục 3 #3 (hoặc lỗi gõ lời thoại – bỏ qua) |
| K-Q | `question.ja` khác đề xuất | xác nhận câu hỏi đúng của câu con này |
| Độ phủ tiếng Việt < 97% | JSON thiếu chữ của lời giải | tìm phần bị bỏ sót |
| Từ thừa (cảnh báo) | thường do bỏ nhãn / bài 2 câu hỏi | xem nhanh, thường bỏ qua |

## 5. Âm Hán Việt – như các dạng trước (Python dò; câu có âm Hán Việt không dịch).

## Checklist

- [ ] Lời thoại: đủ lượt, đúng thứ tự, `ja` nguyên văn, `speaker` đúng, nghĩa đúng lượt, (i)/(ii) giữ, không lẫn câu hỏi / lựa chọn.
- [ ] `question` đúng câu con; `options[i]`: `option_ja` đúng, `meaning`, `quotes` (ja + nghĩa), `analysis` đủ, `is_match` theo lời giải.
- [ ] `key_info` (khuôn B) = khối Thông tin; khuôn khác `null`. `summary = null`; `correct` theo `dap_an_so`.
- [ ] Đã **tự giải** câu hỏi từ lời thoại và so với lời giải (mục 3 #4, #5).
- [ ] Khuôn B / C đã gắn cờ `thieu_noi_dung`.
