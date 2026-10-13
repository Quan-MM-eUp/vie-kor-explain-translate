# Sổ tay chạy – dạng 15 Đọc hiểu: Tìm thông tin (cho phiên Claude mới)

> Viết 2026-10-08. Một cuộc trò chuyện Cowork **mới** chỉ cần đọc **file này + `NHAT_KY.md`** là chạy được, **không đọc lại cả project**.
> Câu mở đầu người dùng gõ: **"Đọc dang_bai/15_doc_hieu_tim_thong_tin/SO_TAY_CHAY.md rồi chạy dạng 15 lô 1"** (hoặc "… mẫu X đến Y", "… lô tiếp theo").
> Trả lời người dùng bằng **tiếng Việt**. Dạng 15 chạy **hoàn toàn bằng Claude Opus 5.5 Cowork** – không có bước GPT API.
> Dạng 15 = **ngữ liệu thông báo / bảng giá / lịch** (Python đã trải bảng) + 1–3 câu hỏi / ngữ liệu; lời giải 4 lựa chọn: `Nghĩa` / trích dẫn 「…」 (+ dịch) / phân tích (**có phép tính**) → `→ ĐÚNG/SAI`. Schema `reading_listening.v1`.
> **Lô = cột `lo` của `output/thu_tu_chay.csv`** (~10 câu, không cắt đôi ngữ liệu, cỡ lô 8–11). Xem lô: `python3 scripts/lo.py`; lô tiếp theo: `python3 scripts/lo.py tiep` (in "X Y").

---

## 0. Khởi động phiên (làm theo thứ tự)

1. Nạp công cụ: ToolSearch `select:mcp__remote-devices__device_bash`. Mọi lệnh chạy trên máy người dùng bằng công cụ này.
2. `DANG=$HOME/mnt/Vie-Kor/dang_bai/15_doc_hieu_tim_thong_tin` – **mỗi lệnh đều `cd $DANG` trước**. Công cụ chung: `python3 ../../pipeline_chung/cong_cu/<tên>.py` (gọi tắt `CC/<tên>.py`).
3. Đọc `NHAT_KY.md`.
4. `python3 scripts/lo.py` (bảng lô + trạng thái), `python3 CC/tien_do.py X Y` (từng mẫu: tạo VI / soát VI / chốt VI / tạo KO / soát KO).
4b. **Chỉ chạy mẫu thuộc đề JLPT từ stt 297** (quyết định người dùng 2026-10-11, `config.loc_nguon_de`): mẫu mà cột `thi_thu_thuoc_de` (file dữ liệu, tra theo `sample_id`) có chữ `Nat Test` – kể cả khi có thêm đề khác – bị **bỏ tự động** ở mọi script khi chọn bằng `--tu/--den` (stt theo `output/thu_tu_chay.csv`), `--lo`, `--tat-ca` (dòng in "Lọc nguồn đề … bỏ N mẫu thuộc NAT-TEST"). Mẫu ô trống (chỉ luyện tập) và mẫu đề Test / Reading Test / Vocabulary Test / Mock Full Exam vẫn chạy. Mẫu stt < 297 giữ nguyên kết quả; `thu_tu_chay.csv` và cột `lo` **không đổi**. **Chọn lô bằng `python3 scripts/lo_jlpt.py --lo 3`** (in `Lô <số>: --tu X --den Y (n mẫu JLPT, bỏ m mẫu NAT)`, bỏ qua lô toàn NAT / đã xong) thay cho gợi ý lô của `CC/tien_do.py` và `scripts/lo.py` (các công cụ này vẫn đếm mẫu NAT là `ĐANG_XỬ_LÝ` / chưa xong – sẽ mãi chỉ vào mẫu NAT). Thống kê: `python3 scripts/lo_jlpt.py --thong-ke`. Muốn chạy cả mẫu NAT cho một lệnh: thêm `--ca-nat`; `--ids`, `--pilot` không bị lọc. Báo cáo lô: ghi các mẫu NAT đã bỏ trong khoảng (lấy từ dòng "Lọc nguồn đề …").
5. Đọc **một lần mỗi phiên** trước khi soát: `prompts/s1_claude_kiem_tra.md` (tiêu chí GĐ1 – mục 3d-1…7) và `prompts/s2_claude_kiem_tra.md`.
6. Phạm vi: `--tu X --den Y` (stt trong `output/thu_tu_chay.csv`) – do `scripts/_dang.py` xử lý nên không hiện trong `--help`. **Không dùng `--lo` với `scripts/*.py`**; riêng `CC/xem_gd1.py` / `CC/xem_gd2.py`: `--lo X Y` = khoảng stt. Người dùng nói "lô N" → `python3 scripts/lo.py N` lấy X Y. Khoảng không tròn ngữ liệu → đề nghị lấy tròn lô rồi làm theo người dùng chọn.
7. Phiên không có công cụ **Agent** → dừng, báo người dùng.

