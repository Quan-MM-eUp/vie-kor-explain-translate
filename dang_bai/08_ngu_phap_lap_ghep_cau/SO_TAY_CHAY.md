# Sổ tay chạy – dạng 08 Ngữ pháp: Lắp ghép câu (cho phiên Claude mới)

> Viết 2026-10-08. Một cuộc trò chuyện Cowork **mới** chỉ cần đọc **file này + `NHAT_KY.md`** là chạy được, **không đọc lại cả project**.
> Câu mở đầu người dùng gõ (từ 2026-10-13 **chạy song song**): **"Đọc dang_bai/08_ngu_phap_lap_ghep_cau/SO_TAY_CHAY.md rồi chạy dạng 08 phần A đợt N"** → làm theo **mục 0b** (lô có `--ids` → thêm **mục 0c**). Câu cũ "… chạy dạng 08 mẫu X đến Y" chỉ dùng khi X–Y là một lô trong `phan_cong.json` (hoặc cuộc điều phối, thêm `--ngoai-phan-cong`). **Lưu ý dạng 08:** X–Y là stt trong `output/thu_tu_chay.csv` (100 câu đầu xáo theo cấp độ), không phải stt file dữ liệu.
> Trả lời người dùng bằng **tiếng Việt**. Dạng 08 chạy **hoàn toàn bằng Claude Opus 5.5 Cowork** – không có bước GPT API.

---

## 0. Khởi động phiên (làm theo thứ tự)

1. Nạp công cụ: ToolSearch `select:mcp__remote-devices__device_bash`. Mọi lệnh chạy trên máy người dùng bằng công cụ này.
2. `DANG=$HOME/mnt/Vie-Kor/dang_bai/08_ngu_phap_lap_ghep_cau` – **mỗi lệnh đều `cd $DANG` trước** (mỗi lần gọi là shell mới).
   - **File tạm (script phụ, bản nháp) đặt trong thư mục riêng theo lô `$HOME/tam08_<X>_<Y>/`** – `$HOME` trên VM dùng chung giữa các cuộc song song, tên chung (`$HOME/work`, `$HOME/show.py`) bị ghi đè lẫn nhau. Khi giao việc cho tác tử TẠO cũng nhắc điều này.
   Công cụ chung: `python3 ../../pipeline_chung/cong_cu/<tên>.py` (gọi tắt `CC/<tên>.py`).
3. Đọc `NHAT_KY.md` (lũy kế, quyết định đã chốt, cách dịch đã thống nhất).
4. `python3 CC/tien_do.py` (lũy kế, lô gợi ý) và `python3 CC/tien_do.py X Y` (từng mẫu: trạng thái + bước đã qua: tạo VI / soát VI / chốt VI / tạo KO / soát KO) → biết lô chưa làm hay đang dở (mục 6). Chạy song song: lô lấy từ `PHAN_CONG.md` (mục 0b).
5. Đọc **một lần mỗi phiên** trước khi soát: `prompts/s1_claude_kiem_tra.md` (tiêu chí GĐ1, nhất là 3d–3e), `prompts/s2_claude_kiem_tra.md` (checklist GĐ2). Phần "ghi lý do từng mẫu" trong hai prompt làm bằng **file đặc tả lô + `ghi_ly_do.py`** (mục 4.3).
6. Phạm vi mẫu: `--tu X --den Y` (số thứ tự trong `output/thu_tu_chay.csv`) do `scripts/_dang.py` xử lý nên **không hiện trong `--help`** – vẫn dùng được với mọi script. **Không dùng `--lo` với `scripts/*.py`** (ở đó `--lo N` = N câu đầu theo trạng thái). Riêng `CC/xem_gd1.py` / `CC/xem_gd2.py`: `--lo X Y` = khoảng số thứ tự.
6b. **Chỉ chạy mẫu thuộc đề JLPT từ mẫu 251** (quyết định người dùng 2026-10-11, `config.loc_nguon_de`): mẫu mà cột `thi_thu_thuoc_de` có chữ `Nat Test` bị **bỏ tự động** ở mọi script khi chọn bằng `--tu/--den` (dòng in "Lọc nguồn đề … bỏ N mẫu thuộc NAT-TEST"). Mẫu ô trống (chỉ luyện tập) và mẫu đề Test / Vocabulary / Reading / Mock Full Exam vẫn chạy. Mẫu 1–250 giữ nguyên kết quả. **Chọn lô bằng `cd scripts && python3 lo_jlpt.py --lo 3`** (in khoảng `--tu X --den Y` chứa 10 mẫu JLPT chưa làm, stt theo `output/thu_tu_chay.csv`) thay cho gợi ý lô của `CC/tien_do.py` (công cụ chung vẫn đếm mẫu NAT là `ĐANG_XỬ_LÝ`; `tien_do.py X Y` vẫn dùng để xem từng mẫu). Thống kê + danh sách loại tên đề: `python3 lo_jlpt.py --thong-ke` – nếu in "CÓ LOẠI TÊN ĐỀ MỚI" → dừng, hỏi người dùng. Muốn chạy cả mẫu NAT cho một lệnh: thêm `--ca-nat`; `--ids` không bị lọc.
7. Phiên không có công cụ **Agent** → **dừng, báo người dùng** (không tự tạo bản thay tác tử TẠO).

