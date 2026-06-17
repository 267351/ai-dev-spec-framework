# 可验证规则标注格式规范

> 解决 Problem 1：为 spec.md 中的规则定义机器可读的验证标注格式，
> 使自动验证工具（Roslyn Analyzer、AI Agent）能够解析和执行检查。

---

## 一、标注体系概览

规则标注分为两个层次：

| 层次 | 标注方式 | 用途 | 适用工具 |
|------|---------|------|---------|
| **语义标注** | `[verifiable:xxx]` | 标记规则的可验证类型 | 人工阅读 + 工具解析 |
| **机器指令** | `<!-- @rule id= ... -->` | 为自动检查提供精确指令 | Roslyn Analyzer, AI Agent |

---

## 二、语义标注：`[verifiable:xxx]`

### 2.1 标注类型

```markdown
### 🚫 [verifiable:di] 分层架构红线
1. **禁止** Web 项目引用 Infrastructure 项目
```

| 标注值 | 含义 | 检查方式 | 工具 |
|--------|------|---------|------|
| `[verifiable:di]` | 依赖注入/项目引用 | Roslyn 语义分析 | Analyzer |
| `[verifiable:naming]` | 命名规范 | AST 分析 / 正则 | Analyzer |
| `[verifiable:pattern]` | 代码模式 | AST 模式匹配 | Analyzer |
| `[verifiable:structure]` | 结构化约束（try/catch、null check） | AST 模式匹配 | Analyzer |
| `[verifiable:semantic]` | 语义规则（需理解上下文） | AI Agent 审查 | spec_compliance_check.py |
| `[contextual]` | 高度上下文依赖的规则 | AI Agent + 人工 | 仅文档参考 |
| `[unverifiable]` | 不可自动验证的规则 | 人工审查 | 仅文档 |

### 2.2 组合标注

一条规则可以同时有多个标注：

```markdown
### 🚫 [confidence:validated] [verifiable:di] [sunset:2027-01-01] 分层架构红线
```

标注顺序建议：`[confidence:xxx] [verifiable:xxx] [sunset:YYYY-MM-DD]`

---

## 三、机器指令：HTML 注释标注

### 3.1 `<!-- @rule -->`：规则标识

```markdown
<!-- @rule id=WM-ARCH-001 type=dependency-check severity=error -->
1. **禁止** Web 项目引用 Infrastructure 项目
```

**字段说明**：

| 字段 | 必需 | 说明 | 示例 |
|------|------|------|------|
| `id` | ✅ | 全局唯一规则ID | `WM-ARCH-001` |
| `type` | ✅ | 检查类型 | `dependency-check` |
| `severity` | ❌ | 违规严重度（error/warning/suggestion） | `error` |
| `scope` | ❌ | 适用范围 | `project:WarehouseManagement.Web` |

**规则ID命名规范**：`{项目缩写}-{类别缩写}-{序号}`
- 项目缩写：WM (WarehouseMS), CF (CSO-FORCS)
- 类别缩写：ARCH(架构), NAMING(命名), CODE(编码), DI(依赖注入), SEC(安全)

### 3.2 `<!-- @check: -->`：检查指令

为不同类型的检查提供精确指令：

```markdown
<!-- @check: Web项目不引用Infrastructure项目 -->
<!-- @check: Web层不包含DbContext类型引用 -->
```

**指令类型**：

| 指令格式 | 用途 | 检查方式 |
|---------|------|---------|
| `@check: <项目A>不引用<项目B>` | 依赖方向检查 | 检查 csproj ProjectReference |
| `@check: <层>不包含<类型>引用` | 类型引用检查 | 检查 using/import 语句 |
| `@check: <方法/类>必须包含<模式>` | 模式存在检查 | AST 遍历检查 |
| `@check: <方法/类>禁止调用<API>` | API 禁止检查 | AST 调用链分析 |
| `@check: 命名匹配:<正则>` | 命名检查 | 正则/AST 符号匹配 |
| `@check: AI审查:<自然语言描述>` | AI 审查指令 | AI Agent Prompt |

