using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.Diagnostics;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using System.Collections.Immutable;

namespace SpecComplianceAnalyzer;

/// <summary>
/// 异步方法命名检查器 (对应 spec.md 规则: [verifiable:naming])
/// 
/// 检查规则：
/// - WM-NAMING-001: 返回 Task/Task<T> 的公共方法必须以 Async 结尾
/// 
/// 检查方式：AST 分析方法签名
/// </summary>
[DiagnosticAnalyzer(LanguageNames.CSharp)]
public class AsyncSuffixAnalyzer : DiagnosticAnalyzer
{
    public const string DiagnosticId = "SPEC002";

    private static readonly LocalizableString Title = "异步方法命名不规范";
    private static readonly LocalizableString MessageFormat = "异步方法 '{0}' 必须以 'Async' 后缀结尾";
    private static readonly LocalizableString Description = 
        "返回 Task 或 Task<T> 的公共/内部方法应以 'Async' 后缀结尾，提高代码可读性。";
    private const string Category = "Naming";

    private static readonly DiagnosticDescriptor Rule = new(
        DiagnosticId,
        Title,
        MessageFormat,
        Category,
        DiagnosticSeverity.Warning,
        isEnabledByDefault: true,
        description: Description);

    public override ImmutableArray<DiagnosticDescriptor> SupportedDiagnostics =>
        ImmutableArray.Create(Rule);

    public override void Initialize(AnalysisContext context)
    {
        context.ConfigureGeneratedCodeAnalysis(GeneratedCodeAnalysisFlags.None);
        context.EnableConcurrentExecution();
        context.RegisterSyntaxNodeAction(AnalyzeMethodDeclaration, SyntaxKind.MethodDeclaration);
    }

    private static void AnalyzeMethodDeclaration(SyntaxNodeAnalysisContext context)
    {
        var methodDecl = (MethodDeclarationSyntax)context.Node;

        // 只检查 public 和 internal 方法
        if (!methodDecl.Modifiers.Any(m => m.IsKind(SyntaxKind.PublicKeyword) || 
                                           m.IsKind(SyntaxKind.InternalKeyword)))
            return;

        var methodName = methodDecl.Identifier.Text;

        // 跳过已经以 Async 结尾的方法
        if (methodName.EndsWith("Async"))
            return;

        // 检查返回类型是否为 Task 或 Task<T>
        var returnType = methodDecl.ReturnType;
        var returnTypeText = returnType.ToString();

        // 处理 Task 和 Task<T>
        bool returnsTask = returnTypeText == "Task" ||
                          (returnTypeText.StartsWith("Task<") && returnTypeText.EndsWith(">"));

        // 处理 ValueTask 和 ValueTask<T>
        bool returnsValueTask = returnTypeText == "ValueTask" ||
                               (returnTypeText.StartsWith("ValueTask<") && returnTypeText.EndsWith(">"));

        if (returnsTask || returnsValueTask)
        {
            var diagnostic = Diagnostic.Create(
                Rule,
                methodDecl.Identifier.GetLocation(),
                methodName);
            context.ReportDiagnostic(diagnostic);
        }
    }
}
