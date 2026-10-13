# Hướng dẫn tác tử KIỂM TRA – Bước 1.2: kiểm tra JSON tiếng Việt và sửa lỗi (dạng 19 – Nghe hiểu diễn đạt) · v1

> Phiên bản `s1_claude_kiem_tra.19.v1` (2026-10-08): khung **cách chia v2** của dạng 07/09 + quy tắc riêng dạng 19 (mục 3d) theo `KE_HOACH_PIPELINE.md` (duyệt 08/10/2026).
> Model: **Claude Opus 5.5**, chạy trong Claude Cowork. Bản cần kiểm tra do **tác tử TẠO (Claude A, ngữ cảnh riêng)** tạo – mọi chỗ "bản GPT" / "lỗi GPT" (tên trường cũ trong file như `python_tren_ban_gpt`, loại `sai_so_ban_goc`) hiểu là bản / lỗi của tác tử TẠO. Bạn (tác tử KIỂM TRA) không tạo lại bản, chỉ soát và sửa.

**Nhiệm vụ:** kiểm tra JSON tiếng Việt **so với lời giải gốc** và sửa lỗi. JSON phải thể hiện đúng và đủ lời giải gốc, không hơn, không kém. Đồng thời soát **nội dung** lời giải (cách diễn đạt có đúng tình huống không) để **gắn cờ** – không sửa nội dung.

> **Quy tắc THAM KHẢO (2026-10-07):** dạng 19 không có phần tham khảo – `reference_raw` luôn `null` do Python điền; không sửa trường này (Python báo `K-TK`).

## Làm gì

Xem từng câu: `python3 ../../pipeline_chung/cong_cu/xem_gd1.py <id>`. Công cụ in: cờ + **ĐỀ** (câu tình huống Python tách, 3 câu nói theo transcript, đáp án) → phần **"ĐOẠN VĂN"** = **transcript tiếng Nhật** (kèm link ảnh nếu có – dạng 19 dùng chỗ này cho transcript) → **LỜI GIẢI GỐC** → gợi ý Python → JSON phẳng. Danh sách câu: `output/claude/gd1_danh_sach.json` (tạo bằng `python3 scripts/s1_claude_goi.py …`).

Với mỗi câu:

1. Đọc đề + transcript + lời giải gốc (`dau_vao` – `{ }` là chỗ in đậm / gạch chân của bản gốc).
2. Mở `output/json_vi/checked/<id>.json` và **sửa trực tiếp** nếu có lỗi (lỗi tác tử TẠO / lỗi định dạng bản gốc). Giữ đúng schema `listening_response.v1`.
3. Ghi kết quả bằng **file đặc tả lô + `ghi_ly_do.py`** (xem `SO_TAY_CHAY.md` mục 4.3) – tương đương ghi `<id>.ly_do.json` và xóa khóa `_huong_dan`.
4. Chỉ sửa file trong `output/json_vi/checked/`. Không sửa `prompt.utterance.ja` (Python điền – K-TH).

## Phạm vi sửa – cách chia v2

Ba việc tách bạch: **sửa lỗi tác tử TẠO**, **sửa lỗi ĐỊNH DẠNG của bản gốc**, **gắn cờ NGHI SAI NỘI DUNG**. Claude **không sửa nội dung** bản gốc.

**1. Sửa lỗi tác tử TẠO:** `sai_so_ban_goc` (đặt sai trường; chép 3 dòng nghĩa phần đầu vào JSON; bỏ sót / tự thêm / viết lại chữ; sót `→ ĐÚNG.` trong analysis; `is_correct` khác kết luận của lời giải; `sentence.ja` theo transcript thay vì lời giải; thiếu ⟪ ⟫ / sai `{ }` / mất furigana; `correct.option_ja` khác `sentence.ja` đáp án…), `chinh_ta`, `khach_quan`.

**2. Sửa lỗi ĐỊNH DẠNG có sẵn trong bản gốc** – `loai: sua_dinh_dang` + `nhom` (`dinh_chu`, `xuong_dong`, `lap_tu`, `chinh_ta`, `dau_cau`, `khoang_trang`, `ky_tu`, `furigana`, `khac`):
- Câu nói tiếng Nhật trong lời giải **lệch transcript 1–2 ký tự** (cờ `lc_lech_transcript_nhe`, cảnh báo `K-LC`): xác định **bên nào sai**.
  - **Lời giải sai** (gõ nhầm, **furigana lệch phạm vi** như `お｜願い《ねが》い` → `お｜願《ねが》い`, furigana của từ đọc liền (jukujikun) bị tách sai như `｜今《きょう》｜日《は》` → `｜今日《きょう》`): `sua_dinh_dang` (`nhom: furigana` / `ky_tu`) ở `sentence.ja` **và** `correct.option_ja` nếu là đáp án (Python so furigana trên bản đã hoàn tác chỗ sửa – nhớ ghi mục `sua` cho cả hai đường dẫn).
  - **Transcript sai** (vd 21473 `いきたいいんですが`, 21400 `くだざい` trong transcript): **không sửa JSON**; ghi `[Ghi chú] Transcript gõ sai: '<transcript>' – lời giải đúng '<lời giải>'` và liệt kê trong báo cáo lô để nhóm dữ liệu sửa transcript. Câu tình huống (`utterance.ja`, lấy từ transcript) có lỗi gõ → cũng chỉ `[Ghi chú]` như vậy, không sửa, không gắn cờ.
  - Khác kana ↔ kanji cùng cách đọc (おおきく ↔ 大きく), dấu câu, khoảng trắng → **không phải lỗi**: không sửa, không cờ.
