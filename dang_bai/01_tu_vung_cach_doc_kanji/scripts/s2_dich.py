"""Giai đoạn 2 – Bước 2.1–2.3: dịch JSON tiếng Việt (đã chốt) sang tiếng Hàn.

2.1 Python tách trường cần dịch: mã f1…fn ↔ đường dẫn ↔ nội dung vi (bảng đối chiếu <id>.map.json);
    điền sẵn câu cố định (bảng thuật ngữ) và bộ nhớ dịch → không gửi GPT
2.2 GPT nhận cả JSON (mã gắn tại chỗ) + ngữ cảnh đề, CHỈ trả về {"fN": "…"} cho các mã còn lại (schema strict)
2.3 Python ghép lại, kiểm tra khớp nội dung; lỗi ghép → LỖI_GĐ2

Cách chạy:
  python scripts/s2_dich.py --pilot --dry-run      # in prompt câu đầu tiên, không gọi API
  python scripts/s2_dich.py --pilot
  python scripts/s2_dich.py --lo 200
Đầu ra: output/json_ko/gpt/<id>.json (+ .map.json, .request.json, .output.json, .meta.json)
"""
import argparse
import datetime
import json
import os

import _dang as D
from pipeline_chung.common import drop_lang, load_json, save_json
from pipeline_chung.dich import build_map, merge, output_schema, prefill, tagged_copy
from pipeline_chung.gpt_client import GPTError, call_json
from pipeline_chung.trang_thai import Status


def terms_text(g):
    lines = ["Thuật ngữ (Việt → Hàn):"] + [f"- {k} → {v}" for k, v in g["thuat_ngu"].items()]
    if g["cau_co_dinh"]:
        by_ko = {}
        for vi, ko in g["cau_co_dinh"].items():
            by_ko.setdefault(ko, []).append(vi)
        lines += ["", "Câu cố định (mọi cách viết tiếng Việt bên trái đều dịch đúng một câu bên phải):"]
        lines += [f"- {' | '.join(v)} → {ko}" for ko, v in by_ko.items()]
    if g["mau_cau"]:
        lines += ["", "Mẫu câu (X, A, B là phần thay đổi):"] + [f"- {k} → {v}" for k, v in g["mau_cau"].items()]
    return "\n".join(lines)


def load_tm(cfg):
    path = D.OUT(cfg["bo_nho_dich"]["file"])
    return load_json(path) if cfg["bo_nho_dich"].get("dung") and os.path.exists(path) else {}


