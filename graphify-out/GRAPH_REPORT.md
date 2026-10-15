# Graph Report - .  (2026-10-16)

## Corpus Check
- Corpus is ~20,921 words - fits in a single context window. You may not need a graph.

## Summary
- 367 nodes · 668 edges · 19 communities (18 shown, 1 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 26 edges (avg confidence: 0.88)
- Token cost: 140,477 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_页面渲染（报告与深挖卡片）|页面渲染（报告与深挖卡片）]]
- [[_COMMUNITY_代码侦察 agent 与配置|代码侦察 agent 与配置]]
- [[_COMMUNITY_深挖：上下文与报价|深挖：上下文与报价]]
- [[_COMMUNITY_额度与 API key 认证|额度与 API key 认证]]
- [[_COMMUNITY_页面交互与本机 API 调用|页面交互与本机 API 调用]]
- [[_COMMUNITY_GitHub 搜索与对照核实|GitHub 搜索与对照核实]]
- [[_COMMUNITY_包仓库与论文来源|包仓库与论文来源]]
- [[_COMMUNITY_命令行入口与意图闸门|命令行入口与意图闸门]]
- [[_COMMUNITY_本机页面服务（HTTP）|本机页面服务（HTTP）]]
- [[_COMMUNITY_AgentsView 会话与页面构建|AgentsView 会话与页面构建]]
- [[_COMMUNITY_SQLite 报告存储|SQLite 报告存储]]
- [[_COMMUNITY_旧版会话文件监听|旧版会话文件监听]]
- [[_COMMUNITY_报告 Markdown 与措辞守卫|报告 Markdown 与措辞守卫]]
- [[_COMMUNITY_只读代码工具（MCP）|只读代码工具（MCP）]]
- [[_COMMUNITY_候选排序与新鲜度|候选排序与新鲜度]]
- [[_COMMUNITY_项目依赖与风险|项目依赖与风险]]
- [[_COMMUNITY_明暗主题样式|明暗主题样式]]

## God Nodes (most connected - your core abstractions)
1. `ask()` - 14 edges
2. `q()` - 13 edges
3. `taskCard()` - 12 edges
4. `run()` - 11 edges
5. `deepBody()` - 11 edges
6. `render()` - 11 edges
7. `api()` - 11 edges
8. `giants CLI entry command` - 10 edges
9. `reportBody()` - 10 edges
10. `Document click event dispatcher (data-* actions)` - 10 edges

## Surprising Connections (you probably didn't know these)
- `External README/code/web content is untrusted data` --semantically_similar_to--> `safeUrl()`  [INFERRED] [semantically similar]
  SKILL.md → engine/deja/page.html
- `No 'does not exist' claims from partial searches` --semantically_similar_to--> `channelWarn()`  [INFERRED] [semantically similar]
  SKILL.md → engine/deja/page.html
- `giants collect command` --conceptually_related_to--> `renderTasks()`  [AMBIGUOUS]
  SKILL.md → engine/deja/page.html
- `giants page command` --conceptually_related_to--> `render()`  [INFERRED]
  SKILL.md → engine/deja/page.html
- `giants deep command (task deep-dive)` --conceptually_related_to--> `loadPlan()`  [INFERRED]
  SKILL.md → engine/deja/page.html

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Page render pipeline (tasks/reports views)** — engine_deja_page_render, engine_deja_page_rendertasks, engine_deja_page_renderreports, engine_deja_page_taskcard, engine_deja_page_card, engine_deja_page_reportbody, engine_deja_page_deepbody, engine_deja_page_matchrow [EXTRACTED 1.00]
- **Local server API client actions (X-Radar-Token)** — engine_deja_page_api, engine_deja_page_settingsaction, engine_deja_page_opensettings, engine_deja_page_startdeep, engine_deja_page_polldeep, engine_deja_page_settodo, engine_deja_page_todoaction, engine_deja_page_opentodo, engine_deja_page_loadplan [EXTRACTED 1.00]
- **Deep-dive workflow: quote, run, poll, render** — skill_deep_command, engine_deja_page_loadplan, engine_deja_page_startdeep, engine_deja_page_polldeep, engine_deja_page_deepbody, skill_triz_method [INFERRED 0.85]

