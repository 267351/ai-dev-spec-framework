# Bug Pattern Knowledge Base

> **Category**: Workflow  
> **Reusable**: ✅ Yes — copy to any project, adapt bug patterns to your tech stack  
> **Dependencies**: None (pure knowledge management pattern)

---

## When to Use

Your team repeatedly encounters the same bugs. You want AI assistants to learn from past mistakes so they don't regenerate the same broken code.

---

## Pattern

Maintain a structured bug registry organized by category. AI reads it before modifying code in the affected area.

---

## Template

```markdown
# Bug Pattern Registry

## Blazor Framework Traps

### BUG-001: Nested RenderMode Causes State Loss
- **Phenomenon**: Component state resets on navigation
- **Root Cause**: Adding `@rendermode="InteractiveServer"` to a page when `App.razor` already sets it globally creates nested render boundaries
- **Fix**: Set rendermode ONCE in `App.razor`; NEVER add to individual pages/components
- **Detection**: Check for `@rendermode` in .razor files

### BUG-002: Route Parameter Case Sensitivity
- **Phenomenon**: Page parameters are null on first render
- **Root Cause**: `[Parameter]` from query string is case-sensitive; `@page "/goods/{GoodsId}"` vs `[Parameter] public string GoodsId`
- **Fix**: Match parameter name exactly with route template `{ParameterName}`

## Architecture Traps

### BUG-003: Circular Project Reference
- **Phenomenon**: Build error "circular dependency detected"
- **Root Cause**: Project A references B, and B references A
- **Fix**: Extract shared types to a third project; never create bidirectional project references
- **Detection**: `dotnet build` or check csproj `ProjectReference` graph

## Data Traps

### BUG-004: EF Core WAL Mode Not Enabled
- **Phenomenon**: "database is locked" under concurrent writes
- **Root Cause**: SQLite default journal_mode=delete causes write locks
- **Fix**: Connection string must include `Journal Mode=WAL`; or set `PRAGMA journal_mode=WAL` on startup
- **Detection**: Check connection string for "WAL" keyword
```

---

## Usage

1. **When adding a new bug**: Record phenomenon + root cause + fix + detection method
2. **When AI modifies code**: AI reads Bug Registry → checks if modification area has known bugs
3. **When a bug is fixed**: Verify the registry entry and update if solution evolved

---

## Verification

- [ ] Each bug has: phenomenon / root cause / fix / detection
- [ ] Bugs organized by category (Framework / Architecture / Data / API)
- [ ] AI reads registry before modifying code in affected areas
- [ ] New bugs added within 24h of discovery
- [ ] Detection method is executable (not just description)
