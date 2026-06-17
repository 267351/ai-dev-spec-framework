#!/usr/bin/env python3
"""
Spec 合规性检查 Agent (AI 审查)
在代码提交前，读取 spec.md 并检查变更是否符合约束。

工作原理：
1. 接收 git diff 或变更文件列表
2. 找到变更文件对应的 spec.md
3. 提取 spec.md 中的可验证规则（尤其是 semantic/contextual 类型）
4. 构建 AI 审查 Prompt
5. 输出合规性报告

使用方法：
  python3 tools/spec-tools/spec_compliance_check.py --diff <git-diff-output>              # 检查 diff
  python3 tools/spec-tools/spec_compliance_check.py --changed-files <file1,file2,...>   # 检查文件变更
  python3 tools/spec-tools/spec_compliance_check.py --staged                             # 检查 git staged 变更
  python3 tools/spec-tools/spec_compliance_check.py --spec <spec.md> --code <code-file>  # 单文件检查
  python3 tools/spec-tools/spec_compliance_check.py --pre-commit-hook                    # 生成 pre-commit hook 配置

输出：合规性报告 (JSON/Markdown)
"""

import os
import sys
import re
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent if "skills" in str(SCRIPT_DIR) else SCRIPT_DIR.parent


# ---- Prompt 模板 ----

REVIEW_SYSTEM_PROMPT = """你是一个代码合规性审查专家。你的任务是根据 spec.md 中定义的约束，
检查代码变更是否符合规范。

审查规则：
1. 只关注 spec.md 中明确规定的约束（特别是"禁止修改的内容"和"必须遵守的技术规范"）
2. 不要提出 spec.md 未明确规定的建议
3. 对于不确定的项目，标记为"需人工确认"而非直接判定违规
4. 每个判断必须引用具体的 spec.md 规则
5. 区分违规严重度：
   - 🔴 违规: 明确违反 spec.md 铁律（阻止合并）
   - 🟡 警告: 违反了建议性规范（建议修改）
   - 🔵 建议: 代码可以改进但未违反规范

输出格式：JSON
{
  "spec_file": "被引用的 spec.md 路径",
  "rules_checked": 检查的规则数量,
  "verdicts": [
    {
      "rule_id": "WM-ARCH-001",
      "rule_description": "规则描述",
      "severity": "error|warning|suggestion",
      "verdict": "pass|fail|warning|manual_review",
      "explanation": "详细解释",
      "affected_code": "受影响的代码位置"
    }
  ],
  "summary": {
    "total": N,
    "passed": N,
    "failed": N,
    "warnings": N,
    "manual_review": N
  },
  "recommendation": "approve|reject|review"
}"""


def build_user_prompt(spec_content: str, code_diff: str, file_path: str = "") -> str:
    """构建用户 Promp（spec.md 内容 + 代码变更）"""
    return f"""请检查以下代码变更是否符合 spec.md 规范。

## Spec 文件内容

{spec_content[:8000]}

## 代码变更 (git diff)

文件: {file_path}

```diff
{code_diff[:12000]}
```

请逐条检查 spec.md 中的"禁止修改的内容"和"必须遵守的技术规范"是否被违反。
以 JSON 格式输出审查结果。"""


def build_structured_prompt(rules: list, code_diff: str, file_path: str = "") -> str:
    """构建结构化 Promp（仅提取关键规则 + 代码变更）"""
    rules_text = ""
    for r in rules:
        sev = r.get("severity", "warning")
        icon = {"error": "🔴", "warning": "🟡", "suggestion": "🔵"}.get(sev, "⚪")
        rules_text += f"\n### {icon} 规则 {r.get('id', '-')}: {r.get('title', '')}\n"
        if r.get("checks"):
            for c in r["checks"]:
                rules_text += f"  - 检查: {c}\n"
        if r.get("patterns"):
            for p in r["patterns"]:
                rules_text += f"  - 模式: {p}\n"
        if r.get("description"):
            rules_text += f"  - 描述: {r['description'][:200]}\n"

    return f"""请检查以下代码变更是否符合规范约束。

## 适用规则

{rules_text[:6000]}

## 代码变更

文件: {file_path}

```diff
{code_diff[:10000]}
```

请以 JSON 格式输出审查结果。"""


# ---- Git 操作 ----

