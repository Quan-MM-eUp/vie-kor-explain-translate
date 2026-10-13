# Hướng dẫn tác tử KIỂM TRA – Bước 1.2: soát JSON tiếng Việt (dạng 20 – Nghe hiểu: Trả lời nhanh) · v1

> Phiên bản `s1_claude_kiem_tra.20.v1` (2026-10-08): khung **cách chia v2** (sửa định dạng / gắn cờ nội dung) của dạng 07/08 + **quy tắc riêng dạng 20 (mục 3d)** + **gợi ý Python (mục 3e)**.
> Model: **Claude Opus 5.5** trong Cowork. Bản cần soát do **tác tử TẠO (Claude A, ngữ cảnh riêng)** tạo – bạn không tạo lại bản, chỉ soát và sửa.
> Dạng 20 không có phần THAM KHẢO (`reference_raw` luôn null – không sửa).

**Nhiệm vụ:** so JSON với **lời giải gốc** (`output/samples/norm/<id>.json` → `dau_vao`) và **script nghe**: JSON phải thể hiện đúng và đủ lời giải, không hơn, không kém; đồng thời phát hiện chỗ lời giải gốc **sai nội dung** để gắn cờ.

## Làm gì

1. Xem từng câu bằng `python3 ../../pipeline_chung/cong_cu/xem_gd1.py <id> …` (đề + **script nghe đã tách** + lời giải gốc + gợi ý Python + JSON phẳng).
2. Sửa lỗi của tác tử TẠO / lỗi định dạng (mục 1–2) và gắn cờ nội dung (mục 3) – ghi tất cả vào **một file đặc tả lô** rồi chạy `ghi_ly_do.py` (xem `SO_TAY_CHAY.md` mục 4.3). Sửa cấu trúc (bool `is_correct`, mảng `prompt.analysis`) thì sửa thẳng `output/json_vi/checked/<id>.json` bằng python read-modify-write và ghi lý do vào `sua`.
3. Chạy `python3 scripts/s1_kiem_tra.py --tu X --den Y`, xử lý lỗi K.

## Phạm vi sửa – cách chia v2

Ba việc tách bạch: **sửa lỗi tác tử TẠO**, **sửa lỗi ĐỊNH DẠNG của bản gốc**, **gắn cờ NGHI SAI NỘI DUNG**. Không sửa nội dung của bản gốc.

