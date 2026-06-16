# 模板6：WarehouseMS 可提取的 Skills 清单

> 本文档基于对 WarehouseMS 项目的深度分析，提取可复用的开发 Skills。
> 每个 Skill 包含：名称、描述、来源、验证标准、可复用性评估。

---

## 一、架构 Skills

### Skill 1：四层分层架构（Clean Layered Architecture）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `four-layer-architecture` |
| **描述** | 采用 Shared → Infrastructure → Core → Web 四层架构，每层职责明确：Shared 为纯数据定义层（无依赖），Infrastructure 为数据访问层，Core 为业务逻辑层，Web 为前端展示层。层间依赖严格单向，禁止循环引用。 |
| **来源** | `src/WarehouseManagement.Shared/`, `src/WarehouseManagement.Infrastructure/`, `src/WarehouseManagement.Core/`, `src/WarehouseManagement.Web/`, `AGENTS.md` §二, `架构总纲.spec.md` §3 |
| **验证标准** | 1. Shared 项目不引用任何其他项目<br>2. Infrastructure 仅引用 Shared<br>3. Core 引用 Infrastructure 和 Shared<br>4. Web 引用 Core 和 Shared<br>5. Web 层不直接操作 DbContext<br>6. Core 层不直接操作 DbContext（通过 Repository） |
| **可复用性评估** | **高** — 适用于所有中大型 .NET 项目。四层架构比三层更清晰地分离了数据访问和业务逻辑，便于单元测试和数据源替换。 |

### Skill 2：仓储模式 + 工作单元（Repository + Unit of Work）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `repository-uow-pattern` |
| **描述** | 通用 `IRepository<T>` 接口封装 CRUD 操作，专属仓储扩展复杂查询。`IUnitOfWork` 统一提交变更，保证跨仓储操作在同一事务中。Repository 不包含 SaveChanges，确保多步操作的事务一致性。 |
| **来源** | `src/WarehouseManagement.Infrastructure/Repositories/IRepository.cs`, `Repository.cs`, `IUnitOfWork.cs`, `UnitOfWork.cs`, 6 个专属仓储实现 |
| **验证标准** | 1. 通用 Repository 包含 GetByIdAsync/ListAsync/AddAsync/Update/SoftDelete<br>2. 专属 Repository 继承通用 Repository 并扩展业务查询<br>3. UnitOfWork 仅暴露 SaveChangesAsync<br>4. Service 层通过构造函数注入 Repository 和 UnitOfWork<br>5. 所有 SaveChanges 通过 UnitOfWork 调用 |
| **可复用性评估** | **高** — 经典的 DDD 模式，适用于所有使用 EF Core 的项目。通用 Repository 减少样板代码，专属 Repository 保持查询灵活性。 |

### Skill 3：依赖注入集中注册（Centralized DI Registration）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `centralized-di-registration` |
| **描述** | 每层提供 `DependencyInjection.cs` 扩展方法（如 `AddWarehouseCore()`、`AddWarehouseInfrastructure(connectionString)`），Web 层 Program.cs 一行调用即可注册整层服务。服务生命周期统一使用 `AddScoped`。 |
| **来源** | `src/WarehouseManagement.Core/DependencyInjection.cs`, `src/WarehouseManagement.Infrastructure/DependencyInjection.cs`, `src/WarehouseManagement.Web/Program.cs` |
| **验证标准** | 1. 每层有独立的 `DependencyInjection.cs` 静态类<br>2. 扩展方法返回 `IServiceCollection` 支持链式调用<br>3. 所有服务使用 `AddScoped`（Blazor InteractiveServer 场景）<br>4. 新增服务后必须在 DI 文件中注册<br>5. 注册语句按字母序排列 |
| **可复用性评估** | **高** — 适用于所有 ASP.NET Core 项目。集中注册便于管理服务依赖，避免遗漏注册导致运行时错误。 |

