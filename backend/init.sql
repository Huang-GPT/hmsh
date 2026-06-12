-- ===========================================
-- 红门售后服务号微信服务系统 - 数据库初始化脚本
-- ===========================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS hongmen_after_sales 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE hongmen_after_sales;

-- ===========================================
-- 用户表
-- ===========================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    openid VARCHAR(64) NOT NULL UNIQUE COMMENT '微信openid',
    nickname VARCHAR(64) COMMENT '微信昵称',
    avatar VARCHAR(255) COMMENT '微信头像',
    phone VARCHAR(20) COMMENT '手机号',
    role ENUM('customer', 'service', 'admin') DEFAULT 'customer' NOT NULL COMMENT '角色：customer-客户, service-客服, admin-管理员',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_openid (openid),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ===========================================
-- 产品表
-- ===========================================
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    serial_number VARCHAR(64) NOT NULL UNIQUE COMMENT '产品序列号',
    model VARCHAR(64) NOT NULL COMMENT '产品型号',
    production_date DATE COMMENT '生产日期',
    sap_order_no VARCHAR(32) COMMENT 'SAP销售订单号',
    sap_line_item VARCHAR(16) COMMENT 'SAP行项目号',
    status ENUM('active', 'inactive') DEFAULT 'active' COMMENT '状态：active-有效, inactive-无效',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_serial_number (serial_number),
    INDEX idx_sap_order (sap_order_no, sap_line_item)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='产品表';

-- ===========================================
-- 用户产品关联表
-- ===========================================
CREATE TABLE IF NOT EXISTS user_products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID',
    product_id INT NOT NULL COMMENT '产品ID',
    bind_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '绑定时间',
    bind_method ENUM('manual', 'qrcode', 'order') NOT NULL COMMENT '绑定方式：manual-手动, qrcode-扫码, order-订单',
    UNIQUE KEY uk_user_product (user_id, product_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户产品关联表';

-- ===========================================
-- 工单表
-- ===========================================
CREATE TABLE IF NOT EXISTS work_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_no VARCHAR(32) NOT NULL UNIQUE COMMENT '工单编号',
    user_id INT NOT NULL COMMENT '用户ID',
    product_id INT NOT NULL COMMENT '产品ID',
    fault_type VARCHAR(32) NOT NULL COMMENT '故障类型',
    fault_desc TEXT NOT NULL COMMENT '故障描述',
    images JSON COMMENT '故障图片',
    contact_name VARCHAR(32) NOT NULL COMMENT '联系人姓名',
    contact_phone VARCHAR(20) NOT NULL COMMENT '联系电话',
    expected_time DATETIME COMMENT '期望服务时间',
    status ENUM('pending_assign', 'pending_process', 'processing', 'pending_confirm', 'completed', 'closed') 
        DEFAULT 'pending_assign' NOT NULL COMMENT '状态',
    handler_id INT COMMENT '处理人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_order_no (order_no),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (handler_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工单表';

-- ===========================================
-- 工单状态记录表
-- ===========================================
CREATE TABLE IF NOT EXISTS order_status_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL COMMENT '工单ID',
    from_status VARCHAR(32) COMMENT '原状态',
    to_status VARCHAR(32) NOT NULL COMMENT '新状态',
    operator_id INT NOT NULL COMMENT '操作人ID',
    remark VARCHAR(255) COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    INDEX idx_order_id (order_id),
    FOREIGN KEY (order_id) REFERENCES work_orders(id) ON DELETE CASCADE,
    FOREIGN KEY (operator_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工单状态记录表';

-- ===========================================
-- 常见故障表
-- ===========================================
CREATE TABLE IF NOT EXISTS common_faults (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_model VARCHAR(64) NOT NULL COMMENT '产品型号',
    fault_type VARCHAR(32) NOT NULL COMMENT '故障类型',
    fault_desc TEXT NOT NULL COMMENT '故障描述',
    solution TEXT NOT NULL COMMENT '解决方案',
    view_count INT DEFAULT 0 COMMENT '查看次数',
    helpful_count INT DEFAULT 0 COMMENT '有帮助次数',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_product_model (product_model),
    INDEX idx_fault_type (fault_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='常见故障表';

-- ===========================================
-- 插入初始管理员账号
-- ===========================================
INSERT INTO users (openid, nickname, role) VALUES 
('admin_system', '系统管理员', 'admin')
ON DUPLICATE KEY UPDATE nickname = '系统管理员';

-- ===========================================
-- 插入示例常见故障数据
-- ===========================================
INSERT INTO common_faults (product_model, fault_type, fault_desc, solution) VALUES
('HM-001', '无法启动', '设备按下电源键无反应', '1. 检查电源线是否插好\n2. 检查电池是否有电\n3. 长按电源键5秒尝试重启'),
('HM-001', '运行异常', '设备运行时有异响', '1. 检查是否有异物卡住\n2. 检查设备是否放置平稳\n3. 联系售后服务'),
('HM-001', '显示屏故障', '屏幕显示不正常或黑屏', '1. 检查亮度设置\n2. 长按电源键重启\n3. 如问题持续，联系售后'),
('HM-002', '无法启动', '设备通电后无任何反应', '1. 检查电源适配器\n2. 检查插座是否通电\n3. 尝试更换电源线'),
('HM-002', '连接异常', '无法连接到WiFi或蓝牙', '1. 重启设备\n2. 检查网络设置\n3. 恢复出厂设置后重试')
ON DUPLICATE KEY UPDATE view_count = view_count;

-- ===========================================
-- 授予权限（如果需要远程访问）
-- ===========================================
-- GRANT ALL PRIVILEGES ON hongmen_after_sales.* TO 'root'@'%';
-- FLUSH PRIVILEGES;