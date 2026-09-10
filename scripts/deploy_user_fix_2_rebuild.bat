@echo off
REM 新增用户500修复：2/3 重建前后端（cmd.exe 里双击运行）
set KEY=%USERPROFILE%\.ssh\magic.pem
set REMOTE=root@39.106.217.235
set OPT=-o ConnectTimeout=10 -o BatchMode=yes -o IdentitiesOnly=yes
echo [1/2] build backend + frontend
ssh -i %KEY% %OPT% %REMOTE% "cd /hongmen-after-sales && docker compose build backend 2>&1 | tail -3 && docker compose build frontend 2>&1 | tail -3"
echo [2/2] force-recreate（必须，否则旧镜像还跑着）
ssh -i %KEY% %OPT% %REMOTE% "cd /hongmen-after-sales && docker compose up -d --force-recreate backend frontend && sleep 15 && docker ps --filter name=hongmen --format '{{.Names}} {{.Status}}'"
pause
