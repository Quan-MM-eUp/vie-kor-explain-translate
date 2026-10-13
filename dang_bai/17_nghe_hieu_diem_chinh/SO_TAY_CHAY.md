# Sổ tay chạy – dạng 17 Nghe hiểu điểm chính (cho phiên Claude mới)

> Viết 2026-10-08. Một cuộc trò chuyện Cowork **mới** chỉ cần đọc **file này + `NHAT_KY.md`** là chạy được, **không đọc lại cả project**.
> Câu mở đầu người dùng gõ: **"Đọc dang_bai/17_nghe_hieu_diem_chinh/SO_TAY_CHAY.md rồi chạy dạng 17 mẫu X đến Y"** (hoặc "… lô tiếp theo").
> Trả lời người dùng bằng **tiếng Việt**. Dạng 17 chạy **hoàn toàn bằng Claude Opus 5.5 Cowork** – không GPT API.
> **Lô chuẩn = 10 câu** (1–10, 11–20 …). Mỗi câu độc lập (một bài nghe). Kế hoạch đã duyệt: `KE_HOACH_PIPELINE.md` (Q1–Q8 đồng ý theo đề xuất).

---

## 0. Khởi động phiên

1. Nạp công cụ: ToolSearch `select:mcp__remote-devices__device_bash`. Mọi lệnh chạy trên máy người dùng.
2. `DANG=$HOME/mnt/Vie-Kor/dang_bai/17_nghe_hieu_diem_chinh` – **mỗi lệnh `cd $DANG` trước**. Công cụ chung: `python3 ../../pipeline_chung/cong_cu/<tên>.py` (gọi tắt `CC/<tên>.py`).
3. Đọc `NHAT_KY.md`.
4. `python3 CC/tien_do.py` (lũy kế, lô gợi ý) và `python3 CC/tien_do.py X Y` (từng mẫu). **Từ stt 331: lấy lô bằng `python3 scripts/lo_jlpt.py` (mục 6b), bỏ qua lô gợi ý của `tien_do.py`.**
5. Đọc **một lần mỗi phiên** trước khi soát: `prompts/s1_claude_kiem_tra.md` và `prompts/s2_claude_kiem_tra.md`.
6. Phạm vi `--tu X --den Y` = stt trong `output/thu_tu_chay.csv`. **Không dùng `--lo` với `scripts/*.py`**; `scripts/xem_17.py --lo X Y` và `CC/xem_gd2.py --lo X Y` = khoảng stt.
6b. **Chỉ chạy mẫu thuộc đề JLPT từ stt 331** (quyết định người dùng 2026-10-11, `config.loc_nguon_de`): mẫu mà cột `thi_thu_thuoc_de` (file dữ liệu, tra theo sample_id) có chữ `Nat Test` – kể cả khi có thêm đề khác – bị **bỏ tự động** ở mọi script khi chọn bằng `--tu/--den` (dòng in "Lọc nguồn đề … bỏ N mẫu thuộc NAT-TEST"). Mẫu ô trống (chỉ luyện tập) và mẫu đề Test / Listening Test / Reading Test / Vocabulary Test / Mock Full Exam vẫn chạy. Mẫu stt 1–330 giữ nguyên kết quả; 92 câu khuôn D (`LỖI_GĐ1`, stt 990–1081) vẫn bỏ qua như cũ (Q2), `lo_jlpt.py` không tính vào lô. **Chọn lô bằng `python3 scripts/lo_jlpt.py --lo 3`** (in khoảng `--tu X --den Y` = stt trong `output/thu_tu_chay.csv`, chứa 10 mẫu JLPT chưa làm) **thay cho "Lô tiếp theo gợi ý" của `CC/tien_do.py`** (công cụ chung vẫn đếm mẫu NAT là `ĐANG_XỬ_LÝ` – các mẫu NAT này sẽ mãi ở `ĐANG_XỬ_LÝ`, bình thường). Thống kê: `python3 scripts/lo_jlpt.py --thong-ke`. Muốn chạy cả mẫu NAT cho một lệnh: thêm `--ca-nat`; `--ids` / `--pilot` không bị lọc. Sao lưu trước khi sửa: `_sao_luu/2026-10-11_truoc_loc_jlpt/`.
7. Phiên không có công cụ **Agent** → dừng, báo người dùng.
8. `output/` đã có sẵn kết quả s0 (chuẩn hóa 1081 câu, `thu_tu_chay.csv`). Chạy lại s0 (`python3 scripts/s0_chuan_bi.py`) chỉ khi dữ liệu gốc / `_dang.py` đổi – **không** thêm `--tao-lai-thu-tu`.

## 1. Quy tắc bất biến

