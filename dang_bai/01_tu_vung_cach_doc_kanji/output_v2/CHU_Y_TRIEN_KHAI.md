# Chú ý khi triển khai cách chia dạng mới (v2) – Dạng 01: Cách đọc kanji

Ngày bắt đầu: 2026-10-01 · Lý do: phản hồi CTV tiếng Hàn trên file 50 câu (41 Đạt · 2 Sửa nhỏ · 7 Không đạt – đa số do lỗi có sẵn trong lời giải VI gốc: sai thì/thiếu ý ở nghĩa câu đề, sai tự/tha động từ, dính câu; 35/50 câu CTV muốn có 한자음).

## 1. Phạm vi – không động vào dữ liệu cũ

- Kết quả cách chia cũ (Dạng 1/2/3) nằm ở `output/` – **giữ nguyên, không phân loại lại**.
- Cách chia mới chạy hoàn toàn trong thư mục này `output_v2/` (đã khởi tạo bằng `s0_chuan_bi.py --chon-pilot`: 1.872 câu, tất cả ĐANG_XỬ_LÝ).
- Bật/tắt bằng `config.json`:
  - `"output": "output_v2"` và `"cach_chia_dang": "v2"` → cách mới (đang bật).
  - Quay về cách cũ: `"output": "output"` và xóa `cach_chia_dang`.
- Bộ nhớ dịch (`reports/bo_nho_dich_ko.json`) **bắt đầu lại từ đầu** trong `output_v2/` (không mang bản dịch cũ sang).
- `--tu/--den` vẫn tính theo thứ tự câu trong CSV → câu số 1–70 đã chạy ở `output/` sẽ được chạy lại nếu chọn lại khoảng đó. Muốn chạy câu mới thì bắt đầu từ `--tu 71`.

## 2. Định nghĩa dạng và 2 cờ

| | Ý nghĩa | Ai quyết định |
|---|---|---|
| **Dạng 1** | Lời giải gốc **không sai định dạng** – Claude không sửa định dạng | `so_cho_sua_dinh_dang = 0` |
| **Dạng 2** | Lời giải gốc **có sai định dạng** – Claude đã sửa, có ghi chú từng chỗ | `so_cho_sua_dinh_dang > 0` |
| Cờ **nghi_noi_dung** | Claude nghi **nội dung** sai (nghĩa, thì, tự/tha động từ, cách đọc…) – **chỉ gắn cờ + đề xuất, KHÔNG sửa** | Claude (bước 1.2) |
| Cờ **han_viet** | Phần tham khảo (reference) của lời giải gốc có **âm Hán Việt** | Python tự phát hiện (`_dang.han_viet_src`) |

Dạng và cờ độc lập: một câu Dạng 1 hay Dạng 2 đều có thể có cờ.

**Quy tắc dịch: CHỈ câu KHÔNG có cờ nghi_noi_dung VÀ KHÔNG có cờ han_viet mới được dịch sang tiếng Hàn.**
`s2_dich.py` tự bỏ qua các câu có cờ (in "Bỏ qua N câu…"), kể cả khi gọi bằng `--ids`.

## 3. Trạng thái mới (sau `s1_kiem_tra.py`)

Thứ tự ưu tiên khi gán:

1. `LỖI_GĐ1` – còn lỗi kiểm tra (như cũ).
2. `CHỜ_DUYỆT_NỘI_DUNG` – có cờ nghi_noi_dung → **không dịch**, chờ CTV tiếng Nhật/bạn duyệt.
3. `CHỜ_XỬ_LÝ_HÁN_VIỆT` – có âm Hán Việt → **không dịch**, chờ quyết định cách xử lý.
4. `GĐ1_XONG` – không cờ → được `s1_chot` → `s2_dich`.

Câu có cả 2 cờ mang trạng thái CHỜ_DUYỆT_NỘI_DUNG nhưng `co_han_viet = 1` vẫn được ghi lại.
`s1_chot.py` chỉ chốt câu GĐ1_XONG; câu CHỜ_… giữ JSON ở `json_vi/checked/`.

## 4. Sửa định dạng – BẮT BUỘC ghi chú từng chỗ

- Trong `<id>.ly_do.json`, mỗi chỗ là 1 mục `"loai": "sua_dinh_dang"` có `nhom`, `path`, `cu`, `moi`, `ly_do`.
- Mỗi chỗ phải có 1 dòng tương ứng trong `ghi_chu_ban_goc`:
  `[Đã sửa định dạng] <chỗ>: 'cũ' → 'mới' – lý do`
  ví dụ: `[Đã sửa định dạng] options[2].analysis: 'trường học.Học sinh' → 'trường học. Học sinh' – tách câu dính`
