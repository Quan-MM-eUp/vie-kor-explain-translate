# Sổ tay chạy – dạng 05 Từ vựng: Hình thành từ (cho phiên Claude mới)

> Viết 2026-10-08. Tổng **209 mẫu**. Mẫu 1–100 đã có bản GPT + Claude kiểm tra (56 CTV đã duyệt – kho `da_duyet/`, 25 chờ CTV Nhật, **19 đã chốt VI nhưng CHƯA dịch Hàn**); từ 2026-10-08 bản tạo (GĐ1 + GĐ2) do tác tử TẠO Claude làm. Mục đích: một cuộc trò chuyện Cowork **mới** chỉ cần đọc **file này + `NHAT_KY.md`** là chạy tiếp được, **không đọc lại cả project**.
> Câu mở đầu người dùng gõ: **"Đọc dang_bai/05_tu_vung_hinh_thanh_tu/SO_TAY_CHAY.md rồi chạy dạng 05 mẫu X đến Y"**.
> Trả lời người dùng bằng **tiếng Việt**.

---

## 0. Khởi động phiên (làm theo thứ tự, không làm thêm)

1. Nạp công cụ: ToolSearch `select:mcp__remote-devices__device_bash`. Mọi lệnh chạy trên máy người dùng bằng công cụ này.
2. `DANG=$HOME/mnt/Vie-Kor/dang_bai/05_tu_vung_hinh_thanh_tu` – **mọi lệnh `cd $DANG` trước** (mỗi lần gọi là shell mới).
   Công cụ chung gọi bằng `python3 ../../pipeline_chung/cong_cu/<tên>.py` (gọi tắt `CC/<tên>.py` trong sổ tay).
3. Đọc `NHAT_KY.md` (lũy kế, quyết định đã chốt, cách dịch đã thống nhất).
4. `python3 CC/tien_do.py` → xác nhận lô X–Y chưa làm / đang dở ở bước nào (xem mục 6 nếu đang dở).
5. Chỉ mở thêm file khi sổ tay bảo. Hai hướng dẫn chuẩn phải đọc **một lần mỗi phiên** trước khi soát: `prompts/s1_claude_kiem_tra.md` (soát GĐ1, nhất là mục 3c–3e), `prompts/s2_claude_kiem_tra.md` (soát GĐ2). Đọc để lấy **tiêu chí và checklist**; phần "ghi `.ly_do.json` từng mẫu / xóa `_huong_dan`" trong hai prompt được **thay bằng** file đặc tả lô + `ghi_ly_do.py` (mục 4.3) – kết quả như nhau.
6. Phạm vi mẫu: `--tu X --den Y` (số thứ tự trong `thu_tu_chay.csv` = đúng thứ tự file dữ liệu) do `scripts/_dang.py` xử lý nên **không hiện trong `--help`** – vẫn dùng được với mọi script. **Không dùng `--lo`** (nghĩa là "N câu đầu theo trạng thái", không phải khoảng mẫu).
7. Phiên không có công cụ **Agent** (không tạo được tác tử TẠO) → **dừng, báo người dùng**; không tự tạo bản thay tác tử TẠO.

## 1. Quy tắc bất biến

- **Bảo mật:** không đọc / mở `.env`, không in API key. Không dùng GPT API (dạng này `config.tao_ban.nguon = "claude"`). Không chạy `git status`.
- **Không xóa file** trong thư mục máy người dùng (bị chặn). Cần bỏ file thì `mv -n` vào `_to_delete/`.
- **Nội dung lời giải sai → chỉ gắn cờ** `nghi_noi_dung`, **không sửa**. Chỉ sửa **định dạng** (`loai: sua_dinh_dang` + `nhom` + dòng `[Đã sửa định dạng] …` trong `ghi_chu_ban_goc`) và **lỗi của tác tử TẠO** so với lời giải (`sai_so_ban_goc`, `chinh_ta`, `khach_quan`, `chu_quan`). Ghi chú không kèm thay đổi JSON → dòng `[Ghi chú] …`.
- Phần THÔNG TIN THAM KHẢO: không xử lý (Python chép vào `reference_raw`), không kiểm tra, không sửa, không gắn cờ, không dịch.
- **Chạy song song nhiều dạng:** phiên này **chỉ sửa file trong `$DANG`**. **Không sửa** `pipeline_chung/`, `explanation_schema/`, file của dạng khác. Thấy cần sửa code chung → dừng, mô tả cho người dùng để xử lý ở cuộc trò chuyện điều phối. Được sửa `scripts/_dang.py` của dạng 05 khi lỗi tách lời giải (mục 6), sau khi báo người dùng.
- Ngữ cảnh: tối đa **3 lô (30 mẫu) mỗi cuộc trò chuyện**; sau đó đề nghị người dùng mở cuộc trò chuyện mới.

