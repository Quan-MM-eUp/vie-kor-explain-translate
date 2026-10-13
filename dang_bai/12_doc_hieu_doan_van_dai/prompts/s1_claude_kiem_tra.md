# Hướng dẫn tác tử KIỂM TRA – Bước 1.2: kiểm tra JSON tiếng Việt và sửa lỗi (dạng 12 – Đọc hiểu: Đoạn văn dài) · v1

> Phiên bản `s1_claude_kiem_tra.12.v1` (2026-10-08). Model: **Claude Opus 5.5**, chạy trong Claude Cowork (không qua API).
> Bản cần kiểm tra do **tác tử TẠO (Claude A, ngữ cảnh riêng)** tạo – mọi chỗ "bản GPT" trong công cụ / nhật ký (`python_tren_ban_gpt`, "GPT sai…") hiểu là bản của tác tử TẠO. Bạn (tác tử KIỂM TRA) không tạo lại bản, chỉ soát và sửa.

**Nhiệm vụ:** kiểm tra JSON tiếng Việt **so với lời giải gốc** (chuẩn so sánh = lời giải gốc đã chuẩn hóa `dau_vao`) và **so lời giải với đoạn văn** để phát hiện lỗi nội dung. JSON phải thể hiện đúng và đủ lời giải gốc, không hơn, không kém; lỗi nội dung của lời giải chỉ **gắn cờ**, không sửa.

> **Quy tắc THAM KHẢO (2026-10-07):** dạng 12 không có phần tham khảo – `reference_raw` luôn `null` (Python điền, không sửa).

## Làm gì

Xem từng câu: `python3 ../../pipeline_chung/cong_cu/xem_gd1.py <id> <id> …` (đề + **đoạn văn** (in một lần cho mỗi đoạn) + lời giải gốc + gợi ý Python + JSON dạng phẳng). Danh sách: `output/claude/gd1_danh_sach.json` (tạo bằng `python3 scripts/s1_claude_goi.py …`) – mỗi mục có cờ (`co`), ghi chú bản gốc tự động, **kết quả Python chạy thử trên bản tạo** (`python_tren_ban_gpt`: lỗi K…, cảnh báo `K-TD`, `[Trích dẫn ↔ đoạn văn] TD: …`, `[Âm Hán Việt] …`, `[Nghi dính câu/định dạng] …`).

Với mỗi câu:

1. Đọc `output/samples/norm/<id>.json`: `de` (câu hỏi, 4 lựa chọn, đáp án), `doan_van`, `khuon_goc`, `dau_vao`, `co`, `phan.trich_doan_van` (kết quả so từng câu trích với đoạn văn).
2. Soát `output/json_vi/checked/<id>.json` (đã chép sẵn từ bản tạo). Sửa lỗi của tác tử TẠO / lỗi định dạng (mục 1–2) bằng khóa `thay` của file đặc tả lô hoặc python read-modify-write.
3. **Đọc đoạn văn** và soát nội dung (mục 3) – đây là phần quan trọng nhất của dạng 12.
4. Ghi kết quả cả lô bằng **một** file đặc tả `output/claude/ly_do_lo/gd1_X_Y.json` → `python3 ../../pipeline_chung/cong_cu/ghi_ly_do.py <file>` (mẫu cuối file). Liệt kê **mọi** mẫu của lô.
5. Chạy `python3 scripts/s1_kiem_tra.py --tu X --den Y` và báo kết quả.

## 1. Sửa lỗi của tác tử TẠO (`sai_so_ban_goc` / `chinh_ta` / `khach_quan`)

- Đặt sai trường: câu trích để trong `analysis` (hoặc ngược lại – câu giải thích bắt đầu bằng 「từ」 bị đưa vào `quotes`); dịch câu trích để trong `analysis` thay vì `quotes[].meaning`; còn 「」 bao ngoài `quotes[].ja` / ( ) bao ngoài `quotes[].meaning`; nhận xét đặt nhầm lựa chọn; mọi dòng phần đầu không vào `question.meaning`.
- Bỏ sót / tự thêm / viết lại chữ; còn nhãn (`Nghĩa:`, `Giải thích:`, `Trích dẫn:`, `→ SAI.`) trong chữ; thiếu ⟪ ⟫ quanh tiếng Nhật trong câu Việt; sai `{ }` / furigana.
- `is_match` khác chữ đánh giá của lời giải (K6) – sửa theo lời giải (kể cả khi lời giải sai – rồi gắn cờ ở mục 3).
- Khuôn `chi_ban_dich` / `tu_do` làm sai mục 4a / 4b của `prompts/s1_chuyen_json.md`.

