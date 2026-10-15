"""GitHub 之外的结构化来源：Hacker News、npm、crates.io、Homebrew、VS Code 插件市场、arXiv、Hugging Face。

移植自两个 MIT 项目，保留原作者的做法和实测结论：
  - r14dd/patent (MIT OR Apache-2.0, © 2026 Riad Mukhtarov)
      按想法挑来源、"长词优先"逐步放宽的查询、各注册表的请求参数（VS Code 必须 flags=914 才有更新时间）、
      Homebrew 拉全量目录本地匹配、HN 只搜 story。
  - luckmanqasim/sota-anchor (MIT, © 2026 Luckman Qasim)
      STOPWORDS、extract_terms（按作者书写顺序保留关键程度）、arXiv 逐项 all: 再 AND 的查询梯子
      （百分号编码，不能用 +）、Hugging Face 论文语义搜索、MIN_OVERLAP 准入门槛。
PyPI 没有搜索 API，网页版有 JS 挑战（两个项目都实测过），交给全网侦察覆盖。
"""
import html
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

from . import __version__, config

USER_AGENT = f"deja-repo/{__version__} (prior-art radar; local tool)"
TIMEOUT = 10

# ---- 来自 sota-anchor ----
STOPWORDS = frozenset(
    ["a", "an", "the", "and", "or", "but", "nor", "for", "yet", "so", "of", "in", "on", "at", "to", "from", "by",
     "with", "without", "into", "onto", "upon", "about", "above", "below", "over", "under", "between", "among",
     "through", "during", "before", "after", "since", "is", "are", "was", "were", "be", "been", "being", "am", "do",
     "does", "did", "doing", "done", "have", "has", "had", "having", "can", "cannot", "could", "shall", "should",
     "will", "would", "may", "might", "must", "not", "no", "only", "just", "that", "this", "these", "those",
     "there", "here", "it", "its", "they", "them", "their", "which", "who", "whom", "whose", "what", "when",
     "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "than",
     "too", "very", "we", "our", "you", "your", "he", "she", "his", "her", "him", "me", "my", "i", "us", "using",
     "use", "used", "via", "as", "if", "then", "else", "also", "etc", "per"]
)
MIN_TERM_LENGTH = 3
MIN_OVERLAP = 2      # 结果至少要提到几个检索词才算数（检索词更少时要求全部）
ARXIV_MAX_TERMS = 4


def extract_terms(text):
    """检索词，按书写顺序 = 关键程度。"""
    terms = []
    for token in re.findall(r"[A-Za-z0-9_+#.]+", text.lower()):
        token = token.strip(".")
        if len(token) < MIN_TERM_LENGTH or token in STOPWORDS or token in terms:
            continue
        terms.append(token)
    return terms


def admissible(text, terms, floor=MIN_OVERLAP):
    low = text.lower()
    return sum(1 for t in terms if t in low) >= min(floor, len(terms))


# ---- 来自 patent ----
def narrowed(terms, n):
    """取最长的 n 个词，保持原顺序。"""
    idx = sorted(range(len(terms)), key=lambda i: -len(terms[i]))[:n]
    return " ".join(terms[i] for i in sorted(idx))


def ladder(terms, min_terms=2):
    """从全部关键词逐级收窄到 min_terms 个最长词；注册表都是 AND 匹配，词多常常 0 结果。"""
    out = []
    for n in [len(terms), *range(3, min_terms - 1, -1)]:
        q = narrowed(terms, n)
        if q and q not in out:
            out.append(q)
    return out


def _word_in(text, words):
    low = text.lower()
    return any(re.search(r"(?<![a-z0-9])" + re.escape(w) + r"(?![a-z0-9])", low) for w in words)


def select_sources(text, hinted=()):
    """GitHub、HN 永远搜；其它按想法里提到的生态挑（中英文都认），再并上模型给的建议。"""
    s = {"hackernews"}
    rules = [
        ("npm", ["npm", "node", "javascript", "typescript", "deno", "bun", "react", "vue", "前端", "网页", "浏览器", "chrome"]),
        ("crates", ["rust", "crate", "cargo"]),
        ("homebrew", ["brew", "homebrew", "macos", "mac", "cli", "命令行", "终端"]),
        ("vscode", ["vscode", "vs code", "编辑器插件", "editor extension"]),
        ("arxiv", ["paper", "论文", "算法", "algorithm", "模型", "model", "训练", "train", "llm", "neural", "检测", "识别"]),
        ("huggingface", ["模型", "model", "llm", "whisper", "diffusion", "embedding", "训练", "识别", "生成", "tts", "asr", "ai"]),
    ]
    for name, words in rules:
        if _word_in(text, words) or any(w in text.lower() for w in words if not w.isascii()):
            s.add(name)
    s |= set(hinted) & set(SOURCES)
    if not s - {"hackernews"}:
        s |= {"npm", "crates"}  # patent 的兜底：没识别出语言就搜最大的几个注册表
    return s


