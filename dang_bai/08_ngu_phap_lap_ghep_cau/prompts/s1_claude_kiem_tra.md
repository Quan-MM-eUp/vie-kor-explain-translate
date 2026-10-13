# Hướng dẫn tác tử KIỂM TRA – Bước 1.2: soát JSON tiếng Việt (dạng 08 – Lắp ghép câu) · v1

> Phiên bản `s1_claude_kiem_tra.08.v1` (2026-10-08): khung **cách chia v2** của dạng 07 (sửa định dạng / gắn cờ nội dung) + **quy tắc riêng dạng 08 (mục 3d)** + **gợi ý Python ghép câu (mục 3e)**.
> Model: **Claude Opus 5.5** trong Cowork. Bản cần soát do **tác tử TẠO (Claude A, ngữ cảnh riêng)** tạo – bạn không tạo lại bản, chỉ soát và sửa.
> **Quy tắc THAM KHẢO (2026-10-07):** phần THÔNG TIN / NGỮ PHÁP THAM KHẢO không kiểm tra, không sửa, không gắn cờ; Python chép nguyên văn vào `reference_raw` – không sửa trường này.

**Nhiệm vụ:** so JSON với **lời giải gốc** (`output/samples/norm/<id>.json` → `dau_vao`): JSON phải thể hiện đúng và đủ lời giải, không hơn, không kém; đồng thời phát hiện chỗ lời giải gốc **sai nội dung** để gắn cờ.

## Làm gì

1. Xem từng câu bằng `python3 ../../pipeline_chung/cong_cu/xem_gd1.py --lo X Y` (đề + lời giải gốc + gợi ý Python + JSON phẳng).
2. Sửa lỗi của tác tử TẠO / lỗi định dạng (mục 1–2) và gắn cờ nội dung (mục 3) – ghi tất cả vào **một file đặc tả lô** rồi chạy `ghi_ly_do.py` (xem `SO_TAY_CHAY.md` mục 4.3). Sửa cấu trúc lớn (mảng, bool) thì sửa thẳng `output/json_vi/checked/<id>.json` bằng python read-modify-write và ghi lý do vào `sua`.
3. Chạy `python3 scripts/s1_kiem_tra.py --tu X --den Y`, xử lý lỗi K.

## Phạm vi sửa – cách chia v2

Ba việc tách bạch: **sửa lỗi tác tử TẠO**, **sửa lỗi ĐỊNH DẠNG của bản gốc**, **gắn cờ NGHI SAI NỘI DUNG**. Không sửa nội dung của bản gốc.

**1. Sửa lỗi tác tử TẠO** – `loai`: `sai_so_ban_goc` (đặt sai trường, bỏ sót, tự thêm, viết lại, thiếu / thừa ⟪ ⟫, mất `{ }` / ★ / furigana, `gloss` sai dạng, gộp / tách sai ý `sentence_analysis` hoặc `explanation`, `order` khác `thu_tu_python_ghep`, câu hoàn chỉnh đặt nhầm vào `correct`), `chinh_ta` (lỗi do tác tử TẠO), `khach_quan`.

**2. Sửa lỗi ĐỊNH DẠNG có sẵn trong bản gốc** – `loai: sua_dinh_dang` + `nhom` (`dinh_chu`, `xuong_dong`, `lap_tu`, `chinh_ta`, `dau_cau`, `khoang_trang`, `ky_tu`, `furigana`, `khac`). Dạng 08 hay gặp:

| Trường hợp | Cách xử lý |
|---|---|
| ★ lẫn trong `Cách đọc` của câu hoàn chỉnh (cờ `doc_co_sao`, cảnh báo K-DOC) | bỏ ★ khỏi `arrangement.full_sentence.reading` – `nhom: ky_tu` |
| Câu hoàn chỉnh lệch đề **chỉ do gõ** kana / ký hiệu (`ghep_lech_nhe`, vd パーテイー ↔ パーティー, thiếu `？`) | sửa `full_sentence.ja` theo đề – `nhom: ky_tu` / `dau_cau` |
| Câu đề trong lời giải gõ sai so với đề (lặp chữ, thiếu dấu) | sửa `question.ja` theo đề |
| Số gõ nhầm ở LỰA CHỌN ĐÚNG (`lcd_go_nham_so`) | JSON đã theo `dap_an_so` – chỉ ghi `[Đã sửa định dạng]` |
| Rác chen vào câu (vd `ごうかく` thừa giữa câu – 8245) **khi chắc chắn là rác** | bỏ – `nhom: khac`; không chắc → gắn cờ |

