#!/usr/bin/env python3
"""
Spec MD 约定文件管理器 v2
增强版：增加可信度分级、审计追踪、质疑记录、Sunset 机制支持

保留 v1 功能：
  python3 tools/spec-tools/spec_md_manager_v2.py scan          # 扫描缺失的 spec.md
  python3 tools/spec-tools/spec_md_manager_v2.py scan --smart              # 智能扫描（跳过 Entity/DTO/Enum）
  python3 tools/spec-tools/spec_md_manager_v2.py create                    # 批量创建缺失的 spec.md
  python3 tools/spec-tools/spec_md_manager_v2.py create --smart            # 智能创建（只对有逻辑的文件创建）
  python3 tools/spec-tools/spec_md_manager_v2.py report                    # 生成覆盖度报告
  python3 tools/spec-tools/spec_md_manager_v2.py report --density           # 信息密度报告（区分空壳/有内容）

新增 v2 功能：
  python3 tools/spec-tools/spec_md_manager_v2.py init <spec-file>                        # 为现有 spec.md 添加增强字段
  python3 tools/spec-tools/spec_md_manager_v2.py audit <spec-file> --action <op> ...     # 记录审计追踪条目
  python3 tools/spec-tools/spec_md_manager_v2.py review --stale-days <N> [--dir <path>]  # 列出过期未审规则
  python3 tools/spec-tools/spec_md_manager_v2.py challenge <spec-file> --rule <r> ...    # 添加质疑记录
  python3 tools/spec-tools/spec_md_manager_v2.py sunset <spec-file> --rule <r> --date <YYYY-MM-DD>  # 设置 Sunset
  python3 tools/spec-tools/spec_md_manager_v2.py confidence <spec-file> --rule <r> --level <lvl>      # 设置可信度
  python3 tools/spec-tools/spec_md_manager_v2.py clean [--dry-run|--force]              # 清理纯数据文件的空壳 spec.md
"""

import os
import sys
import re
import argparse
from datetime import datetime, date, timedelta
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent if "skills" in str(Path(__file__).parent) else Path(__file__).parent.parent

# ---- v1 保留配置 ----

EXCLUDE_DIRS = {"obj", "bin", "Migrations", "debug", "release", "node_modules", ".git", "tools"}
EXCLUDE_FILES = {"Program.cs", "_Imports.razor", "_Host.cshtml", "App.razor", "Routes.razor"}
INCLUDE_EXTENSIONS = {".cs", ".razor", ".razor.cs", ".razor.css", ".css"}

SPEC_TEMPLATE_V2 = """# 【{file_name}】开发约定

## 1. 文件用途
本文件是：{file_path}

---

## 2. 踩过的坑 - 永久记录

> 本文件暂无历史坑点，请在修改过程中发现问题后补充。

### ❌ 待补充...

---

## 3. 禁止修改的内容（绝对不能动）

> 根据文件实际功能填写...

---

## 4. 必须遵守的技术规范

> 根据文件实际功能填写...

---

## 5. 允许的操作

只允许：
1. ✅ 修复 bug
2. ✅ 新增指定功能
3. ✅ 优化代码可读性
4. ✅ 优化性能

---

## 6. 当前状态 - 最后验证

**最后验证时间**：{date}
**验证人**：自动创建
**验证结果**：✅ 初始创建，待验证

---

## 7. 维护提示

> 请在修改本文件后，及时更新此文档，记录踩过的坑。

---

## 📋 审计追踪

| 日期 | 操作 | 操作者 | 理由 | 影响文件数 |
|------|------|--------|------|-----------|
| {date} | 创建 | auto | 自动初始化 | 0 |

---

## 💬 质疑记录

> 暂无质疑记录。

---

## ⏰ Sunset 记录

> 暂无 Sunset 记录。

---

*本文件由 spec_md_manager_v2.py 自动创建，首次修改时请补充内容。
"""

CONFIDENCE_LEVELS = {
    "validated": (5, "由实际事故验证，有明确证据"),
    "proven": (4, "在多项目中验证有效"),
    "consensus": (3, "团队共识，基于经验"),
    "preventive": (2, "预防性规则，未实际触发"),
    "speculative": (1, "个人偏好或实验性规则"),
}

CONFIDENCE_STARS = {5: "⭐⭐⭐⭐⭐", 4: "⭐⭐⭐⭐", 3: "⭐⭐⭐", 2: "⭐⭐", 1: "⭐"}

AUDIT_ACTIONS = ["create", "modify", "strengthen", "relax", "validate", "challenge", "abolish"]

# ---- 智能分类：区分有逻辑的文件 vs 纯数据文件 ----

# 文件名包含这些关键词 → 值得建 spec.md（有业务逻辑/坑点）
MEANINGFUL_NAME_PATTERNS = [
    "Service", "Controller", "Repository", "Manager", "Handler",
    "Provider", "Component", "Page", "Workflow", "Engine", "Helper",
    "Validator", "Calculator", "Generator", "Converter", "Importer",
    "Exporter", "Authenticator", "Authorizer",
]

# 文件名包含这些关键词 → 纯数据定义，不值得建 spec.md
DATA_ONLY_NAME_PATTERNS = [
    "Entity", "Dto", "DTO", "Enum", "Record", "Model",
    "Constants", "Options", "Config", "Configuration",
    "Extensions", "Mapping", "Attribute",
]

# 目录名包含这些 → 大概率纯数据
DATA_ONLY_DIR_PATTERNS = [
    "Entities", "DTOs", "Dtos", "Enums", "Models",
    "Configuration", "Config", "Migrations",
    "Attributes", "Extensions",
]

