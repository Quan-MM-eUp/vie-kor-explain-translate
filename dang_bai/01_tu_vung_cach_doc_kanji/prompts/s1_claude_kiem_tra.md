# Hướng dẫn Claude – Bước 1.2: kiểm tra JSON tiếng Việt và sửa lỗi (dạng 01)

> Model: **Claude Opus 5.5**, chạy trong Claude Cowork (không qua API). Nếu chia việc cho tác tử con thì tác tử con cũng dùng Opus 5.5.

**Nhiệm vụ:** kiểm tra JSON tiếng Việt do GPT tạo **so với lời giải gốc** và sửa lỗi. Chuẩn so sánh duy nhất là lời giải gốc đã chuẩn hóa. JSON phải thể hiện đúng và đủ lời giải gốc, không hơn, không kém.

## Làm gì

Danh sách câu: `output/claude/gd1_danh_sach.json` (tạo bằng `python scripts/s1_claude_goi.py …`). Mỗi mục có: cờ (`co`), ghi chú bản gốc tự động, **kết quả Python chạy thử trên bản GPT** (`python_tren_ban_gpt` – gợi ý chỗ nên xem, không phải kết luận), đường dẫn các file.

Với mỗi câu:

1. Đọc `output/samples/norm/<id>.json`: `de` (đề, 4 lựa chọn, đáp án), `dau_vao` (lời giải gốc đã chuẩn hóa), `co`.
2. Mở `output/json_vi/checked/<id>.json` (đã chép sẵn từ bản GPT) và **sửa trực tiếp** nếu có lỗi. Giữ đúng schema; file phải là JSON hợp lệ.
3. Ghi `output/json_vi/checked/<id>.ly_do.json` theo mẫu bên dưới – **xong thì xóa khóa `_huong_dan`** (còn khóa này thì Python coi như câu chưa được kiểm tra). Không có gì sửa thì để `"sua": []`.
4. Chỉ sửa file trong `output/json_vi/checked/`. Không sửa bản GPT, dữ liệu gốc hay file khác.
5. Làm xong cả danh sách thì chạy `python scripts/s1_kiem_tra.py …` (cùng phạm vi) và báo kết quả.

## Phạm vi sửa – CÁCH CHIA V2 (từ 2026-10-01, output_v2)

Ba việc tách bạch: **sửa lỗi GPT**, **sửa lỗi định dạng của bản gốc**, **gắn cờ nghi sai nội dung**. Claude **không sửa nội dung** của bản gốc.

**1. Sửa lỗi của GPT** – như cũ: `sai_so_ban_goc` (đặt sai trường, bỏ sót, tự thêm, viết lại, sai ký hiệu ⟪ ⟫/{ }/furigana, không tách thể từ điển…), `chinh_ta` (lỗi GPT tạo ra), `khach_quan`. Không làm câu đổi dạng.

**2. Sửa lỗi ĐỊNH DẠNG có sẵn trong bản gốc** – `loai: sua_dinh_dang` + `nhom`:

| nhom | Ví dụ |
|---|---|
| `dinh_chu` | dính câu / dính chữ: "phía sauMột số…" → "phía sau⏎Một số…"; "(きまった).Phân biệt" |
| `xuong_dong` | thiếu xuống dòng giữa các mục: "…từ bỏ".3. 物…" → "…từ bỏ".⏎3. 物…"; số mục chèn nhầm chỗ |
| `lap_tu` | "chữ chữ hán", "này này", "bệnh bệnh" |
| `chinh_ta` | lỗi chính tả / dấu tiếng Việt: "Cố gằng", "sân khẩu", "nh ấy" (mất chữ), viết hoa "người nhật" |
| `dau_cau` | dấu câu thừa/thiếu: ", )", ")" thừa, thiếu ngoặc kép đóng |
| `khoang_trang` | khoảng trắng thừa trong cách đọc câu, trong ví dụ tiếng Nhật |
| `gach_chan` | thiếu `{ }` ở cách đọc câu / nghĩa câu đúng chỗ từ đang hỏi (câu đề có) |
| `ky_tu` | sai ký tự rõ ràng: パーテイー → パーティー, ベ (katakana) trong chữ hiragana |
| `cach_doc_lan_so` | cách đọc câu lẫn số thứ tự ①②③ đọc thành chữ: `いち{はまべ}…`, `にかだん` |
| `khac` | lỗi định dạng khác (ghi rõ trong `ly_do`) |

