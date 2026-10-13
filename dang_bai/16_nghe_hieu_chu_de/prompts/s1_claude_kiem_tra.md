# Hướng dẫn tác tử KIỂM TRA – Bước 1.2: kiểm tra JSON tiếng Việt và sửa lỗi (dạng 16 – Nghe hiểu chủ đề) · v1

> Phiên bản `s1_claude_kiem_tra.16.v1` (2026-10-08). Khung cách chia v2 như dạng 07 / 09 + tiêu chí riêng dạng 16 (mục 3d).
> Model: **Claude Opus 5.5** trong Claude Cowork (không qua API). Tác tử con (nếu có) cũng dùng Opus 5.5.
> Bản cần kiểm tra do **tác tử TẠO (Claude A)** tạo – hoặc **Python dựng** với câu không có phân tích (`tao_bang = python`). Mọi chỗ "bản tạo" dưới đây hiểu là bản đó. Bạn không tạo lại bản, chỉ soát và sửa.

**Nhiệm vụ:** kiểm tra JSON tiếng Việt **so với lời giải gốc** (và lời thoại gốc), sửa lỗi của bản tạo / lỗi định dạng, gắn cờ nghi sai nội dung. JSON phải thể hiện đúng và đủ lời giải gốc, không hơn, không kém.

> **Quy tắc THAM KHẢO (2026-10-07):** dạng 16 không có phần tham khảo – `reference_raw` luôn null (Python điền, không sửa).

## Làm gì

Danh sách câu: `output/claude/gd1_danh_sach.json` (tạo bằng `python3 scripts/s1_claude_goi.py …`). Xem từng câu: **`python3 scripts/xem16.py <id> …`** (hoặc `--lo X Y`) – in đề, lời giải gốc đã tách (J = dòng Nhật, V = dòng Việt, khối 1.–4.), gợi ý Python, và JSON với **đường dẫn đầy đủ** từng trường.

Với mỗi câu:
1. Đọc lời giải gốc đã tách (`dau_vao` trong `output/samples/norm/<id>.json`, `xem16.py` in sẵn).
2. Soát `output/json_vi/checked/<id>.json` (đã chép từ bản tạo); sửa trực tiếp nếu có lỗi – qua file đặc tả lô (`SO_TAY_CHAY.md` mục 4.3) hoặc python read-modify-write cho thay đổi cấu trúc.
3. Ghi kết quả (sua / ghi_chu_ban_goc / nghi_noi_dung) qua file đặc tả lô + `ghi_ly_do.py` (xóa `_huong_dan`).
4. Xong lô: `python3 scripts/s1_kiem_tra.py …` (cùng phạm vi) và báo kết quả.

## Phạm vi sửa – cách chia v2

Ba việc tách bạch: **sửa lỗi bản tạo**, **sửa lỗi ĐỊNH DẠNG của bản gốc**, **gắn cờ NGHI SAI NỘI DUNG**. Không sửa nội dung bản gốc.

**1. Sửa lỗi bản tạo** (`sai_so_ban_goc` / `chinh_ta` / `khach_quan`): đặt sai trường (nhận xét nằm nhầm lựa chọn, câu trích giữa câu bị tách ra quotes làm mất chữ, phần dẫn bị chép vào analysis, câu nhận xét sau `→ ĐÚNG/SAI` bị bỏ), `option_ja` khác đề, `meaning` của lựa chọn chữ bị bỏ / lựa chọn tranh có meaning, `is_match` sai so với kết luận của khối, thiếu ⟪ ⟫, tự sửa câu trích cho khớp lời thoại, ghép dòng sai (câu `lech_dong`: dòng Việt gán nhầm dòng Nhật, bỏ dòng, tự dịch).

**2. Sửa lỗi ĐỊNH DẠNG có sẵn trong bản gốc** – `loai: sua_dinh_dang` + `nhom` (`dinh_chu`, `xuong_dong`, `lap_tu`, `chinh_ta`, `dau_cau`, `khoang_trang`, `ky_tu`, `furigana`, `khac`) + dòng `[Đã sửa định dạng] <chỗ>: '<cũ>' → '<mới>' – <lỗi gì>` trong `ghi_chu_ban_goc` (một dòng, xuống dòng ghi `⏎`).
- Ví dụ: dính câu trong nhận xét; lặp từ; dấu câu thừa; ruby hỏng (cách đọc lặp ngay sau chữ Hán) trong câu trích.
- **Không** sửa định dạng lời thoại tiếng Nhật (`lines[].ja`) và câu trích về chữ – lỗi gõ trong lời thoại gốc (`わかしました`, `準備はん済んでいます`) **giữ nguyên**, chỉ ghi `[Ghi chú] Lời thoại gốc gõ nhầm '…' (… ) – giữ nguyên` (quyết định Q6 ngày 2026-10-08).
- **Một trường – một loại sửa** (như dạng 07/09): trường đã có `sua_dinh_dang` thì không sửa lỗi bản tạo trên cùng trường; trùng thì ưu tiên sửa lỗi bản tạo, lỗi định dạng ghi thành mô tả.