# 目录名包含这些 → 大概率有逻辑
MEANINGFUL_DIR_PATTERNS = [
    "Services", "Controllers", "Repositories", "Managers",
    "Handlers", "Components", "Pages", "Validators",
    "Workflows", "Engines",
]

# 占位符文本（用于判断 spec.md 是否为空壳）
PLACEHOLDER_PATTERNS = [
    "暂无历史坑点",
    "待补充...",
    "根据文件实际功能填写",
    "请在修改过程中发现问题后补充",
    "首次修改时请补充内容",
]


def is_meaningful_file(file_path: Path) -> bool:
    """判断文件是否值得创建 spec.md（有业务逻辑，而非纯数据定义）"""
    file_stem = file_path.stem  # 不含扩展名的文件名
    file_dir = str(file_path.parent)

    # .razor 和 .razor.cs 文件 → 通常是组件/页面，值得建
    if file_path.suffix in (".razor", ".razor.cs"):
        return True

    # .css 文件 → 隔离样式，不需要独立 spec
    if file_path.suffix in (".css", ".razor.css"):
        return False

    # 按文件名分类
    meaningful_hit = any(p in file_stem for p in MEANINGFUL_NAME_PATTERNS)
    data_only_hit = any(p in file_stem for p in DATA_ONLY_NAME_PATTERNS)

    if meaningful_hit and not data_only_hit:
        return True
    if data_only_hit and not meaningful_hit:
        return False

    # 按目录名分类
    dir_parts = set(Path(file_dir).parts)
    in_meaningful_dir = bool(dir_parts & set(MEANINGFUL_DIR_PATTERNS))
    in_data_dir = bool(dir_parts & set(DATA_ONLY_DIR_PATTERNS))

    if in_meaningful_dir and not in_data_dir:
        return True
    if in_data_dir and not in_meaningful_dir:
        return False

    # 文件名和目录都无法判断 → 检查文件内容
    try:
        content = file_path.read_text(encoding="utf-8")
        return _has_business_logic(content)
    except Exception:
        return True  # 读不了就当有逻辑，宁可多建不可漏建


def _has_business_logic(content: str) -> bool:
    """启发式判断 C# 文件是否有业务逻辑"""
    lines = [l.strip() for l in content.split("\n") if l.strip() and not l.strip().startswith("//")]
    if len(lines) < 5:
        return False  # 极短文件大概率是简单的类定义

    # 统计可能是简单属性的行
    prop_pattern = re.compile(r'^\s*public\s+\S+\s+\S+\s*\{\s*get;\s*(set;\s*)?\}\s*$')
    prop_lines = sum(1 for l in lines if prop_pattern.match(l))
    code_lines = len(lines)

    # 如果 >70% 的行都是简单属性，判定为纯数据类
    if code_lines > 0 and prop_lines / code_lines > 0.7:
        return False

    # 检查是否有方法体
    method_count = len(re.findall(r'\b(void|Task|ActionResult|IActionResult|bool|int|string|double|decimal|DateTime|Guid)\s+\w+\s*\(', content))
    if method_count > 0:
        return True

    return True  # 默认值得建


def spec_content_quality(spec_path: Path) -> dict:
    """评估 spec.md 的内容质量（区分空壳和有内容）"""
    try:
        content = spec_path.read_text(encoding="utf-8")
    except Exception:
        return {"is_shell": True, "score": 0, "rule_count": 0, "pitfall_count": 0}

    # 统计占位符命中数
    placeholder_hits = sum(1 for p in PLACEHOLDER_PATTERNS if p in content)

    # 统计实际规则数（编号的禁止/建议/必须）
    rule_count = len(re.findall(r'^\d+\.\s+\*\*(禁止|建议|必须)\*\*', content, re.MULTILINE))

    # 统计坑点（坑N 标题）
    pitfall_count = len(re.findall(r'###\s*(?:❌|坑\d+)', content))

    # 综合评分
    if placeholder_hits >= 3 and rule_count == 0 and pitfall_count == 0:
        score = 0  # 完全空壳
        is_shell = True
    elif placeholder_hits >= 2 and rule_count <= 1:
        score = 20  # 几乎空壳
        is_shell = True
    elif placeholder_hits >= 1:
        score = 50  # 半空壳
        is_shell = False
    else:
        score = min(100, rule_count * 20 + pitfall_count * 10)
        is_shell = False

    return {
        "is_shell": is_shell,
        "score": score,
        "rule_count": rule_count,
        "pitfall_count": pitfall_count,
    }


# ---- v1 函数保留 ----

def should_process_file(file_path: Path) -> bool:
    if file_path.suffix not in INCLUDE_EXTENSIONS:
        return False
    if file_path.name in EXCLUDE_FILES:
        return False
    for part in file_path.parts:
        if part in EXCLUDE_DIRS:
            return False
    if file_path.name.endswith(".spec.md"):
        return False
    return True

def get_spec_md_path(file_path: Path) -> Path:
    path_str = str(file_path)
    if path_str.endswith(".razor.cs"):
        return Path(path_str[:-9] + ".spec.md")
    if path_str.endswith(".razor.css"):
        return Path(path_str[:-10] + ".spec.md")
    if path_str.endswith(".razor"):
        return Path(path_str[:-6] + ".spec.md")
    if path_str.endswith(".cs"):
        return Path(path_str[:-3] + ".spec.md")
    if path_str.endswith(".css"):
        return Path(path_str[:-4] + ".spec.md")
    return None

def get_all_source_files() -> list:
    src_path = PROJECT_ROOT / "src"
    files = []
    if not src_path.exists():
        src_path = PROJECT_ROOT
    for root, _, filenames in os.walk(src_path):
        for filename in filenames:
            file_path = Path(root) / filename
            if should_process_file(file_path):
                files.append(file_path)
    return sorted(files)

