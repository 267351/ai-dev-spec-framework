# Design System Master File — 哈电重装库房管理系统

> **LOGIC:** When building a specific page, first check `design-system/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.
>
> 本文件基于 AGENTS.md §九 哈电品牌规范制定，是项目 UI 设计的唯一事实来源。

---

**Project:** 哈电重装库房管理系统
**Updated:** 2026-05-30
**Category:** B2B Industrial — 央企库房管理

---

## Global Rules

### Color Palette

> 品牌语义：蓝 = 科技创新（水力/风力发电），红 = 激情与希望（火力/核能）。
> 红仅作点缀（≤5% 面积），蓝主导。

| Role | Hex | CSS Variable | Usage |
|------|-----|--------------|-------|
| 哈电蓝主色 | `#15315A` | `--color-primary` | 页面品牌面板背景、深色区块、标题文字 |
| 哈电蓝深 | `#0B1A30` | `--color-primary-dark` | 品牌面板渐变起点、导航深色区 |
| 哈电蓝浅 | `#1E4D8C` | `--color-primary-light` | hover 态、次要标题 |
| 哈电红 | `#C41E3A` | `--color-accent` | 按钮、超链接、分割线、聚焦态、强调文字 |
| 哈电红深 | `#A01830` | `--color-accent-dark` | 按钮渐变终点、hover 加深 |
| 卡片白 | `#FFFFFF` | `--color-surface` | 表单/内容卡片背景 |
| 面板底灰 | `#F4F6F9` | `--color-background` | 右侧/内容区浅色背景 |
| 面板底灰深 | `#E8ECF1` | `--color-background-alt` | 交替行、分区底色 |
| 文字主色 | `#1A1A2E` | `--color-text` | 正文、标题（≥4.5:1 对比度） |
| 辅助灰 | `#5A6B7A` | `--color-text-muted` | 副标题、标签、图标（≥4.5:1 对比度） |
| 边框灰 | `#D5DBDB` | `--color-border` | 输入框默认边框、分割线 |

**Color Notes:** 严禁粉色/紫色渐变、AI 风格霓虹色、高饱和糖果色。

### Typography

- **Font Stack:** `'Microsoft YaHei', 'PingFang SC', 'SimHei', sans-serif`
- **Mood:** 稳重、厚重大气、央企质感 — 拒绝轻浮/花哨/过度动画
- **不引入 Web Font** — 系统 CJK 字体已覆盖 99% 场景

**CSS:**
```css
body {
    font-family: 'Microsoft YaHei', 'PingFang SC', 'SimHei', sans-serif;
    letter-spacing: 0.04em;
}

h1, h2, h3 {
    font-family: 'Microsoft YaHei', 'PingFang SC', 'SimHei', sans-serif;
    letter-spacing: 0.10em;
    font-weight: 600;
}
```

### Spacing Variables

| Token | Value | Usage |
|-------|-------|-------|
| `--space-xs` | `4px` / `0.25rem` | Tight gaps |
| `--space-sm` | `8px` / `0.5rem` | Icon gaps, inline spacing |
| `--space-md` | `16px` / `1rem` | Standard padding |
| `--space-lg` | `24px` / `1.5rem` | Section padding |
| `--space-xl` | `32px` / `2rem` | Large gaps |
| `--space-2xl` | `48px` / `3rem` | Section margins |
| `--space-3xl` | `64px` / `4rem` | Hero padding |

### Shadow Depths

| Level | Value | Usage |
|-------|-------|-------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | Subtle lift |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.1)` | Cards, buttons |
| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.1)` | Modals, dropdowns |
| `--shadow-xl` | `0 20px 25px rgba(0,0,0,0.15)` | Hero images, featured cards |

### Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | `4px` | Inputs, chips |
| `--radius-md` | `8px` | Cards, buttons |
| `--radius-lg` | `12px` | Modals, dialogs |

---

## Component Specs

### Buttons

**Primary (哈电蓝):**
```css
.btn-primary {
    background: linear-gradient(135deg, #15315A, #1E4D8C);
    color: #FFFFFF;
    padding: 10px 24px;
    border-radius: 8px;
    border: none;
    font-weight: 600;
    font-family: 'Microsoft YaHei', 'PingFang SC', 'SimHei', sans-serif;
    cursor: pointer;
    transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-primary:hover {
    background: linear-gradient(135deg, #0B1A30, #15315A);
}

.btn-primary:focus-visible {
    outline: 2px solid #C41E3A;
    outline-offset: 2px;
}
```

