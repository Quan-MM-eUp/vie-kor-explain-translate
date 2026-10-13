# Sổ tay chạy – dạng 14 Đọc hiểu chủ đề / quan điểm (cho phiên Claude mới)

> Viết 2026-10-08. Một cuộc trò chuyện Cowork **mới** chỉ cần đọc **file này + `NHAT_KY.md`** là chạy được, **không đọc lại cả project**.
> Câu mở đầu người dùng gõ: **"Đọc dang_bai/14_doc_hieu_chu_de_quan_diem/SO_TAY_CHAY.md rồi chạy dạng 14 lô 1"** (hoặc "… lô tiếp theo", "… mẫu X đến Y").
> Trả lời người dùng bằng **tiếng Việt**. Dạng 14 chạy **hoàn toàn bằng Claude Opus 5.5 Cowork** – không có bước GPT API.
> Dạng 14 = **đoạn văn dài chung** cho 2–4 câu con (82 đoạn, 265 câu, N1/N2); schema `reading_listening.v1`. **Lô = 3 đoạn văn (~9–11 câu)** – khoảng stt của từng lô ở `output/lo_chay.csv` (lô 1 = PILOT: 1 đoạn N1 kiểu A, 1 đoạn N2 kiểu B có câu quan điểm, 1 đoạn khuôn lạ).

---

## 0. Khởi động phiên (làm theo thứ tự)

1. Nạp công cụ: ToolSearch `select:mcp__remote-devices__device_bash`. Mọi lệnh chạy trên máy người dùng bằng công cụ này.
2. `DANG=$HOME/mnt/Vie-Kor/dang_bai/14_doc_hieu_chu_de_quan_diem` – **mỗi lệnh đều `cd $DANG` trước**. Công cụ chung: `python3 ../../pipeline_chung/cong_cu/<tên>.py` (gọi tắt `CC/<tên>.py`).
3. Đọc `NHAT_KY.md`.
4. `cat output/lo_chay.csv` (lô → stt từ–đến) · `python3 CC/tien_do.py` (lũy kế) · `python3 CC/tien_do.py X Y` (từng mẫu của lô: trạng thái + bước đã qua). (`tien_do.py` gợi ý lô theo cột `lo` của `thu_tu_chay.csv` – khớp `lo_chay.csv`.)
5. Đọc **một lần mỗi phiên** trước khi soát: `prompts/s1_claude_kiem_tra.md` (tiêu chí GĐ1 – 3d-14, khuôn lạ) và `prompts/s2_claude_kiem_tra.md`.
6. Phạm vi: `--tu X --den Y` (stt trong `output/thu_tu_chay.csv`, đúng ranh giới lô). **Không dùng `--lo` với `scripts/*.py`**; riêng `CC/xem_gd1.py` / `CC/xem_gd2.py`: `--lo X Y` = khoảng stt.
7. Phiên không có công cụ **Agent** → dừng, báo người dùng.

## 1. Quy tắc bất biến

- **Bảo mật:** không đọc / mở `.env`, không in API key. Không chạy `git status`. **Không xóa file** – cần bỏ thì `mv -n` vào `_to_delete/`.
- **Khuôn chuẩn:** nội dung lời giải sai → **chỉ gắn cờ** `nghi_noi_dung`, **không sửa**. Chỉ sửa **định dạng** (`sua_dinh_dang` + `nhom` + dòng `[Đã sửa định dạng] …`) và **lỗi của tác tử TẠO**. Ghi chú không kèm thay đổi JSON → `[Ghi chú] …`.
- **Khuôn lạ (`tao_moi`, 46 câu / 16 đoạn – xếp cuối, trừ 1 đoạn ở lô PILOT):** tác tử TẠO soạn mới phần thiếu; tác tử KIỂM TRA **được sửa** phần tạo mới (lỗi tác tử TẠO, `khach_quan`); Python luôn chặn câu (`CHỜ_DUYỆT_NỘI_DUNG`) cho tới khi CTV tiếng Nhật duyệt (mục 4.4).
- **Chạy song song nhiều dạng:** chỉ sửa file trong `$DANG`; **không sửa** `pipeline_chung/`, `explanation_schema/`, dạng khác. Cần sửa code chung → dừng, báo người dùng. Được sửa `scripts/_dang.py`, `scripts/_doc_hieu_14.py`, `scripts/_dau_vao.py`, prompt dạng 14 khi lỗi tách lời giải (mục 6), sau khi báo.
- Ngữ cảnh: tối đa **3 lô mỗi cuộc trò chuyện** (lời giải dạng 14 dài – lô có khuôn lạ tính như 1,5 lô).

