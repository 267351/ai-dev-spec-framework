# Process Orchestrator (Launcher)

> **Category**: Architecture / Deployment  
> **Reusable**: ✅ Yes — copy to any project with 3+ service processes  
> **Dependencies**: .NET, HTTP health checks

---

## When to Use

Your project has 3+ service processes (API, Web, microservices) that need coordinated startup, health monitoring, and crash recovery. Typical scenarios:
- Blazor SSR + REST API + SignalR Hub
- Microservice suite on single machine
- On-premise deployment without container orchestration

---

## Core Components

### 1. Health Check Endpoint

Every service exposes a health endpoint:

```csharp
// In Program.cs of each service
app.MapGet("/health", () => Results.Ok(new { status = "healthy", timestamp = DateTime.UtcNow }));
```

### 2. Launcher Process

A separate console app that orchestrates startup:

```csharp
var services = new[]
{
    new ServiceConfig { Name = "API", Port = 5005, ExePath = "./Api/App", HealthUrl = "http://localhost:5005/health" },
    new ServiceConfig { Name = "Web", Port = 5193, ExePath = "./Web/App", HealthUrl = "http://localhost:5193/health" },
    new ServiceConfig { Name = "Reader", Port = 5100, ExePath = "./Reader/App", HealthUrl = "http://localhost:5100/health" },
};

// Step 1: Clean ports (kill stale processes)
foreach (var svc in services)
    PortCleaner.EnsurePortFree(svc.Port);

// Step 2: Start in dependency order
foreach (var svc in services)
{
    var process = Process.Start(new ProcessStartInfo
    {
        FileName = svc.ExePath,
        UseShellExecute = false,
        RedirectStandardOutput = true,
    });
    svc.Process = process;

    // Wait for health check
    await WaitForHealthy(svc.HealthUrl, timeout: TimeSpan.FromSeconds(30));
    Console.WriteLine($"[OK] {svc.Name} healthy on :{svc.Port}");
}
```

### 3. Crash Recovery

```csharp
// Monitor and auto-restart
_ = Task.Run(async () =>
{
    while (!_shutdownToken.IsCancellationRequested)
    {
        foreach (var svc in services)
        {
            if (svc.Process?.HasExited == true)
            {
                // Save crash diagnostics
                var crashLog = svc.RecentLogs.TakeLast(50);
                File.WriteAllLines($"logs/crash-{svc.Name}-{DateTime.Now:yyyyMMddHHmmss}.log", crashLog);

                if (svc.AutoRestart)
                {
                    Console.WriteLine($"[RESTART] {svc.Name}");
                    RestartService(svc);
                    await WaitForHealthy(svc.HealthUrl, TimeSpan.FromSeconds(30));
                }
            }
        }
        await Task.Delay(1000);
    }
});
```

### 4. Health Dashboard (optional)

A built-in web UI showing service statuses with SSE (Server-Sent Events):

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

### 5. Ready File (IPC)

After all services are healthy, write a `.ready` file that external scripts poll:

```csharp
File.WriteAllText(".ready", DateTime.UtcNow.ToString("O"));
Console.WriteLine("[READY] All services running");
```

---

## Deployment Integration

Kiosk/sh scripts poll for `.ready` before launching browsers:

```bash
while [ ! -f .ready ]; do sleep 1; done
echo "Services ready, launching browsers..."
```

---

## Verification

- [ ] Services start in correct dependency order
- [ ] Each service validated via `/health` before next starts
- [ ] Crashed services auto-restart (configurable)
- [ ] Crash diagnostics saved (last N log lines + metadata)
- [ ] Health dashboard shows real-time status
- [ ] `.ready` file signals completion
- [ ] Port conflicts cleaned before startup
