# 传感器偏差分级告警

> **分类**: 编码  
> **可复用**: ✅ 是 — 复制到任何有传感器/测量数据验证的项目  
> **依赖**: 无（纯模式）

---

## 适用场景

系统获取测量值（重量、温度、压力、距离），需要与期望值对比并分级响应：
- 偏差小 → 自动放行
- 偏差中 → 人工确认
- 偏差大 → 强制告警

---

## 模式

### 三级分类体系

```
偏差百分比:
  0% ─────────── 5% ────────────── 10% ──────────►

  正常 (🟢)       警告 (🟡)        严重 (🔴)
  自动放行         需人工确认        强制告警
```

### 可配置阈值

```json
{
  "DeviationThresholds": {
    "NormalMaxPercent": 5.0,    // < 5% → 绿灯，自动通过
    "WarningMaxPercent": 10.0,  // 5-10% → 黄灯，需确认
    "CriticalMinPercent": 10.0  // ≥ 10% → 红灯，强制告警
  }
}
```

---

## 实现

```csharp
public class DeviationClassifier
{
    private readonly DeviationThresholds _thresholds;

    public DeviationClassifier(IOptions<DeviationThresholds> thresholds)
        => _thresholds = thresholds.Value;

    public DeviationResult Classify(double expected, double actual)
    {
        if (expected == 0) return DeviationResult.Error("期望值不能为零");

        var percent = Math.Abs((actual - expected) / expected) * 100;

        return percent switch
        {
            <= var n when n <= _thresholds.NormalMaxPercent =>
                DeviationResult.Normal(actual, percent),

            <= var w when w <= _thresholds.WarningMaxPercent =>
                DeviationResult.Warning(actual, percent, $"偏差 {percent:F1}% 超过正常阈值"),

            _ => DeviationResult.Critical(actual, percent, $"严重告警: 偏差 {percent:F1}%")
        };
    }
}

public record DeviationResult(double Value, double Percent, DeviationLevel Level, string Message)
{
    public static DeviationResult Normal(double v, double p) => new(v, p, DeviationLevel.Normal, "正常");
    public static DeviationResult Warning(double v, double p, string msg) => new(v, p, DeviationLevel.Warning, msg);
    public static DeviationResult Critical(double v, double p, string msg) => new(v, p, DeviationLevel.Critical, msg);
    public static DeviationResult Error(string msg) => new(0, 0, DeviationLevel.Error, msg);
}

public enum DeviationLevel { Normal, Warning, Critical, Error }
```

---

## 业务层使用

```csharp
var expectedWeight = 25.0; // kg — 产品规格
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

## 验证清单

- [ ] 三级分类有明确的可配置阈值
- [ ] 正常级自动通过（无需人工）
- [ ] 警告级要求人工确认
- [ ] 严重级触发告警并阻断操作
- [ ] 阈值从配置读取，不硬编码
- [ ] 边界情况：期望值 = 0 → 优雅处理
