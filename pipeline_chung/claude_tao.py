"""Luồng TÁC TỬ TẠO dùng chung (Claude Opus 5.5 trong Cowork làm thay GPT API) – đưa từ dạng 07 lên 2026-10-08.

Hai tác tử tách bạch (giữ kiểm tra chéo):
  * Tác tử TẠO (Claude A) – tác tử con, ngữ cảnh riêng: GĐ1 chuyển lời giải → JSON tiếng Việt; GĐ2 dịch → tiếng Hàn.
  * Tác tử KIỂM TRA – phiên Claude chính: soát như trước (s1_claude_goi / s2_claude_goi …).

Mỗi dạng chỉ cần một script mỏng gọi các hàm ở đây và truyền phần RIÊNG của dạng:
  scripts/s1_claude_tao.py:
      import _dang as D
      from s1_gpt_chuyen import STATES, user_message
      from pipeline_chung import claude_tao as CT
      CT.main_gd1(D, STATES, user_message)
  scripts/s2_claude_dich.py:
      CT.main_gd2(D, CT.HookGD2(user_message=…, load_tm=…, terms_text=…, chon=…, danh_dau=…, prefill=…, tagged=…))

Module dạng `D` (_dang.py) phải có: DANG, cfg(), P(), OUT(), load_norm(), select_ids(), bo_qua_da_duyet(),
status_path(), glossary(), read_prompt().
config.json của dạng cần: schema_api, claude.model, claude.cach_chay, phien_ban_prompt.gd1_tao / gd2_tao,
ngon_ngu_dich, tao_ban.nguon ("claude" | "gpt").
"""
import argparse
import datetime
import json
import os
from dataclasses import dataclass
from typing import Callable, Optional

from .checks_chung import schema_errors
from .common import drop_lang, load_json, save_json
from .dich import build_map, merge, prefill as _prefill, tagged_copy as _tagged
from . import tham_khao as TK
from .trang_thai import Status

THU_MUC_TAO = {"gpt": "gpt", "claude": "claude_tao"}


# ---------------- vị trí bản TẠO (GPT cũ / Claude A) ----------------
def nguon_tao(cfg):
    """config.tao_ban.nguon: 'claude' (tác tử tạo) | 'gpt' (GPT API cũ)."""
    return (cfg.get("tao_ban") or {}).get("nguon", "gpt")


def thu_muc_tao(D, lop, sid):
    """Ưu tiên claude_tao/ nếu đã có bản, không thì gpt/, không có cả hai thì theo nguon_tao."""
    for d in ("claude_tao", "gpt"):
        if os.path.exists(D.OUT(lop, d, sid + ".json")):
            return d
    return THU_MUC_TAO[nguon_tao(D.cfg())]


def ban_tao(D, lop, sid, ext=".json"):
    return D.OUT(lop, thu_muc_tao(D, lop, sid), sid + ext)


def ten_ban_tao(D, lop, sid):
    return "Claude (tác tử tạo)" if thu_muc_tao(D, lop, sid) == "claude_tao" else "GPT"


def chan_gpt(D, args_list):
    """Gọi đầu s1_gpt_chuyen / s2_dich: dạng đã chuyển sang Claude thì không gọi GPT trừ khi --dung-gpt / --dry-run."""
    if nguon_tao(D.cfg()) == "claude" and "--dung-gpt" not in args_list and "--dry-run" not in args_list:
        raise SystemExit("Dạng này đã chuyển sang tác tử tạo Claude (config.tao_ban.nguon = 'claude'). "
                         "Dùng s1_claude_tao.py / s2_claude_dich.py; muốn gọi GPT thật thì thêm --dung-gpt.")


def _rel(D, p):
    return os.path.relpath(p, D.DANG).replace("\\", "/")


def _meta_base(cfg, prompt_key):
    return {"nguon": "claude", "model": cfg["claude"]["model"], "cach_chay": cfg["claude"]["cach_chay"],
            "prompt": cfg["phien_ban_prompt"][prompt_key], "luc_nhan": datetime.datetime.now().isoformat(timespec="seconds")}


def _ghi_usage(D, ten, meta):
    os.makedirs(D.OUT("reports"), exist_ok=True)
    with open(D.OUT("reports", ten), "a", encoding="utf-8") as f:
        f.write(json.dumps(meta, ensure_ascii=False) + "\n")


