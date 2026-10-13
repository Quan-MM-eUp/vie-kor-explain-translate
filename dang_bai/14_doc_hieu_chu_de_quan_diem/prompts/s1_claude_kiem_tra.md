# Hướng dẫn tác tử KIỂM TRA – Bước 1.2: kiểm tra JSON tiếng Việt và sửa lỗi (dạng 14 – Đọc hiểu chủ đề / quan điểm) · v1

> Phiên bản `s1_claude_kiem_tra.14.v1` (2026-10-08). Khung = prompt kiểm tra dạng 07/09 (cách chia v2) + **tiêu chí riêng đọc hiểu (3d-14)** đã duyệt trong `KE_HOACH_PIPELINE.md`.
> Model: **Claude Opus 5.5**, chạy trong Claude Cowork. Bản cần kiểm tra do **tác tử TẠO (Claude A)** tạo – mọi chỗ "bản GPT" / "lỗi GPT" trong các file chung hiểu là bản / lỗi của tác tử TẠO.

**Nhiệm vụ:** kiểm tra JSON tiếng Việt **so với lời giải gốc** (khuôn chuẩn) hoặc **so với đoạn văn + đáp án** (khuôn lạ – phần tạo mới) và sửa lỗi theo phạm vi dưới đây.

> Dạng 14 không có phần THAM KHẢO – `reference_raw` luôn `null`, không sửa (K-TK).

## Làm gì

Xem từng câu: `python3 ../../pipeline_chung/cong_cu/xem_gd1.py <id> …` (in **đoạn văn một lần cho mỗi đoạn**, rồi lời giải gốc + gợi ý Python + JSON). Danh sách: `output/claude/gd1_danh_sach.json` (`python3 scripts/s1_claude_goi.py …`). Mỗi mục có cờ (`co`), ghi chú bản gốc tự động, **kết quả Python trên bản tác tử TẠO** (`python_tren_ban_gpt` – gồm `[Âm Hán Việt]`, `[Nghi dính câu/định dạng]`, K-TD, K-GC, K-NQ…).

Với mỗi câu:
1. Đọc `output/samples/norm/<id>.json`: `de`, `doan_van`, `loai_cau_hoi`, `khuon_goc`, `dau_vao` (lời giải gốc đã chuẩn hóa), `co`.
2. Sửa trực tiếp `output/json_vi/checked/<id>.json` nếu có lỗi (đúng schema `reading_listening.v1`).
3. Ghi kết quả bằng **file đặc tả lô** + `ghi_ly_do.py` (SO_TAY_CHAY mục 4.3).
4. Chạy `python3 scripts/s1_kiem_tra.py …` và báo kết quả.

**Soát theo ĐOẠN VĂN:** đọc đoạn văn trước (một lần), rồi các câu con của đoạn đó liền nhau – nhiều lỗi nội dung chỉ thấy khi đối chiếu đoạn văn.

## Phạm vi sửa – cách chia v2

**1. Sửa lỗi của tác tử TẠO** (`sai_so_ban_goc` / `khach_quan` / `chinh_ta`): đặt sai trường; nhận xét nằm nhầm lựa chọn (K-PL); trích dẫn giữa câu Việt bị tách ra `quotes` làm câu cụt (hoặc ngược lại – trích dẫn đứng sau nhãn thuần mà để trong `analysis`); chép nhãn dẫn thuần / `Dịch:` vào JSON; còn `「」` ngoài cùng ở `quotes[].ja`; `is_match` khác `→ ĐÚNG/SAI` của lời giải (K4); thiếu ⟪ ⟫; bỏ sót / tự thêm chữ.

**2. Sửa lỗi ĐỊNH DẠNG có sẵn trong bản gốc** – `loai: sua_dinh_dang` + `nhom` (`dinh_chu`, `xuong_dong`, `lap_tu`, `chinh_ta`, `dau_cau`, `khoang_trang`, `ky_tu`, `furigana`, `khac`) + dòng `[Đã sửa định dạng] <chỗ>: '<cũ>' → '<mới>' – <lỗi gì>` (một dòng, xuống dòng ghi `⏎`):
- dòng lặp lại liền nhau do dán hai lần (cờ `dong_lap`, vd 16865_3 lặp dòng lựa chọn và dòng trích) → bỏ bản lặp (`lap_tu`);
- lỗi gõ / ruby hỏng trong câu trích, câu hỏi, lựa chọn (`｜今一《いまいちばん》番` → `｜今一番《いまいちばん》`) → `furigana`;
- nhãn rác tiếng Nhật trong câu Việt (`Giải釈:`) đã được bỏ khi chuyển – chỉ ghi chú.
- Câu tiếng Nhật (`question.ja`, `option_ja`, `quotes[].ja`) Python so với lời giải (K5–K7): sửa định dạng ở đây phải có mục `sua` đúng đường dẫn, không thì K5/K6/K7 báo LỖI.

