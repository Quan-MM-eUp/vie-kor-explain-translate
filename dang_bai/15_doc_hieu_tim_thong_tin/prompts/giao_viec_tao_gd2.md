<!-- Mẫu lời giao việc cho TÁC TỬ TẠO – GĐ2. Tác tử KIỂM TRA chép nguyên văn phần dưới vào tham số prompt của Agent
     (subagent_type "general-purpose", model "opus", description "Tác tử TẠO: dịch Hàn mẫu X–Y"), thay {{SO_CAU}} và {{CAU_CO_DINH}} (= các dòng mục "Cách dịch đã thống nhất" trong NHAT_KY.md; chưa có thì bỏ cả gạch đầu dòng đó). -->
Bạn là tác tử TẠO (Claude A) của pipeline dạng 15 (Đọc hiểu – Tìm thông tin), bước dịch sang tiếng Hàn. Làm việc trên máy người dùng bằng công cụ mcp__remote-devices__device_bash (nạp bằng ToolSearch query "select:mcp__remote-devices__device_bash" nếu chưa có). Thư mục dạng bài: $HOME/mnt/Vie-Kor/dang_bai/15_doc_hieu_tim_thong_tin (gọi là DANG).

Nhiệm vụ: làm đúng theo DANG/prompts/s2_claude_dich.md cho toàn bộ {{SO_CAU}} câu trong DANG/output/claude/tao_gd2_danh_sach.json.
- Đọc kỹ DANG/prompts/s2_claude_dich.md rồi TOÀN BỘ DANG/output/claude/tao_gd2/_he_thong.md (hướng dẫn dịch + bảng thuật ngữ).
- Với từng câu: đọc file_vao ("user" = ngữ cảnh đề + JSON lời giải có mã fN; "ids" = các mã cần dịch). Tự dịch từng mã (bạn là người dịch – KHÔNG dùng script tự động để dịch). Ghi file_ra = một object {"fN": "bản dịch tiếng Hàn"} gồm ĐÚNG và ĐỦ các mã trong ids, bằng python json.dump(ensure_ascii=False, indent=1) (nội dung qua python heredoc có trích dẫn 'EOF').
- Kiểm tra lại sau khi ghi: số khóa = số ids; mã có dich_tu_tieng_nhat dịch từ cau_tieng_nhat (bản Việt chỉ tham khảo); MỌI con số / giờ / ngày / giá / phép tính giữ đúng như bản nguồn (đơn vị: 엔, 월/일, 시/분); mỗi khối ⟪…⟫ của bản Việt có mặt nguyên vẹn trong bản Hàn (kể cả furigana ｜…《…》 bên trong); trợ từ sau ⟫ (kể cả sau ⟫' hay ⟫)) theo âm cuối cách đọc tiếng Nhật của khối đó (ん → 은/이/을/과/이라는/이며/으로; kana khác → 는/가/를/와/라는/며/로); ngữ liệu KHÔNG dịch; câu trích giống nhau dịch giống hệt nhau giữa các lựa chọn / câu con; không tự thêm ý, không sửa phép tính / kết luận; văn phong -습니다 ở phần phân tích; giữ \n, gạch đầu dòng.
- Câu cố định / cách dịch đã thống nhất (dùng đúng nguyên văn nếu gặp): {{CAU_CO_DINH}}
- CHỈ mở: prompt, _he_thong.md, danh sách, file_vao/file_ra của các câu trong danh sách. Không mở file nào khác, không chạy script pipeline.

Báo lại ngắn: các id đã ghi + số mã mỗi câu + điểm khó (chỉ mô tả).
