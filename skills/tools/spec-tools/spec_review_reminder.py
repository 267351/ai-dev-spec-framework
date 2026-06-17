#!/usr/bin/env python3
"""
Spec 审查提醒工具
扫描所有 spec.md，找出需要审查的规则。

功能：
1. 扫描所有 spec.md，提取最后审查日期
2. 按 stale-days 过滤
3. 按可信度等级优先排序（speculative 先审）
4. 生成审查报告（Markdown）

使用方法：
  python3 tools/spec-tools/spec_review_reminder.py                      # 默认：列出超 90 天未审规则
  python3 tools/spec-tools/spec_review_reminder.py --stale-days 30      # 自定义天数阈值
  python3 tools/spec-tools/spec_review_reminder.py --dir src            # 指定搜索目录
  python3 tools/spec-tools/spec_review_reminder.py --by-confidence      # 按可信度优先排序
  python3 tools/spec-tools/spec_review_reminder.py --output report.md   # 输出到文件
  python3 tools/spec-tools/spec_review_reminder.py --show-sunsets       # 同时显示 Sunset 过期
"""

import os
import sys
import re
import argparse
from pathlib import Path
from datetime import datetime, date, timedelta

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent if "skills" in str(SCRIPT_DIR) else SCRIPT_DIR.parent

CONFIDENCE_PRIORITY = ["speculative", "preventive", "consensus", "proven", "validated"]
CONFIDENCE_STARS = {
    "validated": "⭐⭐⭐⭐⭐",
    "proven": "⭐⭐⭐⭐",
    "consensus": "⭐⭐⭐",
    "preventive": "⭐⭐",
    "speculative": "⭐",
}

# Sunset 默认有效期（天）
SUNSET_DEFAULTS = {
    "validated": None,  # 不过期
    "proven": 365,
    "consensus": 180,
    "preventive": 90,
    "speculative": 30,
}


def find_all_spec_files(search_dir: str) -> list:
    """查找所有 spec.md 文件"""
    return list(Path(search_dir).rglob("*.spec.md"))


def parse_audit_trail(content: str) -> dict:
    """解析审计追踪，提取最后审查日期和操作历史"""
    audit_match = re.search(r'## 📋 审计追踪.*?(?=\n## |\Z)', content, re.DOTALL)
    if not audit_match:
        audit_match = re.search(r'## 审计追踪.*?(?=\n## |\Z)', content, re.DOTALL)

    if not audit_match:
        return {
            "has_audit": False,
            "last_review": None,
            "last_action": None,
            "total_entries": 0,
        }

    audit_section = audit_match.group(0)
    entries = re.findall(r'\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(\S+)\s*\|', audit_section)

    last_review = None
    last_action = None

    for date_str, action in entries:
        if action in ("验证", "validate"):
            if last_review is None or date_str > last_review:
                last_review = date_str
        last_action = action

    # 如果没有验证记录，使用最后操作日期
    if last_review is None and entries:
        last_review = entries[-1][0]

    return {
        "has_audit": True,
        "last_review": last_review,
        "last_action": last_action,
        "total_entries": len(entries),
    }


def parse_confidence(content: str) -> list:
    """解析 spec.md 中的可信度标注"""
    confidences = []
    for m in re.finditer(r'\[confidence:(\w+)\]', content):
        level = m.group(1)
        # 找到上下文
        start = max(0, m.start() - 200)
        end = min(len(content), m.end() + 200)
        context = content[start:end]
        # 提取标题
        title_match = re.search(r'###\s+(.+?)(?:\n|$)', context)
        title = title_match.group(1).strip() if title_match else "未知规则"
        confidences.append({"level": level, "title": title})
    return confidences


def parse_sunsets(content: str) -> list:
    """解析 spec.md 中的 Sunset 标注"""
    sunsets = []
    for m in re.finditer(r'\[sunset:(\d{4}-\d{2}-\d{2})\]', content):
        sunset_date = m.group(1)
        start = max(0, m.start() - 200)
        end = min(len(content), m.end() + 200)
        context = content[start:end]
        title_match = re.search(r'###\s+(.+?)(?:\n|$)', context)
        title = title_match.group(1).strip() if title_match else "未知规则"
        sunsets.append({"date": sunset_date, "title": title})
    return sunsets


