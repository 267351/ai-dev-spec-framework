# 哈电集团设计系统：作为可复用、可升版的 UI Skill

> "韩电子集装风格" → 实际是 **哈电集团（Harbin Electric Corporation）装风格**
> 这是一个完整的 B2B 工业品牌设计系统，已封装为可跨项目复用的规范体系。

---

## 一、设计系统概览

### 1.1 三层结构

```
┌─────────────────────────────────────────────────────┐
│ L1: 品牌规范（AGENTS.md §九）                        │
│     色彩 / 字体 / 调性 / 反模式（约 30 行）          │
│     → AI 不需要读完整设计系统，先看摘要               │
├─────────────────────────────────────────────────────┤
│ L2: MASTER.md（design-system/哈电重装库房管理系统/） │
│     完整设计规范：色彩变量 / 组件 CSS / 间距 / 阴影   │
│     → AI 在需要具体 UI 细节时按需加载                 │
├─────────────────────────────────────────────────────┤
│ L3: 页面级覆盖（design-system/pages/*.md）           │
│     特定页面的设计覆写规则                            │
│     → 页面规则 > MASTER > AGENTS.md                  │
└─────────────────────────────────────────────────────┘
```

### 1.2 核心设计参数

| 参数 | 值 | 语义 |
|------|-----|------|
| 品牌色-蓝 | `#15315A` → `#1E4D8C`（渐变） | 科技创新（水力/风力发电） |
| 品牌色-红 | `#C41E3A` | 激情与希望（火力/核能），≤5% 面积 |
| 字体栈 | `'Microsoft YaHei', 'PingFang SC', 'SimHei', sans-serif` | 系统 CJK，不引入 Web Font |
| 调性 | 稳重、厚重大气、央企质感 | B2B Industrial |
| 组件库 | MudBlazor 8.x | 统一 UI 框架 |
| 图标 | MudBlazor Icons (SVG) | 禁止 emoji 作为图标 |
| 动画 | `cubic-bezier(0.4, 0, 0.2, 1)` | 尊重 prefers-reduced-motion |
| 对比度 | ≥4.5:1 | WCAG AA |

---

## 二、为什么可以当做 Skill 来复用

### 2.1 设计系统作为 Skill 的四个条件

| 条件 | 哈电设计系统 | 满足？ |
|------|-------------|:------:|
| **自包含** | 所有颜色、字体、间距、阴影、组件规范都在 MASTER.md（301行）中完整定义 | ✅ |
| **可加载** | OpenCode 的 Skill 机制支持按需加载，AI 读取 SKILL.md → 遵循约束 | ✅ |
| **可版本化** | 设计系统有独立的目录和版本标记（Updated: 2026-05-30），可独立演进 | ✅ |
| **跨项目可迁移** | 品牌色板、组件规范、反模式清单是"哈电集团"的品牌标准，不是项目特定的 | ✅ |

### 2.2 Skill 化设计

当前 WarehouseMS 通过 AGENTS.md §九 + `design-system/MASTER.md` 两级加载。更进一步的设计是将其封装为独立的 OpenCode Skill：

```
.opencode/skills/hadian-design-system/
├── SKILL.md                 # Skill 入口：何时加载、加载什么
├── data/
│   ├── colors.css           # CSS 变量文件（可被项目直接引用）
│   ├── components.css       # 按钮/卡片/输入框/模态框 样式
│   └── MASTER.md            # 完整设计规范（同当前文件）
└── scripts/
    └── verify.sh            # 交付前检查脚本（Pre-Delivery Checklist）
```

**SKILL.md 关键设计**：

```markdown
# 哈电集团品牌设计系统 Skill

## 触发条件
- 任何涉及 UI 设计、页面创建、样式修改的操作
- 用户提到"哈电"、"央企风格"、"工业 B2B"、"蓝红配色"

## 加载内容
1. 先读 `data/MASTER.md` 获取完整设计规范
2. 参考 `data/colors.css` 获取 CSS 变量定义
3. 参考 `data/components.css` 获取组件样式模板

## 核心规则（AGENTS.md 级别摘要）
- 蓝 = 主色 (#15315A)，红 = 强调色 (#C41E3A)，红 ≤5% 面积
- 字体：系统 CJK，不引入 Web Font
- 调性：稳重、央企质感，拒绝花哨
- 图标：MudBlazor Icons only
- 动画：cubic-bezier 标准曲线，尊重 reduced-motion
- 禁止：粉色/紫色/霓虹色/高饱和糖果色/emoji 图标

## 版本
- v1.0 (2026-05-30)
```

