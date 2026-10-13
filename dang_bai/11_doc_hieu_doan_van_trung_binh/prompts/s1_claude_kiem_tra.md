# Hướng dẫn tác tử KIỂM TRA – Bước 1.2: soát JSON tiếng Việt (dạng 11 – Đọc hiểu: Đoạn văn trung bình) · v1

> Phiên bản `s1_claude_kiem_tra.11.v1` (2026-10-08): khung **cách chia v2** của dạng 07/08 (sửa định dạng / gắn cờ nội dung) + **quy tắc riêng dạng 11 (mục 3d)** + **gợi ý Python (mục 3e)**.
> Model: **Claude Opus 5.5** trong Cowork. Bản cần soát do **tác tử TẠO (Claude A, ngữ cảnh riêng)** tạo – bạn không tạo lại bản, chỉ soát và sửa.
> Dạng 11 không có phần THAM KHẢO – `reference_raw` luôn `null`, không sửa.

**Nhiệm vụ:** so JSON với **lời giải gốc** (`output/samples/norm/<id>.json` → `dau_vao`): JSON phải thể hiện đúng và đủ lời giải, không hơn, không kém; đồng thời đối chiếu lời giải với **đoạn văn** (`doan_van`) để phát hiện chỗ lời giải **sai nội dung** và gắn cờ.

## Làm gì

1. Xem từng câu bằng `python3 ../../pipeline_chung/cong_cu/xem_gd1.py --lo X Y` (đoạn văn – in một lần mỗi đoạn – + đề + lời giải gốc + gợi ý Python + JSON phẳng). Soát **theo đoạn**: đọc đoạn văn một lần rồi soát lần lượt các câu con.
2. Sửa lỗi của tác tử TẠO / lỗi định dạng (mục 1–2) và gắn cờ nội dung (mục 3) – ghi tất cả vào **một file đặc tả lô** rồi chạy `ghi_ly_do.py` (xem `SO_TAY_CHAY.md` mục 4.3). Sửa cấu trúc lớn (mảng quotes, bool is_match, chuyển đoạn giữa analysis ↔ quotes) thì sửa thẳng `output/json_vi/checked/<id>.json` bằng python read-modify-write và ghi lý do vào `sua`.
3. Chạy `python3 scripts/s1_kiem_tra.py --tu X --den Y`, xử lý lỗi K.

## Phạm vi sửa – cách chia v2

Ba việc tách bạch: **sửa lỗi tác tử TẠO**, **sửa lỗi ĐỊNH DẠNG của bản gốc**, **gắn cờ NGHI SAI NỘI DUNG**. Không sửa nội dung của bản gốc.

**1. Sửa lỗi tác tử TẠO** – `loai`: `sai_so_ban_goc` (đặt sai trường / sai lựa chọn, bỏ sót, tự thêm, viết lại, thiếu / thừa ⟪ ⟫, mất `{ }` / furigana, câu Nhật trong câu Việt bị tách thành `quotes` hoặc câu trích đứng riêng bị để trong `analysis`, còn 「」 bao ngoài câu trích / ( ) bao ngoài dòng dịch, còn nhãn dẫn, `is_match` khác kết luận của lời giải, tự tạo `summary` / `full_translation`), `chinh_ta` (lỗi do tác tử TẠO), `khach_quan`.

**2. Sửa lỗi ĐỊNH DẠNG có sẵn trong bản gốc** – `loai: sua_dinh_dang` + `nhom` (`dinh_chu`, `xuong_dong`, `lap_tu`, `chinh_ta`, `dau_cau`, `khoang_trang`, `ky_tu`, `furigana`, `khac`). Dạng 11 hay gặp:

| Trường hợp | Cách xử lý |
|---|---|
| Chữ Việt dính chữ Nhật trong một từ (`đồng⟪情する⟫` – 54150_2) **khi từ Nhật đúng kiểm chứng được** trong đoạn văn / lựa chọn (同情) | sửa thành từ đúng, vd `⟪同情する⟫` – `nhom: kanji_chen` (nhóm chung với dạng 10); không kiểm chứng được → gắn cờ `khac` |
| Lỗi gõ / lặp từ / dính câu tiếng Việt (gợi ý `[Nghi dính câu/định dạng]`) | sửa – `nhom` tương ứng |
| Câu trích gõ sai 1–2 kana so với đoạn văn **rõ là lỗi gõ** (K-TD khớp một phần) | sửa theo đoạn văn – `nhom: ky_tu`; khác chữ / khác ý → không sửa (xem 3d-1) |
| Câu hỏi / lựa chọn trong lời giải chỉ khác đề về cách viết kana ↔ kanji, số toàn góc (`cau_hoi_lech`, `lua_chon_lech`) | **không sửa**, không gắn cờ |

