# 红门售后服务号微信服务系统 - 部署指南

## 目录

1. [环境要求](#环境要求)
2. [项目结构](#项目结构)
3. [配置文件说明](#配置文件说明)
4. [部署步骤](#部署步骤)
5. [常用命令](#常用命令)
6. [问题排查](#问题排查)

---

## 环境要求

### 必需软件

| 软件 | 版本要求 | 说明 |
|------|----------|------|
| Docker | 20.10+ | 容器化运行环境 |
| Docker Compose | 2.0+ | 多容器编排工具 |
| Git | 2.0+ | 代码版本管理 |

### 可选软件（本地开发）

| 软件 | 版本要求 | 说明 |
|------|----------|------|
| Node.js | 16+ | 前端开发环境 |
| Python | 3.8+ | 后端开发环境 |
| MySQL | 5.7+ | 数据库（Docker会自动创建） |

---

## 项目结构

```
hongmen-after-sales/
├── docker-compose.yml          # Docker编排配置
├── Dockerfile.frontend         # 前端Docker镜像
├── Dockerfile.backend          # 后端Docker镜像
├── nginx.conf                  # Nginx配置文件
├── .env.example                # 环境变量示例
├── .env                        # 环境变量（需创建）
├── frontend/                   # 前端项目
│   ├── package.json
│   ├── vue.config.js
│   ├── public/
│   └── src/
└── backend/                    # 后端项目
    ├── requirements.txt
    ├── config.py
    ├── run.py
    └── app/
```

---

## 配置文件说明

### 1. 环境变量文件 (.env)

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

**.env 文件内容：**

```bash
# ===========================================
# 数据库配置
# ===========================================
DB_PASSWORD=your_strong_password_here

# ===========================================
# 微信公众号配置
# ===========================================
# 从微信公众平台获取
WECHAT_APP_ID=wx1234567890abcdef
WECHAT_APP_SECRET=your_wechat_app_secret_here

# ===========================================
# ERP系统配置
# ===========================================
# 红门ERP系统API地址
ERP_API_URL=https://erp.hongmen.com/api
# ERP系统API密钥
ERP_API_KEY=your_erp_api_key_here

# ===========================================
# 前端配置（可选）
# ===========================================
# 前端访问地址（用于生成回调链接）
FRONTEND_URL=http://your-domain.com

# ===========================================
# 微信模板消息ID（可选）
# ===========================================
WECHAT_TEMPLATE_ORDER_STATUS=your_template_id_here
```

### 2. Nginx配置文件 (nginx.conf)

```nginx
server {
    listen 80;
    server_name localhost;
    
    # 前端静态文件
    root /usr/share/nginx/html;
    index index.html;

    # 前端路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api {
        proxy_pass http://backend:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 禁止访问隐藏文件
    location ~ /\. {
        deny all;
    }
}
```

### 3. Docker Compose配置 (docker-compose.yml)

```yaml
version: '3.8'

services:
  # 前端服务（Nginx）
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - app-network

  # 后端服务（Flask）
  backend:
    build:
      context: ./backend
      dockerfile: ../Dockerfile.backend
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=mysql+pymysql://root:${DB_PASSWORD}@db/hongmen_after_sales
      - REDIS_URL=redis://redis:6379/0
      - WECHAT_APP_ID=${WECHAT_APP_ID}
      - WECHAT_APP_SECRET=${WECHAT_APP_SECRET}
      - ERP_API_URL=${ERP_API_URL}
      - ERP_API_KEY=${ERP_API_KEY}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    restart: unless-stopped
    networks:
      - app-network

  # MySQL数据库
  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=${DB_PASSWORD}
      - MYSQL_DATABASE=hongmen_after_sales
      - MYSQL_CHARACTER_SET_SERVER=utf8mb4
      - MYSQL_COLLATION_SERVER=utf8mb4_unicode_ci
    volumes:
      - mysql_data:/var/lib/mysql
      - ./backend/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "3306:3306"
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - app-network

  # Redis缓存
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    networks:
      - app-network

volumes:
  mysql_data:
  redis_data:

networks:
  app-network:
    driver: bridge
```

### 4. 前端Dockerfile (Dockerfile.frontend)

```dockerfile
# 第一阶段：构建
FROM node:16-alpine as builder

WORKDIR /app

# 安装依赖
COPY package*.json ./
RUN npm ci --only=production

# 复制源码并构建
COPY . .
RUN npm run build

# 第二阶段：运行
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制Nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 5. 后端Dockerfile (Dockerfile.backend)

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# 启动Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:create_app()"]
```

---

## 部署步骤

### 第一步：克隆项目

```bash
# 克隆项目到服务器
git clone <repository-url> hongmen-after-sales
cd hongmen-after-sales
```

### 第二步：配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑环境变量文件
# Windows:
notepad .env

# Linux/Mac:
nano .env
```

**必须配置的参数：**

| 参数 | 说明 | 示例 |
|------|------|------|
| `DB_PASSWORD` | MySQL root密码 | `MyStr0ngP@ssw0rd` |
| `WECHAT_APP_ID` | 微信公众号AppID | `wx1234567890abcdef` |
| `WECHAT_APP_SECRET` | 微信公众号AppSecret | `abcdef1234567890` |
| `ERP_API_URL` | ERP系统API地址 | `https://erp.hongmen.com/api` |
| `ERP_API_KEY` | ERP系统API密钥 | `your-api-key` |

### 第三步：创建数据库初始化脚本

```bash
# 创建后端初始化目录
mkdir -p backend

# 创建init.sql文件
cat > backend/init.sql << 'EOF'
-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS hongmen_after_sales 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE hongmen_after_sales;

-- 授予权限
GRANT ALL PRIVILEGES ON hongmen_after_sales.* TO 'root'@'%';
FLUSH PRIVILEGES;
EOF
```

### 第四步：构建并启动服务

```bash
# 构建所有镜像
docker-compose build

# 启动所有服务（后台运行）
docker-compose up -d

# 查看启动状态
docker-compose ps
```

### 第五步：验证部署

```bash
# 查看服务日志
docker-compose logs -f

# 测试后端API
curl http://localhost:5000/api/health

# 测试前端页面
curl http://localhost:80
```

### 第六步：初始化数据库表

```bash
# 进入后端容器
docker-compose exec backend bash

# 运行数据库迁移
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"

# 退出容器
exit
```

---

## 常用命令

### 服务管理

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启所有服务
docker-compose restart

# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f [service_name]

# 查看实时日志
docker-compose logs -f --tail=100
```

### 单个服务管理

```bash
# 重启前端服务
docker-compose restart frontend

# 重启后端服务
docker-compose restart backend

# 查看后端日志
docker-compose logs -f backend

# 进入后端容器
docker-compose exec backend bash

# 进入数据库容器
docker-compose exec db bash
```

### 数据库操作

```bash
# 进入MySQL命令行
docker-compose exec db mysql -uroot -p

# 备份数据库
docker-compose exec db mysqldump -uroot -p hongmen_after_sales > backup.sql

# 恢复数据库
docker-compose exec db mysql -uroot -p hongmen_after_sales < backup.sql
```

### 更新部署

```bash
# 拉取最新代码
git pull

# 重新构建并部署
docker-compose up -d --build

# 或者分步执行
docker-compose build
docker-compose up -d
```

---

## 问题排查

### 1. 端口被占用

**错误信息：**
```
Bind for 0.0.0.0:80 failed: port is already allocated
```

**解决方案：**
```bash
# 查看占用端口的进程
# Windows:
netstat -ano | findstr :80

# Linux:
lsof -i :80

# 停止占用端口的进程，或修改docker-compose.yml中的端口映射
```

### 2. 数据库连接失败

**错误信息：**
```
OperationalError: (pymysql.err.OperationalError) (2003, "Can't connect to MySQL server")
```

**解决方案：**
```bash
# 检查数据库服务是否启动
docker-compose ps db

# 检查数据库日志
docker-compose logs db

# 确认.env中的DB_PASSWORD配置正确
```

### 3. 前端页面404

**错误信息：**
访问页面显示404或空白页

**解决方案：**
```bash
# 检查Nginx配置
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf

# 检查前端构建是否成功
docker-compose logs frontend

# 重新构建前端
docker-compose build frontend
docker-compose up -d frontend
```

### 4. 后端API无响应

**错误信息：**
```
502 Bad Gateway
```

**解决方案：**
```bash
# 检查后端服务状态
docker-compose ps backend

# 检查后端日志
docker-compose logs backend

# 进入容器检查进程
docker-compose exec backend ps aux

# 重启后端服务
docker-compose restart backend
```

### 5. 微信授权失败

**错误信息：**
```
微信授权回调失败
```

**解决方案：**
1. 确认微信公众平台配置的回调域名正确
2. 检查 `.env` 中的 `WECHAT_APP_ID` 和 `WECHAT_APP_SECRET`
3. 确认服务器域名已通过ICP备案
4. 检查微信公众号是否已认证

### 6. 容器无法启动

**错误信息：**
```
Error response from daemon: Cannot start container
```

**解决方案：**
```bash
# 清理Docker资源
docker-compose down
docker system prune -a

# 重新构建
docker-compose build --no-cache
docker-compose up -d
```

---

## 生产环境配置

### 1. 使用HTTPS

```bash
# 安装certbot（Let's Encrypt）
# 将证书挂载到Nginx
# 修改nginx.conf添加SSL配置
```

### 2. 配置域名

```bash
# 修改nginx.conf中的server_name
server_name your-domain.com;

# 配置DNS解析
```

### 3. 数据持久化

```bash
# 已配置Docker volumes，数据会自动持久化
# 备份重要数据
docker-compose exec db mysqldump -uroot -p hongmen_after_sales > backup_$(date +%Y%m%d).sql
```

### 4. 监控和日志

```bash
# 配置日志轮转
# 使用docker logs命令查看日志
# 考虑使用ELK或Prometheus进行监控
```

---

## 技术支持

如有问题，请联系：

- **项目地址**: `C:\hongmen-after-sales`
- **文档位置**: `C:\hongmen-after-sales\docs`

---

**最后更新**: 2026-06-12