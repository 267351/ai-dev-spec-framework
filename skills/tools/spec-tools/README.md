# spec-tools：spec.md 体系工具集

> `.spec.md` 是 AI 辅助开发中的"持久化记忆文件"——记录架构约束、踩过的坑、技术规范。
> 本工具集管理 spec.md 的完整生命周期：创建 → 标注 → 验证 → 审计 → 清理。

---

## 快速开始（新项目）

```bash
./deploy.sh /path/to/新项目
```

部署后打开 `架构总纲.spec.md`，搜索 `✅保留` 逐条确认/修改/删除推理出的规则，回答发散性问题即可。

---

## 核心概念

### 什么文件需要 spec.md

| 需要 | 不需要 |
|------|--------|
| Service / Controller / Repository | Entity / DTO / Enum |
| 复杂 Component (.razor) | 纯 POCO 类 |
| 有业务逻辑的 Manager / Handler | 配置文件 / 常量类 |

**原则**：文件有"设计决策"或"踩过坑"才建 spec.md。`scan --smart` 会自动跳过纯数据文件。

### 可信度：规则的信源质量

| 星级 | 标注 | 含义 |
|------|------|------|
| ⭐⭐⭐⭐⭐ | `validated` | 生产事故验证过 |
| ⭐⭐⭐⭐ | `proven` | 多项目持续有效 |
| ⭐⭐⭐ | `consensus` | 团队共识 |
| ⭐⭐ | `preventive` | 预防性质，没实际触发过 |
| ⭐ | `speculative` | 个人偏好，鼓励质疑 |

---

## 工具速查

| 工具 | 用途 | 场景 |
|------|------|------|
| `deploy.sh` | 一键部署整套体系 | 新项目初始化 |
| `spec_deploy_init.py` | 分析项目结构 → 生成架构总纲 | 部署时自动调用 |
| `spec_md_manager_v2.py` | 生命周期管理（主工具） | 日常：扫描/创建/审计/标注/清理 |
| `spec_rule_extractor.py` | 提取可验证规则 → JSON | CI 集成 / 规则盘点 |
| `spec_compliance_check.py` | 检查代码是否符合 spec | 提交前审查 / CI 门禁 |
| `SpecComplianceAnalyzer/` | Roslyn 编译时检查 | `dotnet build` 自动拦截 |
| `spec_impact_analyzer.py` | 改规则前分析影响范围 | 规则变更决策支持 |
| `spec_review_reminder.py` | 找出过期未审规则 | 月度/季度维护 |

---

## 主工具：spec_md_manager_v2.py

最常用的工具，所有日常操作都通过它。

### 扫描与创建

```bash
python3 tools/spec-tools/spec_md_manager_v2.py scan              # 全量扫描
python3 tools/spec-tools/spec_md_manager_v2.py scan --smart      # 跳过 Entity/DTO/Enum
python3 tools/spec-tools/spec_md_manager_v2.py create            # 批量创建
python3 tools/spec-tools/spec_md_manager_v2.py create --smart    # 只为有逻辑的文件创建
```

### 覆盖度与质量

```bash
python3 tools/spec-tools/spec_md_manager_v2.py report             # 传统覆盖度（数量）
python3 tools/spec-tools/spec_md_manager_v2.py report --density   # 信息密度（质量分 + 空壳比例）
```

`--density` 模式区分空壳和有内容的文件，用有意义覆盖率取代原始覆盖率指标。

### 增强模板（可信度 + 审计追踪）

```bash
python3 tools/spec-tools/spec_md_manager_v2.py init <spec-file>   # 追加审计/质疑/Sunset 章节
```

### 可信度标注

```bash
python3 tools/spec-tools/spec_md_manager_v2.py confidence <file> --rule "分层架构红线" --level validated
python3 tools/spec-tools/spec_md_manager_v2.py confidence <file> --rule "异步方法命名" --level consensus
python3 tools/spec-tools/spec_md_manager_v2.py list-rules <file>   # 查看所有规则及其状态
```

### 审计追踪

```bash
python3 tools/spec-tools/spec_md_manager_v2.py audit <file> --action modify --operator @user --reason "修改分层规则" --files 5
python3 tools/spec-tools/spec_md_manager_v2.py audit <file> --action validate --operator @user --reason "季度审查通过"
```

### Sunset（自动过期）

```bash
python3 tools/spec-tools/spec_md_manager_v2.py sunset <file> --rule "异步模式" --date 2026-12-31
python3 tools/spec-tools/spec_md_manager_v2.py review --stale-days 90    # 列出过期未审规则
```

### 质疑

```bash
python3 tools/spec-tools/spec_md_manager_v2.py challenge <file> --rule "禁止style" --challenger @user --reason "MudBlazor 需要内联覆盖" --suggestion "限制10行内"
```

### 清理空壳

