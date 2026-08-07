-- ============================================================
-- 数据库 schema 迁移脚本（用于 16482f8 之后的部署）
-- ============================================================
-- 适用：从任何 master < 16482f8 升级到当前代码版本
-- 用法：mysql -uroot -p dbname < scripts/db_migration.sql
-- 已创建的新表（用 db.create_all() 自动建）：
--   * role_permissions
--   * token_blacklist
-- 手动加的列（MySQL 8.0 不支持 CREATE COLUMN IF NOT EXISTS）：

ALTER TABLE users
  ADD COLUMN permissions JSON NULL COMMENT '菜单权限列表';

ALTER TABLE work_orders
  ADD COLUMN assigned_engineer_name VARCHAR(50) NULL AFTER engineer_id,
  ADD COLUMN assigned_engineer_phone VARCHAR(20) NULL AFTER assigned_engineer_name;

-- 若已存在可注释/跳过（重复执行会报 1060 Duplicate column）
-- 验证：
--   SHOW COLUMNS FROM users LIKE 'permissions';
--   SHOW COLUMNS FROM work_orders LIKE 'assigned_engineer_%';
-- ============================================================

