# Sổ tay chạy – dạng 16 Nghe hiểu chủ đề (cho phiên Claude mới)

> Viết 2026-10-08. Một cuộc trò chuyện Cowork **mới** chỉ cần đọc **file này + `NHAT_KY.md`** là chạy được, **không đọc lại cả project**.
> Câu mở đầu người dùng gõ: **"Đọc dang_bai/16_nghe_hieu_chu_de/SO_TAY_CHAY.md rồi chạy dạng 16 mẫu X đến Y"** (hoặc "… lô tiếp theo").
> Trả lời người dùng bằng **tiếng Việt**. Dạng 16 chạy **hoàn toàn bằng Claude Opus 5.5 Cowork** – không có bước GPT API.
> Mỗi câu = 1 bài nghe (`cau_con = 1`). **Lô chuẩn = 10 câu** theo `output/thu_tu_chay.csv` (1–10, 11–20 …). Lô 1 là lô pilot (đủ N1–N5, 4 câu tranh, 1 câu Python dựng, 2 câu lệch dòng, 1 câu lời thoại ở `doan_van`, 1 câu có phân tích mở đầu).

---

## 0. Khởi động phiên

1. Nạp công cụ: ToolSearch `select:mcp__remote-devices__device_bash`. Mọi lệnh chạy trên máy người dùng bằng công cụ này.
2. `DANG=$HOME/mnt/Vie-Kor/dang_bai/16_nghe_hieu_chu_de` – **mỗi lệnh `cd $DANG` trước**. Công cụ chung: `python3 ../../pipeline_chung/cong_cu/<tên>.py` (gọi tắt `CC/<tên>.py`).
3. Đọc `NHAT_KY.md`.
4. `python3 CC/tien_do.py` (lũy kế, lô gợi ý) và `python3 CC/tien_do.py X Y` (từng mẫu: trạng thái + bước đã qua). **Từ stt 231: lấy lô bằng `python3 scripts/lo_jlpt.py` (mục 6b), bỏ qua lô gợi ý của `tien_do.py`.**
5. Đọc **một lần mỗi phiên** trước khi soát: `prompts/s1_claude_kiem_tra.md` (tiêu chí 3d, 3e) và `prompts/s2_claude_kiem_tra.md`.
6. Phạm vi: `--tu X --den Y` (stt trong `output/thu_tu_chay.csv`). Không dùng `--lo` với `scripts/*.py`.
6b. **Chỉ chạy mẫu thuộc đề JLPT từ stt 231** (quyết định người dùng 2026-10-11, `config.loc_nguon_de`): mẫu mà cột `thi_thu_thuoc_de` (file dữ liệu, tra theo sample_id) có chữ `Nat Test` – kể cả khi có thêm đề khác – bị **bỏ tự động** ở mọi script khi chọn bằng `--tu/--den` (dòng in "Lọc nguồn đề … bỏ N mẫu thuộc NAT-TEST"). Mẫu ô trống (chỉ luyện tập) và mẫu đề Test / Listening Test / Reading Test / Vocabulary Test / Mock Full Exam vẫn chạy. Mẫu stt 1–230 giữ nguyên kết quả. **Chọn lô bằng `python3 scripts/lo_jlpt.py --lo 3`** (in khoảng `--tu X --den Y` = stt trong `output/thu_tu_chay.csv`, chứa 10 mẫu JLPT chưa làm) **thay cho "Lô tiếp theo gợi ý" của `CC/tien_do.py`** (công cụ chung vẫn đếm mẫu NAT là `ĐANG_XỬ_LÝ` – các mẫu NAT này sẽ mãi ở `ĐANG_XỬ_LÝ`, bình thường). Thống kê: `python3 scripts/lo_jlpt.py --thong-ke`. Muốn chạy cả mẫu NAT cho một lệnh: thêm `--ca-nat`; `--ids` / `--pilot` không bị lọc. Sao lưu trước khi sửa: `_sao_luu/2026-10-11_truoc_loc_jlpt/`.
7. Phiên không có công cụ **Agent** → dừng, báo người dùng.
8. GĐ0 (`scripts/s0_chuan_bi.py`) **đã chạy** (2026-10-08). Chỉ chạy lại khi sửa `scripts/_nghe.py` / `_dang.py` – **không** thêm `--tao-lai-thu-tu` khi đã chạy lô.

