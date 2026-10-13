# Sổ tay chạy – dạng 06 Từ vựng: Ứng dụng từ (cho phiên Claude mới)

> Viết 2026-10-08. Mẫu 1–100 đã xong bằng GPT (giữ nguyên); **từ mẫu 101** bản tạo do tác tử TẠO Claude làm. Mục đích: một cuộc trò chuyện Cowork **mới** chỉ cần đọc **file này + `NHAT_KY.md`** là chạy tiếp được, **không đọc lại cả project**.
> Câu mở đầu người dùng gõ (từ 2026-10-12 **chạy song song**): **"Đọc dang_bai/06_tu_vung_ung_dung_tu/SO_TAY_CHAY.md rồi chạy dạng 06 phần A đợt N"** → làm theo **mục 0b** (lô có `--ids` → thêm **mục 0c**). Câu cũ "… chạy dạng 06 mẫu X đến Y" chỉ dùng khi X–Y là một lô trong `phan_cong.json` (hoặc cuộc điều phối, thêm `--ngoai-phan-cong`).
> Trả lời người dùng bằng **tiếng Việt**.

---

## 0. Khởi động phiên (làm theo thứ tự, không làm thêm)

1. Nạp công cụ: ToolSearch `select:mcp__remote-devices__device_bash`. Mọi lệnh chạy trên máy người dùng bằng công cụ này.
2. `DANG=$HOME/mnt/Vie-Kor/dang_bai/06_tu_vung_ung_dung_tu` – **mọi lệnh `cd $DANG` trước** (mỗi lần gọi là shell mới).
   Công cụ chung gọi bằng `python3 ../../pipeline_chung/cong_cu/<tên>.py` (gọi tắt `CC/<tên>.py` trong sổ tay).
3. Đọc `NHAT_KY.md` (lũy kế, quyết định đã chốt, cách dịch đã thống nhất).
4. `python3 CC/tien_do.py X Y` → xác nhận lô X–Y chưa làm / đang dở ở bước nào (xem mục 6 nếu đang dở). Chạy song song: lô lấy từ `PHAN_CONG.md` (mục 0b).
5. Chỉ mở thêm file khi sổ tay bảo. Hai hướng dẫn chuẩn phải đọc **một lần mỗi phiên** trước khi soát: `prompts/s1_claude_kiem_tra.md` (soát GĐ1, nhất là mục 3c–3e), `prompts/s2_claude_kiem_tra.md` (soát GĐ2). Đọc để lấy **tiêu chí và checklist**; phần "ghi `.ly_do.json` từng mẫu / xóa `_huong_dan`" trong hai prompt được **thay bằng** file đặc tả lô + `ghi_ly_do.py` (mục 4.3) – kết quả như nhau.
6. Phạm vi mẫu: `--tu X --den Y` (số thứ tự trong `thu_tu_chay.csv` = đúng thứ tự file dữ liệu) do `scripts/_dang.py` xử lý nên **không hiện trong `--help`** – vẫn dùng được với mọi script. **Không dùng `--lo`** (nghĩa là "N câu đầu theo trạng thái", không phải khoảng mẫu).
6b. **Chỉ chạy mẫu thuộc đề JLPT từ mẫu 361** (quyết định người dùng 2026-10-11, `config.loc_nguon_de`): mẫu mà cột `thi_thu_thuoc_de` có chữ `Nat Test` bị **bỏ tự động** ở mọi script khi chọn bằng `--tu/--den` (dòng in "Lọc nguồn đề … bỏ N mẫu thuộc NAT-TEST"). Mẫu ô trống (chỉ luyện tập) và mẫu đề Test / Vocabulary / Reading / Mock Full Exam vẫn chạy. Mẫu 1–360 giữ nguyên kết quả. **Chọn lô bằng `cd scripts && python3 lo_jlpt.py --lo 3`** (in khoảng `--tu X --den Y` chứa 10 mẫu JLPT chưa làm, stt theo `output/thu_tu_chay.csv`) thay cho gợi ý lô của `CC/tien_do.py` (công cụ chung vẫn đếm mẫu NAT là `ĐANG_XỬ_LÝ`; `tien_do.py X Y` vẫn dùng để xem từng mẫu). Thống kê + danh sách loại tên đề: `python3 lo_jlpt.py --thong-ke` – nếu in "CÓ LOẠI TÊN ĐỀ MỚI" → dừng, hỏi người dùng. Muốn chạy cả mẫu NAT cho một lệnh: thêm `--ca-nat`; `--ids` không bị lọc.
7. Phiên không có công cụ **Agent** (không tạo được tác tử TẠO) → **dừng, báo người dùng**; không tự tạo bản thay tác tử TẠO.

