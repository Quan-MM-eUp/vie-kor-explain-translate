# Sổ tay chạy – dạng 09 Ngữ pháp theo đoạn văn (cho phiên Claude mới)

> Viết 2026-10-08. Một cuộc trò chuyện Cowork **mới** chỉ cần đọc **file này + `NHAT_KY.md`** là chạy được, **không đọc lại cả project**.
> Câu mở đầu người dùng gõ (từ 2026-10-13 **chạy song song**): **"Đọc dang_bai/09_ngu_phap_theo_doan_van/SO_TAY_CHAY.md rồi chạy dạng 09 phần A đợt N"** → làm theo **mục 0b** (lô có `--ids` → thêm **mục 0c**). Câu cũ "… chạy dạng 09 mẫu X đến Y" chỉ dùng khi X–Y là một lô trong `phan_cong.json` (hoặc cuộc điều phối, thêm `--ngoai-phan-cong`).
> Trả lời người dùng bằng **tiếng Việt**. Dạng 09 chạy **hoàn toàn bằng Claude Opus 5.5 Cowork** – không có bước GPT API.
> Dạng 09 = khuôn lời giải của **dạng 07** (chọn ngữ pháp điền chỗ trống) + **đoạn văn chung** cho 4 câu con. **Lô chuẩn = 12 câu = 3 đoạn văn** (1–12, 13–24, 25–36 …).

---

## 0. Khởi động phiên (làm theo thứ tự)

1. Nạp công cụ: ToolSearch `select:mcp__remote-devices__device_bash`. Mọi lệnh chạy trên máy người dùng bằng công cụ này.
2. `DANG=$HOME/mnt/Vie-Kor/dang_bai/09_ngu_phap_theo_doan_van` – **mỗi lệnh đều `cd $DANG` trước** (mỗi lần gọi là shell mới).
   - **File tạm (script phụ, bản nháp) đặt trong thư mục riêng theo lô `$HOME/tam09_<X>_<Y>/`** – `$HOME` trên VM dùng chung giữa các cuộc song song, tên chung (`$HOME/work`, `$HOME/show.py`) bị ghi đè lẫn nhau. Khi giao việc cho tác tử TẠO cũng nhắc điều này (`{{LO}}`).
   Công cụ chung: `python3 ../../pipeline_chung/cong_cu/<tên>.py` (gọi tắt `CC/<tên>.py`).
3. Đọc `NHAT_KY.md` (lũy kế, quyết định đã chốt, cách dịch đã thống nhất).
4. `python3 CC/tien_do.py` (lũy kế, lô gợi ý 12 câu) và `python3 CC/tien_do.py X Y` (từng mẫu: trạng thái + bước đã qua: tạo VI / soát VI / chốt VI / tạo KO / soát KO) → biết lô chưa làm hay đang dở (mục 6). Chạy song song: lô lấy từ `PHAN_CONG.md` (mục 0b).
5. Đọc **một lần mỗi phiên** trước khi soát: `prompts/s1_claude_kiem_tra.md` (tiêu chí GĐ1 – mục 3c, 3d-1…10, 3e) và `prompts/s2_claude_kiem_tra.md`. Phần "ghi `.ly_do.json` từng mẫu" trong hai prompt làm bằng **file đặc tả lô + `ghi_ly_do.py`** (mục 4.3).
6. Phạm vi: `--tu X --den Y` (stt trong `output/thu_tu_chay.csv`, 4 câu của một đoạn liền nhau) – do `scripts/_dang.py` xử lý nên không hiện trong `--help`. **Không dùng `--lo` với `scripts/*.py`**; riêng `CC/xem_gd1.py` / `CC/xem_gd2.py`: `--lo X Y` = khoảng stt. Người dùng xin khoảng không tròn đoạn (vd 11–20) → đề nghị lấy tròn đoạn (vd 1–12 / 13–24) rồi làm theo người dùng chọn.
6b. **Chỉ chạy mẫu thuộc đề JLPT từ mẫu 289** (quyết định người dùng 2026-10-11, `config.loc_nguon_de`): mẫu mà cột `thi_thu_thuoc_de` có chữ `Nat Test` bị **bỏ tự động** ở mọi script khi chọn bằng `--tu/--den` (dòng in "Lọc nguồn đề … bỏ N mẫu thuộc NAT-TEST"). Mẫu ô trống (chỉ luyện tập) và mẫu đề Test / Vocabulary / Reading / Mock Full Exam vẫn chạy. Mẫu 1–288 giữ nguyên kết quả. Lọc **trọn đoạn văn** (cột `doan`, `config.loc_nguon_de.nhom_theo`): kiểm tra 2026-10-11 không có đoạn nào lẫn câu NAT và câu không NAT (từ mẫu 289: 122 đoạn JLPT, 31 đoạn NAT); nếu dữ liệu đổi mà có đoạn lẫn → script **dừng**, hỏi người dùng. **Chọn lô bằng `cd scripts && python3 lo_jlpt.py --lo 3`** (in khoảng `--tu X --den Y` chứa 12 mẫu JLPT = 3 đoạn trọn chưa làm, stt theo `output/thu_tu_chay.csv`) thay cho gợi ý lô của `CC/tien_do.py` (công cụ chung vẫn đếm mẫu NAT là `ĐANG_XỬ_LÝ`; `tien_do.py X Y` vẫn dùng để xem từng mẫu). Thống kê + danh sách loại tên đề: `python3 lo_jlpt.py --thong-ke` – nếu in "CÓ LOẠI TÊN ĐỀ MỚI" → dừng, hỏi người dùng. Muốn chạy cả mẫu NAT cho một lệnh: thêm `--ca-nat`; `--ids` không bị lọc.
7. Phiên không có công cụ **Agent** → dừng, báo người dùng.

