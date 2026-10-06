# Hướng dẫn chạy pipeline – Dạng 02: Thay đổi cách nói

## ⚑ Cách làm hiện tại (nâng cấp 2026-10-05 – giống dạng 01 / pipeline_v3)

| Điểm | Cách làm |
|---|---|
| Chia dạng | **v2**: Dạng 1 (không lỗi định dạng) / Dạng 2 (Claude sửa định dạng, ghi chú từng chỗ). Lỗi nội dung **chỉ gắn cờ** `nghi_noi_dung`; âm Hán Việt gắn cờ |
| Chặn dịch | Mọi câu có cờ (nghi sai nội dung / Hán Việt) **không dịch** → Excel CTV tiếng Nhật (`s3b_xuat_ctv_nhat.py`). Chỉ câu không cờ được dịch → Excel CTV tiếng Hàn (`s3_xuat_ctv.py`) |
| Dịch | `question.meaning` dịch **trực tiếp từ câu tiếng Nhật**; phân tích của từng lựa chọn dịch từ tiếng Việt nhưng câu "Nghĩa là "…"" dịch **theo lựa chọn tiếng Nhật**; tham khảo, mở đầu, kết luận dịch từ tiếng Việt |
| Quy tắc Claude GĐ1 | `prompts/s1_claude_kiem_tra.md` (v3): quy tắc chung 3c (từ phản hồi CTV tiếng Hàn) + quy tắc riêng dạng 02 mục 3d (đáp án không đồng nghĩa, phân tích mâu thuẫn đáp án, "Nghĩa là" sai, danh sách đồng nghĩa sai…) |
| Kiểm tra mới | D6 (cảnh báo: nghĩa lựa chọn mất phủ định / bị động), D7 (lỗi: số `{ }` Nghĩa câu ≠ câu Nhật), dò Hán Việt kiểu "chữ TRỊ" |
| Kho đã duyệt | `da_duyet/` – mẫu trong kho được bỏ qua; thêm bằng `scripts/s10_luu_da_duyet.py --file <excel CTV>` |

**Chạy thử 10 mẫu** (bạn chạy 2 lệnh gọi GPT, Claude làm phần còn lại):

```
cd C:\Users\MaiMinhQuan\Desktop\Vie-Kor\dang_bai\02_tu_vung_thay_doi_cach_noi
python scripts/s1_gpt_chuyen.py --ids 2610_1,54417_1,1636_1,3119_1,21956_1,19541_1,19762_1,10760_1,22028_1,19372_1
   → Claude: s1_claude_goi → kiểm tra → s1_kiem_tra → s1_chot
python scripts/s2_dich.py --ids 2610_1,54417_1,1636_1,3119_1,21956_1,19541_1,19762_1,10760_1,22028_1,19372_1
   → Claude: s2_claude_goi → kiểm tra → s2_kiem_tra
python scripts/s3_xuat_ctv.py --ids …          # Excel CTV tiếng Hàn (câu ĐẠT)
python scripts/s3b_xuat_ctv_nhat.py --ids …    # Excel CTV tiếng Nhật (câu bị cờ)
```

Phần dưới đây là hướng dẫn chi tiết các bước (vẫn đúng; trạng thái có thêm `CHỜ_DUYỆT_NỘI_DUNG`, `CHỜ_XỬ_LÝ_HÁN_VIỆT`, `ĐÃ_DUYỆT_CTV`).

---


Chạy mọi lệnh **từ thư mục `dang_bai/02_tu_vung_thay_doi_cach_noi`**. Các bước có gọi GPT (1.1 và 2.1) **chỉ chạy khi bạn quyết định**; luôn có `--dry-run` để xem prompt trước mà không gọi API.

