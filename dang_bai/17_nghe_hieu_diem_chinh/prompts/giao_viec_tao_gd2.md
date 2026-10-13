<!-- Mẫu lời giao việc cho TÁC TỬ TẠO – GĐ2. Tác tử KIỂM TRA chép nguyên văn phần dưới vào tham số prompt của Agent
     (subagent_type "general-purpose", model "opus", description "Tác tử TẠO: dịch Hàn mẫu X–Y"), thay {{SO_CAU}} và {{CAU_CO_DINH}} (= các dòng mục "Cách dịch đã thống nhất" trong NHAT_KY.md; chưa có thì ghi "(chưa có)"). -->
Bạn là tác tử TẠO (Claude A) của pipeline dạng 17 (Nghe hiểu điểm chính), bước dịch sang tiếng Hàn. Làm việc trên máy người dùng bằng công cụ mcp__remote-devices__device_bash (nạp bằng ToolSearch query "select:mcp__remote-devices__device_bash" nếu chưa có). Thư mục dạng bài: $HOME/mnt/Vie-Kor/dang_bai/17_nghe_hieu_diem_chinh (gọi là DANG).

Nhiệm vụ: làm đúng theo DANG/prompts/s2_claude_dich.md cho toàn bộ {{SO_CAU}} câu trong DANG/output/claude/tao_gd2_danh_sach.json.
- Đọc kỹ DANG/prompts/s2_claude_dich.md rồi TOÀN BỘ DANG/output/claude/tao_gd2/_he_thong.md.
- Với từng câu: đọc file_vao; tự dịch từng mã (bạn là người dịch – KHÔNG dùng script để dịch); ghi file_ra = {"fN": "…"} gồm đúng các mã trong ids TRỪ các mã trong sao_chep, bằng python json.dump(ensure_ascii=False, indent=1).
- Kiểm lại sau khi ghi: số khóa = len(ids) − len(sao_chep); câu Nhật có (i) thì bản Hàn có (i) đúng chỗ; mọi chữ số của câu Nhật có trong bản Hàn; lời thoại giữ mức kính ngữ / thân mật của câu Nhật (です/ます → 존댓말, thể thường → 반말); câu hỏi -ㅂ니까; lý do -습니다, giữ ⟪ ⟫ và trợ từ sau ⟫ theo âm cuối cách đọc tiếng Nhật; cùng câu Nhật lặp lại dịch giống hệt; tên người phiên âm Hàn theo cách đọc Nhật; không còn chữ Nhật / chữ Việt trong bản Hàn (trừ khối ⟪ ⟫).
- Câu cố định / cách dịch đã thống nhất (dùng đúng nguyên văn nếu gặp): {{CAU_CO_DINH}}
- CHỈ mở: prompt, _he_thong.md, danh sách, file_vao/file_ra của các câu trong danh sách. Không mở file khác, không chạy script pipeline.

Báo lại ngắn: các id đã ghi + số mã mỗi câu + điểm khó (chỉ mô tả).
