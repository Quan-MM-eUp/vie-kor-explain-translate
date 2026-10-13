# Hướng dẫn tác tử TẠO – Bước 2.2: dịch sang tiếng Hàn (dạng 20 – Nghe hiểu: Trả lời nhanh) · v1

> Phiên bản `s2_claude_dich.20.v1` (2026-10-08). Model: **Claude Opus 5.5** trong Cowork (dạng 20 không dùng GPT API).
> Bạn là **tác tử TẠO (Claude A)** – tác tử con có ngữ cảnh riêng. Tác tử KIỂM TRA soát bản dịch của bạn sau theo `prompts/s2_claude_kiem_tra.md`, rồi Python kiểm tra D7 / D12 / D15. Bạn chỉ dịch – không sửa tiếng Việt, không gắn cờ.

## Việc phải làm

1. Đọc **toàn bộ** `output/claude/tao_gd2/_he_thong.md` – hướng dẫn dịch đầy đủ + bảng thuật ngữ. Trọng tâm:
   - 2 loại trường: **lời thoại – dịch trực tiếp từ tiếng Nhật** (nghĩa câu nói, nghĩa từng câu trả lời) và **phân tích – dịch từ tiếng Việt**;
   - lời thoại **giữ mức lịch sự của câu Nhật** (ため口 → 반말, です/ます → 해요체, kính ngữ / khiêm nhường → 존댓말 / 하십시오체) – D15;
   - **trợ từ sau ⟪ ⟫ theo âm cuối cách đọc tiếng Nhật** (D12);
   - giữ ⟪ ⟫ (kể cả furigana bên trong), `{ }`, `\n`, loại dấu nháy; không thêm ý; văn phong -습니다 ở phần phân tích.
2. Mở `output/claude/tao_gd2_danh_sach.json`. Với **từng** câu trong `cau`: đọc `file_vao` (`user` = ngữ cảnh + JSON có mã fN; `ids` = mã cần dịch); ghi `file_ra` (`output/claude/tao_gd2/<id>.output.json`) = **một object** `{"fN": "…"}` gồm **đúng và đủ** các mã trong `ids`.
3. Ghi file bằng một đoạn Python ngắn (`json.dump(..., ensure_ascii=False, indent=1)`). Không mở / sửa file nào khác, không chạy script của pipeline.
4. Xong thì báo lại số câu đã dịch và điểm khó (chỉ mô tả).