## 1. Quy tắc bất biến

- **Bảo mật:** không đọc / mở `.env`, không in API key. Không chạy `git status`. **Không xóa file** – cần bỏ thì `mv -n` vào `_to_delete/`.
- **Nội dung lời giải sai → chỉ gắn cờ** `nghi_noi_dung`, **không sửa** (kể cả phép tính sai, trích dẫn tự dựng, đáp án lệch). Chỉ sửa **định dạng** (`sua_dinh_dang` + `nhom` + dòng `[Đã sửa định dạng] …`) và **lỗi của tác tử TẠO**. Ghi chú không kèm thay đổi JSON → `[Ghi chú] …`.
- **Chạy song song nhiều dạng:** chỉ sửa file trong `$DANG`; **không sửa** `pipeline_chung/` (kể cả `doc_hieu_chung.py`), `explanation_schema/`, dạng khác. Cần sửa code chung → dừng, báo người dùng. Được sửa `scripts/_dang.py`, `scripts/_dau_vao.py`, prompt dạng 15 khi lỗi tách lời giải (mục 6), sau khi báo.
- Ngữ cảnh: tối đa **3 lô (~33 câu) mỗi cuộc trò chuyện** (ngữ liệu bảng dài).

## 2. Hai tác tử

- **Tác tử TẠO (Claude A)** = tác tử con (Agent tool, `subagent_type: "general-purpose"`, `model: "opus"`). Lời giao việc chép **nguyên văn** `prompts/giao_viec_tao_gd1.md` / `giao_viec_tao_gd2.md` (thay `{{SO_CAU}}`, bỏ dòng `<!-- -->`; GĐ2: chép cách dịch đã thống nhất trong NHAT_KY vào dòng "Câu cố định", chưa có thì bỏ dòng đó).
- **Tác tử KIỂM TRA** = phiên chính (bạn). Không tự tạo bản.

## 3. Quy trình một lô X–Y

### GĐ1 – JSON tiếng Việt

| # | Việc | Lệnh |
|---|---|---|
| 1 | Chuẩn bị | `python3 scripts/s1_claude_tao.py --chuan-bi --tu X --den Y` → N câu (N nhỏ hơn: xem dòng 'bỏ qua …'; chạy lại an toàn) |
| 2 | Tác tử TẠO | Agent với `giao_viec_tao_gd1.md` ({{SO_CAU}} = N). Ghi lại "điểm khó" |
| 3 | Nhận | `python3 scripts/s1_claude_tao.py --nhan --tu X --den Y` → "lỗi 0, chưa có 0" |
| 4 | Chuẩn bị soát | `python3 scripts/s1_claude_goi.py --tu X --den Y` |
| 5 | Soát | `python3 CC/xem_gd1.py <id> …` (in **ngữ liệu một lần cho mỗi nhóm**, rồi đề + lời giải gốc + gợi ý Python + JSON) – soát **theo ngữ liệu**: đọc ngữ liệu → tự giải câu hỏi → soát từng lựa chọn (mục 4) |
| 6 | Ghi kết quả | `output/claude/ly_do_lo/gd1_X_Y.json` (mục 4.3) → `python3 CC/ghi_ly_do.py output/claude/ly_do_lo/gd1_X_Y.json` |
| 7 | Python kiểm tra | `python3 scripts/s1_kiem_tra.py --tu X --den Y` → cờ = `CHỜ_DUYỆT_NỘI_DUNG`, còn lại `GĐ1_XONG`; `LỖI_GĐ1` → mục 6 |
| 8 | Chốt | `python3 scripts/s1_chot.py --tu X --den Y` |

