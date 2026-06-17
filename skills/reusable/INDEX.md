# 可复用 Skills 索引

> 从 CSO-FORCS 和 WarehouseMS 两个工业项目中提炼的**可独立复用 Skills**。
> 每个 Skill 文件自包含——直接复制到其他项目的 Skill 系统中即可使用。

---

## 目录

### 架构

| Skill | 文件 | 适用场景 |
|-------|------|----------|
| HAL 硬件抽象层 + 三实现模式 | `architecture/hal-triple-implementation.md` | 涉及硬件/传感器的项目 |
| 进程编排器（Launcher） | `architecture/process-orchestrator.md` | 3+ 服务进程需协调启动 |
| 统一配置层 | `architecture/unified-configuration-layer.md` | .NET 项目配置管理 |

### 编码

| Skill | 文件 | 适用场景 |
|-------|------|----------|
| 作业状态机 | `coding/state-machine.md` | 有状态业务流程的项目 |
| 传感器偏差分级告警 | `coding/deviation-classification.md` | 传感器/测量数据验证 |
| 系数快照模式 | `coding/coefficient-snapshot.md` | 历史数据需免疫配置变更 |
| 策略模式驱动业务扩展 | `coding/strategy-pattern-business-rules.md` | 业务规则需按类型扩展 |
| SignalR 自适应轮询 | `coding/signalr-adaptive-polling.md` | Blazor 实时数据推送 |

### 工作流 / 治理

| Skill | 文件 | 适用场景 |
|-------|------|----------|
| Bug 模式知识库 | `workflow/bug-pattern-knowledge-base.md` | 任何积累 Bug 的项目 |
| 偏差检测系统 | `workflow/deviation-detection.md` | 使用 AGENTS.md + spec.md 体系的项目 |

### 部署

| Skill | 文件 | 适用场景 |
|-------|------|----------|
| 升级保护与回滚 | `deployment/upgrade-protection-rollback.md` | 本地部署需现场升级 |
| Kiosk 自启动部署 | `deployment/kiosk-self-boot.md` | 工业/展厅自助终端 |

### UI

| Skill | 文件 | 适用场景 |
|-------|------|----------|
| 三组搜索列表模式 | `ui/three-group-search-list.md` | 有搜索列表页的 Web 项目 |

---

## 使用方式

### 方式一：复制到 OpenCode 项目

```bash
cp -r skills/reusable/coding/state-machine.md /path/to/project/.opencode/skills/state-machine/SKILL.md
```

### 方式二：复制到使用 spec-tools 的项目

```bash
# deploy.sh 会自动处理。手动：
cp skills/reusable/coding/state-machine.md /path/to/project/tools/skills/
```

### 方式三：直接在 AGENTS.md 中引用

```markdown
# AGENTS.md
## 可用 Skills
- 作业状态机 → 参见 tools/skills/state-machine.md
- 系数快照 → 参见 tools/skills/coefficient-snapshot.md
```

---

## 如何添加新 Skill

1. 选择合适的分类目录（architecture/coding/workflow/deployment/ui）
2. 使用统一模板：`适用场景` → `模式` → `实现` → `验证清单`
3. 在 **依赖** 字段准确标注外部依赖
4. 确保 Skill **自包含**——依赖外部工具/库必须在"依赖"中说明
5. 更新本索引文件
