# 三组搜索列表模式

> **分类**: UI / 编码  
> **可复用**: ✅ 是 — 复制到任何有搜索列表页的 Blazor/Web 项目  
> **依赖**: Blazor（概念适用于任何前端框架）

---

## 适用场景

列表页需要搜索/过滤，要求：
- 2-3 个搜索框，AND 逻辑组合
- 实时过滤（输入即搜，无需点"搜索"按钮）
- 客户端过滤（不重新请求 API）
- 配合分页

---

## 模式

```
┌──────────────────────────────────────────────────────────┐
│  搜索框1          搜索框2          搜索框3               │
│  [姓名______]     [工号______]     [部门______]           │
│                                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │  结果列表（内存过滤）                              │    │
│  │  - 匹配的结果...                                  │    │
│  └──────────────────────────────────────────────────┘    │
│  [<<] [1] [2] [3] [>>]                                   │
└──────────────────────────────────────────────────────────┘
```

---

## 实现（Blazor）

```razor
@* 搜索框 —— @bind:event="oninput" 实现实时搜索 *@
<MudTextField @bind-Value="_searchName" 
              @bind:event="oninput"
              Label="姓名" 
              Immediate="true" />

<MudTextField @bind-Value="_searchCode" 
              @bind:event="oninput"
              Label="工号" 
              Immediate="true" />

<MudTextField @bind-Value="_searchDept" 
              @bind:event="oninput"
              Label="部门" 
              Immediate="true" />

@* 过滤后的列表 *@
@foreach (var item in FilteredItems)
{
    <MudTr>
        <MudTd>@item.Name</MudTd>
        <MudTd>@item.Code</MudTd>
        <MudTd>@item.Department</MudTd>
    </MudTr>
}
```

```csharp
// 代码后置
private List<Person> _allItems = new();
private string _searchName = "", _searchCode = "", _searchDept = "";
private int _currentPage = 1;
private const int _pageSize = 20;

private IEnumerable<Person> FilteredItems => _allItems
    .Where(p => string.IsNullOrEmpty(_searchName) || p.Name.Contains(_searchName))
    .Where(p => string.IsNullOrEmpty(_searchCode) || p.Code.Contains(_searchCode))
    .Where(p => string.IsNullOrEmpty(_searchDept) || p.Department.Contains(_searchDept))
    .Skip((_currentPage - 1) * _pageSize)
    .Take(_pageSize);

// 搜索值变更时重置到第1页
private void OnSearchChanged()
{
    _currentPage = 1;
}
```

---

## 关键设计决策

1. **`@bind:event="oninput"`** — 每次按键触发过滤（非失焦时）
2. **AND 逻辑** — 所有非空搜索条件必须同时满足
3. **内存过滤** — 过滤已加载的数据，不重新请求 API
4. **搜索时回到第 1 页** — 任何搜索条件变更时重置分页
5. **空 = 通配** — 空搜索框匹配所有数据

---

## 验证清单

- [ ] 搜索框使用 oninput 实现实时过滤
- [ ] 多个搜索框 AND 组合
- [ ] 过滤在客户端内存中完成
- [ ] 搜索变更时分页重置
- [ ] 空搜索框 = 匹配全部
- [ ] 1000+ 数据量下性能可接受（必要时考虑虚拟化）
