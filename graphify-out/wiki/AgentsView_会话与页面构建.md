# AgentsView 会话与页面构建

> 19 nodes

## Key Concepts

- **build()** (17 connections) — `engine/deja/page.py`
- **page.py** (14 connections) — `engine/deja/page.py`
- **agentsview.py** (12 connections) — `engine/deja/agentsview.py`
- **_get()** (6 connections) — `engine/deja/agentsview.py`
- **sessions()** (5 connections) — `engine/deja/agentsview.py`
- **user_prompts()** (5 connections) — `engine/deja/agentsview.py`
- **ts()** (5 connections) — `engine/deja/agentsview.py`
- **alive()** (4 connections) — `engine/deja/agentsview.py`
- **_dedupe()** (4 connections) — `engine/deja/page.py`
- **Unavailable** (3 connections) — `engine/deja/agentsview.py`
- **_iso_ts()** (3 connections) — `engine/deja/page.py`
- **_slim()** (2 connections) — `engine/deja/page.py`
- **_native()** (2 connections) — `engine/deja/page.py`
- **Exception** (1 connections)
- **从本机 AgentsView 的 HTTP API 读会话和用户消息（只读）。  AgentsView 负责解析 Claude Code、Codex 等 20** (1 connections) — `engine/deja/agentsview.py`
- **最近活跃的人类会话（不含子代理/自动化会话）。** (1 connections) — `engine/deja/agentsview.py`
- **把雷达报告和 AgentsView 里的会话渲染成一个自带数据的 HTML 页面（不需要服务器，直接用浏览器打开）。** (1 connections) — `engine/deja/page.py`
- **同一句需求扫过好几次时只留最新的一份，旧的记在 repeats 里。返回 (保留的, 旧 id → 新 id)。** (1 connections) — `engine/deja/page.py`
- **server 给了（本机服务在用）就只返回 HTML 字符串，不写文件；否则写 radar.html 返回路径。** (1 connections) — `engine/deja/page.py`

## Relationships

- [代码侦察 agent 与配置](%E4%BB%A3%E7%A0%81%E4%BE%A6%E5%AF%9F_agent_%E4%B8%8E%E9%85%8D%E7%BD%AE.md) (8 shared connections)
- [命令行入口与意图闸门](%E5%91%BD%E4%BB%A4%E8%A1%8C%E5%85%A5%E5%8F%A3%E4%B8%8E%E6%84%8F%E5%9B%BE%E9%97%B8%E9%97%A8.md) (7 shared connections)
- [深挖：上下文与报价](%E6%B7%B1%E6%8C%96%EF%BC%9A%E4%B8%8A%E4%B8%8B%E6%96%87%E4%B8%8E%E6%8A%A5%E4%BB%B7.md) (5 shared connections)
- [SQLite 报告存储](SQLite_%E6%8A%A5%E5%91%8A%E5%AD%98%E5%82%A8.md) (4 shared connections)
- [旧版会话文件监听](%E6%97%A7%E7%89%88%E4%BC%9A%E8%AF%9D%E6%96%87%E4%BB%B6%E7%9B%91%E5%90%AC.md) (2 shared connections)
- [本机页面服务（HTTP）](%E6%9C%AC%E6%9C%BA%E9%A1%B5%E9%9D%A2%E6%9C%8D%E5%8A%A1%EF%BC%88HTTP%EF%BC%89.md) (2 shared connections)

## Source Files

- `engine/deja/agentsview.py`
- `engine/deja/page.py`

## Audit Trail

- EXTRACTED: 88 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*