**1. Sửa lỗi tác tử TẠO** – `loai`: `sai_so_ban_goc` (đặt sai trường, bỏ sót, tự thêm, viết lại, chép nhãn người nói, chép phần dịch trùng lặp trước ###, thiếu / thừa ⟪ ⟫, mất `{ }` / furigana, `is_correct` khác dòng ĐÚNG/SAI, còn `→ ĐÚNG/SAI` trong `analysis`), `chinh_ta` (lỗi do tác tử TẠO), `khach_quan`.

**2. Sửa lỗi ĐỊNH DẠNG có sẵn trong bản gốc** – `loai: sua_dinh_dang` + `nhom` (`dinh_chu`, `xuong_dong`, `lap_tu`, `chinh_ta`, `dau_cau`, `khoang_trang`, `ky_tu`, `furigana`, `khac`). Dạng 20 hay gặp:

| Trường hợp | Cách xử lý |
|---|---|
| Dấu `。` (Nhật) cuối câu tiếng Việt (`… giúp tôi。`) | đổi thành `.` – `nhom: dau_cau` |
| Ruby hỏng (cách đọc lặp ngay sau chữ Hán: `大学大学`, `一番いちばん`) ở câu Nhật / trong ⟪ ⟫ | bỏ phần lặp – `nhom: furigana` |
| Nhãn người nói còn sót giữa câu dịch, dính dòng (`…nhé.Nữ:`) | bỏ / xuống dòng – `nhom: dinh_chu` |
| Câu Nhật trong lời giải lệch script **chỉ do gõ** (`どもう` ↔ `どうも`, thiếu `。`) – cảnh báo K-SC | sửa `sentence.ja` theo script – `nhom: ky_tu`; **kana ↔ kanji cùng cách đọc → KHÔNG sửa** (chỉ `[Ghi chú]` nếu cần) |

- Mỗi chỗ sửa định dạng có **hai** ghi chép: mục trong `sua` (`duong_dan` mức trường nhỏ nhất, `loai`, `nhom`, `muc_do`, `ly_do`) **và** một dòng `[Đã sửa định dạng] <chỗ>: '<cũ>' → '<mới>' – <lỗi gì>` (một dòng, xuống dòng ghi `⏎`). Không có thay đổi JSON → dùng `[Ghi chú] …`.
- Câu tiếng Nhật (`sentence.ja`, `correct.option_ja`) Python so với lời giải (K8): sửa mà không có mục `sua` đúng đường dẫn → LỖI. `prompt.utterance.ja` do Python điền từ script – **không sửa** (K-UT).
- Một trường – một loại sửa.

**3. Gắn cờ NGHI SAI NỘI DUNG – không sửa** (câu không được dịch, chuyển CTV tiếng Nhật). Khóa `nghi_noi_dung`, mỗi chỗ một mục:

```json
{"vi_tri": "Phân tích lựa chọn 3", "nhom": "ly_do_loai",
 "mo_ta": "(quy tắc 3d-1) Nói 'そうだね' là đồng ý nên không hợp – nhưng câu nói là lời than phiền, đồng tình là phản hồi tự nhiên; lý do loại thật là phần sau '35分待っていたら' trái tình huống.",
 "de_xuat": "Lựa chọn này không hợp vì người nói lo không kịp tàu, không phải định đợi 35 phút."}
```

- `vi_tri`: `Câu nói – nghĩa`, `Lựa chọn N – câu Nhật`, `Lựa chọn N – nghĩa`, `Phân tích lựa chọn N`, `Đúng/Sai lựa chọn N`, `Đáp án`, `Lời giải`.
- `nhom`: `ly_do_loai` · `sac_thai` · `nghia_cau` · `cau_khac_de` · `dap_an` · `thieu_noi_dung` · `khac`.

**3c. Quy tắc chung (phản hồi CTV)** – nghĩa câu tiếng Việt lệch câu Nhật (thêm / bớt ý, mất phủ định / bị động / sai khiến / thì, sai người cho – người nhận) → `nghia_cau`.

**3d. Quy tắc riêng dạng 20 – Trả lời nhanh (duyệt 08/10/2026)**

| # | Lỗi cần bắt | `nhom` |
|---|---|---|
| 1 | **Lý do chọn / loại sai**: phân tích hiểu sai **chức năng** câu nói (lời mời, nhờ vả, khen, trách, xin phép, than phiền, chào hỏi…) hoặc lập luận vì sao câu trả lời hợp / không hợp là sai, tự mâu thuẫn, trái với chính câu Nhật của lựa chọn. | `ly_do_loai` |
| 2 | **Đánh giá sai sắc thái / mức lịch sự**: nói kính ngữ / khiêm nhường sai (vd gọi 申す là tôn kính ngữ), nhận định ため口 ↔ lịch sự sai, hiểu sai quan hệ trên – dưới, bỏ qua mỉa mai / nói giảm (vd 結構です = từ chối). | `sac_thai` |
| 3 | **Nghĩa câu sai**: dịch câu nói / câu trả lời lệch câu Nhật (3c). **Bản dịch còn chen chữ Nhật** (cờ `chen_tu_nhat_dich`, cảnh báo K-NJ – vd `Nữ: 店 này …`) → luôn gắn cờ (quyết định 08/10/2026), `de_xuat` ghi nghĩa Việt. | `nghia_cau` |
| 4 | **Câu Nhật của lựa chọn khác script về nội dung** (K-SC: khác từ / khác nghĩa, không phải kana ↔ kanji hay lỗi gõ). | `cau_khac_de` |
| 5 | **Đáp án đáng ngờ**: lời giải chấm ĐÚNG khác `dap_an_so` (`lech_dap_an`), nhiều / không có lựa chọn ĐÚNG (`nhieu_dung`), hoặc thấy rõ một câu trả lời khác cũng hợp lý ngang đáp án. | `dap_an` |
| 6 | **Thiếu nội dung**: khuôn C (`khuon_C` – chỉ có bản dịch, không phân tích), khuôn B thiếu dịch câu nói (`khong_dich_cau_noi`), lựa chọn không có phân tích / thiếu câu Nhật (`thieu_phan_tich`, `thieu_cau_nhat`). **Khuôn C luôn gắn cờ** (quyết định 08/10/2026). | `thieu_noi_dung` |
| 7 | Dữ liệu đề lỗi (`du_lieu_loi`: thiếu cột lựa chọn, đáp án ngoài số lựa chọn), script không tách được mà lời giải không có câu Nhật. | `khac` |

- Bắt buộc so: **chức năng câu nói ↔ đáp án ↔ phân tích từng lựa chọn**, **nghĩa câu nói / câu trả lời ↔ câu Nhật**, **câu Nhật lựa chọn ↔ script**.
- **Không gắn cờ:** phân tích ngắn (1 câu) nhưng đúng; dịch khẩu ngữ hơi vụng nhưng đúng ý; lệch kana / kanji giữa lời giải và script; nhãn người nói khác script (Nam ↔ M); `lua_chon_thua` (cột lua_chon_4 thừa – chỉ báo cáo dữ liệu gốc); câu ví dụ `script_vi_du` (れい) – ghi `[Ghi chú]`.

**3e. Gợi ý Python** (trong `xem_gd1.py` / `gd1_danh_sach.json` – chỉ là gợi ý, xác nhận rồi mới gắn cờ; bỏ qua gợi ý nào thì ghi `[Ghi chú] … không gắn cờ vì …`):
- **K-SC** – câu Nhật lựa chọn lệch script (kèm chỗ lệch) → 3d-4 / sửa định dạng.
- **K-NJ** – bản dịch chen chữ Nhật → 3d-3.
- **K-TL** – bản dịch lựa chọn trước ### khác dòng `Nghĩa:` (JSON theo `Nghĩa:`; khác **nghĩa** thì xem dòng `Nghĩa:` có sai không).
- Cờ s0 `khuon_C`, `khuon_D`, `lech_dap_an`, `nhieu_dung`, `script_khong_tach`.

**3b. Sau khi CTV tiếng Nhật trả kết quả** (chỉ khi người dùng đưa phản hồi): CTV xác nhận không sai → xóa cờ; sai → sửa theo CTV (`loai: sua_theo_ctv` + dòng `[Đã sửa theo CTV] …`), xóa cờ, chạy lại `s1_kiem_tra.py`.

**4. Âm Hán Việt** – Python tự dò; câu có âm Hán Việt không được dịch. Python dò sót → cờ nhóm `khac`.

## Checklist cấu trúc

- [ ] `prompt.utterance.ja` = câu nói Python tách từ script (không sửa); `reading = null`; `meaning` = dòng dịch câu nói **không có nhãn người nói**.
- [ ] `prompt.situation = null`; `prompt.analysis = []` (trừ câu chữ thừa sau phần dịch / trước lựa chọn 1).
- [ ] Mỗi lựa chọn: `sentence.ja` = câu Nhật của lời giải (khuôn C: của script); `reading = null`; `meaning` = dòng `Nghĩa:` (không lấy phần dịch trùng lặp trước ###); `is_correct` = dòng ĐÚNG/SAI; `analysis` đủ chữ, không còn `→ ĐÚNG/SAI`.
- [ ] `correct.index` = `dap_an_so`; `correct.option_ja` = `sentence.ja` lựa chọn đó; `correct.full_sentence = null`.
- [ ] ⟪ ⟫ quanh mọi tiếng Nhật trong câu Việt; `{ }`, furigana đúng như lời giải.
- [ ] Soát đủ 3c, 3d, 3e.

## Mẫu lý do (một mẫu trong file đặc tả lô)

```json
"22764_1": {
  "thay": [],
  "sua": [],
  "ghi_chu_ban_goc": [],
  "nghi_noi_dung": [{"vi_tri": "Câu nói – nghĩa", "nhom": "nghia_cau",
                     "mo_ta": "(quy tắc 3d-3) Bản dịch còn chen chữ Nhật: 'chuyến ⟪｜電《でん》｜車《しゃ》⟫'; Nghĩa lựa chọn 2 còn '⟪｜出《しゅっ》｜発《ぱつ》⟫'.",
                     "de_xuat": "Có thể tôi sẽ không kịp lên chuyến tàu xuất phát lúc 35 phút. / Đúng vậy. Giờ xuất phát muộn thật."}]
}
```
- `loai`: `sai_so_ban_goc` | `chinh_ta` | `khach_quan` | `chu_quan` | `sua_dinh_dang` (bắt buộc `nhom` + dòng `[Đã sửa định dạng]`) | `sua_theo_ctv`. `muc_do`: `nghiem_trong` | `nang` | `nhe`.
