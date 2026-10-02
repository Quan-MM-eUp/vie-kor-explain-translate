# Workflow tổng quát: chuyển lời giải thích sang JSON và dịch Việt → Hàn

> Phiên bản: 2026-09-27 · Áp dụng cho cả 21 dạng bài. Workflow chi tiết của từng dạng chỉ ghi **phần khác biệt** so với file này (xem mục 10).
> Trạng thái: **đã chốt quy trình, chưa cập nhật code.**

## 1. Mục tiêu

- Chuyển lời giải thích tiếng Việt (`giai_thich_vi`, nhiều khuôn: JSON cũ, HTML, `###`) sang **JSON tiếng Việt** theo schema của từng dạng. Phần tiếng Nhật và tiếng Việt được tách riêng.
- Dịch các trường tiếng Việt sang **tiếng Hàn**. Sau này dịch thêm tiếng Đài Loan theo cùng quy trình.
- Chỉ gửi cho CTV tiếng Hàn những câu đã qua kiểm tra. Không để CTV mất thời gian với bản dịch tệ.

## 2. Vai trò và nguyên tắc

| Ai | Làm gì |
|---|---|
| **GPT** (model tốt nhất trên LLM Gateway, qua API) | Chuyển sang JSON tiếng Việt; dịch sang tiếng Hàn |
| **Claude Cowork** | **Giai đoạn 1:** kiểm tra JSON tiếng Việt **so với lời giải gốc** và sửa lỗi. **Giai đoạn 2:** kiểm tra bản dịch **có đúng với ngữ cảnh không** và sửa lỗi. Chỉ sửa lỗi, không thêm nội dung (mục 2a); mọi chỗ sửa đều được ghi lại (mục 2b) |
| **Python** | Chuẩn hóa dữ liệu đầu vào; tách và ghép trường dịch; **kiểm tra lần cuối** ở mỗi giai đoạn; gắn trạng thái; xuất Excel |
| **Bạn** | Duyệt JSON tiếng Việt trước khi dịch; quyết định với các câu bị lỗi |
| **CTV tiếng Hàn** | Đánh giá bản dịch cuối trong file Excel |

**Nguyên tắc:**

1. Ở mỗi giai đoạn, thứ tự là: **GPT tạo → Claude kiểm tra và sửa → Python kiểm tra lần cuối.** Python đứng cuối vì cho kết quả chắc chắn, và mọi chỗ Claude sửa cũng phải qua Python.
2. Việc gì đo được bằng code thì code làm, ví dụ chuẩn hóa furigana hay đếm ký hiệu. LLM chỉ làm phần cần hiểu nghĩa.
3. Trung thành với bản gốc. Chỗ nghi bản gốc tiếng Việt sai thì **không sửa**, chỉ ghi chú với nhãn `[Bản gốc VI]`.
4. Mọi bản trung gian đều được lưu lại (bản GPT, bản Claude đã sửa, bản cuối), để đo được chất lượng của từng bước.

## 2a. Phạm vi sửa của Claude

Claude chỉ **sửa lỗi**, **không được thêm nội dung**. Quy tắc này áp dụng cho cả bước 1.2 và bước 2.4. Từ 2026-09-29, ở **giai đoạn 1** Claude được sửa cả **lỗi có sẵn trong lời giải gốc** (loại `sua_ban_goc`, xem bên dưới), với điều kiện ghi chú rõ ràng; GPT vẫn chỉ chép nguyên.

**Được sửa** (mỗi chỗ sửa phải ghi một trong các loại sau vào nhật ký):

| Loại | Giai đoạn 1 (JSON tiếng Việt) | Giai đoạn 2 (bản dịch tiếng Hàn) |
|---|---|---|
| `sai_so_ban_goc` | GPT làm lệch so với lời giải gốc: đặt sai trường, bỏ sót ý, tự thêm ý, viết lại câu, mất hoặc sai tiếng Nhật, furigana, ký hiệu | Bản dịch lệch so với tiếng Việt: dịch thiếu, dịch thừa, sai ký hiệu |
| `chinh_ta` | Lỗi chính tả, lỗi đánh máy do GPT tạo ra | Lỗi chính tả, khoảng cách, dấu câu tiếng Hàn |
| `khach_quan` | Lỗi kiểm chứng được: sai vị trí gạch chân, sai đáp án, sai cấu trúc | Dịch sai nghĩa, sai thuật ngữ, thuật ngữ không nhất quán |
| `chu_quan` | (không áp dụng) | Câu thiếu tự nhiên, sai văn phong -습니다. Chỉ diễn đạt lại **cùng một nội dung** |
| `sua_ban_goc` | **Lỗi có sẵn trong lời giải gốc** (không do GPT): chính tả / gõ nhầm, cách đọc sai (vd lẫn số thứ tự ①②③ thành いち・に・さん), lỗi kiến thức rõ ràng. Bắt buộc ghi `nhom` và ghi chú `[Đã sửa bản gốc]` (xem 2a-1) | (không áp dụng) |

**Không được làm:**

- **Thêm nội dung** không có trong bản gốc (giai đoạn 1) hoặc trong bản tiếng Việt (giai đoạn 2): giải thích thêm, ví dụ thêm, ghi chú thêm, mở rộng ý.
- **Xóa nội dung** có trong bản gốc. Chỉ được xóa phần GPT tự thêm vào.
- **Viết lại cho hay hơn** khi câu không sai.
- Sửa `vi`, `ja` hay cấu trúc JSON ở giai đoạn 2.

### 2a-1. Sửa lỗi của lời giải gốc ở giai đoạn 1 (`sua_ban_goc`)

**Được sửa** – chỉ lỗi **rõ ràng, kiểm chứng được**, sửa **ít chữ nhất có thể** tại đúng chỗ sai:

| `nhom` | Ví dụ |
|---|---|
| `chinh_ta` | Lỗi chính tả / gõ nhầm / lặp chữ: "Cố gằng" → "Cố gắng", "hai chữ chữ hán" → "hai chữ hán", "toàn câu" → "toàn cầu" |
| `cach_doc` | Cách đọc (kana) sai: số thứ tự ①②③ bị đọc lẫn vào (`いち{はまべ}…` → `{はまべ}…`), đọc sai chữ (`ちょうむ` → `いどむ`), thiếu đoạn trong dòng cách đọc |
| `kien_thuc` | Sai kiến thức rõ ràng, sửa được bằng cách thay đúng từ / cụm sai: nghĩa sai (人才 "thiên tài" → "nhân tài"), cách đọc ghi sai của từ ví dụ (地形 じぎょう → ちけい), chữ Hán sai (高層 → 高僧) |
| `khac` | Lỗi rõ ràng khác (vd dấu ngoặc thừa, số thứ tự bị chèn nhầm giữa câu) |

