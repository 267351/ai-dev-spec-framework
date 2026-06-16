# 共同模式分析

## 一、概述

本文档详细描述从CSO-FORCS和WarehouseMS两个项目中提取的共同开发模式。这些模式在两个项目中都得到验证，具有较高的可复用性。

---

## 二、共同模式清单

### 2.1 架构模式

#### 模式1：分层架构

**描述**：严格分层，单向依赖，禁止反向引用

**两个项目的实现**：

| 项目 | 分层结构 | 依赖方向 |
|------|----------|----------|
| CSO-FORCS | Models <- DAL <- BLL <- Api <- App | 单向向下 |
| WarehouseMS | Shared <- Infrastructure <- Core <- Web | 单向向下 |

**共同特征**：
- 每层有明确职责
- 依赖方向单向（上层依赖下层）
- 禁止反向引用（下层不能引用上层）
- 通过接口解耦

**验证标准**：
1. 检查ProjectReference方向是否符合依赖图
2. 下层项目不引用上层项目
3. `dotnet build`通过

**可复用性**：高 - 任何分层架构的.NET项目均可复用

---

#### 模式2：Repository模式

**描述**：数据访问层抽象，封装数据库操作

**两个项目的实现**：

| 项目 | Repository数量 | 特点 |
|------|----------------|------|
| CSO-FORCS | 20个 | 每个实体一个Repository |
| WarehouseMS | 8个+泛型基类 | 泛型Repository+特化Repository |

**共同特征**：
- 接口+实现分离
- 封装CRUD操作
- 支持查询条件
- 生命周期为Scoped

**验证标准**：
1. 每个Repository有对应接口
2. Repository不包含业务逻辑
3. 通过DI注册

**可复用性**：高 - 数据访问层的标准抽象

---

#### 模式3：Unit of Work模式

**描述**：事务管理，确保多个操作原子性

**两个项目的实现**：

| 项目 | 实现方式 | 特点 |
|------|----------|------|
| CSO-FORCS | EF Core DbContext | 隐式UoW |
| WarehouseMS | IUnitOfWork接口 | 显式UoW |

**共同特征**：
- 通过DbContext管理事务
- SaveChangesAsync提交所有变更
- 生命周期为Scoped

**验证标准**：
1. 多个Repository操作在同一事务中
2. 通过SaveChangesAsync统一提交
3. 异常时自动回滚

**可复用性**：高 - 事务管理的标准模式

---

### 2.2 编码模式

#### 模式4：命名约定

**描述**：遵循Microsoft C#标准命名约定

**两个项目的实现**：

| 元素 | 约定 | 示例 |
|------|------|------|
| Namespace | PascalCase | `LimitedSpaceForeignObject.BLL.Services` |
| Class | PascalCase | `GoodsService` |
| Interface | I前缀+PascalCase | `IGoodsService` |
| Method | PascalCase | `GetByIdAsync` |
| Property | PascalCase | `GoodsName` |
| Private Field | _camelCase | `_goodsRepository` |
| Parameter | camelCase | `goodsCode` |
| Local Variable | camelCase | `existingSession` |
| Async Method | Async后缀 | `GetByIdAsync` |

**验证标准**：
1. 公开类型符合PascalCase
2. 接口有I前缀
3. 私有字段有_前缀
4. 异步方法有Async后缀

**可复用性**：高 - C#社区标准约定

---

#### 模式5：异步编程

**描述**：所有I/O操作使用async/await

**两个项目的实现**：

| 项目 | 异步方法比例 | 特点 |
|------|--------------|------|
| CSO-FORCS | 100% | 所有Repository/Service/Controller方法都是异步 |
| WarehouseMS | 100% | 所有Service/Repository方法都是异步 |

**共同特征**：
- 异步方法有Async后缀
- 返回Task<T>
- 使用await而非.Result/.Wait()
- 接受CancellationToken参数

**验证标准**：
1. 异步方法有Async后缀
2. 无async void（除事件处理器）
3. 使用await而非.Result/.Wait()

**可复用性**：高 - .NET异步编程的通用最佳实践

---

#### 模式6：结构化日志

**描述**：使用Serilog的{Placeholder}语法

**两个项目的实现**：

| 项目 | 日志框架 | 特点 |
|------|----------|------|
| CSO-FORCS | Serilog双系统 | BLL用Serilog.ILogger，API用ILogger<T> |
| WarehouseMS | Serilog via ILogger<T> | 统一使用ILogger<T> |

