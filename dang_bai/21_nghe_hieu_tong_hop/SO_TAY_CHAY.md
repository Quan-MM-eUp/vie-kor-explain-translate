# Sổ tay chạy – dạng 21 Nghe hiểu tổng hợp (cho phiên Claude mới)

> Viết 2026-10-08. Một cuộc trò chuyện Cowork **mới** chỉ cần đọc **file này + `NHAT_KY.md`** là chạy được, **không đọc lại cả project**.
> Câu mở đầu người dùng gõ: **"Đọc dang_bai/21_nghe_hieu_tong_hop/SO_TAY_CHAY.md rồi chạy dạng 21 mẫu X đến Y"** (hoặc "… lô tiếp theo").
> Trả lời người dùng bằng **tiếng Việt**. Dạng 21 chạy **hoàn toàn bằng Claude Opus 5.5 Cowork** – không có bước GPT API.
> Dạng 21 = **bài nghe dài** (lời thoại nhiều người, N1–N2) + câu hỏi + 4 lựa chọn; schema `reading_listening.v1`. **Lô = 5 bài nghe** (≈ 6 câu; bài 2 câu hỏi không tách) – khoảng mẫu từng lô ở `output/lo_chay.csv` / `python3 scripts/lo.py`.

---

## 0. Khởi động phiên (làm theo thứ tự)

1. Nạp công cụ: ToolSearch `select:mcp__remote-devices__device_bash`. Mọi lệnh chạy trên máy người dùng bằng công cụ này.
2. `DANG=$HOME/mnt/Vie-Kor/dang_bai/21_nghe_hieu_tong_hop` – **mỗi lệnh đều `cd $DANG` trước**. Công cụ chung: `python3 ../../pipeline_chung/cong_cu/<tên>.py` (gọi tắt `CC/<tên>.py`).
3. Đọc `NHAT_KY.md`.
4. `python3 scripts/lo.py tiep` (lô tiếp theo + khoảng mẫu) · `python3 scripts/lo.py` (mọi lô) · `python3 CC/tien_do.py X Y` (từng mẫu: trạng thái + bước đã qua).
5. Đọc **một lần mỗi phiên** trước khi soát: `prompts/s1_claude_kiem_tra.md` và `prompts/s2_claude_kiem_tra.md`. Phần ghi lý do làm bằng **file đặc tả lô + `ghi_ly_do.py`** (mục 4.3).
6. Phạm vi: `--tu X --den Y` (stt trong `output/thu_tu_chay.csv`) – do `scripts/_dang.py` xử lý. **Không dùng `--lo` với `scripts/*.py`**; riêng `CC/xem_gd1.py` / `CC/xem_gd2.py`: `--lo X Y` = khoảng stt. Người dùng xin khoảng không tròn lô → đề nghị lấy tròn lô (theo `lo_chay.csv`) rồi làm theo người dùng chọn.
7. Phiên không có công cụ **Agent** → dừng, báo người dùng.
8. `output/samples/norm/` chưa có (chưa chạy s0) → `python3 scripts/s0_chuan_bi.py` (an toàn, chạy lại được; **không** thêm `--tao-lai-thu-tu`).

## 1. Quy tắc bất biến

- **Bảo mật:** không đọc / mở `.env`, không in API key. Không chạy `git status`. **Không xóa file** – cần bỏ thì `mv -n` vào `_to_delete/`.
- **Nội dung lời giải sai → chỉ gắn cờ** `nghi_noi_dung`, **không sửa**. Chỉ sửa **định dạng** (`sua_dinh_dang` + `nhom` + dòng `[Đã sửa định dạng] …`) và **lỗi của tác tử TẠO**. Ghi chú không kèm thay đổi JSON → `[Ghi chú] …`. THAM KHẢO: không xử lý.
- **Lời thoại tiếng Nhật gõ sai** (`明、月曜日`, `フ降り`, `水曜日はもり`): **giữ nguyên** trong `lines[].ja`, chỉ `[Ghi chú] Lời thoại gõ sai: '…' (nên là '…') – giữ nguyên`.
- **Chạy song song nhiều dạng:** chỉ sửa file trong `$DANG`; **không sửa** `pipeline_chung/`, `explanation_schema/`, dạng khác. Cần sửa code chung → dừng, báo người dùng. Được sửa `scripts/_dang.py`, `scripts/_dau_vao.py`, `scripts/_dich_21.py`, prompt dạng 21 khi lỗi tách lời giải / lời thoại (mục 6), sau khi báo.
- Ngữ cảnh: tối đa **3 lô mỗi cuộc trò chuyện** (bài dài, lời giải ~4.000 ký tự / câu).