- Thiếu dòng ghi chú → `s1_kiem_tra` báo lỗi. Không dùng `sua_ban_goc` (cách cũ) nữa – dùng sẽ bị cảnh báo.
- Nhóm (`nhom`) hợp lệ: `dinh_chu` (dính câu/dính chữ) · `xuong_dong` · `lap_tu` · `chinh_ta` · `dau_cau` · `khoang_trang` · `gach_chan` · `ky_tu` · `cach_doc_lan_so` · `khac`.
- `cach_doc_lan_so` (cách đọc bị lẫn số ①②③/1.2.3 vào chữ) **tính là lỗi định dạng**. Mọi cách đọc sai khác (sai âm, sai trường âm…) là **lỗi nội dung** → gắn cờ, không sửa.
- `..` (hai dấu chấm) trong bản gốc **không sửa**.
- Sửa định dạng không được đổi nghĩa; thay đổi > 50% hoặc > 30 từ ở một chỗ sẽ bị cảnh báo (`src_fix_warnings`).
- Lỗi GPT gây ra (`sai_so_ban_goc`, `chinh_ta`, `khach_quan`) vẫn sửa như cũ, **không** tính vào Dạng 2.

## 5. Nghi sai nội dung – BẮT BUỘC ghi rõ nghi ở phần nào

- Trong `<id>.ly_do.json`: `"nghi_noi_dung": [{"vi_tri": …, "nhom": …, "mo_ta": …, "de_xuat": …}]`
  - `vi_tri`: đường dẫn trường JSON, ví dụ `question.meaning`, `options[1].analysis`, `reference.meaning`.
  - `mo_ta`: sai gì; `de_xuat`: nên sửa thế nào (CTV quyết định, Claude không tự sửa).
- Hiển thị: `[Nghi sai nội dung] question.meaning (nghia_cau): thiếu thì quá khứ "đã" – đề xuất: "Hôm qua tôi đã…"`
- Nhóm hợp lệ: `nghia_cau` (sai thì/thiếu ý) · `thi_the` · `tu_tha_dong_tu` · `nghia_tu` · `khong_ton_tai` · `dong_am` · `chu_han` · `cach_doc` · `dap_an` · `thieu_noi_dung` · `khac`.
- Chỉ gắn cờ khi có căn cứ; không gắn cho chuyện văn phong.

### 5a. Gỡ cờ sau khi CTV tiếng Nhật duyệt

- CTV nói **không sai** → Claude xóa mục trong `nghi_noi_dung`.
- CTV nói **sai** → Claude sửa JSON theo CTV, ghi `"loai": "sua_theo_ctv"` + `nhom` và dòng `[Đã sửa theo CTV] <chỗ>: 'cũ' → 'mới' – <CTV nói gì>` (thiếu ghi chú → cảnh báo). Không tính vào Dạng 2; báo cáo ở cột `da_sua_theo_ctv` của `phan_loai.csv`.
- Chạy lại `python scripts/s1_kiem_tra.py --ids …` → hết cờ thành GĐ1_XONG → `s1_chot` → `s2_dich`.

## 6. Âm Hán Việt

- Python nhận diện ở lời giải gốc: "âm Hán Việt …", "chữ Hán NÃO", "選 (せん) - TUYỂN". Bỏ qua chữ viết tắt trong `HV_BO_QUA`.
- Kết quả thử trên 1.872 câu: 63 câu, đều đúng.
- Giới hạn: kiểu viết khác 3 mẫu trên có thể lọt. Claude thấy thì ghi chú `[Bản gốc VI] Có âm Hán Việt …` và báo lại để bổ sung mẫu nhận diện vào `HV_SRC_RES` (không ghi vào `nghi_noi_dung`).
- Câu Hán Việt **chờ quyết định** (bỏ âm HV, đổi sang 한자음, hay giữ) – chưa dịch.

## 7. Gợi ý Python cho Claude (`_dang.format_hints`) – chỉ là gợi ý

Gợi ý `[Nghi dính câu/định dạng]` trong file việc của `s1_claude_goi`: dính câu (`…)Chữ hoa`, `chữ.Chữ`), dính mục đánh số (`…. 2. `), lặp từ, dấu câu thừa (` ,` `,)` `( .`).
Có thể báo nhầm (tên riêng, viết tắt) và bỏ sót → Claude vẫn phải đọc cả lời giải.

