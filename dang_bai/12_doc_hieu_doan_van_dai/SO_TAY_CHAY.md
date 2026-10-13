# Sổ tay chạy – dạng 12 Đọc hiểu: Đoạn văn dài (cho phiên Claude mới)

> Viết 2026-10-08. Một cuộc trò chuyện Cowork **mới** chỉ cần đọc **file này + `NHAT_KY.md`** là chạy được, **không đọc lại cả project**.
> Câu mở đầu người dùng gõ: **"Đọc dang_bai/12_doc_hieu_doan_van_dai/SO_TAY_CHAY.md rồi chạy dạng 12 lô N"** (hoặc "lô tiếp theo").
> Trả lời người dùng bằng **tiếng Việt**. Dạng 12 chạy **hoàn toàn bằng Claude Opus 5.5 Cowork** – không có bước GPT API.

---

## 0. Khởi động phiên (làm theo thứ tự)

1. Nạp công cụ: ToolSearch `select:mcp__remote-devices__device_bash`. Mọi lệnh chạy trên máy người dùng bằng công cụ này.
2. `DANG=$HOME/mnt/Vie-Kor/dang_bai/12_doc_hieu_doan_van_dai` – **mỗi lệnh đều `cd $DANG` trước** (mỗi lần gọi là shell mới). Công cụ chung: `python3 ../../pipeline_chung/cong_cu/<tên>.py` (gọi tắt `CC/<tên>.py`).
3. Kiểm tra SudachiPy: `python3 -c 'import sudachipy'` – lỗi thì `pip install --user sudachipy sudachidict_core --break-system-packages` (không có thì K-TD không so được theo cách đọc → nhiều cảnh báo giả).
4. Đọc `NHAT_KY.md` (lũy kế, quyết định đã chốt, cách dịch đã thống nhất).
5. `python3 scripts/lo.py` → lô tiếp theo + khoảng `--tu X --den Y` (lô = **2 đoạn văn, 6–8 câu**; luôn chạy trọn lô – không cắt đôi đoạn văn). Lô cụ thể: `python3 scripts/lo.py N`; cả bảng: `python3 scripts/lo.py --tat-ca`. Từng mẫu: `python3 CC/tien_do.py X Y` (trạng thái + bước đã qua) → biết lô chưa làm hay đang dở (mục 6).
5b. **Chỉ chạy mẫu thuộc đề JLPT từ stt 260** (quyết định người dùng 2026-10-11, `config.loc_nguon_de`): mẫu mà cột `thi_thu_thuoc_de` (file dữ liệu, tra theo `sample_id`) có chữ `Nat Test` – kể cả khi có thêm đề khác – bị **bỏ tự động** ở mọi script khi chọn bằng `--tu/--den` (stt theo `output/thu_tu_chay.csv`), `--lo`, `--tat-ca` (dòng in "Lọc nguồn đề … bỏ N mẫu thuộc NAT-TEST"). Mẫu ô trống (chỉ luyện tập) và mẫu đề Test / Reading Test / Vocabulary Test / Mock Full Exam vẫn chạy. Mẫu stt < 260 giữ nguyên kết quả; `thu_tu_chay.csv` và cột `lo` **không đổi**. **Chọn lô bằng `python3 scripts/lo_jlpt.py --lo 3`** (in `Lô <số>: --tu X --den Y (n mẫu JLPT, bỏ m mẫu NAT)`, bỏ qua lô toàn NAT / đã xong) thay cho gợi ý lô của `CC/tien_do.py` và `scripts/lo.py` (các công cụ này vẫn đếm mẫu NAT là `ĐANG_XỬ_LÝ` / chưa xong – sẽ mãi chỉ vào mẫu NAT). Thống kê: `python3 scripts/lo_jlpt.py --thong-ke`. Muốn chạy cả mẫu NAT cho một lệnh: thêm `--ca-nat`; `--ids`, `--pilot` không bị lọc. Báo cáo lô: ghi các mẫu NAT đã bỏ trong khoảng (lấy từ dòng "Lọc nguồn đề …").
6. Đọc **một lần mỗi phiên** trước khi soát: `prompts/s1_claude_kiem_tra.md` (nhất là mục 2–3), `prompts/s2_claude_kiem_tra.md`.
7. Phạm vi mẫu: `--tu X --den Y` (số thứ tự trong `output/thu_tu_chay.csv`) – không hiện trong `--help` nhưng dùng được với mọi script. **Không dùng `--lo` với `scripts/s*.py`**. `CC/xem_gd1.py` / `CC/xem_gd2.py`: `--lo X Y` = khoảng số thứ tự.
8. Phiên không có công cụ **Agent** → **dừng, báo người dùng** (không tự tạo bản thay tác tử TẠO).