## 2. Hai tác tử

- **Tác tử TẠO (Claude A)** = tác tử con (Agent tool, `subagent_type: "general-purpose"`, `model: "opus"`). Lời giao việc chép **nguyên văn** `prompts/giao_viec_tao_gd1.md` / `giao_viec_tao_gd2.md` (thay `{{SO_CAU}}`, bỏ dòng `<!-- -->`; GĐ2: thay `{{CAU_CO_DINH}}` bằng các dòng mục "Cách dịch đã thống nhất" trong NHAT_KY, chưa có thì "(chưa có)").
- **Tác tử KIỂM TRA** = phiên chính (bạn). Không tự tạo bản.
- **Khuôn C_ja** (lời giải chỉ chép lại lời thoại tiếng Nhật): **Python dựng JSON** ở bước `--chuan-bi` – không giao tác tử TẠO; bạn vẫn soát.

## 3. Quy trình một lô X–Y

### GĐ1 – JSON tiếng Việt

| # | Việc | Lệnh |
|---|---|---|
| 1 | Chuẩn bị | `python3 scripts/s1_claude_tao.py --chuan-bi --tu X --den Y` → N câu cho tác tử TẠO (+ số câu C_ja Python dựng; câu dữ liệu lỗi bị bỏ qua) |
| 2 | Tác tử TẠO | Agent với `giao_viec_tao_gd1.md` ({{SO_CAU}} = N; N = 0 thì bỏ bước này). Ghi lại "điểm khó" |
| 3 | Nhận | `python3 scripts/s1_claude_tao.py --nhan --tu X --den Y` → "lỗi 0, chưa có 0" (Python điền `correct`, `summary`, lời thoại câu con 2) |
| 4 | Chuẩn bị soát | `python3 scripts/s1_claude_goi.py --tu X --den Y` (khuôn B / C: Python **điền sẵn** cờ `thieu_noi_dung` trong `.ly_do.json`) |
| 5 | Soát | `python3 CC/xem_gd1.py <id> …` (in **lời thoại JA một lần mỗi bài** ở khối "ĐOẠN VĂN", lời giải gốc, gợi ý Python, JSON) – soát **theo bài**, **tự giải câu hỏi từ lời thoại** |
| 6 | Ghi kết quả | `output/claude/ly_do_lo/gd1_X_Y.json` (mục 4.3) → `python3 CC/ghi_ly_do.py output/claude/ly_do_lo/gd1_X_Y.json` |
| 7 | Python kiểm tra | `python3 scripts/s1_kiem_tra.py --tu X --den Y` → cờ = `CHỜ_DUYỆT_NỘI_DUNG`, còn lại `GĐ1_XONG`; `LỖI_GĐ1` → mục 6 |
| 8 | Chốt | `python3 scripts/s1_chot.py --tu X --den Y` |

### GĐ2 – tiếng Hàn (chỉ câu GĐ1_XONG đã chốt, không cờ)

| # | Việc | Lệnh |
|---|---|---|
| 9 | Chuẩn bị | `python3 scripts/s2_claude_dich.py --chuan-bi --tu X --den Y` → M câu (M = 0: bỏ GĐ2) |
| 10 | Tác tử TẠO dịch | Agent với `giao_viec_tao_gd2.md` ({{SO_CAU}} = M) |
| 11 | Nhận | `python3 scripts/s2_claude_dich.py --nhan --tu X --den Y` → "lỗi 0" (câu con 2: Python chép bản Hàn lời thoại của câu con 1) |
| 12 | Chuẩn bị soát | `python3 scripts/s2_claude_goi.py --tu X --den Y` |
| 13 | Soát | `python3 CC/xem_gd2.py <id> …` theo mục 5 (lời thoại JA ở dòng đầu `output/claude/gd2/<id>.md`) |
| 14 | Ghi kết quả | `output/claude/ly_do_lo/gd2_X_Y.json` (`"giai_doan": "2"`, liệt kê **mọi** câu GĐ2) → `ghi_ly_do.py` |
| 15 | Python kiểm tra | `python3 scripts/s2_kiem_tra.py --tu X --den Y` → `ĐẠT`; xử lý lỗi / D12 / D15 / D16 / D17 rồi chạy lại |
| 16 | Báo cáo + nhật ký | mục 7 |

Excel CTV (khi người dùng yêu cầu): `python3 scripts/s3_xuat_ctv.py --tu A --den B` (ĐẠT, CTV tiếng Hàn – cột "Ngữ liệu" là lời thoại) · `python3 scripts/s3b_xuat_ctv_nhat.py --tu A --den B` (câu có cờ, gồm mọi khuôn B / C – CTV tiếng Nhật) → `output/reports/ctv/`.

