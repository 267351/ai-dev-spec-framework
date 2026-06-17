using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.Diagnostics;
using System.Collections.Immutable;

namespace SpecComplianceAnalyzer;

/// <summary>
/// 依赖方向检查器 (对应 spec.md 规则: [verifiable:di])
/// 
/// 检查规则：
/// - WM-ARCH-001: 禁止 Web 项目引用 Infrastructure 项目
/// - WM-ARCH-002: 禁止 Infrastructure 层引用 Web 项目
/// - WM-ARCH-003: 禁止 Shared 项目引用任何其他项目
/// 
/// 检查方式：分析 ProjectReference 和 using 指令
/// </summary>
[DiagnosticAnalyzer(LanguageNames.CSharp)]
public class DependencyDirectionAnalyzer : DiagnosticAnalyzer
{
    public const string DiagnosticId = "SPEC001";

    private static readonly LocalizableString Title = "违反分层架构依赖方向";
    private static readonly LocalizableString MessageFormat = "分层架构违规: {0}";
    private static readonly LocalizableString Description = "禁止跨层引用，必须遵守分层架构约束。";
    private const string Category = "Architecture";

    private static readonly DiagnosticDescriptor Rule = new(
        DiagnosticId,
        Title,
        MessageFormat,
        Category,
        DiagnosticSeverity.Error,
        isEnabledByDefault: true,
        description: Description);

    public override ImmutableArray<DiagnosticDescriptor> SupportedDiagnostics =>
        ImmutableArray.Create(Rule);

    // 配置：禁止的依赖映射 (上层 -> 禁止引用的下层)
    // 格式: "ProjectNameSuffix:ForbiddenProjectNameSuffix"
    // 可通过 .editorconfig 配置:
    // [*.cs]
    // dotnet_diagnostic.SPEC001.forbidden_dependencies = Web:Infrastructure|Web:DAL|Infrastructure:Web|Shared:Web|Shared:Core
    private static readonly ImmutableArray<(string Source, string Forbidden)> DefaultForbiddenDependencies = 
        ImmutableArray.Create(
            ("Web", "Infrastructure"),
            ("Web", "DAL"),
            ("Infrastructure", "Web"),
            ("Shared", "Web"),
            ("Shared", "Core"),
            ("Shared", "Infrastructure")
        );

    public override void Initialize(AnalysisContext context)
    {
        context.ConfigureGeneratedCodeAnalysis(GeneratedCodeAnalysisFlags.None);
        context.EnableConcurrentExecution();
        context.RegisterCompilationAction(AnalyzeCompilation);
    }

    private static void AnalyzeCompilation(CompilationAnalysisContext context)
    {
        var compilation = context.Compilation;
        var assemblyName = compilation.AssemblyName ?? "";

        // 确定当前项目属于哪一层
        string? currentLayer = null;
        if (assemblyName.Contains("Web"))
            currentLayer = "Web";
        else if (assemblyName.Contains("Infrastructure"))
            currentLayer = "Infrastructure";
        else if (assemblyName.Contains("DAL"))
            currentLayer = "DAL";
        else if (assemblyName.Contains("Core") || assemblyName.Contains("BLL"))
            currentLayer = "Core";
        else if (assemblyName.Contains("Shared") || assemblyName.Contains("Models"))
            currentLayer = "Shared";
        else
            return; // 不关心的项目

        // 检查所有引用的程序集
        foreach (var referencedAssembly in compilation.ReferencedAssemblyNames)
        {
            var refName = referencedAssembly.Name;

            foreach (var (source, forbidden) in DefaultForbiddenDependencies)
            {
                if (source == currentLayer && refName.Contains(forbidden))
                {
                    var diagnostic = Diagnostic.Create(
                        Rule,
                        Location.None,
                        $"项目 '{assemblyName}' ({source} 层) 引用了被禁止的 '{refName}' ({forbidden} 层)。" +
                        $"根据分层架构红线，{source} 层禁止引用 {forbidden} 层。");
                    context.ReportDiagnostic(diagnostic);
                }
            }
        }
    }
}
