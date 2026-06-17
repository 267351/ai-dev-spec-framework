# 【WarehouseMS】项目架构总纲

> 🔗 此文件是 `/home/hys/projects/WarehouseMS/架构总纲.spec.md` 的增强版，
> 添加了可信度标注和审计追踪。用于试点验证增强模板的可行性。

## 0. 三大系统架构

> 项目拆分为三个独立子系统，边界由 `docs/系统架构-三大系统边界.md` 唯一定义。

| 系统 | 职责 | 核心文件 |
|------|------|---------|
| **库房管理系统** | 物资三级分类、入库/领用/回收、库存管理、Excel 导入 | MaterialCategoryService, StockOutService, ImportService |
| **磨料工作效率折算** | 物资效率配置管理、砂轮片折算、标准量计算、效率排名、完成率 | MaterialEfficiencyService, IConversionEngine, WorkloadService |
| **工时录入系统** | 工时记录（实际工时×难度系数）、审核 | WorkHourService, WorkHourAuditService |

**铁律**：三大系统在 Service 层禁止互相调用。跨系统数据聚合仅在 Web 层（看板页面）进行。
**v2.0**：效率参数已从 Material 实体分离至独立的 MaterialEfficiencyConfig 表，由效率系统独立管理。

> **可信度**: ⭐⭐⭐⭐⭐ (项目级架构决策)

---

## 1. 项目概述
库房物资管理系统，.NET 10 + Blazor Web App + SQLite（开发期，可迁移至 SQL Server 2022）。

**核心业务**：
- 物资全链路管理（入库/领用/回收/报废）
- 砂轮片多维度折算（规格系数 × 材质系数 × 砂轮片材质类型匹配）
- 磨锉工工时与工作量双维度评估
- 可视化看板（效率排名、完成率、趋势分析）

### 🏭 核心业务规则：项目-标准-打磨对象-砂轮片材质四层匹配

**设计背景**：不同项目执行不同的技术标准（如 AP1000、华龙一号），同一标准下不同打磨对象需要不同材质的砂轮片。廉江项目执行的可能是 AP1000 标准，另一个项目执行的可能是华龙一号标准——对应的砂轮片材质要求完全不同。

**四层匹配链路**：
```
项目 → 执行标准 → 打磨对象 → 允许的砂轮片材质
```

**关键概念**：

| 概念 | 说明 | 示例 |
|------|------|------|
| 项目 | 产线实际在干的项目 | AP1000、廉江项目、C5 项目 |
| 标准 | 项目执行的技术标准体系 | AP1000 标准、华龙一号标准 |
| 打磨对象 | 被磨金属材质 | 不锈钢、镍基合金、碳钢 |
| 砂轮片材质 | 砂轮片自身的材质类型 | 铝基无铁、碳化硅、不区分材质 |

**示例（AP1000 标准下的对照表）**：

| 打磨对象 | 允许的砂轮片材质 | 推荐 |
|---------|-----------------|------|
| 不锈钢 | 铝基无铁 | ✅ |
| 镍基合金 | 碳化硅 | ✅ |
| 碳钢 | 不区分材质 | ✅ |

**示例（华龙一号标准下的对照表，可能不同）**：

| 打磨对象 | 允许的砂轮片材质 | 推荐 |
|---------|-----------------|------|
| 不锈钢 | 铝基无铁、碳化硅 | 铝基无铁 |
| 镍基合金 | 碳化硅 | ✅ |
| 碳钢 | 不区分材质 | ✅ |

**发放流程**：
```
保管员确认：
1. 磨锉工在哪个项目干活？（项目名称）
2. 打磨的是什么材料？（打磨对象）
       ↓
3. 系统根据【项目→标准→打磨对象】自动查出允许的砂轮片材质
       ↓
4. 保管员只能从匹配的砂轮片材质中选择发放
       ↓
5. 如果磨锉工要求的砂轮片材质不在允许列表中 → 不予发放
```

**可编辑的对照表**：
- 技术人员可以在系统内编辑「标准-材质对照表」
- 修改对照表后，新发放在下次领用时立即生效
- 历史领用记录不受对照表修改影响（已发放的不追溯）

