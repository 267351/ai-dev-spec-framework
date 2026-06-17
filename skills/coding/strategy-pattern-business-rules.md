# 策略模式驱动业务扩展

> **分类**: 编码  
> **可复用**: ✅ 是 — 复制到任何需按类型扩展业务规则的项目  
> **依赖**: 无（GoF 经典模式，针对 AI 辅助开发场景优化）

---

## 适用场景

- 业务规则依赖实体类型（不同产品类型有不同的计算方式）
- 新增类型应通过配置 + 新类完成，不改现有代码
- AI 助手频繁需要添加新类型，但不能破坏已有逻辑

---

## 模式

```
ICalculationStrategy              ← 策略接口
├── StandardCalculationStrategy   ← 类型 A 的策略
├── AbrasiveCalculationStrategy   ← 类型 B 的策略
└── CustomCalculationStrategy     ← 新类型的策略（新增，不动已有代码）

CalculationStrategyFactory        ← 工厂：根据类型选择策略
```

---

## 实现

### 第1步：策略接口

```csharp
public interface ICalculationStrategy
{
    string StrategyName { get; }
    bool CanHandle(string businessType);
    Task<CalculationResult> CalculateAsync(CalculationContext ctx);
}
```

### 第2步：策略工厂

```csharp
public class CalculationStrategyFactory
{
    private readonly IEnumerable<ICalculationStrategy> _strategies;

    public CalculationStrategyFactory(IEnumerable<ICalculationStrategy> strategies)
        => _strategies = strategies;

    public ICalculationStrategy GetStrategy(string businessType)
    {
        var strategy = _strategies.FirstOrDefault(s => s.CanHandle(businessType));
        if (strategy == null)
            throw new NotSupportedException($"未找到类型 {businessType} 的策略");
        return strategy;
    }
}
```

### 第3步：DI 注册

```csharp
// 所有策略通过 DI 自动发现
services.AddScoped<ICalculationStrategy, StandardCalculationStrategy>();
services.AddScoped<ICalculationStrategy, AbrasiveCalculationStrategy>();
services.AddScoped<ICalculationStrategy, CustomCalculationStrategy>();
services.AddScoped<CalculationStrategyFactory>();
```

### 第4步：Service 中使用

```csharp
public class CalculationService
{
    private readonly CalculationStrategyFactory _factory;

    public CalculationService(CalculationStrategyFactory factory)
        => _factory = factory;

    public async Task<CalculationResult> CalculateAsync(string type, CalculationContext ctx)
    {
        var strategy = _factory.GetStrategy(type);
        return await strategy.CalculateAsync(ctx);
    }
}
```

---

## 新增类型只需 3 步（0 处现有代码修改）

1. 新建类实现 `ICalculationStrategy`
2. DI 注册: `services.AddScoped<ICalculationStrategy, NewTypeStrategy>()`
3. 完成。工厂自动发现。

---

## 为什么对 AI 辅助开发友好

- **AI 可独立添加新策略**——只需实现接口，无需理解已有策略
- **工厂模式对 AI 友好**——契约明确，无歧义
- **减少合并冲突**——新策略是新文件，不改已有文件

---

## 验证清单

- [ ] 策略接口有 `CanHandle(type)` 谓词
- [ ] 工厂通过 DI 自动发现所有策略
- [ ] 新增类型 = 新类 + DI 注册（不修改已有代码）
- [ ] 按类型选择策略，而非 if/else 链
- [ ] 未知类型抛明确异常（非空引用）
