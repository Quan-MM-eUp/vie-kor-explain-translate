# Sổ tay chạy – dạng 18 Nghe hiểu khái quát (cho phiên Claude mới)

> Viết 2026-10-08. Một cuộc trò chuyện Cowork **mới** chỉ cần đọc **file này + `NHAT_KY.md`** là chạy được, **không đọc lại cả project**.
> Câu mở đầu người dùng gõ: **"Đọc dang_bai/18_nghe_hieu_khai_quat/SO_TAY_CHAY.md rồi chạy dạng 18 mẫu X đến Y"** (hoặc "… lô tiếp theo").
> Trả lời người dùng bằng **tiếng Việt**. Dạng 18 chạy **hoàn toàn bằng Claude Opus 5.5 Cowork** – không có bước GPT API.
> Mỗi câu = **một bài nghe** (cau_con = 1). **Lô chuẩn = 10 câu** (1–10, 11–20 …). Schema `reading_listening.v1`.

---

## 0. Khởi động phiên (làm theo thứ tự)

1. Nạp công cụ: ToolSearch `select:mcp__remote-devices__device_bash`. Mọi lệnh chạy trên máy người dùng bằng công cụ này.
2. `DANG=$HOME/mnt/Vie-Kor/dang_bai/18_nghe_hieu_khai_quat` – **mỗi lệnh đều `cd $DANG` trước**. Công cụ chung: `python3 ../../pipeline_chung/cong_cu/<tên>.py` (gọi tắt `CC/<tên>.py`).
3. Đọc `NHAT_KY.md`.
4. `python3 CC/tien_do.py` (lũy kế, lô gợi ý) và `python3 CC/tien_do.py X Y` (từng mẫu: trạng thái + bước đã qua). **Từ stt 211: lấy lô bằng `python3 scripts/lo_jlpt.py` (mục 6b), bỏ qua lô gợi ý của `tien_do.py`.**
5. Đọc **một lần mỗi phiên** trước khi soát: `prompts/s1_claude_kiem_tra.md` (tiêu chí GĐ1 – 3d-1…7) và `prompts/s2_claude_kiem_tra.md`.
6. Phạm vi: `--tu X --den Y` (stt trong `output/thu_tu_chay.csv`) – do `scripts/_dang.py` xử lý nên không hiện trong `--help`. **Không dùng `--lo` với `scripts/*.py`**; riêng `CC/xem_gd1.py` / `CC/xem_gd2.py` / `scripts/xem_loi_thoai.py`: `--lo X Y` = khoảng stt.
6b. **Chỉ chạy mẫu thuộc đề JLPT từ stt 211** (quyết định người dùng 2026-10-11, `config.loc_nguon_de`): mẫu mà cột `thi_thu_thuoc_de` (file dữ liệu, tra theo sample_id) có chữ `Nat Test` – kể cả khi có thêm đề khác – bị **bỏ tự động** ở mọi script khi chọn bằng `--tu/--den` (dòng in "Lọc nguồn đề … bỏ N mẫu thuộc NAT-TEST"). Mẫu ô trống (chỉ luyện tập) và mẫu đề Test / Listening Test / Reading Test / Vocabulary Test / Mock Full Exam vẫn chạy. Mẫu stt 1–210 giữ nguyên kết quả. **Chọn lô bằng `python3 scripts/lo_jlpt.py --lo 3`** (in khoảng `--tu X --den Y` = stt trong `output/thu_tu_chay.csv`, chứa 10 mẫu JLPT chưa làm) **thay cho "Lô tiếp theo gợi ý" của `CC/tien_do.py`** (công cụ chung vẫn đếm mẫu NAT là `ĐANG_XỬ_LÝ` – các mẫu NAT này sẽ mãi ở `ĐANG_XỬ_LÝ`, bình thường). Thống kê: `python3 scripts/lo_jlpt.py --thong-ke`. Muốn chạy cả mẫu NAT cho một lệnh: thêm `--ca-nat`; `--ids` / `--pilot` không bị lọc. Sao lưu trước khi sửa: `_sao_luu/2026-10-11_truoc_loc_jlpt/`.
7. Phiên không có công cụ **Agent** → dừng, báo người dùng.

## 1. Quy tắc bất biến