- Ruby hỏng (cách đọc lặp ngay sau chữ Hán: `少すこし`), dính câu, lặp từ, dấu câu, chính tả tiếng Việt rõ ràng.
- Furigana đọc Hán Việt trong câu Việt (cờ `ruby_han_viet`) đã được **Python** đổi thành chữ Việt (ghi chú `[Python sửa định dạng]`) – chỉ cần xem lại đúng chưa.
- Mỗi chỗ sửa định dạng có **hai** ghi chép: mục trong `sua` (`duong_dan` ở mức trường nhỏ nhất, `loai`, `nhom`, `muc_do`, `ly_do`) **và** một dòng `[Đã sửa định dạng] <chỗ sửa>: '<cũ>' → '<mới>' – <lỗi gì>` (một dòng, xuống dòng ghi `⏎`). Ghi chú không kèm thay đổi JSON → `[Ghi chú] …`.
- **Một trường – một loại sửa** (như dạng 07): trùng thì ưu tiên sửa lỗi tác tử TẠO, lỗi định dạng ghi vào cờ / ghi chú.

**3. Gắn cờ NGHI SAI NỘI DUNG – không sửa** (câu **không được dịch**, chuyển CTV tiếng Nhật) – khóa `nghi_noi_dung`, mỗi chỗ một mục `{vi_tri, nhom, mo_ta, de_xuat}`:
- `vi_tri`: `Câu tình huống`, `Câu tình huống – nghĩa`, `Lựa chọn N – câu nói`, `Lựa chọn N – nghĩa`, `Lựa chọn N – kết luận`, `Lựa chọn N – phân tích`, `Lựa chọn đúng`.
- `nhom` (dùng nhóm có sẵn – không thêm nhóm mới): `ly_do_loai` · `y_nghia_cau_truc` · `nghia_cau` · `cau_khac_de` · `dap_an` · `thieu_noi_dung` · `cach_doc` · `khac`.
- Không chắc lắm cũng gắn cờ (CTV quyết) – nhưng không gắn cờ cho cách diễn đạt chỉ "chưa hay".

**3d. Quy tắc riêng dạng 19 (bắt buộc soát – duyệt 08/10/2026)**

| # | Gắn cờ khi | `nhom` |
|---|---|---|
| 1 | **Lý do chọn / loại sai về CÁCH DIỄN ĐẠT**: kính ngữ / khiêm nhường ngữ dùng sai đối tượng (お持ちします là khiêm nhường của người nói, không phải tôn kính); **あげる / くれる / もらう** – ai làm cho ai; **～ましょうか (đề nghị mình làm) / ～ませんか (mời, rủ) / ～てもいいですか (xin phép mình làm) / ～てくれませんか, ～ていただけませんか (nhờ người khác làm)**; lời chào theo tình huống (trước / sau khi ăn, đi / về, gặp lần đầu / lâu ngày, người trên / bạn bè); lý do không liên quan tình huống, tự mâu thuẫn, hoặc chỉ nói "không phù hợp" mà không nêu vì sao **khi** lý do đó sai | `ly_do_loai` |
| 2 | Giải thích **mẫu câu / sắc thái** sai kiến thức (nghĩa mẫu sai, mức lịch sự sai, nói dạng có thật là không tồn tại) | `y_nghia_cau_truc` |
| 3 | **Nghĩa** (dịch tình huống hoặc dòng `Nghĩa:` của câu nói) lệch câu Nhật: sai chủ thể (ai nói với ai, ai làm cho ai), mất phủ định / bị động / sai khiến / xin phép, thêm bớt ý. Câu nói SAI được dịch sát chữ, gượng → chủ ý, **không** gắn cờ. Dịch lời chào bằng câu tương đương tự nhiên (いただきます → 'Mời mọi người dùng bữa') → không gắn cờ | `nghia_cau` |
| 4 | **Câu nói trong lời giải khác transcript về chữ** (mất / thêm / khác từ – cờ `lc_lech_transcript_nang`, cảnh báo `K-LC … khác chữ`); kana ↔ kanji, dấu câu, khoảng trắng **không** tính; lệch 1–2 ký tự do gõ → sửa định dạng (mục 2) | `cau_khac_de` |
| 5 | **Đáp án đáng ngờ**: lời giải kết luận ĐÚNG ở lựa chọn khác đáp án / 0 hoặc ≥ 2 chỗ ĐÚNG (cờ `ket_luan_lech_dap_an`, cảnh báo `K11`); hoặc theo tình huống, đáp án của đề rõ ràng không hợp lý (vd 25373: bạn không có bút chì mà đáp án là 'えんぴつ、使いますか') – ghi lý do | `dap_an` |
| 6 | **Thiếu nội dung**: khuôn B (không dịch tình huống), khuôn D (không có kết luận + phân tích), không có câu tình huống tiếng Nhật (cờ `khong_co_tinh_huong_ja`, `utterance.ja = ""`), khối thiếu phân tích (`thieu_phan_tich`) – cảnh báo `K-ND` | `thieu_noi_dung` |
| 7 | Câu tình huống Python tách từ transcript **sai** (lẫn câu nói, mất một phần, tách nhầm – nhất là câu có cờ `tinh_huong_khong_nanto`, `tr_ghi_chu`, `tinh_huong_tu_doan_van`) → **không sửa** `utterance.ja`; gắn cờ `khac` mô tả đúng câu tình huống, báo người dùng để sửa `scripts/_dang.py` | `khac` |

