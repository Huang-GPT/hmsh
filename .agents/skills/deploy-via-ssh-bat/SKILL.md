---
name: deploy-via-ssh-bat
description: 从 opencode agent 容器远程部署代码到 Linux 服务器（通过 SSH 私钥 + cmd.exe .bat 脚本）。适用于 PowerShell 容器调 OpenSSH 客户端 hang 的情况。适用：hmsh 及类似 Linux Docker 项目。
---

# Deploy via SSH + .bat（绕开 PowerShell hang）

## 问题（为什么这个 skill 存在）

**opencode agent 容器跑 PowerShell 调 OpenSSH 客户端（`C:\Windows\System32\OpenSSH\ssh.exe`）会 hang**——`GetConsoleMode on STD_INPUT_HANDLE failed with 6`。已验证：

- ❌ `& ssh user@host "cmd"` — hang
- ❌ `cmd /c "ssh user@host cmd"` — 偶尔成功但不稳定
- ❌ `[System.Diagnostics.Process]::Start(ssh.exe)` + `WaitForExit()` — hang
- ✅ **直接调 `ssh.exe` 不带 PowerShell pipe（但容器环境难做到）**
- ✅ **PowerShell Agent 调 OpenSSH Client 但只跑极简命令（< 100ms 输出）—— 不稳定**

**唯一 100% 稳定方案**：用户在本地 cmd.exe / 终端跑 .bat 脚本，脚本调 ssh.exe。

## 前置条件

| 项 | 说明 |
|---|---|
| SSH 私钥 | `C:\Users\123\.ssh\<keyname>.pem`（RSA/PEM 格式）或 `id_ed25519` |
| 服务器账号 | 假设为 `root@<server_ip>` |
| 服务器预装 | 1) 项目已 clone  2) docker + docker compose  3) `/root/.ssh/id_ed25519_hmsh`（专门给此项目） |

**服务器上生成 hmsh 专用 SSH key**（这样不影响其他 key）：
```bash
ssh-keygen -t ed25519 -C "hmsh-server" -f /root/.ssh/id_ed25519_hmsh
cat /root/.ssh/id_ed25519_hmsh.pub   # 添加到 GitHub Deploy Keys（read-only 即可）
```

## 核心：4 个 .bat 脚本

### 1_pull.bat — 拉取最新代码到服务器
```bat
@echo off
set KEY=C:\Users\123\.ssh\opencode.pem
set REMOTE=root@39.106.217.235
echo [1/4] git pull
ssh -i %KEY% -o ConnectTimeout=10 -o BatchMode=yes -o IdentitiesOnly=yes %REMOTE% "export GIT_SSH_COMMAND='ssh -i /root/.ssh/id_ed25519_hmsh -o IdentitiesOnly=yes' && cd /hongmen-after-sales && git pull origin master --no-edit 2>&1"
echo [2/4] 验证源码
ssh -i %KEY% -o ConnectTimeout=10 -o BatchMode=yes -o IdentitiesOnly=yes %REMOTE% "grep -c 'cv-empty' /hongmen-after-sales/frontend/src/views/admin/AdminOrders.vue"
echo [3/4] 验证 dist
ssh -i %KEY% -o ConnectTimeout=10 -o BatchMode=yes -o IdentitiesOnly=yes %REMOTE% "docker exec hongmen-frontend sh -c 'grep -c cv-empty /usr/share/nginx/html/js/app.*.js'"
pause
```

### 2_rebuild.bat — 重建前端 Docker 镜像
```bat
@echo off
set KEY=C:\Users\123\.ssh\opencode.pem
set REMOTE=root@39.106.217.235
echo ============================================
echo  重建前端容器
echo ============================================
ssh -i %KEY% -o ConnectTimeout=10 -o BatchMode=yes -o IdentitiesOnly=yes %REMOTE% "cd /hongmen-after-sales && docker compose stop frontend && docker compose rm -f frontend && docker rmi hongmen-frontend:latest 2>/dev/null && docker compose build --no-cache --pull frontend 2>&1 | tail -10"
echo ============================================
echo  启动新容器
echo ============================================
ssh -i %KEY% -o ConnectTimeout=10 -o BatchMode=yes -o IdentitiesOnly=yes %REMOTE% "cd /hongmen-after-sales && docker compose up -d --force-recreate frontend"
pause
```