- **Bảo mật:** không đọc / mở `.env`, không in API key. Không chạy `git status`. **Không xóa file** – cần bỏ thì `mv -n` vào `_to_delete/`.
- **Nội dung lời giải sai → chỉ gắn cờ** `nghi_noi_dung`, **không sửa**. Chỉ sửa **định dạng** (`sua_dinh_dang` + `nhom` + dòng `[Đã sửa định dạng] …`) và **lỗi của tác tử TẠO**. Ghi chú không kèm thay đổi JSON → `[Ghi chú] …`.
- **Lời thoại tiếng Nhật không sửa** (kể cả lỗi gõ `えーつ`, `(i)`) – chỉ ghi chú (quyết định Q5).
- **Chạy song song nhiều dạng:** chỉ sửa file trong `$DANG`; **không sửa** `pipeline_chung/`, `explanation_schema/`, dạng khác. Cần sửa code chung → dừng, báo người dùng. Được sửa `scripts/_dang.py`, `scripts/_loi_thoai.py`, `scripts/_dau_vao.py`, prompt dạng 18 khi Python tách sai (mục 6), sau khi báo.
- Ngữ cảnh: tối đa **3 lô (30 câu) mỗi cuộc trò chuyện**.

## 2. Hai tác tử

- **Tác tử TẠO (Claude A)** = tác tử con (Agent tool, `subagent_type: "general-purpose"`, `model: "opus"`). Lời giao việc chép **nguyên văn** `prompts/giao_viec_tao_gd1.md` / `giao_viec_tao_gd2.md` (thay `{{SO_CAU}}`, bỏ dòng `<!-- -->`; GĐ2: thay `{{CAU_CO_DINH}}` bằng các dòng mục "Cách dịch đã thống nhất" trong NHAT_KY, chưa có thì ghi "(chưa có)").
- **Tác tử KIỂM TRA** = phiên chính (bạn). Không tự tạo bản.

## 3. Quy trình một lô X–Y (10 câu)

### GĐ1 – JSON tiếng Việt

| # | Việc | Lệnh |
|---|---|---|
| 1 | Chuẩn bị | `python3 scripts/s1_claude_tao.py --chuan-bi --tu X --den Y` → N câu (chạy lại an toàn; câu đã có bản tạo bị bỏ qua) |
| 2 | Tác tử TẠO | Agent với `giao_viec_tao_gd1.md` ({{SO_CAU}} = N). Ghi lại "điểm khó" |
| 3 | Nhận | `python3 scripts/s1_claude_tao.py --nhan --tu X --den Y` → "lỗi 0, chưa có 0" |
| 4 | Chuẩn bị soát | `python3 scripts/s1_claude_goi.py --tu X --den Y` |
| 5 | Soát | mỗi câu: `python3 CC/xem_gd1.py <id>` (lời thoại L1…Ln, lời giải gốc, gợi ý, JSON) + `python3 scripts/xem_loi_thoai.py <id>` (bản dịch V1…Vm ↔ ghép `Lk Nhật ‖ Việt`) |
| 6 | Ghi kết quả | `output/claude/ly_do_lo/gd1_X_Y.json` (mục 4.3) → `python3 CC/ghi_ly_do.py output/claude/ly_do_lo/gd1_X_Y.json` |
| 7 | Python kiểm tra | `python3 scripts/s1_kiem_tra.py --tu X --den Y` → cờ = `CHỜ_DUYỆT_NỘI_DUNG`, còn lại `GĐ1_XONG`; `LỖI_GĐ1` → mục 6 |
| 8 | Chốt | `python3 scripts/s1_chot.py --tu X --den Y` |

### GĐ2 – tiếng Hàn

| # | Việc | Lệnh |
|---|---|---|
| 9 | Chuẩn bị | `python3 scripts/s2_claude_dich.py --chuan-bi --tu X --den Y` → M câu |
| 10 | Tác tử TẠO dịch | Agent với `giao_viec_tao_gd2.md` ({{SO_CAU}} = M). Lời thoại dài: nếu tác tử báo quá tải, chia 2 lượt Agent – mỗi lượt chạy lại bước 9 với `--ids <5 id>` (danh sách chỉ còn 5 câu) rồi giao việc |
| 11 | Nhận | `python3 scripts/s2_claude_dich.py --nhan --tu X --den Y` → "lỗi 0" |
| 12 | Chuẩn bị soát | `python3 scripts/s2_claude_goi.py --tu X --den Y` |
| 13 | Soát | `python3 CC/xem_gd2.py <id> …` theo mục 5 |
| 14 | Ghi kết quả | `output/claude/ly_do_lo/gd2_X_Y.json` (`"giai_doan": "2"`, liệt kê **mọi** câu GĐ2) → `ghi_ly_do.py` |
| 15 | Python kiểm tra | `python3 scripts/s2_kiem_tra.py --tu X --den Y` → `ĐẠT`; xử lý lỗi / D12 / D15 / D16 rồi chạy lại |
| 16 | Báo cáo + nhật ký | mục 7 |