```bash
python3 tools/spec-tools/spec_md_manager_v2.py clean --dry-run    # 预览将删除的空壳
python3 tools/spec-tools/spec_md_manager_v2.py clean              # 确认删除
```

删除纯数据类（Entity/DTO/Enum）的空壳 spec.md，释放认知负载。

---

## 辅助工具

### spec_rule_extractor.py

```bash
python3 tools/spec-tools/spec_rule_extractor.py 架构总纲.spec.md
python3 tools/spec-tools/spec_rule_extractor.py --dir src --summary    # 规则覆盖度摘要
python3 tools/spec-tools/spec_rule_extractor.py --dir src --output json
```

输出每条规则的 ID、类型（di/naming/pattern/semantic）、可信度、Severity、Sunset 状态。

### spec_compliance_check.py

```bash
python3 tools/spec-tools/spec_compliance_check.py --staged                    # git staged 变更
python3 tools/spec-tools/spec_compliance_check.py --staged --structured       # 结构化规则检查
python3 tools/spec-tools/spec_compliance_check.py --spec a.spec.md --code a.cs
python3 tools/spec-tools/spec_compliance_check.py --pre-commit-hook           # 生成 hook 配置
```

生成的 Prompt 发送给 AI 审查 Agent 即可获得合规性判断。

### spec_impact_analyzer.py

```bash
python3 tools/spec-tools/spec_impact_analyzer.py --spec 架构总纲.spec.md --rule "分层架构红线"
```

输出：依赖此规则的代码文件数、引用此规则的其他 spec.md、风险等级、建议修改步骤。

### spec_review_reminder.py

```bash
python3 tools/spec-tools/spec_review_reminder.py                                       # 90 天阈值
python3 tools/spec-tools/spec_review_reminder.py --stale-days 30 --by-confidence       # 低可信度优先
python3 tools/spec-tools/spec_review_reminder.py --show-sunsets --output report.md     # 含 Sunset 检查
```

### SpecComplianceAnalyzer/

C# Roslyn Analyzer。在目标 csproj 中添加引用后编译时自动生效：

```xml
<ProjectReference Include="../../tools/spec-tools/SpecComplianceAnalyzer/SpecComplianceAnalyzer.csproj"
                  PrivateAssets="all" ReferenceOutputAssembly="false" OutputItemType="Analyzer" />
```

| 规则 ID | 检查内容 | 严重度 |
|---------|---------|--------|
| SPEC001 | 分层依赖方向 | Error |
| SPEC002 | 异步方法 Async 后缀 | Warning |
| SPEC003 | 禁止 `new Service()` | Error |
| SPEC004 | 禁止 `new HttpClient()` | Error |

---

## 典型工作流

```
┌─ 新项目 ─────────────────────────────────────────────────────┐
│ deploy.sh → 编辑架构总纲 → [✅保留/⚠️修改/❌删除] → 开始开发  │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─ 日常开发 ───────────────────────────────────────────────────┐
│ AI 修改代码 → 自动读取 .spec.md → 修改后提示更新 .spec.md     │
│ 提交前：compliance_check --staged                            │
│ 编译时：Roslyn Analyzer 自动拦截违规                          │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─ 定期维护 ───────────────────────────────────────────────────┐
│ review_reminder → audit validate → 季度审查会议               │
│ report --density → clean（清理空壳）                          │
└──────────────────────────────────────────────────────────────┘
```

---

## 常见问题

**Q: 新项目要建多少 spec.md？**
A: 刚初始化时只建 `架构总纲.spec.md`。日常开发中 AI 会在修改代码时主动提议创建文件级 spec.md。不要 `create` 全量空壳。

**Q: Entity 类要不要 spec.md？**
A: 不要。纯数据类没有设计决策也没有坑点，建了是空壳。`scan --smart` 自动跳过。

**Q: 可信度谁来标？**
A: AI 创建新规则默认标 `speculative`。只有人类可以将它升级为 `validated`/`proven`（升级需要提供验证证据）。

**Q: 什么情况下质疑 spec 规则？**
A: 任何合理怀疑都可以质疑。质疑不需要"证明规则错误"，只需要提供具体理由和建议方案。

---

## 目录结构

```
spec-tools/
├── README.md
├── deploy.sh                      ← 一键部署入口
├── spec_deploy_init.py            ← 项目分析 + 架构总纲生成
├── spec_md_manager_v2.py          ← 生命周期管理（主工具）
├── spec_rule_extractor.py         ← 规则提取（供 CI 消费）
├── spec_compliance_check.py       ← AI 审查 Agent
├── spec_impact_analyzer.py        ← 变更影响分析
├── spec_review_reminder.py        ← 审查提醒
└── SpecComplianceAnalyzer/        ← Roslyn 编译时检查器
    ├── SpecComplianceAnalyzer.csproj
    ├── DependencyDirectionAnalyzer.cs
    ├── AsyncSuffixAnalyzer.cs
    └── DirectInstantiationAnalyzer.cs
```