## 2. Hai tác tử

- **Tác tử TẠO (Claude A)** = tác tử con (Agent tool, `subagent_type: "general-purpose"`, `model: "opus"`), ngữ cảnh riêng. Làm việc GPT từng làm: GĐ1 chuyển JSON, GĐ2 dịch Hàn. Lời giao việc chép **nguyên văn** từ `prompts/giao_viec_tao_gd1.md` / `prompts/giao_viec_tao_gd2.md` (thay `{{SO_CAU}}` / `{{CAU_CO_DINH}}`, bỏ dòng chú thích `<!-- -->`). Không tự soạn lời giao việc khác.
- **Tác tử KIỂM TRA** = phiên chính (bạn). Không tự tạo bản, chỉ soát + Python kiểm tra. Không để tác tử TẠO soát bài của chính nó.

## 2b. Lô đặc biệt "1–100" (làm một lần, trước lô 101–110)

19 mẫu của 1–100 đã chốt VI (`GĐ1_XONG`) nhưng chưa dịch (trước đây bị cờ chỉ vì phần Tham khảo – quy tắc 2026-10-07 bỏ cờ). Khi người dùng gõ "chạy dạng 05 mẫu 1 đến 100": **bỏ qua GĐ1** (không có mẫu nào cần tạo), làm thẳng GĐ2 bước 9–16 với `--tu 1 --den 100` (19 câu – nên giao tác tử TẠO 2 đợt bằng `--ids`: 10 + 9 câu). Mẫu `ĐÃ_DUYỆT_CTV` / `CHỜ_DUYỆT_NỘI_DUNG` tự bị bỏ qua.
`CC/tien_do.py` đếm `ĐÃ_DUYỆT_CTV` là chưa xong và gợi ý lô 1–10 – **bỏ qua gợi ý đó**; sau lô đặc biệt, lô thường bắt đầu từ 101 (đến 209).

## 3. Quy trình một lô X–Y (mặc định 10 mẫu, thứ tự theo `output/thu_tu_chay.csv`)

### GĐ1 – JSON tiếng Việt

| # | Việc | Lệnh |
|---|---|---|
| 1 | Chuẩn bị gói đầu vào | `python3 scripts/s1_claude_tao.py --chuan-bi --tu X --den Y` → in số câu N |
| 2 | Tác tử TẠO tạo JSON | Agent với `giao_viec_tao_gd1.md` ({{SO_CAU}} = N). Ghi lại "điểm khó" nó báo. |
| 3 | Nhận | `python3 scripts/s1_claude_tao.py --nhan --tu X --den Y` → phải "lỗi 0, chưa có 0" (lỗi → mục 6) |
| 4 | Chuẩn bị soát | `python3 scripts/s1_claude_goi.py --tu X --den Y` |
| 5 | Soát từng mẫu | `python3 CC/xem_gd1.py --lo X Y` (từng phần nếu dài: truyền id). So JSON với LỜI GIẢI GỐC theo mục 4. |
| 6 | Ghi kết quả soát | Viết `output/claude/ly_do_lo/gd1_X_Y.json` (mục 4.3) → `python3 CC/ghi_ly_do.py output/claude/ly_do_lo/gd1_X_Y.json` |
| 7 | Python kiểm tra | `python3 scripts/s1_kiem_tra.py --tu X --den Y` → mẫu có cờ = `CHỜ_DUYỆT_NỘI_DUNG`, còn lại `GĐ1_XONG`. `LỖI_GĐ1` → mục 6 |
| 8 | Chốt | `python3 scripts/s1_chot.py --tu X --den Y` (chỉ chốt `GĐ1_XONG`) |

### GĐ2 – tiếng Hàn (chỉ mẫu đã chốt, không cờ)

