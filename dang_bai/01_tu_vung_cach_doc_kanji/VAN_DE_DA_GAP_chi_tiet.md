# Cây vấn đề đã gặp – Dạng 01: Cách đọc kanji (VI → KO)

Cập nhật: 2026-10-02 · Số liệu lấy từ nhật ký Claude sửa (`output/json_vi|json_ko/checked/*.ly_do.json`: 117 câu GĐ1, 108 câu GĐ2) và phản hồi CTV tiếng Hàn (file 50 câu: 41 Đạt · 2 Sửa nhỏ · 7 Không đạt).

**Cách đọc file**
- Cây chính (mục 1) xếp vấn đề theo **nơi phát sinh lỗi**: bản gốc VI → GPT chuyển JSON → GPT dịch KO → kiểm tra Python → Excel CTV → vận hành. Cách xếp này không đổi khi cách chia dạng thay đổi.
- Mỗi lá có nhãn:
  - **Phiên bản**: `[pilot]` (trước 29/09) · `[v1]` cách chia 3 dạng (29/09) · `[v2]` cách chia mới (01/10)
  - **Trạng thái**: `ĐÃ XỬ LÝ` · `THEO DÕI` (đã có biện pháp, cần xem thêm) · `CHƯA CHỐT` (cần bạn quyết định)
- Mục 2 đối chiếu cây với từng cách chia dạng. Mục 3 là dòng thời gian.

---

## Tổng quan

```
Vấn đề dịch VI → KO (dạng 01)
├── A. Lỗi có sẵn trong lời giải VI gốc                ← nguyên nhân chính khiến CTV đánh "Không đạt"
│   ├── A1. Định dạng
│   │   ├── A1.1 Dính câu / dính mục đánh số
│   │   ├── A1.2 Cách đọc lẫn số ①②③
│   │   ├── A1.3 Chính tả, lặp chữ, dấu câu
│   │   └── A1.4 Gạch đầu dòng / số thứ tự đặt sai chỗ, thiếu gạch chân
│   ├── A2. Nội dung
│   │   ├── A2.1 Sai thì / thiếu ý ở nghĩa câu đề
│   │   ├── A2.2 Sai tự động từ / tha động từ
│   │   ├── A2.3 Nghĩa từ sai, nhầm từ đồng âm
│   │   └── A2.4 Cách đọc sai (không phải lẫn số)
│   ├── A3. Âm Hán Việt trong phần tham khảo
│   └── A4. Dữ liệu không khớp (lệch đáp án, thiếu phân tích, không có lời giải)
├── B. GPT chuyển sang JSON tiếng Việt (GĐ1)
│   ├── B1. Bọc ⟪ ⟫ quanh chữ Latinh
│   ├── B2. Đổi danh sách đánh số thành "- "
│   └── B3. Không tách thể từ điển / phân tích bị dồn
├── C. GPT dịch sang tiếng Hàn (GĐ2)
│   ├── C1. Không nhất quán giữa các câu con cùng câu đề
│   ├── C2. Dịch đúng chữ nhưng sai ngữ cảnh / sai thuật ngữ
│   ├── C3. Đánh dấu { } và trợ từ
│   ├── C4. Lỗi VI lan sang KO (hệ quả của A2)
│   └── C5. Thiếu 한자음 cho người Hàn
├── D. Kiểm tra tự động (Python) báo nhầm
├── E. File Excel cho CTV
└── F. Vận hành pipeline
```

---

## 1. Cây chi tiết

### A. Lỗi có sẵn trong lời giải VI gốc

> CTV: cả 7 câu "Không đạt" và 2 câu "Sửa nhỏ" đều có lỗi từ bản VI gốc (riêng 3122 có thêm lỗi dịch KO 兄/姉 – xem C2). GPT dịch đúng theo bản VI nên lỗi VI thành lỗi KO.

#### A1. Định dạng (Claude được sửa, phải ghi chú từng chỗ)

- **A1.1 Dính câu / dính mục đánh số** – `[v2]` `THEO DÕI`
  - Hiện tượng: `…trường học.Học sinh…`, `…kỳ vọng. 3. …` dính vào câu trước, nhất là ở phần Tham khảo.
  - Ví dụ: 3163, 873 (Sửa nhỏ), 1449 (kèm lỗi nội dung). CTV ghi "Dính câu ở phần Tham khảo".
  - Xử lý: v2 thêm nhóm `dinh_chu`; Python gợi ý bằng `_dang.format_hints` (có thể báo nhầm hoặc bỏ sót); Claude sửa, ghi `[Đã sửa định dạng] …`.
