# CSO-FORCS 可单独复用的 Skills 清单

> 基于对 CSO-FORCS 项目（工业安全管理系统，14个子项目，300+ spec.md 文件，9个 AI Skills）的深度分析，
> 提取可独立复用的开发技能。按原创价值分类：🔴原创 / 🟡创新应用 / 🟢工业标准。

---

## 一、架构 Skills

### S1：🔴 双子系统独立部署架构

| 属性 | 内容 |
|------|------|
| **名称** | `dual-subsystem-isolated-deployment` |
| **描述** | 两个独立业务子系统（有限空间作业系统 + 库房管理系统）共享 BLL/DAL/Models 层，但各自拥有独立的 API 进程、Blazor SSR Host、前端页面和认证授权。子系统间通过 HTTP API 通信，禁止代码级互相引用。 |
| **来源** | `AGENTS.md.spec.md` §三, `架构总纲.spec.md`, 14 个 csproj 的依赖关系 |
| **验证标准** | 1. 两个 SSR Host 不互相引用 csproj<br>2. 跨子系统通信仅通过 HTTP API<br>3. 共享接口定义在 Models 层<br>4. 每个子系统独立端口分配（4+ 端口）<br>5. 认证 Token 跨子系统共享 |
| **复用条件** | 项目有 ≥2 个独立业务域，需要独立部署、独立升级、但共享核心业务逻辑 |

### S2：🔴 硬件抽象层 + 三实现模式（HAL with Triple Implementation）

| 属性 | 内容 |
|------|------|
| **名称** | `hal-triple-implementation` |
| **描述** | 为每个硬件设备定义接口（如 `ICardReader`），提供三种实现：(1) Mock 实现用于开发/测试，(2) 真实硬件实现用于生产，(3) Disabled 实现用于硬件不可用时优雅降级。通过配置切换实现，维护实现状态矩阵防止误删 Mock。 |
| **来源** | `src/LimitedSpaceForeignObject.HAL/`, `AGENTS.md.spec.md` HAL 实现状态矩阵 |
| **验证标准** | 1. 每个硬件接口有 ≥2 个实现<br>2. Mock 可配置行为（构造参数/回调）<br>3. 禁用实现返回"不可用"而非抛异常<br>4. 维护 HAL 实现状态矩阵<br>5. 生产前验证矩阵确认所有真实实现就绪 |
| **复用条件** | 项目涉及物理硬件（读卡器、传感器、摄像头、打印机等），需要开发-测试-生产环境切换 |

### S3：🔴 32位微服务隔离（32-bit Microservice Isolation）

| 属性 | 内容 |
|------|------|
| **名称** | `bitness-microservice-isolation` |
| **描述** | 当主应用为 64 位但依赖 32 位原生 DLL 时，将原生调用封装为独立的 32 位 HTTP 微服务。主应用通过 HTTP Client 代理访问。使用 `SemaphoreSlim` 序列化硬件访问，缓存状态（TTL 5s）减少轮询。支持热插拔检测和自动重连。 |
| **来源** | `src/LimitedSpaceForeignObject.CardReader/`, `src/LimitedSpaceForeignObject.HAL/CardReader/HttpCardReaderClient.cs` |
| **验证标准** | 1. 微服务独立进程（端口 5100）<br>2. HTTP Client 配置超时和重试<br>3. 设备独占锁（SemaphoreSlim）<br>4. 状态缓存 + TTL 过期<br>5. 设备断开自动重连<br>6. 部署时指定 win-x86 RID |
| **复用条件** | 主应用与原生 DLL 位数不匹配（64位主应用 + 32位DLL），或需要进程级硬件隔离 |

### S4：🟡 三大系统边界隔离

| 属性 | 内容 |
|------|------|
| **名称** | `system-boundary-isolation` |
| **描述** | 业务域拆分为独立子系统，Service 层禁止跨系统注入。跨系统数据聚合仅在 Web/API 层进行。每个系统有独立的 Controller 和 Blazor 页面。 |
| **来源** | `AGENTS.md`, `架构总纲.spec.md`（同 WarehouseMS Skill 4，但 CSO-FORCS 实现了进程级隔离） |
| **复用条件** | 业务域 ≥3 且有明确边界 |

