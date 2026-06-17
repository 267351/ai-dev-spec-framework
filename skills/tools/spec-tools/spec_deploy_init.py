#!/usr/bin/env python3
"""
spec.md 部署初始化 —— 自动分析新项目结构，生成架构总纲

用法:
  python3 tools/spec-tools/spec_deploy_init.py /path/to/new-project
  python3 tools/spec-tools/spec_deploy_init.py /path/to/new-project --dry-run   # 只输出预览
  python3 tools/spec-tools/spec_deploy_init.py /path/to/new-project --openai    # 调 AI 自动补全

工作流程:
  1. 扫描项目结构 (.csproj, .slnx, 目录树)
  2. 推理分层架构、依赖关系、技术栈
  3. 生成架构总纲.spec.md（自动填入能推理的内容）
  4. 标记需要人工确认的 [待确认] 项
"""

import os
import re
import sys
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from xml.etree import ElementTree as ET


def scan_project(target_dir: str) -> dict:
    """扫描项目结构，提取元信息"""
    target = Path(target_dir)
    if not target.exists():
        print(f"❌ 目录不存在: {target}")
        sys.exit(1)

    info = {
        "name": target.name,
        "projects": [],
        "solutions": [],
        "layers": [],
        "dependencies": defaultdict(list),
        "tech_stack": set(),
        "namespaces": set(),
        "error_patterns": [],
        "naming_conventions": {},
        "has_tests": False,
        "has_blazor": False,
        "has_api": False,
        "has_database": False,
        "di_framework": None,
        "existing_agents_md": None,
    }

    # 1. 扫描解决方案文件
    for sln in target.rglob("*.sln"):
        info["solutions"].append(str(sln.relative_to(target)))
    for slnx in target.rglob("*.slnx"):
        info["solutions"].append(str(slnx.relative_to(target)))

    # 2. 扫描项目文件
    for csproj in target.rglob("*.csproj"):
        proj_name = csproj.stem
        proj_rel = str(csproj.relative_to(target))
        proj_info = {
            "name": proj_name,
            "path": proj_rel,
            "references": [],
            "packages": [],
            "target_framework": None,
        }

        try:
            tree = ET.parse(csproj)
            root = tree.getroot()

            # SDK-style csproj 无 XML 命名空间；兼容两种
            def get_local(name):
                return name.split("}")[-1] if "}" in name else name

            # 提取 TargetFramework
            for el in root.iter():
                if get_local(el.tag) == "TargetFramework" and el.text:
                    proj_info["target_framework"] = el.text
                    info["tech_stack"].add(f".NET {el.text.replace('net', '')}")
                    break

            # 提取 ProjectReference
            for el in root.iter():
                if get_local(el.tag) == "ProjectReference":
                    ref_path = el.get("Include", "")
                    if ref_path:
                        ref_name = Path(ref_path).stem
                        proj_info["references"].append(ref_name)
                        info["dependencies"][proj_name].append(ref_name)

            # 提取 PackageReference 并识别技术栈
            for el in root.iter():
                if get_local(el.tag) == "PackageReference":
                    pkg_name = el.get("Include", "")
                    if pkg_name:
                        proj_info["packages"].append(pkg_name)
                        # 识别技术栈
                        if "EntityFrameworkCore" in pkg_name or "EFCore" in pkg_name:
                            info["has_database"] = True
                            info["tech_stack"].add("EF Core")
                        if "Blazor" in pkg_name:
                            info["has_blazor"] = True
                            info["tech_stack"].add("Blazor")
                        if "MudBlazor" in pkg_name:
                            info["tech_stack"].add("MudBlazor")
                        if "Microsoft.AspNetCore" in pkg_name:
                            info["has_api"] = True
                        if "Serilog" in pkg_name or "NLog" in pkg_name:
                            info["tech_stack"].add(pkg_name.split(".")[0])
                        if "xUnit" in pkg_name or "NUnit" in pkg_name:
                            info["has_tests"] = True
                            info["tech_stack"].add("xUnit" if "xUnit" in pkg_name else "NUnit")
                        if "Moq" in pkg_name:
                            info["tech_stack"].add("Moq")
                        if "Autofac" in pkg_name:
                            info["di_framework"] = "Autofac"
                        if "SignalR" in pkg_name:
                            info["tech_stack"].add("SignalR")
        except Exception:
            pass

        # 推理项目层级
        name_lower = proj_name.lower()
        if any(k in name_lower for k in ["web", "ui", "frontend", "client"]):
            proj_info["layer"] = "Web"
        elif any(k in name_lower for k in ["api", "server", "host"]):
            proj_info["layer"] = "API"
        elif any(k in name_lower for k in ["core", "bll", "business", "service", "domain"]):
            proj_info["layer"] = "Core"
        elif any(k in name_lower for k in ["infrastructure", "dal", "data", "repository"]):
            proj_info["layer"] = "Infrastructure"
        elif any(k in name_lower for k in ["shared", "model", "common", "contract"]):
            proj_info["layer"] = "Shared"
        elif "test" in name_lower:
            proj_info["layer"] = "Test"
        else:
            proj_info["layer"] = "Unknown"

        info["projects"].append(proj_info)
        if proj_info["layer"] not in info["layers"]:
            info["layers"].append(proj_info["layer"])

    # 3. 检查现有 AGENTS.md
    agents_md = target / "AGENTS.md"
    if agents_md.exists():
        info["existing_agents_md"] = agents_md.read_text(encoding="utf-8")[:2000]

    # 4. 扫描代码中的命名约定和错误模式
    cs_files = list(target.rglob("*.cs"))[:50]  # 采样前50个
    method_returns = defaultdict(int)
    error_count = 0
    try_catch_count = 0
    for cs_file in cs_files:
        try:
            content = cs_file.read_text(encoding="utf-8")
            # 提取命名空间
            ns_matches = re.findall(r'namespace\s+(\S+)', content)
            info["namespaces"].update(ns_matches)
            # 异步方法后缀
            async_methods = re.findall(r'(?:public|private|protected|internal)\s+.*?(?:Task|ValueTask)\S*\s+(\w+)\s*\(', content)
            for m in async_methods:
                method_returns["async"] += 1
                if m.endswith("Async"):
                    method_returns["async_suffixed"] += 1
            # try-catch 模式
            try_catch_count += len(re.findall(r'try\s*\{', content))
            # BadRequest 模式
            if "BadRequest" in content:
                error_count += 1
        except Exception:
            pass

    if method_returns.get("async", 0) > 0:
        ratio = method_returns.get("async_suffixed", 0) / method_returns["async"]
        if ratio > 0.5:
            info["naming_conventions"]["async_suffix"] = "遵循"
        elif ratio > 0:
            info["naming_conventions"]["async_suffix"] = "部分遵循"

    if try_catch_count > 0 and error_count > 0:
        info["error_patterns"].append("Controller try/catch + BadRequest")

    # 5. 排序层级（从上到下）
    layer_order = {
        "Shared": 0, "Models": 0,
        "Infrastructure": 1, "DAL": 1,
        "Core": 2, "BLL": 2,
        "API": 3,
        "Web": 4, "UI": 4,
    }
    info["layers"].sort(key=lambda l: layer_order.get(l, 99))

    return info


