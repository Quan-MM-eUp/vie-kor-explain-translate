# Sổ tay chạy – dạng 10 Đọc hiểu: Đoạn văn ngắn (cho phiên Claude mới)

> Viết 2026-10-08. Một cuộc trò chuyện Cowork **mới** chỉ cần đọc **file này + `NHAT_KY.md`** là chạy được, **không đọc lại cả project**.
> Câu mở đầu người dùng gõ: **"Đọc dang_bai/10_doc_hieu_doan_van_ngan/SO_TAY_CHAY.md rồi chạy dạng 10 mẫu X đến Y"**.
> Trả lời người dùng bằng **tiếng Việt**. Dạng 10 chạy **hoàn toàn bằng Claude Opus 5.5 Cowork** – không có bước GPT API.

---

## 0. Khởi động phiên (làm theo thứ tự)

1. Nạp công cụ: ToolSearch `select:mcp__remote-devices__device_bash`. Mọi lệnh chạy trên máy người dùng bằng công cụ này.
2. `DANG=$HOME/mnt/Vie-Kor/dang_bai/10_doc_hieu_doan_van_ngan` – **mỗi lệnh đều `cd $DANG` trước** (mỗi lần gọi là shell mới).
   Công cụ chung: `python3 ../../pipeline_chung/cong_cu/<tên>.py` (gọi tắt `CC/<tên>.py`).
3. Đọc `NHAT_KY.md` (lũy kế, quyết định đã chốt, cách dịch đã thống nhất).
4. `python3 CC/tien_do.py` (lũy kế, lô gợi ý) và `python3 CC/tien_do.py X Y` (từng mẫu: trạng thái + bước đã qua) → biết lô chưa làm hay đang dở (mục 6).
5. Đọc **một lần mỗi phiên** trước khi soát: `prompts/s1_claude_kiem_tra.md` (tiêu chí GĐ1, nhất là 3d–3f), `prompts/s2_claude_kiem_tra.md` (checklist GĐ2). Phần "ghi lý do từng mẫu" làm bằng **file đặc tả lô + `ghi_ly_do.py`** (mục 4.3).
6. Phạm vi mẫu: `--tu X --den Y` (số thứ tự trong `output/thu_tu_chay.csv`) do `scripts/_dang.py` xử lý nên **không hiện trong `--help`** – vẫn dùng được với mọi script. **Không dùng `--lo` với `scripts/*.py`** (ở đó `--lo N` = N câu đầu theo trạng thái). Riêng `CC/xem_gd1.py` / `CC/xem_gd2.py`: `--lo X Y` = khoảng số thứ tự.
6b. **Chỉ chạy mẫu thuộc đề JLPT từ mẫu 292** (quyết định người dùng 2026-10-11, `config.loc_nguon_de`): mẫu mà cột `thi_thu_thuoc_de` có chữ `Nat Test` bị **bỏ tự động** ở mọi script khi chọn bằng `--tu/--den` (dòng in "Lọc nguồn đề … bỏ N mẫu thuộc NAT-TEST"). Mẫu ô trống (chỉ luyện tập) và mẫu đề Test / Vocabulary / Reading / Mock Full Exam vẫn chạy. Mẫu 1–291 giữ nguyên kết quả. Lọc **trọn nhóm chung đoạn văn** (cột `nhom_doan_van`, `config.loc_nguon_de.nhom_theo`): kiểm tra 2026-10-11 không có nhóm nào (kể cả lô nhỏ `lo_nho`) lẫn câu NAT và câu không NAT; nếu dữ liệu đổi mà có nhóm lẫn → script **dừng**, hỏi người dùng. `lo_jlpt.py` không cắt đôi nhóm (lô có thể 11–12 mẫu) và cho mẫu `lo_nho` (khuôn B, stt 774–822) lô 5 riêng. **Chọn lô bằng `cd scripts && python3 lo_jlpt.py --lo 3`** (in khoảng `--tu X --den Y` chứa 10 mẫu JLPT, không cắt đôi nhóm; khuôn B lô 5 chưa làm, stt theo `output/thu_tu_chay.csv`) thay cho gợi ý lô của `CC/tien_do.py` (công cụ chung vẫn đếm mẫu NAT là `ĐANG_XỬ_LÝ`; `tien_do.py X Y` vẫn dùng để xem từng mẫu). Thống kê + danh sách loại tên đề: `python3 lo_jlpt.py --thong-ke` – nếu in "CÓ LOẠI TÊN ĐỀ MỚI" → dừng, hỏi người dùng. Muốn chạy cả mẫu NAT cho một lệnh: thêm `--ca-nat`; `--ids` không bị lọc.
7. **Kích thước lô:** mặc định 10 mẫu. Mẫu có `lo_nho = x` trong `output/thu_tu_chay.csv` (khuôn B – dịch cả bài, đoạn văn > 2000 ký tự) chạy **lô 5**. Các mẫu chung một đoạn văn (`nhom_doan_van` giống nhau) đã xếp liền nhau – **không cắt đôi nhóm** giữa hai lô (lùi / tiến `Y` cho trọn nhóm).
8. Phiên không có công cụ **Agent** → **dừng, báo người dùng** (không tự tạo bản thay tác tử TẠO).