### S5：🔴 进程编排器（Launcher Process Orchestrator）

| 属性 | 内容 |
|------|------|
| **名称** | `launcher-process-orchestrator` |
| **描述** | 一个独立的 Launcher 进程（1439行）负责：(1) 端口冲突检测和自动清理，(2) 按依赖顺序启动 5 个服务，(3) 对每个服务执行 HTTP 健康检查（超时可配），(4) 崩溃监控和自动重启，(5) 崩溃诊断转储（最近 50 行日志 + 进程元数据），(6) SSE 实时健康面板（844行，暗色主题），(7) IPC 通过 `.ready` 文件通知外部脚本。 |
| **来源** | `src/LimitedSpaceForeignObject.Launcher/Program.cs`, `HealthDashboard.cs` |
| **验证标准** | 1. 服务按依赖顺序启动<br>2. 每个服务启动后验证健康检查<br>3. 崩溃自动重启（可配置）<br>4. 崩溃保存诊断日志<br>5. 健康面板实时显示状态<br>6. .ready 文件通知外部 |
| **复用条件** | 项目有 ≥3 个需要协调启动的服务进程，需要崩溃自动恢复 |

### S6：🔴 统一配置层（Unified Configuration Layer）

| 属性 | 内容 |
|------|------|
| **名称** | `unified-configuration-layer` |
| **描述** | 独立的 Configuration 项目作为最底层（不依赖任何其他项目），定义所有 Options 类。通过单个扩展方法 `AddCsoForcsConfiguration()` 一行注册所有 Options + Named HttpClients + Aspire 默认配置。日志通过 `UseCsoForcsLogging()` 一行配置 Serilog 双输出（控制台+文件）。 |
| **来源** | `src/LimitedSpaceForeignObject.Configuration/` |
| **验证标准** | 1. Configuration 项目无项目依赖<br>2. 所有 Options 类集中定义<br>3. 一行扩展方法注册全部配置<br>4. Options 使用强类型绑定<br>5. 配置值通过 DI 注入，不直接读 appsettings.json |
| **复用条件** | 大型项目有 ≥5 个 Options 类需要统一管理 |

---

## 二、UI/交互 Skills

### S7：🔴 双屏 Kiosk 操作台 + 协调器

| 属性 | 内容 |
|------|------|
| **名称** | `dual-screen-kiosk-coordinator` |
| **描述** | A 屏幕负责业务操作（人员进出、物资登记），B 屏幕负责 4 路摄像头监控。两个屏幕通过 SignalR Hub 实时通信——A 屏登录触发 B 屏拍照，B 屏扫码结果回传 A 屏。`OperationCoordinatorService` 管理跨屏共享状态（当前会话 ID、当前人员 ID）和 29 种摄像头指令类型。 |
| **来源** | `Components/Layout/ScreenABLayout.razor`, `Services/OperationCoordinatorService.cs`, `Services/SignalRService.cs` |
| **验证标准** | 1. ScreenABLayout 无导航、无侧栏、满屏<br>2. A/B 屏通信通过 SignalR CameraCommand<br>3. Coordinator 持有共享状态<br>4. SignalR 重连后刷新待处理指令<br>5. 双屏独立 URL（/operations, /operations/cameras） |
| **复用条件** | 工业场景需要操作台 + 监控屏双屏联动 |

### S8：🔴 Kiosk 自启动部署

| 属性 | 内容 |
|------|------|
| **名称** | `kiosk-self-boot-deployment` |
| **描述** | 部署脚本自动生成平台特定的 Kiosk 启动脚本：(1) 自动检测无头环境跳过浏览器，(2) Chrome→Chromium→Edge→Firefox 优先级链，(3) 窗口几何持久化（wmctrl 保存/恢复位置），(4) Root 用户自动添加 --no-sandbox，(5) 终端 Raw 模式 ReadKey 后台线程，(6) 交互式菜单（R=重启, Q=退出），(7) Launcher 通过 .ready 文件通知启动完成。 |
| **来源** | `deploy.sh` §Kiosk 生成部分, `src/LimitedSpaceForeignObject.Launcher/Program.cs` |
| **验证标准** | 1. 部署后在目标机上可一键启动<br>2. 浏览器全屏到正确显示器<br>3. 窗口位置跨重启保持<br>4. 服务崩溃自动恢复<br>5. 无头环境优雅降级 |
| **复用条件** | 工业/展厅场景需要自助终端式部署 |

