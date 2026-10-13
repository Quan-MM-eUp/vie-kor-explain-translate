# Hướng dẫn tác tử KIỂM TRA – Bước 1.2: kiểm tra JSON tiếng Việt và sửa lỗi (dạng 15 – Đọc hiểu: Tìm thông tin) · v1

> Phiên bản `s1_claude_kiem_tra.15.v1` (2026-10-08) – cách chia v2 (như 07–09) + tiêu chí riêng dạng 15 (mục 3d). Model: **Claude Opus 5.5** trong Cowork.
> Bản cần kiểm tra do **tác tử TẠO (Claude A, ngữ cảnh riêng)** tạo – mọi chỗ "bản GPT / lỗi GPT" trong các công cụ hiểu là bản / lỗi của tác tử TẠO. Bạn (tác tử KIỂM TRA) không tạo lại bản, chỉ soát, sửa lỗi tác tử TẠO / lỗi định dạng, và **gắn cờ** lỗi nội dung.

**Nhiệm vụ:** JSON phải thể hiện **đúng và đủ lời giải gốc** (không hơn, không kém); đồng thời đọc **ngữ liệu** để phát hiện lời giải **sai nội dung** (trích dẫn, phân tích, tính toán, kết luận) → gắn cờ, không sửa.

> Dạng 15 không có phần THAM KHẢO – `reference_raw` luôn `null` (Python điền, không sửa).

## Làm gì

Xem từng câu: `python3 ../../pipeline_chung/cong_cu/xem_gd1.py <id> …` (in **ngữ liệu đã trải bảng một lần cho mỗi nhóm**, rồi đề + lời giải gốc + gợi ý Python + JSON). Danh sách: `output/claude/gd1_danh_sach.json`. Mỗi mục có cờ (`co`), ghi chú bản gốc tự động, **kết quả Python chạy thử trên bản tạo** (`python_tren_ban_gpt` – gồm K-TD, K-TT, `[Âm Hán Việt]`, `[Nghi dính câu/định dạng]`).

Với mỗi câu:
1. Đọc ngữ liệu (cột `doan_van` của `output/samples/norm/<id>.json` hoặc `xem_gd1.py`), đề (`de`), lời giải gốc (`dau_vao`), cờ.
2. Mở `output/json_vi/checked/<id>.json` (đã chép từ bản tạo) và **sửa trực tiếp** nếu có lỗi tác tử TẠO / lỗi định dạng (mục 1–2). Giữ đúng schema; file phải là JSON hợp lệ.
3. Ghi kết quả cả lô bằng **file đặc tả + `ghi_ly_do.py`** (xem `SO_TAY_CHAY.md` mục 4.3).
4. Xong cả lô thì chạy `python3 scripts/s1_kiem_tra.py …` (cùng phạm vi) và báo kết quả.

## Phạm vi sửa – cách chia v2

Ba việc tách bạch: **sửa lỗi tác tử TẠO**, **sửa lỗi ĐỊNH DẠNG của bản gốc**, **gắn cờ NGHI SAI NỘI DUNG**. Không sửa nội dung bản gốc.

**1. Sửa lỗi tác tử TẠO** (`loai`: `sai_so_ban_goc` / `chinh_ta` / `khach_quan`): đặt sai trường (câu trích để trong analysis, trích dẫn tiếng Việt đưa vào quotes, chữ phân tích lọt vào `quotes[].meaning`), bỏ sót / tự thêm / viết lại chữ, gộp hai câu trích, còn nhãn `Trích dẫn:` / cặp 「」 hoặc ( ) ngoài cùng, mất `\n` / gạch đầu dòng, thiếu `⟪ ⟫`, mất furigana, `is_match` khác chữ `→ ĐÚNG/SAI` của lời giải, `question.ja` chép từ đề khi lời giải không có, tự sửa trích dẫn / phép tính.

