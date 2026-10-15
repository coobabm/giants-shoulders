# 代码侦察 agent 与配置

> 51 nodes

## Key Concepts

- **process()** (28 connections) — `engine/deja/pipeline.py`
- **pipeline.py** (26 connections) — `engine/deja/pipeline.py`
- **config.py** (20 connections) — `engine/deja/config.py`
- **__init__.py** (17 connections) — `engine/deja/__init__.py`
- **group.py** (15 connections) — `engine/deja/group.py`
- **ask()** (15 connections) — `engine/deja/llm.py`
- **codeagent.py** (12 connections) — `engine/deja/codeagent.py`
- **model()** (11 connections) — `engine/deja/config.py`
- **llm.py** (10 connections) — `engine/deja/llm.py`
- **load()** (9 connections) — `engine/deja/group.py`
- **update()** (9 connections) — `engine/deja/group.py`
- **local.py** (8 connections) — `engine/deja/local.py`
- **_run()** (7 connections) — `engine/deja/codeagent.py`
- **repocache.py** (7 connections) — `engine/deja/repocache.py`
- **save()** (6 connections) — `engine/deja/group.py`
- **LLMError** (6 connections) — `engine/deja/llm.py`
- **match()** (5 connections) — `engine/deja/local.py`
- **is_project()** (4 connections) — `engine/deja/codeagent.py`
- **setting()** (4 connections) — `engine/deja/config.py`
- **analyze_repo()** (3 connections) — `engine/deja/codeagent.py`
- **analyze_project()** (3 connections) — `engine/deja/codeagent.py`
- **reset()** (3 connections) — `engine/deja/group.py`
- **_frontmatter()** (3 connections) — `engine/deja/local.py`
- **skills()** (3 connections) — `engine/deja/local.py`
- **_deepdive_picks()** (3 connections) — `engine/deja/pipeline.py`
- *... and 26 more nodes in this community*

## Relationships

- [深挖：上下文与报价](%E6%B7%B1%E6%8C%96%EF%BC%9A%E4%B8%8A%E4%B8%8B%E6%96%87%E4%B8%8E%E6%8A%A5%E4%BB%B7.md) (20 shared connections)
- [本机页面服务（HTTP）](%E6%9C%AC%E6%9C%BA%E9%A1%B5%E9%9D%A2%E6%9C%8D%E5%8A%A1%EF%BC%88HTTP%EF%BC%89.md) (13 shared connections)
- [命令行入口与意图闸门](%E5%91%BD%E4%BB%A4%E8%A1%8C%E5%85%A5%E5%8F%A3%E4%B8%8E%E6%84%8F%E5%9B%BE%E9%97%B8%E9%97%A8.md) (10 shared connections)
- [SQLite 报告存储](SQLite_%E6%8A%A5%E5%91%8A%E5%AD%98%E5%82%A8.md) (9 shared connections)
- [AgentsView 会话与页面构建](AgentsView_%E4%BC%9A%E8%AF%9D%E4%B8%8E%E9%A1%B5%E9%9D%A2%E6%9E%84%E5%BB%BA.md) (8 shared connections)
- [GitHub 搜索与对照核实](GitHub_%E6%90%9C%E7%B4%A2%E4%B8%8E%E5%AF%B9%E7%85%A7%E6%A0%B8%E5%AE%9E.md) (8 shared connections)
- [额度与 API key 认证](%E9%A2%9D%E5%BA%A6%E4%B8%8E_API_key_%E8%AE%A4%E8%AF%81.md) (6 shared connections)
- [报告 Markdown 与措辞守卫](%E6%8A%A5%E5%91%8A_Markdown_%E4%B8%8E%E6%8E%AA%E8%BE%9E%E5%AE%88%E5%8D%AB.md) (5 shared connections)
- [包仓库与论文来源](%E5%8C%85%E4%BB%93%E5%BA%93%E4%B8%8E%E8%AE%BA%E6%96%87%E6%9D%A5%E6%BA%90.md) (4 shared connections)
- [候选排序与新鲜度](%E5%80%99%E9%80%89%E6%8E%92%E5%BA%8F%E4%B8%8E%E6%96%B0%E9%B2%9C%E5%BA%A6.md) (3 shared connections)
- [旧版会话文件监听](%E6%97%A7%E7%89%88%E4%BC%9A%E8%AF%9D%E6%96%87%E4%BB%B6%E7%9B%91%E5%90%AC.md) (2 shared connections)
- [项目依赖与风险](%E9%A1%B9%E7%9B%AE%E4%BE%9D%E8%B5%96%E4%B8%8E%E9%A3%8E%E9%99%A9.md) (2 shared connections)

## Source Files

- `engine/deja/__init__.py`
- `engine/deja/codeagent.py`
- `engine/deja/config.py`
- `engine/deja/group.py`
- `engine/deja/llm.py`
- `engine/deja/local.py`
- `engine/deja/pipeline.py`
- `engine/deja/repocache.py`

## Audit Trail

- EXTRACTED: 280 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*