Phạm vi câu cho mọi script: `--pilot` (câu trong `output/pilot.csv`) · `--ids 2610_1,54417_1` · `--tu 1 --den 50` (mẫu thứ 1 đến 50 theo thứ tự trong file dữ liệu CSV; chỉ lấy các câu đang ở trạng thái phù hợp với bước đó, nên chạy lại cùng đoạn sẽ không làm lại câu đã xong) · `--lo 200` (200 câu tiếp theo) · `--tat-ca`.

## Chuẩn bị một lần

1. File `.env` có `OPENAI_API_KEY=…` và `OPENAI_BASE_URL=https://llm.eup.ai/v1` (đặt ở `Vie-Kor/.env` – mẫu: `Vie-Kor/.env.example`). Không dán key vào khung chat.
2. Xem tên model trên gateway: `python -m pipeline_chung.gpt_client --list-models` (chạy từ thư mục `Vie-Kor`) rồi điền vào `config.json` → `gpt.model`. Model không nhận `temperature` thì giữ `null`.
3. Thư viện: `pip install jsonschema openpyxl`.
4. Nếu gateway không nhận `minItems/maxItems/minimum/maximum` ở chế độ strict: `python ../../pipeline_chung/schema_tools.py schema/vocab_synonym.v2.json --bo-rang-buoc`.

## Các bước

| Bước | Việc | Lệnh | Nói với Claude |
|---|---|---|---|
| 0 | Chuẩn hóa 1.028 câu (in đậm / gạch chân → `{ }`), tách phần, gắn cờ, chọn pilot | `python scripts/s0_chuan_bi.py --chon-pilot` | "Chạy bước 0 dạng 02" |
| 1.1 | GPT chuyển sang JSON tiếng Việt | `python scripts/s1_gpt_chuyen.py --pilot --dry-run` rồi bỏ `--dry-run` | "Chạy bước 1.1 dạng 02 cho pilot" |
| 1.2a | Chuẩn bị việc cho Claude | `python scripts/s1_claude_goi.py --pilot` | (Claude tự chạy) |
| 1.2b | **Claude kiểm tra và sửa** | – | "Kiểm tra giai đoạn 1 dạng 02 theo prompts/s1_claude_kiem_tra.md" |
| 1.3–1.4 | Python kiểm tra lần cuối, gắn trạng thái | `python scripts/s1_kiem_tra.py --pilot` | (Claude tự chạy sau 1.2b) |
| 1.5 | **Bạn duyệt**, chốt JSON tiếng Việt | `python scripts/s1_chot.py --pilot [--tra-lai id1,id2 --ly-do "…"]` | "Chốt giai đoạn 1, trả lại câu …" |
| 2.1–2.3 | Tách trường → GPT dịch → ghép | `python scripts/s2_dich.py --pilot --dry-run` rồi bỏ `--dry-run` | "Chạy bước 2.1 dạng 02 cho pilot" |
| 2.4a | Chuẩn bị việc cho Claude | `python scripts/s2_claude_goi.py --pilot` | (Claude tự chạy) |
| 2.4b | **Claude kiểm tra và sửa bản dịch** | – | "Kiểm tra giai đoạn 2 dạng 02 theo prompts/s2_claude_kiem_tra.md" |
| 2.5–2.6 | Python kiểm tra lần cuối, chốt bản dịch | `python scripts/s2_kiem_tra.py --pilot` | (Claude tự chạy sau 2.4b) |
| 3 | Xuất Excel cho CTV | `python scripts/s3_xuat_ctv.py --pilot` | "Xuất file CTV dạng 02" |
| – | Báo cáo số liệu so với tiêu chí đạt (tỷ lệ ĐẠT, chỗ Claude sửa, token) | `python scripts/s9_bao_cao.py --pilot` | "Báo cáo kết quả pilot dạng 02" |

## Kết quả chính (thư mục `output/`)