### Skill 4：三大系统边界隔离（System Boundary Isolation）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `system-boundary-isolation` |
| **描述** | 项目拆分为三个独立子系统（库房管理/效率折算/工时录入），在 Service 层禁止互相调用。跨系统数据聚合仅在 Web 层（看板页面）进行。每个系统有独立的 Service 和 Repository。 |
| **来源** | `AGENTS.md` §一, `架构总纲.spec.md` §0, `docs/系统架构-三大系统边界.md` |
| **验证标准** | 1. MaterialCategoryService 不调用 IConversionEngine<br>2. WorkHourService 不调用 IConversionEngine<br>3. WorkloadService 只读库房数据，不写入<br>4. 跨系统聚合仅在 Web 层进行<br>5. Service 层无跨系统服务注入 |
| **可复用性评估** | **中高** — 适用于业务域复杂的项目。需要项目本身有清晰的业务边界划分，不适合小型单体应用。 |

### Skill 5：策略模式驱动业务扩展（Strategy Pattern for Business Extension）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `strategy-pattern-extension` |
| **描述** | 物资消耗计算采用策略模式，通过 `IMaterialConsumptionStrategy` 接口定义计算契约，`IMaterialConsumptionStrategyFactory` 根据物资类型和配置选择策略实现。支持通过配置而非代码修改扩展新物资类型。 |
| **来源** | `src/WarehouseManagement.Core/Interfaces/IMaterialConsumptionStrategy.cs`, `IMaterialConsumptionStrategyFactory.cs`, `Services/WorkloadService.cs` |
| **验证标准** | 1. 定义策略接口（IMaterialConsumptionStrategy）<br>2. 工厂类根据配置选择策略实现<br>3. 新增物资类型只需新增策略实现类 + 配置记录<br>4. 策略通过 DI 注册为 Scoped<br>5. 业务服务通过工厂获取策略，不直接依赖具体实现 |
| **可复用性评估** | **高** — 适用于需要可扩展业务规则的场景。配置驱动而非代码修改，降低维护成本。 |

---

## 二、编码 Skills

### Skill 6：统一命名约定（Unified Naming Conventions）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `unified-naming-conventions` |
| **描述** | 严格的 C# 命名约定：Namespace/Class/Method/Property 使用 PascalCase，Interface 加 `I` 前缀，Private Field 使用 `_camelCase`，数据库表名 PascalCase 复数，列名 camelCase。 |
| **来源** | `AGENTS.md` §四, `架构总纲.spec.md` §4 |
| **验证标准** | 1. 类名 PascalCase：`WorkloadService`<br>2. 接口 I 前缀：`IWorkloadService`<br>3. 私有字段 `_camelCase`：`_dbContext`<br>4. 数据库表名复数：`Materials`, `WorkHours`<br>5. 数据库列名 camelCase：`createdAt`, `materialId`<br>6. 异步方法 Async 后缀：`CalculateWorkloadAsync` |
| **可复用性评估** | **高** — .NET 社区标准约定，适用于所有 C# 项目。可配合 .editorconfig 和 StyleCop 自动化检查。 |

### Skill 7：Result 模式替代异常（Result Pattern for Business Errors）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `result-pattern-business-errors` |
| **描述** | Service 层使用 `Result<T>` 包装返回值（IsSuccess/Value/Error/ErrorCode），替代抛业务异常。Web/UI 拿到结构化的成功/失败反馈，避免到处 try/catch。真正的不可恢复错误（如数据库不可用）仍允许抛异常。 |
| **来源** | `src/WarehouseManagement.Core/Common/Result.cs`, `Services/MaterialService.cs`, `Services/StockInService.cs` |
| **验证标准** | 1. Service 方法返回 `Result<T>` 或 `Result`<br>2. 成功时 `Result.Success(value)`<br>3. 失败时 `Result.Failure("错误消息", "ERROR_CODE")`<br>4. ErrorCode 使用 UPPER_SNAKE_CASE 格式<br>5. Web 层检查 `IsSuccess` 决定显示成功/错误<br>6. 仅用于业务校验错误，不用于系统级异常 |
| **可复用性评估** | **高** — 适用于所有需要清晰错误处理的 Service 层。比异常更轻量，比 tuple 更结构化。 |