**共同特征**：
- 使用{Placeholder}而非$""
- 结构化日志便于查询
- 统一配置

**验证标准**：
1. 使用{Placeholder}语法
2. 日志配置通过扩展方法
3. 日志文件按服务分离

**可复用性**：高 - Serilog是.NET生态主流日志库

---

### 2.3 流程模式

#### 模式7：Conventional Commits

**描述**：提交信息格式规范

**两个项目的实现**：

| 项目 | 遵循程度 | 特点 |
|------|----------|------|
| CSO-FORCS | 99% | type(scope): description |
| WarehouseMS | 100% | type(scope): description |

**共同特征**：
- 格式：`type(scope): description`
- 类型：feat/fix/docs/refactor/chore/test/style/build/perf
- 范围可选
- 描述使用英文

**验证标准**：
1. 提交信息符合格式
2. 类型使用标准值
3. 描述简洁明了

**可复用性**：高 - 开源项目标准实践

---

#### 模式8：Spec.md约定文件体系

**描述**：每个核心代码文件对应一个.spec.md文件

**两个项目的实现**：

| 项目 | 文件数量 | 特点 |
|------|----------|------|
| CSO-FORCS | 100+ | 记录设计规范、踩坑记录 |
| WarehouseMS | 100+ | 记录业务规则、禁止项 |

**共同特征**：
- 核心文件有对应.spec.md
- 记录：文件用途、踩过的坑、禁止修改的内容
- 修改代码前必须检查spec.md
- 修改后主动询问是否更新spec.md

**验证标准**：
1. 核心文件有对应.spec.md
2. 修改前加载并审查spec
3. 新坑点记录到spec
4. spec修改需用户批准

**可复用性**：极高 - 解决AI辅助开发"忘记历史"问题的核心创新

---

### 2.4 测试模式

#### 模式9：单元测试

**描述**：使用xUnit + Moq进行单元测试

**两个项目的实现**：

| 项目 | 测试数量 | 特点 |
|------|----------|------|
| CSO-FORCS | 56+ | 测试BLL服务 |
| WarehouseMS | 41 | 测试Core服务 |

**共同特征**：
- 使用xUnit测试框架
- 使用Moq模拟依赖
- 测试类构造函数设置Mock
- 测试方法命名：{Method}_{Scenario}_{ExpectedResult}

**验证标准**：
1. 测试类有完整Mock设置
2. 测试方法命名符合约定
3. 覆盖正常/异常/边界场景
4. `dotnet test`通过

**可复用性**：高 - .NET单元测试的标准模式

---

### 2.5 文档模式

#### 模式10：XML文档注释

**描述**：使用XML文档注释

**两个项目的实现**：

| 项目 | 注释覆盖率 | 特点 |
|------|------------|------|
| CSO-FORCS | ~80% | 公开类和方法 |
| WarehouseMS | ~90% | 公开类和方法 |

**共同特征**：
- 使用`/// <summary>`注释
- 注释公开类和方法
- 中文业务描述
- 英文技术术语

**验证标准**：
1. 公开类有XML文档
2. 公开方法有XML文档
3. 参数有`<param>`标签
4. 返回值有`<returns>`标签

**可复用性**：高 - .NET代码文档标准

---

## 三、共同模式总结

### 3.1 模式分类

| 类别 | 模式数量 | 关键模式 |
|------|----------|----------|
| 架构模式 | 3 | 分层架构、Repository、Unit of Work |
| 编码模式 | 3 | 命名约定、异步编程、结构化日志 |
| 流程模式 | 2 | Conventional Commits、Spec.md体系 |
| 测试模式 | 1 | 单元测试 |
| 文档模式 | 1 | XML文档注释 |

### 3.2 优先级建议

**必须遵守（红线规范）**：
- 分层架构（依赖方向单向）
- 命名约定（代码一致性）
- Spec.md体系（AI辅助开发核心）

**建议遵守（最佳实践）**：
- Repository模式
- Unit of Work模式
- 异步编程
- 结构化日志
- Conventional Commits
- 单元测试
- XML文档注释

---

**分析完成时间**: 2026-06-17  
**分析版本**: v1.0  
**数据来源**: 模板7横向对比分析报告