- **A1.2 Cách đọc lẫn số ①②③** – `[v1]` `ĐÃ XỬ LÝ`
  - Hiện tượng: số thứ tự bị đọc thành chữ trong dòng cách đọc: `いち…`, `さんけて` (= ③ + 駆けて).
  - Ví dụ: 389, 390, 391. Có 13 chỗ sửa trong 117 câu GĐ1.
  - Xử lý: v1 xếp vào `sua_ban_goc/cach_doc`; v2 xếp vào lỗi định dạng `cach_doc_lan_so`.
- **A1.3 Chính tả, lặp chữ, dấu câu** – `[v1]` `ĐÃ XỬ LÝ`
  - Ví dụ: 379 "dạt đến" → "đạt đến"; 381 "hai chữ chữ hán"; 434 thiếu ngoặc kép đóng. Có 11 chỗ.
  - Lưu ý: `..` (hai dấu chấm) trong bản gốc không sửa.
- **A1.4 Gạch đầu dòng / số thứ tự sai chỗ, thiếu gạch chân** – `[v1]` `ĐÃ XỬ LÝ`
  - Ví dụ: 2583 có dòng "-" trống thừa; 385 có số "3." chèn giữa từ; 440 dòng cách đọc thiếu gạch chân. Có 8 chỗ (nhóm "khác").

#### A2. Nội dung (v2: Claude chỉ gắn cờ `nghi_noi_dung`, KHÔNG sửa, câu không được dịch)

- **A2.1 Sai thì / thiếu ý ở nghĩa câu đề** – `[v2]` `THEO DÕI`
  - Hiện tượng: VI thêm "đã" nên KO dịch thành quá khứ, trong khi câu Nhật là tiếp diễn hoặc trạng thái.
  - Ví dụ: 3134 (耳: "đã đau" ≠ "đau từ sáng đến giờ"), 1326 ("đã nhận được" ≠ "đang nhận được"), 1639 ("đã giảm" ≠ "đang giảm"), 658 (thiếu ý).
  - Xử lý: cờ `nghi_noi_dung` nhóm `nghia_cau`, vị trí thường là `question.meaning`.
- **A2.2 Sai tự động từ / tha động từ** – `[v2]` `THEO DÕI`
  - Ví dụ: 1449 (決まる là tự động từ, 決める là tha động từ, bản VI ghi ngược); 14802 (焦がす là tha động từ "làm cháy", không phải "cháy").
  - Xử lý: cờ nhóm `tu_tha_dong_tu`.
- **A2.3 Nghĩa từ sai, nhầm từ đồng âm** – `[v1]` (v1 đã sửa) → `[v2]` (chỉ gắn cờ)
  - Ví dụ: 15066 月賦 bị ghi thêm nghĩa "ợ hơi" (nhầm với げっぷ); 2209 繋駕 bị dịch nhầm từ "harness". Có 9 chỗ (nhóm `kien_thuc`).
  - Thay đổi: v1 cho Claude sửa; v2 chỉ gắn cờ (nhóm `nghia_tu` / `dong_am`).
- **A2.4 Cách đọc sai (không phải lẫn số)** – `[v2]` `THEO DÕI`
  - Ví dụ: 391 貝殻 đọc thành がいがら (đúng: かいがら).
  - v2: gắn cờ nhóm `cach_doc`. Chỉ trường hợp lẫn số ①②③ mới là lỗi định dạng.

#### A3. Âm Hán Việt trong phần tham khảo – `[v1]` `[v2]` `CHƯA CHỐT`
- Hiện tượng: phần tham khảo có "âm Hán Việt …", "chữ Hán NÃO", "選 (せん) - TUYỂN". Dịch sang tiếng Hàn thì vô nghĩa với người Hàn.
- Quy mô: Python phát hiện 63/1.872 câu (`_dang.han_viet_src`), đều là trường hợp đúng. Ví dụ: 600, 601.
- Lịch sử xử lý: `[v1]` kiểm tra D5 báo lỗi GĐ2 và xếp Dạng 3 → `[v2]` cờ `han_viet`, trạng thái `CHỜ_XỬ_LÝ_HÁN_VIỆT`, không dịch.
- Cần chốt: bỏ đi / thay bằng 한자음 / giữ kèm ghi chú (liên quan C5).

#### A4. Dữ liệu không khớp – `[pilot]` `THEO DÕI`
- **Lệch đáp án**: `correct_index` trong lời giải khác `dap_an_so`, có 9 câu (ví dụ 603). Chính sách: lấy `dap_an_so` làm chuẩn và ghi `[Bản gốc VI]`.
- **Thiếu phân tích / thiếu lựa chọn**, **thể từ điển dính vào cách đọc** (63 câu), **dạng `###`**: có cờ riêng ở `s0`.
- **Không có lời giải**: gắn `LỖI_GĐ1` ngay từ `s0`.

### B. GPT chuyển sang JSON tiếng Việt (GĐ1)

> Ít lỗi: chỉ 3 chỗ Claude sửa lỗi GPT trong 117 câu.