## 4. Soát GĐ1

Chuẩn: **JSON đúng và đủ lời giải gốc**, lời giải **đúng với lời thoại**. Đầy đủ: `prompts/s1_claude_kiem_tra.md`.

**Khuôn (cột `khuon` của `lo_chay.csv`, `khuon_goc` trong norm):**

| Khuôn | Số câu | JSON đúng |
|---|---|---|
| A | 86 | `full_translation` ghép lượt JA ↔ VI; `options[i]`: `option_ja` (dòng lời giải, có furigana), `meaning` (Nghĩa:), `quotes` (「…」 + (dịch)), `analysis`, `is_match` (→ ĐÚNG/SAI); `key_info = null` |
| B | 8 | như A phần lời thoại; `options[i].meaning` từ danh sách 'Câu N:' của câu con này; `quotes = []`, `analysis = null`, `is_match` theo đáp án; `key_info` = khối 'Thông tin:' (giống nhau 2 câu con); cờ `thieu_noi_dung` (Python điền sẵn) |
| C_vi | 10 | `full_translation` ghép; `meaning` câu hỏi / lựa chọn từ cuối bản dịch; `quotes = []`, `analysis = null`; cờ `thieu_noi_dung` |
| C_ja | 23 | Python dựng: lời thoại (`meaning = null`), câu hỏi, lựa chọn, `is_match` theo đáp án; cờ `thieu_noi_dung` – soát `question.ja` đúng câu con, `speaker` tách đúng |
| trong / dữ liệu lỗi | 3 | `LỖI_GĐ1` từ s0: 53921_2 (không lời giải), 53342_1 · 53343_1 (thiếu `lua_chon_4`) – báo người dùng sửa dữ liệu gốc |

**Bài 2 câu hỏi** (cờ `bai_2_cau_hoi`, 14 bài): lời thoại do **câu con 1** giữ; câu con 2 có cờ `chep_loi_thoai` – `full_translation` Python chép, **sửa lời thoại ở câu con 1** (`s1_claude_goi` / `s1_kiem_tra` tự đồng bộ câu con 2, không tính là chỗ sửa). Soát `question.ja` đúng câu hỏi của từng câu con.

### 4.1 Sửa (lỗi tác tử TẠO / định dạng)
- Ghép lời thoại sai lượt / tách gộp sai / speaker sai / dòng dịch câu hỏi lọt vào lời thoại / mất `(i)`; `ja` khác lời thoại (K-FT LỖI chữ thừa) → sửa (`sai_so_ban_goc`).
- Nhận xét nhầm lựa chọn, câu trích sót (K-QT), `is_match` sai (K-IM), thiếu ⟪ ⟫, mất furigana → sửa.
- Định dạng bản gốc (dính câu, lặp chữ, `. . .`) → `sua_dinh_dang`.
- K-FT cảnh báo "thiếu …" là câu hỏi / lựa chọn / "1番" Python cắt sót → bỏ qua, ghi `[Ghi chú]`.

### 4.2 Gắn cờ (`nhom`: `thieu_noi_dung`, `nghia_cau`, `trich_dan`, `phan_tich`, `dap_an`, `khac`)
- Khuôn B / C: `thieu_noi_dung` (Python điền sẵn – **giữ**; nếu đặc tả lô ghi `nghi_noi_dung` cho câu đó thì phải chép lại cả mục `thieu_noi_dung`, vì danh sách bị ghi đè).
- Nghĩa sai (`nghia_cau`), câu trích sai / không chứng minh (`trich_dan`), phân tích trái lời thoại – nhất là suy luận nhiều bước, đổi ý (`phan_tich`), kết luận / đáp án sai, nhiều ĐÚNG (`dap_an`).
- **Không gắn cờ:** phân tích sơ sài nhưng đúng; diễn đạt vụng; lỗi gõ lời thoại; câu trích viết đúng chỗ lời thoại gõ sai (K-TD).

