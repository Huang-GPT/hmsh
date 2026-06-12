# 红门售后服务号微信服务系统

基于微信公众号的售后工单管理系统，支持产品绑定、维修工单、进度查询、常见故障等功能。

## 快速部署

### Windows系统

```bash
# 双击运行部署脚本
deploy.bat
```

### Linux/Mac系统

```bash
# 添加执行权限
chmod +x deploy.sh

# 运行部署脚本
./deploy.sh
```

### 手动部署

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入真实配置

# 2. 构建并启动
docker-compose up -d

# 3. 访问系统
# 前端: http://localhost
# 后端API: http://localhost:5000/api
```

## 功能特性

- ✅ 用户认证（微信OAuth）
- ✅ 产品绑定（手动、扫码、订单）
- ✅ 工单管理（创建、状态流转、进度查询）
- ✅ 常见故障知识库
- ✅ ERP系统集成
- ✅ 微信模板消息通知
- ✅ 管理后台

## 项目结构

```
hongmen-after-sales/
├── docker-compose.yml      # Docker编排配置
├── deploy.bat             # Windows部署脚本
├── deploy.sh              # Linux部署脚本
├── .env.example           # 环境变量示例
├── frontend/              # 前端项目
├── backend/               # 后端项目
│   ├── init.sql           # 数据库初始化脚本
│   └── app/               # 应用代码
└── data/                  # 数据目录（自动创建）
    ├── mysql/             # MySQL数据
    └── redis/             # Redis数据
```

## 环境要求

- Docker 20.10+
- Docker Compose 2.0+

## 配置说明

编辑 `.env` 文件：

```bash
# 数据库密码
DB_PASSWORD=your_password

# 微信公众号配置
WECHAT_APP_ID=wx1234567890abcdef
WECHAT_APP_SECRET=your_secret

# ERP系统配置
ERP_API_URL=https://erp.hongmen.com/api
ERP_API_KEY=your_api_key
```

## 常用命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 查看日志
docker-compose logs -f

# 查看状态
docker-compose ps

# 重启服务
docker-compose restart
```

## 访问地址

| 服务 | 地址 |
|------|------|
| 前端页面 | http://localhost |
| 后端API | http://localhost:5000/api |
| MySQL | localhost:3306 |
| Redis | localhost:6379 |

## 数据备份

```bash
# 备份数据库
docker-compose exec db mysqldump -uroot -p hongmen_after_sales > backup.sql

# 恢复数据库
docker-compose exec db mysql -uroot -p hongmen_after_sales < backup.sql
```

## 问题排查

查看服务日志：
```bash
docker-compose logs -f
```

检查服务状态：
```bash
docker-compose ps
```

重启所有服务：
```bash
docker-compose restart
```

## 技术栈

- **前端**: Vue.js 2.6 + Vant UI + 微信JS-SDK
- **后端**: Python Flask + SQLAlchemy
- **数据库**: MySQL 8.0 + Redis 7
- **部署**: Docker + Nginx

## 文档

- [部署指南](docs/deployment-guide.md)
- [需求文档](docs/compose/specs/2026-06-11-hongmen-after-sales-service-wechat-design.md)
- [实现计划](docs/compose/plans/2026-06-11-hongmen-after-sales-implementation.md)