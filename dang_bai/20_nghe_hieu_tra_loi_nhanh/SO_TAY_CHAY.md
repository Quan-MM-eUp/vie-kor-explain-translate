# Sổ tay chạy – dạng 20 Nghe hiểu: Trả lời nhanh (cho phiên Claude mới)

> Viết 2026-10-08. Một cuộc trò chuyện Cowork **mới** chỉ cần đọc **file này + `NHAT_KY.md`** là chạy được, **không đọc lại cả project**.
> Câu mở đầu người dùng gõ: **"Đọc dang_bai/20_nghe_hieu_tra_loi_nhanh/SO_TAY_CHAY.md rồi chạy dạng 20 mẫu X đến Y"** (vd 1 đến 10; hoặc "… lô tiếp theo").
> Trả lời người dùng bằng **tiếng Việt**. Dạng 20 chạy **hoàn toàn bằng Claude Opus 5.5 Cowork** – không có bước GPT API.
> Dạng 20: nghe **một câu nói**, chọn **câu đáp lại** (3 lựa chọn). Đề không in lựa chọn – tiếng Nhật nằm ở **script** (cột `transcript_vi`, Python đã tách). **Lô chuẩn = 10 câu** (2 câu mỗi cấp N1–N5; 1–10, 11–20 …). Kế hoạch đã duyệt: `KE_HOACH_PIPELINE.md`.

---

## 0. Khởi động phiên (làm theo thứ tự)

1. Nạp công cụ: ToolSearch `select:mcp__remote-devices__device_bash`. Mọi lệnh chạy trên máy người dùng bằng công cụ này.
2. `DANG=$HOME/mnt/Vie-Kor/dang_bai/20_nghe_hieu_tra_loi_nhanh` – **mỗi lệnh đều `cd $DANG` trước**. Công cụ chung: `python3 ../../pipeline_chung/cong_cu/<tên>.py` (gọi tắt `CC/<tên>.py`).
3. Đọc `NHAT_KY.md`.
4. `python3 CC/tien_do.py` (lũy kế, lô gợi ý 10 câu) và `python3 CC/tien_do.py X Y` (từng mẫu: trạng thái + bước đã qua). **Từ stt 271: lấy lô bằng `python3 scripts/lo_jlpt.py` (mục 6b), bỏ qua lô gợi ý của `tien_do.py`.**
5. Đọc **một lần mỗi phiên** trước khi soát: `prompts/s1_claude_kiem_tra.md` (tiêu chí GĐ1 – mục 3c, 3d-1…7, 3e) và `prompts/s2_claude_kiem_tra.md`. Phần "ghi `.ly_do.json` từng mẫu" làm bằng **file đặc tả lô + `ghi_ly_do.py`** (mục 4.3).
6. Phạm vi: `--tu X --den Y` (stt trong `output/thu_tu_chay.csv`) – do `scripts/_dang.py` xử lý nên không hiện trong `--help`. **Không dùng `--lo` với `scripts/*.py`**; riêng `CC/xem_gd1.py` / `CC/xem_gd2.py`: `--lo X Y` = khoảng stt.
6b. **Chỉ chạy mẫu thuộc đề JLPT từ stt 271** (quyết định người dùng 2026-10-11, `config.loc_nguon_de`): mẫu mà cột `thi_thu_thuoc_de` (file dữ liệu, tra theo sample_id) có chữ `Nat Test` – kể cả khi có thêm đề khác – bị **bỏ tự động** ở mọi script khi chọn bằng `--tu/--den` (dòng in "Lọc nguồn đề … bỏ N mẫu thuộc NAT-TEST"). Mẫu ô trống (chỉ luyện tập) và mẫu đề Test / Listening Test / Reading Test / Vocabulary Test / Mock Full Exam vẫn chạy. Mẫu stt 1–270 giữ nguyên kết quả. **Chọn lô bằng `python3 scripts/lo_jlpt.py --lo 3`** (in khoảng `--tu X --den Y` = stt trong `output/thu_tu_chay.csv`, chứa 10 mẫu JLPT chưa làm) **thay cho "Lô tiếp theo gợi ý" của `CC/tien_do.py`** (công cụ chung vẫn đếm mẫu NAT là `ĐANG_XỬ_LÝ` – các mẫu NAT này sẽ mãi ở `ĐANG_XỬ_LÝ`, bình thường). Thống kê: `python3 scripts/lo_jlpt.py --thong-ke`. Muốn chạy cả mẫu NAT cho một lệnh: thêm `--ca-nat`; `--ids` / `--pilot` không bị lọc. Sao lưu trước khi sửa: `_sao_luu/2026-10-11_truoc_loc_jlpt/`.
7. Phiên không có công cụ **Agent** → dừng, báo người dùng.