## 1. Quy tắc bất biến

- **Bảo mật:** không đọc / mở `.env`, không in API key. Không chạy `git status`.
- **Không xóa file** (bị chặn) – cần bỏ thì `mv -n` vào `_to_delete/`.
- **Nội dung lời giải sai → chỉ gắn cờ** `nghi_noi_dung`, **không sửa**. Chỉ sửa **định dạng** (`sua_dinh_dang` + `nhom` + dòng `[Đã sửa định dạng] …`; gồm khôi phục chữ Việt bị thay bằng chữ Hán – `nhom: kanji_chen`) và **lỗi của tác tử TẠO**. Ghi chú không kèm thay đổi JSON → `[Ghi chú] …`.
- `full_translation` / `summary` chỉ có khi lời giải có – **không tự tạo** (đã duyệt 08/10/2026).
- **Chạy song song nhiều dạng:** phiên này **chỉ sửa file trong `$DANG`**. **Không sửa** `pipeline_chung/`, `explanation_schema/`, file của dạng khác. Cần sửa code chung → dừng, mô tả cho người dùng để xử lý ở cuộc trò chuyện điều phối. Được sửa `scripts/_dang.py` / `scripts/_dau_vao.py` / prompt của dạng 10 khi lỗi tách lời giải (mục 6), sau khi báo người dùng.
- Ngữ cảnh: lời giải dạng 10 dài gấp 2–3 lần dạng 07 → tối đa **2 lô (20 mẫu) mỗi cuộc trò chuyện**.

## 2. Hai tác tử

- **Tác tử TẠO (Claude A)** = tác tử con (Agent tool, `subagent_type: "general-purpose"`, `model: "opus"`). GĐ1 chuyển JSON, GĐ2 dịch Hàn. Lời giao việc chép **nguyên văn** từ `prompts/giao_viec_tao_gd1.md` / `prompts/giao_viec_tao_gd2.md` (thay `{{SO_CAU}}`, bỏ dòng `<!-- -->`; GĐ2: chép các cách dịch đã thống nhất trong NHAT_KY vào dòng "Câu cố định", chưa có thì bỏ dòng đó).
- **Tác tử KIỂM TRA** = phiên chính (bạn). Không tự tạo bản; soát + Python kiểm tra. Không để tác tử TẠO soát bài của chính nó.

## 3. Quy trình một lô X–Y

### GĐ1 – JSON tiếng Việt

| # | Việc | Lệnh |
|---|---|---|
| 1 | Chuẩn bị gói đầu vào | `python3 scripts/s1_claude_tao.py --chuan-bi --tu X --den Y` → số câu N (mỗi gói có `khung_python` = khung Python tách sẵn) |
| 2 | Tác tử TẠO tạo JSON | Agent với `giao_viec_tao_gd1.md` ({{SO_CAU}} = N). Ghi lại "điểm khó" nó báo (nhất là chỗ khung Python tách sai) |
| 3 | Nhận | `python3 scripts/s1_claude_tao.py --nhan --tu X --den Y` → "lỗi 0, chưa có 0" |
| 4 | Chuẩn bị soát | `python3 scripts/s1_claude_goi.py --tu X --den Y` |
| 5 | Soát | `python3 CC/xem_gd1.py <id> <id>` (1–2 mẫu mỗi lần – có in **đoạn văn**; `--gon` bỏ đoạn văn + lời giải). So JSON với LỜI GIẢI GỐC và ĐOẠN VĂN theo mục 4 |
| 6 | Ghi kết quả | `output/claude/ly_do_lo/gd1_X_Y.json` (mục 4.3) → `python3 CC/ghi_ly_do.py output/claude/ly_do_lo/gd1_X_Y.json` |
| 7 | Python kiểm tra | `python3 scripts/s1_kiem_tra.py --tu X --den Y` → có cờ = `CHỜ_DUYỆT_NỘI_DUNG`, còn lại `GĐ1_XONG`; `LỖI_GĐ1` → mục 6 (hay gặp: **K-KC chưa xử lý**) |
| 8 | Chốt | `python3 scripts/s1_chot.py --tu X --den Y` |

