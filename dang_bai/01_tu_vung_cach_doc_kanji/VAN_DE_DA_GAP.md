# Các vấn đề gặp phải – Dịch lời giải "Cách đọc kanji" từ tiếng Việt sang tiếng Hàn

```
Dịch lời giải "Cách đọc kanji" (Việt → Hàn)
│
├── 1. Lời giải tiếng Việt gốc có lỗi   ← nguyên nhân chính
│   ├── Lỗi trình bày: dính câu, số thứ tự lẫn vào cách đọc, chính tả
│   │      → Claude sửa và ghi chú từng chỗ
│   ├── Lỗi nội dung: sai thì của câu, sai tự/tha động từ, sai nghĩa từ
│   │      → Gắn cờ, không dịch, chờ CTV tiếng Nhật xác nhận
│   ├── Có âm Hán Việt (63/1.872 câu) – người Hàn không dùng được
│   │      → Chưa dịch, chờ quyết định cách xử lý
│   └── Dữ liệu không khớp: lệch đáp án, thiếu lời giải
│          → Lấy đáp án trong dữ liệu làm chuẩn, đánh dấu để kiểm tra
│
├── 2. Chuyển lời giải sang định dạng chuẩn (GPT)
│   └── Ít lỗi (3/117 câu), Claude sửa được
│
├── 3. Dịch sang tiếng Hàn (GPT)
│   ├── Cùng một câu đề nhưng dịch không thống nhất giữa các câu
│   │      → Claude thống nhất lại, dùng bộ nhớ dịch
│   ├── Từ đúng nhưng sai ngữ cảnh (vd 兄/姉: tiếng Hàn phân biệt người nói nam/nữ)
│   │      → Bổ sung vào bảng thuật ngữ
│   └── Người Hàn cần thêm âm Hán-Hàn (한자음) để dễ nhớ (CTV gợi ý 35/50 câu)
│          → Chờ quyết định có bổ sung hay không
│
├── 4. Kiểm duyệt với cộng tác viên
│   ├── Lỗi tiếng Việt gốc lan sang bản tiếng Hàn → nguyên nhân của 7/50 câu không đạt
│   │      → Đổi cách phân loại: lỗi nội dung bị chặn trước khi dịch
│   ├── Phần Claude sửa tiếng Việt cần người biết tiếng Nhật kiểm tra
│   │      → Tạo file riêng cho CTV tiếng Nhật
│   └── Thiếu mẫu ở cấp độ N3–N5 → chọn mẫu cân bằng 10 câu mỗi cấp độ
│
└── 5. Công cụ và vận hành
    ├── Kiểm tra tự động báo lỗi nhầm → đã chỉnh
    ├── File Excel hiển thị chữ Hàn như in đậm (lỗi font) → đã chỉnh
    ├── API key hết hạn giữa chừng → chạy lại tiếp được, không mất kết quả
    └── Chạy lại có thể làm lại mẫu đã duyệt → lưu mẫu đã duyệt vào kho riêng
```

**Kết quả hiện tại:** CTV tiếng Hàn chấp nhận 49 mẫu (đã lưu vào kho riêng). Trong file 50 câu: 41 đạt, 2 sửa nhỏ, 7 không đạt.

**Cần quyết định:** cách xử lý âm Hán Việt, và có bổ sung âm Hán-Hàn (한자음) cho người Hàn hay không.
