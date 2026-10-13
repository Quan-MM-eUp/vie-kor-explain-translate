# Hướng dẫn tác tử KIỂM TRA – Bước 1.2: kiểm tra JSON tiếng Việt và sửa lỗi (dạng 13 – Đọc hiểu tổng hợp) · v1

> Phiên bản `s1_claude_kiem_tra.13.v1` (2026-10-08) – cách chia v2 (như 07–09) + tiêu chí riêng đọc hiểu tổng hợp (duyệt 08/10/2026, mục 3d).
> Model: **Claude Opus 5.5** trong Cowork. Bản cần kiểm tra do **tác tử TẠO (Claude A)** tạo – mọi chỗ "bản GPT" / "lỗi GPT" (trong công cụ, báo cáo) hiểu là bản / lỗi của tác tử TẠO. Bạn không tạo lại bản, chỉ soát và sửa.

**Nhiệm vụ:** kiểm tra JSON tiếng Việt **so với lời giải gốc** (và đoạn văn A / B) rồi sửa lỗi của tác tử TẠO / lỗi định dạng, gắn cờ nghi sai nội dung. JSON phải thể hiện **đúng và đủ** lời giải gốc, không hơn, không kém.

## Làm gì

Xem từng câu: `python3 ../../pipeline_chung/cong_cu/xem_gd1.py <id> …` (đề + **đoạn văn A/B in một lần cho mỗi đoạn** + lời giải gốc + gợi ý Python + JSON phẳng). Danh sách: `output/claude/gd1_danh_sach.json` (cờ `co`, ghi chú tự động, kết quả Python trên bản tạo – gồm `[Âm Hán Việt]`, `[Nghi dính câu/định dạng]`, và gợi ý câu trích `[Từ điển Sudachi] K-TD / K-NGUON` – tên nhãn giữ như dạng khác, dạng 13 không dùng Sudachi). **Soát theo đoạn văn** – đọc đoạn văn A / B trước, rồi các câu con.

1. Đọc `output/samples/norm/<id>.json`: `de`, `doan_van` (A/B), `dau_vao` (lời giải đã chuẩn hóa – `{ }` là in đậm / gạch chân gốc), `khuon`, `co`, `phan` (Python tách: câu trích, nhãn đoạn lời giải nêu `nhan_neu`, đoạn thật chứa câu trích `nhan_thay`, mức khớp `muc`).
2. Sửa trực tiếp `output/json_vi/checked/<id>.json` nếu có lỗi (giữ schema `reading_listening.v1`).
3. Ghi kết quả bằng **file đặc tả lô + `ghi_ly_do.py`** (SO_TAY_CHAY mục 4.3) – `sua`, `ghi_chu_ban_goc`, `nghi_noi_dung`.
4. Xong lô thì chạy `python3 scripts/s1_kiem_tra.py --tu X --den Y`.

## Phạm vi sửa – cách chia v2

Ba việc tách bạch: **sửa lỗi tác tử TẠO**, **sửa lỗi ĐỊNH DẠNG của bản gốc**, **gắn cờ NGHI SAI NỘI DUNG**. Không sửa nội dung bản gốc.

**1. Sửa lỗi của tác tử TẠO** (`sai_so_ban_goc` / `chinh_ta` / `khach_quan`): đặt sai trường; gộp / tách sai câu trích (câu trích khối phải ở `quotes`, mỗi câu một phần tử, bản dịch `(…)` vào `quotes[].meaning`; câu trích giữa câu Việt phải ở lại `analysis`); còn cặp 「」 ngoài cùng trong `quotes[].ja`; bỏ mất câu dẫn có thông tin (`Đoạn A có câu:`…); để sót nhãn trống `Trích dẫn:` / `Giải thích:`; `is_match` sai so với dòng kết luận; tự thêm / viết lại; sai ⟪ ⟫ / { } / furigana; `question.ja` / `option_ja` chép theo đề thay vì theo lời giải.

