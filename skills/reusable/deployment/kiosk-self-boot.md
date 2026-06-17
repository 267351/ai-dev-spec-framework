# Kiosk 自启动部署

> **分类**: 部署  
> **可复用**: ✅ 是 — 复制到任何工业/展厅自助终端部署  
> **依赖**: Bash (Linux) 或 PowerShell (Windows)，浏览器

---

## 适用场景

应用运行在专用机器上，作为自助终端、信息看板或工业工作站：
- 无需键盘鼠标交互（或最小化交互）
- 浏览器开机自动全屏启动
- 多显示器需指定窗口位置
- 崩溃自动恢复，无需人工干预

---

## 关键特性

1. **无头环境检测** — 无显示器时跳过浏览器启动（WSL、SSH 环境）
2. **浏览器优先级链** — Chrome → Chromium → Edge → Firefox
3. **窗口几何持久化** — 保存/恢复窗口位置和尺寸
4. **Root 用户沙箱处理** — 自动添加 `--no-sandbox`
5. **服务就绪等待** — 轮询 Launcher 的 `.ready` 文件

---

## 实现（Bash）

```bash
#!/bin/bash
# start-kiosk.sh — 由 deploy.sh 生成

# 1. 无头检测
if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
    echo "检测到无头环境，跳过浏览器启动"
    LAUNCH_BROWSER=false
fi

# 2. 查找浏览器（优先级链）
find_browser() {
    for cmd in google-chrome-stable google-chrome chromium-browser chromium microsoft-edge firefox; do
        if command -v "$cmd" &>/dev/null; then
            echo "$cmd"
            return
        fi
    done
    echo ""
}
BROWSER=$(find_browser)

# 3. Root 用户沙箱处理
SANDBOX_FLAG=""
if [ "$EUID" -eq 0 ]; then
    case "$BROWSER" in
        *chrome*|*chromium*|*edge*) SANDBOX_FLAG="--no-sandbox" ;;
    esac
fi

# 4. 等待服务就绪
while [ ! -f "./deploy/.ready" ]; do
    sleep 1
done
echo "服务已就绪"

# 5. 全屏启动浏览器
if [ -f ".browser-state" ]; then
    source .browser-state  # 恢复上次窗口位置
    $BROWSER $SANDBOX_FLAG --window-position=$WIN_X,$WIN_Y \
             --window-size=$WIN_W,$WIN_H --kiosk "http://localhost:5193" &
else
    $BROWSER $SANDBOX_FLAG --kiosk "http://localhost:5193" &
fi
BROWSER_PID=$!

# 6. 退出时保存窗口几何信息
save_geometry() {
    if command -v wmctrl &>/dev/null; then
        eval $(wmctrl -lG | grep "localhost" | awk '{print "WIN_X="$3,"WIN_Y="$4,"WIN_W="$5,"WIN_H="$6}')
        echo "WIN_X=$WIN_X; WIN_Y=$WIN_Y; WIN_W=$WIN_W; WIN_H=$WIN_H" > .browser-state
    fi
}
trap save_geometry EXIT

# 7. 交互菜单
echo "按 R 重启，按 Q 退出"
while true; do
    read -n 1 -t 1 key
    case "$key" in
        r|R) kill $BROWSER_PID; exec "$0" ;;
        q|Q) kill $BROWSER_PID; exit 0 ;;
    esac
done
```

---

## 多显示器配置

```bash
# 浏览器在指定显示器上启动
# 显示器1（左，1920x1080）: --window-position=0,0
# 显示器2（右，1920x1080）: --window-position=1920,0

# A 屏（操作台） → 左显示器
google-chrome --window-position=0,0 --window-size=1920,1080 --kiosk \
    "http://localhost:5193/operations" &

# B 屏（监控） → 右显示器
google-chrome --window-position=1920,0 --window-size=1920,1080 --kiosk \
    "http://localhost:5193/operations/cameras" &
```

---

## 验证清单

- [ ] 无头环境被正确检测并优雅跳过
- [ ] 浏览器通过优先级链查找（非硬编码）
- [ ] Root 用户自动添加 `--no-sandbox`
- [ ] 浏览器启动前等待服务就绪（轮询 `.ready`）
- [ ] 退出时保存窗口几何，重启时恢复
- [ ] 交互式重启/退出菜单正常工作
- [ ] 多显示器：每个屏幕在正确的显示器上