## 1. Quy tắc bất biến

- **Bảo mật:** không đọc / mở `.env`. Không chạy `git status`. **Không xóa file** – cần bỏ thì `mv -n` vào `_to_delete/`.
- **Nội dung lời giải sai → chỉ gắn cờ** `nghi_noi_dung`, **không sửa**. Chỉ sửa **định dạng** (`sua_dinh_dang` + `nhom` + `[Đã sửa định dạng] …`) và **lỗi của bản tạo**. Ghi chú không kèm thay đổi → `[Ghi chú] …`.
- **Lời thoại tiếng Nhật gõ nhầm** (`わかしました`…): giữ nguyên, chỉ `[Ghi chú]` (quyết định Q6).
- **Chạy song song nhiều dạng:** chỉ sửa file trong `$DANG`; **không sửa** `pipeline_chung/`, `explanation_schema/`, dạng khác (đặc biệt `pipeline_chung/nghe_hieu.py` là của dạng 21). Cần sửa code chung → dừng, báo người dùng.
- Ngữ cảnh: tối đa **3 lô (30 câu) mỗi cuộc trò chuyện**.

## 2. Hai tác tử

- **Tác tử TẠO (Claude A)** = tác tử con (Agent, `subagent_type: "general-purpose"`, `model: "opus"`). Lời giao việc chép **nguyên văn** `prompts/giao_viec_tao_gd1.md` / `giao_viec_tao_gd2.md` (thay `{{SO_CAU}}`, bỏ dòng `<!-- -->`; GĐ2: thay `{{CAU_CO_DINH}}` bằng mục "Cách dịch đã thống nhất" trong NHAT_KY).
- **Python** dựng cả JSON cho câu **không có phân tích** (`tao_bang = python`, ~145 câu) ngay ở bước `--chuan-bi` – không giao tác tử TẠO; cờ `thieu_noi_dung` được điền sẵn, tác tử KIỂM TRA xác nhận.
- **Python** ghép `full_translation` (lời thoại Nhật ↔ bản dịch Việt theo dòng) cho mọi câu trừ câu `lech_dong` (~65 câu – tác tử TẠO ghép).
- **Tác tử KIỂM TRA** = phiên chính (bạn). Không tự tạo bản.

## 3. Quy trình một lô X–Y

### GĐ1 – JSON tiếng Việt

| # | Việc | Lệnh |
|---|---|---|
| 1 | Chuẩn bị | `python3 scripts/s1_claude_tao.py --chuan-bi --tu X --den Y` → "Python dựng JSON cho k câu" + N câu cho tác tử TẠO |
| 2 | Tác tử TẠO | Agent với `giao_viec_tao_gd1.md` ({{SO_CAU}} = N; N = 0 thì bỏ bước này). Ghi lại "điểm khó" |
| 3 | Nhận | `python3 scripts/s1_claude_tao.py --nhan --tu X --den Y` → "lỗi 0, chưa có 0" (Python điền full_translation / key_info / reference_raw) |
| 4 | Chuẩn bị soát | `python3 scripts/s1_claude_goi.py --tu X --den Y` |
| 5 | Soát | **`python3 scripts/xem16.py <id> …`** (hoặc `--lo X Y`): đề, lời thoại J / bản dịch V, khối phân tích, gợi ý, JSON có đường dẫn đầy đủ |
| 6 | Ghi kết quả | `output/claude/ly_do_lo/gd1_X_Y.json` (mục 4.3) → `python3 CC/ghi_ly_do.py output/claude/ly_do_lo/gd1_X_Y.json` |
| 7 | Python kiểm tra | `python3 scripts/s1_kiem_tra.py --tu X --den Y` → cờ = `CHỜ_DUYỆT_NỘI_DUNG`, còn lại `GĐ1_XONG`; `LỖI_GĐ1` → mục 6 |
| 8 | Chốt | `python3 scripts/s1_chot.py --tu X --den Y` |

### GĐ2 – tiếng Hàn

