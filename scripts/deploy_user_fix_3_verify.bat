@echo off
REM 新增用户500修复：3/3 验证闭环（cmd.exe 里双击运行）
set KEY=%USERPROFILE%\.ssh\magic.pem
set REMOTE=root@39.106.217.235
set OPT=-o ConnectTimeout=10 -o BatchMode=yes -o IdentitiesOnly=yes
echo [1/3] backend 容器内代码（期望 ^>= 2）
ssh -i %KEY% %OPT% %REMOTE% "docker exec hongmen-backend grep -c '手机号已存在' /app/app/api/admin.py"
echo [2/3] frontend dist 产物（期望非空）
ssh -i %KEY% %OPT% %REMOTE% "docker exec hongmen-frontend sh -c 'ls /usr/share/nginx/html/js/'"
echo [3/3] HTTP 可达（期望 200）
ssh -i %KEY% %OPT% %REMOTE% "curl -sI -o /dev/null -w '%%{http_code}\n' 'http://127.0.0.1:80/product/repair?v=userfix'"
pause