## 1. Quy tắc bất biến

- **Bảo mật:** không đọc / mở `.env`, không in API key. Không chạy `git status`. **Không xóa file** – cần bỏ thì `mv -n` vào `_to_delete/`.
- **Nội dung lời giải sai → chỉ gắn cờ** `nghi_noi_dung`, **không sửa**. Chỉ sửa **định dạng** (`sua_dinh_dang` + `nhom` + dòng `[Đã sửa định dạng] …`) và **lỗi của tác tử TẠO**. Ghi chú không kèm thay đổi JSON → `[Ghi chú] …`.
- **Chạy song song nhiều dạng:** chỉ sửa file trong `$DANG`; **không sửa** `pipeline_chung/`, `explanation_schema/`, dạng khác. Cần sửa code chung → dừng, báo người dùng. Được sửa `scripts/_dang.py`, `scripts/_dau_vao.py`, prompt dạng 20 khi lỗi tách lời giải / script (mục 6), sau khi báo.
- Ngữ cảnh: tối đa **3 lô (30 câu) mỗi cuộc trò chuyện**.

## 2. Hai tác tử

- **Tác tử TẠO (Claude A)** = tác tử con (Agent tool, `subagent_type: "general-purpose"`, `model: "opus"`). Lời giao việc chép **nguyên văn** `prompts/giao_viec_tao_gd1.md` / `giao_viec_tao_gd2.md` (thay `{{SO_CAU}}`, bỏ dòng `<!-- -->`; GĐ2: thay `{{CAU_CO_DINH}}` bằng các dòng của mục "Cách dịch đã thống nhất" trong NHAT_KY, chưa có thì bỏ dòng đó).
- **Tác tử KIỂM TRA** = phiên chính (bạn). Không tự tạo bản.

## 3. Quy trình một lô X–Y (10 câu)

### GĐ1 – JSON tiếng Việt

| # | Việc | Lệnh |
|---|---|---|
| 1 | Chuẩn bị | `python3 scripts/s1_claude_tao.py --chuan-bi --tu X --den Y` → N câu (N nhỏ hơn: xem dòng 'bỏ qua …'; chạy lại an toàn) |
| 2 | Tác tử TẠO | Agent với `giao_viec_tao_gd1.md` ({{SO_CAU}} = N). Ghi lại "điểm khó" |
| 3 | Nhận | `python3 scripts/s1_claude_tao.py --nhan --tu X --den Y` → "lỗi 0, chưa có 0" (Python tự điền `prompt.utterance.ja` từ script, `reading = null`) |
| 4 | Chuẩn bị soát | `python3 scripts/s1_claude_goi.py --tu X --den Y` |
| 5 | Soát | `python3 CC/xem_gd1.py <id> …` (đề + **SCRIPT NGHE đã tách** + lời giải gốc + gợi ý + JSON) |
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
| 15 | Python kiểm tra | `python3 scripts/s2_kiem_tra.py --tu X --den Y` → `ĐẠT`; xử lý lỗi / D4 / D12 / D15 rồi chạy lại |
| 16 | Báo cáo + nhật ký | mục 7 |

Excel CTV (khi người dùng yêu cầu): `python3 scripts/s3_xuat_ctv.py --tu A --den B` (ĐẠT, tiếng Hàn – cột "Câu hỏi" = câu nói, "Các lựa chọn" / "Ngữ liệu" = script) · `python3 scripts/s3b_xuat_ctv_nhat.py --tu A --den B` (câu có cờ, CTV tiếng Nhật) → `output/reports/ctv/`.

## 4. Soát GĐ1

Chuẩn: **JSON đúng và đủ lời giải gốc**; lời giải phải đúng **chức năng câu nói** và **sắc thái / mức lịch sự**. Đầy đủ: `prompts/s1_claude_kiem_tra.md`.

**Cờ s0 hay gặp → JSON đúng** (đầy đủ: FLAG_HINT trong `scripts/_dau_vao.py`; số liệu: NHAT_KY):