## 2. Hai tác tử

- **Tác tử TẠO (Claude A)** = tác tử con (Agent tool, `subagent_type: "general-purpose"`, `model: "opus"`). Lời giao việc chép **nguyên văn** `prompts/giao_viec_tao_gd1.md` / `giao_viec_tao_gd2.md` (thay `{{SO_CAU}}`, bỏ dòng `<!-- -->`; GĐ2: thay `{{CAU_CO_DINH}}` bằng các dòng mục "Cách dịch đã thống nhất" trong NHAT_KY).
- **Tác tử KIỂM TRA** = phiên chính (bạn). Không tự tạo bản.

## 3. Quy trình một lô X–Y (3 đoạn văn)

### GĐ1 – JSON tiếng Việt

| # | Việc | Lệnh |
|---|---|---|
| 1 | Chuẩn bị | `python3 scripts/s1_claude_tao.py --chuan-bi --tu X --den Y` → N câu (chạy lại an toàn) |
| 2 | Tác tử TẠO | Agent với `giao_viec_tao_gd1.md` ({{SO_CAU}} = N). Ghi lại "điểm khó" + câu đã tạo mới |
| 3 | Nhận | `python3 scripts/s1_claude_tao.py --nhan --tu X --den Y` → "lỗi 0, chưa có 0" |
| 4 | Chuẩn bị soát | `python3 scripts/s1_claude_goi.py --tu X --den Y` |
| 5 | Soát | `python3 CC/xem_gd1.py <id> …` (đoạn văn in **một lần mỗi đoạn**, rồi lời giải gốc + gợi ý + JSON) – soát **theo từng đoạn** |
| 6 | Ghi kết quả | `output/claude/ly_do_lo/gd1_X_Y.json` (mục 4.3) → `python3 CC/ghi_ly_do.py output/claude/ly_do_lo/gd1_X_Y.json` |
| 7 | Python kiểm tra | `python3 scripts/s1_kiem_tra.py --tu X --den Y` → cờ / tạo mới = `CHỜ_DUYỆT_NỘI_DUNG`, còn lại `GĐ1_XONG`; `LỖI_GĐ1` → mục 6 |
| 8 | Chốt | `python3 scripts/s1_chot.py --tu X --den Y` |

### GĐ2 – tiếng Hàn (chỉ câu đã chốt, không cờ)

| # | Việc | Lệnh |
|---|---|---|
| 9 | Chuẩn bị | `python3 scripts/s2_claude_dich.py --chuan-bi --tu X --den Y` → M câu |
| 10 | Tác tử TẠO dịch | Agent với `giao_viec_tao_gd2.md` ({{SO_CAU}} = M) |
| 11 | Nhận | `python3 scripts/s2_claude_dich.py --nhan --tu X --den Y` → "lỗi 0" |
| 12 | Chuẩn bị soát | `python3 scripts/s2_claude_goi.py --tu X --den Y` |
| 13 | Soát | `python3 CC/xem_gd2.py <id> …` theo mục 5 |
| 14 | Ghi kết quả | `output/claude/ly_do_lo/gd2_X_Y.json` (`"giai_doan": "2"`, liệt kê **mọi** câu GĐ2) → `ghi_ly_do.py` |
| 15 | Python kiểm tra | `python3 scripts/s2_kiem_tra.py --tu X --den Y` → `ĐẠT`; xử lý lỗi / D4 / D12 / D13 / D15 rồi chạy lại |
| 16 | Báo cáo + nhật ký | mục 7 |

