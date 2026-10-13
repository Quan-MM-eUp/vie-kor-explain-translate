# Sổ tay chạy – dạng 13 Đọc hiểu tổng hợp (cho phiên Claude mới)

> Viết 2026-10-08. Một cuộc trò chuyện Cowork **mới** chỉ cần đọc **file này + `NHAT_KY.md`** là chạy được, **không đọc lại cả project**.
> Câu mở đầu người dùng gõ: **"Đọc dang_bai/13_doc_hieu_tong_hop/SO_TAY_CHAY.md rồi chạy dạng 13 lô N"** (hoặc "… lô tiếp theo", "… mẫu X đến Y").
> Trả lời người dùng bằng **tiếng Việt**. Dạng 13 chạy **hoàn toàn bằng Claude Opus 5.5 Cowork** – không có bước GPT API.
> Dạng 13 = đoạn văn **A / B** (có khi C, hoặc 相談者 + 回答者Ａ/Ｂ; 15 đoạn N2 là bài đơn không A/B) + 1–3 câu hỏi mỗi đoạn; lời giải khuôn đọc hiểu → schema `reading_listening.v1`. **Lô = 4 đoạn văn (8–11 câu)** theo cột `lo` của `output/thu_tu_chay.csv` – **lô 1 là pilot**.

---

## 0. Khởi động phiên (làm theo thứ tự)

1. Nạp công cụ: ToolSearch `select:mcp__remote-devices__device_bash`. Mọi lệnh chạy trên máy người dùng bằng công cụ này.
2. `DANG=$HOME/mnt/Vie-Kor/dang_bai/13_doc_hieu_tong_hop` – **mỗi lệnh đều `cd $DANG` trước**. Công cụ chung: `python3 ../../pipeline_chung/cong_cu/<tên>.py` (gọi tắt `CC/<tên>.py`).
3. Đọc `NHAT_KY.md`.
4. `python3 scripts/lo.py` (bảng các lô + trạng thái + lô tiếp theo) và `python3 scripts/lo.py N` (in `--tu X --den Y` của lô N). Từng mẫu: `python3 CC/tien_do.py X Y`. (**Không** dùng "lô gợi ý" của `CC/tien_do.py` – nó đếm theo số câu, có thể cắt ngang đoạn.)
5. Đọc **một lần mỗi phiên** trước khi soát: `prompts/s1_claude_kiem_tra.md` (tiêu chí GĐ1 – mục 3d-1…7) và `prompts/s2_claude_kiem_tra.md`. Phần ghi lý do làm bằng **file đặc tả lô + `ghi_ly_do.py`** (mục 4.3).
6. Phạm vi: `--tu X --den Y` (stt trong `output/thu_tu_chay.csv`) – do `scripts/_dang.py` xử lý nên không hiện trong `--help`. **Không dùng `--lo` với `scripts/*.py`**; riêng `CC/xem_gd1.py` / `CC/xem_gd2.py`: `--lo X Y` = khoảng stt. Người dùng xin khoảng cắt ngang đoạn → đề nghị lấy tròn lô.
7. Phiên không có công cụ **Agent** → dừng, báo người dùng.

## 1. Quy tắc bất biến

- **Bảo mật:** không đọc / mở `.env`, không in API key. Không chạy `git status`. **Không xóa file** – cần bỏ thì `mv -n` vào `_to_delete/`.
- **Nội dung lời giải sai → chỉ gắn cờ** `nghi_noi_dung`, **không sửa**. Chỉ sửa **định dạng** (`sua_dinh_dang` + `nhom` + dòng `[Đã sửa định dạng] …`) và **lỗi của tác tử TẠO**. Ghi chú không kèm thay đổi JSON → `[Ghi chú] …`.
- **Chạy song song nhiều dạng:** chỉ sửa file trong `$DANG`; **không sửa** `pipeline_chung/`, `explanation_schema/`, dạng khác. Cần sửa code chung → dừng, báo người dùng. Được sửa `scripts/_doc_hieu_13.py`, `scripts/_dang.py`, `scripts/_dau_vao.py`, prompt dạng 13 khi lỗi tách lời giải (mục 6), sau khi báo.
- Nhóm cờ `trich_dan`, `phan_tich` được `scripts/_dang.py` thêm vào `claude_log.NHOM_NOI_DUNG` lúc chạy (không cần sửa file chung).
- Ngữ cảnh: tối đa **3 lô (~30 câu) mỗi cuộc trò chuyện**.

