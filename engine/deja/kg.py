"""项目知识图谱：查到过的 GitHub 项目之间、以及它们和你的任务 / 卡点 / 需求之间的关系。给 AI agent 读。

节点
  repo     GitHub 仓库（星数、许可证、更新、语言、topics、一句话"做什么"）
  task     你的任务（会话归类出来的，如"灵光 Unity 游戏开发"）
  need     一次需求扫描（"做一个 Markdown 转离线 HTML 的 CLI"）
  problem  深挖出的卡点（带 TRIZ 矛盾）
  part     需求拆出来的部件（"Markdown 解析渲染"）
  field    TRIZ 相邻领域（"增量游戏数值设计"）
  topic    GitHub topic（至少两个仓库共有才建）

关系（confidence：EXTRACTED = 报告或 GitHub API 里明写的；INFERRED = 推出来的）
  task  -has_need / has_problem->  need / problem
  need  -matches->       repo   契合度 fit、怎么用、缺什么、风险        EXTRACTED（扫描报告）
  need  -has_part->      part
  part  -covered_by->    repo                                         EXTRACTED（部件核验）
  problem -helped_by->   repo   fit、借什么、用在哪                   EXTRACTED（深挖报告）
  problem -analogous_field-> field                                    EXTRACTED（深挖 TRIZ）
  repo  -mentions->      repo   README 里链接了对方                   EXTRACTED（GitHub README）
  repo  -fork_of->       repo                                         EXTRACTED（GitHub API）
  repo  -same_owner->    repo                                         EXTRACTED
  repo  -tagged->        topic                                        EXTRACTED（GitHub API）
  repo  -alternative_to-> repo  解决同一个卡点 / 覆盖同一个部件        INFERRED

产物（~/.deja-repo/kg/）
  index.md            agent 入口：概览、社区、怎么查
  repos/<owner>__<name>.md   每个仓库一张卡：它是什么、在你哪些任务里出现、跟谁有关系
  tasks/<id>.md       每个任务：卡点 / 需求 → 项目
  graph.json          全图（graphify 格式，`graphify query` 可用，cwd=~/.deja-repo/kg）
  graph.html          可视化（给人看）
"""
import hashlib
import json
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import config, group, store
from .github import _gh

KG = config.DATA_DIR / "kg"
GOUT = KG / "graphify-out"
CACHE = KG / "github_cache.json"
TTL = 7 * 86400
README_MAX = 40000
LINK = re.compile(r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)")
NOT_REPO = {"orgs", "sponsors", "features", "marketplace", "topics", "apps", "settings", "login", "about", "site"}


def _slug(s):
    """ascii 部分 + 短哈希：中文名不会撞成同一个 id。"""
    a = re.sub(r"[^a-z0-9_]+", "_", s.lower()).strip("_")[:60]
    return (a + "_" if a else "") + hashlib.md5(s.encode()).hexdigest()[:6]


def rid(name):
    return "repo_" + re.sub(r"[^a-z0-9_]+", "_", name.lower().replace("/", "__"))


def _repo_name(x):
    """报告里的各种写法 → owner/name；不是 GitHub 仓库返回 None。"""
    s = (x.get("repo") or x.get("id") or x.get("name") or x.get("url") or "").strip()
    if s.startswith("github:"):
        s = s[7:]
    if "github.com/" in s:
        m = LINK.search(s)
        s = f"{m.group(1)}/{m.group(2)}" if m else ""
    s = s.removesuffix(".git").rstrip("/")
    if x.get("source") not in (None, "github", "web") and not str(x.get("id", "")).startswith("github:"):
        return None
    return s if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", s) else None


# ---------- 收集：报告 → 节点和边 ----------