| Cờ | JSON đúng |
|---|---|
| `khuon_A` | `utterance.meaning` = dòng dịch câu nói (không nhãn); 3 dòng dịch lựa chọn trước ### **không** vào JSON; `sentence.meaning` = `Nghĩa:` |
| `co_nhan_nguoi_noi` | `utterance.meaning` không có `Nam:` / `Nữ:` / `F:` / `Cô gái:` … |
| `khuon_C` | `sentence.ja` = câu trả lời của script, `meaning` = dòng dịch, `is_correct` theo đáp án, `analysis = null` → **luôn gắn cờ `thieu_noi_dung`** |
| `khuon_B`, `khong_dich_cau_noi` | `utterance.meaning = null` → gắn cờ `thieu_noi_dung` |
| `khuon_D` | tác tử TẠO chuyển theo nội dung – soát kỹ từng trường; K có thể báo độ phủ / mất tiếng Nhật do Python không tách được → sửa JSON cho đúng lời giải, hoặc báo người dùng |
| `chen_tu_nhat_dich` | chép nguyên + ⟪ ⟫ (`⟪店⟫ này`) → **gắn cờ `nghia_cau`** (K-NJ), `de_xuat` = nghĩa Việt |
| `dich_lap_lech` | JSON theo `Nghĩa:`; K-TL chỉ cảnh báo |
| `lech_script` | K-SC: kana ↔ kanji / lỗi gõ → không cờ (gõ sai rõ → sửa định dạng); khác nội dung → cờ `cau_khac_de` |
| `co_doan_sau_dich`, `co_doan_truoc_khoi` | câu chữ đó → `prompt.analysis[]` |
| `lua_chon_thua` | 3 lựa chọn; không cờ (đã ghi `output/reports/du_lieu_goc.csv`) |
| `lech_dap_an`, `nhieu_dung`, `du_lieu_loi` | `is_correct` như lời giải, `correct.index = dap_an_so` → gắn cờ `dap_an` / `khac`, báo người dùng |
| mọi câu | `prompt.utterance.ja` / `reading` do Python điền – không sửa (K-UT); `sentence.reading = null`; `correct.full_sentence = null` |

### 4.1 Sửa (lỗi tác tử TẠO / định dạng)
- Lỗi tác tử TẠO: chép nhãn người nói, chép bản dịch trùng lặp trước ###, `is_correct` sai so với dòng ĐÚNG/SAI, còn `→ ĐÚNG/SAI` trong `analysis`, thiếu ⟪ ⟫ → `sai_so_ban_goc` / `khach_quan`.
- Định dạng bản gốc: `。` cuối câu Việt, ruby hỏng (`大学大学`), dính dòng, lỗi gõ câu Nhật so với script → `sua_dinh_dang`.

### 4.2 Gắn cờ (`nhom`: `ly_do_loai`, `sac_thai`, `nghia_cau`, `cau_khac_de`, `dap_an`, `thieu_noi_dung`, `khac`)
- 3d-1 lý do chọn / loại sai (hiểu sai chức năng câu nói); 3d-2 sắc thái / mức lịch sự sai; 3d-3 nghĩa câu sai + chen chữ Nhật; 3d-4 câu Nhật khác script về nội dung; 3d-5 đáp án đáng ngờ; 3d-6 thiếu nội dung (khuôn C luôn cờ); 3d-7 dữ liệu đề lỗi.
- **Không gắn cờ:** phân tích ngắn nhưng đúng; dịch khẩu ngữ vụng nhưng đúng ý; kana ↔ kanji; `lua_chon_thua`; câu ví dụ れい.

### 4.3 File đặc tả lô (một file mỗi lô mỗi giai đoạn) – mẫu minh họa cách ghi
```json
{"giai_doan": "1",
 "cau": {
  "17921_1": {},
  "22764_1": {"nghi_noi_dung": [{"vi_tri": "Câu nói – nghĩa", "nhom": "nghia_cau", "mo_ta": "(quy tắc 3d-3) Bản dịch còn chen chữ Nhật: '⟪｜電《でん》｜車《しゃ》⟫'; Nghĩa lựa chọn 2: '⟪｜出《しゅっ》｜発《ぱつ》⟫'.", "de_xuat": "… chuyến tàu …; Giờ xuất phát muộn thật."}]},
  "14683_1": {"thay": [{"duong_dan": "$.options[0].sentence.meaning.vi", "cu": "giúp tôi。", "moi": "giúp tôi."}],
              "sua": [{"duong_dan": "$.options[0].sentence.meaning", "loai": "sua_dinh_dang", "nhom": "dau_cau", "muc_do": "nhe", "ly_do": "dấu 。 Nhật cuối câu Việt"}],
              "ghi_chu_ban_goc": ["[Đã sửa định dạng] Lựa chọn 1 – nghĩa: 'giúp tôi。' → 'giúp tôi.' – dấu câu Nhật trong câu Việt"]}
 }}
```
Ghi bằng python (`os.makedirs('output/claude/ly_do_lo', exist_ok=True)` rồi `json.dump(..., ensure_ascii=False, indent=1)`, heredoc `'EOF'`). Liệt kê **mọi** câu của lô. Danh sách bị **ghi đè** khi chạy lại – sửa thêm thì sửa trong **cùng file** rồi chạy lại. `duong_dan` = đường dẫn `xem_gd1.py` in ra **thêm `$.`** ở đầu. Sửa bool / cấu trúc → python read-modify-write `output/json_vi/checked/<id>.json` + ghi `sua`.

