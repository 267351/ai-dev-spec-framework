#!/usr/bin/env python3
"""
Spec 影响分析工具
在修改 spec.md 规则前，分析变更的影响范围。

功能：
1. 输入 spec 规则 → 搜索所有依赖它的代码文件
2. 输入 spec 规则 → 搜索所有引用它的其他 spec.md
3. 风险评估算法
4. 修改步骤建议生成

使用方法：
  python3 tools/spec-tools/spec_impact_analyzer.py --spec <spec-file> --rule <rule-pattern>
  python3 tools/spec-tools/spec_impact_analyzer.py --spec <spec-file> --rule-id <WM-ARCH-001>
"""

import os
import sys
import re
import argparse
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent if "skills" in str(SCRIPT_DIR) else SCRIPT_DIR.parent


# 风险等级定义
RISK_LEVELS = {
    "架构核心": {"level": "high", "icon": "🔴", "description": "影响项目分层结构，修改可能导致大范围重构"},
    "业务逻辑": {"level": "medium", "icon": "🟡", "description": "影响特定业务模块，修改需对应业务方确认"},
    "代码风格": {"level": "low", "icon": "🔵", "description": "影响代码外观，不改变行为，修改成本低"},
    "安全规则": {"level": "high", "icon": "🔴", "description": "影响系统安全性，修改需安全评审"},
}

CONFIDENCE_LEVELS = {
    "validated": 5,
    "proven": 4,
    "consensus": 3,
    "preventive": 2,
    "speculative": 1,
}


def find_all_spec_files(search_dir: str) -> list:
    """查找所有 .spec.md 文件"""
    return list(Path(search_dir).rglob("*.spec.md"))


def find_all_code_files(search_dir: str) -> list:
    """查找所有代码文件"""
    extensions = {".cs", ".razor", ".razor.cs", ".razor.css", ".css", ".csproj", ".slnx", ".sln"}
    files = []
    for ext in extensions:
        files.extend(Path(search_dir).rglob(f"*{ext}"))
    return files


def extract_rule_info_from_spec(spec_path: str, rule_pattern: str) -> dict:
    """从 spec.md 中提取指定规则的信息"""
    content = Path(spec_path).read_text(encoding="utf-8")
    lines = content.split("\n")

    rule_info = {
        "file": spec_path,
        "pattern": rule_pattern,
        "found": False,
        "title": "",
        "confidence": None,
        "confidence_stars": 0,
        "verifiable_type": None,
        "rule_id": None,
        "line_number": 0,
        "full_text": "",
    }

    for i, line in enumerate(lines):
        if rule_pattern.lower() in line.lower():
            rule_info["found"] = True
            rule_info["line_number"] = i + 1

            # 提取规则 ID
            id_match = re.search(r'<!--\s*@rule\s+id=(\S+)', line)
            if id_match:
                rule_info["rule_id"] = id_match.group(1)

            # 提取可信度
            conf_match = re.search(r'\[confidence:(\w+)\]', line)
            if conf_match:
                rule_info["confidence"] = conf_match.group(1)
                rule_info["confidence_stars"] = CONFIDENCE_LEVELS.get(conf_match.group(1), 0)

            # 提取可验证类型
            ver_match = re.search(r'\[verifiable:(\w+)\]', line)
            if ver_match:
                rule_info["verifiable_type"] = ver_match.group(1)

            # 提取标题
            for j in range(i, max(0, i - 5), -1):
                if lines[j].startswith("### "):
                    rule_info["title"] = lines[j].strip("# ").strip()
                    break

            # 收集规则文本（前后各3行）
            start = max(0, i - 2)
            end = min(len(lines), i + 5)
            rule_info["full_text"] = "\n".join(lines[start:end])

            break

    return rule_info


def search_dependent_code(spec_path: str, rule_pattern: str, search_dir: str) -> list:
    """搜索可能依赖此规则的代码文件"""
    spec_info = extract_rule_info_from_spec(spec_path, rule_pattern)
    if not spec_info["found"]:
        return []

    # 从规则中提取关键词用于搜索
    keywords = extract_keywords_from_rule(spec_info["full_text"])

    code_files = find_all_code_files(search_dir)
    dependent_files = []

    for code_file in code_files:
        try:
            content = code_file.read_text(encoding="utf-8")
        except Exception:
            continue

        score = 0
        matched_keywords = []
        for kw in keywords:
            if kw.lower() in content.lower():
                score += 1
                matched_keywords.append(kw)

        if score >= max(1, len(keywords) * 0.5):  # 匹配超过一半的关键词
            dependent_files.append({
                "file": str(code_file),
                "score": score,
                "matched_keywords": matched_keywords,
                "line_count": len(content.splitlines()),
            })

    # 按匹配度排序
    dependent_files.sort(key=lambda x: x["score"], reverse=True)
    return dependent_files