# ---------------- GĐ1 – bước 1.1 ----------------
def gd1_out(D, sid):
    return D.OUT("json_vi", "claude_tao", sid + ".json")


def gd1_chuan_bi(D, args, cfg, st, states, user_message, bo_qua=lambda norm: norm.get("khuon_goc") == "trong"):
    ids = D.bo_qua_da_duyet(D.select_ids(args, st, states), args, "1.1")
    tasks, skip = [], 0
    for sid in ids:
        norm = D.load_norm(sid)
        if bo_qua(norm):
            continue
        if not args.force and (os.path.exists(gd1_out(D, sid)) or os.path.exists(D.OUT("json_vi", "gpt", sid + ".json"))):
            skip += 1
            continue
        inp = D.OUT("claude", "tao_gd1", sid + ".input.json")
        save_json({"sample_id": sid, "yeu_cau": user_message(norm)}, inp)
        tasks.append({"sample_id": sid, "file_vao": _rel(D, inp), "file_ra": _rel(D, gd1_out(D, sid))})
    save_json({"prompt": "prompts/s1_claude_tao.md", "huong_dan_chi_tiet": "prompts/s1_chuyen_json.md",
               "schema": cfg["schema_api"], "cau": tasks}, D.OUT("claude", "tao_gd1_danh_sach.json"))
    print(f"{len(tasks)} câu cho tác tử tạo → output/claude/tao_gd1_danh_sach.json"
          + (f" | bỏ qua {skip} câu đã có bản tạo" if skip else ""))
    print("Tác tử tạo làm theo prompts/s1_claude_tao.md, xong chạy: python scripts/s1_claude_tao.py --nhan …")
    return tasks


def gd1_nhan(D, args, cfg, st, states, kiem_them: Optional[Callable] = None, bo_sung: Optional[Callable] = None):
    """kiem_them(doc, norm) → danh sách lỗi riêng của dạng (tùy chọn); bo_sung(doc, norm) → doc: Python điền trường x-python-dien riêng của dạng (vd passage dạng 09)."""
    ids = D.select_ids(args, st, states)
    schema = load_json(D.P(cfg["schema_api"]))
    ok = err = thieu = 0
    for sid in ids:
        p = gd1_out(D, sid)
        if not os.path.exists(p):
            if not os.path.exists(D.OUT("json_vi", "gpt", sid + ".json")):
                thieu += 1
                print(f"CHƯA CÓ {sid}: tác tử tạo chưa ghi {_rel(D, p)}")
            continue
        try:
            doc = load_json(p)
        except Exception as e:
            st.update(sid, trang_thai="LỖI_KỸ_THUẬT", giai_doan_loi="1", loi=f"Claude A: JSON không hợp lệ – {e}")
            err += 1
            print(f"LỖI_KỸ_THUẬT {sid}: JSON không hợp lệ – {e}")
            continue
        doc.pop(TK.TRUONG, None)
        if hasattr(D, "bo_truong_python"):      # dạng 20: bỏ trường Python điền (x-python-dien) trước khi so schema api – chạy lại --nhan không lỗi
            doc = D.bo_truong_python(doc)
        norm = D.load_norm(sid)
        loi = schema_errors(doc, schema)
        for k in ("question_id", "cau_con"):
            if str(doc.get(k)) != str(norm[k]):
                loi.append(f"{k} = {doc.get(k)} ≠ {norm[k]}")
        if kiem_them:
            loi += list(kiem_them(doc, norm) or [])
        if loi:
            st.update(sid, trang_thai="LỖI_KỸ_THUẬT", giai_doan_loi="1", loi=["Claude A: " + x for x in loi[:5]])
            err += 1
            print(f"LỖI_KỸ_THUẬT {sid}: {loi[:3]}")
            continue
        TK.dien(doc, (norm.get("phan") or {}).get("tham_khao"))
        if bo_sung:
            doc = bo_sung(doc, norm)
        save_json(doc, p)
        meta = {"sample_id": sid, **_meta_base(cfg, "gd1_tao")}
        save_json(meta, D.OUT("json_vi", "claude_tao", sid + ".meta.json"))
        _ghi_usage(D, "usage_gd1.jsonl", meta)
        st.update(sid, trang_thai="ĐANG_XỬ_LÝ", loi="", giai_doan_loi="", model_gd1=meta["model"], prompt_gd1=meta["prompt"])
        ok += 1
    st.save()
    print(f"Nhận {ok} câu, lỗi {err}, chưa có {thieu}.")
    print("Bước tiếp theo: python scripts/s1_claude_goi.py … rồi Claude kiểm tra (prompts/s1_claude_kiem_tra.md)")


