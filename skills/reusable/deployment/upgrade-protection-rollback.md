# Upgrade Protection & Rollback (Local Deployment)

> **Category**: Deployment  
> **Reusable**: ✅ Yes — copy to any on-premise / local-deploy project  
> **Dependencies**: Bash or PowerShell

---

## When to Use

Your application is deployed locally (not containerized) and needs:
- In-place upgrades without full reinstall
- Data preservation across versions
- Rollback capability if upgrade fails
- Version tracking

---

## Pattern

```
upgrade.sh / upgrade.ps1
  ├── Step 1: Detect existing installation
  ├── Step 2: Backup current binaries + config
  ├── Step 3: User chooses data handling (keep/clear/merge)
  ├── Step 4: Extract new version
  ├── Step 5: Merge configuration (preserve user settings)
  ├── Step 6: Run migration / seed
  ├── Step 7: Write version file
  └── On failure: Restore from backup
```

---

## Implementation (Bash)

```bash
#!/bin/bash
set -e

DEPLOY_DIR="./deploy"
BACKUP_DIR="./backup_$(date +%Y%m%d_%H%M%S)"
VERSION_FILE="$DEPLOY_DIR/.version"
NEW_VERSION="$1"

# Step 1: Detect
if [ ! -d "$DEPLOY_DIR" ]; then
    echo "No existing installation found. Run deploy.sh first."
    exit 1
fi

# Step 2: Backup
echo "Backing up to $BACKUP_DIR..."
cp -r "$DEPLOY_DIR" "$BACKUP_DIR"

# Step 3: Data handling
echo "Data directories:"
ls -d "$DEPLOY_DIR/data" "$DEPLOY_DIR/logs" 2>/dev/null
read -p "Keep (k) / Clear (c) / Merge (m)? " choice

# Step 4: Extract new version
echo "Extracting new version..."
# Copy new binaries over old ones

# Step 5: Merge appsettings
# Preserve user's local settings
if [ -f "$BACKUP_DIR/appsettings.Local.json" ]; then
    cp "$BACKUP_DIR/appsettings.Local.json" "$DEPLOY_DIR/"
fi

# Step 7: Write version
cat > "$VERSION_FILE" << EOF
{
  "version": "$NEW_VERSION",
  "installedAt": "$(cat $BACKUP_DIR/.version | jq -r .installedAt)",
  "upgradedAt": "$(date -Iseconds)"
}
EOF

echo "Upgrade complete. Backup at: $BACKUP_DIR"
echo "To rollback: cp -r $BACKUP_DIR/* $DEPLOY_DIR/"
```

---

## Version File Format

```json
{
  "version": "2.1.0",
  "installedAt": "2026-01-15T10:30:00+08:00",
  "upgradedAt": "2026-06-18T14:00:00+08:00"
}
```

---

## Verificatio

- [ ] Upgrade creates backup before touching existing files
- [ ] User can choose data handling (keep/clear)
- [ ] User config (appsettings.Local.json) preserved
- [ ] Rollback path is documented and tested
- [ ] Version file updated with install + upgrade timestamps
- [ ] Failed upgrade leaves system in recoverable state
