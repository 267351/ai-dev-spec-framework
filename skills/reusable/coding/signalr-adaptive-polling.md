# SignalR Adaptive Polling + Reconnection

> **Category**: Coding / Real-time  
> **Reusable**: ✅ Yes — copy to any Blazor project needing real-time updates  
> **Dependencies**: Microsoft.AspNetCore.SignalR.Client

---

## When to Use

Your Blazor (or .NET) app needs real-time server→client data push with:
- Adaptive polling interval (faster when active, slower when idle)
- Reconnection with pending message flush
- Multiple message type support

---

## Server Side (Background Service + Hub)

```csharp
// Hub
public class MonitoringHub : Hub
{
    // Clients connect and receive broadcasts
}

// Background service — broadcasts data on adaptive interval
public class MonitoringBroadcastService : BackgroundService
{
    private readonly IHubContext<MonitoringHub> _hub;
    private const int ActiveIntervalMs = 30_000;   // 30s when sessions active
    private const int IdleIntervalMs = 60_000;     // 60s when idle

    protected override async Task ExecuteAsync(CancellationToken ct)
    {
        while (!ct.IsCancellationRequested)
        {
            var sessions = GetActiveSessions();
            await _hub.Clients.All.SendAsync("UpdateActiveSessions", sessions, ct);

            var interval = sessions.Any() ? ActiveIntervalMs : IdleIntervalMs;
            await Task.Delay(interval, ct);
        }
    }
}
```

---

## Client Side (SignalR Service)

```csharp
public class SignalRService : IAsyncDisposable
{
    private HubConnection _connection;
    private readonly List<Func<string, object, Task>> _handlers = new();
    private readonly List<Action> _pendingOnReconnect = new();

    public event Action<bool>? ConnectionStateChanged;

    public async Task StartAsync(string hubUrl)
    {
        _connection = new HubConnectionBuilder()
            .WithUrl(hubUrl)
            .WithAutomaticReconnect(new[] { TimeSpan.Zero, TimeSpan.FromSeconds(2), TimeSpan.FromSeconds(10) })
            .Build();

        // Register all handlers
        _connection.On<object>("UpdateActiveSessions", data =>
            InvokeHandlersAsync("UpdateActiveSessions", data));

        // Reconnect: flush pending actions
        _connection.Reconnected += async (_) =>
        {
            ConnectionStateChanged?.Invoke(true);
            foreach (var action in _pendingOnReconnect)
                action();
            _pendingOnReconnect.Clear();
        };

        _connection.Closed += (_) =>
        {
            ConnectionStateChanged?.Invoke(false);
            return Task.CompletedTask;
        };

        await _connection.StartAsync();
    }

    public void OnReconnect(Action action)
        => _pendingOnReconnect.Add(action);

    public async ValueTask DisposeAsync()
    {
        if (_connection != null)
            await _connection.DisposeAsync();
    }
}
```

---

## Usage Example: Cross-Screen Coordination

```csharp
// A-Screen: when user logs in, tell B-Screen to take photos
await SignalR.SendAsync("CameraCommand", new { Command = "CaptureEntryPhotos", SessionId });

// B-Screen: receives command, takes photos
SignalR.On<CameraCommand>("CameraCommand", cmd =>
{
    if (cmd.Command == "CaptureEntryPhotos")
        _cameraService.Capture(cmd.SessionId);
});

// On reconnect, retry pending QR scan commands
SignalR.OnReconnect(() =>
{
    if (_pendingQrScan != null)
        SignalR.SendAsync("CameraCommand", _pendingQrScan);
});
```

---

## Verification

- [ ] Background service uses adaptive interval (active/idle)
- [ ] Client auto-reconnects with exponential backoff
- [ ] Pending messages flushed on reconnect
- [ ] Multiple handler registration supported
- [ ] Connection state changes trigger UI update
- [ ] Graceful disposal on component/page teardown