### GĐ2 – tiếng Hàn

| # | Việc | Lệnh |
|---|---|---|
| 9 | Chuẩn bị | `python3 scripts/s2_claude_dich.py --chuan-bi --tu X --den Y` → M câu (chỉ câu đã chốt, không cờ) |
| 10 | Tác tử TẠO dịch | Agent với `giao_viec_tao_gd2.md` ({{SO_CAU}} = M) |
| 11 | Nhận | `python3 scripts/s2_claude_dich.py --nhan --tu X --den Y` → "lỗi 0" |
| 12 | Chuẩn bị soát | `python3 scripts/s2_claude_goi.py --tu X --den Y` |
| 13 | Soát | `python3 CC/xem_gd2.py <id> …` theo mục 5 |
| 14 | Ghi kết quả | `output/claude/ly_do_lo/gd2_X_Y.json` (`"giai_doan": "2"`, liệt kê **mọi** câu GĐ2) → `ghi_ly_do.py` |
| 15 | Python kiểm tra | `python3 scripts/s2_kiem_tra.py --tu X --den Y` → `ĐẠT`; xử lý lỗi / D-SO / D12 / D4 rồi chạy lại |
| 16 | Báo cáo + nhật ký | mục 7 |

Excel CTV (khi người dùng yêu cầu): `python3 scripts/s3_xuat_ctv.py --tu A --den B` (ĐẠT, CTV tiếng Hàn – cột "Ngữ liệu" hiện ngữ liệu ở câu con đầu nhóm) · `python3 scripts/s3b_xuat_ctv_nhat.py --tu A --den B` (câu có cờ, CTV tiếng Nhật) → `output/reports/ctv/`.

## 4. Soát GĐ1

Chuẩn: **JSON đúng và đủ lời giải gốc**; lời giải phải **đúng với ngữ liệu**. Đầy đủ: `prompts/s1_claude_kiem_tra.md`.

**Cách soát một ngữ liệu:** (1) đọc ngữ liệu (bảng đã trải `| ô | ô |`; `[ẢNH: …]` = không đọc được); (2) **tự giải** từng câu hỏi – tính lại tiền / giờ / ngày theo đúng điều kiện; (3) so với kết luận của lời giải và `dap_an_so`; (4) từng câu trích ↔ ngữ liệu; (5) nghĩa câu hỏi / lựa chọn / câu trích ↔ tiếng Nhật; (6) cấu trúc JSON ↔ lời giải.

**Cờ s0 hay gặp → JSON đúng** (đầy đủ: FLAG_HINT trong `scripts/_dau_vao.py`):

| Cờ | JSON đúng |
|---|---|
| `khong_cau_hoi_ja` | `question.ja = null`; `Câu hỏi: <tiếng Việt>` → `question.meaning` |
| `co_phan_dau`, `co_ban_dich` | bản dịch ngữ liệu → `full_translation` (1 dòng `lines`, giữ `\n`); tóm tắt / liệt kê → `summary` |
| `khuon_la` (B / C) | JSON phần có được (lựa chọn thiếu: `option_ja` của đề, `meaning`/`analysis` null, `quotes` []); tác tử KIỂM TRA gắn cờ `thieu_noi_dung` (3d-6) |
| `lua_chon_la_tranh` | `option_ja` = '1'…'4' của đề; mô tả tranh → `analysis`; ngữ liệu là tranh → cờ `thieu_noi_dung` nếu không xác minh được |
| `lua_chon_lech` | `option_ja` = dòng `k.` của lời giải (nếu là tiếng Nhật) |
| `lech_dap_an` (12736_2, 53801_2) | `is_match` theo lời giải, `correct.index = dap_an_so`; tự giải → gắn cờ `dap_an` + báo người dùng sửa dữ liệu |
| `tinh_toan_sai`, cảnh báo K-TT | tính lại theo ngữ liệu → cờ `tinh_toan` nếu sai thật |
| `trich_dan_ngoai_ngu_lieu`, cảnh báo K-TD | đối chiếu ngữ liệu → cờ `trich_dan` nếu tự dựng / sai chỗ; rút gọn đúng ý → không cờ |
| `thieu_ngu_lieu`, `ngu_lieu_anh` | không xác minh được → cờ `thieu_noi_dung` ("ngữ liệu rỗng / là ảnh – không xác minh được trích dẫn và đáp án") |
| `lua_chon_de_hong` (16919_2) | cờ `khac`: lựa chọn của đề là ngày giờ Excel → báo người dùng sửa dữ liệu |
| mọi câu | `key_info = null`, `reading = null`, `correct.full_sentence = null`, `reference_raw = null` (Python điền) |