**错误发放后果**：不锈钢打磨用了碳化硅砂轮片 → 打磨效率极低、工件表面质量不合格。

### 👤 身份验证方式

领用和回收环节必须验证领用人身份，支持三种方式：

| 方式 | 说明 | 适用场景 |
|------|------|---------|
| **刷卡** | 员工刷工卡（RFID/IC卡），系统自动识别 | 日常领用/回收，最快 |
| **用户名+密码** | 手动输入工号+密码 | 卡丢失或系统故障时备用 |
| **人脸识别** | 摄像头抓拍，比对已注册的人脸数据 | 高安全要求场景，防止代领 |

**验证规则**：
1. 领用人必须是系统内已注册的磨锉工
2. 刷卡或人脸识别成功后，系统自动填充领用人信息
3. 三种方式任选其一，任意一种验证通过即可继续领用/回收流程
4. 未通过身份验证不允许进行领用/回收操作

---

## 2. 踩过的坑 - 架构级（永久记录）

### 坑1：测试中的时间边界问题 [confidence:validated]
> **可信度**: ⭐⭐⭐⭐⭐ (在测试中反复触发，有明确的修复记录)
**现象**：WorkloadService单元测试中，StockOut记录的UseTime不在查询日期范围内，导致标准砂轮片计算结果为0。
**根源**：WorkloadService的SumStandardWheelsAsync方法会根据UseTime进行过滤，如果UseTime不在查询范围内，该记录不会被计入。
**解决**：在单元测试中，StockOut的UseTime必须设置为查询日期范围内的时间（如`today.ToDateTime(TimeOnly.MinValue)`），而不是`DateTime.UtcNow.AddDays(-1)`。
**预防**：测试辅助方法中，默认时间应使用查询日期范围内的时间。

### 坑2：WorkloadService的除零保护 [confidence:validated]
> **可信度**: ⭐⭐⭐⭐⭐ (实际触发过，有防御代码)
**现象**：当标准工时为0时，效率计算（标准砂轮片 ÷ 标准工时）会导致除以0。
**根源**：数学运算未考虑边界条件。
**解决**：在BuildStats方法中，当standardHours为0时，效率设为0，避免除以0。
**预防**：所有涉及除法的业务计算，都需要检查除数是否为0。

### 坑3：EF Core全局查询过滤器影响测试 [confidence:validated]
> **可信度**: ⭐⭐⭐⭐ (多项目验证的通用问题)
**现象**：AppDbContext配置了软删除过滤器（IsDeleted），测试中创建的数据如果未正确设置IsDeleted字段，可能被过滤掉。
**根源**：EF Core的全局查询过滤器会自动应用到所有查询。
**解决**：测试数据创建时，确保IsDeleted字段为false（默认值）。
**预防**：了解DbContext中配置的所有全局过滤器，避免测试数据被意外过滤。

---

## 3. 禁止修改的内容（架构红线，绝对不能动）

### 🚫 [confidence:validated] 分层架构红线
> **可信度**: ⭐⭐⭐⭐⭐ (由 3 次生产事故验证)
> **验证记录**: 
>   - CSO-FORCS 坑1: 循环依赖导致编译失败
>   - CSO-FORCS 坑3: Web 直接调用 DbContext 导致数据库驱动冲突
>   - WarehouseMS: 跨层引用导致 DI 崩溃
1. **禁止** Shared 项目引用任何其他项目（纯数据定义层，位于最底层）
2. **禁止** Web 项目直接操作 EF Core DbContext（必须通过 Core 层 Service）
3. **禁止** Web 层写业务逻辑（必须下沉到 Core 层）
4. **禁止** Infrastructure 层引用 Web 项目（循环引用红线）
5. **禁止** Core 层直接操作 DbContext（必须通过 Infrastructure 层 Repository）

