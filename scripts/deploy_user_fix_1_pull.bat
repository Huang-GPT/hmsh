@echo off
REM 新增用户500修复：1/3 拉取 + 源码验证（cmd.exe 里双击运行）
set KEY=%USERPROFILE%\.ssh\magic.pem
set REMOTE=root@39.106.217.235
set OPT=-o ConnectTimeout=10 -o BatchMode=yes -o IdentitiesOnly=yes
echo [1/3] git pull
ssh -i %KEY% %OPT% %REMOTE% "export GIT_SSH_COMMAND='ssh -i /root/.ssh/id_ed25519_hmsh -o IdentitiesOnly=yes' && cd /hongmen-after-sales && git pull origin master --no-edit 2>&1"
echo [2/3] git log（期望首行 c6ad377）
ssh -i %KEY% %OPT% %REMOTE% "git -C /hongmen-after-sales log --oneline -3"
echo [3/3] 源码判据（后端期望^>=2，前端期望^>=1）
ssh -i %KEY% %OPT% %REMOTE% "grep -c '手机号已存在' /hongmen-after-sales/backend/app/api/admin.py"
ssh -i %KEY% %OPT% %REMOTE% "grep -c '空字符串归一化' /hongmen-after-sales/frontend/src/views/admin/AdminUsers.vue"
pause