---

## 三、编码 Skills

### S9：🟡 人脸识别流水线（Face Recognition Pipeline）

| 属性 | 内容 |
|------|------|
| **名称** | `face-recognition-pipeline` |
| **描述** | 多阶段人脸处理流水线：(1) 人脸检测（FaceDetectionService），(2) 质量评估（FaceQualityService：光照、角度、遮挡），(3) 活体检测（LivenessDetectionService），(4) 1:N 比对（ComparisonService），(5) 结果记录（ComparisonRecord 实体）。每阶段可独立 Mock 用于测试。 |
| **来源** | `src/LimitedSpaceForeignObject.BLL/Services/FaceDetectionService.cs`, `FaceQualityService.cs`, `LivenessDetectionService.cs`, `ComparisonService.cs` |
| **验证标准** | 1. 每个阶段独立接口<br>2. 每阶段有 Mock 实现<br>3. 流水线可跳过中间阶段<br>4. 比对结果记录到数据库<br>5. 质量不合格时拒绝比对 |
| **复用条件** | 需要人脸识别门禁/考勤/安防 |

### S10：🔴 作业状态机（Work Session State Machine）

| 属性 | 内容 |
|------|------|
| **名称** | `work-session-state-machine` |
| **描述** | 有限空间作业的 5 状态生命周期：Entering → Working → Exiting → Completed/CompletedWithWarning。超时告警覆盖所有未完成状态（不仅 Working）。空手进入必须调用 ConfirmEntryAsync 否则状态卡在 Entering。在区人员列表显示 Entering + Working 两种状态。 |
| **来源** | `src/LimitedSpaceForeignObject.BLL/Services/LimitedSpaceService.cs`, `WorkSessionService.cs`, `PersonLimitedSpaceStatus` 枚举 |
| **验证标准** | 1. 5 个状态有明确转换条件<br>2. 超时覆盖所有中间状态<br>3. 状态转换记录时间戳<br>4. 异常状态（卡 Entering）可检测<br>5. 在区人员含 Entering 状态 |
| **复用条件** | 任何需要状态机的业务流程（审批流、作业流、物流跟踪） |

### S11：🔴 重量偏差分级告警

| 属性 | 内容 |
|------|------|
| **名称** | `weight-deviation-classification` |
| **描述** | 三级偏差分类体系：< 5% 正常（绿灯自动通过），5%-10% 警告（黄灯需人工确认），≥10% 严重（红灯强制告警）。同时支持重量识别模式——通过重量唯一识别物资而不需要扫码。分类阈值可配置。 |
| **来源** | `src/LimitedSpaceForeignObject.BLL/Services/WeightService.cs` |
| **验证标准** | 1. 三级分类有明确阈值<br>2. 阈值可配置（非硬编码）<br>3. 警告级需人工确认<br>4. 严重级强制告警<br>5. 支持重量识别模式<br>6. Mock 可配置重量值 |
| **复用条件** | 任何需要传感器数据分级告警的场景（温度、压力、重量、速度等） |

### S12：🟡 SignalR 自适应轮询

| 属性 | 内容 |
|------|------|
| **名称** | `signalr-adaptive-polling` |
| **描述** | `MonitoringBroadcastService` 后台服务向 SignalR Hub 广播实时数据：有活跃会话时 30s 间隔，空闲时 60s 间隔。客户端 `SignalRService` 支持：(1) 多类型消息处理器注册，(2) 断线自动重连，(3) 重连后刷新待处理消息，(4) 连接状态变更事件。 |
| **来源** | `src/LimitedSpaceForeignObject.Api/Services/MonitoringBroadcastService.cs`, `src/LimitedSpaceForeignObject.App/.../Services/SignalRService.cs` |
| **验证标准** | 1. 广播间隔自适应（活跃/空闲）<br>2. 客户端重连自动恢复<br>3. 重连后刷新待处理消息<br>4. 支持多种消息类型<br>5. 连接状态 UI 反馈 |
| **复用条件** | 需要实时数据推送的 Blazor 应用 |

