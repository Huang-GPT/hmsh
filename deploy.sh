#!/usr/bin/env bash
# ============================================================
#   红门售后工单系统 - 生产环境一键部署
#
#   用法:
#     ./deploy.sh                # 部署（默认）
#     ./deploy.sh status         # 查看状态
#     ./deploy.sh logs [service] # 跟踪日志
#     ./deploy.sh stop           # 停止（保留数据）
#     ./deploy.sh restart        # 重启
#     ./deploy.sh update         # 拉代码 + 重新构建 + 滚动重启
#     ./deploy.sh reset          # ⚠  删数据卷（危险）
# ============================================================

set -euo pipefail

# ----- 颜色 -----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[✗]${NC} $*"; }
info() { echo -e "${BLUE}[i]${NC} $*"; }

# ----- 项目根 -----
cd "$(dirname "$0")"
PROJECT_ROOT="$(pwd)"

# ----- 检测 compose 命令 -----
COMPOSE_CMD="docker compose"
if ! docker compose version >/dev/null 2>&1; then
    if command -v docker-compose >/dev/null 2>&1; then
        COMPOSE_CMD="docker-compose"
    else
        err "未检测到 docker compose / docker-compose"
        exit 1
    fi
fi

# ----- 端口检查（避免生产机端口冲突） -----
check_port() {
    local port="$1"
    local service="$2"
    if ss -ltn 2>/dev/null | awk '{print $4}' | grep -E "[:.]${port}$" >/dev/null 2>&1; then
        warn "端口 ${port} 已被占用（${service}）"
        return 1
    fi
    if command -v netstat >/dev/null 2>&1; then
        if netstat -ltn 2>/dev/null | awk '{print $4}' | grep -E "[:.]${port}$" >/dev/null 2>&1; then
            warn "端口 ${port} 已被占用（${service}）"
            return 1
        fi
    fi
    return 0
}

check_all_ports() {
    # 加载 .env 拿到 HOST_PORT_* 值
    if [ -f .env ]; then
        set -a; source .env; set +a
    fi

    local conflicts=0
    for entry in \
        "HOST_PORT_FRONTEND frontend" \
        "HOST_PORT_BACKEND backend" \
        "HOST_PORT_MYSQL mysql" \
        "HOST_PORT_REDIS redis"
    do
        local var="${entry% *}"
        local label="${entry#* }"
        local port="${!var:-}"
        if [ -n "$port" ]; then
            if ! check_port "$port" "$label"; then
                conflicts=$((conflicts + 1))
            fi
        fi
    done

    if [ "$conflicts" -gt 0 ]; then
        err "${conflicts} 个端口冲突，请编辑 .env 修改 HOST_PORT_* 变量"
        err "示例: 把 HOST_PORT_FRONTEND=18080 改为未占用的端口"
        return 1
    fi
    ok "端口检查通过"
}

# ----- 检查 .env -----
ensure_env() {
    if [ ! -f .env ]; then
        if [ -f .env.production ]; then
            warn ".env 不存在，从 .env.production 复制"
            cp .env.production .env
            err "请编辑 .env 修改 SECRET_KEY、DB_PASSWORD 等敏感字段"
            err "然后重新运行 $0"
            exit 1
        else
            err ".env 和 .env.production 都不存在"
            exit 1
        fi
    fi

    # 检查是否仍是模板值
    if grep -qE '^SECRET_KEY=ChangeMe_' .env; then
        err "SECRET_KEY 仍是模板默认值，请在 .env 中修改为强随机字符串"
        exit 1
    fi
    if grep -qE '^DB_PASSWORD=ChangeMe_' .env; then
        err "DB_PASSWORD 仍是模板默认值，请在 .env 中修改为强密码"
        exit 1
    fi
    ok ".env 已就绪"
}

