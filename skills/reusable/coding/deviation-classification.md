# Sensor Deviation Classification

> **Category**: Coding  
> **Reusable**: ✅ Yes — copy to any project with sensor/measurement data validation  
> **Dependencies**: None (pure pattern)

---

## When to Use

Your system takes measurements (weight, temperature, pressure, distance) and needs to validate them against expected values with graded responses:
- Auto-pass when close enough
- Warn when slightly off
- Alarm when significantly off

---

## Pattern

### Three-Tier Classification

```
Deviation from expected:
  0% ─────────── 5% ────────────── 10% ──────────►

  Normal (🟢)     Warning (🟡)      Critical (🔴)
  Auto-pass       Human confirm      Force alarm
```

### Configuration

```json
{
  "DeviationThresholds": {
    "NormalMaxPercent": 5.0,    // < 5% → green, auto-pass
    "WarningMaxPercent": 10.0,  // 5-10% → yellow, needs confirm
    "CriticalMinPercent": 10.0  // ≥ 10% → red, force alarm
  }
}
```

---

## Implementation

```csharp
public class DeviationClassifier
{
    private readonly DeviationThresholds _thresholds;

    public DeviationClassifier(IOptions<DeviationThresholds> thresholds)
        => _thresholds = thresholds.Value;

    public DeviationResult Classify(double expected, double actual)
    {
        if (expected == 0) return DeviationResult.Error("Expected value cannot be zero");

        var percent = Math.Abs((actual - expected) / expected) * 100;

        return percent switch
        {
            < var n when n <= _thresholds.NormalMaxPercent =>
                DeviationResult.Normal(actual, percent),

            < var w when w <= _thresholds.WarningMaxPercent =>
                DeviationResult.Warning(actual, percent, $"Deviation {percent:F1}% exceeds normal threshold"),

            _ => DeviationResult.Critical(actual, percent, $"CRITICAL: deviation {percent:F1}%")
        };
    }
}

public record DeviationResult(double Value, double Percent, DeviationLevel Level, string Message)
{
    public static DeviationResult Normal(double v, double p) => new(v, p, DeviationLevel.Normal, "OK");
    public static DeviationResult Warning(double v, double p, string msg) => new(v, p, DeviationLevel.Warning, msg);
    public static DeviationResult Critical(double v, double p, string msg) => new(v, p, DeviationLevel.Critical, msg);
    public static DeviationResult Error(string msg) => new(0, 0, DeviationLevel.Error, msg);
}

public enum DeviationLevel { Normal, Warning, Critical, Error }
```

---

## Usage in Business Logic

```csharp
var expectedWeight = 25.0; // kg — from product spec
var actualWeight = await _weightSensor.ReadAsync();

var result = _classifier.Classify(expectedWeight, actualWeight);

switch (result.Level)
{
    case DeviationLevel.Normal:
        await ApproveAutomatically(session);
        break;
    case DeviationLevel.Warning:
        await RequestHumanConfirmation(session, result.Message);
        break;
    case DeviationLevel.Critical:
        await TriggerAlarm(session, result.Message);
        await BlockOperation(session);
        break;
}
```

---

## Verification

- [ ] Three levels clearly defined with configurable thresholds
- [ ] Normal level auto-approves (no human interaction)
- [ ] Warning level requires human confirmation
- [ ] Critical level triggers alarm AND blocks operation
- [ ] Thresholds are configurable, not hardcoded
- [ ] Edge case: expected value = 0 → handle gracefully
