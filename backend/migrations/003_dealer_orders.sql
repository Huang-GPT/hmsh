-- ============================================
--  经销商工单模块 - 数据库迁移
--  执行: docker exec hongmen-db mysql -uroot -phongmen123 hongmen_after_sales < backend/migrations/003_dealer_orders.sql
-- ============================================
USE hongmen_after_sales;

-- 1. 工单表增加经销商填写的工程师字段
ALTER TABLE work_orders
  ADD COLUMN IF NOT EXISTS assigned_engineer_name VARCHAR(50) DEFAULT NULL COMMENT '经销商指定的工程师姓名',
  ADD COLUMN IF NOT EXISTS assigned_engineer_phone VARCHAR(20) DEFAULT NULL COMMENT '经销商指定的工程师电话';

-- 2. 用户表增加权限字段（JSON 格式存储菜单权限）
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS permissions JSON DEFAULT NULL COMMENT '菜单权限列表';

-- 3. 角色-默认权限配置表（供管理员动态调整）
CREATE TABLE IF NOT EXISTS role_permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role ENUM('admin','dispatcher','service_point','engineer','operator','customer') NOT NULL UNIQUE,
    permissions JSON NOT NULL COMMENT '菜单权限列表',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. 初始化角色默认权限
INSERT INTO role_permissions (role, permissions) VALUES
    ('admin',              '[" dashboard\,\orders\,\dealer_orders\,\users\,\products\,\bindings\,\faults\]'),
 ('dispatcher', '[\dashboard\,\orders\,\products\]'),
 ('service_point', '[\dashboard\,\dealer_orders\]'),
 ('engineer', '[\dashboard\]'),
 ('operator', '[\dashboard\,\orders\]'),
 ('customer', '[]')
ON DUPLICATE KEY UPDATE permissions = VALUES(permissions);

-- 5. 将现有用户的权限按角色初始化（若 permissions 为空）
UPDATE users SET permissions = (
 SELECT rp.permissions FROM role_permissions rp WHERE rp.role = users.role
) WHERE permissions IS NULL OR permissions = @'';