# ---------------- GĐ2 – bước 2.1–2.3 ----------------
GD2_DIR = ("json_ko", "claude_tao")


@dataclass
class HookGD2:
    """Phần riêng của dạng cho GĐ2. Bắt buộc: user_message(norm, tagged, todo), load_tm(cfg), terms_text(glossary).
    Tùy chọn: chon(D, args, cfg, st) → ids; danh_dau(fmap, vi, cfg) → fmap; prefill(fmap, cau_co_dinh, tm); tagged(vi, fmap, lang)."""
    user_message: Callable
    load_tm: Callable
    terms_text: Callable
    chon: Optional[Callable] = None
    danh_dau: Optional[Callable] = None
    prefill: Callable = _prefill
    tagged: Callable = _tagged
    prompt_he_thong: str = "s2_dich_ko.md"


def gd2_chon_mac_dinh(D, args, cfg, st):
    ids = [s for s in D.select_ids(args, st, ("GĐ1_XONG", "LỖI_GĐ2"))
           if os.path.exists(D.OUT("json_vi", "final", s + ".json")) and st.get(s).get("duyet_vi")]
    ids = D.bo_qua_da_duyet(ids, args, "2.1")
    if cfg.get("cach_chia_dang") == "v2":
        hv = getattr(D, "han_viet_src", lambda norm: False)
        chan = [s for s in ids if st.get(s).get("co_nghi_noi_dung") or st.get(s).get("co_han_viet") or hv(D.load_norm(s))]
        if chan:
            print(f"Bỏ qua {len(chan)} câu có cờ nghi sai nội dung / âm Hán Việt (không dịch): {chan[:10]}")
        ids = [s for s in ids if s not in chan]
    return ids


def _chon(D, H, args, cfg, st):
    return (H.chon or gd2_chon_mac_dinh)(D, args, cfg, st)


def _da_dich(D, sid, vi, lang):
    p = ban_tao(D, "json_ko", sid)
    return os.path.exists(p) and drop_lang(load_json(p), lang) == vi


def gd2_chuan_bi(D, H, args, cfg, st):
    lang = cfg["ngon_ngu_dich"]
    g = D.glossary()
    os.makedirs(D.OUT("claude", "tao_gd2"), exist_ok=True)
    with open(D.OUT("claude", "tao_gd2", "_he_thong.md"), "w", encoding="utf-8") as f:
        f.write(D.read_prompt(H.prompt_he_thong).replace("{{THUAT_NGU}}", H.terms_text(g)))
    tm = H.load_tm(cfg)
    tasks, xong_ngay = [], 0
    for sid in _chon(D, H, args, cfg, st):
        vi = load_json(D.OUT("json_vi", "final", sid + ".json"))
        if not args.force and _da_dich(D, sid, vi, lang):
            continue
        fmap = build_map(vi)
        if H.danh_dau:
            fmap = H.danh_dau(fmap, vi, cfg)
        filled, todo = H.prefill(fmap, g.get("cau_co_dinh"), tm)
        tagged = H.tagged(vi, fmap, lang)
        save_json(fmap, D.OUT(*GD2_DIR, sid + ".map.json"))
        req = D.OUT("claude", "tao_gd2", sid + ".request.json")
        save_json({"sample_id": sid, "user": H.user_message(D.load_norm(sid), tagged, todo), "ids": todo,
                   "dien_san": dict(filled)}, req)
        outp = D.OUT("claude", "tao_gd2", sid + ".output.json")
        if not todo:
            save_json({}, outp)
            xong_ngay += 1
            continue
        tasks.append({"sample_id": sid, "file_vao": _rel(D, req), "file_ra": _rel(D, outp), "so_ma": len(todo)})
    save_json({"prompt": "prompts/s2_claude_dich.md", "huong_dan_he_thong": "output/claude/tao_gd2/_he_thong.md", "cau": tasks},
              D.OUT("claude", "tao_gd2_danh_sach.json"))
    print(f"{len(tasks)} câu cho tác tử tạo dịch → output/claude/tao_gd2_danh_sach.json"
          + (f" | {xong_ngay} câu điền sẵn hết (không cần dịch)" if xong_ngay else ""))
    print("Tác tử tạo làm theo prompts/s2_claude_dich.md, xong chạy: python scripts/s2_claude_dich.py --nhan …")
    return tasks


