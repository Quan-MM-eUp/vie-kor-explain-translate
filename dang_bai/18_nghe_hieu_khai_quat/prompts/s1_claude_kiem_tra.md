# Hướng dẫn tác tử KIỂM TRA – Bước 1.2: kiểm tra JSON tiếng Việt và sửa lỗi (dạng 18 – Nghe hiểu khái quát) · v1

> Phiên bản `s1_claude_kiem_tra.18.v1` (2026-10-08): khung **cách chia v2** của dạng 07/09 + tiêu chí riêng dạng 18 (3d-1…7) – duyệt 08/10/2026.
> Model: **Claude Opus 5.5**, chạy trong Claude Cowork (không qua API). Tác tử con (nếu có) cũng dùng Opus 5.5.
> Bản cần kiểm tra do **tác tử TẠO (Claude A, ngữ cảnh riêng)** tạo – mọi chỗ "bản tạo / lỗi bản tạo" dưới đây là của tác tử TẠO. Bạn (tác tử KIỂM TRA) không tạo lại bản, chỉ soát và sửa.

**Nhiệm vụ:** kiểm tra JSON tiếng Việt **so với lời giải gốc và lời thoại** và sửa lỗi. JSON phải thể hiện đúng và đủ lời giải gốc, không hơn, không kém; lời giải phải đúng **với lời thoại** (khái quát: ý chính / mục đích / điều muốn nói nhất).

> Dạng 18 không có phần THAM KHẢO: `reference_raw` luôn `null` (Python điền, không sửa).

## Làm gì

Mỗi câu xem bằng hai lệnh (chạy trong thư mục dạng):
- `python3 ../../pipeline_chung/cong_cu/xem_gd1.py <id>` – đề, **lời thoại Nhật đã tách L1…Ln** (in ở mục "ĐOẠN VĂN"), lời giải gốc, gợi ý Python, JSON phẳng;
- `python3 scripts/xem_loi_thoai.py <id>` – bản dịch Việt của lời giải (V1…Vm) và cách JSON ghép `Lk [người nói] Nhật ‖ Việt` (dòng lệch lời thoại có dấu ⚠).

Danh sách câu: `output/claude/gd1_danh_sach.json` (tạo bằng `python3 scripts/s1_claude_goi.py …`): cờ (`co`), ghi chú bản gốc tự động, kết quả Python chạy thử trên bản tạo (`python_tren_ban_gpt`), đường dẫn file.

Với mỗi câu:
1. Đọc `output/samples/norm/<id>.json`: `loi_thoai` (L1…Ln), `de` (câu hỏi, 4 lựa chọn tiếng Nhật, đáp án), `dau_vao` (lời giải gốc), `phan` (Python tách: bản dịch, câu hỏi VI, 4 khối), `co`, `khuon_goc`.
2. Sửa trực tiếp `output/json_vi/checked/<id>.json` nếu có lỗi (giữ đúng schema `reading_listening.v1`, JSON hợp lệ).
3. Ghi kết quả bằng **file đặc tả lô** + `ghi_ly_do.py` (xem `SO_TAY_CHAY.md` mục 4.3) – tương đương ghi `…/<id>.ly_do.json` và xóa `_huong_dan`.
4. Chỉ sửa file trong `output/json_vi/checked/`. Xong cả lô chạy `python3 scripts/s1_kiem_tra.py …` và báo kết quả.

## Phạm vi sửa – cách chia v2

Ba việc tách bạch: **sửa lỗi bản tạo**, **sửa lỗi ĐỊNH DẠNG của bản gốc**, **gắn cờ NGHI SAI NỘI DUNG**. Không sửa nội dung bản gốc.

**1. Sửa lỗi của bản tạo** (`loai`: `sai_so_ban_goc` / `chinh_ta` / `khach_quan`): ghép sai câu dịch với dòng lời thoại; bỏ sót / tự thêm câu chữ; **tự dịch** dòng không có bản dịch (→ đặt `meaning = null`); sót nhãn người nói trong `meaning.vi`; tách nhầm câu trích (từ nằm giữa câu Việt bị đưa vào `quotes`, hoặc câu trích đứng riêng bị để trong `analysis`); để sót `→ SAI.` / `Dịch:` / dòng dẫn `…nói:`; `is_match` trái lời giải; `option_ja` không theo dòng `n. …` của lời giải hoặc mất furigana; thiếu ⟪ ⟫.
- Sửa `ja` / `speaker` của `full_translation` **chỉ để khớp lại L1…Ln** (Python K-LT1 so từng dòng – không sửa lời thoại).

