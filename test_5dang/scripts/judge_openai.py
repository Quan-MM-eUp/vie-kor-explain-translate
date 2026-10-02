"""Bước 5 – Giám khảo OpenAI chấm mù bản dịch của Haiku và Sonnet.

Với mỗi mẫu, giám khảo nhận:
  - Ngữ cảnh đề (câu hỏi, 4 lựa chọn, đáp án) – chỉ để hiểu
  - Từng trường: bản tiếng Việt + 2 bản dịch A/B (Haiku/Sonnet, thứ tự A/B xáo ngẫu nhiên)
  - Bản tiếng Hàn cũ (giai_thich_ko) dạng văn bản, gọi là C
Giám khảo trả về (JSON bắt buộc theo schema): bản tốt hơn cho từng trường, danh sách lỗi,
điểm 1–5 cho A, B, C. Script tự "mở mù" (A/B → tên model) khi lưu kết quả.

Key: đọc OPENAI_API_KEY (và OPENAI_BASE_URL nếu có) từ biến môi trường hoặc file .env (test_5dang/.env).
Key eUp gọi qua LLM Gateway https://llm.eup.ai/v1 (không gọi thẳng OpenAI). Không in key ra màn hình.

Cách chạy:
  python scripts/judge_openai.py --list-models      # xem tên các model gateway cung cấp
  python scripts/judge_openai.py --dry-run          # chỉ in prompt của mẫu đầu tiên, KHÔNG gọi API
  python scripts/judge_openai.py                    # chấm tất cả mẫu chưa chấm
  python scripts/judge_openai.py --only 01_kanji_1196_1 --force
Kết quả: reports/judge/<sample_id>.json và reports/judge_results.json
"""
import argparse
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (clean_html, explanation_text, iter_lang_fields, load_config, load_env, load_json, load_raw,  # noqa: E402
                    load_samples, p, save_json)

SYSTEM_PROMPT = """Bạn là biên tập viên song ngữ Việt–Hàn, chuyên tài liệu luyện thi JLPT cho người Hàn Quốc.
Nhiệm vụ: đánh giá các bản dịch tiếng Hàn của lời giải thích (viết bằng tiếng Việt) cho một câu hỏi JLPT.

Quy ước trong văn bản:
- Nội dung trong ⟪ ⟫ là tiếng Nhật, phải giữ nguyên, không dịch.
- Dấu { } đánh dấu phần gạch chân; bản dịch phải đặt { } quanh phần tương ứng.
- Văn phong yêu cầu: -습니다/-ㅂ니다, tự nhiên, chính xác thuật ngữ ngữ pháp/từ vựng tiếng Nhật.

Với MỖI trường, so sánh bản A và bản B với bản tiếng Việt: chọn bản tốt hơn ("A", "B" hoặc "tie"),
liệt kê lỗi (nếu có) theo loại: sai_nghia, thieu_thua, thuat_ngu, thieu_tu_nhien, loi_danh_dau, van_phong;
mức độ: nghiem_trong (sai kiến thức/đổi nghĩa), nang (người học hiểu sai một phần), nhe (câu chữ chưa hay).
Sau đó cho điểm tổng thể 1–5 cho A, B và bản cũ C (C chỉ đánh giá tổng thể, không theo trường).
Chỉ đánh giá chất lượng dịch, không đánh giá đúng/sai của nội dung gốc; nếu thấy nội dung gốc tiếng Việt
có vấn đề thì ghi vào "van_de_ban_goc". Ghi chú viết bằng tiếng Việt, ngắn gọn."""

RESPONSE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["fields", "overall", "van_de_ban_goc"],
    "properties": {
        "fields": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["id", "better", "errors"],
            "properties": {
                "id": {"type": "string"},
                "better": {"type": "string", "enum": ["A", "B", "tie"]},
                "errors": {"type": "array", "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["candidate", "type", "severity", "note"],
                    "properties": {
                        "candidate": {"type": "string", "enum": ["A", "B"]},
                        "type": {"type": "string", "enum": ["sai_nghia", "thieu_thua", "thuat_ngu",
                                                            "thieu_tu_nhien", "loi_danh_dau", "van_phong"]},
                        "severity": {"type": "string", "enum": ["nghiem_trong", "nang", "nhe"]},
                        "note": {"type": "string"}}}}}}},
        "overall": {"type": "object", "additionalProperties": False,
                    "required": ["score_A", "score_B", "score_C", "comment"],
                    "properties": {"score_A": {"type": "integer"}, "score_B": {"type": "integer"},
                                   "score_C": {"type": "integer"}, "comment": {"type": "string"}}},
        "van_de_ban_goc": {"type": "string"}}}


def build_payload(sample, models, lang, rng):
    sid = sample["sample_id"]
    raw = load_raw(sid)
    docs = {m: load_json(p("json_ko", m, sid + ".json")) for m in models}
    order = models[:]
    rng.shuffle(order)
    mapping = {"A": order[0], "B": order[1]}
    base = docs[models[0]]
    by_model = {m: {fp: o.get(lang, "") for fp, o in iter_lang_fields(docs[m])} for m in models}
    fields = [{"id": fp, "vi": o["vi"], "A": by_model[mapping["A"]].get(fp, ""), "B": by_model[mapping["B"]].get(fp, "")}
              for fp, o in iter_lang_fields(base)]
    context = {
        "dang_bai": sample["dang_bai"], "cap_do": raw["cap_do"],
        "cau_hoi": clean_html(raw["cau_hoi"]),
        "lua_chon": [clean_html(raw[f"lua_chon_{i}"]) for i in range(1, 5) if raw.get(f"lua_chon_{i}")],
        "dap_an_so": raw["dap_an_so"],
    }
    user = ("NGỮ CẢNH ĐỀ (chỉ để tham khảo):\n" + json.dumps(context, ensure_ascii=False, indent=1) +
            "\n\nCÁC TRƯỜNG CẦN ĐÁNH GIÁ (vi = bản gốc, A/B = bản dịch):\n" +
            json.dumps(fields, ensure_ascii=False, indent=1) +
            "\n\nBẢN CŨ C (toàn bộ lời giải tiếng Hàn cũ, dạng văn bản):\n" + explanation_text(raw.get("giai_thich_ko", "")))
    return user, mapping, [f["id"] for f in fields]


