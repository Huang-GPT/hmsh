#!/bin/bash
# 服务器端诊断脚本（用户在服务器上跑，或 agent 通过 scp 推送后远程执行）
set +e  # 不让任何错误中断

echo "============================================"
echo "服务器部署诊断"
echo "============================================"

echo ""
echo "[1] /hongmen-after-sales/ 是否 git 仓库"
ls -la /hongmen-after-sales/.git/HEAD 2>&1 | head -3
cd /hongmen-after-sales && git rev-parse --is-inside-work-tree 2>&1 | head -1

echo ""
echo "[2] git 状态"
git status -sb 2>&1 | head -10

echo ""
echo "[3] 最近 5 个 commits"
git log --oneline -5 2>&1 | head -10

echo ""
echo "[4] frontend/ 目录文件清单"
ls -la /hongmen-after-sales/frontend/ 2>&1 | head -20

echo ""
echo "[5] frontend/src/views/ 目录"
ls -la /hongmen-after-sales/frontend/src/views/ 2>&1 | head -20

echo ""
echo "[6] frontend/src/views/admin/ 目录"
ls -la /hongmen-after-sales/frontend/src/views/admin/ 2>&1 | head -20

echo ""
echo "[7] AdminOrders.vue 是否存在 + 新 CSS class"
if [ -f /hongmen-after-sales/frontend/src/views/admin/AdminOrders.vue ]; then
  echo "  文件大小：$(wc -c < /hongmen-after-sales/frontend/src/views/admin/AdminOrders.vue) bytes"
  echo "  cv-empty: $(grep -c "cv-empty" /hongmen-after-sales/frontend/src/views/admin/AdminOrders.vue)"
  echo "  dot-cyan: $(grep -c "dot-cyan" /hongmen-after-sales/frontend/src/views/admin/AdminOrders.vue)"
  echo "  appt-hint: $(grep -c "appt-hint" /hongmen-after-sales/frontend/src/views/admin/AdminOrders.vue)"
else
  echo "  ❌ AdminOrders.vue 文件不存在！"
fi

echo ""
echo "[8] /hongmen-after-sales/frontend/dist 是否存在"
ls -la /hongmen-after-sales/frontend/dist/ 2>&1 | head -10

echo ""
echo "[9] nginx 容器 dist 内容"
docker exec hongmen-frontend ls /usr/share/nginx/html/js/ 2>&1 | head -10

echo ""
echo "[10] dist 中 AdminOrders 重写标记"
docker exec hongmen-frontend sh -c "grep -c 'cv-empty\|dot-cyan\|appt-hint' /usr/share/nginx/html/js/app.*.js 2>&1" 2>&1 | head -5

echo ""
echo "============================================"
echo "诊断完成"
echo "============================================"