## Communities (19 total, 1 thin omitted)

### Community 0 - "页面渲染（报告与深挖卡片）"
Cohesion: 0.06
Nodes (49): ago(), card(), channelWarn(), cmd(), codeBlock(), DATA (embedded JSON payload), deepBody(), det() (+41 more)

### Community 1 - "代码侦察 agent 与配置"
Cohesion: 0.07
Nodes (35): analyze_project(), analyze_repo(), is_project(), 代码侦察 agent：真的去读候选仓库（和你当前项目）的代码，而不是只看 README。  每个 agent 是一次 `claude -p`：内置工具全部关掉，, 当前目录像不像一个代码项目（避免去扫家目录、下载目录）。, _run(), _item(), load() (+27 more)

### Community 2 - "深挖：上下文与报价"
Cohesion: 0.13
Nodes (22): _cwds(), _docs(), _estimate(), guess_root(), _lines(), plan(), _prev_deep(), _project_of() (+14 more)

### Community 3 - "额度与 API key 认证"
Cohesion: 0.18
Nodes (22): _add_api_cost(), api_key(), base_url(), _env(), info(), _limited(), list_models(), masked() (+14 more)

### Community 4 - "页面交互与本机 API 调用"
Cohesion: 0.17
Nodes (22): api(), Document click event dispatcher (data-* actions), fetchModels(), loadPlan(), localSet(), openSettings(), openTodo(), pollDeep() (+14 more)

### Community 5 - "GitHub 搜索与对照核实"
Cohesion: 0.12
Nodes (21): _meta(), 返回 (仓库信息 | None, 记录)。404 才算"查无此仓库"；限流、网络错误只能算"没核实"。, 返回 (星数 ≥30 的结果, 记录)。记录里的 n 是 GitHub 原始返回条数，过滤之前的。, _search(), canary(), channel_status(), classify(), _gh() (+13 more)

### Community 6 - "包仓库与论文来源"
Cohesion: 0.16
Nodes (21): arxiv(), _brew_catalog(), crates(), extract_terms(), _get(), hackernews(), homebrew(), huggingface() (+13 more)

### Community 7 - "命令行入口与意图闸门"
Cohesion: 0.10
Nodes (10): 第一道闸：正则粗筛，免得每条消息都去调模型。宁可放进来，交给 Haiku 再判。, _caller_path(), cmd_annotate(), cmd_auth(), cmd_collect(), cmd_scan(), 巨人的肩膀（技能版）命令行：python3 -m deja <status|collect|scan|recent|show|page>  会话数据来自本机运行, 给旧报告里的每个候选补一句中文"它是做什么的"（Haiku，很便宜）。 (+2 more)

### Community 8 - "本机页面服务（HTTP）"
Cohesion: 0.18
Nodes (11): BaseHTTPRequestHandler, alive(), Handler, launch(), 本机小服务：打开就是最新的雷达页面，页面里能改模型 / Base URL / API key，能对一个任务点"深挖"。  只监听 127.0.0.1。所有 /a, 在终端里开一个 Claude Code 会话做这个卡点：写一个 .command 文件再 open（不需要 AppleScript 权限）。, serve(), settings() (+3 more)

### Community 9 - "AgentsView 会话与页面构建"
Cohesion: 0.15
Nodes (16): alive(), _get(), 从本机 AgentsView 的 HTTP API 读会话和用户消息（只读）。  AgentsView 负责解析 Claude Code、Codex 等 20, 最近活跃的人类会话（不含子代理/自动化会话）。, sessions(), Unavailable, user_prompts(), build() (+8 more)