## 2. Sửa lỗi ĐỊNH DẠNG có sẵn trong bản gốc – `loai: sua_dinh_dang` + `nhom`

| nhom | Ví dụ dạng 12 |
|---|---|
| `dinh_chu` / `xuong_dong` | câu dính nhau, thiếu xuống dòng giữa các ý |
| `lap_tu` | "của của"; chữ Nhật lặp do gõ (`最近最近では` trong câu hỏi 12723_3 – nếu chắc là gõ lặp) |
| `chinh_ta` / `dau_cau` / `khoang_trang` | lỗi chính tả / dấu tiếng Việt; dấu thừa; khoảng trắng thừa giữa các chữ Nhật (`と ある が` – 17039_1) |
| `ky_tu` | ký tự rác: `>` lẻ (`ビール>` – 12724), `<| trích;`, `начально:` (13483_2), `|` thừa |
| `furigana` | ruby hỏng / furigana lệch phạm vi; furigana gắn lên chữ Việt |
| `khac` | lỗi định dạng khác (ghi rõ) |

- **Câu trích lệch nhẹ đoạn văn** (cảnh báo `K-TD … lệch nhẹ`, cờ `trich_lech_doan_van_nhe`): khác 1–2 kana do gõ / ruby hỏng, **không đổi nghĩa**. Xác định bên nào gõ sai: **đoạn văn** gõ sai (vd 12724_1 đoạn văn viết `子とも`, câu trích `子ども` đúng) → không sửa, ghi `[Ghi chú]`; **câu trích** gõ sai → `sua_dinh_dang` `quotes[j].ja` theo đoạn văn (`nhom: ky_tu` / `furigana`). Khác chữ Hán ↔ kana cùng cách đọc, thêm / bỏ `注1`, ①②, dấu câu, khoảng trắng, cách đọc trong ngoặc → **không** tính (Python đã bỏ qua).
- **Câu hỏi / lựa chọn trong lời giải khác đề** chỉ vì **đề gõ sai** (`ヨーロッバ`, `とれか`, `コゴミ` – cờ `lua_chon_khac_de` / `cau_hoi_khac_de`): lời giải đúng → **không sửa, không gắn cờ**, ghi `[Ghi chú] Đề gõ sai '…' – lời giải đúng`. Lời giải gõ sai (`頂上に<|着;つ|いた` đã được Python sửa) → sửa định dạng theo đề.
- Mỗi chỗ sửa định dạng có **hai** ghi chép: mục `sua` (`duong_dan` ở trường nhỏ nhất, `loai`, `nhom`, `muc_do`, `ly_do`) **và** dòng `ghi_chu_ban_goc`: `[Đã sửa định dạng] <chỗ>: '<cũ>' → '<mới>' – <lỗi gì>` (một dòng, xuống dòng ghi `⏎`).
- **Một trường – một loại sửa** (sửa định dạng + sửa lỗi tác tử TẠO trên cùng một trường thì đè nhau → ưu tiên lỗi tác tử TẠO, lỗi định dạng mô tả trong ghi chú / cờ).

## 3. Gắn cờ NGHI SAI NỘI DUNG – không sửa (câu **không được dịch**, chuyển CTV tiếng Nhật)

Ghi vào `nghi_noi_dung`, mỗi chỗ nghi một mục `{vi_tri, nhom, mo_ta, de_xuat}`. `vi_tri`: `Câu hỏi – nghĩa`, `Lựa chọn N – nghĩa`, `Lựa chọn N – trích dẫn`, `Lựa chọn N – nghĩa trích dẫn`, `Lựa chọn N – giải thích`, `Lựa chọn N – đánh giá`, `Toàn bộ lời giải`.

**Nhóm cờ dạng 12** (đã có trong `pipeline_chung/claude_log.py`):

| # | Lỗi cần bắt | `nhom` |
|---|---|---|
| 1 | **Câu trích không có trong đoạn văn / khác đoạn văn về chữ – nghĩa** (cảnh báo `K-TD … khác / không tìm thấy`, cờ `trich_lech_doan_van_nang`, `trich_khong_tim_thay`): trích bịa, ghép hai câu xa nhau thành một, đổi chữ làm **đổi nghĩa**; **hoặc** câu trích có thật nhưng **không chứng minh** được điều nhận xét nói / trích sai chỗ (trích câu nói về nhóm khác, đoạn khác). Câu trích là câu đoạn văn đã **điền lựa chọn vào chỗ trống** (`khop_dien`) → bình thường. | `trich_dan` |
| 2 | **Phân tích trái đoạn văn / lập luận sai**: nói "đoạn văn không đề cập" nhưng đoạn văn có nói; hiểu sai chủ thể / phạm vi của chỉ thị từ (これ / それ), của phần gạch chân; lý do loại một lựa chọn sai sự thật hoặc mâu thuẫn với chính câu trích; câu hỏi điền liên từ mà phân tích sai quan hệ câu trước – sau. **Phải đọc đoạn văn** khi soát lựa chọn đúng và lý do loại. Nhận xét đúng ý nhưng diễn đạt vụng → không gắn cờ. | `phan_tich` |
| 3 | **Đáp án đáng ngờ**: lời giải chấm lệch đáp án của đề (cờ `danh_gia_lech_dap_an`, `khong_danh_gia_dung`, cảnh báo K8); 2 lựa chọn được chấm ĐÚNG; 'Câu trả lời đúng là …' khác lựa chọn đúng (`dap_an_cuoi_lech`); **đáp án của đề có vẻ sai** khi đọc đoạn văn. | `dap_an` |
| 4 | **Nghĩa câu hỏi / lựa chọn / câu trích (tiếng Việt) lệch câu Nhật**: dịch sai, thêm / bớt ý, mất phủ định / bị động / sai khiến, sai chủ thể (vd dịch 'câu hỏi phủ định' thành khẳng định: `違うもの` → 'cái nào đúng'). Dịch câu trích **tóm tắt / chỉ một phần** câu Nhật (vd 12671_1 lựa chọn 4: bản dịch có thêm ý "trường tiểu học và trung học cơ sở nơi sự đoàn kết trong lớp rất mạnh" không có trong câu trích) → cờ. | `nghia_cau` |
| 5 | **Thiếu nội dung**: khuôn `chi_ban_dich` (chỉ có bản dịch, không phân tích – gắn **mọi** câu khuôn này, `vi_tri: Toàn bộ lời giải`), `tu_do` (không phân tích từng lựa chọn), lời giải thiếu khối lựa chọn (`khong_du_4_khoi`, vd 12730_3), khối thiếu nghĩa / nhận xét làm người học không hiểu vì sao loại; câu hỏi chọn **hình** (`can_hinh` – lựa chọn là số 1–4, hình không có trong dữ liệu: `mo_ta` ghi rõ "câu hỏi dùng hình, dữ liệu không có hình"). | `thieu_noi_dung` |
| 6 | Lời giải dịch máy ngược / vô nghĩa (cờ `nhan_tieng_nhat`, `tieng_nhat_tran` khi câu không đọc hiểu được – 13483, 17033_2: '｜表現《ひょうげん》 của một ｜人《ひと》 luôn ｜満《み》…'); âm Hán Việt Python dò sót; lỗi khác. | `khac` |

- Có `{nhom: "trich_dan"}` / `phan_tich` thì `mo_ta` nêu **câu nào trong đoạn văn** là căn cứ đúng (trích ngắn), `de_xuat` nêu cách sửa.
- Không chắc lắm cũng gắn cờ (CTV quyết) – nhưng không gắn cờ cho cách diễn đạt chỉ "chưa hay".
- `tieng_nhat_tran` chỉ là gợi ý: câu Việt có chen từ Nhật có furigana nhưng **vẫn đọc hiểu được** (`để cây ｜長生《ながい》き (sống lâu)`) → không gắn cờ.

**3b. Sau khi CTV tiếng Nhật trả kết quả** (chỉ khi người dùng đưa phản hồi): CTV xác nhận không sai → xóa mục cờ; sai → sửa JSON theo CTV, mục `sua` với `"loai": "sua_theo_ctv"` + `nhom`, dòng `[Đã sửa theo CTV] <chỗ>: '<cũ>' → '<mới>' – <CTV nói gì>`; chạy lại `s1_kiem_tra.py`.

**4. Âm Hán Việt** – Python tự dò (`[Âm Hán Việt] …`); câu có âm Hán Việt tự động không dịch. Python dò sót → cờ `khac`.

**Dạng của câu:** có ít nhất một `sua_dinh_dang` → Dạng 2; không → Dạng 1. Chỉ câu **không có** `nghi_noi_dung` và không có âm Hán Việt mới được chốt và dịch.