def infer_arch_rules(info: dict) -> list:
    """根据项目结构推理架构红线"""
    rules = []
    layers = info["layers"]
    projects = info["projects"]
    deps = info["dependencies"]

    # 规则1: 分层依赖方向
    if "Web" in layers and "Infrastructure" in layers:
        rules.append({
            "category": "分层架构红线",
            "confidence": "proven",
            "rules": [
                "**禁止** Web 项目直接操作 EF Core DbContext（必须通过 Core/Service 层）",
                "**禁止** Web 层写业务逻辑（必须下沉到 Core 层）",
                "**禁止** Infrastructure 层引用 Web 项目（循环引用红线）",
            ]
        })
    if "Shared" in layers:
        rules.append({
            "category": "分层架构红线",
            "confidence": "validated",
            "item": "**禁止** Shared 项目引用任何其他项目（纯数据定义层，位于最底层）",
        })

    # 规则2: 配置管理
    rules.append({
        "category": "配置管理红线",
        "confidence": "proven",
        "rules": [
            "**禁止**在代码中硬编码任何数据库连接字符串（必须从 appsettings.json 读取）",
            "**禁止**在代码中硬编码 URL、端口号、文件路径",
        ]
    })

    # 规则3: Blazor 相关
    if info["has_blazor"]:
        rules.append({
            "category": "Blazor 前端红线",
            "confidence": "proven",
            "rules": [
                "**禁止**在 `.razor` 文件中直接实例化 Service（必须通过 DI 注入）",
                "**禁止**在 `.razor` 文件中写复杂的 C# 业务逻辑（必须代码后置到 `.razor.cs`）",
                "**禁止**在 `.razor` 文件中写 `<style>` 块（必须用 `.razor.css` 隔离样式）",
            ]
        })

    # 规则4: 命名约定
    if info["naming_conventions"].get("async_suffix"):
        rules.append({
            "category": "命名约定",
            "confidence": "consensus",
            "item": "**建议** 异步方法使用 Async 后缀",
        })

    # 规则5: 错误处理
    if info.get("has_api") or "API" in layers:
        rules.append({
            "category": "API 规范",
            "confidence": "proven",
            "rules": [
                "**必须** Controller 方法使用 try/catch + BadRequest(ex.Message)",
                "**禁止** Controller 返回 HTTP 500（必须 catch 后返回 4xx）",
            ]
        })

    # 规则6: 数据库
    if info["has_database"]:
        rules.append({
            "category": "数据管理红线",
            "confidence": "proven",
            "rules": [
                "**禁止**在 Service 层直接写原始 SQL（必须通过 EF Core / Repository）",
                "**禁止**删除历史数据（软删除或标记作废，保留审计轨迹）",
            ]
        })

    return rules


