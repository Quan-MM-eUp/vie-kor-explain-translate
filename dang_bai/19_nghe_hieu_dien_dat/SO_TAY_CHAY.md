# Sổ tay chạy – dạng 19 Nghe hiểu diễn đạt (cho phiên Claude mới)

> Viết 2026-10-08. Một cuộc trò chuyện Cowork **mới** chỉ cần đọc **file này + `NHAT_KY.md`** là chạy được, **không đọc lại cả project**.
> Câu mở đầu người dùng gõ: **"Đọc dang_bai/19_nghe_hieu_dien_dat/SO_TAY_CHAY.md rồi chạy dạng 19 mẫu X đến Y"** (hoặc "… lô tiếp theo").
> Trả lời người dùng bằng **tiếng Việt**. Dạng 19 chạy **hoàn toàn bằng Claude Opus 5.5 Cowork** – không có bước GPT API.
> Dạng 19 = đề **nghe**: câu tình huống tiếng Nhật ('… 何と言いますか') + 3 câu nói (nằm trong **transcript**), chọn câu nói phù hợp. Schema `listening_response.v1`. **Lô chuẩn = 12 câu** (1–12, 13–24 …); **lô 1–12 là lô pilot** (có khuôn B, khuôn D, câu có ảnh, câu có furigana).

---

## 0. Khởi động phiên (làm theo thứ tự)

1. Nạp công cụ: ToolSearch `select:mcp__remote-devices__device_bash`. Mọi lệnh chạy trên máy người dùng bằng công cụ này.
2. `DANG=$HOME/mnt/Vie-Kor/dang_bai/19_nghe_hieu_dien_dat` – **mỗi lệnh đều `cd $DANG` trước**. Công cụ chung: `python3 ../../pipeline_chung/cong_cu/<tên>.py` (gọi tắt `CC/<tên>.py`).
3. Đọc `NHAT_KY.md`.
4. `python3 CC/tien_do.py` (lũy kế, lô gợi ý 12 câu) và `python3 CC/tien_do.py X Y` (từng mẫu: trạng thái + bước đã qua).
5. Đọc **một lần mỗi phiên** trước khi soát: `prompts/s1_claude_kiem_tra.md` (tiêu chí GĐ1 – mục 3d-1…7) và `prompts/s2_claude_kiem_tra.md`.
6. Phạm vi: `--tu X --den Y` (stt trong `output/thu_tu_chay.csv`) – do `scripts/_dang.py` xử lý nên không hiện trong `--help`. **Không dùng `--lo` với `scripts/*.py`**; riêng `CC/xem_gd1.py` / `CC/xem_gd2.py`: `--lo X Y` = khoảng stt.
7. Phiên không có công cụ **Agent** → dừng, báo người dùng.
8. `output/` đã có sẵn (s0 chạy 2026-10-08). Chỉ chạy lại `python3 scripts/s0_chuan_bi.py` khi sửa `scripts/_dang.py` / dữ liệu gốc – **không** thêm `--tao-lai-thu-tu` khi đã chạy lô.

## 1. Quy tắc bất biến

- **Bảo mật:** không đọc / mở `.env`, không in API key. Không chạy `git status`. **Không xóa file** – cần bỏ thì `mv -n` vào `_to_delete/`.
- **Nội dung lời giải sai → chỉ gắn cờ** `nghi_noi_dung`, **không sửa**. Chỉ sửa **định dạng** (`sua_dinh_dang` + `nhom` + dòng `[Đã sửa định dạng] …`) và **lỗi của tác tử TẠO**. Ghi chú không kèm thay đổi JSON → `[Ghi chú] …`.
- **Không sửa `prompt.utterance.ja`** (Python điền từ transcript – K-TH). Tách sai → gắn cờ `khac` + báo người dùng (sửa `scripts/_dang.py`, mục 6).
- **Chạy song song nhiều dạng:** chỉ sửa file trong `$DANG`; **không sửa** `pipeline_chung/`, `explanation_schema/`, dạng khác. Cần sửa code chung → dừng, báo người dùng.
- Ngữ cảnh: tối đa **3 lô (36 câu) mỗi cuộc trò chuyện**.

