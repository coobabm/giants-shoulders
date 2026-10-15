"""增量读取 Claude Code / Codex 的会话 jsonl，吐出"用户亲手打的消息"。"""
import json
import re
from datetime import datetime
from pathlib import Path

from . import config, store


def _ts(iso):
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def normalize(text):
    return re.sub(r"\s+", " ", text).strip().lower()[:500]


# ---- 解析单行 ----

def parse_claude(line, ctx):
    d = json.loads(line)
    if d.get("type") != "user" or d.get("isMeta") or d.get("isSidechain"):
        return None
    c = (d.get("message") or {}).get("content")
    if isinstance(c, list):
        if any(x.get("type") == "tool_result" for x in c):
            return None
        c = "\n".join(x.get("text", "") for x in c if x.get("type") == "text")
    if not isinstance(c, str):
        return None
    text = c.strip()
    # 斜杠命令输出、系统注入、hook 回显等都以标签开头
    if not text or text.startswith("<") or text.startswith("[Request interrupted"):
        return None
    return {"source": "claude", "session": d.get("sessionId", ""), "cwd": d.get("cwd", ""),
            "text": text, "ts": _ts(d.get("timestamp", "")) or 0}


def parse_codex(line, ctx):
    d = json.loads(line)
    p = d.get("payload") or {}
    if d.get("type") == "session_meta":
        ctx["session"] = p.get("id", "")
        ctx["cwd"] = p.get("cwd", "")
        return None
    if d.get("type") != "event_msg" or p.get("type") != "user_message":
        return None
    text = (p.get("message") or "").strip()
    if not text or text.startswith("<"):  # 子代理通知等系统注入
        return None
    return {"source": "codex", "session": ctx.get("session", ""), "cwd": ctx.get("cwd", ""),
            "text": text, "ts": _ts(d.get("timestamp", "")) or 0}


def _codex_ctx(path):
    """Codex 的 cwd/session 只写在第一行，续读时要补回来。"""
    try:
        with open(path, "rb") as f:
            first = json.loads(f.readline())
        p = first.get("payload") or {}
        if first.get("type") == "session_meta":
            return {"session": p.get("id", ""), "cwd": p.get("cwd", "")}
    except Exception:
        pass
    return {}


SOURCES = [
    ("claude", config.CLAUDE_DIR, parse_claude),
    ("codex", config.CODEX_DIR, parse_codex),
]


def list_files():
    for name, root, parser in SOURCES:
        if not root.exists():
            continue
        for p in root.rglob("*.jsonl"):
            if "subagents" in p.parts:
                continue
            yield name, p, parser


class Watcher:
    """每次 poll() 返回自上次以来新出现的用户消息。"""

    def __init__(self):
        self.offsets = store.get_offsets()
        self.mtimes = {}
        self.files = 0

    def bootstrap(self, backfill_hours):
        """首次运行：所有文件跳到末尾，只回看最近 N 小时。"""
        if store.get_meta("bootstrapped"):
            return []
        import time
        cutoff = time.time() - backfill_hours * 3600
        msgs = []
        for name, path, parser in list_files():
            size = path.stat().st_size
            if path.stat().st_mtime >= cutoff:
                msgs += [m for m in self._read(path, parser, 0)[0] if m["ts"] >= cutoff]
            self.offsets[str(path)] = size
            store.set_offset(path, size)
        store.set_meta("bootstrapped", "1")
        msgs.sort(key=lambda m: m["ts"])
        return msgs

    def poll(self):
        out = []
        n = 0
        for name, path, parser in list_files():
            n += 1
            key = str(path)
            try:
                st = path.stat()
            except FileNotFoundError:
                continue
            if self.mtimes.get(key) == st.st_mtime:
                continue
            self.mtimes[key] = st.st_mtime
            pos = self.offsets.get(key, 0)
            if st.st_size < pos:  # 文件被重写
                pos = 0
            if st.st_size == pos:
                continue
            msgs, new_pos = self._read(path, parser, pos)
            self.offsets[key] = new_pos
            store.set_offset(path, new_pos)
            out += msgs
        self.files = n
        return out

    def _read(self, path, parser, pos):
        ctx = _codex_ctx(path) if parser is parse_codex else {}
        msgs = []
        with open(path, "rb") as f:
            f.seek(pos)
            chunk = f.read()
        end = chunk.rfind(b"\n")
        if end < 0:
            return [], pos
        for raw in chunk[:end].split(b"\n"):
            if not raw.strip():
                continue
            try:
                m = parser(raw.decode("utf-8", "replace"), ctx)
            except Exception:
                continue
            if m:
                m["norm"] = normalize(m["text"])
                msgs.append(m)
        return msgs, pos + end + 1
