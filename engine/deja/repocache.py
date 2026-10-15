"""把候选仓库安全地浅克隆到本地缓存，给代码侦察 agent 读。

仓库是不可信数据：只克隆、不执行。
  - 不跑 hooks、不拉子模块、不下 LFS、不提示输入凭证
  - core.symlinks=false：符号链接检出成普通文本文件，不会指向仓库外
  - 只要最新一次提交，单个文件超过 1MB 的不下载
缓存在 ~/.deja-repo/repos/<owner>__<repo>，7 天内复用。
"""
import os
import re
import shutil
import subprocess
import time

from . import config

REPOS = config.DATA_DIR / "repos"
MAX_AGE = 7 * 86400
MAX_MB = 300
NAME = re.compile(r"^[\w.-]+/[\w.-]+$")


def _size_mb(path):
    total = 0
    for dirpath, _, files in os.walk(path):
        for f in files:
            try:
                total += os.lstat(os.path.join(dirpath, f)).st_size
            except OSError:
                pass
    return total / 1e6


def fetch(full_name, timeout=120):
    """返回本地路径；失败返回 None。"""
    if not NAME.match(full_name) or ".." in full_name:
        return None
    dest = REPOS / full_name.replace("/", "__")
    if dest.exists() and time.time() - dest.stat().st_mtime < MAX_AGE:
        return dest
    shutil.rmtree(dest, ignore_errors=True)
    REPOS.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_LFS_SKIP_SMUDGE": "1"}
    cmd = ["git", "-c", "core.hooksPath=/dev/null", "-c", "core.symlinks=false", "-c", "protocol.file.allow=never",
           "clone", "--depth", "1", "--single-branch", "--no-recurse-submodules", "--filter=blob:limit=1m",
           "--quiet", f"https://github.com/{full_name}.git", str(dest)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        shutil.rmtree(dest, ignore_errors=True)
        return None
    if r.returncode != 0 or not dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
        return None
    if _size_mb(dest) > MAX_MB:
        shutil.rmtree(dest, ignore_errors=True)
        return None
    shutil.rmtree(dest / ".git", ignore_errors=True)  # 只留源码，agent 也就看不到 git 历史里的东西
    os.utime(dest)
    return dest


def prune():
    """清掉过期缓存。"""
    if not REPOS.exists():
        return
    for p in REPOS.iterdir():
        if time.time() - p.stat().st_mtime > MAX_AGE:
            shutil.rmtree(p, ignore_errors=True)