### 2.3 升版（版本升级）策略

用户提到"可以升版，以实现项目之间的迁徙"。设计系统版本升级的支持策略：

```
v1.0 (WarehouseMS)
  品牌色板 + 组件规范 + 字体/间距
         │
         ▼ 版本号升到 v1.1
  v1.1 新增：响应式断点表、Dark Mode 配色
         │
         ▼ 版本号升到 v2.0
  v2.0 新增：DataGrid/Table 专用组件规范、图表配色方案
         │
         ▼ 跨项目迁移
  新项目（如 CSO-FORCS）引入 hadian-design-system Skill v2.0
  → AI 自动获得完整的哈电品牌 UI 规范
  → 不需要在新项目中重新定义颜色/字体/组件
```

**升版的关键设计**：
- CSS 变量命名稳定（`--color-primary` 永远指向哈电蓝，即使色值微调）
- 组件语义稳定（`.btn-primary` 永远是主要按钮，样式可升级但不改名）
- 反模式清单随版本追加（新版本可以增加"禁止 xxx"而不断裂旧约束）

---

## 三、CSO-FORCS 是否有独立的 UI 设计系统？

**对比**：CSO-FORCS 没有独立的 design-system 目录或 UI Skill。

| 维度 | WarehouseMS | CSO-FORCS |
|------|-------------|-----------|
| 设计系统文件 | `design-system/MASTER.md`（301行） | 无独立文件 |
| 品牌规范 | 哈电集团：蓝红配色、央企调性 | 无品牌定义 |
| 组件库 | MudBlazor 8.x | 无第三方 UI 库（纯 Blazor 组件） |
| 样式管理 | `.razor.css` CSS 隔离（46 文件） | `.razor.css` CSS 隔离（46 文件） |
| UI 约束 | AGENTS.md §九（品牌规范）+ spec.md 文件 | 架构总纲.spec.md §Blazor 红线 |

**差异分析**：
- CSO-FORCS 的 UI 关注点在**技术约束**（不许在 `.razor` 写 `<style>`、不许嵌套 rendermode），而非**视觉风格约束**（品牌色、字体、调性）。
- WarehouseMS 的 UI 约束更完整——技术约束 + 视觉风格约束都有覆盖。这是因为 WarehouseMS 面向央企客户（哈电集团），品牌一致性是硬需求；CSO-FORCS 面向工业操作员，功能性优先。

---

## 四、提炼论文可用的洞察

### 洞察 1：设计系统 = Skills 的自然形态

Skills 的设计初衷就是封装可复用的领域知识。UI 设计系统天然符合这一范式：
- 知识自包含（颜色、字体、间距、组件是一个完整的域）
- 有明确的"触发条件"（做 UI 时自动加载）
- 有可版本化的演进过程（品牌色可能调整，组件样式可能优化）
- 跨项目可复用（哈电集团的品牌标准适用所有哈电相关系统）

### 洞察 2：三层加载策略的通用性

```
L1: AGENTS.md（30行摘要）→ AI 快速了解"我们用什么风格"
L2: Skill/MASTER.md（完整规范）→ AI 需要具体细节时按需加载
L3: Page-level spec.md（页面覆盖）→ 特殊页面可以覆写通用规则
```

这个三层加载策略不仅适用于 UI 设计系统，也适用于任何大型规范体系——它是 AGENTS.md 精简原则（≤100行）在设计系统领域的自然延伸。

### 洞察 3：spec.md 的双重身份

在 WarehouseMS 中，MainLayout.spec.md、DashboardLayout.spec.md、NavMenu.spec.md 等文件兼具两种角色：
1. **架构约束**（spec.md 的传统角色）：不许在 layout 中直接操作数据
2. **UI 风格约束**（design-system 的延伸）：必须遵守哈电品牌色、字体、调性

这证明 spec.md 体系不仅适用于架构约束，也适用于 UI 风格约束——它是统一的"约束表达格式"。

---

**分析时间**: 2026-06-17
**数据来源**: WarehouseMS/design-system/MASTER.md（301行）、AGENTS.md §九、46个 .razor.css 文件