## 0b. Chạy song song nhiều cuộc trò chuyện (từ 2026-10-12)

Nhiều cuộc trò chuyện cùng chạy dạng 09, mỗi cuộc một **phần** (A, B, C…) gồm các lô đã giao sẵn. Một cuộc là **điều phối** (cuộc người dùng chỉ định).

**Cuộc chạy phần (A/B/C…):**
1. Khởi động như mục 0 (bỏ bước 4 – không tự chọn lô). Đọc thêm các file `nhat_ky_lo/*.md` (nhật ký lô của các cuộc khác chưa gộp – nếu có) sau `NHAT_KY.md`.
2. Mở `PHAN_CONG.md`, lấy các lô của **đúng phần và đợt** người dùng nêu; chạy **lần lượt** từng lô theo mục 3 với `--tu X --den Y` đúng như bảng. Các bước chính (`s1_claude_tao/goi/kiem_tra/chot`, `s2_claude_dich/goi/kiem_tra`) **từ chối** khoảng không có trong `phan_cong.json`.
3. File danh sách việc đặt tên theo lô (`{{LO}}` = `X_Y` – thư mục tạm của tác tử TẠO): lệnh `--chuan-bi` in dòng `[Song song] File danh sách của lô này: output/claude/tao_gd1_danh_sach_X_Y.json` → điền tên file đó vào `{{DANH_SACH}}` của lời giao việc (mục 2). Tương tự `gd1_/tao_gd2_/gd2_danh_sach_X_Y.json`.
4. `CC/xem_gd1.py` không còn in khối GỢI Ý → chạy thêm `cd scripts && python3 goi_y_gd1.py --tu X --den Y` khi soát GĐ1.
5. Bước Python có thể in `[Khóa] Cuộc khác đang chạy bước Python – chờ…` → bình thường, lệnh tự chạy khi đến lượt (chờ tối đa 120 s; quá thì chạy lại lệnh). Lệnh đang giữ khóa tự "báo còn sống" mỗi 15 s; lệnh chết (vd bị cắt 180 s) thì khóa được lấy lại sau 60 s. **Không** xóa / đổi tên gì trong `output/.khoa/`. Không chạy hai bước Python song song trong cùng một lệnh.
6. Cuối mỗi lô **không sửa `NHAT_KY.md`**: ghi `nhat_ky_lo/X_Y.md` (mẫu dưới). `{{CAU_CO_DINH}}` (GĐ2): chạy `cd scripts && python3 trich_cau_co_dinh.py --tu X --den Y` → điền `đọc TOÀN BỘ file DANG/output/claude/cau_co_dinh_X_Y.md` vào `{{CAU_CO_DINH}}` (dạng 09: gạch đầu dòng 'Câu cố định … bổ sung' của `giao_viec_tao_gd2.md`; các câu cố định đã ghi sẵn trong mẫu giữ nguyên) (gồm mục "Cách dịch đã thống nhất" của `NHAT_KY.md` + các `nhat_ky_lo/*.md`).
7. **Không sửa** `scripts/`, `config.json`, `prompts/`, `SO_TAY_CHAY.md`, `phan_cong.json`, `PHAN_CONG.md` (được chạy `lo_jlpt.py --cap-nhat`), không chạy `s0_chuan_bi.py`, không chạy `lo_jlpt.py --phan-cong`. Gặp lỗi Python tách lời giải / cần sửa code → dừng lô đó, báo người dùng để cuộc điều phối xử lý; chạy tiếp lô khác của phần mình nếu không liên quan.
8. Không gợi ý "Chạy dạng 09 mẫu <Y+1> đến …" ở cuối lô – lô tiếp theo là lô kế trong phần. Hết phần: báo người dùng "Phần A đợt N xong".

