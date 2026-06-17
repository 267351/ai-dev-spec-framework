# 统一配置层

> **分类**: 架构  
> **可复用**: ✅ 是 — 复制到配置项较多的 .NET 项目  
> **依赖**: .NET Options 模式, Microsoft.Extensions.Options

---

## 适用场景

项目有 5 个以上 `appsettings.json` 配置段，Options 类分散在各项目中。期望：
- 一行方法注册所有配置
- 强类型 Options（不在 Service 中直接读 `IConfiguration`）
- Configuration 项目位于依赖链最底层

---

## 模式

```
Project.Configuration（不引用任何其他项目）
├── Options/
│   ├── ApiOptions.cs         (ApiUrl, Timeout)
│   ├── DbOptions.cs          (ConnectionString, Provider)
│   ├── LogOptions.cs         (LogPath, LogLevel)
│   └── FeatureOptions.cs
└── Extensions/
    ├── ServiceCollectionExtensions.cs   ← 一个方法注册所有配置
    └── HostExtensions.cs                ← 一个方法配置所有日志
```

---

## 实现

### 第1步：Options 类（放在 Configuration 项目中）

```csharp
// Options/ApiOptions.cs
public class ApiOptions
{
    public const string SectionName = "Api";
    public string MainApiUrl { get; set; } = "http://localhost:5005";
    public int TimeoutSeconds { get; set; } = 30;
}

// Options/DbOptions.cs
public class DbOptions
{
    public const string SectionName = "Database";
    public string ConnectionString { get; set; } = "Data Source=app.db";
    public string Provider { get; set; } = "sqlite";
}
```

### 第2步：一招注册所有配置

```csharp
// Extensions/ServiceCollectionExtensions.cs
public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddAppConfiguration(this IServiceCollection services, IConfiguration config)
    {
        // 所有 Options 集中注册
        services.Configure<ApiOptions>(config.GetSection(ApiOptions.SectionName));
        services.Configure<DbOptions>(config.GetSection(DbOptions.SectionName));

        // 命名的 HttpClient，绑定 Options
        services.AddHttpClient("MainApi", (sp, client) =>
        {
            var opts = sp.GetRequiredService<IOptions<ApiOptions>>().Value;
            client.BaseAddress = new Uri(opts.MainApiUrl);
            client.Timeout = TimeSpan.FromSeconds(opts.TimeoutSeconds);
        });

        return services;
    }
}
```

### 第3步：一招配置所有日志

```csharp
// Extensions/HostExtensions.cs
public static class HostExtensions
{
    public static IHostBuilder UseAppLogging(this IHostBuilder host)
    {
        return host.UseSerilog((ctx, config) =>
        {
            config
                .ReadFrom.Configuration(ctx.Configuration)
                .WriteTo.Console()
                .WriteTo.File("logs/app-.log", rollingInterval: RollingInterval.Day);
        });
    }
}
```

### 第4步：Program.cs 中一行搞定

```csharp
var builder = WebApplication.CreateBuilder(args);

// 一行注册所有配置
builder.Services.AddAppConfiguration(builder.Configuration);

// 一行配置日志
builder.Host.UseAppLogging();
```

---

## 铁律

1. **Configuration 项目绝对不引用其他项目**——它位于依赖链最底层
2. **Service 中绝不直接读 `IConfiguration`**——始终注入 `IOptions<T>`
3. **Options 类使用 `const string SectionName`** 保证一致性
4. **新增 Options 只在唯一的 `AddAppConfiguration` 方法中注册**——不允许散落各处

---

## 验证清单

- [ ] Configuration 项目的项目引用数为零
- [ ] 所有 Options 类集中在一个项目中
- [ ] 一个扩展方法注册全部配置
- [ ] Service 中不存在 `IConfiguration["key"]` 或 `builder.Configuration.GetValue<>()`
- [ ] 新增 Options 只需：新建 Options 类 + 在 `AddAppConfiguration` 中加一行
