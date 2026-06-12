@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo   红门售后服务号微信服务系统 - 一键部署
echo ========================================
echo.

:: 检查Docker是否安装
echo [1/6] 检查Docker是否安装...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Docker，请先安装Docker Desktop
    echo 下载地址: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo [成功] Docker已安装

:: 检查Docker Compose是否安装
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Docker Compose，请先安装
    pause
    exit /b 1
)
echo [成功] Docker Compose已安装

:: 检查.env文件是否存在
echo.
echo [2/6] 检查配置文件...
if not exist .env (
    echo [提示] 未找到.env文件，正在从示例文件创建...
    copy .env.example .env
    echo [提示] 请编辑.env文件配置以下参数：
    echo   - DB_PASSWORD: 数据库密码
    echo   - WECHAT_APP_ID: 微信公众号AppID
    echo   - WECHAT_APP_SECRET: 微信公众号AppSecret
    echo   - ERP_API_URL: ERP系统API地址
    echo   - ERP_API_KEY: ERP系统API密钥
    echo.
    echo 按任意键继续（确保已配置.env文件）...
    pause >nul
)
echo [成功] 配置文件已就绪

:: 创建数据库初始化脚本目录
echo.
echo [3/6] 准备数据库初始化...
if not exist "backend\init.sql" (
    echo [错误] 未找到数据库初始化脚本
    pause
    exit /b 1
)
echo [成功] 数据库初始化脚本已就绪

:: 构建Docker镜像
echo.
echo [4/6] 构建Docker镜像（可能需要几分钟）...
docker-compose build
if errorlevel 1 (
    echo [错误] Docker镜像构建失败
    pause
    exit /b 1
)
echo [成功] Docker镜像构建完成

:: 启动所有服务
echo.
echo [5/6] 启动所有服务...
docker-compose up -d
if errorlevel 1 (
    echo [错误] 服务启动失败
    pause
    exit /b 1
)
echo [成功] 所有服务已启动

:: 等待服务启动
echo.
echo [6/6] 等待服务启动...
timeout /t 10 /nobreak >nul

:: 检查服务状态
echo.
echo 检查服务状态...
docker-compose ps

:: 初始化数据库表
echo.
echo 初始化数据库表...
docker-compose exec -T backend python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()" 2>nul
if errorlevel 1 (
    echo [警告] 数据库表初始化可能需要手动执行
)

echo.
echo ========================================
echo   部署完成！
echo ========================================
echo.
echo 访问地址：
echo   前端页面: http://localhost
echo   后端API:  http://localhost:5000/api
echo.
echo 常用命令：
echo   查看状态: docker-compose ps
echo   查看日志: docker-compose logs -f
echo   停止服务: docker-compose down
echo   重启服务: docker-compose restart
echo.
echo 按任意键退出...
pause >nul