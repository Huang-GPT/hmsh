#!/usr/bin/env bash
# ============================================================
#   红门售后工单系统 - 生产环境 Gunicorn 配置
# ============================================================

# 监听地址（容器内）
bind = "0.0.0.0:5000"

# worker 进程数
workers = int(__import__('os').environ.get('GUNICORN_WORKERS', 4))

# 每个 worker 的线程数
threads = 2

# worker 超时（秒）
timeout = int(__import__('os').environ.get('GUNICORN_TIMEOUT', 60))

# 请求队列满后丢弃新连接（防 DoS）
backlog = 2048

# 进程名（ps/top 显示）
proc_name = "hongmen-after-sales"

# 日志输出到 stdout/stderr（Docker 收集）
accesslog = "-"
errorlog = "-"
loglevel = "info"

# access log 格式
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sus'

# 预加载应用（节省内存 + 提前暴露 import 错误）
preload_app = True

# worker 临时文件放 /dev/shm
worker_tmp_dir = "/dev/shm"

# 优雅重启（收到 SIGTERM 后给 worker 60s 收尾）
graceful_timeout = 30
keepalive = 5
