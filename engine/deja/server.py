"""本机小服务：打开就是最新的雷达页面，页面里能改模型 / Base URL / API key，能对一个任务点"深挖"。

只监听 127.0.0.1。所有 /api 请求要带页面里的随机 token（X-Radar-Token），并且校验 Host 头，
别的网站不能借你的浏览器调用它，也读不到 API key（接口只返回掩码）。
"""
import json
import secrets
import sys
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import auth, config, group, store

PORT = int(__import__("os").environ.get("DEJA_PAGE_PORT", 4848))
TOKEN_FILE = config.DATA_DIR / "token"
_deep_running = {}
_lock = threading.Lock()


def token():
    if not TOKEN_FILE.exists():
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.touch(mode=0o600)
        TOKEN_FILE.write_text(secrets.token_urlsafe(24))
    return TOKEN_FILE.read_text().strip()


def url():
    return f"http://127.0.0.1:{PORT}/"


def alive():
    try:
        with urllib.request.urlopen(url() + "ping", timeout=2) as r:
            return r.read() == b"radar"
    except Exception:
        return False


def settings():
    return {**auth.info(), "modes": list(auth.MODES), "deep_budget": config.setting("deep_budget"),
            "models": {k: config.model(k) for k in config.MODEL_STAGES},
            "stages": {k: {"default": d, "label": label, "web": config.WEB_STAGES.get(k)} for k, (d, label) in config.MODEL_STAGES.items()}}


def launch(rid, idx, root, prompt):
    """在终端里开一个 Claude Code 会话做这个卡点：写一个 .command 文件再 open（不需要 AppleScript 权限）。"""
    import os
    import shlex
    import subprocess
    from pathlib import Path
    from . import deep
    root = str(Path(root).expanduser())
    if not Path(root).is_dir():
        raise ValueError(f"目录不存在：{root}")
    if not prompt.strip():
        raise ValueError("提示词是空的")
    d = config.DATA_DIR / "todo"
    d.mkdir(parents=True, exist_ok=True)
    md = d / f"{rid}-{idx}.md"
    md.write_text(prompt)
    sh = d / f"{rid}-{idx}.command"
    sh.write_text(f"#!/bin/sh\ncd {shlex.quote(root)} || exit 1\nexec claude \"$(cat {shlex.quote(str(md))})\"\n")
    os.chmod(sh, 0o700)
    subprocess.run(["open", str(sh)], check=True)
    return deep.set_todo(rid, idx, "doing")


def _deep(gid, rid, full):
    from . import deep
    try:
        deep.run(gid, rid, full=full)
    finally:
        with _lock:
            _deep_running.pop(gid, None)


def start_deep(gid, full=False):
    with _lock:
        if gid in _deep_running:
            return _deep_running[gid]
        g = next((x for x in group.load()["groups"] if x["id"] == gid), None)
        if not g:
            raise ValueError("没有这个任务")
        rid = store.add_report({"source": "deep", "text": f"深挖：{g['name']}", "norm": f"deep {gid}"})
        st = group.load()
        st["assign"][f"r:{rid}"] = gid
        group.save(st)
        _deep_running[gid] = rid
    threading.Thread(target=_deep, args=(gid, rid, full), daemon=True).start()
    return rid


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _host_ok(self):
        return self.headers.get("Host", "") in (f"127.0.0.1:{PORT}", f"localhost:{PORT}")

    def _auth_ok(self):
        origin = self.headers.get("Origin")
        if origin and origin not in (f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"):
            return False
        return self._host_ok() and secrets.compare_digest(self.headers.get("X-Radar-Token", ""), token())

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if not isinstance(body, (bytes, str)):
            body = json.dumps(body, ensure_ascii=False)
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _json(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > 100_000:
            raise ValueError("请求太大")
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/ping":
            return self._send(200, "radar", "text/plain")
        if not self._host_ok():
            return self._send(403, {"error": "host"})
        if u.path in ("/", "/index.html"):
            from . import page
            regroup = "regroup" in parse_qs(u.query)
            html = page.build(regroup=regroup, server={"token": token()})
            return self._send(200, html, "text/html; charset=utf-8")
        if not self._auth_ok():
            return self._send(403, {"error": "token"})
        if u.path == "/api/settings":
            return self._send(200, settings())
        if u.path == "/api/deep/plan":
            from . import deep
            q = parse_qs(u.query)
            try:
                return self._send(200, deep.plan((q.get("task") or [""])[0], full="full" in q))
            except Exception as e:
                return self._send(400, {"error": str(e)[:300]})
        if u.path == "/api/todo/prompt":
            from . import deep
            q = parse_qs(u.query)
            rid, idx = int(q["id"][0]), int(q["idx"][0])
            d = store.get_report(rid)["data"]
            g = next((x for x in group.load()["groups"] if x["id"] == d.get("task")), {})
            return self._send(200, {"prompt": deep.todo_prompt(rid, idx), "root": g.get("root") or d.get("root") or ""})
        if u.path == "/api/models":
            try:
                ms = auth.list_models()
                return self._send(200, {"models": ms, "base_url": auth.base_url(),
                                        "names": {m: auth.display_name(m) for m in ms if auth.display_name(m) != m},
                                        "native": {m: config.native(m) for m in ms}})
            except Exception as e:
                return self._send(400, {"error": str(e)[:300]})
        if u.path == "/api/report":
            rid = int((parse_qs(u.query).get("id") or ["0"])[0])
            r = store.get_report(rid)
            return self._send(200 if r else 404, r or {"error": "没有这份报告"})
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if not self._auth_ok():
            return self._send(403, {"error": "token"})
        path = urlparse(self.path).path
        try:
            body = self._json()
            if path == "/api/settings":
                if body.get("mode") in auth.MODES:
                    auth.set_mode(body["mode"])
                if "base_url" in body:
                    auth.set_base_url(body["base_url"])
                if body.get("clear_key"):
                    auth.clear_key()
                if (body.get("api_key") or "").strip():
                    auth.save_key(body["api_key"])
                if isinstance(body.get("models"), dict):
                    config.save_models(body["models"])
                if body.get("deep_budget") not in (None, ""):
                    b = float(body["deep_budget"])
                    if not 0.1 <= b <= 50:
                        raise ValueError("每次深挖上限要在 $0.1–50 之间")
                    config.save_settings(deep_budget=b)
                return self._send(200, settings())
            if path == "/api/test":
                from .llm import ask
                schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]}
                stage = body.get("stage") or "gate"
                out, cost, model = ask('只回答 {"ok": true}', schema, config.model(stage), timeout=120)
                return self._send(200, {"ok": True, "model": model, "cost": cost, "mode": auth.mode()})
            if path == "/api/deep":
                from . import deep
                gid = str(body.get("task") or "")
                if "root" in body:
                    deep.set_root(gid, body["root"])
                return self._send(200, {"id": start_deep(gid, full=bool(body.get("full")))})
            if path == "/api/todo":
                from . import deep
                return self._send(200, {"todo": deep.set_todo(int(body["id"]), int(body["idx"]), body["status"])})
            if path == "/api/launch":
                return self._send(200, {"todo": launch(int(body["id"]), int(body["idx"]), body.get("root") or "",
                                                       body.get("prompt") or "")})
        except Exception as e:
            return self._send(400, {"error": str(e)[:300]})
        self._send(404, {"error": "not found"})


def serve():
    token()
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"巨人的肩膀页面：{url()}（Ctrl-C 停止）", file=sys.stderr)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
