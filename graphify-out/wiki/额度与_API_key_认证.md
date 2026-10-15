# 额度与 API key 认证

> 25 nodes

## Key Concepts

- **auth.py** (26 connections) — `engine/deja/auth.py`
- **run()** (9 connections) — `engine/deja/auth.py`
- **_state()** (8 connections) — `engine/deja/auth.py`
- **status()** (8 connections) — `engine/deja/auth.py`
- **base_url()** (7 connections) — `engine/deja/auth.py`
- **api_key()** (7 connections) — `engine/deja/auth.py`
- **info()** (7 connections) — `engine/deja/auth.py`
- **mode()** (6 connections) — `engine/deja/auth.py`
- **_save_state()** (5 connections) — `engine/deja/auth.py`
- **list_models()** (5 connections) — `engine/deja/auth.py`
- **_plan()** (5 connections) — `engine/deja/auth.py`
- **set_mode()** (4 connections) — `engine/deja/auth.py`
- **set_base_url()** (4 connections) — `engine/deja/auth.py`
- **masked()** (4 connections) — `engine/deja/auth.py`
- **_env()** (4 connections) — `engine/deja/auth.py`
- **normalize_base_url()** (3 connections) — `engine/deja/auth.py`
- **save_key()** (3 connections) — `engine/deja/auth.py`
- **clear_key()** (3 connections) — `engine/deja/auth.py`
- **_limited()** (3 connections) — `engine/deja/auth.py`
- **_add_api_cost()** (3 connections) — `engine/deja/auth.py`
- **模型调用走哪份额度：Claude 订阅（claude.ai 登录）还是 Anthropic API key。  模式（`radar auth --mode` 设** (1 connections) — `engine/deja/auth.py`
- **claude 会自己在后面拼 /v1/messages，所以去掉用户填的 /v1；没写协议就补 https://。** (1 connections) — `engine/deja/auth.py`
- **问 Base URL（没填就是官方）有哪些模型，用的是已保存的 API key。** (1 connections) — `engine/deja/auth.py`
- **订阅这次没跑成，是不是因为额度/登录问题（值得换 API 再试）。** (1 connections) — `engine/deja/auth.py`
- **像 subprocess.run 一样跑一次 `claude -p ...`，按模式选额度。返回 (结果, "subscription"|"api")。** (1 connections) — `engine/deja/auth.py`

## Relationships

- [本机页面服务（HTTP）](%E6%9C%AC%E6%9C%BA%E9%A1%B5%E9%9D%A2%E6%9C%8D%E5%8A%A1%EF%BC%88HTTP%EF%BC%89.md) (9 shared connections)
- [代码侦察 agent 与配置](%E4%BB%A3%E7%A0%81%E4%BE%A6%E5%AF%9F_agent_%E4%B8%8E%E9%85%8D%E7%BD%AE.md) (6 shared connections)
- [命令行入口与意图闸门](%E5%91%BD%E4%BB%A4%E8%A1%8C%E5%85%A5%E5%8F%A3%E4%B8%8E%E6%84%8F%E5%9B%BE%E9%97%B8%E9%97%A8.md) (6 shared connections)

## Source Files

- `engine/deja/auth.py`

## Audit Trail

- EXTRACTED: 129 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*