# WarehouseMS 架构：目的、结构、依赖关系

> 哈电重装库房物资管理系统，C# / .NET 10 + Blazor Web App + SQLite，三大子系统。

---

## 架构全景图

```
┌─────────────────────────────────────────────────────────────┐
│                    【前端层 — Blazor】                        │
│                                                             │
│  WarehouseManagement.Web (Server)                            │
│  ├─ InteractiveServer RenderMode                            │
│  ├─ MudBlazor 8.x 组件库                                    │
│  ├─ 哈电品牌设计系统 (design-system/)                        │
│  ├─ 人脸识别/刷卡/密码 三重身份验证                          │
│  └─ 依赖: Core + Shared + Web.Client                        │
│                                                             │
│  WarehouseManagement.Web.Client (Wasm)                       │
│  └─ 浏览器端交互组件                                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│              【Core 层 — 业务逻辑 + 服务】                    │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐      │
│  │ 库房管理系统  │  │ 磨料效率折算   │  │ 工时录入系统   │      │
│  │ MaterialSvc  │  │ EfficiencySvc │  │ WorkHourSvc   │      │
│  │ StockOutSvc  │  │ ConversionEng │  │ AuditSvc      │      │
│  │ ImportSvc    │  │ WorkloadSvc   │  │               │      │
│  └─────────────┘  └──────────────┘  └───────────────┘      │
│                                                             │
│  三大子系统铁律：Service 层禁止互相调用                       │
│  跨系统数据聚合仅限 Web 层看板页面                           │
│                                                             │
│  依赖: Infrastructure + Shared                              │
│  能力: BCrypt / ClosedXML(Excel) / ONNX(人脸) / ImageSharp  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│            【Infrastructure 层 — 数据访问】                   │
│                                                             │
│  EF Core DbContext / Repository / Migrations                 │
│  SQLite (开发) → SQL Server 2022 (生产可迁移)                │
│  ASP.NET Core Identity (用户/角色)                           │
│                                                             │
│  依赖: Shared                                               │
│  红线: Core 不直接操作 DbContext，通过 Repository            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│            【Shared 层 — 纯数据定义】（0 依赖）               │
│                                                             │
│  Entity / DTO / Enum / 常量                                  │
│  被 Infrastructure / Core / Web 共同引用                     │
│  红线: 绝不引用任何其他项目                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 每层存在的目的（为什么需要这一层？）

### 1. Shared 层 — "数据定义的唯一来源"（0 依赖）

| 维度 | 内容 |
|------|------|
| **目的** | 定义整个系统的实体结构、传输对象、枚举常量。 |
| **为什么独立** | 四层项目（Infrastructure/Core/Web/Web.Client）都需要访问相同的 Entity 定义。如果不独立，每个项目各自定义 → 类型不兼容 → 反复转换 → 维护噩梦。 |
| **对比 CSO-FORCS** | 完全相同的设计理念。CSO-FORCS 的 Models 就是 WarehouseMS 的 Shared。 |

### 2. Infrastructure 层 — "数据访问封装"（仅依赖 Shared）

| 维度 | 内容 |
|------|------|
| **目的** | 封装所有数据库操作：DbContext、Repository 实现、EF Core 迁移、Identity 框架集成。 |
| **为什么独立** | Core 层不应该知道"数据存在 SQLite 还是 SQL Server"。换数据库时只改 Infrastructure，不改业务逻辑。 |
| **设计决策** | 使用 Repository 模式——Core 层通过 IRepository 接口操作数据，而非直接操作 DbContext。这比 CSO-FORCS 更严格（CSO-FORCS 允许 BLL 在跨仓储查询时直接注入 AppDbContext）。 |

### 3. Core 层 — "三大子系统中枢"（依赖 Infrastructure + Shared）

| 维度 | 内容 |
|------|------|
| **目的** | 实现所有业务规则。这是项目中"最值钱"的层。 |
| **三大子系统**： |

| 子系统 | 核心 Service | 职责 |
|--------|-------------|------|
| 库房管理系统 | MaterialCategoryService, StockOutService, ImportService | 物资三级分类、入库/领用/回收、Excel 导入 |
| 磨料效率折算 | MaterialEfficiencyService, IConversionEngine, WorkloadService | 砂轮片折算（规格×材质×类型匹配）、效率排名、完成率 |
| 工时录入系统 | WorkHourService, WorkHourAuditService | 工时记录（实际工时×难度系数）、审核流程 |

| **子系统边界铁律**： |
| - `MaterialCategoryService` 禁止调用 `IConversionEngine`（分类不承载折算） |
| - `WorkHourService` 禁止调用 `IConversionEngine`（工时不调用折算） |
| - `WorkloadService` 禁止写入 `StockOut/StockRecycle`（效率系统只读库房数据） |
| - 跨系统数据聚合**仅限 Web 层看板页面** |

**为什么需要三大子系统边界**：库房管理、效率折算、工时录入是三个完全不同的业务领域。如果 Service 层允许互相调用，一个领域的修改会连锁影响其他领域，导致"改一处崩三处"。web 层做数据聚合是一种妥协——看板需要跨数据源展示，但不得让 Service 产生耦合。

**核心业务规则——四层匹配**：这是 WarehouseMS 独有的业务复杂度。发放砂轮片必须校验：
```
项目 → 执行标准 → 打磨对象 → 允许的砂轮片材质
```
例如：廉江项目（AP1000 标准）下，打磨不锈钢 → 只能用铝基无铁砂轮片。如果用碳化硅打磨不锈钢 → 效率极低、工件不合格。这条规则不是"编码规范"，而是"物理规律"——错一次就是生产事故。

### 4. Web 层 — "三大系统看板 + 前端入口"（依赖 Core + Shared + Web.Client）

| 维度 | 内容 |
|------|------|
| **目的** | 提供所有用户界面，包括库房管理、效率看板、工时录入、系统设置。 |
| **技术栈** | Blazor Web App（InteractiveServer）+ MudBlazor 8.x + 哈电品牌设计系统。 |
| **身份验证** | 三种方式：刷卡（RFID/IC卡）/ 用户名+密码 / 人脸识别（ONNX 模型）。 |

| **Blazor 组件红线**： |
| - 代码后置 `Xxx.razor` + `Xxx.razor.cs` |
| - 样式隔离 `Xxx.razor.css` |
| - 全局 rendermode：App.razor 设定，页面禁止重复设置 |
| - 不许在 `.razor` 中写 `<style>` 块或复杂 C# 逻辑 |
| - 不许直接 new HttpClient，必须通过 DI 注入的 Service |

### 5. Web.Client 层 — "浏览器端交互组件"

| 维度 | 内容 |
|------|------|
| **目的** | 承载需要浏览器端运行的 Blazor 交互组件（WebAssembly）。 |
| **价值** | 某些交互（如摄像头拍照、本地计算）在 Server 端运行延迟高，Wasm 模式提供更好的用户体验。 |

---

## 依赖方向总图（单向无环）

```
                        Web
                      (Server)
                    ┌───┼───┐
                    │   │   │
                    ▼   ▼   │
                  Core  Shared│
                  │           │
                  ▼           │
              Infrastructure  │
                  │           │
                  ▼           │
                Shared ◄──────┘
                  ▲
                  │
              Web.Client

方向: Web → Core → Infrastructure → Shared
Shared ← 零依赖（最底层）
Web.Client ← 引用 Shared 和 Web 类型
```

**与 CSO-FORCS 的关键差异**：
- CSO-FORCS: 14 个项目 / 9 个逻辑层 / 独立的 Configuration 和 HAL 层
- WarehouseMS: 5 个项目 / 4 个逻辑层 / 更精简的架构，无独立 Configuration 层
- WarehouseMS 使用 Repository 模式，比 CSO-FORCS 的数据访问更严格
- WarehouseMS 的三大子系统边界通过"Service 层禁止互调"来实现，而 CSO-FORCS 的子系统边界通过物理拆分（独立的 Api/App 项目）来实现

---

**分析时间**: 2026-06-17
**数据来源**: 5个 .csproj 文件、架构总纲.spec.md、design-system/MASTER.md
