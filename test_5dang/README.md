# Test chuyển JSON + dịch Việt → Hàn: 5 dạng bài × 5 mẫu, so sánh Haiku và Sonnet

Hệ thống thử nghiệm cho 5 dạng: Cách đọc kanji, Thay đổi cách nói, Cách viết từ, Điền từ theo văn cảnh, Hình thành từ.

- **Chuyển JSON và dịch** do Claude làm trong Cowork, bằng hai tác tử: một chạy **Haiku**, một chạy **Sonnet**, nhận cùng đầu vào và cùng hướng dẫn.
- **Python chỉ dùng để**: chọn mẫu, kiểm tra tự động, gọi giám khảo OpenAI và tổng hợp báo cáo.

## Cấu trúc thư mục

```
test_5dang/
├── README.md                  ← file này
├── config.json                ← cấu hình: dạng bài, số mẫu, model giám khảo, ngưỡng kiểm tra
├── .env.example               ← mẫu file chứa OPENAI_API_KEY (bạn tự tạo .env)
├── instructions/
│   ├── convert_rules.md       ← hướng dẫn cho Claude khi chuyển sang JSON (bước 2)
│   ├── translate_ko_rules.md  ← hướng dẫn cho Claude khi dịch (bước 3)
│   └── glossary_ko.json       ← bảng thuật ngữ Việt → Hàn (bản nháp, cần biên tập viên duyệt)
├── scripts/
│   ├── common.py              ← hàm dùng chung
│   ├── select_samples.py      ← bước 1: chọn mẫu
│   ├── validate_json_vi.py    ← bước 2: kiểm tra JSON tiếng Việt
│   ├── check_ko.py            ← bước 4: kiểm tra tự động bản dịch
│   ├── judge_openai.py        ← bước 5: giám khảo OpenAI chấm mù
│   └── make_report.py         ← bước 6–7: báo cáo Excel + phiếu chấm cho biên tập viên
├── samples/                   ← samples.csv + raw/<sample_id>.json (dữ liệu gốc từng mẫu)
├── json_vi/haiku|sonnet|final ← JSON tiếng Việt do từng model tạo; final = bản chuẩn đã duyệt
├── json_ko/haiku|sonnet       ← JSON có thêm bản dịch tiếng Hàn
└── reports/                   ← kết quả kiểm tra, giám khảo, báo cáo Excel
```

Schema và ví dụ chuẩn dùng chung nằm ở `../explanation_schema/`. Dữ liệu gốc: `../question-explain-INTEGRATED.csv`.

## Chuẩn bị (làm một lần)

1. **Tạo file `.env`**: mở file `.env` trong thư mục `test_5dang` và điền key sau `OPENAI_API_KEY=`. Key eUp gọi qua LLM Gateway (`OPENAI_BASE_URL=https://llm.eup.ai/v1`, đã có sẵn trong file), không gọi thẳng OpenAI. Không dán key vào khung chat, không gửi file này cho ai.
2. **Điền tên model giám khảo**: chạy `python scripts/judge_openai.py --list-models` để xem các model mà LLM Gateway eUp cung cấp, rồi điền tên vào `config.json`, mục `judge.model`. Nếu model đó không nhận tham số `temperature` thì giữ `null`.
3. **Thư viện Python**: `pip install jsonschema openpyxl` (script gọi OpenAI dùng thư viện có sẵn, không cần cài `openai`).

## Các bước chạy

Cột "Nói với Claude" là câu bạn có thể gửi trong Cowork để Claude làm bước đó. Bạn cũng có thể tự chạy lệnh Python trong terminal, **từ trong thư mục `test_5dang`**.