def cmd_scan(smart: bool = False):
    mode_label = "智能 " if smart else ""
    print(f"\n🔍 正在{mode_label}扫描解决方案中的源文件...\n")
    files = get_all_source_files()

    # 智能模式下先分类
    meaningful_files = set()
    data_only_files = set()
    if smart:
        for f in files:
            if is_meaningful_file(f):
                meaningful_files.add(f)
            else:
                data_only_files.add(f)
        scan_files = list(meaningful_files)
        skipped_data = len(data_only_files)
    else:
        scan_files = files
        skipped_data = 0

    missing_spec = []
    has_spec = []
    data_missing = []  # 智能模式下被跳过的文件

    for file_path in scan_files:
        spec_path = get_spec_md_path(file_path)
        if spec_path and spec_path.exists():
            has_spec.append(file_path)
        else:
            missing_spec.append(file_path)

    if smart:
        for f in data_only_files:
            spec_path = get_spec_md_path(f)
            if not spec_path or not spec_path.exists():
                data_missing.append(f)

    total = len(scan_files)
    covered = len(has_spec)
    missing = len(missing_spec)
    coverage = round((covered / total) * 100, 1) if total > 0 else 0

    print(f"📊 扫描结果:")
    if smart:
        print(f"   有意义文件数:  {total} (跳过 {skipped_data} 个 Entity/DTO/Enum)")
    else:
        print(f"   总文件数:      {total}")
    print(f"   已有 spec.md:  {covered} ✅")
    print(f"   缺失 spec.md:  {missing} ❌")
    print(f"   覆盖度:        {coverage}%\n")

    if smart and data_missing:
        print(f"💡 智能模式跳过的纯数据文件 ({len(data_missing)} 个，不需要 spec.md):")
        for f in data_missing[:10]:
            rel_path = f.relative_to(PROJECT_ROOT)
            print(f"   ⏭️  {rel_path}")
        if len(data_missing) > 10:
            print(f"   ... 还有 {len(data_missing) - 10} 个")
        print()

    if missing > 0:
        print("📋 缺失的文件列表 (前20个):")
        for f in missing_spec[:20]:
            rel_path = f.relative_to(PROJECT_ROOT)
            print(f"   ❌ {rel_path}")
        if missing > 20:
            print(f"   ... 还有 {missing - 20} 个文件")
        print()
    return missing_spec

def cmd_create(smart: bool = False):
    mode_label = "智能 " if smart else ""
    print(f"\n📝 开始{mode_label}批量创建 spec.md 文件...\n")
    missing_files = cmd_scan(smart=smart)
    if len(missing_files) == 0:
        print("✅ 所有文件都已有 spec.md，无需创建！\n")
        return
    created = 0
    skipped = 0
    created_specs = set()
    for file_path in missing_files:
        spec_path = get_spec_md_path(file_path)
        if spec_path in created_specs or (spec_path and spec_path.exists()):
            skipped += 1
            continue
        file_name = file_path.name
        rel_path = file_path.relative_to(PROJECT_ROOT)
        print(f"   创建: {spec_path.relative_to(PROJECT_ROOT)}")
        content = SPEC_TEMPLATE_V2.format(
            file_name=file_name,
            file_path=str(rel_path),
            date=datetime.now().strftime("%Y-%m-%d")
        )
        spec_path.write_text(content, encoding="utf-8")
        created_specs.add(spec_path)
        created += 1
    print(f"\n✅ 创建完成！")
    print(f"   新创建: {created} 个 spec.md")
    print(f"   已跳过: {skipped} 个（已存在或共用）\n")

