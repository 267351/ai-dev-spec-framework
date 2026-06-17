# Work Session State Machine

> **Category**: Coding  
> **Reusable**: ✅ Yes — copy to any project with stateful business workflows  
> **Dependencies**: None (pure pattern)

---

## When to Use

Your business process has a multi-step lifecycle where:
- States have clear transition rules
- Anomalous states (stuck, timeout) need detection
- Both active AND pending states count as "in-progress"

---

## Pattern

### State Design

```
Entering → Working → Exiting → Completed
                         ↘ CompletedWithWarning  (completed but had issues)
```

### Key Design Decisions

1. **Timeout covers ALL incomplete states** (not just "Working")
   - A worker entered but never confirmed → stuck at "Entering"
   - A worker started working but never exited → stuck at "Working"
   - A worker started exiting but never completed → stuck at "Exiting"

2. **"In-progress" list includes intermediate states**
   - Not just `WHERE Status = 'Working'`
   - But `WHERE Status IN ('Entering', 'Working', 'Exiting')`

3. **Explicit confirmation required for edge cases**
   - Empty-hand entry → must call `ConfirmEntryAsync()` or status stays at "Entering" forever

---

## Implementation

```csharp
public enum WorkSessionStatus
{
    Entering = 0,           // Worker entered area, not yet confirmed
    Working = 1,            // Confirmed working
    Exiting = 2,            // Initiated exit process
    Completed = 3,          // Normal completion
    CompletedWithWarning = 4 // Completed with warnings (weight deviation, timeout, etc.)
}

public class WorkSession
{
    public Guid Id { get; set; }
    public WorkSessionStatus Status { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime? EnteredAt { get; set; }
    public DateTime? ExitedAt { get; set; }
    public DateTime? CompletedAt { get; set; }

    // Which operations are valid from current state
    public bool CanConfirmEntry => Status == WorkSessionStatus.Entering;
    public bool CanStartExit => Status == WorkSessionStatus.Working;
    public bool IsActive => Status is WorkSessionStatus.Entering
                                 or WorkSessionStatus.Working
                                 or WorkSessionStatus.Exiting;
}

public class WorkSessionService
{
    public async Task ConfirmEntryAsync(Guid sessionId)
    {
        var session = await GetSessionAsync(sessionId);
        if (!session.CanConfirmEntry)
            throw new InvalidOperationException($"Cannot confirm entry in {session.Status} state");

        session.Status = WorkSessionStatus.Working;
        session.EnteredAt = DateTime.UtcNow;
    }

    public async Task<List<WorkSession>> DetectStuckSessionsAsync(TimeSpan timeout)
    {
        var cutoff = DateTime.UtcNow - timeout;
        return await _db.WorkSessions
            .Where(s => s.IsActive)
            .Where(s => s.Status != WorkSessionStatus.Completed)
            .Where(s => s.CreatedAt < cutoff)
            .ToListAsync();
    }
}
```

---

## Verification

- [ ] All states have clear entry/exit conditions defined
- [ ] Timeout detection covers ALL incomplete states
- [ ] "Active" queries include intermediate states (not just "in progress")
- [ ] Edge cases (empty entry, forced exit) have explicit handling
- [ ] State transitions record timestamps for audit
- [ ] Stuck session detection runs periodically