def search_referencing_specs(spec_path: str, rule_pattern: str, search_dir: str) -> list:
    """搜索引用此规则的其他 spec.md"""
    all_specs = find_all_spec_files(search_dir)
    referencing_specs = []

    spec_name = Path(spec_path).name
    rule_info = extract_rule_info_from_spec(spec_path, rule_pattern)

    for spec_file in all_specs:
        if str(spec_file) == spec_path:
            continue
        try:
            content = spec_file.read_text(encoding="utf-8")
        except Exception:
            continue

        # 检查是否引用了此文件或规则
        references = []
        if spec_name in content:
            references.append(f"引用文件: {spec_name}")
        if rule_info.get("rule_id") and rule_info["rule_id"] in content:
            references.append(f"引用规则ID: {rule_info['rule_id']}")

        for line in content.split("\n"):
            if rule_pattern.lower() in line.lower() and "参见" in line or "参考" in line or "参照" in line:
                references.append(f"参见: {line.strip()[:80]}")

        if references:
            referencing_specs.append({
                "file": str(spec_file),
                "references": references,
            })

    return referencing_specs


def extract_keywords_from_rule(rule_text: str) -> list:
    """从规则文本中提取关键词"""
    keywords = []

    # 提取引号中的术语
    quoted = re.findall(r'"([^"]+)"', rule_text)
    keywords.extend(quoted)

    # 提取反引号中的代码
    backticked = re.findall(r'`([^`]+)`', rule_text)
    keywords.extend(backticked)

    # 提取项目/类名（大驼峰命名）
    pascal = re.findall(r'\b([A-Z][a-zA-Z]+(?:Service|Controller|Repository|Manager|Dto|Entity|Model|Enum|Component))\b', rule_text)
    keywords.extend(pascal)

    # 提取技术术语
    tech_terms = re.findall(r'\b(DbContext|HttpClient|DI|Repository|Service|BLL|DAL|API|Web|Core|Shared|Infrastructure)\b', rule_text)
    keywords.extend(tech_terms)

    return list(set(keywords))


def assess_risk(rule_info: dict, dependent_files: list, referencing_specs: list) -> dict:
    """评估修改此规则的风险等级"""
    # 判断规则类别
    title_lower = rule_info.get("title", "").lower()
    pattern_lower = rule_info.get("pattern", "").lower()

    if any(w in title_lower + pattern_lower for w in ["架构", "分层", "architecture", "引用", "reference"]):
        category = "架构核心"
    elif any(w in title_lower + pattern_lower for w in ["安全", "密码", "认证", "security", "auth"]):
        category = "安全规则"
    elif any(w in title_lower + pattern_lower for w in ["业务", "business", "发放", "领用", "匹配"]):
        category = "业务逻辑"
    else:
        category = "代码风格"

    risk = RISK_LEVELS.get(category, RISK_LEVELS["代码风格"])

    # 根据影响范围调整
    dep_count = len(dependent_files)
    if dep_count > 20:
        risk = RISK_LEVELS["架构核心"]
    elif dep_count > 10:
        risk_level = max(risk.get("level", "low"), "medium", key=lambda x: {"low": 0, "medium": 1, "high": 2}.get(x, 0))

    return {
        "category": category,
        "level": risk["level"],
        "icon": risk["icon"],
        "description": risk["description"],
        "dependent_file_count": dep_count,
        "referencing_spec_count": len(referencing_specs),
        "confidence_stars": rule_info.get("confidence_stars", 0),
    }