def cmd_review(stale_days: int = 90, search_dir: str = None,
               by_confidence: bool = False, show_sunsets: bool = False,
               output_file: str = None):
    """执行审查提醒"""
    if search_dir is None:
        search_dir = str(PROJECT_ROOT)

    spec_files = find_all_spec_files(search_dir)
    today = date.today()
    cutoff = today - timedelta(days=stale_days)

    stale_rules = []
    expired_sunsets = []

    for spec_path in spec_files:
        try:
            content = spec_path.read_text(encoding="utf-8")
        except Exception:
            continue

        # 检查审计追踪
        audit = parse_audit_trail(content)

        if audit["has_audit"] and audit["last_review"]:
            try:
                last_review_date = datetime.strptime(audit["last_review"], "%Y-%m-%d").date()
                if last_review_date < cutoff:
                    confidences = parse_confidence(content)
                    stale_rules.append({
                        "file": str(spec_path),
                        "last_review": audit["last_review"],
                        "days_stale": (today - last_review_date).days,
                        "last_action": audit.get("last_action", "未知"),
                        "audit_entries": audit["total_entries"],
                        "confidences": confidences,
                    })
            except ValueError:
                pass
        elif not audit["has_audit"]:
            # 没有审计追踪的 spec.md，标记为需要审查
            confidences = parse_confidence(content)
            if confidences:
                stale_rules.append({
                    "file": str(spec_path),
                    "last_review": "无审计追踪",
                    "days_stale": 999,
                    "last_action": "未知",
                    "audit_entries": 0,
                    "confidences": confidences,
                })

        # 检查 Sunset
        if show_sunsets:
            sunsets = parse_sunsets(content)
            for s in sunsets:
                try:
                    sd = datetime.strptime(s["date"], "%Y-%m-%d").date()
                    if sd <= today:
                        expired_sunsets.append({
                            "file": str(spec_path),
                            "title": s["title"],
                            "sunset_date": s["date"],
                            "days_expired": (today - sd).days,
                        })
                except ValueError:
                    pass

    # 排序
    if by_confidence:
        # 按可信度优先级排序（低可信度优先）
        def confidence_sort_key(rule):
            lowest = 5
            for c in rule["confidences"]:
                if c["level"] in CONFIDENCE_PRIORITY:
                    priority = CONFIDENCE_PRIORITY.index(c["level"])
                    lowest = min(lowest, priority)
            return lowest
        stale_rules.sort(key=confidence_sort_key)
    else:
        # 按过时天数倒序
        stale_rules.sort(key=lambda r: r["days_stale"], reverse=True)

    # 输出
    output = []
    output.append("\n" + "=" * 60)
    output.append(f"  Spec 审查提醒报告")
    output.append(f"  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append(f"  阈值: 超过 {stale_days} 天未审查")
    output.append("=" * 60 + "\n")

    output.append(f"📊 统计:")
    output.append(f"   扫描 spec.md 文件: {len(spec_files)} 个")
    output.append(f"   需要审查的规则: {len(stale_rules)} 个")
    if show_sunsets:
        output.append(f"   Sunset 已过期: {len(expired_sunsets)} 个")
    output.append("")

    if stale_rules:
        output.append(f"📋 需要审查的规则:\n")
        for i, rule in enumerate(stale_rules, 1):
            rel_path = Path(rule["file"]).name
            stars_display = ""
            if rule["confidences"]:
                levels = [c["level"] for c in rule["confidences"]]
                stars_display = ", ".join([f"{l} {CONFIDENCE_STARS.get(l, '')}" for l in levels])

            output.append(f"{i}. 📄 {rel_path}")
            output.append(f"   最后审查: {rule['last_review']} ({rule['days_stale']} 天前)")
            if stars_display:
                output.append(f"   可信度:   {stars_display}")
            if rule["audit_entries"] > 0:
                output.append(f"   审计条目: {rule['audit_entries']} 条")
            output.append("")

    if show_sunsets and expired_sunsets:
        output.append(f"\n⏰ Sunset 已过期的规则:\n")
        for s in expired_sunsets:
            rel_path = Path(s["file"]).name
            output.append(f"   🔴 {rel_path}: {s['title']}")
            output.append(f"      Sunset: {s['sunset_date']} (已过期 {s['days_expired']} 天)")
        output.append("")

    if not stale_rules and not expired_sunsets:
        output.append("   ✅ 所有规则均在有效期内，无需审查！\n")

    output.append("📋 建议行动:")
    output.append("   1. 安排团队审查会议，逐条确认规则是否仍然有效")
    output.append("   2. 对低可信度规则（speculative/preventive）优先审查")
    output.append("   3. 更新审计追踪，记录审查结果")
    output.append("   4. 使用 spec_md_manager_v2.py audit 命令记录每次审查")
    output.append("")

    text_output = "\n".join(output)
    print(text_output)

    if output_file:
        Path(output_file).write_text(text_output, encoding="utf-8")
        print(f"📄 报告已保存至: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Spec 审查提醒工具 - 找出需要审查的 spec.md 规则",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                                   列出超90天未审规则
  %(prog)s --stale-days 30                   30天阈值
  %(prog)s --by-confidence                   按可信度优先级排序
  %(prog)s --show-sunsets                    同时显示Sunset过期
  %(prog)s --output review-report.md         输出到文件
        """
    )
    parser.add_argument("--stale-days", type=int, default=90, help="未审天数阈值（默认90）")
    parser.add_argument("--dir", help="搜索目录（默认项目根目录）")
    parser.add_argument("--by-confidence", action="store_true", help="按可信度优先级排序")
    parser.add_argument("--show-sunsets", action="store_true", help="同时显示 Sunset 过期的规则")
    parser.add_argument("--output", help="输出到文件（Markdown 格式）")

    args = parser.parse_args()
    cmd_review(args.stale_days, args.dir, args.by_confidence, args.show_sunsets, args.output)


if __name__ == "__main__":
    main()
