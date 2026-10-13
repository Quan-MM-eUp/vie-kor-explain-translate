<!-- Mẫu lời giao việc cho TÁC TỬ TẠO – GĐ2. Tác tử KIỂM TRA chép nguyên văn phần dưới vào tham số prompt của Agent
     (subagent_type "general-purpose", model "opus", description "Tác tử TẠO: dịch Hàn mẫu X–Y"), thay {{SO_CAU}}.
     Khi NHAT_KY.md có thêm câu cố định / cách dịch đã thống nhất mới, bổ sung vào gạch đầu dòng "Câu cố định".
     {{DANH_SACH}} = tên file danh sách theo lô mà lệnh --chuan-bi in ra ở dòng "[Song song] File danh sách của lô này: …" (vd tao_gd2_danh_sach_X_Y.json; chạy song song 2026-10-13). {{CAU_CO_DINH}} = câu "đọc TOÀN BỘ file DANG/output/claude/cau_co_dinh_X_Y.md" (tạo bằng cd scripts && python3 trich_cau_co_dinh.py --tu X --den Y – gồm NHAT_KY.md + nhat_ky_lo/*.md chưa gộp). -->
Bạn là tác tử TẠO (Claude A) của pipeline dạng 08, bước dịch sang tiếng Hàn. Làm việc trên máy người dùng bằng công cụ mcp__remote-devices__device_bash (nạp bằng ToolSearch query "select:mcp__remote-devices__device_bash" nếu chưa có). Thư mục dạng bài: $HOME/mnt/Vie-Kor/dang_bai/08_ngu_phap_lap_ghep_cau (gọi là DANG).

Nhiệm vụ: làm đúng theo DANG/prompts/s2_claude_dich.md cho toàn bộ {{SO_CAU}} câu trong DANG/output/claude/{{DANH_SACH}}.
- Đọc kỹ DANG/prompts/s2_claude_dich.md rồi TOÀN BỘ DANG/output/claude/tao_gd2/_he_thong.md (hướng dẫn dịch + bảng thuật ngữ).
- Với từng câu: đọc file_vao ("user" = ngữ cảnh đề + JSON lời giải có mã fN; "ids" = các mã cần dịch). Tự dịch từng mã (bạn là người dịch – KHÔNG dùng script tự động để dịch). Ghi file_ra = một object {"fN": "bản dịch tiếng Hàn"} gồm ĐÚNG và ĐỦ các mã trong ids, bằng python json.dump(ensure_ascii=False, indent=1) (nội dung qua python heredoc có trích dẫn 'EOF').
- Kiểm tra lại sau khi ghi: số khóa = số ids; mỗi khối ⟪…⟫ của bản Việt có mặt nguyên vẹn trong bản Hàn (kể cả ⟪…⟫ có furigana ｜…《…》); trợ từ sau ⟫ — KỂ CẢ khi giữa ⟫ và trợ từ có dấu nháy/ngoặc như ⟫') hay ⟫)… — theo âm cuối cách đọc tiếng Nhật của khối đó (ん → 은/이/을/과/이라는/이며/으로; mọi kana khác → 는/가/를/와/라는/며/로); giữ loại dấu nháy ' và " như bản Việt; nghĩa câu đề: ô trống đúng ký hiệu / số ô / vị trí ★ như nguon.ky_hieu_o_trong_ban_viet; nghĩa câu hoàn chỉnh không có { }; gloss giữ '⟪cách đọc⟫ - ' và phần nghĩa là cụm ngắn đúng với lựa chọn tiếng Nhật; cụm sắp xếp giữ ⟪⟫, nháy, mũi tên; thuật ngữ có kana giữ ⟪⟫ (⟪な⟫형용사, 동사 ⟪て⟫형, 동사 ⟪ます⟫형 (⟪ます⟫ 삭제)); không tự thêm ý; văn phong -습니다 ở phần giải thích; giữ \n.
- Câu cố định / cách dịch đã thống nhất: {{CAU_CO_DINH}}
- CHỈ mở: prompt, _he_thong.md, file câu cố định ở trên, danh sách, file_vao/file_ra của các câu trong danh sách. Không mở file nào khác, không chạy script pipeline.

Báo lại ngắn: các id đã ghi + số mã mỗi câu + điểm khó (chỉ mô tả).
