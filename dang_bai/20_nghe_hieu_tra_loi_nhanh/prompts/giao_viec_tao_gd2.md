<!-- Mẫu lời giao việc cho TÁC TỬ TẠO – GĐ2. Tác tử KIỂM TRA chép nguyên văn phần dưới vào tham số prompt của Agent
     (subagent_type "general-purpose", model "opus", description "Tác tử TẠO: dịch Hàn mẫu X–Y"), thay {{SO_CAU}}
     và {{CAU_CO_DINH}} (các dòng của mục "Cách dịch đã thống nhất" trong NHAT_KY.md; chưa có thì bỏ dòng đó). -->
Bạn là tác tử TẠO (Claude A) của pipeline dạng 20 (Nghe hiểu – Trả lời nhanh), bước dịch sang tiếng Hàn. Làm việc trên máy người dùng bằng công cụ mcp__remote-devices__device_bash (nạp bằng ToolSearch query "select:mcp__remote-devices__device_bash" nếu chưa có). Thư mục dạng bài: $HOME/mnt/Vie-Kor/dang_bai/20_nghe_hieu_tra_loi_nhanh (gọi là DANG).

Nhiệm vụ: làm đúng theo DANG/prompts/s2_claude_dich.md cho toàn bộ {{SO_CAU}} câu trong DANG/output/claude/tao_gd2_danh_sach.json.
- Đọc kỹ DANG/prompts/s2_claude_dich.md rồi TOÀN BỘ DANG/output/claude/tao_gd2/_he_thong.md (hướng dẫn dịch + bảng thuật ngữ).
- Với từng câu: đọc file_vao ("user" = ngữ cảnh đề nghe + JSON lời giải có mã fN; "ids" = các mã cần dịch). Tự dịch từng mã (bạn là người dịch – KHÔNG dùng script tự động để dịch). Ghi file_ra = một object {"fN": "bản dịch tiếng Hàn"} gồm ĐÚNG và ĐỦ các mã trong ids, bằng python json.dump(ensure_ascii=False, indent=1) (nội dung qua python heredoc có trích dẫn 'EOF').
- Lời thoại (mã có dich_tu_tieng_nhat): dịch thẳng từ nguon.cau_tieng_nhat như lời nói tự nhiên, GIỮ MỨC LỊCH SỰ của câu Nhật (thể thường/ため口 → 반말; です・ます → 해요체; kính ngữ/khiêm nhường → 존댓말/하십시오체); câu trả lời sai vẫn dịch đúng như câu Nhật; không thêm { }.
- Phân tích (mã có vi): dịch đúng đủ ý bản Việt, văn phong -습니다; mỗi khối ⟪…⟫ của bản Việt có mặt nguyên vẹn (kể cả furigana ｜…《…》); trợ từ sau ⟫ — KỂ CẢ khi giữa ⟫ và trợ từ có dấu nháy/ngoặc — theo âm cuối cách đọc tiếng Nhật của khối đó (ん → 은/이/을/과/이라는/이며/으로; mọi kana khác → 는/가/를/와/라는/며/로); câu trích lại nghĩa lời thoại dịch khớp với bản dịch lời thoại; giữ loại dấu nháy, \n.
- Kiểm tra lại sau khi ghi: số khóa = số ids.
- Câu cố định / cách dịch đã thống nhất: {{CAU_CO_DINH}}
- CHỈ mở: prompt, _he_thong.md, danh sách, file_vao/file_ra của các câu trong danh sách. Không mở file nào khác, không chạy script pipeline.

Báo lại ngắn: các id đã ghi + số mã mỗi câu + điểm khó (chỉ mô tả).
