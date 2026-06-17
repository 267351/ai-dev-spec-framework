# Unified Configuration Layer

> **Category**: Architecture  
> **Reusable**: ✅ Yes — copy to any .NET project with many configuration options  
> **Dependencies**: .NET Options pattern, Microsoft.Extensions.Options

---

## When to Use

Your project has 5+ `appsettings.json` sections and Options classes scattered across projects. You want:
- Single-method registration for all config
- Strong-typed Options (never read raw `IConfiguration` in services)
- Configuration project at the bottom of the dependency chain

---

## Pattern

```
Project.Configuration (depends on: nothing)
├── Options/
│   ├── ApiOptions.cs         (ApiUrl, Timeout)
│   ├── DbOptions.cs          (ConnectionString, Provider)
│   ├── LogOptions.cs         (LogPath, LogLevel)
│   └── FeatureOptions.cs
└── Extensions/
    ├── ServiceCollectionExtensions.cs   ← ONE method for all config
    └── HostExtensions.cs                ← ONE method for all logging
```

---

## Implementation

### Step 1: Options classes (in Configuration project)

```csharp
// Options/ApiOptions.cs
public class ApiOptions
{
    public const string SectionName = "Api";
    public string MainApiUrl { get; set; } = "http://localhost:5005";
    public string WarehouseApiUrl { get; set; } = "http://localhost:5100";
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

### Step 2: Single registration method

```csharp
// Extensions/ServiceCollectionExtensions.cs
public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddAppConfiguration(this IServiceCollection services, IConfiguration config)
    {
        // All Options in one place
        services.Configure<ApiOptions>(config.GetSection(ApiOptions.SectionName));
        services.Configure<DbOptions>(config.GetSection(DbOptions.SectionName));

        // Named HttpClients with Options binding
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

### Step 3: Single logging method

```csharp
// Extensions/HostExtensions.cs
public static class HostExtensions
{
    public static IHostBuilder UseAppLogging(this IHostBuilder host)
    {
        return host.UseSerilog((ctx, config) =>
        {
            config
                .ReadFrom.Configuration(ctx.Configuration)  // appsettings.json
                .WriteTo.Console()
                .WriteTo.File("logs/app-.log", rollingInterval: RollingInterval.Day);
        });
    }
}
```

### Step 4: Usage in Program.cs

```csharp
var builder = WebApplication.CreateBuilder(args);

// ONE line for all config
builder.Services.AddAppConfiguration(builder.Configuration);

// ONE line for logging
builder.Host.UseAppLogging();
```

---

## Rules

1. **Configuration project NEVER references other projects** — it sits at the bottom
2. **Services NEVER read `IConfiguration` directly** — always inject `IOptions<T>`
3. **Options classes use `const string SectionName`** for consistency
4. **New Options are registered in the single `AddAppConfiguration` method** — no scattered registrations

---

## Verification

- [ ] Configuration project has zero project references
- [ ] All Options classes in one project
- [ ] One extension method registers all config
- [ ] No `IConfiguration["key"]` or `builder.Configuration.GetValue<>()` in services
- [ ] Adding new Options only requires modifying the Options class + one line in `AddAppConfiguration`
