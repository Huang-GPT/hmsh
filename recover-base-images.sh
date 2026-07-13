#!/usr/bin/env bash
# ============================================================
#   在服务器上恢复 mysql:8.0 和 redis:7-alpine 基础镜像
#
#   场景: docker compose up 报
#     manifest for tvi2u0g2.mirror.aliyuncs.com/library/redis:7-alpine
#     not found: manifest unknown
#   原因: 阿里云 ACR 个人版不提供 redis:7-alpine tag
#
#   用法:
#     ./recover-base-images.sh             # 自动从本地缓存恢复
#
#   流程:
#     1. 检查本地 docker images 是否有 redis:7-alpine 和 mysql:8.0
#     2. 如果有 → 跳过
#     3. 如果无 → 检查 /tmp 下是否有 tar 文件
#     4. 如果有 → docker load
#     5. 如果无 → 提示用户从本地 pull + save + scp
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[X]${NC} $*"; }

cd "$(dirname "$0")"

has_image() {
    docker images --format '{{.Repository}}:{{.Tag}}' 2>/dev/null | grep -qx "$1"
}

load_tar_if_exists() {
    local tar_path="$1"
    local image_name="$2"
    if [ -f "$tar_path" ]; then
        warn "找到 $tar_path, 正在 load..."
        docker load -i "$tar_path"
        if has_image "$image_name"; then
            ok "已加载: $image_name"
            return 0
        fi
    fi
    return 1
}

# redis
if has_image "redis:7-alpine"; then
    ok "redis:7-alpine 已存在"
else
    warn "redis:7-alpine 不在本地, 尝试从 /tmp 加载..."
    if ! load_tar_if_exists "/tmp/redis-7-alpine.tar" "redis:7-alpine"; then
        err "redis:7-alpine 不可用!"
        echo ""
        echo "请在本地 Windows PowerShell 跑:"
        echo "  docker pull redis:7-alpine"
        echo "  docker save -o C:\\Users\\<you>\\redis-7-alpine.tar redis:7-alpine"
        echo "  scp C:\\Users\\<you>\\redis-7-alpine.tar root@<SERVER>:/tmp/"
        echo "然后再跑本脚本"
        exit 1
    fi
fi

# mysql
if has_image "mysql:8.0"; then
    ok "mysql:8.0 已存在"
else
    warn "mysql:8.0 不在本地, 尝试从 /tmp 加载..."
    if ! load_tar_if_exists "/tmp/mysql-8.0.tar" "mysql:8.0"; then
        err "mysql:8.0 不可用!"
        echo ""
        echo "请在本地 Windows PowerShell 跑:"
        echo "  docker pull mysql:8.0"
        echo "  docker save -o C:\\Users\\<you>\\mysql-8.0.tar mysql:8.0"
        echo "  scp C:\\Users\\<you>\\mysql-8.0.tar root@<SERVER>:/tmp/"
        echo "然后再跑本脚本"
        exit 1
    fi
fi

ok "基础镜像就绪"
docker images | grep -E "redis:7-alpine|mysql:8.0"
