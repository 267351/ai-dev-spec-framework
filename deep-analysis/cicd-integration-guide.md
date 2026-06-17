# Spec 合规性 CI/CD 集成指南

> 将 spec.md 自动验证集成到 CI/CD 流水线中，建立完整的编译时→提交时→合并门禁检查链。

---

## 一、三层检查架构

```
┌──────────────────────────────────────────────────────────┐
│                    编译时 (Build Time)                     │
│  Roslyn Analyzer: 依赖方向|命名规范|DI 注入              │
│  → dotnet build 失败 = 编译错误，阻止本地构建              │
├──────────────────────────────────────────────────────────┤
│                    提交时 (Pre-Commit)                     │
│  AI 审查 Agent: 业务逻辑|语义规则                         │
│  → Pre-Commit Hook 拒绝 = 提交被阻止                      │
├──────────────────────────────────────────────────────────┤
│                    合并时 (CI Gate)                        │
│  CI Pipeline: 全量 spec 覆盖度 + 合规性报告               │
│  → PR Check 失败 = 合并被阻止                             │
└──────────────────────────────────────────────────────────┘
```

---

## 二、步骤 1: 集成 Roslyn Analyzer（编译时检查）

### 2.1 添加 Analyzer 到项目

在每个 `.csproj` 文件中添加：

```xml
<ItemGroup>
  <ProjectReference Include="..\..\tools\SpecComplianceAnalyzer\SpecComplianceAnalyzer\SpecComplianceAnalyzer.csproj"
                    PrivateAssets="all"
                    ReferenceOutputAssembly="false"
                    OutputItemType="Analyzer" />
</ItemGroup>
```

### 2.2 配置规则级别（.editorconfig）

在项目根目录创建 `.editorconfig`：

```ini
[*.cs]
# SPEC001: 依赖方向检查
dotnet_diagnostic.SPEC001.severity = error

# SPEC002: 异步命名检查
dotnet_diagnostic.SPEC002.severity = warning

# SPEC003: DI 注入检查
dotnet_diagnostic.SPEC003.severity = error

# SPEC004: HttpClient 检查
dotnet_diagnostic.SPEC004.severity = error
```

### 2.3 验证

```bash
# 构建时自动运行
dotnet build

# 预期输出（如果违规）:
# error SPEC001: 分层架构违规: 项目 'Warehouse.Web' (Web 层) 引用了 'Warehouse.Infrastructure' (Infrastructure 层)
```

---

## 三、步骤 2: 配置 Pre-Commit Hook（提交时检查）

### 3.1 创建 Hook 脚本

在 `.git/hooks/pre-commit`（或使用 husky 等工具管理）：

```bash
#!/bin/bash
# Pre-Commit Spec 合规性检查

echo "🔍 Spec Compliance Check..."

# 运行 AI 审查 Agent
python3 tools/spec-tools/spec_compliance_check.py --staged --structured

exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo ""
    echo "❌ Spec 合规性检查未通过。提交被阻止。"
    echo "   可运行: python3 tools/spec-tools/spec_compliance_check.py --staged 查看详情"
    exit 1
fi

echo "✅ Spec 合规性检查通过"
```

### 3.2 安装

```bash
chmod +x .git/hooks/pre-commit
```

### 3.3 跳过检查（紧急情况）

```bash
git commit --no-verify -m "hotfix: 紧急修复"
```

---

## 四、步骤 3: GitHub Actions CI Pipeline（合并门禁）

### 4.1 Workflow 文件

创建 `.github/workflows/spec-compliance.yml`：