def cmd_report(density: bool = False):
    print("\n" + "=" * 60)
    title = "Spec MD 信息密度报告 (v2)" if density else "Spec MD 覆盖度报告 (v2)"
    print(f"  {title}")
    print(f"  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")

    files = get_all_source_files()
    meaningful_files = {f for f in files if is_meaningful_file(f)}
    data_only_files = {f for f in files if not is_meaningful_file(f)}

    categories = {}
    for file_path in files:
        rel_path = file_path.relative_to(PROJECT_ROOT)
        parts = rel_path.parts
        project = parts[0] if len(parts) > 0 else "根目录"
        if project not in categories:
            categories[project] = {
                "total": 0, "covered": 0,
                "meaningful": 0, "meaningful_covered": 0,
                "shell_count": 0, "quality_scores": [],
            }
        cat = categories[project]
        cat["total"] += 1
        if file_path in meaningful_files:
            cat["meaningful"] += 1

        spec_path = get_spec_md_path(file_path)
        if spec_path and spec_path.exists():
            cat["covered"] += 1
            if file_path in meaningful_files:
                cat["meaningful_covered"] += 1

            if density:
                quality = spec_content_quality(spec_path)
                if quality["is_shell"]:
                    cat["shell_count"] += 1
                cat["quality_scores"].append(quality["score"])

    grand_total = 0
    grand_covered = 0
    grand_meaningful = 0
    grand_meaningful_covered = 0
    grand_shells = 0
    all_scores = []

    for project in sorted(categories.keys()):
        stats = categories[project]
        total = stats["total"]
        covered = stats["covered"]
        meaningful = stats["meaningful"]
        meaningful_covered = stats["meaningful_covered"]
        coverage = round((covered / total) * 100, 1) if total > 0 else 100

        if density:
            meaningful_cov = round((meaningful_covered / meaningful) * 100, 1) if meaningful > 0 else 100
            shells = stats["shell_count"]
            avg_score = round(sum(stats["quality_scores"]) / len(stats["quality_scores"]), 1) if stats["quality_scores"] else 0
            status = "✅" if meaningful_cov >= 80 else "⚠️" if meaningful_cov >= 50 else "❌"
            print(f"{status} {project}:")
            print(f"     总量 {total} | 有意义 {meaningful} | 纯数据 {total - meaningful}")
            print(f"     有意义覆盖率 {meaningful_cov}% ({meaningful_covered}/{meaningful})")
            print(f"     空壳 {shells} 个 | 平均质量分 {avg_score}/100")
            print()
        else:
            status = "✅" if coverage == 100 else "⚠️" if coverage >= 70 else "❌"
            print(f"{status} {project}: {total} 个文件, 覆盖 {covered} 个, 覆盖率 {coverage}%")

        grand_total += total
        grand_covered += covered
        grand_meaningful += meaningful
        grand_meaningful_covered += meaningful_covered
        grand_shells += stats["shell_count"]
        all_scores.extend(stats["quality_scores"])

    print("=" * 60)

    if density:
        meaningful_coverage = round((grand_meaningful_covered / grand_meaningful) * 100, 1) if grand_meaningful > 0 else 100
        coverage = round((grand_covered / grand_total) * 100, 1) if grand_total > 0 else 100
        avg_score = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0
        print(f"  📊 总计")
        print(f"     总文件 {grand_total} | 有意义 {grand_meaningful} | 纯数据 {grand_total - grand_meaningful}")
        print(f"     粗覆盖率 {coverage}% | 有意义覆盖率 {meaningful_coverage}%")
        print(f"     空壳 {grand_shells}/{grand_covered} | 平均质量分 {avg_score}/100")
        if meaningful_coverage < 80:
            print(f"\n  ⚠️  有意义文件覆盖率低于 80%")
            print(f"  建议: python3 tools/spec_md_manager_v2.py create --smart")
        if grand_shells > grand_covered * 0.3:
            print(f"  ⚠️  空壳比例过高 ({round(grand_shells/max(grand_covered,1)*100,0)}%)，建议淘汰纯数据文件的空壳 spec.md")
    else:
        grand_coverage = round((grand_covered / grand_total) * 100, 1) if grand_total > 0 else 100
        print(f"  📊 总计: {grand_total} 个文件, 覆盖 {grand_covered} 个, 总覆盖率 {grand_coverage}%")
        if grand_coverage < 80:
            print(f"\n  ⚠️  覆盖率低于 80%，建议执行 python3 tools/spec_md_manager_v2.py create")
        else:
            print(f"  🎉 覆盖度良好！")

    print("=" * 60 + "\n")

# ---- v2 新增功能 ----

# ---- spec.md 内容解析 ----

def read_spec(spec_path: str) -> str:
    """读取 spec.md 内容"""
    p = Path(spec_path)
    if not p.exists():
        print(f"❌ 文件不存在: {spec_path}")
        sys.exit(1)
    return p.read_text(encoding="utf-8")

def write_spec(spec_path: str, content: str):
    """写入 spec.md 内容"""
    Path(spec_path).write_text(content, encoding="utf-8")

def has_audit_trail(content: str) -> bool:
    """检查是否已有审计追踪表格"""
    return "## 📋 审计追踪" in content or "## 审计追踪" in content

def has_challenge_section(content: str) -> bool:
    """检查是否已有质疑记录章节"""
    return "## 💬 质疑记录" in content or "## 质疑记录" in content

def has_sunset_section(content: str) -> bool:
    """检查是否已有 Sunset 记录章节"""
    return "## ⏰ Sunset" in content or "## Sunset" in content

def has_confidence_annotations(content: str) -> bool:
    """检查是否已有可信度标注"""
    return "[confidence:" in content

def find_section_end(content: str, start_pos: int) -> int:
    """找到章节结束位置（下一个 ## 标题之前）"""
    next_section = content.find("\n## ", start_pos + 1)
    if next_section == -1:
        return len(content)
    return next_section

# ---- init 命令 ----

def cmd_init(spec_path: str):
    """为现有 spec.md 添加增强字段（审计追踪、质疑记录、Sunset 记录）"""
    print(f"\n🔧 正在升级 spec.md: {spec_path}\n")
    content = read_spec(spec_path)
    today = datetime.now().strftime("%Y-%m-%d")

    additions = []
    modified = False

    # 检查并添加审计追踪
    if not has_audit_trail(content):
        audit_section = f"""\n## 📋 审计追踪

| 日期 | 操作 | 操作者 | 理由 | 影响文件数 |
|------|------|--------|------|-----------|
| {today} | 创建 | init | 由 spec_md_manager_v2.py init 升级 | 0 |

"""
        additions.append(("审计追踪", audit_section))
        modified = True

    # 检查并添加质疑记录
    if not has_challenge_section(content):
        challenge_section = """\n## 💬 质疑记录

> 暂无质疑记录。

"""
        additions.append(("质疑记录", challenge_section))
        modified = True

    # 检查并添加 Sunset 记录
    if not has_sunset_section(content):
        sunset_section = """\n## ⏰ Sunset 记录

> 暂无 Sunset 记录。

"""
        additions.append(("Sunset记录", sunset_section))
        modified = True

    for name, section in additions:
        content += section
        print(f"   ✅ 已添加 {name} 章节")

    if not modified:
        print("   ℹ️  文件已包含所有增强字段，无需升级。")
    else:
        write_spec(spec_path, content)
        print(f"\n✅ 升级完成！共添加 {len(additions)} 个增强章节。\n")

# ---- audit 命令 ----

