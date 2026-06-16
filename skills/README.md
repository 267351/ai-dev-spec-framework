# 可复用 Skills 库

从 CSO-FORCS 和 WarehouseMS 两个工业项目中提取的可复用 OpenCode Skills。

## Skills 列表

| Skill | 来源项目 | 类型 | 跨项目可复用 | 版本 |
|-------|---------|------|:-----------:|------|
| [hadian-design-system](hadian-design-system/SKILL.md) | WarehouseMS | UI 设计系统 (品牌+组件+视觉规范) | ✅ | v1.1 |

## Skill 目录规范

每个 Skill 遵循 OpenCode Skill 标准结构：

```
skill-name/
├── SKILL.md              # Skill 入口：触发条件、核心规则、加载流程
├── data/                 # 数据和规范文件
│   ├── *.css             # 可被项目直接引用的样式文件
│   └── MASTER.md         # 完整设计/技术规范
└── scripts/              # 自动化脚本（如有）
    └── *.sh / *.py
```

## 提取原则

从源项目中提取 Skill 时，遵循以下判断标准：
- **自包含**：Skill 内容能在不依赖源项目其他文件的情况下被理解和使用
- **跨项目价值**：规则或模式不是源项目特定的，可用于相同技术栈的其他项目
- **可版本化**：有明确的版本标识，支持独立演进和升级
- **AI 可执行**：规则是操作性的，AI 能据此生成或约束代码

## 待提取 Skill 候选

| 候选 | 来源 | 说明 |
|------|------|------|
| CSO-FORCS 架构成套约束 | CSO-FORCS | HAL 层设计、Configuration 统一配置、Blazor 组件规范 |
| 偏差检测机制 | CSO-FORCS | 硬偏差/软偏差/演进偏差三级分类 |
| spec.md 编写规范 | CSO-FORCS | AGENTS.md.spec.md 元规范（531行） |
| 三大子系统边界 | WarehouseMS | Service 禁止互调、跨系统数据聚合规则 |

---

**目录创建时间**: 2026-06-17
