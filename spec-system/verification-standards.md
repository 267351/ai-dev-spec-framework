# 验证标准

## 一、概述

本文档为"可复用的AI辅助开发规范体系"中的每个规范定义明确的验证标准，区分红线规范（必须遵守）和最佳实践（建议遵守）。

---

## 二、验证标准分类

### 2.1 红线规范（必须遵守）

**定义**：违反红线规范的代码不能合并到主分支

**验证方式**：自动化检查+人工审查

**处理方式**：必须修复才能通过

### 2.2 最佳实践（建议遵守）

**定义**：建议遵守但不强制的规范

**验证方式**：代码审查+工具检查

**处理方式**：可以有例外，但需要说明原因

---

## 三、核心规范验证标准（L1）

### C01：分层架构

**规范描述**：严格分层，单向依赖，禁止反向引用

**验证标准**：

| 检查项 | 验证方法 | 优先级 |
|--------|----------|--------|
| 依赖方向正确 | 检查ProjectReference方向 | 红线 |
| 无反向引用 | 下层项目不引用上层项目 | 红线 |
| 接口解耦 | 通过接口而非具体类依赖 | 最佳实践 |

**验证命令**：
```bash
# 检查依赖方向
dotnet build 2>&1 | grep "circular dependency"

# 检查ProjectReference
grep -r "ProjectReference" src/ --include="*.csproj"
```

**验证结果**：
- ✅ 通过：依赖方向正确，无反向引用
- ❌ 失败：存在反向引用或循环依赖

---

### C02：命名约定

**规范描述**：遵循Microsoft C#标准命名约定

**验证标准**：

| 检查项 | 验证方法 | 优先级 |
|--------|----------|--------|
| 类名PascalCase | 静态分析 | 红线 |
| 接口I前缀 | 静态分析 | 红线 |
| 私有字段_前缀 | 静态分析 | 红线 |
| 异步方法Async后缀 | 静态分析 | 红线 |
| 参数camelCase | 静态分析 | 最佳实践 |

**验证命令**：
```bash
# 使用Roslyn Analyzer
dotnet format --verify-no-changes

# 使用StyleCop
dotnet build -p:EnforceCodeStyleInBuild=true
```

**验证结果**：
- ✅ 通过：所有命名符合约定
- ❌ 失败：有命名不符合约定

---

### C03：异步编程

**规范描述**：所有I/O操作使用async/await

**验证标准**：

| 检查项 | 验证方法 | 优先级 |
|--------|----------|--------|
| 异步方法Async后缀 | 静态分析 | 红线 |
| 无async void | 静态分析 | 红线 |
| 使用await | 代码审查 | 红线 |
| 接受CancellationToken | 代码审查 | 最佳实践 |

**验证命令**：
```bash
# 检查async void
grep -r "async void" src/ --include="*.cs"

# 检查.Result/.Wait()
grep -r "\.Result\b\|\.Wait()" src/ --include="*.cs"
```

**验证结果**：
- ✅ 通过：异步编程符合规范
- ❌ 失败：存在async void或.Result/.Wait()

---

### C04：Spec.md体系

**规范描述**：每个核心代码文件对应一个.spec.md文件

**验证标准**：

| 检查项 | 验证方法 | 优先级 |
|--------|----------|--------|
| 核心文件有spec.md | 文件检查 | 红线 |
| 修改前审查spec.md | 流程检查 | 红线 |
| 新坑点记录到spec.md | 流程检查 | 最佳实践 |
| spec修改需用户批准 | 流程检查 | 红线 |

**验证命令**：
```bash
# 检查spec.md覆盖
python3 tools/spec_md_manager.py report

# 检查spec.md格式
grep -l "## 文件用途" *.spec.md
```

**验证结果**：
- ✅ 通过：核心文件有spec.md，修改前已审查
- ❌ 失败：缺少spec.md或未审查

---

### C05：Conventional Commits

**规范描述**：提交信息格式规范

**验证标准**：

