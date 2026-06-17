#!/bin/bash
# ============================================================
# spec.md 体系一键部署脚本
# 用法: ./deploy.sh /path/to/new-project
# ============================================================
set -e

TARGET="${1:-}"
if [ -z "$TARGET" ]; then
    echo "用法: ./deploy.sh /path/to/新项目"
    exit 1
fi
if [ ! -d "$TARGET" ]; then
    echo "❌ 目录不存在: $TARGET"
    exit 1
fi

SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_NAME="$(basename "$TARGET")"

echo ""
echo "=========================================="
echo "  spec.md 体系一键部署"
echo "  目标: $PROJECT_NAME"
echo "=========================================="
echo ""

# ---------- Step 1: 复制工具 ----------
echo "📦 [1/4] 复制 spec-tools ..."
if [ -d "$TARGET/tools/spec-tools" ]; then
    echo "  ⚠️  tools/spec-tools 已存在，跳过"
else
    mkdir -p "$TARGET/tools"
    cp -r "$SOURCE_DIR" "$TARGET/tools/spec-tools"
    # 删除部署脚本自身和 README（避免污染目标项目）
    rm -f "$TARGET/tools/spec-tools/deploy.sh"
    rm -f "$TARGET/tools/spec-tools/README.md"
    echo "  ✅ 已复制到 tools/spec-tools/"
fi

# ---------- Step 2: 注入 AGENTS.md ----------
echo "📝 [2/4] 注入 AGENTS.md spec.md 规则 ..."
SPEC_RULES='
## spec.md 约定

> 每个代码文件对应一个 .spec.md 文件，记录该文件的架构约束、踩过的坑、技术规范。
> .spec.md 是 AI 的"持久化记忆"——跨会话保留关键知识。

### 规则
- 修改代码前**必须**读取对应的 .spec.md（如果存在）
- .spec.md 不存在时**主动提议创建**
- 修改代码后**主动询问**是否需要更新 .spec.md
- 架构级约束见 `架构总纲.spec.md`（项目根目录）

### 管理工具
```bash
python3 tools/spec-tools/spec_md_manager_v2.py scan --smart   # 查看缺失情况
python3 tools/spec-tools/spec_md_manager_v2.py create --smart  # 智能创建
python3 tools/spec-tools/spec_md_manager_v2.py report --density # 信息密度报告
```
'

if [ -f "$TARGET/AGENTS.md" ]; then
    if grep -q "spec.md" "$TARGET/AGENTS.md"; then
        echo "  ⚠️  AGENTS.md 已包含 spec.md 规则，跳过"
    else
        echo "$SPEC_RULES" >> "$TARGET/AGENTS.md"
        echo "  ✅ 已追加 spec.md 规则到 AGENTS.md"
    fi
else
    cat > "$TARGET/AGENTS.md" << 'AGENTS_EOF'
# AGENTS.md

> AI 助手入口文件。保持简洁（≤100行），详细内容放入 spec.md 或 docs/。

## 项目信息
<!-- 在此填写项目基本信息 -->

AGENTS_EOF
    echo "$SPEC_RULES" >> "$TARGET/AGENTS.md"
    echo "  ✅ 已创建 AGENTS.md"
fi

# ---------- Step 3: 智能生成架构总纲 ----------
echo "🏗️  [3/4] 智能分析项目结构，生成架构总纲 ..."
ARCH_FILE="$TARGET/架构总纲.spec.md"
if [ -f "$ARCH_FILE" ]; then
    echo "  ⚠️  架构总纲.spec.md 已存在，跳过"
else
    python3 "$SOURCE_DIR/spec_deploy_init.py" "$TARGET" 2>&1
fi

# ---------- Step 4: 扫描 ----------
echo "🔍 [4/4] 扫描项目文件 ..."
python3 "$TARGET/tools/spec-tools/spec_md_manager_v2.py" scan --smart 2>&1 || true

echo ""
echo "=========================================="
echo "  ✅ 部署完成"
echo "=========================================="
echo ""
echo "  下一步:"
echo "  1. 编辑 架构总纲.spec.md — 填写项目实际的架构约束"
echo "  2. 编辑 AGENTS.md — 填写项目基本信息"
echo "  3. python3 tools/spec-tools/spec_md_manager_v2.py create --smart"
echo "  4. 开发过程中，AI 会自动提议创建/更新文件级 .spec.md"
echo ""
