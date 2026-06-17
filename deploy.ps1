# ========================================
#   红门售后服务号微信服务系统 - PowerShell部署脚本
# ========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  红门售后服务号微信服务系统 - 一键部署" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Docker
Write-Host "[1/5] 检查Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "[成功] Docker已安装: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "[错误] 未检测到Docker，请先安装Docker Desktop" -ForegroundColor Red
    Write-Host "下载地址: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    Read-Host "按回车键退出"
    exit 1
}

# 检查.env文件
Write-Host ""
Write-Host "[2/5] 检查配置文件..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "[提示] 正在创建配置文件..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host ""
    Write-Host "请编辑 .env 文件配置以下参数:" -ForegroundColor Cyan
    Write-Host "  - DB_PASSWORD (数据库密码)" -ForegroundColor White
    Write-Host "  - WECHAT_APP_ID (微信AppID)" -ForegroundColor White
    Write-Host "  - WECHAT_APP_SECRET (微信AppSecret)" -ForegroundColor White
    Write-Host ""
    notepad .env
    Read-Host "配置完成后按回车键继续"
}
Write-Host "[成功] 配置文件已就绪" -ForegroundColor Green

# 构建镜像
Write-Host ""
Write-Host "[3/5] 构建Docker镜像（请耐心等待）..." -ForegroundColor Yellow
docker compose build
if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] 构建失败" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}
Write-Host "[成功] 镜像构建完成" -ForegroundColor Green

# 启动服务
Write-Host ""
Write-Host "[4/5] 启动所有服务..." -ForegroundColor Yellow
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] 启动失败" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}
Write-Host "[成功] 服务已启动" -ForegroundColor Green

# 等待启动
Write-Host ""
Write-Host "[5/5] 等待服务就绪..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# 检查状态
docker compose ps

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  部署完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  前端访问: http://localhost" -ForegroundColor White
Write-Host "  后端API:  http://localhost:5000/api" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Read-Host "按回车键退出"