**3. Gắn cờ NGHI SAI NỘI DUNG – không sửa** (câu không được dịch, chuyển CTV tiếng Nhật). Khóa `nghi_noi_dung`, mỗi chỗ một mục `{vi_tri, nhom, mo_ta, de_xuat}`:
- `vi_tri`: `Câu hỏi – nghĩa`, `Lựa chọn N – nghĩa`, `Lựa chọn N – trích dẫn`, `Lựa chọn N – nghĩa câu trích`, `Lựa chọn N – giải thích`, `Lựa chọn N – ĐÚNG/SAI`, `Bản dịch đoạn văn`, `Toàn bộ lời giải`.
- `nhom` (dạng 14): `trich_dan` · `phan_tich` · `quan_diem` · `dap_an` · `nghia_cau` · `thieu_noi_dung` · `tao_moi` · `khac`.

### 3d-14. Tiêu chí riêng dạng 14 (duyệt 2026-10-08)

| # | Gắn cờ khi | `nhom` |
|---|---|---|
| 1 | **Câu hỏi quan điểm tác giả** (`hoi_quan_diem`, cả câu hỏi cuối kiểu 筆者の考え / 言いたいこと): lời giải lấy ý của **người khác / ví dụ / quan điểm bị tác giả phản bác** trong bài làm ý của tác giả, hoặc bỏ qua đoạn kết luận (thường đoạn cuối) mà kết luận theo một câu lẻ | `quan_diem` |
| 2 | **Câu hỏi cụm gạch chân / chỉ định** (`hoi_chi_dinh`, cảnh báo K-GC): giải thích sai cái mà cụm / đại từ chỉ tới (sai phạm vi, sai chủ thể, lấy câu không chứa cụm đó) | `phan_tich` |
| 3 | Trích dẫn **không có trong đoạn văn** (K-TD + đã tự đối chiếu), trích **sai chỗ** (câu trích không liên quan tới lựa chọn), hoặc câu trích **không chứng minh được** điều phân tích nói | `trich_dan` |
| 4 | Phân tích **trái nội dung đoạn văn** / lập luận sai (nói "đoạn văn không đề cập" nhưng có; kết luận sai vì hiểu sai câu trích) | `phan_tich` |
| 5 | Kết luận ĐÚNG/SAI trái đáp án (`lech_dap_an`), nhiều / không có ĐÚNG (`nhieu_dung`, K3) | `dap_an` |
| 6 | Dịch câu hỏi / lựa chọn / câu trích **sai nghĩa** (mất phủ định, đổi chủ thể, thêm bớt ý, hiểu sai từ) – kể cả câu trích dịch khác nhau giữa các câu con mà một bản sai (K-NQ) | `nghia_cau` |
| 7 | Câu Việt có cụm tiếng Nhật chen vào **làm câu vô nghĩa / sai nghĩa** (vd `｜創造《そうぞう》 ｜的《てき》`, `｜出《で》｜現《げん》` thay cho chữ Việt – máy dịch hỏng) | `nghia_cau` |
| 8 | Lời giải khuôn chuẩn **thiếu nội dung** làm người học không hiểu vì sao loại (lựa chọn không có giải thích nào) | `thieu_noi_dung` |

**Không gắn cờ:** phân tích sơ sài nhưng không sai; lựa chọn sai không kèm trích dẫn; dịch vụng nhưng đúng ý; trích dài hơn cần thiết; từ Nhật chen trong câu Việt mà câu vẫn hiểu đúng (giữ, bọc ⟪ ⟫); câu trích khớp một phần đoạn văn do lược bớt / thêm `…` / khác furigana.

### Khuôn lạ – TẠO MỚI (`co` có `tao_moi`)

- Python **tự** gắn dòng `[Nghi sai nội dung] Toàn bộ lời giải (tao_moi): …` (câu luôn chuyển CTV tiếng Nhật) – bạn **không** cần ghi cờ `tao_moi`.
- Soát phần tạo mới như một người ra đề: `is_match` đúng ở `dap_an_so`; trích dẫn **chép nguyên** câu của đoạn văn (K-TM báo LỖI nếu không có trong đoạn văn) và đúng là căn cứ; giải thích đúng nội dung, đúng quan điểm tác giả; nghĩa lựa chọn / câu trích dịch đúng. Phần tạo mới sai → **sửa trực tiếp** (đây là lỗi của tác tử TẠO – `loai: khach_quan`, ghi `ly_do`), không cần gắn cờ.
- Phần **chép từ bản gốc** (bản dịch đoạn văn, dịch câu hỏi / lựa chọn, câu giải thích có sẵn) vẫn theo nguyên tắc: định dạng → sửa; nội dung sai → gắn cờ.
- `full_translation` = đúng bản dịch đoạn văn của lời giải (mỗi đoạn một line) – chỉ ở câu có cờ `co_dich_doan` (K-FT).
- Sau khi CTV tiếng Nhật duyệt (SO_TAY mục 4.4): ghi `"ctv_duyet_tao_moi": "<file CTV – ngày>"` vào `.ly_do.json` → chạy lại `s1_kiem_tra.py`.

