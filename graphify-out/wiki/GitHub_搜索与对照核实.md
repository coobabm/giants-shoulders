# GitHub 搜索与对照核实

> 23 nodes

## Key Concepts

- **github.py** (17 connections) — `engine/deja/github.py`
- **_gh()** (9 connections) — `engine/deja/github.py`
- **log_entry()** (6 connections) — `engine/deja/github.py`
- **canary()** (6 connections) — `engine/deja/github.py`
- **_meta()** (4 connections) — `engine/deja/deep.py`
- **_search()** (4 connections) — `engine/deja/deep.py`
- **channel_status()** (4 connections) — `engine/deja/github.py`
- **repo_meta()** (4 connections) — `engine/deja/github.py`
- **narrowed()** (4 connections) — `engine/deja/registries.py`
- **classify()** (3 connections) — `engine/deja/github.py`
- **search()** (3 connections) — `engine/deja/github.py`
- **scan()** (3 connections) — `engine/deja/github.py`
- **_tokens()** (2 connections) — `engine/deja/github.py`
- **readme()** (2 connections) — `engine/deja/github.py`
- **readmes()** (2 connections) — `engine/deja/github.py`
- **RuntimeError** (2 connections)
- **返回 (仓库信息 | None, 记录)。404 才算"查无此仓库"；限流、网络错误只能算"没核实"。** (1 connections) — `engine/deja/deep.py`
- **返回 (星数 ≥30 的结果, 记录)。记录里的 n 是 GitHub 原始返回条数，过滤之前的。** (1 connections) — `engine/deja/deep.py`
- **用 gh CLI 搜 GitHub：名字/描述 + README 两路，多关键词并发，去重打分。** (1 connections) — `engine/deja/github.py`
- **rate_limit = 等一会儿重跑就行；source_error = 要排查（没登录、网络、gh 坏了）。两者处理方式相反，不能混。** (1 connections) — `engine/deja/github.py`
- **正式搜之前先搜一个肯定能搜到的仓库。搜不到说明是通道坏了，不是"这个领域没东西"。** (1 connections) — `engine/deja/github.py`
- **ok：对照通过且没出错；degraded：对照通过但有查询出错；blind：对照没通过，搜不到不代表没有。** (1 connections) — `engine/deja/github.py`
- **把全网搜索里出现的 GitHub 链接补成和 scan() 一样的结构。** (1 connections) — `engine/deja/github.py`

## Relationships

- [代码侦察 agent 与配置](%E4%BB%A3%E7%A0%81%E4%BE%A6%E5%AF%9F_agent_%E4%B8%8E%E9%85%8D%E7%BD%AE.md) (8 shared connections)
- [深挖：上下文与报价](%E6%B7%B1%E6%8C%96%EF%BC%9A%E4%B8%8A%E4%B8%8B%E6%96%87%E4%B8%8E%E6%8A%A5%E4%BB%B7.md) (6 shared connections)
- [包仓库与论文来源](%E5%8C%85%E4%BB%93%E5%BA%93%E4%B8%8E%E8%AE%BA%E6%96%87%E6%9D%A5%E6%BA%90.md) (2 shared connections)

## Source Files

- `engine/deja/deep.py`
- `engine/deja/github.py`
- `engine/deja/registries.py`

## Audit Trail

- EXTRACTED: 80 (98%)
- INFERRED: 2 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*