## Gợi ý / cảnh báo Python

| Mã | Ý nghĩa | Xử lý |
|---|---|---|
| K0–K9 (LỖI) | sai cấu trúc / trường cố định / thiếu chữ so với lời giải / `is_match` khác lời giải / `correct` | sửa (lỗi tác tử TẠO) |
| K-TD (cảnh báo) | câu trích ↔ đoạn văn: lệch nhẹ / khác / không tìm thấy | mục 2 (lệch nhẹ) hoặc 3-1 |
| K7 (cảnh báo) | lời giải có 「…」 đứng riêng nhưng `quotes = []` | xem có phải câu trích bị bỏ vào `analysis` không |
| K8 (cảnh báo) | `is_match = true` không đúng 1 lựa chọn = đáp án | 3-3 |
| `TD:` | kết quả so câu trích của **lời giải gốc** | như K-TD |

## Checklist

- [ ] `question.ja` = dòng câu hỏi của lời giải (khuôn bất thường: câu hỏi của đề); `question.meaning` = mọi dòng còn lại của phần đầu.
- [ ] Mỗi lựa chọn: `option_ja` = dòng `i.`; `meaning` = dòng Nghĩa; `quotes` = mọi câu trích đứng riêng (bỏ 「」 / ( ) bao ngoài, nhãn dẫn); `analysis` = phần nhận xét còn lại; `is_match` = chữ đánh giá; `reading = null`.
- [ ] `correct.index` = `dap_an_so`; `correct.option_ja` giống hệt; `full_sentence`, `full_translation`, `summary`, `key_info` = null.
- [ ] ⟪ ⟫ quanh mọi tiếng Nhật trong câu Việt; `{ }`, furigana đúng như bản gốc.
- [ ] **Đã đọc đoạn văn** và soát: câu trích có thật & đúng chỗ, phân tích từng lựa chọn khớp đoạn văn, đáp án hợp lý, nghĩa câu hỏi / lựa chọn / câu trích đúng câu Nhật.

## Mẫu file đặc tả lô (GĐ1)

```json
{"giai_doan": "1",
 "cau": {
  "16447_1": {},
  "12724_1": {"ghi_chu_ban_goc": ["[Ghi chú] Lựa chọn 1 – trích dẫn: K-TD lệch nhẹ vì ĐOẠN VĂN gõ '子とも' – câu trích '子ども' đúng, không sửa, không gắn cờ"]},
  "12724_2": {"ghi_chu_ban_goc": ["[Ghi chú] Lựa chọn 1 – trích dẫn: K-TD 'khác' vì đoạn văn gõ '全券' (câu trích '金券' đúng) và câu trích viết 'ここでは' thay '買い物で' – không đổi ý, không gắn cờ"]},
  "<id_a>": {"thay": [{"duong_dan": "$.options[2].quotes[0].ja", "cu": "<chuỗi gõ sai>", "moi": "<chuỗi theo đoạn văn>"}],
             "sua": [{"duong_dan": "$.options[2].quotes[0].ja", "loai": "sua_dinh_dang", "nhom": "ky_tu", "muc_do": "nhe", "ly_do": "câu trích gõ sai kana so với đoạn văn"}],
             "ghi_chu_ban_goc": ["[Đã sửa định dạng] Lựa chọn 3 – trích dẫn: '<cũ>' → '<mới>' – gõ sai kana so với đoạn văn"]},
  "<id_b>": {"nghi_noi_dung": [{"vi_tri": "Lựa chọn 2 – trích dẫn", "nhom": "trich_dan",
              "mo_ta": "Câu trích không có trong đoạn văn (ghép đoạn 2 và đoạn 4, đổi chủ ngữ); căn cứ đúng là câu '…' ở đoạn 3.",
              "de_xuat": "Trích: 「…」"}]}
 }}
```
- Lệch nhẹ (K-TD): **xác định bên nào gõ sai** – đoạn văn gõ sai → không sửa, ghi `[Ghi chú]`; câu trích gõ sai → `sua_dinh_dang` theo đoạn văn.
- `<id_a>` / `<id_b>` là chỗ thay bằng mã mẫu thật. Chuỗi `cu` phải xuất hiện đúng 1 lần trong trường; `duong_dan` = đường dẫn `xem_gd1.py` in ra, thêm `$.` ở đầu. Một file cho mỗi lô mỗi giai đoạn (chạy lại thì sửa trong cùng file – các khóa danh sách bị ghi đè).
