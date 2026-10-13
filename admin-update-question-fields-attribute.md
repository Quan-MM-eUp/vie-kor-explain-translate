# 3 API admin quản lý câu hỏi — bảng & luồng xử lý

---

## 1. Thông tin 3 bảng

### Bảng `questions` — ngân hàng câu hỏi chính (~37K dòng)

1 dòng = 1 **câu to**; mỗi phần tử trong `content[]` = 1 **câu con** (đơn vị user nhìn thấy). Các cột sửa được qua `update-fields`:

| Nhóm | Cột | Ý nghĩa |
|---|---|---|
| Nội dung | `title`, `title_trans` | Tiêu đề / đề bài (tiếng Nhật) và bản dịch |
| | `general` | Thông tin chung (JSON: đoạn văn gốc `txt_read`, ảnh, audio, bản dịch `text_read_*`) |
| | `content` | Các câu con + đáp án + giải thích đa ngôn ngữ (JSON) |
| | `correct_answers` | Đáp án đúng (JSON array, index tính từ 0) |
| Phân loại | `level` | Level JLPT: 1=N1 … 5=N5 (số nhỏ = khó hơn) |
| | `kind`, `tag`, `source` | Dạng bài (tiếng Việt lowercase), tag, nguồn |
| | `count_question`, `score` | Số câu con, điểm |
| Duyệt | `check_admin` | 0 chưa duyệt / 1 đã duyệt — **chỉ câu = 1 mới vào luyện tập** |
| | `check_explain` | 0/1 — đã có giải thích đầy đủ chưa |
| Độ khó | `score_difficult` | Điểm độ khó, dùng sắp xếp & recommend |
| | `level_of_difficult`, `irt_difficulty_level`, `label` | Độ khó chi tiết (legacy), độ khó IRT (NULL = chưa đánh giá), nhãn 1 very easy … 5 very hard |

Cột JSON (`general`, `content`, `correct_answers`) phải gửi dạng **chuỗi JSON đã stringify**, không gửi object/mảng.

**Không sửa qua API**: `id` (PK), `created_at`, `updated_at` (tự đổi), `status` (workflow 9 bước, admin PHP quản lý), `mazii`, `check_change`, `note`, `theory`, `admin`, `qrcode_link`, `source_import`.

### Bảng `questions_attribute` — giải thích mới, tách ra từ giải thích cũ trong `questions`

Chứa các dạng giải thích **mới**, được tách ra từ giải thích cũ nằm trong `questions` (`content[i].explainAll`). **Hiện tại mới tách xong dạng "Cách đọc kanji"**; các dạng khác chưa có giải thích mới (vẫn dùng giải thích cũ).

Client có 2 cách hiển thị giải thích, **ưu tiên giải thích mới**:

| | Nguồn | Phạm vi hiện tại |
|---|---|---|
| Mới (ưu tiên) | `questions_attribute.explain_all` | Chỉ dạng Cách đọc kanji |
| Cũ (dự phòng) | `questions.content[i].explainAll` | Các dạng còn lại (và câu kanji chưa có giải thích mới) |

Quan hệ: 1 câu hỏi ↔ 1 dòng, nối qua `question_id` → `questions.id`.

| Cột | Ý nghĩa | Sửa qua `update-attribute` |
|---|---|---|
| `id` | Khoá chính | — (dùng để định danh, được ưu tiên hơn `question_id`) |
| `question_id` | ID câu hỏi (→ `questions.id`) | — (định danh thay thế) |
| `explain_all` | Giải thích đầy đủ (JSON lưu dạng chuỗi, nhiều ngôn ngữ) → field `explain_all` trong response | ✅ |
| `text_transcript` | Transcript audio (câu nghe) → field `text_transcript` trong response | ✅ |
| `active` | 0 = chưa active (mặc định, vì mới import cần duyệt) / 1 = đã active | ✅ |
| `created_at`, `updated_at` | Thời điểm tạo / update gần nhất | ❌ (tự động) |

**App dùng thế nào**: khi trả câu hỏi, BE chỉ lấy `explain_all` + `text_transcript` của dòng **`active = 1`**. Dòng `active = 0` hoặc chưa có dòng → cả hai field trả `null` (client dùng giải thích cũ).