- **Bảo mật:** không đọc `.env`, không in API key, không chạy `git status`. **Không xóa file** – cần bỏ thì `mv -n` vào `_to_delete/`.
- **Nội dung lời giải sai → chỉ gắn cờ** `nghi_noi_dung`, không sửa. Chỉ sửa **định dạng** (`sua_dinh_dang` + `nhom` + dòng `[Đã sửa định dạng] …`) và **lỗi của tác tử TẠO**. Không sửa chữ tiếng Nhật của lời thoại.
- **Chạy song song nhiều dạng:** chỉ sửa file trong `$DANG`; không sửa `pipeline_chung/`, `explanation_schema/`, dạng khác. Cần sửa code chung → dừng, báo người dùng.
- Ngữ cảnh: tối đa **3 lô (30 câu) mỗi cuộc trò chuyện**.
- Khuôn D (92 câu không có tiếng Việt) ở trạng thái `LỖI_GĐ1`, xếp cuối thứ tự chạy – **bỏ qua** (Q2); danh sách `output/reports/khuon_D.csv`, xuất cho CTV: `s3b_xuat_ctv_nhat.py … --khuon-d`.

## 2. Hai tác tử

- **Tác tử TẠO (Claude A)** = tác tử con (Agent, `subagent_type: "general-purpose"`, `model: "opus"`). Lời giao việc chép **nguyên văn** `prompts/giao_viec_tao_gd1.md` / `giao_viec_tao_gd2.md` (thay `{{SO_CAU}}`, bỏ dòng `<!-- -->`; GĐ2 thay `{{CAU_CO_DINH}}` bằng mục "Cách dịch đã thống nhất" trong NHAT_KY, chưa có thì "(chưa có)").
- **Tác tử KIỂM TRA** = phiên chính (bạn). Không tự tạo bản.

## 3. Quy trình một lô X–Y

### GĐ1 – JSON tiếng Việt

| # | Việc | Lệnh |
|---|---|---|
| 1 | Chuẩn bị | `python3 scripts/s1_claude_tao.py --chuan-bi --tu X --den Y` → N câu (gói có **khung JSON** Python dựng sẵn) |
| 2 | Tác tử TẠO | Agent với `giao_viec_tao_gd1.md` ({{SO_CAU}} = N). Ghi lại "điểm khó" |
| 3 | Nhận | `python3 scripts/s1_claude_tao.py --nhan --tu X --den Y` → "lỗi 0, chưa có 0" (Python bỏ `reference_raw`, chép nghĩa key_info – Q3) |
| 4 | Chuẩn bị soát | `python3 scripts/s1_claude_goi.py --tu X --den Y` |
| 5 | Soát | `python3 scripts/xem_17.py --lo X Y` (lời thoại SONG SONG Nhật → Việt + dòng Việt gốc + gợi ý Python) – theo mục 4 |
| 6 | Ghi kết quả | `output/claude/ly_do_lo/gd1_X_Y.json` (mục 4.3) → `python3 CC/ghi_ly_do.py output/claude/ly_do_lo/gd1_X_Y.json` |
| 7 | Python kiểm tra | `python3 scripts/s1_kiem_tra.py --tu X --den Y` → cờ = `CHỜ_DUYỆT_NỘI_DUNG`, còn lại `GĐ1_XONG`; `LỖI_GĐ1` → mục 6 |
| 8 | Chốt | `python3 scripts/s1_chot.py --tu X --den Y` |

### GĐ2 – tiếng Hàn

| # | Việc | Lệnh |
|---|---|---|
| 9 | Chuẩn bị | `python3 scripts/s2_claude_dich.py --chuan-bi --tu X --den Y` → M câu (danh sách ghi `so_ma` cần dịch, `so_ma_sao_chep`) |
| 10 | Tác tử TẠO dịch | Agent với `giao_viec_tao_gd2.md` ({{SO_CAU}} = M) |
| 11 | Nhận | `python3 scripts/s2_claude_dich.py --nhan --tu X --den Y` → Python chép bản Hàn cho mã sao chép (key_info), "lỗi 0" |
| 12 | Chuẩn bị soát | `python3 scripts/s2_claude_goi.py --tu X --den Y` |
| 13 | Soát | `python3 CC/xem_gd2.py --lo X Y` theo mục 5 |
| 14 | Ghi kết quả | `output/claude/ly_do_lo/gd2_X_Y.json` (`"giai_doan": "2"`, liệt kê **mọi** câu) → `ghi_ly_do.py` |
| 15 | Python kiểm tra | `python3 scripts/s2_kiem_tra.py --tu X --den Y` → `ĐẠT` |
| 16 | Báo cáo + nhật ký | mục 7 |