## 0b. Chạy song song nhiều cuộc trò chuyện (từ 2026-10-12)

Nhiều cuộc trò chuyện cùng chạy dạng 08, mỗi cuộc một **phần** (A, B, C…) gồm các lô đã giao sẵn. Một cuộc là **điều phối** (cuộc người dùng chỉ định).

**Cuộc chạy phần (A/B/C…):**
1. Khởi động như mục 0 (bỏ bước 4 – không tự chọn lô). Đọc thêm các file `nhat_ky_lo/*.md` (nhật ký lô của các cuộc khác chưa gộp – nếu có) sau `NHAT_KY.md`.
2. Mở `PHAN_CONG.md`, lấy các lô của **đúng phần và đợt** người dùng nêu; chạy **lần lượt** từng lô theo mục 3 với `--tu X --den Y` đúng như bảng. Các bước chính (`s1_claude_tao/goi/kiem_tra/chot`, `s2_claude_dich/goi/kiem_tra`) **từ chối** khoảng không có trong `phan_cong.json`.
3. File danh sách việc đặt tên theo lô: lệnh `--chuan-bi` in dòng `[Song song] File danh sách của lô này: output/claude/tao_gd1_danh_sach_X_Y.json` → điền tên file đó vào `{{DANH_SACH}}` của lời giao việc (mục 2). Tương tự `gd1_/tao_gd2_/gd2_danh_sach_X_Y.json`.
4. `CC/xem_gd1.py` không còn in khối GỢI Ý → chạy thêm `cd scripts && python3 goi_y_gd1.py --tu X --den Y` khi soát GĐ1.
5. Bước Python có thể in `[Khóa] Cuộc khác đang chạy bước Python – chờ…` → bình thường, lệnh tự chạy khi đến lượt (chờ tối đa 120 s; quá thì chạy lại lệnh). Lệnh đang giữ khóa tự "báo còn sống" mỗi 15 s; lệnh chết (vd bị cắt 180 s) thì khóa được lấy lại sau 60 s. **Không** xóa / đổi tên gì trong `output/.khoa/`. Không chạy hai bước Python song song trong cùng một lệnh.
6. Cuối mỗi lô **không sửa `NHAT_KY.md`**: ghi `nhat_ky_lo/X_Y.md` (mẫu dưới). `{{CAU_CO_DINH}}` (GĐ2): chạy `cd scripts && python3 trich_cau_co_dinh.py --tu X --den Y` → điền `đọc TOÀN BỘ file DANG/output/claude/cau_co_dinh_X_Y.md` vào `{{CAU_CO_DINH}}` (dạng 08: gạch đầu dòng 'Câu cố định … bổ sung' của `giao_viec_tao_gd2.md`; các câu cố định đã ghi sẵn trong mẫu giữ nguyên) (gồm mục "Cách dịch đã thống nhất" của `NHAT_KY.md` + các `nhat_ky_lo/*.md`).
7. **Không sửa** `scripts/`, `config.json`, `prompts/`, `SO_TAY_CHAY.md`, `phan_cong.json`, `PHAN_CONG.md` (được chạy `lo_jlpt.py --cap-nhat`), không chạy `s0_chuan_bi.py`, không chạy `lo_jlpt.py --phan-cong`. Gặp lỗi Python tách lời giải / cần sửa code → dừng lô đó, báo người dùng để cuộc điều phối xử lý; chạy tiếp lô khác của phần mình nếu không liên quan.
8. Không gợi ý "Chạy dạng 08 mẫu <Y+1> đến …" ở cuối lô – lô tiếp theo là lô kế trong phần. Hết phần: báo người dùng "Phần A đợt N xong".