def user_message(norm, tagged, todo):
    de = norm["de"]
    ctx = {"cau_hoi": de["cau_hoi"], "cac_lua_chon": {str(i + 1): x for i, x in enumerate(de["lua_chon"])},
           "dap_an_so": de["dap_an_so"]}
    return ("NGỮ CẢNH ĐỀ (chỉ để hiểu):\n" + json.dumps(ctx, ensure_ascii=False, indent=1) +
            "\n\nJSON LỜI GIẢI (trường cần dịch có dạng {\"id\": …, \"vi\": …}):\n" + json.dumps(tagged, ensure_ascii=False, indent=1) +
            "\n\nDỊCH CÁC ID SAU (chỉ các id này): " + ", ".join(todo))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--ids")
    ap.add_argument("--lo", type=int)
    ap.add_argument("--tat-ca", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--ca-da-duyet", action="store_true", help="vẫn chạy cả mẫu đã có trong kho da_duyet/")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    cfg, lang = D.cfg(), D.cfg()["ngon_ngu_dich"]
    st = Status(D.status_path())
    ids = [s for s in D.select_ids(args, st, ("GĐ1_XONG", "LỖI_GĐ2"))
           if os.path.exists(D.OUT("json_vi", "final", s + ".json")) and st.get(s).get("duyet_vi")]
    ids = D.bo_qua_da_duyet(ids, args, "2.1")
    if cfg.get("cach_chia_dang") == "v2":
        # Cách chia v2: chỉ dịch câu KHÔNG nghi sai nội dung và KHÔNG có âm Hán Việt (chốt chặn thứ 2, sau trạng thái GĐ1)
        chan = [s for s in ids if st.get(s).get("co_nghi_noi_dung") or st.get(s).get("co_han_viet")
                or D.han_viet_src(D.load_norm(s))]
        if chan:
            print(f"Bỏ qua {len(chan)} câu có cờ nghi sai nội dung / âm Hán Việt (không dịch): {chan[:10]}")
        ids = [s for s in ids if s not in chan]
    if not ids:
        raise SystemExit(f"Không có câu nào đã chốt JSON tiếng Việt ({D.OUT('json_vi', 'final')} + đã duyệt). Hãy chạy bước 1.5: python scripts/s1_chot.py … trước.")
    g = D.glossary()
    system = D.read_prompt("s2_dich_ko.md").replace("{{THUAT_NGU}}", terms_text(g))
    tm = load_tm(cfg)
    tot = {"prompt_tokens": 0, "completion_tokens": 0}
    n_ok = n_err = n_prefill = n_sent = 0
    for k, sid in enumerate(ids):
        out = D.OUT("json_ko", "gpt", sid + ".json")
        vi = load_json(D.OUT("json_vi", "final", sid + ".json"))
        if os.path.exists(out) and not args.force and not args.dry_run:
            if drop_lang(load_json(out), lang) == vi:
                continue
            print(f"{sid}: JSON tiếng Việt đã thay đổi sau lần dịch trước → dịch lại")
        norm = D.load_norm(sid)
        fmap = build_map(vi)
        filled, todo = prefill(fmap, g["cau_co_dinh"], tm)
        tagged = tagged_copy(vi, fmap, lang)
        if args.dry_run:
            print("=== SYSTEM ===\n" + system + "\n\n=== USER ===\n" + user_message(norm, tagged, todo))
            print(f"\nĐiền sẵn (không gửi GPT): { {i: v['nguon'] for i, v in filled.items()} }")
            print(f"Schema output: {json.dumps(output_schema(todo), ensure_ascii=False)[:300]}")
            return
        base = D.OUT("json_ko", "gpt", sid)
        save_json(fmap, base + ".map.json")
        trans, meta = {i: v["text"] for i, v in filled.items()}, {"sample_id": sid, "dien_san": {i: v["nguon"] for i, v in filled.items()}}
        if todo:
            save_json({"system_version": cfg["phien_ban_prompt"]["gd2"], "user": user_message(norm, tagged, todo), "ids": todo},
                      base + ".request.json")
            t0 = datetime.datetime.now()
            try:
                res, usage, model = call_json(cfg["gpt"], system, user_message(norm, tagged, todo), output_schema(todo),
                                              "translation", [D.DANG])
            except GPTError as e:
                if e.kind == "cau_hinh":
                    st.save()
                    raise SystemExit(f"Dừng: lỗi cấu hình – {e}")
                st.update(sid, trang_thai="LỖI_GĐ2", giai_doan_loi="2", loi=f"LỖI_KỸ_THUẬT – GPT: {e}")
                n_err += 1
                print(f"LỖI_KỸ_THUẬT {sid}: {e}")
                continue
            save_json(res, base + ".output.json")
            trans.update(res)
            meta.update(model=model, usage=usage, prompt=cfg["phien_ban_prompt"]["gd2"],
                        thoi_gian_giay=(datetime.datetime.now() - t0).total_seconds())
            for kk in tot:
                tot[kk] += usage.get(kk, 0)
            st.update(sid, model_gd2=model, prompt_gd2=cfg["phien_ban_prompt"]["gd2"])
        save_json(meta, base + ".meta.json")
        with open(D.OUT("reports", "usage_gd2.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(meta, ensure_ascii=False) + "\n")
        n_prefill += len(filled); n_sent += len(todo)
        doc, errs = merge(vi, fmap, trans, lang)
        if errs:
            st.update(sid, trang_thai="LỖI_GĐ2", giai_doan_loi="2", loi=["Ghép bản dịch: " + e for e in errs])
            n_err += 1
            print(f"LỖI_GĐ2 {sid}: {errs[:3]}")
            continue
        save_json(doc, out)
        st.update(sid, loi="", giai_doan_loi="")
        n_ok += 1
        print(f"xong {sid}: {len(fmap)} trường (điền sẵn {len(filled)}, gửi GPT {len(todo)})")
        if (k + 1) % 20 == 0:
            st.save()
    st.save()
    print(f"Xong {n_ok} câu, lỗi {n_err}. Trường điền sẵn {n_prefill}, gửi GPT {n_sent}. Token: {tot}")
    print("Bước tiếp theo: python scripts/s2_claude_goi.py … rồi nhờ Claude kiểm tra (prompts/s2_claude_kiem_tra.md)")


if __name__ == "__main__":
    main()