def get_git_root() -> Path:
    """获取 Git 根目录"""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, cwd=PROJECT_ROOT
    )
    if result.returncode != 0:
        return PROJECT_ROOT
    return Path(result.stdout.strip())


def get_staged_diff() -> str:
    """获取 git staged 变更"""
    result = subprocess.run(
        ["git", "diff", "--cached"],
        capture_output=True, text=True, cwd=get_git_root()
    )
    return result.stdout


def get_changed_files_from_diff(diff_text: str) -> list:
    """从 diff 文本中提取变更文件列表"""
    files = re.findall(r'^\+\+\+ b/(.+)$', diff_text, re.MULTILINE)
    return [f for f in files if f != "/dev/null"]


def find_spec_for_file(file_path: str, project_root: Path = None) -> str:
    """为代码文件查找对应的 spec.md"""
    if project_root is None:
        project_root = get_git_root()

    file_path_obj = Path(file_path)
    if not file_path_obj.is_absolute():
        file_path_obj = project_root / file_path_obj

    # .razor.cs -> .spec.md
    path_str = str(file_path_obj)
    spec_candidates = []

    if path_str.endswith(".razor.cs"):
        spec_candidates.append(Path(path_str[:-9] + ".spec.md"))
    elif path_str.endswith(".razor.css"):
        spec_candidates.append(Path(path_str[:-10] + ".spec.md"))
    elif path_str.endswith(".razor"):
        spec_candidates.append(Path(path_str[:-6] + ".spec.md"))
    elif path_str.endswith(".cs"):
        spec_candidates.append(Path(path_str[:-3] + ".spec.md"))
    elif path_str.endswith(".css"):
        spec_candidates.append(Path(path_str[:-4] + ".spec.md"))

    for candidate in spec_candidates:
        if candidate.exists():
            return str(candidate)

    return None


def find_all_specs_in_project(project_root: Path = None) -> list:
    """查找项目中所有 spec.md 文件"""
    if project_root is None:
        project_root = get_git_root()
    return list(project_root.rglob("*.spec.md"))


# ---- 主功能 ----

def cmd_check_diff(diff_text: str, structured: bool = False):
    """检查 git diff 是否符合 spec 约束"""
    changed_files = get_changed_files_from_diff(diff_text)

    if not changed_files:
        print("✅ 没有检测到代码变更。")
        return

    print(f"\n🔍 Spec 合规性检查\n")
    print(f"   变更文件数: {len(changed_files)}")

    findings = []
    found_spec = False

    for file_path in changed_files:
        spec_path = find_spec_for_file(file_path)
        if spec_path:
            found_spec = True
            try:
                spec_content = Path(spec_path).read_text(encoding="utf-8")

                # 提取关键规则
                if structured:
                    # 使用 spec_rule_extractor 提取结构化规则
                    rules = _extract_rules_from_spec(spec_path)
                    if rules:
                        prompt = build_structured_prompt(rules, diff_text, file_path)
                    else:
                        prompt = build_user_prompt(spec_content, diff_text, file_path)
                else:
                    prompt = build_user_prompt(spec_content, diff_text, file_path)

                findings.append({
                    "file": file_path,
                    "spec": spec_path,
                    "has_spec": True,
                    "prompt_ready": True,
                    "prompt": prompt,
                    "spec_content": spec_content,
                })
            except Exception as e:
                findings.append({
                    "file": file_path,
                    "spec": spec_path,
                    "has_spec": True,
                    "prompt_ready": False,
                    "error": str(e),
                })
        else:
            findings.append({
                "file": file_path,
                "spec": None,
                "has_spec": False,
            })

    # 输出结果
    _output_check_results(findings, found_spec)


def cmd_check_staged(structured: bool = False):
    """检查 git staged 变更"""
    diff_text = get_staged_diff()
    if not diff_text:
        print("✅ 没有 staged 的变更。")
        return
    cmd_check_diff(diff_text, structured)