### Skill 8：结构化日志规范（Structured Logging）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `structured-logging` |
| **描述** | 使用 Serilog 结构化日志，日志消息使用占位符 `{PropertyName}` 格式（非字符串插值），便于日志聚合和查询。Service 层关键操作（创建/更新/删除）必须记录 Info 级别日志。 |
| **来源** | `AGENTS.md` §四, `src/WarehouseManagement.Core/Services/MaterialService.cs`, `src/WarehouseManagement.Web/Program.cs` |
| **验证标准** | 1. 使用 `ILogger<T>` 注入，非静态 Logger<br>2. 日志消息使用 `{占位符}` 格式：`Log.Information("创建：Id={Id}", id)`<br>3. 异常日志使用 `Log.Error(ex, "消息", 参数)`<br>4. 关键业务操作记录 Info 级别<br>5. Serilog 配置从 appsettings.json 读取<br>6. 日志输出包含结构化属性（便于查询） |
| **可复用性评估** | **高** — 适用于所有生产级应用。结构化日志是现代 .NET 应用的标准实践。 |

### Skill 9：实体审计基类（Auditable Entity Base Class）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `auditable-entity-base` |
| **描述** | 所有业务实体继承 `AuditableEntity` 基类，包含 Id/CreatedAt/UpdatedAt/IsDeleted 字段。`AuditFieldsInterceptor` 拦截器自动填充 CreatedAt/UpdatedAt（UTC），避免 Service 层重复手填。配合 EF Core 全局查询过滤器实现软删除。 |
| **来源** | `src/WarehouseManagement.Shared/Entities/AuditableEntity.cs`, `src/WarehouseManagement.Infrastructure/Interceptors/AuditFieldsInterceptor.cs`, `src/WarehouseManagement.Infrastructure/Data/AppDbContext.cs` |
| **验证标准** | 1. 所有业务实体继承 `AuditableEntity`<br>2. CreatedAt/UpdatedAt 由拦截器自动填充（UTC 时间）<br>3. IsDeleted 配合全局查询过滤器 `HasQueryFilter(e => !e.IsDeleted)`<br>4. 物理删除被禁止（软删除）<br>5. Modified 状态下 CreatedAt 标记为 IsModified=false |
| **可复用性评估** | **高** — 适用于所有需要审计追踪的业务系统。自动填充减少人为遗漏，软删除保护数据安全。 |

### Skill 10：Blazor 组件代码后置（Blazor Code-Behind Pattern）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `blazor-code-behind` |
| **描述** | Blazor 页面采用代码后置模式：`.razor` 文件仅包含 UI 模板，`.razor.cs` 包含 C# 逻辑，`.razor.css` 包含隔离样式。禁止在 `.razor` 文件中写复杂 C# 逻辑或 `<style>` 块。 |
| **来源** | `AGENTS.md` §五, `架构总纲.spec.md` §4 |
| **验证标准** | 1. 每个页面有对应的 `.razor.cs` 代码后置文件<br>2. `.razor` 文件中无复杂 C# 逻辑（仅有 @inject/@page/@using）<br>3. 样式使用 `.razor.css` 隔离文件<br>4. 页面组件不添加 `@rendermode`（全局已设置）<br>5. 所有 Service 通过 `@inject` 注入 |
| **可复用性评估** | **高** — 适用于所有 Blazor 项目。代码后置提高可维护性，便于 AI 和人类分别处理 UI 和逻辑。 |

