# 差异模式分析

## 一、概述

本文档详细描述从CSO-FORCS和WarehouseMS两个项目中提取的差异开发模式。这些模式在某个项目中得到验证，具有特定场景的适用性。

---

## 二、差异模式清单

### 2.1 CSO-FORCS特有模式

#### 模式1：硬件抽象层（HAL）

**描述**：定义硬件接口，Mock实现支持离线调试

**适用场景**：
- 物联网/工业应用
- 需要硬件设备交互
- 需要离线调试能力

**实现方式**：
```csharp
// 接口定义
public interface ICardReader
{
    Task<string?> ReadCardAsync(CancellationToken ct = default);
}

// Mock实现
public class DisabledCardReader : ICardReader
{
    public Task<string?> ReadCardAsync(CancellationToken ct = default)
        => Task.FromResult<string?>(null);
}

// 真实实现
public class HttpCardReaderClient : ICardReader
{
    // HTTP调用微服务
}
```

**验证标准**：
1. 每个HAL接口至少有一个实现（真实或Mock）
2. DI注册前检查实现状态矩阵
3. 32位依赖通过独立进程隔离

**可复用性**：中高 - 工业/物联网项目的通用模式

---

#### 模式2：双子系统架构

**描述**：两个独立子系统共享业务层，但拥有独立的前端和API

**适用场景**：
- 多个相关但独立的业务模块
- 需要共享数据层但前端独立
- 需要独立部署和扩展

**实现方式**：
```
有限空间作业系统（主系统）
├── Api（14个控制器）
├── App（20个页面）
└── 共享层：BLL/DAL/Models

库房管理系统（配套系统）
├── Warehouse.Api（15个控制器）
├── Warehouse.App（16个页面）
└── 共享层：BLL/DAL/Models
```

**验证标准**：
1. 两个API项目独立
2. 两个App宿主独立
3. 共享层无子系统特有逻辑

**可复用性**：中 - 适用于需要多子系统共享数据层的企业应用

---

#### 模式3：API异常处理

**描述**：Controller捕获异常，返回BadRequest而非500

**适用场景**：
- RESTful API
- 需要用户友好的错误消息
- 需要统一的错误处理

**实现方式**：
```csharp
[HttpGet]
public async Task<IActionResult> GetAll()
{
    try
    {
        var goods = await _goodsService.GetAllAsync();
        return Ok(goods);
    }
    catch (InvalidOperationException ex)
    {
        return BadRequest(ex.Message);
    }
}
```

**验证标准**：
1. 每个Controller action有try/catch
2. 返回BadRequest(ex.Message)而非500
3. 前端不展示原始JSON ProblemDetails

**可复用性**：高 - RESTful API的通用最佳实践

---

#### 模式4：验证前置原则

**描述**：业务验证在用户操作的第一时机执行

**适用场景**：
- 复杂业务验证
- 需要提前反馈
- 需要复用验证逻辑

**实现方式**：
```csharp
// 独立验证方法
public async Task<ValidationResult> ValidateGoodsEntryAsync(string goodsCode, int personId)
{
    // 验证逻辑
}

// 注册方法复用验证
public async Task RegisterGoodsEntryAsync(string goodsCode, int personId)
{
    var validation = await ValidateGoodsEntryAsync(goodsCode, personId);
    if (!validation.IsValid)
        throw new InvalidOperationException(validation.ErrorMessage);
    
    // 业务逻辑
}
```

**验证标准**：
1. BLL有独立的Validate方法
2. Register方法复用Validate
3. 前端在操作入口调用验证

**可复用性**：高 - 通用的防御性编程模式

---

#### 模式5：AGENTS.md知识索引架构

**描述**：精简索引+按需加载的知识管理架构

**适用场景**：
- AI辅助开发
- 大型项目知识管理
- 需要控制上下文窗口

**实现方式**：
```
L1: AGENTS.md（精简索引，≤100行）
├── 架构铁律
├── Skills路由索引
├── 铁律速查
└── 构建命令

L2: Skills（按需加载，每个≤700行）
├── cso-forcs（主技能）
├── cso-forcs-bugs（bug模式）
├── cso-forcs-reference（参考查询）
└── ...

L3: docs/（详细参考文档）
├── architecture.md
├── deployment-guide.md
└── ...
```

**验证标准**：
1. AGENTS.md ≤ 100行
2. 无重复内容
3. Skills路由索引完整
4. 修改需用户批准

**可复用性**：极高 - 解决AI上下文窗口限制的核心架构模式

---

#### 模式6：偏差检测机制

**描述**：检测AI偏离规范的机制

**适用场景**：
- AI辅助开发
- 需要质量保障
- 需要规范执行

