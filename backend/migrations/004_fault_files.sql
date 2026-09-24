-- ============================================
--  故障文件库 v2 (2026-09 重构) - 数据库迁移
--  执行: docker exec -i hongmen-db mysql -uroot -phongmen123 hongmen_after_sales < backend/migrations/004_fault_files.sql
--
--  改动：
--  1. 新建 fault_files 表（平铺的 PDF/图片/文档库，不依赖旧 fault_categories / common_faults）
--  2. 旧表保留不动（兼容）
-- ============================================
USE hongmen_after_sales;

CREATE TABLE IF NOT EXISTS fault_files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL COMMENT '原始文件名',
    url VARCHAR(512) NOT NULL COMMENT '存储路径 /uploads/faults2/<date>/<uuid>.<ext>',
    size INT NOT NULL DEFAULT 0 COMMENT '字节',
    mime VARCHAR(128) COMMENT 'MIME 类型',
    kind ENUM('pdf','image','doc') NOT NULL COMMENT '文件分类（pdf / image / doc）',
    description VARCHAR(500) COMMENT '可选描述',
    sort_order INT DEFAULT 0,
    status ENUM('active','disabled') NOT NULL DEFAULT 'active',
    uploaded_by INT COMMENT '上传者用户 ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    deleted_at DATETIME COMMENT '软删时间（NULL=可见）',
    INDEX idx_kind_active (kind, status, deleted_at),
    INDEX idx_uploaded_by (uploaded_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;