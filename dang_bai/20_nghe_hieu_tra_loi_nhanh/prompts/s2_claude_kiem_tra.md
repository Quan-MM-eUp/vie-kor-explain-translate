# Hướng dẫn tác tử KIỂM TRA – Bước 2.4: soát bản dịch tiếng Hàn (dạng 20 – Nghe hiểu: Trả lời nhanh) · v1

> Phiên bản `s2_claude_kiem_tra.20.v1` (2026-10-08). Model: **Claude Opus 5.5** trong Cowork. Bản dịch do **tác tử TẠO (Claude A)** dịch.
> `reference_raw` không dịch, không soát.

**Nhiệm vụ:** kiểm tra bản dịch **đúng với ngữ cảnh** (script: câu nói, câu trả lời, đáp án; tiếng Nhật trong JSON; tiếng Việt của lời giải) và sửa lỗi.

Cột "Dịch từ" trong bảng `output/claude/gd2/<id>.md` (xem gọn: `python3 ../../pipeline_chung/cong_cu/xem_gd2.py <id> …`):
- **JA** = lời thoại: nghĩa câu nói (`prompt.utterance.meaning`), nghĩa từng câu trả lời (`options[i].sentence.meaning`) – dịch thẳng từ câu Nhật;
- **VI** = phân tích (`options[i].analysis`, `prompt.analysis`).

## Làm gì

1. Sửa **chỉ giá trị `ko`** trong `output/json_ko/checked/<id>.json` – qua file đặc tả lô (`"giai_doan": "2"`, `thay` với đường dẫn tới chuỗi `….ko`) rồi `ghi_ly_do.py` (SO_TAY_CHAY mục 5). Không sửa `vi`, `ja`, cấu trúc.
2. Câu cố định (nguồn `cau_co_dinh`) không sửa trong file – thấy chưa hay → `ghi_chu_khi_dich: ["[Khi dịch] Đề nghị sửa câu cố định: …"]`.
3. JSON tiếng Việt sai / mâu thuẫn nội bộ → không sửa theo ý mình, ghi `loi_json_vi: ["[Lỗi JSON VI] <phần>: <vấn đề>"]` → câu quay lại GĐ1.
4. Chạy `python3 scripts/s2_kiem_tra.py --tu X --den Y`.

## Phạm vi sửa

- `loai`: `sai_so_ban_goc`, `chinh_ta` (gồm **trợ từ sai theo âm cuối**), `khach_quan`, `chu_quan`. Không thêm nội dung.
- Phần dịch từ tiếng Việt: không sửa theo ý mình khi tiếng Việt sai → `[Bản gốc VI] …` trong `ghi_chu_ban_goc`.
- Lời thoại: sửa theo **tiếng Nhật** – khác bản Việt là bình thường.

## Checklist

- [ ] **(JA)** nghĩa câu nói / câu trả lời: đúng câu Nhật (thì, phủ định, bị động, sai khiến, chủ thể, cho – nhận), tự nhiên như lời nói; câu trả lời sai vẫn dịch đúng như câu Nhật.
- [ ] **(JA) Mức lịch sự** khớp câu Nhật: ため口 → 반말; です/ます → 해요체; kính ngữ / khiêm nhường → 존댓말 / 하십시오체 (D15 – Python chỉ cảnh báo, phải tự soát; đặc biệt câu hỏi mà phân tích nói về "lịch sự / suồng sã").
- [ ] **(VI)** phân tích: đủ ý, -습니다; khi trích lại nghĩa lời thoại trong nháy → khớp bản dịch lời thoại ở trên.
- [ ] **Trợ từ sau ⟪ ⟫** theo âm cuối cách đọc tiếng Nhật (D12 – cảnh báo, tự soát cả trường hợp có nháy / ngoặc giữa ⟫ và trợ từ).
- [ ] Giữ ⟪ ⟫ (kể cả furigana bên trong), `{ }` (theo bản Việt), `\n`, loại dấu nháy.
- [ ] Nhất quán: D4 (cùng vi khác ko giữa các câu) → theo bản đã duyệt.

## Mẫu (trong file đặc tả lô GĐ2)

```json
"17921_1": {"thay": [{"duong_dan": "$.options[0].sentence.meaning.ko", "cu": "네, 맡을게.", "moi": "네, 맡아 두겠습니다."}],
            "sua": [{"duong_dan": "$.options[0].sentence.meaning", "loai": "khach_quan", "muc_do": "nang", "ly_do": "お預かりします là khiêm nhường ngữ – bản Hàn phải 하십시오체, không phải 반말"}],
            "ghi_chu_ban_goc": [], "ghi_chu_khi_dich": [], "loi_json_vi": []}
```
