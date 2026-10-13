Hãy sửa pipeline của **5 dạng bài 06–10** để từ nay **chỉ chạy các mẫu tiếp theo thuộc đề JLPT** (bỏ mẫu NAT-TEST). Trả lời tôi bằng tiếng Việt.

Thư mục: `C:\Users\MaiMinhQuan\Desktop\Vie-Kor` (trên máy tôi, dùng `device_bash`, mount tại `$HOME/mnt/Vie-Kor`). Các dạng:
- `dang_bai/06_tu_vung_ung_dung_tu`
- `dang_bai/07_ngu_phap_lua_chon_ngu_phap`
- `dang_bai/08_ngu_phap_lap_ghep_cau`
- `dang_bai/09_ngu_phap_theo_doan_van` (lô 12 câu = 3 đoạn văn; `thu_tu_chay.csv` có cột `doan`)
- `dang_bai/10_doc_hieu_doan_van_ngan` (`thu_tu_chay.csv` có cột `lo_nho`, `nhom_doan_van`)

## Tiêu chí "đề JLPT" (đã chốt, không hỏi lại)
Dựa vào cột `thi_thu_thuoc_de` của file dữ liệu (`config.json` → `du_lieu`). Cột ghi các đề thi thử chứa câu, cách nhau `|`.
- **Bỏ** mẫu mà cột chứa chữ `Nat Test` (kể cả khi có thêm đề khác).
- **Giữ** mẫu thuộc đề `Test …`, `Vocabulary Test …`, `Reading Test …`, `Mock Full Exam …` và mẫu **ô trống** (chỉ có ở phần luyện tập).
- **Mẫu đã chạy giữ nguyên kết quả.** Chỉ lọc từ **mẫu chưa làm đầu tiên** của mỗi dạng (xác định bằng `NHAT_KY.md` mục "Lô tiếp theo" + `python3 ../../pipeline_chung/cong_cu/tien_do.py` chạy trong thư mục dạng; kiểm tra mọi mẫu từ đó trở đi đều `ĐANG_XỬ_LÝ`). Tham khảo hiện tại: 06 → 361, 07 → 311 (xác nhận lại, NHAT_KY và tien_do chênh nhau), 08 → 251, 09 → 289, 10 → 292.

## Cách làm mẫu – đã làm xong ở dạng 02, hãy làm y hệt
Đọc trước 4 chỗ này ở `dang_bai/02_tu_vung_thay_doi_cach_noi/`:
1. `config.json` → mục `loc_nguon_de` (`bat`, `tu_mau`, `cot`, `bo_neu_chua`, `_ghi_chu`).
2. `scripts/_dang.py` → biến `CA_NAT` (cờ `--ca-nat`, ngay sau dòng `TU, DEN = _pop_int(...)`), hàm `mau_ngoai_jlpt()`, `_loc_jlpt()`, và 2 chỗ gọi `_loc_jlpt` trong `select_ids` (nhánh `--tu/--den` và nhánh `--lo/--tat-ca`; **không** lọc `--ids`, `--pilot`).
3. `scripts/lo_jlpt.py` → gợi ý khoảng `--tu X --den Y` chứa đủ N mẫu JLPT chưa làm (`--lo 3`, `--thong-ke`).
4. `SO_TAY_CHAY.md` mục **0.6b** và dòng **2026-10-11** trong `NHAT_KY.md` mục Tổng quan.

Với mỗi dạng 06–10:
1. Sao lưu `scripts/_dang.py`, `config.json`, `SO_TAY_CHAY.md`, `NHAT_KY.md` vào `<dạng>/_sao_luu/2026-10-11_truoc_loc_jlpt/` (`cp -n`).
2. Xem `select_ids` của dạng đó trước khi sửa – có thể khác dạng 02. Kiểm tra thứ tự `--tu/--den` dùng (file dữ liệu hay `output/thu_tu_chay.csv`) và so với `thu_tu_chay.csv`; `mau_ngoai_jlpt()` và `lo_jlpt.py` phải đếm stt **theo đúng thứ tự mà `--tu/--den` dùng**.
3. Thêm `loc_nguon_de` vào `config.json` (sửa bằng python đọc–ghi, giữ nguyên các mục khác), sửa `_dang.py`, thêm `scripts/lo_jlpt.py`, cập nhật `SO_TAY_CHAY.md` + `NHAT_KY.md` (thay "Lô tiếp theo" bằng lô JLPT đầu tiên).
4. **Dạng 09 và 10 (theo đoạn văn):** không được cắt đôi một đoạn văn / một lô nhỏ. Trước khi sửa, thống kê trong mỗi đoạn (`doan` / `nhom_doan_van` / `lo_nho`) có đoạn nào **lẫn** câu NAT và câu không NAT không. Nếu không có → lọc theo đoạn; nếu có → **dừng, báo số liệu và hỏi tôi** cách xử lý (bỏ cả đoạn nếu có câu NAT / giữ cả đoạn nếu có câu JLPT / lọc từng câu). `lo_jlpt.py` của 2 dạng này phải gợi ý lô tròn đoạn (09: 3 đoạn = 12 câu; 10: theo `lo_nho`).
5. Kiểm tra: `python3 -c "import ast;…"` cho `_dang.py`; chạy `lo_jlpt.py --thong-ke` và `lo_jlpt.py --lo 3`; gọi thử `select_ids` với một khoảng có mẫu NAT (phải in dòng "Lọc nguồn đề … bỏ N mẫu") và với khoảng đã chạy (số mẫu không đổi so với trước khi sửa).

## Quy tắc
- **Chỉ sửa file trong 5 thư mục dạng 06–10.** Không sửa `pipeline_chung/`, `explanation_schema/`, dạng khác. Cần sửa code chung → dừng, báo tôi.
- Không xóa file (bị chặn) – cần bỏ thì `mv -n` vào `_to_delete/`. Không đọc `.env`, không in API key, không chạy GPT API, không `git status`.
- Không đổi trạng thái trong `output/reports/trang_thai.csv`, không chạy `s0_chuan_bi.py`, không chạy lô nào – chỉ sửa pipeline.
- Có thể dùng `TaskCreate` theo dõi 5 dạng.

## Báo cáo cuối (ngắn)
Bảng mỗi dạng: lọc từ mẫu nào · số mẫu JLPT sẽ chạy · số mẫu NAT bỏ · 3 lô JLPT đầu tiên (`--tu X --den Y`) · câu mở đầu cho phiên chạy mới, dạng: "Đọc dang_bai/<dạng>/SO_TAY_CHAY.md rồi chạy dạng <số> mẫu X đến Y". Kèm vấn đề phát sinh (nếu có).