- Mỗi chỗ sửa định dạng phải có **hai** ghi chép: mục trong `sua` (`duong_dan` ở mức trường nhỏ nhất, `loai`, `nhom`, `muc_do`, `ly_do`) **và** một dòng trong `ghi_chu_ban_goc`:
  `[Đã sửa định dạng] <chỗ sửa>: '<cũ>' → '<mới>' – <lỗi gì>` (ví dụ `[Đã sửa định dạng] Tham khảo: '…phía sauMột số…' → '…phía sau⏎Một số…' – dính câu, thiếu xuống dòng`).
- Chỉ sửa đúng chỗ sai, không đổi câu chữ khác. Python kiểm tra trung thành trên bản đã trả các chỗ này về như GPT, và cảnh báo khi thiếu ghi chú / thiếu nhom.
- Gợi ý của Python ở `python_tren_ban_gpt.canh_bao` (`[Nghi dính câu/định dạng] …`) chỉ là gợi ý – Claude xác nhận rồi mới sửa; không sửa "..", "…" (cách viết của bản gốc).

**3. Gắn cờ NGHI SAI NỘI DUNG – không sửa** (câu sẽ **không được dịch**, chuyển CTV tiếng Nhật xác nhận). Ghi vào khóa `nghi_noi_dung` của file lý do, **mỗi chỗ nghi một mục**, nói rõ nghi sai ở **phần nào**:

```json
"nghi_noi_dung": [
  {"vi_tri": "Nghĩa câu", "nhom": "thi_the", "mo_ta": "Câu Nhật 減っている (đang giảm) nhưng nghĩa câu dịch 'đã giảm bớt'",
   "de_xuat": "…mà số lượng tội phạm và các vụ việc đang giảm."}
]
```

- `vi_tri`: phần bị nghi – `Nghĩa từ`, `Cách đọc từ`, `Thể từ điển`, `Câu hỏi`, `Cách đọc câu`, `Nghĩa câu`, `Phân tích lựa chọn N (…)`, `Tham khảo` (nêu cả câu/mục nếu dài), `Đáp án`.
- `nhom`: `nghia_cau` (dịch sai/thiếu ý nghĩa câu) · `thi_the` (sai thì/thể: đã/đang/sẽ, bị động…) · `tu_tha_dong_tu` (nhầm tự động từ/tha động từ: 決まる/決める, 焦がす "làm cháy") · `nghia_tu` · `khong_ton_tai` (ghi "không tồn tại" cho từ có thật) · `dong_am` (nhầm từ đồng âm: 月賦 "ợ hơi") · `chu_han` (sai chữ Hán: 高層/高僧, 通勤/通報) · `cach_doc` (đọc sai không do lẫn số: ちょうむ, さいされた) · `dap_an` (lệch đáp án, 2 đáp án đúng) · `thieu_noi_dung` (thiếu phân tích/thiếu đoạn) · `khac`.
- `mo_ta`: vì sao nghi sai; `de_xuat`: cách sửa đề xuất (CTV xác nhận) – **không** sửa vào JSON.
- Bắt buộc so **nghĩa câu tiếng Việt với câu tiếng Nhật** (thì, thể, đủ ý) và **nghĩa từ/tham khảo với kiến thức** (tự/tha động từ, từ đồng âm, "không tồn tại").
- Không chắc lắm cũng gắn cờ (CTV sẽ quyết) – nhưng không gắn cờ cho cách diễn đạt chỉ "chưa hay".
- `[Bản gốc VI]` trong `ghi_chu_ban_goc` không còn dùng cho nghi vấn nội dung (dùng `nghi_noi_dung`).

**3b. Sau khi CTV tiếng Nhật trả kết quả cho câu bị cờ** (chỉ làm khi bạn đưa phản hồi CTV):
- CTV xác nhận **không sai** → xóa mục tương ứng trong `nghi_noi_dung`, không sửa JSON.
- CTV xác nhận **sai** → sửa JSON đúng theo CTV, ghi mục `sua` với `"loai": "sua_theo_ctv"` + `nhom` (nhóm của nghi_noi_dung) và dòng ghi chú `[Đã sửa theo CTV] <chỗ>: '<cũ>' → '<mới>' – <CTV nói gì>`; xóa mục cờ đã xử lý.
- Chạy lại `s1_kiem_tra.py` → câu hết cờ thành GĐ1_XONG, được chốt và dịch. `sua_theo_ctv` không làm câu thành Dạng 2.

**4. Âm Hán Việt** – Python tự dò (`[Âm Hán Việt] …` trong gợi ý). Claude không sửa, không cần gắn cờ; câu có âm Hán Việt tự động **không được dịch**.

