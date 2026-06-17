# HAL 硬件抽象层 + 三实现模式

> **分类**: 架构  
> **可复用**: ✅ 是 — 复制到任何有硬件/传感器依赖的项目  
> **依赖**: 无（纯设计模式）

---

## 适用场景

项目涉及物理硬件（传感器、读卡器、摄像头、打印机），需要：
- 不依赖真实硬件即可开发和测试
- 通过配置在 Mock 和生产实现之间切换
- 硬件不可用时优雅降级

---

## 模式

每个硬件接口提供**三种实现**：

```
硬件接口（如 ICardReader）
├── Mock 实现     ← 开发/测试用（可配行为）
├── Real 实现     ← 生产环境（真实硬件）
└── Disabled 实现 ← 优雅降级（硬件缺失时）
```

---

## 实现

### 第1步：定义接口

```csharp
// src/Project.HAL/Interfaces/ICardReader.cs
public interface ICardReader
{
    Task<bool> IsAvailableAsync();
    Task<CardReadResult> ReadCardAsync(CancellationToken ct);
}

public record CardReadResult(string Uid, bool Success, string Error);
```

### 第2步：创建三种实现

```csharp
// Mock —— 可配置行为，用于测试
public class MockCardReader : ICardReader
{
    private readonly string _mockUid;
    public MockCardReader(string mockUid) => _mockUid = mockUid;

    public Task<bool> IsAvailableAsync() => Task.FromResult(true);
    public Task<CardReadResult> ReadCardAsync(CancellationToken ct)
        => Task.FromResult(new CardReadResult(_mockUid, true, null));
}

// Real —— 封装真实硬件访问
public class RealCardReader : ICardReader, IDisposable
{
    private IntPtr _deviceHandle;

    public async Task<bool> IsAvailableAsync()
    {
        // P/Invoke 或硬件 SDK 调用
    }

    public async Task<CardReadResult> ReadCardAsync(CancellationToken ct)
    {
        // 使用 SemaphoreSlim 序列化硬件访问
    }

    public void Dispose() { /* 释放句柄 */ }
}

// Disabled —— 硬件不可用时的降级
public class DisabledCardReader : ICardReader
{
    public Task<bool> IsAvailableAsync() => Task.FromResult(false);
    public Task<CardReadResult> ReadCardAsync(CancellationToken ct)
        => Task.FromResult(new CardReadResult(null, false, "读卡器已禁用"));
}
```

### 第3步：配置驱动的注册

```csharp
// DI 注册
services.AddSingleton<ICardReader>(sp =>
{
    var config = sp.GetRequiredService<IOptions<HardwareOptions>>();
    return config.Value.EnableCardReader switch
    {
        true when IsRealHardwareAvailable() => new RealCardReader(),
        true => new MockCardReader("TEST-UID-001"),
        false => new DisabledCardReader()
    };
});
```

### 第4步：维护实现状态矩阵

在架构文档中维护表格：

```
| 硬件       | 接口            | Mock | Real | Disabled | 状态       |
|------------|-----------------|------|------|----------|------------|
| 读卡器     | ICardReader     | ✅   | ✅   | ✅       | 已完成     |
| 重量传感器 | IWeightSensor   | ✅   | ⬜   | ⬜       | 仅 Mock    |
```

**铁律**：删除 Mock 前必须查看矩阵——Real 未就绪时删掉 Mock 会导致 DI 启动崩溃。

---

## 验证清单

- [ ] 每个硬件接口有 ≥2 个实现
- [ ] Mock 可通过构造函数参数或回调配置行为
- [ ] Disabled 返回"不可用"（不抛异常）
- [ ] 维护实现状态矩阵
- [ ] 切换实现仅需修改配置，不改代码