## 0b. Chạy song song nhiều cuộc trò chuyện (từ 2026-10-12)

Nhiều cuộc trò chuyện cùng chạy dạng 06, mỗi cuộc một **phần** (A, B, C…) gồm các lô đã giao sẵn. Một cuộc là **điều phối** (cuộc người dùng chỉ định).

**Cuộc chạy phần (A/B/C…):**
1. Khởi động như mục 0 (bỏ bước 4 – không tự chọn lô). Đọc thêm các file `nhat_ky_lo/*.md` (nhật ký lô của các cuộc khác chưa gộp – nếu có) sau `NHAT_KY.md`.
2. Mở `PHAN_CONG.md`, lấy các lô của **đúng phần và đợt** người dùng nêu; chạy **lần lượt** từng lô theo mục 3 với `--tu X --den Y` đúng như bảng. Các bước chính (`s1_claude_tao/goi/kiem_tra/chot`, `s2_claude_dich/goi/kiem_tra`) **từ chối** khoảng không có trong `phan_cong.json`.
3. File danh sách việc đặt tên theo lô: lệnh `--chuan-bi` in dòng `[Song song] File danh sách của lô này: output/claude/tao_gd1_danh_sach_X_Y.json` → điền tên file đó vào `{{DANH_SACH}}` của lời giao việc (mục 2). Tương tự `gd1_/tao_gd2_/gd2_danh_sach_X_Y.json`.
4. `CC/xem_gd1.py` không còn in khối GỢI Ý → chạy thêm `cd scripts && python3 goi_y_gd1.py --tu X --den Y` khi soát GĐ1.
5. Bước Python có thể in `[Khóa] Cuộc khác đang chạy bước Python – chờ…` → bình thường, lệnh tự chạy khi đến lượt (chờ tối đa 120 s; quá thì chạy lại lệnh). Lệnh đang giữ khóa tự "báo còn sống" mỗi 15 s; lệnh chết (vd bị cắt 180 s) thì khóa được lấy lại sau 60 s. **Không** xóa / đổi tên gì trong `output/.khoa/`. Không chạy hai bước Python song song trong cùng một lệnh.
6. Cuối mỗi lô **không sửa `NHAT_KY.md`**: ghi `nhat_ky_lo/X_Y.md` (mẫu dưới). `{{CAU_CO_DINH}}` (GĐ2): chạy `cd scripts && python3 trich_cau_co_dinh.py --tu X --den Y` → điền `đọc TOÀN BỘ file DANG/output/claude/cau_co_dinh_X_Y.md` (gồm mục "Cách dịch đã thống nhất" của `NHAT_KY.md` + các `nhat_ky_lo/*.md`).
7. **Không sửa** `scripts/`, `config.json`, `prompts/`, `SO_TAY_CHAY.md`, `phan_cong.json`, `PHAN_CONG.md` (được chạy `lo_jlpt.py --cap-nhat`), không chạy `s0_chuan_bi.py`, không chạy `lo_jlpt.py --phan-cong`. Gặp lỗi Python tách lời giải / cần sửa code → dừng lô đó, báo người dùng để cuộc điều phối xử lý; chạy tiếp lô khác của phần mình nếu không liên quan.
8. Không gợi ý "Chạy dạng 06 mẫu <Y+1> đến …" ở cuối lô – lô tiếp theo là lô kế trong phần. Hết phần: báo người dùng "Phần A đợt N xong".