- Mỗi chỗ sửa định dạng có **hai** ghi chép: mục trong `sua` (`duong_dan` mức trường nhỏ nhất, `loai`, `nhom`, `muc_do`, `ly_do`) **và** một dòng `[Đã sửa định dạng] <chỗ>: '<cũ>' → '<mới>' – <lỗi gì>` (một dòng, xuống dòng ghi `⏎`). Không có thay đổi JSON → dùng `[Ghi chú] …`.
- Câu tiếng Nhật (`question.*`, `option_ja`, `full_sentence.*`) Python so với lời giải (K8): sửa mà không có mục `sua` đúng đường dẫn → LỖI.
- Một trường – một loại sửa (sửa định dạng làm Python trả cả trường về bản tạo khi đo độ phủ).

**3. Gắn cờ NGHI SAI NỘI DUNG – không sửa** (câu không được dịch, chuyển CTV tiếng Nhật). Khóa `nghi_noi_dung`, mỗi chỗ một mục:

```json
{"vi_tri": "Phân tích lựa chọn 4 – khả năng sắp xếp", "nhom": "kha_nang_sap_xep",
 "mo_ta": "(quy tắc 3d-3) Nói 'いいので' đứng trước 'からだに' – trong câu hoàn chỉnh 'からだに いいので' nó đứng SAU.",
 "de_xuat": "Có thể đứng sau 'からだに' để tạo thành 'からだにいいので' (vì tốt cho cơ thể)."}
```

- `vi_tri`: `Câu đề`, `Câu đề – cách đọc`, `Câu đề – nghĩa`, `Phân tích đề bài`, `Phân tích lựa chọn N – nghĩa lựa chọn` / `– ngữ pháp` / `– khả năng sắp xếp`, `Cách sắp xếp`, `Câu hoàn chỉnh`, `Câu hoàn chỉnh – cách đọc`, `Câu hoàn chỉnh – nghĩa`, `Vị trí ★`, `Lựa chọn đúng`.
- `nhom`: `cau_khac_de` · `dap_an` · `kha_nang_sap_xep` · `ngu_phap` · `nghia_tu` · `nghia_cau` · `cach_doc` · `thieu_noi_dung` · `khac`.

**3c. Quy tắc chung (phản hồi CTV)** – nghĩa câu tiếng Việt lệch câu Nhật (thêm / bớt ý, mất phủ định / bị động / sai khiến / thì) → `nghia_cau`; giải thích ngữ pháp sai kiến thức → `ngu_phap`.

**3d. Quy tắc riêng dạng 08 – Lắp ghép câu (duyệt 08/10/2026)**

| # | Lỗi cần bắt | `nhom` |
|---|---|---|
| 1 | **Câu hoàn chỉnh khác đề + lựa chọn về chữ / nghĩa** (cờ `ghep_lech_nang`, gợi ý `A:`; vd 5995 時給は安い ↔ đề 給料が安い; 8429 ３万円 ↔ ３千円). Chỉ khác dấu câu / khoảng trắng / kana gõ nhầm → sửa định dạng (mục 2). | `cau_khac_de` |
| 2 | **Ô ★ / đáp án đáng ngờ**: theo câu hoàn chỉnh, ô ★ là lựa chọn khác đáp án (`sao_lech_dap_an`, K11); dòng `Vị trí ★` ghi khác đáp án (`vi_tri_sao_lech`); LỰA CHỌN ĐÚNG khác đề cả số lẫn nội dung (`lech_dap_an`). | `dap_an` |
| 3 | **'Khả năng sắp xếp' mâu thuẫn với cách sắp xếp đúng** (gợi ý `SX:` – vd 19634 'いいので' nói đứng trước 'からだに' nhưng thực tế đứng sau); cụm ghép nêu ra không xuất hiện trong câu đúng mà trình bày như cách ghép đúng. Cách nói "có thể đứng trước / sau …" chung chung, không trái câu đúng → không gắn cờ. | `kha_nang_sap_xep` |
| 4 | **Giải thích ngữ pháp sai kiến thức**: loại từ sai (大切 là tính từ đuôi な nhưng ghi 'Tính từ đuôi い (bỏ い) + か'), thể / cách chia sai, nghĩa mẫu ngữ pháp sai. | `ngu_phap` |
| 5 | **Nghĩa lựa chọn sai** (phần trong ngoặc ở dòng tiêu đề, vd '⟪からだに⟫' ghi 'có lợi cho cơ thể' – chỉ là 'cho cơ thể'): sai rõ mới gắn cờ, dịch theo ngữ cảnh chấp nhận được thì không. | `nghia_tu` |
| 6 | **Nghĩa câu** (câu đề, câu hoàn chỉnh) lệch câu Nhật (3c). Nghĩa câu đề để trống đúng các ô → bình thường; nghĩa câu đề tự điền nội dung vào ô → cờ. | `nghia_cau` |
| 7 | **Cách đọc** câu đề / câu hoàn chỉnh sai (gợi ý **R1**; chữ nhiều âm đúng ngữ cảnh thì không). Cách đọc Python ghép (`doc_hoan_chinh_ghep`) → soát như cách đọc thường. | `cach_doc` |
| 8 | **Thiếu nội dung làm người học không hiểu**: không có câu hoàn chỉnh (`khong_cau_hoan_chinh`), chỉ có phần tham khảo (`chi_tham_khao`), lựa chọn không có phân tích. | `thieu_noi_dung` |
| 9 | **Nhiều câu hoàn chỉnh** (`nhieu_cau_hoan_chinh`): JSON dùng câu ghép khớp đề, câu kia nằm cuối `explanation` → gắn cờ để CTV quyết (quyết định 08/10/2026). | `khac` |