## 2. Hai tác tử

- **Tác tử TẠO (Claude A)** = tác tử con (Agent tool, `subagent_type: "general-purpose"`, `model: "opus"`). Lời giao việc chép **nguyên văn** `prompts/giao_viec_tao_gd1.md` / `giao_viec_tao_gd2.md` (thay `{{SO_CAU}}`, bỏ dòng `<!-- -->`; GĐ2: thay `{{CAU_CO_DINH}}` bằng các dòng mục "Cách dịch đã thống nhất" trong NHAT_KY, chưa có thì "(chưa có)").
- **Tác tử KIỂM TRA** = phiên chính (bạn). Không tự tạo bản.

## 3. Quy trình một lô X–Y

### GĐ1 – JSON tiếng Việt

| # | Việc | Lệnh |
|---|---|---|
| 1 | Chuẩn bị | `python3 scripts/s1_claude_tao.py --chuan-bi --tu X --den Y` → N câu (chạy lại an toàn) |
| 2 | Tác tử TẠO | Agent với `giao_viec_tao_gd1.md` ({{SO_CAU}} = N). Ghi lại "điểm khó" |
| 3 | Nhận | `python3 scripts/s1_claude_tao.py --nhan --tu X --den Y` → "lỗi 0, chưa có 0" |
| 4 | Chuẩn bị soát | `python3 scripts/s1_claude_goi.py --tu X --den Y` |
| 5 | Soát | `python3 CC/xem_gd1.py <id> …` (in **đoạn văn A/B một lần cho mỗi đoạn**, rồi lời giải gốc + gợi ý + JSON) – soát **theo từng đoạn**; đọc đoạn văn trước |
| 6 | Ghi kết quả | `output/claude/ly_do_lo/gd1_X_Y.json` (mục 4.3) → `python3 CC/ghi_ly_do.py output/claude/ly_do_lo/gd1_X_Y.json` |
| 7 | Python kiểm tra | `python3 scripts/s1_kiem_tra.py --tu X --den Y` → cờ = `CHỜ_DUYỆT_NỘI_DUNG`, còn lại `GĐ1_XONG`; `LỖI_GĐ1` → mục 6 |
| 8 | Chốt | `python3 scripts/s1_chot.py --tu X --den Y` (lô 1 pilot: **chờ người dùng duyệt** trước khi chốt) |

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

Excel CTV (khi người dùng yêu cầu): `python3 scripts/s3_xuat_ctv.py --tu A --den B` (ĐẠT, tiếng Hàn – cột "Ngữ liệu" = đoạn văn A/B, một lần mỗi đoạn) · `python3 scripts/s3b_xuat_ctv_nhat.py --tu A --den B` (câu có cờ, CTV tiếng Nhật) → `output/reports/ctv/`. Báo cáo số liệu: `python3 scripts/s9_bao_cao.py --tu A --den B`.

## 4. Soát GĐ1

Chuẩn: **JSON đúng và đủ lời giải gốc**; lời giải phải đúng **so với đoạn văn A / B**. Đầy đủ: `prompts/s1_claude_kiem_tra.md`.

**Cờ s0 hay gặp → JSON đúng** (đầy đủ: FLAG_HINT trong `scripts/_dau_vao.py`; mô tả cờ: `scripts/_doc_hieu_13.py` FLAG_TEXT):

