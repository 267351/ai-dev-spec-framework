# AGENTS.md Spec.md 生命周期规则（补充）

> 本文档定义应添加到 AGENTS.md（或 AGENTS.md.spec.md）中的 spec.md 生命周期管理规则。
> 适用于 CSO-FORCS 和 WarehouseMS 两个项目。

---

## 一、可信度分级规则

### 规则：每条约束必须标注可信度等级

AI 在创建或修改 spec.md 时，必须为每条规则添加可信度标注。

**标注格式**：`[confidence:validated|proven|consensus|preventive|speculative]`

**等级选择决策树**：
```
这条规则是否有生产事故支撑？
├── 是 → [confidence:validated]  ⭐⭐⭐⭐⭐
└── 否 → 是否在多个项目中验证有效？
    ├── 是 → [confidence:proven]  ⭐⭐⭐⭐
    └── 否 → 是否团队共识？
        ├── 是 → [confidence:consensus]  ⭐⭐⭐
        └── 否 → 是否有明确的问题驱动？
            ├── 是 → [confidence:preventive]  ⭐⭐
            └── 否 → [confidence:speculative]  ⭐
```

**示例**：
```markdown
### 🚫 [confidence:validated] 分层架构红线
> **可信度**: ⭐⭐⭐⭐⭐ (由 3 次生产事故验证)
1. **禁止** Web 项目引用 Infrastructure 项目
```

**规则**：
- AI 创建新规则时默认标注 `[confidence:speculative]`
- 只有人类开发者可以将可信度升级为 `validated` 或 `proven`
- 可信度标注必须包含验证记录（对于 validated 级别）

---

## 二、审计追踪记录规则

### 规则：每次 spec.md 变更必须记录审计追踪

**审计追踪表格格式**：
```markdown
## 📋 审计追踪

| 日期 | 操作 | 操作者 | 理由 | 影响文件数 |
|------|------|--------|------|-----------|
```

**操作类型**：
| 操作 | 含义 | 何时使用 |
|------|------|---------|
| 创建 | 规则首次写入 | 新建规则 |
| 修改 | 规则内容变更 | 更改规则描述 |
| 强化 | 从"建议"升级为"禁止" | 置信度升级 |
| 放松 | 从"禁止"降级为"建议" | 置信度降级 |
| 验证 | 确认规则仍然有效 | 审查通过 |
| 质疑 | 有人提出质疑 | 质疑记录 |
| 废除 | 规则被删除 | 移除规则 |

**规则**：
- 每次修改 spec.md 必须在审计追踪中添加一条记录
- "理由"字段必须具体（禁止使用"优化"、"调整"等模糊描述）
- AI 修改时操作者为 `AI:<模型名>`，人类修改时操作者为 `@用户名`

---

## 三、质疑机制规则

### 规则：任何人可以安全地质疑任何 spec 规则

**质疑流程**：
```
发现 spec 规则可能有问题
  → 在 spec.md 底部 「💬 质疑记录」章节添加质疑
  → 团队讨论（异步，通过 issue/PR/群聊）
  → 决议：✅ 采纳 / ❌ 驳回 / 🔄 修改
  → 更新 spec.md 和审计追踪
```

**质疑记录格式**：
```markdown
### 质疑 #N（日期，质疑者）
**质疑的规则**：{规则描述}
**质疑理由**：{具体理由}
**建议方案**：{改进建议}
**决议**：✅ 已采纳 / ❌ 已驳回 / ⏳ 待决议
**理由**：{决议理由}
```

**安全保障**：
- 质疑不需要"证明规则错误"——只需"有合理怀疑"
- 质疑被驳回不丢人——驳回理由对后来者有参考价值
- 质疑记录不可删除——即使被驳回也保留

---

## 四、Sunset 过期规则

### 规则：低可信度规则必须设置 Sunset 日期

**格式**：`[sunset:YYYY-MM-DD]`

**默认有效期**：
| 可信度 | 有效期 | 过期后行为 |
|--------|--------|-----------|
| `validated` | 不过期 | 保持原样 |
| `proven` | 12个月 | 降级为 consensus，提醒审查 |
| `consensus` | 6个月 | 提醒审查 |
| `preventive` | 3个月 | 提醒审查，可能降级 |
| `speculative` | 1个月 | 提醒审查，可能删除 |

**规则**：
- `validated` 级别规则不需要 Sunset
- 其他级别规则创建时自动计算 Sunset 日期
- 到达 Sunset 日期后，规则不会自动删除，但会触发审查提醒
- 审查后可以：延长 Sunset / 修改内容 / 降级 / 升级 / 删除

---

## 五、AI 行为规则（应写入 AGENTS.md）

### 创建 spec.md 时
- 使用增强模板（含审计追踪、质疑记录、Sunset 记录）
- 不确定的规则标注 `[confidence:speculative]`
- 自动计算 Sunset 日期

### 读取 spec.md 时
- 优先关注 `[confidence:validated]` 和 `[confidence:proven]` 规则
- 对 `[confidence:speculative]` 规则可以合理质疑
- 检查 Sunset 是否过期

### 修改 spec.md 时
- 修改前记录当前状态到审计追踪
- 修改后添加新的审计追踪条目
- 如果修改涉及规则内容，询问是否需要调整可信度等级
- **禁止**静默删除或降级 `[confidence:validated]` 规则

### 发现规则可能有问题时
- 使用质疑记录而非直接修改
- 提供具体质疑理由和建议方案
- 不自行决定规则的存废

---

## 六、工具支持

使用 `spec_md_manager_v2.py` 管理增强字段：

```bash
# 为现有 spec.md 添加增强字段
python3 tools/spec-tools/spec_md_manager_v2.py init <spec-file>

# 记录变更
python3 tools/spec-tools/spec_md_manager_v2.py audit <spec-file> --action modify --operator @user --reason "..." 

# 设置可信度
python3 tools/spec-tools/spec_md_manager_v2.py confidence <spec-file> --rule "规则名" --level validated

# 设置 Sunset
python3 tools/spec-tools/spec_md_manager_v2.py sunset <spec-file> --rule "规则名" --date 2026-09-01

# 添加质疑
python3 tools/spec-tools/spec_md_manager_v2.py challenge <spec-file> --rule "..." --challenger @user --reason "..."

# 列出规则状态
python3 tools/spec-tools/spec_md_manager_v2.py list-rules <spec-file>

# 定期审查提醒
python3 tools/spec-tools/spec_md_manager_v2.py review --stale-days 90
```

---

**文档版本**: v1.0
**创建日期**: 2026-06-18