## 2. Hai tác tử

- **Tác tử TẠO (Claude A)** = tác tử con (Agent tool, `subagent_type: "general-purpose"`, `model: "opus"`). Lời giao việc chép **nguyên văn** `prompts/giao_viec_tao_gd1.md` / `giao_viec_tao_gd2.md` (thay `{{SO_CAU}}`, bỏ dòng `<!-- -->`; GĐ2: thay `{{CAU_CO_DINH}}` bằng các dòng của mục "Cách dịch đã thống nhất" trong NHAT_KY).
- **Tác tử KIỂM TRA** = phiên chính (bạn). Không tự tạo bản.

## 3. Quy trình một lô X–Y (12 câu)

### GĐ1 – JSON tiếng Việt

| # | Việc | Lệnh |
|---|---|---|
| 1 | Chuẩn bị | `python3 scripts/s1_claude_tao.py --chuan-bi --tu X --den Y` → N câu (chạy lại an toàn) |
| 2 | Tác tử TẠO | Agent với `giao_viec_tao_gd1.md` ({{SO_CAU}} = N). Ghi lại "điểm khó" |
| 3 | Nhận | `python3 scripts/s1_claude_tao.py --nhan --tu X --den Y` → "lỗi 0, chưa có 0" (Python điền `prompt.utterance.ja`, `reference_raw`) |
| 4 | Chuẩn bị soát | `python3 scripts/s1_claude_goi.py --tu X --den Y` |
| 5 | Soát | `python3 CC/xem_gd1.py <id> …` – phần **"ĐOẠN VĂN" = transcript tiếng Nhật** (+ link ảnh); rồi lời giải gốc, gợi ý Python, JSON |
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
| 15 | Python kiểm tra | `python3 scripts/s2_kiem_tra.py --tu X --den Y` → `ĐẠT`; xử lý lỗi / D12 / D15 / D4 rồi chạy lại |
| 16 | Báo cáo + nhật ký | mục 7 |

Excel CTV (khi người dùng yêu cầu): `python3 scripts/s3_xuat_ctv.py --tu A --den B` (ĐẠT, tiếng Hàn – cột "Ngữ liệu" là transcript) · `python3 scripts/s3b_xuat_ctv_nhat.py --tu A --den B` (câu có cờ, CTV tiếng Nhật) → `output/reports/ctv/`.

## 4. Soát GĐ1

Chuẩn: **JSON đúng và đủ lời giải gốc**; lời giải phải đúng **cách diễn đạt trong tình huống**. Đầy đủ: `prompts/s1_claude_kiem_tra.md`.

**Khuôn và cờ s0 → JSON đúng:**

| Khuôn / cờ | JSON đúng |
|---|---|
| A (330 câu) | `utterance.meaning` = dòng dịch tình huống (không gồm 3 dòng nghĩa phần đầu, không gồm nhãn `Nam:`/`Nữ:`); 3 khối → `options` (`sentence.ja` theo lời giải + furigana, `meaning` = `Nghĩa:`, `is_correct` = kết luận lời giải, `analysis` = phần còn lại) |
| `khuon_B` (14253, 25373) | `utterance.meaning = null` → gắn cờ `thieu_noi_dung` |
| `khuon_D` (34 câu) | `sentence.ja` = transcript, `is_correct` theo đáp án, `analysis = null` → gắn cờ `thieu_noi_dung` |
| `khong_co_tinh_huong_ja` (14253, 22370) | `utterance.ja = ""` → gắn cờ `thieu_noi_dung` |
| `lc_lech_transcript_nhe` | xác định bên sai: lời giải (gõ / furigana lệch, vd 12222 `お｜願い《ねが》い`, 14256 `｜今《きょう》｜日《は》`) → `sua_dinh_dang`; transcript (21473 `いきたいい`, 21400 `くだざい`) → `[Ghi chú] Transcript gõ sai …` |
| `ket_luan_lech_dap_an` / K11 | gắn cờ `dap_an` |
| `ruby_han_viet` (21395, 25368) | Python đã đổi 人《nhân》員《viên》 → 'nhân viên' – chỉ xem lại |
| `tinh_huong_tu_doan_van`, `tinh_huong_khong_nanto`, `tr_ghi_chu` | đối chiếu `utterance.ja` với transcript; tách sai → cờ `khac` + báo người dùng |
| mọi câu | `reading = null`, `situation = null`, `prompt.analysis = []`, `full_sentence = null`, `correct.option_ja` = `sentence.ja` đáp án |

