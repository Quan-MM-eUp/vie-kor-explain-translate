<!-- Mẫu lời giao việc cho TÁC TỬ TẠO – GĐ1. Tác tử KIỂM TRA chép nguyên văn phần dưới vào tham số prompt của Agent
     (subagent_type "general-purpose", model "opus", description "Tác tử TẠO: JSON mẫu X–Y"), thay {{SO_CAU}}. -->
Bạn là tác tử TẠO (Claude A) của pipeline dạng 17 (Nghe hiểu điểm chính). Làm việc trên máy người dùng bằng công cụ mcp__remote-devices__device_bash (nạp bằng ToolSearch query "select:mcp__remote-devices__device_bash" nếu chưa có). Thư mục dạng bài: $HOME/mnt/Vie-Kor/dang_bai/17_nghe_hieu_diem_chinh (gọi là DANG).

Nhiệm vụ: làm đúng theo DANG/prompts/s1_claude_tao.md cho toàn bộ {{SO_CAU}} câu trong DANG/output/claude/tao_gd1_danh_sach.json.
- Đọc kỹ DANG/prompts/s1_claude_tao.md, rồi TOÀN BỘ DANG/prompts/s1_chuyen_json.md, rồi schema DANG/schema/reading_listening.v1.api.json.
- Với từng câu: đọc file_vao (trường yeu_cau). Lấy khung_json làm gốc, đối chiếu TỪNG cặp lượt Nhật (J…) ↔ dòng Việt (V…), sửa chỗ ghép lệch / điền chỗ null bằng python (gán theo chỉ số, không gõ lại tiếng Nhật), ghi file_ra bằng json.dump(ensure_ascii=False, indent=1).
- Tự kiểm sau khi ghi (sửa đến khi rỗng): cd DANG/scripts && python3 -c "import json,_dang as D; from pipeline_chung.checks_chung import schema_errors; n=D.load_norm('<id>'); d=json.load(open(D.OUT('json_vi','claude_tao','<id>.json'),encoding='utf-8')); print(schema_errors(d, json.load(open(D.P(D.cfg()['schema_api'])))), [e for e in D.check_k(D.bo_sung(d,n), n)[0]])" – lệnh này chỉ báo lỗi cấu trúc / K-LT / K-NG / K-DV / K-LC / K-DA; sửa cấu trúc và ghép cặp, KHÔNG đổi nội dung chép.
- CHỈ mở các file: 2 prompt, schema, danh sách, file_vao và file_ra của các câu trong danh sách. KHÔNG mở/tìm kiếm file nào khác, không chạy script pipeline khác, không sửa nội dung lời giải dù thấy sai.
- Nhớ: ja chép nguyên lượt thoại (không nhãn, giữ (i)); meaning.vi bỏ nhãn người nói tiếng Việt; key_info bỏ (i); khuôn B: analysis của lựa chọn đúng = nguyên văn phần sau ###; tiếng Nhật trong câu Việt bọc ⟪ ⟫.

Báo lại ngắn: danh sách id đã ghi + kết quả tự kiểm + điểm khó (chỉ mô tả).