```yaml
name: Spec Compliance

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main, develop]

jobs:
  # Job 1: 编译时检查（Roslyn Analyzer）
  build-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup .NET
        uses: actions/setup-dotnet@v4
        with:
          dotnet-version: '10.0.x'
      
      - name: Build with Analyzers
        run: dotnet build --no-restore -warnaserror
      
      - name: Collect Analyzer Results
        if: always()
        run: |
          dotnet build --no-restore > build.log 2>&1
          grep -E "SPEC\d+" build.log > analyzer-errors.txt || true
      
      - name: Upload Analyzer Results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: analyzer-results
          path: analyzer-errors.txt

  # Job 2: spec.md 覆盖度检查
  coverage-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Run Coverage Report
        run: |
          python3 tools/spec-tools/spec_md_manager_v2.py report
          python3 tools/spec-tools/spec_md_manager_v2.py review --stale-days 90
      
      - name: Check Coverage Threshold
        run: |
          # 确保覆盖度 >= 80%
          COVERAGE=$(python3 tools/spec-tools/spec_md_manager_v2.py report 2>&1 | grep "总覆盖率" | grep -oP '\d+\.\d+')
          echo "Spec 覆盖度: $COVERAGE%"
          if (( $(echo "$COVERAGE < 80" | bc -l) )); then
            echo "❌ Spec 覆盖度低于 80% 阈值"
            exit 1
          fi

  # Job 3: AI 审查 (可选，需要 AI API)
  ai-review:
    runs-on: ubuntu-latest
    if: false  # 默认禁用，配置 AI API 后启用
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Generate Review Prompts
        run: |
          git diff origin/${{ github.base_ref }}...HEAD > /tmp/pr.diff
          python3 tools/spec-tools/spec_compliance_check.py --diff /tmp/pr.diff --structured
      
      - name: Run AI Review
        env:
          AI_API_KEY: ${{ secrets.AI_API_KEY }}
        run: |
          # 将 Prompt 发送到 AI API 并获取结果
          # 实现取决于具体的 AI 服务
          echo "AI review configured"
      
      - name: Upload Review Report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: ai-review-report
          path: /tmp/spec-compliance-report.json
```

### 4.2 GitLab CI 替代方案

```yaml
# .gitlab-ci.yml
spec-compliance:
  stage: test
  script:
    - python3 tools/spec-tools/spec_md_manager_v2.py report
    - python3 tools/spec-tools/spec_md_manager_v2.py review --stale-days 90
    - python3 tools/spec-tools/spec_rule_extractor.py --dir src --summary
  artifacts:
    reports:
      junit: spec-report.xml
```

---

## 五、步骤 4: 合并门禁规则

### 5.1 PR Check 要求

在 GitHub/GitLab 配置以下必过项：

| 检查项 | 工具 | 阈值 |
|--------|------|------|
| Build | dotnet build | 全部通过（含 Analyzer 错误） |
| Spec 覆盖度 | spec_md_manager_v2.py | >= 80% |
| 过期规则 | spec_md_manager_v2.py review | 0 条超 90 天未审 |
| AI 审查 (可选) | spec_compliance_check.py | 0 条 error |

### 5.2 分支保护规则

在 GitHub Settings > Branches > Branch protection 中：
- Require status checks to pass before merging
- 勾选 `build-check`、`coverage-check`、`ai-review`
- Require branches to be up to date before merging

---

## 六、步骤 5: 月度审计任务

创建 GitHub Actions 定时任务：

```yaml
# .github/workflows/spec-monthly-audit.yml
name: Monthly Spec Audit

on:
  schedule:
    - cron: '0 0 1 * *'  # 每月1号执行

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Generate Audit Report
        run: |
          python3 tools/spec-tools/spec_md_manager_v2.py review --stale-days 30 --show-sunsets > audit-monthly.md
          python3 tools/spec-tools/spec_md_manager_v2.py report >> audit-monthly.md
      
      - name: Create Issue
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('audit-monthly.md', 'utf8');
            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: `📋 Spec 月度审计报告 - ${new Date().toISOString().slice(0, 7)}`,
              body: report,
              labels: ['spec', 'audit', 'automated']
            });
```

---

## 七、IDE 集成（可选增强）

### 7.1 VS Code Tasks

`.vscode/tasks.json`:
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "检查 Spec 合规性",
      "type": "shell",
      "command": "python3 tools/spec-tools/spec_compliance_check.py --staged",
      "group": "test",
      "presentation": {"reveal": "always"}
    },
    {
      "label": "生成 Spec 覆盖度报告",
      "type": "shell",
      "command": "python3 tools/spec-tools/spec_md_manager_v2.py report",
      "group": "test"
    }
  ]
}
```

### 7.2 Rider/Visual Studio 外部工具

在 IDE 中配置外部工具快捷方式：
- Tool: `python3`
- Arguments: `tools/spec-tools/spec_compliance_check.py --staged`
- Working directory: `$ProjectFileDir$`

---

## 八、故障排除

| 问题 | 解决方案 |
|------|---------|
| Analyzer 不生效 | 检查 `.csproj` 中的 `<ProjectReference>` 配置 |
| Pre-commit 卡住 | 检查 Python3 环境，手动运行 `python3 tools/spec-tools/spec_compliance_check.py --staged` |
| CI 中的 Python 找不到 | 确保 CI 安装了 Python 3.11+ |
| 覆盖度总是低于阈值 | 运行 `python3 tools/spec-tools/spec_md_manager_v2.py create` 批量补全 |
| AI 审查误报过多 | 调整 `spec_compliance_check.py` 中的 Prompt 模板 |

---

**指南版本**: v1.0
**制定日期**: 2026-06-18
