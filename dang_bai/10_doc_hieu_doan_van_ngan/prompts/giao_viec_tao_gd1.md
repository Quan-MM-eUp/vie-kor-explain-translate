<!-- Mẫu lời giao việc cho TÁC TỬ TẠO – GĐ1. Tác tử KIỂM TRA chép nguyên văn phần dưới vào tham số prompt của Agent
     (subagent_type "general-purpose", model "opus", description "Tác tử TẠO: JSON mẫu X–Y"), thay {{SO_CAU}}. -->
Bạn là tác tử TẠO (Claude A) của pipeline dạng 10 (Đọc hiểu – Đoạn văn ngắn). Làm việc trên máy người dùng bằng công cụ mcp__remote-devices__device_bash (nạp bằng ToolSearch query "select:mcp__remote-devices__device_bash" nếu chưa có). Thư mục dạng bài: $HOME/mnt/Vie-Kor/dang_bai/10_doc_hieu_doan_van_ngan (gọi là DANG).

Nhiệm vụ: làm đúng theo DANG/prompts/s1_claude_tao.md cho toàn bộ {{SO_CAU}} câu trong DANG/output/claude/tao_gd1_danh_sach.json.
- Đọc kỹ DANG/prompts/s1_claude_tao.md, rồi TOÀN BỘ DANG/prompts/s1_chuyen_json.md (hướng dẫn chi tiết + 2 ví dụ), rồi schema DANG/schema/reading_listening.v1.api.json.
- Với từng câu: đọc file_vao (trường yeu_cau), lấy khung_python làm khung NHƯNG đối chiếu lại với loi_giai_goc, tạo JSON đúng schema (đủ mọi khóa, null khi không có, không có reference_raw), ghi vào file_ra bằng python json.dump(ensure_ascii=False, indent=1). Được dùng script để dựng từ khung và bọc ⟪ ⟫, nhưng PHẢI tự đọc lại từng lựa chọn so với lời giải (trích dẫn đứng riêng dòng → quotes, trích dẫn trong câu → analysis, nhãn bỏ, câu dẫn giữ, kana đơn / katakana / chữ Hán có furigana trong câu Việt đều bọc ⟪ ⟫, dấu 「」 và nháy để ngoài ⟪ ⟫).
- Sau khi ghi, tự kiểm tra schema từng file: cd DANG/scripts && python3 -c "import json,_dang as D; from pipeline_chung.checks_chung import schema_errors; s=json.load(open(D.P(D.cfg()['schema_api']))); print(schema_errors(json.load(open(D.OUT('json_vi','claude_tao','<id>.json'),encoding='utf-8')), s))" – lỗi thì sửa cấu trúc (không đổi nội dung chép).
- CHỈ mở các file: 2 prompt, schema, danh sách, file_vao và file_ra của các câu trong danh sách. KHÔNG mở/tìm kiếm file nào khác (kể cả các file khác trong claude_tao), không chạy script pipeline khác, không sửa nội dung lời giải dù thấy sai (kể cả chữ Hán chen giữa câu Việt – chép nguyên).
- is_match / correct theo dap_an_so của ĐỀ; khuôn B: full_translation từ 'Đoạn văn:', question.ja / option_ja theo khung (câu của đề), không chép dòng 'Câu trả lời đúng là'; làm theo luu_y của từng câu.

Báo lại ngắn: danh sách id đã ghi + kết quả schema + điểm khó (chỉ mô tả).