### 🚫 [confidence:proven] 配置管理红线
> **可信度**: ⭐⭐⭐⭐ (在两个项目中持续验证)
> **提出者**: @architect | **提出日期**: 2026-01-15
1. **禁止**在代码中硬编码任何数据库连接字符串（必须从 appsettings.json 读取）
2. **禁止**在 `.razor` 文件中直接实例化 Service（必须通过 DI 注入）
3. **禁止**在 `.razor` 文件中写复杂的 C# 业务逻辑（必须代码后置到 `.razor.cs`）
4. **禁止**在 `.razor` 文件中写 `<style>` 块（必须用 `.razor.css` 隔离样式）

### 🚫 [confidence:validated] 业务规则红线
> **可信度**: ⭐⭐⭐⭐⭐ (由业务逻辑分析验证，违反将导致数据错误)
1. **禁止**发放砂轮片时不校验项目→标准→打磨对象→砂轮片材质四层匹配关系
2. **禁止**绕过对照表直接发放不匹配材质的砂轮片（即使库存有货）
3. **禁止**入库时物资不标注砂轮片材质类型（铝基无铁/碳化硅/不区分材质）
4. **禁止**领用时不记录项目名称和打磨对象（后续无法追溯和统计）
5. **禁止**修改系数时影响历史领用记录中的快照值
6. **禁止**非技术人员修改标准-材质对照表（权限控制）
7. **禁止**未通过身份验证（刷卡/密码/人脸）即执行领用或回收操作
8. **禁止**非磨锉工角色的人员执行领用操作（角色+身份双重验证）

### 🚫 [confidence:proven] 三大系统边界红线
> **可信度**: ⭐⭐⭐⭐ (由架构设计验证)
> **提出者**: @architect | **提出日期**: 2026-03-01
1. **禁止** MaterialCategoryService 调用 IConversionEngine（分类不承载折算）
2. **禁止** WorkHourService 调用 IConversionEngine（工时不调用折算）
3. **禁止** WorkloadService 写入 StockOut/StockRecycle（效率系统只读库房数据）
4. **禁止** 在分类体系中嵌入折算系数模板（系数存储在 MaterialEfficiencyConfig 实体上）
5. **禁止** Service 层跨系统耦合（跨系统聚合仅限于 Web 层看板页面）

### 🚫 [confidence:consensus] 数据管理红线
> **可信度**: ⭐⭐⭐ (团队共识)
> **提出者**: @team | **提出日期**: 2026-02-01
1. **禁止**在 Service 层直接写原始 SQL（必须通过 EF Core / Repository）
2. **禁止**跳过审批流程直接修改物资库存数据
3. **禁止**删除历史领用/报废记录（软删除或标记作废，保留审计轨迹）

---

## 4. 必须遵守的技术规范

### ✅ [confidence:proven] 项目分层规范
> **可信度**: ⭐⭐⭐⭐ (两个项目的基础架构)
```
WarehouseManagement.Shared/       ← 最底层：实体、枚举、DTO 定义，无依赖
WarehouseManagement.Infrastructure/ ← 数据访问层：引用 Shared
WarehouseManagement.Core/         ← 业务逻辑层：引用 Infrastructure、Shared
WarehouseManagement.Web/          ← 前端层：引用 Core、Shared
```

### ✅ [confidence:consensus] Blazor 组件规范
> **可信度**: ⭐⭐⭐ (团队共识)
- 代码必须后置：`Xxx.razor` + `Xxx.razor.cs`
- 样式必须隔离：`Xxx.razor.css`
- 全局 rendermode：App.razor 设定，页面组件禁止重复设置
- API 调用必须通过 DI 注入的 Service，不能在页面直接 new HttpClient
- 使用 MudBlazor 8.x 组件，保持 UI 风格统一

### ✅ [confidence:consensus] 命名约定
> **可信度**: ⭐⭐⭐ (团队共识)
| 元素 | 约定 | 示例 |
|------|------|------|
| Namespace | PascalCase | `WarehouseManagement.Core.Services` |
| Class | PascalCase | `WorkloadService` |
| Interface | PascalCase + `I` 前缀 | `IWorkloadService` |
| Method | PascalCase | `CalculateWorkloadAsync` |
| Property | PascalCase | `TotalStandardHours` |
| Private Field | `_camelCase` | `_dbContext` |
| 数据库表 | PascalCase 复数 | `Materials`, `WorkHours` |
| 数据库列 | camelCase | `createdAt`, `materialId` |

