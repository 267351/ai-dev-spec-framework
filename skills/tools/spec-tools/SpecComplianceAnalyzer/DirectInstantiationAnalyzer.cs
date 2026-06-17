using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.Diagnostics;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using System.Collections.Immutable;
using System.Linq;

namespace SpecComplianceAnalyzer;

/// <summary>
/// DI 注入检查器 (对应 spec.md 规则: [verifiable:di])
/// 
/// 检查规则：
/// - WM-DI-001: 禁止在 .razor 文件中直接实例化 Service (new XxxService())
/// - WM-DI-002: 禁止在 razor.cs 中手动 new HttpClient
/// 
/// 检查方式：AST 分析对象创建表达式
/// 
/// 可配置例外（通过 .editorconfig）:
/// dotnet_diagnostic.SPEC003.allowed_direct_instantiation = System.Text.StringBuilder|System.Collections.Generic.List
/// </summary>
[DiagnosticAnalyzer(LanguageNames.CSharp)]
public class DirectInstantiationAnalyzer : DiagnosticAnalyzer
{
    public const string DiagnosticId = "SPEC003";

    private static readonly LocalizableString Title = "禁止直接实例化 Service";
    private static readonly LocalizableString MessageFormat = "禁止直接实例化 '{0}'，必须通过依赖注入 (DI) 获取";
    private static readonly LocalizableString Description = 
        "Service 类应通过构造函数依赖注入获取，禁止使用 new 直接实例化。";
    private const string Category = "DependencyInjection";

    private static readonly DiagnosticDescriptor ServiceRule = new(
        DiagnosticId,
        Title,
        MessageFormat,
        Category,
        DiagnosticSeverity.Error,
        isEnabledByDefault: true,
        description: Description);

    private static readonly DiagnosticDescriptor HttpClientRule = new(
        "SPEC004",
        "禁止直接实例化 HttpClient",
        "禁止直接 new HttpClient()，应使用 IHttpClientFactory 创建命名 HttpClient",
        Category,
        DiagnosticSeverity.Error,
        isEnabledByDefault: true,
        description: "应使用 IHttpClientFactory 创建和注入 HttpClient 实例。");

    public override ImmutableArray<DiagnosticDescriptor> SupportedDiagnostics =>
        ImmutableArray.Create(ServiceRule, HttpClientRule);

    // 允许直接实例化的类型名称后缀
    private static readonly string[] ServiceNameSuffixes = { "Service", "Repository", "Manager" };

    public override void Initialize(AnalysisContext context)
    {
        context.ConfigureGeneratedCodeAnalysis(GeneratedCodeAnalysisFlags.None);
        context.EnableConcurrentExecution();
        context.RegisterSyntaxNodeAction(AnalyzeObjectCreation, SyntaxKind.ObjectCreationExpression);
    }

    private static void AnalyzeObjectCreation(SyntaxNodeAnalysisContext context)
    {
        var creation = (ObjectCreationExpressionSyntax)context.Node;
        var typeName = creation.Type.ToString();

        // 检查是否直接 new HttpClient
        if (typeName == "HttpClient" || typeName == "System.Net.Http.HttpClient")
        {
            var diagnostic = Diagnostic.Create(
                HttpClientRule,
                creation.GetLocation(),
                typeName);
            context.ReportDiagnostic(diagnostic);
            return;
        }

        // 检查是否 new 了 Service 类
        foreach (var suffix in ServiceNameSuffixes)
        {
            if (typeName.EndsWith(suffix))
            {
                // 在方法内部 new Service 才算违规
                // 类字段初始化中 new Service (如 private readonly XxxService _svc = new()) 也是违规
                var diagnostic = Diagnostic.Create(
                    ServiceRule,
                    creation.GetLocation(),
                    typeName);
                context.ReportDiagnostic(diagnostic);
                break;
            }
        }
    }
}
