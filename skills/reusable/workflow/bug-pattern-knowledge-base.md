# Bug 模式知识库

> **分类**: 工作流  
> **可复用**: ✅ 是 — 复制到任何项目，按技术栈适配 Bug 模式  
> **依赖**: 无（纯知识管理模式）

---

## 适用场景

团队反复踩同样的坑。希望 AI 助手从历史 Bug 中学习，不再生成同样的错误代码。

---

## 模式

维护一个按类别组织的结构化 Bug 登记表。AI 在修改相关代码区域前自动读取。

---

## 模板

```markdown
# Bug 模式登记表

## Blazor 框架陷阱

### BUG-001: 嵌套 RenderMode 导致状态丢失
- **现象**: 页面导航后组件状态重置
- **根因**: App.razor 已全局设置 rendermode，个别页面又加了 @rendermode，产生嵌套渲染边界
- **修复**: 只在 App.razor 设置一次 rendermode；页面/组件中绝不添加
- **检测**: 在 .razor 文件中搜索 @rendermode

### BUG-002: 路由参数大小写敏感
- **现象**: 页面参数首次渲染时为 null
- **根因**: 查询字符串的 [Parameter] 大小写敏感；@page "/goods/{GoodsId}" 和 [Parameter] public string GoodsId 必须完全匹配
- **修复**: 参数名与路由模板 {ParameterName} 严格一致

## 架构陷阱

### BUG-003: 循环项目引用
- **现象**: 编译报错"检测到循环依赖"
- **根因**: 项目 A 引用 B，B 又引用 A
- **修复**: 提取共享类型到第三个项目；绝不创建双向项目引用
- **检测**: `dotnet build` 或检查 csproj 的 ProjectReference 图

## 数据陷阱

### BUG-004: EF Core WAL 模式未启用
- **现象**: 并发写入时出现"database is locked"
- **根因**: SQLite 默认 journal_mode=delete 导致写锁
- **修复**: 连接字符串必须包含 `Journal Mode=WAL`；或在启动时执行 `PRAGMA journal_mode=WAL`
- **检测**: 检查连接字符串是否含 "WAL"
```

---

## 使用方式

1. **新增 Bug**：记录现象 + 根因 + 修复方案 + 检测方法
2. **AI 修改代码时**：AI 先读 Bug 登记表 → 检查修改区域是否有已知 Bug
3. **Bug 修复后**：验证登记表条目、如有方案变更则更新

---

## 验证清单

- [ ] 每个 Bug 包含：现象 / 根因 / 修复 / 检测方法
- [ ] Bug 按类别组织（框架 / 架构 / 数据 / API）
- [ ] AI 修改相关代码前自动读取登记表
- [ ] 新 Bug 在 24h 内补充到登记表
- [ ] 检测方法是可执行的（不是描述性的一句空话）