class G:
    def __init__(self):
        self.nodes, self.edges = {}, []

    def node(self, nid, label, kind, **attrs):
        n = self.nodes.setdefault(nid, {"id": nid, "kgid": nid, "label": label, "kind": kind, "file_type": "concept",
                                        "source_file": f"kg/{kind}", "source_location": None})
        for k, v in attrs.items():
            if v not in (None, "", []) and not n.get(k):
                n[k] = v
        return nid

    def edge(self, a, b, relation, confidence="EXTRACTED", score=1.0, **attrs):
        self.edges.append({"source": a, "target": b, "relation": relation, "confidence": confidence,
                           "confidence_score": score, "weight": 1.0, "source_file": attrs.pop("src", "kg"),
                           "source_location": None, **{k: v for k, v in attrs.items() if v not in (None, "")}})


def _task_of(r, assign):
    for key in (f"r:{r['id']}", f"s:{r.get('session') or ''}", f"s:codex:{r.get('session') or ''}"):
        if assign.get(key) and assign[key] != "misc":
            return assign[key]
    return None


def collect():
    g = G()
    st = group.load()
    tasks = {x["id"]: x for x in st["groups"]}
    reports = sorted((r for r in store.list_reports(limit=1000) if r["status"] == "done"), key=lambda r: -r["id"])
    latest_deep = {}
    for r in reports:          # 每个任务只用最新一次深挖
        d = r.get("data") or {}
        if d.get("kind") == "deep" and d.get("task") and d["task"] not in latest_deep:
            latest_deep[d["task"]] = r["id"]
    peers = defaultdict(set)   # 同一部件下的仓库 → alternative_to；同一卡点下 → co_recommended（常是互补，不是替代）

    def task_node(gid):
        t = tasks.get(gid)
        return g.node(f"task_{gid}", t["name"], "task", summary=t.get("summary")) if t else None

    def repo_node(name, x):
        return g.node(rid(name), name, "repo", url=f"https://github.com/{name}", what=x.get("what"),
                      desc=x.get("desc"), lang=x.get("lang"), license=(x.get("license") or "").upper() or None,
                      stars=x.get("stars") if isinstance(x.get("stars"), int) else None, updated=x.get("updated"))

    for r in reports:
        d = r.get("data") or {}
        src = f"report#{r['id']}"
        if d.get("kind") == "deep":
            if latest_deep.get(d.get("task")) != r["id"]:
                continue
            t = task_node(d["task"])
            for i, p in enumerate(d.get("problems") or []):
                pid = g.node(f"prob_{r['id']}_{i}", p["problem"], "problem", contradiction=p.get("contradiction"),
                             ideal=p.get("ideal"), fix=p.get("fix"), report=r["id"])
                if t:
                    g.edge(t, pid, "has_problem", src=src)
                for f in p.get("fields") or []:
                    fid = g.node("field_" + _slug(f["field"]), f["field"], "field")
                    g.edge(pid, fid, "analogous_field", src=src, how=f.get("how"))
                for x in p.get("picks") or []:
                    name = _repo_name(x)
                    if not name:
                        continue
                    rn = repo_node(name, x)
                    g.edge(pid, rn, "helped_by", src=src, fit=x.get("fit"), borrow=x.get("borrow"), where=x.get("where"))
                    peers[pid].add(rn)
            continue
        # 普通扫描（新格式 matches / 旧格式 repos）
        title = re.sub(r"\s*[（(][一二三四五六七八九十\d]+[)）]\s*$", "", d.get("title") or r.get("summary") or r["message"][:40])
        nid = g.node(f"need_{r['id']}", title, "need",
                     goal=d.get("goal") or r["message"][:200], verdict=r.get("verdict"), report=r["id"])
        gid = _task_of(r, st["assign"])
        if gid and task_node(gid):
            g.edge(f"task_{gid}", nid, "has_need", src=src)
        by_id = {}
        for x in (d.get("matches") or []) + (d.get("repos") or []):
            name = _repo_name(x)
            if not name:
                continue
            by_id[x.get("id") or f"github:{name}"] = name
            rn = repo_node(name, x)
            g.edge(nid, rn, "matches", src=src, fit=_int(x.get("fit")), use_mode=x.get("use_mode"),
                   how_to_use=x.get("how_to_use"), missing=x.get("missing"), risk=x.get("risk"),
                   code=((x.get("code") or {}).get("summary") if (x.get("code") or {}).get("ok") else None))
        for c in d.get("components") or []:
            pid = g.node(f"part_{r['id']}_{_slug(c['name'])}", c["name"], "part", status=c.get("status"), note=c.get("note"))
            g.edge(nid, pid, "has_part", src=src)
            for b in c.get("by") or []:
                name = by_id.get(b) or _repo_name({"id": b})
                if name and rid(name) in g.nodes:
                    g.edge(pid, rid(name), "covered_by", src=src)
                    peers[pid].add(rid(name))
    for anchor, rs in peers.items():
        rs = sorted(rs)
        rel = "alternative_to" if anchor.startswith("part_") else "co_recommended"
        for i, a in enumerate(rs):
            for b in rs[i + 1:]:
                g.edge(a, b, rel, "INFERRED", 0.75 if rel == "alternative_to" else 0.6,
                       src=f"同属 {g.nodes[anchor]['label'][:30]}", via=anchor)
    return g