| # | Việc | Lệnh |
|---|---|---|
| 9 | Chuẩn bị | `python3 scripts/s2_claude_dich.py --chuan-bi --tu X --den Y` → M câu |
| 10 | Tác tử TẠO dịch | Agent với `giao_viec_tao_gd2.md` ({{SO_CAU}} = M) |
| 11 | Nhận | `python3 scripts/s2_claude_dich.py --nhan --tu X --den Y` → "lỗi 0" |
| 12 | Chuẩn bị soát | `python3 scripts/s2_claude_goi.py --tu X --den Y` |
| 13 | Soát | `python3 CC/xem_gd2.py <id> …` theo mục 5 |
| 14 | Ghi kết quả | `output/claude/ly_do_lo/gd2_X_Y.json` (`"giai_doan": "2"`, liệt kê **mọi** câu GĐ2) → `ghi_ly_do.py` |
| 15 | Python kiểm tra | `python3 scripts/s2_kiem_tra.py --tu X --den Y` → `ĐẠT`; xử lý lỗi / D7 / D12 / D15 / D16 rồi chạy lại |
| 16 | Báo cáo + nhật ký | mục 7 |

Excel CTV (khi người dùng yêu cầu): `python3 scripts/s3_xuat_ctv.py --tu A --den B` (ĐẠT, CTV tiếng Hàn – cột "Ngữ liệu" là lời thoại Nhật) · `python3 scripts/s3b_xuat_ctv_nhat.py --tu A --den B` (câu có cờ, CTV tiếng Nhật) → `output/reports/ctv/`. Báo cáo số liệu: `python3 scripts/s9_bao_cao.py --tu A --den B`.

## 4. Soát GĐ1

Chuẩn: **JSON đúng và đủ lời giải gốc**; nội dung đúng với **lời thoại**. Đầy đủ: `prompts/s1_claude_kiem_tra.md`.

**Cờ s0 hay gặp → cách xử lý** (đầy đủ: `FLAG_TEXT` trong `scripts/_dang.py`, `FLAG_HINT` trong `scripts/_dau_vao.py`):

| Cờ | Xử lý |
|---|---|
| `lua_chon_tranh` | option_ja = '1'…'4', meaning = null; mô tả tranh không kiểm chứng – chỉ cờ khi mâu thuẫn lời thoại |
| `thieu_phan_tich` (Python dựng) | xác nhận cờ `thieu_noi_dung` điền sẵn; soát question / full_translation như bình thường |
| `lech_dong` | soát kỹ full_translation tác tử TẠO ghép: đủ dòng Nhật đúng thứ tự (K8), không mất dòng Việt (K9), dòng Việt đúng hàng |
| `nguoi_noi_lech` | đọc từng cặp dòng – Python ghép theo số dòng có thể trượt; trượt → sửa meaning cho đúng hàng (`sai_so_ban_goc`) |
| `trich_ngoai_loi_thoai` / K-TD | so câu trích với lời thoại: khác 1–2 kana → `[Ghi chú]`; khác chữ / người nói / không chứng minh được → cờ `trich_dan` |
| `lech_dap_an`, `nhieu_dung`, `khong_co_dung` / K4 | is_match giữ theo lời giải; gắn cờ `dap_an` |
| `mo_dau_phan_tich` | summary = đoạn mở đầu (giữ phần dẫn + câu trích trong dòng) |
| `khong_cau_hoi_cuoi` | xem question.ja lấy đúng câu hỏi (dòng mở đầu / cột câu hỏi) |
| `phu_loi_thoai` | khối từ vựng / ghi chú sau lời thoại → nhóm 2 của full_translation |

### 4.1 Sửa (lỗi bản tạo / định dạng)
- Câu trích giữa câu bị tách ra quotes làm mất chữ → trả lại analysis; phần dẫn bị chép vào analysis → bỏ; câu sau `→ ĐÚNG/SAI` bị mất → bổ sung (`sai_so_ban_goc`).
- Thiếu ⟪ ⟫, option_ja khác đề, meaning lựa chọn chữ bị bỏ, is_match sai kết luận khối → sửa.
- Dính câu / lặp từ / dấu câu thừa / ruby hỏng trong nhận xét, câu trích → `sua_dinh_dang`.

### 4.2 Gắn cờ (`nhom`: `nghia_cau`, `trich_dan`, `phan_tich`, `dap_an`, `thieu_noi_dung`, `khac`) – 7 quy tắc 3d của prompt.

