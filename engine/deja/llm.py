"""通过 `claude -p` 无头调用模型：默认用已登录的 Claude 订阅，也可以用 API key（见 auth.py）。"""
import json
import shutil

from . import auth, config


class LLMError(RuntimeError):
    pass


def ask(prompt, schema, model, timeout=240, tools="", budget=None):
    exe = shutil.which("claude")
    if not exe:
        raise LLMError("找不到 claude 命令")
    cmd = [exe, "-p", "--model", model,
           "--no-session-persistence",          # 不写会话文件，避免被自己监听到
           "--setting-sources", "",             # 不加载用户 settings/hooks
           "--strict-mcp-config", "--tools", tools,  # 默认不给任何工具
           "--output-format", "json",
           "--json-schema", json.dumps(schema)]
    if tools:
        cmd += ["--allowedTools", tools]
    if budget:
        cmd += ["--max-budget-usd", f"{budget:.2f}"]
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    r, _ = auth.run(cmd, input=prompt, capture_output=True, text=True,
                    timeout=timeout, cwd=config.DATA_DIR)
    try:
        d = json.loads(r.stdout)
    except json.JSONDecodeError:
        raise LLMError((r.stderr or r.stdout or "无输出")[:300])
    if "budget" in str(d.get("subtype") or ""):
        raise LLMError(f"超出这一步的预算上限 ${budget or 0:.2f}（可以在设置里调高每次深挖上限）")
    if d.get("is_error") or d.get("structured_output") is None:
        raise LLMError(str(d.get("result") or d.get("api_error_status") or "模型没有返回结构化结果")[:300])
    model_used = next(iter(d.get("modelUsage") or {}), model)
    return d["structured_output"], float(d.get("total_cost_usd") or 0), model_used