### 4.1 Sửa (lỗi tác tử TẠO / định dạng)
- Tác tử TẠO: chép 3 dòng nghĩa phần đầu / nhãn `Nam:` vào `utterance.meaning`; sót `→ ĐÚNG.` trong `analysis`; `is_correct` khác lời giải; `sentence.ja` theo transcript thay vì lời giải; thiếu ⟪ ⟫ (「～てくれませんか」 → 「⟪～てくれませんか⟫」) → sửa (`sai_so_ban_goc`).
- Định dạng bản gốc: ruby hỏng / lệch phạm vi, dính câu, lặp từ, chính tả → `sua_dinh_dang`.

### 4.2 Gắn cờ (`nhom`: `ly_do_loai`, `y_nghia_cau_truc`, `nghia_cau`, `cau_khac_de`, `dap_an`, `thieu_noi_dung`, `cach_doc`, `khac`)
- 3d-1 lý do chọn / loại sai về cách diễn đạt (kính ngữ – khiêm nhường; あげる / くれる / もらう; ましょうか / ませんか / てもいいですか / てくれませんか; lời chào theo tình huống) → `ly_do_loai`.
- 3d-2 giải thích mẫu câu / sắc thái sai → `y_nghia_cau_truc`. 3d-3 nghĩa lệch câu Nhật (sai chủ thể, mất phủ định…) → `nghia_cau`.
- 3d-4 câu nói lời giải khác transcript về chữ → `cau_khac_de`. 3d-5 đáp án đáng ngờ → `dap_an`. 3d-6 thiếu nội dung → `thieu_noi_dung`. 3d-7 câu tình huống Python tách sai → `khac`.
- **Không gắn cờ:** phân tích ngắn nhưng đúng; câu nói SAI được dịch gượng; lời chào dịch bằng câu tương đương; kana ↔ kanji.

### 4.3 File đặc tả lô (một file mỗi lô mỗi giai đoạn)
```json
{"giai_doan": "1",
 "cau": {
  "21479_1": {},
  "12222_1": {"thay": [{"duong_dan": "$.options[0].sentence.ja", "cu": "お｜願い《ねが》い", "moi": "お｜願《ねが》い"},
                       {"duong_dan": "$.correct.option_ja", "cu": "お｜願い《ねが》い", "moi": "お｜願《ねが》い"}],
              "sua": [{"duong_dan": "$.options[0].sentence.ja", "loai": "sua_dinh_dang", "nhom": "furigana", "muc_do": "nhe", "ly_do": "furigana lệch phạm vi"},
                      {"duong_dan": "$.correct.option_ja", "loai": "sua_dinh_dang", "nhom": "furigana", "muc_do": "nhe", "ly_do": "furigana lệch phạm vi (bản sao đáp án)"}],
              "ghi_chu_ban_goc": ["[Đã sửa định dạng] Lựa chọn 1 – câu nói: 'お｜願い《ねが》い' → 'お｜願《ねが》い' – furigana lệch phạm vi"]},
  "55070_1": {"nghi_noi_dung": [{"vi_tri": "Lựa chọn 1 – phân tích", "nhom": "thieu_noi_dung", "mo_ta": "(3d-6) Lời giải chỉ dịch tình huống và 3 câu nói – không có kết luận, không phân tích.", "de_xuat": "Bổ sung phân tích 3 lựa chọn"}]}
 }}
```
(Ví dụ 12222 minh họa cách ghi – xác nhận với lời giải thật trước khi sửa; chỉ sửa `correct.option_ja` khi lựa chọn đó là đáp án.)
Ghi bằng python (`os.makedirs('output/claude/ly_do_lo', exist_ok=True)` rồi `json.dump(..., ensure_ascii=False, indent=1)`, heredoc `'EOF'`). Liệt kê **mọi** câu của lô. Danh sách bị **ghi đè** khi chạy lại – sửa thêm thì sửa trong **cùng file** rồi chạy lại. `duong_dan` = đường dẫn `xem_gd1.py` in ra **thêm `$.`** ở đầu. Sửa bool / cấu trúc → python read-modify-write `output/json_vi/checked/<id>.json` + ghi `sua`.