**3. Gắn cờ NGHI SAI NỘI DUNG – không sửa** (câu không được dịch, chuyển CTV tiếng Nhật) – khóa `nghi_noi_dung`, mỗi chỗ một mục `{vi_tri, nhom, mo_ta, de_xuat}`:
- `vi_tri`: `Lời thoại – dòng N`, `Câu hỏi`, `Phân tích chung`, `Phân tích lựa chọn N`, `Phân tích lựa chọn N – câu trích`, `Phân tích lựa chọn N – nghĩa lựa chọn`, `Đáp án`, `Phân tích các lựa chọn`.
- `nhom`: `nghia_cau` · `trich_dan` · `phan_tich` · `dap_an` · `thieu_noi_dung` · `khac`.
- Không chắc lắm cũng gắn cờ (CTV quyết) – nhưng không gắn cờ cho cách diễn đạt chỉ "chưa hay".

### 3d. Tiêu chí riêng dạng 16 (duyệt 2026-10-08)

| # | Gắn cờ khi | `nhom` |
|---|---|---|
| 1 | **Bản dịch lời thoại sai nghĩa** so với dòng Nhật: sai chủ thể / người nói, mất phủ định / bị động / sai khiến / thì, sai số liệu (giờ, ngày, giá, số lượng), thiếu hẳn một ý, dịch nhầm sang dòng khác. Dịch thoáng nhưng đúng ý → không cờ. **Chỉ soát kỹ các dòng liên quan đến đáp án** (dòng có `(i)`, dòng in đậm `{ }`, dòng được trích trong phân tích) và câu hỏi; các dòng khác đọc lướt. | `nghia_cau` |
| 2 | **Câu hỏi** dịch sai (hỏi "làm gì trước" thành "làm gì", sai chủ thể) | `nghia_cau` |
| 3 | **Câu trích không có trong lời thoại** (cờ s0 `trich_ngoai_loi_thoai`, cảnh báo `K-TD`): khác chữ làm đổi nghĩa, hoặc lấy câu của người khác; hoặc câu trích **không chứng minh được** điều phân tích nói; hoặc dịch câu trích sai nghĩa. Khác do gõ nhầm 1–2 kana / dấu câu / furigana → không cờ, ghi `[Ghi chú]`. | `trich_dan` |
| 4 | **Phân tích trái nội dung lời thoại**: nói "không nhắc đến" nhưng có; suy luận sai thứ tự việc (dạng "làm gì trước / tiếp theo"); nhầm người nói; lý do chọn / loại không liên quan lựa chọn; tự mâu thuẫn. Mô tả tranh: **không kiểm chứng được** – chỉ gắn cờ khi mô tả tranh mâu thuẫn với chính lời thoại / kết luận (vd nói tranh có sách chữ Hán rồi kết luận thiếu sách chữ Hán). | `phan_tich` |
| 5 | **Kết luận trái đáp án**: khối đáp án bị kết luận SAI, khối khác kết luận ĐÚNG, nhiều / không có ĐÚNG (cờ `lech_dap_an`, `nhieu_dung`, `khong_co_dung`, cảnh báo K4); hoặc đọc lời thoại thấy **đáp án của đề sai** | `dap_an` |
| 6 | **Thiếu phân tích**: câu `tao_bang = python` (lời giải chỉ có bản dịch / lời thoại) – Python đã điền sẵn cờ: **xác nhận** (sửa mô tả nếu cần); khối có lựa chọn mà chỉ chép lại lời thoại, không nói vì sao đúng / sai | `thieu_noi_dung` |
| 7 | **Lời thoại / bản dịch thiếu**: bản dịch thiếu hẳn một lượt thoại quan trọng (dòng Nhật `meaning = null` mà dòng đó liên quan đáp án), câu thiếu lời thoại tiếng Nhật (cờ `thieu_loi_thoai`) | `thieu_noi_dung` |

**Không gắn cờ:** nhãn người nói khác nhau giữa Nhật / Việt (người nói lấy theo dòng Nhật); bản dịch không có `(i)`; lời thoại gõ nhầm không đổi nghĩa (giữ nguyên + `[Ghi chú]`); phân tích sơ sài nhưng không sai; lựa chọn sai không kèm câu trích; câu dịch vụng nhưng đúng ý; mô tả tranh không kiểm chứng được.

### 3e. Soát cấu trúc (lỗi bản tạo → sửa)

