# 报告 Markdown 与措辞守卫

> 14 nodes

## Key Concepts

- **to_md()** (8 connections) — `engine/deja/report_md.py`
- **report_md.py** (7 connections) — `engine/deja/report_md.py`
- **verdict.py** (7 connections) — `engine/deja/verdict.py`
- **_code_md()** (4 connections) — `engine/deja/report_md.py`
- **guard()** (4 connections) — `engine/deja/verdict.py`
- **floor_level()** (3 connections) — `engine/deja/verdict.py`
- **claims_absence()** (3 connections) — `engine/deja/verdict.py`
- **data_headline()** (3 connections) — `engine/deja/verdict.py`
- **_blob()** (2 connections) — `engine/deja/report_md.py`
- **deep_md()** (2 connections) — `engine/deja/report_md.py`
- **把一份报告压成 Markdown：给 Claude 读（工具结果、提示词上下文），也给面板显示。** (1 connections) — `engine/deja/report_md.py`
- **代码侦察结论（缩进在某个 match 下面）。** (1 connections) — `engine/deja/report_md.py`
- **领域饱和度 + 措辞守卫，移植自 r14dd/patent 的 src/verdict.rs（MIT OR Apache-2.0）。  两条规则原样保留：** (1 connections) — `engine/deja/verdict.py`
- **fits：整体覆盖型匹配的 fit 列表。** (1 connections) — `engine/deja/verdict.py`

## Relationships

- [命令行入口与意图闸门](%E5%91%BD%E4%BB%A4%E8%A1%8C%E5%85%A5%E5%8F%A3%E4%B8%8E%E6%84%8F%E5%9B%BE%E9%97%B8%E9%97%A8.md) (6 shared connections)
- [代码侦察 agent 与配置](%E4%BB%A3%E7%A0%81%E4%BE%A6%E5%AF%9F_agent_%E4%B8%8E%E9%85%8D%E7%BD%AE.md) (5 shared connections)

## Source Files

- `engine/deja/report_md.py`
- `engine/deja/verdict.py`

## Audit Trail

- EXTRACTED: 47 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*