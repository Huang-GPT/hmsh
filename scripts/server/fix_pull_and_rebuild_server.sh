# 一次性脚本：服务器 git pull + 重建前端
# 复制粘贴到服务器 VNC 终端

export GIT_SSH_COMMAND="ssh -i /root/.ssh/id_ed25519_hmsh -o IdentitiesOnly=yes"

# 1) 拉取最新代码（merge 策略，不会有冲突）
cd /hongmen-after-sales
git pull origin master --no-edit

# 2) 验证新代码已拉到位
echo "=== 验证: AdminOrders.vue 新 CSS class 计数 ==="
grep -c "cv-empty\|dot-cyan\|appt-hint" frontend/src/views/admin/AdminOrders.vue
echo "  期望 >= 3"

# 3) 重新 build 前端
echo "=== 重建前端镜像 ==="
docker compose stop frontend
docker compose rm -f frontend
docker rmi hongmen-frontend:latest 2>/dev/null
docker compose build --no-cache --pull frontend
docker compose up -d --force-recreate frontend
sleep 5

# 4) 验证 dist 是否含新代码
echo "=== 验证 dist 新 CSS class 计数 ==="
docker exec hongmen-frontend sh -c "grep -o 'cv-empty\|dot-cyan\|appt-hint' /usr/share/nginx/html/js/app.*.js | sort | uniq -c"
echo "  期望："
echo "    cv-empty  >= 7"
echo "    dot-cyan  >= 1"
echo "    appt-hint >= 1"

# 5) 报告
echo "=== 完成 ==="