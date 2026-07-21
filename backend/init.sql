-- ===========================================
-- 红门售后服务系统 - 完整数据库设计
-- ===========================================

CREATE DATABASE IF NOT EXISTS hongmen_after_sales
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE hongmen_after_sales;

-- ===========================================
-- 用户表
-- ===========================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    openid VARCHAR(64) UNIQUE COMMENT '微信openid',
    phone VARCHAR(20) UNIQUE COMMENT '手机号',
    nickname VARCHAR(64),
    avatar VARCHAR(255),
    password_hash VARCHAR(128) COMMENT '管理端密码bcrypt',
    role ENUM('customer','dispatcher','service_point','engineer','operator','admin') NOT NULL DEFAULT 'customer',
    status ENUM('active','disabled') NOT NULL DEFAULT 'active',
    service_point_id INT COMMENT '所属服务点',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_openid (openid),
    INDEX idx_phone (phone),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===========================================
-- 服务点表
-- ===========================================
CREATE TABLE IF NOT EXISTS service_points (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '服务点名称',
    contact_person VARCHAR(50) COMMENT '联系人',
    contact_phone VARCHAR(20) COMMENT '联系电话',
    address VARCHAR(255) COMMENT '地址',
    region VARCHAR(100) COMMENT '所属区域',
    status ENUM('active','disabled') NOT NULL DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===========================================
-- 工程师档案表
-- ===========================================
CREATE TABLE IF NOT EXISTS engineers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT COMMENT '关联用户账号',
    name VARCHAR(50) NOT NULL COMMENT '工程师姓名',
    phone VARCHAR(20) NOT NULL COMMENT '联系电话',
    service_point_id INT NOT NULL COMMENT '所属服务点',
    specialty VARCHAR(200) COMMENT '擅长领域',
    status ENUM('active','disabled') NOT NULL DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (service_point_id) REFERENCES service_points(id),
    INDEX idx_service_point (service_point_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===========================================
-- 产品表
-- ===========================================
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    serial_number VARCHAR(64) UNIQUE COMMENT '产品序列号',
    model VARCHAR(64) COMMENT '产品型号',
    product_family VARCHAR(64) COMMENT '产品族',
    production_date DATE COMMENT '生产日期',
    sap_order_no VARCHAR(32) COMMENT 'SAP销售订单号',
    sap_line_item INT COMMENT 'SAP行项目号',
    status ENUM('active','inactive') DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    -- 销售订单 17~19 CSV 导入字段
    sales_no VARCHAR(32) COMMENT '销售单号',
    customer_name VARCHAR(128) COMMENT '客户名称',
    dealer_name VARCHAR(128) COMMENT '经销商名称',
    dealer_contact VARCHAR(64) COMMENT '经销商联系人',
    dealer_phone VARCHAR(32) COMMENT '经销商电话',
    product_no VARCHAR(64) COMMENT '产品编号(型号代码)',
    product_name VARCHAR(256) COMMENT '产品名称',
    shipping_address VARCHAR(512) COMMENT '发货地址',
    qr_code VARCHAR(64) UNIQUE COMMENT '二维码（一码一物）',
    receiver VARCHAR(64) COMMENT '收货人',
    receiver_phone VARCHAR(32) COMMENT '联系电话',
    order_date DATETIME COMMENT '下单日期',
    delivery_date DATETIME COMMENT '交货日期',
    activation_date DATE COMMENT '激活日期',
    expiry_date DATE COMMENT '截至日期',
    INDEX idx_serial_number (serial_number),
    INDEX idx_qr_code (qr_code),
    INDEX idx_sap_order (sap_order_no, sap_line_item),
    INDEX idx_model (model),
    INDEX idx_sales_no (sales_no),
    INDEX idx_customer_name (customer_name),
    INDEX idx_dealer_name (dealer_name),
    INDEX idx_product_no (product_no),
    INDEX idx_product_name (product_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 兼容老部署：若 products 表存在但缺新列，逐列 ALTER TABLE 添加
-- MySQL 8.0.29+ 支持 ADD COLUMN IF NOT EXISTS

ALTER TABLE products ADD COLUMN IF NOT EXISTS sales_no VARCHAR(32) COMMENT '销售单号';
ALTER TABLE products ADD COLUMN IF NOT EXISTS customer_name VARCHAR(128) COMMENT '客户名称';
ALTER TABLE products ADD COLUMN IF NOT EXISTS dealer_name VARCHAR(128) COMMENT '经销商名称';
ALTER TABLE products ADD COLUMN IF NOT EXISTS dealer_contact VARCHAR(64) COMMENT '经销商联系人';
ALTER TABLE products ADD COLUMN IF NOT EXISTS dealer_phone VARCHAR(32) COMMENT '经销商电话';
ALTER TABLE products ADD COLUMN IF NOT EXISTS product_no VARCHAR(64) COMMENT '产品编号';
ALTER TABLE products ADD COLUMN IF NOT EXISTS product_name VARCHAR(256) COMMENT '产品名称';
ALTER TABLE products ADD COLUMN IF NOT EXISTS shipping_address VARCHAR(512) COMMENT '发货地址';
ALTER TABLE products ADD COLUMN IF NOT EXISTS qr_code VARCHAR(64) COMMENT '二维码';
ALTER TABLE products ADD COLUMN IF NOT EXISTS receiver VARCHAR(64) COMMENT '收货人';
ALTER TABLE products ADD COLUMN IF NOT EXISTS receiver_phone VARCHAR(32) COMMENT '联系电话';
ALTER TABLE products ADD COLUMN IF NOT EXISTS order_date DATETIME COMMENT '下单日期';
ALTER TABLE products ADD COLUMN IF NOT EXISTS delivery_date DATETIME COMMENT '交货日期';

ALTER TABLE products ADD INDEX IF NOT EXISTS idx_qr_code (qr_code);
ALTER TABLE products ADD INDEX IF NOT EXISTS idx_sales_no (sales_no);
ALTER TABLE products ADD INDEX IF NOT EXISTS idx_customer_name (customer_name);
ALTER TABLE products ADD INDEX IF NOT EXISTS idx_dealer_name (dealer_name);
ALTER TABLE products ADD INDEX IF NOT EXISTS idx_product_no (product_no);
ALTER TABLE products ADD INDEX IF NOT EXISTS idx_product_name (product_name);

-- ===========================================
-- 用户产品绑定表
-- ===========================================
CREATE TABLE IF NOT EXISTS user_products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    bind_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    bind_method ENUM('manual','qrcode_product','qrcode_sap') NOT NULL,
    UNIQUE KEY uk_user_product (user_id, product_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===========================================
-- 故障分类表（树形结构）
-- ===========================================
CREATE TABLE IF NOT EXISTS fault_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    parent_id INT DEFAULT 0 COMMENT '父分类ID，0为顶级',
    name VARCHAR(50) NOT NULL COMMENT '分类名称',
    icon VARCHAR(255) COMMENT '分类图标',
    sort_order INT DEFAULT 0 COMMENT '排序',
    status ENUM('active','disabled') NOT NULL DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_parent (parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===========================================
-- 常见故障表
-- ===========================================
CREATE TABLE IF NOT EXISTS common_faults (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL COMMENT '所属分类',
    title VARCHAR(100) NOT NULL COMMENT '故障标题',
    content TEXT COMMENT '故障详情（富文本）',
    product_model VARCHAR(64) COMMENT '适用型号，空=全部',
    images JSON COMMENT '图片列表',
    videos JSON COMMENT '视频列表',
    sort_order INT DEFAULT 0,
    view_count INT DEFAULT 0,
    helpful_count INT DEFAULT 0,
    status ENUM('active','disabled') NOT NULL DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (category_id),
    FOREIGN KEY (category_id) REFERENCES fault_categories(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===========================================
-- 工单表（核心）
-- ===========================================
CREATE TABLE IF NOT EXISTS work_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_no VARCHAR(32) NOT NULL UNIQUE COMMENT '工单号 RM+YYYYMMDD+4位流水',
    user_id INT NOT NULL COMMENT '报修用户',
    product_id INT NOT NULL COMMENT '故障产品',
    fault_category_id INT COMMENT '故障分类',
    fault_type VARCHAR(64) NOT NULL COMMENT '故障类型',
    fault_desc TEXT NOT NULL COMMENT '故障描述',
    images JSON COMMENT '故障图片',
    videos JSON COMMENT '故障视频',
    fault_address VARCHAR(255) COMMENT '故障地址',
    fault_location_lat DECIMAL(10,7) COMMENT '纬度',
    fault_location_lng DECIMAL(10,7) COMMENT '经度',
    appointment_date DATE COMMENT '预约日期',
    appointment_period ENUM('AM','PM') COMMENT '预约时段',
    contact_name VARCHAR(32) NOT NULL,
    contact_phone VARCHAR(20) NOT NULL,
    status ENUM(
        'pending_accept',
        'pending_dispatch',
        'dispatched',
        'assigned_engineer',
        'processing',
        'pending_confirm',
        'completed',
        'closed',
        'cancelled'
    ) NOT NULL DEFAULT 'pending_accept',
    service_point_id INT COMMENT '指派服务点',
    engineer_id INT COMMENT '指派工程师',
    reject_reason VARCHAR(255) COMMENT '拒绝/关闭原因',
    cancel_reason VARCHAR(255) COMMENT '撤销原因',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (service_point_id) REFERENCES service_points(id),
    FOREIGN KEY (engineer_id) REFERENCES engineers(id),
    INDEX idx_user (user_id),
    INDEX idx_status (status),
    INDEX idx_order_no (order_no),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===========================================
-- 工单状态日志
-- ===========================================
CREATE TABLE IF NOT EXISTS order_status_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    from_status VARCHAR(32),
    to_status VARCHAR(32) NOT NULL,
    operator_id INT COMMENT '操作人',
    operator_name VARCHAR(50) COMMENT '操作人姓名（冗余）',
    remark TEXT COMMENT '备注',
    images JSON COMMENT '处理图片',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_order (order_id),
    FOREIGN KEY (order_id) REFERENCES work_orders(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===========================================
-- 客服电话配置表
-- ===========================================
CREATE TABLE IF NOT EXISTS system_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(50) NOT NULL UNIQUE,
    config_value VARCHAR(255),
    description VARCHAR(100),
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===========================================
-- JWT Token 黑名单（登出用）
-- ===========================================
CREATE TABLE IF NOT EXISTS token_blacklist (
    id INT AUTO_INCREMENT PRIMARY KEY,
    token_jti VARCHAR(64) NOT NULL UNIQUE COMMENT 'JWT jti',
    expired_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_jti (token_jti)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===========================================
-- 初始数据
-- ===========================================

-- 默认客服电话
INSERT INTO system_config (config_key, config_value, description) VALUES
('customer_service_phone', '400-123-4567', '客服电话'),
('sms_api_key', '', '短信API密钥')
ON DUPLICATE KEY UPDATE config_value = VALUES(config_value);

-- 默认故障分类
INSERT INTO fault_categories (id, parent_id, name, sort_order) VALUES
(1, 0, '电气系统', 1),
(2, 0, '机械系统', 2),
(3, 0, '控制系统', 3),
(4, 0, '其他', 4),
(5, 1, '无法启动', 1),
(6, 1, '运行异常', 2),
(7, 1, '显示屏故障', 3),
(8, 2, '异响', 1),
(9, 2, '振动异常', 2),
(10, 3, '连接异常', 1),
(11, 3, '程序错误', 2)
ON DUPLICATE KEY UPDATE name = VALUES(name);

-- 默认服务点
INSERT INTO service_points (name, contact_person, contact_phone, address, region) VALUES
('北京服务中心', '张经理', '010-12345678', '北京市朝阳区XX路XX号', '华北'),
('上海服务中心', '李经理', '021-12345678', '上海市浦东新区XX路XX号', '华东'),
('广州服务中心', '王经理', '020-12345678', '广州市天河区XX路XX号', '华南')
ON DUPLICATE KEY UPDATE name = VALUES(name);