- Mỗi chỗ sửa định dạng có **hai** ghi chép: mục trong `sua` (`duong_dan` mức trường nhỏ nhất, `loai`, `nhom`, `muc_do`, `ly_do`) **và** một dòng `[Đã sửa định dạng] <chỗ>: '<cũ>' → '<mới>' – <lỗi gì>` (một dòng, xuống dòng ghi `⏎`). Không có thay đổi JSON → dùng `[Ghi chú] …`.
- Một trường – một loại sửa.

**3. Gắn cờ NGHI SAI NỘI DUNG – không sửa** (câu không được dịch, chuyển CTV tiếng Nhật). Khóa `nghi_noi_dung`, mỗi chỗ một mục:

```json
{"vi_tri": "Phân tích lựa chọn 3 – câu trích", "nhom": "trich_dan",
 "mo_ta": "(quy tắc 3d-1) Câu trích '…' không có trong đoạn văn – đoạn văn chỉ có '…' (ý khác).",
 "de_xuat": "Trích đúng câu '…' của đoạn 2."}
```

- `vi_tri`: `Câu hỏi`, `Câu hỏi – nghĩa`, `Phân tích lựa chọn N – nghĩa lựa chọn` / `– câu trích` / `– dịch câu trích` / `– nhận xét` / `– kết luận`, `Lựa chọn đúng`, `Toàn bộ lời giải`.
- `nhom`: `trich_dan` · `phan_tich` · `dap_an` · `nghia_cau` · `nghia_tu` · `thieu_noi_dung` · `khac`.

**3c. Quy tắc chung (phản hồi CTV)** – nghĩa câu tiếng Việt lệch câu Nhật (thêm / bớt ý, mất phủ định / bị động / sai khiến / thì, sai chủ thể) → `nghia_cau`.

**3d. Quy tắc riêng dạng 11 – Đọc hiểu (duyệt 08/10/2026)**

| # | Lỗi cần bắt | `nhom` |
|---|---|---|
| 1 | **Câu trích sai**: không có trong đoạn văn (gợi ý `TD:` / cảnh báo `K-TD`) mà không phải lỗi gõ; trích nhầm chỗ (câu trích không chứa ý mà nhận xét dựa vào); trích câu của **câu hỏi / lựa chọn** rồi gọi là câu trong đoạn văn. Trích lược bớt (`…`), trích một phần câu nhưng đúng ý → **không** gắn cờ. | `trich_dan` |
| 2 | **Nhận xét sai nội dung đoạn văn**: nói "đoạn văn không đề cập" nhưng đoạn văn có; diễn giải ngược ý đoạn văn; lý do đúng / sai dựa trên chi tiết không có hoặc hiểu sai; lập luận cho lựa chọn đúng không khớp đoạn văn. | `phan_tich` |
| 3 | **Kết luận / đáp án đáng ngờ**: kết luận ĐÚNG / SAI lệch đáp án (`ket_luan_lech_dap_an`, `nhieu_dung`); câu hỏi phủ định mà "→ ĐÚNG" dùng lẫn lộn hai nghĩa (đáp án / phù hợp đoạn văn) trong cùng lời giải; đáp án của đề có vẻ sai so với đoạn văn. | `dap_an` |
| 4 | **Dịch sai**: dịch câu hỏi, dịch lựa chọn ('Nghĩa:'), dịch câu trích lệch câu Nhật (3c) – nhất là phủ định, chủ thể, ai làm gì cho ai (あげる / くれる / もらう), thì. Dịch vụng nhưng đúng ý → không gắn cờ. | `nghia_cau` |
| 5 | **Từ vựng giải thích sai** trong nhận xét (vd giải thích nghĩa từ Nhật sai). | `nghia_tu` |
| 6 | **Thiếu nội dung**: khuôn lạ (`khuon_la` – chỉ dịch đoạn văn, chỉ vài câu giải thích, không phân tích 4 lựa chọn) → **luôn** gắn cờ; khuôn chuẩn nhưng một lựa chọn không có nhận xét nào. | `thieu_noi_dung` |
| 7 | Lỗi khác làm người học hiểu sai (từ Việt–Nhật lẫn không kiểm chứng được, câu hỏi trong lời giải khác đề về **nội dung**…). | `khac` |

- Bắt buộc so: **câu trích ↔ đoạn văn**, **nhận xét ↔ đoạn văn**, **kết luận ↔ đáp án**, **dịch câu trích / câu hỏi / lựa chọn ↔ câu Nhật**.
- **Không gắn cờ:** diễn đạt chỉ "chưa hay"; lựa chọn sai không kèm câu trích; nhận xét ngắn nhưng không sai; dịch câu trích tự do nhưng đúng ý; câu trích bỏ chú thích `注1`.