**实现方式**：
```markdown
## 偏差检测与更新提醒机制

### 偏差类型
- **硬偏差**：直接违反AGENTS.md明文禁止的行为
- **软偏差**：偏离最佳实践但未明确禁止
- **演进偏差**：AGENTS.md过时，需要更新

### 检测流程
1. 发现偏差 → 记录证据
2. 判断偏差类型
3. 提醒用户
4. 逐一批准审批
```

**验证标准**：
1. 偏差报告包含精确行号
2. 审查使用工具输出作为证据
3. 修改需用户逐一批准

**可复用性**：高 - AI辅助开发的质量保障机制

---

#### 模式7：一键跨平台部署

**描述**：部署脚本支持Linux/Windows双平台

**适用场景**：
- 需要跨平台部署
- 需要标准化部署流程
- 需要可移植部署

**实现方式**：
```bash
# deploy.sh - Linux部署
# deploy.ps1 - Windows部署

# 功能：
# 1. 构建全部服务
# 2. 生成配置文件
# 3. 生成启动脚本
# 4. 所有路径使用相对路径
```

**验证标准**：
1. 部署文件夹可复制到新位置运行
2. 配置文件使用相对路径
3. 启动脚本可执行

**可复用性**：高 - 多服务部署的通用模式

---

#### 模式8：升级保护与回滚

**描述**：升级前自动备份，失败时自动回滚

**适用场景**：
- 生产环境升级
- 需要数据保护
- 需要回滚能力

**实现方式**：
```bash
# upgrade.sh
# 1. 版本检查
# 2. 自动备份（数据库/配置/日志/证据）
# 3. 停止服务
# 4. 更新程序文件
# 5. 合并配置
# 6. 数据库迁移
# 7. 健康检查
# 8. 失败时自动回滚
```

**验证标准**：
1. 升级前自动备份
2. 用户数据不丢失
3. 配置合并保留自定义项
4. 失败时自动回滚

**可复用性**：高 - 生产环境升级的通用最佳实践

---

### 2.2 WarehouseMS特有模式

#### 模式9：Result模式

**描述**：使用Result/Result<T>替代异常进行业务错误处理

**适用场景**：
- 业务验证频繁
- 需要轻量级错误处理
- 需要结构化错误信息

**实现方式**：
```csharp
public class Result
{
    public bool IsSuccess { get; }
    public string? Error { get; }
    public string? ErrorCode { get; }
    
    public static Result Success() => new(true, null, null);
    public static Result Failure(string error, string? errorCode = null) => new(false, error, errorCode);
}

public sealed class Result<T> : Result
{
    public T? Value { get; }
    
    public static Result<T> Ok(T value) => new(true, value, null, null);
    public static Result<T> Fail(string error, string? errorCode = null) => new(false, default, error, errorCode);
}

// 使用
public async Task<Result<UserInfo>> CreateAsync(UserInfo user)
{
    var validation = ValidateAndNormalize(user);
    if (validation.IsFailure)
        return Result.Failure<UserInfo>(validation.Error!, validation.ErrorCode);
    
    // 业务逻辑
    return Result.Success(user);
}
```

**验证标准**：
1. Service方法返回Result/Result<T>
2. 错误码有统一前缀
3. 前端检查IsSuccess

**可复用性**：高 - 轻量级错误处理模式

---

#### 模式10：审计实体基类

**描述**：实体基类+拦截器自动填充审计字段

**适用场景**：
- 需要审计追踪
- 需要自动填充创建/修改时间
- 需要软删除

**实现方式**：
```csharp
// 基类
public abstract class AuditableEntity
{
    public int Id { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
    public bool IsDeleted { get; set; }
}

// 拦截器
public sealed class AuditFieldsInterceptor : SaveChangesInterceptor
{
    public override InterceptionResult<int> SavingChanges(DbContextEventData eventData, InterceptionResult<int> result)
    {
        ApplyAuditFields(eventData.Context);
        return base.SavingChanges(eventData, result);
    }
    
    private static void ApplyAuditFields(DbContext? context)
    {
        foreach (var entry in context.ChangeTracker.Entries<AuditableEntity>())
        {
            switch (entry.State)
            {
                case EntityState.Added:
                    entry.Entity.CreatedAt = DateTime.UtcNow;
                    entry.Entity.UpdatedAt = DateTime.UtcNow;
                    break;
                case EntityState.Modified:
                    entry.Entity.UpdatedAt = DateTime.UtcNow;
                    break;
            }
        }
    }
}

// 全局查询过滤器
modelBuilder.Entity<Material>().HasQueryFilter(e => !e.IsDeleted);
```

**验证标准**：
1. 所有业务实体继承AuditableEntity
2. 拦截器自动填充审计字段
3. 全局查询过滤器排除软删除记录

