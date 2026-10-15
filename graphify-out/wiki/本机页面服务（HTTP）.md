# 本机页面服务（HTTP）

> 20 nodes

## Key Concepts

- **server.py** (19 connections) — `engine/deja/server.py`
- **.do_POST()** (18 connections) — `engine/deja/server.py`
- **.do_GET()** (13 connections) — `engine/deja/server.py`
- **Handler** (9 connections) — `engine/deja/server.py`
- **settings()** (6 connections) — `engine/deja/server.py`
- **start_deep()** (5 connections) — `engine/deja/server.py`
- **._auth_ok()** (5 connections) — `engine/deja/server.py`
- **token()** (4 connections) — `engine/deja/server.py`
- **url()** (4 connections) — `engine/deja/server.py`
- **launch()** (4 connections) — `engine/deja/server.py`
- **serve()** (4 connections) — `engine/deja/server.py`
- **alive()** (3 connections) — `engine/deja/server.py`
- **._host_ok()** (3 connections) — `engine/deja/server.py`
- **._send()** (3 connections) — `engine/deja/server.py`
- **_deep()** (2 connections) — `engine/deja/server.py`
- **._json()** (2 connections) — `engine/deja/server.py`
- **BaseHTTPRequestHandler** (1 connections)
- **.log_message()** (1 connections) — `engine/deja/server.py`
- **本机小服务：打开就是最新的雷达页面，页面里能改模型 / Base URL / API key，能对一个任务点"深挖"。  只监听 127.0.0.1。所有 /a** (1 connections) — `engine/deja/server.py`
- **在终端里开一个 Claude Code 会话做这个卡点：写一个 .command 文件再 open（不需要 AppleScript 权限）。** (1 connections) — `engine/deja/server.py`

## Relationships

- [代码侦察 agent 与配置](%E4%BB%A3%E7%A0%81%E4%BE%A6%E5%AF%9F_agent_%E4%B8%8E%E9%85%8D%E7%BD%AE.md) (13 shared connections)
- [额度与 API key 认证](%E9%A2%9D%E5%BA%A6%E4%B8%8E_API_key_%E8%AE%A4%E8%AF%81.md) (9 shared connections)
- [深挖：上下文与报价](%E6%B7%B1%E6%8C%96%EF%BC%9A%E4%B8%8A%E4%B8%8B%E6%96%87%E4%B8%8E%E6%8A%A5%E4%BB%B7.md) (7 shared connections)
- [命令行入口与意图闸门](%E5%91%BD%E4%BB%A4%E8%A1%8C%E5%85%A5%E5%8F%A3%E4%B8%8E%E6%84%8F%E5%9B%BE%E9%97%B8%E9%97%A8.md) (4 shared connections)
- [SQLite 报告存储](SQLite_%E6%8A%A5%E5%91%8A%E5%AD%98%E5%82%A8.md) (3 shared connections)
- [AgentsView 会话与页面构建](AgentsView_%E4%BC%9A%E8%AF%9D%E4%B8%8E%E9%A1%B5%E9%9D%A2%E6%9E%84%E5%BB%BA.md) (2 shared connections)

## Source Files

- `engine/deja/server.py`

## Audit Trail

- EXTRACTED: 108 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*