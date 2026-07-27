# 服务器端脚本（**必须**在服务器 PowerShell 跑）

本目录下的所有脚本都是 **服务器侧操作**，不能在本地跑。

## deploy_frontend_clean_server.sh

彻底重建前端 Docker 容器（清旧镜像 + 强制 rebuild + force-recreate）。

### 为什么需要
- 前端 Dockerfile 是多阶段 build：node:16-alpine builder → nginx:alpine
- 如果只跑 `docker compose build --no-cache frontend` 但不删旧镜像，旧镜像会继续跑
- 必须 `--force-recreate` 才会用新镜像
- 必须清旧镜像层缓存，否则 build 命中旧 COPY 层

### 使用方式

```bash
# 在本地 PowerShell，SSH 上服务器跑
ssh root@39.106.217.235 "bash /hongmen-after-sales/scripts/server/deploy_frontend_clean_server.sh"
```

### 验证脚本输出

跑完后应看到：

```
[1/5] 停止并删除旧容器  ✓
[2/5] 删除旧镜像         ✓
[3/5] 重新 build 前端     ✓ (这一步会 3-5 分钟)
[4/5] 启动新容器          ✓
[5/5] 验证                ✓
```

`[5/5 验证]` 输出应包含：
- `ls /usr/share/nginx/html/js/` 出现 `app.xxx.js` 文件
- `grep -c "期望服务时间"` 结果 >= 1
- `grep -c "type.:.date"` 结果 >= 3

### 浏览器访问（必须用破缓存参数）

```
http://39.106.217.235:18080/product/repair?v=$(date +%s)
```

## cleanup_uploads.py

清理 `/app/uploads/` 下的历史视频文件（节省磁盘空间，前端已禁止视频上传）。

### 使用方式

```bash
# 1) 复制进容器
ssh root@39.106.217.235 "docker cp /hongmen-after-sales/scripts/cleanup_uploads.py hongmen-backend:/tmp/"

# 2) 先 dry-run 预览
ssh root@39.106.217.235 "docker exec hongmen-backend python /tmp/cleanup_uploads.py --dry-run"

# 3) 确认后真删
ssh root@39.106.217.235 "docker exec hongmen-backend python /tmp/cleanup_uploads.py"

# 4) 看磁盘释放
ssh root@39.106.217.235 "df -h"
```

### 写在最后

> 所有服务器操作都通过本地 PowerShell 的 SSH 转发。
> 不要试图在 opencode agent 内直接 ssh/scp —— 沙箱里没网络。