| File | Nội dung |
|---|---|
| `reports/can_kiem_tra.csv` | **Danh sách câu cần người xem** (tự tạo lại mỗi lần script lưu trạng thái), cột `nhom`: 1 – lỗi pipeline (LỖI_KỸ_THUẬT, LỖI_GĐ1, CẦN_SỬA_GĐ1, LỖI_GĐ2) · 2 – chờ bạn duyệt GĐ1 · 3 – đã chạy được nhưng có ghi chú [Bản gốc VI]; kèm cột `viec_can_lam`, `loi`, `canh_bao` |
| `reports/trang_thai.csv` | Mỗi câu một dòng: trạng thái, lỗi, cảnh báo, cờ, số chỗ Claude sửa, ghi chú bản gốc, model/prompt đã dùng |
| `samples/norm/<id>.json` | Đầu vào đã chuẩn hóa + cờ |
| `json_vi/gpt → checked → final/` | JSON tiếng Việt: bản GPT → bản Claude sửa → bản đã duyệt |
| `json_ko/gpt → checked → final/` | JSON tiếng Hàn tương tự (+ `.map.json` bảng đối chiếu mã ↔ đường dẫn) |
| `reports/claude_sua/vi|ko/<id>.json` | Nhật ký Claude đã sửa (trước/sau do Python tính, lý do do Claude ghi) |
| `reports/validate_vi.json`, `check_ko.json` | Chi tiết kiểm tra Python (kèm kết quả trên bản GPT để đo) |
| `reports/co_ban_goc.csv`, `ruby_hong_ban_goc.csv`, `doc_trong_ngoac.csv`, `danh_dau_rac.csv` | Vấn đề của bản gốc – gửi nhóm sửa dữ liệu |
| `reports/khong_nhat_quan.csv` | Cùng câu tiếng Việt nhưng dịch khác nhau giữa các câu (D4) |
| `reports/bo_nho_dich_ko.json` | Bộ nhớ dịch (từ các câu ĐẠT) |
| `reports/usage_gd1.jsonl` | Token từng câu giai đoạn 1 (để tính chi phí) |
| `reports/ctv/<ngày>-CTV-02_thay_doi_cach_noi.xlsx` | File gửi CTV |
| `reports/cau_loi_gd2.csv` | Câu lỗi giai đoạn 2 (không gửi CTV) |

## Trạng thái

`ĐANG_XỬ_LÝ` → (GĐ1) `LỖI_KỸ_THUẬT` · `LỖI_GĐ1` · `CẦN_SỬA_GĐ1` · `GĐ1_XONG` → (GĐ2) `LỖI_GĐ2` · `ĐẠT`.

| Trạng thái | Xử lý tiếp |
|---|---|
| `LỖI_KỸ_THUẬT` | Chạy lại bước 1.1 (script tự lấy các câu này) |
| `LỖI_GĐ1` | Dừng. Xem cột `loi`; sửa prompt rồi chạy lại cả nhóm (`--ids … --force` ở bước 1.1), hoặc gửi nhóm sửa dữ liệu gốc |
| `CẦN_SỬA_GĐ1` (bạn trả lại ở bước 1.5, hoặc Claude phát hiện `[Lỗi JSON VI]` ở bước 2.4) | Quay về bước 1.2: `s1_claude_goi.py` đưa lại câu cho Claude (giữ bản đang sửa và lý do cũ) → `s1_kiem_tra.py` → `s1_chot.py`. Bước 2.1 tự nhận ra JSON tiếng Việt đã đổi và dịch lại |
| `LỖI_GĐ2` | Lỗi ghép / lỗi kỹ thuật: chạy lại bước 2.1. Lỗi kiểm tra: Claude sửa tiếp ở bước 2.4 hoặc chạy lại 2.1 với `--force` |

## Chạy thử với file test

Thêm `--test` vào mọi lệnh: dùng `data/test_02_tu_vung_thay_doi_cach_noi.csv` (5 câu: 2610, 54417, 2260, 1636, 3119) và ghi ra `output_test/` (tách khỏi `output/`). Bắt đầu bằng `python scripts/s0_chuan_bi.py --test`.