Mẫu `nhat_ky_lo/X_Y.md` (giữ đúng 4 tiêu đề; mỗi ý một dòng `- …`, bảng lô một dòng `| … |`):
```
# Nhật ký lô X–Y (phần A, đợt N)
## Bảng lô
| X–Y (đoạn …, bỏ n NAT) | n | n | id (lý do ngắn), … | ghi chú ngắn |
## Quyết định soát đã chốt
- (lô X–Y) …
## Cách dịch đã thống nhất (GĐ2)
- 〈câu Nhật〉 (id) → 〈bản Hàn〉 …
## Sửa code / sự cố
- …
```

**Cuộc điều phối:**
- Phân công: `cd scripts && python3 lo_jlpt.py --phan-cong 30 --so-phan 10` (30 lô kế tiếp → A–J mỗi phần 3 lô; lô 12 câu = 3 đoạn trọn, không cắt đôi đoạn; **tối đa 3 lô / cuộc** – mục 1) → ghi `phan_cong.json` + `PHAN_CONG.md` (có sẵn câu mở đầu cho từng cuộc). Tiến độ: `python3 lo_jlpt.py --cap-nhat`.
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
5. Nhật ký lô đặt tên `nhat_ky_lo/X_Y.md` theo khoảng hiển thị (vd `409_880.md`).

## 1. Quy tắc bất biến

- **Bảo mật:** không đọc / mở `.env`, không in API key. Không chạy `git status`. **Không xóa file** – cần bỏ thì `mv -n` vào `_to_delete/`.
- **Nội dung lời giải sai → chỉ gắn cờ** `nghi_noi_dung`, **không sửa**. Chỉ sửa **định dạng** (`sua_dinh_dang` + `nhom` + dòng `[Đã sửa định dạng] …`) và **lỗi của tác tử TẠO**. Ghi chú không kèm thay đổi JSON → `[Ghi chú] …`. Phần THAM KHẢO: không xử lý.
- **Chạy song song nhiều dạng:** chỉ sửa file trong `$DANG`; **không sửa** `pipeline_chung/`, `explanation_schema/`, dạng khác. Cần sửa code chung → dừng, báo người dùng. Được sửa `scripts/_dang.py`, `scripts/_dau_vao.py`, prompt dạng 09 khi lỗi tách lời giải (mục 6), sau khi báo – **chỉ cuộc điều phối / chạy đơn**; cuộc chạy phần song song không sửa code (mục 0b bước 7).
- Ngữ cảnh: tối đa **3 lô (36 câu) mỗi cuộc trò chuyện** (= một phần khi chạy song song).

## 2. Hai tác tử

- **Tác tử TẠO (Claude A)** = tác tử con (Agent tool, `subagent_type: "general-purpose"`, `model: "opus"`). Lời giao việc chép **nguyên văn** `prompts/giao_viec_tao_gd1.md` / `giao_viec_tao_gd2.md` (thay `{{SO_CAU}}`, `{{DANH_SACH}}`, `{{LO}}`, bỏ dòng `<!-- -->`; GĐ2: thay `{{CAU_CO_DINH}}` theo mục 0b bước 6).
- **Tác tử KIỂM TRA** = phiên chính (bạn). Không tự tạo bản.