---

## 四、工作流程/治理 Skills

### S13：🔴 偏差检测系统（Deviation Detection System）

| 属性 | 内容 |
|------|------|
| **名称** | `deviation-detection-system` |
| **描述** | 在 AGENTS.md.spec.md（531 行元规范）中定义三级偏差：硬偏差（代码违反铁律→必须立即修复）、软偏差（代码优于文档→建议更新）、演进偏差（技术过时→需评估）。AI 在每次任务中主动检测偏差，逐项向用户确认，不支持批量审批。变更记录在 Git 提交信息中以 `[AGENTS.md]` 标记。支持回滚到修改前状态。 |
| **来源** | `AGENTS.md.spec.md` §偏差检测, `.opencode/skills/spec-md-loader/SKILL.md` |
| **验证标准** | 1. 定义三级偏差分类<br>2. AI 任务开始时主动加载 AGENTS.md<br>3. 输出"已加载：AGENTS.md + 架构总纲 + X.spec.md"<br>4. 偏差逐项审批<br>5. 支持回滚 |
| **复用条件** | 使用 AGENTS.md + spec.md 体系的项目 |

### S14：🔴 spec.md 治理系统（三模式）

| 属性 | 内容 |
|------|------|
| **名称** | `spec-md-governance-three-mode` |
| **描述** | spec-md-loader Skill 定义三种工作模式：(1) REVIEW MODE——5 道防线验证 spec（证据必须来自工具输出、行号要求、矛盾找原文对照、拒绝主观主张、审查与修改分离），(2) ANALYZE MODE——先加载 AGENTS.md + 架构总纲 + 文件 spec.md 再分析，(3) IMPLEMENT MODE——修改前完整检查所有铁律。 |
| **来源** | `.opencode/skills/spec-md-loader/SKILL.md` |
| **验证标准** | 1. 三种模式明确切换规则<br>2. REVIEW MODE 有 5 道防线<br>3. 证据必须有工具输出<br>4. 矛盾必须有原文对照<br>5. 审查和修改分离 |
| **复用条件** | 使用 OpenCode + spec.md 体系的项目 |

### S15：🔴 配置管理 Skill（config-manager）

| 属性 | 内容 |
|------|------|
| **名称** | `config-file-manager-skill` |
| **描述** | OpenCode Skill，管理配置文件的 10 步工作流：(1) 自动扫描项目配置文件，(2) git diff 显示变更，(3) 结构化展示差异，(4) 关联 git blame 作者，(5) 用户逐项确认，(6) 批量授权，(7) 危险操作双重确认，(8) 变更后自动备份，(9) 回滚支持，(10) 提交信息自动生成。包含 6 个 Python 辅助脚本。 |
| **来源** | `.opencode/skills/config-manager/SKILL.md`, `scripts/` |
| **验证标准** | 1. 自动扫描项目配置<br>2. 差异结构化展示<br>3. 危险操作双重确认<br>4. 自动备份和回滚<br>5. 提交信息自动生成 |
| **复用条件** | 使用 OpenCode 且有敏感配置文件的项目 |

### S16：🔴 双推送 Skill（dual-push）

| 属性 | 内容 |
|------|------|
| **名称** | `dual-remote-git-push` |
| **描述** | OpenCode Skill，智能双推送（GitHub + Gitee）：(1) 自动检测未推送提交，(2) 按语义分组（相关文件合并为一个提交），(3) 中文语义化提交信息，(4) Gitee 必须成功策略（失败阻断），(5) 合并提交处理（跳过非 origin 提交），(6) 远程分支自动创建。 |
| **来源** | `.opencode/skills/dual-push/SKILL.md` |
| **验证标准** | 1. 双远程推送<br>2. 提交自动分组<br>3. 语义化中文提交信息<br>4. 关键远程失败阻断<br>5. 远程分支自动创建 |
| **复用条件** | 需要同步推送到 GitHub + Gitee 的项目 |

### S17：🟡 三组搜索列表模式（3-Group Search List）