### 4.3 File đặc tả lô (một file mỗi lô mỗi giai đoạn)
```json
{"giai_doan": "1",
 "cau": {
  "22973_1": {},
  "12309_1": {"thay": [{"duong_dan": "$.full_translation[0].lines[3].meaning.vi", "cu": "Thứ Tư trời nhiều mây.", "moi": "Thứ Tư trời nhiều mây. Nhiệt độ sẽ tăng…"}],
              "sua": [{"duong_dan": "$.full_translation[0].lines[3].meaning.vi", "loai": "sai_so_ban_goc", "muc_do": "nhe", "ly_do": "tác tử TẠO cắt thiếu nửa sau dòng dịch V4"}],
              "ghi_chu_ban_goc": ["[Ghi chú] Lời thoại gõ sai: '今降っているこの雨は明、' (nên là '明日') và 'フ降り' (nên là '降り') – giữ nguyên"],
              "nghi_noi_dung": []},
  "12311_1": {"nghi_noi_dung": [{"vi_tri": "Toàn câu", "nhom": "thieu_noi_dung", "mo_ta": "Lời giải gốc chỉ có bản dịch lời thoại và đoạn 'Thông tin:' – không phân tích 4 lựa chọn", "de_xuat": "CTV viết phân tích"},
                                {"vi_tri": "Đáp án", "nhom": "dap_an", "mo_ta": "…", "de_xuat": "…"}]}
 }}
```
Ghi bằng python (`os.makedirs('output/claude/ly_do_lo', exist_ok=True)` rồi `json.dump(..., ensure_ascii=False, indent=1)`, heredoc `'EOF'`). Liệt kê **mọi** câu của lô. Danh sách bị **ghi đè** khi có khóa – sửa thêm thì sửa trong **cùng file** rồi chạy lại. `duong_dan` = đường dẫn `xem_gd1.py` in ra **thêm `$.`**. Sửa cấu trúc (tách / gộp lượt thoại, đổi `speaker`, bool) → python read-modify-write `output/json_vi/checked/<id>.json` + ghi mục `sua` (đường dẫn cha, vd `$.full_translation`).

## 5. Soát GĐ2 – tiếng Hàn

Theo `prompts/s2_claude_kiem_tra.md`: lượt thoại / câu hỏi / lựa chọn / câu trích / câu then chốt **dịch thẳng từ tiếng Nhật** – lượt thoại là **văn nói** đúng mức lịch sự (bạn bè 반말, khách – nhân viên 존댓말), giữ `(i)` / `(ii)` (D17); câu trích trùng lượt thoại dịch giống hệt (D15); nhận xét -습니다, trợ từ sau ⟪kana⟫ theo âm cuối cách đọc (D12); câu con 2: lời thoại theo câu con 1 (D16 – sửa ở câu con 1).

## 6. Sự cố thường gặp

| Hiện tượng | Xử lý |
|---|---|
| `--nhan` GĐ1 LỖI_KỸ_THUẬT | `s1_claude_tao.py --chuan-bi --ids <id> --force` → giao lại → `--nhan --ids <id>` |
| `--nhan` GĐ2 LỖI_GĐ2 | `s2_claude_dich.py --chuan-bi --ids <id> --force` → giao lại → `--nhan --ids <id>`; câu con 2 "chưa có bản Hàn của câu con 1" → `--nhan` câu con 1 trước |
| `s1_kiem_tra` LỖI_GĐ1 | đọc lỗi; sửa file checked → `s1_kiem_tra --ids <id>` |
| "Khuôn … phải gắn cờ thieu_noi_dung" | đặc tả lô đã ghi đè `nghi_noi_dung` – thêm lại mục `thieu_noi_dung` |
| Python cắt lời thoại / đề xuất câu hỏi sai, tách khối 1.–4. sai | báo người dùng; sửa `scripts/_dang.py` hoặc `pipeline_chung/nghe_hieu.py` (code chung – chỉ khi người dùng cho phép), chạy lại `python3 scripts/s0_chuan_bi.py` (không `--tao-lai-thu-tu`); ghi NHAT_KY |
| `nhom 'X' không hợp lệ` | dùng đúng danh sách mục 4.2 |
| `[Lỗi JSON VI]` ở GĐ2 → CẦN_SỬA_GĐ1 | `s1_claude_goi --ids <id>` → sửa → `s1_kiem_tra` → `s1_chot` → GĐ2 lại |
| Lô đang dở | `CC/tien_do.py X Y` (soát 'dở' = còn `_huong_dan`); chạy tiếp từ bước đó |

## 7. Báo cáo cuối lô (tiếng Việt, ngắn)

1. Bảng ĐẠT / nghi nội dung (id) theo bài. 2. Mỗi câu gắn cờ: 1 dòng lý do (khuôn B / C chỉ cần ghi "thiếu phân tích"); sửa định dạng / sửa ko: liệt kê ngắn. 3. Lũy kế (`CC/tien_do.py`). 4. Lệnh tiếp: theo `python3 scripts/lo.py tiep` (sau lô thứ 3: đề nghị mở cuộc trò chuyện mới).

Sau báo cáo **cập nhật `NHAT_KY.md`**: dòng bảng lô; quyết định / cách dịch mới; sự cố.