def cmd_check_single_file(spec_path: str, code_path: str):
    """检查单个代码文件是否符合对应 spec.md"""
    try:
        spec_content = Path(spec_path).read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"❌ spec 文件不存在: {spec_path}")
        sys.exit(1)

    try:
        code_content = Path(code_path).read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"❌ 代码文件不存在: {code_path}")
        sys.exit(1)

    # 模拟 diff（全量代码）
    diff = f"--- a/{code_path}\n+++ b/{code_path}\n@@ -0,0 +1,{len(code_content.splitlines())} @@\n"
    for line in code_content.splitlines():
        diff += f"+{line}\n"

    prompt = build_user_prompt(spec_content, diff, code_path)

    print("\n" + "=" * 60)
    print(f"  Spec 合规性检查: {code_path}")
    print("=" * 60 + "\n")

    print(f"📄 Spec 文件: {spec_path}")
    print(f"📄 代码文件: {code_path}")
    print(f"\n--- AI Review Prompt ---\n")
    print(prompt)
    print("\n--- 将以上 Prompt 发送给 AI 审查 Agent 获取结果 ---\n")


def cmd_pre_commit_hook():
    """生成 pre-commit hook 配置"""
    hook_script = '''#!/bin/bash
# Pre-Commit Spec 合规性检查 Hook
# 在提交前检查代码是否符合 spec.md 规范

echo "🔍 正在检查 Spec 合规性..."

# 获取 staged 变更
python3 tools/spec-tools/spec_compliance_check.py --staged --structured

# 检查退出码
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Spec 合规性检查发现违规，提交被阻止。"
    echo "   请修正违规项后重试，或使用 git commit --no-verify 跳过检查。"
    exit 1
fi

echo "✅ Spec 合规性检查通过"
'''

    ci_config = '''# .github/workflows/spec-compliance.yml
name: Spec Compliance Check

on:
  pull_request:
    branches: [main, develop]

jobs:
  spec-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Run Spec Compliance Check
        run: |
          git diff origin/${{ github.base_ref }}...HEAD > /tmp/pr.diff
          python3 tools/spec-tools/spec_compliance_check.py --diff /tmp/pr.diff --structured

      - name: Upload Report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: spec-compliance-report
          path: spec-compliance-report.json
'''

    print("\n📋 Pre-Commit Hook 和 CI 配置\n")

    hook_path = Path(".git/hooks/pre-commit")
    ci_path = Path(".github/workflows/spec-compliance.yml")

    print(f"### Pre-Commit Hook: {hook_path}")
    print("```bash")
    print(hook_script)
    print("```")

    print(f"\n### CI Workflow: {ci_path}")
    print("```yaml")
    print(ci_config)
    print("```")

    print("\n💡 提示: 将以上内容复制到对应的文件中即可启用自动检查。")


# ---- 辅助函数 ----

def _extract_rules_from_spec(spec_path: str) -> list:
    """从 spec.md 提取结构化规则（复用 spec_rule_extractor 的逻辑）"""
    content = Path(spec_path).read_text(encoding="utf-8")
    lines = content.split("\n")
    rules = []

    i = 0
    while i < len(lines):
        line = lines[i]
        verifiable_match = re.search(r'\[verifiable:(\w+)\]', line)
        rule_id_match = re.search(r'<!--\s*@rule\s+id=(\S+)\s+type=(\S+)(?:\s+severity=(\S+))?', line)

        if verifiable_match or rule_id_match:
            rule = {
                "verifiable_type": verifiable_match.group(1) if verifiable_match else None,
                "title": "",
                "checks": [],
                "patterns": [],
                "description": "",
                "severity": "warning",
            }

            if rule_id_match:
                rule["id"] = rule_id_match.group(1)
                rule["type"] = rule_id_match.group(2)
                if rule_id_match.group(3):
                    rule["severity"] = rule_id_match.group(3)

            # 查找标题
            header_match = re.match(r'^###\s+(.+)', line)
            if header_match:
                rule["title"] = header_match.group(1).strip()

            # 收集后续行的检查指令和模式
            j = i + 1
            while j < len(lines) and j < i + 20:
                check_match = re.search(r'<!--\s*@check:\s*(.+?)\s*-->', lines[j])
                if check_match:
                    rule["checks"].append(check_match.group(1))

                pattern_match = re.search(r'<!--\s*@pattern:\s*(.+?)\s*-->', lines[j])
                if pattern_match:
                    rule["patterns"].append(pattern_match.group(1))

                # 收集描述
                if lines[j].strip().startswith("**") and not rule["description"]:
                    rule["description"] = lines[j].strip()

                j += 1

            rules.append(rule)
            i = j
        else:
            i += 1

    return rules