Mẫu `nhat_ky_lo/X_Y.md` (giữ đúng 4 tiêu đề; mỗi ý một dòng `- …`, bảng lô một dòng `| … |`):
```
# Nhật ký lô X–Y (phần A, đợt N)
## Bảng lô
| X–Y (JLPT, bỏ n NAT) | n | n | id (lý do ngắn), … | ghi chú ngắn |
## Quyết định soát đã chốt
- (lô X–Y) …
## Cách dịch đã thống nhất (GĐ2)
- 〈câu Nhật〉 (id) → 〈bản Hàn〉 …
## Sửa code / sự cố
- …
```

**Cuộc điều phối:**
- Phân công: `cd scripts && python3 lo_jlpt.py --phan-cong 9 --nhom 3` (9 lô kế tiếp → A/B/C mỗi phần 3 lô; lô không cắt ngang nhóm mẫu chung câu Nhật) → ghi `phan_cong.json` + `PHAN_CONG.md` (có sẵn câu mở đầu cho từng cuộc). Tiến độ: `python3 lo_jlpt.py --cap-nhat`.
- Sau mỗi đợt: `python3 scripts/gop_nhat_ky.py --xem` rồi `python3 scripts/gop_nhat_ky.py` (gộp `nhat_ky_lo/*.md` vào `NHAT_KY.md`, chuyển file sang `nhat_ky_lo/da_gop/`); soát lại các quyết định lệch nhau giữa các phần.
- Kiểm tra nhất quán dịch toàn đợt: `python3 scripts/s2_kiem_tra.py --tu <đầu đợt> --den <cuối đợt> --ngoai-phan-cong` → xem D4 (`output/reports/khong_nhat_quan.csv`). D4 dùng bộ nhớ đệm `output/reports/d4_cache.json`; cuộc chạy phần chỉ đọc lại file của mẫu vừa xử lý, còn `--ngoai-phan-cong` / `--d4-day-du` so lại mọi file (sửa tay file final ngoài pipeline → chạy lại với `--d4-day-du`).
- Sửa code / xuất Excel CTV / lưu phản hồi CTV: chỉ cuộc điều phối, khi các cuộc khác **không** đang chạy bước Python (khóa chỉ bảo vệ từng lệnh, không bảo vệ việc sửa code).
- Tắt chế độ song song: `config.song_song.bat = false` (khóa, đổi tên danh sách, kiểm tra phân công đều tắt).

## 0c. Lô giao theo DANH SÁCH ID (từ đợt 2, 2026-10-12)

Lô có cột Lô dạng `X–Y **--ids …**` trong `PHAN_CONG.md` (vd các mẫu đã sửa lỗi GĐ1, nằm rải rác): khoảng X–Y chứa nhiều mẫu cũ đã ĐẠT / chờ CTV – chạy theo khoảng sẽ soát lại và có thể đổi trạng thái của chúng.
1. **Mọi lệnh của lô dùng `--ids <danh sách>` đúng như bảng thay cho `--tu X --den Y`** (`s2_claude_dich/goi/kiem_tra`, `trich_cau_co_dinh.py`…). Dùng `--tu/--den` của lô này bị script từ chối.
2. File danh sách / câu cố định đặt tên `…_ids_<id đầu>.json/.md` (dòng `[Song song] …` in ra) → điền vào `{{DANH_SACH}}` / `{{CAU_CO_DINH}}`.
3. Xem mẫu: `CC/xem_gd2.py <id> <id> …` (không dùng `--lo`).
4. Lô ghi chú "chỉ GĐ2": bỏ bước 1–8, làm từ bước 9.
5. Nhật ký lô đặt tên `nhat_ky_lo/X_Y.md` theo khoảng hiển thị (vd `586_1083.md`).

