# build()

> God node · 17 connections · `engine/deja/page.py`

**Community:** [AgentsView 会话与页面构建](AgentsView_%E4%BC%9A%E8%AF%9D%E4%B8%8E%E9%A1%B5%E9%9D%A2%E6%9E%84%E5%BB%BA.md)

## Connections by Relation

### calls
- [get_report()](get_report%28%29.md) `EXTRACTED`
- .do_GET() `EXTRACTED`
- update() `EXTRACTED`
- load() `EXTRACTED`
- list_reports() `EXTRACTED`
- sessions() `EXTRACTED`
- user_prompts() `EXTRACTED`
- _dedupe() `EXTRACTED`
- cmd_page() `EXTRACTED`
- alive() `EXTRACTED`
- stats() `EXTRACTED`
- _iso_ts() `EXTRACTED`
- reset() `EXTRACTED`
- _slim() `EXTRACTED`
- _native() `EXTRACTED`

### contains
- page.py `EXTRACTED`

### rationale_for
- server 给了（本机服务在用）就只返回 HTML 字符串，不写文件；否则写 radar.html 返回路径。 `EXTRACTED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*