| 属性 | 内容 |
|------|------|
| **名称** | `three-group-search-list` |
| **描述** | 列表页标准化搜索模式：三个搜索框（如姓名/工号/部门），`@bind:event="oninput"` 实现实时搜索（输入即搜），三个条件 AND 逻辑组合。搜索结果在内存中过滤（不重新请求 API），配合分页组件。 |
| **来源** | `.opencode/skills/list-query-pattern/SKILL.md`, `docs/patterns/ListPageQuery.spec.md` |
| **验证标准** | 1. 三个搜索框 AND 组合<br>2. oninput 实时搜索<br>3. 内存过滤（非 API 重新请求）<br>4. 配合分页<br>5. 空白搜索恢复全部数据 |
| **复用条件** | 任何有列表页的 Blazor/Web 项目 |

---

## 五、部署 Skills

### S18：🟡 跨平台一键部署（Cross-Platform One-Click Deploy）

| 属性 | 内容 |
|------|------|
| **名称** | `cross-platform-one-click-deploy` |
| **描述** | deploy.sh（1000行）/ deploy.ps1（731行）：(1) 检测平台和 .NET SDK 版本，(2) 运行单元测试，(3) build + publish 所有项目（含 win-x86 RID 特殊处理），(4) 内嵌 Python3 生成 6 个 appsettings.json（相对路径），(5) 生成启动/停止脚本，(6) 升级保护（保留数据），(7) 版本追踪（.version JSON），(8) 部署后安全提醒（Auth:SecretKey）。 |
| **来源** | `deploy.sh`, `deploy.ps1` |
| **验证标准** | 1. Linux/Windows 双平台<br>2. 自动运行测试<br>3. 生成完整配置<br>4. 支持升级保留数据<br>5. 部署后可直接运行 |
| **复用条件** | 需要简化部署流程的 .NET 项目（尤其含多个服务进程） |

### S19：🔴 升级保护与回滚（Upgrade Protection & Rollback）

| 属性 | 内容 |
|------|------|
| **名称** | `upgrade-protection-rollback` |
| **描述** | 交互式升级脚本：(1) 检测已有部署，(2) 列出数据目录，(3) 用户选择保留/清理/升级，(4) 备份旧版本，(5) 替换二进制文件，(6) 合并配置，(7) 升级失败时恢复旧版本。版本信息写入 `.version` JSON（安装时间+升级时间+版本号）。 |
| **来源** | `deploy.sh` §升级逻辑, `upgrade.sh`, `.version` 格式 |
| **验证标准** | 1. 升级前备份<br>2. 数据目录可选择保留<br>3. 升级失败可回滚<br>4. 版本信息可追溯<br>5. 交互式确认 |
| **复用条件** | 需要现场升级的本地部署应用 |

---

## 六、AI 辅助开发 Skills（元 Skills）

### S20：🔴 AI Skills 体系设计

| 属性 | 内容 |
|------|------|
| **名称** | `ai-skills-system-design` |
| **描述** | 9 个 OpenCode Skill 文件覆盖：(1) 项目级 Skill（cso-forcs：架构约束、代码风格、工作流），(2) 领域 Skill（cso-forcs-bugs：11种 Bug 模式，cso-forcs-reference：完整参考索引），(3) 工具 Skill（config-manager、dual-push），(4) 治理 Skill（spec-md-loader），(5) 设计 Skill（ui-ux-pro-max：67风格+96色板+57字体+99 UX准则），(6) 模式 Skill（list-query-pattern）。每个 Skill 包含触发条件和执行流程。 |
| **来源** | `.opencode/skills/` 目录 |
| **验证标准** | 1. Skill 有明确的触发条件<br>2. Skill 有结构化执行流程<br>3. 项目级 Skill 覆盖全项目约束<br>4. 领域 Skill 可独立加载<br>5. 工具 Skill 有 Python 脚本辅助 |
| **复用条件** | 使用 OpenCode 的项目，需要 AI 持久化领域知识 |

### S21：🟡 cso-forcs-bugs：Bug 模式知识库

