# 部署产品库功能到阿里云 ECS

把本机 (`C:\hongmen-after-sales`) 的 2 个新 commit
（产品库 + 累积清理）部署到阿里云 ECS (39.106.217.235)。

需要部署的文件清单（**20 个文件**，来自 2 个 commit）：

| 来源 commit | 文件 |
|------------|------|
| `d0cfcd4`  | `backend/app/api/admin.py`（加 5 个产品端点）|
| `d0cfcd4`  | `backend/app/models/product.py`（加 13 个 CSV 字段）|
| `d0cfcd4`  | `backend/init.sql`（schema 扩展 + ALTER 迁移）|
| `d0cfcd4`  | `frontend/src/api/admin.js`（加 4 个函数）|
| `d0cfcd4`  | `frontend/src/views/admin/AdminProducts.vue`（重写）|
| `d0cfcd4`  | `fix-80-port.sh`（80 端口冲突）|
| `d0cfcd4`  | `recover-base-images.sh`（ACR 镜像恢复）|
| `4725633`  | `.env.production`、`Dockerfile.backend`、`Dockerfile.frontend` |
| `4725633`  | `backend/requirements.txt`（+cryptography）|
| `4725633`  | `deploy.sh`、`deploy.ps1`（+bootstrap）|
| `4725633`  | `docker-compose.yml`（网络 + 端口）|
| `4725633`  | `frontend/package.json`、`frontend/package-lock.json` |
| `4725633`  | `frontend/src/views/admin/AdminLogin.vue`（+密码）|
| `4725633`  | `frontend/src/views/admin/AdminOrders.vue`（9 态对齐）|
| `4725633`  | `.dockerignore`、`aliyun-prepull.sh` |

---

## 方式 A：手工 scp（推荐首次）

### 本地 Windows PowerShell（一次性传）

```powershell
# 项目根
$root = "C:\hongmen-after-sales"
$server = "root@39.106.217.235"
$remote = "/hongmen-after-sales"

# 工具函数：scp 相对项目根的多个文件
function Push-Files($relPaths) {
    foreach ($rel in $relPaths) {
        $local = Join-Path $root $rel
        $target = "$server`:$remote/$rel"
        Write-Host "scp $rel"
        scp $local $target
    }
}

# 后端
Push-Files @(
    "backend/app/api/admin.py",
    "backend/app/models/product.py",
    "backend/init.sql",
    "backend/requirements.txt"
)

# 前端
Push-Files @(
    "frontend/src/api/admin.js",
    "frontend/src/views/admin/AdminProducts.vue",
    "frontend/src/views/admin/AdminLogin.vue",
    "frontend/src/views/admin/AdminOrders.vue",
    "frontend/package.json",
    "frontend/package-lock.json"
)

# 部署配置
Push-Files @(
    ".env.production",
    "Dockerfile.backend",
    "Dockerfile.frontend",
    "docker-compose.yml",
    ".dockerignore",
    "deploy.sh",
    "deploy.ps1",
    "aliyun-prepull.sh",
    "fix-80-port.sh",
    "recover-base-images.sh"
)
```

### 阿里云服务器

```bash
cd /hongmen-after-sales

# 1. 重建 backend（含 cryptography + 5 个新端点）
docker compose build --no-cache backend

# 2. 重建 frontend（含 AdminProducts 重写 + AdminLogin 密码 + AdminOrders 9 态）
docker compose build --no-cache frontend

# 3. 重启所有 4 容器
docker compose up -d

# 4. 等待健康检查
sleep 40
docker compose ps
# 期望 4 容器全 healthy
```

### 验证产品库功能

```bash
# 1. 健康检查
curl -s http://localhost:15000/api/health
# 期望: {"status":"ok"}

# 2. 登录拿 token
TOKEN=$(curl -s -X POST http://localhost:15000/api/auth/admin/login \
  -H "Content-Type: application/json" \
  -d '{"account":"admin","password":"你的密码"}' | jq -r .access_token)

echo "Token: $TOKEN"

# 3. 测试产品列表 API
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:15000/api/admin/products?page=1&page_size=5" | jq .
# 期望: {"items": [], "total": 0, "page": 1, "page_size": 5}

# 4. 测试 CSV 导入（用你的销售订单17_19.csv）
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -F "file=@销售订单17_19.csv" \
  http://localhost:15000/api/admin/products/import | jq .
# 期望: {"inserted": N, "skipped": [], "errors": [], "total": N, "filename": "..."}

# 5. 验证导入的记录
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:15000/api/admin/products?keyword=2532622938587124" | jq .
# 期望: items 数组里有 1 条，qr_code="2532622938587124"
```

### 浏览器测试

访问 `http://39.106.217.235/admin/products`（先用 admin 登录）：
- 看搜索框 + "新建产品" + "导入CSV" 按钮
- 点"导入CSV" 选 `销售订单17_19.csv` → 看导入结果弹窗
- 点"新建产品" → 14 字段对话框
- 列表显示导入的产品记录

---

## 方式 B：git pull（前提：已 push 到 GitHub）

如果之前 push 过代码到 GitHub：

```bash
# 阿里云服务器
cd /hongmen-after-sales
git pull
docker compose build --no-cache backend frontend
docker compose up -d
sleep 40
docker compose ps
```

如果还没 push 到 GitHub，先在本机做：

```powershell
# 本地 PowerShell（如果有 GitHub remote）
cd C:\hongmen-after-sales
git remote add origin https://github.com/<user>/hongmen-after-sales.git
git push -u origin master
```

然后阿里云上 `git clone` 或 `git pull`。

---

## 故障排查

| 现象 | 排查 |
|------|------|
| `cryptography` 安装失败 | Dockerfile.backend 已用 `--only-binary=:all:`，若仍 OOM 给服务器加 swap |
| `redis:7-alpine` 拉不到 | 阿里云 ACR 个人版无此 tag，先 `./recover-base-images.sh` |
| 80 端口被占 | `./fix-80-port.sh --proxy` 装宿主机 nginx 反代 |
| `GET /admin/products` 返回 404 | 后端镜像没重建，跑 `docker compose build --no-cache backend` |
| `Module parse failed: ?.` | 这是老版本 babel 问题，commit `537d863` 已修，确保 AdminOrders.vue 是新版 |

---

## 回滚（如果产品库功能有问题）

```bash
# 在阿里云
cd /hongmen-after-sales
git log --oneline -5
# 找到 4725633 和 d0cfcd4 的 commit hash

# 回滚
git revert 4725633 d0cfcd4 --no-edit
docker compose build --no-cache backend frontend
docker compose up -d
```

（前提是阿里云是 git 仓库；如果不是，只能从本机 scp 旧版文件）
