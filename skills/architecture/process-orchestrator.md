# 进程编排器（Launcher）

> **分类**: 架构 / 部署  
> **可复用**: ✅ 是 — 复制到有 3 个以上服务进程的项目  
> **依赖**: .NET, HTTP 健康检查

---

## 适用场景

项目有 3 个以上服务进程（API、Web、微服务），需要协调启动、健康监控、崩溃恢复。典型场景：
- Blazor SSR + REST API + SignalR Hub
- 单机部署的微服务套件
- 无容器编排的本地部署

---

## 核心组件

### 1. 健康检查端点

每个服务暴露健康检查接口：

```csharp
// 每个服务的 Program.cs
app.MapGet("/health", () => Results.Ok(new { status = "healthy", timestamp = DateTime.UtcNow }));
```

### 2. 启动编排

一个独立的控制台程序负责按顺序启动：

```csharp
var services = new[]
{
    new ServiceConfig { Name = "API",    Port = 5005, ExePath = "./Api/App", HealthUrl = "http://localhost:5005/health" },
    new ServiceConfig { Name = "Web",    Port = 5193, ExePath = "./Web/App", HealthUrl = "http://localhost:5193/health" },
    new ServiceConfig { Name = "Reader", Port = 5100, ExePath = "./Reader/App", HealthUrl = "http://localhost:5100/health" },
};

// 第1步：清理端口（杀掉残留进程）
foreach (var svc in services)
    PortCleaner.EnsurePortFree(svc.Port);

// 第2步：按依赖顺序依次启动
foreach (var svc in services)
{
    var process = Process.Start(new ProcessStartInfo
    {
        FileName = svc.ExePath,
        UseShellExecute = false,
        RedirectStandardOutput = true,
    });
    svc.Process = process;

    // 等待健康检查通过
    await WaitForHealthy(svc.HealthUrl, timeout: TimeSpan.FromSeconds(30));
    Console.WriteLine($"[OK] {svc.Name} 已在 :{svc.Port} 启动");
}
```

### 3. 崩溃恢复

```csharp
// 监控并自动重启
_ = Task.Run(async () =>
{
    while (!_shutdownToken.IsCancellationRequested)
    {
        foreach (var svc in services)
        {
            if (svc.Process?.HasExited == true)
            {
                // 保存崩溃诊断信息
                var crashLog = svc.RecentLogs.TakeLast(50);
                File.WriteAllLines($"logs/crash-{svc.Name}-{DateTime.Now:yyyyMMddHHmmss}.log", crashLog);

                if (svc.AutoRestart)
                {
                    Console.WriteLine($"[重启] {svc.Name}");
                    RestartService(svc);
                    await WaitForHealthy(svc.HealthUrl, TimeSpan.FromSeconds(30));
                }
            }
        }
        await Task.Delay(1000);
    }
});
```

### 4. 健康面板（可选）

内置 Web 界面，通过 SSE 实时显示服务状态：

```csharp
app.MapGet("/dashboard/stream", async (HttpContext ctx) =>
{
    ctx.Response.ContentType = "text/event-stream";
    while (!ctx.RequestAborted.IsCancellationRequested)
    {
        var statuses = GetServiceStatuses();
        await ctx.Response.WriteAsync($"data: {JsonSerializer.Serialize(statuses)}\n\n");
        await Task.Delay(1000);
    }
});
```

### 5. 就绪文件（进程间通信）

所有服务健康后，写入 `.ready` 文件供外部脚本轮询：

```csharp
File.WriteAllText(".ready", DateTime.UtcNow.ToString("O"));
Console.WriteLine("[就绪] 所有服务已启动");
```

---

## 部署集成

Kiosk/Shell 脚本轮询 `.ready` 后再启动浏览器：

```bash
while [ ! -f .ready ]; do sleep 1; done
echo "服务已就绪，正在启动浏览器..."
```

---

## 验证清单

- [ ] 服务按依赖顺序启动
- [ ] 每个服务通过 `/health` 验证后才启动下一个
- [ ] 崩溃服务自动重启（可配置开关）
- [ ] 崩溃时保存诊断日志（最后 N 行日志 + 进程元数据）
- [ ] 健康面板显示实时状态
- [ ] `.ready` 文件标记全部就绪
- [ ] 端口冲突在启动前清理