## 3. Quy trình một lô X–Y (12 câu = 3 đoạn văn)

### GĐ1 – JSON tiếng Việt

| # | Việc | Lệnh |
|---|---|---|
| 1 | Chuẩn bị | `python3 scripts/s1_claude_tao.py --chuan-bi --tu X --den Y` → N câu (N nhỏ hơn: xem dòng 'bỏ qua …'; chạy lại an toàn) |
| 2 | Tác tử TẠO | Agent với `giao_viec_tao_gd1.md` ({{SO_CAU}} = N). Ghi lại "điểm khó" |
| 3 | Nhận | `python3 scripts/s1_claude_tao.py --nhan --tu X --den Y` → "lỗi 0, chưa có 0" (Python tự điền `passage`) |
| 4 | Chuẩn bị soát | `python3 scripts/s1_claude_goi.py --tu X --den Y` |
| 5 | Soát | `python3 CC/xem_gd1.py <id> …` (in **đoạn văn một lần cho mỗi đoạn**, rồi lời giải gốc + gợi ý + JSON) – soát **theo từng đoạn** (4 câu con liền) |
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
| 15 | Python kiểm tra | `python3 scripts/s2_kiem_tra.py --tu X --den Y` → `ĐẠT`; xử lý lỗi / D4 / D12 / D13 / D14 rồi chạy lại |
| 16 | Báo cáo + nhật ký | mục 7 |

Excel CTV (khi người dùng yêu cầu): `python3 scripts/s3_xuat_ctv.py --tu A --den B` (ĐẠT, tiếng Hàn – cột "Ngữ liệu" là đoạn văn) · `python3 scripts/s3b_xuat_ctv_nhat.py --tu A --den B` (câu có cờ, CTV tiếng Nhật) → `output/reports/ctv/`.

## 4. Soát GĐ1

Chuẩn: **JSON đúng và đủ lời giải gốc**; lời giải phải đúng kiến thức **trong mạch đoạn văn**. Đầy đủ: `prompts/s1_claude_kiem_tra.md` (= prompt dạng 07 + 3d-9, 3d-10).

**Cờ s0 hay gặp → JSON đúng** (đầy đủ: FLAG_HINT trong `scripts/_dau_vao.py`):

| Cờ | JSON đúng |
|---|---|
| `nhan_de_bai`, `nhan_in_dam` | `question.ja` không có 'Đề bài:' / `{ }` |
| `doc_tu_furigana` | `question.reading` = chuỗi Python ghép; `khong_cach_doc` → `null` |
| `hai_cho_trong` | câu 2 chỗ a/b: `option_ja` chép nguyên `a.X／ｂ.Y`, câu áp dụng chép như lời giải |
| `lien_dong` | Python đã xuống dòng; nội dung chép nguyên (vd `Cấu trúc:+ Danh từ…` giữ nguyên dòng) |
| `de_lech_doan_van_nhe/nang`, `de_khong_tim_thay_doan_van` | `question.ja` = câu đề **trong lời giải** (không sửa theo đoạn văn ở bước TẠO) |
| `ap_dung_lech_nhe/nang`, `hoan_chinh_khac_de` | JSON chép nguyên; tác tử KIỂM TRA quyết sửa định dạng hay gắn cờ (3d-5) |
| `dap_an_de_loi` | dữ liệu đề lỗi (53467_3: `dap_an_so = 33`) → gắn cờ `dap_an`, báo người dùng |
| mọi câu | `passage = {"blank_label": "[n]", "lines": []}` – Python điền, không sửa (K-PS) |

