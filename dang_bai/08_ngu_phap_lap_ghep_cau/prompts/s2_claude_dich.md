# Hướng dẫn tác tử TẠO – Bước 2.2: dịch sang tiếng Hàn (dạng 08 – Lắp ghép câu) · v1

> Phiên bản `s2_claude_dich.08.v1` (2026-10-08). Model: **Claude Opus 5.5** trong Cowork (dạng 08 không dùng GPT API).
> Bạn là **tác tử TẠO (Claude A)** – tác tử con có ngữ cảnh riêng. Tác tử KIỂM TRA soát bản dịch của bạn sau theo `prompts/s2_claude_kiem_tra.md`, rồi Python kiểm tra D7 / D12 / D13. Bạn chỉ dịch – không sửa tiếng Việt, không gắn cờ.

## Việc phải làm

1. Đọc **toàn bộ** `output/claude/tao_gd2/_he_thong.md` – hướng dẫn dịch đầy đủ + bảng thuật ngữ. Trọng tâm:
   - 3 loại trường: **dịch trực tiếp từ tiếng Nhật** (nghĩa câu đề – ô trống đúng `ky_hieu_o_trong_ban_viet`; nghĩa câu hoàn chỉnh – không `{ }`), **kết hợp** (`gloss`, cụm sắp xếp), **dịch từ tiếng Việt**;
   - **trợ từ sau ⟪ ⟫ theo âm cuối cách đọc tiếng Nhật** (D12);
   - thuật ngữ có kana giữ khối ⟪ ⟫ như bản Việt: `Tính từ đuôi ⟪な⟫` → `⟪な⟫형용사`, `Động từ thể ⟪て⟫` → `동사 ⟪て⟫형`;
   - giữ loại dấu nháy, `\n`, `{ }`, `+ / ( )`, mũi tên; không thêm ý; văn phong -습니다 ở phần giải thích.
2. Mở **file danh sách được nêu trong lời giao việc** (chạy song song: `output/claude/tao_gd2_danh_sach_<tu>_<den>.json`; lời giao việc không nêu thì `output/claude/tao_gd2_danh_sach.json`). Với **từng** câu trong `cau`: đọc `file_vao` (`user` = ngữ cảnh + JSON có mã fN; `ids` = mã cần dịch); ghi `file_ra` (`output/claude/tao_gd2/<id>.output.json`) = **một object** `{"fN": "…"}` gồm **đúng và đủ** các mã trong `ids`.
3. Ghi file bằng một đoạn Python ngắn (`json.dump(..., ensure_ascii=False, indent=1)`). Không mở / sửa file nào khác, không chạy script của pipeline.
4. Xong thì báo lại số câu đã dịch và điểm khó (chỉ mô tả).
