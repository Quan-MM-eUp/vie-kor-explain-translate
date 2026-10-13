"""Dạng 15 – phần riêng giai đoạn 2 (lấy từ pipeline_chung/doc_hieu_chung.py):

  - question.meaning, options[i].meaning, options[i].quotes[j].meaning, full_translation[k].lines[m].meaning (khi có ja)
      ← dịch TRỰC TIẾP từ câu tiếng Nhật (tác tử TẠO thấy bản Việt chỉ để tham khảo); không dùng câu cố định / bộ nhớ dịch
  - analysis, summary, bản dịch không có tiếng Nhật ← dịch từ tiếng Việt
Kiểm tra riêng: D-SO (số khác bản nguồn – cảnh báo), D12 (trợ từ sau ⟪kana⟫ – cảnh báo), D4 nhất quán theo câu tiếng Nhật.
"""
import _dang  # noqa: F401  (đặt sys.path tới thư mục Vie-Kor)
import pipeline_chung.doc_hieu_chung as H

NOTE_JA = H.NOTE_JA
danh_dau = H.danh_dau
prefill_v3 = H.prefill
tagged_copy_v3 = H.tagged_copy
loc_kiem_tra = H.loc_kiem_tra
d4_key = H.d4_key


def kiem_tra_v3(doc_ko, fmap, lang="ko"):
    """→ (lỗi, cảnh báo): D-SO + D12 đều là cảnh báo."""
    return [], H.kiem_tra_so(doc_ko, fmap, lang) + H.tro_tu(doc_ko, lang)