Mẫu `nhat_ky_lo/X_Y.md` (giữ đúng 4 tiêu đề; mỗi ý một dòng `- …`, bảng lô một dòng `| … |`):
```
# Nhật ký lô X–Y (phần A, đợt N)
## Bảng lô
| X–Y (JLPT, bỏ n NAT) | Claude A | n | n | id (lý do ngắn), … |
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

- **Bảo mật:** không đọc / mở `.env`, không in API key. Không dùng GPT API (dạng này `config.tao_ban.nguon = "claude"`). Không chạy `git status`.
- **Không xóa file** trong thư mục máy người dùng (bị chặn). Cần bỏ file thì `mv -n` vào `_to_delete/`.
- **Nội dung lời giải sai → chỉ gắn cờ** `nghi_noi_dung`, **không sửa**. Chỉ sửa **định dạng** (`loai: sua_dinh_dang` + `nhom` + dòng `[Đã sửa định dạng] …` trong `ghi_chu_ban_goc`) và **lỗi của tác tử TẠO** so với lời giải (`sai_so_ban_goc`, `chinh_ta`, `khach_quan`, `chu_quan`). Ghi chú không kèm thay đổi JSON → dòng `[Ghi chú] …`.
- Dạng 06 **không có** phần THÔNG TIN THAM KHẢO (0/676 câu) và schema `vocab_usage.v2` không có `reference_raw` – `s1_claude_tao.py --nhan` tự bỏ trường này.
- **Chạy song song nhiều dạng:** phiên này **chỉ sửa file trong `$DANG`**. **Không sửa** `pipeline_chung/`, `explanation_schema/`, file của dạng khác. Thấy cần sửa code chung → dừng, mô tả cho người dùng để xử lý ở cuộc trò chuyện điều phối. Được sửa `scripts/_dang.py` của dạng 06 khi lỗi tách lời giải (mục 6), sau khi báo người dùng.
- Ngữ cảnh: tối đa **3 lô (30 mẫu) mỗi cuộc trò chuyện** (= một phần khi chạy song song); sau đó đề nghị người dùng mở cuộc trò chuyện mới.

## 2. Hai tác tử

- **Tác tử TẠO (Claude A)** = tác tử con (Agent tool, `subagent_type: "general-purpose"`, `model: "opus"`), ngữ cảnh riêng. Làm việc GPT từng làm: GĐ1 chuyển JSON, GĐ2 dịch Hàn. Lời giao việc chép **nguyên văn** từ `prompts/giao_viec_tao_gd1.md` / `prompts/giao_viec_tao_gd2.md` (thay `{{SO_CAU}}` / `{{CAU_CO_DINH}}`, bỏ dòng chú thích `<!-- -->`). Không tự soạn lời giao việc khác.
- **Tác tử KIỂM TRA** = phiên chính (bạn). Không tự tạo bản, chỉ soát + Python kiểm tra. Không để tác tử TẠO soát bài của chính nó.

## 3. Quy trình một lô X–Y (mặc định 10 mẫu, thứ tự theo `output/thu_tu_chay.csv`)

### GĐ1 – JSON tiếng Việt

| # | Việc | Lệnh |
|---|---|---|
| 1 | Chuẩn bị gói đầu vào | `python3 scripts/s1_claude_tao.py --chuan-bi --tu X --den Y` → in số câu N |
| 2 | Tác tử TẠO tạo JSON | Agent với `giao_viec_tao_gd1.md` ({{SO_CAU}} = N). Ghi lại "điểm khó" nó báo. |
| 3 | Nhận | `python3 scripts/s1_claude_tao.py --nhan --tu X --den Y` → phải "lỗi 0, chưa có 0" (lỗi → mục 6) |
| 4 | Chuẩn bị soát | `python3 scripts/s1_claude_goi.py --tu X --den Y` |
| 5 | Soát từng mẫu | `python3 CC/xem_gd1.py --lo X Y` (từng phần nếu dài: truyền id). So JSON với LỜI GIẢI GỐC theo mục 4. |
| 6 | Ghi kết quả soát | Viết `output/claude/ly_do_lo/gd1_X_Y.json` (mục 4.3) → `python3 CC/ghi_ly_do.py output/claude/ly_do_lo/gd1_X_Y.json` |
| 7 | Python kiểm tra | `python3 scripts/s1_kiem_tra.py --tu X --den Y` → mẫu có cờ = `CHỜ_DUYỆT_NỘI_DUNG`, còn lại `GĐ1_XONG`. `LỖI_GĐ1` → mục 6 |
| 8 | Chốt | `python3 scripts/s1_chot.py --tu X --den Y` (chỉ chốt `GĐ1_XONG`) |

### GĐ2 – tiếng Hàn (chỉ mẫu đã chốt, không cờ)

| # | Việc | Lệnh |
|---|---|---|
| 9 | Chuẩn bị | `python3 scripts/s2_claude_dich.py --chuan-bi --tu X --den Y` → số câu M (câu điền sẵn hết không cần dịch) |
| 10 | Tác tử TẠO dịch | Agent với `giao_viec_tao_gd2.md` ({{SO_CAU}} = M, {{CAU_CO_DINH}} = các dòng mục "Cách dịch đã thống nhất" của NHAT_KY; chưa có thì ghi "(chưa có)") |
| 11 | Nhận | `python3 scripts/s2_claude_dich.py --nhan --tu X --den Y` → "lỗi 0" |
| 12 | Chuẩn bị soát | `python3 scripts/s2_claude_goi.py --tu X --den Y` |
| 13 | Soát | `python3 CC/xem_gd2.py --lo X Y` (Mã \| Bản nguồn \| Tiếng Hàn) theo mục 5 |
| 14 | Ghi kết quả | `output/claude/ly_do_lo/gd2_X_Y.json` → `python3 CC/ghi_ly_do.py …` (luôn liệt kê **mọi** mẫu của GĐ2, kể cả không sửa, để xóa `_huong_dan`) |
| 15 | Python kiểm tra | `python3 scripts/s2_kiem_tra.py --tu X --den Y` → `ĐẠT`; xử lý cảnh báo D… (mục 5) rồi chạy lại đến khi hết lỗi |
| 16 | Báo cáo + nhật ký | mục 7 |

## 4. Soát GĐ1 – tiêu chí (áp dụng như mẫu 1–100)

Chuẩn: **JSON phải thể hiện đúng và đủ lời giải gốc**, và lời giải gốc phải đúng kiến thức. Hướng dẫn đầy đủ: `prompts/s1_claude_kiem_tra.md` (mục 3c, **3d – quy tắc riêng dạng 06**, 3e – gợi ý Sudachi R1/R2).

Đề dạng 06: một **từ** (có thể kèm **định nghĩa tiếng Nhật** sau `……` → `word.definition_ja`) + 4 câu dùng từ đó; chọn câu dùng từ đúng. Lời giải: đoạn giới thiệu từ → PHÂN TÍCH từng câu (Cách đọc / Nghĩa / nhận xét / `Sửa lại:` + Cách đọc / Nghĩa của câu sửa) → LỰA CHỌN ĐÚNG.

### 4.1 Sửa (lỗi tác tử TẠO / định dạng)
- Tác tử TẠO đặt sai trường: `word.meaning` (chỉ câu đầu "có nghĩa là …") ↔ `word.usage` (phần còn lại); Cách đọc / Nghĩa của câu gốc ↔ của câu sửa bị đổi chỗ; nhận xét nằm nhầm lựa chọn; `word.paren` / `definition_ja` / `is_correct` sai; **`usage_ok` khác điều lời giải nói** (true = lời giải nói từ dùng đúng, kể cả "đúng nhưng khác nghĩa định nghĩa"; false = dùng sai; null = lời giải không nói rõ) → sửa (`sai_so_ban_goc` / `khach_quan`).
- Thiếu ⟪ ⟫, sai `{ }` / furigana so với lời giải → sửa (lỗi tác tử TẠO).
- Lỗi gõ của bản gốc (dấu câu thừa/thiếu, thiếu dấu cách, lặp từ) → `sua_dinh_dang` + `nhom` (`dau_cau`, `khoang_trang`, `lap_tu`, `chinh_ta`, `furigana`, `khac`) + dòng `[Đã sửa định dạng] <vị trí>: '<cũ>' → '<mới>' – <lý do>`. Một trường chỉ một loại sửa (xem prompt mục 2).

### 4.2 Gắn cờ `nghi_noi_dung` (không sửa) – bảng 3d
| 3d | Khi nào | `nhom` |
|---|---|---|
| 1 | Câu dùng từ tự nhiên bị nói là sai; đề có định nghĩa mà câu "đúng nhưng khác nghĩa" bị nói "sai / không tự nhiên" | `ly_do_loai` |
| 2 | "Sửa lại" một câu vốn đúng (cảnh báo K16) | `cau_dung_bi_sua` |
| 3 | Lý do loại không nêu lỗi chính (chỉ chê lỗi phụ, nói từ "dùng đúng") – K15; **hoặc nêu sai / tuyệt đối hóa** ("không bao giờ dùng với…", "chỉ dùng cho…") khi có phản ví dụ | `ly_do_loai` |
| 4 | Câu sửa sai / không tự nhiên / đổi nghĩa / sửa chỗ khác mà không thay từ đang hỏi / **không sửa đúng lỗi chính** (538) – gợi ý R2 | `cau_sua` |
| 5 | Nghĩa / chữ Hán / cách đọc của từ ở đoạn giới thiệu sai | `nghia_tu` / `chu_han` / `cach_doc` |
| 6 | Cách đọc câu / câu sửa sai – gợi ý R1 (chữ nhiều âm đúng ngữ cảnh thì không cờ, ghi `[Ghi chú] R1 …`) | `cach_doc` |
| 7 | Nghĩa câu (`sentence.meaning`, `correction.meaning`) lệch câu Nhật (thêm 'đã', sai chủ thể, sai thì…) | `nghia_cau` |
| 8 | Đáp án đáng ngờ: ≥ 2 câu dùng đúng (đề thường) – **phương án nhiễu có nghĩa mở rộng / kết hợp tự nhiên** (感覚を研ぐ, 微妙に年上, 数学がうまい); **chính đáp án không tự nhiên** (塗装を塗る); nhận xét mâu thuẫn đáp án – K6 / K13 / K16 | `dap_an` |
| 9 | Câu trong lời giải khác đề | `cau_khac_de` |
| 10 | Thiếu lựa chọn / nhận xét / "Sửa lại" làm người học không hiểu | `thieu_noi_dung` |
| 11 | Sai kiến thức thực tế (589 "châu Âu chỉ dùng một loại tiền") | `kien_thuc` (tạm dùng `khac` nếu code chung chưa nhận) |
| 12 | Sai từ loại làm lý do (701 "軽率 là tính từ" → ナ形容詞) | `tu_loai` (tạm dùng `khac`) |

**Bắt buộc mục 3f (phản biện từng phương án)** của `prompts/s1_claude_kiem_tra.md` cho cả 4 lựa chọn: phương án nhiễu có dùng được không · lý do loại có tuyệt đối hóa / sai từ loại / sai thực tế không · câu sửa và câu đáp án có tự nhiên, sửa đúng lỗi chính không. Phản hồi CTV 2026-10-09: 10/63 mẫu Claude cho ĐẠT bị trả lại (432, 483, 538, 589, 701, 1374, 1439, 2476, 10523, 10558) – đều là các lỗi này.

Thống kê mẫu 1–100 (GPT + Claude kiểm tra): 37/100 câu gắn cờ; nhóm hay gặp nhất `cau_sua` (20 chỗ), `ly_do_loai` (12), `nghia_cau` (5), `cach_doc` (3). Câu sửa thường **không tự nhiên / sai ngữ pháp** (vd 485: 'もし勉強したら、…上がったかもしれません' phải là 勉強していたら) hoặc nghĩa câu thêm thì 'đã' – soát kỹ hai chỗ này.
**Không gắn cờ khi:** lời giải đã nêu đúng lỗi chính và chỉ thêm nhận xét phụ; câu sửa đổi thêm chỗ khác nhưng cần thiết để câu tự nhiên; gợi ý R1/R2 sai (ghi `[Ghi chú] R1/R2 … không gắn cờ vì …`).

Mẫu cờ: `{"vi_tri": "Phân tích lựa chọn 3 – câu sửa", "nhom": "cau_sua" | "ly_do_loai" | "nghia_cau" | …, "mo_ta": "(quy tắc 3d-x) <sai gì, đúng là gì>", "de_xuat": "<câu đề xuất cho CTV>"}`.

### 4.3 File đặc tả lô (một file cho cả lô – không viết script riêng)
```json
{"giai_doan": "1",
 "cau": {
  "10560_1": {},
  "10561_1": {"thay": [{"duong_dan": "$.analysis.options[1].analysis.vi", "cu": "phù hợp .", "moi": "phù hợp."}],
              "sua": [{"duong_dan": "$.analysis.options[1].analysis.vi", "loai": "sua_dinh_dang", "nhom": "dau_cau", "muc_do": "nhe", "ly_do": "thừa dấu cách trước dấu chấm"}],
              "ghi_chu_ban_goc": ["[Đã sửa định dạng] Phân tích lựa chọn 2: 'phù hợp .' → 'phù hợp.' – thừa dấu cách"],
              "nghi_noi_dung": [{"vi_tri": "Phân tích lựa chọn 1 – câu sửa", "nhom": "cau_sua", "mo_ta": "(quy tắc 3d-4) …", "de_xuat": "…"}]},
  "10562_1": {"ghi_chu_ban_goc": ["[Ghi chú] R1 lựa chọn 2: 何 đọc なん đúng ngữ cảnh – không gắn cờ"]}
 }}
