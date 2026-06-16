# AGENTS.md - AI助手工作指南

## 项目目标

本工作区用于分析两个外部项目，构建**"可复用的AI辅助开发规范体系"**。最终产出是一份学术论文。

## 关键约束

### 源项目访问（只读）

```
/home/hys/projects/CSO-FORCS    # 项目1 - 只读
/home/hys/projects/WarehouseMS  # 项目2 - 只读
```

**禁止**对这两个目录进行写入、删除、重命名或任何修改操作。仅允许读取。

### 输出位置

所有产出物（总结、分析、论文）必须写入：
```
/home/hys/projects/ai-dev-spec-framework/
```

## 目录结构

```
/home/hys/projects/ai-dev-spec-framework/
├── AGENTS.md                    # 项目配置（本文件）
├── plans/                       # 执行计划
│   ├── 01-data-collection.md    # 数据收集计划
│   ├── 02-pattern-extraction.md # 模式提取计划
│   ├── 03-systematization.md    # 体系化计划
│   └── 04-paper-writing.md      # 论文撰写计划
├── data-collection/             # 阶段1：数据收集
│   ├── report.md                # 数据收集报告
│   ├── warehousems-skills.md    # WarehouseMS Skills清单
│   └── comparison-analysis.md   # 横向对比分析
├── pattern-extraction/          # 阶段2：模式提取
│   ├── common-patterns.md       # 共同模式
│   ├── difference-patterns.md   # 差异模式
│   └── workflow-summary.md      # 工作流程总结
├── spec-system/                 # 阶段3：规范体系
│   ├── initial-list.md          # 初步规范清单
│   ├── structure.md             # 规范体系结构
│   ├── structured.md            # 规范体系结构化文档
│   ├── template.md              # 规范模板
│   ├── index.md                 # 规范索引
│   ├── validation-report.md     # 规范验证报告
│   ├── verification-standards.md # 验证标准
│   └── final.md                 # 规范体系最终文档
└── paper/                       # 阶段4：论文
    ├── final.md                 # 完整论文
    └── chapters/                # 论文章节
        ├── 01-introduction.md   # 第1章 引言
        ├── 02-related-work.md   # 第2章 相关工作
        ├── 03-methodology.md    # 第3章 方法论
        ├── 04-implementation.md # 第4章 实现
        ├── 05-evaluation.md     # 第5章 评估
        └── 06-conclusion.md     # 第6章 结论
```

## 工作流程

线性阶段，不可跳过或乱序：

1. **数据收集** - 使用标准化模板分析两个项目 → `data-collection/`
2. **模式提取** - 识别共同的开发模式 → `pattern-extraction/`
3. **体系化** - 将模式组织为可复用的规范 → `spec-system/`
4. **论文撰写** - 基于规范体系撰写学术论文 → `paper/`

## 分析模板

详见 `pattern-extraction/workflow-summary.md` 中的7个标准化分析模板：
- 模板1：项目基本信息
- 模板2：架构分析
- 模板3：代码规范分析
- 模板4：工作流程分析
- 模板5：设计模式分析
- 模板6：可提取的Skills清单
- 模板7：横向对比分析

## 核心工作原则（最高优先级）

### 原则一：启用头脑风暴
**每一次执行任务时，都要进行特别认真的思考和详细查询，往死里查，查到全部到位。**

- 任务开始前，必须进行全面的信息收集和调研
- 使用多维度搜索：代码库分析、文档查阅、外部资料检索
- 不满足于表面信息，深入挖掘底层逻辑和设计意图
- 记录所有发现，确保不遗漏任何关键细节

### 原则二：制定详细计划与技术方案
**每一次执行任务时，都要制定详细的计划跟技术方案，确保 AI 在断开后重新连接时，任务能接得上，且意图保持不变。**

- 任务开始前，必须输出书面的执行计划
- 计划包含：目标、步骤、依赖、验收标准、风险点
- 每个步骤必须有明确的输入/输出定义
- 计划存档于工作目录，确保可追溯、可恢复

---

## 核心规则

1. **先分析两个项目**，再提取共同模式
2. **先验证再声明** - 每条规范都需要明确的验证标准
3. **AI可执行的规范** - 提取的skills必须是AI可验证的，而非模糊的原则
4. **区分红线和最佳实践** - 区分必须遵守 vs 建议遵守