**Dạng của câu:** có ít nhất một `sua_dinh_dang` → **Dạng 2**; không → **Dạng 1**. Chỉ câu **không có** `nghi_noi_dung` **và không có** âm Hán Việt mới được chốt (s1_chot) và dịch.

## Checklist

- [ ] Nội dung đặt đúng trường; không thiếu ý, thừa ý, không bị viết lại so với bản gốc; đã bỏ các nhãn cố định.
- [ ] **Mỗi phân tích nằm đúng lựa chọn của nó.** Câu có cờ `nghi_don_phan_tich`: phần bị dồn đã tách hết về đúng lựa chọn chưa, có tách nhầm không.
- [ ] `options` đủ 4, `option_ja` đúng đề; `correct.index` = `dap_an_so`; lựa chọn đúng: có phân tích trong bản gốc thì phải chép, không có thì `null`.
- [ ] `{ }` bọc đúng từ đang hỏi ở `question.ja`, cách đọc tương ứng ở `question.reading`, phần nghĩa tương ứng ở `question.meaning.vi` – chỉ ở chỗ bản gốc có gạch chân.
- [ ] `word.ja`, `word.reading` đúng như bản gốc; thể từ điển tách đúng (kể cả trường hợp viết dính vào cách đọc).
- [ ] `question.reading` chép từ bản gốc; bản gốc không có dòng cách đọc (dạng ###) thì `null`, không tự ghép từ furigana.
- [ ] Mọi tiếng Nhật trong câu tiếng Việt được bọc `⟪ ⟫`; không bọc chữ tiếng Việt.
- [ ] Furigana `｜…《…》`: chỗ bản gốc có thì JSON có đúng như vậy; chỗ bản gốc không có thì JSON không có.
- [ ] Lựa chọn thiếu phân tích trong bản gốc → `null` + ghi `[Bản gốc VI] Thiếu phân tích lựa chọn X` (nếu chưa có trong ghi chú tự động).
- [ ] Cách đọc bị lẫn số ①②③ (vd `いちはまべ`, `にかいさい`) → sửa, `loai: sua_dinh_dang, nhom: cach_doc_lan_so` + dòng `[Đã sửa định dạng]`. Đọc sai âm thật (không do lẫn số) → **không sửa**, gắn cờ `nghi_noi_dung` nhóm `cach_doc`.
- [ ] Lỗi trình bày (dính câu/dính mục, thiếu xuống dòng, lặp từ, chính tả, dấu câu, khoảng trắng) → sửa (`sua_dinh_dang`, `nhom` tương ứng) + dòng `[Đã sửa định dạng]`. Lỗi kiến thức → **không sửa**, gắn cờ `nghi_noi_dung`.
- [ ] Nghĩa câu tiếng Việt so với câu tiếng Nhật (thì, thể, đủ ý); nghĩa từ / tham khảo (tự–tha động từ, đồng âm, "không tồn tại") → nghi sai thì gắn cờ `nghi_noi_dung`, ghi rõ `vi_tri`, kể cả khi không chắc.

## Mẫu file lý do (cách chia v2)

```json
{
  "sua": [
    {"duong_dan": "$.options[3].analysis", "loai": "sai_so_ban_goc", "muc_do": "nang",
     "ly_do": "GPT chưa tách phân tích lựa chọn 4 khỏi ô lựa chọn 2"},
    {"duong_dan": "$.reference.vi", "loai": "sua_dinh_dang", "nhom": "dinh_chu", "muc_do": "nhe",
     "ly_do": "Dính câu 'phía sauMột số…', thiếu xuống dòng"}
  ],
  "ghi_chu_ban_goc": ["[Đã sửa định dạng] Tham khảo: '…phía sauMột số…' → '…phía sau⏎Một số…' – dính câu, thiếu xuống dòng"],
  "nghi_noi_dung": [
    {"vi_tri": "Tham khảo – dòng '+ 決まる'", "nhom": "tu_tha_dong_tu",
     "mo_ta": "決まる là tự động từ ('được quyết định'), bản gốc giải nghĩa 'Quyết định, được quyết định' giống 決める",
     "de_xuat": "+ 決まる (きまる): được quyết định"}
  ]
}
```

- `loai`: `sai_so_ban_goc` | `chinh_ta` | `khach_quan` (lỗi GPT) | `sua_dinh_dang` (lỗi định dạng bản gốc – bắt buộc `nhom` + dòng `[Đã sửa định dạng]`). `muc_do`: `nghiem_trong` | `nang` | `nhe`. Không dùng `sua_ban_goc` nữa (Python cảnh báo).
- Không có gì thì để `"sua": []`, `"nghi_noi_dung": []`. Xong thì xóa khóa `_huong_dan`.