## 1. Quy tắc bất biến

- **Bảo mật:** không đọc / mở `.env`, không in API key. Không chạy `git status`.
- **Không xóa file** (bị chặn) – cần bỏ thì `mv -n` vào `_to_delete/`.
- **Nội dung lời giải sai → chỉ gắn cờ** `nghi_noi_dung`, **không sửa**. Chỉ sửa **định dạng** (`sua_dinh_dang` + `nhom` + dòng `[Đã sửa định dạng] …`) và **lỗi của tác tử TẠO**. Ghi chú không kèm thay đổi JSON → `[Ghi chú] …`.
- Phần THAM KHẢO: không xử lý (Python chép vào `reference_raw`).
- **Chạy song song nhiều dạng:** phiên này **chỉ sửa file trong `$DANG`**. **Không sửa** `pipeline_chung/`, `explanation_schema/`, file của dạng khác. Cần sửa code chung (vd thêm `nhom` cờ mới vào `pipeline_chung/claude_log.py`) → dừng, mô tả cho người dùng để xử lý ở cuộc trò chuyện điều phối. Được sửa `scripts/_dang.py` / `scripts/_dau_vao.py` / prompt của dạng 08 khi lỗi tách lời giải (mục 6), sau khi báo người dùng.
- Ngữ cảnh: tối đa **3 lô (30 mẫu) mỗi cuộc trò chuyện** (= một phần khi chạy song song).

## 2. Hai tác tử

- **Tác tử TẠO (Claude A)** = tác tử con (Agent tool, `subagent_type: "general-purpose"`, `model: "opus"`). GĐ1 chuyển JSON, GĐ2 dịch Hàn. Lời giao việc chép **nguyên văn** từ `prompts/giao_viec_tao_gd1.md` / `prompts/giao_viec_tao_gd2.md` (thay `{{SO_CAU}}`, bỏ dòng `<!-- -->`; GĐ2: chép các cách dịch đã thống nhất trong NHAT_KY vào dòng "Câu cố định", chưa có thì bỏ dòng đó).
- **Tác tử KIỂM TRA** = phiên chính (bạn). Không tự tạo bản; soát + Python kiểm tra.

## 3. Quy trình một lô X–Y (mặc định 10 mẫu)

### GĐ1 – JSON tiếng Việt

| # | Việc | Lệnh |
|---|---|---|
| 1 | Chuẩn bị gói đầu vào | `python3 scripts/s1_claude_tao.py --chuan-bi --tu X --den Y` → số câu N (N < số mẫu: xem dòng 'bỏ qua …' – mẫu đã có bản tạo / không có lời giải; chạy lại an toàn) |
| 2 | Tác tử TẠO tạo JSON | Agent với `giao_viec_tao_gd1.md` ({{SO_CAU}} = N). Ghi lại "điểm khó" nó báo |
| 3 | Nhận | `python3 scripts/s1_claude_tao.py --nhan --tu X --den Y` → "lỗi 0, chưa có 0" |
| 4 | Chuẩn bị soát | `python3 scripts/s1_claude_goi.py --tu X --den Y` |
| 5 | Soát | `python3 CC/xem_gd1.py <id> <id> …` (2–3 mẫu mỗi lần; `--lo X Y` cho cả lô). So JSON với LỜI GIẢI GỐC theo mục 4 |
| 6 | Ghi kết quả | `output/claude/ly_do_lo/gd1_X_Y.json` (mục 4.3) → `python3 CC/ghi_ly_do.py output/claude/ly_do_lo/gd1_X_Y.json` |
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
| 14 | Ghi kết quả | `output/claude/ly_do_lo/gd2_X_Y.json` (`"giai_doan": "2"`, liệt kê **mọi** mẫu GĐ2, kể cả không sửa) → `ghi_ly_do.py` |
| 15 | Python kiểm tra | `python3 scripts/s2_kiem_tra.py --tu X --den Y` → `ĐẠT`; xử lý lỗi / D4 / D12 / D13 rồi chạy lại |
| 16 | Báo cáo + nhật ký | mục 7 |