### Skill 11：EF Core Provider 中立设计（Database Provider Agnostic）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `db-provider-agnostic` |
| **描述** | DbContext 保持 Provider 中立设计，开发期使用 SQLite（零依赖），生产期可切换 SQL Server。切换仅需修改 Program.cs 中的 `UseSqlite` → `UseSqlServer`，无需修改 DbContext 或 Repository 代码。 |
| **来源** | `AGENTS.md` §十, `src/WarehouseManagement.Web/Program.cs` |
| **验证标准** | 1. DbContext 不包含 Provider 特定代码<br>2. 连接字符串从配置读取<br>3. 切换 Provider 仅需修改 Program.cs<br>4. 使用 EF Core 标准 API（避免 Provider 特定扩展）<br>5. 迁移文件可在目标 Provider 上生成 |
| **可复用性评估** | **中高** — 适用于需要灵活部署的项目。SQLite 零依赖便于开发和 CI，生产切换 SQL Server 获得更好性能。 |

### Skill 12：系数快照模式（Coefficient Snapshot Pattern）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `coefficient-snapshot` |
| **描述** | 业务系数（如规格系数、材质系数）在领用时快照记录到 StockOut 中，而非引用实时配置。修改系数配置不影响历史记录，保证数据可追溯性。 |
| **来源** | `src/WarehouseManagement.Shared/Entities/StockOut.cs`, `架构总纲.spec.md` |
| **验证标准** | 1. 业务记录包含系数快照字段（SpecCoeff, MaterialCoeff）<br>2. 创建记录时从配置表读取系数并复制到快照字段<br>3. 修改配置不影响历史记录<br>4. 统计计算使用快照值而非实时配置<br>5. 快照字段标记为不可修改 |
| **可复用性评估** | **高** — 适用于所有需要数据可追溯性的业务系统。价格、税率、汇率等场景均可应用。 |

---

## 三、工作流程 Skills

### Skill 13：Spec.md 约定文件体系（Spec.md Convention System）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `spec-md-convention` |
| **描述** | 每个代码文件对应一个 `.spec.md` 约定文件，记录：文件用途、踩过的坑、禁止修改的内容、技术规范、允许的操作、当前状态。修改代码前必须阅读 spec.md，修改后必须询问是否更新。使用 `spec_md_manager.py` 工具管理覆盖度。 |
| **来源** | `AGENTS.md` §七, `tools/spec_md_manager.py`, 100+ 个 `.spec.md` 文件 |
| **验证标准** | 1. 每个 `.cs`/`.razor` 文件有对应 `.spec.md`<br>2. 修改代码前必须检查并阅读 spec.md<br>3. spec.md 包含 6 个标准章节<br>4. 新增文件后必须提议创建 spec.md<br>5. 使用 `python3 tools/spec_md_manager.py report` 检查覆盖度<br>6. 覆盖度 ≥ 80% |
| **可复用性评估** | **高** — 适用于所有需要 AI 辅助开发的项目。spec.md 是 AI 的"记忆文件"，防止 AI 重复犯错或违反约束。 |

### Skill 14：验证清单模式（Verification Checklist Pattern）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `verification-checklist` |
| **描述** | 每个开发阶段结束时，执行标准化验证清单：编译（0 警告 0 错误）、测试（全部通过）、功能验证（各页面 HTTP 200）、日志验证（文件输出正常）、spec 覆盖度检查。 |
| **来源** | `DEVELOP.md` 各阶段验证清单 |
| **验证标准** | 1. 每个开发阶段有对应的验证清单<br>2. 验证项包含：编译/测试/启动/功能/日志<br>3. 所有验证项必须通过才能进入下一阶段<br>4. 验证结果记录在开发日志中<br>5. 使用命令行工具自动化验证（dotnet build/test/run） |
| **可复用性评估** | **高** — 适用于所有项目。验证清单是质量门禁的基础，防止"开发完成但无法运行"的情况。 |

### Skill 15：开发日志记录（Development Worklog）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `development-worklog` |
| **描述** | 使用 `DEVELOP.md` 记录每个开发阶段的详细日志：已完成任务、关键决策、Bug 修复、验证清单。每个阶段有明确的日期标记和任务边界。 |
| **来源** | `DEVELOP.md`, `notes/` 目录 |
| **验证标准** | 1. 每个开发阶段有对应的日志条目<br>2. 包含：日期、任务描述、已完成项、关键决策、验证结果<br>3. Bug 修复记录根因和解决方案<br>4. 关键决策记录理由<br>5. 日志按时间倒序排列 |
| **可复用性评估** | **中高** — 适用于需要可追溯性的项目。开发日志帮助团队成员理解历史决策，便于知识传递。 |