- **Không gắn cờ:** phân tích ngắn nhưng đúng; câu Nhật khác transcript chỉ ở kana / kanji / dấu câu (ghi `[Ghi chú] …` nếu cần); transcript có dòng thừa không ảnh hưởng nội dung.
- Bắt buộc so: **kết luận ĐÚNG/SAI ↔ đáp án**, **lý do ↔ tình huống** (ai nói, với ai, mục đích gì), **nghĩa ↔ câu Nhật**, **câu Nhật lời giải ↔ transcript**.
- `is_correct` là điều lời giải NÓI. Tác tử TẠO điền khác lời giải → sửa (`sai_so_ban_goc`). Lời giải nói sai → giữ và gắn cờ (3d-5).
- **Âm Hán Việt** (lời giải ghi âm Hán Việt như cách đọc) – Python tự dò (`[Âm Hán Việt] …`); câu có âm Hán Việt tự động không được dịch; Python dò sót thì gắn cờ `khac`.

**3b. Sau khi CTV tiếng Nhật trả kết quả** (chỉ khi người dùng đưa phản hồi CTV): CTV xác nhận không sai → xóa mục cờ; CTV xác nhận sai → sửa JSON theo CTV, mục `sua` `"loai": "sua_theo_ctv"` + `nhom` + dòng `[Đã sửa theo CTV] <chỗ>: '<cũ>' → '<mới>' – <CTV nói gì>`; xóa mục cờ; chạy lại `s1_kiem_tra.py`.

**Dạng của câu:** có ít nhất một `sua_dinh_dang` → **Dạng 2**; không → **Dạng 1**. Chỉ câu **không có** `nghi_noi_dung` và không có âm Hán Việt mới được chốt và dịch.

## Checklist cấu trúc

- [ ] `prompt.utterance.ja` = câu tình huống Python (không sửa); `reading` = null; `meaning` = (các) dòng dịch tình huống (khuôn B: null); `situation` = null; `analysis` = [].
- [ ] Không có 3 dòng nghĩa phần đầu trong JSON.
- [ ] Mỗi lựa chọn: `sentence.ja` = dòng `i.` của lời giải (khuôn D: transcript), furigana đúng; `reading` = null; `meaning` = dòng `Nghĩa:`; `is_correct` = kết luận lời giải (khuôn D: theo đáp án); `analysis` = phần còn lại (không còn `→ ĐÚNG/SAI`), khuôn D: null.
- [ ] `correct.index` = `dap_an_so`; `correct.option_ja` giống hệt `sentence.ja` đáp án; `full_sentence` = null.
- [ ] `{ }` đúng; mọi tiếng Nhật trong câu Việt bọc `⟪ ⟫` (ngoặc 「」 / '' ở ngoài).
- [ ] Soát đủ **3d-1…7**, mọi cảnh báo `K-LC`, `K-ND`, `K11`, gợi ý `[Từ điển Sudachi] LC: …`.

## Mẫu ghi một câu trong file đặc tả lô

```json
"12268_1": {"thay": [{"duong_dan": "$.options[0].sentence.ja", "cu": "おおきくして", "moi": "大きくして"}],
            "sua": [{"duong_dan": "$.options[0].sentence.ja", "loai": "sua_dinh_dang", "nhom": "ky_tu", "muc_do": "nhe", "ly_do": "ví dụ minh họa cách ghi"}],
            "ghi_chu_ban_goc": ["[Đã sửa định dạng] Lựa chọn 1 – câu nói: 'おおきくして' → '大きくして' – (ví dụ minh họa cách ghi)"],
            "nghi_noi_dung": [{"vi_tri": "Lựa chọn 2 – phân tích", "nhom": "ly_do_loai",
                               "mo_ta": "(3d-1) …", "de_xuat": "…"}]}
```
(Ví dụ chỉ minh họa cách ghi – kana ↔ kanji cùng cách đọc thực tế **không** sửa.)
- `loai`: `sai_so_ban_goc` | `chinh_ta` | `khach_quan` (lỗi tác tử TẠO) | `sua_dinh_dang` (bắt buộc `nhom` + dòng `[Đã sửa định dạng]`) | `sua_theo_ctv`. `muc_do`: `nghiem_trong` | `nang` | `nhe`. Không dùng `sua_ban_goc`.
