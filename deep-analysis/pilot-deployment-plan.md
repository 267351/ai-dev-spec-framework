# Phase 4: 试点与推广计划

> 在 CSO-FORCS 和 WarehouseMS 两个项目中试点增强版 spec.md 体系，
> 收集反馈，迭代优化，最终推广。

---

## 一、试点策略

### 1.1 试点范围

| 阶段 | 范围 | 内容 | 时间 |
|------|------|------|------|
| **Alpha** | 单个 spec.md 文件 | 在架构总纲.spec.md 上试用可信度标注 | 第 1-2 天 |
| **Beta** | 5-10 个 spec.md | 扩展试点范围，试用审计追踪和质疑机制 | 第 3-7 天 |
| **RC** | 全量 spec.md | 全量迁移，启用自动验证闭环 | 第 2-4 周 |

### 1.2 选择试点项目

**首选 CSO-FORCS**：
- 原因：已有 spec.md 体系元文档（AGENTS.md.spec.md，531行）和偏差检测机制
- 优势：团队对 spec.md 体系理解最深，反馈质量最高

**第二站 WarehouseMS**：
- 原因：架构总纲.spec.md 最完整（242行，涵盖架构/业务/配置/数据）
- 优势：规则分类清晰，适合测试可信度分级和 Sunset 机制

---

## 二、Alpha 试点（架构总纲.spec.md）

### 2.1 操作步骤

```bash
# Step 1: 为架构总纲添加增强字段
python3 tools/spec-tools/spec_md_manager_v2.py init 架构总纲.spec.md

# Step 2: 为各类规则设置可信度
python3 tools/spec-tools/spec_md_manager_v2.py confidence 架构总纲.spec.md --rule "分层架构红线" --level validated
python3 tools/spec-tools/spec_md_manager_v2.py confidence 架构总纲.spec.md --rule "配置管理红线" --level proven
python3 tools/spec-tools/spec_md_manager_v2.py confidence 架构总纲.spec.md --rule "业务规则红线" --level validated
python3 tools/spec-tools/spec_md_manager_v2.py confidence 架构总纲.spec.md --rule "Blazor组件规范" --level consensus
python3 tools/spec-tools/spec_md_manager_v2.py confidence 架构总纲.spec.md --rule "异步模式" --level preventive
# ... 其他规则

# Step 3: 为 preventive/speculative 规则设置 Sunset
python3 tools/spec-tools/spec_md_manager_v2.py sunset 架构总纲.spec.md --rule "异步模式" --date 2026-09-18
python3 tools/spec-tools/spec_md_manager_v2.py sunset 架构总纲.spec.md --rule "错误处理规范" --date 2026-09-18

# Step 4: 记录试点操作到审计追踪
python3 tools/spec-tools/spec_md_manager_v2.py audit 架构总纲.spec.md --action modify --operator "@试点者" --reason "Alpha 试点：添加可信度分级和 Sunset 机制" --files 1

# Step 5: 验证格式可读性
python3 tools/spec-tools/spec_md_manager_v2.py list-rules 架构总纲.spec.md
```

### 2.2 验证检查项

- [ ] 可信度标注正确展示了每个规则的星级
- [ ] 审计追踪表格格式正确，与 Markdown 渲染器兼容
- [ ] Sunset 标注位置合理，不影响规则可读性
- [ ] 质疑记录章节就绪，可随时添加质疑
- [ ] 团队对可信度等级的理解一致

---

## 三、Beta 试点（5-10 个高频 spec.md）

### 3.1 选择试点文件

优先选择以下类型的 spec.md：
1. **高频修改文件**：WorkloadService.spec.md、MaterialCategoryService.spec.md
2. **复杂业务文件**：StockOut 相关、Inventory 相关
3. **新创建文件**：最近 1 周内创建的 spec.md（测试从零开始用增强模板）
4. **空壳文件**：Entity 类的 spec.md（测试是否有必要）

### 3.2 试点任务

