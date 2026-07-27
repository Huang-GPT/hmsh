#!/usr/bin/env bash
# ============================================================
# ⚠️  本脚本需在服务器 PowerShell 跑（不是本地）
#    SSH 入口：ssh root@39.106.217.235 "bash /hongmen-after-sales/scripts/server/deploy_frontend_clean_server.sh"
#    作用：彻底重建前端容器 + 清旧镜像 + 验证 dist 真的进去了
# ============================================================

set -e

cd /hongmen-after-sales

echo "============================================"
echo "[1/5] 停止并删除旧容器"
echo "============================================"
docker compose stop frontend
docker compose rm -f frontend
echo "✓ 旧容器已删"

echo ""
echo "============================================"
echo "[2/5] 删除旧镜像（强制重新 build）"
echo "============================================"
docker rmi hongmen-frontend:latest 2>/dev/null || echo "  无旧镜像可删"
docker images --filter "dangling=true" -q | xargs -r docker rmi 2>/dev/null || true
echo "✓ 镜像已清"

echo ""
echo "============================================"
echo "[3/5] 重新 build 前端（--no-cache + --pull）"
echo "============================================"
docker compose build --no-cache --pull frontend
echo "✓ build 完成"

echo ""
echo "============================================"
echo "[4/5] 启动新容器"
echo "============================================"
docker compose up -d frontend
sleep 3
echo "✓ 启动完成"

echo ""
echo "============================================"
echo "[5/5] 验证"
echo "============================================"
echo "容器内 dist 是否存在？"
docker exec hongmen-frontend ls /usr/share/nginx/html/js/ | head -5

echo ""
echo "dist 中是否含 '期望服务时间'？"
docker exec hongmen-frontend sh -c 'grep -c "期望服务时间" /usr/share/nginx/html/js/app.*.js'

echo ""
echo "dist 中是否含 type=\"date\"？"
docker exec hongmen-frontend sh -c 'grep -c "type.:.date" /usr/share/nginx/html/js/app.*.js'

echo ""
echo "容器访问 nginx 健康检查"
curl -sI http://localhost:18080/ | head -3

echo ""
echo "============================================"
echo "✓ 全部完成！"
echo "请用浏览器访问（带随机参数破缓存）："
echo "  http://39.106.217.235:18080/product/repair?v=$(date +%s)"
echo "============================================"