**2. Sửa lỗi ĐỊNH DẠNG có sẵn trong lời giải gốc** – `loai: sua_dinh_dang` + `nhom` (`dinh_chu`, `xuong_dong`, `lap_tu`, `chinh_ta`, `dau_cau`, `khoang_trang`, `ky_tu`, `furigana`, `khac`): dính câu, lặp từ, lỗi chính tả / dấu tiếng Việt, ruby hỏng / furigana lệch, dấu câu thừa. Mỗi chỗ có **hai** ghi chép: mục trong `sua` (`duong_dan` mức trường nhỏ nhất, `loai`, `nhom`, `muc_do`, `ly_do`) **và** một dòng `[Đã sửa định dạng] <chỗ>: '<cũ>' → '<mới>' – <lỗi gì>` trong `ghi_chu_ban_goc` (một dòng, xuống dòng ghi `⏎`).
- **Lỗi gõ trong lời thoại Nhật** (`えーつ`, `何ががん`, `延期さて`, `(i)`, `ちゃんとと`) – quyết định Q5: **chép nguyên, không sửa**, chỉ ghi `[Ghi chú] Lời thoại L5: 'えーつ' – nghi lỗi gõ của 'えーっ', giữ nguyên` khi ảnh hưởng hiểu nghĩa. Câu trích trong lời giải lệch lời thoại vì lỗi gõ của một bên → cũng chỉ ghi chú.
- **Một trường – một loại sửa:** không vừa `sua_dinh_dang` vừa sửa lỗi bản tạo trên cùng một trường (Python hoàn tác cả trường khi đo trung thành) – ưu tiên sửa lỗi bản tạo, chuyển lỗi định dạng thành ghi chú.

**3. Gắn cờ NGHI SAI NỘI DUNG – không sửa** (câu **không được dịch**, chuyển CTV tiếng Nhật). Ghi vào `nghi_noi_dung`, mỗi chỗ một mục `{vi_tri, nhom, mo_ta, de_xuat}`:
- `vi_tri`: `Lời thoại Lk – bản dịch`, `Câu hỏi – nghĩa`, `Lựa chọn N – nghĩa`, `Lựa chọn N – câu trích`, `Lựa chọn N – phân tích`, `Lựa chọn N – kết luận`, `Đáp án`, `Toàn bộ phân tích`.
- `nhom` (dạng 18): `nghia_cau` · `trich_dan` · `phan_tich` · `dap_an` · `thieu_noi_dung` · `khac`.
- Không chắc lắm cũng gắn cờ (CTV quyết) – nhưng không gắn cờ cho cách diễn đạt chỉ "chưa hay".

**3d. Tiêu chí riêng dạng 18 (bắt buộc soát – duyệt 08/10/2026)**

| # | Gắn cờ khi | `nhom` |
|---|---|---|
| 1 | **Bản dịch lời thoại sai nghĩa / bỏ sót ý quan trọng / dịch nhầm người nói** (so từng dòng `Lk` với câu Nhật): sai cấu trúc, mất phủ định / bị động / sai khiến / điều kiện, đổi chủ thể, thêm bớt ý. Dịch thoát nhưng đúng ý → không cờ. | `nghia_cau` |
| 2 | **Dịch câu hỏi / lựa chọn / câu trích sai nghĩa** so với câu Nhật (nhất là từ then chốt của lựa chọn: 長所 ↔ 短所, 理由 ↔ 方法, まだ ↔ もう). | `nghia_cau` |
| 3 | **Câu trích không có trong lời thoại, trích sai chỗ / gán sai người nói, hoặc không chứng minh được điều phân tích nói** (cờ tự động `trich_dan_ngoai_loi_thoai`, cảnh báo `K-TD`). Lệch chỉ do chữ Hán ↔ kana / lỗi gõ nhỏ → không cờ (ghi chú). | `trich_dan` |
| 4 | **Phân tích trái lời thoại hoặc sai lập luận "khái quát"**: nói "không đề cập" nhưng lời thoại có; coi chi tiết phụ là ý chính (hoặc ngược lại) trái với câu hỏi; lý do loại không liên quan tới lựa chọn; tự mâu thuẫn. | `phan_tich` |
| 5 | **Kết luận / đáp án đáng ngờ**: `→ ĐÚNG` ở lựa chọn khác `dap_an_so` (cờ `lech_dap_an`), nhiều `→ ĐÚNG` (`nhieu_dung`), hoặc đọc lời thoại thấy đáp án của đề sai. | `dap_an` |
| 6 | **Khuôn D / E** (lời giải không phân tích 4 lựa chọn) – **bắt buộc** (Python K-KH báo LỖI nếu thiếu); và câu có **bản dịch lời thoại thiếu nhiều dòng** (cảnh báo `K-LT2` vượt ngưỡng, hoặc lời giải không có bản dịch – `khong_ban_dich`); lựa chọn thiếu phân tích làm người học không hiểu vì sao loại. | `thieu_noi_dung` |
| 7 | Lựa chọn trong lời giải **khác lựa chọn trong lời thoại về chữ / nghĩa** (cờ `lua_chon_lech`) – chỉ khác chữ Hán ↔ kana, dấu câu, lỗi gõ nhỏ → không cờ (ghi chú). | `khac` |

**Không gắn cờ:** phân tích ngắn / sơ sài nhưng không sai; lựa chọn sai không kèm câu trích; dịch vụng nhưng đúng ý; lỗi gõ trong lời thoại Nhật gốc (chỉ ghi chú, xem mục 2); nhãn dẫn câu trích bị bỏ (đúng quy tắc).

