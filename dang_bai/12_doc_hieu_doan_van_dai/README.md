# 12. Đọc hiểu – Đoạn văn dài

| Mục | Giá trị |
|---|---|
| Tên trong sheet "Format giải thích" | Đoạn văn dài |
| Giá trị cột `dang_bai` trong CSV | `đoạn văn dài` |
| Số dòng | 331 câu / 86 đoạn văn (73 đoạn 4 câu, 13 đoạn 3 câu) – N1: 105, N3: 226 |
| Dữ liệu | `data/12_doc_hieu_doan_van_dai.csv` |
| Schema | `reading_listening.v1` (`schema/reading_listening.v1.json`; bản cho tác tử TẠO: `.api.json`) |
| Ví dụ JSON mẫu | `../../explanation_schema/examples/12_doc_hieu_doan_van_dai.json` |

## Trạng thái (2026-10-08)

Pipeline dạng 12 đã dựng (Claude Opus 5.5 Cowork, không GPT) và **kiểm thử khô** toàn luồng (s0 → GĐ1 → GĐ2 → Excel CTV) bằng bản giả lập; **chưa chạy lô thật nào**. `s0_chuan_bi.py` đã chạy trên 331 câu (`output/samples/norm`, `output/thu_tu_chay.csv`, `output/reports/`).

Chạy: `HUONG_DAN_CHAY.md` → `SO_TAY_CHAY.md`; tiến độ: `NHAT_KY.md`.

## Tệp chính

| Tệp | Vai trò |
|---|---|
| `scripts/_doc_hieu.py` | Tách lời giải đọc hiểu (khuôn chuan / chi_ban_dich / tu_do), cờ s0, K-TD (câu trích ↔ đoạn văn), kiểm tra K0–K9, hiển thị Excel |
| `scripts/_dang.py` | Hạ tầng (cấu hình, chọn mẫu, bản tạo Claude) + gắn `_doc_hieu` + thứ tự chạy theo đoạn văn |
| `scripts/_dau_vao.py` / `_dich_v3.py` | Đầu vào tác tử TẠO GĐ1 (FLAG_HINT) / GĐ2 (trường dịch thẳng từ tiếng Nhật, D7 / D12 / D15) |
| `scripts/lo.py` | Lô theo đoạn văn (2 đoạn / lô): lô tiếp theo + khoảng `--tu/--den` |
| `prompts/` | 8 prompt: `s1_chuyen_json`, `s1_claude_tao`, `s1_claude_kiem_tra`, `s2_dich_ko`, `s2_claude_dich`, `s2_claude_kiem_tra`, `giao_viec_tao_gd1/gd2` |

Ghi chú: `pipeline_chung/doc_hieu_chung.py` (dựng song song cùng dạng 15) là bản dùng chung cho các dạng đọc hiểu; dạng 12 hiện dùng parser riêng `scripts/_doc_hieu.py` (đã thử trên đủ 331 câu). Gộp về bản chung để ở cuộc trò chuyện điều phối khi các dạng đọc hiểu đã chạy ổn.