**Không được** (chỉ ghi `[Bản gốc VI]` như trước):

- Sửa đòi hỏi **viết nội dung mới** (vd lựa chọn ghi "không tồn tại" nhưng thực ra có tồn tại → phải viết phân tích mới), hoặc sửa cả câu / cả đoạn.
- Sửa **đề bài, lựa chọn, đáp án** (chỉ ghi chú; vd đề có 2 đáp án đúng).
- Sửa khi **không chắc chắn**, hoặc chỉ là cách diễn đạt chưa hay.
- Sửa câu dịch nghĩa chưa sát nhưng không sai rõ ràng.

**Ghi chú bắt buộc** cho mỗi chỗ sửa:

1. Trong file lý do: mục `sua` có `"loai": "sua_ban_goc"`, `"nhom"`, `"muc_do"`, `"ly_do"` (nêu căn cứ: vì sao là lỗi, đúng phải là gì). Python tự điền `truoc` (chữ của bản gốc) và `sau`.
2. Trong `ghi_chu_ban_goc`: một dòng `[Đã sửa bản gốc] <chỗ sửa>: '<cũ>' → '<mới>' – <lý do ngắn>` để nhóm dữ liệu sửa lại nguồn.
3. Lỗi bản gốc **không sửa** vẫn ghi `[Bản gốc VI] …` như trước.

**Python kiểm soát:**

- Kiểm tra "trung thành với bản gốc" (mất tiếng Nhật, độ phủ chữ Việt, furigana, `{ }`) chạy trên bản Claude **đã hoàn lại các chỗ `sua_ban_goc`** về bản GPT – mọi chỗ khác vẫn phải khớp bản gốc; các chỗ `sua_ban_goc` được miễn nhưng liệt kê trong nhật ký.
- Chỗ `sua_ban_goc` đổi quá nhiều chữ (> 50% trường, hoặc > 30 chữ) → CẢNH BÁO "sửa bản gốc quá nhiều, xem có viết lại / thêm nội dung không".
- Có `sua_ban_goc` mà thiếu `nhom` hoặc thiếu ghi chú `[Đã sửa bản gốc]` → CẢNH BÁO.
- Câu có `sua_ban_goc` thuộc **Dạng 2** khi phân loại; file CTV Dạng 2 liệt kê riêng "Claude đã sửa lỗi bản gốc".
- **Phân loại 3 dạng (áp dụng cho mọi dạng bài):** Dạng 1 = GĐ1 Claude không sửa lỗi bản gốc (kể cả khi chỉ sửa lỗi GPT hoặc có ghi chú `[Bản gốc VI]` chưa sửa); Dạng 2 = GĐ1 Claude có sửa lỗi bản gốc; Dạng 3 = GĐ2 còn vấn đề dịch âm Hán Việt (giữ `dang_gd1` = 1/2 để câu tự trở về sau khi dịch lại). Lỗi pipeline khác không xếp dạng, xử lý theo `can_kiem_tra.csv`.
- **Cách chia v2 (thử ở dạng 01 từ 2026-10-01, bật bằng `cach_chia_dang: v2` trong config):** Dạng 1 = lời giải gốc không sai định dạng; Dạng 2 = Claude có sửa định dạng (`sua_dinh_dang`, ghi `[Đã sửa định dạng] <chỗ>: 'cũ' → 'mới' – lý do`). Lỗi nội dung Claude **không sửa** mà gắn cờ `nghi_noi_dung` (ghi rõ vị trí + đề xuất); âm Hán Việt trong bản gốc → cờ `han_viet`. Chỉ câu không có cờ nào mới được dịch. Xem `dang_bai/01_tu_vung_cach_doc_kanji/output_v2/CHU_Y_TRIEN_KHAI.md`.

**Python kiểm soát việc Claude thêm nội dung:**

- **Giai đoạn 1:** so bản Claude đã sửa với lời giải gốc. Nếu tỷ lệ từ thừa **tăng** so với bản của GPT thì báo CẢNH BÁO "Claude có thể đã thêm nội dung", kèm danh sách từ mới xuất hiện.
- **Giai đoạn 2:** trường nào bản `ko` của Claude dài hơn bản của GPT quá 30% thì báo CẢNH BÁO để xem lại.
- Chỗ sửa trong nhật ký thiếu loại, hoặc có loại ngoài 4 loại trên, thì báo CẢNH BÁO.

## 2b. Lưu lại những gì Claude đã sửa

Schema strict không cho thêm trường lạ vào JSON, và JSON cuối cùng còn được đưa lên app. Vì vậy **không ghi lịch sử sửa vào trong file JSON**. Thông tin sửa được lưu ở 3 nơi:

**1. File nhật ký cho từng câu:** `reports/claude_sua/vi/<id>.json` (giai đoạn 1) và `reports/claude_sua/ko/<id>.json` (giai đoạn 2).

```json
{
  "sample_id": "01_kanji_15284_1",
  "giai_doan": 1,
  "so_cho_sua": 1,
  "sua": [
    {
      "stt": 1,
      "duong_dan": "$.options[1].analysis.vi",
      "truoc": "Không tồn tại từ nào có cách đọc",
      "sau": "Không tồn tại từ nào có cách đọc này",
      "loai": "sai_so_ban_goc",
      "muc_do": "nhe",
      "ly_do": "GPT bỏ sót chữ \"này\" so với lời giải gốc"
    }
  ],
  "ghi_chu_ban_goc": [
    "[Bản gốc VI] だまして có tồn tại (騙して – lừa gạt), bản gốc ghi \"Không tồn tại\" là sai"
  ]
}
```

| Trường | Ai điền | Ý nghĩa |
|---|---|---|
| `duong_dan` | **Python** | Vị trí trường bị sửa |
| `truoc`, `sau` | **Python** | Nội dung trước và sau khi sửa |
| `loai` | Claude | Một trong các loại ở mục 2a (`sua_ban_goc` chỉ ở giai đoạn 1) |
| `nhom` | Claude | Chỉ với `sua_ban_goc`: `chinh_ta` / `cach_doc` / `kien_thuc` / `khac` |
| `muc_do` | Claude | `nghiem_trong` / `nang` / `nhe` |
| `ly_do` | Claude | Vì sao sửa, ngắn gọn |
| `ghi_chu_ban_goc` | Claude | `[Bản gốc VI]` – chỗ nghi bản gốc sai, không sửa; `[Đã sửa bản gốc]` – chỗ đã sửa (mục 2a-1) |