**3e. Gợi ý Python** (trong `xem_gd1.py` / `gd1_danh_sach.json` – chỉ là gợi ý, xác nhận rồi mới gắn cờ; bỏ qua gợi ý nào thì ghi `[Ghi chú] … không gắn cờ vì …`):
- **TD** / **K-TD** – câu trích không tìm thấy trong đoạn văn (so sau khi bỏ furigana, dấu câu, khoảng trắng, 注n; trích có `…` so từng mảnh). Thường do: trích câu đã ghép lựa chọn (đề điền chỗ trống), trích sai, gõ khác, trích từ câu hỏi.
- **KL** / **K-KL (gợi ý)** – kết luận ĐÚNG lệch đáp án (đã tính trường hợp câu hỏi phủ định dùng "→ ĐÚNG" = phù hợp đoạn văn).
- **LC** – dòng lựa chọn viết khác đề (thường chỉ khác kana / kanji – bỏ qua).
- **K-TR** – số câu trích JSON ↔ số đoạn 「…」 Python đếm thô: lệch thì xem tác tử TẠO có tách / gộp sai không.

**3b. Sau khi CTV tiếng Nhật trả kết quả** (chỉ khi người dùng đưa phản hồi): CTV xác nhận không sai → xóa cờ; sai → sửa theo CTV (`loai: sua_theo_ctv` + dòng `[Đã sửa theo CTV] …`), xóa cờ, chạy lại `s1_kiem_tra.py`.

**4. Âm Hán Việt** – Python tự dò; câu có âm Hán Việt không được dịch. Python dò sót → cờ nhóm `khac`.

## Checklist cấu trúc

- [ ] `question.ja` = dòng câu hỏi của lời giải (không có → câu hỏi của đề); `question.meaning` = dòng dịch câu hỏi.
- [ ] Mỗi lựa chọn: `option_ja` = dòng `i.` của lời giải (có furigana); `reading = null`; `meaning` = dòng `Nghĩa:`; `quotes` = câu trích đứng riêng (bỏ 「」 bao ngoài; dịch bỏ ( ) bao ngoài); `analysis` = phần nhận xét còn lại, đủ chữ, đúng thứ tự; `is_match` = kết luận của lời giải.
- [ ] Câu Nhật nằm trong câu tiếng Việt ở lại `analysis` (bọc ⟪ ⟫); nhãn dẫn đã bỏ, nhãn dẫn mang nội dung giữ trong `analysis`.
- [ ] `correct.index` = `dap_an_so`; `correct.option_ja` giống hệt lựa chọn đó; `correct.full_sentence = null`; `summary = key_info = null`; `full_translation = null` (trừ khuôn lạ có bản dịch đoạn văn).
- [ ] ⟪ ⟫ quanh mọi tiếng Nhật trong câu Việt (giữ furigana bên trong); `{ }` như lời giải.
- [ ] Soát đủ 3c, 3d, 3e.

## Mẫu lý do (một mẫu trong file đặc tả lô)

```json
"54150_2": {
  "thay": [{"duong_dan": "$.options[3].analysis.vi", "cu": "đồng⟪情する⟫", "moi": "⟪同情する⟫"}],
  "sua": [{"duong_dan": "$.options[3].analysis.vi", "loai": "sua_dinh_dang", "nhom": "kanji_chen", "muc_do": "nhe", "ly_do": "chữ Việt 'đồng' dính chữ Nhật – từ đúng 同情する (có trong lựa chọn 4)"}],
  "ghi_chu_ban_goc": ["[Đã sửa định dạng] Lựa chọn 4 – nhận xét: 'đồng情する' → '同情する' – chữ Việt dính chữ Nhật"],
  "nghi_noi_dung": [{"vi_tri": "Toàn bộ lời giải", "nhom": "thieu_noi_dung", "mo_ta": "(quy tắc 3d-6) Khuôn lạ: chỉ vài câu giải thích, không phân tích 4 lựa chọn.", "de_xuat": "Viết lại theo khuôn: dịch câu hỏi, từng lựa chọn (Nghĩa / Trích dẫn / nhận xét / kết luận)."}]
}
```
- `loai`: `sai_so_ban_goc` | `chinh_ta` | `khach_quan` | `chu_quan` | `sua_dinh_dang` (bắt buộc `nhom` + dòng `[Đã sửa định dạng]`) | `sua_theo_ctv`. `muc_do`: `nghiem_trong` | `nang` | `nhe`.
