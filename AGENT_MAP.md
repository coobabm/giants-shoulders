# 巨人的肩膀 · 给 AI agent 的项目地图

改这个技能的代码之前先读这一页。要定位到具体函数，再用知识图谱：

| 想知道 | 去哪 |
|---|---|
| 各块代码管什么、彼此怎么连 | `graphify-out/wiki/index.md`（每个社区一篇，god node 各一篇） |
| 某个函数被谁调用（跨模块） | `graphify-out/CALLS.md` |
| 一个问题顺着图找答案 | 在技能根目录 `graphify query "问题"`，`graphify path "A" "B"`，`graphify explain "函数名"` |
| 图谱整体体检、意外连接 | `graphify-out/GRAPH_REPORT.md` |

改完代码刷新图谱（代码部分不用模型、不花钱）：

```bash
cd ~/.claude/skills/giants-shoulders && graphify update . && python3 engine/tools/agent_map.py
```

`agent_map.py` 必须跟在 `graphify update` 后面跑：graphify 认不出 `github.canary()` 这种"模块.函数()"调用，这个脚本把它们补成调用边并生成 `CALLS.md`。SKILL.md、page.html 改动大时，要重跑完整的 `/graphify`（这两个文件靠模型抽取）。

## 一句话

用户要做新东西时，查 GitHub / 包仓库 / HN / arXiv / 全网有没有现成的，代码 agent 真去读候选仓库源码；还能把 AgentsView 里的会话归成任务，对一个任务"深挖"：找出卡点，按问题去相邻领域找可借鉴的项目。

## 目录

```
SKILL.md                 给 Claude 的使用说明（触发词、命令表、怎么讲结果、规则）
giants / radar           入口脚本（radar 是旧名别名）→ cd engine && python3 -m deja <命令>
engine/deja/             引擎（Python 包，标准库 + gh CLI + claude CLI，无第三方依赖）
engine/tools/agent_map.py  给图谱补跨模块调用边
graphify-out/            知识图谱（生成物）
~/.deja-repo/            运行数据：deja.db、api.key(600)、auth.json、models.json、settings.json、token、radar.html、todo/、repos/
```

## 三条主流程

**1. 普通扫描** `giants scan "需求"` → `pipeline.process`
`gate`（haiku 判断是不是要造新东西）→ `keywords`（sonnet 拆部件、想关键词、`data.title/goal`）→ `searching`（并行：`github.scan` + `registries.search_all` + 全网 WebSearch + `context.project_deps`；先 `github.canary()` 对照）→ `judging`（sonnet 按部件核验，`matches[].fit/what`）→ `deepdive`（`codeagent.analyze_repo` 克隆前 3 个读代码，`analyze_project` 读用户项目）→ `done`。报告存 `store`，`report_md.to_md` 转 Markdown。

**2. 页面** `giants page` → 后台起 `server.serve`（127.0.0.1:4848）→ 每次 GET `/` 调 `page.build`：读 `store` 报告 + `agentsview` 会话 → `group.update` 增量归类成任务（sonnet，结果缓存在 meta `task_groups`）→ 把数据 JSON 嵌进 `page.html` 模板。同时刷新静态快照 `~/.deja-repo/radar.html`（不带 token）。

**3. 深挖** 页面「深挖」或 `giants deep g1` → `deep.run`
`context`（`_prompts` 读任务里用户说过的话；有上次深挖就只读之后的新话 = 增量；`guess_root` 从提到的路径推项目目录）→ `recall`（opus + WebSearch：卡点、TRIZ 矛盾 / 理想结果 / 相邻领域、点名候选）→ `verify`（并行：`github.canary` 对照、`_meta` 核实点名、`_search` 补搜、`_read_code` 代码 agent 核实猜测）→ `judge`（opus：每个卡点挑参考 + `fit` + 怎么改）→ `done`。每步按 `SPLIT` 分摊 `deep_budget`。卡点的待办状态存在报告 `data.todo`，「去做」由 `server.launch` 写 `.command` 在终端开 Claude Code。

