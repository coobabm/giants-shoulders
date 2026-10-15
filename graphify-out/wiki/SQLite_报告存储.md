# SQLite 报告存储

> 18 nodes

## Key Concepts

- **store.py** (25 connections) — `engine/deja/store.py`
- **q()** (14 connections) — `engine/deja/store.py`
- **get_report()** (13 connections) — `engine/deja/store.py`
- **list_reports()** (8 connections) — `engine/deja/store.py`
- **update_report()** (7 connections) — `engine/deja/store.py`
- **set_meta()** (6 connections) — `engine/deja/store.py`
- **add_report()** (6 connections) — `engine/deja/store.py`
- **get_meta()** (5 connections) — `engine/deja/store.py`
- **set_offset()** (4 connections) — `engine/deja/store.py`
- **find_duplicate()** (4 connections) — `engine/deja/store.py`
- **stats()** (4 connections) — `engine/deja/store.py`
- **conn()** (3 connections) — `engine/deja/store.py`
- **get_offsets()** (3 connections) — `engine/deja/store.py`
- **add_also_in()** (3 connections) — `engine/deja/store.py`
- **recent_session_summaries()** (3 connections) — `engine/deja/store.py`
- **_row()** (3 connections) — `engine/deja/store.py`
- **SQLite 存储：文件读取进度、雷达报告。** (1 connections) — `engine/deja/store.py`
- **同一句话在时间窗口内已经出现过（比如同时发给 Claude 和 Codex）。** (1 connections) — `engine/deja/store.py`

## Relationships

- [命令行入口与意图闸门](%E5%91%BD%E4%BB%A4%E8%A1%8C%E5%85%A5%E5%8F%A3%E4%B8%8E%E6%84%8F%E5%9B%BE%E9%97%B8%E9%97%A8.md) (16 shared connections)
- [深挖：上下文与报价](%E6%B7%B1%E6%8C%96%EF%BC%9A%E4%B8%8A%E4%B8%8B%E6%96%87%E4%B8%8E%E6%8A%A5%E4%BB%B7.md) (11 shared connections)
- [代码侦察 agent 与配置](%E4%BB%A3%E7%A0%81%E4%BE%A6%E5%AF%9F_agent_%E4%B8%8E%E9%85%8D%E7%BD%AE.md) (9 shared connections)
- [旧版会话文件监听](%E6%97%A7%E7%89%88%E4%BC%9A%E8%AF%9D%E6%96%87%E4%BB%B6%E7%9B%91%E5%90%AC.md) (6 shared connections)
- [AgentsView 会话与页面构建](AgentsView_%E4%BC%9A%E8%AF%9D%E4%B8%8E%E9%A1%B5%E9%9D%A2%E6%9E%84%E5%BB%BA.md) (4 shared connections)
- [本机页面服务（HTTP）](%E6%9C%AC%E6%9C%BA%E9%A1%B5%E9%9D%A2%E6%9C%8D%E5%8A%A1%EF%BC%88HTTP%EF%BC%89.md) (3 shared connections)

## Source Files

- `engine/deja/store.py`

## Audit Trail

- EXTRACTED: 113 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*