**2. Sửa lỗi ĐỊNH DẠNG có sẵn trong bản gốc** – `loai: sua_dinh_dang` + `nhom` (`dinh_chu`, `xuong_dong`, `lap_tu`, `chinh_ta`, `dau_cau`, `khoang_trang`, `ky_tu`, `furigana`, `khac`):
- Ví dụ: dính câu; lặp chữ do gõ trong câu Nhật (`占占い`, `呼呼んで`, `お願いいしたい`, `であるる`); **ruby hỏng** (cách đọc lặp sau chữ Hán `一度いちど;傷;きずつき`, `<|起;お|き`) → bỏ phần đọc lặp / khôi phục `｜X《y》` như chỗ khác; từ Nhật gõ dính chữ Việt (`đồng情する`) → tách và bọc ⟪ ⟫.
- Mỗi chỗ: mục `sua` (`duong_dan` mức trường nhỏ nhất, `loai`, `nhom`, `muc_do`, `ly_do`) **và** dòng `ghi_chu_ban_goc`: `[Đã sửa định dạng] <chỗ>: '<cũ>' → '<mới>' – <lỗi gì>` (một dòng).
- Câu Nhật (`question.ja`, `option_ja`, `quotes[].ja`) Python so với lời giải – sửa định dạng ở đây phải có mục `sua_dinh_dang` đúng đường dẫn. Lời giải viết **khác đề / khác đoạn văn về chữ – nghĩa** → **gắn cờ**, không sửa.
- **Một trường – một loại sửa** (như các dạng trước).

**3. Gắn cờ NGHI SAI NỘI DUNG – không sửa** (câu **không được dịch**, chuyển CTV tiếng Nhật) – khóa `nghi_noi_dung`, mỗi chỗ một mục `{vi_tri, nhom, mo_ta, de_xuat}`:
- `vi_tri`: `Câu hỏi`, `Câu hỏi – nghĩa`, `Lựa chọn N – nghĩa`, `Lựa chọn N – câu trích k`, `Lựa chọn N – nghĩa câu trích k`, `Lựa chọn N – phân tích`, `Lựa chọn N – kết luận`, `Toàn câu`.
- `mo_ta`: vì sao nghi (ghi số quy tắc 3d-x); `de_xuat`: cách sửa đề xuất – không sửa vào JSON.

**3d. Tiêu chí riêng dạng 13 (duyệt 08/10/2026)**

| # | Gắn cờ khi | `nhom` |
|---|---|---|
| 1 | **Câu trích sai**: không có trong đoạn văn (gợi ý `K-TD` / cờ `trich_dan_ngoai_doan` – kiểm tay, bỏ qua lệch do ruby / dấu câu / `…` rút gọn), **gán nhầm đoạn A ↔ B** (gợi ý `K-NGUON` / cờ `trich_dan_sai_nguon`, hoặc tự phát hiện – vd "Đoạn A có câu" nhưng câu nằm ở B, "phần trả lời của A" nhưng là lời B), trích sai chỗ, hoặc câu trích **không chứng minh được** điều phân tích nói | `trich_dan` |
| 2 | **Phân tích sai quan điểm A / B**: nói "cả A và B đều…" nhưng chỉ một bên nói (hoặc ngược lại); đảo quan điểm A ↔ B; nói "đoạn văn không đề cập" nhưng có; lập luận trái nội dung đoạn văn; lý do loại không liên quan lựa chọn. **Phải đọc đoạn văn.** | `phan_tich` |
| 3 | **Kết luận / đáp án**: kết luận ĐÚNG ≠ 1 lựa chọn (cờ `nhieu_dung`, cảnh báo K4), ĐÚNG lệch đáp án (`lech_dap_an`), lời giải lập luận ủng hộ lựa chọn khác đáp án | `dap_an` |
| 4 | **Nghĩa sai**: dịch câu hỏi / lựa chọn / câu trích lệch câu Nhật (sai chủ thể A/B, mất phủ định, sai so sánh, thêm bớt ý – vd 「自分で自分のイメージを決めてしまわずに…身につけてみては」 dịch thành "thử theo anh ta một lần") | `nghia_cau` |
| 5 | **Khuôn lạ – thiếu phân tích các lựa chọn** (cờ `khuon_la`: `dich_doan_van`, `chi_dap_an`, `goi_y`, `khuon_khac`); hoặc khuôn chuẩn nhưng có lựa chọn không có nhận xét làm người học không hiểu vì sao loại | `thieu_noi_dung` |
| 6 | Câu hỏi / lựa chọn trong lời giải **khác đề về chữ – nghĩa** (cờ `cau_hoi_lech`, `lua_chon_lech` – trừ lệch kana / chữ Hán cùng cách đọc, lặp chữ do gõ, ruby hỏng → sửa định dạng hoặc bỏ qua) | `cau_khac_de` |
| 7 | Khác (ghi rõ) – vd đoạn tiếng Nhật chen vào câu Việt bị hỏng không còn hiểu được (16885_2: "…と述べているとは述べていない") | `khac` |

