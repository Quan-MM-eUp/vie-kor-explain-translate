<!-- Mẫu lời giao việc cho TÁC TỬ TẠO – GĐ1. Tác tử KIỂM TRA chép nguyên văn phần dưới vào tham số prompt của Agent
     (subagent_type "general-purpose", model "opus", description "Tác tử TẠO: JSON mẫu X–Y"), thay {{SO_CAU}}. -->
Bạn là tác tử TẠO (Claude A) của pipeline dạng 21 (Nghe hiểu tổng hợp). Làm việc trên máy người dùng bằng công cụ mcp__remote-devices__device_bash (nạp bằng ToolSearch query "select:mcp__remote-devices__device_bash" nếu chưa có). Thư mục dạng bài: $HOME/mnt/Vie-Kor/dang_bai/21_nghe_hieu_tong_hop (gọi là DANG).

Nhiệm vụ: làm đúng theo DANG/prompts/s1_claude_tao.md cho toàn bộ {{SO_CAU}} câu trong DANG/output/claude/tao_gd1_danh_sach.json.
- Đọc kỹ DANG/prompts/s1_claude_tao.md, rồi TOÀN BỘ DANG/prompts/s1_chuyen_json.md, rồi schema DANG/schema/reading_listening.v1.api.json.
- Với từng câu: đọc file_vao (trường yeu_cau), tạo JSON đúng schema (đủ mọi khóa, null khi không có, không có reference_raw), ghi vào file_ra bằng python json.dump(ensure_ascii=False, indent=1). Được dùng Python để dựng khung (tách nhãn người nói của loi_thoai_ja, tách khối 1.–4.), nhưng PHẢI tự đọc lại từng câu: ghép đúng lượt thoại JA ↔ dòng dịch VI, đặt đúng trường từng câu nhận xét / câu trích.
- Sau khi ghi, tự kiểm tra schema từng file: cd DANG/scripts && python3 -c "import json,_dang as D; from pipeline_chung.checks_chung import schema_errors; s=json.load(open(D.P(D.cfg()['schema_api']))); print(schema_errors(json.load(open(D.OUT('json_vi','claude_tao','<id>.json'),encoding='utf-8')), s))" – lỗi thì sửa cấu trúc (không đổi nội dung chép).
- CHỈ mở các file: 2 prompt, schema, danh sách, file_vao và file_ra của các câu trong danh sách. KHÔNG mở/tìm kiếm file nào khác, không chạy script pipeline khác, không sửa nội dung lời giải dù thấy sai.
- Chép NGUYÊN VĂN: lines[].ja đúng từng chữ của loi_thoai_ja (kể cả lỗi gõ, (i)/(ii)); option_ja / quotes[].ja đúng như lời giải (kể cả furigana ｜…《…》); bọc ⟪ ⟫ mọi tiếng Nhật trong câu tiếng Việt; bỏ nhãn người nói ("Nam:", "Nam nói:"); dòng dịch câu hỏi / lựa chọn không đưa vào full_translation; câu con 2 có ghi "full_translation: null – Python chép…" thì để full_translation = null.

Báo lại ngắn: danh sách id đã ghi + kết quả schema + điểm khó (chỉ mô tả).
