# Hướng dẫn chạy pipeline – Dạng 01: Cách đọc kanji

Chạy mọi lệnh **từ thư mục `dang_bai/01_tu_vung_cach_doc_kanji`**. Các bước có gọi GPT (1.1 và 2.1) **chỉ chạy khi bạn quyết định**; luôn có `--dry-run` để xem prompt trước mà không gọi API.

Phạm vi câu cho mọi script: `--pilot` (câu trong `output/pilot.csv`) · `--ids 393_1,1150_1` · `--tu 1 --den 50` (mẫu thứ 1 đến 50 theo thứ tự trong file dữ liệu CSV; chỉ lấy các câu đang ở trạng thái phù hợp với bước đó, nên chạy lại cùng đoạn sẽ không làm lại câu đã xong) · `--lo 200` (200 câu tiếp theo) · `--tat-ca`.

## ĐANG DÙNG: cách chia dạng v2 (thư mục `output_v2/`, từ 2026-10-01)

`config.json` đang đặt `"output": "output_v2"` và `"cach_chia_dang": "v2"` → mọi lệnh bên dưới đọc/ghi `output_v2/` (đọc "output/" trong bảng là `output_v2/`). Kết quả cũ ở `output/` không bị động tới.

- Các bước và lệnh giữ nguyên. Khác biệt: sau bước 1.3–1.4, câu có cờ **nghi sai nội dung** → `CHỜ_DUYỆT_NỘI_DUNG`, câu có **âm Hán Việt** → `CHỜ_XỬ_LÝ_HÁN_VIỆT`; hai loại này **không được chốt và không được dịch** (`s2_dich.py` tự bỏ qua).
- Bước 2.7 (`s8_phan_loai.py`): Dạng 1 = không sai định dạng, Dạng 2 = Claude có sửa định dạng; thêm `nghi_noi_dung.csv`, `han_viet.csv`.
- Bước 3c (`s3b_xuat_ctv_nhat.py`, chạy ngay sau bước 1.3–1.4, không cần chờ dịch): file `…-CTV-NHAT-…-co.xlsx` gồm **chỉ các câu bị cờ** (nghi sai nội dung và/hoặc âm Hán Việt). Cột chính: Giải thích VI gốc · Giải thích VI JSON mới · Chi tiết lỗi format đã sửa (Dạng 2; Dạng 1 để trống) · Nghi ngờ sai nội dung (có/không) · Chi tiết nghi ngờ · Từ Hán Việt (có/không) · VI — CTV SỬA TẠI ĐÂY · Kết quả (Sai – đã sửa / Không sai / Khác) · Ghi chú CTV. Câu Hán Việt: CTV chỉ xác nhận, chờ leader quyết định.
- Câu không cờ (Dạng 1 và Dạng 2) → dịch → `s3_xuat_ctv.py --dang 1|2` gửi CTV tiếng Hàn; có cột "Chi tiết lỗi format đã sửa" ngay trước "Giải thích VI JSON mới" (Dạng 1 để trống).
- Lưu ý chi tiết: `output_v2/CHU_Y_TRIEN_KHAI.md`. Muốn quay lại cách cũ: đặt `"output": "output"` và xóa `cach_chia_dang`.

## Chuẩn bị một lần

1. File `.env` có `OPENAI_API_KEY=…` và `OPENAI_BASE_URL=https://llm.eup.ai/v1` (đặt ở `Vie-Kor/.env` hoặc dùng lại `Vie-Kor/test_5dang/.env`). Không dán key vào khung chat.
2. Xem tên model trên gateway: `python -m pipeline_chung.gpt_client --list-models` (chạy từ thư mục `Vie-Kor`) rồi điền vào `config.json` → `gpt.model`. Model không nhận `temperature` thì giữ `null`.
3. Thư viện: `pip install jsonschema openpyxl`.
4. Nếu gateway không nhận `minItems/maxItems/minimum/maximum` ở chế độ strict: `python ../../pipeline_chung/schema_tools.py schema/vocab_kanji_reading.v2.json --bo-rang-buoc`.

## Các bước

