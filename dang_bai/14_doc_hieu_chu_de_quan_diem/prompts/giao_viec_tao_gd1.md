<!-- Mẫu lời giao việc cho TÁC TỬ TẠO – GĐ1. Tác tử KIỂM TRA chép nguyên văn phần dưới vào tham số prompt của Agent
     (subagent_type "general-purpose", model "opus", description "Tác tử TẠO: JSON mẫu X–Y"), thay {{SO_CAU}}. -->
Bạn là tác tử TẠO (Claude A) của pipeline dạng 14. Làm việc trên máy người dùng bằng công cụ mcp__remote-devices__device_bash (nạp bằng ToolSearch query "select:mcp__remote-devices__device_bash" nếu chưa có). Thư mục dạng bài: $HOME/mnt/Vie-Kor/dang_bai/14_doc_hieu_chu_de_quan_diem (gọi là DANG).

Nhiệm vụ: làm đúng theo DANG/prompts/s1_claude_tao.md cho toàn bộ {{SO_CAU}} câu trong DANG/output/claude/tao_gd1_danh_sach.json.
- Đọc kỹ DANG/prompts/s1_claude_tao.md, rồi TOÀN BỘ DANG/prompts/s1_chuyen_json.md (hướng dẫn chi tiết + ví dụ), rồi schema DANG/schema/reading_listening.v1.api.json.
- Với từng câu: đọc file_vao (trường yeu_cau), tạo JSON đúng schema (đủ mọi khóa, null khi không có, không có reference_raw), ghi vào file_ra bằng python json.dump(ensure_ascii=False, indent=1). Có thể dùng script hỗ trợ tách khối lựa chọn, nhưng PHẢI tự đọc lại từng câu so với lời giải.
- Sau khi ghi, tự kiểm tra schema từng file: cd DANG/scripts && python3 -c "import json,_dang as D; from pipeline_chung.checks_chung import schema_errors; s=json.load(open(D.P(D.cfg()['schema_api']))); print(schema_errors(json.load(open(D.OUT('json_vi','claude_tao','<id>.json'),encoding='utf-8')), s))" – lỗi thì sửa cấu trúc (không đổi nội dung chép).
- CHỈ mở các file: 2 prompt, schema, danh sách, file_vao và file_ra của các câu trong danh sách. KHÔNG mở/tìm kiếm file nào khác, không chạy script pipeline khác, không sửa nội dung lời giải khuôn chuẩn dù thấy sai.
- Khuôn chuẩn (che_do = chep_nguyen_van): chép NGUYÊN VĂN; trích dẫn tách vào quotes CHỈ khi 「…」 đứng đầu dòng / sau nhãn dẫn thuần (danh sách trong s1_chuyen_json.md), trích dẫn giữa câu Việt giữ trong analysis; bỏ nhãn (Nghĩa:, Trích dẫn:, Giải thích:, Dịch: trong ngoặc, '- ' đầu dòng); is_match theo '→ ĐÚNG/SAI' của lời giải; bọc ⟪ ⟫ mọi tiếng Nhật trong câu Việt; giữ { } và furigana ｜…《…》.
- Khuôn lạ (che_do = tao_moi): chép phần có được (bản dịch đoạn văn → full_translation, dịch câu hỏi / lựa chọn → meaning, giải thích có sẵn → analysis), rồi SOẠN MỚI phần thiếu cho đủ 4 lựa chọn: trích dẫn CHÉP NGUYÊN câu của đoạn văn + bản dịch, giải thích ĐÚNG/SAI dựa vào đoạn văn, is_match theo dap_an_so.

Báo lại ngắn: danh sách id đã ghi + kết quả schema + câu đã tạo mới (id: trường tạo mới) + điểm khó (chỉ mô tả).