**Accent (哈电红 — 仅关键操作，面积≤5%):**
```css
.btn-accent {
    background: linear-gradient(135deg, #C41E3A, #A01830);
    color: #FFFFFF;
    padding: 10px 24px;
    border-radius: 8px;
    border: none;
    font-weight: 600;
    font-family: 'Microsoft YaHei', 'PingFang SC', 'SimHei', sans-serif;
    cursor: pointer;
    transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-accent:hover {
    background: #A01830;
}
```

### Cards

```css
.card {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 24px;
    box-shadow: var(--shadow-md);
    border: 1px solid #D5DBDB;
    transition: box-shadow 200ms cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
}

.card:hover {
    box-shadow: var(--shadow-lg);
}
```

### Inputs

```css
.input {
    padding: 12px 16px;
    border: 1px solid #D5DBDB;
    border-radius: 4px;
    font-size: 14px;
    font-family: 'Microsoft YaHei', 'PingFang SC', 'SimHei', sans-serif;
    color: #1A1A2E;
    background: #FFFFFF;
    transition: border-color 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

.input:focus {
    border-color: #C41E3A;
    outline: none;
    box-shadow: 0 0 0 3px rgba(196, 30, 58, 0.12);
}

.input::placeholder {
    color: #9CA3AF;
}
```

### Modals

```css
.modal-overlay {
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
}

.modal {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 32px;
    box-shadow: var(--shadow-xl);
    max-width: 500px;
    width: 90%;
}
```

### Dividers

```css
.divider {
    border: none;
    border-top: 1px solid #D5DBDB;
    margin: 16px 0;
}

.divider-accent {
    border: none;
    border-top: 2px solid #C41E3A;
    margin: 16px 0;
}
```

---

## Style Guidelines

**Style:** 稳重、厚重大气、央企质感 — Trust & Authority

**Keywords:** 工业、制造业、央企、可靠、专业、稳重

**Key Effects:** 微妙的 hover 状态变化，避免过度动画。所有动画使用 `cubic-bezier(0.4, 0, 0.2, 1)`，必须尊重 `prefers-reduced-motion`。

### Animation

```css
/* 标准缓动函数 */
--ease-standard: cubic-bezier(0.4, 0, 0.2, 1);

/* 必须尊重用户偏好 */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
```

### Accessibility

- 文字对比度 ≥4.5:1
- `:focus-visible` 键盘焦点可见（红色 2px outline）
- `aria-live` / `role="alert"` 用于错误提示
- 所有可点击元素必须 `cursor: pointer`

### Responsive Breakpoints

| 断点 | 宽度 | 行为 |
|------|------|------|
| Desktop | ≥901px | 双面板布局 |
| Tablet | ≤900px | 面板堆叠 |
| Mobile | ≤480px | 紧凑布局 |
| Small Phone | ≤375px | 最小适配 |

---

## Logo Resources

| File | Dimensions | Usage |
|------|-----------|-------|
| `wwwroot/LOGOimg/logo-long.gif` | 1011×147 | 完整品牌横幅（含中英文），页面顶部/右上角 |
| `wwwroot/LOGOimg/logo-short.png` | 60×61 | 方形标志，favicon 或小尺寸品牌锚点 |
| `wwwroot/LOGOimg/logo-short-tail.jpg` | 733×50 | 横向简洁版，备选 |

---

## Anti-Patterns (Do NOT Use)

- ❌ 粉色/紫色渐变
- ❌ AI 风格霓虹色
- ❌ 高饱和糖果色
- ❌ 引入 Web Font（Lexend、Source Sans 3、Noto Sans SC 等）
- ❌ 过度动画 / 花哨效果
- ❌ 轻浮设计
- ❌ Emojis as icons — 使用 SVG icons（MudBlazor Icons）
- ❌ 低对比度文字（<4.5:1）
- ❌ 不可见的 focus states
- ❌ layout-shifting hovers（禁止 scale transform 导致布局偏移）
- ❌ 橘色作为强调色

---

## Pre-Delivery Checklist

Before delivering any UI code, verify:

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
