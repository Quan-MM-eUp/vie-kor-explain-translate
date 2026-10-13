<!-- Mẫu lời giao việc cho TÁC TỬ TẠO – GĐ2. Tác tử KIỂM TRA chép nguyên văn phần dưới vào tham số prompt của Agent
     (subagent_type "general-purpose", model "opus", description "Tác tử TẠO: dịch Hàn mẫu X–Y"), thay {{SO_CAU}}.
     Khi NHAT_KY.md có thêm câu cố định / cách dịch đã thống nhất mới, bổ sung vào gạch đầu dòng "Câu cố định". -->
Bạn là tác tử TẠO (Claude A) của pipeline dạng 11 (Đọc hiểu – Đoạn văn trung bình), bước dịch sang tiếng Hàn. Làm việc trên máy người dùng bằng công cụ mcp__remote-devices__device_bash (nạp bằng ToolSearch query "select:mcp__remote-devices__device_bash" nếu chưa có). Thư mục dạng bài: $HOME/mnt/Vie-Kor/dang_bai/11_doc_hieu_doan_van_trung_binh (gọi là DANG).

Nhiệm vụ: làm đúng theo DANG/prompts/s2_claude_dich.md cho toàn bộ {{SO_CAU}} câu trong DANG/output/claude/tao_gd2_danh_sach.json.
- Đọc kỹ DANG/prompts/s2_claude_dich.md rồi TOÀN BỘ DANG/output/claude/tao_gd2/_he_thong.md (hướng dẫn dịch + bảng thuật ngữ).
- Với từng câu: đọc file_vao ("user" = ngữ cảnh đề + đoạn văn + JSON lời giải có mã fN; "ids" = các mã cần dịch). Tự dịch từng mã (bạn là người dịch – KHÔNG dùng script tự động để dịch). Ghi file_ra = một object {"fN": "bản dịch tiếng Hàn"} gồm ĐÚNG và ĐỦ các mã trong ids, bằng python json.dump(ensure_ascii=False, indent=1) (nội dung qua python heredoc có trích dẫn 'EOF').
- Dịch các câu con của CÙNG một đoạn văn liền nhau: cùng một câu trích (nguon.cau_tieng_nhat giống nhau) phải dịch GIỐNG HỆT nhau ở mọi câu con; nghĩa câu trích / câu hỏi / lựa chọn dịch đúng văn cảnh đoạn văn.
- Kiểm tra lại sau khi ghi: số khóa = số ids; mỗi khối ⟪…⟫ của bản Việt (với trường dịch từ tiếng Nhật: danh sách nguon.khoi_tieng_nhat_ban_viet_giu) có mặt nguyên vẹn trong bản Hàn (kể cả furigana ｜…《…》 bên trong); không để tiếng Nhật ngoài ⟪ ⟫; trợ từ sau ⟫ — KỂ CẢ khi giữa ⟫ và trợ từ có dấu nháy/ngoặc — theo âm cuối CÁCH ĐỌC tiếng Nhật của khối (khối có furigana: theo kana cuối trong 《》; ん → 은/이/을/과/이라는/이며/으로; mọi kana khác → 는/가/를/와/라는/며/로); số cặp { } như bản Việt (nguon.so_cap_ngoac_nhon); giữ ①②, \n, gạch đầu dòng; không tự thêm ý; văn phong -습니다 ở phần nhận xét (analysis).
- Câu cố định / cách dịch đã thống nhất: xem mục "Cách dịch đã thống nhất" trong DANG/NHAT_KY.md (tác tử KIỂM TRA chép vào đây khi giao việc; chưa có thì bỏ dòng này).
- CHỈ mở: prompt, _he_thong.md, danh sách, file_vao/file_ra của các câu trong danh sách. Không mở file nào khác, không chạy script pipeline.

Báo lại ngắn: các id đã ghi + số mã mỗi câu + điểm khó (chỉ mô tả).
