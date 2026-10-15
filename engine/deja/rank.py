"""统一排序 + 新鲜度。

patent 用本地向量（fastembed）算相似度；这里坚持纯标准库，用 BM25 做词法相关度，
再交给模型核验时补上语义判断。新鲜度规则照搬 patent：两年没动的打 ⚑ 标记，但不降权——
一个没人维护的项目依然证明"这东西有人做过"。
"""
import math
import re
from collections import Counter
from datetime import date

STALE_DAYS = 730


def _stem(w):
    """极简英文词干：videos→video、subtitles→subtitle、generates/generated→generat、libraries→library。"""
    if len(w) <= 4:
        return w
    if w.endswith("ically"):
        return w[:-4]
    if w.endswith("ies"):
        return w[:-3] + "y"
    if w.endswith(("sses", "xes", "ches", "shes", "zes")):
        return w[:-2]
    for suf in ("ing", "ed", "ly"):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            w = w[: -len(suf)]
            return w[:-1] if w.endswith("e") else w
    if w.endswith("s") and not w.endswith(("ss", "us", "is")):
        w = w[:-1]
    return w[:-1] if w.endswith("e") else w


def _tok(text):
    t = text.lower()
    words = [_stem(w) for w in re.findall(r"[a-z][a-z0-9]+", t)]
    zh = re.sub(r"[^一-鿿]", "", t)
    return words + [zh[i:i + 2] for i in range(len(zh) - 1)]


def bm25(query, docs, k1=1.4, b=0.75):
    """返回每个文档 0–1 的相关度（按最大值归一）。"""
    q = set(_tok(query))
    toks = [_tok(d) for d in docs]
    n = len(toks) or 1
    avg = sum(map(len, toks)) / n or 1
    df = Counter(w for t in toks for w in set(t))
    scores = []
    for t in toks:
        tf = Counter(t)
        s = 0.0
        for w in q:
            if w in tf:
                idf = math.log(1 + (n - df[w] + .5) / (df[w] + .5))
                s += idf * tf[w] * (k1 + 1) / (tf[w] + k1 * (1 - b + b * len(t) / avg))
        scores.append(s)
    top = max(scores, default=0) or 1
    return [round(s / top, 3) for s in scores]


def age_days(updated):
    try:
        return (date.today() - date.fromisoformat(updated[:10])).days
    except (ValueError, TypeError):
        return None


def annotate(items, query):
    """给每条候选加 sim / stale，并按 相关度 + 人气 排序。"""
    sims = bm25(query, [f"{i['name']} {i['name']} {i.get('desc', '')}" for i in items])
    for i, s in zip(items, sims):
        i["sim"] = s
        d = age_days(i.get("updated"))
        i["stale"] = d is not None and d >= STALE_DAYS
        pop = i.get("popularity") or 0
        # 被多个关键词同时命中是很强的相关信号；只在 README 里提到的（大合集、awesome 清单常见）打折
        hits = i.get("hits", [])
        name_hits = len({h for h in hits if "·" not in h})
        readme_hits = len({h.split(" ·")[0] for h in hits if "·readme" in h} - set(hits))
        bonus = min(max(name_hits - 1, 0), 4) * 0.8 + min(readme_hits, 3) * 0.25
        i["rank"] = s * 10 + math.log10(pop + 1) * 0.6 + bonus
    return sorted(items, key=lambda x: -x["rank"])


def pick(items, total, per_source=2, quota=None):
    """先保证每个来源至少有前 N 名（quota 可单独指定），再按总分补满，避免一家独大或一家缺席。"""
    chosen, seen = [], set()
    by_src = {}
    for i in items:
        by_src.setdefault(i["source"], []).append(i)
    for lst in by_src.values():
        for i in lst[:(quota or {}).get(lst[0]["source"], per_source)]:
            if i["sim"] > 0.15:
                chosen.append(i)
                seen.add(i["id"])
    for i in items:
        if len(chosen) >= total:
            break
        if i["id"] not in seen:
            chosen.append(i)
            seen.add(i["id"])
    return sorted(chosen, key=lambda x: -x["rank"])[:total]