---

## 四、测试 Skills

### Skill 16：SQLite 内存数据库测试基类（SQLite In-Memory Test Base）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `sqlite-memory-test-base` |
| **描述** | 测试基类 `ServiceTestBase` 使用 SQLite 内存数据库 + 真实拦截器，最大限度逼近生产环境（包括 unique index、cascade、软删除过滤器、AuditFields）。每个测试用例独立数据库连接，自动 Dispose。 |
| **来源** | `tests/WarehouseManagement.Tests/Common/ServiceTestBase.cs` |
| **验证标准** | 1. 测试基类创建 SQLite 内存连接（`:memory:`）<br>2. 使用 `EnsureCreated()` 创建 schema<br>3. 包含真实拦截器（AuditFieldsInterceptor）<br>4. 提供 `UnitOfWork` 和 `Db` 属性<br>5. 实现 `IDisposable` 自动清理<br>6. 提供 `NullLogger<T>` 避免日志干扰 |
| **可复用性评估** | **高** — 适用于所有使用 EF Core 的项目。SQLite 内存数据库比 InMemory Provider 更接近真实数据库行为（支持约束、索引等）。 |

### Skill 17：冒烟测试先行（Smoke Tests First）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `smoke-tests-first` |
| **描述** | 项目初始化阶段优先编写冒烟测试，验证基础设施能正常工作：实体增查、软删除过滤器、审计字段自动填充。冒烟测试作为后续业务测试的基线。 |
| **来源** | `tests/WarehouseManagement.Tests/Infrastructure/AppDbContextSmokeTests.cs` |
| **验证标准** | 1. 冒烟测试覆盖：实体 CRUD、软删除过滤、审计字段<br>2. 冒烟测试在项目初始化时编写<br>3. 冒烟测试使用 InMemory 和 SQLite 两种 Provider<br>4. 冒烟测试作为 CI 的第一批测试<br>5. 冒烟测试失败时阻断后续开发 |
| **可复用性评估** | **高** — 适用于所有项目。冒烟测试快速验证基础设施，避免在基础问题上浪费时间。 |

### Skill 18：业务规则单元测试（Business Rule Unit Tests）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `business-rule-unit-tests` |
| **描述** | 针对业务规则编写单元测试：SKU 唯一性校验、工号重复校验、MaterialCode 唯一性校验等。测试使用真实 Repository（非 Mock），验证完整的业务流程。 |
| **来源** | `tests/WarehouseManagement.Tests/Services/MaterialServiceTests.cs`, `UserServiceTests.cs`, `StandardServiceTests.cs` |
| **验证标准** | 1. 每个业务规则有对应的单元测试<br>2. 测试使用真实 Repository（非 Mock）<br>3. 测试验证 Result 模式的 ErrorCode<br>4. 测试方法命名：`方法名_场景_预期结果`<br>5. 测试数据幂等（可重复运行） |
| **可复用性评估** | **高** — 适用于所有有业务规则的项目。真实 Repository 测试比 Mock 测试更可靠，能发现数据库层面的问题。 |

---

## 五、部署 Skills

### Skill 19：开发期 SQLite + 生产期 SQL Server（Dev SQLite / Prod SQL Server）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `dev-sqlite-prod-sqlserver` |
| **描述** | 开发期使用 SQLite（零依赖，便于本机/容器/CI 快速跑起来），生产期切换 SQL Server 2022。DbContext Provider 中立，切换仅需修改 Program.cs。 |
| **来源** | `AGENTS.md` §十, `DEVELOP.md` 关键架构决策 |
| **验证标准** | 1. 开发环境使用 SQLite，无需安装数据库<br>2. CI/CD 使用 SQLite，无需数据库服务<br>3. 生产环境配置 SQL Server 连接字符串<br>4. 切换 Provider 仅需修改配置<br>5. 迁移文件兼容目标 Provider |
| **可复用性评估** | **中高** — 适用于需要快速启动的项目。SQLite 零依赖降低开发门槛，SQL Server 提供生产级性能。 |

