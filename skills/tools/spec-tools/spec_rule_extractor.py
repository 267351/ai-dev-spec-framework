#!/usr/bin/env python3
"""
Spec 规则解析器
从 spec.md 文件中提取可验证规则，生成结构化 JSON 输出。

功能：
1. 提取 [verifiable:xxx] 标注的规则
2. 提取 <!-- @rule id=... --> 机器指令标注
3. 提取 <!-- @check: ... --> 检查指令
4. 提取 <!-- @pattern: ... --> 代码模式
5. 生成结构化规则 JSON 输出

使用方法：
  python3 tools/spec-tools/spec_rule_extractor.py <spec-file>                  # 解析单个文件
  python3 tools/spec_rule_extractor.py --dir <path>                 # 解析目录下所有 spec.md
  python3 tools/spec_rule_extractor.py --dir <path> --output json   # 输出 JSON
  python3 tools/spec_rule_extractor.py --dir <path> --filter di     # 按类型过滤
  python3 tools/spec_rule_extractor.py --dir <path> --summary       # 生成摘要
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from typing import Optional

# 项目根目录
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent if "skills" in str(SCRIPT_DIR) else SCRIPT_DIR.parent

# 可验证性标注定义
VERIFIABLE_TYPES = {
    "di": {"name": "依赖注入/项目引用", "tool": "Roslyn Analyzer", "method": "语义分析"},
    "naming": {"name": "命名规范", "tool": "Roslyn Analyzer / Regex", "method": "AST 匹配"},
    "pattern": {"name": "代码模式", "tool": "Roslyn Analyzer", "method": "模式匹配"},
    "structure": {"name": "结构化约束", "tool": "Roslyn Analyzer", "method": "模式匹配"},
    "semantic": {"name": "语义规则", "tool": "AI Agent", "method": "LLM 审查"},
    "contextual": {"name": "上下文规则", "tool": "AI Agent + 人工", "method": "人工审查"},
    "unverifiable": {"name": "不可自动验证", "tool": "人工审查", "method": "仅文档"},
}

CONFIDENCE_LEVELS = {
    "validated": 5,
    "proven": 4,
    "consensus": 3,
    "preventive": 2,
    "speculative": 1,
}


class Rule:
    """单条可验证规则"""
    def __init__(self):
        self.id: Optional[str] = None
        self.title: str = ""
        self.description: str = ""
        self.verifiable_type: Optional[str] = None
        self.confidence: Optional[str] = None
        self.confidence_stars: int = 0
        self.severity: str = "warning"
        self.rule_type: Optional[str] = None  # dependency-check, naming-check, etc.
        self.checks: list = []  # <!-- @check: ... -->
        self.patterns: list = []  # <!-- @pattern: ... -->
        self.sunset: Optional[str] = None  # [sunset:YYYY-MM-DD]
        self.source_file: str = ""
        self.source_line: int = 0
        self.section: str = ""  # 所属章节
        self.raw_text: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "verifiable_type": self.verifiable_type,
            "verifiable_info": VERIFIABLE_TYPES.get(self.verifiable_type, {}) if self.verifiable_type else None,
            "confidence": self.confidence,
            "confidence_stars": self.confidence_stars,
            "severity": self.severity,
            "rule_type": self.rule_type,
            "checks": self.checks,
            "patterns": self.patterns,
            "sunset": self.sunset,
            "source_file": self.source_file,
            "source_line": self.source_line,
            "section": self.section,
            "raw_text": self.raw_text[:200] + "..." if len(self.raw_text) > 200 else self.raw_text,
        }


def extract_rules_from_file(spec_path: str) -> list:
    """从单个 spec.md 文件中提取所有可验证规则"""
    content = Path(spec_path).read_text(encoding="utf-8")
    lines = content.split("\n")
    rules = []

    # 找到所有规则块
    # 规则块以 ### 或 ## 开头，或者以编号列表项开始
    # 我们扫描包含 [verifiable:xxx] 或 [confidence:xxx] 的行

    # 策略：找到所有包含标注的行，然后向上/向下扩展获取完整上下文

    current_section = ""
    for i, line in enumerate(lines):
        # 追踪当前章节
        if line.startswith("## ") or line.startswith("### "):
            current_section = line.strip("# ").strip()

    i = 0
    while i < len(lines):
        line = lines[i]

        # 检测规则标题行 (### 开头 或 包含标注的编号行)
        is_rule_header = False
        verifiable_match = re.search(r'\[verifiable:(\w+)\]', line)
        confidence_match = re.search(r'\[confidence:(\w+)\]', line)
        sunset_match = re.search(r'\[sunset:(\d{4}-\d{2}-\d{2})\]', line)
        rule_id_match = re.search(r'<!--\s*@rule\s+id=(\S+)\s+type=(\S+)(?:\s+severity=(\S+))?', line)

        rule_num_match = re.match(r'^(\d+)\.\s+\*\*(禁止|建议|必须)\*\*\s+(.+)$', line)
        header_match = re.match(r'^###\s+(.+)', line)

        if verifiable_match or confidence_match or sunset_match or rule_id_match:
            is_rule_header = True

        if is_rule_header or (rule_num_match and i > 0):
            rule = Rule()
            rule.source_file = spec_path
            rule.source_line = i + 1

            # 提取标注
            if verifiable_match:
                rule.verifiable_type = verifiable_match.group(1)
            if confidence_match:
                rule.confidence = confidence_match.group(1)
                rule.confidence_stars = CONFIDENCE_LEVELS.get(rule.confidence, 0)
            if sunset_match:
                rule.sunset = sunset_match.group(1)

            # 提取 @rule 指令
            if rule_id_match:
                rule.id = rule_id_match.group(1)
                rule.rule_type = rule_id_match.group(2)
                if rule_id_match.group(3):
                    rule.severity = rule_id_match.group(3)

            # 确定规则标题
            if header_match:
                rule.title = header_match.group(1).strip()
            elif rule_num_match:
                rule.title = f"规则 {rule_num_match.group(1)}: {rule_num_match.group(3).strip()}"

            # 收集规则描述文本（从当前行到下一个规则或章节边界）
            raw_lines = []
            j = i
            while j < len(lines):
                current = lines[j]
                # 检查是否到达下一个规则
                if j > i and (re.search(r'\[verifiable:\w+\]', current) or
                             re.search(r'\[confidence:\w+\]', current) or
                             re.match(r'^###\s+', current) or
                             re.match(r'^##\s', current)):
                    if not re.match(r'^>', current):  # 引用行不中断
                        break
                raw_lines.append(current)
                j += 1

            rule.raw_text = "\n".join(raw_lines)

            # 提取描述（第一个非空非标题行）
            for k in range(i + 1, min(j, len(lines))):
                desc_line = lines[k].strip()
                if desc_line and not desc_line.startswith(">") and not desc_line.startswith("<!--"):
                    if not rule.description:
                        rule.description = desc_line[:200]
                        break

            # 提取 @check 指令
            for k in range(i, min(j, len(lines))):
                check_match = re.search(r'<!--\s*@check:\s*(.+?)\s*-->', lines[k])
                if check_match:
                    rule.checks.append(check_match.group(1))

            # 提取 @pattern 指令
            for k in range(i, min(j, len(lines))):
                pattern_match = re.search(r'<!--\s*@pattern:\s*(.+?)\s*-->', lines[k])
                if pattern_match:
                    rule.patterns.append(pattern_match.group(1))

            # 提取所属章节
            rule.section = current_section

            # 如果规则标题为空但有关联规则编号行，查找上下文
            if not rule.title and j > i:
                for k in range(i, min(j, len(lines))):
                    title_line = lines[k].strip()
                    if title_line.startswith("### ") or title_line.startswith("## "):
                        rule.title = title_line.strip("# ").strip()
                        break

            # 只添加有 verifiable 标注或 @rule 指令的规则
            if rule.verifiable_type or rule.id:
                rules.append(rule)

            i = j
        else:
            i += 1

    return rules


def extract_rules_from_dir(search_dir: str, filter_type: str = None) -> list:
    """从目录中所有 spec.md 文件提取规则"""
    all_rules = []
    spec_files = list(Path(search_dir).rglob("*.spec.md"))

    for spec_path in sorted(spec_files):
        try:
            rules = extract_rules_from_file(str(spec_path))
            if filter_type:
                rules = [r for r in rules if r.verifiable_type == filter_type]
            all_rules.extend(rules)
        except Exception as e:
            print(f"⚠️  解析失败: {spec_path}: {e}", file=sys.stderr)

    return all_rules


def cmd_extract_file(spec_path: str, output_format: str = "text"):
    """解析单个 spec.md 文件"""
    rules = extract_rules_from_file(spec_path)

    if output_format == "json":
        print(json.dumps([r.to_dict() for r in rules], ensure_ascii=False, indent=2))
        return

    print(f"\n📋 规则解析: {spec_path}\n")
    print(f"   共提取 {len(rules)} 条可验证规则\n")

    for idx, rule in enumerate(rules, 1):
        print(f"--- 规则 {idx} ---")
        if rule.id:
            print(f"ID:       {rule.id}")
        print(f"标题:     {rule.title}")
        print(f"类型:     {rule.verifiable_type} ({VERIFIABLE_TYPES.get(rule.verifiable_type, {}).get('name', 'N/A')})")
        if rule.confidence:
            stars = "⭐" * rule.confidence_stars
            print(f"可信度:   {rule.confidence} {stars}")
        if rule.sunset:
            print(f"Sunset:   {rule.sunset}")
        print(f"严重度:   {rule.severity}")
        if rule.checks:
            print(f"检查指令: {rule.checks}")
        if rule.patterns:
            print(f"代码模式: {rule.patterns}")
        if rule.description:
            print(f"描述:     {rule.description[:100]}")
        print(f"位置:     {rule.source_file}:{rule.source_line}")
        print()


def cmd_extract_dir(search_dir: str, output_format: str = "text", filter_type: str = None):
    """解析目录下所有 spec.md"""
    rules = extract_rules_from_dir(search_dir, filter_type)

    if output_format == "json":
        print(json.dumps([r.to_dict() for r in rules], ensure_ascii=False, indent=2))
        return

    print(f"\n📋 规则提取结果 - 目录: {search_dir}\n")
    print(f"   共从 spec.md 文件中提取 {len(rules)} 条规则\n")

    # 按类型分组
    by_type = {}
    for r in rules:
        t = r.verifiable_type or "未标注"
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(r)

    for vtype, type_rules in sorted(by_type.items()):
        type_info = VERIFIABLE_TYPES.get(vtype, {})
        tool = type_info.get("tool", "N/A")
        print(f"\n## [{vtype}] {type_info.get('name', 'N/A')} ({len(type_rules)} 条)")
        print(f"   检查工具: {tool}")
        for r in type_rules:
            fid = r.id or "-"
            sev = r.severity
            title = r.title[:60]
            print(f"   [{sev:>8}] {fid:<20} {title}")


def cmd_summary(search_dir: str):
    """生成规则覆盖度摘要"""
    rules = extract_rules_from_dir(search_dir)
    total = len(rules)

    if total == 0:
        print("\n📊 未找到任何可验证规则\n")
        return

    print("\n" + "=" * 60)
    print("  Spec 可验证规则覆盖度摘要")
    print("=" * 60 + "\n")

    # 按可验证性分类
    auto_verifiable = [r for r in rules if r.verifiable_type in ("di", "naming", "pattern", "structure")]
    ai_verifiable = [r for r in rules if r.verifiable_type == "semantic"]
    manual_only = [r for r in rules if r.verifiable_type in ("contextual", "unverifiable")]
    unannotated = [r for r in rules if not r.verifiable_type]

    print(f"📊 规则总数: {total}")
    print(f"   ✅ 可自动验证 (编译时): {len(auto_verifiable)} ({_pct(len(auto_verifiable), total)}%)")
    print(f"   🤖 AI 审查 (提交时):   {len(ai_verifiable)} ({_pct(len(ai_verifiable), total)}%)")
    print(f"   👤 仅人工审查:          {len(manual_only)} ({_pct(len(manual_only), total)}%)")
    print(f"   ❓ 未标注:              {len(unannotated)} ({_pct(len(unannotated), total)}%)")

    # 按可信度分类
    by_confidence = {}
    for r in rules:
        c = r.confidence or "未标注"
        by_confidence[c] = by_confidence.get(c, 0) + 1

    print(f"\n📊 按可信度分布:")
    for level_name in ["validated", "proven", "consensus", "preventive", "speculative"]:
        count = by_confidence.get(level_name, 0)
        print(f"   {'⭐' * CONFIDENCE_LEVELS[level_name]:10} {level_name:<15} {count} 条 ({_pct(count, total)}%)")
    unconf = by_confidence.get("未标注", 0)
    if unconf > 0:
        print(f"   {'❓':10} 未标注{'':13} {unconf} 条 ({_pct(unconf, total)}%)")

    # 按严重度分类
    by_severity = {}
    for r in rules:
        s = r.severity or "warning"
        by_severity[s] = by_severity.get(s, 0) + 1

    print(f"\n📊 按严重度分布:")
    for sev in ["error", "warning", "suggestion"]:
        count = by_severity.get(sev, 0)
        icon = "🔴" if sev == "error" else "🟡" if sev == "warning" else "🔵"
        print(f"   {icon} {sev:<12} {count} 条 ({_pct(count, total)}%)")

    # Sunset 检查
    sunset_rules = [r for r in rules if r.sunset]
    print(f"\n⏰ Sunset 规则: {len(sunset_rules)} 条")
    if sunset_rules:
        from datetime import date
        today = date.today()
        for r in sunset_rules:
            try:
                sd = __import__('datetime').datetime.strptime(r.sunset, "%Y-%m-%d").date()
                days_left = (sd - today).days
                status = "🔴 已过期" if days_left < 0 else "🟡 即将到期" if days_left < 30 else "🔵"
                print(f"   {status} {r.title[:50]} → {r.sunset} ({days_left} 天)")
            except:
                pass

    print("\n" + "=" * 60 + "\n")


def _pct(part: int, total: int) -> str:
    if total == 0:
        return "0.0"
    return f"{round(part / total * 100, 1)}"


def main():
    parser = argparse.ArgumentParser(
        description="Spec 规则解析器 - 从 spec.md 提取可验证规则",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s 架构总纲.spec.md                       解析单个 spec.md
  %(prog)s --dir /path/to/project                 解析整个项目
  %(prog)s --dir /path/to/project --output json   输出 JSON 格式
  %(prog)s --dir /path/to/project --filter di     仅提取 DI 类型规则
  %(prog)s --dir /path/to/project --summary       生成覆盖度摘要
        """
    )
    parser.add_argument("spec_file", nargs="?", help="spec.md 文件路径")
    parser.add_argument("--dir", help="搜索目录（递归查找所有 spec.md）")
    parser.add_argument("--output", choices=["text", "json"], default="text", help="输出格式")
    parser.add_argument("--filter", choices=list(VERIFIABLE_TYPES.keys()), help="按可验证类型过滤")
    parser.add_argument("--summary", action="store_true", help="生成覆盖度摘要")

    args = parser.parse_args()

    if args.summary:
        search_dir = args.dir or PROJECT_ROOT
        cmd_summary(search_dir)
    elif args.dir:
        cmd_extract_dir(args.dir, args.output, args.filter)
    elif args.spec_file:
        cmd_extract_file(args.spec_file, args.output)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
