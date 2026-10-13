<!-- Mẫu lời giao việc cho TÁC TỬ TẠO – GĐ2. Tác tử KIỂM TRA chép nguyên văn phần dưới vào tham số prompt của Agent
     (subagent_type "general-purpose", model "opus", description "Tác tử TẠO: dịch Hàn dạng 12 mẫu X–Y"), thay {{SO_CAU}}.
     Khi NHAT_KY.md có cách dịch đã thống nhất mới, chép vào dòng "Câu cố định"; chưa có thì bỏ dòng đó. -->
Bạn là tác tử TẠO (Claude A) của pipeline dạng 12 (Đọc hiểu – Đoạn văn dài), bước dịch sang tiếng Hàn. Làm việc trên máy người dùng bằng công cụ mcp__remote-devices__device_bash (nạp bằng ToolSearch query "select:mcp__remote-devices__device_bash" nếu chưa có). Thư mục dạng bài: $HOME/mnt/Vie-Kor/dang_bai/12_doc_hieu_doan_van_dai (gọi là DANG). Mỗi lệnh là một shell mới – luôn `cd` vào DANG trước.

Nhiệm vụ: làm đúng theo DANG/prompts/s2_claude_dich.md cho toàn bộ {{SO_CAU}} câu trong DANG/output/claude/tao_gd2_danh_sach.json.
- Đọc kỹ DANG/prompts/s2_claude_dich.md rồi TOÀN BỘ DANG/output/claude/tao_gd2/_he_thong.md (hướng dẫn dịch + bảng thuật ngữ).
- Với từng câu: đọc file_vao ("user" = ngữ cảnh đề + JSON lời giải có mã fN; "ids" = các mã cần dịch). Tự dịch từng mã (bạn là người dịch – KHÔNG dùng script tự động để dịch). Ghi file_ra = một object {"fN": "bản dịch tiếng Hàn"} gồm ĐÚNG và ĐỦ các mã trong ids, bằng python json.dump(ensure_ascii=False, indent=1) (nội dung qua python heredoc có trích dẫn 'EOF').
- Nghĩa câu hỏi / nghĩa lựa chọn / nghĩa câu trích (dich_tu_tieng_nhat): dịch TRỰC TIẾP, sát câu tiếng Nhật; cùng một câu trích trong các câu của cùng đoạn văn → dịch giống hệt (lập bảng câu trích → bản dịch dùng chung cho cả lô).
- analysis (dịch từ tiếng Việt): mỗi khối ⟪…⟫ của bản Việt có mặt nguyên vẹn trong bản Hàn (kể cả ⟪…⟫ có furigana ｜…《…》); trợ từ sau ⟫ — KỂ CẢ khi giữa ⟫ và trợ từ có dấu nháy/ngoặc như ⟫") hay ⟫」 — theo âm cuối cách đọc tiếng Nhật của khối đó (ん → 은/이/을/과/이라는/이며/으로; mọi kana khác → 는/가/를/와/라는/며/로); giữ loại dấu nháy, \n, '- ' như bản Việt; 'đoạn văn' → 본문, 'tác giả' → 필자; không tự thêm ý; văn phong -습니다.
- Câu cố định đã thống nhất (dùng đúng nguyên văn nếu gặp): {{CAU_CO_DINH}}
- CHỈ mở: prompt, _he_thong.md, danh sách, file_vao/file_ra của các câu trong danh sách. Không mở file nào khác, không chạy script pipeline.

Báo lại ngắn: các id đã ghi + số mã mỗi câu + điểm khó (chỉ mô tả).
