# Cách chia dạng mới – Dạng bài "Cách đọc Kanji" (dịch Việt → Hàn)

## 1. Vì sao phải đổi

Cách chia cũ có 3 dạng: **Dạng 1** – không phải sửa gì · **Dạng 2** – Claude sửa lỗi bản gốc · **Dạng 3** – gặp âm Hán Việt khi dịch.

CTV tiếng Hàn kiểm tra 50 câu: **41 đạt · 2 sửa nhỏ · 7 không đạt**.

- 2 câu sửa nhỏ: lỗi **trình bày** (dính câu) mà Claude chưa bắt hết.
- 7 câu không đạt: **nội dung** tiếng Việt gốc sai (sai thì của câu, thiếu ý, sai tự/tha động từ). GPT dịch đúng theo bản tiếng Việt sai nên bản tiếng Hàn cũng sai.

→ Cách cũ vẫn cho câu sai nội dung đi dịch. Cần tách **lỗi trình bày** (sửa được) khỏi **lỗi nội dung** (phải có người biết tiếng Nhật xác nhận).

## 2. Cách chia mới

```
Mẫu lời giải tiếng Việt gốc
│
├── Phân dạng theo TRÌNH BÀY
│   ├── Dạng 1: không sai trình bày
│   └── Dạng 2: sai trình bày – dính câu, lặp từ, chính tả, thiếu xuống dòng,
│               cách đọc bị lẫn số ①②③
│               → Claude sửa, ghi chú rõ từng chỗ đã sửa
│
└── Gắn 2 CỜ (áp dụng cho cả Dạng 1 và Dạng 2)
    ├── Cờ "nghi sai nội dung" – sai thì / thiếu ý, sai tự/tha động từ,
    │                            sai nghĩa từ, đọc sai âm
    │   → Claude chỉ đánh dấu, ghi rõ nghi ở phần nào, KHÔNG tự sửa
    └── Cờ "âm Hán Việt" ở phần tham khảo → máy tự phát hiện
```

## 3. Mẫu đi tiếp thế nào

```
Không có cờ        → Dịch sang tiếng Hàn → CTV tiếng Hàn kiểm tra
Cờ nghi sai nội dung → CTV tiếng Nhật xác nhận → sửa theo CTV hoặc gỡ cờ → dịch
Cờ âm Hán Việt     → Chưa dịch, chờ quyết định cách xử lý
```

**Chỉ mẫu không có cờ nào mới được dịch sang tiếng Hàn.**

## 4. Tình trạng

- Đã cài đặt xong, chạy ở thư mục riêng; kết quả cũ giữ nguyên.
- 49 mẫu CTV tiếng Hàn đã chấp nhận được lưu vào kho riêng, không bị chạy lại.
- Bước tiếp theo: chạy thử 30–50 câu để đo tỷ lệ bị gắn cờ; CTV tiếng Nhật xem thêm khoảng 10% câu không có cờ để kiểm tra Claude có bỏ sót không.

## 5. Cần leader quyết định

1. **Âm Hán Việt** (63/1.872 câu): bỏ đi, thay bằng âm Hán-Hàn (한자음), hay giữ kèm ghi chú?
2. **Bổ sung âm Hán-Hàn cho người Hàn:** CTV tiếng Hàn gợi ý ở 35/50 câu để người học dễ liên tưởng – có thêm không? (Việc này là thêm nội dung so với bản gốc.)
