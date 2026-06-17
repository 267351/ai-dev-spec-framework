# Spec 季度审查流程

> 每季度对 spec.md 体系进行系统审查，防止规则腐化。

---

## 一、审查前准备（审查会议前 3 天）

### 1.1 数据收集

```bash
# 生成审查清单
python3 tools/spec-tools/spec_review_reminder.py --stale-days 90 --by-confidence --show-sunsets --output /tmp/spec-review-$(date +%Y%m).md

# 生成覆盖度报告
python3 tools/spec-tools/spec_md_manager_v2.py report

# 生成规则摘要
python3 tools/spec-tools/spec_rule_extractor.py --dir src --summary
```

### 1.2 整理审查材料

- 上次审查以来的所有审计追踪变更
- 新增的 spec.md 文件列表
- 被质疑但未解决的规则
- Sunset 即将到期的规则

---

## 二、审查会议议程（60 分钟）

### 2.1 指标回顾（10 分钟）

| 检查项 | 来源 | 目标 |
|--------|------|------|
| spec.md 覆盖度 | spec_md_manager_v2.py report | >= 80% |
| 过期规则数 | spec_review_reminder.py | 0 |
| 空壳 spec.md 比例 | 人工检查 | < 20% |
| Sunset 过期数 | spec_review_reminder.py --show-sunsets | 0 |

### 2.2 逐条审查（30 分钟）

按以下优先级审查过期规则：

1. **speculative 级别规则**（最多质疑）— 是否有足够证据升级？
2. **Sunset 已过期规则** — 保持/降级/升级/删除？
3. **preventive 级别规则** — 是否触发过？证据如何？
4. **consensus 级别规则** — 团队共识是否仍然一致？

### 2.3 体系健康检查（15 分钟）

- [ ] AGENTS.md 是否符合 ≤100 行原则？
- [ ] 是否有新的架构级坑点需要记录到架构总纲？
- [ ] spec.md 命名是否一致？有无重复？
- [ ] 工具（spec_md_manager_v2.py）功能是否满足需求？

### 2.4 行动项分配（5 分钟）

- 分配 spec.md 更新责任人
- 设定完成期限
- 记录到审计追踪

---

## 三、审查后操作

### 3.1 更新审计追踪

每条审查过的规则，使用工具记录：

```bash
python3 tools/spec-tools/spec_md_manager_v2.py audit <spec-file> \
  --action validate \
  --operator "@审查者" \
  --reason "季度审查通过，规则仍然有效" \
  --files 0
```

### 3.2 处理 Sunset 过期规则

```bash
# 延长 Sunset
python3 tools/spec-tools/spec_md_manager_v2.py sunset <spec-file> \
  --rule "规则名" --date 2027-03-01

# 升级可信度
python3 tools/spec-tools/spec_md_manager_v2.py confidence <spec-file> \
  --rule "规则名" --level consensus
```

### 3.3 处理质疑记录

- 更新质疑决议（✅ 采纳 / ❌ 驳回 / 🔄 修改）
- 根据决议更新对应规则
- 更新审计追踪

---

## 四、审查清单模板

```markdown
# Q{季度} 2026 Spec 体系审查报告

## 一、指标

| 指标 | 当前值 | 目标 | 状态 |
|------|--------|------|------|
| spec.md 覆盖度 | {X}% | >= 80% | ✅/⚠️/❌ |
| 过期规则数 | {N} | 0 | ✅/⚠️ |
| 空壳比例 | {X}% | < 20% | ✅/⚠️ |
| Sunset 过期 | {N} | 0 | ✅/⚠️ |

## 二、逐条审查结果

| 规则 | 可信度 | 审查结果 | 行动 |
|------|--------|---------|------|
| ... | ... | 保持/升级/降级/删除 | ... |

## 三、质疑处理

| 质疑编号 | 状态 | 决议 |
|---------|------|------|
| ... | ✅ 已处理 / ⏳ 待处理 | ... |

## 四、行动项

| 行动 | 责任人 | 期限 |
|------|--------|------|
| ... | @user | YYYY-MM-DD |
```

---

## 五、审查频率建议

| 阶段 | 频率 | 重点 |
|------|------|------|
| 项目初期（前 3 个月） | 每 2 周 | spec.md 创建频率高，需频繁校准 |
| 稳定期（3-12 个月） | 每月 | 关注空壳比例和过期规则 |
| 维护期（> 12 个月） | 每季度 | 关注体系完整性和 Sunset 过期 |

---

**文档版本**: v1.0
**制定日期**: 2026-06-18