| 检查项 | 验证方法 | 优先级 |
|--------|----------|--------|
| 格式正确 | 正则匹配 | 红线 |
| 类型标准 | 白名单检查 | 红线 |
| 描述简洁 | 长度检查 | 最佳实践 |

**验证命令**：
```bash
# 检查提交格式
git log --format="%s" | grep -E "^(feat|fix|docs|refactor|chore|test|style|build|perf)(\(.+\))?: .{1,72}$"

# 使用commitlint
npx commitlint --from HEAD~1
```

**验证结果**：
- ✅ 通过：提交信息符合格式
- ❌ 失败：提交信息不符合格式

---

### C06：单元测试

**规范描述**：使用xUnit + Moq进行单元测试

**验证标准**：

| 检查项 | 验证方法 | 优先级 |
|--------|----------|--------|
| 测试通过 | dotnet test | 红线 |
| 核心逻辑有测试 | 覆盖率检查 | 红线 |
| 测试命名规范 | 代码审查 | 最佳实践 |
| Mock设置完整 | 代码审查 | 最佳实践 |

**验证命令**：
```bash
# 运行测试
dotnet test

# 检查覆盖率
dotnet test /p:CollectCoverage=true /p:CoverletOutput=coverage.json
```

**验证结果**：
- ✅ 通过：测试通过，核心逻辑有覆盖
- ❌ 失败：测试失败或核心逻辑无覆盖

---

### C07：XML文档注释

**规范描述**：公开类和方法有XML文档注释

**验证标准**：

| 检查项 | 验证方法 | 优先级 |
|--------|----------|--------|
| 公开类有XML文档 | 静态分析 | 红线 |
| 公开方法有XML文档 | 静态分析 | 红线 |
| 参数有param标签 | 静态分析 | 最佳实践 |
| 返回值有returns标签 | 静态分析 | 最佳实践 |

**验证命令**：
```bash
# 生成文档警告
dotnet build -p:GenerateDocumentationFile=true -warnaserror

# 检查XML文档
grep -r "/// <summary>" src/ --include="*.cs" | wc -l
```

**验证结果**：
- ✅ 通过：公开类和方法有XML文档
- ❌ 失败：缺少XML文档

---

## 四、最佳实践验证标准（L2）

### B01：Repository模式

**验证标准**：
1. 接口+实现分离
2. 封装CRUD操作
3. 不包含业务逻辑
4. 通过DI注册

**验证命令**：
```bash
# 检查Repository接口
grep -r "IRepository" src/ --include="*.cs" | head -10

# 检查DI注册
grep -r "AddScoped.*Repository" src/ --include="*.cs"
```

---

### B02：Unit of Work

**验证标准**：
1. 通过DbContext管理事务
2. SaveChangesAsync提交变更
3. 生命周期为Scoped

**验证命令**：
```bash
# 检查UoW接口
grep -r "IUnitOfWork" src/ --include="*.cs"

# 检查SaveChangesAsync
grep -r "SaveChangesAsync" src/ --include="*.cs" | head -10
```

---

### B03：结构化日志

**验证标准**：
1. 使用{Placeholder}语法
2. 日志配置通过扩展方法
3. 日志文件按服务分离

**验证命令**：
```bash
# 检查结构化日志
grep -r 'LogInformation\|LogWarning\|LogError' src/ --include="*.cs" | head -10

# 检查Serilog配置
grep -r "UseSerilog" src/ --include="*.cs"
```

---

### B04：错误处理

**验证标准**：
1. 统一的错误处理策略
2. 用户友好的错误消息
3. 错误日志记录

**验证命令**：
```bash
# 检查try-catch
grep -r "try" src/ --include="*.cs" | wc -l

# 检查异常处理
grep -r "catch.*Exception" src/ --include="*.cs" | head -10
```

---

### B05：代码审查

**验证标准**：
1. PR审查流程
2. 自动化检查
3. 审查清单

**验证命令**：
```bash
# 检查PR模板
ls -la .github/PULL_REQUEST_TEMPLATE.md

# 检查CI/CD
ls -la .github/workflows/
```

---

### B06：测试覆盖