## 1. Quy tắc bất biến

- **Bảo mật:** không đọc / mở `.env`, không in API key. Không chạy `git status`.
- **Không xóa file** (bị chặn) – cần bỏ thì `mv -n` vào `_to_delete/`.
- **Nội dung lời giải sai → chỉ gắn cờ** `nghi_noi_dung`, **không sửa**. Chỉ sửa **định dạng** (`sua_dinh_dang` + `nhom` + dòng `[Đã sửa định dạng] …`) và **lỗi của tác tử TẠO**. Ghi chú không kèm thay đổi JSON → `[Ghi chú] …`.
- **Chạy song song nhiều dạng:** phiên này **chỉ sửa file trong `$DANG`**. Không sửa `pipeline_chung/`, `explanation_schema/`, file của dạng khác. Cần sửa code chung → dừng, mô tả cho người dùng để xử lý ở cuộc trò chuyện điều phối. Được sửa `scripts/_doc_hieu.py` / `_dang.py` / `_dau_vao.py` / prompt của dạng 12 khi Python tách lời giải sai (mục 6), sau khi báo người dùng.
- Ngữ cảnh: tối đa **2 lô mỗi cuộc trò chuyện** (lời giải + đoạn văn dài gấp ~3 lần dạng ngữ pháp).

## 2. Hai tác tử

- **Tác tử TẠO (Claude A)** = tác tử con (Agent tool, `subagent_type: "general-purpose"`, `model: "opus"`). GĐ1 chuyển JSON, GĐ2 dịch Hàn. Lời giao việc chép **nguyên văn** từ `prompts/giao_viec_tao_gd1.md` / `prompts/giao_viec_tao_gd2.md` (thay `{{SO_CAU}}`, bỏ dòng `<!-- -->`; GĐ2: thay `{{CAU_CO_DINH}}` bằng các cách dịch đã thống nhất trong NHAT_KY, chưa có thì bỏ cả dòng đó).
- **Tác tử KIỂM TRA** = phiên chính (bạn). Không tự tạo bản; đọc đoạn văn, soát + Python kiểm tra.

## 3. Quy trình một lô X–Y

### GĐ1 – JSON tiếng Việt

| # | Việc | Lệnh |
|---|---|---|
| 1 | Chuẩn bị gói đầu vào | `python3 scripts/s1_claude_tao.py --chuan-bi --tu X --den Y` → số câu N |
| 2 | Tác tử TẠO tạo JSON | Agent với `giao_viec_tao_gd1.md` ({{SO_CAU}} = N). Ghi lại "điểm khó" nó báo |
| 3 | Nhận | `python3 scripts/s1_claude_tao.py --nhan --tu X --den Y` → "lỗi 0, chưa có 0" |
| 4 | Chuẩn bị soát | `python3 scripts/s1_claude_goi.py --tu X --den Y` |
| 5 | Soát | `python3 CC/xem_gd1.py <id> <id> …` (đoạn văn in 1 lần cho mỗi đoạn; 2 câu mỗi lần với N1). So JSON với LỜI GIẢI GỐC **và đọc đoạn văn** theo mục 4 |
| 6 | Ghi kết quả | `output/claude/ly_do_lo/gd1_X_Y.json` → `python3 CC/ghi_ly_do.py output/claude/ly_do_lo/gd1_X_Y.json` |
| 7 | Python kiểm tra | `python3 scripts/s1_kiem_tra.py --tu X --den Y` → có cờ = `CHỜ_DUYỆT_NỘI_DUNG`, còn lại `GĐ1_XONG`; `LỖI_GĐ1` → mục 6 |
| 8 | Chốt | `python3 scripts/s1_chot.py --tu X --den Y` |

### GĐ2 – tiếng Hàn (chỉ mẫu đã chốt)

| # | Việc | Lệnh |
|---|---|---|
| 9 | Chuẩn bị | `python3 scripts/s2_claude_dich.py --chuan-bi --tu X --den Y` → M câu |
| 10 | Tác tử TẠO dịch | Agent với `giao_viec_tao_gd2.md` ({{SO_CAU}} = M) |
| 11 | Nhận | `python3 scripts/s2_claude_dich.py --nhan --tu X --den Y` → "lỗi 0" |
| 12 | Chuẩn bị soát | `python3 scripts/s2_claude_goi.py --tu X --den Y` |
| 13 | Soát | `python3 CC/xem_gd2.py <id> …` (Mã \| Bản nguồn \| Tiếng Hàn) theo mục 5 |
| 14 | Ghi kết quả | `output/claude/ly_do_lo/gd2_X_Y.json` (`"giai_doan": "2"`, liệt kê **mọi** mẫu GĐ2) → `ghi_ly_do.py` |
| 15 | Python kiểm tra | `python3 scripts/s2_kiem_tra.py --tu X --den Y` → `ĐẠT`; xử lý lỗi / D12 / D15 rồi chạy lại |
| 16 | Báo cáo + nhật ký | mục 7 |