### GĐ2 – tiếng Hàn (chỉ mẫu đã chốt, không cờ)

| # | Việc | Lệnh |
|---|---|---|
| 9 | Chuẩn bị | `python3 scripts/s2_claude_dich.py --chuan-bi --tu X --den Y` → M câu |
| 10 | Tác tử TẠO dịch | Agent với `giao_viec_tao_gd2.md` ({{SO_CAU}} = M) |
| 11 | Nhận | `python3 scripts/s2_claude_dich.py --nhan --tu X --den Y` → "lỗi 0" |
| 12 | Chuẩn bị soát | `python3 scripts/s2_claude_goi.py --tu X --den Y` |
| 13 | Soát | `python3 CC/xem_gd2.py <id> …` (Mã \| Bản nguồn \| Tiếng Hàn) theo mục 5; cần đoạn văn thì `CC/xem_gd1.py <id>` |
| 14 | Ghi kết quả | `output/claude/ly_do_lo/gd2_X_Y.json` (`"giai_doan": "2"`, liệt kê **mọi** mẫu GĐ2, kể cả không sửa) → `ghi_ly_do.py` |
| 15 | Python kiểm tra | `python3 scripts/s2_kiem_tra.py --tu X --den Y` → `ĐẠT`; xử lý lỗi / D-QT / D4 / D12 rồi chạy lại |
| 16 | Báo cáo + nhật ký | mục 7 |

Excel CTV (khi người dùng yêu cầu): `python3 scripts/s3_xuat_ctv.py --tu A --den B` (mẫu ĐẠT, tiếng Hàn – có cột đoạn văn), `python3 scripts/s3b_xuat_ctv_nhat.py --tu A --den B` (mẫu có cờ, CTV tiếng Nhật) → `output/reports/ctv/`.

## 4. Soát GĐ1 – trọng tâm dạng 10

Chuẩn: **JSON đúng và đủ lời giải gốc**; lời giải gốc phải đúng với đoạn văn. Đầy đủ: `prompts/s1_claude_kiem_tra.md`.

**Cờ s0 trên đầu dòng `xem_gd1` → JSON đúng trông thế nào** (đầy đủ: `scripts/_dau_vao.py` – FLAG_HINT):

| Cờ | JSON đúng |
|---|---|
| `khuon_a` | `full_translation = null`; mỗi lựa chọn: `meaning` / `quotes` / `analysis` / `is_match` |
| `khuon_b` | `full_translation` = các dòng 'Đoạn văn:'; `question.ja` / `option_ja` = câu của **đề** (bỏ furigana); `quotes = []`; `analysis = null` (trừ lựa chọn đúng nếu có giải thích); không có dòng 'Câu trả lời đúng là' – **không** cờ vì thiếu phân tích |
| `khuon_le` | tác tử TẠO tự đặt – soát kỹ từng trường; chỉ có gợi ý / một câu → cờ `thieu_noi_dung` |
| `co_phan_tich_chung` | `summary = [{heading: null, points: [...]}]` |
| `co_trich_dan` | trích dẫn đứng riêng dòng → `quotes` (ja không 「」, meaning không ( )); trong câu → `analysis` |
| `trich_dan_khong_dich` | `quotes[].meaning = null` |
| `ket_luan_lech_dap_an` / `b_dap_an_lech` | `is_match` / `correct` theo đề; lệch thật → cờ `dap_an` |
| `kanji_chen` | **phải xử lý** (3e): khôi phục chữ Việt / cờ `kanji_chen` / `[Ghi chú] kanji_chen: … không phải lỗi` |
| `ky_hieu_furigana_hong` | `<|今;いま|` rõ → `｜今《いま》` (sua_dinh_dang, `nhom: furigana`); không rõ → giữ + `[Ghi chú]` |
| `trich_dan_lech_doan_van` | đối chiếu đoạn văn: sai thật → cờ `trich_dan`; chỉ khác kana/kanji, chú thích → `[Ghi chú]` |
| `doan_van_trong` / `doan_van_co_hinh` | không so được trích dẫn – đọc kỹ hơn |

