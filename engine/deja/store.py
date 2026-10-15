"""SQLite 存储：文件读取进度、雷达报告。"""
import json
import sqlite3
import threading
import time

from . import config

_lock = threading.Lock()
_conn = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS offsets (path TEXT PRIMARY KEY, pos INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS reports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created REAL, updated REAL,
  source TEXT, session TEXT, cwd TEXT,
  message TEXT, msg_ts REAL, norm TEXT,
  status TEXT,      -- queued / gate / keywords / searching / judging / done / skipped / error
  summary TEXT, verdict TEXT,
  data TEXT,        -- JSON：关键词、仓库、本地重叠、成本等
  cost REAL DEFAULT 0,
  error TEXT,
  also_in TEXT DEFAULT '[]',
  pinned INTEGER DEFAULT 0, hidden INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_reports_created ON reports(created);
CREATE INDEX IF NOT EXISTS idx_reports_norm ON reports(norm);
"""


def conn():
    global _conn
    if _conn is None:
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.executescript(SCHEMA)
        _conn.execute("PRAGMA journal_mode=WAL")
    return _conn


def q(sql, args=(), one=False):
    with _lock:
        cur = conn().execute(sql, args)
        conn().commit()
        rows = cur.fetchall()
    return (rows[0] if rows else None) if one else rows


# ---- 读取进度 ----

def get_offsets():
    return {r["path"]: r["pos"] for r in q("SELECT path, pos FROM offsets")}


def set_offset(path, pos):
    q("INSERT INTO offsets(path, pos) VALUES(?, ?) "
      "ON CONFLICT(path) DO UPDATE SET pos=excluded.pos", (str(path), pos))


def get_meta(key, default=None):
    r = q("SELECT value FROM meta WHERE key=?", (key,), one=True)
    return r["value"] if r else default


def set_meta(key, value):
    q("INSERT INTO meta(key, value) VALUES(?, ?) "
      "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))


# ---- 报告 ----

def add_report(msg, status="queued"):
    now = time.time()
    with _lock:
        cur = conn().execute(
            "INSERT INTO reports(created, updated, source, session, cwd, message, msg_ts, norm, status, data) "
            "VALUES(?,?,?,?,?,?,?,?,?,?)",
            (now, now, msg["source"], msg.get("session", ""), msg.get("cwd", ""),
             msg["text"], msg.get("ts", now), msg.get("norm", ""), status, "{}"))
        conn().commit()
        return cur.lastrowid


def update_report(rid, **fields):
    if "data" in fields and not isinstance(fields["data"], str):
        fields["data"] = json.dumps(fields["data"], ensure_ascii=False)
    fields["updated"] = time.time()
    cols = ", ".join(f"{k}=?" for k in fields)
    q(f"UPDATE reports SET {cols} WHERE id=?", (*fields.values(), rid))


def get_report(rid):
    r = q("SELECT * FROM reports WHERE id=?", (rid,), one=True)
    return _row(r) if r else None


def find_duplicate(norm, ts):
    """同一句话在时间窗口内已经出现过（比如同时发给 Claude 和 Codex）。"""
    return q("SELECT id, also_in, source FROM reports WHERE norm=? AND msg_ts > ? ORDER BY id LIMIT 1",
             (norm, ts - config.DUP_WINDOW_SECONDS), one=True)


def add_also_in(rid, source):
    r = q("SELECT also_in FROM reports WHERE id=?", (rid,), one=True)
    lst = json.loads(r["also_in"] or "[]")
    if source not in lst:
        lst.append(source)
    q("UPDATE reports SET also_in=? WHERE id=?", (json.dumps(lst), rid))


def recent_session_summaries(session, limit=3):
    rows = q("SELECT summary FROM reports WHERE session=? AND status='done' AND summary IS NOT NULL "
             "ORDER BY id DESC LIMIT ?", (session, limit))
    return [r["summary"] for r in rows]


def list_reports(include_skipped=False, limit=150, session=None):
    where = "hidden=0" + ("" if include_skipped else " AND status!='skipped'")
    args = []
    if session:
        where += " AND session=?"
        args.append(session)
    rows = q(f"SELECT * FROM reports WHERE {where} ORDER BY pinned DESC, id DESC LIMIT ?", (*args, limit))
    return [_row(r) for r in rows]


def stats():
    r = q("SELECT COUNT(*) n, "
          "SUM(status='done') done, SUM(status='skipped') skipped, "
          "SUM(status NOT IN ('done','skipped','error')) running, SUM(status='error') errors, "
          "COALESCE(SUM(cost),0) cost FROM reports", one=True)
    return dict(r)


def _row(r):
    d = dict(r)
    d["data"] = json.loads(d.get("data") or "{}")
    d["also_in"] = json.loads(d.get("also_in") or "[]")
    d.pop("norm", None)
    return d
