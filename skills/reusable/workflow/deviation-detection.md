# Deviation Detection System

> **Category**: Workflow / Governance  
> **Reusable**: ✅ Yes — for any project using AGENTS.md + spec.md  
> **Dependencies**: AGENTS.md file, spec.md files

---

## When to Use

Your project uses AGENTS.md and spec.md files. Over time, code and docs diverge — code evolves but AGENTS.md gets stale. You need AI to detect AND report this automatically, without waiting for a human to notice.

---

## Deviation Types (三级偏差)

### 🔴 Hard Deviation (硬偏差)
Code violates an AGENTS.md/spec.md ironclad rule → build or runtime known to fail.

| Example | AGENTS.md says | Code does |
|---------|---------------|-----------|
| Dependency violation | "Web is forbidden to reference Infrastructure" | Web.csproj has `<ProjectReference Include="../Infrastructure">` |

**Action**: AI MUST stop and report. Cannot proceed without fixing.

### 🟡 Soft Deviation (软偏差)
Code implementation is actually correct/better than what AGENTS.md describes.

| Example | AGENTS.md says | Code does |
|---------|---------------|-----------|
| Deployment | "Use deploy.sh" | `deploy.ps1` for Windows support → actually an improvement |

**Action**: AI suggests updating AGENTS.md to match current better practice.

### 🟢 Evolution Deviation (演进偏差)
Technology has evolved; old rules are suboptimal but not wrong.

| Example | AGENTS.md says | Code/Reality |
|---------|---------------|--------------|
| .NET version | ".NET 9" | Project uses .NET 10 → should update reference |

**Action**: AI notes this for team discussion. Optional update.

---

## AI Behavior Rules

```
┌─────────────────────────────────────────────────────────┐
│  Every task start:                                        │
│  1. Load AGENTS.md + 架构总纲 + relevant *.spec.md       │
│  2. Compare against current code state                    │
│  3. If deviation found: STOP and report                   │
│  4. Output confirmation line:                             │
│     "已加载：AGENTS.md + 架构总纲 + X.spec.md"            │
└─────────────────────────────────────────────────────────┘
```

---

## AGENTS.md Rule Injection

Add these rules to your AGENTS.md:

```markdown
## 偏差检测规则

1. **每次任务开始前**，必须读取 AGENTS.md 和当前要修改的文件对应的 .spec.md
2. **如发现以下偏差，立即停止**并报告给用户：
   - 硬偏差：代码违反 AGENTS.md 中的禁止性规定 → 不允许继续
   - 软偏差：代码实现优于 AGENTS.md 描述 → 建议更新 AGENTS.md
   - 演进偏差：技术栈或实践已更新 → 标记待讨论
3. **偏差审批**必须逐条进行，不允许批量处理
4. **输出确认**：每次任务完成后输出 `已加载：AGENTS.md + [文件名]`
```

---

## Verification

- [ ] AGENTS.md contains deviation detection rules
- [ ] AI outputs "已加载" line at task start
- [ ] Deviations are reported per-item (not batched)
- [ ] Hard deviations block progress
- [ ] Team has a regular (quarterly) deviation review process
