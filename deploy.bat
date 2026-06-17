@echo off
chcp 65001 >nul

echo ========================================
echo   红门售后服务号微信服务系统 - 一键部署
echo ========================================
echo.

:: 检查Docker是否安装
echo [1/6] 检查Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [错误] 未检测到Docker！
    echo.
    echo 请先安装Docker Desktop:
    echo https://www.docker.com/products/docker-desktop
    echo.
    echo 安装后请重启电脑，再运行此脚本。
    echo.
    pause
    exit /b 1
)
echo [成功] Docker已安装

:: 检查Docker Compose
echo.
echo [2/6] 检查Docker Compose...
docker compose version >nul 2>&1
if %errorlevel% neq 0 (
    docker-compose --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [错误] 未检测到Docker Compose
        pause
        exit /b 1
    )
)
echo [成功] Docker Compose已安装

:: 检查.env文件
echo.
echo [3/6] 检查配置文件...
if not exist .env (
    echo [提示] 正在创建配置文件...
    copy .env.example .env >nul
    echo.
    echo 请先编辑 .env 文件，配置以下参数后重新运行:
    echo   - DB_PASSWORD (数据库密码)
    echo   - WECHAT_APP_ID (微信AppID)
    echo   - WECHAT_APP_SECRET (微信AppSecret)
    echo.
    notepad .env
    pause
    exit /b 1
)
echo [成功] 配置文件已就绪

:: 使用docker compose命令（新版Docker）
set COMPOSE_CMD=docker compose
docker compose version >nul 2>&1
if %errorlevel% neq 0 (
    set COMPOSE_CMD=docker-compose
)

:: 构建镜像
echo.
echo [4/6] 构建Docker镜像（请耐心等待）...
%COMPOSE_CMD% build
if %errorlevel% neq 0 (
    echo [错误] 构建失败
    pause
    exit /b 1
)
echo [成功] 镜像构建完成

:: 启动服务
echo.
echo [5/6] 启动所有服务...
%COMPOSE_CMD% up -d
if %errorlevel% neq 0 (
    echo [错误] 启动失败
    pause
    exit /b 1
)
echo [成功] 服务已启动

:: 等待启动
echo.
echo [6/6] 等待服务就绪...
timeout /t 15 /nobreak >nul

:: 检查状态
%COMPOSE_CMD% ps

echo.
echo ========================================
echo   部署完成！
echo ========================================
echo.
echo   前端访问: http://localhost
echo   后端API:  http://localhost:5000/api
echo.
echo ========================================
echo.
pause