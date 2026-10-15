"""用 gh CLI 搜 GitHub：名字/描述 + README 两路，多关键词并发，去重打分。"""
import json
import math
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from . import config

FIELDS = "fullName,description,stargazersCount,updatedAt,license,language,url,isArchived"


def _gh(args, timeout=60):
    for attempt in range(2):
        r = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=timeout)
        if r.returncode == 0:
            return r.stdout
        if "rate limit" in r.stderr.lower() and attempt == 0:
            time.sleep(35)  # 搜索 API 限 30 次/分钟
            continue
        raise RuntimeError(r.stderr.strip()[:200])
    return ""


RATE_HINTS = ("rate limit", "429", "secondary rate", "abuse detection")
CANARY = "repo:torvalds/linux"     # 对照：一个多年来一定搜得到的仓库


def classify(err):
    """rate_limit = 等一会儿重跑就行；source_error = 要排查（没登录、网络、gh 坏了）。两者处理方式相反，不能混。"""
    return "rate_limit" if any(h in str(err).lower() for h in RATE_HINTS) else "source_error"


def log_entry(source, query, n, err=None):
    return {"source": source, "query": query, "n": n,
            "error": {"kind": classify(err), "message": str(err)[:160]} if err else None}


def canary():
    """正式搜之前先搜一个肯定能搜到的仓库。搜不到说明是通道坏了，不是"这个领域没东西"。"""
    try:
        d = json.loads(_gh(["api", "-X", "GET", "search/repositories", "-f", f"q={CANARY}", "-f", "per_page=1"], timeout=30))
        n = int(d.get("total_count") or 0)
        return {**log_entry("canary", CANARY, n), "ok": n >= 1}
    except Exception as e:
        return {**log_entry("canary", CANARY, 0, e), "ok": False}


def channel_status(canary_row, log):
    """ok：对照通过且没出错；degraded：对照通过但有查询出错；blind：对照没通过，搜不到不代表没有。"""
    if not canary_row.get("ok"):
        return "blind"
    return "degraded" if any(x.get("error") for x in log) else "ok"


def search(query, match=None, topic=None, limit=12, log=None):
    # 单词分开传：整串传给 gh 会被加引号变成"精确短语"搜索，多词时几乎搜不到
    args = ["search", "repos", "--sort", "stars", "--limit", str(limit), "--json", FIELDS]
    if match:
        args += ["--match", match]
    if topic:
        args += ["--topic", topic]
    args += ["--", *query.split()]
    label = query + (f" ·{match}" if match else "") + (f" ·#{topic}" if topic else "")
    try:
        rows = json.loads(_gh(args) or "[]")
    except Exception as e:
        if log is not None:
            log.append(log_entry("github", label, 0, e))
        return []
    if log is not None:
        log.append(log_entry("github", label, len(rows)))
    return rows


def _tokens(text):
    return set(re.findall(r"[a-z0-9]+", text.lower())) - {"a", "the", "and", "for", "of", "to", "with"}


def scan(keywords, topics=(), log=None):
    jobs = []
    for kw in keywords[:config.MAX_KEYWORDS]:
        jobs.append((kw, None, None))
        jobs.append((kw, "readme", None))
    for t in list(topics)[:2]:
        jobs.append((keywords[0], None, t))

    def run(job):
        """沿查询梯子往下走（sota-anchor 的做法）：结果太少就收窄成最长的 2 个词再搜，GitHub 是全词 AND。"""
        kw, match, topic = job
        items = search(kw, match=match, topic=topic, log=log)
        words = kw.split()
        if len(items) < 5 and len(words) > 2 and not topic:
            from .registries import narrowed
            items += search(narrowed(words, 2), match=match, log=log)
        return job, items

    repos = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        results = ex.map(run, jobs)
        for (kw, match, topic), items in results:
            label = kw + (" ·readme" if match else "") + (f" ·#{topic}" if topic else "")
            for r in items:
                cur = repos.setdefault(r["fullName"], {**r, "hits": []})
                cur["hits"].append(label)

    kw_tokens = set().union(*(_tokens(k) for k in keywords)) if keywords else set()
    now = datetime.now(timezone.utc)
    rows = []
    for r in repos.values():
        if r["isArchived"] or r["stargazersCount"] < config.MIN_STARS:
            continue
        age_m = (now - datetime.fromisoformat(r["updatedAt"].replace("Z", "+00:00"))).days / 30
        text_tokens = _tokens(r["fullName"] + " " + (r["description"] or ""))
        relevance = len(kw_tokens & text_tokens) / max(len(kw_tokens), 1)
        score = (math.log10(r["stargazersCount"] + 1) * 8
                 + (4 if age_m < 6 else 0)  # 只奖励活跃，不惩罚停更（停更也证明有人做过）
                 + 5 * (len(set(h.split(" ·")[0] for h in r["hits"])) - 1)
                 + 30 * relevance)
        rows.append({
            "repo": r["fullName"], "url": r["url"], "stars": r["stargazersCount"],
            "lang": r["language"] or "", "license": ((r.get("license") or {}).get("key") or "none"),
            "updated": r["updatedAt"][:10], "desc": (r["description"] or "")[:200],
            "hits": r["hits"], "score": round(score, 1),
        })
    rows.sort(key=lambda x: x["score"], reverse=True)
    return rows, len(jobs)


def readme(full_name):
    try:
        txt = _gh(["api", f"repos/{full_name}/readme", "-H", "Accept: application/vnd.github.raw"], timeout=30)
    except Exception:
        return ""
    txt = re.sub(r"<img[^>]*>|!\[[^\]]*\]\([^)]*\)", "", txt)  # 去图片
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    return txt[:config.README_CHARS]


def readmes(names):
    with ThreadPoolExecutor(max_workers=6) as ex:
        return dict(zip(names, ex.map(readme, names)))


def repo_meta(full_name):
    """把全网搜索里出现的 GitHub 链接补成和 scan() 一样的结构。"""
    try:
        r = json.loads(_gh(["api", f"repos/{full_name}"], timeout=30))
    except Exception:
        return None
    if r.get("archived"):
        return None
    return {
        "repo": r["full_name"], "url": r["html_url"], "stars": r["stargazers_count"],
        "lang": r.get("language") or "", "license": ((r.get("license") or {}).get("key") or "none"),
        "updated": (r.get("pushed_at") or "")[:10], "desc": (r.get("description") or "")[:200],
        "hits": ["web"], "score": 0,
    }