### Bảng `question_contributors` — phân công & theo dõi tiến độ CTV chỉnh sửa câu hỏi

Dữ liệu của trang admin `/contributor` (repo `admin-jlpt`). 1 câu hỏi ↔ 1 dòng, khoá theo `question_id` (model admin dùng `question_id` làm primary key; API cũng tìm theo `question_id` nên không tạo trùng).

| Cột | Ý nghĩa | Ghi qua `POST /question-contributors` |
|---|---|---|
| `id` | Khoá chính | — |
| `question_id` | ID câu hỏi (→ `questions.id`), dùng để tìm dòng | ✅ từ `question_ids` |
| `admin_id` | **CTV phụ trách sửa** câu hỏi (cột "Admin"/"CTV" ở admin; các tab của CTV lọc `admin_id` = người đang đăng nhập) | ✅ từ `admin_id` |
| `admin_check` | **Người review / duyệt** câu hỏi (cột "Admin check" ở tab Đã duyệt; tab Duyệt chéo / Check lại lọc theo cột này) | ✅ từ `user_ids[i]` |
| `status` | Tiến độ xử lý — xem bảng dưới | ✅ từ `status` |
| `created_at`, `updated_at` | Thời điểm bắt đầu đóng góp / update gần nhất | ❌ (tự động) |

`admin_id` và `admin_check` đều là ID trong bảng **`admins`** (không phải `users`). Lưu ý API đặt tên tham số là `user_ids` nhưng giá trị là ID bảng `admins`.

**Giá trị `status` và tab hiển thị.** Tab = tham số `?status=` của trang `/contributor`: 0 *Chưa sửa* · 1 *Đã sửa* · 2 *Duyệt chéo* · 3 *Check lại* · 4 *Đã duyệt* (đây là số thứ tự tab, **không** phải cột `status` trong DB). Mỗi tab lọc theo người đang đăng nhập: CTV thấy câu có `admin_id` = mình, người review thấy câu có `admin_check` = mình, BTV (role 2) thấy cả câu của CTV khác.

| `status` | Tên (`Contributor::STATUS` / nhãn UI) | Ý nghĩa | Hiện ở tab |
|---|---|---|---|
| `0` | `UNEDITED` — "Mới" | Đã giao, CTV chưa sửa | **Chưa sửa** |
| `-1` | không có hằng số — "Yêu cầu duyệt lại" | Người duyệt thêm comment → trả câu về cho CTV sửa lại | **Chưa sửa** (tab này lọc `status <= 0`) |
| `1` | `EDITED` — "Xong" | CTV đã sửa xong, chờ duyệt | **Đã sửa** (của CTV) · **Duyệt chéo** (câu chưa có comment) · **Check lại** (câu có comment / được giao check) |
| `2` | `PEER_REVIEWED` — "Đã được duyệt" (hoặc "…bởi AI" nếu câu có comment của `aiAgent`) | Đã duyệt xong | **Đã duyệt** · vẫn hiện ở **Đã sửa** của CTV (tab này lọc `status >= 1`) |
| `3`, `4` | `RECHECKED`, `APPROVED` | Có khai báo trong `Contributor::STATUS` nhưng **không thấy code admin nào ghi** giá trị này | Không có tab riêng (nếu có dữ liệu sẽ rơi vào **Đã sửa**) |

Admin tự ghi `status` ở: thêm comment → `-1`; bấm duyệt (`accept`) → `2` (kèm `admin_check` = người duyệt); lưu câu sau AI review (`JlptController`) → `0` / `1` / `2` tuỳ kết quả comment của AI.

**Một số BTV / CTV hay được chị Ngọc Anh giao review** — cột `id` là giá trị truyền vào `user_ids` (→ `admin_check`):

| id | username | email |
|---|---|---|
| 460576 | giangngh1206 | giangngh1206@gmail.com |
| 460581 | hamy36547 | hamy36547@gmail.com |
| 460577 | nguyenhaohaoxx | nguyenhaohaoxx@gmail.com |
| 460582 | phamphong10027002 | phamphong10027002@gmail.com |

---

## 2. Luồng xử lý 3 API

> Giá trị `X-Admin-Key` được cung cấp qua kênh private, **không nằm trong spec này**.