**2. Sửa lỗi ĐỊNH DẠNG có sẵn trong bản gốc** – `loai: sua_dinh_dang` + `nhom` (`dinh_chu`, `xuong_dong`, `lap_tu`, `chinh_ta`, `dau_cau`, `khoang_trang`, `ky_tu`, `furigana`, `khac`): dính câu, thiếu xuống dòng, lặp từ do gõ, lỗi chính tả / dấu tiếng Việt, ruby hỏng (`少すこし` → `少し`), furigana lệch phạm vi / gắn lên chữ Việt, số toàn góc / bán góc lẫn lộn **trong câu Việt**.
- Mỗi chỗ có **hai** ghi chép: mục trong `sua` (`duong_dan` mức trường nhỏ nhất, `loai`, `nhom`, `muc_do`, `ly_do`) **và** một dòng `ghi_chu_ban_goc`: `[Đã sửa định dạng] <chỗ>: '<cũ>' → '<mới>' – <lỗi gì>` (một dòng, xuống dòng ghi `⏎`).
- Câu tiếng Nhật (`question.ja`, `option_ja`, `quotes[].ja`) Python so với lời giải (K5, K6, K-TD) – chỉ sửa định dạng rõ ràng (ruby hỏng, lặp ký tự) kèm mục `sua_dinh_dang` đúng đường dẫn; **không** sửa câu trích cho khớp ngữ liệu (đó là nội dung → cờ).
- Một trường – một loại sửa (như 07–09): trường đã có sửa lỗi tác tử TẠO thì lỗi định dạng ghi thành mô tả trong cờ / `ghi_chu_ban_goc`.
- Gợi ý `[Nghi dính câu/định dạng] …` chỉ là gợi ý – xác nhận rồi mới sửa.

**3. Gắn cờ NGHI SAI NỘI DUNG – không sửa** (câu **không được dịch**, chuyển CTV tiếng Nhật) – khóa `nghi_noi_dung`, mỗi chỗ một mục `{vi_tri, nhom, mo_ta, de_xuat}`:
- `vi_tri`: `Câu hỏi`, `Câu hỏi – nghĩa`, `Bản dịch ngữ liệu`, `Tóm tắt`, `Lựa chọn N – nghĩa`, `Lựa chọn N – trích dẫn`, `Lựa chọn N – nghĩa câu trích`, `Lựa chọn N – phân tích`, `Lựa chọn N – kết luận`, `Đáp án`.
- `nhom` dùng cho dạng 15: `tinh_toan` · `trich_dan` · `phan_tich` · `dap_an` · `nghia_cau` · `thieu_noi_dung` · `khac`.
- `mo_ta`: vì sao nghi sai (ghi số quy tắc 3d-n, **dẫn chữ của ngữ liệu** làm bằng chứng); `de_xuat`: cách sửa đề xuất – **không** sửa vào JSON.
- Không chắc lắm cũng gắn cờ (CTV quyết) – nhưng không gắn cờ cho cách diễn đạt chỉ "chưa hay".

**3d. Tiêu chí riêng dạng 15 (bắt buộc soát – đã duyệt 08/10/2026)**

