"""给 graphify 图谱补上跨模块调用边，并生成 graphify-out/CALLS.md。

graphify 的 AST 提取认得 `from .llm import ask` 这种直接导入的调用，但认不出 `github.canary()`、
`store.get_report()` 这种"先 `from . import 模块` 再 `模块.函数()`"的调用——而这个引擎跨模块几乎都这么写。
这个脚本用 Python ast 确定性地找出这些调用（不用模型），按 (文件, 函数名) 对上图谱里已有的节点，
加 EXTRACTED 的 calls 边，然后重新导出 wiki 和 HTML。

用法（在技能根目录）：graphify update . && python3 engine/tools/agent_map.py
"""
import ast
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "engine" / "deja"
GRAPH = ROOT / "graphify-out" / "graph.json"
CALLS_MD = ROOT / "graphify-out" / "CALLS.md"
CONTEXT = "module_attr_call"


def rel(p):
    return str(p.relative_to(ROOT))


def module_aliases(tree):
    """这个文件里 `from . import a, b as c`（任何位置，含函数内的延迟导入）→ {别名: 模块文件}。"""
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 1 and not node.module:
            for a in node.names:
                f = PKG / f"{a.name}.py"
                if f.exists():
                    out[a.asname or a.name] = f
    return out


def calls_in(path):
    """[(调用者标签, 被调模块文件, 被调函数名, 行号)]。嵌套函数里的调用算到最外层函数 / 方法上。"""
    tree = ast.parse(path.read_text())
    aliases = module_aliases(tree)
    found = []

    def visit(node, owner):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                visit(child, owner or f"{child.name}()")
            elif isinstance(child, ast.ClassDef):
                for item in child.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        visit(item, f".{item.name}()")
                    else:
                        visit(item, owner)
            else:
                if (owner and isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute)
                        and isinstance(child.func.value, ast.Name) and child.func.value.id in aliases):
                    found.append((owner, aliases[child.func.value.id], child.func.attr, child.lineno))
                visit(child, owner)

    visit(tree, None)
    return found


def main():
    g = json.loads(GRAPH.read_text())
    by_key = defaultdict(list)
    for n in g["nodes"]:
        by_key[(n.get("source_file"), n.get("label"))].append(n["id"])
    existing = {(e["source"], e["target"]) for e in g["links"] if e.get("relation") == "calls"}
    added, unmatched, table = 0, [], defaultdict(set)
    for f in sorted(PKG.glob("*.py")):
        for caller, target_file, name, line in calls_in(f):
            src = by_key.get((rel(f), caller))
            dst = by_key.get((rel(target_file), f"{name}()"))
            if not dst:          # 模块常量 / 类，不是函数
                continue
            if not src:
                unmatched.append(f"{rel(f)}:{line} {caller} → {target_file.stem}.{name}()")
                continue
            table[(target_file.stem, name)].add(f"{f.stem}.{caller.lstrip('.').rstrip('()')}")
            if (src[0], dst[0]) in existing or (dst[0], src[0]) in existing:
                continue
            g["links"].append({"relation": "calls", "context": CONTEXT, "confidence": "EXTRACTED",
                               "confidence_score": 1.0, "source_file": rel(f), "source_location": f"L{line}",
                               "weight": 1.0, "source": src[0], "target": dst[0]})
            existing.add((src[0], dst[0]))
            added += 1
    GRAPH.write_text(json.dumps(g, ensure_ascii=False, indent=2))

    lines = ["# 跨模块调用表（自动生成，别手改）", "",
             "由 `engine/tools/agent_map.py` 用 Python ast 生成：`模块.函数()` 形式的跨模块调用。"
             "改了函数签名 / 删函数之前，先看这里谁在调它。", ""]
    for mod in sorted({m for m, _ in table}):
        lines.append(f"## {mod}.py")
        for (m, name), callers in sorted(table.items()):
            if m == mod:
                lines.append(f"- `{name}()` ← {', '.join(f'`{c}`' for c in sorted(callers))}")
        lines.append("")
    CALLS_MD.write_text("\n".join(lines))
    print(f"补了 {added} 条跨模块调用边；调用表 {len(table)} 个被调函数 → {rel(CALLS_MD)}")
    if unmatched:
        print(f"{len(unmatched)} 处调用者在图里没找到节点（多半是模块顶层代码）：", *unmatched[:5], sep="\n  ")
    for cmd in (["graphify", "export", "wiki"], ["graphify", "export", "html"]):
        subprocess.run(cmd, cwd=ROOT, check=False, stdout=subprocess.DEVNULL)
    return 0


if __name__ == "__main__":
    sys.exit(main())
