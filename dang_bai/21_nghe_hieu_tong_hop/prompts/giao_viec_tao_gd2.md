<!-- Mẫu lời giao việc cho TÁC TỬ TẠO – GĐ2. Tác tử KIỂM TRA chép nguyên văn phần dưới vào tham số prompt của Agent
     (subagent_type "general-purpose", model "opus", description "Tác tử TẠO: dịch Hàn mẫu X–Y"), thay {{SO_CAU}} và {{CAU_CO_DINH}} (= các dòng mục "Cách dịch đã thống nhất" trong NHAT_KY.md; chưa có thì ghi "(chưa có)"). -->
Bạn là tác tử TẠO (Claude A) của pipeline dạng 21 (Nghe hiểu tổng hợp), bước dịch sang tiếng Hàn. Làm việc trên máy người dùng bằng công cụ mcp__remote-devices__device_bash (nạp bằng ToolSearch query "select:mcp__remote-devices__device_bash" nếu chưa có). Thư mục dạng bài: $HOME/mnt/Vie-Kor/dang_bai/21_nghe_hieu_tong_hop (gọi là DANG).

Nhiệm vụ: làm đúng theo DANG/prompts/s2_claude_dich.md cho toàn bộ {{SO_CAU}} câu trong DANG/output/claude/tao_gd2_danh_sach.json.
- Đọc kỹ DANG/prompts/s2_claude_dich.md rồi TOÀN BỘ DANG/output/claude/tao_gd2/_he_thong.md.
- Với từng câu: đọc file_vao ("user" = ngữ cảnh + JSON lời giải có mã fN; "ids" = các mã cần dịch). Tự dịch từng mã (KHÔNG dùng script để dịch). Ghi file_ra = một object {"fN": "bản dịch tiếng Hàn"} gồm ĐÚNG và ĐỦ các mã trong ids, bằng python json.dump(ensure_ascii=False, indent=1) (nội dung qua heredoc 'EOF').
- Kiểm tra lại sau khi ghi: số khóa = số ids; lượt thoại là văn nói đúng mức lịch sự của câu Nhật, giữ (i)/(ii), không thêm nhãn người nói; câu trích / câu then chốt trùng lượt thoại dịch GIỐNG HỆT lượt thoại; nhận xét (-습니다) giữ nguyên mọi khối ⟪…⟫ (kể cả furigana ｜…《…》), trợ từ sau ⟫ theo âm cuối cách đọc tiếng Nhật (ん → 은/이/을/과/이라는/이며/으로; kana khác → 는/가/를/와/라는/며/로); giữ \n, dấu nháy như bản Việt; không tự thêm ý.
- Câu cố định / cách dịch đã thống nhất (dùng đúng nguyên văn nếu gặp): {{CAU_CO_DINH}}
- CHỈ mở: prompt, _he_thong.md, danh sách, file_vao/file_ra của các câu trong danh sách. Không mở file nào khác, không chạy script pipeline.

Báo lại ngắn: các id đã ghi + số mã mỗi câu + điểm khó (chỉ mô tả).