def cmd_audit(spec_path: str, action: str, operator: str, reason: str, affected_files: int = 0):
    """在 spec.md 的审计追踪表格中添加一条记录"""
    if action not in AUDIT_ACTIONS:
        print(f"❌ 无效操作类型: {action}。有效值: {', '.join(AUDIT_ACTIONS)}")
        sys.exit(1)

    content = read_spec(spec_path)
    today = datetime.now().strftime("%Y-%m-%d")

    if not has_audit_trail(content):
        print("⚠️  文件没有审计追踪章节，请先运行 init 命令。")
        sys.exit(1)

    # 在审计追踪表格末尾添加一行
    new_row = f"| {today} | {action} | {operator} | {reason} | {affected_files} |\n"

    # 找到审计追踪表格的末尾
    audit_start = content.find("## 📋 审计追踪")
    if audit_start == -1:
        audit_start = content.find("## 审计追踪")

    if audit_start == -1:
        print("❌ 无法找到审计追踪章节")
        sys.exit(1)

    # 找到表格末尾（## 或连续空行后非表格行）
    table_end = content.find("\n## ", audit_start + 1)
    if table_end == -1:
        table_end = len(content)

    # 在表格末尾插入新行（在分隔线或空行之前）
    # 找到最后的表格行
    lines = content[audit_start:table_end].split("\n")
    last_table_line = -1
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].startswith("|"):
            last_table_line = i
            break

    if last_table_line == -1:
        # 表格为空，插入在表头之后
        header_end = audit_start
        for i, line in enumerate(lines):
            if line.startswith("|") and "---" in line:
                header_end = audit_start + len("\n".join(lines[:i+2]))
                break
        content = content[:header_end] + "\n" + new_row.strip() + content[header_end:]
    else:
        insert_pos = audit_start + len("\n".join(lines[:last_table_line + 1]))
        content = content[:insert_pos] + "\n" + new_row.rstrip() + content[insert_pos:]

    write_spec(spec_path, content)
    print(f"✅ 审计追踪已更新: {action} by {operator} on {today}")
    print(f"   理由: {reason}")
    if affected_files > 0:
        print(f"   影响文件数: {affected_files}")

# ---- review 命令 ----

def parse_audit_last_review(content: str) -> dict:
    """解析审计追踪，返回每条规则的最后审查日期"""
    # 简单实现：找到审计追踪表格中最后一次"验证"操作
    audit_match = re.search(r'## 📋 审计追踪.*?(?=\n## |\Z)', content, re.DOTALL)
    if not audit_match:
        audit_match = re.search(r'## 审计追踪.*?(?=\n## |\Z)', content, re.DOTALL)
    if not audit_match:
        return None

    audit_section = audit_match.group(0)
    # 找最后一条 validate 操作的日期
    validate_dates = re.findall(r'\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*验证', audit_section)
    if not validate_dates:
        # 找最后一条操作的日期（作为替代）
        all_dates = re.findall(r'\|\s*(\d{4}-\d{2}-\d{2})\s*\|', audit_section)
        if all_dates:
            return {"last_review": all_dates[-1], "is_validate": False}
        return None

    return {"last_review": validate_dates[-1], "is_validate": True}

def parse_confidence_from_content(content: str) -> list:
    """从 spec.md 内容中提取所有规则的可信度标注"""
    rules = []
    # 匹配 [confidence:xxx] 标注
    for m in re.finditer(r'\[confidence:(\w+)\]', content):
        level = m.group(1)
        # 找到这条规则的标题
        line_start = content.rfind('\n', 0, m.start()) + 1
        line_end = content.find('\n', m.end())
        title = content[line_start:line_end].strip()[:80]
        rules.append({"level": level, "title": title, "pos": m.start()})
    return rules

def parse_sunset_from_content(content: str) -> list:
    """从 spec.md 中提取所有 Sunset 标注"""
    sunsets = []
    for m in re.finditer(r'\[sunset:(\d{4}-\d{2}-\d{2})\]', content):
        sunset_date = m.group(1)
        line_start = content.rfind('\n', 0, m.start()) + 1
        line_end = content.find('\n', m.end())
        title = content[line_start:line_end].strip()[:80]
        sunsets.append({"date": sunset_date, "title": title, "pos": m.start()})
    return sunsets

def cmd_review(stale_days: int = 90, search_dir: str = None, show_sunsets: bool = False):
    """列出需要审查的 spec.md 规则"""
    print(f"\n📋 审查提醒 - 超过 {stale_days} 天未审查的规则\n")

    if search_dir is None:
        search_dir = PROJECT_ROOT

    spec_files = list(Path(search_dir).rglob("*.spec.md"))
    stale_count = 0
    today = date.today()

    for spec_path in sorted(spec_files):
        try:
            content = spec_path.read_text(encoding="utf-8")
        except Exception:
            continue

        # 检查审计追踪中的最后审查日期
        review_info = parse_audit_last_review(content)
        is_stale = False
        days_since = None

        if review_info:
            try:
                last_date = datetime.strptime(review_info["last_review"], "%Y-%m-%d").date()
                days_since = (today - last_date).days
                if days_since > stale_days:
                    is_stale = True
            except ValueError:
                pass

        # 检查 Sunset 日期
        sunsets = parse_sunset_from_content(content) if show_sunsets else []
        expired_sunsets = [s for s in sunsets if s["date"] < today.strftime("%Y-%m-%d")]

        if is_stale or expired_sunsets:
            stale_count += 1
            rel_path = spec_path.relative_to(PROJECT_ROOT)
            print(f"⚠️  {rel_path}")
            if is_stale and days_since:
                print(f"      上次审查: {review_info['last_review']} ({days_since} 天前)")
            for s in expired_sunsets:
                print(f"      ⏰ Sunset 已过期: {s['date']} - {s['title']}")

    if stale_count == 0:
        print("   ✅ 所有 spec.md 规则均在有效期内！\n")
    else:
        print(f"\n📊 共发现 {stale_count} 个需要审查的文件")
        print("   建议：安排团队审查会议，逐条确认规则是否仍然有效。\n")

