# 明天执行清单

> 对应 `two-problems-solution-plan.md` 中的 Phase 1-4

---

## Phase 1: Spec 可信度与审计追踪（基础改造）🔴 最先做

### P1-1: 设计增强版 spec.md 模板
- [ ] 设计 `[confidence:validated|proven|consensus|preventive|speculative]` 标注格式
- [ ] 设计审计追踪表格格式（日期/操作/操作者/理由/影响文件数）
- [ ] 设计质疑记录格式（质疑者/日期/理由/决议/决议理由）
- [ ] 设计 Sunset 标注格式（`[sunset:YYYY-MM-DD]`）
- [ ] 生成增强版模板文件 `deep-analysis/enhanced-spec-template.md`

### P1-2: 改造 spec_md_manager.py
- [ ] 读取 CSO-FORCS/WarehouseMS 现有的 `tools/spec_md_manager.py`
- [ ] 新增 `init` 命令：为现有 spec.md 批量添加可信度标注和审计追踪（空表格）
- [ ] 新增 `audit` 命令：为单条规则记录变更
- [ ] 新增 `review` 命令：列出超过 N 天未审查的规则
- [ ] 新增 `challenge` 命令：在 spec.md 中添加质疑记录
- [ ] 更新 `SPEC_TEMPLATE` 为增强版模板
- [ ] 输出改造后的 `tools/spec_md_manager_v2.py`

### P1-3: 更新 AGENTS.md 中的 spec.md 规则
- [ ] 在 CSO-FORCS AGENTS.md 或 AGENTS.md.spec.md 中加入：
  - 可信度分级规则
  - 审计追踪记录规则
  - 质疑机制规则
  - Sunset 规则

### P1-4: 在 架构总纲.spec.md 上试点
- [ ] 读取 WarehouseMS 的 `架构总纲.spec.md`
- [ ] 为每条红线添加可信度标注
- [ ] 添加审计追踪表格
- [ ] 验证格式可读性

---

## Phase 2: 自动验证闭环（技术实现）

### P2-1: 设计可验证规则标注格式
- [ ] 定义 `[verifiable:di|naming|pattern|contextual|unverifiable]` 标注语法
- [ ] 定义 `<!-- @rule id= -->` 和 `<!-- @check: -->` HTML 注释标注语法
- [ ] 编写标注格式规范文档 `deep-analysis/verifiable-annotation-spec.md`

### P2-2: 开发 spec 规则解析器
- [ ] 实现从 spec.md 提取 `[verifiable:xxx]` 标注的解析逻辑
- [ ] 实现从 spec.md 提取 `<!-- @check: -->` 检查规则
- [ ] 生成结构化规则 JSON（rule_id, type, check_description, file_path）
- [ ] 输出工具脚本 `tools/spec_rule_extractor.py`

### P2-3: 开发 Roslyn Analyzer（编译时检查）
- [ ] 选择高价值的 3 条规则作为 MVP
  - 依赖方向检查（禁止 Web 引用 DAL）
  - 命名约定检查（异步方法 Async 后缀）
  - DI 注入检查（禁止在 razor 中 new Service）
- [ ] 创建 Roslyn Analyzer 项目模板
- [ ] 实现第一条规则（依赖方向检查）
- [ ] 测试：在故意违反的代码上运行

### P2-4: 开发 AI 审查 Agent（spec_compliance_check.py）
- [ ] 设计 Prompt 模板（system prompt + spec.md + code diff → 合规性判断）
- [ ] 实现代码 diff 提取（git diff --cached）
- [ ] 实现 spec.md 匹配（变更文件 → 对应 spec.md）
- [ ] 实现审查结果输出（JSON 格式：file, rule, verdict, explanation）
- [ ] 实现 Pre-Commit Hook 集成示例
- [ ] 输出工具脚本 `tools/spec_compliance_check.py`

### P2-5: 集成到 CI/CD
- [ ] 编写 CI 配置文件示例（GitHub Actions / GitLab CI）
- [ ] 设置：编译时 Roslyn Analyzer 检查 → 提交时 AI 审查 → 合并门禁
- [ ] 编写流程文档

---

## Phase 3: 影响分析与定期审查（运维工具）

### P3-1: 开发 spec_impact_analyzer.py
- [ ] 实现：输入 spec 规则 → 搜索所有依赖它的代码文件
- [ ] 实现：输入 spec 规则 → 搜索所有引用它的其他 spec.md
- [ ] 实现：风险评估算法（架构核心 / 业务逻辑 / 代码风格）
- [ ] 实现：修改步骤建议生成
- [ ] 输出工具脚本 `tools/spec_impact_analyzer.py`

### P3-2: 开发 spec_review_reminder.py
- [ ] 实现：扫描所有 spec.md，提取最后审查日期
- [ ] 实现：按 stale-days 过滤
- [ ] 实现：按可信度等级优先排序（speculative 先审）
- [ ] 输出工具脚本 `tools/spec_review_reminder.py`

### P3-3: 建立季度审查流程文档
- [ ] 编写审查清单模板
- [ ] 编写审查会议流程
- [ ] 编写审查报告模板

---

## Phase 4: 试点与推广

### P4-1: 在 CSO-FORCS 试点
- [ ] 部署增强版 spec_md_manager_v2.py
- [ ] 为关键 spec.md（架构级 + 高频使用）添加可信度标注
- [ ] 运行 spec_rule_extractor.py 提取可验证规则
- [ ] 运行 AI 审查 Agent 进行试点审查

### P4-2: 收集反馈
- [ ] 记录可信度分级的实际效果
- [ ] 记录审计追踪的使用频率
- [ ] 记录质疑机制的触发次数
- [ ] 记录 AI 审查 Agent 的误报率

### P4-3: 推广到 WarehouseMS
- [ ] 根据 CSO-FORCS 反馈调整工具
- [ ] 部署到 WarehouseMS
- [ ] 对比两个项目的实施效果

---

## 速览：今天即可做的最小可行动作（MVP）

| 优先级 | 任务 | 预计时间 | 产出物 |
|--------|------|----------|--------|
| 🔴 P0 | 设计增强版 spec.md 模板 | 30 min | `enhanced-spec-template.md` |
| 🔴 P0 | 为 架构总纲.spec.md 添加可信度标注 | 20 min | 改造后的 架构总纲.spec.md（副本） |
| 🟡 P1 | 设计可验证规则标注格式 | 20 min | `verifiable-annotation-spec.md` |
| 🟡 P1 | 开发 spec_rule_extractor.py | 1 h | 规则解析器 v0.1 |
| 🟢 P2 | 开发 spec_compliance_check.py (Prompt + 框架) | 1 h | AI 审查 Agent v0.1 |

---

**清单制定时间**: 2026-06-17
**状态**: 待执行