### 4.1 Sửa (lỗi tác tử TẠO / định dạng)
- Tác tử TẠO: thiếu ⟪ ⟫ (katakana, kana đơn, chữ Hán có furigana), dấu 「」 lọt vào ⟪ ⟫, trích dẫn sai chỗ (quotes ↔ analysis), mất câu dẫn, chép nhãn / kết luận vào analysis, `is_match` sai → sửa (`sai_so_ban_goc` / `khach_quan`).
- Định dạng bản gốc: chữ Hán chèn câu Việt nghĩa rõ (`nhom: kanji_chen`), furigana hỏng `<|…` (`furigana`), dính dòng (`dinh_chu`), lặp chữ / gõ nhầm → `sua_dinh_dang` + `[Đã sửa định dạng]`.

### 4.2 Gắn cờ `nghi_noi_dung` (không sửa) – `nhom` hợp lệ: `trich_dan`, `nghia_cau`, `phan_tich`, `dap_an`, `kanji_chen`, `thieu_noi_dung`, `khac`
**Gắn cờ khi:** trích dẫn không có trong đoạn văn / trích nhầm (`trich_dan`); dịch sai câu trích dẫn / nghĩa lựa chọn / nghĩa câu hỏi (`nghia_cau` – vd 16715 変わっていることも大好きだ); lý do chọn / loại trái đoạn văn, sai chủ thể, tự mâu thuẫn (`phan_tich`); kết luận lệch đáp án (`dap_an`); chữ Hán chèn câu Việt không đoán chắc (`kanji_chen`); khuôn lẻ chỉ có gợi ý, lựa chọn đúng không có phân tích (`thieu_noi_dung`).
**KHÔNG gắn cờ khi:** dịch thoáng đúng ý; câu dẫn kết thúc bằng `:`; khuôn B không có phân tích; trích dẫn chỉ khác kana/kanji / khoảng trắng / chú thích.

### 4.3 File đặc tả lô (một file cho cả lô)
```json
{"giai_doan": "1",
 "cau": {
  "16980_1": {},
  "15_1": {"thay": [{"duong_dan": "$.options[0].analysis.vi", "cu": "⟪｜休《やす》⟫ việc ⟪｜歩《あゆ》⟫ vào nhà", "moi": "nghỉ việc bước vào nhà"}],
           "sua": [{"duong_dan": "$.options[0].analysis", "loai": "sua_dinh_dang", "nhom": "kanji_chen", "muc_do": "nhe", "ly_do": "chữ Việt bị thay bằng chữ Hán"}],
           "ghi_chu_ban_goc": ["[Đã sửa định dạng] Lựa chọn 1 – phân tích: '｜休《やす》 việc ｜歩《あゆ》 vào nhà' → 'nghỉ việc bước vào nhà' – chữ Việt bị thay bằng chữ Hán",
                               "[Ghi chú] kanji_chen: ｜妻《つま》 / ｜夫《おっと》 – từ của lựa chọn, không phải lỗi"]},
  "16715_1": {"nghi_noi_dung": [{"vi_tri": "Lựa chọn 1 – trích dẫn", "nhom": "nghia_cau", "mo_ta": "(3d-2) …", "de_xuat": "…"}]}
 }}
```
Ghi bằng python (`json.dump(..., ensure_ascii=False, indent=1)`, nội dung qua heredoc `'EOF'`). Liệt kê **mọi** mẫu của lô. **Một file cho mỗi lô mỗi giai đoạn**: các khóa danh sách bị **ghi đè** khi chạy lại – sửa thêm thì sửa mục của mẫu đó **trong cùng file** rồi chạy lại. `duong_dan` = đường dẫn `xem_gd1.py` in ra **thêm `$.` ở đầu**. `thay`: chuỗi `cu` phải xuất hiện **đúng 1 lần** trong trường (khối lặp lại → thêm chữ xung quanh cho duy nhất, hoặc python read-modify-write). Sửa cấu trúc (chuyển trích dẫn quotes ↔ analysis, bool) thì python read-modify-write `output/json_vi/checked/<id>.json` + ghi `sua`.