| 属性 | 内容 |
|------|------|
| **名称** | `bug-pattern-knowledge-base` |
| **描述** | 将已知 Bug 模式编码为 AI Skill：(1) Blazor 框架陷阱（rendermode 嵌套、路由参数大小写），(2) 架构陷阱（项目引用混乱、循环依赖），(3) API 陷阱（中间件顺序、JWT 配置），(4) 数据陷阱（WAL 模式、迁移冲突）。每个 Bug 记录现象-根因-修复方案。 |
| **来源** | `.opencode/skills/cso-forcs-bugs/SKILL.md` |
| **验证标准** | 1. 每个 Bug 有现象+根因+修复<br>2. Bug 按类别组织<br>3. AI 在修改相关代码前自动加载<br>4. 新 Bug 及时补充<br>5. 修复方案有代码示例 |
| **复用条件** | 任何需要积累 Bug 知识防止重复踩坑的项目 |

---

## 七、设计 Skills

### S22：🟡 UI/UX 智能设计系统（ui-ux-pro-max）

| 属性 | 内容 |
|------|------|
| **名称** | `ui-ux-design-intelligence` |
| **描述** | 包含 67 种 UI 风格、96 种调色板、57 种字体组合、99 条 UX 准则、25 种图表类型的结构化知识库。覆盖 13 个技术栈（React/Next.js/Vue/Svelte/Blazor 等）。AI 根据项目描述推荐设计方向，生成品牌色板和应用方案。 |
| **来源** | `.opencode/skills/ui-ux-pro-max/SKILL.md`, `data/` CSV 文件 |
| **验证标准** | 1. 知识库 CSV 可查询<br>2. 支持按技术栈筛选<br>3. AI 推荐有依据<br>4. 生成品牌色板可落地 |
| **复用条件** | 需要 AI 辅助 UI/UX 设计的项目 |

---

## CSO-FORCS Skills 总结表

| 序号 | 分类 | Skill 名称 | 原创度 | 可单独复用 |
|------|------|-----------|:---:|:---:|
| S1 | 架构 | 双子系统独立部署 | 🔴 | ✅ |
| S2 | 架构 | HAL + 三实现模式 | 🔴 | ✅ |
| S3 | 架构 | 32位微服务隔离 | 🔴 | ✅ (特定场景) |
| S4 | 架构 | 三大系统边界隔离 | 🟡 | ✅ |
| S5 | 架构 | 进程编排器 | 🔴 | ✅ |
| S6 | 架构 | 统一配置层 | 🔴 | ✅ |
| S7 | UI/交互 | 双屏 Kiosk + 协调器 | 🔴 | ✅ (工业场景) |
| S8 | UI/交互 | Kiosk 自启动部署 | 🔴 | ✅ (工业场景) |
| S9 | 编码 | 人脸识别流水线 | 🟡 | ✅ (AI 场景) |
| S10 | 编码 | 作业状态机 | 🔴 | ✅ |
| S11 | 编码 | 重量偏差分级告警 | 🔴 | ✅ |
| S12 | 编码 | SignalR 自适应轮询 | 🟡 | ✅ |
| S13 | 治理 | 偏差检测系统 | 🔴 | ✅ (spec.md 体系) |
| S14 | 治理 | spec.md 三模式治理 | 🔴 | ✅ (spec.md 体系) |
| S15 | 治理 | 配置管理 Skill | 🔴 | ✅ (OpenCode) |
| S16 | 治理 | 双推送 Skill | 🔴 | ✅ (双远程) |
| S17 | 编码 | 三组搜索列表 | 🟡 | ✅ |
| S18 | 部署 | 跨平台一键部署 | 🟡 | ✅ |
| S19 | 部署 | 升级保护与回滚 | 🔴 | ✅ |
| S20 | AI开发 | AI Skills 体系设计 | 🔴 | ✅ (OpenCode) |
| S21 | AI开发 | Bug 模式知识库 | 🟡 | ✅ |
| S22 | 设计 | UI/UX 智能设计 | 🟡 | ✅ (AI 辅助设计) |

**原创度统计**：🔴 原创 14 / 🟡 创新应用 8 / 🟢 工业标准 0

---

*文档生成时间：2026-06-18*
*数据来源：CSO-FORCS 项目深度分析*
