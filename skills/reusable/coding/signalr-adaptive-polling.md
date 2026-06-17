# SignalR 自适应轮询 + 重连机制

> **分类**: 编码 / 实时通信  
> **可复用**: ✅ 是 — 复制到任何需要实时数据推送的 Blazor 项目  
> **依赖**: Microsoft.AspNetCore.SignalR.Client

---

## 适用场景

Blazor（或 .NET）应用需要服务端→客户端实时数据推送，且要求：
- 轮询间隔自适应（活跃时快、空闲时慢）
- 断线自动重连，重连后刷新待处理消息
- 支持多种消息类型

---

## 服务端（后台服务 + Hub）

```csharp
// Hub
public class MonitoringHub : Hub
{
    // 客户端连接后接收广播
}

// 后台服务 —— 自适应间隔广播数据
public class MonitoringBroadcastService : BackgroundService
{
    private readonly IHubContext<MonitoringHub> _hub;
    private const int ActiveIntervalMs = 30_000;   // 有活跃会话时 30s
    private const int IdleIntervalMs = 60_000;     // 空闲时 60s

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

## 客户端（SignalR Service）

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

        // 注册消息处理器
        _connection.On<object>("UpdateActiveSessions", data =>
            InvokeHandlersAsync("UpdateActiveSessions", data));

        // 重连：刷新待处理消息
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

    // 注册重连后需执行的操作
    public void OnReconnect(Action action)
        => _pendingOnReconnect.Add(action);

    // 发送跨屏指令
    public async Task SendCameraCommandAsync(string command, Guid sessionId)
        => await _connection.SendAsync("CameraCommand", new { Command = command, SessionId = sessionId });

    public async ValueTask DisposeAsync()
    {
        if (_connection != null)
            await _connection.DisposeAsync();
    }
}
```

---

## 使用示例：跨屏协调

```csharp
// A 屏：用户登录后，通知 B 屏拍照
await SignalR.SendCameraCommandAsync("CaptureEntryPhotos", sessionId);

// B 屏：收到拍照指令
SignalR.On<CameraCommand>("CameraCommand", cmd =>
{
    if (cmd.Command == "CaptureEntryPhotos")
        _cameraService.Capture(cmd.SessionId);
});

// 断线重连后重试未完成的扫码指令
SignalR.OnReconnect(() =>
{
    if (_pendingQrScan != null)
        SignalR.SendCameraCommandAsync("QRScanStarted", _pendingQrScan.SessionId);
});
```

---

## 验证清单

- [ ] 后台服务使用自适应间隔（活跃/空闲）
- [ ] 客户端自动重连（指数退避）
- [ ] 重连后刷新待处理消息
- [ ] 支持注册多种消息处理器
- [ ] 连接状态变更触发 UI 更新
- [ ] 组件/页面销毁时优雅释放连接
