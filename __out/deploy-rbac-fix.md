# RBAC 修复部署命令（一键跑）

> **前置：上一轮我已经改了 8 个文件，但没部署到服务器。服务器上的 1003 看到的是改之前的代码。这就是"看到所有菜单"的根因。**
> 部署后，1003 应该只看到 2~3 个菜单（工作台 / 工单管理 / 工单售后）。

---

## 第一步：commit 本地改动

```powershell
cd C:\hongmen-after-sales
git add backend/app/api/admin.py backend/app/init_rbac.py backend/app/models/user.py backend/app/services/auth_service.py frontend/src/api/admin.js frontend/src/router/index.js frontend/src/views/admin/AdminLayout.vue frontend/src/views/admin/AdminLogin.vue
git status -sb   # 确认只 staged 这 8 个文件
git commit -m "fix(rbac): JWT 读 RBAC 表 / 接口补 permission 装饰器 / 前端守卫 + 菜单过滤"
```

---

## 第二步：推送到 GitHub

```powershell
git push origin master
```

如果 `git push` 失败（GitHub SSH 在 PowerShell 容器里可能挂），可以走 HTTPS：
```powershell
git remote set-url origin https://github.com/Huang-GPT/hmsh.git
git push origin master
# 第一次 push HTTPS 会问账号密码，用 PAT
```

---

## 第三步：服务器拉代码 + 重建

```bash
ssh root@39.106.217.235   # 你用你的 magic.pem 登
cd /hongmen-after-sales
git pull
docker compose build --no-cache backend
docker compose build --no-cache frontend
docker compose up -d
sleep 40
docker compose ps
# 期望：hongmen-frontend / hongmen-backend / hongmen-db / hongmen-redis 4 个全 healthy
```

---

## 第四步：服务器验证（按 PUA #7，≥3 个独立匹配）

### 验证 1：容器都健康
```bash
docker compose ps | grep -E 'hongmen-(frontend|backend|db|redis)'
```

### 验证 2：后端启动时自动绑了 RBAC 角色
```bash
docker logs hongmen-backend --tail 50 | grep -E 'init_rbac|RBAC roles'
# 期望看到：[init_rbac] auto-granted RBAC roles to N users by users.role
# N >= 1（至少 1003 被自动绑了 service_point_admin）
```

### 验证 3：1003 登录后 JWT 里的 permissions 是 RBAC 聚合的 8 个权限
```bash
curl -s -X POST http://localhost:15000/api/auth/admin/login \
  -H "Content-Type: application/json" \
  -d '{"account":"1003","password":"<1003的密码>"}' | python3 -c "
import json,sys
d = json.load(sys.stdin)
u = d.get('user',{})
print('user.id =', u.get('id'))
print('user.role =', u.get('role'))
print('user.permissions =', u.get('permissions'))
print('user.roles =', [r.get('code') for r in u.get('roles',[])])
"
```

**期望输出**（1003 应该是 service_point 角色，自动绑了 service_point_admin）：
```
user.id = <某个ID>
user.role = service_point
user.permissions = ['dashboard:view', 'dealer_order:assign_engineer', 'dealer_order:edit',
                    'dealer_order:export', 'dealer_order:view', 'order:view',
                    'service_point:view', 'statistics:view']
user.roles = ['service_point_admin']
```

### 验证 4：1003 调 admin-only 接口返回 403
```bash
# 先拿 token
TOKEN=$(curl -s -X POST http://localhost:15000/api/auth/admin/login \
  -H "Content-Type: application/json" \
  -d '{"account":"1003","password":"<1003的密码>"}' | jq -r '.user.token // ""')

# 如果上面拿不到 token，从响应 header 取：
# TOKEN=$(curl -s -D - -X POST http://localhost:15000/api/auth/admin/login \
#   -H "Content-Type: application/json" \
#   -d '{"account":"1003","password":"<1003的密码>"}' -o /dev/null \
#   | awk '/^Authorization:/ {print $2}' | tr -d '\r')

curl -sI -H "Authorization: Bearer $TOKEN" http://localhost:15000/api/admin/users
# 期望：HTTP/1.1 403 FORBIDDEN

curl -sI -H "Authorization: Bearer $TOKEN" http://localhost:15000/api/admin/products
# 期望：HTTP/1.1 403 FORBIDDEN

curl -sI -H "Authorization: Bearer $TOKEN" http://localhost:15000/api/admin/roles
# 期望：HTTP/1.1 403 FORBIDDEN
```

### 验证 5：1003 调 dealer 业务接口返回 200
```bash
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:15000/api/admin/dealer-orders?page=1 | head -c 200
# 期望：JSON {"orders": [...]}

curl -s -H "Authorization: Bearer $TOKEN" http://localhost:15000/api/admin/dashboard
# 期望：JSON {"total_orders":N,...}
```

### 验证 6：dashboard 工作台统计也能访问
```bash
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:15000/api/admin/dashboard
# 期望：JSON 数据，不是 403
```

---

## 第五步：浏览器验证（强刷缓存）

```
1. 强制清缓存（防老 admin.js/router 缓存）：
   http://magic666.cn:18080/?v=20251118
   Ctrl+Shift+R 强制刷新

2. 登入 1003：
   http://magic666.cn:18080/admin/login
   账号：1003
   密码：<1003 的密码>

3. 期望看到：
   ✓ 自动跳到 /dealer/orders（service_point 角色跳转）
   ✓ 侧边栏只显示 2~3 个菜单：工作台 / 工单售后 / （可能）工单管理
   ✓ 顶栏显示 "[service_point]"
   ✓ 直接输 /admin/users → 自动跳回 dashboard + ?denied=user:view
   ✓ 直接输 /admin/products → 自动跳回 dashboard
```

---

## 如果还有问题，把以下 3 段贴回来

如果 1003 还是看到全部菜单，**不要急着再改代码**，先收集证据：

1. **docker logs hongmen-backend | tail -80**（看 init_rbac 是否跑了、是否有报错）
2. **1003 登录响应的 user 对象**（第四步验证 3 的输出）
3. **浏览器 F12 → Network → /api/admin/dashboard 响应**（看 permissions 是什么、status code 是什么）

把这 3 段贴回来，我就能精确定位是哪一层没生效（是 RBAC 没绑、JWT 没读对、前端没拦截、还是镜像没更新）。

---

## 时间预估

| 步骤 | 时间 |
|---|---|
| commit + push | 1 分钟 |
| 服务器 pull + build | 5~10 分钟（前端 npm install 慢） |
| 验证 + 浏览器测 | 5 分钟 |
| **总计** | **15~20 分钟** |