def _int(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


# ---------- GitHub 补充：fork、topics、README 互相提到 ----------

def _fetch(name):
    out = {"fetched": time.time()}
    try:
        r = json.loads(_gh(["api", f"repos/{name}"], timeout=30))
        out.update(full_name=r["full_name"], stars=r["stargazers_count"], updated=(r.get("pushed_at") or "")[:10],
                   license=((r.get("license") or {}).get("spdx_id") or ""), lang=r.get("language") or "",
                   topics=r.get("topics") or [], archived=r.get("archived", False), desc=(r.get("description") or "")[:200],
                   parent=(r.get("parent") or {}).get("full_name"), owner=r["owner"]["login"])
    except Exception as e:
        out["error"] = str(e)[:120]
        return out
    try:
        txt = _gh(["api", f"repos/{name}/readme", "-H", "Accept: application/vnd.github.raw"], timeout=30)[:README_MAX]
        out["links"] = sorted({f"{a}/{b.removesuffix('.git')}" for a, b in LINK.findall(txt)
                               if a.lower() not in NOT_REPO} - {name})
    except Exception:
        out["links"] = []
    return out


def enrich(g, refresh=False):
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    names = [n["label"] for n in g.nodes.values() if n["kind"] == "repo"]
    todo = [n for n in names if refresh or n not in cache or time.time() - cache[n].get("fetched", 0) > TTL
            or cache[n].get("error")]
    if todo:
        with ThreadPoolExecutor(max_workers=6) as ex:
            for n, info in zip(todo, ex.map(_fetch, todo)):
                cache[n] = info
        KG.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(cache, ensure_ascii=False))
    lower = {n.lower(): n for n in names}
    topic_count = Counter(t for n in names for t in (cache.get(n) or {}).get("topics", []))
    owners = defaultdict(list)
    for n in names:
        c = cache.get(n) or {}
        node = g.nodes[rid(n)]
        for k in ("stars", "updated", "license", "lang", "desc"):
            if c.get(k) not in (None, ""):
                node[k] = c[k]
        if c.get("archived"):
            node["archived"] = True
        if c.get("topics"):
            node["topics"] = c["topics"]
        owners[n.split("/")[0].lower()].append(n)
        for t in c.get("topics", []):
            if topic_count[t] >= 2:
                g.edge(rid(n), g.node("topic_" + _slug(t), t, "topic"), "tagged", src="GitHub API")
        for link in c.get("links", []):
            if link.lower() in lower:
                g.edge(rid(n), rid(lower[link.lower()]), "mentions", src=f"README of {n}")
        if c.get("parent") and c["parent"].lower() in lower:
            g.edge(rid(n), rid(lower[c["parent"].lower()]), "fork_of", src="GitHub API")
    for _, rs in owners.items():
        for i, a in enumerate(rs):
            for b in rs[i + 1:]:
                g.edge(rid(a), rid(b), "same_owner", src="GitHub API")
    return len(todo)


# ---------- 聚类（graphify）、写给 agent 的 Markdown ----------

