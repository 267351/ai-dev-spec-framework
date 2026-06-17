# HAL (Hardware Abstraction Layer) with Triple Implementation

> **Category**: Architecture  
> **Reusable**: ✅ Yes — copy this file to any project with hardware/sensor dependencies  
> **Dependencies**: None (pure design pattern)

---

## When to Use

Your project interacts with physical hardware (sensors, card readers, cameras, printers) and you need to:
- Develop and test without real hardware
- Switch between mock and real implementations via config
- Gracefully degrade when hardware is unavailable

---

## Pattern

For every hardware interface, provide **three implementations**:

```
Hardware Interface (e.g. ICardReader)
├── Mock Implementation     ← for dev/test (configurable behavior)
├── Real Implementation     ← for production (real hardware)
└── Disabled Implementation ← for graceful degradation (hardware absent)
```

---

## Implementation

### Step 1: Define the interface

```csharp
// src/Project.HAL/Interfaces/ICardReader.cs
public interface ICardReader
{
    Task<bool> IsAvailableAsync();
    Task<CardReadResult> ReadCardAsync(CancellationToken ct);
}

public record CardReadResult(string Uid, bool Success, string Error);
```

### Step 2: Create three implementations

```csharp
// Mock — configurable for tests
public class MockCardReader : ICardReader
{
    private readonly string _mockUid;
    public MockCardReader(string mockUid) => _mockUid = mockUid;

    public Task<bool> IsAvailableAsync() => Task.FromResult(true);
    public Task<CardReadResult> ReadCardAsync(CancellationToken ct)
        => Task.FromResult(new CardReadResult(_mockUid, true, null));
}

// Real — wraps actual hardware
public class RealCardReader : ICardReader, IDisposable
{
    private IntPtr _deviceHandle;

    public async Task<bool> IsAvailableAsync()
    {
        // P/Invoke or hardware SDK call
    }

    public async Task<CardReadResult> ReadCardAsync(CancellationToken ct)
    {
        // Blocking hardware access with SemaphoreSlim
    }

    public void Dispose() { /* release handle */ }
}

// Disabled — graceful fallback
public class DisabledCardReader : ICardReader
{
    public Task<bool> IsAvailableAsync() => Task.FromResult(false);
    public Task<CardReadResult> ReadCardAsync(CancellationToken ct)
        => Task.FromResult(new CardReadResult(null, false, "Card reader disabled"));
}
```

### Step 3: Configuration-driven registration

```csharp
// DI registration
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

### Step 4: Maintain implementation status matrix

Keep a table in your architecture doc:

```
| Hardware      | Interface      | Mock | Real | Disabled | Status    |
|---------------|----------------|------|------|----------|-----------|
| Card Reader   | ICardReader    | ✅   | ✅   | ✅       | Complete  |
| Weight Sensor | IWeightSensor  | ✅   | ⬜   | ⬜       | Mock only |
```

**Rule**: Never delete a Mock implementation without checking the matrix — deleting a Mock when no Real exists causes DI crash.

---

## Verification

- [ ] Each hardware interface has ≥2 implementations
- [ ] Mock can be configured via constructor params or callbacks
- [ ] Disabled returns "unavailable" (not exception)
- [ ] Implementation matrix is maintained
- [ ] Switching implementations only requires config change
