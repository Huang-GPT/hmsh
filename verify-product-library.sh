#!/usr/bin/env bash
# 服务器端产品库功能验证脚本
# 在阿里云服务器 /hongmen-after-sales 目录跑
#
# 用法:
#   ./verify-product-library.sh                 # 全流程验证
#   ./verify-product-library.sh token           # 单独打 token
#   ./verify-product-library.sh health          # 单独看 health
#   ./verify-product-library.sh list           # 列表 API
#   ./verify-product-library.sh import <file>   # 导入 CSV
#   ./verify-product-library.sh cleanup         # 删测试数据

set -e

API="http://localhost:15000/api"
TOKEN_FILE="/tmp/hongmen_token"

color() {
    case "$1" in
        ok)   echo -e "\033[0;32m$2\033[0m" ;;
        err)  echo -e "\033[0;31m$2\033[0m" ;;
        info) echo -e "\033[0;36m$2\033[0m" ;;
        *)    echo "$2" ;;
    esac
}

# 1. 拿 token
get_token() {
    # 默认密码从 .env 读
    if [ ! -f .env ]; then
        color err ".env 不存在"
        return 1
    fi
    local account
    account=$(grep "^WECHAT_APP_ID\|^DB_PASSWORD" .env | head -1 > /dev/null; echo "admin")
    # 简化：直接提示输入
    echo ""
    color info "请输入 admin 账号密码"
    read -p "  账号 [默认 admin]: " -r input_acc
    local acc="${input_acc:-admin}"
    read -s -p "  密码: " input_pwd
    echo ""

    local resp
    resp=$(curl -s -X POST "$API/auth/admin/login" \
        -H "Content-Type: application/json" \
        -d "{\"account\":\"$acc\",\"password\":\"$input_pwd\"}")

    local token
    token=$(echo "$resp" | python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)

    if [ -z "$token" ]; then
        color err "登录失败: $resp"
        return 1
    fi
    echo "$token" > "$TOKEN_FILE"
    color ok "token 已保存到 $TOKEN_FILE"
    echo "$token"
}

# 2. health
do_health() {
    color info "[health check]"
    curl -s "$API/health"
    echo ""
    color info "[ready check (DB)]"
    curl -s "$API/health/ready"
    echo ""
}

# 3. 列表
do_list() {
    color info "[list products]"
    local token
    token=$(cat "$TOKEN_FILE" 2>/dev/null) || { color err "无 token，先跑 token"; return 1; }

    curl -s -H "Authorization: Bearer $token" \
        "$API/admin/products?page=1&page_size=5" | python3 -m json.tool
}

# 4. 导入
do_import() {
    local file="$1"
    color info "[import $file]"
    if [ ! -f "$file" ]; then
        color err "文件不存在: $file"
        return 1
    fi
    local token
    token=$(cat "$TOKEN_FILE" 2>/dev/null) || { color err "无 token"; return 1; }

    curl -s -X POST -H "Authorization: Bearer $token" \
        -F "file=@$file" \
        "$API/admin/products/import" | python3 -m json.tool
}

# 5. 创建测试
do_create_test() {
    color info "[create test product]"
    local token
    token=$(cat "$TOKEN_FILE" 2>/dev/null) || { color err "无 token"; return 1; }

    curl -s -X POST -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d '{"qr_code":"TEST_QR_001","product_no":"TEST001","product_name":"测试产品","customer_name":"测试客户","sales_no":"TEST-ORDER-001"}' \
        "$API/admin/products" | python3 -m json.tool
}

# 6. 删除测试
do_cleanup() {
    color info "[cleanup test data]"
    local token
    token=$(cat "$TOKEN_FILE" 2>/dev/null) || { color err "无 token"; return 1; }

    # 拿所有 test_ 开头的 qr_code
    local ids
    ids=$(curl -s -H "Authorization: Bearer $token" \
        "$API/admin/products?keyword=TEST_" | python3 -c "
import sys,json
data = json.load(sys.stdin)
for p in data.get('items', []):
    if p.get('qr_code','').startswith('TEST_'):
        print(p['id'])
")
    for id in $ids; do
        color info "  delete id=$id"
        curl -s -X DELETE -H "Authorization: Bearer $token" "$API/admin/products/$id" >/dev/null
    done
    color ok "清理完成"
}

# 主入口
case "${1:-all}" in
    health)  do_health ;;
    token)   get_token ;;
    list)    do_list ;;
    import)  do_import "$2" ;;
    create)  do_create_test ;;
    cleanup) do_cleanup ;;
    all|"")
        do_health
        echo ""
        get_token > /dev/null
        echo ""
        color info "=== 创建测试产品 ==="
        do_create_test
        echo ""
        color info "=== 列表 ==="
        do_list
        echo ""
        color info "=== 清理测试 ==="
        do_cleanup
        echo ""
        color ok "=== 全部完成 ==="
        color info "浏览器访问: http://39.106.217.235/admin/products"
        ;;
    *) color err "未知命令: $1"; exit 1 ;;
esac
