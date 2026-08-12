-- RBAC 迁移
-- 1. users 表加扩展字段
ALTER TABLE users
  ADD COLUMN email VARCHAR(128) NULL COMMENT '邮箱',
  ADD COLUMN real_name VARCHAR(64) NULL COMMENT '真实姓名',
  ADD COLUMN department VARCHAR(64) NULL COMMENT '部门',
  ADD COLUMN remark VARCHAR(255) NULL COMMENT '备注',
  ADD COLUMN last_login_at DATETIME NULL COMMENT '最近登录时间';

-- 2. permissions 表
CREATE TABLE IF NOT EXISTS permissions (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  code VARCHAR(64) NOT NULL UNIQUE COMMENT '权限编码',
  name VARCHAR(64) NOT NULL COMMENT '权限名称',
  module VARCHAR(32) NOT NULL COMMENT '所属模块',
  action VARCHAR(32) NOT NULL COMMENT '操作类型',
  description VARCHAR(255) NULL,
  sort_order INT DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_module (module)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='权限资源';

-- 3. roles 表
CREATE TABLE IF NOT EXISTS roles (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  code VARCHAR(32) NOT NULL UNIQUE COMMENT '角色编码',
  name VARCHAR(64) NOT NULL COMMENT '角色名称',
  description VARCHAR(255) NULL,
  builtin TINYINT(1) DEFAULT 0 COMMENT '内置角色',
  status VARCHAR(16) DEFAULT 'active' NOT NULL,
  sort_order INT DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色';

-- 4. role_permissions_v2 表（角色-权限）
CREATE TABLE IF NOT EXISTS role_permissions_v2 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  role_id INT NOT NULL,
  permission_id INT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_role_permission (role_id, permission_id),
  INDEX idx_role (role_id),
  INDEX idx_perm (permission_id),
  FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
  FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色-权限';

-- 5. user_roles 表（用户-角色）
CREATE TABLE IF NOT EXISTS user_roles (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  role_id INT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_user_role (user_id, role_id),
  INDEX idx_user (user_id),
  INDEX idx_role (role_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户-角色';

-- 6. legacy_role_permissions 表（保留旧 RBAC 表）
CREATE TABLE IF NOT EXISTS legacy_role_permissions (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  role VARCHAR(32) NOT NULL UNIQUE,
  permissions JSON NOT NULL,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='旧 RBAC 兼容表';
