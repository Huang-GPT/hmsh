#!/usr/bin/env bash
# ============================================================
#   备份脚本
#
#   用法: ./backup.sh [/path/to/backup-dir]
#   默认备份到 ./backups/YYYYMMDD-HHMMSS/
# ============================================================

set -euo pipefail

cd "$(dirname "$0")"

COMPOSE_CMD="docker compose"
if ! docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
fi

BACKUP_ROOT="${1:-./backups}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="${BACKUP_ROOT}/${TIMESTAMP}"

mkdir -p "${BACKUP_DIR}"

echo "============================================="
echo "  备份到: ${BACKUP_DIR}"
echo "============================================="

# 加载 .env 拿 DB 密码
if [ -f .env ]; then
    set -a; source .env; set +a
fi

# ----- MySQL 备份 -----
echo "[1/2] 备份 MySQL..."
DB_DUMP="${BACKUP_DIR}/mysql_dump.sql.gz"
$COMPOSE_CMD exec -T db mysqldump \
    -uroot -p"${DB_PASSWORD}" \
    --single-transaction \
    --routines \
    --triggers \
    --events \
    --hex-blob \
    hongmen_after_sales | gzip > "${DB_DUMP}"

if [ ! -s "${DB_DUMP}" ]; then
    echo "ERROR: MySQL dump is empty"
    exit 1
fi
echo "  -> $(du -h ${DB_DUMP} | cut -f1)  ${DB_DUMP}"

# ----- Redis 备份 -----
echo "[2/2] 备份 Redis..."
$COMPOSE_CMD exec -T redis sh -c 'redis-cli BGSAVE' >/dev/null 2>&1 || true
sleep 2
$COMPOSE_CMD cp redis:/data/dump.rdb "${BACKUP_DIR}/redis_dump.rdb" 2>/dev/null || {
    echo "  WARN: redis dump.rdb not found (Redis 可能未触发 BGSAVE)"
}

# ----- 备份元信息 -----
cat > "${BACKUP_DIR}/info.txt" <<EOF
backup_time:   ${TIMESTAMP}
compose_cmd:   ${COMPOSE_CMD}
mysql_size:    $(du -h ${DB_DUMP} 2>/dev/null | cut -f1)
redis_exists:  $([ -f "${BACKUP_DIR}/redis_dump.rdb" ] && echo yes || echo no)
EOF

echo ""
echo "============================================="
echo "  备份完成: ${BACKUP_DIR}"
echo "============================================="
echo ""
ls -la "${BACKUP_DIR}/"
