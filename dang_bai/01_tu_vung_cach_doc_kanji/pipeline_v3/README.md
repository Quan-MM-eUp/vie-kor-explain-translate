# Pipeline v3 – Dạng 01 Cách đọc kanji (dịch Nghĩa câu + Nghĩa từ trực tiếp từ tiếng Nhật)

Dựng ngày 2026-10-05 theo phản hồi CTV tiếng Hàn (file `../da_duyet/ctv_phan_hoi/2026-10-02-CTV-01_cach_doc_kanji 02.10.2026_1.xlsx`):
bản dịch Việt → Hàn chính xác, nhưng **bản tiếng Việt sai** (mất bị động / phủ định / từ loại, dịch lệch nghĩa câu, giải thích chưa chuẩn) nên bản Hàn sai theo.

Pipeline cũ (v2: `../scripts`, `../prompts`, `../output_v2`) **giữ nguyên, không sửa**. Thư mục này là bản độc lập cho cách làm mới.

## Khác gì so với v2

| | v2 | v3 |
|---|---|---|
| GĐ1 – GPT chuyển JSON tiếng Việt | `s1_chuyen_json.v1` | **giữ nguyên** (mẫu đã chạy ở v2 lấy lại kết quả GPT, không gọi API – `s1_lay_gpt_v2.py`) |
| GĐ1 – Claude kiểm tra | quy tắc v2 | v2 + **mục 3c: 15 quy tắc nghi sai nội dung** rút ra từ lỗi CTV bắt được (`prompts/s1_claude_kiem_tra.md`) |
| Câu bị cờ (nghi sai nội dung / Hán Việt) | chặn dịch → CTV tiếng Nhật | **giữ nguyên** (chặn dịch → CTV tiếng Nhật) |
| GĐ2 – `question.meaning` (Nghĩa câu) | dịch từ tiếng Việt | **dịch trực tiếp từ `question.ja` (Câu hỏi)** |
| GĐ2 – `word.meaning` (Nghĩa từ) | dịch từ tiếng Việt, dạng từ điển | **dịch trực tiếp từ `word.ja` (Từ), theo đúng dạng trong câu** (催された → 개최되었다, 詳しく → 자세히, 惜しまない → 아끼지 않다) |
| GĐ2 – phân tích lựa chọn, tham khảo | dịch từ tiếng Việt | **giữ nguyên** (dịch từ tiếng Việt) |
| Kiểm tra Python GĐ2 | D1–D5 | trường dịch từ JA bỏ các phép so với bản Việt; thêm **D6** (cảnh báo: nghĩa từ mất phủ định / bị động), **D7** (lỗi: số `{ }` Nghĩa câu ≠ câu Nhật); D4 so Nghĩa câu theo câu Nhật |
| Claude kiểm tra GĐ2 | theo tiếng Việt | trường JA kiểm tra theo **tiếng Nhật**; Nghĩa từ (JA) mâu thuẫn với tham khảo (VI) → `loi_json_vi` → quay lại GĐ1 gắn cờ |
| Excel CTV tiếng Hàn | | ghi rõ Nghĩa câu / Nghĩa từ bám tiếng Nhật; sheet chi tiết ghi `[dịch từ tiếng Nhật] <câu/từ>` |

Dùng chung với v2 (không sao chép): dữ liệu `../data`, schema `../schema`, bảng thuật ngữ `../glossary_ko.json`, **kho mẫu đã duyệt `../da_duyet`** (mẫu trong kho tự bỏ qua), thư viện `../../../pipeline_chung`.

## File trong thư mục

| File | Ghi chú |
|---|---|
| `config.json` | `output: output` (= `pipeline_v3/output/`), `dich_tu_nhat.truong`, đường dẫn dùng chung `../…`, phiên bản prompt `gd1_claude: s1_claude_kiem_tra.v3`, `gd2: s2_dich_ko.v3` |
| `scripts/_dich_v3.py` | **mới** – đánh dấu trường dịch từ JA, bản gửi GPT, lọc kiểm tra, D6/D7 |
| `scripts/s1_lay_gpt_v2.py` | **mới** – lấy lại JSON GPT GĐ1 từ `../output_v2` (chỉ khi dữ liệu gốc không đổi) |
| `scripts/s2_dich.py`, `s2_claude_goi.py`, `s2_kiem_tra.py`, `s3_xuat_ctv.py` | **sửa cho v3** (đầu file ghi `[PIPELINE v3]`) |
| `scripts/_dang.py` | sửa đường dẫn (thư mục Vie-Kor, bảng thuật ngữ) |
| các script khác | bản sao y nguyên của v2 |
| `prompts/s1_claude_kiem_tra.md` | v2 + mục 3c |
| `prompts/s2_dich_ko.md`, `prompts/s2_claude_kiem_tra.md` | viết lại / bổ sung cho trường dịch từ JA |

## Cách chạy (từ thư mục `pipeline_v3`)

```
cd dang_bai\01_tu_vung_cach_doc_kanji\pipeline_v3
python scripts/s0_chuan_bi.py                         # (đã chạy 2026-10-05) chuẩn hóa + đánh dấu mẫu trong kho

# GĐ1
python scripts/s1_lay_gpt_v2.py --tu 1 --den 130       # mẫu đã có GPT ở v2 → lấy lại, không gọi API
python scripts/s1_gpt_chuyen.py --tu 131 --den 140     # mẫu mới → gọi GPT (bạn chạy)
python scripts/s1_claude_goi.py --tu … --den …          # rồi Claude kiểm tra theo prompts/s1_claude_kiem_tra.md
python scripts/s1_kiem_tra.py --tu … --den …
python scripts/s1_chot.py --tu … --den …                # chỉ chốt câu GĐ1_XONG (không cờ)

# GĐ2
python scripts/s2_dich.py --tu … --den …                # bạn chạy (gọi GPT)
python scripts/s2_claude_goi.py --tu … --den …          # rồi Claude kiểm tra theo prompts/s2_claude_kiem_tra.md
python scripts/s2_kiem_tra.py --tu … --den …

# Xuất Excel
python scripts/s3_xuat_ctv.py --tu … --den …            # CTV tiếng Hàn (câu ĐẠT)
python scripts/s3b_xuat_ctv_nhat.py --tu … --den …      # CTV tiếng Nhật (câu bị cờ)
python scripts/s10_luu_da_duyet.py --file <excel CTV>   # lưu mẫu "Đạt" vào kho chung ../da_duyet
```

Kết quả nằm ở `pipeline_v3/output/` (bỏ qua khi đẩy git).

## Việc tiếp theo

Chạy thử lại 36 mẫu CTV tiếng Hàn đã kiểm tra ngày 02/10 (20 mẫu đã vào kho – chạy lại cần `--ca-da-duyet`) và so với phản hồi CTV trước khi chạy toàn bộ.
