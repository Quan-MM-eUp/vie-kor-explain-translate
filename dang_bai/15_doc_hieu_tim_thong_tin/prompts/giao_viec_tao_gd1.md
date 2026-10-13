<!-- Mẫu lời giao việc cho TÁC TỬ TẠO – GĐ1. Tác tử KIỂM TRA chép nguyên văn phần dưới vào tham số prompt của Agent
     (subagent_type "general-purpose", model "opus", description "Tác tử TẠO: JSON mẫu X–Y"), thay {{SO_CAU}}. -->
Bạn là tác tử TẠO (Claude A) của pipeline dạng 15 (Đọc hiểu – Tìm thông tin). Làm việc trên máy người dùng bằng công cụ mcp__remote-devices__device_bash (nạp bằng ToolSearch query "select:mcp__remote-devices__device_bash" nếu chưa có). Thư mục dạng bài: $HOME/mnt/Vie-Kor/dang_bai/15_doc_hieu_tim_thong_tin (gọi là DANG).

Nhiệm vụ: làm đúng theo DANG/prompts/s1_claude_tao.md cho toàn bộ {{SO_CAU}} câu trong DANG/output/claude/tao_gd1_danh_sach.json.
- Đọc kỹ DANG/prompts/s1_claude_tao.md, rồi TOÀN BỘ DANG/prompts/s1_chuyen_json.md (hướng dẫn chi tiết + ví dụ), rồi schema DANG/schema/reading_listening.v1.api.json.
- Với từng câu: đọc file_vao (trường yeu_cau), tạo JSON đúng schema (đủ mọi khóa, null / [] khi không có, không có reference_raw), ghi vào file_ra bằng python json.dump(ensure_ascii=False, indent=1). Nên cắt chuỗi từ chính loi_giai_goc theo dòng rồi thêm ⟪ ⟫ (tránh gõ lại tiếng Nhật); PHẢI tự đọc lại từng lựa chọn so với lời giải: câu trích nào vào quotes (bỏ nhãn dẫn, bỏ 「」 / ( ) ngoài cùng), chữ nào vào analysis (giữ thứ tự, \n, gạch đầu dòng, phép tính), is_match theo đúng '→ ĐÚNG/SAI' của lời giải.
- Sau khi ghi, tự kiểm tra schema từng file: cd DANG/scripts && python3 -c "import json,_dang as D; from pipeline_chung.checks_chung import schema_errors; s=json.load(open(D.P(D.cfg()['schema_api']))); print(schema_errors(json.load(open(D.OUT('json_vi','claude_tao','<id>.json'),encoding='utf-8')), s))" – lỗi thì sửa cấu trúc (không đổi nội dung chép).
- CHỈ mở các file: 2 prompt, schema, danh sách, file_vao và file_ra của các câu trong danh sách. KHÔNG mở/tìm kiếm file nào khác, không chạy script pipeline khác, không sửa nội dung lời giải dù thấy sai (trích dẫn không có trong ngữ liệu, tính sai, kết luận trái đáp án…).
- Chép NGUYÊN VĂN, bọc ⟪ ⟫ mọi tiếng Nhật trong câu tiếng Việt (kể cả kana đơn, tên katakana, cụm có furigana, ⟪600円⟫), giữ { } và furigana ｜…《…》 đúng chỗ. Ngữ liệu chỉ để hiểu – không chép vào JSON. question.ja = null khi lời giải không có dòng câu hỏi tiếng Nhật.

Báo lại ngắn: danh sách id đã ghi + kết quả schema + điểm khó (chỉ mô tả).
