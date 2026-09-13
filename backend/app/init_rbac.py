"""
RBAC 初始化：在 backend 容器启动时自动建表 + seed 预置数据
幂等：每次启动检查，若表为空则 seed
"""
from app import db
from app.models.rbac import Permission, Role, RolePermission, UserRole
from app.models.user import User
from app.services.auth_service import hash_password


# 47 个预置权限 — 与前端 rbac_design.json 严格对齐
PRESET_PERMISSIONS = [
    ('dashboard:view', '查看工作台', 'dashboard', 'view', '查看数据概览与统计', 1),

    ('order:view', '查看工单', 'order', 'view', '查看工单列表与详情', 10),
    ('order:accept', '受理工单', 'order', 'accept', '从待受理转为受理', 11),
    ('order:dispatch', '派发工单', 'order', 'dispatch', '总部派单给服务点', 12),
    ('order:assign_engineer', '分配工程师', 'order', 'assign', '给工单指定工程师', 13),
    ('order:start_process', '开始处理', 'order', 'process', '标记工单开始处理', 14),
    ('order:complete', '完成工单', 'order', 'complete', '工程师完成处理', 15),
    ('order:confirm', '确认完成', 'order', 'confirm', '客户确认完成', 16),
    ('order:reject', '拒绝工单', 'order', 'reject', '拒绝工单', 17),
    ('order:cancel', '撤销工单', 'order', 'cancel', '撤销工单', 18),
    ('order:edit', '编辑工单', 'order', 'edit', '编辑工单信息', 19),
    ('order:delete', '删除工单', 'order', 'delete', '永久删除工单', 20),
    ('order:export', '导出工单', 'order', 'export', '导出工单数据', 21),
    ('order:reopen', '取消关闭工单', 'order', 'reopen', '把已关闭工单恢复到安全业务状态', 22),

    ('dealer_order:view', '查看售后工单', 'dealer_order', 'view', '查看经销商工单', 30),
    ('dealer_order:accept_admin', '总部代接单', 'dealer_order', 'accept', '总部代替经销商接单', 31),
    ('dealer_order:edit', '编辑售后工单', 'dealer_order', 'edit', '修改售后工单信息', 32),
    ('dealer_order:export', '导出售后工单', 'dealer_order', 'export', '导出售后工单', 33),
    ('dealer_order:assign_engineer', '指派工程师', 'dealer_order', 'assign', '给售后工单指派工程师', 34),

    ('user:view', '查看用户', 'user', 'view', '查看用户列表', 40),
    ('user:create', '新建用户', 'user', 'create', '创建新账号', 41),
    ('user:edit', '编辑用户', 'user', 'edit', '修改用户信息', 42),
    ('user:delete', '删除用户', 'user', 'delete', '删除账号', 43),
    ('user:toggle_status', '启停账号', 'user', 'toggle', '启用/停用账号', 44),
    ('user:reset_password', '重置密码', 'user', 'reset', '重置用户密码', 45),

    ('role:view', '查看角色', 'role', 'view', '查看角色列表', 50),
    ('role:create', '新建角色', 'role', 'create', '创建新角色', 51),
    ('role:edit', '编辑角色', 'role', 'edit', '修改角色与权限', 52),
    ('role:delete', '删除角色', 'role', 'delete', '删除非内置角色', 53),
    ('role:assign', '分配角色', 'role', 'assign', '为用户分配角色', 54),

    ('product:view', '查看产品', 'product', 'view', '查看产品列表', 60),
    ('product:create', '新建产品', 'product', 'create', '新增产品', 61),
    ('product:edit', '编辑产品', 'product', 'edit', '修改产品', 62),
    ('product:delete', '删除产品', 'product', 'delete', '删除产品', 63),

    ('binding:view', '查看绑定记录', 'binding', 'view', '查看产品绑定记录', 70),
    ('binding:create', '创建绑定', 'binding', 'create', '手动创建绑定记录', 71),
    ('binding:edit', '编辑绑定', 'binding', 'edit', '修改绑定记录', 72),

    ('fault:view', '查看故障库', 'fault', 'view', '查看常见故障', 80),
    ('fault:create', '新建故障', 'fault', 'create', '新增故障条目', 81),
    ('fault:edit', '编辑故障', 'fault', 'edit', '修改故障条目', 82),
    ('fault:delete', '删除故障', 'fault', 'delete', '删除故障条目', 83),

    ('service_point:view', '查看服务点', 'service_point', 'view', '查看服务点', 90),
    ('service_point:create', '新建服务点', 'service_point', 'create', '新增服务点', 91),
    ('service_point:edit', '编辑服务点', 'service_point', 'edit', '修改服务点', 92),

    ('statistics:view', '查看统计', 'statistics', 'view', '查看数据统计', 100),
    ('statistics:export', '导出统计', 'statistics', 'export', '导出统计报表', 101),

    ('system:config', '系统设置', 'system', 'config', '修改系统配置', 110),
    ('system:audit_log', '审计日志', 'system', 'audit', '查看操作审计', 111),
]


