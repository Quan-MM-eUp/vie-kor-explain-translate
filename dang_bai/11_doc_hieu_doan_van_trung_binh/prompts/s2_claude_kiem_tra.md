# Hướng dẫn tác tử KIỂM TRA – Bước 2.4: soát bản dịch tiếng Hàn (dạng 11 – Đọc hiểu: Đoạn văn trung bình) · v1

> Phiên bản `s2_claude_kiem_tra.11.v1` (2026-10-08). Model: **Claude Opus 5.5** trong Cowork. Bản dịch do **tác tử TẠO (Claude A)** dịch.
> `reference_raw` không dịch, không soát.

**Nhiệm vụ:** kiểm tra bản dịch **đúng với ngữ cảnh** (đoạn văn, câu hỏi, 4 lựa chọn, đáp án, tiếng Nhật trong JSON, tiếng Việt của lời giải) và sửa lỗi.

Cột "Dịch từ" trong bảng `output/claude/gd2/<id>.md` (xem gọn: `python3 ../../pipeline_chung/cong_cu/xem_gd2.py --lo X Y`):
- **JA** = nghĩa câu hỏi (`question.meaning`), nghĩa lựa chọn (`options[i].meaning`), nghĩa câu trích (`options[i].quotes[j].meaning`) – dịch thẳng từ tiếng Nhật;
- **VI** = phần nhận xét (`options[i].analysis`).

## Làm gì

1. Soát **theo đoạn** (các câu con của cùng `question_id` liền nhau): đọc đoạn văn (`xem_gd1.py <id>` hoặc `output/samples/norm/<id>.json` → `doan_van`) rồi soát bản dịch.
2. Sửa **chỉ giá trị `ko`** trong `output/json_ko/checked/<id>.json` – qua file đặc tả lô (`"giai_doan": "2"`, `thay` với đường dẫn tới chuỗi `….ko`) rồi `ghi_ly_do.py` (SO_TAY_CHAY mục 5). Không sửa `vi`, `ja`, cấu trúc.
3. Câu cố định (nguồn `cau_co_dinh`) không sửa trong file – thấy chưa hay → `ghi_chu_khi_dich: ["[Khi dịch] Đề nghị sửa câu cố định: …"]`.
4. JSON tiếng Việt sai / mâu thuẫn nội bộ → không sửa theo ý mình, ghi `loi_json_vi: ["[Lỗi JSON VI] <phần>: <vấn đề>"]` → câu quay lại GĐ1.
5. Chạy `python3 scripts/s2_kiem_tra.py --tu X --den Y`; xem `output/reports/khong_nhat_quan.csv` (D4) cho các câu trích của đoạn.

## Phạm vi sửa

- `loai`: `sai_so_ban_goc`, `chinh_ta` (gồm **trợ từ sai theo âm cuối**), `khach_quan`, `chu_quan`. Không thêm nội dung.
- Phần dịch từ tiếng Việt: không sửa theo ý mình khi tiếng Việt sai → `[Bản gốc VI] …` trong `ghi_chu_ban_goc`.
- Phần dịch từ tiếng Nhật: sửa theo **tiếng Nhật + đoạn văn** – khác bản Việt là bình thường.

## Checklist

- [ ] **(JA)** nghĩa câu hỏi: đúng kiểu hỏi (なぜ → 왜, 何 / どれ / どんな …), giữ ①② và nháy quanh phần trích; phủ định (…ないもの / 合っていない) dịch rõ.
- [ ] **(JA)** nghĩa lựa chọn: sát lựa chọn (phủ định, chủ thể, あげる / くれる / もらう, thì); `…から。` dịch thống nhất trong cùng câu hỏi.
- [ ] **(JA)** nghĩa câu trích: đúng văn cảnh đoạn văn; **cùng câu trích → cùng bản dịch** ở mọi câu con của đoạn (D4 – `khong_nhat_quan.csv`); văn phong theo câu Nhật.
- [ ] **(VI)** nhận xét: đủ ý bản Việt, -습니다; thuật ngữ theo bảng (본문, 필자, 선택지, 인용문, 밑줄 친 부분…); cách nói về đoạn văn thống nhất.
- [ ] Giữ mọi khối ⟪ ⟫ (kể cả furigana bên trong) – trường JA: các khối trong `khoi_tieng_nhat_ban_viet_giu`; không có tiếng Nhật ngoài ⟪ ⟫.
- [ ] **Trợ từ sau ⟪ ⟫** theo âm cuối CÁCH ĐỌC (khối có furigana: kana cuối trong 《》; D12 – Python chỉ cảnh báo, tự soát cả trường hợp có nháy / ngoặc giữa ⟫ và trợ từ).
- [ ] `{ }` (theo bản Việt), `\n`, gạch đầu dòng, loại dấu nháy.

## Mẫu (trong file đặc tả lô GĐ2)

```json
"9_1": {"thay": [{"duong_dan": "$.options[0].analysis.ko", "cu": "⟪｜表現《ひょうげん》⟫를", "moi": "⟪｜表現《ひょうげん》⟫을"}],
        "sua": [{"duong_dan": "$.options[0].analysis", "loai": "chinh_ta", "muc_do": "nhe", "ly_do": "trợ từ sau ⟪表現⟫ (ひょうげん – âm cuối ん) → 을"}],
        "ghi_chu_ban_goc": [], "ghi_chu_khi_dich": [], "loi_json_vi": []}
```
