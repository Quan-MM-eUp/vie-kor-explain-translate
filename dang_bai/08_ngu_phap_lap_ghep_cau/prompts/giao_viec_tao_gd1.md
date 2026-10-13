<!-- Mẫu lời giao việc cho TÁC TỬ TẠO – GĐ1. Tác tử KIỂM TRA chép nguyên văn phần dưới vào tham số prompt của Agent
     (subagent_type "general-purpose", model "opus", description "Tác tử TẠO: JSON mẫu X–Y"), thay {{SO_CAU}}.
     {{DANH_SACH}} = tên file danh sách theo lô mà lệnh --chuan-bi in ra ở dòng "[Song song] File danh sách của lô này: …" (vd tao_gd1_danh_sach_X_Y.json; chạy song song 2026-10-13). -->
Bạn là tác tử TẠO (Claude A) của pipeline dạng 08. Làm việc trên máy người dùng bằng công cụ mcp__remote-devices__device_bash (nạp bằng ToolSearch query "select:mcp__remote-devices__device_bash" nếu chưa có). Thư mục dạng bài: $HOME/mnt/Vie-Kor/dang_bai/08_ngu_phap_lap_ghep_cau (gọi là DANG).

Nhiệm vụ: làm đúng theo DANG/prompts/s1_claude_tao.md cho toàn bộ {{SO_CAU}} câu trong DANG/output/claude/{{DANH_SACH}}.
- Đọc kỹ DANG/prompts/s1_claude_tao.md, rồi TOÀN BỘ DANG/prompts/s1_chuyen_json.md (hướng dẫn chi tiết + ví dụ), rồi schema DANG/schema/grammar_ordering.v1.api.json.
- Với từng câu: đọc file_vao (trường yeu_cau), tạo JSON đúng schema (đủ mọi khóa, null khi không có, không có reference_raw), ghi vào file_ra bằng python json.dump(ensure_ascii=False, indent=1). Có thể dùng script hỗ trợ tách nhãn, nhưng PHẢI tự đọc lại từng câu so với lời giải để chắc chắn đúng trường (nhãn lặp, dòng lạ, câu hoàn chỉnh thứ 2, câu chữ sau LỰA CHỌN ĐÚNG…). Không bọc ⟪⟫ quanh dấu '・' đầu dòng.
- Sau khi ghi, tự kiểm tra schema từng file: cd DANG/scripts && python3 -c "import json,_dang as D; from pipeline_chung.checks_chung import schema_errors; s=json.load(open(D.P(D.cfg()['schema_api']))); print(schema_errors(json.load(open(D.OUT('json_vi','claude_tao','<id>.json'),encoding='utf-8')), s))" – lỗi thì sửa cấu trúc (không đổi nội dung chép).
- CHỈ mở các file: 2 prompt, schema, danh sách, file_vao và file_ra của các câu trong danh sách. KHÔNG mở/tìm kiếm file nào khác (kể cả các file khác trong claude_tao), không chạy script pipeline khác, không sửa nội dung lời giải dù thấy sai.
- Chép NGUYÊN VĂN, bọc ⟪ ⟫ mọi tiếng Nhật trong câu tiếng Việt (kể cả kana đơn), giữ { }, ★, ô trống và furigana ｜…《…》 đúng chỗ; gloss = nội dung trong ngoặc của dòng tiêu đề lựa chọn (cách đọc bọc ⟪ ⟫); mỗi ý PHÂN TÍCH ĐỀ BÀI / mỗi dòng cụm sắp xếp là một phần tử; arrangement.order = thu_tu_python_ghep; câu hoàn chỉnh ở arrangement.full_sentence, correct.full_sentence = null; làm theo luu_y của từng câu.

Báo lại ngắn: danh sách id đã ghi + kết quả schema + điểm khó (chỉ mô tả).