Excel CTV (khi người dùng yêu cầu): `python3 scripts/s3_xuat_ctv.py --tu A --den B` (mẫu ĐẠT, tiếng Hàn), `python3 scripts/s3b_xuat_ctv_nhat.py --tu A --den B` (mẫu có cờ, CTV tiếng Nhật) → `output/reports/ctv/`.

## 4. Soát GĐ1 – trọng tâm dạng 08

Chuẩn: **JSON đúng và đủ lời giải gốc**; lời giải gốc phải đúng kiến thức. Đầy đủ: `prompts/s1_claude_kiem_tra.md`.

**Cờ s0 trên đầu dòng `xem_gd1` → JSON đúng trông thế nào** (đầy đủ: `scripts/_dau_vao.py` – FLAG_HINT):

| Cờ | JSON đúng |
|---|---|
| `nhan_de_bai` | `question.ja` không có chữ 'Đề bài:' |
| `de_toan_kana` / `hoan_chinh_toan_kana` / `khong_cach_doc` | `reading = null` |
| `doc_tu_furigana` / `doc_hoan_chinh_ghep` | `reading` = đúng chuỗi Python ghép (ghi chú `[Cách đọc ghép]`) |
| `phan_cau_truc_cau` | phần PHÂN TÍCH CẤU TRÚC CÂU → `sentence_analysis` như PHÂN TÍCH ĐỀ BÀI |
| `thieu_phan_de_bai` | `sentence_analysis = []` |
| `hoi_thoai` | `question.ja` giữ đủ các dòng (`\n`) |
| `co_doan_sau_hoan_chinh` / `lcd_co_nhan_xet` / `co_doan_sau_lcd` | câu chữ đó chép nguyên thành phần tử **cuối** `arrangement.explanation` |
| `nhieu_cau_hoan_chinh` | `full_sentence.ja` = câu ghép khớp đề; câu kia cuối `explanation` + gắn cờ `khac` |
| `khong_cau_hoan_chinh` / `thieu_phan_sap_xep` | `full_sentence.ja` = câu đề (giữ ô trống), reading / meaning = null; gắn cờ `thieu_noi_dung` |
| `lua_chon_dong_la` | câu chữ trước '- Ngữ pháp:' ở đầu `grammar` |
| `khong_gloss` | `gloss = null` |
| `lech_dap_an` / `lcd_go_nham_so` / `khong_so_lcd` | `correct.index` = `dap_an_so` (lệch thật → cờ `dap_an`; gõ nhầm số → chỉ `[Đã sửa định dạng]`) |
| `ghep_lech_nhe` / `ghep_lech_nang` / `sao_lech_dap_an` / `vi_tri_sao_lech` / `kha_nang_sap_xep_lech` | JSON chép nguyên; quyết định sửa định dạng hay gắn cờ theo mục 4.1–4.2 |

**Công cụ riêng dạng 08:** Python đã **ghép câu** (thử mọi thứ tự 4 lựa chọn so với `Câu hoàn chỉnh`) – kết quả nằm trong gợi ý `A:` / cảnh báo `K11`, `K-SX` của `xem_gd1.py`; `arrangement.order` phải bằng thứ tự Python ghép (K-ORD).