| Cờ | JSON đúng / việc của tác tử KIỂM TRA |
|---|---|
| (mọi câu khuôn chuẩn) | câu trích **khối** → `quotes[]` (ja bỏ 「」 ngoài, meaning = bản dịch trong ngoặc); câu dẫn có A/B giữ trong `analysis`; nhãn trống `Trích dẫn:` / `Câu gốc:` / `Giải thích:` bỏ |
| `trich_dan_giua_cau` | câu trích giữa câu Việt **ở lại** `analysis`, bọc 「⟪…⟫」 – không tính thiếu quotes (K-QN chỉ đếm câu trích khối) |
| `trich_dan_ngoai_doan`, gợi ý `K-TD` | kiểm tay với đoạn văn → sai thật: cờ `trich_dan` (3d-1); lệch do ruby / `…` / dấu câu: `[Ghi chú] … không gắn cờ` |
| `trich_dan_sai_nguon`, gợi ý `K-NGUON` | đọc câu dẫn + đoạn văn → gán nhầm A↔B thật: cờ `trich_dan` (3d-1) |
| `nhieu_dung`, `lech_dap_an` | `is_match` theo lời giải; cờ `dap_an` (3d-3) |
| `khuon_la` (+ `dich_doan_van` / `chi_dap_an` / `goi_y` / `khuon_khac`) | JSON theo mục "Khuôn lạ" của `s1_chuyen_json.md`; **luôn** gắn cờ `thieu_noi_dung` (3d-5), `vi_tri: "Toàn câu"` |
| `cau_hoi_lech`, `lua_chon_lech` | lệch do gõ lặp chữ / ruby hỏng → `sua_dinh_dang`; kana ↔ chữ Hán cùng cách đọc → bỏ qua; khác chữ – nghĩa → cờ `cau_khac_de` (3d-6) |
| `chen_tu_nhat` | từ Nhật trong câu Việt bọc ⟪ ⟫; dính chữ (`đồng情する`) → `sua_dinh_dang`; hỏng không hiểu được (16885_2) → cờ `khac` |
| `doan_khong_ab` | chỉ là lưu ý phân loại (đã ghi NHAT_KY) – không gắn cờ |
| `ruby_hong` | Python đã đổi `<|X;y|` → `｜X《y》`; ruby hỏng kiểu khác → `sua_dinh_dang` `nhom: furigana` |

### 4.1 Sửa (lỗi tác tử TẠO / định dạng) – như prompt mục 1, 2.
### 4.2 Gắn cờ (`nhom`: `trich_dan`, `phan_tich`, `dap_an`, `nghia_cau`, `thieu_noi_dung`, `cau_khac_de`, `khac`) – theo 3d-1…7; **phải đọc đoạn văn** cho 3d-1, 3d-2.

### 4.3 File đặc tả lô (một file mỗi lô mỗi giai đoạn)
```json
{"giai_doan": "1",
 "cau": {
  "16904_1": {},
  "16886_2": {"nghi_noi_dung": [{"vi_tri": "Lựa chọn 1 – câu trích 1", "nhom": "trich_dan",
                                  "mo_ta": "(3d-1) Lời giải nói 'Đoạn A có câu' nhưng 「努力できる人にとっては…」 nằm ở đoạn B.",
                                  "de_xuat": "Đổi câu dẫn thành 'Đoạn B có câu:'."}]},
  "12648_2": {"thay": [{"duong_dan": "$.question.ja", "cu": "占占い", "moi": "占い"}],
              "sua": [{"duong_dan": "$.question.ja", "loai": "sua_dinh_dang", "nhom": "lap_tu", "muc_do": "nhe", "ly_do": "lặp chữ do gõ"}],
              "ghi_chu_ban_goc": ["[Đã sửa định dạng] Câu hỏi: '占占い' → '占い' – lặp chữ do gõ"]}
 }}
```
Ghi bằng python (`os.makedirs('output/claude/ly_do_lo', exist_ok=True)` rồi `json.dump(..., ensure_ascii=False, indent=1)`, heredoc `'EOF'`). Liệt kê **mọi** câu của lô. Danh sách bị **ghi đè** khi chạy lại – sửa thêm thì sửa trong **cùng file** rồi chạy lại. `duong_dan` = đường dẫn `xem_gd1.py` in ra **thêm `$.`** ở đầu (`options[1].quotes[0].meaning.vi` → `$.options[1].quotes[0].meaning.vi`). Sửa bool / cấu trúc (chuyển câu trích giữa `quotes` ↔ `analysis`, `is_match`) → python read-modify-write `output/json_vi/checked/<id>.json` + ghi `sua`.

