#!/usr/bin/env bash
# ============================================================
#   恢复脚本
#
#   用法: ./restore.sh <backup-dir>
#   示例: ./restore.sh ./backups/20260101-120000
# ============================================================

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "用法: $0 <backup-dir>"
    echo "示例: $0 ./backups/20260101-120000"
    exit 1
fi

BACKUP_DIR="$1"
if [ ! -d "${BACKUP_DIR}" ]; then
    echo "ERROR: 备份目录不存在: ${BACKUP_DIR}"
    exit 1
fi

cd "$(dirname "$0")"
COMPOSE_CMD="docker compose"
if ! docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
fi

if [ -f .env ]; then
    set -a; source .env; set +a
fi

echo "============================================="
echo "  即将从 ${BACKUP_DIR} 恢复"
echo "  ⚠  当前数据库将被覆盖"
echo "============================================="
read -p "确认输入 'yes' 继续: " confirm
if [ "$confirm" != "yes" ]; then
    echo "已取消"
    exit 0
fi

# ----- MySQL 恢复 -----
MYSQL_DUMP="${BACKUP_DIR}/mysql_dump.sql.gz"
if [ -f "${MYSQL_DUMP}" ]; then
    echo "[1/2] 恢复 MySQL..."
    gunzip -c "${MYSQL_DUMP}" | $COMPOSE_CMD exec -T db mysql -uroot -p"${DB_PASSWORD}" hongmen_after_sales
    echo "  MySQL 恢复完成"
else
    echo "WARN: ${MYSQL_DUMP} 不存在，跳过 MySQL 恢复"
fi

# ----- Redis 恢复 -----
REDIS_DUMP="${BACKUP_DIR}/redis_dump.rdb"
if [ -f "${REDIS_DUMP}" ]; then
    echo "[2/2] 恢复 Redis..."
    $COMPOSE_CMD stop redis
    $COMPOSE_CMD cp "${REDIS_DUMP}" redis:/data/dump.rdb
    $COMPOSE_CMD start redis
    echo "  Redis 恢复完成"
else
    echo "WARN: ${REDIS_DUMP} 不存在，跳过 Redis 恢复"
fi

echo ""
echo "============================================="
echo "  恢复完成"
echo "============================================="
