#!/usr/bin/env bash
# ============================================================
#   80 端口冲突排查 + 一键解决
#
#   场景: docker compose up 报
#     Error starting userland proxy: listen tcp4 0.0.0.0:80:
#     bind: address already in use
#
#   微信公众平台 JS 安全域名不支持端口号, 必须能从 80 端口访问
#
#   三种修法:
#     A. 杀掉占 80 的进程(如果该进程没用)
#     B. 装宿主机 nginx 反代 80 -> hongmen:18080(保留原 80 服务)
#     C. 改回 18080 端口(**微信 JS 安全域名会失败**, 不推荐)
#
#   用法:
#     ./fix-80-port.sh              # 自动诊断 + 提示
#     ./fix-80-port.sh --kill       # 强制杀掉占 80 的进程
#     ./fix-80-port.sh --proxy      # 一键装宿主机 nginx 反代
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[X]${NC} $*"; }
info() { echo -e "${BLUE}[i]${NC} $*"; }

# ----- 1. 诊断 -----
echo "============================================="
echo "  80 端口冲突诊断"
echo "============================================="

if ss -ltnp 2>/dev/null | grep -E "[:.]80\s" >/dev/null; then
    err "80 端口已被占用:"
    ss -ltnp 2>/dev/null | grep -E "[:.]80\s" | sed 's/^/  /'
else
    ok "80 端口空闲"
fi

echo ""

# ----- 2. 模式 A: kill -----
if [ "${1:-}" = "--kill" ]; then
    warn "尝试杀掉占 80 端口的进程..."
    PIDS=$(ss -ltnp 2>/dev/null | grep -E "[:.]80\s" | grep -oE 'pid=[0-9]+' | cut -d= -f2 | sort -u)
    if [ -z "$PIDS" ]; then
        err "没找到占 80 端口的 PID（可能需要 sudo）"
        exit 1
    fi
    for pid in $PIDS; do
        PROCESS=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
        warn "杀进程 PID=$pid ($PROCESS)"
        kill -9 $pid 2>/dev/null || true
    done
    sleep 2
    if ss -ltn 2>/dev/null | grep -E "[:.]80\s" >/dev/null; then
        err "80 仍被占（可能没权限）"
        exit 1
    fi
    ok "80 端口已释放"
    echo "现在可以: docker compose up -d"
    exit 0
fi

# ----- 3. 模式 B: nginx 反代 -----
if [ "${1:-}" = "--proxy" ]; then
    info "安装宿主机 nginx 反代 80 -> hongmen:18080"

    # 检测发行版
    if command -v apt-get >/dev/null 2>&1; then
        info "Debian/Ubuntu 系统"
        apt-get update -qq
        apt-get install -y -qq nginx
    elif command -v yum >/dev/null 2>&1; then
        info "CentOS/RHEL 系统"
        yum install -y -y nginx
    else
        err "未识别的发行版，请手动装 nginx"
        exit 1
    fi

    # 写反代配置
    cat > /etc/nginx/conf.d/hongmen.conf <<'EOF'
server {
    listen 80;
    server_name _;

    # 微信 JS 安全域名验证文件必须能直访
    # vue-cli 已把 frontend/public/ 整个拷到 dist/, 所以 /MP_verify_xxx.txt 直接走下面
    location / {
        proxy_pass http://127.0.0.1:18080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

    # 关掉默认 server 块（占 80，导致我们的 conf 被 ignore）
    # Ubuntu/Debian: /etc/nginx/sites-enabled/default
    # CentOS/RHEL  : /etc/nginx/conf.d/default.conf
    rm -f /etc/nginx/sites-enabled/default
    rm -f /etc/nginx/conf.d/default.conf

    # 注释掉 /etc/nginx/nginx.conf 主配置里的 default_server 块
    # （如果存在的话，否则会触发 conflicting server name 警告）
    if [ -f /etc/nginx/nginx.conf ]; then
        # 备份一次
        cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.hongmen-bak
        # 把 listen 80 default_server 注释掉
        sed -i 's/^\([[:space:]]*\)listen[[:space:]]*80;/\1# listen 80;  # disabled by hongmen fix-80-port/' /etc/nginx/nginx.conf
        sed -i 's/^\([[:space:]]*\)listen[[:space:]]*\[::\]:80;/\1# listen [::]:80;  # disabled by hongmen fix-80-port/' /etc/nginx/nginx.conf
    fi

    nginx -t
    systemctl enable nginx
    systemctl restart nginx

    sleep 2
    if ss -ltn 2>/dev/null | grep -E "[:.]80\s" >/dev/null; then
        ok "宿主机 nginx 已在 80 监听"
        curl -sI http://localhost | head -1
    else
        err "nginx 启动失败，请 systemctl status nginx"
        exit 1
    fi

    echo ""
    echo "现在改 docker-compose.yml: HOST_PORT_FRONTEND=80 不再需要（容器仍用 18080）"
    echo "对外访问用 http://你的域名 或 http://公网IP"
    exit 0
fi

# ----- 4. 默认: 提示 -----
cat <<EOF

请选择修法:

  A. 杀掉占 80 的进程
     $ ./fix-80-port.sh --kill

  B. 装宿主机 nginx 反代 80 -> hongmen:18080 (推荐!)
     $ ./fix-80-port.sh --proxy

  C. 改回 18080 端口 (微信 JS 安全域名会失败, 不推荐)
     $ sed -i 's/^HOST_PORT_FRONTEND=80/HOST_PORT_FRONTEND=18080/' .env
     $ docker compose up -d

  D. 手动诊断
     $ ss -ltnp | grep ':80 '
     $ netstat -tlnp | grep ':80 '

EOF
