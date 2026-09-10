# 一次性脚本：新增用户500修复（c6ad377）发布到阿里云
# 用法（二选一）：
#   A) 服务器 VNC 终端直接粘贴本文件全部内容
#   B) 本地 cmd 双击配套的 deploy_user_fix_*.bat（走 SSH）
# 判据：>=2 个独立匹配（源码 grep + 容器 grep + git log 三维）

export GIT_SSH_COMMAND="ssh -i /root/.ssh/id_ed25519_hmsh -o IdentitiesOnly=yes"

# 1) 拉取（含本次修复 c6ad377）
cd /hongmen-after-sales
git pull origin master --no-edit
echo "=== git log（期望首行含 c6ad377）==="
git log --oneline -3

# 2) 验证源码已到位（判据①：后端；判据②：前端）
echo "=== 源码判据①：后端『手机号已存在』计数（期望 >= 2）==="
grep -c "手机号已存在" backend/app/api/admin.py
echo "=== 源码判据②：前端『空字符串归一化』计数（期望 >= 1）==="
grep -c "空字符串归一化" frontend/src/views/admin/AdminUsers.vue

# 3) 重建前后端（AGENTS.md PUA#2：必须 --force-recreate，否则旧镜像还跑着）
echo "=== 重建后端 ==="
docker compose build backend 2>&1 | tail -3
echo "=== 重建前端 ==="
docker compose build frontend 2>&1 | tail -3
docker compose up -d --force-recreate backend frontend
sleep 15

# 4) 验证容器（判据③：容器内后端代码；判据④：容器状态）
echo "=== 容器状态（期望 Up）==="
docker ps --filter name=hongmen --format '{{.Names}} {{.Status}}'
echo "=== 容器判据：backend 内『手机号已存在』计数（期望 >= 2）==="
docker exec hongmen-backend grep -c "手机号已存在" /app/app/api/admin.py
echo "=== 容器判据：frontend dist 有 js 产物（期望非空）==="
docker exec hongmen-frontend sh -c "ls /usr/share/nginx/html/js/"

# 5) 客户端可达性
echo "=== HTTP 状态（期望 200）==="
curl -sI -o /dev/null -w "%{http_code}\n" "http://127.0.0.1:80/product/repair?v=userfix"

echo "=== 完成：4 个判据全过才算发布成功 ==="