Lô gồm toàn câu khuôn bất thường (lô 38–43): GĐ1 vẫn chạy đủ, phần lớn câu sẽ có cờ `thieu_noi_dung` → không có GĐ2.

Excel CTV (khi người dùng yêu cầu): `python3 scripts/s3_xuat_ctv.py --tu A --den B` (mẫu ĐẠT, tiếng Hàn; đoạn văn ghi ở câu đầu của mỗi đoạn), `python3 scripts/s3b_xuat_ctv_nhat.py --tu A --den B` (mẫu có cờ, CTV tiếng Nhật) → `output/reports/ctv/`.

## 4. Soát GĐ1 – trọng tâm dạng 12

Chuẩn: **JSON đúng và đủ lời giải gốc**; lời giải gốc phải **đúng với đoạn văn**. Đầy đủ: `prompts/s1_claude_kiem_tra.md`.

**Cờ s0 trên đầu dòng `xem_gd1` → JSON đúng trông thế nào** (đầy đủ: `scripts/_dau_vao.py` – FLAG_HINT, `scripts/_doc_hieu.py` – FLAG_TEXT):

| Cờ | JSON đúng / việc của tác tử KIỂM TRA |
|---|---|
| `khuon_chuan` | mục 2 của `s1_chuyen_json.md` |
| `chi_ban_dich` | `question.ja` / `option_ja` theo đề; `meaning` = dòng Việt; `quotes = []`, `analysis = null`; `is_match` theo đáp án. **Gắn cờ `thieu_noi_dung`** (`vi_tri: Toàn bộ lời giải`) |
| `tu_do` | toàn bộ lời giải vào `analysis` của lựa chọn đáp án; **gắn cờ `thieu_noi_dung`** |
| `can_hinh` | chép như lời giải (lựa chọn '1'…'4'); **gắn cờ `thieu_noi_dung`** – "câu hỏi dùng hình, dữ liệu không có hình" |
| `khong_du_4_khoi` | khối thiếu: lựa chọn theo đề, `meaning`/`analysis` null; **gắn cờ `thieu_noi_dung`** |
| `danh_gia_lech_dap_an` / `khong_danh_gia_dung` | `is_match` theo LỜI GIẢI; **gắn cờ `dap_an`** (sau khi đọc đoạn văn: đề sai hay lời giải sai) |
| `trich_lech_doan_van_nhe` | xem bên nào gõ sai: câu trích → `sua_dinh_dang`; đoạn văn → `[Ghi chú]` |
| `trich_lech_doan_van_nang` / `trich_khong_tim_thay` | đối chiếu tay; khác chữ – nghĩa / không có → **cờ `trich_dan`**; chỉ khác cách viết → `[Ghi chú]` |
| `lua_chon_khac_de` / `cau_hoi_khac_de` | JSON chép như lời giải; đề gõ sai → `[Ghi chú]`; lời giải gõ sai → `sua_dinh_dang`; khác nghĩa → cờ `khac` |
| `nhan_tieng_nhat` | lời giải dịch máy ngược – **gắn cờ `khac`** (câu vô nghĩa) |
| `tieng_nhat_tran` | ⟪ ⟫ quanh từ Nhật; câu đọc hiểu được → bình thường; vô nghĩa → cờ `khac` |
| `co_dau_khac` | dòng 1 → `question.ja`, mọi dòng còn lại phần đầu → `question.meaning` |
| `furigana_hong` / `ky_tu_rac` / `dong_nhay_le` | Python đã sửa (ghi chú `[Python sửa định dạng]`) – soát phần rác còn lại → `sua_dinh_dang` `nhom: ky_tu` |

**Soát nội dung (mỗi câu, đọc đoạn văn):** (1) câu trích có thật & đúng chỗ, chứng minh được nhận xét → `trich_dan`; (2) phân tích từng lựa chọn khớp đoạn văn ("không đề cập" mà thực ra có, hiểu sai これ / それ, sai quan hệ câu trước – sau) → `phan_tich`; (3) đáp án hợp lý → `dap_an`; (4) nghĩa câu hỏi / lựa chọn / câu trích đúng câu Nhật → `nghia_cau`.
`nhom` hợp lệ cho dạng 12: `trich_dan`, `phan_tich`, `dap_an`, `nghia_cau`, `thieu_noi_dung`, `khac`.