**Python tự so bản GPT với bản Claude đã sửa** để điền `duong_dan`, `truoc` và `sau`. Claude chỉ giải thích lý do. Như vậy nhật ký luôn đúng với thay đổi thật, và **không có chỗ sửa nào bị bỏ sót khỏi nhật ký**:

- Chỗ thay đổi không có lý do từ Claude thì báo CẢNH BÁO "Claude sửa nhưng không ghi lý do".
- Claude ghi lý do cho một chỗ không hề thay đổi thì báo CẢNH BÁO.

**2. Cột tóm tắt trong `reports/trang_thai.csv`:** `claude_da_sua_vi` và `claude_da_sua_ko`, mỗi chỗ sửa một dòng, ví dụ:
`$.options[1].analysis.vi (sai_so_ban_goc): "…cách đọc" → "…cách đọc này"`

**3. Cột "Claude đã sửa" trong file Excel gửi CTV** (bước 3.3), để CTV biết chỗ nào đã bị Claude đụng vào.

Dữ liệu này còn dùng để **đo chất lượng của GPT** theo từng dạng bài: số chỗ phải sửa, loại lỗi, mức độ.

## 3. Quy ước trong JSON

| Ký hiệu | Ý nghĩa | Ví dụ |
|---|---|---|
| `{"vi": "..."}` | Trường cần dịch. Khi dịch chỉ thêm khóa ngôn ngữ bên cạnh: `"ko"`, `"zh_tw"` | `{"vi": "Nghĩa là…", "ko": "…"}` |
| `⟪ ⟫` | Tiếng Nhật nằm trong câu tiếng Việt, giữ nguyên, không dịch | `Mẫu ⟪〜につれて⟫ diễn tả…` |
| `{ }` | Phần **gạch chân hoặc in đậm** của lời giải gốc (mục 3a). Chép đúng vị trí, đúng số cặp như bản gốc; bản gốc không có thì không có | `{根}を張る` |
| `｜漢字《かな》` | Furigana: `｜` đánh dấu chỗ bắt đầu chữ gốc, cách đọc trong `《》` (chi tiết ở mục 8) | `｜仕事《しごと》`, `型｜家事《かじ》` |

## 3a. Quy tắc gạch chân / in đậm → `{ }` (áp dụng cho mọi dạng bài)

1. **Trong lời giải gốc, mọi đoạn gạch chân hoặc in đậm đều đổi thành `{ }`**, ở bất kỳ phần nào của lời giải. Các thẻ được tính:
   - gạch chân: `<u>`, `<span style="text-decoration(-line): underline">`;
   - in đậm: `<b>`, `<strong>`, `<span style="font-weight: 700 | bold">`;
   - bản gốc viết sẵn `{ }` hoặc `｛ ｝`.
2. **Không tính nhãn cố định** được in đậm / gạch chân (`<b>PHÂN TÍCH:</b>`, `<b>Câu hỏi:</b>`…): chỉ bỏ thẻ.
3. **Đoạn đánh dấu liền nhau** (chỉ cách khoảng trắng, hoặc lồng nhau như `<u><b>…</b></u>`) gộp thành một cặp.
4. **Đoạn đánh dấu rỗng hoặc chỉ gồm dấu câu / khoảng trắng** (vd `<u>.</u>`): bỏ thẻ, không tạo `{ }`, ghi vào `reports/danh_dau_rac.csv`.
5. **Không tự thêm, không lấy từ đề:** đề chỉ để tham khảo; `{ }` chỉ theo lời giải. Một dòng có mấy đoạn đánh dấu thì có mấy cặp.
6. Code (bước 0.3) làm việc chuyển đổi này; GPT và Claude chỉ chép nguyên `{ }` vào đúng trường, không tự thêm, không bỏ.
7. Khi dịch: số cặp `{ }` của mỗi trường giữ đúng như tiếng Việt, bọc phần dịch tương ứng. Excel cho CTV hiển thị `{ }` bằng in đậm.

Schema dùng chế độ strict (`additionalProperties: false`), nên **không ghi trạng thái hay ghi chú vào trong file JSON**. Những thông tin đó nằm ở file theo dõi (mục 7) và nhật ký.

## 4. Giai đoạn 0: Chuẩn bị (Python)

| Bước | Việc | Đầu ra |
|---|---|---|
| 0.1 | Chọn model GPT (xem danh sách bằng `--list-models`) và điền vào `config.json` | `config.json` |
| 0.2 | Chọn mẫu (pilot) hoặc lấy toàn bộ câu của dạng bài | `samples/samples.csv`, `samples/raw/` |
| 0.3 | **Chuẩn hóa gạch chân / in đậm** thành `{ }` (mục 3a) và **furigana:** đổi mọi thẻ `<ruby>` trong lời giải gốc thành `｜chữ gốc《cách đọc》` (mục 8). Lập danh sách cặp (chữ gốc, cách đọc) làm chuẩn so sánh. Ghi lại ruby hỏng và các câu có cách đọc viết trong ngoặc | `samples/norm/<id>.json`, `reports/ruby_hong_ban_goc.csv`, `reports/doc_trong_ngoac.csv`, `reports/danh_dau_rac.csv` |

## 5. Giai đoạn 1: Chuyển sang JSON tiếng Việt

| Bước | Ai | Việc | Đầu ra |
|---|---|---|---|
| 1.1 | **GPT** | Chuyển lời giải **đã chuẩn hóa** sang JSON tiếng Việt, bắt buộc đầu ra theo schema (strict). Prompt gồm hướng dẫn chuyển, schema và ví dụ mẫu của dạng | `json_vi/gpt/<id>.json` |
| 1.2 | **Claude** | **Kiểm tra JSON so với lời giải gốc và sửa lỗi** (checklist bên dưới). Ghi nhật ký sửa | `json_vi/checked/<id>.json`, `reports/claude_sua/vi/<id>.json` |
| 1.3 | **Python** | Kiểm tra lần cuối (checklist bên dưới) | `reports/validate_vi.json` |
| 1.4 | Python | Có **LỖI** thì gắn `LỖI_GĐ1` kèm danh sách lỗi và **dừng, không sang giai đoạn 2**. Chỉ **CẢNH BÁO** thì đi tiếp, cảnh báo được đưa vào cột "Điểm cần chú ý" | `reports/trang_thai.csv` |
| 1.5 | **Bạn** | Duyệt các câu không lỗi | `json_vi/final/<id>.json` |

**Claude kiểm tra ở bước 1.2**