| Bước | Việc | Lệnh | Nói với Claude |
|---|---|---|---|
| 0 | Chuẩn hóa 1.872 câu, gắn cờ, chọn pilot | `python scripts/s0_chuan_bi.py --chon-pilot` | "Chạy bước 0 dạng 01" |
| 1.1 | GPT chuyển sang JSON tiếng Việt | `python scripts/s1_gpt_chuyen.py --pilot --dry-run` rồi bỏ `--dry-run` | "Chạy bước 1.1 dạng 01 cho pilot" |
| 1.2a | Chuẩn bị việc cho Claude | `python scripts/s1_claude_goi.py --pilot` | (Claude tự chạy) |
| 1.2b | **Claude kiểm tra và sửa** | – | "Kiểm tra giai đoạn 1 dạng 01 theo prompts/s1_claude_kiem_tra.md" |
| 1.3–1.4 | Python kiểm tra lần cuối, gắn trạng thái | `python scripts/s1_kiem_tra.py --pilot` | (Claude tự chạy sau 1.2b) |
| 1.5 | **Bạn duyệt**, chốt JSON tiếng Việt | `python scripts/s1_chot.py --pilot [--tra-lai id1,id2 --ly-do "…"]` | "Chốt giai đoạn 1, trả lại câu …" |
| 2.1–2.3 | Tách trường → GPT dịch → ghép | `python scripts/s2_dich.py --pilot --dry-run` rồi bỏ `--dry-run` | "Chạy bước 2.1 dạng 01 cho pilot" |
| 2.4a | Chuẩn bị việc cho Claude | `python scripts/s2_claude_goi.py --pilot` | (Claude tự chạy) |
| 2.4b | **Claude kiểm tra và sửa bản dịch** | – | "Kiểm tra giai đoạn 2 dạng 01 theo prompts/s2_claude_kiem_tra.md" |
| 2.5–2.6 | Python kiểm tra lần cuối, chốt bản dịch | `python scripts/s2_kiem_tra.py --pilot` | (Claude tự chạy sau 2.4b) |
| 3 | Xuất Excel cho CTV | `python scripts/s3_xuat_ctv.py --pilot` | "Xuất file CTV dạng 01" |
| 2.7 | **Phân loại kết quả thành 3 dạng** (1 – GĐ1 Claude không sửa lỗi bản gốc; 2 – GĐ1 Claude đã sửa lỗi bản gốc [Đã sửa bản gốc]; 3 – GĐ2 còn âm Hán Việt, kèm `dang_gd1`; lỗi pipeline khác → `chua_phan_loai.csv`) | `python scripts/s8_phan_loai.py --tu 1 --den 40` | "Phân loại kết quả dạng 01" |
| 3b | Xuất Excel CTV **riêng Dạng 1** (`--dang 1`) hoặc **riêng Dạng 2** (thêm cột S "Thay đổi so với lời giải gốc khi chuyển sang JSON": ① GPT đã đổi gì, ② Claude sửa lỗi GPT, ③ Claude sửa lỗi có sẵn trong bản gốc – kèm ghi chú [Đã sửa bản gốc], ④ vấn đề bản gốc chưa sửa) – chạy sau bước 2.7 | `python scripts/s3_xuat_ctv.py --tu 1 --den 40 --dang 2` | "Xuất file CTV dạng 2" |
| 3c | Xuất Excel cho **CTV tiếng Nhật** kiểm tra chỗ Claude sửa lỗi bản gốc (mọi câu có `dang_gd1` = 2, kể cả câu Dạng 3; không có tiếng Hàn). Cột chính: Giải thích VI gốc → Giải thích VI JSON mới → Thay đổi… (GĐ1) (chỉ ghi các dòng [Đã sửa bản gốc] và [Bản gốc VI]) → Kết quả (Đồng ý / Đồng ý một phần / Không đồng ý) → Ghi chú CTV – chạy sau bước 2.7 | `python scripts/s3b_xuat_ctv_nhat.py --tu 1 --den 30` | "Xuất file CTV tiếng Nhật dạng 2" |
| 4 | **Lưu mẫu CTV đã chấp nhận vào kho `da_duyet/`** (kiểm tra JSON khớp bản CTV đã xem; bước 1.1 và 2.1 sau đó tự bỏ qua các mẫu này, thêm `--ca-da-duyet` để vẫn chạy) | `python scripts/s10_luu_da_duyet.py --file <excel CTV> --nguon output` | "Lưu các mẫu CTV đã chấp nhận" |
| – | Báo cáo số liệu so với tiêu chí đạt (tỷ lệ ĐẠT, chỗ Claude sửa, token) | `python scripts/s9_bao_cao.py --pilot` | "Báo cáo kết quả pilot dạng 01" |