def base_url(cfg):
    """Ưu tiên OPENAI_BASE_URL trong .env / biến môi trường; nếu không có thì suy ra từ config."""
    env = os.environ.get("OPENAI_BASE_URL", "").strip().rstrip("/")
    if env:
        return env
    return cfg["judge"]["endpoint"].rsplit("/chat/completions", 1)[0]


def list_models(cfg, key):
    req = urllib.request.Request(base_url(cfg) + "/models", headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    ids = sorted(m.get("id", "") for m in data.get("data", []))
    print("Các model gateway cung cấp:")
    for i in ids:
        print("  -", i)


def call_openai(cfg, key, user):
    j = cfg["judge"]
    endpoint = base_url(cfg) + "/chat/completions"
    body = {"model": j["model"],
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}],
            "response_format": {"type": "json_schema",
                                "json_schema": {"name": "judge_result", "strict": True, "schema": RESPONSE_SCHEMA}}}
    if j.get("temperature") is not None:
        body["temperature"] = j["temperature"]
    req = urllib.request.Request(endpoint, data=json.dumps(body).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    last = None
    for attempt in range(1, j.get("max_retries", 3) + 1):
        try:
            with urllib.request.urlopen(req, timeout=j.get("timeout_sec", 180)) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return json.loads(data["choices"][0]["message"]["content"]), data.get("usage", {})
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:300]}"
            if e.code in (400, 401, 403, 404):
                break  # lỗi cấu hình (model sai, key sai) – không thử lại
        except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as e:
            last = repr(e)
        time.sleep(3 * attempt)
    raise RuntimeError(last)


def unblind(result, mapping):
    for f in result["fields"]:
        f["better_model"] = mapping.get(f["better"], "tie")
        for e in f["errors"]:
            e["model"] = mapping[e["candidate"]]
    o = result["overall"]
    o["score_by_model"] = {mapping["A"]: o["score_A"], mapping["B"]: o["score_B"], "old_ko": o["score_C"]}
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="in prompt của mẫu đầu tiên, không gọi API")
    ap.add_argument("--only", help="chỉ chấm sample_id này")
    ap.add_argument("--force", action="store_true", help="chấm lại cả mẫu đã có kết quả")
    ap.add_argument("--list-models", action="store_true", help="liệt kê model mà gateway cung cấp rồi thoát")
    args = ap.parse_args()

    if args.list_models:
        key = load_env()
        if not key:
            sys.exit("Không tìm thấy OPENAI_API_KEY trong .env.")
        list_models(load_config(), key)
        return

    cfg = load_config()
    models, lang = cfg["models"], cfg["target_lang"]
    rng = random.Random(cfg["seed"])
    samples = [s for s in load_samples() if not args.only or s["sample_id"] == args.only]

    ready = [s for s in samples if all(os.path.exists(p("json_ko", m, s["sample_id"] + ".json")) for m in models)]
    if not ready:
        sys.exit("Chưa có mẫu nào đủ bản dịch của cả hai model trong json_ko/.")

    if args.dry_run:
        user, mapping, _ = build_payload(ready[0], models, lang, rng)
        print("=== SYSTEM ===\n" + SYSTEM_PROMPT + "\n\n=== USER ===\n" + user)
        print(f"\n(Ánh xạ A/B: {mapping}; model giám khảo: {cfg['judge']['model']})")
        return

    key = load_env()
    if not key:
        sys.exit("Không tìm thấy OPENAI_API_KEY (đặt trong biến môi trường hoặc file test_5dang/.env).")
    if "ĐIỀN" in cfg["judge"]["model"]:
        sys.exit("Hãy điền tên model OpenAI vào config.json → judge.model trước khi chạy.")

    all_results, usage_total = [], {"prompt_tokens": 0, "completion_tokens": 0}
    for s in ready:
        sid = s["sample_id"]
        out = p("reports", "judge", sid + ".json")
        if os.path.exists(out) and not args.force:
            all_results.append(load_json(out))
            print(f"bỏ qua (đã chấm) {sid}")
            continue
        user, mapping, ids = build_payload(s, models, lang, rng)
        try:
            result, usage = call_openai(cfg, key, user)
        except RuntimeError as e:
            print(f"LỖI {sid}: {e}")
            continue
        rec = {"sample_id": sid, "dang_bai": s["dang_bai"], "mapping": mapping,
               "judge_model": cfg["judge"]["model"], "usage": usage, "result": unblind(result, mapping)}
        save_json(rec, out)
        all_results.append(rec)
        for k in usage_total:
            usage_total[k] += usage.get(k, 0)
        o = rec["result"]["overall"]["score_by_model"]
        print(f"đã chấm {sid}: {o}")
    save_json({"results": all_results, "usage_lan_chay_nay": usage_total}, p("reports", "judge_results.json"))
    print(f"Xong {len(all_results)} mẫu → reports/judge_results.json | token lần này: {usage_total}")


if __name__ == "__main__":
    main()