- Bắt buộc so: **câu hoàn chỉnh ↔ đề + thứ tự**, **ô ★ ↔ đáp án**, **'Khả năng sắp xếp' của từng lựa chọn ↔ câu hoàn chỉnh**, **giải thích ngữ pháp ↔ lựa chọn**, **nghĩa câu ↔ câu tiếng Nhật**.
- **Không gắn cờ:** lỗi diễn đạt chỉ "chưa hay"; phân tích đề chung chung nhưng không sai; cụm trong CÁCH SẮP XẾP viết liền không cách (`'せっかく書いた'`).

**3e. Gợi ý Python** (trong `xem_gd1.py` / `gd1_danh_sach_<tu>_<den>.json` (chạy song song; trước đó `gd1_danh_sach.json`) – chỉ là gợi ý, xác nhận rồi mới gắn cờ; bỏ qua gợi ý nào thì ghi `[Ghi chú] … không gắn cờ vì …`):
- **A** – kết quả ghép câu: `lech_nhe` / `lech_nang` (kèm chỗ lệch), `ô ★ … khác đáp án`.
- **SX** – 'Khả năng sắp xếp' mâu thuẫn rõ với câu hoàn chỉnh (độ chính xác cao, vẫn phải đọc lại).
- **R1** – cách đọc câu đề lệch từ điển.
- Cảnh báo **K11** (câu hoàn chỉnh lệch / ô ★ lệch) → 3d-1 / 3d-2.

**3b. Sau khi CTV tiếng Nhật trả kết quả** (chỉ khi người dùng đưa phản hồi): CTV xác nhận không sai → xóa cờ; sai → sửa theo CTV (`loai: sua_theo_ctv` + dòng `[Đã sửa theo CTV] …`), xóa cờ, chạy lại `s1_kiem_tra.py`.

**4. Âm Hán Việt** – Python tự dò; câu có âm Hán Việt không được dịch. Python dò sót → cờ nhóm `khac`.

## Checklist cấu trúc

- [ ] `question.ja` / `reading` / `meaning` = dòng câu đề / Cách đọc / Nghĩa của lời giải (không nhãn 'Đề bài:', giữ ô trống và ★).
- [ ] `sentence_analysis` = mỗi ý PHÂN TÍCH ĐỀ BÀI một phần tử, không còn `- `.
- [ ] Mỗi lựa chọn: `option_ja` = dòng `i.` của lời giải; `gloss` = nội dung ngoặc (cách đọc bọc ⟪ ⟫); `grammar`, `arrangement` đủ chữ.
- [ ] `arrangement.explanation` = các dòng cụm (+ câu chữ khác chép nguyên ở cuối); `full_sentence` = Câu hoàn chỉnh + Cách đọc (hoặc chuỗi Python ghép) + Nghĩa; `order` = thứ tự Python ghép.
- [ ] `correct.index` = `dap_an_so`; `correct.option_ja` = lựa chọn đó; `correct.full_sentence = null`.
- [ ] ⟪ ⟫ quanh mọi tiếng Nhật trong câu Việt; `{ }`, ★, furigana đúng như lời giải.
- [ ] Soát đủ 3c, 3d, 3e, K11.

## Mẫu lý do (một mẫu trong file đặc tả lô)

```json
"5994_1": {
  "thay": [{"duong_dan": "$.arrangement.full_sentence.reading", "cu": "かいた ★ てがみを", "moi": "かいた てがみを"}],
  "sua": [{"duong_dan": "$.arrangement.full_sentence.reading", "loai": "sua_dinh_dang", "nhom": "ky_tu", "muc_do": "nhe", "ly_do": "★ lẫn trong cách đọc câu hoàn chỉnh"}],
  "ghi_chu_ban_goc": ["[Đã sửa định dạng] Câu hoàn chỉnh – cách đọc: '…かいた ★ てがみを…' → '…かいた てがみを…' – ★ lẫn trong cách đọc"],
  "nghi_noi_dung": []
}
```
- `loai`: `sai_so_ban_goc` | `chinh_ta` | `khach_quan` | `chu_quan` | `sua_dinh_dang` (bắt buộc `nhom` + dòng `[Đã sửa định dạng]`) | `sua_theo_ctv`. `muc_do`: `nghiem_trong` | `nang` | `nhe`.