- **B1. Bọc ⟪ ⟫ quanh chữ Latinh** (te, Kabuki, Noh) – ví dụ 1094, 548 – `ĐÃ XỬ LÝ` (Claude sửa, loại `sai_so_ban_goc`).
- **B2. Đổi danh sách đánh số thành "- "** (2/5 câu test) – `[pilot]` `ĐÃ XỬ LÝ` (sửa quy tắc 8 của prompt, thêm kiểm tra K9).
- **B3. Không tách thể từ điển / phân tích bị dồn** – ví dụ 595 – `ĐÃ XỬ LÝ` (quy tắc tách trong prompt; Claude sửa nếu còn sót).

### C. GPT dịch sang tiếng Hàn (GĐ2)

> 34 chỗ Claude sửa trong 108 câu. CTV không sửa bản KO ở câu "Đạt" nào.

- **C1. Không nhất quán giữa các câu con cùng câu đề** – `THEO DÕI` (lỗi hay gặp nhất, 22 chỗ)
  - Ví dụ: 434–437 dùng cùng câu tiếng Việt nhưng được dịch khác nhau.
  - Xử lý: Claude thống nhất theo câu đã dịch trước; bộ nhớ dịch (`bo_nho_dich_ko.json`). v2 khởi động lại bộ nhớ dịch trong `output_v2/`.
- **C2. Đúng chữ nhưng sai ngữ cảnh / sai thuật ngữ** – `THEO DÕI` (9 chỗ)
  - 2440: "đáp án này" chỉ lựa chọn sai → dùng `선택지`, không dùng `정답`.
  - 3163: 午前 là `오전`, không phải `아침` (trùng nghĩa với 朝).
  - 3122 (CTV): 兄/姉 dịch thành `형`/`누나` là cách gọi theo người nói nam; tiếng Nhật dùng chung → cần chọn theo ngữ cảnh (`형/오빠`, `누나/언니`). Dùng `지칭` (nhắc đến) thay cho `부르는 방식` (cách gọi). → `CHƯA CHỐT`: bổ sung vào glossary / prompt GĐ2.
- **C3. Đánh dấu { } và trợ từ** – `ĐÃ XỬ LÝ` (Claude sửa)
  - `{ }` chỉ bọc phần dịch của từ đang hỏi, không bọc trợ từ (2691: `{운동}을`; 15504: `산의` nằm ngoài).
  - Trợ từ theo phụ âm cuối (435: `가장자리와`).
- **C4. Lỗi VI lan sang KO** – xem A2. Không sửa ở GĐ2 vì bản dịch phải bám bản VI. `[v2]` chặn từ GĐ1: câu có cờ thì không dịch.
- **C5. Thiếu 한자음 cho người Hàn** – `CHƯA CHỐT`
  - CTV gợi ý ở 35/50 câu: "khi phần tham khảo phân tích từng Hán tự, nên bổ sung 한자음" (ví dụ 午 → 오, 後 → 후). Có câu CTV ghi "không cần".
  - Vướng quy tắc "không thêm nội dung". Kho `da_duyet/` đã ghi cột `goi_y_han_han` để lọc khi quyết định.

### D. Kiểm tra tự động (Python) báo nhầm

- **D1. Furigana với dạng `###`**: dòng "Từ:" làm báo lỗi giả (53760) → `furi_src_text` – `ĐÃ XỬ LÝ`.
- **D2. Kiểm tra trung thành khi Claude sửa bản gốc**: báo "mất chữ" ở chỗ đã sửa → kiểm tra trên bản đã hoàn tác (`revert_src_fixes`); với 603 thêm K8 và đường dẫn lý do – `ĐÃ XỬ LÝ`.
- **D3. Nhãn đáp án của bản gốc không có trong đề** → `src_text_for_check` – `ĐÃ XỬ LÝ`.
- **D4. Đếm từ tiếng Nhật sai** (cảnh báo "sửa quá nhiều") → mỗi chữ CJK = 1 từ – `ĐÃ XỬ LÝ`.
- **D5. Lọc trước mẫu (s7) báo nhầm cách đọc** với katakana và số → chuẩn hóa katakana → hiragana; ngưỡng 75%, vùng 75–90% đánh dấu "cần xem" – `ĐÃ XỬ LÝ`.

### E. File Excel cho CTV

- **E1. Tiếng Hàn trông như in đậm** – nguyên nhân: font Calibri không có chữ Hàn nên Excel thay font khác → đặt Malgun Gothic cho các cột KO – `THEO DÕI` (file `THU_FONT_tieng_Han.xlsx` chờ bạn xem).
- **E2. Nhãn in đậm thừa**; `{ }` hiển thị thành gạch chân – `ĐÃ XỬ LÝ`.
- **E3. CTV tiếng Nhật cần file riêng** cho chỗ Claude sửa bản gốc → `s3b_xuat_ctv_nhat.py`; `[v2]` gồm cả câu có cờ nghi sai nội dung – `ĐÃ XỬ LÝ`.

