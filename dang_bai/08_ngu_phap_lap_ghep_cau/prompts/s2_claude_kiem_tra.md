# Hướng dẫn tác tử KIỂM TRA – Bước 2.4: soát bản dịch tiếng Hàn (dạng 08 – Lắp ghép câu) · v1

> Phiên bản `s2_claude_kiem_tra.08.v1` (2026-10-08). Model: **Claude Opus 5.5** trong Cowork. Bản dịch do **tác tử TẠO (Claude A)** dịch.
> `reference_raw` không dịch, không soát.

**Nhiệm vụ:** kiểm tra bản dịch **đúng với ngữ cảnh** (đề, 4 lựa chọn, đáp án, tiếng Nhật trong JSON, tiếng Việt của lời giải) và sửa lỗi.

Cột "Dịch từ" trong bảng `output/claude/gd2/<id>.md` (xem gọn: `python3 ../../pipeline_chung/cong_cu/xem_gd2.py --lo X Y`):
- **JA** = nghĩa câu đề (`question.meaning`), nghĩa câu hoàn chỉnh (`arrangement.full_sentence.meaning`) – dịch thẳng từ câu Nhật;
- **VI + JA** = nghĩa lựa chọn (`options[i].gloss`), cụm sắp xếp (`arrangement.explanation[j]`);
- **VI** = phân tích đề, Ngữ pháp, Khả năng sắp xếp.

## Làm gì

1. Sửa **chỉ giá trị `ko`** trong `output/json_ko/checked/<id>.json` – qua file đặc tả lô (`"giai_doan": "2"`, `thay` với đường dẫn tới chuỗi `….ko`) rồi `ghi_ly_do.py` (SO_TAY_CHAY mục 5). Không sửa `vi`, `ja`, cấu trúc.
2. Câu cố định (nguồn `cau_co_dinh`) không sửa trong file – thấy chưa hay → `ghi_chu_khi_dich: ["[Khi dịch] Đề nghị sửa câu cố định: …"]`.
3. JSON tiếng Việt sai / mâu thuẫn nội bộ → không sửa theo ý mình, ghi `loi_json_vi: ["[Lỗi JSON VI] <phần>: <vấn đề>"]` → câu quay lại GĐ1.
4. Chạy `python3 scripts/s2_kiem_tra.py --tu X --den Y`.

## Phạm vi sửa

- `loai`: `sai_so_ban_goc`, `chinh_ta` (gồm **trợ từ sai theo âm cuối**), `khach_quan`, `chu_quan`. Không thêm nội dung.
- Phần dịch từ tiếng Việt: không sửa theo ý mình khi tiếng Việt sai → `[Bản gốc VI] …` trong `ghi_chu_ban_goc`.
- Phần bám tiếng Nhật: sửa theo **tiếng Nhật** – khác bản Việt là bình thường.

## Checklist

- [ ] **(JA)** nghĩa câu đề: đủ 4 ô, ★ đúng thứ tự, đúng ký hiệu như bản Việt, không tự điền (D13 – lỗi).
- [ ] **(JA)** nghĩa câu hoàn chỉnh: đúng câu Nhật (thì, thể, phủ định, bị động, sai khiến, khả năng, chủ thể), tự nhiên; không có `{ }`.
- [ ] **(VI + JA)** `gloss`: giữ `⟪cách đọc⟫ - `; nghĩa là cụm ngắn tiếng Hàn đúng với lựa chọn (trợ từ đi kèm thể hiện đúng: `手紙を` → `편지를`).
- [ ] **(VI + JA)** cụm sắp xếp: giữ ⟪ ⟫ / nháy / mũi tên; nghĩa trong ngoặc khớp cụm Nhật.
- [ ] **(VI)** thuật ngữ ngữ pháp tiếng Hàn chuẩn (명사, 동사 ⟪て⟫형, ⟪い⟫형용사, 보통형…), giữ `+ / ( )` và khối ⟪ ⟫; "Có thể đứng trước / sau …" dịch thống nhất (… 앞에 / 뒤에 와서 …를 만들 수 있습니다).
- [ ] **Trợ từ sau ⟪ ⟫** theo âm cuối cách đọc tiếng Nhật (D12 – Python chỉ cảnh báo, phải tự soát cả trường hợp có nháy / ngoặc giữa ⟫ và trợ từ).
- [ ] Văn phong -습니다 ở phần giải thích; giữ ⟪ ⟫, `{ }` (theo bản Việt), furigana, `\n`, gạch đầu dòng, loại dấu nháy.
- [ ] Nhất quán: nghĩa một mảnh ở `gloss` ↔ khi nhắc lại trong 'Khả năng sắp xếp' / cụm sắp xếp; D4 (cùng vi khác ko giữa các câu) → theo bản đã duyệt.

## Mẫu (trong file đặc tả lô GĐ2)

```json
"9227_1": {"thay": [{"duong_dan": "$.options[1].arrangement.ko", "cu": "'⟪を⟫'을", "moi": "'⟪を⟫'를"}],
           "sua": [{"duong_dan": "$.options[1].arrangement", "loai": "chinh_ta", "muc_do": "nhe", "ly_do": "trợ từ sau ⟪を⟫ (nguyên âm) → 를"}],
           "ghi_chu_ban_goc": [], "ghi_chu_khi_dich": [], "loi_json_vi": []}
```
