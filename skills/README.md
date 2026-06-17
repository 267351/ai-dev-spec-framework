# Skills 库

> 从 CSO-FORCS 和 WarehouseMS 两个工业项目中提炼的可复用开发技能。
> 按领域分类，每个 Skill 自包含——直接复制到其他项目即可使用。

---

## 目录结构

```
skills/
├── README.md                           ← 本文件
├── architecture/                       ← 架构模式（3 个）
├── coding/                             ← 编码模式（5 个）
├── workflow/                           ← 工作流 / 治理模式（2 个）
├── deployment/                         ← 部署模式（2 个）
├── ui/                                 ← UI 模式（1 个）
├── design-system/                      ← OpenCode Skill：品牌设计系统
└── tools/                              ← spec-tools 工具集
    └── spec-tools/
```

---

## 架构（Architecture）

| Skill | 文件 | 一句话 |
|-------|------|--------|
| HAL 硬件抽象层 + 三实现 | `architecture/hal-triple-implementation.md` | Mock/Real/Disabled 三实现 + 状态矩阵管理 |
| 进程编排器 | `architecture/process-orchestrator.md` | 多服务按序启动、健康检查、崩溃自恢复 |
| 统一配置层 | `architecture/unified-configuration-layer.md` | 一行注册全部配置，强类型 Options |

## 编码（Coding）

| Skill | 文件 | 一句话 |
|-------|------|--------|
| 作业状态机 | `coding/state-machine.md` | 多状态生命周期 + 超时全覆盖 + 异常检测 |
| 偏差分级告警 | `coding/deviation-classification.md` | 三级可配阈值（正常/警告/严重） |
| 系数快照模式 | `coding/coefficient-snapshot.md` | 历史记录免疫配置变更 |
| 策略模式业务扩展 | `coding/strategy-pattern-business-rules.md` | 新增类型 = 新类 + DI，不改已有代码 |
| SignalR 自适应轮询 | `coding/signalr-adaptive-polling.md` | 活跃/空闲自适应 + 重连消息刷新 |

## 工作流 / 治理（Workflow）

| Skill | 文件 | 一句话 |
|-------|------|--------|
| Bug 模式知识库 | `workflow/bug-pattern-knowledge-base.md` | 结构化 Bug 登记，AI 修改前自动读取 |
| 偏差检测系统 | `workflow/deviation-detection.md` | 硬/软/演进三级偏差，AI 主动检测报告 |

## 部署（Deployment）

| Skill | 文件 | 一句话 |
|-------|------|--------|
| 升级保护与回滚 | `deployment/upgrade-protection-rollback.md` | 原地升级 + 数据保留 + 失败回滚 |
| Kiosk 自启动 | `deployment/kiosk-self-boot.md` | 无头检测 + 浏览器优先级链 + 窗口持久化 |

## UI

| Skill | 文件 | 一句话 |
|-------|------|--------|
| 三组搜索列表 | `ui/three-group-search-list.md` | 实时 AND 组合搜索 + 内存过滤 + 分页 |

## 设计系统（OpenCode Skill）

| Skill | 目录 | 说明 |
|-------|------|------|
| 品牌设计系统 | `design-system/` | MudBlazor 品牌色板、字体栈、组件规范（SKILL.md + data/） |

## 工具集

| 工具 | 目录 | 说明 |
|------|------|------|
| spec-tools | `tools/spec-tools/` | spec.md 体系全生命周期工具链（8 个组件） |

---

## 使用方式

### 复制单个 Skill

```bash
# 直接复制 .md 文件到目标项目
cp skills/coding/state-machine.md /path/to/project/docs/patterns/
```

### 复制 OpenCode Skill

```bash
cp -r skills/design-system /path/to/project/.opencode/skills/
```

### 部署整套 spec-tools

```bash
cd skills/tools/spec-tools && ./deploy.sh /path/to/project
```

---

## Skill 文件约定

每个 Skill 文件统一使用以下结构：

```markdown
# Skill 名称

> **分类**: 架构 / 编码 / 工作流 / 部署 / UI
> **可复用**: ✅ 是
> **依赖**: 无（或列出依赖）

## 适用场景
（什么时候用）

## 模式
（核心设计图示）

## 实现
（分步骤的代码示例）

## 验证清单
（可检查的完成标准）
```