```
(id trong ví dụ chỉ minh họa.) **Giữ lại** file đặc tả của mỗi lô. Ghi bằng python (`json.dump(..., ensure_ascii=False, indent=1)`, nội dung qua heredoc `'EOF'`). Liệt kê **mọi** mẫu của lô. `thay` chỉ dùng cho sửa chuỗi nhỏ; sửa bool (`usage_ok`, `is_correct`) / cấu trúc thì python read-modify-write trực tiếp `output/json_vi/checked/<id>.json` rồi ghi lý do trong `sua`.

## 5. Soát GĐ2 – tiếng Hàn

Hướng dẫn đầy đủ: `prompts/s2_claude_kiem_tra.md`. Trọng tâm:
- **Nghĩa câu của 4 lựa chọn + nghĩa câu sửa dịch TRỰC TIẾP từ câu tiếng Nhật** (bám thì, thể, chủ thể); câu dùng sai từ dịch đúng như câu đang viết (không sửa cho hợp lý); nghĩa câu sửa giống cách dịch câu gốc ở phần không đổi.
- **`word.meaning`** bắt đầu bằng trợ từ chủ đề theo âm cuối cách đọc của từ (ん → 은, còn lại → 는), giữ số nghĩa; nghĩa của từ nhắc lại trong nhận xét dùng cùng cách dịch.
- **Trợ từ sau ⟪kana⟫ theo âm cuối cách đọc tiếng Nhật** (Python chỉ cảnh báo, phải tự soát): ん → 은/이/을/과/이라는/이라고/이며/으로; nguyên âm → 는/가/를/와/라는/라고/며/로.
- **D4 không nhất quán** (cùng vi, khác ko giữa các câu) → sửa câu mới theo bản đã duyệt trước (`output/reports/khong_nhat_quan.csv`).
- Câu cố định / thuật ngữ: NHAT_KY mục "Cách dịch đã thống nhất" + `glossary_ko.json` (đã nạp vào `_he_thong.md`).
- Sửa ko: dùng `thay` với `duong_dan` tới chuỗi `….ko` trong file đặc tả `"giai_doan": "2"`; `sua` ghi `{"duong_dan": "<đường dẫn object>", "loai": "chinh_ta", "muc_do": "nhe", "ly_do": "…"}`. JSON tiếng Việt sai → `loi_json_vi: ["[Lỗi JSON VI] <phần>: <vấn đề>"]` (mẫu quay lại GĐ1).

## 6. Sự cố thường gặp

| Hiện tượng | Xử lý |
|---|---|
| `--nhan` GĐ1 báo LỖI_KỸ_THUẬT (schema / JSON hỏng) | `python3 scripts/s1_claude_tao.py --chuan-bi --ids <id> --force` → giao lại tác tử TẠO chỉ mẫu đó → `--nhan --ids <id>` |
| `--nhan` GĐ2 báo LỖI_GĐ2 (thiếu / thừa mã, lệch nội dung) | `s2_claude_dich.py --chuan-bi --ids <id> --force` → giao lại → `--nhan --ids <id>` |
| `s1_kiem_tra` báo LỖI_GĐ1 (K…) | Đọc lỗi; sửa file checked (lỗi tác tử TẠO / định dạng) hoặc ghi chú; chạy lại `s1_kiem_tra --ids <id>` |
| Lỗi do **Python tách lời giải sai** (nhãn lặp, "Cách đọc:" / "Sửa lại:" dính câu…) | Báo người dùng, sửa `scripts/_dang.py` (backup trước vào `$HOME/bak06`), chạy lại `python3 scripts/s0_chuan_bi.py` (giữ thứ tự chạy), ghi vào NHAT_KY |
| `[Đã sửa định dạng]` không có `sua` tương ứng → cảnh báo | Đổi thành `[Ghi chú]` hoặc thêm `sua` |
| `s2_kiem_tra` báo `[Lỗi JSON VI]` → CẦN_SỬA_GĐ1 | `s1_claude_goi --ids <id>` (tự gắn `_huong_dan` CẦN SỬA LẠI) → sửa → `s1_kiem_tra` → `s1_chot` → GĐ2 lại |
| Lô đang dở (phiên trước dừng giữa chừng) | `CC/tien_do.py X Y` xem trạng thái từng mẫu; file `output/claude/tao_gd1_danh_sach.json` / `tao_gd2_danh_sach.json` và `_huong_dan` trong `.ly_do.json` cho biết bước nào chưa xong; chạy tiếp từ bước đó (các lệnh đều bỏ qua mẫu đã làm) |
| Tác tử TẠO mở file ngoài phạm vi | Ghi vào NHAT_KY; kết quả vẫn dùng được nếu nó không sửa file khác |

## 7. Báo cáo cuối lô (tiếng Việt, ngắn)

1. Bảng: ĐẠT n (id…), nghi nội dung n (id…).
2. Mỗi mẫu gắn cờ: 1 dòng lý do. Sửa định dạng / sửa ko: liệt kê ngắn.
3. Lũy kế (`CC/tien_do.py`).
4. Lệnh tiếp: **"Chạy dạng 06 mẫu <Y+1> đến <Y+10>"** (sau lô thứ 3 trong phiên: đề nghị mở cuộc trò chuyện mới với câu mở đầu ở đầu sổ tay).

Sau báo cáo **cập nhật nhật ký**: chạy song song → ghi `nhat_ky_lo/X_Y.md` (mục 0b, không sửa `NHAT_KY.md`); chạy đơn (cuộc điều phối) → sửa thẳng `NHAT_KY.md`. Nội dung: dòng bảng lô; quyết định / cách dịch mới đã thống nhất; sự cố đã gặp.

## 8. Excel CTV (khi người dùng yêu cầu)

- CTV tiếng Hàn (mẫu ĐẠT): `python3 scripts/s3_xuat_ctv.py --tu X --den Y` → `output/reports/ctv/<ngày>-CTV-06_ung_dung_tu….xlsx`.
- CTV tiếng Nhật (mẫu có cờ, chưa dịch): `python3 scripts/s3b_xuat_ctv_nhat.py --tu X --den Y`.
- Mẫu 1–100 đã xuất (2026-10-07): `2026-10-07-CTV-06_ung_dung_tu-v1-mau1-100.xlsx`, `2026-10-07-CTV-NHAT-06_ung_dung_tu-co-mau1-100.xlsx`.
