"""领域饱和度 + 措辞守卫，移植自 r14dd/patent 的 src/verdict.rs（MIT OR Apache-2.0）。

两条规则原样保留：
  1. 模型给的饱和度不能低于数据算出来的下限（floor_level）——模型说"空白"但数据里有一堆强匹配，就以数据为准。
  2. 永远不说"不存在"。只搜了部分来源，能证明"有"，不能证明"没有"。模型越界时用数据生成的标题替换。
patent 用向量相似度做阈值；这里用核验模型给出的 fit（0–100），阈值按同样比例换算。
"""
import re

LEVELS = ["open", "crowded", "saturated"]
LEVEL_ZH = {"open": "空白", "crowded": "拥挤", "saturated": "饱和"}

CAVEAT = "不代表不存在——只是在已搜索的来源里没找到更接近的。动手前还可以看看应用商店和小众社区。"

ABSENCE_PHRASES = [
    "不存在", "从来没有", "从未有人", "没有人做过", "还没有人做", "没人做过", "尚无人", "无先例", "前所未有",
    "没有任何类似", "没有类似", "完全没有", "独一无二", "首创",
    "does not exist", "doesn't exist", "do not exist", "no prior art", "nothing exists", "nothing like this",
    "never been built", "has not been built", "hasn't been built", "no one has built", "first of its kind",
]
SCOPE_WORDS = ["已搜索", "搜索范围", "在这些来源", "搜到的", "检索到的", "本次搜索", "sources checked"]


def floor_level(model_level, fits):
    """fits：整体覆盖型匹配的 fit 列表。"""
    strong = sum(f >= 60 for f in fits)
    close = sum(f >= 55 for f in fits)
    very_strong = sum(f >= 70 for f in fits)
    data = "saturated" if strong >= 5 else "crowded" if close >= 2 or very_strong >= 1 else "open"
    return max(model_level, data, key=LEVELS.index)


def claims_absence(text):
    low = (text or "").lower()
    return any(p in low for p in ABSENCE_PHRASES) and not any(w in low for w in SCOPE_WORDS)


def data_headline(level, fits, n_sources):
    close = sum(f >= 55 for f in fits)
    if level == "saturated":
        return f"饱和：在已搜索的 {n_sources} 个来源里找到 {close} 个高度相关的实现。"
    if level == "crowded":
        return f"拥挤：在已搜索的 {n_sources} 个来源里找到 {close} 个高度相关的实现。"
    if close:
        return f"在已搜索的 {n_sources} 个来源里有 {close} 个相关实现，但空间仍然比较开放，动手前值得先看看。"
    return f"在已搜索的 {n_sources} 个来源里没找到接近的实现，动手前再多看看。"


def guard(text, level, fits, n_sources):
    return data_headline(level, fits, n_sources) if claims_absence(text) else text