### Skill 20：EF Core 迁移管理（EF Core Migration Management）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `ef-core-migration-management` |
| **描述** | 使用 EF Core Code-First 迁移管理数据库 schema。迁移文件命名清晰描述变更内容（如 `AddMaterialNewFields`、`AddDashboardDisplaySettings`）。迁移命令标准化：`dotnet ef migrations add <Name> -p Infrastructure -s Web`。 |
| **来源** | `src/WarehouseManagement.Infrastructure/Migrations/`, `DEVELOP.md` |
| **验证标准** | 1. 数据库变更通过迁移文件管理<br>2. 迁移命名描述变更内容<br>3. 迁移文件提交到版本控制<br>4. 使用标准命令生成和应用迁移<br>5. 迁移后验证数据库 schema |
| **可复用性评估** | **高** — 适用于所有使用 EF Core 的项目。迁移管理是数据库版本控制的标准实践。 |

### Skill 21：种子数据初始化（Seed Data Initialization）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `seed-data-initialization` |
| **描述** | 应用启动时自动初始化种子数据：Identity 角色和管理员账户、物资消耗类型配置、权限页面配置。种子数据使用独立的 SeedData 类，幂等执行（已存在则跳过）。 |
| **来源** | `src/WarehouseManagement.Web/Program.cs` SeedIdentityAsync/SeedMaterialConsumptionTypesAsync/SeedPermissionsAsync, `src/WarehouseManagement.Infrastructure/SeedData/` |
| **验证标准** | 1. 种子数据在 Program.cs 启动时执行<br>2. 种子数据幂等（已存在则跳过）<br>3. 种子数据使用独立的 SeedData 类<br>4. 失败时记录错误日志但不阻断启动<br>5. 种子数据包含：角色、管理员、配置数据 |
| **可复用性评估** | **高** — 适用于所有需要初始数据的应用。种子数据确保应用首次启动即可用。 |

---

## 六、文档 Skills

### Skill 22：架构总纲（Architecture Constitution）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `architecture-constitution` |
| **描述** | `架构总纲.spec.md` 作为项目的"架构宪法"，包含：三大系统边界定义、踩过的坑（架构级）、禁止修改的内容（架构红线）、必须遵守的技术规范、允许的操作、项目健康检查清单。任何修改必须经过团队评审。 |
| **来源** | `架构总纲.spec.md` |
| **验证标准** | 1. 架构总纲在项目根目录<br>2. 包含系统边界定义<br>3. 包含架构红线（禁止修改的内容）<br>4. 包含技术规范（必须遵守）<br>5. 包含健康检查清单<br>6. 标注"架构宪法"，修改需评审 |
| **可复用性评估** | **高** — 适用于所有中大型项目。架构总纲是 AI 和人类共同遵守的"最高法律"，防止架构腐化。 |

### Skill 23：业务规则编号体系（Business Rule Numbering）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `business-rule-numbering` |
| **描述** | 业务规则使用 `BR-XX-YY` 编号体系（如 `BR-MAT-03`、`BR-STOCK-05`），在代码注释和文档中引用。便于追溯规则来源和影响范围。 |
| **来源** | `src/WarehouseManagement.Shared/Entities/Material.cs` 注释, `架构总纲.spec.md` |
| **验证标准** | 1. 业务规则使用 `BR-XX-YY` 格式编号<br>2. 代码注释引用规则编号<br>3. 文档中列出规则清单<br>4. 规则编号全局唯一<br>5. 修改规则时更新所有引用 |
| **可复用性评估** | **中** — 适用于业务规则复杂的项目。规则编号便于追溯，但增加维护成本。小型项目可省略。 |

