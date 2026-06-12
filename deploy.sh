#!/bin/bash

# ========================================
#   红门售后服务号微信服务系统 - 一键部署
# ========================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_success() {
    echo -e "${GREEN}[成功] $1${NC}"
}

print_error() {
    echo -e "${RED}[错误] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[提示] $1${NC}"
}

print_info() {
    echo -e "[信息] $1"
}

echo "========================================"
echo "  红门售后服务号微信服务系统 - 一键部署"
echo "========================================"
echo ""

# 检查Docker是否安装
print_info "1/6 检查Docker是否安装..."
if ! command -v docker &> /dev/null; then
    print_error "未检测到Docker，请先安装Docker"
    echo "安装命令: curl -fsSL https://get.docker.com | sh"
    exit 1
fi
print_success "Docker已安装"

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    print_error "未检测到Docker Compose，请先安装"
    echo "安装命令: sudo apt install docker-compose"
    exit 1
fi
print_success "Docker Compose已安装"

# 检查.env文件是否存在
echo ""
print_info "2/6 检查配置文件..."
if [ ! -f .env ]; then
    print_warning "未找到.env文件，正在从示例文件创建..."
    cp .env.example .env
    echo ""
    echo "请编辑.env文件配置以下参数："
    echo "  - DB_PASSWORD: 数据库密码"
    echo "  - WECHAT_APP_ID: 微信公众号AppID"
    echo "  - WECHAT_APP_SECRET: 微信公众号AppSecret"
    echo "  - ERP_API_URL: ERP系统API地址"
    echo "  - ERP_API_KEY: ERP系统API密钥"
    echo ""
    echo "按任意键继续（确保已配置.env文件）..."
    read -n 1 -s
fi
print_success "配置文件已就绪"

# 检查数据库初始化脚本
echo ""
print_info "3/6 准备数据库初始化..."
if [ ! -f "backend/init.sql" ]; then
    print_error "未找到数据库初始化脚本"
    exit 1
fi
print_success "数据库初始化脚本已就绪"

# 构建Docker镜像
echo ""
print_info "4/6 构建Docker镜像（可能需要几分钟）..."
docker-compose build
print_success "Docker镜像构建完成"

# 启动所有服务
echo ""
print_info "5/6 启动所有服务..."
docker-compose up -d
print_success "所有服务已启动"

# 等待服务启动
echo ""
print_info "6/6 等待服务启动..."
sleep 10

# 检查服务状态
echo ""
print_info "检查服务状态..."
docker-compose ps

# 初始化数据库表
echo ""
print_info "初始化数据库表..."
docker-compose exec -T backend python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()" 2>/dev/null || true

echo ""
echo "========================================"
echo "  部署完成！"
echo "========================================"
echo ""
echo "访问地址："
echo "  前端页面: http://localhost"
echo "  后端API:  http://localhost:5000/api"
echo ""
echo "常用命令："
echo "  查看状态: docker-compose ps"
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo ""