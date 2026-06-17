# 升级保护与回滚（本地部署）

> **分类**: 部署  
> **可复用**: ✅ 是 — 复制到任何本地部署/现场部署项目  
> **依赖**: Bash 或 PowerShell

---

## 适用场景

应用以本地方式部署（非容器化），需要：
- 原地升级而非完整重装
- 升级时保留数据
- 升级失败可回滚
- 版本可追溯

---

## 模式

```
upgrade.sh / upgrade.ps1
  ├── 第1步: 检测已有安装
  ├── 第2步: 备份当前二进制 + 配置
  ├── 第3步: 用户选择数据处理方式（保留/清理/合并）
  ├── 第4步: 解压新版本
  ├── 第5步: 合并配置（保留用户本地设置）
  ├── 第6步: 运行迁移/种子数据
  ├── 第7步: 写入版本文件
  └── 失败时: 从备份恢复
```

---

## 实现（Bash）

```bash
#!/bin/bash
set -e

DEPLOY_DIR="./deploy"
BACKUP_DIR="./backup_$(date +%Y%m%d_%H%M%S)"
VERSION_FILE="$DEPLOY_DIR/.version"
NEW_VERSION="$1"

# 第1步: 检测
if [ ! -d "$DEPLOY_DIR" ]; then
    echo "未找到已有安装。请先运行 deploy.sh。"
    exit 1
fi

# 第2步: 备份
echo "正在备份到 $BACKUP_DIR ..."
cp -r "$DEPLOY_DIR" "$BACKUP_DIR"

# 第3步: 数据处理
echo "数据目录:"
ls -d "$DEPLOY_DIR/data" "$DEPLOY_DIR/logs" 2>/dev/null
read -p "保留(k) / 清理(c) / 合并(m)? " choice

# 第4步: 解压新版本
echo "正在解压新版本..."
# 将新二进制覆盖到部署目录

# 第5步: 合并配置
# 保留用户的本地配置
if [ -f "$BACKUP_DIR/appsettings.Local.json" ]; then
    cp "$BACKUP_DIR/appsettings.Local.json" "$DEPLOY_DIR/"
fi

# 第7步: 写入版本
cat > "$VERSION_FILE" << EOF
{
  "version": "$NEW_VERSION",
  "installedAt": "$(cat $BACKUP_DIR/.version | jq -r .installedAt)",
  "upgradedAt": "$(date -Iseconds)"
}
EOF

echo "升级完成。备份位于: $BACKUP_DIR"
echo "如需回滚: cp -r $BACKUP_DIR/* $DEPLOY_DIR/"
```

---

## 版本文件格式

```json
{
  "version": "2.1.0",
  "installedAt": "2026-01-15T10:30:00+08:00",
  "upgradedAt": "2026-06-18T14:00:00+08:00"
}
```

---

## 验证清单

- [ ] 升级前创建完整备份
- [ ] 用户可选择数据保留/清理
- [ ] 用户配置（appsettings.Local.json）被保留
- [ ] 回滚路径文档化且经过测试
- [ ] 版本文件记录安装时间 + 升级时间
- [ ] 升级失败后系统处于可恢复状态