### 4.1 Sửa (lỗi tác tử TẠO / định dạng)
- Lỗi tác tử TẠO: câu trích để trong analysis / trích tiếng Việt trong quotes, gộp câu trích, sót nhãn `Trích dẫn:` / 「」 / ( ) ngoài cùng, mất dòng phân tích, `is_match` sai so với lời giải, thiếu ⟪ ⟫ → sửa (`sai_so_ban_goc` / `khach_quan`).
- Định dạng bản gốc: dính câu, lặp từ, ruby hỏng, chính tả → `sua_dinh_dang`.

### 4.2 Gắn cờ (`nhom`: `tinh_toan`, `trich_dan`, `phan_tich`, `dap_an`, `nghia_cau`, `thieu_noi_dung`, `khac`) – quy tắc 3d-1…7 trong prompt.
- **Không gắn cờ:** phân tích ngắn nhưng đúng; lựa chọn SAI không kèm trích dẫn; lặp lại cùng phép tính; trích dẫn khác ngữ liệu chỉ ở khoảng trắng / `|` / 注; dịch vụng nhưng đúng ý.

### 4.3 File đặc tả lô (một file mỗi lô mỗi giai đoạn) – mẫu dưới chỉ minh họa cách ghi
```json
{"giai_doan": "1",
 "cau": {
  "16574_1": {},
  "12736_2": {"nghi_noi_dung": [{"vi_tri": "Đáp án", "nhom": "dap_an", "mo_ta": "(3d-4) Ngày 5/5: cá giảm 30% (600×0.7=420), xúc xích giảm 20% (400×0.8=320) → 740円 = lựa chọn 4; lời giải chấm ĐÚNG lựa chọn 4 nhưng dap_an_so = 2.", "de_xuat": "Sửa dữ liệu gốc: dap_an_so = 4"}]},
  "13403_1": {"thay": [{"duong_dan": "$.options[0].analysis.vi", "cu": "yên.Như", "moi": "yên. Như"}],
              "sua": [{"duong_dan": "$.options[0].analysis.vi", "loai": "sua_dinh_dang", "nhom": "dinh_chu", "muc_do": "nhe", "ly_do": "dính câu"}],
              "ghi_chu_ban_goc": ["[Đã sửa định dạng] Lựa chọn 1 – phân tích: 'yên.Như' → 'yên. Như' – dính câu"],
              "nghi_noi_dung": [{"vi_tri": "Lựa chọn 4 – trích dẫn", "nhom": "trich_dan", "mo_ta": "(3d-2) Câu trích '14:00 ~ 16:00 皆でパーティーに行って、買い物' không có trong lịch trình; ngữ liệu: '14:00 ~ 16:00 | いっしょにデパートに行って、買い物します。'", "de_xuat": "14:00 ~ 16:00 いっしょにデパートに行って、買い物します。"}]}
 }}
```
Ghi bằng python (`json.dump(..., ensure_ascii=False, indent=1)`, heredoc `'EOF'`). Liệt kê **mọi** câu của lô. Danh sách bị **ghi đè** khi chạy lại – sửa thêm thì sửa trong **cùng file** rồi chạy lại. `duong_dan` = đường dẫn `xem_gd1.py` in ra **thêm `$.`** ở đầu (`options[0].analysis.vi` → `$.options[0].analysis.vi`). Sửa cấu trúc (tách / gộp quotes, đổi `is_match`) → python read-modify-write `output/json_vi/checked/<id>.json` + ghi mục `sua` (đường dẫn mức trường, vd `$.options[2].quotes`).