## Kết quả chính (thư mục `output/`)

| File | Nội dung |
|---|---|
| `reports/phan_loai/` | `phan_loai.csv` (mọi câu đã xong + dạng 1/2/3), `dang_1.csv`, `dang_2.csv`, `dang_3.csv`, `chi_tiet/<id>.json` (so chữ bản gốc ↔ GPT đầy đủ, nhật ký Claude), `tong_hop.md` |
| `reports/can_kiem_tra.csv` | **Danh sách câu cần người xem** (tự tạo lại mỗi lần script lưu trạng thái), cột `nhom`: 1 – lỗi pipeline (LỖI_KỸ_THUẬT, LỖI_GĐ1, CẦN_SỬA_GĐ1, LỖI_GĐ2) · 2 – chờ bạn duyệt GĐ1 · 3 – đã chạy được nhưng có ghi chú [Bản gốc VI] / [Đã sửa bản gốc]; kèm cột `viec_can_lam`, `loi`, `canh_bao` |
| `reports/trang_thai.csv` | Mỗi câu một dòng: trạng thái, lỗi, cảnh báo, cờ, số chỗ Claude sửa, ghi chú bản gốc, model/prompt đã dùng |
| `samples/norm/<id>.json` | Đầu vào đã chuẩn hóa + cờ |
| `json_vi/gpt → checked → final/` | JSON tiếng Việt: bản GPT → bản Claude sửa → bản đã duyệt |
| `json_ko/gpt → checked → final/` | JSON tiếng Hàn tương tự (+ `.map.json` bảng đối chiếu mã ↔ đường dẫn) |
| `reports/claude_sua/vi|ko/<id>.json` | Nhật ký Claude đã sửa (trước/sau do Python tính, lý do do Claude ghi) |
| `reports/validate_vi.json`, `check_ko.json` | Chi tiết kiểm tra Python (kèm kết quả trên bản GPT để đo) |
| `reports/co_ban_goc.csv`, `ruby_hong_ban_goc.csv`, `doc_trong_ngoac.csv` | Vấn đề của bản gốc – gửi nhóm sửa dữ liệu |
| `reports/khong_nhat_quan.csv` | Cùng câu tiếng Việt nhưng dịch khác nhau giữa các câu (D4) |
| `reports/bo_nho_dich_ko.json` | Bộ nhớ dịch (từ các câu ĐẠT) |
| `reports/usage_gd1.jsonl` | Token từng câu giai đoạn 1 (để tính chi phí) |
| `reports/ctv/<ngày>-CTV-01_cach_doc_kanji.xlsx` | File gửi CTV |
| `reports/cau_loi_gd2.csv` | Câu lỗi giai đoạn 2 (không gửi CTV) |

## Trạng thái

`ĐANG_XỬ_LÝ` → (GĐ1) `LỖI_KỸ_THUẬT` · `LỖI_GĐ1` · `CẦN_SỬA_GĐ1` · `GĐ1_XONG` → (GĐ2) `LỖI_GĐ2` · `ĐẠT`.

| Trạng thái | Xử lý tiếp |
|---|---|
| `LỖI_KỸ_THUẬT` | Chạy lại bước 1.1 (script tự lấy các câu này) |
| `LỖI_GĐ1` | Dừng. Xem cột `loi`; sửa prompt rồi chạy lại cả nhóm (`--ids … --force` ở bước 1.1), hoặc gửi nhóm sửa dữ liệu gốc |
| `CẦN_SỬA_GĐ1` (bạn trả lại ở bước 1.5, hoặc Claude phát hiện `[Lỗi JSON VI]` ở bước 2.4) | Quay về bước 1.2: `s1_claude_goi.py` đưa lại câu cho Claude (giữ bản đang sửa và lý do cũ) → `s1_kiem_tra.py` → `s1_chot.py`. Bước 2.1 tự nhận ra JSON tiếng Việt đã đổi và dịch lại |
| `LỖI_GĐ2` | Lỗi ghép / lỗi kỹ thuật: chạy lại bước 2.1. Lỗi kiểm tra: Claude sửa tiếp ở bước 2.4 hoặc chạy lại 2.1 với `--force` |
