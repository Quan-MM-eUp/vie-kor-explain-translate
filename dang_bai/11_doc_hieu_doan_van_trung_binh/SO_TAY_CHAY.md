# Sổ tay chạy – dạng 11 Đọc hiểu: Đoạn văn trung bình (cho phiên Claude mới)

> Viết 2026-10-08. Một cuộc trò chuyện Cowork **mới** chỉ cần đọc **file này + `NHAT_KY.md`** là chạy được, **không đọc lại cả project**.
> Câu mở đầu người dùng gõ: **"Đọc dang_bai/11_doc_hieu_doan_van_trung_binh/SO_TAY_CHAY.md rồi chạy dạng 11 mẫu X đến Y"** (X, Y = số thứ tự trong `output/thu_tu_chay.csv`).
> Trả lời người dùng bằng **tiếng Việt**. Dạng 11 chạy **hoàn toàn bằng Claude Opus 5.5 Cowork** – không có bước GPT API.

---

## 0. Khởi động phiên (làm theo thứ tự)

1. Nạp công cụ: ToolSearch `select:mcp__remote-devices__device_bash`. Mọi lệnh chạy trên máy người dùng bằng công cụ này.
2. `DANG=$HOME/mnt/Vie-Kor/dang_bai/11_doc_hieu_doan_van_trung_binh` – **mỗi lệnh đều `cd $DANG` trước** (mỗi lần gọi là shell mới).
   Công cụ chung: `python3 ../../pipeline_chung/cong_cu/<tên>.py` (gọi tắt `CC/<tên>.py`).
3. Đọc `NHAT_KY.md` (lũy kế, quyết định đã chốt, cách dịch đã thống nhất).
4. **Phạm vi = mẫu X đến Y do người dùng đưa** → mọi lệnh dùng `--tu X --den Y`, chạy **đúng** khoảng đó (không tự nới, không tự cắt). Các câu con của một đoạn văn luôn liền nhau trong `thu_tu_chay.csv` (cột `doan`); nếu X–Y cắt ngang một đoạn thì vẫn chạy, chỉ ghi một dòng trong báo cáo (vd "mẫu 28 là câu 1/3 của đoạn 53635 – câu 2–3 ở lần sau") để lần sau soát tiếp đoạn đó. Nếu khoảng lớn hơn ~12 mẫu: chia thành các đợt ~10 mẫu liền nhau (mỗi đợt chạy trọn GĐ1 → GĐ2) bên trong khoảng X–Y. `output/lo_chay.csv` chỉ là gợi ý ranh giới tròn đoạn (tham khảo).
5. `python3 CC/tien_do.py` (lũy kế, lô gợi ý) và `python3 CC/tien_do.py X Y` (từng mẫu: trạng thái + bước đã qua: tạo VI / soát VI / chốt VI / tạo KO / soát KO) → biết lô chưa làm hay đang dở (mục 6).
5b. **Chỉ chạy mẫu thuộc đề JLPT từ stt 272** (quyết định người dùng 2026-10-11, `config.loc_nguon_de`): mẫu mà cột `thi_thu_thuoc_de` (file dữ liệu, tra theo `sample_id`) có chữ `Nat Test` – kể cả khi có thêm đề khác – bị **bỏ tự động** ở mọi script khi chọn bằng `--tu/--den` (stt theo `output/thu_tu_chay.csv`), `--lo`, `--tat-ca` (dòng in "Lọc nguồn đề … bỏ N mẫu thuộc NAT-TEST"). Mẫu ô trống (chỉ luyện tập) và mẫu đề Test / Reading Test / Vocabulary Test / Mock Full Exam vẫn chạy. Mẫu stt < 272 giữ nguyên kết quả; `thu_tu_chay.csv` và cột `lo` **không đổi**. **Chọn lô bằng `python3 scripts/lo_jlpt.py --lo 3`** (in `Lô <số>: --tu X --den Y (n mẫu JLPT, bỏ m mẫu NAT)`, bỏ qua lô toàn NAT / đã xong) thay cho gợi ý lô của `CC/tien_do.py` (các công cụ này vẫn đếm mẫu NAT là `ĐANG_XỬ_LÝ` / chưa xong – sẽ mãi chỉ vào mẫu NAT). Thống kê: `python3 scripts/lo_jlpt.py --thong-ke`. Muốn chạy cả mẫu NAT cho một lệnh: thêm `--ca-nat`; `--ids`, `--pilot` không bị lọc. Báo cáo lô: ghi các mẫu NAT đã bỏ trong khoảng (lấy từ dòng "Lọc nguồn đề …").
6. Đọc **một lần mỗi phiên** trước khi soát: `prompts/s1_claude_kiem_tra.md` (tiêu chí GĐ1, nhất là 3d–3e), `prompts/s2_claude_kiem_tra.md` (checklist GĐ2). Phần "ghi lý do từng mẫu" làm bằng **file đặc tả lô + `ghi_ly_do.py`** (mục 4.3).
7. Phạm vi mẫu: `--tu X --den Y` (số thứ tự trong `output/thu_tu_chay.csv`) do `scripts/_dang.py` xử lý nên **không hiện trong `--help`** – vẫn dùng được với mọi script. **Không dùng `--lo` với `scripts/*.py`** (ở đó `--lo N` = N câu đầu theo trạng thái). Riêng `CC/xem_gd1.py` / `CC/xem_gd2.py`: `--lo X Y` = khoảng số thứ tự.
8. Phiên không có công cụ **Agent** → **dừng, báo người dùng** (không tự tạo bản thay tác tử TẠO).

