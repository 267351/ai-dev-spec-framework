# 系数快照模式

> **分类**: 编码 / 数据  
> **可复用**: ✅ 是 — 复制到任何历史记录需免疫配置变更的项目  
> **依赖**: 无（纯数据设计模式）

---

## 适用场景

系统中有业务系数（价格、税率、汇率、材质系数等），这些系数：
- 会随时间变化（管理员可修改）
- 但历史记录必须反映交易当时的数值
- 修改当前配置不能追溯影响历史

---

## 模式

**记录创建时**：将当前系数值复制到记录的快照字段中。  
**系数更新后**：仅新记录使用新值。  
**查询历史时**：始终使用快照字段，绝不联查当前配置。

---

## 实现

### 实体设计

```csharp
// 配置表（可变——管理员可修改）
public class MaterialConfig
{
    public int Id { get; set; }
    public string MaterialCode { get; set; }
    public decimal SpecCoefficient { get; set; }     // 可变更！
    public decimal MaterialCoefficient { get; set; } // 可变更！
}

// 交易记录（不可变——创建时快照）
public class StockOut
{
    public int Id { get; set; }
    public string MaterialCode { get; set; }
    public int Quantity { get; set; }
    public DateTime CreatedAt { get; set; }

    // 快照字段——创建时从配置复制，写入后永不修改
    public decimal SpecCoefficientSnapshot { get; set; }
    public decimal MaterialCoefficientSnapshot { get; set; }

    // 计算字段使用快照值（绝不用配置表！）
    public decimal EffectiveQuantity => Quantity * SpecCoefficientSnapshot * MaterialCoefficientSnapshot;
}
```

### Service 实现

```csharp
public async Task<StockOut> CreateStockOutAsync(string materialCode, int quantity)
{
    // 读取当前配置
    var config = await _db.MaterialConfigs
        .FirstAsync(m => m.MaterialCode == materialCode);

    // 创建记录时使用快照值
    var record = new StockOut
    {
        MaterialCode = materialCode,
        Quantity = quantity,
        SpecCoefficientSnapshot = config.SpecCoefficient,         // 快照！
        MaterialCoefficientSnapshot = config.MaterialCoefficient, // 快照！
        CreatedAt = DateTime.UtcNow
    };

    _db.StockOuts.Add(record);
    await _db.SaveChangesAsync();
    return record;
}

// 之后：管理员将 config.SpecCoefficient 从 1.5 改成 1.8
// 历史 StockOut 记录的快照值仍为 1.5 ← 正确！
```

---

## 铁律

1. **快照字段创建时设置一次，永不再修改**
2. **计算值使用快照，绝不 JOIN 配置表**
3. **快照字段命名 = 配置字段名 + "Snapshot" 后缀**
4. **配置变更绝不要求历史数据迁移**

---

## 常见应用场景

| 领域 | 配置字段 | 快照字段 |
|------|---------|---------|
| 电商 | ProductPrice | PriceSnapshot |
| 金融 | ExchangeRate | ExchangeRateSnapshot |
| 税务 | TaxRate | TaxRateSnapshot |
| 制造 | MaterialCoefficient | MaterialCoefficientSnapshot |
| 物流 | FuelSurcharge | FuelSurchargeSnapshot |

---

## 验证清单

- [ ] 交易记录中每个可变配置值有对应快照字段
- [ ] 快照值创建时设置，永不更新
- [ ] 计算列使用快照值（不 JOIN 配置表）
- [ ] 配置变更不触发历史数据迁移
- [ ] 快照字段命名明显区别于配置字段