def build_arch_spec(info: dict, rules: list, existing_content: str = None) -> str:
    """生成架构总纲.spec.md 内容，带引导式提示"""
    today = datetime.now().strftime("%Y-%m-%d")
    tech = ", ".join(sorted(info["tech_stack"])) if info["tech_stack"] else "（未自动检测到，请填写）"
    layers_desc = " → ".join(info["layers"]) if info["layers"] else "（未自动检测到）"

    parts = [
        f"# 【{info['name']}】项目架构总纲",
        "",
        "## 1. 项目概述",
        "",
        "<!-- ═══════════════════════════════════════════",
        "💡 请回答以下问题，然后删除本注释块：",
        "   1. 这个项目解决什么业务问题？一句话描述。",
        "   2. 核心用户是谁？（管理员/操作员/外部用户/...）",
        "   3. 有没有多个子系统？各自的职责是什么？",
        "   （参考：WarehouseMS 是「工业研磨物资全链路管理」，CSO-FORCS 是「有限空间作业安全管控」）",
        "═══════════════════════════════════════════ -->",
        "",
        f"**项目定位**：（请填写一句话描述）",
        f"**技术栈**：{tech}",
        f"**分层架构**：{layers_desc}",
    ]

    # 自动检测到的项目列表
    if info["projects"]:
        parts.append("")
        parts.append("**项目结构**（自动检测）：")
        parts.append("| 项目 | 层级 | 引用 |")
        parts.append("|------|------|------|")
        for p in info["projects"]:
            refs = ", ".join(p["references"][:3]) if p["references"] else "无"
            parts.append(f"| {p['name']} | {p['layer']} | {refs} |")

    parts.extend([
        "",
        "---",
        "",
        "## 2. 踩过的坑 - 架构级（永久记录）",
        "",
        "> 暂无。发现架构级坑点后在此记录：现象 → 根源 → 解决 → 预防。",
        "> 例如：循环依赖导致编译失败、CSS 隔离失效、迁移历史不一致 等。",
        "",
        "---",
        "",
        "## 3. 禁止修改的内容（架构红线）",
        "",
        "<!-- ═══════════════════════════════════════════",
        "💡 以下规则由工具根据项目结构自动推理。请逐条确认：",
        "   ✅ = 保留          ⚠️ = 需修改           ❌ = 删除",
        "   ───────────────────────────────────────────",
        "   发散思考：",
        "   - 有没有「不明显的」耦合？（比如通过静态类/事件/消息队列间接耦合）",
        "   - 有没有「只在这个项目有效的」特殊约束？",
        "   - 有没有第三方库强加的约束？（如 MudBlazor 要求特定 DI 注册顺序）",
        "═══════════════════════════════════════════ -->",
        "",
    ])

    # 按类别输出规则
    by_category = defaultdict(list)
    for r in rules:
        cat = r.get("category", "其他")
        by_category[cat].append(r)

    for cat, cat_rules in by_category.items():
        confidence = cat_rules[0].get("confidence", "consensus")
        conf_emoji = {"validated": "🔴", "proven": "🟡", "consensus": "🟢", "preventive": "🔵", "speculative": "⚪"}
        parts.append(f"### 🚫 [confidence:{confidence}] {cat}")
        parts.append(f"> 推理置信度: {conf_emoji.get(confidence, '⚪')} {confidence} / 状态: [✅保留 / ⚠️修改 / ❌删除]")
        parts.append("")

        for r in cat_rules:
            if "rules" in r:
                for i, item in enumerate(r["rules"], 1):
                    parts.append(f"{i}. {item}")
            elif "item" in r:
                parts.append(f"1. {r['item']}")
        parts.append("")

    # 发散思维提示
    parts.extend(_build_thinking_prompts(info))

    parts.extend([
        "---",
        "",
        "## 4. 必须遵守的技术规范",
        "",
    ])

    # 技术规范引导
    parts.extend(_build_tech_guide(info))

    parts.extend([
        "---",
        "",
        "## 5. 允许的操作",
        "",
        "只允许：",
        "1. ✅ 新增功能模块（必须遵守分层架构）",
        "2. ✅ 修复 bug",
        "3. ✅ 性能优化",
        "4. ✅ 补充单元测试",
        "5. ✅ 优化代码可读性和结构",
        "",
        "<!-- 💡 发散：是否有些操作「可以但需要审批」？如：修改数据库迁移、删除 spec.md -->",
        "",
        "---",
        "",
        "## 6. 项目健康检查清单",
        "",
    ])

    for p in info["projects"]:
        layer = p["layer"]
        if layer in ("Web", "API"):
            parts.append(f"- [ ] **{p['name']}**：没有直接操作 DbContext？")
        elif layer == "Shared":
            parts.append(f"- [ ] **{p['name']}**：没有引用任何其他项目？")
        elif layer == "Core":
            parts.append(f"- [ ] **{p['name']}**：业务逻辑都在 Service？")
    parts.extend([
        "- [ ] **配置**：无硬编码？从 appsettings 读取？",
        "- [ ] **中间件**：顺序正确（UseRouting → UseAuth → MapControllers）？",
        "",
    ])

    if info.get("has_blazor"):
        parts.append("- [ ] **Blazor**：页面没有重复加 @rendermode？")

    parts.extend([
        "",
        "---",
        "",
        "## 7. 维护提示",
        "",
        "**此文件是项目架构宪法。任何修改需团队评审。**",
        "架构上偷的懒，未来会加倍还回来。",
        "",
        "---",
        "",
        "## 📋 审计追踪",
        "",
        "| 日期 | 操作 | 操作者 | 理由 | 影响文件数 |",
        "|------|------|--------|------|-----------|",
        f"| {today} | 创建 | spec_deploy_init.py | 自动分析项目结构后初始化 | 0 |",
        "",
        "---",
        "",
        "## 💬 质疑记录",
        "",
        "> 暂无质疑记录。",
        "",
        "---",
        "",
        "## ⏰ Sunset 记录",
        "",
        "> 暂无 Sunset 记录。",
        "",
        "---",
        "",
        "*本文件由 spec_deploy_init.py 自动生成。搜索 [✅保留 / ⚠️修改 / ❌删除] 逐条确认规则。*",
    ])

    return "\n".join(parts)