**File đặc tả lô:** mẫu ở cuối `prompts/s1_claude_kiem_tra.md`. Ghi bằng python (`json.dump(..., ensure_ascii=False, indent=1)`, nội dung qua heredoc `'EOF'`). Liệt kê **mọi** mẫu của lô. Một file cho mỗi lô mỗi giai đoạn: chạy lại thì sửa trong cùng file (các khóa danh sách bị ghi đè). `duong_dan` = đường dẫn `xem_gd1.py` in ra **thêm `$.`** (`options[0].quotes[0].ja` → `$.options[0].quotes[0].ja`). `thay` chỉ cho sửa chuỗi nhỏ; sửa cấu trúc (dời câu trích từ `analysis` sang `quotes`…) thì python read-modify-write `output/json_vi/checked/<id>.json` + ghi `sua`.

## 5. Soát GĐ2 – tiếng Hàn

Đầy đủ: `prompts/s2_claude_kiem_tra.md`. Trọng tâm:
- **JA** (nghĩa câu hỏi / lựa chọn / câu trích): sát câu Nhật; câu hỏi phủ định giữ phủ định; **cùng câu trích → cùng bản dịch** (D15 trong câu; giữa các câu của đoạn văn đối chiếu bảng cả lô + D4 `output/reports/khong_nhat_quan.csv`).
- **VI** (`analysis`): đủ ý; 'đoạn văn' → 본문, 'tác giả' → 필자; văn phong -습니다.
- **Trợ từ sau ⟪kana⟫ theo âm cuối cách đọc tiếng Nhật** (D12 chỉ cảnh báo – tự soát cả khi có nháy / ngoặc): ん → 은/이/을/과/이라는/이라고/이며/으로; nguyên âm → 는/가/를/와/라는/라고/며/로.
- Sửa ko: `thay` với `duong_dan` tới `….ko`; `sua` ghi đường dẫn object. JSON tiếng Việt sai → `loi_json_vi: ["[Lỗi JSON VI] …"]`.

## 6. Sự cố thường gặp

| Hiện tượng | Xử lý |
|---|---|
| `--nhan` GĐ1 LỖI_KỸ_THUẬT (schema / JSON hỏng) | `s1_claude_tao.py --chuan-bi --ids <id> --force` → giao lại tác tử TẠO mẫu đó → `--nhan --ids <id>` |
| `--nhan` GĐ2 LỖI_GĐ2 | `s2_claude_dich.py --chuan-bi --ids <id> --force` → giao lại → `--nhan --ids <id>` |
| `s1_kiem_tra` LỖI_GĐ1 (K…, độ phủ, furigana) | sửa file checked (lỗi tác tử TẠO / định dạng) → `s1_kiem_tra --ids <id>` |
| K9 thiếu chữ ở một khối nhưng JSON đúng (Python tách khối sai, vd nhận xét có dòng bắt đầu `2.`) | báo người dùng; sửa `scripts/_doc_hieu.py` (backup vào `$HOME/bak12` trước), chạy lại `python3 scripts/s0_chuan_bi.py` – **không** thêm `--tao-lai-thu-tu`; ghi NHAT_KY |
| K-TD báo nhiều "khác" giả | kiểm tra SudachiPy (mục 0.3); chạy lại s0 |
| `nhom 'X' không hợp lệ` | dùng đúng danh sách `nhom` ở mục 4; cần nhóm mới → báo người dùng (code chung) |
| `s2_kiem_tra` báo `[Lỗi JSON VI]` → CẦN_SỬA_GĐ1 | `s1_claude_goi --ids <id>` → sửa → `s1_kiem_tra` → `s1_chot` → GĐ2 lại |
| Lô đang dở | `CC/tien_do.py X Y` cho biết bước đã qua (soát 'dở' = còn `_huong_dan`); chạy tiếp từ bước đó |

## 7. Báo cáo cuối lô (tiếng Việt, ngắn)

1. Bảng ĐẠT / nghi nội dung (id). 2. Mỗi mẫu gắn cờ: 1 dòng lý do; sửa định dạng / sửa ko: liệt kê ngắn. 3. Lũy kế (`CC/tien_do.py`). 4. Lệnh tiếp: **"Chạy dạng 12 lô <N+1>"** (sau lô thứ 2: đề nghị mở cuộc trò chuyện mới).

Sau báo cáo **cập nhật `NHAT_KY.md`**: dòng bảng lô (kèm token / thời gian tác tử TẠO); quyết định / cách dịch mới; sự cố.
