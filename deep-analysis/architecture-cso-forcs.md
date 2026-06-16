# CSO-FORCS 架构：目的、结构、依赖关系

> 有限空间作业外来物控制系统 + 库房管理系统，C# / .NET 10，双子系统架构。
> 这个架构是多人多次迭代的结果，每层都有明确的"为什么存在"。

---

## 架构全景图（依赖方向）

```
                          ┌─────────────────────────────────────────┐
                          │           【前端层 — Blazor】             │
                          │   主系统 App           库房系统 App       │
                          │   (InteractiveServer)   (InteractiveServer)│
                          │   + App.Client          + Warehouse.     │
                          │     (Wasm)                App.Client     │
                          └──────┬──────────────────────┬───────────┘
                                 │ HTTP/HttpClient       │ HTTP
                                 │ (绝不引用BLL/DAL!)     │
              ┌──────────────────┼──────────────────────┼──────────────┐
              │                  ▼                      ▼              │
              │        【API 层 — REST Controllers】                    │
              │    主系统 Api           库房系统 Warehouse.Api          │
              │    (JWT Auth, 人员/监控)   (物资/审批/借用)             │
              │    ┌──────────────────────────────────────────────┐    │
              │    │      依赖: BLL + DAL + Models + Configuration  │    │
              │    └──────────────────────────────────────────────┘    │
              │                  │                                     │
              ├──────────────────┼─────────────────────────────────────┤
              │                  ▼                                     │
              │        【BLL 层 — 业务逻辑】                            │
              │    Services (人员管理/称重比对/监控分析)                 │
              │    ONNX 人脸识别模型 / JWT / BCrypt                     │
              │    ┌─────────────────────────────────────────┐         │
              │    │  依赖: DAL + Models + HAL                │         │
              │    │  红线: 不含 Controller 逻辑              │         │
              │    └─────────────────────────────────────────┘         │
              │        │              │              │                 │
              │        ▼              ▼              ▼                 │
              │   【DAL 层】    【HAL 层】      【CardReader】           │
              │   EF Core     硬件抽象层        Windows Only(x86)       │
              │   SQLite      二维码/图像处理   刷卡器/IC卡             │
              │   依赖:        依赖: Models     依赖: HAL+Configuration │
              │   Models+Config                 + hfrdapi.dll           │
              │        │              │                                 │
              │        └──────┬───────┘                                 │
              │               ▼                                         │
              │        【Models 层 — 纯 POCO】                          │
              │    Entity / DTO / Enum / Request / Response             │
              │    零引用，被所有上层引用（项目根基）                     │
              │                                                         │
              └─────────────────────────────────────────────────────────┘

                                【Configuration 层 — 统一配置】
                                  Serilog / HttpClient / Options
                                  依赖: ServiceDefaults
                                  被 DAL / Api / App / CardReader 引用
                                  红线: 绝不引用任何业务项目
```

---

## 每层存在的目的（为什么需要这一层？）

### 1. Models 层 — "纯数据定义"（0 依赖）

| 维度 | 内容 |
|------|------|
| **目的** | 定义整个系统的数据形状。Entity（数据库映射）、DTO（传输对象）、Enum（枚举）、Request/Response（API 契约）都在这里。 |
| **为什么独立** | 避免"循环引用"。如果 Models 引用任何其他项目，上层项目在引用 Models 时会间接引入不必要的依赖。 |
| **解决的问题** | 如果 Entity 定义和业务逻辑混在一起，修改 Entity 可能触发业务逻辑变更——违反了单一职责。 |
| **类比** | 建筑的"地基标准"——所有上层结构都建立在它之上，但它不关心上层是什么。 |

### 2. Configuration 层 — "基础设施统一"（仅依赖 ServiceDefaults）

| 维度 | 内容 |
|------|------|
| **目的** | 统一管理日志（Serilog）、HTTP 客户端（IHttpClientFactory）、配置（appsettings）三大基础设施。 |
| **为什么独立** | 防止"7处硬编码 localhost"。每个项目不再各自配置，而是调用 `AddCsoForcsConfiguration()` 一次性完成。 |
| **解决的问题** | 踩过的坑：全项目硬编码端口号、各自独立配置日志、配置连接字符串格式不统一。 |
| **红线** | Configuration 绝不引用任何业务项目。一旦反了，DAL 引用 Configuration → Configuration 引用 DAL → 循环依赖。 |

### 3. DAL 层 — "数据访问封装"（依赖 Models + Configuration）

| 维度 | 内容 |
|------|------|
| **目的** | 封装所有数据库操作（EF Core DbContext、Migrations、查询）。上层不应关心"数据存在 SQLite 还是 SQL Server"。 |
| **为什么独立** | 如果 BLL 直接操作 EF Core，切换数据库（如开发 SQLite → 生产 SQL Server）需要改动 BLL 层所有代码。 |
| **依赖** | 引用 Models（知道实体结构）+ Configuration（读数据库连接串）。 |

### 4. HAL 层 — "硬件抽象"（仅依赖 Models）