## 5. Soát GĐ2 – tiếng Hàn

Theo `prompts/s2_claude_kiem_tra.md`: nghĩa câu hỏi / lựa chọn / câu trích **dịch thẳng từ tiếng Nhật** (đúng chủ thể A / B, phủ định, so sánh); **câu trích giống nhau dịch giống hệt** (D15 trong câu, D4 giữa các câu – `output/reports/khong_nhat_quan.csv`); nhận xét dịch từ tiếng Việt, -습니다, câu dẫn "Đoạn A có câu:" thống nhất (`A 글에 다음 문장이 있습니다:` – xem glossary); trợ từ sau ⟪kana⟫ theo âm cuối (D12 chỉ cảnh báo); đoạn văn không dịch. Các câu con cùng đoạn xem liền nhau.

## 6. Sự cố thường gặp

| Hiện tượng | Xử lý |
|---|---|
| `--nhan` GĐ1 LỖI_KỸ_THUẬT | `s1_claude_tao.py --chuan-bi --ids <id> --force` → giao lại → `--nhan --ids <id>` |
| `--nhan` GĐ2 LỖI_GĐ2 | `s2_claude_dich.py --chuan-bi --ids <id> --force` → giao lại → `--nhan --ids <id>` |
| `s1_kiem_tra` LỖI_GĐ1 | đọc lỗi; sửa file checked (lỗi tác tử TẠO / định dạng) → `s1_kiem_tra --ids <id>`. "Độ phủ tiếng Việt … thiếu: [nhãn lạ]" do nhãn mới → báo người dùng, thêm vào `LABELS` trong `scripts/_doc_hieu_13.py` |
| "Furigana thừa/sai" chỉ vì `correct.option_ja` | đã bỏ qua bằng `FURI_SKIP` – nếu vẫn báo, xem furigana ở `option_ja` / `quotes` |
| Python tách lời giải / câu trích sai (`phan` trong norm), `luu_y` trái lời giải | báo người dùng; sửa `scripts/_doc_hieu_13.py` (backup `$HOME/bak13`), chạy lại `python3 scripts/s0_chuan_bi.py` – **không** thêm `--tao-lai-thu-tu`; ghi NHAT_KY |
| `[Lỗi JSON VI]` ở GĐ2 → CẦN_SỬA_GĐ1 | `s1_claude_goi --ids <id>` → sửa → `s1_kiem_tra` → `s1_chot` → GĐ2 lại |
| Lô đang dở | `CC/tien_do.py X Y` (soát 'dở' = còn `_huong_dan`); chạy tiếp từ bước đó |

## 7. Báo cáo cuối lô (tiếng Việt, ngắn)

1. Bảng ĐẠT / nghi nội dung (id), theo đoạn văn. 2. Mỗi câu gắn cờ: 1 dòng lý do; sửa định dạng / sửa ko: liệt kê ngắn. 3. Lũy kế (`scripts/lo.py`). 4. Lệnh tiếp: **"Chạy dạng 13 lô <N+1>"** (sau lô thứ 3: đề nghị mở cuộc trò chuyện mới). Lô 1 (pilot): dừng sau GĐ1 bước 7 để người dùng duyệt JSON + cờ trước khi chốt / dịch.

Sau báo cáo **cập nhật `NHAT_KY.md`**: dòng bảng lô; quyết định / cách dịch mới; sự cố; số token tác tử TẠO mỗi giai đoạn (đo chi phí).