| # | Việc | Lệnh |
|---|---|---|
| 9 | Chuẩn bị | `python3 scripts/s2_claude_dich.py --chuan-bi --tu X --den Y` → số câu M (câu điền sẵn hết không cần dịch) |
| 10 | Tác tử TẠO dịch | Agent với `giao_viec_tao_gd2.md` ({{SO_CAU}} = M, {{CAU_CO_DINH}} = các dòng mục "Cách dịch đã thống nhất" của NHAT_KY; chưa có thì ghi "(chưa có)") |
| 11 | Nhận | `python3 scripts/s2_claude_dich.py --nhan --tu X --den Y` → "lỗi 0" |
| 12 | Chuẩn bị soát | `python3 scripts/s2_claude_goi.py --tu X --den Y` |
| 13 | Soát | `python3 CC/xem_gd2.py --lo X Y` (Mã \| Bản nguồn \| Tiếng Hàn) theo mục 5 |
| 14 | Ghi kết quả | `output/claude/ly_do_lo/gd2_X_Y.json` → `python3 CC/ghi_ly_do.py …` (luôn liệt kê **mọi** mẫu của GĐ2, kể cả không sửa, để xóa `_huong_dan`) |
| 15 | Python kiểm tra | `python3 scripts/s2_kiem_tra.py --tu X --den Y` → `ĐẠT`; xử lý cảnh báo D… (mục 5) rồi chạy lại đến khi hết lỗi |
| 16 | Báo cáo + nhật ký | mục 7 |

## 4. Soát GĐ1 – tiêu chí (áp dụng như mẫu 1–100)

Chuẩn: **JSON phải thể hiện đúng và đủ lời giải gốc**, và lời giải gốc phải đúng kiến thức. Hướng dẫn đầy đủ: `prompts/s1_claude_kiem_tra.md` (mục 3c, **3d – quy tắc riêng dạng 05**, 3e – gợi ý Sudachi W1/W2/F1).

Đề dạng 05: câu đề có **một chỗ trống** sát một từ; chọn **thành phần** (tiền tố / hậu tố chữ Hán, đuôi kana, động từ ghép…) ghép thành từ ghép hợp văn cảnh. Lời giải: câu đề (câu / cách đọc / nghĩa – giữ chỗ trống) → PHÂN TÍCH 4 lựa chọn (dòng nhãn `i. X (…) - nghĩa gốc` + dòng từ ghép `XY (đọc): nghĩa + nhận xét`) → LỰA CHỌN ĐÚNG (số + Câu hoàn chỉnh + Nghĩa) → THÔNG TIN THAM KHẢO (không xử lý).

### 4.1 Sửa (lỗi tác tử TẠO / định dạng)
- Tác tử TẠO đặt sai trường: tách sai phần sau `:` của dòng từ ghép (`compound.meaning` = định nghĩa, phần nhận xét → `analysis`); `option_ja` / `label_paren` / `compound.reading` sai; **`is_valid` khác điều lời giải nói** (true = lời giải giải nghĩa từ ghép, kể cả "có nghĩa nhưng không phù hợp"; false = "không có nghĩa / không tồn tại" và `compound.meaning = null`; null = không có dòng từ ghép); ký hiệu chỗ trống bị đổi / mất; thiếu ⟪ ⟫, sai `{ }` / furigana → sửa (`sai_so_ban_goc` / `khach_quan`). Mẫu 1–100: GPT sai 5 chỗ loại này.
- Lỗi gõ của bản gốc → `sua_dinh_dang` + `nhom` (hay gặp: `xuong_dong` 11, `dau_cau` 4, `khoang_trang` 3, `chinh_ta` 2) + dòng `[Đã sửa định dạng] <vị trí>: '<cũ>' → '<mới>' – <lý do>`. Một trường chỉ một loại sửa.

### 4.2 Gắn cờ `nghi_noi_dung` (không sửa) – bảng 3d
| 3d | Khi nào | `nhom` |
|---|---|---|
| 1 | Lời giải ghi "không có nghĩa / không tồn tại" cho từ ghép **có thật, thông dụng** (gợi ý W1). Từ rất hiếm / cổ → không cờ, ghi `[Ghi chú] W1 …` | `khong_ton_tai` |
| 2 | Nghĩa gốc (`gloss`) sai nghĩa thành phần trong câu này, sai từ loại / thể | `nghia_tu` / `thi_the` |
| 3 | Nghĩa từ ghép sai, lý do loại / chọn sai | `nghia_tu` / `dap_an` |
| 4 | Đáp án không hợp văn cảnh, có lựa chọn khác cũng ghép tự nhiên, phân tích mâu thuẫn đáp án | `dap_an` |
| 7 | Câu hoàn chỉnh sai (điền nhầm, sai / thiếu / thừa chữ so với câu đề – gợi ý F1; đổi đuôi hợp ngữ pháp thì không tính) | `khac` / `dap_an` |
| 8 | Nghĩa câu đề / câu hoàn chỉnh lệch câu Nhật; chỗ trống trong nghĩa câu đề đặt lệch | `nghia_cau` |
| 9 | Câu đề / cách đọc trong lời giải khác đề (cách đọc lệch thật – gợi ý W2; chữ nhiều âm đúng ngữ cảnh thì không cờ) | `cach_doc` / `khac` |
| 10 | Thiếu lựa chọn / dòng từ ghép / phần | `thieu_noi_dung` |