Excel CTV (khi người dùng yêu cầu): `python3 scripts/s3_xuat_ctv.py --tu A --den B` (ĐẠT → CTV tiếng Hàn) · `python3 scripts/s3b_xuat_ctv_nhat.py --tu A --den B [--khuon-d]` (câu có cờ / khuôn D → CTV tiếng Nhật) → `output/reports/ctv/`.

## 4. Soát GĐ1

Chuẩn: **JSON đúng và đủ lời giải gốc**; tiêu chí đầy đủ ở `prompts/s1_claude_kiem_tra.md`. Thứ tự soát mỗi câu:
1. **Ghép cặp** từng dòng `[k] người nói | Nhật → Việt` so với `V…` gốc (đặc biệt cờ `lech_so_dong`, `ghep_gop_dong`, `ghep_nghi_nguoi_noi`, cảnh báo K-NV / K-DV).
2. **Câu hỏi** (không có câu dẫn), **4 lựa chọn + nghĩa**, `✔` đúng đáp án, **key_info** (A: Thông tin · B: [] · C: dòng (i)), **analysis** (B: nguyên văn lý do).
3. **Nội dung**: đọc dòng có `(i)` / dòng in đậm, so nghĩa Việt với tiếng Nhật ở chỗ quyết định đáp án → gắn cờ nếu sai (bảng mục 3 của prompt).

**Cờ s0 hay gặp → JSON đúng** (đầy đủ: `FLAG_HINT` trong `scripts/_dau_vao.py`, `FLAG_TEXT` trong `scripts/_dang.py`):

| Cờ | JSON đúng |
|---|---|
| `loi_thoai_co_lua_chon`, `loi_thoai_co_tu_vung` | Python đã bỏ 4 lựa chọn / phần `*** 言葉表現` khỏi lời thoại – không thêm lại |
| `cau_hoi_trong_loi_thoai`, `cau_hoi_la_so_thu_tu` | `question.ja` = câu hỏi trong lời thoại (đề không có / chỉ ghi '3番') |
| `thong_tin_khong_dich` | `key_info.meaning` do Python chép từ dòng thoại; không có dòng trùng → để null (cảnh báo K-KI, không cờ) |
| `khong_nghia_lua_chon` | `options[*].meaning` = null – bình thường, không cờ |
| `dap_an_ly_do_lech`, `thong_tin_khong_phai_tieng_viet`, `thong_tin_ngoai_loi_thoai` | xem xét gắn cờ `dap_an` / `thong_tin` |
| `in_dam` | Q4: không có `{ }` trong JSON; dòng in đậm chỉ là gợi ý dòng then chốt |

### 4.1 Sửa
- Lỗi tác tử TẠO: ghép lệch, sót nhãn Việt, sót `(i)` ở key_info, câu dẫn trong `question.meaning`, `analysis` sai chỗ, thiếu `⟪ ⟫` → sửa (`sai_so_ban_goc` / `khach_quan`).
- Đổi cấu trúc (gộp / tách dòng, đổi null) → python read-modify-write `output/json_vi/checked/<id>.json` + ghi `sua` cho các đường dẫn bị đổi; `ja` gộp / tách phải nối lại đúng lời thoại (K-LT).
- Định dạng bản gốc (`???`, `❔`, "Người đang ông"…) → `sua_dinh_dang`.

### 4.2 Gắn cờ (`nhom`: `nghia_cau`, `thong_tin`, `phan_tich`, `dap_an`, `loi_thoai`, `thieu_noi_dung`, `khac`)
- Chỉ khi sai ảnh hưởng tới việc hiểu đáp án / dòng then chốt; lỗi gõ nhẹ của lời thoại không gắn cờ (Q8). Không gắn cờ cách xưng hô, phiên âm tên, dịch thoát đúng ý.

