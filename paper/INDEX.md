# 论文版本索引

> 多版本并存，互相借鉴，最终融合为最优论文。

---

## 版本一览

| 版本 | 文件 | 定位 | 状态 | 核心贡献 |
|------|------|------|------|----------|
| **v1** | `paper/final-v1.md` | 第一版：成功报告型 | ✅ 完成（不再修改） | 规范提取方法论、三层体系架构 |
| **v2** | `paper/final-v2.md` | 第二版：问题驱动型 | 🔴 进行中 | 失败模式分析、7个弊端、2个根本缺陷 |
| **v3** | `paper/final-v3.md` | 第三版：模型感知型 | ⬜ 规划中 | LLM 模型差异分析、混合流水线、元 Skills |

---

## v1 → v2 → v3 的演化逻辑

```
v1 (成功报告)
  "我们建立了一套规范体系，它有83.3%的完整性"
  定位：描述性 → 说了"做了什么"

v2 (问题驱动)                    ← 当前正在写
  "这个体系有7个弊端和2个根本性缺陷，需要6项改进"
  定位：批判性 → 说了"出了什么问题，为什么，怎么办"

v3 (模型感知)                    ← 未来方向
  "体系的效果取决于使用的LLM模型，弱模型需要不同的设计策略"
  定位：条件性 → 说了"在不同的条件下，体系需要不同的形态"
```

### v1 的价值（不应丢弃的部分）

- ✅ 完整的问题背景和文献综述（第1-2章）
- ✅ 45个规范的分类体系（附录A）
- ✅ 规范组合建议（附录C）
- ⚠️ 第4章太薄（需用 v2 的第4章替换）
- ⚠️ 第5章是假评估（需用 v2 的第5章和实际数据替换）

### v2 的核心创新（已写部分）

- ✅ 第4章：创立/更新/正效应/7个弊端/跨项目对比（5000字）
- ✅ 第5章：验证闭环缺失 + 错误约定毒性 + 6项解决方案（4500字）
- ⬜ 第1-3章、第6-7章待重写

### v3 的未来方向（素材已准备）

- ✅ `deep-analysis/llm-model-impact-analysis.md` — LLM 模型差异分析
- ✅ `deep-analysis/methodology-review.md` — 元 Skills 框架
- ⬜ 需要整合为论文章节

---

## 章节对应关系（v1 vs v2 vs v3）

| 章节 | v1 文件名 | v2 文件名 | v3 计划 |
|------|-----------|-----------|---------|
| 引言 | `chapters/01-introduction.md` | 待重写 | 加入模型感知的问题定义 |
| 相关工作 | `chapters/02-related-work.md` | 待重写 | 加入 LLM 能力评估文献 |
| 方法论 | `chapters/03-methodology.md` | 待重写 | 加入混合流水线设计 |
| 深度剖析 | ❌ 无 | `chapters-v2/04-deep-analysis.md` ✅ | 加入模型感知约束设计 |
| 根本缺陷 | ❌ 无 | `chapters-v2/05-fundamental-defects.md` ✅ | 加入模型能力对缺陷的放大效应 |
| 改进方案 | ❌ 无 | 待写 | 加入模型降级策略 |
| 结论 | `chapters/06-conclusion.md` | 待重写 | 加入多模型协同的未来方向 |

---

## 深度分析文件（论文素材）

| 文件 | 内容 | 可贡献给哪个版本 |
|------|------|-----------------|
| `deep-analysis/spec-md-system-analysis.md` | .spec.md 全维度分析 | → v2 第4章 ✅ 已用 |
| `deep-analysis/two-problems-solution-plan.md` | 两个缺陷+方案 | → v2 第5章 ✅ 已用 |
| `deep-analysis/methodology-review.md` | 方法论批判+元 Skills | → v2 第3章 / v3 |
| `deep-analysis/llm-model-impact-analysis.md` | LLM 模型差异分析 | → v3 |
| `deep-analysis/paper-rewrite-plan.md` | 重写计划 | 元信息 |
| `deep-analysis/tomorrow-todo.md` | 执行清单 | 元信息 |

---

## 文件命名规则

```
paper/
├── final-v1.md              ← 第一版（不再修改）
├── final-v2.md              ← 第二版（整合中）
├── final-v3.md              ← 第三版（未来）
├── chapters/                ← v1 的原始分章节文件
│   ├── 01-introduction.md
│   └── ...
└── chapters-v2/             ← v2 的新分章节文件
    ├── 04-deep-analysis.md
    └── 05-fundamental-defects.md
```

**规则**：
- `final-vN.md` — 完整论文，N 递增，不覆盖
- `chapters-vN/` — 第 N 版的分章节文件
- `deep-analysis/` — 深度分析文件，不是论文，是论文的素材

---

**索引更新时间**: 2026-06-17
