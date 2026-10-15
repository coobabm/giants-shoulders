"""第一道闸：正则粗筛，免得每条消息都去调模型。宁可放进来，交给 Haiku 再判。"""
import re

ZH_VERB = r"(做|写|搞|弄|搭|建|开发|实现|设计|生成|创建|造|整)"
ZH_NOUN = (r"(工具|应用|app|网站|网页|页面|插件|扩展|脚本|机器人|bot|skill|技能|mcp|服务|系统|平台|"
           r"项目|库|游戏|小程序|助手|面板|看板|dashboard|cli|命令行|爬虫|编辑器|播放器|生成器|"
           r"转换器|监控|自动化|agent|智能体|工作流|模型|api|接口|扩展程序)")
EN_VERB = r"\b(build|make|create|write|implement|develop|set ?up|code|design)\b"
EN_NOUN = (r"\b(tool|app|cli|bot|plugin|extension|script|service|website|site|dashboard|library|"
           r"skill|mcp|server|game|system|generator|scraper|crawler|agent|workflow|api|editor|viewer)s?\b")

PATTERNS = [
    re.compile(ZH_VERB + r"(一个|个|一款|一套|一份|成一个|成)"),
    re.compile(ZH_VERB + r".{0,24}" + ZH_NOUN, re.I),
    re.compile(r"(有没有|是否有|找找|找一下)(现成|开源|类似)"),
    re.compile(r"(帮我|给我|我想|我要|能不能|可以).{0,6}" + ZH_VERB),
    re.compile(EN_VERB + r".{0,40}" + EN_NOUN, re.I),
]


def maybe_build(text):
    t = text.strip()
    if len(t) < 6 or len(t) > 6000:
        return False
    head = t[:800]  # 长消息通常是粘贴的日志/代码，只看开头
    return any(p.search(head) for p in PATTERNS)