Thống kê mẫu 1–100: cờ theo nhóm `khac` 10 · `nghia_tu` 9 · `nghia_cau` 8 · `khong_ton_tai` 6 · `cach_doc` 4 · `thi_the` 2 · `dap_an` 1.
**Không gắn cờ khi:** gợi ý W1/W2/F1 sai (ghi `[Ghi chú] W1/W2/F1 … không gắn cờ vì …`); câu hoàn chỉnh chỉ đổi đuôi hợp ngữ pháp; bất cứ gì trong phần THAM KHẢO.

Mẫu cờ: `{"vi_tri": "Phân tích lựa chọn 3 – dòng từ ghép", "nhom": "khong_ton_tai" | "nghia_tu" | "nghia_cau" | …, "mo_ta": "(quy tắc 3d-x) <sai gì, đúng là gì>", "de_xuat": "<câu đề xuất cho CTV>"}`.

### 4.3 File đặc tả lô (một file cho cả lô – không viết script riêng)
```json
{"giai_doan": "1",
 "cau": {
  "47235_1": {},
  "47236_1": {"thay": [{"duong_dan": "$.analysis.options[1].analysis.vi", "cu": "phù hợp .", "moi": "phù hợp."}],
              "sua": [{"duong_dan": "$.analysis.options[1].analysis.vi", "loai": "sua_dinh_dang", "nhom": "dau_cau", "muc_do": "nhe", "ly_do": "thừa dấu cách trước dấu chấm"}],
              "ghi_chu_ban_goc": ["[Đã sửa định dạng] Phân tích lựa chọn 2: 'phù hợp .' → 'phù hợp.' – thừa dấu cách"],
              "nghi_noi_dung": [{"vi_tri": "Phân tích lựa chọn 1 – dòng từ ghép", "nhom": "khong_ton_tai", "mo_ta": "(quy tắc 3d-1) …", "de_xuat": "…"}]},
  "47237_1": {"ghi_chu_ban_goc": ["[Ghi chú] W2 lựa chọn 2: 市場 đọc いちば đúng ngữ cảnh – không gắn cờ"]}
 }}
```
(id trong ví dụ chỉ minh họa.) **Giữ lại** file đặc tả của mỗi lô. Ghi bằng python (`json.dump(..., ensure_ascii=False, indent=1)`, nội dung qua heredoc `'EOF'`). Liệt kê **mọi** mẫu của lô. `thay` chỉ dùng cho sửa chuỗi nhỏ; sửa bool (`is_valid`) / cấu trúc (`compound` = null…) thì python read-modify-write trực tiếp `output/json_vi/checked/<id>.json` rồi ghi lý do trong `sua`.

## 5. Soát GĐ2 – tiếng Hàn

Hướng dẫn đầy đủ: `prompts/s2_claude_kiem_tra.md`. Trọng tâm:
- **Nghĩa câu đề + nghĩa câu hoàn chỉnh dịch TRỰC TIẾP từ câu tiếng Nhật**; nghĩa câu đề **giữ ký hiệu chỗ trống** (cùng loại, cùng số) đặt sát từ tương ứng; phần giống nhau của hai câu dịch giống nhau.
- **Nghĩa gốc (`gloss`) / nghĩa từ ghép (`compound.meaning`)**: cụm nghĩa ngắn, đúng với chính từ tiếng Nhật (kể cả khi bản Việt lệch).
- **Trợ từ sau ⟪kana⟫ theo âm cuối cách đọc tiếng Nhật** (Python chỉ cảnh báo, phải tự soát): ん → 은/이/을/과/이라는/이라고/이며/으로; nguyên âm → 는/가/를/와/라는/라고/며/로.
- **D4 không nhất quán** (cùng vi, khác ko giữa các câu) → sửa câu mới theo bản đã duyệt trước (`output/reports/khong_nhat_quan.csv`; mẫu CTV đã duyệt trong `da_duyet/` là chuẩn).
- Phần THAM KHẢO không dịch.
- Câu cố định / thuật ngữ: NHAT_KY mục "Cách dịch đã thống nhất" + `glossary_ko.json` (đã nạp vào `_he_thong.md`).
- Sửa ko: dùng `thay` với `duong_dan` tới chuỗi `….ko` trong file đặc tả `"giai_doan": "2"`; `sua` ghi `{"duong_dan": "<đường dẫn object>", "loai": "chinh_ta", "muc_do": "nhe", "ly_do": "…"}`. JSON tiếng Việt sai → `loi_json_vi: ["[Lỗi JSON VI] <phần>: <vấn đề>"]` (mẫu quay lại GĐ1).