## 5. Soát GĐ2 – tiếng Hàn

Đầy đủ: `prompts/s2_claude_kiem_tra.md`. Trọng tâm:
- **Nghĩa câu hỏi / nghĩa lựa chọn / bản dịch trích dẫn** (VI + JA): theo **tiếng Nhật** – khác bản Việt là bình thường.
- **Cùng câu trích dẫn → cùng bản Hàn** trong mẫu (D-QT – lỗi) và giữa các câu con cùng đoạn văn (D4 – `output/reports/khong_nhat_quan.csv`).
- **Trợ từ sau ⟪kana⟫ theo âm cuối cách đọc tiếng Nhật** (D12 chỉ cảnh báo – tự soát, kể cả khối có furigana và khi có nháy / ngoặc).
- Phân tích: đủ ý bản Việt, -습니다; tên riêng phiên âm theo đoạn văn tiếng Nhật.
- Sửa ko: `thay` với `duong_dan` tới `….ko`; `sua` ghi đường dẫn object. JSON tiếng Việt sai → `loi_json_vi: ["[Lỗi JSON VI] …"]`.

## 6. Sự cố thường gặp

| Hiện tượng | Xử lý |
|---|---|
| `--nhan` GĐ1 LỖI_KỸ_THUẬT (schema / JSON hỏng) | `s1_claude_tao.py --chuan-bi --ids <id> --force` → giao lại tác tử TẠO mẫu đó → `--nhan --ids <id>` |
| `--nhan` GĐ2 LỖI_GĐ2 | `s2_claude_dich.py --chuan-bi --ids <id> --force` → giao lại → `--nhan --ids <id>` |
| `s1_kiem_tra` LỖI_GĐ1 `K-KC` | xử lý chữ Hán chèn câu Việt theo 3e (sửa / cờ / `[Ghi chú] kanji_chen: …`) → `s1_kiem_tra --ids <id>` |
| `s1_kiem_tra` LỖI `K9 … thiếu chữ` | thường do tác tử TẠO bỏ sót câu dẫn / dòng phân tích / bản dịch trích dẫn → bổ sung (`sai_so_ban_goc`) |
| `s1_kiem_tra` LỖI `K-TD … không có nguyên văn trong lời giải` | `quotes[].ja` bị chép sai / tự sửa → chép lại đúng lời giải |
| `nhom 'X' không hợp lệ` | dùng đúng danh sách `nhom` ở mục 4.2; cần nhóm mới → báo người dùng (code chung) |
| Python tách khung sai (tác tử TẠO báo khung trái lời giải) | báo người dùng; sửa `scripts/_dang.py` (backup trước vào `$HOME/bak10`), chạy lại `python3 scripts/s0_chuan_bi.py` – **không** thêm `--tao-lai-thu-tu`; ghi NHAT_KY |
| `s2_kiem_tra` báo `[Lỗi JSON VI]` → CẦN_SỬA_GĐ1 | `s1_claude_goi --ids <id>` → sửa → `s1_kiem_tra` → `s1_chot` → GĐ2 lại |
| Lô đang dở | `CC/tien_do.py X Y` cho biết bước đã qua của từng mẫu; chạy tiếp từ bước đó (các lệnh bỏ qua mẫu đã làm) |

## 7. Báo cáo cuối lô (tiếng Việt, ngắn)

1. Bảng ĐẠT / nghi nội dung (id). 2. Mỗi mẫu gắn cờ: 1 dòng lý do; sửa định dạng (nhất là kanji_chen) / sửa ko: liệt kê ngắn. 3. Lũy kế (`CC/tien_do.py`). 4. Lệnh tiếp: **"Chạy dạng 10 mẫu <Y+1> đến <Y+10>"** (sau lô thứ 2: đề nghị mở cuộc trò chuyện mới).

Sau báo cáo **cập nhật `NHAT_KY.md`**: dòng bảng lô; quyết định / cách dịch mới; sự cố.