| # | Lỗi cần bắt | `nhom` |
|---|---|---|
| 1 | **Phép tính sai** (cảnh báo **K-TT**, cờ `tinh_toan_sai`, `output/reports/tinh_toan.csv`) hoặc **áp sai điều kiện** khi tính: sai ngày / thứ áp dụng giảm giá, sai đối tượng / hạng vé / độ tuổi, quên phí cộng thêm, vượt số lượng tối đa, nhầm giờ mở cửa… → phải **tự tính lại theo ngữ liệu**. Kết quả tính của lời giải khác lựa chọn nó chấm ĐÚNG cũng thuộc mục này. | `tinh_toan` |
| 2 | **Trích dẫn sai**: câu trích tiếng Nhật không có trong ngữ liệu / tự dựng (vd 12735_1 「4 回 一 日 食べた後…」), trích nhầm hàng / ô của bảng, trích đúng nhưng không chứng minh được điều phân tích nói (cảnh báo **K-TD**, cờ `trich_dan_ngoai_ngu_lieu`, `output/reports/trich_dan.csv`). Trích **rút gọn / bỏ khoảng trắng / bỏ chú thích 注** mà đúng ý → **không** gắn cờ. | `trich_dan` |
| 3 | **Phân tích trái ngữ liệu**: nói "ngữ liệu không đề cập" nhưng có, đọc sai bảng (lẫn cột / hàng), bỏ sót điều kiện ※ / chú thích, lý do loại không đúng, mô tả lựa chọn sai. | `phan_tich` |
| 4 | **Kết luận / đáp án**: lời giải chấm ĐÚNG lựa chọn khác `dap_an_so` (cờ `lech_dap_an`), chấm ĐÚNG nhiều lựa chọn, chấm ĐÚNG nhưng phần phân tích nói không khớp (vd 307_1); hoặc **đáp án của dữ liệu sai** khi tự giải theo ngữ liệu (vd 12736_2: lời giải tính ra 740円 = lựa chọn 4, `dap_an_so = 2`) → gắn cờ + **báo người dùng sửa dữ liệu gốc**. | `dap_an` |
| 5 | **Nghĩa sai**: dịch câu hỏi / lựa chọn / câu trích lệch tiếng Nhật – đặc biệt **sai số, giá, giờ, ngày, thứ**, phủ định, chủ thể; dòng "dịch" của câu trích chỉ lặp lại tiếng Nhật (không dịch). | `nghia_cau` |
| 6 | **Thiếu nội dung**: khuôn lạ B / C (cờ `khuon_la`) – không phân tích đủ 4 lựa chọn; lựa chọn chỉ có kết luận không lý do; **ngữ liệu rỗng** (cờ `thieu_ngu_lieu`) hoặc **là ảnh** (cờ `ngu_lieu_anh`, lựa chọn là tranh) nên không xác minh được → ghi rõ "không xác minh được vì …". | `thieu_noi_dung` |
| 7 | **Dữ liệu đề hỏng**: lựa chọn của đề bị đổi thành ngày giờ Excel (`lua_chon_de_hong`, vd 16919_2), câu hỏi / lựa chọn trong lời giải khác đề về **nội dung** (không phải khoảng trắng / chữ Hán ↔ kana) → gắn cờ + báo người dùng. | `khac` / `dap_an` |

- Bắt buộc so cho **mọi** câu: kết luận ĐÚNG ↔ đáp án ↔ tự giải theo ngữ liệu; mỗi câu trích ↔ ngữ liệu; mỗi phép tính ↔ tính lại; nghĩa câu hỏi / lựa chọn / câu trích ↔ tiếng Nhật.
- Câu con cùng ngữ liệu: cùng câu trích mà nghĩa khác nhau (cảnh báo **K-NQ**) → xem có dịch sai không (sai → `nghia_cau`), không tự thống nhất.
- **Không gắn cờ:** phân tích ngắn nhưng đúng; lựa chọn SAI không kèm trích dẫn; lặp lại cùng phép tính ở nhiều lựa chọn; dịch vụng nhưng đúng ý; trích dẫn khác ngữ liệu chỉ ở khoảng trắng / dấu câu / `|` của bảng / 注; lời giải viết một phần bằng tiếng Nhật (chỉ cần bọc ⟪ ⟫ đúng).
- `is_match` là điều lời giải NÓI: tác tử TẠO điền sai so với lời giải → sửa (`sai_so_ban_goc`); lời giải nói sai sự thật → giữ và gắn cờ (3d-4).

**3b. Sau khi CTV tiếng Nhật trả kết quả** (chỉ làm khi người dùng đưa phản hồi CTV): CTV xác nhận không sai → xóa mục cờ; sai → sửa JSON theo CTV (`loai: sua_theo_ctv` + `nhom` + dòng `[Đã sửa theo CTV] <chỗ>: '<cũ>' → '<mới>' – <CTV nói gì>`), xóa mục cờ; chạy lại `s1_kiem_tra.py`.

**4. Âm Hán Việt** – Python tự dò (`[Âm Hán Việt] …`); câu có âm Hán Việt tự động không được dịch. Python dò sót → cờ `khac`, ghi rõ.

**Dạng của câu:** có ít nhất một `sua_dinh_dang` → **Dạng 2**; không → **Dạng 1**. Chỉ câu **không có** `nghi_noi_dung` và không có âm Hán Việt mới được chốt và dịch.

## Kiểm tra Python (s1_kiem_tra.py)