def _build_thinking_prompts(info: dict) -> list:
    """生成发散思维提示"""
    prompts = [
        "",
        "---",
        "",
        "### 🤔 需要你确认的发散性问题",
        "",
        "> 以下问题没有标准答案，需要根据项目实际情况判断。",
        "> 回答后把结论填入上方的规则中（保留/修改/删除）。",
        "",
    ]

    if info["has_database"]:
        prompts.extend([
            "**🔹 数据库策略**",
            "- 开发期和生产环境用同一个数据库类型吗？（如 SQLite → SQL Server）",
            "- 软删除策略：哪些表需要软删除？哪些可以硬删除？",
            "- 数据库迁移：谁来管理？CI 自动执行还是人工执行？",
            "- 有没有需要保留审计日志的敏感操作（如库存变更、权限修改）？",
            "",
        ])

    if info["has_blazor"]:
        prompts.extend([
            "**🔹 Blazor 渲染策略**",
            "- 渲染模式：SSR / InteractiveServer / InteractiveWebAssembly / InteractiveAuto？",
            "- 全局 rendermode 在哪里设置？页面组件是否可以单独覆盖？",
            "- 哪些页面需要实时更新（SignalR）？哪些可以静态 SSR？",
            "- 是否有双屏/多屏场景？布局组件如何处理？",
            "",
        ])

    if info["has_api"] or "API" in info.get("layers", []):
        prompts.extend([
            "**🔹 API 设计**",
            "- Controller 返回格式统一吗？（Result<T> / IActionResult / 直接返 DTO）",
            "- 异常处理策略：Controller 层 catch 一切 → BadRequest？还是让中间件统一处理？",
            "- 有没有版本控制？（/api/v1/ vs /api/v2/）",
            "- 认证方式：JWT / Cookie / API Key？多个 API 进程如何共享认证？",
            "",
        ])

    # 通用发散问题
    prompts.extend([
        "**🔹 团队约定**",
        "- 代码审查：PR 必须几人 approve？有没有必须检查的清单？",
        "- 测试策略：单元测试覆盖率目标？集成测试用真实数据库还是 InMemory？",
        "- Git 策略：分支模型（GitFlow / Trunk-Based）？commit message 格式？",
        "- 部署频率：每日？每周？按需？谁有权限触发部署？",
        "",
        "**🔹 安全边界**",
        "- 有没有绝对不能出现在日志中的敏感数据？（密码、身份证号、手机号）",
        "- 有没有必须在内网才能访问的接口？",
        "- 文件上传：大小限制？类型白名单？存储位置？",
        "",
    ])

    return prompts


