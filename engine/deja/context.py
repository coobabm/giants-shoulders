"""本地上下文：当前项目已经装了哪些依赖（思路来自 search-before-building：先看项目和已装依赖，再往外找），
以及外部仓库安装说明里的风险信号（思路来自 ECC 的 skill-scout：推荐外部东西前先审查 shell 命令和凭证处理）。"""
import json
import re
from pathlib import Path

MAX_DEPS = 120


def _read(p, limit=200_000):
    try:
        return p.read_text("utf-8", "replace")[:limit]
    except Exception:
        return ""


def project_deps(cwd):
    """返回 {清单文件: [依赖名]}。cwd 不存在或没有清单就是空。"""
    if not cwd:
        return {}
    root = Path(cwd)
    if not root.is_dir() or root == Path.home():
        return {}
    out = {}

    p = root / "package.json"
    if p.exists():
        try:
            d = json.loads(_read(p))
            out["package.json"] = sorted({*d.get("dependencies", {}), *d.get("devDependencies", {})})
        except Exception:
            pass
    for name in ("requirements.txt", "requirements-dev.txt"):
        p = root / name
        if p.exists():
            out[name] = [m.group(1) for m in re.finditer(r"^\s*([A-Za-z0-9_.\-\[\]]+)", _read(p), re.M)
                         if not m.group(1).startswith("-")]
    p = root / "pyproject.toml"
    if p.exists():
        block = re.search(r"dependencies\s*=\s*\[(.*?)\]", _read(p), re.S)
        if block:
            out["pyproject.toml"] = re.findall(r"[\"']([A-Za-z0-9_.\-]+)", block.group(1))
    p = root / "Cargo.toml"
    if p.exists():
        block = re.search(r"\[dependencies\](.*?)(\n\[|\Z)", _read(p), re.S)
        if block:
            out["Cargo.toml"] = re.findall(r"^\s*([A-Za-z0-9_\-]+)\s*=", block.group(1), re.M)
    p = root / "go.mod"
    if p.exists():
        out["go.mod"] = re.findall(r"^\s*([\w./\-]+)\s+v\d", _read(p), re.M)
    p = root / "Packages" / "manifest.json"  # Unity
    if p.exists():
        try:
            out["Packages/manifest.json"] = sorted(json.loads(_read(p)).get("dependencies", {}))
        except Exception:
            pass
    p = root / "Gemfile"
    if p.exists():
        out["Gemfile"] = re.findall(r"^\s*gem\s+[\"']([^\"']+)", _read(p), re.M)

    total, trimmed = 0, {}
    for k, v in out.items():
        v = [x for x in v if x][: max(0, MAX_DEPS - total)]
        if v:
            trimmed[k] = v
            total += len(v)
    return trimmed


RISK_PATTERNS = [
    (r"curl[^\n|]{0,200}\|\s*(sudo\s+)?(ba|z)?sh\b|wget[^\n|]{0,200}\|\s*(sudo\s+)?(ba|z)?sh\b|irm [^\n|]+\|\s*iex",
     "curl | sh 一键安装脚本，装前先读脚本"),
    (r"\bsudo\b", "安装需要 sudo"),
    (r"rm\s+-rf\s+[/~$]", "说明里有 rm -rf"),
    (r"dangerously-skip-permissions|bypassPermissions|--yolo|disable[^\n]{0,30}(sandbox|permission)",
     "要求关闭 AI 助手的权限确认"),
    (r"\bhooks?\.json\b|PreToolUse|PostToolUse|UserPromptSubmit|SessionStart",
     "会安装 hooks，每次操作都会运行"),
    (r"(OPENAI|ANTHROPIC|GEMINI|GOOGLE|HF|GITHUB)_[A-Z_]*(KEY|TOKEN)|api[_ -]?key", "需要第三方 API key"),
    (r"\bGPL-3|\bAGPL\b|GNU (Affero )?General Public", "GPL/AGPL 许可，闭源分发要注意"),
]


def risk_flags(text):
    flags = []
    for pat, label in RISK_PATTERNS:
        if re.search(pat, text or "", re.I) and label not in flags:
            flags.append(label)
    return flags