# 预置角色 — 6 个
PRESET_ROLES = [
    {
        'code': 'admin',
        'name': '系统管理员',
        'description': '拥有系统全部权限（不可删除）',
        'builtin': True,
        'sort_order': 1,
        'permissions': '__all__',  # 全部权限
    },
    {
        'code': 'dispatcher',
        'name': '总部派单员',
        'description': '总部客服，负责派单与售后监督',
        'builtin': True,
        'sort_order': 2,
        'permissions': [
            'dashboard:view',
            'order:view', 'order:accept', 'order:dispatch', 'order:assign_engineer',
            'order:edit',
            'order:reject', 'order:cancel', 'order:export',
            'dealer_order:view', 'dealer_order:accept_admin',
            'dealer_order:assign_engineer', 'dealer_order:export',
            'service_point:view',
            'statistics:view', 'statistics:export',
        ],
    },
    {
        'code': 'service_point_admin',
        'name': '经销商管理员',
        'description': '经销商负责人，管理本服务点工单与工程师',
        'builtin': True,
        'sort_order': 3,
        'permissions': [
            'dashboard:view',
            'dealer_order:view', 'dealer_order:edit', 'dealer_order:assign_engineer', 'dealer_order:export',
            'order:view', 'order:edit',
            'order:assign_engineer',
            'service_point:view', 'service_point:edit',
            'statistics:view',
        ],
    },
    {
        'code': 'engineer',
        'name': '工程师',
        'description': '上门维修工程师，处理指派的工单',
        'builtin': True,
        'sort_order': 4,
        'permissions': [
            'dashboard:view',
            'order:view', 'order:start_process', 'order:complete',
            'dealer_order:view',
        ],
    },
    {
        'code': 'operator',
        'name': '运营人员',
        'description': '日常运营与基础数据维护',
        'builtin': True,
        'sort_order': 5,
        'permissions': [
            'dashboard:view',
            'order:view', 'order:edit',
            'dealer_order:view',
            'user:view', 'user:create', 'user:edit',
            'product:view', 'product:create', 'product:edit',
            'binding:view', 'binding:create', 'binding:edit',
            'fault:view', 'fault:create', 'fault:edit',
            'statistics:view',
        ],
    },
    {
        'code': 'customer',
        'name': '客户',
        'description': '终端客户，自助报修与查询',
        'builtin': True,
        'sort_order': 6,
        'permissions': [
            'order:view',
        ],
    },
]