> **Nhiệm vụ:** kiểm tra JSON tiếng Việt **so với lời giải gốc** và sửa lỗi. Chuẩn so sánh duy nhất là lời giải gốc (đã chuẩn hóa furigana): JSON phải thể hiện **đúng và đủ** lời giải gốc, không hơn, không kém. Claude không đánh giá lời giải gốc hay hay dở, đúng hay sai về kiến thức.

Các điểm cần kiểm tra:

- Nội dung đặt đúng trường không, ví dụ phân tích của lựa chọn 3 có bị đưa sang lựa chọn 2 không.
- Có thiếu ý, thừa ý hay bị viết lại so với bản gốc không.
- Tiếng Nhật được tách đúng không; phần tiếng Nhật trong câu tiếng Việt có được bọc `⟪ ⟫` không.
- `{ }` có đúng số cặp và đúng vị trí như chỗ gạch chân / in đậm của lời giải gốc không (mục 3a); GPT tự thêm hoặc bỏ thì sửa lại.
- **Furigana `｜…《…》` khớp với bản gốc:** chỗ nào lời giải gốc **có** furigana thì JSON phải có đúng furigana đó, đúng chữ gốc, có `｜`, nằm bên trong `⟪ ⟫` hoặc `{ }` nếu có; GPT làm mất thì khôi phục lại. Chỗ nào bản gốc **không có** furigana thì JSON cũng **không có**; GPT tự thêm thì xóa đi.
- Chỗ nghi bản gốc sai (sai chữ Hán, sai cách đọc, ghi "không tồn tại" sai…) thì **không sửa**, chỉ ghi `[Bản gốc VI]`.
- Mỗi chỗ sửa ghi: trường, nội dung trước, nội dung sau, **loại** (theo mục 2a), lý do, mức độ (nghiêm trọng / nặng / nhẹ).
- **Chỉ sửa lỗi, không thêm nội dung** (mục 2a).

**Python kiểm tra ở bước 1.3** (lỗi nào cũng là **LỖI**, trừ các mục ghi CẢNH BÁO):

1. File parse được và khớp schema.
2. `question_id`, `cau_con`, `correct.index` trùng dữ liệu gốc. `correct.option_ja` khác lựa chọn gốc là CẢNH BÁO.
3. Không mất đoạn tiếng Nhật nào so với bản gốc.
4. Độ phủ chữ Việt ≥ 97% (bỏ nhãn cố định và từ khung). Từ thừa > 5% là CẢNH BÁO. Trường `vi` không được để trống.
5. `{ }`: danh sách đoạn trong `{ }` của JSON trùng với danh sách đoạn gạch chân / in đậm của lời giải gốc đã chuẩn hóa (mục 3a), cả số lượng lẫn nội dung, theo thứ tự; dấu `{` `}` cân bằng, không lồng nhau.
6. `⟪ ⟫`: số dấu mở bằng số dấu đóng; bên trong phải có tiếng Nhật. Còn tiếng Nhật chưa bọc là CẢNH BÁO.
7. **Furigana:** danh sách cặp (chữ gốc, cách đọc) trong JSON phải trùng hoàn toàn với danh sách từ bản gốc đã chuẩn hóa, cả về số lượng lẫn nội dung. Không có `《》` nào thiếu `｜`, không có `｜` nào không đi kèm `《》`. Ruby hỏng trong bản gốc và phần trùng lặp đã khai báo (quy tắc 8 ở mục 8) không tính. So từng cặp theo thứ tự xuất hiện, để bắt cả trường hợp furigana bị chuyển sang chỗ khác.

## 6. Giai đoạn 2: Dịch sang tiếng Hàn

Chỉ xử lý các câu có trong `json_vi/final/` và không bị `LỖI_GĐ1`.

**GPT không chép lại JSON.** GPT nhận toàn bộ JSON làm ngữ cảnh, nhưng chỉ trả về bản dịch của các trường cần dịch. Python lo việc tách trường và ghép lại (cơ chế chi tiết ở mục 6a).

| Bước | Ai | Việc | Đầu ra |
|---|---|---|---|
| 2.1 | Python | **Tách trường cần dịch:** gán mã `f1…fn` cho mọi trường `vi` theo thứ tự xuất hiện; lập bảng đối chiếu mã → đường dẫn → nội dung `vi`; tạo bản gửi GPT (bản sao JSON có mã gắn tại chỗ) và schema output riêng cho câu đó | `json_ko/gpt/<id>.map.json`, `json_ko/gpt/<id>.request.json` |
| 2.2 | **GPT** | Đọc ngữ cảnh (đề bài, các lựa chọn, đáp án, JSON có mã), **chỉ trả về** `{"f1": "…", …}` theo hướng dẫn dịch và bảng thuật ngữ. Schema strict buộc đủ mọi mã, không cho mã lạ | `json_ko/gpt/<id>.output.json` |
| 2.3 | Python | **Ghép lại:** với mỗi mã, đi theo đường dẫn, kiểm tra `vi` ở đó khớp với bảng, rồi ghi `ko` bên cạnh `vi`. Không khớp, thiếu hoặc thừa mã thì báo **LỖI** | `json_ko/gpt/<id>.json` |
| 2.4 | **Claude** | **Kiểm tra bản dịch có đúng với ngữ cảnh không và sửa lỗi** (checklist bên dưới), xem theo bảng Mã / Vị trí / Tiếng Việt / Tiếng Hàn. Ghi nhật ký sửa | `json_ko/checked/<id>.json`, `reports/claude_sua/ko/<id>.json` |
| 2.5 | **Python** | Kiểm tra lần cuối (checklist bên dưới) | `reports/check_ko.json` |
| 2.6 | Python | Có **LỖI** (ở bước 2.3 hoặc 2.5) thì gắn `LỖI_GĐ2` kèm danh sách lỗi. Không lỗi thì gắn `ĐẠT` và chép sang bản cuối | `reports/trang_thai.csv`, `json_ko/final/<id>.json` |

**Claude kiểm tra ở bước 2.4**

> **Nhiệm vụ:** kiểm tra bản dịch **có đúng với ngữ cảnh không** và sửa lỗi. Ngữ cảnh gồm: đề bài, các lựa chọn, đáp án, phần tiếng Nhật trong JSON (câu ví dụ, cách đọc, từ đang hỏi) và bản tiếng Việt của **cả lời giải**. Một câu dịch có thể đúng khi đứng riêng nhưng sai khi đặt vào vị trí của nó. Claude phải xét từng trường trong đúng vị trí đó.

Các điểm cần kiểm tra theo ngữ cảnh:

- **Nghĩa từ khớp với câu ví dụ:** nghĩa tiếng Hàn của từ (`word.meaning`) phải là nghĩa được dùng trong câu tiếng Nhật của đề, không phải một nghĩa khác của từ đó.
- **Bản dịch câu ví dụ khớp với câu tiếng Nhật:** `question.meaning` dịch đúng câu `ja` bên cạnh, và `{ }` bọc đúng phần tương ứng với chỗ gạch chân.
- **Phân tích khớp với lựa chọn của nó:** bản dịch `options[i].analysis` nói đúng về lựa chọn `option_ja` đó, và đúng kết luận đúng/sai theo đáp án.
- **Nhất quán trong toàn bộ lời giải:** cùng một khái niệm hoặc từ tiếng Nhật được gọi bằng cùng một thuật ngữ tiếng Hàn ở mọi trường.
- **Phù hợp người học Hàn Quốc:** thuật ngữ ngữ pháp tiếng Nhật theo cách người Hàn quen dùng (theo bảng thuật ngữ).

Các điểm cần kiểm tra về câu chữ:

- Dịch đúng nghĩa, không thiếu, không thừa so với tiếng Việt.
- Thuật ngữ ngữ pháp và từ vựng đúng, theo bảng thuật ngữ; **nhất quán giữa các trường** trong cùng một câu.
- Câu tự nhiên với người Hàn; phần giải thích dùng văn phong -습니다/-ㅂ니다.
- Giữ nguyên `⟪ ⟫`, `{ }` (bọc đúng phần tương ứng) và furigana `｜…《…》`.
- Chỗ bản tiếng Việt dùng ví dụ riêng của Việt Nam (như giải thích お年玉 bằng Tết) thì chuyển cho phù hợp, và ghi nhãn `[Khi dịch]`.
- Không "sửa" bản dịch cho đúng khi bản tiếng Việt sai. Chỉ ghi `[Bản gốc VI]`.
- Claude chỉ sửa **nội dung** `ko`, không sửa `vi`, `ja` hay cấu trúc JSON.
- **Chỉ sửa lỗi, không thêm nội dung.** Mỗi chỗ sửa ghi loại theo mục 2a.

**Python kiểm tra ở bước 2.5:**

1. Khớp schema; mọi trường `vi` đều có `ko` và không để trống.
2. **Các phần không phải `ko` giống hệt `json_vi/final`**: `vi`, `ja`, `reading`, số thứ tự, cấu trúc. Nhờ vậy bảo đảm GPT hoặc Claude không vô tình làm thay đổi.
3. Không còn chữ tiếng Việt trong `ko`.
4. `⟪ ⟫`: nội dung bên trong giống bản tiếng Việt (được đổi thứ tự). Không có tiếng Nhật nằm ngoài `⟪ ⟫`.
5. `{ }`: số cặp giống bản tiếng Việt.
6. **Furigana:** danh sách cặp `｜chữ gốc《cách đọc》` trong `ko` giống hệt trong `vi`.
7. Tỷ lệ độ dài KO/VI trong khoảng [0,3; 1,5], ngoài khoảng là CẢNH BÁO. Văn phong -습니다 ở các trường giải thích, sai là CẢNH BÁO.

## 6a. Cơ chế tách và ghép trường dịch

**Nguyên tắc:** GPT chỉ thấy **mã ngắn**, Python giữ **đường dẫn chính xác**. Hai thứ nối với nhau qua bảng đối chiếu `<id>.map.json`, GPT không đụng vào.

**Ví dụ thật:** câu 15284 (Cách đọc kanji).

**Bước 2.1: bảng đối chiếu Python tạo ra**

| Mã | Đường dẫn | Nội dung `vi` |
|---|---|---|
| f1 | `$.word.meaning` | khuyến khích; động viên; khích lệ |
| f2 | `$.question.meaning` | Các đồng đội đã {khích lệ} tôi thực hiện hoài bão của mình. |
| f3 | `$.options[0].analysis` | Không tồn tại từ nào có cách đọc này |
| f4 | `$.options[1].analysis` | Không tồn tại từ nào có cách đọc này |
| f5 | `$.options[2].analysis` | Không tồn tại từ nào có cách đọc này |
| f6 | `$.reference` | "⟪励ます⟫" (⟪はげます⟫) là một động từ… |

Cách đọc đường dẫn `$.options[1].analysis`:

- `$` là gốc của file.
- `.options` là vào khóa `options`.
- `[1]` là **phần tử thứ 2** trong danh sách (đếm từ 0), tức lựa chọn 2, だまして.
- `.analysis` là vào khóa `analysis` của lựa chọn đó.

Trường có giá trị `null` (ví dụ `options[3].analysis`) không được gán mã.

**Bước 2.1: bản gửi GPT, mã gắn ngay tại chỗ**

```json
"options": [
  {"index": 1, "option_ja": "みまして", "analysis": {"id": "f3", "vi": "Không tồn tại từ nào có cách đọc này"}},
  {"index": 2, "option_ja": "だまして", "analysis": {"id": "f4", "vi": "Không tồn tại từ nào có cách đọc này"}}
]
```

Kèm theo là schema output: đúng các khóa `f1…f6`, khóa nào cũng bắt buộc, `additionalProperties: false`.

**Bước 2.2: GPT chỉ trả về bản dịch**

```json
{"f1": "격려하다; 응원하다; 북돋우다", "f2": "동료들이 제가 야망을 이루도록 {격려해} 주었습니다.",
 "f3": "이 읽기를 가진 단어는 존재하지 않습니다.", "f4": "…", "f5": "…", "f6": "…"}
```

**Bước 2.3: Python ghép, ví dụ với f4**

1. Tra bảng: f4 → `$.options[1].analysis`.
2. Đi theo đường dẫn trong `json_vi/final`.
3. So `vi` ở đó với nội dung đã lưu trong bảng: khớp.
4. Ghi `"ko"` bên cạnh `"vi"`.
5. Làm hết các mã, rồi đếm lại: số trường có `ko` phải bằng đúng số mã.

**Python báo LỖI khi:**

- Đường dẫn không còn tồn tại.
- `vi` tại đường dẫn khác với bảng. Ví dụ bản tiếng Việt đã bị sửa sau khi tạo bảng; nhờ vậy bản dịch cũ không bị gắn nhầm vào nội dung mới.
- Output thiếu mã, thừa mã, hoặc có bản dịch rỗng.

**Vì sao làm như vậy:**

