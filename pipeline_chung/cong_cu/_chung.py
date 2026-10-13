"""Tiện ích cho các công cụ của tác tử KIỂM TRA. Chạy mọi công cụ với thư mục hiện tại = thư mục dạng bài (DANG)."""
import csv
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

DANG = os.getcwd()


def lj(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def sj(p, d):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def cfg():
    return lj(os.path.join(DANG, "config.json"))


def out(*parts):
    return os.path.join(DANG, os.environ.get("PIPELINE_OUTPUT") or cfg().get("output", "output"), *parts)


def thu_tu():
    with open(out("thu_tu_chay.csv"), encoding="utf-8-sig") as f:
        return [(int(r["stt"]), r["sample_id"]) for r in csv.DictReader(f)]


def trang_thai():
    p = out("reports", "trang_thai.csv")
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8-sig") as f:
        return {r["sample_id"]: r for r in csv.DictReader(f)}


def ids_tu_den(tu, den):
    return [sid for stt, sid in thu_tu() if tu <= stt <= den]


def kiem_dang():
    if not os.path.exists(os.path.join(DANG, "config.json")):
        sys.exit("Hãy chạy công cụ trong thư mục dạng bài (có config.json), vd: cd dang_bai/07_ngu_phap_lua_chon_ngu_phap")