| Bước | Việc | Nói với Claude | Hoặc tự chạy |
|---|---|---|---|
| 1 | Chọn 25 mẫu (cố định theo `seed`) | "Chạy bước 1" | `python scripts/select_samples.py` |
| 2a | Haiku và Sonnet cùng chuyển 25 mẫu sang JSON | "Chạy bước 2" | Chỉ làm được trong Cowork |
| 2b | Kiểm tra JSON của từng model | (Claude tự chạy sau 2a) | `python scripts/validate_json_vi.py haiku` và `… sonnet` |
| 2c | Tạo bộ chuẩn `json_vi/final/` (lấy bản đúng hơn, sửa chỗ sai), **bạn duyệt** | "Tạo bộ JSON chuẩn" | `python scripts/validate_json_vi.py final` |
| 3 | Haiku và Sonnet cùng dịch bộ chuẩn sang tiếng Hàn | "Chạy bước 3" | Chỉ làm được trong Cowork |
| 4 | Kiểm tra tự động bản dịch | (Claude tự chạy sau 3) | `python scripts/check_ko.py haiku` và `… sonnet` |
| 5 | Giám khảo OpenAI chấm mù | "Chạy bước 5" | `python scripts/judge_openai.py --dry-run` (xem prompt, không gọi API), rồi `python scripts/judge_openai.py` |
| 6 | Tạo báo cáo + phiếu chấm cho biên tập viên | "Tạo báo cáo" | `python scripts/make_report.py` |
| 7 | Đưa điểm biên tập viên vào báo cáo | "Cập nhật điểm biên tập viên" | `python scripts/make_report.py --editor reports/phieu_bien_tap_vien.xlsx` |

### Kết quả chính

- `reports/bao_cao_so_sanh.xlsx`: sheet **Tong_hop** (so sánh Haiku và Sonnet theo từng dạng), **Chuyen_JSON**, **Chi_tiet_dich** (từng trường: tiếng Việt, bản Haiku, bản Sonnet, lỗi tự động, lựa chọn của giám khảo), **Van_de_ban_goc**.
- `reports/phieu_bien_tap_vien.xlsx`: gửi cho biên tập viên. Hai bản được gọi là A/B, không ghi tên model; biên tập viên điền điểm 1–5 và ghi chú.
- `reports/_dap_an_phieu_bien_tap_vien.json`: đáp án A/B tương ứng model nào. **Không gửi file này cho biên tập viên.**

## Tinh chỉnh

- **Muốn chuyển JSON hoặc dịch tốt hơn**: sửa `instructions/convert_rules.md`, `instructions/translate_ko_rules.md`, `instructions/glossary_ko.json`, rồi yêu cầu Claude chạy lại bước 2 hoặc 3.
- **Đổi số mẫu, dạng bài, ngưỡng kiểm tra**: sửa `config.json`. Chọn lại mẫu bằng `python scripts/select_samples.py --force` (sẽ ghi đè bộ mẫu cũ).
- **Thêm ngôn ngữ khác** (vd. tiếng Đài Loan): đổi `target_lang` trong `config.json`, tạo `translate_<lang>_rules.md` và `glossary_<lang>.json` tương ứng.
- **Chấm lại một mẫu**: `python scripts/judge_openai.py --only <sample_id> --force`.

## Lưu ý

- **Cowork dùng để test, chạy thật nên qua Claude API.** Chạy trong Cowork tính vào hạn mức gói Claude, không tính tiền theo token, và không phù hợp để xử lý toàn bộ 18.630 câu. Khi chạy thật nên dùng Claude API (Batch), giữ nguyên các file trong `instructions/`.
- **Kết quả trong Cowork là gần đúng.** Tác tử con không đặt được temperature, nên nếu Haiku và Sonnet chênh nhau ít, hãy xác nhận lại trên 5–10 mẫu qua API trước khi chốt.
- **Nếu Claude không gọi được LLM Gateway (llm.eup.ai) từ máy bạn** (tùy cấu hình mạng), hãy tự chạy bước 5 trong terminal. Kết quả vẫn ghi vào `reports/`, sau đó bảo Claude "Tạo báo cáo".