- **Ghép theo đường dẫn, không theo nội dung chữ.** Cùng một câu có thể lặp lại nhiều lần; ví dụ trên có f3, f4, f5 giống hệt nhau.
- **GPT không thể làm hỏng tiếng Nhật và cấu trúc JSON,** vì nó không phải chép lại.
- **Output ngắn hơn, nên rẻ hơn.**
- **Mã gắn tại chỗ** nên GPT không phải dò xem mã nào ứng với phần nào; vẫn đủ ngữ cảnh để dịch đúng và nhất quán.
- **Dịch lại một phần:** chỉ gửi các mã bị lỗi, dùng lại bảng cũ để ghép.
- Giai đoạn 1 **không** áp dụng được cơ chế này, vì ở đó GPT phải tạo ra chính cấu trúc JSON.

## 7. Giai đoạn 3: Gửi CTV

| Bước | Việc | Đầu ra |
|---|---|---|
| 3.1 | Xuất Excel đúng định dạng 17 cột CTV đã quen dùng. Furigana hiển thị dạng `漢字《かな》` (code ẩn `｜`), `{ }` (gạch chân / in đậm của bản gốc) hiển thị in đậm | `reports/ctv/<ngày>-CTV-<tên>.xlsx` |
| 3.2 | Cột **"Điểm cần chú ý"** gom từ các nguồn, ghi nhãn: `[Kiểm tra tự động]`, `[Claude – JSON VI]`, `[Claude – Dịch]`, `[Bản gốc VI]`, `[Khi dịch]` | |
| 3.3 | Cột **"Claude đã sửa"** (cột mới, chỉ để tham khảo): liệt kê các chỗ Claude đã sửa trong bản dịch, dạng `vị trí (loại): "trước" → "sau"`, để CTV xem kỹ các chỗ này | |
| 3.4 | CTV đánh giá (Đạt / Sửa nhỏ / Không đạt), rồi đưa kết quả vào báo cáo | báo cáo so sánh |

> **Chưa chốt:** câu `LỖI_GĐ2` có đưa vào file CTV không. Đề xuất: không đưa vào sheet chính, để ở một sheet riêng cho bạn xem.

### File theo dõi trạng thái: `reports/trang_thai.csv`

Mỗi câu một dòng, dùng để xem tiến độ và lọc câu cho giai đoạn sau.

| Cột | Ý nghĩa |
|---|---|
| `sample_id`, `dang_bai`, `cap_do` | Định danh |
| `trang_thai` | `ĐANG_XỬ_LÝ` / `LỖI_GĐ1` / `LỖI_GĐ2` / `ĐẠT` |
| `giai_doan_loi` | 1 hoặc 2 |
| `loi` | Danh sách lỗi Python |
| `canh_bao` | Danh sách cảnh báo |
| `so_cho_claude_sua_vi`, `so_cho_claude_sua_ko` | Số chỗ Claude đã sửa, dùng để đo chất lượng của GPT |
| `claude_da_sua_vi`, `claude_da_sua_ko` | **Tóm tắt những gì Claude đã sửa**, mỗi chỗ một dòng: `đường dẫn (loại): "trước" → "sau"`. Chi tiết đầy đủ ở `reports/claude_sua/` (mục 2b) |
| `ghi_chu_ban_goc` | Chỗ nghi bản gốc sai |


**Danh sách cần người xem: `reports/can_kiem_tra.csv`** – tạo lại tự động mỗi lần lưu `trang_thai.csv`. Nhóm 1: lỗi pipeline (`LỖI_KỸ_THUẬT`, `LỖI_GĐ1`, `CẦN_SỬA_GĐ1`, `LỖI_GĐ2`); nhóm 2: chờ bạn duyệt GĐ1; nhóm 3: đã chạy được nhưng có ghi chú `[Bản gốc VI]`. Mỗi dòng có việc cần làm, lỗi, cảnh báo.

## 8. Quy tắc furigana

**Hiện trạng dữ liệu** (quét ngày 2026-09-27):

- 6.960/18.630 dòng có thẻ `<ruby>`, tổng khoảng 226.000 chỗ.
- Biến thể:
  - có `<rp>`: 154 chỗ;
  - có thuộc tính như `<rt style="">`: 31 chỗ;
  - có thẻ khác lồng bên trong (`<span>`, `<b>`…): 896 chỗ;
  - ruby hỏng: 265 chỗ có furigana mà không có chữ Hán, cùng một số chỗ lồng sai.

**Nguyên tắc chung (áp dụng cho mọi dạng bài): lời giải gốc có furigana ở đâu thì JSON có furigana ở đúng chỗ đó.**

- Furigana đi theo **chữ** mà nó gắn vào. Đoạn chữ đó được đưa vào trường JSON nào (`ja`, `option_ja`, `terms`, ví dụ, hay `⟪ ⟫` trong câu tiếng Việt) thì furigana đi theo vào trường đó, đúng vị trí, đúng chữ gốc.
- Chỗ bản gốc **không có** furigana thì JSON **không có**, kể cả khi cùng một từ ở chỗ khác có furigana.
- **Không lấy furigana từ nơi khác:** không lấy từ đề, lựa chọn, dòng cách đọc hay từ điển để thêm vào; đề và lựa chọn chỉ dùng để xác định vị trí `{ }` hoặc lựa chọn nào (so sánh sau khi bỏ furigana).
- **Không đổi furigana thành trường khác:** không chuyển furigana thành `reading` hay tách ra một trường riêng. Trường `reading` chỉ lấy từ dòng cách đọc riêng mà bản gốc viết ra.

**Quy tắc:**

1. **Chỉ một cách ghi furigana:** `｜chữ gốc《cách đọc》`, theo quy ước ruby của Aozora Bunko.
   - **Luôn** viết `｜` trước chữ được gắn furigana, kể cả khi không dễ nhầm.
   - Chữ gốc là phần nằm giữa `｜` và `《`. Cách đọc nằm trong `《》` và chỉ gồm kana.
   - Không lồng nhau.
   - `｜` (U+FF5C) và `《》` chỉ dùng cho furigana, không dùng vào việc khác. Quét dữ liệu gốc: không dòng nào có `｜`. Có **1 dòng (câu 12726)** dùng `《 》` làm ngoặc trích dẫn tên sự kiện. Code chuẩn hóa không coi đó là furigana, mà ghi câu này vào `ruby_hong_ban_goc.csv` để nhóm đổi sang `『 』` trong dữ liệu gốc.