## 1. Quy tắc bất biến

- **Bảo mật:** không đọc / mở `.env`, không in API key. Không chạy `git status`.
- **Không xóa file** (bị chặn) – cần bỏ thì `mv -n` vào `_to_delete/`.
- **Nội dung lời giải sai → chỉ gắn cờ** `nghi_noi_dung`, **không sửa**. Chỉ sửa **định dạng** (`sua_dinh_dang` + `nhom` + dòng `[Đã sửa định dạng] …`) và **lỗi của tác tử TẠO**. Ghi chú không kèm thay đổi JSON → `[Ghi chú] …`.
- **Chạy song song nhiều dạng:** phiên này **chỉ sửa file trong `$DANG`**. **Không sửa** `pipeline_chung/`, `explanation_schema/`, file của dạng khác. Cần sửa code chung (vd thêm `nhom` cờ mới vào `pipeline_chung/claude_log.py`) → dừng, mô tả cho người dùng để xử lý ở cuộc trò chuyện điều phối. Được sửa `scripts/_dang.py` / `scripts/_dau_vao.py` / prompt của dạng 11 khi lỗi tách lời giải (mục 6), sau khi báo người dùng.
- Ngữ cảnh: tối đa **~30 mẫu mỗi cuộc trò chuyện** (khoảng lớn hơn → làm 30 mẫu đầu rồi đề nghị mở cuộc trò chuyện mới với khoảng còn lại).

## 2. Hai tác tử

- **Tác tử TẠO (Claude A)** = tác tử con (Agent tool, `subagent_type: "general-purpose"`, `model: "opus"`). GĐ1 chuyển JSON, GĐ2 dịch Hàn. Lời giao việc chép **nguyên văn** từ `prompts/giao_viec_tao_gd1.md` / `prompts/giao_viec_tao_gd2.md` (thay `{{SO_CAU}}`, bỏ dòng `<!-- -->`; GĐ2: chép các cách dịch đã thống nhất trong NHAT_KY vào dòng "Câu cố định", chưa có thì bỏ dòng đó).
- **Tác tử KIỂM TRA** = phiên chính (bạn). Không tự tạo bản; soát + Python kiểm tra.

## 3. Quy trình cho mẫu X–Y (một đợt ~10 mẫu)

### GĐ1 – JSON tiếng Việt

