"""[Dạng 21] Giai đoạn 2 – Bước 2.1–2.3 do tác tử TẠO Claude dịch (không GPT API). Logic chung: pipeline_chung/claude_tao.py.

  python3 scripts/s2_claude_dich.py --chuan-bi --tu 1 --den 6  → map, request, _he_thong.md, tao_gd2_danh_sach.json
  (tác tử tạo theo prompts/s2_claude_dich.md ghi output/claude/tao_gd2/<id>.output.json = {"fN": "…"})
  python3 scripts/s2_claude_dich.py --nhan --tu 1 --den 6      → ghép → output/json_ko/claude_tao/<id>.json; lỗi → LỖI_GĐ2
Câu con 2 (bài 2 câu hỏi): full_translation không giao dịch – --nhan chép bản Hàn của câu con 1 (câu con 1 phải --nhan trước / cùng lượt).
Bước tiếp theo: s2_claude_goi.py → tác tử KIỂM TRA → s2_kiem_tra.py
"""
import os

import _dang as D
from pipeline_chung import claude_tao as CT
from pipeline_chung.common import load_json, save_json
from pipeline_chung.trang_thai import Status
from _dich_21 import GIU_CHO, chep_ft_tu_cau_1, danh_dau, prefill_21, tagged_copy_21
from _dau_vao import load_tm, terms_text, user_message_gd2

_CHEP = {"on": False}


def _prefill(fmap, fixed, tm):
    return prefill_21(fmap, fixed, tm, chep_ft=_CHEP["on"])


def _user_message(norm, tagged, todo):
    _CHEP["on"] = False
    return user_message_gd2(norm, tagged, todo)


class Hook(CT.HookGD2):
    pass


def _danh_dau(fmap, vi, cfg):
    _CHEP["on"] = bool(D.load_norm(f"{vi['question_id']}_{vi['cau_con']}").get("ft_chep_tu"))
    return danh_dau(fmap, vi, cfg)


HOOK = Hook(user_message=_user_message, load_tm=load_tm, terms_text=terms_text,
            danh_dau=_danh_dau, prefill=_prefill, tagged=tagged_copy_21)


def sau_nhan(args, cfg):
    """Câu con 2: thay chỗ giữ chỗ trong full_translation bằng bản Hàn của câu con 1."""
    st = Status(D.status_path())
    lang = cfg["ngon_ngu_dich"]
    n = 0
    for sid in CT._chon(D, HOOK, args, cfg, st):
        p = D.OUT("json_ko", "claude_tao", sid + ".json")
        norm = D.load_norm(sid)
        if not norm.get("ft_chep_tu") or not os.path.exists(p):
            continue
        doc = load_json(p)
        if GIU_CHO not in str(doc.get("full_translation")) and st.get(sid).get("trang_thai") != "LỖI_GĐ2":
            continue
        loi = chep_ft_tu_cau_1(doc, norm, lang)
        if loi:
            st.update(sid, trang_thai="LỖI_GĐ2", giai_doan_loi="2", loi=["Chép lời thoại câu con 1: " + x for x in loi])
            print(f"LỖI_GĐ2 {sid}: {loi}")
            continue
        save_json(doc, p)
        n += 1
    st.save()
    if n:
        print(f"Câu con 2: đã chép bản Hàn lời thoại của câu con 1 cho {n} câu")


if __name__ == "__main__":
    args, cfg = CT._args(), D.cfg()
    st = Status(D.status_path())
    if args.chuan_bi:
        CT.gd2_chuan_bi(D, HOOK, args, cfg, st)
    else:
        CT.gd2_nhan(D, HOOK, args, cfg, st)
        sau_nhan(args, cfg)