# ---- 请求 ----
def _get(url, data=None, headers=None, timeout=TIMEOUT):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def _q(params):
    return urllib.parse.urlencode(params, quote_via=urllib.parse.quote)


def _item(source, id_, name, url, desc, pop=None, pop_label="", updated=""):
    return {"id": f"{source}:{id_}", "source": source, "name": html.unescape(name), "url": url,
            "desc": re.sub(r"\s+", " ", html.unescape(desc or "")).strip()[:240],
            "popularity": pop, "pop_label": pop_label, "updated": (updated or "")[:10]}


def _walk(terms, rung, min_terms=2):
    """沿梯子往下走，拿到结果就停。"""
    for q in ladder(terms, min_terms):
        items = rung(q)
        if items:
            return items
    return []


def hackernews(terms, core):
    def rung(q):
        d = json.loads(_get("https://hn.algolia.com/api/v1/search?" + _q({"query": q, "hitsPerPage": 20, "tags": "story"})))
        out = []
        for h in d.get("hits", []):
            title = h.get("title") or ""
            if not title:
                continue
            desc = re.sub(r"<[^>]+>", " ", h.get("story_text") or "") or (h.get("url") or "")
            out.append(_item("hackernews", h["objectID"], title, f"https://news.ycombinator.com/item?id={h['objectID']}",
                             desc, h.get("points"), "▲"))
            out[-1]["homepage"] = h.get("url") or ""
        return out
    return _walk(terms, rung)


def npm(terms, core):
    def rung(q):
        d = json.loads(_get("https://registry.npmjs.org/-/v1/search?" + _q({"text": q, "size": 20})))
        out = []
        for o in d.get("objects", []):
            p = o["package"]
            dl = (o.get("downloads") or {}).get("weekly")
            out.append(_item("npm", p["name"], p["name"], f"https://www.npmjs.com/package/{p['name']}",
                             p.get("description"), dl, "↓/周" if dl is not None else "", p.get("date")))
        return out
    return _walk(terms, rung)


def crates(terms, core):
    def rung(q):
        d = json.loads(_get("https://crates.io/api/v1/crates?" + _q({"q": q, "per_page": 20})))
        return [_item("crates", c["name"], c["name"], f"https://crates.io/crates/{c['name']}", c.get("description"),
                      c.get("downloads"), "↓", c.get("updated_at")) for c in d.get("crates", [])]
    return _walk(terms, rung)


_BREW_CACHE = config.DATA_DIR / "homebrew.json"


def _brew_catalog():
    if _BREW_CACHE.exists() and time.time() - _BREW_CACHE.stat().st_mtime < 86400:
        return json.loads(_BREW_CACHE.read_text())
    cat = []
    for kind, url in (("formula", "https://formulae.brew.sh/api/formula.json"),
                      ("cask", "https://formulae.brew.sh/api/cask.json")):
        for p in json.loads(_get(url, timeout=30)):
            name = p.get("name") if kind == "formula" else p.get("token")
            if isinstance(name, list):
                name = name[0]
            cat.append({"kind": kind, "name": name, "desc": p.get("desc") or "", "homepage": p.get("homepage") or ""})
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    _BREW_CACHE.write_text(json.dumps(cat))
    return cat


def homebrew(terms, core):
    cat = _brew_catalog()

    def rung(q):
        words = q.split()
        out = []
        for p in cat:
            text = (p["name"] + " " + p["desc"]).lower()
            if all(w in text for w in words):
                flag = "--cask " if p["kind"] == "cask" else ""
                it = _item("homebrew", p["name"], p["name"], f"https://formulae.brew.sh/{p['kind']}/{p['name']}", p["desc"])
                it["homepage"], it["install"] = p["homepage"], f"brew install {flag}{p['name']}"
                out.append(it)
        return out[:20]
    return _walk(terms, rung)