# ---- challenge 命令 ----

def cmd_challenge(spec_path: str, rule: str, challenger: str, reason: str, suggestion: str = ""):
    """在 spec.md 中添加质疑记录"""
    content = read_spec(spec_path)
    today = datetime.now().strftime("%Y-%m-%d")

    if not has_challenge_section(content):
        print("⚠️  文件没有质疑记录章节，请先运行 init 命令。")
        sys.exit(1)

    # 查找质疑记录章节并计算质疑编号
    challenge_start = content.find("## 💬 质疑记录")
    if challenge_start == -1:
        challenge_start = content.find("## 质疑记录")

    if challenge_start == -1:
        print("❌ 无法找到质疑记录章节")
        sys.exit(1)

    # 计算现有质疑数量
    existing_section = content[challenge_start:]
    challenge_count = len(re.findall(r'### 质疑 #\d+', existing_section))
    challenge_num = challenge_count + 1

    # 构建质疑记录
    record = f"""### 质疑 #{challenge_num}（{today}，{challenger}）
**质疑的规则**：{rule}
**质疑理由**：
{reason}
"""

    if suggestion:
        record += f"""**建议方案**：{suggestion}
"""
    else:
        record += """**建议方案**：（待补充）
"""

    record += """**决议**：⏳ 待决议
**理由**：-
"""

    # 在质疑记录章节末尾插入（在下一个 ## 或文件末尾之前）
    challenge_end = content.find("\n## ", challenge_start + 1)
    if challenge_end == -1:
        challenge_end = len(content)

    # 找到 "暂无质疑记录" 并替换
    placeholder_pos = content.find("> 暂无质疑记录。", challenge_start)
    if placeholder_pos != -1 and placeholder_pos < challenge_end:
        # 替换占位符
        before = content[:placeholder_pos]
        after = content[placeholder_pos + len("> 暂无质疑记录。"):]
        content = before + "\n" + record.strip() + "\n" + after
    else:
        # 在章节末尾追加
        content = content[:challenge_end] + "\n" + record.strip() + "\n" + content[challenge_end:]

    write_spec(spec_path, content)
    print(f"✅ 质疑记录 #{challenge_num} 已添加")
    print(f"   规则: {rule}")
    print(f"   质疑者: {challenger}")

# ---- sunset 命令 ----

def cmd_set_sunset(spec_path: str, rule_pattern: str, sunset_date: str):
    """为 spec.md 中的规则设置 Sunset 日期"""
    content = read_spec(spec_path)
    today = datetime.now().strftime("%Y-%m-%d")

    if not has_sunset_section(content):
        print("⚠️  文件没有 Sunset 记录章节，请先运行 init 命令。")
        sys.exit(1)

    # 查找包含 rule_pattern 的行
    lines = content.split("\n")
    rule_found = False
    for i, line in enumerate(lines):
        if rule_pattern.lower() in line.lower() and line.strip().startswith(("1.", "2.", "3.", "4.", "5.", "- **", "###")):
            # 在此行前插入 Sunset 信息
            confidence_match = re.search(r'\[confidence:(\w+)\]', line)
            level = confidence_match.group(1) if confidence_match else "consensus"

            sunset_info = f"> ⏰ 此规则在 {sunset_date} 前有效，届时需重新评估"
            if f"[sunset:" not in line:
                # 检查是否已有 [confidence:xxx] 标注，将 [sunset:xxx] 插入在同一行
                if "[confidence:" in line:
                    lines[i] = line.rstrip() + f" [sunset:{sunset_date}]"
                else:
                    lines[i] = line.rstrip() + f" [sunset:{sunset_date}]"
                # 在下一行插入 Sunset 说明
                lines.insert(i + 1, sunset_info)
            else:
                # 更新已有的 sunset 标注
                lines[i] = re.sub(r'\[sunset:[^\]]+\]', f'[sunset:{sunset_date}]', line)
            rule_found = True
            break

    if not rule_found:
        print(f"⚠️  未找到匹配的规则: {rule_pattern}")
        sys.exit(1)

    content = "\n".join(lines)

    # 同时更新 Sunset 记录表格
    sunset_start = content.find("## ⏰ Sunset")
    if sunset_start == -1:
        sunset_start = content.find("## Sunset")

    if sunset_start != -1:
        sunset_end = content.find("\n## ", sunset_start + 1)
        if sunset_end == -1:
            sunset_end = len(content)

        # 替换占位符
        placeholder_pos = content.find("> 暂无 Sunset 记录。", sunset_start)
        if placeholder_pos != -1 and placeholder_pos < sunset_end:
            table_content = f"""| {rule_pattern[:60]} | {level} | {sunset_date} | 🔵 活跃 |
|------|--------|------|------|
"""
            before = content[:placeholder_pos]
            after = content[placeholder_pos + len("> 暂无 Sunset 记录。"):]
            content = before + table_content + after
        else:
            # 追加到表格
            new_row = f"| {rule_pattern[:60]} | {level} | {sunset_date} | 🔵 活跃 |\n"
            content = content[:sunset_end] + new_row + content[sunset_end:]

    write_spec(spec_path, content)
    print(f"✅ Sunset 已设置")
    print(f"   规则: {rule_pattern}")
    print(f"   Sunset 日期: {sunset_date}")

# ---- confidence 命令 ----