def _build_tech_guide(info: dict) -> list:
    """生成技术规范填写引导"""
    guide = [
        "<!-- ═══════════════════════════════════════════",
        "💡 技术规范不需要「发明」——直接引用团队已在用的规范即可。",
        "   如果没有现成规范，填写以下常见项：",
        "═══════════════════════════════════════════ -->",
        "",
        "### ✅ 命名约定",
        "| 元素 | 约定 | 示例 |",
        "|------|------|------|",
        "| Namespace | [待确认] | （如 WarehouseManagement.Core.Services）",
        "| Class / Interface | [待确认] | （如 IWorkloadService / WorkloadService）",
        "| Method | [待确认] | （如 CalculateWorkloadAsync）",
        "| Private Field | [待确认] | （如 _dbContext / _logger）",
        "| 数据库表 | [待确认] | （如 Materials / WorkHours）",
        "",
    ]

    if info["has_database"]:
        guide.extend([
            "### ✅ 数据访问规范",
            f"- **ORM**：EF Core（已检测）",
            "- **仓储模式**：[待确认] 是否使用 Repository 封装 DbContext？",
            "- **迁移策略**：[待确认] 开发期重置 vs 生产增量迁移？",
            "- **查询优化**：[待确认] AsNoTracking / SplitQuery / 全局过滤器",
            "",
        ])

    if info["has_blazor"]:
        guide.extend([
            "### ✅ Blazor 组件规范",
            "- 代码后置：`Xxx.razor` + `Xxx.razor.cs`",
            "- 样式隔离：`Xxx.razor.css`",
            "- 全局 rendermode：App.razor 设定，页面组件禁止重复设置",
            "- DI 注入：通过 `@inject` 或构造函数注入，禁止 `new Service()`",
        ])
        if "MudBlazor" in info["tech_stack"]:
            guide.append("- UI 组件库：MudBlazor（已检测），保持风格统一")
        guide.append("")

    guide.extend([
        "### ✅ 错误处理规范",
        "```csharp",
        "// [待确认] 使用具体异常类型",
        "throw new ArgumentNullException(nameof(xxx));",
        "throw new InvalidOperationException(\"描述\");",
        "",
        "// [待确认] 使用结构化日志（检测到 Serilog/NLog 时填写）",
        "Log.Error(ex, \"操作失败，参数: {Param}\", value);",
        "```",
        "",
        "### ✅ 异步模式",
        "```csharp",
        "// [待确认] 异步方法是否必须 Async 后缀？",
        "public async Task<ResultDto> DoSomethingAsync(int id)",
        "```",
        "",
        "<!-- 💡 发散：你们项目有没有特殊的异步规则？如：",
        "   - ConfigureAwait(false) 是否必须？",
        "   - CancellationToken 是否必须传递？",
        "   - async void 是否完全禁止（除事件处理器外）？",
        "-->",
        "",
    ])

    return guide


