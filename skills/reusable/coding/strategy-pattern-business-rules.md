# Strategy Pattern for Business Rules

> **Category**: Coding  
> **Reusable**: ✅ Yes — copy to any project where business rules must be extensible without code changes  
> **Dependencies**: None (Gang of Four pattern, applied for AI-assisted development)

---

## When to Use

- Business rules depend on entity type (different calculation for different product types)
- New entity types should be addable via config + new class, without modifying existing code
- AI assistants frequently need to add new types without breaking existing ones

---

## Pattern

```
IMaterialConsumptionStrategy          ← Strategy interface
├── StandardConsumptionStrategy       ← Strategy for type A
├── AbrasiveConsumptionStrategy       ← Strategy for type B
└── CustomConsumptionStrategy         ← Strategy for new type (add without touching existing code)

IMaterialConsumptionStrategyFactory   ← Factory: selects strategy by type
```

---

## Implementation

### Step 1: Strategy Interface

```csharp
public interface ICalculationStrategy
{
    string StrategyName { get; }
    bool CanHandle(string businessType);
    Task<CalculationResult> CalculateAsync(CalculationContext ctx);
}
```

### Step 2: Strategy Factory

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
            throw new NotSupportedException($"No strategy for type: {businessType}");
        return strategy;
    }
}
```

### Step 3: DI Registration

```csharp
// All strategies auto-discovered via DI
services.AddScoped<ICalculationStrategy, StandardCalculationStrategy>();
services.AddScoped<ICalculationStrategy, AbrasiveCalculationStrategy>();
services.AddScoped<ICalculationStrategy, CustomCalculationStrategy>();
services.AddScoped<CalculationStrategyFactory>();
```

### Step 4: Usage in Service

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

## Adding a New Type (3 steps, 0 existing code changes)

1. Create new class implementing `ICalculationStrategy`
2. Register in DI: `services.AddScoped<ICalculationStrategy, NewTypeStrategy>()`
3. That's it. Factory auto-discovers it.

---

## Why This Helps AI-Assisted Development

- **AI can add new strategies** without understanding existing ones — just implement the interface
- **Factory pattern is AI-friendly**: clear contract, no ambiguity
- **Reduces merge conflicts**: new strategies are new files, not edits to existing ones

---

## Verification

- [ ] Strategy interface has `CanHandle(type)` predicate
- [ ] Factory uses DI to auto-discover all strategies
- [ ] Adding new type = new class + DI registration (no existing code modified)
- [ ] Strategy selection by type, not by if/else chain
- [ ] Unknown type throws clear error (not null reference)