def cmd_set_confidence(spec_path: str, rule_pattern: str, level: str):
    """为 spec.md 中的规则设置可信度等级"""
    if level not in CONFIDENCE_LEVELS:
        print(f"❌ 无效的可信度等级: {level}")
        print(f"   有效值: {', '.join(CONFIDENCE_LEVELS.keys())}")
        sys.exit(1)

    content = read_spec(spec_path)
    stars, description = CONFIDENCE_LEVELS[level]

    lines = content.split("\n")
    rule_found = False
    for i, line in enumerate(lines):
        if rule_pattern.lower() in line.lower() and line.strip().startswith(("1.", "2.", "3.", "4.", "5.", "- **", "###")):
            # 添加或更新 [confidence:xxx] 标注
            existing = re.search(r'\[confidence:\w+\]', line)
            if existing:
                lines[i] = line[:existing.start()] + f'[confidence:{level}]' + line[existing.end():]
            else:
                lines[i] = line.rstrip() + f' [confidence:{level}]'

            # 在下一行插入可信度说明
            confidence_info = f'> **可信度**: {CONFIDENCE_STARS[stars]} ({description})'
            # 检查是否已有可信度注释行
            if i + 1 < len(lines) and lines[i + 1].strip().startswith("> **可信度**:"):
                lines[i + 1] = confidence_info
            else:
                lines.insert(i + 1, confidence_info)
            rule_found = True
            break

    if not rule_found:
        print(f"⚠️  未找到匹配的规则: {rule_pattern}")
        sys.exit(1)

    content = "\n".join(lines)
    write_spec(spec_path, content)
    print(f"✅ 可信度已设置")
    print(f"   规则: {rule_pattern}")
    print(f"   等级: {level} ({CONFIDENCE_STARS[stars]})")

# ---- list-rules 命令 ----

def cmd_list_rules(spec_path: str):
    """列出 spec.md 中的所有规则（带可信度和 Sunset 信息）"""
    content = read_spec(spec_path)
    today = date.today()

    print(f"\n📋 规则清单: {spec_path}\n")
    print(f"{'#':<4} {'规则':<50} {'可信度':<18} {'Sunset':<12} {'状态':<8}")
    print("-" * 92)

    # 提取规则编号行
    rule_pattern = re.compile(r'^(\d+)\.\s+\*\*(禁止|建议|必须)\*\*\s+(.+)$', re.MULTILINE)
    rule_num = 0
    for m in rule_pattern.finditer(content):
        rule_num += 1
        rule_text = m.group(3)[:45].strip()
        full_line = m.group(0)

        # 检查可信度
        conf_match = re.search(r'\[confidence:(\w+)\]', full_line)
        if conf_match:
            level = conf_match.group(1)
            conf_display = f"{level} ({CONFIDENCE_STARS[CONFIDENCE_LEVELS[level][0]]})"
        else:
            conf_display = "未标注"

        # 检查 Sunset
        sunset_match = re.search(r'\[sunset:(\d{4}-\d{2}-\d{2})\]', full_line)
        status = "🔵"
        if sunset_match:
            sunset_date = sunset_match.group(1)
            sunset_display = sunset_date
            try:
                if datetime.strptime(sunset_date, "%Y-%m-%d").date() < today:
                    status = "🔴 过期"
            except ValueError:
                pass
        else:
            sunset_display = "-"

        print(f"{rule_num:<4} {rule_text:<50} {conf_display:<18} {sunset_display:<12} {status:<8}")

    if rule_num == 0:
        print("   (未找到格式化规则)")
    print(f"\n   共 {rule_num} 条规则\n")

# ---- clean 命令 ----

def cmd_clean(dry_run: bool = False, force: bool = False):
    """清理纯数据文件的空壳 spec.md"""
    mode = "预览" if dry_run else "清理"
    print(f"\n🧹 开始{mode}空壳 spec.md 文件...\n")

    files = get_all_source_files()
    to_delete = []

    for file_path in files:
        # 跳过有意义文件的 spec.md
        if is_meaningful_file(file_path):
            continue

        spec_path = get_spec_md_path(file_path)
        if not spec_path or not spec_path.exists():
            continue

        # 检查是否是空壳
        quality = spec_content_quality(spec_path)
        if quality["is_shell"]:
            to_delete.append((file_path, spec_path, quality))

    if not to_delete:
        print("   ✅ 没有可清理的空壳 spec.md 文件。\n")
        return

    print(f"   发现 {len(to_delete)} 个纯数据文件的空壳 spec.md:\n")
    for file_path, spec_path, quality in to_delete:
        rel = spec_path.relative_to(PROJECT_ROOT)
        score = quality["score"]
        print(f"   🗑️  {rel} (质量分: {score}/100) ← {file_path.name}")

    print(f"\n   这些文件对应的代码文件是 Entity/DTO/Enum/纯数据类，")
    print(f"   spec.md 内容为空壳占位符，边际价值为零。\n")

    if dry_run:
        print(f"💡 执行以下命令实际删除:")
        print(f"   python3 tools/spec-tools/spec_md_manager_v2.py clean\n")
        return

    if not force:
        resp = input("   确认删除以上 {0} 个文件? [y/N]: ".format(len(to_delete)))
        if resp.lower() not in ("y", "yes"):
            print("   已取消。\n")
            return

    deleted = 0
    for _, spec_path, _ in to_delete:
        try:
            spec_path.unlink()
            rel = spec_path.relative_to(PROJECT_ROOT)
            print(f"   ✅ 已删除: {rel}")
            deleted += 1
        except Exception as e:
            print(f"   ❌ 删除失败: {spec_path}: {e}")

    print(f"\n✅ 清理完成，共删除 {deleted} 个空壳 spec.md")
    print(f"💡 建议运行 python3 tools/spec_md_manager_v2.py report --density 查看效果\n")