## 8. Các bước chạy (từ thư mục dạng bài, ví dụ câu 71–80)

| Bước | Lệnh | Ai chạy |
|---|---|---|
| 1.1 | `python scripts/s1_gpt_chuyen.py --tu 71 --den 80` | Bạn (gọi API) |
| 1.2a | `python scripts/s1_claude_goi.py --tu 71 --den 80` | Claude |
| 1.2b | Claude sửa `json_vi/checked/<id>.json` + `<id>.ly_do.json` (10 câu/lần) | Claude |
| 1.3–1.4 | `python scripts/s1_kiem_tra.py --tu 71 --den 80` | Claude |
| 1.5 | `python scripts/s1_chot.py --tu 71 --den 80` (chỉ câu GĐ1_XONG) | Bạn/Claude |
| 2.1–2.3 | `python scripts/s2_dich.py --tu 71 --den 80` (tự bỏ câu có cờ) | Bạn (gọi API) |
| 2.4 | `python scripts/s2_claude_goi.py …` → Claude sửa → `python scripts/s2_kiem_tra.py …` | Claude |
| 2.7 | `python scripts/s8_phan_loai.py --tu 71 --den 80` | Claude |
| 3 | `python scripts/s3_xuat_ctv.py --tu 71 --den 80 --dang 1` (hoặc `--dang 2`) – CTV tiếng Hàn, chỉ câu đã dịch | Claude |
| 3c | `python scripts/s3b_xuat_ctv_nhat.py --tu 71 --den 80` – CTV tiếng Nhật: **chỉ câu bị cờ** (nghi sai nội dung và/hoặc Hán Việt), chạy được ngay sau 1.3–1.4. Câu Dạng 2 không cờ không đưa vào (đi dịch như thường) | Claude |

Kết quả phân loại (`output_v2/reports/phan_loai/`): `phan_loai.csv`, `dang_1.csv`, `dang_2.csv`, `nghi_noi_dung.csv`, `han_viet.csv`, `chi_tiet/<id>.json`, `tong_hop.md`.
Bị ngắt giữa chừng (hết key…) → chạy lại đúng lệnh cũ; câu đã xong tự bỏ qua.

## 8a. Quyết định đã chốt (2026-10-02)

- Chạy lại từ mẫu 1, **gọi GPT lại từ đầu** (không dùng bản GPT cũ ở `output/`). 49 mẫu trong kho `da_duyet/` mang trạng thái `ĐÃ_DUYỆT_CTV` – không chạy lại.

- Đánh số giữ nguyên: **Dạng 1 = không sai định dạng**, **Dạng 2 = có sửa định dạng**.
- Cách đọc lẫn số ①②③ = lỗi định dạng (Claude sửa); đọc sai âm thật = lỗi nội dung (chỉ gắn cờ).
- **Xử lý từng mẫu riêng biệt**: không áp cờ, không gợi ý theo nhóm câu dùng chung một câu tiếng Nhật (342 câu tiếng Nhật dùng chung cho 1.079 câu hỏi – mỗi câu có lời giải viết riêng). Dữ liệu dạng 01 chỉ có 1 câu con / câu hỏi.
- Đợt đầu: chạy thử 30–50 câu để đo tỷ lệ gắn cờ; CTV tiếng Nhật xem thêm khoảng 10% câu không có cờ để đo tỷ lệ Claude bỏ sót.

## 9. Việc còn mở

- Cách xử lý câu Hán Việt (bỏ / chuyển 한자음 / giữ).
- Sau khi CTV tiếng Nhật duyệt câu CHỜ_DUYỆT_NỘI_DUNG: Claude sửa JSON theo ý CTV, xóa mục tương ứng trong `nghi_noi_dung` của `<id>.ly_do.json`, chạy lại `s1_kiem_tra` → câu hết cờ thành GĐ1_XONG và mới được dịch.
- Phản hồi CTV tiếng Hàn: 兄/姉 → 형/오빠, 누나/언니 tùy người nói; "지칭" thay cho "부르는 방식" – nên bổ sung vào glossary/prompt GĐ2.

## 10. Lịch sử

| Ngày | Thay đổi |
|---|---|
| 2026-10-01 | Tạo `output_v2/`, bật `cach_chia_dang = v2`; prompt `s1_claude_kiem_tra.md` viết lại theo v2 (bản cũ: `s1_claude_kiem_tra.v1.md`). |