| # | Việc | Lệnh |
|---|---|---|
| 1 | Chuẩn bị gói đầu vào | `python3 scripts/s1_claude_tao.py --chuan-bi --tu X --den Y` → số câu N (N < số mẫu: xem dòng 'bỏ qua …' – mẫu đã có bản tạo; chạy lại an toàn) |
| 2 | Tác tử TẠO tạo JSON | Agent với `giao_viec_tao_gd1.md` ({{SO_CAU}} = N). Ghi lại "điểm khó" nó báo |
| 3 | Nhận | `python3 scripts/s1_claude_tao.py --nhan --tu X --den Y` → "lỗi 0, chưa có 0" |
| 4 | Chuẩn bị soát | `python3 scripts/s1_claude_goi.py --tu X --den Y` |
| 5 | Soát **theo đoạn** | `python3 CC/xem_gd1.py <id> <id> …` (các câu con của **một đoạn** mỗi lần – đoạn văn in một lần ở câu đầu; `--lo X Y` cho cả lô). So JSON với LỜI GIẢI GỐC và lời giải với ĐOẠN VĂN theo mục 4 |
| 6 | Ghi kết quả | `output/claude/ly_do_lo/gd1_X_Y.json` (mục 4.3) → `python3 CC/ghi_ly_do.py output/claude/ly_do_lo/gd1_X_Y.json` |
| 7 | Python kiểm tra | `python3 scripts/s1_kiem_tra.py --tu X --den Y` → có cờ = `CHỜ_DUYỆT_NỘI_DUNG`, còn lại `GĐ1_XONG`; `LỖI_GĐ1` → mục 6 |
| 8 | Chốt | `python3 scripts/s1_chot.py --tu X --den Y` |

### GĐ2 – tiếng Hàn (chỉ mẫu đã chốt)

| # | Việc | Lệnh |
|---|---|---|
| 9 | Chuẩn bị | `python3 scripts/s2_claude_dich.py --chuan-bi --tu X --den Y` → M câu (gói có đoạn văn làm ngữ cảnh) |
| 10 | Tác tử TẠO dịch | Agent với `giao_viec_tao_gd2.md` ({{SO_CAU}} = M) |
| 11 | Nhận | `python3 scripts/s2_claude_dich.py --nhan --tu X --den Y` → "lỗi 0" |
| 12 | Chuẩn bị soát | `python3 scripts/s2_claude_goi.py --tu X --den Y` |
| 13 | Soát | `python3 CC/xem_gd2.py <id> …` (Mã \| Bản nguồn \| Tiếng Hàn) theo mục 5 |
| 14 | Ghi kết quả | `output/claude/ly_do_lo/gd2_X_Y.json` (`"giai_doan": "2"`, liệt kê **mọi** mẫu GĐ2, kể cả không sửa) → `ghi_ly_do.py` |
| 15 | Python kiểm tra | `python3 scripts/s2_kiem_tra.py --tu X --den Y` → `ĐẠT`; xử lý lỗi / D4 / D7 / D12 rồi chạy lại |
| 16 | Báo cáo + nhật ký | mục 7 |

Excel CTV (khi người dùng yêu cầu): `python3 scripts/s3_xuat_ctv.py --tu A --den B` (mẫu ĐẠT, tiếng Hàn), `python3 scripts/s3b_xuat_ctv_nhat.py --tu A --den B` (mẫu có cờ, CTV tiếng Nhật) → `output/reports/ctv/`. Đoạn văn hiện đầy đủ ở câu con đầu tiên của mỗi đoạn (cột "Ngữ liệu").

## 4. Soát GĐ1 – trọng tâm dạng 11

Chuẩn: **JSON đúng và đủ lời giải gốc**; lời giải gốc phải đúng **so với đoạn văn**. Đầy đủ: `prompts/s1_claude_kiem_tra.md`.

