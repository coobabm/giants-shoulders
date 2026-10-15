"""把雷达报告和 AgentsView 里的会话渲染成一个自带数据的 HTML 页面（不需要服务器，直接用浏览器打开）。"""
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import sys

from . import agentsview, config, group, sources, store

TEMPLATE = Path(__file__).with_name("page.html")
PROMPT_SESSIONS = 400    # 最多给这么多个会话取用户消息（本机 API，很快）
PROMPT_CHARS = 600
NUMBERED = re.compile(r"\s*[（(][一二三四五六七八九十\d]+[)）]\s*$")

SESSION_FIELDS = ("id", "agent", "project", "cwd", "display_name", "first_message", "started_at", "ended_at",
                  "message_count", "user_message_count")


def _slim(r):
    """去掉页面用不到的大字段。"""
    d = dict(r.get("data") or {})
    for k in ("candidates", "deps", "search", "others", "topics"):
        d.pop(k, None)
    return {**{k: r.get(k) for k in ("id", "created", "updated", "source", "session", "cwd", "message", "msg_ts", "status",
                                     "summary", "verdict", "cost", "error", "also_in", "pinned")}, "data": d}


def _iso_ts(iso):
    return agentsview.ts(iso) if iso else 0


def _native(sid):
    return sid.split(":", 1)[1] if ":" in sid else sid


def _dedupe(reports):
    """同一句需求扫过好几次时只留最新的一份，旧的记在 repeats 里。返回 (保留的, 旧 id → 新 id)。"""
    keep, alias, seen = [], {}, {}
    for r in reports:            # list_reports 按 id 倒序，先遇到的是最新的
        d = r["data"]
        if d.get("title"):
            d["title"] = NUMBERED.sub("", d["title"])
        if r["status"] != "done":
            keep.append(r)
            continue
        k = sources.normalize(r["message"])
        if k in seen:
            first = seen[k]
            first.setdefault("repeats", []).append(r["id"])
            alias[r["id"]] = first["id"]
            continue
        seen[k] = r
        keep.append(r)
    return keep, alias


def build(days=30, regroup=False, grouping=True, server=None):
    """server 给了（本机服务在用）就只返回 HTML 字符串，不写文件；否则写 radar.html 返回路径。"""
    reports, alias = _dedupe([_slim(r) for r in store.list_reports(include_skipped=False, limit=400)])
    alive = agentsview.alive()
    sessions = []
    if alive:
        raw = agentsview.sessions(hours=days * 24, limit=500)
        sessions = [{k: s.get(k) for k in SESSION_FIELDS} for s in raw]

        def prompts(s):
            try:
                return [{**p, "text": p["text"][:PROMPT_CHARS]} for p in agentsview.user_prompts(s["id"])][-40:]
            except agentsview.Unavailable:
                return []
        with ThreadPoolExecutor(max_workers=8) as ex:
            for s, ps in zip(sessions[:PROMPT_SESSIONS], ex.map(prompts, sessions[:PROMPT_SESSIONS])):
                s["prompts"] = ps

    # 报告挂到会话上：AgentsView 的 ID 可能带 "codex:" 前缀，雷达早期记的是原生 ID
    index = {}
    for s in sessions:
        index[s["id"]] = s["id"]
        index.setdefault(_native(s["id"]), s["id"])
        s["reports"] = []
    by_id = {}
    for r in reports:
        by_id[r["id"]] = r
        sid = index.get(r["session"] or "")
        if sid:
            next(s for s in sessions if s["id"] == sid)["reports"].append(r["id"])
    for old, new in alias.items():   # 旧报告挂过的会话改挂到最新那份
        sid = index.get(store.get_report(old)["session"] or "")
        if sid:
            lst = next(s for s in sessions if s["id"] == sid)["reports"]
            if new not in lst:
                lst.append(new)
    # 只有 /login 之类命令、没有一句人话的会话不显示
    sessions = [s for s in sessions if s["reports"] or s.get("prompts", [None])]
    # 按最近活动排序
    sessions.sort(key=lambda s: (s.get("ended_at") or s.get("started_at") or ""), reverse=True)

    # 相似的会话归成任务（结果缓存，只为新会话花钱）
    by_sid = {s["id"]: s for s in sessions}
    orphans = [r for r in reports if r["status"] == "done" and not index.get(r["session"] or "")]
    tasks = []
    if grouping:
        if regroup:
            group.reset()
        try:
            gstate, cost = group.update(sessions, orphans)
            if cost:
                print(f"归类新会话花费 ${cost:.3f}", file=sys.stderr)
        except Exception as e:   # 归类失败不影响页面，只是没有"任务"视图
            print(f"归类失败：{e}", file=sys.stderr)
            gstate = group.load()
        members = {}
        for key, gid in gstate["assign"].items():
            members.setdefault(gid, []).append(key)
        meta = {g["id"]: g for g in gstate["groups"]}
        meta["misc"] = {"id": "misc", "name": "零碎会话", "summary": "登录、闲聊、一次性小问题。"}
        for gid, keys in members.items():
            ss = [by_sid[k[2:]] for k in keys if k.startswith("s:") and k[2:] in by_sid]
            rids = [alias.get(int(k[2:]), int(k[2:])) for k in keys if k.startswith("r:")]
            rids = [r for r in rids if r in by_id]
            rids += [rid for x in ss for rid in x["reports"]]
            if not ss and not rids:
                continue
            last = max([x.get("ended_at") or x.get("started_at") or "" for x in ss] or [""])
            last_ts = max([_iso_ts(last)] + [by_id[r]["created"] or 0 for r in rids])
            tasks.append({**meta.get(gid, {"id": gid, "name": gid, "summary": ""}),
                          "sessions": [x["id"] for x in ss], "reports": sorted(set(rids), reverse=True),
                          "last": last_ts})
        tasks.sort(key=lambda t: (t["id"] == "misc", -t["last"]))

    data = {
        "generated": time.time(),
        "agentsview": alive,
        "agentsviewUrl": config.AGENTSVIEW if alive else "",
        "stats": store.stats(),
        "reports": reports,
        "reportById": by_id,
        "sessions": sessions,
        "tasks": tasks,
        "sessionById": by_sid,
        "sessionIndex": {k: v for k, v in index.items()},
        "server": server,
    }
    tpl = TEMPLATE.read_text()

    def render(d):
        return tpl.replace("__DATA__", json.dumps(d, ensure_ascii=False).replace("</", "<\\/"))
    # 静态文件每次都同步更新（不带 token），免得开着的旧文件标签页落后
    config.PAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    config.PAGE_PATH.write_text(render({**data, "server": None}))
    return render(data) if server else config.PAGE_PATH