**可复用性**：高 - 企业应用的通用模式

---

#### 模式11：三大系统边界隔离

**描述**：Service层禁止跨系统调用，跨系统聚合仅在Web层

**适用场景**：
- 复杂业务域
- 多个相关但独立的子系统
- 需要清晰的边界

**实现方式**：
```markdown
## 三大系统边界

### 库房管理系统
- MaterialCategoryService
- MaterialService
- StockInService
- StockOutService
- StockRecycleService
- InventoryService

### 效率转换系统
- MaterialEfficiencyService
- WorkloadService
- DefaultConversionEngine

### 工时录入系统
- WorkHourService
- WorkHourAuditService

### 边界规则
- Service层禁止跨系统调用
- 跨系统数据聚合仅在Web层（看板页面）进行
```

**验证标准**：
1. Service层不调用其他系统的服务
2. 跨系统聚合在Web层进行
3. 有明确的边界文档

**可复用性**：高 - 复杂业务域的隔离模式

---

#### 模式12：Strategy+Factory模式

**描述**：策略模式+工厂模式组合，支持可扩展业务逻辑

**适用场景**：
- 业务逻辑需要扩展
- 多种计算方式
- 运行时选择策略

**实现方式**：
```csharp
// 策略接口
public interface IMaterialConsumptionStrategy
{
    string StrategyType { get; }
    bool CanHandle(Material material, MaterialConsumptionType config);
    Task ValidateOnIssueAsync(StockOutDto dto, Material material, MaterialConsumptionType config);
    decimal CalculateStandardQuantity(StockOut stockOut, MaterialConsumptionType config);
}

// 具体策略
public class GrindingWheelStrategy : IMaterialConsumptionStrategy
{
    public string StrategyType => "GrindingWheel";
    // 实现
}

// 工厂
public class MaterialConsumptionStrategyFactory : IMaterialConsumptionStrategyFactory
{
    private readonly IEnumerable<IMaterialConsumptionStrategy> _strategies;
    
    public IMaterialConsumptionStrategy GetStrategy(Material material, MaterialConsumptionType config)
    {
        return _strategies.FirstOrDefault(s => s.CanHandle(material, config))
            ?? _strategies.FirstOrDefault(s => s.StrategyType == "Default");
    }
}
```

**验证标准**：
1. 策略接口定义清晰
2. 工厂通过DI注入所有策略
3. 新策略只需实现接口+注册DI

**可复用性**：高 - 可扩展业务逻辑的标准模式

---

#### 模式13：SQLite内存测试

**描述**：使用SQLite内存数据库进行测试，更接近真实行为

**适用场景**：
- 需要测试EF Core逻辑
- 需要接近真实数据库行为
- 需要隔离的测试环境

**实现方式**：
```csharp
public abstract class ServiceTestBase : IDisposable
{
    protected readonly AppDbContext _context;
    protected readonly UnitOfWork _unitOfWork;
    private readonly SqliteConnection _connection;
    
    protected ServiceTestBase()
    {
        _connection = new SqliteConnection("DataSource=:memory:");
        _connection.Open();
        
        var options = new DbContextOptionsBuilder<AppDbContext>()
            .UseSqlite(_connection)
            .AddInterceptors(new AuditFieldsInterceptor())
            .Options;
        
        _context = new AppDbContext(options);
        _context.Database.EnsureCreated();
        _unitOfWork = new UnitOfWork(_context);
    }
    
    public void Dispose()
    {
        _context.Dispose();
        _connection.Dispose();
    }
}
```

**验证标准**：
1. 每个测试获得独立的内存数据库
2. 应用真实的拦截器
3. 测试后正确清理资源

**可复用性**：高 - EF Core测试的最佳实践

---

## 三、差异模式总结

### 3.1 模式分类

| 类别 | 模式数量 | 关键模式 |
|------|----------|----------|
| CSO-FORCS特有 | 8 | HAL、双子系统、API异常处理、验证前置、AGENTS.md索引、偏差检测、部署脚本、升级保护 |
| WarehouseMS特有 | 5 | Result模式、审计实体、系统边界、Strategy+Factory、SQLite内存测试 |

### 3.2 适用场景建议

**物联网/工业应用**：
- 硬件抽象层（HAL）
- 一键跨平台部署
- 升级保护与回滚

**复杂业务域**：
- 三大系统边界隔离
- Strategy+Factory模式
- Result模式

**AI辅助开发**：
- AGENTS.md知识索引架构
- 偏差检测机制
- Spec.md约定文件体系

**企业应用**：
- 审计实体基类
- 软删除
- SQLite内存测试

---

**分析完成时间**: 2026-06-17  
**分析版本**: v1.0  
**数据来源**: 模板7横向对比分析报告