Excel CTV (khi người dùng yêu cầu): `python3 scripts/s3_xuat_ctv.py --tu A --den B` (ĐẠT, CTV tiếng Hàn – cột "Ngữ liệu" là lời thoại L1…Ln) · `python3 scripts/s3b_xuat_ctv_nhat.py --tu A --den B` (câu có cờ, CTV tiếng Nhật) → `output/reports/ctv/`.

## 4. Soát GĐ1

Chuẩn: **JSON đúng và đủ lời giải gốc**, ghép đúng lời thoại; lời giải phải đúng **với lời thoại**. Đầy đủ: `prompts/s1_claude_kiem_tra.md`.

**Khuôn (cột `khuon` trong thu_tu_chay.csv) và cờ s0 → JSON đúng** (đầy đủ: FLAG_HINT trong `scripts/_dau_vao.py`):

| Khuôn / cờ | JSON đúng |
|---|---|
| A (### + phân tích), C (không ###) | đủ `quotes` / `analysis` / `is_match` theo `→ ĐÚNG/SAI` |
| **D** (chỉ bản dịch + câu hỏi + 4 lựa chọn Việt) | `option_ja` theo lời thoại, `meaning` = dòng lựa chọn Việt, `quotes = []`, `analysis = null`, `is_match = (index == dap_an_so)` → **bắt buộc cờ `thieu_noi_dung`** (Python K-KH) |
| **E** (không có tiếng Việt) | như D nhưng mọi `meaning = null` → **bắt buộc cờ `thieu_noi_dung`** |
| mọi câu | `full_translation` = đúng L1…Ln (`speaker`, `ja` y nguyên – K-LT1); `summary = key_info = null`; `correct.full_sentence = null` |
| `so_dong_dich_lech` | số dòng Việt ≠ số dòng Nhật – soát kỹ ghép theo nghĩa (`xem_loi_thoai.py`) |
| `khong_ban_dich` / K-LT2 vượt ngưỡng | nhiều dòng không có bản dịch → cờ `thieu_noi_dung` |
| `lua_chon_lech` | `option_ja` theo lời giải; lệch chữ / nghĩa thật → cờ `khac` (3d-7) |
| `trich_dan_ngoai_loi_thoai`, K-TD | câu trích không có trong lời thoại → xem 3d-3 (`trich_dan`) |
| `lech_dap_an`, `nhieu_dung` | `is_match` theo lời giải, `correct.index = dap_an_so` → cờ `dap_an` (3d-5) |
| `nguon_doan_van`, `loi_thoai_khong_cau_hoi` | lời thoại / câu hỏi lấy từ cột khác – kiểm lại đúng bài |

### 4.1 Sửa (lỗi tác tử TẠO / định dạng)
- Ghép lệch câu dịch với dòng Lk; sót nhãn người nói trong `meaning`; tự dịch dòng không có bản dịch (→ `null`); `quotes` / `analysis` tách sai; sót `→ SAI.` / `Dịch:`; `is_match` sai; `option_ja` mất furigana; thiếu ⟪ ⟫ → sửa (`sai_so_ban_goc` / `khach_quan`).
- Định dạng lời giải gốc (dính câu, lặp từ, chính tả, ruby hỏng) → `sua_dinh_dang`.

### 4.2 Gắn cờ (`nhom`: `nghia_cau`, `trich_dan`, `phan_tich`, `dap_an`, `thieu_noi_dung`, `khac`) – theo 3d-1…7 của prompt kiểm tra.
- **Bắt buộc đọc lời thoại**: so bản dịch từng dòng; câu trích có trong lời thoại không, có chứng minh điều phân tích nói không; lập luận "ý chính / điều muốn nói nhất" của 4 lựa chọn có đúng với câu hỏi không.
- **Không gắn cờ:** phân tích sơ sài nhưng không sai; dịch thoát đúng ý; lỗi gõ lời thoại Nhật (ghi chú); nhãn dẫn câu trích bị bỏ.

### 4.3 File đặc tả lô (một file mỗi lô mỗi giai đoạn)
```json
{"giai_doan": "1",
 "cau": {
  "12136_1": {},
  "22717_1": {"thay": [{"duong_dan": "$.full_translation[0].lines[3].meaning.vi", "cu": "Nam: Vậy", "moi": "Vậy"}],
              "sua": [{"duong_dan": "$.full_translation[0].lines[3].meaning.vi", "loai": "sai_so_ban_goc", "muc_do": "nhe", "ly_do": "bản tạo để sót nhãn người nói"}],
              "ghi_chu_ban_goc": ["[Ghi chú] Lời thoại L5: 'えーつ' – nghi lỗi gõ, giữ nguyên"],
              "nghi_noi_dung": [{"vi_tri": "Lựa chọn 2 – câu trích", "nhom": "trich_dan", "mo_ta": "(3d-3) Câu trích không có trong lời thoại …", "de_xuat": "…"}]},
  "53323_1": {"nghi_noi_dung": [{"vi_tri": "Toàn bộ phân tích", "nhom": "thieu_noi_dung", "mo_ta": "(3d-6) Khuôn D – lời giải không phân tích 4 lựa chọn", "de_xuat": "CTV viết phân tích 4 lựa chọn"}]}
 }}
```
Ghi bằng python (`os.makedirs('output/claude/ly_do_lo', exist_ok=True)` rồi `json.dump(..., ensure_ascii=False, indent=1)`, heredoc `'EOF'`). Liệt kê **mọi** câu của lô. Danh sách bị **ghi đè** khi chạy lại – sửa thêm thì sửa trong **cùng file** rồi chạy lại. `duong_dan` = đường dẫn `xem_gd1.py` in ra **thêm `$.`** ở đầu. Sửa bool / cấu trúc (vd đổi `meaning` thành `null`, chuyển câu trích giữa `quotes` và `analysis`) → python read-modify-write `output/json_vi/checked/<id>.json` + ghi `sua`.

## 5. Soát GĐ2 – tiếng Hàn

Theo `prompts/s2_claude_kiem_tra.md`: lời thoại / câu hỏi / lựa chọn / câu trích **dịch thẳng từ tiếng Nhật**, đúng **sắc thái nói** (반말 / 해요체 / 하십시오체 theo câu Nhật, cùng người nói cùng mức); câu trích giống hệt bản dịch dòng lời thoại (D15) và giống nhau giữa các lựa chọn (D16); `analysis` bám tiếng Việt, -습니다; **trợ từ sau ⟪kana⟫ theo âm cuối cách đọc** (D12 chỉ cảnh báo – tự soát). JSON tiếng Việt sai → `[Lỗi JSON VI]` → câu quay lại GĐ1.

## 6. Sự cố thường gặp

| Hiện tượng | Xử lý |
|---|---|
| `--nhan` GĐ1 LỖI_KỸ_THUẬT | `s1_claude_tao.py --chuan-bi --ids <id> --force` → giao lại → `--nhan --ids <id>` |
| `--nhan` GĐ2 LỖI_GĐ2 | `s2_claude_dich.py --chuan-bi --ids <id> --force` → giao lại → `--nhan --ids <id>` |
| `s1_kiem_tra` LỖI_GĐ1 | đọc lỗi; sửa file checked (lỗi tác tử TẠO / định dạng) → `s1_kiem_tra --ids <id>`. K-KH → thêm cờ `thieu_noi_dung` vào đặc tả lô |
| K-LT1 do **Python tách lời thoại sai** (người nói nhận nhầm, câu hỏi / lựa chọn lẫn vào lời thoại…) | báo người dùng; sửa `scripts/_loi_thoai.py` (backup `$HOME/bak18`), chạy lại `python3 scripts/s0_chuan_bi.py` – **không** thêm `--tao-lai-thu-tu`; rồi `s1_claude_tao.py --chuan-bi --ids <id> --force`; ghi NHAT_KY |
| `nhom 'X' không hợp lệ` | dùng đúng danh sách mục 4.2; nhóm mới → báo người dùng (code chung) |
| `[Lỗi JSON VI]` ở GĐ2 → CẦN_SỬA_GĐ1 | `s1_claude_goi --ids <id>` → sửa → `s1_kiem_tra` → `s1_chot` → GĐ2 lại |
| Lô đang dở | `CC/tien_do.py X Y` (soát 'dở' = còn `_huong_dan`); chạy tiếp từ bước đó |

## 7. Báo cáo cuối lô (tiếng Việt, ngắn)

1. Bảng ĐẠT / nghi nội dung (id). 2. Mỗi câu gắn cờ: 1 dòng lý do; sửa định dạng / sửa ko: liệt kê ngắn. 3. Lũy kế (`CC/tien_do.py`). 4. Lệnh tiếp: **"Chạy dạng 18 mẫu X đến Y"** với X–Y = lô kế tiếp do `python3 scripts/lo_jlpt.py` in (mục 0.6b – từ stt 211 không dùng <Y+1>–<Y+10>) (sau lô thứ 3: đề nghị mở cuộc trò chuyện mới).

Sau báo cáo **cập nhật `NHAT_KY.md`**: dòng bảng lô; quyết định / cách dịch mới; sự cố.
