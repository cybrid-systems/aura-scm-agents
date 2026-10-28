"""Minimal OpenAI-compatible /chat/completions client shared by llm_explain.py and llm_search.py.

Providers:
  glm      : GLM-5.3 Flash ("glm-5.3-flash") on the Zhipu coding-plan endpoint
             https://open.bigmodel.cn/api/coding/paas/v4 (the standard paas/v4 endpoint is not used);
             key file $GLM_KEY_FILE (default ~/.glm-key)
  minimax  : MiniMax-M3.1-Flash, key file $MINIMAX_API_KEY_FILE, base URL $MINIMAX_BASE_URL
             (both usually set in an env file, e.g. ~/.config/aura-build/minimax.env)
  deepseek : DeepSeek-V4.1-Flash ("deepseek-flash"), key file $DEEPSEEK_KEY_FILE (default ~/.deepseek-key)
Keys are read from files only; they are never printed, logged or written to results.
Reasoning models may spend the whole budget thinking and return empty content: callers pass a
large max_tokens (>= 8000) and an empty answer is retried once with double the budget.
"""
import json, os, re, time, urllib.error, urllib.request
from pathlib import Path

PROVIDERS = {
    "glm": dict(base="https://open.bigmodel.cn/api/coding/paas/v4", model="glm-5.3-flash", key_env="GLM_KEY_FILE",
                key_default="~/.glm-key", base_env="GLM_BASE_URL", model_env="GLM_MODEL"),
    "minimax": dict(base="https://api.minimaxi.com/v1", model="MiniMax-M3.1-Flash", key_env="MINIMAX_API_KEY_FILE",
                    key_default="", base_env="MINIMAX_BASE_URL", model_env="SCM_MINIMAX_MODEL"),
    "deepseek": dict(base="https://api.deepseek.com", model="deepseek-flash", key_env="DEEPSEEK_KEY_FILE",
                     key_default="~/.deepseek-key", base_env="DEEPSEEK_BASE_URL", model_env="DEEPSEEK_MODEL"),
}
THINK_RE = re.compile(r"<think>.*?</think>", re.S)


def load_env_file(p):
    for line in Path(os.path.expanduser(p)).read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))


def model_of(provider):
    cfg = PROVIDERS[provider]
    return os.environ.get(cfg["model_env"]) or cfg["model"]


def _post(provider, body, timeout):
    cfg = PROVIDERS[provider]
    keyfile = os.path.expanduser(os.environ.get(cfg["key_env"]) or cfg["key_default"])
    if not keyfile or not Path(keyfile).exists():
        raise RuntimeError(f"{provider}: key file not configured ({cfg['key_env']})")
    base = os.environ.get(cfg["base_env"]) or cfg["base"]
    req = urllib.request.Request(base.rstrip("/") + "/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + Path(keyfile).read_text().strip()})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:   # never echo request headers
        raise RuntimeError(f"{provider}: HTTP {e.code}: {e.read()[:300].decode('utf-8', 'replace')}") from None
    finally:
        del req


def call(provider, messages, max_tokens=8000, temperature=0.0, seed=None, timeout=300):
    """Returns dict(model, text, finish, prompt_tokens, completion_tokens, reasoning_tokens, latency_s, attempts)."""
    body = {"model": model_of(provider), "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    if seed is not None:
        body["seed"] = seed
    if provider == "deepseek":
        body["reasoning_effort"] = "low"
    t0, attempts, usage = time.time(), 0, {"prompt_tokens": 0, "completion_tokens": 0, "reasoning_tokens": 0}
    while True:
        attempts += 1
        out, transient = None, 0
        while out is None:   # transient failures (429 / 5xx / timeout / reset): back off and retry, max 3 more
            try:
                out = _post(provider, body, timeout)
            except Exception as e:
                msg = str(e)
                if transient >= 3 or not re.search(r"HTTP (429|5\d\d)|timed out|timeout|reset|Connection|Remote end|EOF|SSL", msg):
                    raise
                transient += 1
                attempts += 1
                time.sleep(10 * transient)
        u = out.get("usage") or {}
        usage["prompt_tokens"] += u.get("prompt_tokens", 0)
        usage["completion_tokens"] += u.get("completion_tokens", 0)
        usage["reasoning_tokens"] += (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0) or 0
        ch = out["choices"][0]
        text = THINK_RE.sub("", ch["message"].get("content") or "").strip()
        if text or attempts >= 2:
            break
        body["max_tokens"] = max_tokens * 2   # reasoning model ran out of budget before answering
    return dict(model=out.get("model", body["model"]), text=text, finish=ch.get("finish_reason"),
                latency_s=round(time.time() - t0, 2), attempts=attempts, **usage)
