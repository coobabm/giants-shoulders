"""全局配置。都可以用环境变量覆盖。"""
import json
import re
import os
from pathlib import Path

HOME = Path.home()
DATA_DIR = Path(os.environ.get("DEJA_HOME", HOME / ".deja-repo"))
DB_PATH = DATA_DIR / "deja.db"

# 会话来源
CLAUDE_DIR = Path(os.environ.get("DEJA_CLAUDE_DIR", HOME / ".claude" / "projects"))
CODEX_DIR = Path(os.environ.get("DEJA_CODEX_DIR", HOME / ".codex" / "sessions"))

# 本地已有能力（用来判断"你自己是不是已经装过类似的"）
SKILL_GLOBS = [
    (HOME / ".claude" / "skills", "*/SKILL.md"),
    (HOME / ".codex" / "skills", "*/SKILL.md"),
    (HOME / ".claude" / "plugins" / "marketplaces", "**/skills/*/SKILL.md"),
]

# 会话数据来源：本机运行的 AgentsView（原版，不改代码）
AGENTSVIEW = os.environ.get("DEJA_AGENTSVIEW", "http://127.0.0.1:8080").rstrip("/")
PAGE_PATH = DATA_DIR / "radar.html"

HOST = "127.0.0.1"
PORT = int(os.environ.get("DEJA_PORT", 4747))
POLL_SECONDS = float(os.environ.get("DEJA_POLL", 5))

# 首次启动时回看多久的历史消息，以及最多处理几条
BACKFILL_HOURS = float(os.environ.get("DEJA_BACKFILL_HOURS", 24))
BACKFILL_MAX = int(os.environ.get("DEJA_BACKFILL_MAX", 6))

# 模型分工：便宜的做过滤，强的做关键词和判断。优先级：环境变量 DEJA_MODEL_<环节> > 页面设置（models.json）> 默认
MODEL_STAGES = {
    "gate": ("haiku", "判断是不是要造新东西"),
    "web": ("haiku", "全网侦察（只搬运搜索结果）"),
    "keywords": ("sonnet", "拆部件、想搜索关键词"),
    "judge": ("sonnet", "按部件核验候选"),
    "code": ("sonnet", "代码侦察 agent"),
    "group": ("sonnet", "把会话归成任务"),
    "deep": ("opus", "深挖：按项目的问题找参考"),
}
WEB_STAGES = {"web": "全网侦察", "deep": "深挖的点名那一步"}   # 要用 WebSearch 的环节
MODELS_FILE = DATA_DIR / "models.json"
_NATIVE = re.compile(r"(haiku|sonnet|opus|fable|best|default)(\[1m\])?|claude-(\d[\d.-]*-)?(haiku|sonnet|opus|fable)(-\d+(\.\d+)?)*(-\d{8})?(\[1m\])?")


def native(m):
    """Anthropic 自家的模型（订阅能用、WebSearch 能用）。中转站转发的 GPT 之类返回 False。"""
    return bool(_NATIVE.fullmatch((m or "").strip().lower()))


def web_model(stage):
    """要搜网的环节：选的是非 Claude 模型时退回这个环节的默认 Claude 模型（WebSearch 是 Anthropic 服务端工具，转给别家模型会静默失效）。"""
    m = model(stage)
    return m if native(m) else MODEL_STAGES[stage][0]


def model(stage):
    env = os.environ.get(f"DEJA_MODEL_{stage.upper()}")
    if env:
        return env
    try:
        saved = json.loads(MODELS_FILE.read_text()).get(stage)
    except (OSError, ValueError):
        saved = None
    return saved or MODEL_STAGES[stage][0]


def save_models(models):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    clean = {k: str(v).strip() for k, v in models.items() if k in MODEL_STAGES and str(v).strip()}
    MODELS_FILE.write_text(json.dumps(clean, ensure_ascii=False, indent=1))


# 其他页面设置（settings.json）
SETTINGS_FILE = DATA_DIR / "settings.json"
SETTING_DEFAULTS = {"deep_budget": 2.0}    # 每次深挖的花费上限（美元，订阅下是折算值）


def setting(key):
    try:
        v = json.loads(SETTINGS_FILE.read_text()).get(key)
    except (OSError, ValueError):
        v = None
    return SETTING_DEFAULTS[key] if v is None else v


def save_settings(**kw):
    try:
        cur = json.loads(SETTINGS_FILE.read_text())
    except (OSError, ValueError):
        cur = {}
    cur.update({k: v for k, v in kw.items() if k in SETTING_DEFAULTS})
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(cur, ensure_ascii=False, indent=1))


# 代码侦察：克隆前几名候选仓库读代码，顺便读你当前的项目
DEEPDIVE = os.environ.get("DEJA_DEEPDIVE", "1") == "1"
DEEPDIVE_TOP = int(os.environ.get("DEJA_DEEPDIVE_TOP", 3))
DEEPDIVE_PROJECT = os.environ.get("DEJA_DEEPDIVE_PROJECT", "1") == "1"
CODE_BUDGET_USD = float(os.environ.get("DEJA_CODE_BUDGET", 0.6))   # 每个 agent 的花费上限
CODE_MAX_CALLS = int(os.environ.get("DEJA_CODE_MAX_CALLS", 40))

MAX_KEYWORDS = 6
CANDIDATES = 12      # 进入核验的候选仓库数
README_TOP = 10      # 读 README 的仓库数
README_CHARS = 2500
MIN_STARS = 3

# 同一段文字在 Claude/Codex 里重复发送时合并（24 小时内）
DUP_WINDOW_SECONDS = 24 * 3600
