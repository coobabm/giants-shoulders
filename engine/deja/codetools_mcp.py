"""代码侦察 agent 的工具箱：一个只读、锁在根目录里的 MCP 服务（stdio，纯标准库）。

agent 只能用这里的 5 个工具看代码：stats / tree / find / grep / read。
不能执行任何东西，不能联网，路径逃不出根目录（符号链接也解析后再判断），
.env、私钥这类文件一律不给读。调用次数有上限，用完就提示 agent 收尾。

用法：python3 -I -m deja.codetools_mcp <root>   （由 codeagent.py 通过 --mcp-config 拉起）
"""
import fnmatch
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", "vendor", "dist", "build", "out", "target", "__pycache__", ".venv", "venv",
             ".next", ".nuxt", ".cache", "coverage", ".idea", ".vscode", "Library", "Temp", "obj", "Pods"}
SECRET = re.compile(r"(^\.env|\.pem$|\.key$|^id_rsa|^id_ed25519|credentials|\.p12$|\.keystore$|secret)", re.I)
MAX_CALLS = int(os.environ.get("DEJA_CODE_MAX_CALLS", 45))
MAX_FILE = 1_000_000
calls = 0
ROOT = Path(".")


def _safe(rel):
    p = (ROOT / (rel or ".")).resolve()
    if p != ROOT and ROOT not in p.parents:
        raise ValueError(f"路径不在仓库里：{rel}")
    return p


def _rel(p):
    return str(p.relative_to(ROOT)) or "."


def _walk(base):
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        for f in sorted(filenames):
            p = Path(dirpath) / f
            if p.is_symlink():  # 符号链接可能指向仓库外，一律跳过
                continue
            yield p


def _is_text(p):
    try:
        if p.stat().st_size > MAX_FILE:
            return False
        with open(p, "rb") as fh:
            return b"\0" not in fh.read(4096)
    except OSError:
        return False


def t_stats(_):
    exts, files, loc, tests, manifests = Counter(), 0, 0, 0, []
    for p in _walk(ROOT):
        files += 1
        exts[p.suffix.lower() or p.name] += 1
        if re.search(r"(^|/)(tests?|__tests__|spec)(/|$)|_test\.|\.test\.|\.spec\.", _rel(p)):
            tests += 1
        if p.name in ("package.json", "pyproject.toml", "setup.py", "requirements.txt", "Cargo.toml", "go.mod",
                      "pom.xml", "build.gradle", "Gemfile", "composer.json", "Makefile", "Dockerfile"):
            manifests.append(_rel(p))
        if files <= 3000 and _is_text(p):
            try:
                loc += sum(1 for _ in open(p, "rb"))
            except OSError:
                pass
    top = ", ".join(f"{k}×{v}" for k, v in exts.most_common(12))
    return (f"文件 {files} 个，约 {loc} 行（前 3000 个文件）\n测试相关文件 {tests} 个\n"
            f"清单文件：{', '.join(manifests[:20]) or '无'}\n扩展名：{top}")


def t_tree(a):
    base = _safe(a.get("path"))
    depth = min(int(a.get("depth", 2)), 4)
    out = []
    for p in _walk(base):
        rel = p.relative_to(base)
        if len(rel.parts) <= depth:
            out.append(f"{_rel(p)}  ({p.stat().st_size} B)")
        if len(out) >= 400:
            out.append("…（截断）")
            break
    return "\n".join(out) or "（空）"


def t_find(a):
    pat = a.get("glob") or "*"
    base = _safe(a.get("path"))
    out = [_rel(p) for p in _walk(base) if fnmatch.fnmatch(p.name, pat) or fnmatch.fnmatch(_rel(p), pat)]
    return "\n".join(out[:200]) + ("\n…（截断）" if len(out) > 200 else "") if out else "没找到"


def t_grep(a):
    rx = re.compile(a["pattern"], re.I if a.get("ignore_case", True) else 0)
    base = _safe(a.get("path"))
    glob = a.get("glob")
    out = []
    for p in _walk(base):
        if glob and not fnmatch.fnmatch(p.name, glob):
            continue
        if SECRET.search(p.name) or not _is_text(p):
            continue
        try:
            for n, line in enumerate(open(p, encoding="utf-8", errors="replace"), 1):
                if rx.search(line):
                    out.append(f"{_rel(p)}:{n}: {line.strip()[:200]}")
                    if len(out) >= 80:
                        return "\n".join(out) + "\n…（截断，缩小范围再搜）"
        except OSError:
            continue
    return "\n".join(out) or "没有匹配"


def t_read(a):
    p = _safe(a["path"])
    if SECRET.search(p.name):
        return "这个文件可能含密钥，不读。"
    if not p.is_file() or not _is_text(p):
        return "不是可读的文本文件"
    start = max(int(a.get("start", 1)), 1)
    n = min(int(a.get("lines", 200)), 400)
    lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
    chunk = lines[start - 1:start - 1 + n]
    body = "\n".join(f"{start + i:>5}  {l[:300]}" for i, l in enumerate(chunk))
    more = f"\n…（共 {len(lines)} 行，用 start 往下读）" if start - 1 + n < len(lines) else ""
    return body + more


TOOLS = [
    ("stats", "仓库概况：文件数、代码行数、测试数、清单文件、语言分布。先调这个。", {}, t_stats),
    ("tree", "列出目录结构（跳过 node_modules/.git 等）。", {"path": {"type": "string"}, "depth": {"type": "integer"}}, t_tree),
    ("find", "按文件名 glob 找文件，比如 *.py、*session*。", {"glob": {"type": "string"}, "path": {"type": "string"}}, t_find),
    ("grep", "按正则搜代码，返回 路径:行号: 内容。", {"pattern": {"type": "string"}, "path": {"type": "string"},
                                                   "glob": {"type": "string"}, "ignore_case": {"type": "boolean"}}, t_grep),
    ("read", "读文件的一段（带行号，默认 200 行，最多 400 行）。", {"path": {"type": "string"}, "start": {"type": "integer"},
                                                         "lines": {"type": "integer"}}, t_read),
]
REQUIRED = {"grep": ["pattern"], "read": ["path"]}


def handle(msg):
    global calls
    method, mid = msg.get("method"), msg.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "protocolVersion": msg.get("params", {}).get("protocolVersion", "2024-11-05"),
            "capabilities": {"tools": {}}, "serverInfo": {"name": "deja-code", "version": "0.1.0"}}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": [
            {"name": n, "description": d,
             "inputSchema": {"type": "object", "properties": props, "required": REQUIRED.get(n, [])}}
            for n, d, props, _ in TOOLS]}}
    if method == "tools/call":
        name = msg["params"]["name"]
        args = msg["params"].get("arguments") or {}
        calls += 1
        if calls > MAX_CALLS:
            text, err = "工具调用次数用完了，请根据已看到的内容直接给出结论。", True
        else:
            fn = next((f for n, _, _, f in TOOLS if n == name), None)
            try:
                text, err = (fn(args), False) if fn else (f"没有这个工具：{name}", True)
            except Exception as e:
                text, err = f"出错：{e}", True
        return {"jsonrpc": "2.0", "id": mid, "result": {"content": [{"type": "text", "text": text[:40000]}],
                                                        "isError": err}}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if mid is not None:
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"unknown method {method}"}}
    return None  # 通知不回复


def main():
    global ROOT
    ROOT = Path(sys.argv[1]).resolve()
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            out = handle(json.loads(line))
        except Exception as e:
            out = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(e)}}
        if out:
            sys.stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