def gd2_nhan(D, H, args, cfg, st):
    lang = cfg["ngon_ngu_dich"]
    n_ok = n_err = n_thieu = 0
    for sid in _chon(D, H, args, cfg, st):
        vi = load_json(D.OUT("json_vi", "final", sid + ".json"))
        req_p, out_p = D.OUT("claude", "tao_gd2", sid + ".request.json"), D.OUT("claude", "tao_gd2", sid + ".output.json")
        if not os.path.exists(req_p):
            if not _da_dich(D, sid, vi, lang):
                print(f"CHƯA CHUẨN BỊ {sid}: chạy --chuan-bi trước")
            continue
        if not os.path.exists(out_p):
            n_thieu += 1
            print(f"CHƯA CÓ {sid}: tác tử tạo chưa ghi {_rel(D, out_p)}")
            continue
        req, fmap = load_json(req_p), load_json(D.OUT(*GD2_DIR, sid + ".map.json"))
        try:
            res = load_json(out_p)
        except Exception as e:
            st.update(sid, trang_thai="LỖI_GĐ2", giai_doan_loi="2", loi=f"Claude A: output không phải JSON – {e}")
            n_err += 1
            continue
        loi = []
        thua, thieu = sorted(set(res) - set(req["ids"])), sorted(set(req["ids"]) - set(res))
        if thua:
            loi.append(f"mã không được yêu cầu: {thua}")
        if thieu:
            loi.append(f"thiếu mã: {thieu}")
        trans = {i: v["text"] for i, v in req["dien_san"].items()}
        trans.update({k: v for k, v in res.items() if k in req["ids"]})
        doc, errs = merge(vi, fmap, trans, lang)
        loi += errs
        if loi:
            st.update(sid, trang_thai="LỖI_GĐ2", giai_doan_loi="2", loi=["Claude A – ghép bản dịch: " + e for e in loi[:5]])
            n_err += 1
            print(f"LỖI_GĐ2 {sid}: {loi[:3]}")
            continue
        save_json(doc, D.OUT(*GD2_DIR, sid + ".json"))
        meta = {"sample_id": sid, **_meta_base(cfg, "gd2_tao"),
                "dien_san": {i: v["nguon"] for i, v in req["dien_san"].items()}, "so_ma_dich": len(req["ids"])}
        save_json(meta, D.OUT(*GD2_DIR, sid + ".meta.json"))
        _ghi_usage(D, "usage_gd2.jsonl", meta)
        st.update(sid, loi="", giai_doan_loi="", model_gd2=meta["model"], prompt_gd2=meta["prompt"])
        n_ok += 1
    st.save()
    print(f"Ghép xong {n_ok} câu, lỗi {n_err}, chưa có output {n_thieu}.")
    print("Bước tiếp theo: python scripts/s2_claude_goi.py … rồi Claude kiểm tra (prompts/s2_claude_kiem_tra.md)")


# ---------------- dòng lệnh ----------------
def _args():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--chuan-bi", action="store_true")
    g.add_argument("--nhan", action="store_true")
    for a in ("--pilot", "--tat-ca", "--force", "--ca-da-duyet"):
        ap.add_argument(a, action="store_true")
    ap.add_argument("--ids")
    ap.add_argument("--lo", type=int)
    return ap.parse_args()


def main_gd1(D, states, user_message, **kw):
    args, cfg = _args(), D.cfg()
    st = Status(D.status_path())
    if args.chuan_bi:
        gd1_chuan_bi(D, args, cfg, st, states, user_message, **({"bo_qua": kw["bo_qua"]} if "bo_qua" in kw else {}))
    else:
        gd1_nhan(D, args, cfg, st, states, kw.get("kiem_them"), kw.get("bo_sung"))


def main_gd2(D, H):
    args, cfg = _args(), D.cfg()
    st = Status(D.status_path())
    (gd2_chuan_bi if args.chuan_bi else gd2_nhan)(D, H, args, cfg, st)