### Community 10 - "SQLite 报告存储"
Cohesion: 0.21
Nodes (17): add_also_in(), add_report(), conn(), find_duplicate(), get_meta(), get_offsets(), get_report(), list_reports() (+9 more)

### Community 11 - "旧版会话文件监听"
Cohesion: 0.19
Nodes (11): _codex_ctx(), list_files(), normalize(), parse_claude(), parse_codex(), 增量读取 Claude Code / Codex 的会话 jsonl，吐出"用户亲手打的消息"。, Codex 的 cwd/session 只写在第一行，续读时要补回来。, 每次 poll() 返回自上次以来新出现的用户消息。 (+3 more)

### Community 12 - "报告 Markdown 与措辞守卫"
Cohesion: 0.20
Nodes (12): _blob(), _code_md(), deep_md(), 把一份报告压成 Markdown：给 Claude 读（工具结果、提示词上下文），也给面板显示。, 代码侦察结论（缩进在某个 match 下面）。, to_md(), claims_absence(), data_headline() (+4 more)

### Community 13 - "只读代码工具（MCP）"
Cohesion: 0.36
Nodes (12): handle(), _is_text(), main(), 代码侦察 agent 的工具箱：一个只读、锁在根目录里的 MCP 服务（stdio，纯标准库）。  agent 只能用这里的 5 个工具看代码：stats /, _rel(), _safe(), t_find(), t_grep() (+4 more)

### Community 14 - "候选排序与新鲜度"
Cohesion: 0.23
Nodes (11): age_days(), annotate(), bm25(), pick(), 统一排序 + 新鲜度。  patent 用本地向量（fastembed）算相似度；这里坚持纯标准库，用 BM25 做词法相关度， 再交给模型核验时补上语义判断。, 极简英文词干：videos→video、subtitles→subtitle、generates/generated→generat、libraries→lib, 返回每个文档 0–1 的相关度（按最大值归一）。, 给每条候选加 sim / stale，并按 相关度 + 人气 排序。 (+3 more)

### Community 15 - "项目依赖与风险"
Cohesion: 0.40
Nodes (4): project_deps(), 本地上下文：当前项目已经装了哪些依赖（思路来自 search-before-building：先看项目和已装依赖，再往外找）， 以及外部仓库安装说明里的风险信号, 返回 {清单文件: [依赖名]}。cwd 不存在或没有清单就是空。, _read()

## Ambiguous Edges - Review These
- `giants collect command` → `renderTasks()`  [AMBIGUOUS]
  SKILL.md · relation: conceptually_related_to

## Knowledge Gaps
- **4 isolated node(s):** `giants recent command`, `giants annotate command`, `giants show command`, `Light/dark CSS theme tokens`
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `giants collect command` and `renderTasks()`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `ask()` connect `代码侦察 agent 与配置` to `本机页面服务（HTTP）`, `深挖：上下文与报价`, `命令行入口与意图闸门`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `deepBody()` (e.g. with `giants deep command (task deep-dive)` and `TRIZ contradiction analysis for deep-dive blockers`) actually correct?**
  _`deepBody()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `巨人的肩膀（原 Déjà Repo / 轮子雷达）：盯着 Claude / Codex 会话，自动查 GitHub 上有没有现成轮子。`, `巨人的肩膀（技能版）命令行：python3 -m deja <status|collect|scan|recent|show|page>  会话数据来自本机运行`, `从 AgentsView 取最近的用户消息，挑出"要造新东西"的去扫描。` to the rest of the system?**
  _74 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `页面渲染（报告与深挖卡片）` be split into smaller, more focused modules?**
  _Cohesion score 0.0641025641025641 - nodes in this community are weakly interconnected._
- **Should `代码侦察 agent 与配置` be split into smaller, more focused modules?**
  _Cohesion score 0.06823529411764706 - nodes in this community are weakly interconnected._
- **Should `深挖：上下文与报价` be split into smaller, more focused modules?**
  _Cohesion score 0.12615384615384614 - nodes in this community are weakly interconnected._