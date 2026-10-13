<!-- Mẫu lời giao việc cho TÁC TỬ TẠO – GĐ1. Tác tử KIỂM TRA chép nguyên văn phần dưới vào tham số prompt của Agent
     (subagent_type "general-purpose", model "opus", description "Tác tử TẠO: JSON mẫu X–Y"), thay {{SO_CAU}}. -->
Bạn là tác tử TẠO (Claude A) của pipeline dạng 16 (Nghe hiểu chủ đề). Làm việc trên máy người dùng bằng công cụ mcp__remote-devices__device_bash (nạp bằng ToolSearch query "select:mcp__remote-devices__device_bash" nếu chưa có). Thư mục dạng bài: $HOME/mnt/Vie-Kor/dang_bai/16_nghe_hieu_chu_de (gọi là DANG).

Nhiệm vụ: làm đúng theo DANG/prompts/s1_claude_tao.md cho toàn bộ {{SO_CAU}} câu trong DANG/output/claude/tao_gd1_danh_sach.json.
- Đọc kỹ DANG/prompts/s1_claude_tao.md, rồi TOÀN BỘ DANG/prompts/s1_chuyen_json.md (hướng dẫn chi tiết + ví dụ), rồi schema DANG/schema/reading_listening.v1.api.json.
- Với từng câu: đọc file_vao (trường yeu_cau), tạo JSON đúng schema (đủ khóa bắt buộc, null khi không có, KHÔNG có key_info / reference_raw; full_translation CHỈ khi can_ghi_full_translation = true), ghi vào file_ra bằng python json.dump(ensure_ascii=False, indent=1). Dùng goi_y_tach_khoi làm khung nhưng PHẢI tự đối chiếu từng khối với loi_giai_phan_tich (câu trích nào tách ra quotes, câu nào giữ trong analysis, nhận xét sau '→ ĐÚNG/SAI', is_match theo kết luận của khối).
- Sau khi ghi, tự kiểm tra schema từng file: cd DANG/scripts && python3 -c "import json,_dang as D; from pipeline_chung.checks_chung import schema_errors; s=json.load(open(D.P(D.cfg()['schema_api']))); print(schema_errors(json.load(open(D.OUT('json_vi','claude_tao','<id>.json'),encoding='utf-8')), s))" – lỗi thì sửa cấu trúc (không đổi nội dung chép).
- CHỈ mở các file: 2 prompt, schema, danh sách, file_vao và file_ra của các câu trong danh sách. KHÔNG mở/tìm kiếm file nào khác (kể cả các file khác trong claude_tao), không chạy script pipeline khác, không sửa nội dung lời giải dù thấy sai.
- Chép NGUYÊN VĂN; option_ja = đúng lựa chọn của đề (tranh: "1"…"4", meaning = null); bọc ⟪ ⟫ mọi tiếng Nhật trong câu tiếng Việt (kể cả câu trích giữa câu, kana đơn); giữ { }, (i) và furigana ｜…《…》 đúng chỗ; bỏ phần dẫn của câu trích tách được; correct.index = dap_an_so, full_sentence = null.

Báo lại ngắn: danh sách id đã ghi + kết quả schema + điểm khó (chỉ mô tả).
