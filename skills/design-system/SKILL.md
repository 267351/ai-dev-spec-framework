# 哈电集团品牌设计系统

B2B 工业品牌 UI 设计规范，适用于哈电集团（Harbin Electric Corporation）及其关联项目的所有前端开发。
央企质感，稳重厚重大气，拒绝花哨。

## 🎯 触发条件

当以下任一情况出现时，**立即自动触发此 Skill**：

1. 用户要求创建、修改或审查任何 UI 页面、组件、布局
2. 用户提到"哈电"、"央企风格"、"工业 B2B"、"蓝红配色"、"库房管理系统"
3. 用户要求添加样式、调整颜色、修改字体、设计表单、创建看板
4. 任何涉及 MudBlazor 组件使用的场景

---

## 🔍 加载流程

### 第一步：加载完整设计规范

读取 `data/MASTER.md` 获取完整的设计系统定义，包括：
- 品牌色板（蓝 `#15315A` / 红 `#C41E3A`，精确到 HEX）
- 字体栈（系统 CJK，不引入 Web Font）
- 间距和阴影系统
- 按钮/卡片/输入框/模态框等组件的精确 CSS 规范
- 反模式清单（禁止使用的内容）

### 第二步：参考实用样式文件

- `data/colors.css` — CSS 变量定义，可直接 `@import` 或复制到项目中
- `data/components.css` — 组件样式模板，按钮/卡片/输入框/模态框/分割线

### 第三步：执行交付前检查

在交付任何 UI 代码之前，逐项检查 `MASTER.md` 中的 Pre-Delivery Checklist：
- 颜色符合哈电品牌色板（蓝 `#15315A`，红 `#C41E3A`，无其他强调色）
- 字体使用系统 CJK 字体栈，无 Web Font 导入
- 红仅作点缀（≤5% 面积），蓝主导
- 所有 icons 来自 MudBlazor Icons 统一图标集
- 动画使用 `cubic-bezier(0.4, 0, 0.2, 1)`，尊重 `prefers-reduced-motion`

---

## 🚨 核心规则（Agent 必须记住的摘要）

### 品牌色彩
| 用途 | 色值 | CSS 变量 |
|------|------|----------|
| 主色 | `#15315A` 哈电蓝 | `--color-primary` |
| 主色深 | `#0B1A30` | `--color-primary-dark` |
| 主色浅 | `#1E4D8C` | `--color-primary-light` |
| 强调色 | `#C41E3A` 哈电红 | `--color-accent` |
| 强调色深 | `#A01830` | `--color-accent-dark` |

**铁律**：蓝主导，红 ≤5% 面积，**绝不使用**橘色、粉色、紫色、霓虹色、高饱和糖果色。

### 字体
```
font-family: 'Microsoft YaHei', 'PingFang SC', 'SimHei', sans-serif;
letter-spacing: 0.04em; /* 正文 */
letter-spacing: 0.10em; /* 标题 */
```
**铁律**：不引入任何 Web Font（Google Fonts、Adobe Fonts 等）。

### 调性
稳重、厚重大气、央企质感。拒绝轻浮、花哨、过度动画。

### 组件库
- UI 框架：**MudBlazor 8.x**
- 图标：**MudBlazor Icons**（SVG），禁止 emoji 作为图标
- 按钮渐变：`linear-gradient(135deg, #15315A, #1E4D8C)`
- 聚焦态：`outline: 2px solid #C41E3A; outline-offset: 2px;`
- 卡片：白色背景 `#FFFFFF`，`border-radius: 12px`，`box-shadow: var(--shadow-md)`

### 动画
```css
transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
```
**必须**尊重 `prefers-reduced-motion: reduce`。

### 响应式
| 断点 | 行为 |
|------|------|
| ≥901px | 双面板布局 |
| ≤900px | 面板堆叠 |
| ≤480px | 紧凑布局 |
| ≤375px | 最小适配 |

---

## ❌ 反模式（绝对禁止）

- ❌ 粉色/紫色渐变、AI 风格霓虹色、高饱和糖果色
- ❌ 引入 Web Font（Lexend、Source Sans 3、Noto Sans SC 等）
- ❌ 橘色作为强调色
- ❌ 过度动画 / 花哨效果
- ❌ Emoji 作为图标 — 使用 MudBlazor Icons (SVG)
- ❌ 低对比度文字（<4.5:1）
- ❌ 不可见的 focus states
- ❌ layout-shifting hovers（禁止 scale transform 导致布局偏移）
- ❌ 轻浮设计

---

## 📋 交付前检查清单

- [ ] 颜色符合哈电品牌色板（蓝 `#15315A`，红 `#C41E3A`，无其他强调色）
- [ ] 字体使用系统 CJK 字体栈，无 Web Font 导入
- [ ] 红仅作点缀（≤5% 面积），蓝主导
- [ ] 所有 icons 来自 MudBlazor Icons 统一图标集
- [ ] `cursor: pointer` on all clickable elements
- [ ] Hover states with smooth transitions (150-300ms, cubic-bezier)
- [ ] Light mode: text contrast 4.5:1 minimum
- [ ] Focus states visible for keyboard navigation (红色 outline)
- [ ] `prefers-reduced-motion` respected
- [ ] Responsive: 375px, 480px, 900px
- [ ] No horizontal scroll on mobile
- [ ] 无 emoji 作为图标
- [ ] 调性稳重，央企质感

---

## 📦 版本

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-05-30 | 初始版本：品牌色板、组件规范、字体间距、反模式清单 |
| v1.1 | 2026-06-17 | 提取为独立可复用 Skill，增加 CSS 变量文件和组件样式文件 |

## 🔗 跨项目使用

在任意新项目中引入此 Skill：

```bash
# 复制 Skill 到目标项目的 .opencode/skills/
cp -r skills/hadian-design-system /path/to/target/.opencode/skills/
```

AGENTS.md 中添加：
```markdown
## 哈电品牌规范
> 所有 UI 开发自动加载 `hadian-design-system` Skill。
> 核心色板：蓝 #15315A（主），红 #C41E3A（强调，≤5%面积）。
> 调性：央企工业质感，稳重厚重大气。
```