> ⚠️ **Khi cập nhật dữ liệu (cả 3 API) luôn làm đủ 2 việc:**
> - **Backup trước khi update**: sao lưu dữ liệu hiện tại của các bản ghi sắp sửa (bảng tương ứng: `questions` / `questions_attribute` / `question_contributors`), **lưu vào Drive cá nhân**.
> - **QC sau khi update**: yêu cầu **DevLead hoặc BE xuất dữ liệu các câu hỏi đã thay đổi** để QC lại, xem nội dung sau update đã đúng như mong muốn chưa.

### `PATCH /question/update-fields` — sửa nội dung / metadata 1 câu hỏi (bảng `questions`)

Body ví dụ: `{ "id": 12345, "fields": { "level": 3, "check_admin": 1 } }`

1. Kiểm `X-Admin-Key` → sai/thiếu: 401.
2. Validate body → sai kiểu / ngoài khoảng / `fields` rỗng: 400 (vd `level` 1–5; `check_admin`, `check_explain` chỉ 0 hoặc 1).
3. Tìm câu hỏi theo `id` → không thấy: 404.
4. `UPDATE questions SET <các cột trong fields> WHERE id = ?`.
5. Nếu có sửa `kind` / `level` / `check_admin` / `score_difficult` → xoá cache Redis "pool câu hỏi" của nhóm (kind, level) **cũ và mới**, để luyện tập lấy lại danh sách.
6. Trả `200 { message, id, updated: [tên các cột đã ghi] }`.

### `PATCH /question/update-attribute` — sửa giải thích / transcript 1 câu hỏi (bảng `questions_attribute`)

Body ví dụ: `{ "question_id": 12345, "fields": { "explain_all": "<chuỗi JSON>", "active": 1 } }`

1. Kiểm `X-Admin-Key` → sai/thiếu: 401.
2. Validate body → sai kiểu / `active` ngoài 0–1 / `fields` rỗng: 400.
3. Phải có `id` hoặc `question_id` → thiếu cả hai: 400.
4. Tìm dòng attribute: có `id` thì tìm theo `id` (ưu tiên), không thì theo `question_id` → không thấy: 404 (API **không tự tạo** dòng mới).
5. `UPDATE questions_attribute SET <các cột trong fields> WHERE id = <id dòng tìm được>`.
6. Trả `200 { message, id, question_id, updated: [tên các cột đã ghi] }`. Không xoá cache nào.

### `POST /question-contributors` — giao câu hỏi cho CTV & người review (bảng `question_contributors`)

Body ví dụ: `{ "question_ids": [101, 102], "user_ids": [7, 8], "status": 0, "admin_id": 5 }`
→ câu 101 giao review cho 7, câu 102 cho 8; cả hai do CTV 5 phụ trách, trạng thái 0 (Chưa sửa).

1. Kiểm `X-Admin-Key` → sai/thiếu: 401.
2. Validate body → `question_ids`, `user_ids` phải là mảng số **không rỗng**; `admin_id` phải là số → sai: 400. `status` **không bị validate** (nhận số bất kỳ) — nên luôn gửi, thường `0`.
3. Độ dài `question_ids` ≠ `user_ids` → 400 `Mismatched lengths of question_ids and user_ids`. Hai mảng ghép theo **vị trí**: `question_ids[i]` ↔ `user_ids[i]`.
4. Với từng câu (tuần tự, **không transaction** — lỗi giữa chừng thì các câu trước đó đã được ghi), tìm dòng theo `question_id`:
   - Chưa có → `INSERT` { `question_id`, `admin_check = user_ids[i]`, `status`, `admin_id` } → `action: "created"`.
   - Đã có → `UPDATE ... WHERE question_id = ?`, ghi đè `admin_check`, `status`, `admin_id` → `action: "updated"`. ⚠️ Ghi đè cả `status`: câu đã duyệt (`2`) mà gọi lại với `status = 0` sẽ bị đưa về "Chưa sửa".
   - `status` và `admin_id` dùng chung cho mọi câu trong request; chỉ `admin_check` riêng từng câu. API **không kiểm tra** `question_id` / `admin_id` / `user_ids` có tồn tại.
5. Trả `201 { result: [{ question_id, action: "created" | "updated" }], timestamp }`.