### 4.1 Sửa (lỗi tác tử TẠO / định dạng)
- Như dạng 07: đặt sai trường, sót chữ đánh giá trong note, `grammar_ok` / `semantic_ok` sai so với lời giải, thiếu ⟪ ⟫ → sửa (`sai_so_ban_goc` / `khach_quan`).
- Định dạng bản gốc: câu đề / câu áp dụng lệch 1–2 kana do gõ (`de_lech_doan_van_nhe`, `ap_dung_lech_nhe`), dính câu, lặp từ → `sua_dinh_dang`.
- **Ruby hỏng** (cách đọc lặp ngay sau chữ Hán: `少すこし`, `一番いちばん`, `聞きき`) ở **bất kỳ** trường tiếng Nhật nào (câu đề, câu áp dụng, câu hoàn chỉnh, option_ja) → `sua_dinh_dang`, `nhom: furigana`, **dù Python báo lệch nặng**. Cách sửa: bỏ phần kana lặp (`一番いちばん` → `一番`); nếu cùng câu ở chỗ khác có furigana đúng (`｜一番《いちばん》`) thì khôi phục y như chỗ đó.
- Câu áp dụng **bị cụt cuối** do lỗi trình bày (vd 11194_2 lựa chọn 4 dừng ở `一番いちばん`, mất `ダメです`) → gắn cờ `thieu_noi_dung` (không tự thêm chữ).

### 4.2 Gắn cờ (`nhom`: `danh_gia_ngu_phap`, `ly_do_loai`, `y_nghia_cau_truc`, `nghia_cau`, `cau_khac_de`, `dap_an`, `cach_doc`, `thieu_noi_dung`, `khac`)
- 8 quy tắc dạng 07 (3d-1…8): đánh giá ngữ pháp sai rõ; lý do loại chung chung / tự mâu thuẫn; ý nghĩa / cấu trúc sai kiến thức (kể cả nói dạng có thật là "không tồn tại"); nghĩa câu lệch; câu áp dụng / câu hoàn chỉnh khác câu đề về chữ; đáp án đáng ngờ; cách đọc sai; thiếu nội dung.
- **3d-9:** câu đề chép lệch đoạn văn gốc về chữ (mất / thêm / khác chữ – vd 11194_1 mất 'はっきり') → `cau_khac_de`.
- **3d-10:** lý do chọn / loại **trái mạch đoạn văn** (liên từ, thì, chủ thể… chỉ xét câu trích) → `ly_do_loai` / `nghia_cau`. **Phải đọc đoạn văn**.
- **Không gắn cờ:** lỗi kết hợp được chấm "Đúng ngữ pháp" nhưng lý do loại về nghĩa hợp lý; đoạn trích chứa chỗ trống của câu con khác; chữ Hán ↔ kana cùng cách đọc; **thêm / bỏ ký hiệu chú thích `(注n)`** (vd 21790_2); **câu áp dụng chỉ trích mệnh đề / ngoặc 「」 chứa chỗ trống** mà phần trích đúng chữ đề (vd 11194_4 chỉ chép `すみません、もう一度お聞かせください。`) – ghi `[Ghi chú] … không gắn cờ`; cách diễn đạt chỉ "chưa hay".

### 4.3 File đặc tả lô (một file mỗi lô mỗi giai đoạn) – mẫu dưới minh họa cách ghi (11194_1 cần cả sửa định dạng lẫn gắn cờ)
```json
{"giai_doan": "1",
 "cau": {
  "21790_1": {},
  "11194_1": {"thay": [{"duong_dan": "$.question.ja", "cu": "少すこし", "moi": "少し"}],
              "sua": [{"duong_dan": "$.question.ja", "loai": "sua_dinh_dang", "nhom": "furigana", "muc_do": "nhe", "ly_do": "ruby hỏng: chữ đọc lặp sau chữ Hán"}],
              "ghi_chu_ban_goc": ["[Đã sửa định dạng] Câu đề: 'もう少すこし' → 'もう少し' – ruby hỏng"],
              "nghi_noi_dung": [{"vi_tri": "Câu đề", "nhom": "cau_khac_de", "mo_ta": "(quy tắc 3d-9) Câu đề chép thiếu 'はっきり' so với đoạn văn: '声を大きくはっきり言った'.", "de_xuat": "もう少し声を大きくはっきり言った方がいいのだろうか、[1]…"}]}
 }}
```
Ghi bằng python (`os.makedirs('output/claude/ly_do_lo', exist_ok=True)` rồi `json.dump(..., ensure_ascii=False, indent=1)`, heredoc `'EOF'`). Liệt kê **mọi** câu của lô. Danh sách bị **ghi đè** khi chạy lại – sửa thêm thì sửa trong **cùng file** rồi chạy lại. `duong_dan` = đường dẫn `xem_gd1.py` in ra **thêm `$.`** ở đầu (`analysis.options[0].meaning.vi` → `$.analysis.options[0].meaning.vi`; `xem_gd1` viết tắt `O[0]` = `analysis.options[0]`). Sửa bool / cấu trúc → python read-modify-write `output/json_vi/checked/<id>.json` + ghi `sua`.