**Cờ s0 trên đầu dòng `xem_gd1` → JSON đúng trông thế nào** (đầy đủ: `scripts/_dau_vao.py` – FLAG_HINT; số liệu toàn dạng: NHAT_KY):

| Cờ | JSON đúng / việc của bạn |
|---|---|
| `khuon_la` (+ `khuon_dich_doan_van` / `khuon_ngan` / `khuon_markdown` / `khuon_khac`) | đủ 4 options, nội dung đặt vào trường gần nhất (không mất chữ); **luôn gắn cờ `thieu_noi_dung`** (3d-6) |
| `khuon_dich_doan_van` | bản dịch đoạn văn → `full_translation` (một khối, mỗi đoạn một `lines[]`, `ja = null`); `Câu hỏi:` → `question.meaning`; lựa chọn tiếng Việt → `options[i].meaning` |
| `thieu_cau_hoi` | `question.ja` = câu hỏi của đề (đề điền chỗ trống: `ア`, `②` …) |
| `thieu_dich_cau_hoi` / `thieu_nghia_lua_chon` | `question.meaning` / `options[i].meaning` = null |
| `cau_hoi_lech` / `lua_chon_lech` | JSON chép theo lời giải; thường chỉ khác kana ↔ kanji → bỏ qua; khác nội dung thật → cờ `khac` |
| `thieu_ket_luan` | `is_match` = (index == đáp án) |
| `co_sau_ket_luan` | câu chữ sau `→ ĐÚNG/SAI` nằm cuối `analysis` |
| `cau_hoi_phu_dinh` | `is_match` theo lời giải ("→ ĐÚNG" có thể = "phù hợp đoạn văn"); dùng lẫn lộn → cờ `dap_an` |
| `ket_luan_lech_dap_an` / `nhieu_dung` | `is_match` vẫn theo lời giải; xem kỹ → thường gắn cờ `dap_an` |
| `trich_ngoai_doan` (gợi ý `TD:`, cảnh báo `K-TD`) | đối chiếu đoạn văn: trích sai / bịa → cờ `trich_dan`; trích câu đã điền chỗ trống, lỗi gõ nhẹ → không cờ (gõ nhẹ: sửa định dạng) |
| `trich_mot_phan` | thường là lược bớt / kana ↔ kanji – chỉ xem khi nhận xét dựa vào phần bị lược |
| `chen_tu_nhat` | từ Nhật chen trong câu Việt bọc `⟪ ⟫`, giữ furigana (**quyết định Q3** – NHAT_KY); từ Việt–Nhật dính (`đồng情する`) → mục 4.1 |
| `doan_co_bang` / `doan_co_anh` | đoạn văn có bảng / ảnh – `doan_van` chỉ còn chữ; ảnh → không đối chiếu được, ghi `[Ghi chú]` |

**Công cụ riêng dạng 11:** Python đã **dò câu trích trong đoạn văn** (`output/reports/trich_dan.csv`: khop / mot_phan / khong) và kiểm `is_match` ↔ kết luận `→ ĐÚNG/SAI` (K-KL), độ phủ chữ Việt **theo từng lựa chọn** (K9 – đặt nhầm lựa chọn là LỖI), số câu trích (K-TR).

### 4.1 Sửa (lỗi tác tử TẠO / định dạng)
- Tác tử TẠO: câu Nhật trong câu Việt bị tách thành `quotes` / câu trích đứng riêng để trong `analysis`; còn 「」 bao ngoài câu trích, ( ) bao ngoài dòng dịch; còn nhãn dẫn (`Trích dẫn:`, `引用:` …); `is_match` khác kết luận; thiếu ⟪ ⟫ / mất furigana; tự tạo `summary` / `full_translation` → sửa (`sai_so_ban_goc` / `khach_quan`).
- Định dạng bản gốc: chữ Việt dính chữ Nhật khi từ đúng **kiểm chứng được** trong đoạn văn / đề (54150_2 `đồng情する` → `同情する`, `nhom: kanji_chen`); lỗi gõ, lặp từ, dính câu (gợi ý `[Nghi dính câu/định dạng]`); câu trích gõ sai 1–2 kana rõ ràng → `sua_dinh_dang` + `[Đã sửa định dạng]`.