### 4.3 File đặc tả lô (một file mỗi lô mỗi giai đoạn)
```json
{"giai_doan": "1",
 "cau": {
  "24951_1": {},
  "12316_1": {"thay": [{"duong_dan": "$.options[1].analysis.vi", "cu": "chỉ chỉ", "moi": "chỉ"}],
              "sua": [{"duong_dan": "$.options[1].analysis.vi", "loai": "sua_dinh_dang", "nhom": "lap_tu", "muc_do": "nhe", "ly_do": "lặp từ do gõ"}],
              "ghi_chu_ban_goc": ["[Đã sửa định dạng] Phân tích lựa chọn 2: 'chỉ chỉ' → 'chỉ' – lặp từ"],
              "nghi_noi_dung": [{"vi_tri": "Phân tích lựa chọn 2 – câu trích", "nhom": "trich_dan", "mo_ta": "(3d-3) …", "de_xuat": "…"}]}
 }}
```
Ghi bằng python (`json.dump(..., ensure_ascii=False, indent=1)`, heredoc `'EOF'`). Liệt kê **mọi** câu của lô. Danh sách bị **ghi đè** khi chạy lại. `duong_dan` chép đúng như `xem16.py` in (`$.options[1].analysis.vi`, `$.full_translation[0].lines[3].meaning.vi`). Câu Python dựng: để `{}` thì **giữ** cờ `thieu_noi_dung` điền sẵn; muốn đổi thì ghi lại cả danh sách `nghi_noi_dung`. Sửa bool / cấu trúc (is_match, gán lại dòng) → python read-modify-write `output/json_vi/checked/<id>.json` + ghi `sua`.

## 5. Soát GĐ2 – tiếng Hàn

Theo `prompts/s2_claude_kiem_tra.md`: lời thoại / câu hỏi / câu trích / nghĩa lựa chọn chữ **dịch thẳng từ tiếng Nhật** – văn nói, mức lịch sự đúng câu Nhật, nhất quán tên người; câu hỏi & câu trích trùng dòng lời thoại dịch giống hệt dòng đó (D15); giữ `(i)` (D16), `{ }` (D7); phân tích -습니다, trợ từ sau ⟪kana⟫ theo âm cuối cách đọc (D12).

## 6. Sự cố thường gặp

| Hiện tượng | Xử lý |
|---|---|
| `--nhan` GĐ1 LỖI_KỸ_THUẬT | `s1_claude_tao.py --chuan-bi --ids <id> --force` → giao lại → `--nhan --ids <id>` |
| "câu lệch dòng – tác tử TẠO phải ghi full_translation" | giao lại câu đó, nhắc `can_ghi_full_translation` |
| `--nhan` GĐ2 LỖI_GĐ2 | `s2_claude_dich.py --chuan-bi --ids <id> --force` → giao lại → `--nhan --ids <id>` |
| `s1_kiem_tra` LỖI_GĐ1 K8 / K9 / độ phủ | đọc lỗi; sửa file checked (lỗi bản tạo) → `s1_kiem_tra --ids <id>`. Lỗi do Python tách sai nguồn (lời thoại / bản dịch / khối) → báo người dùng; sửa `scripts/_nghe.py` (backup `$HOME/bak16`), chạy lại `s0_chuan_bi.py`, ghi NHAT_KY |
| `nhom 'X' không hợp lệ` | dùng đúng danh sách mục 4.2 |
| `[Lỗi JSON VI]` ở GĐ2 → CẦN_SỬA_GĐ1 | `s1_claude_goi --ids <id>` → sửa → `s1_kiem_tra` → `s1_chot` → GĐ2 lại |
| Lô đang dở | `CC/tien_do.py X Y`; chạy tiếp từ bước đó |

## 7. Báo cáo cuối lô (tiếng Việt, ngắn)

1. Bảng ĐẠT / nghi nội dung (id). 2. Mỗi câu gắn cờ: 1 dòng lý do; sửa: liệt kê ngắn. 3. Lũy kế (`CC/tien_do.py`). 4. Lệnh tiếp: **"Chạy dạng 16 mẫu X đến Y"** với X–Y = lô kế tiếp do `python3 scripts/lo_jlpt.py` in (mục 0.6b – từ stt 231 không dùng <Y+1>–<Y+10>) (sau lô thứ 3: đề nghị mở cuộc trò chuyện mới).

Sau báo cáo **cập nhật `NHAT_KY.md`**: dòng bảng lô; quyết định / cách dịch mới; sự cố.