## 6. Sự cố thường gặp

| Hiện tượng | Xử lý |
|---|---|
| `--nhan` GĐ1 báo LỖI_KỸ_THUẬT (schema / JSON hỏng) | `python3 scripts/s1_claude_tao.py --chuan-bi --ids <id> --force` → giao lại tác tử TẠO chỉ mẫu đó → `--nhan --ids <id>` |
| `--nhan` GĐ2 báo LỖI_GĐ2 (thiếu / thừa mã, lệch nội dung) | `s2_claude_dich.py --chuan-bi --ids <id> --force` → giao lại → `--nhan --ids <id>` |
| `s1_kiem_tra` báo LỖI_GĐ1 (K…) | Đọc lỗi; sửa file checked (lỗi tác tử TẠO / định dạng) hoặc ghi chú; chạy lại `s1_kiem_tra --ids <id>` |
| Lỗi do **Python tách lời giải sai** (dòng nhãn / dòng từ ghép dính nhau, "Câu hoàn chỉnh:" dính câu…) | Báo người dùng, sửa `scripts/_dang.py` (backup trước vào `$HOME/bak05`), chạy lại `python3 scripts/s0_chuan_bi.py` (giữ thứ tự chạy), ghi vào NHAT_KY |
| `[Đã sửa định dạng]` không có `sua` tương ứng → cảnh báo | Đổi thành `[Ghi chú]` hoặc thêm `sua` |
| `s2_kiem_tra` báo `[Lỗi JSON VI]` → CẦN_SỬA_GĐ1 | `s1_claude_goi --ids <id>` (tự gắn `_huong_dan` CẦN SỬA LẠI) → sửa → `s1_kiem_tra` → `s1_chot` → GĐ2 lại |
| Lô đang dở (phiên trước dừng giữa chừng) | `CC/tien_do.py X Y` xem trạng thái từng mẫu; file `output/claude/tao_gd1_danh_sach.json` / `tao_gd2_danh_sach.json` và `_huong_dan` trong `.ly_do.json` cho biết bước nào chưa xong; chạy tiếp từ bước đó (các lệnh đều bỏ qua mẫu đã làm) |
| Tác tử TẠO mở file ngoài phạm vi | Ghi vào NHAT_KY; kết quả vẫn dùng được nếu nó không sửa file khác |

## 7. Báo cáo cuối lô (tiếng Việt, ngắn)

1. Bảng: ĐẠT n (id…), nghi nội dung n (id…).
2. Mỗi mẫu gắn cờ: 1 dòng lý do. Sửa định dạng / sửa ko: liệt kê ngắn.
3. Lũy kế (`CC/tien_do.py`).
4. Lệnh tiếp: **"Chạy dạng 05 mẫu <Y+1> đến <Y+10>"** (sau lô thứ 3 trong phiên: đề nghị mở cuộc trò chuyện mới với câu mở đầu ở đầu sổ tay).

Sau báo cáo **cập nhật `NHAT_KY.md`**: thêm dòng vào bảng lô; thêm quyết định / cách dịch mới đã thống nhất; sự cố đã gặp.

## 8. Excel CTV (khi người dùng yêu cầu)

- CTV tiếng Hàn (mẫu ĐẠT): `python3 scripts/s3_xuat_ctv.py --tu X --den Y` → `output/reports/ctv/<ngày>-CTV-05_hinh_thanh_tu….xlsx`.
- CTV tiếng Nhật (mẫu có cờ, chưa dịch): `python3 scripts/s3b_xuat_ctv_nhat.py --tu X --den Y`.
- Mẫu 1–100 đã xuất (2026-10-06): `2026-10-06-CTV-05_hinh_thanh_tu-v1-mau1-100.xlsx` (56 câu – CTV đã duyệt, đã nhập kho), `2026-10-06-CTV-NHAT-05_hinh_thanh_tu-co-mau1-100.xlsx` (44 câu bị cờ lúc đó).
- Lưu phản hồi CTV đã duyệt vào kho: `python3 scripts/s10_luu_da_duyet.py --file <excel CTV> …` (xem `da_duyet/README.md`).