Excel CTV (khi người dùng yêu cầu): `python3 scripts/s3_xuat_ctv.py --tu A --den B` (ĐẠT → CTV tiếng Hàn; đoạn văn hiện ở dòng câu con đầu của mỗi đoạn) · `python3 scripts/s3b_xuat_ctv_nhat.py --tu A --den B` (câu có cờ + câu tạo mới → CTV tiếng Nhật) → `output/reports/ctv/`.

## 4. Soát GĐ1

Chuẩn: **JSON đúng và đủ lời giải gốc** (khuôn chuẩn) · **phần tạo mới đúng đoạn văn + đáp án** (khuôn lạ). Đầy đủ: `prompts/s1_claude_kiem_tra.md`.

**Cờ s0 hay gặp → JSON đúng** (đầy đủ: FLAG_HINT trong `scripts/_dau_vao.py`):

| Cờ | JSON đúng |
|---|---|
| `chuan_A` / `chuan_B` | Nghĩa → `meaning`; trích dẫn đầu dòng / sau nhãn thuần → `quotes` (không 「」, không `Dịch:`); chữ Việt còn lại → `analysis` (bỏ nhãn, bỏ `- `); `→ ĐÚNG/SAI` → `is_match` |
| `chen_tu_nhat` | từ Nhật chen trong câu Việt giữ nguyên, bọc ⟪ ⟫ |
| `nhieu_dung`, `lech_dap_an` | `is_match` theo lời giải, `correct.index` = `dap_an_so` → tác tử KIỂM TRA gắn cờ `dap_an` |
| `lc_khac_de`, `cau_hoi_khac_de` | `option_ja` / `question.ja` chép như LỜI GIẢI → soát: lỗi gõ / ruby → sửa định dạng; khác chữ thật → gắn cờ `nghia_cau` / `khac` |
| `trich_ngoai_doan` | `quotes[].ja` chép như lời giải → soát K-TD (3d-14 #3) |
| `dong_lap` | bỏ dòng lặp – `sua_dinh_dang` `lap_tu` |
| `khuon_la`, `tao_moi` | xem 4.4 |
| `co_dich_doan` | `full_translation` = bản dịch đoạn văn của lời giải (mỗi đoạn một line) |
| `hoi_quan_diem`, `hoi_chi_dinh` | soát kỹ 3d-14 #1 / #2 (cảnh báo K-GC) |

### 4.1 Sửa (lỗi tác tử TẠO / định dạng)
- Trích dẫn giữa câu bị tách làm câu cụt; nhãn thuần / `Dịch:` bị chép; `「」` ngoài cùng ở `quotes[].ja`; nhận xét nhầm lựa chọn (K-PL); `is_match` sai so với lời giải (K4); thiếu ⟪ ⟫ → sửa (`sai_so_ban_goc` / `khach_quan`).
- Định dạng bản gốc: dòng lặp, ruby hỏng, dính câu, dấu câu → `sua_dinh_dang`.

### 4.2 Gắn cờ (`nhom`: `quan_diem`, `phan_tich`, `trich_dan`, `dap_an`, `nghia_cau`, `thieu_noi_dung`, `khac`)
- 3d-14 #1–8: quan điểm tác giả lấy nhầm ý người khác / bỏ qua kết luận; cụm gạch chân giải thích sai; trích dẫn không có / sai chỗ / không chứng minh; phân tích trái đoạn văn; ĐÚNG/SAI trái đáp án; dịch sai nghĩa; từ Nhật chen làm câu Việt vô nghĩa; thiếu giải thích.
- **Phải đọc đoạn văn.** Không gắn cờ: sơ sài nhưng đúng; lựa chọn sai không có trích dẫn; dịch vụng nhưng đúng ý; từ Nhật chen mà câu vẫn hiểu đúng.

### 4.3 File đặc tả lô (một file mỗi lô mỗi giai đoạn)
```json
{"giai_doan": "1",
 "cau": {
  "17042_1": {},
  "19_2": {"thay": [{"duong_dan": "$.options[0].analysis.vi", "cu": "Câu trích dẫn:", "moi": ""}],
           "sua": [{"duong_dan": "$.options[0].analysis.vi", "loai": "sai_so_ban_goc", "muc_do": "nhe", "ly_do": "tác tử TẠO chép nhãn dẫn thuần 'Câu trích dẫn:' vào analysis"}],
           "nghi_noi_dung": [{"vi_tri": "Lựa chọn 1 – giải thích", "nhom": "phan_tich", "mo_ta": "(3d-14 #2) …", "de_xuat": "…"}]}
 }}
```
Ghi bằng python (`os.makedirs('output/claude/ly_do_lo', exist_ok=True)` rồi `json.dump(..., ensure_ascii=False, indent=1)`, heredoc `'EOF'`). Liệt kê **mọi** câu của lô. Danh sách bị **ghi đè** khi chạy lại – sửa thêm thì sửa trong cùng file rồi chạy lại. `duong_dan` = đường dẫn `xem_gd1.py` in ra **thêm `$.`** ở đầu. Sửa bool / cấu trúc (is_match, tách / gộp quotes, đổi null) → python read-modify-write `output/json_vi/checked/<id>.json` + ghi `sua` ở đường dẫn cha (vd `$.options[2].quotes`).

### 4.4 Khuôn lạ – TẠO MỚI
- Soát phần tạo mới như người ra đề (prompt kiểm tra mục "Khuôn lạ"); sai → **sửa trực tiếp** (`khach_quan`, ghi `ly_do`). Không cần gắn cờ `tao_moi` (Python tự gắn).
- Sau `s1_kiem_tra`: câu `CHỜ_DUYỆT_NỘI_DUNG` với dòng `(tao_moi)` → xuất `s3b_xuat_ctv_nhat.py` cho CTV tiếng Nhật.
- **CTV đã duyệt** (Excel trả về): sửa theo CTV (`sua_theo_ctv` + `[Đã sửa theo CTV] …`) rồi đặt khóa duyệt bằng python:
  `python3 -c "import json;p='output/json_vi/checked/<id>.ly_do.json';d=json.load(open(p,encoding='utf-8'));d['ctv_duyet_tao_moi']='<file CTV – ngày>';json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=1)"`
  → `s1_kiem_tra.py --ids <id>` → `GĐ1_XONG` → `s1_chot` → GĐ2.

## 5. Soát GĐ2 – tiếng Hàn

`prompts/s2_claude_kiem_tra.md`: nghĩa câu hỏi / lựa chọn / câu trích **dịch thẳng từ tiếng Nhật** (giữ ①② – D13; `{ }` – D7); **cùng câu trích dịch giống hệt** trong câu (D15) và giữa các câu con (D4 – `output/reports/khong_nhat_quan.csv`); giải thích văn phong -습니다, '필자', '본문'; bản dịch đoạn văn (nếu có) văn viết -다; trợ từ sau ⟪kana⟫ theo âm cuối cách đọc (D12 – chỉ cảnh báo, tự soát). Đoạn văn không dịch.

## 6. Sự cố thường gặp

| Hiện tượng | Xử lý |
|---|---|
| `--nhan` GĐ1 LỖI_KỸ_THUẬT | `s1_claude_tao.py --chuan-bi --ids <id> --force` → giao lại → `--nhan --ids <id>` |
| `--nhan` GĐ2 LỖI_GĐ2 | `s2_claude_dich.py --chuan-bi --ids <id> --force` → giao lại → `--nhan --ids <id>` |
| `s1_kiem_tra` LỖI_GĐ1 K-PL / K5 / K6 / K7 | thường là lỗi tác tử TẠO (nhận xét nhầm lựa chọn, chép nhầm) → sửa file checked → `s1_kiem_tra --ids <id>`. Nếu do Python tách lời giải sai (khối lựa chọn lạ) → báo người dùng, sửa `scripts/_doc_hieu_14.py` (backup `$HOME/bak14`), chạy lại `python3 scripts/s0_chuan_bi.py` – **không** thêm `--tao-lai-thu-tu`; ghi NHAT_KY |
| "Độ phủ tiếng Việt … thiếu: [nhãn lạ]" | nhãn mới của lời giải → báo người dùng, thêm vào `NHAN_TRICH` / `NHAN_PHAN_TICH` / `_NHAN_DONG` trong `scripts/_doc_hieu_14.py` |
| K-TM (khuôn lạ) | trích dẫn tạo mới không có trong đoạn văn → chép lại nguyên câu của đoạn văn |
| `nhom 'X' không hợp lệ` | dùng đúng danh sách mục 4.2; nhóm mới → báo người dùng (code chung) |
| `[Lỗi JSON VI]` ở GĐ2 → CẦN_SỬA_GĐ1 | `s1_claude_goi --ids <id>` → sửa → `s1_kiem_tra` → `s1_chot` → GĐ2 lại |
| Lô đang dở | `CC/tien_do.py X Y` (soát 'dở' = còn `_huong_dan`); chạy tiếp từ bước đó |

## 7. Báo cáo cuối lô (tiếng Việt, ngắn)

1. Bảng ĐẠT / cờ nội dung / tạo mới (id), theo đoạn văn. 2. Mỗi câu gắn cờ: 1 dòng lý do; sửa định dạng / sửa ko: liệt kê ngắn. 3. Lũy kế (`CC/tien_do.py`). 4. Lệnh tiếp: **"Chạy dạng 14 lô <n+1>"** (sau lô thứ 3: đề nghị mở cuộc trò chuyện mới).

Sau báo cáo **cập nhật `NHAT_KY.md`**: dòng bảng lô; quyết định / cách dịch mới; sự cố; chi phí token tác tử TẠO.

## 8. Lưu ý rút ra từ lô 1–2 (2026-10-08)

- **K5 / K6 / K7 chưa nhận mục `sua_dinh_dang`** cho `question.ja`, `option_ja`, `quotes[].ja` (dù mục 4 / prompt kiểm tra nói có): sửa lỗi gõ / dòng lặp ở các trường tiếng Nhật này → `LỖI_GĐ1`. Tạm thời **không sửa**, chỉ ghi `[Ghi chú] …` (chờ người dùng quyết định sửa code hay bỏ hướng dẫn). Nếu lỡ sửa: chép lại giá trị từ `output/json_vi/claude_tao/<id>.json` và xóa `sua` trong `.ly_do.json` (ghi_ly_do không xóa `sua` cũ khi mục câu không còn khóa `sua`).
- `s1_kiem_tra.py --ids` nhận danh sách **cách nhau dấu phẩy** (`--ids a,b`); câu chưa có `.ly_do.json` thì không kiểm tra được.
- Khuôn lạ: trích dẫn tạo mới **không giữ `{ }`** của đoạn văn (Python báo '{ } thừa') – bỏ `{ }` ở cả `ja` và `meaning`.
- Tác tử TẠO hay **bỏ câu dịch "…" đứng trước câu Nhật** (kiểu 'Trích dẫn: "<câu Việt>" (<câu Nhật>) (<dịch>)') → Python báo độ phủ / K-PL → đưa câu "…" về dòng đầu `analysis` (`sai_so_ban_goc`).
- Lời giải có giải thích **toàn tiếng Nhật** hoặc **kanji rời thay chữ Hán Việt** (⟪表⟫ ⟪示⟫) → gắn cờ (`khac` / `nghia_cau` #7), không sửa.
- Đề có câu lựa chọn trái đoạn văn (nghi đề gõ sai) → gắn cờ `dap_an` / `nghia_cau` để CTV tiếng Nhật xác nhận.
- GĐ2: chữ Hán để trần ngoài ⟪ ⟫ trong bản Hàn → `LỖI_GĐ2` → viết bằng chữ Hàn (十 → '열 십' 자). Thuật ngữ câu hỏi (vd 本人の顔 → '본인의 얼굴') phải thống nhất với phần giải thích. Lời giao việc GĐ2: thêm dòng này vào {{CAU_CO_DINH}}.
- (2026-10-10 lô 20) Dòng dán lặp (cờ `dong_lap`): s0 tự bỏ bằng `bo_dong_lap()` cho câu chưa qua GĐ1 (ghi chú `[Python sửa định dạng] Bỏ dòng dán lặp`) – tác tử TẠO bỏ bản lặp là đúng, không cần mục `sua`.
