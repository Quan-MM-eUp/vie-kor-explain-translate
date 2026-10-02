"""Gọi GPT qua LLM Gateway của công ty (API tương thích OpenAI), bắt buộc output theo JSON Schema (strict).

Key: OPENAI_API_KEY trong .env (Vie-Kor/.env, thư mục dạng bài, hoặc test_5dang/.env). KHÔNG in key ra màn hình.
Base URL: OPENAI_BASE_URL trong .env, nếu không có thì lấy "base_url" trong config (mặc định https://llm.eup.ai/v1).

Cấu hình (mục "gpt" trong config.json của dạng bài):
  model          tên model (xem bằng: python -m pipeline_chung.gpt_client --list-models)
  temperature    null = không gửi (một số model suy luận không nhận tham số này)
  timeout_sec, max_retries
  extra          tham số thêm gửi kèm, vd {"reasoning_effort": "high"}
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

from .common import ENV_FILES_USED, load_env

DEFAULT_BASE = "https://llm.eup.ai/v1"


class GPTError(Exception):
    """Lỗi khi gọi GPT. kind = 'cau_hinh' (key/model sai – không thử lại) | 'ky_thuat' (mạng, hết giờ, output hỏng)."""

    def __init__(self, msg, kind="ky_thuat"):
        super().__init__(msg)
        self.kind = kind


def base_url(cfg):
    return (os.environ.get("OPENAI_BASE_URL") or cfg.get("base_url") or DEFAULT_BASE).rstrip("/")


def _key(extra_dirs=()):
    key = load_env(extra_dirs)
    if not key:
        raise GPTError("Không tìm thấy OPENAI_API_KEY trong .env", "cau_hinh")
    return key


def _request(url, key, body=None, timeout=180):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if body is not None else "GET",
                                 headers={"Content-Type": "application/json", "Accept": "application/json",
                                          "Authorization": f"Bearer {key}",
                                          # một số tường lửa (vd Cloudflare) chặn User-Agent mặc định "Python-urllib" bằng lỗi 403
                                          "User-Agent": "eup-migii-pipeline/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def call_json(cfg, system, user, schema, schema_name, extra_dirs=()):
    """Gửi 1 yêu cầu, trả về (object JSON theo schema, usage, model thực tế)."""
    if not cfg.get("model") or "ĐIỀN" in cfg["model"]:
        raise GPTError("Chưa điền tên model trong config.json → gpt.model", "cau_hinh")
    key = _key(extra_dirs)
    body = {"model": cfg["model"],
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "response_format": {"type": "json_schema",
                                "json_schema": {"name": schema_name, "strict": True, "schema": schema}}}
    if cfg.get("temperature") is not None:
        body["temperature"] = cfg["temperature"]
    body.update(cfg.get("extra") or {})
    url = base_url(cfg) + "/chat/completions"
    last = None
    for attempt in range(1, int(cfg.get("max_retries", 3)) + 1):
        try:
            data = _request(url, key, body, timeout=cfg.get("timeout_sec", 180))
            choice = data["choices"][0]
            msg = choice["message"]
            if msg.get("refusal"):
                raise GPTError(f"GPT từ chối: {msg['refusal'][:200]}")
            if choice.get("finish_reason") == "length":
                raise GPTError("Output bị cắt do hết giới hạn token")
            return json.loads(msg["content"]), data.get("usage", {}), data.get("model", cfg["model"])
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:300]}"
            if e.code in (400, 401, 403, 404):
                raise GPTError(last, "cau_hinh")
        except GPTError as e:
            last = str(e)
        except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as e:
            last = repr(e)
        time.sleep(3 * attempt)
    raise GPTError(last or "lỗi không rõ")


def list_models(cfg, extra_dirs=()):
    data = _request(base_url(cfg) + "/models", _key(extra_dirs))
    return sorted(m.get("id") for m in data.get("data", []))


def diagnose(model=None):
    """Kiểm tra kết nối: .env nào được dùng, key có không (chỉ in độ dài), base URL, gọi thử /models và /chat/completions."""
    key = load_env()
    print("File .env đã đọc:", ENV_FILES_USED or "(không tìm thấy file .env nào)")
    print("OPENAI_API_KEY:", f"có ({len(key)} ký tự)" if key else "KHÔNG CÓ")
    if key and key != key.strip():
        print("  CHÚ Ý: key có khoảng trắng/ký tự thừa ở đầu hoặc cuối")
    url = base_url({})
    print("Base URL:", url)
    if not key:
        return

    def show(name, fn):
        try:
            data = fn()
            print(f"[OK] {name}")
            return data
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")[:400].replace("\n", " ")
            print(f"[LỖI] {name}: HTTP {e.code} {e.reason}\n       Nội dung gateway trả về: {body or '(trống)'}")
        except Exception as e:  # noqa: BLE001
            print(f"[LỖI] {name}: {e!r}")

    data = show("GET /models (danh sách model)", lambda: _request(url + "/models", key, timeout=30))
    if data:
        ids = sorted(m.get("id") for m in data.get("data", []))
        print(f"       {len(ids)} model:", ", ".join(ids[:80]))
    if model:
        body = {"model": model, "messages": [{"role": "user", "content": "Trả lời đúng một từ: OK"}]}
        data = show(f"POST /chat/completions với model {model} (gọi thử, rất ít token)",
                    lambda: _request(url + "/chat/completions", key, body, timeout=120))
        if data:
            print("       Trả lời:", data["choices"][0]["message"].get("content"), "| model thực tế:", data.get("model"))
            schema = {"type": "object", "additionalProperties": False,
                      "properties": {"tra_loi": {"type": "string"}, "so": {"type": "integer", "minimum": 1, "maximum": 4}},
                      "required": ["tra_loi", "so"]}
            body2 = dict(body, reasoning_effort="high",
                         response_format={"type": "json_schema", "json_schema": {"name": "thu", "strict": True, "schema": schema}})
            body2["messages"] = [{"role": "user", "content": "Trả về tra_loi = 'OK' và so = 3."}]
            data = show("Tính năng pipeline cần: reasoning_effort=high + JSON Schema strict (có minimum/maximum)",
                        lambda: _request(url + "/chat/completions", key, body2, timeout=180))
            if data:
                print("       Trả lời:", data["choices"][0]["message"].get("content"), "| token:", data.get("usage"))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    if "--list-models" in sys.argv:
        try:
            for m in list_models({}):
                print(m)
        except urllib.error.HTTPError as e:
            print(f"Không lấy được danh sách model: HTTP {e.code} – {e.read().decode('utf-8', 'ignore')[:300]}")
            print("Chạy chẩn đoán: python -m pipeline_chung.gpt_client --kiem-tra gpt-6-sol")
        except Exception as e:  # noqa: BLE001
            print("Không lấy được danh sách model:", e)
    elif "--kiem-tra" in sys.argv:
        i = sys.argv.index("--kiem-tra")
        diagnose(sys.argv[i + 1] if len(sys.argv) > i + 1 else None)
    else:
        print("Dùng: python -m pipeline_chung.gpt_client --list-models | --kiem-tra [tên model]")