**Không gắn cờ:** phân tích sơ sài nhưng không sai; lựa chọn sai không kèm câu trích; dịch vụng nhưng đúng ý; câu trích rút gọn bằng `…`; câu trích lệch đoạn văn chỉ do ruby / dấu câu / chú thích `注`; đoạn N2 không có A/B (`doan_khong_ab` – chỉ là lưu ý phân loại, đã ghi NHAT_KY); câu trích **giữa câu** giữ trong analysis. Gợi ý bỏ qua thì ghi `[Ghi chú] K-TD/K-NGUON … không gắn cờ vì …` vào `ghi_chu_ban_goc`.

- Câu có cờ `trich_dan_sai_nguon` từ Python **chỉ là gợi ý** (Python dò nhãn A/B quanh câu trích, có thể nhầm khi một câu dẫn nói về cả hai đoạn) – đọc lại rồi mới gắn cờ.
- K-NQ (cùng câu trích dịch khác nhau giữa các câu con) – lời giải gốc khác nhau là bình thường; chỉ gắn cờ `nghia_cau` khi một bản dịch sai.

**3b. Sau khi CTV tiếng Nhật trả kết quả** (khi người dùng đưa phản hồi CTV): như các dạng trước – CTV xác nhận không sai → xóa cờ; sai → sửa JSON theo CTV (`loai: sua_theo_ctv` + `nhom` + `[Đã sửa theo CTV] …`), xóa cờ, chạy lại `s1_kiem_tra.py`.

**4. Âm Hán Việt** – Python tự dò (`[Âm Hán Việt] …`); câu có âm Hán Việt tự động không dịch. Python dò sót → cờ `khac`.

**Dạng của câu:** có ít nhất một `sua_dinh_dang` → Dạng 2; không → Dạng 1. Chỉ câu **không có** `nghi_noi_dung` và không có âm Hán Việt mới được chốt và dịch.

## Checklist cấu trúc

- [ ] `question.ja` = dòng câu hỏi của lời giải; `question.meaning` = dòng dịch (null nếu không có).
- [ ] 4 lựa chọn: `option_ja` = dòng `i.` của lời giải; `meaning` = dòng `Nghĩa:`; `quotes` = mọi câu trích **khối**, theo thứ tự, `ja` không có 「」 ngoài cùng, `meaning` = bản dịch trong ngoặc; `analysis` = chữ còn lại theo thứ tự (giữ câu dẫn có A/B, câu trích giữa câu bọc ⟪ ⟫); `is_match` = dòng kết luận.
- [ ] `correct.index` = `dap_an_so`; `correct.option_ja` giống hệt lựa chọn đó; `full_sentence`, `summary`, `key_info` = null; `full_translation` chỉ ở khuôn `dich_doan_van`.
- [ ] `{ }`, furigana, ⟪ ⟫ đúng như bản gốc.
- [ ] Đã soát đủ 3d-1…7 **có đọc đoạn văn**, mọi gợi ý K-TD / K-NGUON, cảnh báo K4 / K-QN / K-TR.

## Mẫu file lý do

```json
{
  "sua": [
    {"duong_dan": "$.options[1].analysis.vi", "loai": "sai_so_ban_goc", "muc_do": "nhe",
     "ly_do": "tác tử TẠO để sót bản dịch '(Tất nhiên, …)' của câu trích trong analysis – đã có ở quotes[0].meaning"},
    {"duong_dan": "$.options[0].option_ja", "loai": "sua_dinh_dang", "nhom": "lap_tu", "muc_do": "nhe",
     "ly_do": "lặp chữ do gõ: '占占い' → '占い'"}
  ],
  "ghi_chu_ban_goc": ["[Đã sửa định dạng] Lựa chọn 1: '占占い' → '占い' – lặp chữ do gõ"],
  "nghi_noi_dung": [
    {"vi_tri": "Lựa chọn 1 – câu trích 1", "nhom": "trich_dan",
     "mo_ta": "(3d-1) Lời giải nói 'Đoạn A có câu' nhưng 「努力できる人にとっては…」 nằm ở đoạn B.",
     "de_xuat": "Đổi câu dẫn thành 'Đoạn B có câu:'."}
  ]
}
```

- `loai`: `sai_so_ban_goc` | `chinh_ta` | `khach_quan` | `chu_quan` (lỗi tác tử TẠO) | `sua_dinh_dang` (lỗi định dạng bản gốc) | `sua_theo_ctv` (sau CTV). `muc_do`: `nghiem_trong` | `nang` | `nhe`.