**3b. Sau khi CTV tiếng Nhật trả kết quả cho câu bị cờ** (chỉ làm khi người dùng đưa phản hồi CTV): CTV xác nhận **không sai** → xóa mục cờ; **sai** → sửa JSON theo CTV, ghi `sua` với `"loai": "sua_theo_ctv"` + `nhom` và dòng `[Đã sửa theo CTV] <chỗ>: '<cũ>' → '<mới>' – <CTV nói gì>`; chạy lại `s1_kiem_tra.py`.

**4. Âm Hán Việt** – Python tự dò (`[Âm Hán Việt] …`); câu có âm Hán Việt không được dịch. Python dò sót → cờ `khac`, ghi rõ.

**Dạng của câu:** có ít nhất một `sua_dinh_dang` → **Dạng 2**; không → **Dạng 1**. Chỉ câu **không có** `nghi_noi_dung` **và không có** âm Hán Việt mới được chốt và dịch.

## Python kiểm tra (để hiểu thông báo)

- **LỖI:** schema; mất tiếng Nhật; độ phủ chữ Việt < 97% (toàn câu, bản dịch lời thoại `K9`, từng lựa chọn `K9`); furigana / ⟪ ⟫; **K-LT1** số dòng / `ja` / `speaker` lệch L1…Ln; **K-LT2** khuôn E / không có bản dịch mà vẫn có `meaning`; **K-CH** `question.ja` khác câu hỏi lời thoại; **K-LC** `option_ja` khác dòng `n. …` của lời giải (khuôn D/E: khác lời thoại), `reading ≠ null`, khuôn D/E có `quotes` / `analysis`; **K-QT** `quotes[].ja` không có trong khối phân tích của lựa chọn đó; **K-DA** `is_match` trái `→ ĐÚNG/SAI`, `correct` sai, số `is_match = true` ≠ 1; **K-KH** khuôn D/E thiếu cờ `thieu_noi_dung`; **K-NULL** `summary` / `key_info` ≠ null.
- **CẢNH BÁO:** **K-TD** câu trích không khớp lời thoại; **K-LT2** dòng lời thoại không có bản dịch; **K-NQ** cùng câu trích dịch khác nhau giữa các lựa chọn; tiếng Nhật chưa bọc ⟪ ⟫; từ thừa > 5%.

## Checklist cấu trúc

- [ ] `full_translation` = 1 nhóm `label: null`, **đúng n dòng L1…Ln**; mỗi `meaning.vi` đúng câu dịch của dòng đó (không nhãn người nói), không có thì `null`; không câu dịch nào bị bỏ.
- [ ] `question.ja` = câu hỏi lời thoại; `question.meaning` = câu hỏi Việt (không nhãn).
- [ ] Mỗi lựa chọn: `option_ja` theo dòng `n. …` (giữ furigana); `meaning` = dòng `Nghĩa:`; `quotes` = câu trích đứng riêng + dịch; `analysis` = toàn bộ nhận xét còn lại (kể cả câu sau `→`), không còn `→ SAI.` / `Dịch:` / dòng dẫn; `is_match` theo `→`.
- [ ] `correct = {dap_an_so, option_ja giống hệt, full_sentence: null}`; `summary = key_info = null`.
- [ ] Mọi tiếng Nhật trong câu Việt bọc ⟪ ⟫; furigana đúng như bản gốc.
- [ ] Soát đủ **3d-1…7**: đọc lời thoại, so bản dịch từng dòng, đối chiếu câu trích với lời thoại, kiểm lập luận "ý chính" của 4 lựa chọn với câu hỏi.

## Mẫu file lý do (một câu)

```json
{
  "sua": [
    {"duong_dan": "$.full_translation[0].lines[4].meaning.vi", "loai": "sai_so_ban_goc", "muc_do": "nhe",
     "ly_do": "Bản tạo để sót nhãn 'Người đàn ông:' đầu câu dịch L5 – bỏ"},
    {"duong_dan": "$.options[2].analysis.vi", "loai": "sua_dinh_dang", "nhom": "dinh_chu", "muc_do": "nhe",
     "ly_do": "dính câu: 'hội thoại.Lựa chọn' → 'hội thoại.⏎Lựa chọn'"}
  ],
  "ghi_chu_ban_goc": ["[Đã sửa định dạng] Lựa chọn 3 – phân tích: 'hội thoại.Lựa chọn' → 'hội thoại.⏎Lựa chọn' – dính câu",
                      "[Ghi chú] Lời thoại L5: 'えーつ' – nghi lỗi gõ của 'えーっ', giữ nguyên"],
  "nghi_noi_dung": [
    {"vi_tri": "Lựa chọn 4 – phân tích", "nhom": "phan_tich",
     "mo_ta": "(3d-4) Phân tích nói người cha 'không nhắc đến' tính cách con, nhưng L7 「まじめなやつだから」 là nhận xét tính cách – lập luận loại cần sửa.",
     "de_xuat": "Người cha có nhận xét con là người nghiêm túc (L7) nhưng đó không phải ý kiến của ông về suy nghĩ của con."}
  ]
}
```