**验证标准**：
1. 核心逻辑有测试覆盖
2. 覆盖率达标
3. 测试质量高

**验证命令**：
```bash
# 检查覆盖率
dotnet test /p:CollectCoverage=true /p:CoverletOutput=coverage.json

# 查看覆盖率报告
dotnet tool install -g dotnet-reportgenerator-globaltool
reportgenerator -reports:coverage.json -targetdir:coverage-report
```

---

### B07：部署脚本

**验证标准**：
1. 标准化部署流程
2. 跨平台支持
3. 配置管理

**验证命令**：
```bash
# 检查部署脚本
ls -la deploy.sh deploy.ps1

# 检查部署脚本功能
./deploy.sh --help
```

---

### B08：回滚机制

**验证标准**：
1. 升级前备份
2. 失败时回滚
3. 数据保护

**验证命令**：
```bash
# 检查升级脚本
ls -la upgrade.sh

# 检查回滚功能
./upgrade.sh --help | grep rollback
```

---

### B09：变更日志

**验证标准**：
1. Keep a Changelog格式
2. 按日期倒序
3. 变更类型明确

**验证命令**：
```bash
# 检查CHANGELOG.md
ls -la CHANGELOG.md

# 检查格式
grep -E "^## \[.*\]" CHANGELOG.md | head -5
```

---

### B10：架构文档

**验证标准**：
1. Mermaid图表
2. 实测数据
3. 与代码一致

**验证命令**：
```bash
# 检查架构文档
ls -la docs/architecture.md

# 检查Mermaid图表
grep -l "```mermaid" docs/*.md
```

---

## 五、场景规范验证标准（L3）

### S01：硬件抽象层

**验证标准**：
1. 接口定义清晰
2. Mock实现存在
3. 实现状态矩阵维护

**验证命令**：
```bash
# 检查HAL接口
grep -r "I.*Reader\|I.*Sensor\|I.*Scanner" src/ --include="*.cs"

# 检查Mock实现
grep -r "Disabled.*\|Mock.*" src/ --include="*.cs"
```

---

### S02：双子系统架构

**验证标准**：
1. 两个API项目独立
2. 两个App宿主独立
3. 共享层无特有逻辑

**验证命令**：
```bash
# 检查API项目
ls -la src/ | grep Api

# 检查App项目
ls -la src/ | grep App
```

---

### S03：三大系统边界

**验证标准**：
1. Service层不跨系统调用
2. 跨系统聚合在Web层
3. 边界文档完整

**验证命令**：
```bash
# 检查边界文档
ls -la docs/系统架构-三大系统边界.md

# 检查跨系统调用
grep -r "IConversionEngine\|IWorkHourService" src/WarehouseManagement.Core/Services/ --include="*.cs"
```

---

### S04：Strategy+Factory

**验证标准**：
1. 策略接口定义清晰
2. 工厂通过DI注入
3. 新策略易于扩展

**验证命令**：
```bash
# 检查策略接口
grep -r "IMaterialConsumptionStrategy" src/ --include="*.cs"

# 检查工厂
grep -r "MaterialConsumptionStrategyFactory" src/ --include="*.cs"
```

---

### S05：Result模式

**验证标准**：
1. Service方法返回Result
2. 错误码有统一前缀
3. 前端检查IsSuccess

**验证命令**：
```bash
# 检查Result类
grep -r "class Result" src/ --include="*.cs"

# 检查Result使用
grep -r "Result\." src/ --include="*.cs" | head -10
```

---

### S06：API异常处理

**验证标准**：
1. Controller有try/catch
2. 返回BadRequest
3. 前端友好错误

**验证命令**：
```bash
# 检查Controller异常处理
grep -r "try" src/Api/Controllers/ --include="*.cs" | wc -l

# 检查BadRequest
grep -r "BadRequest" src/Api/Controllers/ --include="*.cs" | head -10
```

---

### S07：验证前置

**验证标准**：
1. 独立Validate方法
2. Register复用验证
3. 前端提前调用

**验证命令**：
```bash
# 检查Validate方法
grep -r "Validate.*Async" src/ --include="*.cs"

