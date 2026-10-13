<!-- Mẫu lời giao việc cho TÁC TỬ TẠO – GĐ2. Tác tử KIỂM TRA chép nguyên văn phần dưới vào tham số prompt của Agent
     (subagent_type "general-purpose", model "opus", description "Tác tử TẠO: dịch Hàn mẫu X–Y"), thay {{SO_CAU}} và {{CAU_CO_DINH}} (= các dòng mục "Cách dịch đã thống nhất" trong NHAT_KY.md; chưa có thì ghi "(chưa có)"). -->
Bạn là tác tử TẠO (Claude A) của pipeline dạng 19 (Nghe hiểu diễn đạt), bước dịch sang tiếng Hàn. Làm việc trên máy người dùng bằng công cụ mcp__remote-devices__device_bash (nạp bằng ToolSearch query "select:mcp__remote-devices__device_bash" nếu chưa có). Thư mục dạng bài: $HOME/mnt/Vie-Kor/dang_bai/19_nghe_hieu_dien_dat (gọi là DANG).

Nhiệm vụ: làm đúng theo DANG/prompts/s2_claude_dich.md cho toàn bộ {{SO_CAU}} câu trong DANG/output/claude/tao_gd2_danh_sach.json.
- Đọc kỹ DANG/prompts/s2_claude_dich.md rồi TOÀN BỘ DANG/output/claude/tao_gd2/_he_thong.md (hướng dẫn dịch + thuật ngữ + câu nói cố định).
- Với từng câu: đọc file_vao ("user" = ngữ cảnh đề + JSON lời giải có mã fN; "ids" = các mã cần dịch). Tự dịch từng mã (bạn là người dịch – KHÔNG dùng script tự động để dịch). Ghi file_ra = một object {"fN": "bản dịch tiếng Hàn"} gồm ĐÚNG và ĐỦ các mã trong ids, bằng python json.dump(ensure_ascii=False, indent=1) (nội dung qua python heredoc có trích dẫn 'EOF').
- Kiểm tra lại sau khi ghi: số khóa = số ids; mỗi khối ⟪…⟫ của bản Việt có mặt nguyên vẹn trong bản Hàn; trợ từ sau ⟫ (kể cả ⟫」 / ⟫') theo âm cuối cách đọc tiếng Nhật (ん → 은/이/을/과/이라는/이며/으로; kana khác → 는/가/를/와/라는/며/로); câu nói dịch đúng mức lịch sự + ai làm cho ai như câu Nhật, lời chào cố định dùng câu tương đương tiếng Hàn, câu nói SAI vẫn dịch đúng như câu đang viết; '何と言いますか' → '뭐라고 말합니까?'; cùng câu Nhật → cùng bản Hàn; nghĩa câu nói trích lại trong phân tích khớp bản dịch câu nói; văn phong -습니다 ở phân tích; không tự thêm ý; giữ \n, 「」, { }.
- Câu cố định / cách dịch đã thống nhất (dùng đúng nguyên văn nếu gặp): {{CAU_CO_DINH}}
- CHỈ mở: prompt, _he_thong.md, danh sách, file_vao/file_ra của các câu trong danh sách. Không mở file nào khác, không chạy script pipeline.

Báo lại ngắn: các id đã ghi + số mã mỗi câu + điểm khó (chỉ mô tả).