## 5. Soát GĐ2 – tiếng Hàn

Theo `prompts/s2_claude_kiem_tra.md`: câu tình huống + 3 câu nói **dịch thẳng từ tiếng Nhật** – đúng nghĩa, **đúng mức lịch sự / ai làm cho ai** (khớp với phân tích); lời chào cố định → câu tương đương (`glossary_ko.json` mục `cau_noi_co_dinh`); câu nói SAI vẫn dịch đúng như câu đang viết; `何と言いますか` → `뭐라고 말합니까?`; phân tích -습니다, trợ từ sau ⟪kana⟫ theo âm cuối (D12); cùng câu Nhật → cùng bản Hàn (D15 trong câu, D4 giữa các câu – theo bản đã duyệt).

## 6. Sự cố thường gặp

| Hiện tượng | Xử lý |
|---|---|
| `--nhan` GĐ1 LỖI_KỸ_THUẬT | `s1_claude_tao.py --chuan-bi --ids <id> --force` → giao lại → `--nhan --ids <id>` |
| `--nhan` GĐ2 LỖI_GĐ2 | `s2_claude_dich.py --chuan-bi --ids <id> --force` → giao lại → `--nhan --ids <id>` |
| `s1_kiem_tra` LỖI_GĐ1 | đọc lỗi; sửa file checked (lỗi tác tử TẠO / định dạng) → `s1_kiem_tra --ids <id>` |
| `K-TH` (utterance.ja) | không sửa tay; chạy lại `s1_claude_tao.py --nhan --ids <id>` (Python điền lại) rồi `s1_claude_goi --ids <id> --force` |
| Python tách transcript / lời giải sai | báo người dùng; sửa `scripts/_dang.py` (backup `$HOME/bak19`), chạy lại `python3 scripts/s0_chuan_bi.py` – **không** thêm `--tao-lai-thu-tu`; ghi NHAT_KY |
| `nhom 'X' không hợp lệ` | dùng đúng danh sách mục 4.2 |
| `[Lỗi JSON VI]` ở GĐ2 → CẦN_SỬA_GĐ1 | `s1_claude_goi --ids <id>` → sửa → `s1_kiem_tra` → `s1_chot` → GĐ2 lại |
| Lô đang dở | `CC/tien_do.py X Y` (soát 'dở' = còn `_huong_dan`); chạy tiếp từ bước đó |

## 7. Báo cáo cuối lô (tiếng Việt, ngắn)

1. Bảng ĐẠT / nghi nội dung (id). 2. Mỗi câu gắn cờ: 1 dòng lý do; sửa định dạng / sửa KO / transcript gõ sai: liệt kê ngắn. 3. Lũy kế (`CC/tien_do.py`). 4. Lệnh tiếp: **"Chạy dạng 19 mẫu <Y+1> đến <Y+12>"** (sau lô thứ 3: đề nghị mở cuộc trò chuyện mới).

Sau báo cáo **cập nhật `NHAT_KY.md`**: dòng bảng lô; quyết định / cách dịch mới; sự cố.