### F. Vận hành pipeline

- **F1. Key hết hạn giữa chừng** (401 khi dịch 61–70, xong 596–599): gia hạn key trong `.env`, chạy lại đúng lệnh cũ; câu đã xong tự bỏ qua – `THEO DÕI` (61–70 GĐ2 chưa xong).
- **F2. `.env` từng nằm trong lịch sử git** (`test_5dang/.env`) → nên đổi key – `CHƯA CHỐT` (bạn kiểm tra đã đổi chưa).
- **F3. Duyệt nhiều câu một lúc dễ sai** → Claude duyệt 10 câu mỗi lần – `ĐÃ XỬ LÝ`.
- **F4. Chạy lại vùng `--tu/--den` cũ làm lại mẫu đã duyệt** → kho `da_duyet/`, bước gọi API tự bỏ qua – `ĐÃ XỬ LÝ`.
- **F5. Thiếu mẫu N3–N5 cho CTV** → `s7_chon_mau.py` lọc trước theo cấp độ (58 mẫu lọc trước, 95% là Dạng 1) – `ĐÃ XỬ LÝ`.

---

## 2. Đối chiếu với từng cách chia dạng

| Nhánh | `[pilot]` (≤ 28/09) | `[v1]` 3 dạng (29/09) | `[v2]` (01/10) |
|---|---|---|---|
| A1 Định dạng | Claude không sửa, chỉ ghi `[Bản gốc VI]` | Sửa, `sua_ban_goc` → **Dạng 2** | Sửa, `sua_dinh_dang` → **Dạng 2** |
| A2 Nội dung | Ghi `[Bản gốc VI]` | Sửa (`kien_thuc`, `cach_doc`) → **Dạng 2** | **Chỉ gắn cờ** `nghi_noi_dung`, không dịch |
| A3 Hán Việt | Dịch nguyên | D5 → **Dạng 3** | Cờ `han_viet`, không dịch |
| B, C | Claude sửa (không ảnh hưởng dạng) | Không ảnh hưởng dạng (Dạng 1 vẫn có thể có B, C) | Như v1 |
| Không có A | Đạt | **Dạng 1** | **Dạng 1** (nếu không cờ) |

Vì sao đổi từ v1 sang v2: ở v1, lỗi nội dung "dễ thấy" thì được sửa, còn lỗi tinh (thì, tự/tha động từ) lọt qua và vẫn được dịch. 7 câu "Không đạt" đều nằm trong số này. v2 tách hẳn: định dạng thì sửa, nội dung thì gắn cờ chờ người duyệt.

---

## 3. Dòng thời gian

| Ngày | Vấn đề phát hiện | Thay đổi |
|---|---|---|
| 27/09 | B2 (GPT đổi danh sách đánh số) | Sửa prompt, thêm K9 |
| 28/09 | In đậm trong bản gốc (135 câu) | Quy tắc chung: in đậm cũng → `{ }` (dạng 01 chưa áp dụng) |
| 29/09 | A1.2, A1.3, A2.3 (lỗi bản gốc) | Claude được sửa bản gốc; cách chia 3 dạng `[v1]` |
| 29/09 | A3 (Hán Việt) | Thêm D5 → Dạng 3 |
| 29/09–01/10 | D1–D4 (Python báo nhầm), E1 | Sửa các kiểm tra, đổi font Excel |
| 01/10 | Phản hồi CTV: A1.1, A2.1, A2.2, C2 (兄/姉), C5 | Cách chia `[v2]`, `output_v2/`; kho `da_duyet/` (49 mẫu) |

---

## 4. Việc còn mở (lấy từ các lá `CHƯA CHỐT`)

1. A3 + C5: cách xử lý âm Hán Việt và có bổ sung 한자음 hay không.
2. C2: thêm quy tắc 兄/姉 và `지칭` vào glossary / prompt GĐ2.
3. 2 câu "Sửa nhỏ" (3163, 873): áp dụng chỗ CTV sửa, cho CTV xác nhận lại rồi lưu vào kho.
4. 7 câu "Không đạt": chạy lại theo v2 (sẽ được gắn cờ) hoặc sửa bản VI theo ý CTV.
5. F2: đổi API key.
6. In đậm → `{ }` cho 135 câu (chưa áp dụng ở dạng 01).

## Cách cập nhật file này

- Vấn đề mới: thêm lá vào đúng nhánh A–F, ghi nhãn phiên bản, trạng thái, mã câu ví dụ và cách xử lý.
- Đổi cách chia dạng: thêm một cột ở mục 2, không viết lại cây.
- Khi một vấn đề `CHƯA CHỐT` được quyết định: đổi trạng thái và ghi ngày vào mục 3.
