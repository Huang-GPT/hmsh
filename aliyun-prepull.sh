#!/bin/bash
# 在阿里云 ECS 服务器上执行
# 用途：用 ACR 加速器预拉基础镜像，绕过 docker.io 拉取超时

set -e

MIRROR="tvi2u0g2.mirror.aliyuncs.com"
# 上面这个值是用户的专属加速器 ID，从阿里云容器镜像服务控制台复制

echo "[1/2] 从 ACR 加速器拉基础镜像..."
docker pull ${MIRROR}/library/redis:7-alpine
docker pull ${MIRROR}/library/mysql:8.0

echo "[2/2] tag 成默认名（让 docker-compose 找得到）"
docker tag ${MIRROR}/library/redis:7-alpine redis:7-alpine
docker tag ${MIRROR}/library/mysql:8.0 mysql:8.0

echo "完成。重新跑 ./deploy.sh"