### 3_verify.bat — 验证部署
```bat
@echo off
set KEY=C:\Users\123\.ssh\opencode.pem
set REMOTE=root@39.106.217.235
echo 等待 10 秒
timeout /t 10 /nobreak
echo dist js 文件
ssh -i %KEY% -o ConnectTimeout=10 -o BatchMode=yes -o IdentitiesOnly=yes %REMOTE% "docker exec hongmen-frontend ls /usr/share/nginx/html/js/"
echo dist 中新 CSS class 计数
ssh -i %KEY% -o ConnectTimeout=10 -o BatchMode=yes -o IdentitiesOnly=yes %REMOTE% "docker exec hongmen-frontend sh -c 'grep -o \"cv-empty dot-cyan appt-hint\" /usr/share/nginx/html/js/app.*.js | sort | uniq -c'"
pause
```

### 4_backend_restart.bat — 重启 backend（如有后端改动）
```bat
@echo off
set KEY=C:\Users\123\.ssh\opencode.pem
set REMOTE=root@39.106.217.235
echo 重启 backend
ssh -i %KEY% -o ConnectTimeout=10 -o BatchMode=yes -o IdentitiesOnly=yes %REMOTE% "cd /hongmen-after-sales && docker compose restart backend"
timeout /t 30 /nobreak
echo 检查所有容器
ssh -i %KEY% -o ConnectTimeout=10 -o BatchMode=yes -o IdentitiesOnly=yes %REMOTE% "cd /hongmen-after-sales && docker compose ps"
pause
```

## 跑法

**Win+R → cmd → Enter**，然后：
```cmd
cd C:\Users\123\Desktop
1_pull.bat
2_rebuild.bat
3_verify.bat
4_backend_restart.bat
```

每跑一个，**把屏幕输出贴给 agent**，agent 据此判断闭环。

## 关键调优（实测踩坑）

1. **必须用 cmd.exe**，不是 PowerShell ISE
2. **必须 `set KEY=...`** 写绝对路径，不要依赖 ssh-agent
3. **必须 `-o IdentitiesOnly=yes`**，否则 ssh-agent 可能选错 key
4. **必须 `-o ConnectTimeout=10`**，否则 hang 时永远等
5. **必须 `pause`**，否则 bat 跑完窗口关掉看不到输出
6. **每个命令独立 bat**，不要链式 `&&`（失败会掩盖）

## 不适用情况

- 服务器不是 Linux（如 Windows Server 容器）
- 没有 SSH 私钥（需要用户先在 Windows 端生成并放对位置）
- 服务器没 docker / 没 docker compose
- 项目不是 git 跟踪（需要先 scp 同步，绕开 git pull）

## 替代方案

如果 .bat 也不能跑（比如 PowerShell 完全不能用），退路：
- 用户在阿里云控制台 VNC 终端直接敲命令
- 写好"一段 bash 脚本"让用户粘到 VNC 终端
- 用 `tmux`/`screen` 保持服务器端会话

## 历史教训（hmsh 项目实际返工）

1. **不验证 build context**：`docker build` 输出 "transferring context: 2.13kB" 但实际几百 MB——往往是 `frontend/` 目录没拉到
2. **不验证 dist 内容**：`grep -c "新 CSS class" dist/js/app.*.js` = 0 就是没生效
3. **不验证 git 状态**：服务器 `git pull` 失败但不知道—— `git log --oneline -3` vs 远程 commit 哈希即可对比
4. **build context 小 = 镜像内容旧**：98% 情况是 `git pull` 失败，**不要**怀疑 build 系统

## 引用

- hmsh 项目 14 次返工教训
- AGENTS.md 中标注的"opencode agent 无 SSH 通道"原则