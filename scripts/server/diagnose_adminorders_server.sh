#!/bin/bash
# 一键诊断 — 服务器部署状态
# 跑法（服务器 VNC 终端）：bash /path/to/diagnose_adminorders.sh

echo "============================================"
echo "🔍 AdminOrders 部署诊断"
echo "============================================"

echo ""
echo "[1/6] 服务器源码：AdminOrders.vue 大小 + 新 CSS class"
ls -la /hongmen-after-sales/frontend/src/views/AdminOrders.vue
echo "  新 CSS class 计数："
grep -c "cv-empty" /hongmen-after-sales/frontend/src/views/AdminOrders.vue
grep -c "dot-cyan" /hongmen-after-sales/frontend/src/views/AdminOrders.vue
grep -c "appt-hint" /hongmen-after-sales/frontend/src/views/AdminOrders.vue
echo "  如果上述都是 0 → 服务器源码是旧版"

echo ""
echo "[2/6] 服务器整个 frontend 目录大小"
du -sh /hongmen-after-sales/frontend
echo "  期望 ≥30 MB；如果是几 KB → git 仓库没拉到位"

echo ""
echo "[3/6] 服务器 dist 是否存在（关键！）"
docker exec hongmen-frontend ls /usr/share/nginx/html/js/
echo "  期望看到 app.xxx.js + chunk-vendors.xxx.js"
echo "  如果是空 → build 没产 dist"

echo ""
echo "[4/6] dist 中新 CSS class 计数"
docker exec hongmen-frontend sh -c "grep -o 'cv-empty\|dot-cyan\|appt-hint' /usr/share/nginx/html/js/app.*.js 2>/dev/null | sort | uniq -c"
echo "  期望："
echo "    cv-empty  >= 7"
echo "    dot-cyan  >= 1"
echo "    appt-hint >= 1"
echo "  如果全是 0 → dist 是旧版"

echo ""
echo "[5/6] 服务器 git 状态"
cd /hongmen-after-sales
git log --oneline -3
echo ""
git status
echo "  如果 'Your branch is behind' 或 'Your branch is ahead' → git 状态有问题"

echo ""
echo "[6/6] 服务器 git remote + 同步状态"
git remote -v
echo ""
git fetch origin 2>&1 | head -3
echo ""
git status -sb
echo "  ## master...origin/master 意味着同步"

echo ""
echo "============================================"
echo "✅ 诊断完成。请把上面所有输出贴给 agent。"
echo "============================================"