def _output_check_results(findings: list, found_spec: bool):
    """输出审查结果"""
    print(f"\n{'=' * 60}")
    print(f"  Spec 合规性检查报告")
    print(f"  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 60}\n")

    has_spec_count = sum(1 for f in findings if f["has_spec"])
    no_spec_count = sum(1 for f in findings if not f["has_spec"])
    error_count = sum(1 for f in findings if not f.get("prompt_ready", True))

    print(f"📊 检查统计:")
    print(f"   有 spec.md 的文件: {has_spec_count}")
    print(f"   无 spec.md 的文件: {no_spec_count}")
    if error_count > 0:
        print(f"   解析错误: {error_count}")

    if no_spec_count > 0:
        print(f"\n⚠️  以下文件缺少 spec.md:")
        for f in findings:
            if not f["has_spec"]:
                print(f"   ❌ {f['file']}")

    if has_spec_count > 0:
        print(f"\n📋 AI 审查 Prompt 已生成:")
        for f in findings:
            if f.get("prompt_ready"):
                print(f"   ✅ {f['file']} → {f['spec']}")
                # 输出 prompt 到文件
                prompt_file = f"/tmp/spec-review-{Path(f['file']).name}.txt"
                Path(prompt_file).write_text(f["prompt"], encoding="utf-8")
                print(f"      Prompt 已保存至: {prompt_file}")

    print(f"\n💡 将生成的 Prompt 发送给 AI 审查 Agent (如 Claude/GPT) 获取审查结果。")
    print(f"   或将以下脚本集成到 pre-commit hook 中实现自动化审查。\n")

    # 输出 JSON 格式报告
    json_report = {
        "timestamp": datetime.now().isoformat(),
        "total_files": len(findings),
        "files_with_spec": has_spec_count,
        "files_without_spec": no_spec_count,
        "findings": [
            {
                "file": f["file"],
                "spec": f.get("spec"),
                "ready": f.get("prompt_ready", False),
            }
            for f in findings
        ],
    }
    report_path = "/tmp/spec-compliance-report.json"
    Path(report_path).write_text(json.dumps(json_report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"📄 JSON 报告已保存至: {report_path}")


# ---- 命令行入口 ----

def main():
    parser = argparse.ArgumentParser(
        description="Spec 合规性检查 Agent (AI 审查)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --staged                    检查 git staged 变更
  %(prog)s --staged --structured       使用结构化规则检查
  %(prog)s --changed-files file1.cs    检查指定文件
  %(prog)s --diff "$(cat /tmp/diff)"   检查 diff 文件内容
  %(prog)s --spec a.spec.md --code a.cs 单文件检查（生成 Prompt）
  %(prog)s --pre-commit-hook           生成 pre-commit hook 和 CI 配置
        """
    )
    parser.add_argument("--staged", action="store_true", help="检查 git staged 变更")
    parser.add_argument("--diff", help="diff 文本内容")
    parser.add_argument("--changed-files", help="逗号分隔的变更文件列表")
    parser.add_argument("--spec", help="spec.md 文件路径（单文件模式）")
    parser.add_argument("--code", help="代码文件路径（单文件模式）")
    parser.add_argument("--structured", action="store_true", help="使用结构化规则提取")
    parser.add_argument("--pre-commit-hook", action="store_true", help="生成 pre-commit hook 配置")

    args = parser.parse_args()

    if args.pre_commit_hook:
        cmd_pre_commit_hook()
    elif args.spec and args.code:
        cmd_check_single_file(args.spec, args.code)
    elif args.staged:
        cmd_check_staged(args.structured)
    elif args.diff:
        cmd_check_diff(args.diff, args.structured)
    elif args.changed_files:
        # 构建简化的 diff
        files = args.changed_files.split(",")
        diff_lines = []
        for f in files:
            try:
                content = Path(f).read_text(encoding="utf-8")
                lines_count = len(content.splitlines())
                diff_lines.append(f"--- a/{f}\n+++ b/{f}\n@@ -0,0 +1,{lines_count} @@")
                for line in content.splitlines():
                    diff_lines.append(f"+{line}")
            except Exception as e:
                print(f"⚠️  无法读取文件 {f}: {e}", file=sys.stderr)
        cmd_check_diff("\n".join(diff_lines), args.structured)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