- [ ] `full_translation`: Python ghép theo số dòng (trừ câu `lech_dong` – tác tử TẠO ghép). Soát mỗi dòng Việt có đúng là bản dịch của dòng Nhật cùng hàng (đặc biệt câu có cờ `nguoi_noi_lech`). Ghép lệch (dòng Việt trượt sang dòng Nhật khác) → sửa lại `meaning` cho đúng hàng (`sai_so_ban_goc`, ghi rõ 'ghép dòng lệch'), không sửa chữ, không sửa `ja` / `speaker`; nếu lỗi ghép lặp lại ở nhiều câu → báo người dùng (sửa `scripts/_nghe.py`). Câu `lech_dong`: soát đủ dòng Nhật đúng thứ tự (K8), không mất dòng Việt (K9), mỗi dòng Việt đúng dòng Nhật.
- [ ] `question.ja` = câu hỏi tiếng Nhật (dòng lặp cuối / câu hỏi trong dòng mở đầu); `question.meaning.vi` = dòng dịch tương ứng hoặc null.
- [ ] `summary` = đoạn phân tích mở đầu (null nếu không có).
- [ ] Mỗi lựa chọn: `option_ja` = đề; `reading = null`; `meaning` = `Nghĩa:` / phần (…) sau dòng `n.` / bản dịch lựa chọn (tranh → null); `quotes` = câu trích tách được (đúng thứ tự, ja chép nguyên, meaning = phần trong ngoặc); `analysis` = phần còn lại (cả câu sau `→ ĐÚNG/SAI`), câu trích giữa câu giữ nguyên trong analysis; `is_match` = kết luận khối.
- [ ] `correct = {index: dap_an_so, option_ja: options[index-1].option_ja, full_sentence: null}`; `key_info = null`.
- [ ] Mọi tiếng Nhật trong trường `vi` bọc ⟪ ⟫; furigana / `{ }` / `(i)` đúng như bản gốc.

**Python kiểm tra** (`s1_kiem_tra.py`): K1 option_ja = đề · K2 is_match = kết luận khối · K3 correct · K4 (cảnh báo) kết luận ↔ đáp án · K5 câu trích bị bỏ · K-TD câu trích ngoài lời thoại · K7 nghĩa lựa chọn tranh · K8 dòng Nhật / speaker của full_translation = lời thoại gốc · K9 đủ chữ (từng khối, full_translation, summary) · K10 summary ↔ đoạn mở đầu · K11 key_info null · K12 / K-CH câu hỏi · cộng kiểm tra chung (độ phủ tiếng Việt ≥ 97%, mất tiếng Nhật, furigana, `{ }`, ⟪ ⟫). K8 / K9 tính trên bản đã hoàn tác chỗ `sua_dinh_dang`.

**3b. Sau khi CTV tiếng Nhật trả kết quả** (chỉ làm khi người dùng đưa phản hồi CTV): CTV xác nhận không sai → xóa mục cờ; sai → sửa JSON theo CTV (`"loai": "sua_theo_ctv"` + `nhom` + dòng `[Đã sửa theo CTV] …`), xóa mục cờ; câu thiếu phân tích CTV viết thêm → đưa vào analysis / quotes theo đúng ánh xạ; chạy lại `s1_kiem_tra.py`.

**4. Âm Hán Việt**: Python tự dò (`[Âm Hán Việt] …`) – câu có âm Hán Việt tự động không được dịch.

**Dạng của câu:** có ít nhất một `sua_dinh_dang` → Dạng 2; không → Dạng 1. Chỉ câu không có `nghi_noi_dung` và không có âm Hán Việt mới được chốt và dịch.

## Mẫu file lý do (qua file đặc tả lô)

```json
{"sua": [{"duong_dan": "$.options[1].analysis.vi", "loai": "sai_so_ban_goc", "muc_do": "nang",
          "ly_do": "Bản tạo bỏ mất câu nhận xét sau '→ SAI.' của khối 2 – bổ sung đúng nguyên văn"}],
 "ghi_chu_ban_goc": ["[Ghi chú] Lời thoại gốc dòng 9 gõ nhầm 'わかしました' (わかりました) – giữ nguyên"],
 "nghi_noi_dung": [{"vi_tri": "Phân tích lựa chọn 3 – câu trích", "nhom": "trich_dan",
                    "mo_ta": "(3d-3) Câu trích 「…」 là lời của người đàn ông nhưng phân tích nói là người phụ nữ nói.",
                    "de_xuat": "Người đàn ông nói: 「…」"}]}
```
- `loai`: `sai_so_ban_goc` | `chinh_ta` | `khach_quan` | `chu_quan` (lỗi bản tạo) | `sua_dinh_dang` (bắt buộc `nhom` + `[Đã sửa định dạng]`) | `sua_theo_ctv`. `muc_do`: `nghiem_trong` | `nang` | `nhe`.
