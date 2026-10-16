"""「这个项目还有什么可优化的」——给后台 agent 用的一条龙入口。

当前目录 → 找到 AgentsView 里对应的任务 → 先给免费结果（最近一次深挖 + 项目知识图谱）
→ 报告过期（之后又有新会话）且报价在自动上限内才跑增量深挖，否则只报价、等用户同意。
"""
import time
from pathlib import Path

from . import auth, config, deep, group, report_md, store

FRESH_NEW_PROMPTS = 3          # 上次深挖之后新说的话少于这么多，就算没过期


def _under(a, b):
    """a 在 b 里面（或相同）。"""
    try:
        Path(a).resolve().relative_to(Path(b).resolve())
        return True
    except (ValueError, OSError):
        return False


def _related(cwd, path):
    return bool(path) and (_under(cwd, path) or _under(path, cwd))


def find_task(cwd):
    """返回 (任务, 匹配依据) 或 (None, 原因)。先看已保存的项目目录和会话 cwd，再按会话里提到的路径推断。"""
    cwd = str(Path(cwd).expanduser().resolve())
    st = group.load()
    groups = [g for g in st["groups"] if g["id"] != "misc"]
    if not groups:
        return None, "还没有任务（先打开一次页面让会话归类：giants page）"
    scored = []
    for g in groups:
        if _related(cwd, g.get("root")):
            return g, f"任务的项目目录 {g['root']}"
        _, sids, _ = deep._task(g["id"])
        hits = sum(n for c, n in deep._cwds(sids).items() if _related(cwd, c) and Path(c).resolve() != Path.home())
        if hits:
            scored.append((hits, g))
    if scored:
        hits, g = max(scored, key=lambda t: t[0])
        return g, f"{hits} 个会话在这个目录下开的"
    for g in groups:                       # 会话在 A 目录开、代码在 B 目录：按会话里提到的路径推断
        _, sids, _ = deep._task(g["id"])
        root = deep.guess_root(deep._prompts(sids), deep._cwds(sids))
        if _related(cwd, root):
            deep.set_root(g["id"], root)   # 记住，下次直接命中
            return g, f"会话里提到的项目目录 {root}"
    return None, f"没有任务和 {cwd} 对得上（在这个目录里聊过的会话可能还没归类：打开一次 giants page）"


def _kg_card(gid):
    f = config.DATA_DIR / "kg" / "tasks" / f"{gid}.md"
    return f.read_text() if f.exists() else ""


def advise(cwd, run=None, auto_max=None):
    """run=None 按自动上限决定；True 强制跑（用户已同意）；False 只看免费结果。返回 Markdown。"""
    auto_max = float(config.setting("auto_deep_max") if auto_max is None else auto_max)
    g, why = find_task(cwd)
    if not g:
        return f"# 没找到对应的任务\n\n{why}\n"
    p = deep.plan(g["id"])
    head = [f"# 「{g['name']}」（任务 {g['id']}）", "",
            f"- 怎么对上的：{why}",
            f"- 项目目录：{p['root'] or '（没推断出来）'}",
            f"- 会话 {p['sessions']} 个，用户说过的话 {p['prompts']} 条"]
    prev = store.get_report(p["prev"]) if p.get("prev") else None
    if prev:
        age = (time.time() - prev["created"]) / 86400
        head.append(f"- 上次深挖：报告 #{prev['id']}，{age:.1f} 天前；之后新说了 {p['new_prompts']} 条")
    stale = not prev or p["new_prompts"] >= FRESH_NEW_PROMPTS
    quote = f"${p['est_low']}–{p['est_high']}（上限 ${p['budget']}，深挖模型 {auth.display_name(p['model'])}）"
    if stale and (run or (run is None and p["est_high"] <= auto_max)):
        head.append(f"- 已{'按你的同意' if run else f'自动（报价 ≤ 自动上限 ${auto_max}）'}跑了"
                    f"{'增量' if prev else '首次'}深挖，报价 {quote}")
        rid = deep.run(g["id"])
        r = store.get_report(rid)
        if r["status"] != "done":
            head.append(f"- 深挖没跑完：{r.get('error') or r['status']}")
            r = prev
        else:
            head.append(f"- 实际花费 ${r.get('cost') or 0:.2f}")
    else:
        r = prev
        if stale:
            head += ["", f"**需要用户同意才跑新深挖**：报价 {quote}，超过自动上限 ${auto_max}。"
                         f"同意后运行 `giants advise --cwd \"{cwd}\" --run`。"]
        else:
            head.append("- 报告还新（之后没怎么聊），直接用，没花钱")
    out = "\n".join(head) + "\n\n"
    if r:
        out += report_md.to_md(r, for_model=True) + "\n"
    else:
        out += "这个任务还没深挖过。\n"
    card = _kg_card(g["id"])
    if card:
        out += "\n---\n\n## 项目知识图谱里这个任务的卡片\n\n" + card
    return out
