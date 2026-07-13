# 一键部署脚本
#
# 把本机 (C:\hongmen-after-sales) 的产品库功能 scp 到阿里云 ECS
# 并触发服务器端 rebuild + restart
#
# 用法:
#   .\deploy-to-aliyun.ps1                 # 全流程: scp + rebuild + 验证
#   .\deploy-to-aliyun.ps1 -Step scp       # 只传文件
#   .\deploy-to-aliyun.ps1 -Step rebuild   # 只服务器端 rebuild
#   .\deploy-to-aliyun.ps1 -Step verify    # 只验证
#   .\deploy-to-aliyun.ps1 -Step logs      # 服务器端 logs
#   .\deploy-to-aliyun.ps1 -Step status    # 服务器端容器状态
#   .\deploy-to-aliyun.ps1 -Step rollback  # 回滚
#
# 注意: 兼容 PowerShell 5.1 (Win10 默认), 不用 && / here-string

[CmdletBinding()]
param(
    [ValidateSet('all','scp','rebuild','verify','logs','status','rollback')]
    [string]$Step = 'all',

    [string]$Server = 'root@39.106.217.235',

    [string]$RemoteRoot = '/hongmen-after-sales',

    [string]$LocalRoot = 'C:\hongmen-after-sales',

    [int]$WaitSeconds = 40
)

$ErrorActionPreference = 'Stop'

function Write-Step($msg) { Write-Host '' ; Write-Host "=== $msg ===" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "[OK]  $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[!]   $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "[X]   $msg" -ForegroundColor Red }

# SSH 公共参数: 自动 yes + 不写 known_hosts
$SshOpts = @(
    '-o', 'StrictHostKeyChecking=no',
    '-o', 'UserKnownHostsFile=/dev/null',
    '-o', 'LogLevel=ERROR'
)

# 远端命令串联用 ; 不用 && (PS 5.1 不支持)
function Remote([string[]]$cmds) {
    $joined = ($cmds -join ' ; ')
    & ssh @SshOpts $Server $joined
}

# ---------- 1. scp ----------
function Invoke-Scp {
    Write-Step "Step 1/4: scp 文件到 $Server"

    $relFiles = @(
        'backend/app/api/admin.py',
        'backend/app/models/product.py',
        'backend/init.sql',
        'frontend/src/api/admin.js',
        'frontend/src/views/admin/AdminProducts.vue',
        'frontend/src/views/admin/AdminLogin.vue',
        'frontend/src/views/admin/AdminOrders.vue',
        'frontend/package.json',
        'frontend/package-lock.json',
        '.env.production',
        'Dockerfile.backend',
        'Dockerfile.frontend',
        'docker-compose.yml',
        '.dockerignore',
        'deploy.sh',
        'deploy.ps1',
        'aliyun-prepull.sh',
        'fix-80-port.sh',
        'recover-base-images.sh',
        'backend/requirements.txt'
    )

    $ok = 0
    $fail = 0
    foreach ($rel in $relFiles) {
        $local = Join-Path $LocalRoot $rel
        $target = "$Server`:$RemoteRoot/$rel"
        if (-not (Test-Path $local)) {
            Write-Warn "本地不存在: $local"
            $fail++
            continue
        }
        Write-Host "  -> $rel"
        & scp @SshOpts $local $target 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $ok++
        } else {
            Write-Err "scp 失败: $rel"
            $fail++
        }
    }
    Write-Host ''
    Write-Ok "scp 完成: $ok 成功, $fail 失败"
}

# ---------- 2. rebuild ----------
function Invoke-Rebuild {
    Write-Step "Step 2/4: 服务器端 rebuild + restart"

    $cmds = @(
        "cd $RemoteRoot",
        'docker compose build --no-cache backend frontend',
        'docker compose up -d',
        "sleep $WaitSeconds",
        'docker compose ps'
    )
    Remote $cmds
    if ($LASTEXITCODE -ne 0) { Write-Err "rebuild 失败"; exit 1 }
    Write-Ok "rebuild 完成"
}

# ---------- 3. verify ----------
function Invoke-Verify {
    Write-Step "Step 3/4: 验证产品库 API"

    Write-Host ''
    Write-Host '[3.1] 后端健康检查'
    Remote @('curl -s http://localhost:15000/api/health')

    Write-Host ''
    Write-Host '[3.2] 登录拿 token (请在 SSH 会话里跑):'
    Write-Host '  TOKEN=$(curl -s -X POST http://localhost:15000/api/auth/admin/login \'
    Write-Host '    -H "Content-Type: application/json" \'
    Write-Host '    -d "{\"account\":\"admin\",\"password\":\"你的密码\"}" | jq -r .access_token)'

    Write-Host ''
    Write-Host '[3.3] 测试产品列表 API:'
    Write-Host '  curl -s -H "Authorization: Bearer $TOKEN" \'
    Write-Host '    "http://localhost:15000/api/admin/products?page=1&page_size=5" | jq .'

    Write-Host ''
    Write-Host '[3.4] 测试 CSV 导入:'
    Write-Host '  curl -s -X POST -H "Authorization: Bearer $TOKEN" \'
    Write-Host '    -F "file=@销售订单17_19.csv" \'
    Write-Host '    http://localhost:15000/api/admin/products/import | jq .'

    Write-Host ''
    Write-Host '[3.5] 当前 4 容器状态:'
    Remote @('docker compose ps')
}

# ---------- 4. logs ----------
function Invoke-Logs {
    Write-Step "服务器端 logs (Ctrl+C 退出)"
    & ssh @SshOpts -t $Server "cd $RemoteRoot ; docker compose logs -f --tail=100"
}

# ---------- 5. status ----------
function Invoke-Status {
    Write-Step "服务器端状态"
    Remote @(
        'cd /hongmen-after-sales',
        'docker compose ps',
        'echo ---',
        'curl -s http://localhost:15000/api/health/ready'
    )
}

# ---------- 6. rollback ----------
function Invoke-Rollback {
    Write-Step "回滚产品库 commit"
    Write-Warn "将 revert d0cfcd4 + 4725633"
    $confirm = Read-Host "确认回滚? (yes/no)"
    if ($confirm -ne 'yes') { Write-Warn "已取消"; return }

    $cmds = @(
        'cd /hongmen-after-sales',
        'git revert 4725633 d0cfcd4 --no-edit',
        'docker compose build --no-cache backend frontend',
        'docker compose up -d'
    )
    Remote $cmds
    Write-Ok "回滚完成"
}

# ---------- 主流程 ----------
switch ($Step) {
    'all' {
        Invoke-Scp
        Invoke-Rebuild
        Invoke-Verify
        Write-Step "全部完成!"
        Write-Host "  浏览器访问: http://39.106.217.235/admin/products" -ForegroundColor Green
        Write-Host "  (需先登录 admin 账号)"
    }
    'scp'     { Invoke-Scp }
    'rebuild' { Invoke-Rebuild }
    'verify'  { Invoke-Verify }
    'logs'    { Invoke-Logs }
    'status'  { Invoke-Status }
    'rollback' { Invoke-Rollback }
    default   { Write-Err "未知 step: $Step" }
}