| 任务 | 工具 | 预期结果 |
|------|------|---------|
| 批量 init | spec_md_manager_v2.py init | 所有选中文件增加审计追踪 |
| 设置可信度 | spec_md_manager_v2.py confidence | 每条规则有明确星级 |
| 设置 Sunset | spec_md_manager_v2.py sunset | preventive/speculative 有过期日 |
| 生成审查提醒 | spec_review_reminder.py --stale-days 30 | 列出需要审查的规则 |
| 模拟质疑 | spec_md_manager_v2.py challenge | 测试质疑提交流程 |
| 生成规则清单 | spec_md_manager_v2.py list-rules | 验证规则可追溯 |

---

## 四、试点反馈收集

### 4.1 定量指标

| 指标 | 测量方法 | 基线 | 目标 |
|------|---------|------|------|
| 可信度标注覆盖率 | 标注规则数 / 总规则数 | 0% | > 80% |
| 审计追踪使用率 | 有审计记录的 spec.md / 总 spec.md | 0% | > 90% |
| 质疑机制触发次数 | 质疑记录总数 | 0 | >= 5 |
| Sunset 过期处理率 | 已处理过期 / 总过期 | 0% | > 80% |
| 审查提醒处理率 | 已审查 / 提醒审查 | 0% | > 70% |

### 4.2 定性反馈

访谈团队成员：

1. **可信度分级**：分级标准是否清晰？是否帮助 you 判断哪些规则可以质疑？
2. **审计追踪**：操作是否方便？记录是否增加了维护负担？
3. **质疑机制**：是否感觉安全？是否真的降低了质疑摩擦？
4. **Sunset 机制**：是否提醒了该审查的规则？
5. **总体感受**：增强版 spec.md 是否比原版更有价值？额外维护成本是否值得？

---

## 五、迭代优化

### 5.1 基于反馈的可能调整

| 反馈 | 可能调整 |
|------|---------|
| "可信度分级标准不清晰" | 完善决策树，增加更多示例 |
| "审计追踪操作太繁琐" | 优化 spec_md_manager_v2.py 的 audit 命令 |
| "质疑记录格式太长" | 简化模板，只保留核心字段 |
| "Sunset 日期忘记设置" | 在 init/create 时自动计算 Sunset |
| "空壳 spec.md 也加了审计追踪" | 区分有内容和空壳文件的处理策略 |

### 5.2 工具迭代

```bash
# 根据反馈更新工具后，重新部署
git add tools/spec-tools/spec_md_manager_v2.py tools/spec-tools/spec_rule_extractor.py tools/spec-tools/spec_compliance_check.py
git add tools/spec-tools/spec_impact_analyzer.py tools/spec-tools/spec_review_reminder.py
git commit -m "spec: 根据试点反馈迭代工具 v0.2"
```

---

## 六、推广到 WarehouseMS

### 6.1 推广步骤

1. 汇总 CSO-FORCS 试点反馈报告
2. 根据反馈调整工具和流程
3. 在 WarehouseMS 架构总纲.spec.md 上执行类似试点
4. 对比两个项目的实施效果

### 6.2 推广检查清单

- [ ] 工具 v0.2 在 CSO-FORCS 通过验证
- [ ] 试点反馈报告完成
- [ ] 工具文档更新（README、使用指南）
- [ ] WarehouseMS 团队知晓增强版 spec.md 体系
- [ ] 架构总纲.spec.md 作为第一个试点文件

---

## 七、时间规划

| 阶段 | 任务 | 时间 | 负责人 |
|------|------|------|--------|
| Alpha | 架构总纲试点 | 1-2 天 | 技术负责人 |
| Beta | 5-10 个文件试点 | 3-5 天 | 开发团队 |
| 反馈 | 收集和分析 | 2 天 | 技术负责人 |
| 迭代 | 工具优化 | 2 天 | 工具开发者 |
| 推广 | WarehouseMS 试点 | 2-3 天 | 双方团队 |
| 总结 | 对比报告 | 1 天 | 技术负责人 |

**总计**: 约 2 周

---

**计划版本**: v1.0
**制定日期**: 2026-06-18