### 3b. Sau khi CTV tiếng Nhật trả kết quả cho câu bị cờ

- CTV xác nhận **không sai** → xóa mục cờ tương ứng.
- CTV xác nhận **sai** → sửa JSON theo CTV, mục `sua` với `"loai": "sua_theo_ctv"` + `nhom` + dòng `[Đã sửa theo CTV] <chỗ>: '<cũ>' → '<mới>' – <CTV nói gì>`; xóa mục cờ đã xử lý.

**4. Âm Hán Việt** – Python tự dò (`[Âm Hán Việt] …`). Không sửa; câu có âm Hán Việt tự động không dịch.

## Gợi ý / cảnh báo Python

- **K-TD** câu trích không thấy trong đoạn văn (so mờ) → tự đối chiếu `doan_van`: trích sai thật → 3d-14 #3; chỉ lệch chữ do gõ / ruby → sửa định dạng (nếu ở `quotes[].ja` thì sửa + `sua_dinh_dang` `nhom: ky_tu|furigana`).
- **K-GC** câu hỏi cụm 「…」 mà không lựa chọn nào trích câu chứa cụm đó → soát kỹ 3d-14 #2 (không bắt buộc gắn cờ).
- **K-NQ** cùng câu trích dịch khác nhau giữa các câu con → chỉ gắn cờ khi một bản **sai nghĩa** (#6); khác lời nhưng đúng → `[Ghi chú] K-NQ … không gắn cờ`.
- **K3** (`nhieu_dung`) → #5.
- `[Nghi dính câu/định dạng]`, `dòng lặp` → xác nhận rồi sửa định dạng.

## Checklist cấu trúc

- [ ] `question.ja` = dòng câu hỏi của lời giải (khuôn lạ: câu hỏi của đề); `question.meaning` = dòng dịch.
- [ ] Mỗi lựa chọn: `option_ja` = dòng `i.` của lời giải; `meaning` = dòng `Nghĩa:`; `quotes` = các câu trích đầu dòng / sau nhãn thuần (không 「」 ngoài, không `Dịch:`); `analysis` = mọi chữ Việt còn lại, đúng thứ tự, bỏ nhãn; `is_match` = `→ ĐÚNG/SAI`; `reading = null`.
- [ ] `correct.index` = `dap_an_so`; `correct.option_ja` = `options[index-1].option_ja`; `full_sentence = null`; `summary`, `key_info` = null; `full_translation` chỉ khi có bản dịch đoạn văn.
- [ ] Mọi tiếng Nhật trong câu Việt được bọc ⟪ ⟫ (kể cả có furigana); `{ }`, furigana đúng như bản gốc.
- [ ] Soát đủ 3d-14 cho từng câu, **đối chiếu đoạn văn**.

## Mẫu file lý do (do `ghi_ly_do.py` ghi từ file đặc tả)

```json
{
  "sua": [
    {"duong_dan": "$.options[2].analysis.vi", "loai": "sai_so_ban_goc", "muc_do": "nhe",
     "ly_do": "Tác tử TẠO tách câu trích giữa câu ('… là do 「…」 (…)') ra quotes làm câu cụt – trả lại vào analysis"},
    {"duong_dan": "$.options[0].quotes[0].ja", "loai": "sua_dinh_dang", "nhom": "lap_tu", "muc_do": "nhe",
     "ly_do": "dòng trích bị dán hai lần"}
  ],
  "ghi_chu_ban_goc": ["[Đã sửa định dạng] Lựa chọn 1 – trích dẫn: dòng lặp '｜以《い》のことは…' → bỏ – dán hai lần"],
  "nghi_noi_dung": [
    {"vi_tri": "Lựa chọn 3 – giải thích", "nhom": "quan_diem",
     "mo_ta": "(3d-14 #1) Lời giải lấy ý của 'một số người cho rằng…' (đoạn 2 – ý tác giả phản bác) làm quan điểm tác giả.",
     "de_xuat": "Căn cứ đoạn cuối: 「…」 – tác giả cho rằng …, nên lựa chọn 3 SAI."}
  ]
}
```