GRAPHIFY_SCRIPT = r"""
import json, sys
from pathlib import Path
from graphify.build import build_from_json
from graphify.cluster import cluster
from graphify.export import to_json
out = Path(sys.argv[1])
ex = json.loads((out / '.kg_extract.json').read_text())
G = build_from_json(ex, root=str(out.parent), directed=False)
com = cluster(G)
(out / 'graph.json').unlink(missing_ok=True)      # 图会随报告增减，允许变小
to_json(G, com, str(out / 'graph.json'))
kg = {n: G.nodes[n].get('kgid', n) for n in G.nodes}
print(json.dumps({str(k): [kg.get(x, x) for x in v] for k, v in com.items()}))
"""


def _graphify_python():
    exe = subprocess.run(["sh", "-c", "command -v graphify"], capture_output=True, text=True).stdout.strip()
    if not exe:
        return None
    first = Path(exe).read_text(errors="ignore").splitlines()[0]
    py = first[2:].strip() if first.startswith("#!") else ""
    return py if py and Path(py).exists() else None


def _communities(g):
    """用 graphify 聚类；没装 graphify 就按连通块分。返回 {社区号: [节点 id]}。"""
    GOUT.mkdir(parents=True, exist_ok=True)
    (GOUT / ".kg_extract.json").write_text(json.dumps({"nodes": list(g.nodes.values()), "edges": g.edges,
                                                       "hyperedges": [], "input_tokens": 0, "output_tokens": 0},
                                                      ensure_ascii=False))
    py = _graphify_python()
    if py:
        r = subprocess.run([py, "-c", GRAPHIFY_SCRIPT, str(GOUT)], capture_output=True, text=True, timeout=300)
        if r.returncode == 0 and r.stdout.strip():
            return {int(k): v for k, v in json.loads(r.stdout.strip().splitlines()[-1]).items()}
        print(f"graphify 聚类失败，改用连通块：{r.stderr[-200:]}", file=sys.stderr)
    adj = defaultdict(set)
    for e in g.edges:
        adj[e["source"]].add(e["target"])
        adj[e["target"]].add(e["source"])
    seen, out = set(), {}
    for n in g.nodes:
        if n in seen:
            continue
        stack, comp = [n], []
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            comp.append(x)
            stack += adj[x] - seen
        out[len(out)] = comp
    return out


def _name_community(g, members, deg):
    """社区名：度数最高的任务 / 卡点 / 需求；没有就用前三个仓库。不调模型。"""
    rank = {"task": 0, "need": 1, "problem": 2, "field": 3}
    hubs = sorted((m for m in members if g.nodes[m]["kind"] in rank), key=lambda m: (rank[g.nodes[m]["kind"]], -deg[m]))
    if hubs:
        return g.nodes[hubs[0]]["label"][:40]
    repos = sorted((m for m in members if g.nodes[m]["kind"] == "repo"), key=lambda m: -deg[m])
    return "、".join(g.nodes[m]["label"].split("/")[-1] for m in repos[:3]) or "其他"


REL_ZH = {"matches": "需求匹配", "helped_by": "可借鉴于", "covered_by": "部件由它覆盖", "alternative_to": "覆盖同一部件（可替代）", "co_recommended": "同一卡点的候选（多为互补）",
          "mentions": "README 提到", "fork_of": "fork 自", "same_owner": "同一作者", "tagged": "topic",
          "has_problem": "卡点", "has_need": "需求", "has_part": "部件", "analogous_field": "相邻领域"}


def _file(name):
    return name.replace("/", "__") + ".md"