## 5. Soát GĐ2 – tiếng Hàn

`prompts/s2_claude_kiem_tra.md`: **lời thoại** (nghĩa câu nói, nghĩa câu trả lời) dịch thẳng từ tiếng Nhật, **đúng mức lịch sự** (ため口 → 반말, です/ます → 해요체, kính ngữ / khiêm nhường → 존댓말 / 하십시오체 – D15 chỉ cảnh báo, phải tự soát, nhất là câu mà phân tích nói về "lịch sự / suồng sã"); câu trả lời sai vẫn dịch đúng như câu Nhật; **phân tích** dịch từ bản Việt (-습니다), câu trích lại nghĩa lời thoại khớp bản dịch lời thoại; **trợ từ sau ⟪kana⟫ theo âm cuối cách đọc** (D12); D4 → theo bản đã duyệt.

## 6. Sự cố thường gặp

| Hiện tượng | Xử lý |
|---|---|
| `--nhan` GĐ1 LỖI_KỸ_THUẬT | `s1_claude_tao.py --chuan-bi --ids <id> --force` → giao lại → `--nhan --ids <id>` (chạy lại `--nhan` an toàn: Python tự bỏ / điền lại `utterance.ja`) |
| `--nhan` GĐ2 LỖI_GĐ2 | `s2_claude_dich.py --chuan-bi --ids <id> --force` → giao lại → `--nhan --ids <id>` |
| `s1_kiem_tra` LỖI_GĐ1 | đọc lỗi; sửa file checked (lỗi tác tử TẠO / định dạng) → `s1_kiem_tra --ids <id>`. "Độ phủ … thiếu: [nhãn lạ]" / K-UT do Python tách dịch câu nói sai (nhãn người nói lạ, dòng thừa) → báo người dùng, sửa `scripts/_dang.py` (`SPK_VI`, `_phan_dich`) |
| `nhom 'X' không hợp lệ` | dùng đúng danh sách mục 4.2; nhóm mới → báo người dùng (code chung) |
| Python tách script / lời giải sai, `luu_y` trái lời giải | báo người dùng; sửa `scripts/_dang.py` (backup `$HOME/bak20`), chạy lại `python3 scripts/s0_chuan_bi.py` – **không** thêm `--tao-lai-thu-tu`; ghi NHAT_KY |
| `[Lỗi JSON VI]` ở GĐ2 → CẦN_SỬA_GĐ1 | `s1_claude_goi --ids <id>` → sửa → `s1_kiem_tra` → `s1_chot` → GĐ2 lại |
| Lô đang dở | `CC/tien_do.py X Y` (soát 'dở' = còn `_huong_dan`); chạy tiếp từ bước đó |

## 7. Báo cáo cuối lô (tiếng Việt, ngắn)

1. Bảng ĐẠT / nghi nội dung (id). 2. Mỗi câu gắn cờ: 1 dòng lý do; sửa định dạng / sửa ko: liệt kê ngắn. 3. Lũy kế (`CC/tien_do.py`). 4. Lệnh tiếp: **"Chạy dạng 20 mẫu X đến Y"** với X–Y = lô kế tiếp do `python3 scripts/lo_jlpt.py` in (mục 0.6b – từ stt 271 không dùng <Y+1>–<Y+10>) (sau lô thứ 3: đề nghị mở cuộc trò chuyện mới).

Sau báo cáo **cập nhật `NHAT_KY.md`**: dòng bảng lô; quyết định / cách dịch mới; sự cố; chi phí tác tử TẠO (token, phút) của lô.