### 4.2 Gắn cờ `nghi_noi_dung` (không sửa) – `nhom` hợp lệ: `trich_dan`, `phan_tich`, `dap_an`, `nghia_cau`, `nghia_tu`, `thieu_noi_dung`, `khac`
- `trich_dan`: câu trích không có trong đoạn văn / trích nhầm chỗ / trích từ câu hỏi, lựa chọn mà gọi là đoạn văn.
- `phan_tich`: nhận xét trái đoạn văn ("đoạn văn không đề cập" nhưng có; hiểu ngược ý).
- `dap_an`: kết luận lệch đáp án, nhiều ĐÚNG, câu phủ định dùng "ĐÚNG" lẫn lộn, đáp án đề đáng ngờ.
- `nghia_cau`: dịch câu hỏi / lựa chọn / câu trích lệch câu Nhật (phủ định, chủ thể, あげる/くれる/もらう, thì).
- `thieu_noi_dung`: mọi câu `khuon_la`; khuôn chuẩn mà một lựa chọn không có nhận xét.

**KHÔNG gắn cờ khi:** diễn đạt chưa hay; lựa chọn sai không kèm câu trích; trích lược bớt / bỏ 注n nhưng đúng ý; dịch tự do nhưng đúng ý; câu hỏi / lựa chọn trong lời giải chỉ khác kana ↔ kanji.

### 4.3 File đặc tả lô (một file cho cả lô – xem `prompts/s1_claude_kiem_tra.md` mục "Mẫu lý do")
```json
{"giai_doan": "1",
 "cau": {
  "9_2": {},
  "54150_2": {"thay": [{"duong_dan": "$.options[3].analysis.vi", "cu": "đồng⟪情する⟫", "moi": "⟪同情する⟫"}],
              "sua": [{"duong_dan": "$.options[3].analysis.vi", "loai": "sua_dinh_dang", "nhom": "kanji_chen", "muc_do": "nhe", "ly_do": "chữ Việt dính chữ Nhật – từ đúng 同情する (lựa chọn 4)"}],
              "ghi_chu_ban_goc": ["[Đã sửa định dạng] Lựa chọn 4 – nhận xét: 'đồng情する' → '同情する' – chữ Việt dính chữ Nhật"],
              "nghi_noi_dung": [{"vi_tri": "Toàn bộ lời giải", "nhom": "thieu_noi_dung", "mo_ta": "(quy tắc 3d-6) Khuôn lạ: chỉ vài câu giải thích.", "de_xuat": "Viết lại theo khuôn."}]}
 }}
```
Ghi bằng python (`json.dump(..., ensure_ascii=False, indent=1)`, nội dung qua heredoc `'EOF'`). Liệt kê **mọi** mẫu của lô. **Một file cho mỗi lô mỗi giai đoạn**: các khóa danh sách bị **ghi đè** khi chạy lại – cần sửa thêm thì sửa mục của mẫu đó **trong cùng file** rồi chạy lại. `duong_dan` = đường dẫn `xem_gd1.py` in ra **thêm `$.` ở đầu** (`options[1].quotes[0].ja` → `$.options[1].quotes[0].ja`). `thay` chỉ cho sửa chuỗi nhỏ; sửa cấu trúc (chuyển câu giữa `analysis` ↔ `quotes`, đổi `is_match`) thì python read-modify-write `output/json_vi/checked/<id>.json` + ghi `sua`.

## 5. Soát GĐ2 – tiếng Hàn