# ----- 等待健康 -----
wait_healthy() {
    info "等待服务健康检查..."
    local retries=0
    local max_retries=60
    while [ $retries -lt $max_retries ]; do
        if $COMPOSE_CMD ps | grep -E "(healthy|running)" | grep -qE "hongmen-(backend|frontend|db|redis)"; then
            local unhealthy
            unhealthy=$($COMPOSE_CMD ps --format json 2>/dev/null | grep -c '"Health":"unhealthy"' || true)
            if [ "${unhealthy:-0}" -eq 0 ]; then
                ok "所有服务已就绪"
                return 0
            fi
        fi
        sleep 2
        retries=$((retries + 1))
        echo -n "."
    done
    echo ""
    err "等待服务健康超时（${max_retries} 次重试）"
    err "查看日志: $0 logs"
    return 1
}

# ----- 部署 -----
do_deploy() {
    echo ""
    echo "============================================="
    echo "  红门售后工单系统 - 生产部署"
    echo "============================================="
    echo ""

    info "[1/6] 检查环境"
    command -v docker >/dev/null 2>&1 || { err "未安装 Docker"; exit 1; }
    ok "Docker 已安装"
    ok "使用 $COMPOSE_CMD"

    info "[2/6] 检查配置文件"
    ensure_env

    info "[3/6] 检查端口冲突"
    check_all_ports

    info "[4/6] 构建镜像"
    $COMPOSE_CMD build
    ok "镜像构建完成"

    info "[5/6] 启动服务"
    $COMPOSE_CMD up -d
    ok "服务已启动"

    info "[6/6] 等待健康"
    wait_healthy

    echo ""
    echo "============================================="
    ok "部署完成"
    echo "============================================="
    echo ""
    echo "访问入口："
    echo "  前端: http://<server-ip>:${HOST_PORT_FRONTEND:-18080}"
    echo "  API:  http://<server-ip>:${HOST_PORT_BACKEND:-15000}/api"
    echo ""
    echo "下一步："
    echo "  1. 创建管理员: curl -X POST http://localhost:${HOST_PORT_BACKEND:-15000}/api/auth/bootstrap \\"
    echo "       -H 'Content-Type: application/json' \\"
    echo "       -d '{\"account\":\"admin\",\"password\":\"YourPassword123!\",\"nickname\":\"系统管理员\"}'"
    echo "  2. 访问前端登录页"
    echo ""
}

# ----- 状态 -----
do_status() {
    $COMPOSE_CMD ps
    echo ""
    info "健康检查:"
    $COMPOSE_CMD ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
}

# ----- 日志 -----
do_logs() {
    local svc="${1:-}"
    $COMPOSE_CMD logs -f --tail=200 $svc
}

# ----- 停止 -----
do_stop() {
    info "停止服务（保留数据卷）"
    $COMPOSE_CMD stop
    ok "已停止"
}

# ----- 重启 -----
do_restart() {
    info "重启服务"
    $COMPOSE_CMD restart
    ok "已重启"
}

# ----- 更新（拉代码 + 重建） -----
do_update() {
    info "[1/3] 停止服务"
    $COMPOSE_CMD stop

    info "[2/3] 重新构建镜像"
    $COMPOSE_CMD build --pull

    info "[3/3] 启动新版本"
    $COMPOSE_CMD up -d
    wait_healthy
    ok "更新完成"
}

# ----- 重置（删数据） -----
do_reset() {
    err "这将删除所有 MySQL 和 Redis 数据！"
    read -p "确认输入 'yes-I-understand' 继续: " confirm
    if [ "$confirm" != "yes-I-understand" ]; then
        warn "已取消"
        return
    fi
    $COMPOSE_CMD down -v
    ok "已删除所有数据卷"
}

# ----- 主入口 -----
cmd="${1:-deploy}"
shift || true

case "$cmd" in
    deploy)   do_deploy ;;
    status)   do_status ;;
    logs)     do_logs "$@" ;;
    stop)     do_stop ;;
    restart)  do_restart ;;
    update)   do_update ;;
    reset)    do_reset ;;
    *)        err "未知命令: $cmd"; echo "用法: $0 {deploy|status|logs|stop|restart|update|reset}"; exit 1 ;;
esac
