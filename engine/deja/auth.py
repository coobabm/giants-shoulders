"""模型调用走哪份额度：Claude 订阅（claude.ai 登录）还是 Anthropic API key。

模式（`radar auth --mode` 设置，或环境变量 DEJA_AUTH）：
- auto（默认）：先用订阅；订阅额度用完 / 没登录时，有 API key 就自动改用 API，并在之后一段时间内直接走 API。
- subscription：只用订阅。
- api：只用 API key（`claude -p --bare`，完全不读订阅登录）。

API key 来源，按顺序：环境变量 DEJA_API_KEY → ~/.deja-repo/api.key → 环境变量 ANTHROPIC_API_KEY。
Base URL（兼容 Anthropic 接口的代理）只在走 API key 时生效：环境变量 DEJA_BASE_URL > 页面设置。
"""
import json
import os
import urllib.error
import subprocess
import threading
import time

from . import config

MODES = ("auto", "subscription", "api")
KEY_FILE = config.DATA_DIR / "api.key"
STATE_FILE = config.DATA_DIR / "auth.json"
FALLBACK_SECONDS = 30 * 60     # 订阅撞限后，这么久之内直接走 API
LIMIT_HINTS = ("usage limit", "limit reached", "rate limit", "rate_limit", "429", "quota", "credit balance",
               "not logged in", "/login", "invalid api key", "authentication", "oauth")

_lock = threading.Lock()


def _state():
    try:
        return json.loads(STATE_FILE.read_text())
    except (OSError, ValueError):
        return {}


def _save_state(**kw):
    with _lock:
        st = {**_state(), **kw}
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(st))


def mode():
    m = os.environ.get("DEJA_AUTH") or _state().get("mode") or "auto"
    return m if m in MODES else "auto"


def set_mode(m):
    _save_state(mode=m)


def base_url():
    return (os.environ.get("DEJA_BASE_URL") or _state().get("base_url") or "").strip().rstrip("/")


def normalize_base_url(url):
    """claude 会自己在后面拼 /v1/messages，所以去掉用户填的 /v1；没写协议就补 https://。"""
    u = (url or "").strip().rstrip("/")
    if not u:
        return ""
    if not u.startswith(("http://", "https://")):
        u = "https://" + u
    for tail in ("/v1/messages", "/v1"):
        if u.endswith(tail):
            u = u[: -len(tail)]
    return u


def set_base_url(url):
    _save_state(base_url=normalize_base_url(url))