# ---- 主入口 ----

def build_parser():
    parser = argparse.ArgumentParser(
        description="Spec MD 约定文件管理器 v2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s scan                          扫描缺失的 spec.md
  %(prog)s create                        批量创建缺失的 spec.md
  %(prog)s report                        生成覆盖度报告
  %(prog)s init 架构总纲.spec.md         为现有文件添加增强字段
  %(prog)s audit 架构总纲.spec.md --action modify --operator @zhangsan --reason "修改分层规则" --files 5
  %(prog)s review --stale-days 90        列出超过90天未审查的规则
  %(prog)s review --stale-days 90 --show-sunsets  同时检查 Sunset 过期
  %(prog)s challenge 架构总纲.spec.md --rule "禁止style" --challenger @wangwu --reason "MudBlazor需要" --suggestion "限制10行内"
  %(prog)s sunset 架构总纲.spec.md --rule "Async后缀" --date 2026-09-01
  %(prog)s confidence 架构总纲.spec.md --rule "分层架构红线" --level validated
  %(prog)s list-rules 架构总纲.spec.md   列出所有规则及其状态
        """
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # scan
    scan_parser = subparsers.add_parser("scan", help="扫描缺失 spec.md 的代码文件")
    scan_parser.add_argument("--smart", action="store_true", help="智能模式：跳过 Entity/DTO/Enum 等纯数据文件")

    # create
    create_parser = subparsers.add_parser("create", help="批量创建缺失的 spec.md")
    create_parser.add_argument("--smart", action="store_true", help="智能模式：只为有业务逻辑的文件创建 spec.md")

    # report
    report_parser = subparsers.add_parser("report", help="生成覆盖度报告")
    report_parser.add_argument("--density", action="store_true", help="信息密度模式：区分空壳/有内容，显示质量分")

    # init
    init_parser = subparsers.add_parser("init", help="为现有 spec.md 添加增强字段")
    init_parser.add_argument("spec_file", help="spec.md 文件路径")

    # audit
    audit_parser = subparsers.add_parser("audit", help="记录审计追踪条目")
    audit_parser.add_argument("spec_file", help="spec.md 文件路径")
    audit_parser.add_argument("--action", required=True, choices=AUDIT_ACTIONS, help="操作类型")
    audit_parser.add_argument("--operator", required=True, help="操作者")
    audit_parser.add_argument("--reason", required=True, help="变更理由")
    audit_parser.add_argument("--files", type=int, default=0, help="影响文件数")

    # review
    review_parser = subparsers.add_parser("review", help="列出需要审查的规则")
    review_parser.add_argument("--stale-days", type=int, default=90, help="未审天数阈值（默认90）")
    review_parser.add_argument("--dir", help="搜索目录（默认项目根目录）")
    review_parser.add_argument("--show-sunsets", action="store_true", help="同时显示 Sunset 已过期的规则")

    # challenge
    challenge_parser = subparsers.add_parser("challenge", help="添加质疑记录")
    challenge_parser.add_argument("spec_file", help="spec.md 文件路径")
    challenge_parser.add_argument("--rule", required=True, help="被质疑的规则描述")
    challenge_parser.add_argument("--challenger", required=True, help="质疑者")
    challenge_parser.add_argument("--reason", required=True, help="质疑理由")
    challenge_parser.add_argument("--suggestion", help="建议方案")

    # sunset
    sunset_parser = subparsers.add_parser("sunset", help="设置 Sunset 日期")
    sunset_parser.add_argument("spec_file", help="spec.md 文件路径")
    sunset_parser.add_argument("--rule", required=True, help="规则关键词")
    sunset_parser.add_argument("--date", required=True, help="Sunset 日期 (YYYY-MM-DD)")

    # confidence
    conf_parser = subparsers.add_parser("confidence", help="设置可信度等级")
    conf_parser.add_argument("spec_file", help="spec.md 文件路径")
    conf_parser.add_argument("--rule", required=True, help="规则关键词")
    conf_parser.add_argument("--level", required=True, choices=list(CONFIDENCE_LEVELS.keys()), help="可信度等级")

    # list-rules
    list_parser = subparsers.add_parser("list-rules", help="列出所有规则及其状态")
    list_parser.add_argument("spec_file", help="spec.md 文件路径")

    # clean
    clean_parser = subparsers.add_parser("clean", help="清理纯数据文件的空壳 spec.md")
    clean_parser.add_argument("--dry-run", action="store_true", help="仅列出将要删除的文件，不实际删除")
    clean_parser.add_argument("--force", action="store_true", help="不询问确认直接删除")

    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "scan":
        cmd_scan(smart=args.smart)
    elif args.command == "create":
        cmd_create(smart=args.smart)
    elif args.command == "report":
        cmd_report(density=args.density)
    elif args.command == "init":
        cmd_init(args.spec_file)
    elif args.command == "audit":
        cmd_audit(args.spec_file, args.action, args.operator, args.reason, args.files)
    elif args.command == "review":
        cmd_review(args.stale_days, args.dir)
    elif args.command == "challenge":
        cmd_challenge(args.spec_file, args.rule, args.challenger, args.reason, args.suggestion)
    elif args.command == "sunset":
        cmd_set_sunset(args.spec_file, args.rule, args.date)
    elif args.command == "confidence":
        cmd_set_confidence(args.spec_file, args.rule, args.level)
    elif args.command == "list-rules":
        cmd_list_rules(args.spec_file)
    elif args.command == "clean":
        cmd_clean(dry_run=args.dry_run, force=args.force)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