### 4.1 Sửa (lỗi tác tử TẠO / định dạng)
- Tác tử TẠO: thiếu ⟪ ⟫, `gloss` sai dạng (đúng: `⟪てがみを⟫ - lá thư`), gộp / tách sai ý, `order` sai, câu hoàn chỉnh đặt nhầm `correct` → sửa (`sai_so_ban_goc` / `khach_quan`).
- Định dạng bản gốc: ★ lẫn trong cách đọc câu hoàn chỉnh (5994) · lỗi gõ dakuten `だけて` → `だけで` (23175) · dấu nháy thừa (19849) · câu hoàn chỉnh lệch đề chỉ do kana gõ nhầm (パーテイー) → `sua_dinh_dang` + `[Đã sửa định dạng]`.

### 4.2 Gắn cờ `nghi_noi_dung` (không sửa) – `nhom` hợp lệ: `cau_khac_de`, `dap_an`, `kha_nang_sap_xep`, `ngu_phap`, `nghia_tu`, `nghia_cau`, `cach_doc`, `thieu_noi_dung`, `khac`
**Gắn cờ khi** (ví dụ thật từ pilot):
- 'Khả năng sắp xếp' nói sai vị trí so với câu đúng (19849: CO2削減 "đứng sau につながる"; cụm '事故をしないような' không có trong đề) → `kha_nang_sap_xep`.
- Giải thích ngữ pháp sai kiến thức (8430: と gọi là "liên từ", ~とみえて dịch "nghe nói"; 19596: すわない ghi là thể ない của すわる "ngồi" thay vì 吸う "hút") → `ngu_phap`.
- Nghĩa câu đề / câu hoàn chỉnh hiểu sai (19849: 無理な dịch "vô lý" như kết quả) → `nghia_cau`.
- Câu hoàn chỉnh khác chữ đề (`ghep_lech_nang`: 5995, 8429) → `cau_khac_de`; ô ★ / Vị trí ★ / LỰA CHỌN ĐÚNG lệch đáp án → `dap_an`.

**KHÔNG gắn cờ khi:** cách nói "có thể đứng trước / sau…" chung chung không trái câu đúng; phân tích đề sơ sài nhưng không sai (19858 chỉ 1 ý); gọi だけで là "phó từ" (≈ 副助詞) – chấp nhận; nghĩa câu đề dịch vụng nhưng giữ đúng ô trống.

### 4.3 File đặc tả lô (một file cho cả lô – xem mẫu thật: `output/claude/ly_do_lo/gd1_1_10.json`)
```json
{"giai_doan": "1",
 "cau": {
  "19858_1": {},
  "23175_1": {"thay": [{"duong_dan": "$.arrangement.full_sentence.reading", "cu": "おもいこみだけて", "moi": "おもいこみだけで"}],
              "sua": [{"duong_dan": "$.arrangement.full_sentence.reading", "loai": "sua_dinh_dang", "nhom": "ky_tu", "muc_do": "nhe", "ly_do": "gõ thiếu dakuten"}],
              "ghi_chu_ban_goc": ["[Đã sửa định dạng] Câu hoàn chỉnh – cách đọc: '…だけて…' → '…だけで…' – gõ thiếu dakuten"]},
  "19596_1": {"nghi_noi_dung": [{"vi_tri": "Phân tích lựa chọn 2 – ngữ pháp", "nhom": "ngu_phap", "mo_ta": "(quy tắc 3d-4) …", "de_xuat": "…"}]}
 }}
```
Ghi bằng python (`json.dump(..., ensure_ascii=False, indent=1)`, nội dung qua heredoc `'EOF'`). Liệt kê **mọi** mẫu của lô. **Một file cho mỗi lô mỗi giai đoạn**: các khóa danh sách bị **ghi đè** khi chạy lại – cần sửa thêm thì sửa mục của mẫu đó **trong cùng file** rồi chạy lại (không tạo file phụ chỉ chứa một phần). `duong_dan` = đường dẫn `xem_gd1.py` in ra **thêm `$.` ở đầu** (`arrangement.full_sentence.reading` → `$.arrangement.full_sentence.reading`). `thay` chỉ cho sửa chuỗi nhỏ; sửa cấu trúc thì python read-modify-write `output/json_vi/checked/<id>.json` + ghi `sua`.