## 5. Soát GĐ2 – tiếng Hàn

Như dạng 07 (`prompts/s2_claude_kiem_tra.md`): nghĩa câu đề / câu áp dụng / câu hoàn chỉnh **dịch thẳng từ tiếng Nhật** (giữ nhãn chỗ trống `[1]`, `（1）`, `[1-a]` như bản Việt – D13); câu hoàn chỉnh = bản dịch câu áp dụng của đáp án (D14); Ý nghĩa mẫu ngữ pháp kết hợp; **trợ từ sau ⟪kana⟫ theo âm cuối cách đọc** (ん → 은/이/을/과/이라는/이라고/이며/으로; nguyên âm → 는/가/를/와/라는/라고/며/로 – D12 chỉ cảnh báo, tự soát); "Dạng te" (Latin) → `te형` (kana trần ngoài ⟪ ⟫ bị báo lỗi). **Dạng 09:** đoạn văn không dịch; 4 câu cùng đoạn – câu / cụm lặp lại dịch giống nhau (xem bảng của cả nhóm); D4 → theo bản đã duyệt.

## 6. Sự cố thường gặp

| Hiện tượng | Xử lý |
|---|---|
| `--nhan` GĐ1 LỖI_KỸ_THUẬT | `s1_claude_tao.py --chuan-bi --ids <id> --force` → giao lại → `--nhan --ids <id>` |
| `--nhan` GĐ2 LỖI_GĐ2 | `s2_claude_dich.py --chuan-bi --ids <id> --force` → giao lại → `--nhan --ids <id>` |
| `s1_kiem_tra` LỖI_GĐ1 | đọc lỗi; sửa file checked (lỗi tác tử TẠO / định dạng) → `s1_kiem_tra --ids <id>`. "Độ phủ tiếng Việt … thiếu: [nhãn lạ]" do nhãn mới của lời giải → báo người dùng, thêm vào `LABELS` cuối `scripts/_dang.py` |
| `nhom 'X' không hợp lệ` | dùng đúng danh sách mục 4.2; nhóm mới → báo người dùng (code chung) |
| Python tách lời giải sai / `luu_y` trái lời giải | chạy song song: dừng mẫu đó, ghi vào `nhat_ky_lo/X_Y.md` mục Sửa code, báo người dùng (cuộc điều phối sửa). Chạy đơn / điều phối: báo người dùng; sửa `scripts/_dang.py` (backup `$HOME/bak09`), chạy lại `python3 scripts/s0_chuan_bi.py` – **không** thêm `--tao-lai-thu-tu`; ghi NHAT_KY |
| `[Lỗi JSON VI]` ở GĐ2 → CẦN_SỬA_GĐ1 | `s1_claude_goi --ids <id>` → sửa → `s1_kiem_tra` → `s1_chot` → GĐ2 lại |
| Lô đang dở | `CC/tien_do.py X Y` (soát 'dở' = còn `_huong_dan`); chạy tiếp từ bước đó |

## 7. Báo cáo cuối lô (tiếng Việt, ngắn)

1. Bảng ĐẠT / nghi nội dung (id), theo đoạn văn. 2. Mỗi câu gắn cờ: 1 dòng lý do; sửa định dạng / sửa ko: liệt kê ngắn. 3. Lũy kế (`CC/tien_do.py`). 4. Chạy song song: lô tiếp = lô kế trong phần (hết phần: "Phần A đợt N xong"). Chạy đơn: **"Chạy dạng 09 mẫu <Y+1> đến <Y+12>"** (sau lô thứ 3: đề nghị mở cuộc trò chuyện mới).

Sau báo cáo **cập nhật nhật ký**: chạy song song → ghi `nhat_ky_lo/X_Y.md` (mục 0b, không sửa `NHAT_KY.md`); chạy đơn (cuộc điều phối) → sửa thẳng `NHAT_KY.md`. Nội dung: dòng bảng lô; quyết định / cách dịch mới; sự cố.