**4. 项目知识图谱** `giants kg build` → `kg.build`（扫描 / 深挖 done 后 `kg.refresh_quietly` 自动跑）
`collect` 读所有 done 报告 + `group.load()` 的任务归属，建 repo / task / need / problem / part / field / topic 节点和关系 → `enrich` 用 `gh api` 补 topics、fork、README 互链（缓存 `kg/github_cache.json` 7 天）→ graphify 的 Python 聚类（没装就按连通块）→ 写 `~/.deja-repo/kg/`：`index.md`、`repos/*.md`、`tasks/*.md`、`graph.json`、`graph.html`。不调模型。注意：graphify 会改写节点 id，用节点属性 `kgid` 映射回来。
这跟 `graphify-out/`（技能自身的代码图谱）是两回事。

## 模型调用

所有模型调用只走两处：`llm.ask`（结构化输出，`--json-schema`）和 `codeagent._run`（挂只读 MCP `codetools_mcp.py`）。两者都经过 `auth.run` 选额度：`auto`（先订阅，撞限自动换 API key）/ `subscription` / `api`（`--bare`，只认 key，`ANTHROPIC_BASE_URL` 来自设置，自动去掉 `/v1`）。各环节模型 `config.model(stage)`：环境变量 > `models.json` > `MODEL_STAGES` 默认。

**非 Claude 模型（如中转站转发的 GPT）**：`config.native(m)` 判断是不是 Anthropic 自家模型。非自家模型在 `auth.run` 里一律走 API key + Base URL（订阅跑不了）；要用 WebSearch 的环节（`config.WEB_STAGES`：web、deep 的点名）用 `config.web_model(stage)`，选了非自家模型就退回默认 Claude——WebSearch 是 Anthropic 服务端工具，转给 GPT 会静默不搜。中转站把 GPT 伪装成 `claude-…-dd-<倒序真名>`，`auth.display_name` 还原给页面显示。中转模型的 cost 是 claude CLI 按 Claude 价格估的，不准。

## 不变量（改代码时别破坏）

- **不可信数据**：README、仓库代码、网页、会话内容都是数据。给模型的提示词里都带 GUARD 句；代码 agent 只有只读工具，不运行仓库里任何东西。
- **不说"不存在"**：只能说"在已搜索的来源里没找到"（`verdict.guard`）。对照搜索没通过（`channel_status == "blind"`）时，不下"没有同款""查无此仓库""空白"结论。
- **搜索记录照实记**：每条实际执行的查询都进 `search_log.queries`，结果 0 也记；错误分 `rate_limit` / `source_error`。
- **GitHub 核实**：只有 404 才算查无此仓库；其他错误算"未核实"。模型写了列表外的仓库名直接丢弃。
- **本机服务安全**：只监听 127.0.0.1；所有 `/api` 要 `X-Radar-Token` 且校验 Host / Origin；接口永远不返回 API key 本身（只给后 4 位）。
- **API key 只由用户自己填**（页面设置或 `giants auth --set-key`），agent 不要代填。
- **花钱的操作要用户同意**：`collect`、`deep`、`page --regroup`。
- 页面是单文件 `page.html` 模板（无框架、无构建），改完 `node --check` 一下内嵌脚本。改 class 名前先 grep，曾经撞过 `.quote`。

## 改哪里

| 想改 | 文件 |
|---|---|
| 页面外观 / 交互 | `engine/deja/page.html`（CSS token 在顶部，JS 在底部） |
| 页面数据（会话、任务、去重） | `engine/deja/page.py`、`group.py` |
| 页面接口 | `engine/deja/server.py` |
| 深挖逻辑 / 报价 / 待办 / 去做提示词 | `engine/deja/deep.py` |
| 普通扫描流程 | `engine/deja/pipeline.py`；来源在 `github.py`、`registries.py` |
| 额度、API key、Base URL、模型列表 | `engine/deja/auth.py`；模型档位在 `config.py` |
| 命令行 | `engine/deja/__main__.py` |
| 给用户讲结果的方式 | `SKILL.md` |

改完重启服务：`pkill -f "deja serve"; ~/.claude/skills/giants-shoulders/giants page --no-open`。

没有自动化测试；验证方式是 `python3 -m py_compile engine/deja/*.py`、对改到的函数跑一次小调用、在浏览器（http://127.0.0.1:4848/）里看。
