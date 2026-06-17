# 3-Group Search List Pattern

> **Category**: UI / Coding  
> **Reusable**: ✅ Yes — copy to any Blazor/Web project with searchable list pages  
> **Dependencies**: Blazor (concept applies to any frontend framework)

---

## When to Use

Your list page needs search/filter with these characteristics:
- 2-3 search fields with AND logic
- Real-time filtering (type-to-search, no "Search" button)
- Client-side filtering (no re-request to API)
- Works with pagination

---

## Pattern

```
┌──────────────────────────────────────────────────────────┐
│  搜索框1          搜索框2          搜索框3               │
│  [姓名______]     [工号______]     [部门______]           │
│                                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │  Result List (filtered in-memory)                 │    │
│  │  - matching results...                            │    │
│  └──────────────────────────────────────────────────┘    │
│  [<<] [1] [2] [3] [>>]                                   │
└──────────────────────────────────────────────────────────┘
```

---

## Implementation (Blazor)

```razor
@* Search fields — @bind:event="oninput" enables real-time *@
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

@* Filtered list *@
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
// Code-behind
private List<Person> _allItems = new();
private string _searchName = "", _searchCode = "", _searchDept = "";

private IEnumerable<Person> FilteredItems => _allItems
    .Where(p => string.IsNullOrEmpty(_searchName) || p.Name.Contains(_searchName))
    .Where(p => string.IsNullOrEmpty(_searchCode) || p.Code.Contains(_searchCode))
    .Where(p => string.IsNullOrEmpty(_searchDept) || p.Department.Contains(_searchDept))
    .Skip((_currentPage - 1) * _pageSize)
    .Take(_pageSize);

// Setter triggers filter refresh
private string SearchName
{
    get => _searchName;
    set { _searchName = value; _currentPage = 1; /* reset to page 1 on search */ }
}
```

---

## Key Design Decisions

1. **`@bind:event="oninput"`** — filter on every keystroke (not on blur)
2. **AND logic** — all non-empty search terms must match
3. **Memory filtering** — filter already-loaded data, don't re-request API
4. **Reset to page 1** — on any search term change
5. **Empty = wildcard** — empty search field matches everything

---

## Verification

- [ ] Search fields use oninput for real-time filtering
- [ ] Multiple fields combine with AND logic
- [ ] Filtering is client-side (in memory)
- [ ] Pagination resets on search change
- [ ] Empty search field = match all
- [ ] Performance acceptable with 1000+ items (consider virtualization if needed)