def _write_md(g, comms, deg):
    for sub in ("repos", "tasks"):
        d = KG / sub
        d.mkdir(parents=True, exist_ok=True)
        for f in d.glob("*.md"):
            f.unlink()
    nbr = defaultdict(list)
    for e in g.edges:
        nbr[e["source"]].append((e, e["target"]))
        nbr[e["target"]].append((e, e["source"]))
    cname = {}
    for c, ms in comms.items():
        name = _name_community(g, ms, deg)
        for m in ms:
            cname[m] = (c, name)

    def link(nid, from_dir):
        n = g.nodes[nid]
        if n["kind"] == "repo":
            return f"[{n['label']}]({'' if from_dir == 'repos' else 'repos/' if from_dir == '' else '../repos/'}{_file(n['label'])})"
        if n["kind"] == "task":
            return f"[{n['label']}]({'' if from_dir == 'tasks' else 'tasks/' if from_dir == '' else '../tasks/'}{nid[5:]}.md)"
        return n["label"]

    def meta(n):
        return " · ".join(x for x in (f"★{n['stars']}" if n.get("stars") is not None else "", n.get("license"),
                                     n.get("lang"), f"更新 {n['updated']}" if n.get("updated") else "",
                                     "已归档" if n.get("archived") else "") if x)

    repos = sorted((n for n in g.nodes.values() if n["kind"] == "repo"), key=lambda n: -deg[n["id"]])
    for n in repos:
        L = [f"# {n['label']}", "", f"{n.get('what') or n.get('desc') or ''}", "",
             f"- 链接：{n.get('url')}", f"- {meta(n)}" if meta(n) else "",
             f"- topics：{', '.join(n['topics'])}" if n.get("topics") else "",
             f"- 社区：{cname.get(n['id'], (0, ''))[1]}", ""]
        uses = [(e, o) for e, o in nbr[n["id"]] if g.nodes[o]["kind"] in ("need", "problem", "part")]
        if uses:
            L.append("## 在你的哪些需求 / 卡点里出现")
            for e, o in sorted(uses, key=lambda t: -(t[0].get("fit") or 0)):
                on = g.nodes[o]
                tasks = [t for _, t in nbr[o] if g.nodes[t]["kind"] == "task"]
                head = f"- **{REL_ZH[e['relation']]}** {on['label']}" + (f"（任务：{link(tasks[0], 'repos')}）" if tasks else "")
                L.append(head + (f" · 契合度 {e['fit']}" if e.get("fit") is not None else ""))
                for k, zh in (("borrow", "借"), ("where", "用在"), ("how_to_use", "用法"), ("missing", "缺"),
                              ("risk", "风险"), ("code", "读过代码")):
                    if e.get(k):
                        L.append(f"  - {zh}：{e[k]}")
            L.append("")
        rel = [(e, o) for e, o in nbr[n["id"]] if g.nodes[o]["kind"] == "repo"]
        if rel:
            L.append("## 和其他项目的关系")
            for e, o in sorted(rel, key=lambda t: (t[0]["relation"], g.nodes[t[1]]["label"])):
                why = f"（{e['source_file']}）" if e["relation"] in ("alternative_to", "co_recommended") else ""
                L.append(f"- {REL_ZH[e['relation']]}：{link(o, 'repos')}{why}")
            L.append("")
        tops = [g.nodes[o]["label"] for e, o in nbr[n["id"]] if g.nodes[o]["kind"] == "topic"]
        if tops:
            L += [f"共同 topic：{', '.join(sorted(set(tops)))}", ""]
        (KG / "repos" / _file(n["label"])).write_text("\n".join(x for x in L if x is not None))

    tasks = [n for n in g.nodes.values() if n["kind"] == "task"]
    for t in tasks:
        L = [f"# 任务：{t['label']}", "", t.get("summary") or "", ""]
        for e, o in nbr[t["id"]]:
            on = g.nodes[o]
            if on["kind"] not in ("problem", "need"):
                continue
            L.append(f"## {'卡点' if on['kind'] == 'problem' else '需求'}：{on['label']}")
            if on.get("contradiction"):
                L.append(f"矛盾：{on['contradiction']}")
            fields = [g.nodes[x]["label"] for _, x in nbr[o] if g.nodes[x]["kind"] == "field"]
            if fields:
                L.append(f"相邻领域：{'、'.join(fields)}")
            rs = sorted([(e2, x) for e2, x in nbr[o] if g.nodes[x]["kind"] == "repo"], key=lambda t: -(t[0].get("fit") or 0))
            for e2, x in rs:
                L.append(f"- {link(x, 'tasks')}" + (f" · 契合度 {e2['fit']}" if e2.get("fit") is not None else "")
                         + (f" — {e2.get('borrow') or g.nodes[x].get('what') or ''}"))
            L.append("")
        (KG / "tasks" / f"{t['id'][5:]}.md").write_text("\n".join(L))

    kinds = Counter(n["kind"] for n in g.nodes.values())
    rels = Counter(e["relation"] for e in g.edges)
    L = ["# 项目知识图谱（给 AI agent 读）", "",
         "你（用户）查到过的 GitHub 项目之间、以及它们和你的任务 / 卡点 / 需求之间的关系。由 `giants kg build` 从查询报告 + GitHub API 生成。",
         "",
         f"**{kinds['repo']} 个仓库 · {kinds['task']} 个任务 · {kinds['problem']} 个卡点 · {kinds['need']} 次需求扫描 · {len(g.edges)} 条关系**", "",
         "## 怎么用", "",
         "- 某个项目：读 `repos/<owner>__<name>.md`（它是什么、在哪些任务里出现、和谁可替代 / 互相提到 / fork）。",
         "- 某个任务：读 `tasks/<任务 id>.md`（卡点 / 需求 → 推荐项目，按契合度排）。",
         "- 命令行：`giants kg show <仓库或任务名>`、`giants kg query \"关键词\"`、`giants kg path <A> <B>`。",
         "- 关系可信度：EXTRACTED 来自报告或 GitHub API；`alternative_to`（覆盖同一部件）和 `co_recommended`（同一卡点的候选，多为互补）是 INFERRED——只说明它们在同一处被推荐过，不代表读过代码对比。",
         "- 推荐项目前先看这里：同一个项目可能已经在别的任务里查过、读过代码。", "",
         "## 关系统计", "", ", ".join(f"{REL_ZH.get(k, k)} {v}" for k, v in rels.most_common()), "",
         "## 社区（聚在一起的项目）", ""]
    for c, ms in sorted(comms.items(), key=lambda kv: -len(kv[1])):
        rs = sorted((m for m in ms if g.nodes[m]["kind"] == "repo"), key=lambda m: -deg[m])
        if not rs:
            continue
        L.append(f"### {_name_community(g, ms, deg)}（{len(rs)} 个项目）")
        L.append("、".join(link(m, "") for m in rs[:12]) + (f" 等 {len(rs)} 个" if len(rs) > 12 else ""))
        L.append("")
    L += ["## 连接最多的项目", ""]
    for n in repos[:15]:
        L.append(f"- {link(n['id'], '')}（{deg[n['id']]} 条关系）— {n.get('what') or n.get('desc') or ''}")
    L += ["", "## 任务", ""] + [f"- {link(t['id'], '')}" for t in tasks]
    (KG / "index.md").write_text("\n".join(L) + "\n")


