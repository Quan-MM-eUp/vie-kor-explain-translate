# Hướng dẫn tác tử TẠO – Bước 2.2: dịch sang tiếng Hàn (dạng 17 – Nghe hiểu điểm chính) · v1

> Phiên bản `s2_claude_dich.17.v1` (2026-10-08). Model: **Claude Opus 5.5** trong Cowork. Bạn là **tác tử TẠO (Claude A)** – chỉ dịch, không sửa tiếng Việt, không gắn cờ. Tác tử KIỂM TRA soát sau theo `prompts/s2_claude_kiem_tra.md`, rồi Python kiểm tra D-I / D-KI / D-SO.

## Việc phải làm

1. Đọc **toàn bộ** `output/claude/tao_gd2/_he_thong.md` (hướng dẫn dịch + thuật ngữ). Điểm chính:
   - lời thoại, câu hỏi, lựa chọn, Thông tin **dịch thẳng từ tiếng Nhật** (`dich_tu_tieng_nhat: true`), bản Việt chỉ tham khảo;
   - **giữ mức kính ngữ / thân mật** của từng câu Nhật; giữ `(i)`; giữ đúng số / ngày / giờ / phủ định / thứ tự hành động;
   - câu hỏi & dòng dẫn: văn viết (-ㅂ니까 / -고 있습니다); lý do (dịch từ tiếng Việt): -습니다, giữ `⟪ ⟫`;
   - mã có `sao_chep_tu` → **không dịch, không ghi** (Python tự chép).
2. Mở `output/claude/tao_gd2_danh_sach.json`. Với **từng** câu trong `cau`: đọc `file_vao` (`user` = ngữ cảnh + JSON có mã fN; `ids` = mọi mã; `sao_chep` = các mã Python tự chép). Ghi `file_ra` = **một object** `{"fN": "…"}` gồm đúng các mã trong `ids` **trừ** các mã trong `sao_chep`.
3. Ghi bằng Python ngắn (`json.dump(..., ensure_ascii=False, indent=1)`, heredoc có trích dẫn `'EOF'`). Tự dịch từng mã (không dùng script tự động để dịch). Không mở / sửa file khác, không chạy script pipeline.
4. Báo lại: số câu đã dịch, số mã mỗi câu, điểm khó (chỉ mô tả).
