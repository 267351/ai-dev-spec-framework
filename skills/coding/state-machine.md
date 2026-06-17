# 作业状态机

> **分类**: 编码  
> **可复用**: ✅ 是 — 复制到任何有状态业务流程的项目  
> **依赖**: 无（纯模式）

---

## 适用场景

业务流程有多步生命周期，需要：
- 状态之间有明确的转换规则
- 异常状态（卡住、超时）能被检测
- "进行中"包含活跃态和中间态

---

## 模式

### 状态设计

```
进入中 → 作业中 → 退场中 → 已完成
                       ↘ 带警告完成（完成但有异常）
```

### 关键设计决策

1. **超时覆盖所有未完成状态**（不仅是"作业中"）
   - 人员进入但未确认 → 卡在"进入中"
   - 人员开始作业但未退场 → 卡在"作业中"
   - 人员开始退场但未完成 → 卡在"退场中"

2. **"在场人员"列表包含中间状态**
   - 不是 `WHERE Status = 'Working'`
   - 而是 `WHERE Status IN ('Entering', 'Working', 'Exiting')`

3. **边界情况需要显式确认**
   - 空手进入 → 必须调用 `ConfirmEntryAsync()` 否则状态永远卡在"进入中"

---

## 实现

```csharp
public enum WorkSessionStatus
{
    Entering = 0,               // 人员进入区域，尚未确认
    Working = 1,                // 已确认作业中
    Exiting = 2,                // 发起退场流程
    Completed = 3,              // 正常完成
    CompletedWithWarning = 4    // 完成但有警告（重量偏差、超时等）
}

public class WorkSession
{
    public Guid Id { get; set; }
    public WorkSessionStatus Status { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime? EnteredAt { get; set; }
    public DateTime? ExitedAt { get; set; }
    public DateTime? CompletedAt { get; set; }

    // 当前状态允许哪些操作
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
            throw new InvalidOperationException($"当前状态 {session.Status} 不允许确认进入");

        session.Status = WorkSessionStatus.Working;
        session.EnteredAt = DateTime.UtcNow;
    }

    public async Task<List<WorkSession>> DetectStuckSessionsAsync(TimeSpan timeout)
    {
        var cutoff = DateTime.UtcNow - timeout;
        return await _db.WorkSessions
            .Where(s => s.IsActive)
            .Where(s => s.CreatedAt < cutoff)
            .ToListAsync();
    }
}
```

---

## 验证清单

- [ ] 每个状态的进入/退出条件有明确定义
- [ ] 超时检测覆盖所有未完成状态
- [ ] "活跃"查询包含中间状态（不仅"作业中"）
- [ ] 边界情况（空手进入、强制退场）有显式处理
- [ ] 状态转换记录时间戳，可审计
- [ ] 卡住会话检测定期运行