| 维度 | 内容 |
|------|------|
| **目的** | 封装所有硬件相关操作：二维码生成/识别、图像处理、打印、ONNX 模型调用。 |
| **为什么独立** | CSO-FORCS 部署在工业环境中，需要接二维码扫描枪、摄像头、打印机。如果硬件逻辑散布在 BLL 中，换一种扫码设备就要改业务代码。 |
| **核心价值** | "上层代码不知道底层是接的哪个厂商的扫码枪"。 |
| **依赖** | 仅引用 Models（处理实体 DTO），不依赖 DAL 或 Configuration。 |

### 5. BLL 层 — "业务逻辑中枢"（依赖 DAL + Models + HAL）

| 维度 | 内容 |
|------|------|
| **目的** | 实现所有业务规则：人员进出逻辑、称重比对算法、监控异常检测、人脸识别流程、JWT 认证。 |
| **为什么独立** | 业务规则是系统中"最值钱"的部分，也是最常变更的部分。独立后，修改业务规则不影响 API 接口签名或前端展示。 |
| **依赖** | DAL（读/写数据）+ HAL（调用硬件功能）+ Models（操作实体）。 |
| **设计特性** | BLL 中包含 ONNX 运行时（人脸识别模型），这是 CSO-FORCS 特有的工业场景需求。 |

### 6. 双子系统 API 层

| 子系统 | API 项目 | 职责 |
|--------|---------|------|
| **主系统** | `LimitedSpaceForeignObject.Api` | 人员进出管理、物品核对、称重比对、监控告警 |
| **库房系统** | `LimitedSpaceForeignObject.Warehouse.Api` | 物资借用申请/审批、归还确认、报废登记 |

**为什么双 API**：两个系统的业务领域完全不同。主系统关注"安全"（人进人出、物品核对），库房系统关注"资产"（库存、审批流）。独立部署允许独立扩缩容和独立维护。

### 7. 双子系统 App 层（Blazor 前端）

| 项目 | 职责 | 关键约束 |
|------|------|----------|
| `App` (Server) | 主系统 Blazor 前端，InteractiveServer | 不引用 BLL/DAL，通过 HttpClient 调 API |
| `App.Client` (Wasm) | 主系统客户端 WebAssembly | 交互组件运行在浏览器 |
| `Warehouse.App` (Server) | 库房系统 Blazor 前端 | 不引用任何后端项目 |
| `Warehouse.App.Client` (Wasm) | 库房系统客户端 WebAssembly | — |

**关键设计决策**：Blazor Web App 使用 Server/Client 分离模式。Server 端负责渲染和 API 调用，Client 端负责交互组件。App 项目**绝不能**引用 BLL 或 DAL，这是架构红线——来自"直接调 EF Core 导致依赖混乱"的血的教训。

### 8. CardReader — "Windows 专属硬件集成"

| 维度 | 内容 |
|------|------|
| **目的** | 集成 IC 卡读卡器硬件。依赖 Windows 原生 DLL（hfrdapi.dll, BcHidDevice.dll），编译为 win-x86。 |
| **为什么独立** | 读卡器硬件 API 是平台绑定的，不能跨平台。独立项目防止硬件依赖"污染"跨平台的主系统代码。 |
| **依赖** | HAL（二维码/图像）+ Configuration（配置）。 |

### 9. Launcher — "桌面启动器"

| 维度 | 内容 |
|------|------|
| **目的** | 提供一个桌面应用程序入口，统一启动主系统和库房系统。 |
| **价值** | 工业场景中，操作员不应该关心"如何启动服务"——一键启动。 |

---

## 架构演化：为什么是现在这个样子？

```
v1.0 — 最初的设计：
  Models → DAL → BLL → Api → App
  简单五层，看起来"标准"

v2.0 — 踩坑后演进：
  加入了 Configuration 层（因为硬编码端口号导致部署失败）
  加入了 HAL 层（因为硬件调用散落各处，换设备就改不动）
  加入了 CardReader 项目（因为 Windows DLL 污染了跨平台代码）
  拆分了双子系统（因为主系统和库房系统耦合导致互相影响）

v3.0 — 当前状态：
  14 个项目 / 9 个逻辑层 / 双子系统 / Blazor WebAssembly 分离
```

**架构的核心教训**：v1.0 的"标准分层"在工业场景下不够。Configuration 和 HAL 两层是"被逼出来的"——没有它们就会重复踩坑。CardReader 独立项目是"被逼出来的"——平台绑定代码不能让整个解决方案降级为 Windows Only。

---

## 依赖方向总图（单向无环）

```
                    Launcher
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   主系统 App    库房系统 App    CardReader
        │              │              │
        │ HTTP         │ HTTP         │
        ▼              ▼              │
   主系统 Api    库房系统 Api          │
        │              │              │
        └──────┬───────┘              │
               ▼                      │
             BLL                      │
          ┌───┼───┐                   │
          ▼   ▼   ▼                   │
        DAL  HAL  ←───────────────────┘
         │    │
         ▼    ▼
      Config  Models

方向: 上层 → 下层 (单向依赖，禁止反向)
Models ← 零依赖（最底层）
Config ← 仅依赖 ServiceDefaults
```

---

**分析时间**: 2026-06-17
**数据来源**: 14个 .csproj 文件、架构总纲.spec.md、开源项目结构
