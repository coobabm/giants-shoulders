"""查本机已经装了哪些 skill —— 也许轮子就在你自己硬盘上。"""
import re
import time

from . import config

_cache = {"at": 0, "items": []}


def _frontmatter(path):
    try:
        head = path.read_text("utf-8", "replace")[:3000]
    except Exception:
        return None
    m = re.match(r"---\s*\n(.*?)\n---", head, re.S)
    if not m:
        return None
    fm = m.group(1)
    name = re.search(r"^name:\s*(.+)$", fm, re.M)
    desc = re.search(r"^description:\s*(.+?)(?=^\w[\w-]*:|\Z)", fm, re.M | re.S)
    if not name:
        return None
    return {"name": name.group(1).strip().strip("'\""),
            "desc": re.sub(r"\s+", " ", desc.group(1)).strip().strip("'\"|>")[:400] if desc else "",
            "path": str(path.parent)}


def skills():
    if time.time() - _cache["at"] < 600:
        return _cache["items"]
    seen, items = set(), []
    for root, pattern in config.SKILL_GLOBS:
        if not root.exists():
            continue
        for p in root.glob(pattern):
            fm = _frontmatter(p)
            if fm and fm["name"] not in seen:
                seen.add(fm["name"])
                fm["kind"] = "codex-skill" if ".codex" in p.parts else "claude-skill"
                items.append(fm)
    _cache.update(at=time.time(), items=items)
    return items


def _grams(text):
    t = text.lower()
    words = set(re.findall(r"[a-z][a-z0-9-]{2,}", t))
    zh = re.sub(r"[^一-鿿]", "", t)
    return words | {zh[i:i + 2] for i in range(len(zh) - 1)}


STOP = {"the", "and", "for", "use", "when", "with", "this", "that", "from", "user", "using",
        "使用", "用户", "一个", "可以", "进行"}


def match(summary, keywords, top=6):
    q = _grams(summary + " " + " ".join(keywords)) - STOP
    scored = []
    for s in skills():
        g = _grams(s["name"] + " " + s["desc"]) - STOP
        hit = len(q & g)
        if hit >= 2:
            scored.append((hit, s))
    scored.sort(key=lambda x: -x[0])
    return [s for _, s in scored[:top]]