| Mã | Mức | Nội dung |
|---|---|---|
| chung | LỖI | schema; mất tiếng Nhật; độ phủ tiếng Việt < 97% (nhãn `Nghĩa:`, `→ ĐÚNG/SAI`, nhãn dẫn trích dẫn không tính); furigana; `{ }` |
| K1 | LỖI | đủ 4 lựa chọn index 1–4 |
| K2 / K4 | LỖI | `correct.index = dap_an_so`; `correct.option_ja` = `options[index-1].option_ja`; `full_sentence = null` |
| K3 | LỖI | `is_match` theo kết luận của lời giải; `is_match = true` chỉ ở `correct.index` (câu có cờ lệch đáp án → chỉ cảnh báo) |
| K5 / K6 | LỖI (khuôn C: cảnh báo) | `question.ja` = dòng câu hỏi của lời giải (không có → null); `option_ja` = dòng lựa chọn của lời giải (không phải tiếng Nhật → lựa chọn của đề); `reading = null`; có `Nghĩa:` thì `meaning` khác null |
| K-TD | LỖI / cảnh báo | `quotes[].ja` phải là tiếng Nhật và có nguyên văn trong **lời giải** (LỖI); không tìm thấy trong **ngữ liệu** (cảnh báo → soát 3d-2) |
| K-NQ | cảnh báo | cùng câu trích, nghĩa khác giữa các câu con |
| K-TT | cảnh báo | phép tính trong `analysis` sai khi tính lại |
| K-FT | LỖI / cảnh báo | `key_info` phải null; `full_translation` có mà lời giải không có bản dịch |

## Checklist cấu trúc

- [ ] `question.ja` = dòng câu hỏi tiếng Nhật của lời giải (không có → null); `question.meaning` = dòng dịch.
- [ ] Phần đầu khác: bản dịch ngữ liệu → `full_translation`; tóm tắt / liệt kê → `summary`.
- [ ] Mỗi lựa chọn: `option_ja` đúng; `meaning` = dòng `Nghĩa:`; **mỗi câu trích tiếng Nhật một phần tử `quotes`** (không nhãn, không 「」 / ( ) ngoài cùng); mọi chữ còn lại trong `analysis` đúng thứ tự, giữ `\n`; `is_match` đúng chữ lời giải.
- [ ] `correct` đúng; `key_info = null`; mọi tiếng Nhật trong câu Việt có `⟪ ⟫`; furigana đúng như bản gốc.
- [ ] Soát đủ **3d-1…7** cho mọi câu (đọc ngữ liệu!), mọi cảnh báo K-TD / K-TT / K-NQ.

## Mẫu file lý do (ghi qua file đặc tả lô – SO_TAY_CHAY.md mục 4.3)

```json
{
  "sua": [
    {"duong_dan": "$.options[2].quotes", "loai": "sai_so_ban_goc", "muc_do": "nang",
     "ly_do": "Tác tử TẠO gộp 2 câu trích thành một – tách lại theo lời giải"},
    {"duong_dan": "$.options[0].analysis.vi", "loai": "sua_dinh_dang", "nhom": "dinh_chu", "muc_do": "nhe",
     "ly_do": "dính câu: 'yên.Như vậy' → 'yên. Như vậy'"}
  ],
  "ghi_chu_ban_goc": ["[Đã sửa định dạng] Lựa chọn 1 – phân tích: 'yên.Như vậy' → 'yên. Như vậy' – dính câu"],
  "nghi_noi_dung": [
    {"vi_tri": "Đáp án", "nhom": "dap_an",
     "mo_ta": "(3d-4) Theo phiếu giảm giá ngày 5/5: cá 30% (600×0.7=420), xúc xích 20% (400×0.8=320) → 740円 = lựa chọn 4; lời giải chấm ĐÚNG lựa chọn 4 nhưng dap_an_so = 2 (700円).",
     "de_xuat": "Sửa dữ liệu gốc: dap_an_so = 4"}
  ]
}
```

- `loai`: `sai_so_ban_goc` | `chinh_ta` | `khach_quan` | `chu_quan` (lỗi tác tử TẠO) | `sua_dinh_dang` (bắt buộc `nhom` + dòng `[Đã sửa định dạng]`) | `sua_theo_ctv`. `muc_do`: `nghiem_trong` | `nang` | `nhe`.
- Không có gì thì để `"sua": []`, `"nghi_noi_dung": []`.
