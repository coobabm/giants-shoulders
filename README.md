# 🔭 巨人的肩膀 · Shoulders of Giants

一个 Claude Code 技能：动手造东西之前，先查网上是不是早有人造过，并让代码 agent 真去读候选仓库的源码。

- **扫描**：一句需求 → 搜 GitHub、npm / crates / Homebrew / VS Code、Hacker News、arXiv / Hugging Face、全网 → 按部件核验 → 克隆前 3 个 GitHub 候选读代码（入口、哪些文件实现了哪个部件、怎么复用、隐患）→ 顺便读你的项目找接入点。
- **深挖**：把你最近的 AI 会话（经 [AgentsView](https://github.com/kenn-io/agentsview)）归成任务，读懂任务卡在哪，用 TRIZ 矛盾找相邻领域可借鉴的项目，再在你的代码里核实。结果变成待办，「去做」一键在终端打开 Claude Code。
- **项目知识图谱**：查到过的所有 GitHub 项目之间、以及它们和你的任务 / 卡点之间的关系，给 agent 读（`giants kg`）。
- **本机页面**：`127.0.0.1:4848`，任务视图、查询报告、设置（额度模式、API key、Base URL、每个环节的模型）。
- **搜索可信度**：每次先跑对照搜索，通道坏了就不下"没有现成的"结论；每条查询都记录。

## 安装

```bash
git clone https://github.com/coobabm/giants-shoulders ~/.claude/skills/giants-shoulders
```

依赖：Python 3.10+（只用标准库）、[`gh`](https://cli.github.com/)（已登录）、[`claude`](https://docs.claude.com/en/docs/claude-code) CLI。可选：AgentsView（会话来源，深挖 / 页面任务视图需要）、[graphify](https://github.com/safishamsi/graphify)（知识图谱聚类）。

在 Claude Code 里说"做一个 X"或 `/giants-shoulders` 即可触发；也可以直接用命令：

```bash
~/.claude/skills/giants-shoulders/giants scan "做一个把 Markdown 转成离线单页 HTML 的 CLI"
~/.claude/skills/giants-shoulders/giants page
~/.claude/skills/giants-shoulders/giants deep g1
~/.claude/skills/giants-shoulders/giants kg query "存档"
```

完整命令表和花费见 [SKILL.md](SKILL.md)；改代码前读 [AGENT_MAP.md](AGENT_MAP.md)。

## 额度与隐私

- 模型调用走 `claude -p`：默认先用 Claude 订阅，撞限自动换 API key（`giants auth --set-key`，存在 `~/.deja-repo/api.key`，权限 600）。
- 所有数据在本机 `~/.deja-repo/`；本机服务只监听 127.0.0.1，接口要 token，永远不返回 key 本身。
- README、仓库代码、网页、会话内容都当不可信数据处理；代码 agent 只有只读工具，不运行仓库里的任何东西。

## 许可证

MIT，见 [LICENSE](LICENSE)。
