# AI Dev Spec Framework

> 从两个真实工业项目中提取可复用的 AI 辅助开发规范体系，产出工具链与学术论文。

---

## 项目目标

1. **分析**两个真实项目（CSO-FORCS、WarehouseMS）的开发模式
2. **提取**可复用的规范体系（spec.md 约定 + 配套工具链）
3. **产出**一套 AI 可执行的规范工具集和一篇学术论文

---

## 方法论：四阶段流水线

```
数据收集 → 模式提取 → 体系化 → 论文撰写
```

| 阶段 | 目录 | 产出 |
|------|------|------|
| 1. 数据收集 | `data-collection/` | 项目报告、Skills 清单、横向对比 |
| 2. 模式提取 | `pattern-extraction/` | 共同模式、差异模式、工作流总结 |
| 3. 体系化 | `spec-system/` | 规范清单、结构化文档、验证标准 |
| 4. 论文撰写 | `paper/` | 完整论文（6 章） |

---

## 核心产出：spec-tools 工具集

位于 `skills/tools/spec-tools/`，是一套管理 `.spec.md` 文件生命周期的完整工具链：

| 工具 | 用途 |
|------|------|
| `deploy.sh` | 新项目一键部署 |
| `spec_deploy_init.py` | 智能分析项目结构，自动生成架构总纲 |
| `spec_md_manager_v2.py` | 日常管理：扫描/创建/审计/可信度标注/清理 |
| `spec_rule_extractor.py` | 从 spec.md 提取可验证规则 |
| `spec_compliance_check.py` | 检查代码变更是否符合 spec 约束 |
| `spec_impact_analyzer.py` | 修改规则前分析影响范围 |
| `spec_review_reminder.py` | 找出过期未审规则 |
| `SpecComplianceAnalyzer/` | Roslyn 编译时检查器（C#） |

详细用法见 `skills/tools/spec-tools/README.md`。

---

## 目录结构

```
ai-dev-spec-framework/
├── AGENTS.md                  # AI 助手工作指南
├── plans/                     # 各阶段执行计划
├── data-collection/           # 阶段1：数据收集
├── pattern-extraction/        # 阶段2：模式提取
├── spec-system/               # 阶段3：规范体系
├── paper/                     # 阶段4：论文
│   ├── chapters/              #   论文 v1
│   ├── chapters-v2/           #   论文 v2（重构中）
│   └── INDEX.md               #   章节索引
├── deep-analysis/             # 深度分析文档
├── skills/tools/spec-tools/   # spec.md 工具集（可复用）
└── .gitignore
```

---

## 快速使用 spec-tools

```bash
# 在新项目中部署整套体系
cd skills/tools/spec-tools/
./deploy.sh /path/to/new-project

# 部署后打开架构总纲，确认规则
vim /path/to/new-project/架构总纲.spec.md
```

---

## 关键设计理念

- **spec.md 是约束不是文档** — 记录对 AI 有约束力的架构决策和踩过的坑，不是代码注释
- **空壳有害** — Entity/DTO/Enum 的 spec.md 稀释信任，工具自动跳过
- **可信度五级制** — validated → proven → consensus → preventive → speculative
- **自动验证优先** — 规则标注可验证格式，Roslyn Analyzer + CI Agent 构成闭环

---

## 源项目

| 项目 | 技术栈 | 说明 |
|------|--------|------|
| CSO-FORCS | C# 13, .NET 10, Blazor SSR+WASM, EF Core 10, SignalR | 工业安全管理系统，双子系统架构 |
| WarehouseMS | C# 13, .NET 10, Blazor, MudBlazor 8.x, EF Core 10 | 工业研磨物资管理系统 |

源项目位于 `../CSO-FORCS` 和 `../WarehouseMS`，本仓库仅读取不修改。