def build(refresh=False, quiet=False):
    t0 = time.time()
    g = collect()
    fetched = enrich(g, refresh)
    # 同一对节点同一关系只留一条
    seen, edges = set(), []
    for e in g.edges:
        k = (e["relation"], *sorted((e["source"], e["target"])))
        if k not in seen and e["source"] in g.nodes and e["target"] in g.nodes and e["source"] != e["target"]:
            seen.add(k)
            edges.append(e)
    g.edges = edges
    deg = Counter()
    for e in g.edges:
        deg[e["source"]] += 1
        deg[e["target"]] += 1
    comms = _communities(g)
    _write_md(g, comms, deg)
    (KG / "graph.json").write_text(json.dumps({"nodes": list(g.nodes.values()), "edges": g.edges}, ensure_ascii=False, indent=1))
    if _graphify_python():
        subprocess.run(["graphify", "export", "html"], cwd=KG, capture_output=True, timeout=300)
        if (GOUT / "graph.html").exists():
            (GOUT / "graph.html").replace(KG / "graph.html")
    if not quiet:
        kinds = Counter(n["kind"] for n in g.nodes.values())
        print(f"知识图谱：{kinds['repo']} 个仓库、{len(g.nodes)} 个节点、{len(g.edges)} 条关系、{len(comms)} 个社区；"
              f"查了 GitHub {fetched} 个仓库；{time.time() - t0:.0f}s → {KG / 'index.md'}")
    return g