def cmd_init(target_dir: str, dry_run: bool = False, openai: bool = False):
    """主流程"""
    target = Path(target_dir)
    info = scan_project(str(target))
    rules = infer_arch_rules(info)
    content = build_arch_spec(info, rules)

    # 输出项目分析摘要
    print("\n" + "=" * 60)
    print(f"  项目分析: {info['name']}")
    print("=" * 60)
    print(f"\n📦 发现 {len(info['projects'])} 个项目:")
    for p in info["projects"]:
        print(f"   [{p['layer']:<14}] {p['name']}")
        if p["references"]:
            print(f"                   引用: {', '.join(p['references'][:5])}")
    if info["tech_stack"]:
        print(f"\n🔧 技术栈: {', '.join(sorted(info['tech_stack']))}")
    print(f"\n🏗️  推理的分层: {' → '.join(info['layers']) if info['layers'] else '(未检测到)'}")
    print(f"📋 生成的架构规则: {len(rules)} 组")

    arch_file = target / "架构总纲.spec.md"

    if dry_run:
        print(f"\n📄 预览: {arch_file.name}")
        print("-" * 60)
        print(content[:3000])
        if len(content) > 3000:
            print(f"\n... 共 {len(content)} 字符")
        return

    # 检查是否已存在
    if arch_file.exists():
        existing = arch_file.read_text(encoding="utf-8")
        # 简单检查是否是自动生成的文件
        if "spec_deploy_init.py" in existing:
            resp = input(f"\n⚠️  {arch_file.name} 已存在（由本工具生成）。覆盖? [y/N]: ")
        else:
            resp = input(f"\n⚠️  {arch_file.name} 已存在。覆盖? [y/N]: ")
        if resp.lower() not in ("y", "yes"):
            print("  已跳过。")
            return

    arch_file.write_text(content, encoding="utf-8")
    print(f"\n✅ 已生成: {arch_file}")

    # 统计待确认项
    todo_count = content.count("[待确认]")
    if todo_count > 0:
        print(f"\n⚠️  文件中还有 {todo_count} 处 [待确认] 需要人工填写")
        print(f"   搜索 [待确认] 即可定位")

    if openai:
        print(f"\n🤖 将以下 Prompt 发送给 AI 即可自动补全:")
        print(f"   (openai 模式待实现)")
        # TODO: 调用 OpenAI API 自动补全 [待确认] 项

    print(f"\n下一步:")
    print(f"  1. 搜索 [待确认] 并填写项目特有的业务约束")
    print(f"  2. python3 tools/spec-tools/spec_md_manager_v2.py scan --smart")
    print(f"  3. python3 tools/spec-tools/spec_md_manager_v2.py create --smart\n")


def main():
    parser = argparse.ArgumentParser(
        description="spec.md 部署初始化 —— 自动分析项目结构，生成架构总纲",
    )
    parser.add_argument("target", help="目标项目目录")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不写入文件")
    parser.add_argument("--openai", action="store_true", help="调用 AI 自动补全 (待实现)")
    args = parser.parse_args()
    cmd_init(args.target, args.dry_run, args.openai)


if __name__ == "__main__":
    main()
