# Prompt chạy pipeline dạng 01–21 (chỉ mẫu đề JLPT)

> Cập nhật 2026-10-11. Mỗi dạng chạy trong **một cuộc trò chuyện Cowork riêng** (chọn thư mục `Vie-Kor`), dán đúng câu của dạng đó.
> Tối đa **3 lô mỗi cuộc trò chuyện**; cuối mỗi lô Claude báo lệnh lô tiếp theo – gõ tiếp lệnh đó. Hết 3 lô → mở cuộc trò chuyện mới với câu mở đầu ở dưới, thay khoảng mẫu bằng lô tiếp theo.
> Các lô đã tính bộ lọc JLPT (bỏ mẫu có `Nat Test` trong cột `thi_thu_thuoc_de`). Lô tiếp theo luôn lấy lại được bằng `cd <thư mục dạng>/scripts && python3 lo_jlpt.py` (dạng 11, 12, 15: `python3 scripts/lo.py`).

**Không cần chạy nữa:** dạng 05 (209/209), 13 (149/149), 21 (128/128) – đã chạy xong.

| Dạng | Lô tiếp theo | Ghi chú |
|---|---|---|
| 01 | 571–586 | 10 mẫu JLPT, bỏ 5 NAT |
| 02 | 402–417 | 10 mẫu JLPT, bỏ 6 NAT |
| 03 | 11–22 | 10 mẫu JLPT, bỏ 2 NAT; GĐ2 chạy `--tu 1 --den 22` để dịch luôn 397_1 (sổ tay đã ghi) |
| 04 | 392–405 | 10 mẫu JLPT, bỏ 4 NAT |
| 06 | 364–377 | 10 mẫu JLPT, bỏ 4 NAT |
| 07 | 311–321 | 10 mẫu JLPT, bỏ 1 NAT |
| 08 | 251–264 | 10 mẫu JLPT, bỏ 4 NAT |
| 09 | 297–316 | 3 đoạn văn – 12 mẫu JLPT, bỏ 8 NAT |
| 10 | 292–303 | 11 mẫu JLPT, bỏ 1 NAT |
| 11 | 272–278 | lô 28 – 6 mẫu JLPT, bỏ 1 NAT |
| 12 | 260–267 | lô 34 – 4 mẫu JLPT, bỏ 4 NAT |
| 14 | 263–265 | lô 28 – lô cuối, 3 mẫu, không có NAT |
| 15 | 297–306 | lô 30 – 4 mẫu JLPT, bỏ 6 NAT |
| 16 | 233–244 | 10 mẫu JLPT, bỏ 2 NAT |
| 17 | 331–347 | 10 mẫu JLPT, bỏ 7 NAT |
| 18 | 211–221 | 10 mẫu JLPT, bỏ 1 NAT |
| 19 | 325–336 | lô 12 – không có mẫu NAT, không cần lọc |
| 20 | 271–283 | 10 mẫu JLPT, bỏ 3 NAT |

---

## Dạng 01

_10 mẫu JLPT, bỏ 5 NAT_

```
Đọc dang_bai/01_tu_vung_cach_doc_kanji/pipeline_v3/SO_TAY_CHAY.md rồi chạy dạng 01 mẫu 571 đến 586
```

## Dạng 02

_10 mẫu JLPT, bỏ 6 NAT_

```
Đọc dang_bai/02_tu_vung_thay_doi_cach_noi/SO_TAY_CHAY.md rồi chạy dạng 02 mẫu 402 đến 417
```

## Dạng 03

_10 mẫu JLPT, bỏ 2 NAT; GĐ2 chạy `--tu 1 --den 22` để dịch luôn 397_1 (sổ tay đã ghi)_

```
Đọc dang_bai/03_tu_vung_cach_viet_tu/SO_TAY_CHAY.md rồi chạy dạng 03 mẫu 11 đến 22
```

## Dạng 04