def init_rbac():
    """幂等初始化：建表 + 预置权限/角色/关联 + 给现有 admin 用户授权"""
    # 1. create_all 仅新建不存在的表，不修改既有表
    try:
        db.create_all()
    except Exception as e:
        print(f'[init_rbac] create_all failed: {e}')
        return

    # 2. seed permissions（幂等：基于 code）
    existing_codes = {permission.code for permission in Permission.query.all()}
    added_permissions = 0
    for code, name, module, action, desc, sort in PRESET_PERMISSIONS:
        if code in existing_codes:
            continue
        db.session.add(Permission(
            code=code,
            name=name,
            module=module,
            action=action,
            description=desc,
            sort_order=sort,
        ))
        added_permissions += 1
    if added_permissions:
        db.session.commit()
        print(f'[init_rbac] backfilled {added_permissions} permissions')

    if Role.query.count() == 0:
        perm_index = {permission.code: permission for permission in Permission.query.all()}
        for item in PRESET_ROLES:
            role = Role(
                code=item['code'],
                name=item['name'],
                description=item['description'],
                builtin=item['builtin'],
                sort_order=item['sort_order'],
                status='active',
            )
            db.session.add(role)
            db.session.flush()
            permission_codes = item['permissions']
            if permission_codes == '__all__':
                permission_codes = list(perm_index.keys())
            for code in permission_codes:
                if code in perm_index:
                    db.session.add(RolePermission(
                        role_id=role.id,
                        permission_id=perm_index[code].id,
                    ))
        db.session.commit()
        print(f'[init_rbac] seeded {len(PRESET_ROLES)} roles')

    admin_role = Role.query.filter_by(code='admin').first()
    if admin_role:
        existing_permission_ids = {
            item.permission_id for item in admin_role.role_permissions.all()
        }
        added_admin_links = 0
        for permission in Permission.query.all():
            if permission.id in existing_permission_ids:
                continue
            db.session.add(RolePermission(
                role_id=admin_role.id,
                permission_id=permission.id,
            ))
            added_admin_links += 1
        if added_admin_links:
            db.session.commit()
            print(f'[init_rbac] admin role got {added_admin_links} missing permissions')

    # P2: 对全部 builtin 角色做权限回填
    # —— init_rbac 上一步只在 Role 表为空时跑，对存量角色没作用；
    #    这里补一个 idempotent 的 backfill：遍历 PRESET_ROLES，对每个 builtin 角色
    #    比对 PRESET 期望 vs DB 现状，把缺的 RolePermission 补上。
    perm_index = {permission.code: permission for permission in Permission.query.all()}
    for item in PRESET_ROLES:
        if not item.get('builtin'):
            continue
        role = Role.query.filter_by(code=item['code']).first()
        if not role:
            continue
        desired_codes = item['permissions']
        if desired_codes == '__all__':
            desired_codes = list(perm_index.keys())
        existing_permission_ids = {
            rp.permission_id for rp in role.role_permissions.all()
        }
        added = 0
        for code in desired_codes:
            perm = perm_index.get(code)
            if not perm or perm.id in existing_permission_ids:
                continue
            db.session.add(RolePermission(
                role_id=role.id,
                permission_id=perm.id,
            ))
            added += 1
        if added:
            db.session.commit()
            print(f'[init_rbac] {item["code"]} role backfilled {added} missing permissions')

    admin_user = User.query.filter_by(openid='admin').first()
    if admin_user and admin_role and not UserRole.query.filter_by(user_id=admin_user.id, role_id=admin_role.id).first():
        db.session.add(UserRole(user_id=admin_user.id, role_id=admin_role.id))
        db.session.commit()
        print(f'[init_rbac] granted admin role to user {admin_user.openid}')

    # 5. 【补救】按 users.role 自动绑定同名 RBAC 角色（针对迁移期间 / 早期注册的非 admin 账号）
    #    比如 1003 是 service_point 角色，会自动绑上 service_point_admin 这个 RBAC 角色，
    #    JWT 里就能拿到对应的 8 个权限。
    #    已绑过的不会重复（unique 约束 + skip）。
    legacy_role_to_rbac_code = {
        'admin':         'admin',                # 内置 admin → 全权限 admin
        'dispatcher':    'dispatcher',
        'service_point': 'service_point_admin',  # 老的 users.role='service_point' → 新的 service_point_admin
        'engineer':      'engineer',
        'operator':      'operator',
        'customer':      'customer',
    }
    granted_count = 0
    for user in User.query.filter(User.status == 'active').all():
        rbac_code = legacy_role_to_rbac_code.get(user.role)
        if not rbac_code:
            continue
        rbac_role = Role.query.filter_by(code=rbac_code).first()
        if not rbac_role:
            continue
        if UserRole.query.filter_by(user_id=user.id, role_id=rbac_role.id).first():
            continue
        db.session.add(UserRole(user_id=user.id, role_id=rbac_role.id))
        granted_count += 1
    if granted_count:
        db.session.commit()
        print(f'[init_rbac] auto-granted RBAC roles to {granted_count} users by users.role')

    # 6. P0+P1: 故障库重构迁移（已有 DB 走 Python 迁移；新装 DB 由 init.sql 直接建表）
    _migrate_fault_library()