### 3.3 `<!-- @pattern: -->`：代码模式匹配

对于结构化规则，使用简化的模式描述语言：

```markdown
<!-- @pattern: Controller方法体必须包含 try/catch -->
<!-- @pattern: try { ... } catch(Exception ex) { return BadRequest(ex.Message); } -->
```

---

## 四、完整示例

### 示例1：依赖方向检查规则

```markdown
### 🚫 [confidence:validated] [verifiable:di] 分层架构红线
<!-- @rule id=WM-ARCH-001 type=dependency-check severity=error -->
<!-- @check: WarehouseManagement.Web 不引用 WarehouseManagement.Infrastructure -->
<!-- @check: WarehouseManagement.Infrastructure 不引用 WarehouseManagement.Web -->
1. **禁止** Web 项目引用 Infrastructure 项目
2. **禁止** Infrastructure 层引用 Web 项目
```

### 示例2：命名规范检查规则

```markdown
### ✅ [confidence:consensus] [verifiable:naming] 异步方法命名
<!-- @rule id=WM-NAMING-001 type=naming-check severity=warning -->
<!-- @check: 命名匹配:.*Async$ -->
<!-- @check: 返回类型为 Task 或 Task<T> 的公共方法必须以 Async 结尾 -->
1. **建议** 异步方法使用 Async 后缀
```

### 示例3：代码模式检查规则

```markdown
### ✅ [confidence:proven] [verifiable:pattern] API 异常处理
<!-- @rule id=WM-CODE-001 type=pattern-check severity=error -->
<!-- @pattern: Controller 方法体必须包含 try/catch -->
<!-- @pattern: catch(Exception ex) { return BadRequest(ex.Message); } -->
1. **必须** Controller 方法使用 try/catch + BadRequest(ex.Message)
```

### 示例4：AI 审查规则（无法静态分析）

```markdown
### 🚫 [confidence:validated] [verifiable:semantic] 四层匹配业务规则
<!-- @rule id=WM-BIZ-001 type=ai-review severity=error -->
<!-- @check: AI审查:发放砂轮片时必须校验项目→标准→打磨对象→砂轮片材质的四层匹配关系 -->
1. **禁止**发放砂轮片时不校验四层匹配关系
```

### 示例5：上下文规则（不可自动验证）

```markdown
### ⚠️ [confidence:preventive] [unverifiable] 批量处理时间窗口
1. **建议** 大批量数据导出仅在夜间批处理中执行
```

---

## 五、规则分类与检查工具映射

| verifiable 类型 | 首选检查工具 | 实现成本 | 误报率 |
|----------------|-------------|---------|--------|
| `di` | Roslyn Analyzer | 中 | 低 |
| `naming` | Roslyn Analyzer / Regex | 低 | 低 |
| `pattern` | Roslyn Analyzer | 中-高 | 中 |
| `structure` | Roslyn Analyzer | 中 | 低 |
| `semantic` | AI Agent | 低（开发）/ 持续（调用） | 中 |
| `contextual` | AI Agent + 人工 | - | 高 |
| `unverifiable` | 人工审查 | - | - |

---

## 六、标注的优先级规则

1. `[verifiable:xxx]` 标注的优先级高于 `<!-- @check: -->` 指令
2. `<!-- @rule severity=error -->` 规则违反时阻止构建
3. `<!-- @rule severity=warning -->` 规则违反时产生警告
4. `<!-- @rule severity=suggestion -->` 规则违反时仅提示
5. `[confidence:validated]` 级别的高严重度规则，自动提升检查级别

---

## 七、向后兼容

- 标注格式向后兼容原有 spec.md 格式
- 不加标注的规则视为 `[unverifiable]`
- HTML 注释在 Markdown 渲染中不可见，不影响文档可读性
- 规则解析器对缺失标注采取宽容策略（不报错，但标记为未标注）

---

**规范版本**: v1.0
**制定日期**: 2026-06-18