# 检查Register方法
grep -r "Register.*Async" src/ --include="*.cs"
```

---

### S08：AGENTS.md索引

**验证标准**：
1. AGENTS.md ≤ 100行
2. 无重复内容
3. Skills路由完整

**验证命令**：
```bash
# 检查AGENTS.md长度
wc -l AGENTS.md

# 检查Skills路由
grep -r "skills/" AGENTS.md
```

---

### S09：偏差检测

**验证标准**：
1. 偏差类型定义清晰
2. 检测流程完整
3. 审批机制严格

**验证命令**：
```bash
# 检查偏差检测文档
ls -la AGENTS.md.spec.md

# 检查偏差类型
grep -A 10 "偏差类型" AGENTS.md.spec.md
```

---

### S10：SQLite内存测试

**验证标准**：
1. 测试基类完整
2. 每个测试独立数据库
3. 资源正确清理

**验证命令**：
```bash
# 检查测试基类
grep -r "ServiceTestBase" tests/ --include="*.cs"

# 检查SQLite内存
grep -r "DataSource=:memory:" tests/ --include="*.cs"
```

---

### S11：一键跨平台部署

**验证标准**：
1. Linux/Windows双平台
2. 相对路径
3. 可移植部署

**验证命令**：
```bash
# 检查部署脚本
ls -la deploy.sh deploy.ps1

# 检查相对路径
grep -r "localhost\|127.0.0.1" deploy.sh
```

---

### S12：升级保护与回滚

**验证标准**：
1. 升级前备份
2. 数据保留
3. 失败回滚

**验证命令**：
```bash
# 检查升级脚本
ls -la upgrade.sh

# 检查备份功能
./upgrade.sh --help | grep backup
```

---

### S13：Kiosk双屏模式

**验证标准**：
1. .ready信号等待
2. 浏览器检测
3. 状态记忆

**验证命令**：
```bash
# 检查Kiosk脚本
grep -A 20 "start-kiosk" deploy.sh

# 检查.ready信号
grep -r "\.ready" deploy.sh
```

---

### S14：业务规则引用

**验证标准**：
1. BR-xxx-xxx编号
2. 规则文档完整
3. 代码引用正确

**验证命令**：
```bash
# 检查业务规则引用
grep -r "BR-" src/ --include="*.cs" | head -10

# 检查业务规则文档
ls -la docs/业务规则参考.md
```

---

### S15：坑点记录

**验证标准**：
1. 坑点记录完整
2. 解决方案明确
3. 定期回顾

**验证命令**：
```bash
# 检查坑点记录
grep -r "坑[0-9]" src/ --include="*.cs" | head -10

# 检查spec.md坑点
grep -l "## 踩过的坑" *.spec.md | wc -l
```

---

## 六、验证工具推荐

### 6.1 静态分析工具

| 工具 | 用途 | 配置文件 |
|------|------|----------|
| **Roslyn Analyzer** | C#代码分析 | .editorconfig |
| **StyleCop** | 代码风格检查 | stylecop.json |
| **SonarQube** | 代码质量检查 | sonar-project.properties |

### 6.2 测试工具

| 工具 | 用途 | 配置文件 |
|------|------|----------|
| **xUnit** | 单元测试 | .csproj |
| **Moq** | Mock框架 | .csproj |
| **Coverlet** | 代码覆盖率 | .csproj |

### 6.3 文档工具

| 工具 | 用途 | 配置文件 |
|------|------|----------|
| **spec_md_manager.py** | Spec.md管理 | tools/spec_md_manager.py |
| **Mermaid** | 架构图表 | docs/*.md |

### 6.4 CI/CD工具

| 工具 | 用途 | 配置文件 |
|------|------|----------|
| **GitHub Actions** | CI/CD | .github/workflows/ |
| **GitLab CI** | CI/CD | .gitlab-ci.yml |

---

**文档完成时间**: 2026-06-17  
**文档版本**: v1.0  
**数据来源**: 规范体系结构+项目实际验证