## 5. Soát GĐ2 – tiếng Hàn

Đầy đủ: `prompts/s2_claude_kiem_tra.md`. Trọng tâm:
- **Trợ từ sau ⟪kana⟫ theo âm cuối cách đọc tiếng Nhật** (D12 chỉ cảnh báo – tự soát cả khi có nháy / ngoặc): ん → 은/이/을/과/이라는/이라고/이며/으로; nguyên âm → 는/가/를/와/라는/라고/며/로.
- **Nghĩa câu đề** giữ đủ 4 ô, ★ đúng thứ tự, đúng ký hiệu như bản Việt (D13 – lỗi). **Nghĩa câu hoàn chỉnh** không có `{ }`.
- `gloss`: giữ `⟪cách đọc⟫ - `, nghĩa là cụm ngắn đúng lựa chọn. "Dạng te" (Latin) → `te형` (kana trần ngoài ⟪ ⟫ bị Python báo lỗi – 9227).
- D4 (cùng vi khác ko giữa các câu) → theo bản đã duyệt (`output/reports/khong_nhat_quan.csv`).
- Sửa ko: `thay` với `duong_dan` tới `….ko`; `sua` ghi đường dẫn object. JSON tiếng Việt sai → `loi_json_vi: ["[Lỗi JSON VI] …"]`.

## 6. Sự cố thường gặp

| Hiện tượng | Xử lý |
|---|---|
| `--nhan` GĐ1 LỖI_KỸ_THUẬT (schema / JSON hỏng) | `s1_claude_tao.py --chuan-bi --ids <id> --force` → giao lại tác tử TẠO mẫu đó → `--nhan --ids <id>` |
| `--nhan` GĐ2 LỖI_GĐ2 | `s2_claude_dich.py --chuan-bi --ids <id> --force` → giao lại → `--nhan --ids <id>` |
| `s1_kiem_tra` LỖI_GĐ1 (K…) | sửa file checked (lỗi tác tử TẠO / định dạng) → `s1_kiem_tra --ids <id>` |
| `nhom 'X' không hợp lệ` | dùng đúng danh sách `nhom` ở mục 4.2; cần nhóm mới → báo người dùng (code chung) |
| Python tách lời giải sai (nhãn dính dòng, khung lạ) – tác tử TẠO báo `luu_y` trái lời giải | báo người dùng; sửa `scripts/_dang.py` (backup trước vào `$HOME/bak08`), chạy lại `python3 scripts/s0_chuan_bi.py` – **không** thêm `--tao-lai-thu-tu` (giữ thứ tự chạy; trạng thái mẫu đã làm được giữ), ghi NHAT_KY |
| `s2_kiem_tra` báo `[Lỗi JSON VI]` → CẦN_SỬA_GĐ1 | `s1_claude_goi --ids <id>` → sửa → `s1_kiem_tra` → `s1_chot` → GĐ2 lại |
| Lô đang dở | `CC/tien_do.py X Y` cho biết bước đã qua của từng mẫu (soát 'dở' = còn `_huong_dan`); chạy tiếp từ bước đó (các lệnh bỏ qua mẫu đã làm) |

## 7. Báo cáo cuối lô (tiếng Việt, ngắn)

1. Bảng ĐẠT / nghi nội dung (id). 2. Mỗi mẫu gắn cờ: 1 dòng lý do; sửa định dạng / sửa ko: liệt kê ngắn. 3. Lũy kế (`CC/tien_do.py`). 4. Lệnh tiếp: **"Chạy dạng 08 mẫu <Y+1> đến <Y+10>"** (sau lô thứ 3: đề nghị mở cuộc trò chuyện mới).

Sau báo cáo **cập nhật nhật ký**: chạy song song → ghi `nhat_ky_lo/X_Y.md` (mục 0b, không sửa `NHAT_KY.md`); chạy đơn (cuộc điều phối) → sửa thẳng `NHAT_KY.md`. Nội dung: dòng bảng lô; quyết định / cách dịch mới; sự cố.
