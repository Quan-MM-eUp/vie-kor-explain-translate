"""Đặt sys.path tới thư mục Vie-Kor (để import pipeline_chung) – dùng cho các module phụ của dạng 16."""
import os
import sys

_VK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _VK not in sys.path:
    sys.path.insert(0, _VK)