Đầy đủ: `prompts/s2_claude_kiem_tra.md`. Trọng tâm:
- **JA** (dịch thẳng từ tiếng Nhật, có đoạn văn làm ngữ cảnh): nghĩa câu hỏi, nghĩa lựa chọn, nghĩa câu trích. **Cùng câu trích → cùng bản dịch** ở mọi câu con của đoạn (D4 – `output/reports/khong_nhat_quan.csv`).
- **VI**: phần nhận xét – đủ ý, -습니다, thuật ngữ (본문, 필자, 선택지, 인용문…).
- **Trợ từ sau ⟪…⟫ theo âm cuối cách đọc** – khối có furigana theo kana cuối trong 《》 (`⟪｜表現《ひょうげん》⟫` → 이/은/을). D12 chỉ cảnh báo – tự soát cả khi có nháy / ngoặc.
- Giữ mọi khối ⟪ ⟫ (kể cả furigana); trường JA giữ các khối `khoi_tieng_nhat_ban_viet_giu`; `{ }` như bản Việt (D7).
- Sửa ko: `thay` với `duong_dan` tới `….ko`; `sua` ghi đường dẫn object. JSON tiếng Việt sai → `loi_json_vi: ["[Lỗi JSON VI] …"]`.

## 6. Sự cố thường gặp

| Hiện tượng | Xử lý |
|---|---|
| `--nhan` GĐ1 LỖI_KỸ_THUẬT (schema / JSON hỏng) | `s1_claude_tao.py --chuan-bi --ids <id> --force` → giao lại tác tử TẠO mẫu đó → `--nhan --ids <id>` |
| `--nhan` GĐ2 LỖI_GĐ2 | `s2_claude_dich.py --chuan-bi --ids <id> --force` → giao lại → `--nhan --ids <id>` |
| `s1_kiem_tra` LỖI_GĐ1 (K…, độ phủ, furigana) | sửa file checked (lỗi tác tử TẠO / định dạng) → `s1_kiem_tra --ids <id>` |
| `Furigana thừa: 引用《いんよう》` / `解説《かいせつ》` | tác tử TẠO chép nhãn tiếng Nhật – bỏ nhãn khỏi JSON (`sai_so_ban_goc`) |
| K9 lựa chọn N thiếu chữ | câu nhận xét bị đặt nhầm lựa chọn / bị bỏ – chuyển về đúng lựa chọn |
| Python tách lời giải sai (khối lựa chọn nhận nhầm dòng `1.` tiếng Nhật trong nhận xét…) – K9 / K-TR báo sai dù JSON đúng | báo người dùng; sửa `scripts/_dang.py` (`parse_loi_giai` – backup trước vào `$HOME/bak11`), chạy lại `python3 scripts/s0_chuan_bi.py` – **không** thêm `--tao-lai-thu-tu`, ghi NHAT_KY |
| `nhom 'X' không hợp lệ` | dùng đúng danh sách `nhom` ở mục 4.2; cần nhóm mới → báo người dùng (code chung) |
| `s2_kiem_tra` báo `[Lỗi JSON VI]` → CẦN_SỬA_GĐ1 | `s1_claude_goi --ids <id>` → sửa → `s1_kiem_tra` → `s1_chot` → GĐ2 lại |
| Lô đang dở | `CC/tien_do.py X Y` cho biết bước đã qua của từng mẫu (soát 'dở' = còn `_huong_dan`); chạy tiếp từ bước đó |

## 7. Báo cáo cuối lô (tiếng Việt, ngắn)

1. Bảng ĐẠT / nghi nội dung (id). 2. Mỗi mẫu gắn cờ: 1 dòng lý do; sửa định dạng / sửa ko: liệt kê ngắn. 3. Lũy kế (`CC/tien_do.py`). 4. Lệnh tiếp: **"Chạy dạng 11 mẫu <Y+1> đến <Y+10>"** (nếu Y cắt ngang một đoạn, gợi ý kết thúc ở cuối một đoạn – xem cột `doan`; quá ~30 mẫu trong cuộc trò chuyện: đề nghị mở cuộc trò chuyện mới).

Sau báo cáo **cập nhật `NHAT_KY.md`**: dòng bảng lô; quyết định / cách dịch mới; sự cố.
