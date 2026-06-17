# Coefficient Snapshot Pattern

> **Category**: Coding / Data  
> **Reusable**: ✅ Yes — copy to any project where historical records must be immune to config changes  
> **Dependencies**: None (pure data design pattern)

---

## When to Use

Your system has business coefficients (prices, tax rates, exchange rates, material coefficients) that:
- Change over time (updated by admin)
- But historical records must reflect the value AT THE TIME of the transaction
- Modifying current config must NOT retroactively change history

---

## Pattern

**On record creation**: Copy the current coefficient value into the record as a snapshot field.
**On coefficient update**: Only future records use the new value.
**On history query**: Always use snapshot fields, never join to current config.

---

## Implementation

### Entity Design

```csharp
// Config table (mutable — admin can change)
public class MaterialConfig
{
    public int Id { get; set; }
    public string MaterialCode { get; set; }
    public decimal SpecCoefficient { get; set; }   // Can change!
    public decimal MaterialCoefficient { get; set; } // Can change!
}

// Transaction record (immutable — snapshot at creation time)
public class StockOut
{
    public int Id { get; set; }
    public string MaterialCode { get; set; }
    public int Quantity { get; set; }
    public DateTime CreatedAt { get; set; }

    // SNAPSHOT fields — copied from config at creation
    public decimal SpecCoefficientSnapshot { get; set; }
    public decimal MaterialCoefficientSnapshot { get; set; }

    // Computed from snapshots (never from config!)
    public decimal EffectiveQuantity => Quantity * SpecCoefficientSnapshot * MaterialCoefficientSnapshot;
}
```

### Service Implementation

```csharp
public async Task<StockOut> CreateStockOutAsync(string materialCode, int quantity)
{
    // Read current config
    var config = await _db.MaterialConfigs
        .FirstAsync(m => m.MaterialCode == materialCode);

    // Create record with SNAPSHOT values
    var record = new StockOut
    {
        MaterialCode = materialCode,
        Quantity = quantity,
        SpecCoefficientSnapshot = config.SpecCoefficient,      // Snapshot!
        MaterialCoefficientSnapshot = config.MaterialCoefficient, // Snapshot!
        CreatedAt = DateTime.UtcNow
    };

    _db.StockOuts.Add(record);
    await _db.SaveChangesAsync();
    return record;
}

// Later: admin changes config.SpecCoefficient from 1.5 → 1.8
// Historical StockOut records still use 1.5 ← CORRECT
```

---

## Rules

1. **Snapshot fields are set ONCE at creation, never updated**
2. **Computed values use snapshots, never join to config table**
3. **Snapshot fields match config field names + "Snapshot" suffix**
4. **Config changes NEVER require migration of historical records**

---

## Common Use Cases

| Domain | Config Field | Snapshot Field |
|--------|-------------|----------------|
| E-commerce | Product price | PriceSnapshot |
| Finance | Exchange rate | ExchangeRateSnapshot |
| Tax | Tax rate % | TaxRateSnapshot |
| Manufacturing | Material coefficient | MaterialCoefficientSnapshot |
| Logistics | Fuel surcharge % | FuelSurchargeSnapshot |

---

## Verification

- [ ] Transaction records have snapshot fields for each mutable config value
- [ ] Snapshot values set at creation, never updated
- [ ] Computed columns use snapshots (not config joins)
- [ ] Config changes don't require history migration
- [ ] Snapshot field names clearly distinguishable from config fields
