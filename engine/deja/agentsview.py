"""从本机 AgentsView 的 HTTP API 读会话和用户消息（只读）。

AgentsView 负责解析 Claude Code、Codex 等 20 多种 agent 的会话文件；这里只拿它整理好的结果。
"""
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from . import config

# 系统注入、命令回显这类不是人打的 user 消息（和 AgentsView 的 SystemMsgPrefixes 一致）
SYSTEM_PREFIXES = ("This session is being continued", "[Request interrupted", "<task-notification>",
                   "<command-message>", "<command-name>", "<local-command-", "Stop hook feedback:",
                   "<system-reminder>", "<goal_context>", "<codex_internal_context", "Caveat:")


class Unavailable(Exception):
    pass


def _get(path, params=None, timeout=20):
    url = config.AGENTSVIEW + path
    if params:
        url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v not in (None, "")})
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
        raise Unavailable(f"AgentsView 没在运行（{config.AGENTSVIEW}）：{e}")


def alive():
    try:
        _get("/api/v1/sessions", {"limit": 1}, timeout=3)
        return True
    except Unavailable:
        return False


def sessions(hours=24, limit=100):
    """最近活跃的人类会话（不含子代理/自动化会话）。"""
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    d = _get("/api/v1/sessions", {"active_since": since, "limit": limit})
    return [s for s in d.get("sessions", []) if not s.get("is_automated")
            and s.get("relationship_type", "") != "subagent"]


def user_prompts(session_id, limit=300):
    """一个会话里人亲手打的消息。"""
    d = _get(f"/api/v1/sessions/{urllib.parse.quote(session_id, safe='')}/messages",
             {"roles": "user", "limit": limit})
    out = []
    for m in d.get("messages", []):
        text = (m.get("content") or "").strip()
        if m.get("role") != "user" or m.get("is_system") or m.get("is_sidechain"):
            continue
        if m.get("prompt_source") == "system" or not text or text.startswith(SYSTEM_PREFIXES):
            continue
        out.append({"ordinal": m.get("ordinal"), "text": text, "timestamp": m.get("timestamp", "")})
    return out


def ts(iso):
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
    except (ValueError, AttributeError):
        return time.time()