### Skill 24：踩坑记录模式（Pitfall Documentation Pattern）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `pitfall-documentation` |
| **描述** | 每个 spec.md 文件包含"踩过的坑"章节，记录：现象、根源、解决方案、预防措施。坑点永久记录，防止重复犯错。 |
| **来源** | `架构总纲.spec.md` §2, 各 `.spec.md` 文件 §2 |
| **验证标准** | 1. 每个 spec.md 包含"踩过的坑"章节<br>2. 坑点包含：现象、根源、解决方案、预防<br>3. 坑点永久记录，不删除<br>4. 新坑点及时补充<br>5. 坑点按严重程度排序 |
| **可复用性评估** | **高** — 适用于所有项目。踩坑记录是团队知识的核心组成部分，防止新人重复踩坑。 |

### Skill 25：自动化 Spec.md 管理工具（Automated Spec.md Manager）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `spec-md-manager-tool` |
| **描述** | 使用 `tools/spec_md_manager.py` 工具自动化管理 spec.md 文件：扫描缺失的 spec.md、批量创建、生成覆盖度报告。支持 Git Pre-Commit Hook 集成。 |
| **来源** | `tools/spec_md_manager.py` |
| **验证标准** | 1. 工具支持 scan/create/report 三个命令<br>2. 扫描结果包含：总文件数、已有/缺失数量、覆盖率<br>3. 批量创建使用标准模板<br>4. 覆盖率报告按项目分类<br>5. 排除 wwwroot/Properties 等非业务目录<br>6. 仅扫描 .cs 和 .razor 文件 |
| **可复用性评估** | **高** — 适用于所有使用 spec.md 体系的项目。自动化管理降低维护成本，确保覆盖度。 |

---

## 七、附加 Skills

### Skill 26：MudBlazor UI 统一规范（MudBlazor UI Standards）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `mudblazor-ui-standards` |
| **描述** | 统一使用 MudBlazor 8.x 组件库，保持 UI 风格一致：表单使用 MudForm + MudTextField/MudSelect/MudDatePicker，表格使用 MudTable 或 QuickGrid，按钮颜色统一为 Color.Primary（主操作）/Color.Error（危险操作）。 |
| **来源** | `AGENTS.md` §五 |
| **验证标准** | 1. 使用 MudBlazor 8.x 组件<br>2. 表单使用 MudForm + 标准输入组件<br>3. 按钮颜色统一（Primary/Error）<br>4. 不混用其他 UI 组件库<br>5. 组件参数遵循 MudBlazor 文档 |
| **可复用性评估** | **中** — 仅适用于使用 MudBlazor 的 Blazor 项目。其他 UI 库（如 Radzen、Ant Design Blazor）有类似规范。 |

### Skill 27：品牌设计规范集成（Brand Design System Integration）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `brand-design-system` |
| **描述** | 将企业品牌规范（色彩、字体、Logo、设计原则）集成到代码库。定义品牌色板（主色/辅色/语义色）、字体栈、Logo 资源、响应式断点。品牌规范作为 UI 开发的"铁律"。 |
| **来源** | `AGENTS.md` §九, `design-system/` 目录 |
| **验证标准** | 1. 品牌色板定义在主题配置中<br>2. 字体栈优先系统字体<br>3. Logo 资源包含多种尺寸<br>4. 响应式断点明确定义<br>5. 可访问性标准（对比度 ≥4.5:1）<br>6. 禁止使用的颜色/风格明确列出 |
| **可复用性评估** | **中** — 适用于有企业品牌要求的项目。品牌规范因企业而异，但集成模式可复用。 |

### Skill 28：数据库驱动的动态权限（Database-Driven Dynamic Permissions）