def cmd_analyze(spec_path: str, rule_pattern: str, search_dir: str = None, rule_id: str = None):
    """执行影响分析"""
    if search_dir is None:
        search_dir = str(Path(spec_path).parent)  # 默认在 spec.md 同级目录搜索

    print("\n" + "=" * 60)
    print(f"  Spec 规则影响分析")
    print(f"  分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 查找规则
    if rule_id:
        # 通过 rule_id 查找
        all_specs = find_all_spec_files(search_dir)
        rule_info = None
        for spec in all_specs:
            content = spec.read_text(encoding="utf-8")
            for line in content.split("\n"):
                if rule_id in line and "@rule" in line:
                    spec_path = str(spec)
                    # 提取 rule_pattern
                    rule_match = re.match(r'^\d+\.\s+\*\*(禁止|建议|必须)\*\*\s+(.+)$', line)
                    if not rule_match:
                        for next_lines in content.split("\n"):
                            num_match = re.match(r'^\d+\.\s+\*\*(禁止|建议|必须)\*\*\s+(.+)$', next_lines)
                            if num_match:
                                rule_pattern = num_match.group(2)
                                break
                    if not locals().get('rule_pattern'):
                        rule_pattern = rule_id
                    break

    rule_info = extract_rule_info_from_spec(spec_path, rule_pattern)
    if not rule_info["found"]:
        print(f"\n❌ 未找到匹配的规则: {rule_pattern}")
        print(f"   文件: {spec_path}")
        sys.exit(1)

    # 显示规则信息
    print(f"\n📋 规则信息")
    print(f"   文件:    {rule_info['file']}")
    print(f"   行号:    {rule_info['line_number']}")
    if rule_info["title"]:
        print(f"   章节:    {rule_info['title']}")
    if rule_info["rule_id"]:
        print(f"   ID:      {rule_info['rule_id']}")
    if rule_info["confidence"]:
        stars = "⭐" * rule_info["confidence_stars"]
        print(f"   可信度:  {rule_info['confidence']} {stars}")
    if rule_info["verifiable_type"]:
        print(f"   可验证:  {rule_info['verifiable_type']}")

    # 搜索依赖代码
    print(f"\n🔍 正在搜索依赖此规则的代码文件...")
    dependent_files = search_dependent_code(spec_path, rule_pattern, search_dir)

    # 搜索引用 spec
    print(f"🔍 正在搜索引用此规则的其他 spec.md...")
    referencing_specs = search_referencing_specs(spec_path, rule_pattern, search_dir)

    # 风险评估
    risk = assess_risk(rule_info, dependent_files, referencing_specs)

    print(f"\n📊 影响分析结果\n")
    print(f"   {risk['icon']} 风险等级: {risk['level'].upper()}")
    print(f"   类型:     {risk['category']}")
    print(f"   {risk['description']}")

    if dependent_files:
        print(f"\n📁 依赖此规则的代码文件 ({len(dependent_files)} 个):")
        for df in dependent_files[:15]:
            rel_path = Path(df["file"]).name if not Path(df["file"]).is_absolute() else str(Path(df["file"]))
            print(f"   📄 {rel_path}")
            print(f"      匹配度: {df['score']}/{len(df.get('matched_keywords', []))} 关键词: {', '.join(df['matched_keywords'][:3])}")
        if len(dependent_files) > 15:
            print(f"   ... 还有 {len(dependent_files) - 15} 个文件")
    else:
        print(f"\n📁 依赖此规则的代码文件: 0 个")

    if referencing_specs:
        print(f"\n📁 引用此规则的其他 spec.md ({len(referencing_specs)} 个):")
        for rs in referencing_specs:
            rel_path = Path(rs["file"]).name
            print(f"   📄 {rel_path}")
            for ref in rs["references"]:
                print(f"      ↳ {ref}")
    else:
        print(f"\n📁 引用此规则的其他 spec.md: 0 个")

    # 修改建议
    print(f"\n📋 建议修改步骤:")
    step = 1
    print(f"   {step}. 更新 {Path(spec_path).name} 中的规则内容")
    step += 1

    if referencing_specs:
        print(f"   {step}. 同步更新 {len(referencing_specs)} 个引用此规则的其他 spec.md")
        step += 1

    if dependent_files:
        high_risk = [f for f in dependent_files if f["score"] >= 3]
        if high_risk:
            print(f"   {step}. 重点审查 {len(high_risk)} 个高匹配度代码文件")
            step += 1
        print(f"   {step}. 审查 {len(dependent_files)} 个依赖文件的代码是否需要同步修改")
        step += 1

    print(f"   {step}. 运行完整测试套件")
    step += 1
    print(f"   {step}. 团队评审")

    # 特殊警告
    if rule_info["confidence"] == "validated":
        print(f"\n⚠️  警告: 此规则可信度为 validated (⭐⭐⭐⭐⭐)，由实际事故验证。")
        print(f"   修改前请确保新证据充分，并记录到审计追踪。")

    print("\n" + "=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Spec 影响分析工具 - 分析修改 spec 规则的影响范围",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --spec 架构总纲.spec.md --rule "分层架构红线"
  %(prog)s --spec 架构总纲.spec.md --rule-id WM-ARCH-001
  %(prog)s --spec 架构总纲.spec.md --rule "禁止直接实例化" --dir /path/to/project
        """
    )
    parser.add_argument("--spec", required=True, help="spec.md 文件路径")
    parser.add_argument("--rule", help="规则关键词（在 spec.md 中搜索）")
    parser.add_argument("--rule-id", help="规则 ID（如 WM-ARCH-001）")
    parser.add_argument("--dir", help="搜索目录（默认 spec.md 所在目录）")

    args = parser.parse_args()

    if not args.rule and not args.rule_id:
        parser.error("必须提供 --rule 或 --rule-id")
        sys.exit(1)

    cmd_analyze(
        args.spec,
        args.rule or "",
        args.dir,
        args.rule_id
    )


if __name__ == "__main__":
    main()