### 4.3 File đặc tả lô (một file mỗi lô mỗi giai đoạn)
```json
{"giai_doan": "1",
 "cau": {
  "13594_1": {},
  "24787_1": {"thay": [{"duong_dan": "$.full_translation[0].lines[5].meaning.vi", "cu": "bia thì sao???", "moi": "bia thì sao?"},
                       {"duong_dan": "$.full_translation[0].lines[7].meaning.vi", "cu": "❔ ", "moi": ""},
                       {"duong_dan": "$.question.meaning.vi", "cu": "❔ ", "moi": ""}],
              "sua": [{"duong_dan": "$.full_translation[0].lines[5].meaning.vi", "loai": "sua_dinh_dang", "nhom": "dau_cau", "muc_do": "nhe", "ly_do": "'???' thừa"},
                      {"duong_dan": "$.full_translation[0].lines[7].meaning.vi", "loai": "sua_dinh_dang", "nhom": "ky_tu", "muc_do": "nhe", "ly_do": "ký tự lạ '❔'"},
                      {"duong_dan": "$.question.meaning.vi", "loai": "sua_dinh_dang", "nhom": "ky_tu", "muc_do": "nhe", "ly_do": "ký tự lạ '❔'"}],
              "ghi_chu_ban_goc": ["[Đã sửa định dạng] Lời thoại dòng 5: 'bia thì sao???' → 'bia thì sao?' – dấu hỏi thừa",
                                  "[Đã sửa định dạng] Câu hỏi (dòng 7 + question): '❔ Vật không…' → 'Vật không…' – ký tự lạ"],
              "nghi_noi_dung": []}
 }}
```
Ghi bằng python (`json.dump(..., ensure_ascii=False, indent=1)`, heredoc `'EOF'`). Liệt kê **mọi** câu của lô; danh sách bị **ghi đè** khi chạy lại. Chuỗi trong `xem_17.py`: dòng `[k]` = `$.full_translation[0].lines[k]`, `O[i]` = `$.options[i]`, `KI[k]` = `$.key_info[k]`. Khi `cu` xuất hiện nhiều lần trong chuỗi, lấy đoạn dài hơn cho duy nhất.

## 5. Soát GĐ2 – tiếng Hàn

Theo `prompts/s2_claude_kiem_tra.md`: lời thoại / câu hỏi / lựa chọn / Thông tin **dịch thẳng từ tiếng Nhật** (cột "Bản nguồn" của `xem_gd2.py` ghi `câu Nhật ‖ VI: …`) – đúng số / ngày / giờ / phủ định / thứ tự hành động; **mức kính ngữ theo câu Nhật**; giữ `(i)` (D-I); câu hỏi -ㅂ니까, giống hệt câu hỏi lặp lại trong lời thoại; mã `CHÉP` (key_info) = bản Hàn dòng thoại (D-KI – sửa nguồn thì sửa cả hai); lý do khuôn B dịch từ tiếng Việt, -습니다, giữ `⟪ ⟫`. D-SO (số) là cảnh báo – tự kiểm.

## 6. Sự cố thường gặp

| Hiện tượng | Xử lý |
|---|---|
| `--nhan` GĐ1 LỖI_KỸ_THUẬT | `s1_claude_tao.py --chuan-bi --ids <id> --force` → giao lại → `--nhan --ids <id>` |
| `--nhan` GĐ2 LỖI_GĐ2 (thiếu mã) | kiểm tra tác tử TẠO có ghi đủ mã (trừ `sao_chep`); `s2_claude_dich.py --chuan-bi --ids <id> --force` → giao lại |
| `s1_kiem_tra` LỖI_GĐ1 K-LT / K-NG | sửa `ja` / `speaker` theo `luot` trong `output/samples/norm/<id>.json` → `s1_kiem_tra --ids <id>` |
| K-DV lỗi dù đã ghép đúng (bản gốc có dòng Việt thừa không ứng lượt nào) | nối dòng đó vào dòng kề phù hợp; nếu là rác (vd tiếng Anh) → `sua_dinh_dang` bỏ + ghi chú |
| Python tách lượt / lựa chọn sai (`luot` sai) | báo người dùng; sửa `scripts/_dang.py` (backup `$HOME/bak17`), chạy lại `python3 scripts/s0_chuan_bi.py` (không `--tao-lai-thu-tu`), `s1_claude_tao.py --chuan-bi --ids … --force`; ghi NHAT_KY |
| `nhom 'X' không hợp lệ` | dùng đúng danh sách mục 4.2; nhóm mới → báo người dùng (code chung) |
| `[Lỗi JSON VI]` ở GĐ2 → CẦN_SỬA_GĐ1 | `s1_claude_goi --ids <id>` → sửa → `s1_kiem_tra` → `s1_chot` → GĐ2 lại |
| Lô đang dở | `CC/tien_do.py X Y`; chạy tiếp từ bước đó |

## 7. Báo cáo cuối lô (tiếng Việt, ngắn)

1. Bảng ĐẠT / nghi nội dung (id). 2. Mỗi câu gắn cờ: 1 dòng lý do; sửa định dạng / sửa ko: liệt kê ngắn. 3. Lũy kế (`CC/tien_do.py`). 4. Lệnh tiếp: **"Chạy dạng 17 mẫu X đến Y"** với X–Y = lô kế tiếp do `python3 scripts/lo_jlpt.py` in (mục 0.6b – từ stt 331 không dùng <Y+1>–<Y+10>) (sau lô thứ 3: đề nghị mở cuộc trò chuyện mới).

Sau báo cáo **cập nhật `NHAT_KY.md`**: dòng bảng lô; quyết định / cách dịch mới; sự cố; token tác tử TẠO đo được (để chốt ước tính chi phí).