### ✅ [confidence:consensus] 错误处理规范 [sunset:2026-09-18]
> **可信度**: ⭐⭐⭐ (团队共识)
> ⏰ 此规则在 2026-09-18 前有效，届时重新评估
```csharp
// 使用具体异常类型
throw new ArgumentNullException(nameof(material));
throw new InvalidOperationException("库存不足", ex);

// 使用结构化日志
Log.Error(ex, "领用登记失败，物资ID: {MaterialId}, 数量: {Count}", materialId, count);
```

### ✅ [confidence:preventive] 异步模式 [sunset:2026-09-18]
> **可信度**: ⭐⭐ (预防性规范，未发生过事故)
> **提出者**: @alice | **提出日期**: 2026-06-18
> ⏰ 此规则在 2026-09-18 前有效，届时重新评估
```csharp
// 异步方法使用 Async 后缀
public async Task<WorkloadStatsDto> CalculateWorkloadAsync(int userId, DateOnly start, DateOnly end)
```

---

## 5. 允许的操作

只允许：
1. ✅ 新增功能模块（但必须遵守分层架构和 Blazor 组件规范）
2. ✅ 修复 bug
3. ✅ 性能优化（SQL 查询优化、前端渲染优化）
4. ✅ 补充单元测试
5. ✅ 优化代码可读性和结构

---

## 6. 项目健康检查清单

任何时候怀疑架构被破坏，请对照此清单检查：

- [ ] **Shared 项目**：没有引用任何其他项目？
- [ ] **Web 项目**：没有直接操作 DbContext？
- [ ] **Core 项目**：业务逻辑都在 Service，不在 Controller？
- [ ] **数据库连接**：从配置读取，无硬编码？
- [ ] **Blazor 页面**：`.razor.cs` 代码后置 + `.razor.css` 隔离样式？
- [ ] **Blazor 页面**：没有重复加 `@rendermode`？
- [ ] **依赖注入**：所有 Service 通过 DI 注册和注入？

---

## 7. 维护提示

**此文件是整个项目的架构宪法。任何修改都必须经过团队评审！**

在 CSO-FORCS 项目中，类似的架构红线每条至少浪费了 4 小时以上调试时间：
- 架构分层破坏：花了整整 2 天才把依赖关系掰回来
- Blazor render mode 重复设置：花了 3 天才定位根因

**记住：架构上偷的懒，未来会加倍还回来。**

每次想图省事直接写代码的时候，先看看这个文件，想想前人踩过的坑。

---

## 📋 审计追踪

| 日期 | 操作 | 操作者 | 理由 | 影响文件数 |
|------|------|--------|------|-----------|
| 2026-01-15 | 创建 | @architect | 项目初始化，建立架构约束 | 0 |
| 2026-03-01 | 创建 | @architect | 新增三大系统边界红线 | 0 |
| 2026-04-08 | 强化 | @zhangsan | 循环依赖事故后加强分层约束（参照 CSO-FORCS 坑1） | 5 |
| 2026-05-12 | 验证 | @lisi | 季度审查，确认分层规则有效 | 0 |
| 2026-06-01 | 修改 | @zhangsan | 业务规则新增四层匹配和身份验证规定 | 8 |
| 2026-06-18 | 改造 | AI:deepseek-v4-pro | 增强版模板试点：添加可信度标注 + 审计追踪 + 质疑/Sunset 章节 | 1 |

---

## 💬 质疑记录

> 暂无质疑记录。

---

## ⏰ Sunset 记录

| 规则 | 可信度 | Sunset 日期 | 状态 |
|------|--------|------------|------|
| 错误处理规范 | consensus | 2026-09-18 | 🔵 活跃 |
| 异步模式 | preventive | 2026-09-18 | 🔵 活跃 |
|------|--------|------|------|

---

*此文件由 spec_md_manager_v2.py 增强。原文件路径: /home/hys/projects/WarehouseMS/架构总纲.spec.md*