def vscode(terms, core):
    def rung(q):
        body = json.dumps({"filters": [{"criteria": [{"filterType": 8, "value": "Microsoft.VisualStudio.Code"},
                                                      {"filterType": 10, "value": q}],
                                        "pageSize": 20}], "flags": 914}).encode()
        d = json.loads(_get("https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery", data=body,
                            headers={"Content-Type": "application/json",
                                     "Accept": "application/json;api-version=7.1-preview.1"}))
        out = []
        for e in (d.get("results") or [{}])[0].get("extensions", []):
            if not e.get("shortDescription"):
                continue
            ident = f"{e['publisher']['publisherName']}.{e['extensionName']}"
            installs = next((s["value"] for s in e.get("statistics", []) if s["statisticName"] == "install"), None)
            out.append(_item("vscode", ident, e.get("displayName") or ident,
                             f"https://marketplace.visualstudio.com/items?itemName={ident}", e["shortDescription"],
                             int(installs) if installs else None, "↓", e.get("lastUpdated")))
            out[-1]["install"] = f"code --install-extension {ident}"
        return out
    return _walk(terms, rung)


def arxiv(terms, core):
    t = extract_terms(core)[:ARXIV_MAX_TERMS] or terms[:ARXIV_MAX_TERMS]
    atom = "{http://www.w3.org/2005/Atom}"
    for size in range(len(t), 1, -1):
        sq = " AND ".join(f"all:{x}" for x in t[:size])
        url = "https://export.arxiv.org/api/query?" + _q({"search_query": sq, "sortBy": "relevance", "max_results": 10})
        root = ET.fromstring(_get(url, headers={"Connection": "close"}, timeout=20))
        out = []
        for e in root.findall(f"{atom}entry"):
            title = " ".join((e.findtext(f"{atom}title") or "").split())
            link = (e.findtext(f"{atom}id") or "").strip()
            if title:
                out.append(_item("arxiv", link.rsplit("/", 1)[-1], title, link,
                                 e.findtext(f"{atom}summary"), None, "", e.findtext(f"{atom}published")))
        if out:
            return out
    return []


def huggingface(terms, core):
    out = []
    d = json.loads(_get("https://huggingface.co/api/papers/search?" + _q({"q": core, "limit": 10})))
    for r in d if isinstance(d, list) else []:
        p = r.get("paper") if isinstance(r.get("paper"), dict) else r
        if p.get("id") and p.get("title"):
            it = _item("huggingface", "paper/" + p["id"], p["title"], f"https://huggingface.co/papers/{p['id']}",
                       p.get("summary"), p.get("upvotes"), "▲", p.get("publishedAt"))
            it["homepage"] = p.get("githubRepo") or ""
            out.append(it)
    # Space = 在线可直接试用的 demo，对"有没有现成能用的"最直接
    for q in ladder(terms, 1)[:3]:
        d = json.loads(_get("https://huggingface.co/api/spaces?" + _q({"search": q, "limit": 10, "sort": "likes", "full": "true"})))
        for s in d:
            card = s.get("cardData") or {}
            out.append(_item("huggingface", "space/" + s["id"], s["id"], f"https://huggingface.co/spaces/{s['id']}",
                             card.get("short_description") or card.get("title") or "", s.get("likes"), "♥",
                             s.get("lastModified")))
        if d:
            break
    return out


SOURCES = {"hackernews": hackernews, "npm": npm, "crates": crates, "homebrew": homebrew,
           "vscode": vscode, "arxiv": arxiv, "huggingface": huggingface}
LABELS = {"github": "GitHub", "hackernews": "Hacker News", "npm": "npm", "crates": "crates.io",
          "homebrew": "Homebrew", "vscode": "VS Code 市场", "arxiv": "arXiv", "huggingface": "Hugging Face",
          "web": "全网"}


def search_all(selected, keywords, core):
    """并发搜选中的来源。返回 (items, status)；status 记录每个来源是否真的响应了。"""
    terms = []
    for k in [*keywords, core]:  # 关键词是专门为搜索写的，排前面
        for t in extract_terms(k):
            if t not in terms:
                terms.append(t)
    terms = terms[:6]

    def run(name):
        t0 = time.time()
        try:
            items = SOURCES[name](terms, core)
            kept = [i for i in items if admissible(i["name"] + " " + i["desc"], terms)]
            return name, kept, {"ok": True, "n": len(kept), "raw": len(items), "ms": int((time.time() - t0) * 1000)}
        except Exception as e:
            return name, [], {"ok": False, "error": str(e)[:120]}

    items, status = [], {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        for name, kept, st in ex.map(run, sorted(selected)):
            items += kept
            status[name] = st
    return items, status