2. **Code chuẩn hóa** mọi thẻ ruby về dạng trên ở bước 0.3, gồm đủ các biến thể `<rp>`, `<rt style="">`, thẻ lồng bên trong. GPT không phải tự xử lý HTML.
3. **GPT và Claude chép nguyên** cả `｜`, chữ gốc và cách đọc: không thêm, không bớt, không sửa, không tách hay gộp chữ gốc. Chỗ bản gốc không có furigana thì không thêm. Cách đọc nghi sai thì ghi `[Bản gốc VI]`.
4. **Kết hợp với các ký hiệu khác:** furigana luôn nằm **bên trong** `⟪ ⟫` và `{ }`. Ví dụ: `⟪｜根《ね》⟫`, `{｜医者《いしゃ》}`.
5. **Cách đọc mà bản gốc viết thành chữ trong ngoặc**, như `六本木坂（ろっぽんぎざか）` (125 dòng), là nội dung của lời giải. Giữ nguyên, **không** đổi sang `《》`. Python xuất danh sách những câu này vào `reports/doc_trong_ngoac.csv` để nhóm xem; nếu muốn đổi thành furigana thì sửa từ dữ liệu gốc.
6. **Ruby hỏng trong bản gốc** (có cách đọc mà không có chữ gốc, lồng sai): không đổi sang `《》`, giữ phần chữ như bản gốc. Câu **không** bị tính lỗi. Những chỗ này được ghi vào `reports/ruby_hong_ban_goc.csv` để nhóm sửa dữ liệu gốc.
7. **Hiển thị trong Excel cho CTV:** code ẩn `｜`, nên CTV thấy `漢字《かな》` như cách vẫn đọc.
8. **Phần trùng lặp trong bản gốc:** nếu một đoạn có furigana được đưa vào JSON dưới dạng bản sao của trường khác (VD `correct.option_ja` chép từ `option_ja`, trong khi bản gốc có mục LỰA CHỌN ĐÚNG lặp lại), workflow chi tiết phải ghi rõ trường và mục đó. Check furigana bỏ qua trường bản sao ở JSON và mục tương ứng ở bản gốc, để không bị tính thừa hoặc thiếu cặp.
9. **Workflow chi tiết của mỗi dạng** phải có mục **Furigana** gồm: thống kê furigana xuất hiện ở những phần nào của lời giải (quét bằng code), phần đó vào trường JSON nào, các trường hợp đặc biệt (gạch chân trong ruby, ruby hỏng, phần trùng lặp). Pilot phải có ít nhất 2–3 câu có furigana nếu dạng đó có.
10. **Đưa lên app:** code đổi `｜A《b》` → `<ruby>A<rt>b</rt></ruby>`. **Cần xác nhận với dev** định dạng app đang dùng.

**Ví dụ** (lấy từ dữ liệu thật, số là `question_id`):

| # | Trường hợp | Bản gốc (HTML) | JSON |
|---|---|---|---|
| 1 | Cả một từ (9) | `<ruby>重要<rt>じゅうよう</rt></ruby>なキーワード` | `｜重要《じゅうよう》なキーワード` |
| 2 | Chữ Hán có kana theo sau (3662) | `<ruby>思<rt>おも</rt></ruby>いをする` | `｜思《おも》いをする` |
| 3 | Phía trước có chữ Hán không có furigana (31) | `型<ruby>家事<rt>かじ</rt></ruby>` | `型｜家事《かじ》` |
| 4 | Chữ gốc không phải chữ Hán (19913) | `2<ruby>ヶ<rt>か</rt></ruby>月` | `2｜ヶ《か》月` |
| 5 | Có `<rp>`, `<span>` (54689) | `<ruby><span lang="JA">男</span><rp>(</rp><rt>おとこ</rt><rp>)</rp></ruby>` | `｜男《おとこ》` |
| 6 | Có thuộc tính (121) | `<ruby contenteditable="true" style="">笑<rt style="">わら</rt></ruby>い` | `｜笑《わら》い` |
| 7 | Trong phần gạch chân (9242) | `<u><ruby>医者<rt>いしゃ</rt></ruby></u>` | `{｜医者《いしゃ》}` (không viết `｜{医者}《いしゃ》`) |
| 8 | Trong câu tiếng Việt | … `<ruby>根<rt>ね</rt></ruby>` … | `Ở đây ⟪｜根《ね》⟫ đọc theo âm Kun.` |
| 9 | Cách đọc viết trong ngoặc (1291) | `六本木坂（ろっぽんぎざか）` | Giữ nguyên `六本木坂（ろっぽんぎざか）` |
| 10 | Ruby hỏng (3806) | `<ruby><rt>しゃかい</rt></ruby>` | Giữ `しゃかい` dạng chữ, ghi vào `ruby_hong_ban_goc.csv` |

Vì sao cần `｜` (ví dụ 3): nếu viết `型家事《かじ》`, code không biết furigana bắt đầu từ 型 hay 家, nên có thể đặt かじ lên cả 型家事.

**Python bắt lỗi thế nào** (bản gốc câu 9 có cặp `(重要, じゅうよう)`):

| JSON trả về | Kết quả |
|---|---|
| `｜重要《じゅうよう》なキーワード` | Khớp → ĐẠT |
| `重要なキーワード` | Mất 1 cặp → **LỖI** |
| `｜重要《じゅよう》なキーワード` | Sửa cách đọc → **LỖI** |
| `｜重《じゅう》｜要《よう》なキーワード` | Tách sai chữ gốc → **LỖI** |
| `重要《じゅうよう》なキーワード` (thiếu `｜`) | Sai cách ghi → **LỖI** |
| `｜仲間《なかま》達が…` ở chỗ bản gốc không có | Tự thêm → **LỖI** |

## 9. Cấu trúc thư mục (dự kiến)

```
<thư mục dự án>/
├── config.json
├── instructions/          ← prompt chuyển JSON, prompt dịch, checklist cho Claude, bảng thuật ngữ
├── samples/raw/           ← dữ liệu gốc từng câu
├── samples/norm/          ← dữ liệu đã chuẩn hóa furigana
├── json_vi/gpt|checked|final/
├── json_ko/gpt/            ← <id>.map.json, <id>.request.json, <id>.output.json, <id>.json (đã ghép)
├── json_ko/checked|final/
└── reports/
    ├── trang_thai.csv
    ├── validate_vi.json, check_ko.json
    ├── claude_sua/vi/<id>.json, claude_sua/ko/<id>.json   ← nhật ký Claude đã sửa (mục 2b)
    ├── ruby_hong_ban_goc.csv, doc_trong_ngoac.csv
    └── ctv/
```

## 10. Khung workflow chi tiết cho từng dạng bài

21 dạng dùng 10 schema. Có thể viết theo từng nhóm schema, rồi ghi phần khác biệt cho từng dạng. Mỗi file chi tiết gồm:

1. **Thông tin dạng:** tên, số câu, các cấp độ, khuôn lời giải gốc (A–G), schema dùng.
2. **Đầu vào:** các cột CSV cần dùng (`cau_hoi`, `lua_chon_1–4`, `doan_van`…).
3. **Quy tắc chuyển riêng:** phần nào của bản gốc vào trường JSON nào, kèm ví dụ mẫu.
3a. **Furigana:** furigana xuất hiện ở đâu trong lời giải gốc, vào trường JSON nào, trường hợp đặc biệt (mục 8, quy tắc 9).
4. **Claude kiểm tra JSON:** các điểm riêng.
5. **Python kiểm tra JSON:** các check thêm ngoài mục 5.
6. **Quy tắc dịch riêng:** thuật ngữ, trường giữ nguyên.
7. **Claude kiểm tra bản dịch:** các điểm riêng.
8. **Python kiểm tra bản dịch:** các check thêm ngoài mục 6.
9. **Hiển thị trong Excel cho CTV.**
10. **Mẫu test và tiêu chí đạt.**

Thứ tự đề xuất: bắt đầu với 5 dạng đã chạy pilot (Cách đọc kanji, Thay đổi cách nói, Cách viết từ, Điền từ theo văn cảnh, Hình thành từ).

## 11. Việc còn mở

- [ ] Chọn model GPT; kiểm tra gateway có hỗ trợ `json_schema` strict, Batch API và `temperature` không.
- [ ] Kiểm tra giới hạn số trường của schema strict với bài có nhiều trường dịch (bài đọc dài). Nếu vượt, output dùng dạng mảng `[{"id", "ko"}]` và Python kiểm tra đủ mã.
- [ ] Chốt cách xử lý câu `LỖI_GĐ2` trong file gửi CTV.
- [ ] Xác nhận với dev định dạng furigana trên app.
- [ ] Claude Cowork chỉ phù hợp cho pilot. Khi chạy 18.630 câu, cần chọn giữa dùng Claude qua API, hoặc để Claude chỉ kiểm tra câu có cảnh báo cộng một phần mẫu ngẫu nhiên.
- [ ] Ước tính lại chi phí từ số token thật của pilot, rồi cập nhật báo cáo cho Leader.
- [ ] Cập nhật code theo workflow này: tách và ghép trường dịch (bước 2.1, 2.3), chuẩn hóa ruby, `trang_thai.csv`, nhật ký sửa, check furigana, sửa lỗi nhận `<rt style="">`; `normalize.py` đổi `<b>`, `<strong>`, span font-weight / underline → `{ }` theo mục 3a (hiện mới nhận `<u>`).

## 12. Lịch sử thay đổi

| Ngày | Thay đổi |
|---|---|
| 2026-10-01 | Thêm cách chia dạng v2 (thử ở dạng 01): Dạng 1/2 theo lỗi định dạng; cờ `nghi_noi_dung`, `han_viet`; chỉ dịch câu không cờ |
| 2026-09-29 | Mục 2a-1: Claude được sửa lỗi có sẵn trong lời giải gốc ở giai đoạn 1 (loại `sua_ban_goc`: chính tả, cách đọc, kiến thức rõ ràng), bắt buộc ghi `nhom`, lý do và ghi chú `[Đã sửa bản gốc]`; Python kiểm tra trung thành trên bản đã hoàn lại các chỗ này; câu có sửa bản gốc thuộc Dạng 2 |
| 2026-09-28 (2) | Thêm mục 3a: mọi đoạn gạch chân **hoặc in đậm** trong lời giải gốc (`<u>`, `<b>`, `<strong>`, span underline / font-weight) đều đổi thành `{ }`, ở mọi phần của lời giải; bỏ nhãn cố định và đánh dấu rác; không lấy từ đề; bỏ giới hạn 1 cặp mỗi câu; kiểm tra số 5 so theo danh sách đoạn đánh dấu |
| 2026-09-28 | Mục 8: thêm nguyên tắc chung "lời giải gốc có furigana ở đâu thì JSON có ở đúng chỗ đó" (không lấy từ đề, không đổi thành `reading`); quy tắc 8 phần trùng lặp; quy tắc 9 mỗi workflow chi tiết phải có mục Furigana; check furigana so theo thứ tự; thêm mục 3a vào khung workflow chi tiết (mục 10) |
| 2026-09-27 (7) | Thống nhất cách ghi furigana: luôn dùng `｜chữ gốc《cách đọc》` (quy ước Aozora Bunko); furigana nằm bên trong `⟪ ⟫`/`{ }`; Excel ẩn `｜`; thêm ví dụ thật và bảng lỗi Python ở mục 8; xuất `doc_trong_ngoac.csv` |
| 2026-09-27 (6) | Sửa checklist furigana ở bước 1.2: chỉ khôi phục furigana ở chỗ bản gốc có; chỗ bản gốc không có thì không thêm (GPT tự thêm thì xóa) |
| 2026-09-27 (5) | Làm rõ nhiệm vụ của Claude: giai đoạn 1 kiểm tra so với lời giải gốc và sửa lỗi; giai đoạn 2 kiểm tra bản dịch có đúng với ngữ cảnh không và sửa lỗi; thêm các điểm kiểm tra theo ngữ cảnh |
| 2026-09-27 (4) | Thêm mục 2b: nhật ký "Claude đã sửa" cho từng câu (Python điền trước/sau, Claude điền loại và lý do); cột `claude_da_sua_vi/ko` trong `trang_thai.csv`; cột "Claude đã sửa" trong file Excel CTV |
| 2026-09-27 (3) | Thêm mục 2a: Claude chỉ sửa lỗi (lệch bản gốc, chính tả, lỗi khách quan, lỗi chủ quan), không thêm nội dung; nhật ký sửa phải ghi loại; Python cảnh báo nếu Claude có dấu hiệu thêm nội dung |
| 2026-09-27 (2) | Giai đoạn 2: GPT nhận cả JSON làm ngữ cảnh nhưng chỉ trả về bản dịch theo mã; Python tách trường (mã ↔ đường dẫn) và ghép lại có kiểm tra khớp nội dung; thêm mục 6a và kiểm tra "phần không phải ko giữ nguyên" |
| 2026-09-27 | GPT chuyển JSON và dịch; Claude kiểm tra và sửa trực tiếp; Python kiểm tra lần cuối ở mỗi giai đoạn; lỗi Python gắn trạng thái (lỗi ở giai đoạn 1 thì dừng); giữ furigana dạng `《》`, do code chuẩn hóa từ thẻ ruby |