| 属性 | 内容 |
|------|------|
| **Skill 名称** | `db-driven-dynamic-permissions` |
| **描述** | 替代硬编码 `[Authorize(Roles=...)]`，使用数据库存储角色-页面权限映射。管理员可通过 UI 配置各角色的页面访问权限。使用 `IMemoryCache` 缓存权限配置，即时生效。 |
| **来源** | `AGENTS.md` §十 架构决策记录, `src/WarehouseManagement.Core/Services/PermissionService.cs` |
| **验证标准** | 1. 权限配置存储在数据库<br>2. 管理员可通过 UI 修改权限<br>3. 权限变更即时生效（缓存刷新）<br>4. 不使用硬编码的 `[Authorize]`<br>5. 权限检查在页面级别（非功能级别） |
| **可复用性评估** | **中高** — 适用于需要灵活权限管理的企业应用。比硬编码权限更灵活，但增加实现复杂度。 |

---

## 八、Skills 总结表

| 序号 | Skill 类型 | Skill 名称 | 可复用性 |
|------|-----------|-----------|---------|
| 1 | 架构 | `four-layer-architecture` | 高 |
| 2 | 架构 | `repository-uow-pattern` | 高 |
| 3 | 架构 | `centralized-di-registration` | 高 |
| 4 | 架构 | `system-boundary-isolation` | 中高 |
| 5 | 架构 | `strategy-pattern-extension` | 高 |
| 6 | 编码 | `unified-naming-conventions` | 高 |
| 7 | 编码 | `result-pattern-business-errors` | 高 |
| 8 | 编码 | `structured-logging` | 高 |
| 9 | 编码 | `auditable-entity-base` | 高 |
| 10 | 编码 | `blazor-code-behind` | 高 |
| 11 | 编码 | `db-provider-agnostic` | 中高 |
| 12 | 编码 | `coefficient-snapshot` | 高 |
| 13 | 工作流程 | `spec-md-convention` | 高 |
| 14 | 工作流程 | `verification-checklist` | 高 |
| 15 | 工作流程 | `development-worklog` | 中高 |
| 16 | 测试 | `sqlite-memory-test-base` | 高 |
| 17 | 测试 | `smoke-tests-first` | 高 |
| 18 | 测试 | `business-rule-unit-tests` | 高 |
| 19 | 部署 | `dev-sqlite-prod-sqlserver` | 中高 |
| 20 | 部署 | `ef-core-migration-management` | 高 |
| 21 | 部署 | `seed-data-initialization` | 高 |
| 22 | 文档 | `architecture-constitution` | 高 |
| 23 | 文档 | `business-rule-numbering` | 中 |
| 24 | 文档 | `pitfall-documentation` | 高 |
| 25 | 文档 | `spec-md-manager-tool` | 高 |
| 26 | UI | `mudblazor-ui-standards` | 中 |
| 27 | UI | `brand-design-system` | 中 |
| 28 | 权限 | `db-driven-dynamic-permissions` | 中高 |

---

## 九、高可复用性 Skills 优先实施建议

### 第一优先级（立即可用）

1. **`spec-md-convention`** — 最具创新性的实践，AI 辅助开发的核心记忆机制
2. **`result-pattern-business-errors`** — 统一错误处理，提升代码可维护性
3. **`auditable-entity-base`** — 审计追踪基础设施
4. **`repository-uow-pattern`** — 数据访问层标准模式
5. **`verification-checklist`** — 质量门禁基础

### 第二优先级（项目初始化时引入）

6. **`four-layer-architecture`** — 架构骨架
7. **`centralized-di-registration`** — 依赖注入管理
8. **`sqlite-memory-test-base`** — 测试基础设施
9. **`architecture-constitution`** — 架构宪法
10. **`pitfall-documentation`** — 知识沉淀机制

### 第三优先级（按需引入）

11. **`strategy-pattern-extension`** — 业务扩展场景
12. **`system-boundary-isolation`** — 复杂业务域
13. **`coefficient-snapshot`** — 数据可追溯性
14. **`db-driven-dynamic-permissions`** — 灵活权限管理

---

*文档生成时间：2026-06-17*
*数据来源：WarehouseMS 项目深度分析*
*模板版本：模板6 - 可提取的Skills清单*