def list_models():
    """问 Base URL（没填就是官方）有哪些模型，用的是已保存的 API key。"""
    import urllib.request
    key = api_key()
    if not key:
        raise ValueError("先填 API key 再拉取模型")
    req = urllib.request.Request((base_url() or "https://api.anthropic.com") + "/v1/models?limit=200", headers={
        "x-api-key": key, "Authorization": f"Bearer {key}", "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise ValueError(f"拉取失败：HTTP {e.code} {e.read()[:200].decode(errors='ignore')}")
    rows = d.get("data") or d.get("models") or []
    return sorted({(x.get("id") or x.get("name")) for x in rows if isinstance(x, dict) and (x.get("id") or x.get("name"))})


def display_name(m):
    """有的中转站把别家模型伪装成 claude-xxx-dd-<倒序真名>，例如 claude-fable-5-dd-los-6-tpg = gpt-6-sol。还原给人看。"""
    if "-dd-" in m:
        real = m.split("-dd-", 1)[1][::-1]
        if real.startswith(("gpt", "codex", "o1", "o3", "o4", "gemini", "grok", "deepseek", "qwen", "kimi", "glm")):
            return real
    return m


def api_key():
    k = os.environ.get("DEJA_API_KEY")
    if not k:
        try:
            k = KEY_FILE.read_text().strip()
        except OSError:
            k = ""
    return k or os.environ.get("ANTHROPIC_API_KEY", "")


def save_key(key):
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    KEY_FILE.touch(mode=0o600)
    os.chmod(KEY_FILE, 0o600)
    KEY_FILE.write_text(key.strip() + "\n")


def clear_key():
    KEY_FILE.unlink(missing_ok=True)


def masked():
    k = api_key()
    return f"…{k[-4:]}" if k else ""


def _plan():
    m = mode()
    if m == "subscription":
        return ["subscription"]
    if m == "api":
        return ["api"]
    if not api_key():
        return ["subscription"]
    if _state().get("fallback_until", 0) > time.time():
        return ["api"]
    return ["subscription", "api"]


def _env(kind, extra):
    env = {**os.environ, **(extra or {})}
    if kind == "subscription":
        for k in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
            env.pop(k, None)
    else:
        env["ANTHROPIC_API_KEY"] = api_key()
        env.pop("ANTHROPIC_AUTH_TOKEN", None)
        if base_url():
            env["ANTHROPIC_BASE_URL"] = base_url()
        else:
            env.pop("ANTHROPIC_BASE_URL", None)
    return env


def _limited(r):
    """订阅这次没跑成，是不是因为额度/登录问题（值得换 API 再试）。"""
    text = (r.stdout or "") + (r.stderr or "")
    try:
        d = json.loads(r.stdout)
        if not d.get("is_error") and d.get("structured_output") is not None:
            return False
        text = json.dumps(d)
    except ValueError:
        pass
    low = text.lower()
    return any(h in low for h in LIMIT_HINTS)


def _add_api_cost(r):
    try:
        cost = float(json.loads(r.stdout).get("total_cost_usd") or 0)
    except (ValueError, AttributeError):
        return
    if cost:
        with _lock:
            st = _state()
            st["api_cost"] = round(st.get("api_cost", 0) + cost, 6)
            STATE_FILE.write_text(json.dumps(st))


def run(cmd, env=None, **kw):
    """像 subprocess.run 一样跑一次 `claude -p ...`，按模式选额度。返回 (结果, "subscription"|"api")。"""
    plan = _plan()
    m = cmd[cmd.index("--model") + 1] if "--model" in cmd else ""
    if m and not config.native(m):      # 中转站才有的模型（如 GPT），订阅跑不了
        if not api_key():
            raise RuntimeError(f"模型 {m} 只能通过 API 中转调用，先在设置里填 API key 和 Base URL")
        plan = ["api"]
    r = None
    for i, kind in enumerate(plan):
        c = list(cmd)
        if kind == "api":
            c.insert(c.index("-p") + 1, "--bare")    # 只认 API key，不读订阅登录
        r = subprocess.run(c, env=_env(kind, env), **kw)
        if kind == "api":
            _add_api_cost(r)
            return r, kind
        if i + 1 < len(plan) and _limited(r):
            _save_state(fallback_until=time.time() + FALLBACK_SECONDS)
            continue
        return r, kind
    return r, plan[-1]


def info():
    """给页面用：不返回 key 本身。"""
    st = _state()
    return {"mode": mode(), "base_url": base_url(), "key_set": bool(api_key()), "key_masked": masked(),
            "key_source": "env" if os.environ.get("DEJA_API_KEY") else ("file" if KEY_FILE.exists() else
                          ("ANTHROPIC_API_KEY" if os.environ.get("ANTHROPIC_API_KEY") else "")),
            "api_cost": st.get("api_cost", 0),
            "fallback_min": max(0, int((st.get("fallback_until", 0) - time.time()) / 60))}


def status():
    st = _state()
    desc = {"auto": "先用订阅，额度用完自动换 API key", "subscription": "只用 Claude 订阅", "api": "只用 API key，按量付费"}
    lines = [f"额度模式：{mode()}（{desc[mode()]}）",
             f"API key：{'已设置 ' + masked() if api_key() else '未设置'}"
             + (f"，Base URL {base_url()}" if base_url() else "")]
    if st.get("fallback_until", 0) > time.time():
        lines.append(f"订阅刚撞限，{int((st['fallback_until'] - time.time()) / 60)} 分钟内走 API")
    if st.get("api_cost"):
        lines.append(f"API 实际花费累计 ${st['api_cost']:.2f}")
    return "\n".join(lines)