def _migrate_fault_library():
    """P0+P1 重构数据迁移：把 common_faults.files JSON 拆行到 common_fault_attachments。
       幂等：通过 schema_meta.key='attachments_migrated' 标记。
       新装 DB 由 init.sql 直接建表，无需此迁移。"""
    from sqlalchemy import text

    # schema_meta 表必须存在（init.sql 里建，但保险起见这里也建一次）
    try:
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS schema_meta (
                `key` VARCHAR(64) PRIMARY KEY,
                `value` VARCHAR(255),
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        db.session.commit()
    except Exception as e:
        print(f'[fault_migrate] create schema_meta failed: {e}')
        db.session.rollback()
        return

    # 注意：schema_meta 仅用于「数据迁移」幂等标记；DDL（审计列、FULLTEXT）必须每次启动都检查
    # （早期版本在这里早退，导致 ALTER 失败后下次重启仍跳过，列永远加不上）

    # 2. 审计列 + FULLTEXT 兜底（init.sql 也加了，这里再保险一次）
    #    MySQL < 8.0.29 不支持 ADD COLUMN IF NOT EXISTS，用 information_schema 检查后单独 ALTER
    def _col_exists(table, col):
        return db.session.execute(text(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND COLUMN_NAME = :c"
        ), {'t': table, 'c': col}).scalar() > 0

    for col in ('created_by', 'updated_by'):
        if not _col_exists('common_faults', col):
            try:
                db.session.execute(text(f"ALTER TABLE common_faults ADD COLUMN {col} INT"))
                db.session.commit()
                print(f'[fault_migrate] added column common_faults.{col}')
            except Exception as e:
                print(f'[fault_migrate] add column {col} failed: {e}')
                db.session.rollback()

    has_ft = db.session.execute(text("""
        SELECT COUNT(*) FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'common_faults'
          AND INDEX_NAME = 'ft_title_content'
    """)).scalar()
    if not has_ft:
        try:
            db.session.execute(text(
                "ALTER TABLE common_faults ADD FULLTEXT INDEX ft_title_content (title, content)"
            ))
            db.session.commit()
        except Exception as e:
            print(f'[fault_migrate] ADD FULLTEXT failed: {e}')
            db.session.rollback()

    # 3. 数据迁移：files JSON → attachments 行（仅在未迁移过时执行）
    #    使用 JSON_TABLE（MySQL 8.0.4+）；kind 不在 ENUM 时降级为 'file'
    already = db.session.execute(text(
        "SELECT `value` FROM schema_meta WHERE `key` = 'attachments_migrated'"
    )).scalar()
    if already == '1':
        print('[fault_migrate] data migration already done, skip')
    else:
        try:
            result = db.session.execute(text("""
                INSERT INTO common_fault_attachments
                    (fault_id, filename, url, size, mime, kind, uploaded_at, sort_order)
                SELECT
                    cf.id,
                    jt.filename,
                    jt.url,
                    COALESCE(jt.fsize, 0),
                    jt.content_type,
                    CASE
                        WHEN LOWER(jt.kind) IN ('pdf','doc','docx','image') THEN LOWER(jt.kind)
                        ELSE 'file'
                    END,
                    cf.created_at,
                    0
                FROM common_faults cf
                JOIN JSON_TABLE(
                    cf.files,
                    '$[*]' COLUMNS (
                        filename VARCHAR(255) PATH '$.filename',
                        url VARCHAR(512) PATH '$.url',
                        fsize INT PATH '$.size',
                        content_type VARCHAR(128) PATH '$.content_type',
                        kind VARCHAR(32) PATH '$.kind'
                    )
                ) AS jt
                WHERE cf.files IS NOT NULL
                  AND JSON_TYPE(cf.files) = 'ARRAY'
                  AND JSON_LENGTH(cf.files) > 0
            """))
            inserted = result.rowcount
            db.session.commit()
            print(f'[fault_migrate] inserted {inserted} attachment rows from legacy files JSON')
        except Exception as e:
            # JSON_TABLE 在 MySQL < 8.0.4 不支持；此时 attachments 表为空，前端走新流程会重新上传
            print(f'[fault_migrate] data migration failed (legacy files dropped, new uploads will populate): {e}')
            db.session.rollback()

    # 4. 标记完成（独立于 DDL 失败 — 只标记 data migration）
    try:
        db.session.execute(text(
            "INSERT INTO schema_meta (`key`, `value`) VALUES ('attachments_migrated', '1') "
            "ON DUPLICATE KEY UPDATE `value` = '1'"
        ))
        db.session.commit()
    except Exception as e:
        print(f'[fault_migrate] mark migration done failed: {e}')
        db.session.rollback()