## 5. Soát GĐ2 – tiếng Hàn

Theo `prompts/s2_claude_kiem_tra.md`: nghĩa câu hỏi / lựa chọn / câu trích **dịch thẳng từ tiếng Nhật** (bảng xem nhanh ghi `JA`); phân tích / tóm tắt / bản dịch ngữ liệu dịch từ tiếng Việt. **Số / giờ / ngày / giá giữ nguyên** (D-SO cảnh báo); đơn vị 엔, 월/일, 시/분; **trợ từ sau ⟪kana⟫ theo âm cuối cách đọc** (D12); câu trích giống nhau giữa lựa chọn / câu con dịch giống hệt (D4 → `khong_nhat_quan.csv`); ngữ liệu không dịch.

## 6. Sự cố thường gặp

| Hiện tượng | Xử lý |
|---|---|
| `--nhan` GĐ1 LỖI_KỸ_THUẬT | `s1_claude_tao.py --chuan-bi --ids <id> --force` → giao lại → `--nhan --ids <id>` |
| `--nhan` GĐ2 LỖI_GĐ2 | `s2_claude_dich.py --chuan-bi --ids <id> --force` → giao lại → `--nhan --ids <id>` |
| `s1_kiem_tra` LỖI_GĐ1 | đọc lỗi; sửa file checked (lỗi tác tử TẠO / định dạng) → `s1_kiem_tra --ids <id>`. "Độ phủ tiếng Việt … thiếu: [nhãn lạ]" do nhãn dẫn mới → báo người dùng, thêm vào `NHAN_TRICH_RE` / `NHAN_DAN_RE` trong `scripts/_dang.py` (và mục 4 của `prompts/s1_chuyen_json.md`) |
| K5 / K6 báo lệch dù JSON đúng lời giải | Python tách dòng câu hỏi / lựa chọn sai (lời giải lộn xộn) → báo người dùng; sửa `scripts/_dang.py` hoặc ghi `[Ghi chú]` và để người dùng quyết |
| `nhom 'X' không hợp lệ` | dùng đúng danh sách mục 4.2; nhóm mới → báo người dùng (code chung) |
| Python tách lời giải sai / gợi ý trái lời giải | báo người dùng; sửa `scripts/_dang.py` (backup `$HOME/bak15`), chạy lại `python3 scripts/s0_chuan_bi.py` – **không** thêm `--tao-lai-thu-tu`; ghi NHAT_KY. Lỗi nằm trong `pipeline_chung/doc_hieu_chung.py` → dừng, báo người dùng (code chung) |
| `[Lỗi JSON VI]` ở GĐ2 → CẦN_SỬA_GĐ1 | `s1_claude_goi --ids <id>` → sửa → `s1_kiem_tra` → `s1_chot` → GĐ2 lại |
| Lô đang dở | `CC/tien_do.py X Y` (soát 'dở' = còn `_huong_dan`); chạy tiếp từ bước đó |

## 7. Báo cáo cuối lô (tiếng Việt, ngắn)

1. Bảng ĐẠT / nghi nội dung (id), theo ngữ liệu. 2. Mỗi câu gắn cờ: 1 dòng lý do; sửa định dạng / sửa ko: liệt kê ngắn. 3. **Dữ liệu gốc cần người dùng sửa** (lệch đáp án, đề hỏng). 4. Lũy kế (`python3 scripts/lo.py`). 5. Lệnh tiếp: **"Chạy dạng 15 lô <N+1>"** (sau lô thứ 3: đề nghị mở cuộc trò chuyện mới).

Sau báo cáo **cập nhật `NHAT_KY.md`**: dòng bảng lô; quyết định / cách dịch mới; sự cố.