_10 mẫu JLPT, bỏ 4 NAT_

```
Đọc dang_bai/04_tu_vung_dien_tu_theo_van_canh/SO_TAY_CHAY.md rồi chạy dạng 04 mẫu 392 đến 405
```

## Dạng 06

_10 mẫu JLPT, bỏ 4 NAT_

```
Đọc dang_bai/06_tu_vung_ung_dung_tu/SO_TAY_CHAY.md rồi chạy dạng 06 mẫu 364 đến 377
```

## Dạng 07

_10 mẫu JLPT, bỏ 1 NAT_

```
Đọc dang_bai/07_ngu_phap_lua_chon_ngu_phap/SO_TAY_CHAY.md rồi chạy dạng 07 mẫu 311 đến 321
```

## Dạng 08

_10 mẫu JLPT, bỏ 4 NAT_

```
Đọc dang_bai/08_ngu_phap_lap_ghep_cau/SO_TAY_CHAY.md rồi chạy dạng 08 mẫu 251 đến 264
```

## Dạng 09

_3 đoạn văn – 12 mẫu JLPT, bỏ 8 NAT_

```
Đọc dang_bai/09_ngu_phap_theo_doan_van/SO_TAY_CHAY.md rồi chạy dạng 09 mẫu 297 đến 316
```

## Dạng 10

_11 mẫu JLPT, bỏ 1 NAT_

```
Đọc dang_bai/10_doc_hieu_doan_van_ngan/SO_TAY_CHAY.md rồi chạy dạng 10 mẫu 292 đến 303
```

## Dạng 11

_lô 28 – 6 mẫu JLPT, bỏ 1 NAT_

```
Đọc dang_bai/11_doc_hieu_doan_van_trung_binh/SO_TAY_CHAY.md rồi chạy dạng 11 mẫu 272 đến 278
```

## Dạng 12

_lô 34 – 4 mẫu JLPT, bỏ 4 NAT_

```
Đọc dang_bai/12_doc_hieu_doan_van_dai/SO_TAY_CHAY.md rồi chạy dạng 12 mẫu 260 đến 267
```

## Dạng 14

_lô 28 – lô cuối, 3 mẫu, không có NAT_

```
Đọc dang_bai/14_doc_hieu_chu_de_quan_diem/SO_TAY_CHAY.md rồi chạy dạng 14 mẫu 263 đến 265
```

## Dạng 15

_lô 30 – 4 mẫu JLPT, bỏ 6 NAT_

```
Đọc dang_bai/15_doc_hieu_tim_thong_tin/SO_TAY_CHAY.md rồi chạy dạng 15 mẫu 297 đến 306
```

## Dạng 16

_10 mẫu JLPT, bỏ 2 NAT_

```
Đọc dang_bai/16_nghe_hieu_chu_de/SO_TAY_CHAY.md rồi chạy dạng 16 mẫu 233 đến 244
```

## Dạng 17

_10 mẫu JLPT, bỏ 7 NAT_

```
Đọc dang_bai/17_nghe_hieu_diem_chinh/SO_TAY_CHAY.md rồi chạy dạng 17 mẫu 331 đến 347
```

## Dạng 18

_10 mẫu JLPT, bỏ 1 NAT_

```
Đọc dang_bai/18_nghe_hieu_khai_quat/SO_TAY_CHAY.md rồi chạy dạng 18 mẫu 211 đến 221
```

## Dạng 19

_lô 12 – không có mẫu NAT, không cần lọc_

```
Đọc dang_bai/19_nghe_hieu_dien_dat/SO_TAY_CHAY.md rồi chạy dạng 19 mẫu 325 đến 336
```

## Dạng 20

_10 mẫu JLPT, bỏ 3 NAT_

```
Đọc dang_bai/20_nghe_hieu_tra_loi_nhanh/SO_TAY_CHAY.md rồi chạy dạng 20 mẫu 271 đến 283
```