def refresh_quietly():
    """深挖 / 扫描完成后顺手更新，失败不影响主流程。"""
    try:
        build(quiet=True)
    except Exception as e:
        print(f"知识图谱更新失败：{e}", file=sys.stderr)


# ---------- 查询 ----------

def _load():
    d = json.loads((KG / "graph.json").read_text())
    nodes = {n["id"]: n for n in d["nodes"]}
    nbr = defaultdict(list)
    for e in d["edges"]:
        nbr[e["source"]].append((e, e["target"]))
        nbr[e["target"]].append((e, e["source"]))
    return nodes, nbr


def find(nodes, text):
    t = text.lower().strip()
    exact = [n for n in nodes.values() if n["label"].lower() == t or n["id"] == t]
    if exact:
        return exact
    words = t.split()
    return sorted((n for n in nodes.values()
                   if all(w in (n["label"] + " " + (n.get("what") or "") + " " + (n.get("desc") or "")).lower() for w in words)),
                  key=lambda n: (n["kind"] != "repo", len(n["label"])))


def show(text):
    nodes, _ = _load()
    hits = find(nodes, text)
    if not hits:
        return f"图谱里没有和「{text}」匹配的节点。"
    n = hits[0]
    if n["kind"] == "repo":
        return (KG / "repos" / _file(n["label"])).read_text()
    if n["kind"] == "task":
        return (KG / "tasks" / f"{n['id'][5:]}.md").read_text()
    return query(text)


def query(text, limit=20):
    nodes, nbr = _load()
    hits = find(nodes, text)[:5]
    if not hits:
        return f"图谱里没有和「{text}」匹配的节点。"
    out = []
    for n in hits:
        out.append(f"## [{n['kind']}] {n['label']}" + (f" — {n.get('what') or n.get('desc')}" if n.get("what") or n.get("desc") else ""))
        rest = [(e, o) for e, o in nbr[n["id"]] if e["relation"] != "tagged"]
        for e, o in sorted(rest, key=lambda t: -(t[0].get("fit") or 0))[:limit]:
            on = nodes[o]
            extra = f" · 契合度 {e['fit']}" if e.get("fit") is not None else ""
            out.append(f"- {REL_ZH.get(e['relation'], e['relation'])} → [{on['kind']}] {on['label']}{extra} ({e['confidence']})")
        tops = sorted(nodes[o]["label"] for e, o in nbr[n["id"]] if e["relation"] == "tagged")
        if tops:
            out.append(f"- 共同 topic：{', '.join(tops)}")
        out.append("")
    return "\n".join(out)


def path(a, b):
    nodes, nbr = _load()
    fa, fb = find(nodes, a), find(nodes, b)
    if not fa or not fb:
        return "找不到起点或终点。"
    start, goal = fa[0]["id"], fb[0]["id"]
    for skip in ({"tagged", "same_owner"}, set()):     # 先走有含义的关系，走不通再借 topic
        prev, queue = {start: None}, [start]
        while queue:
            x = queue.pop(0)
            if x == goal:
                break
            for e, o in nbr[x]:
                if o not in prev and e["relation"] not in skip:
                    prev[o] = (x, e)
                    queue.append(o)
        if goal in prev:
            break
    if goal not in prev:
        return f"{nodes[start]['label']} 和 {nodes[goal]['label']} 之间没有路径。"
    steps, x = [], goal
    while prev[x]:
        p, e = prev[x]
        steps.append(f"{nodes[p]['label']} —{REL_ZH.get(e['relation'], e['relation'])}— {nodes[x]['label']}")
        x = p
    return "\n".join(reversed(steps))
