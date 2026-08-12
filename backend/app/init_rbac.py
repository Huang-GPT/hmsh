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
            'order:view',
            'service_point:view',
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
    if Permission.query.count() == 0:
        for code, name, module, action, desc, sort in PRESET_PERMISSIONS:
            db.session.add(Permission(
                code=code, name=name, module=module, action=action,
                description=desc, sort_order=sort,
            ))
        db.session.commit()
        print(f'[init_rbac] seeded {len(PRESET_PERMISSIONS)} permissions')

    # 3. seed roles + role_permissions
    if Role.query.count() == 0:
        perm_index = {p.code: p for p in Permission.query.all()}
        for r in PRESET_ROLES:
            role = Role(
                code=r['code'],
                name=r['name'],
                description=r['description'],
                builtin=r['builtin'],
                sort_order=r['sort_order'],
                status='active',
            )
            db.session.add(role)
            db.session.flush()  # 获取 role.id
            perms = r['permissions']
            if perms == '__all__':
                perms = list(perm_index.keys())
            for code in perms:
                if code in perm_index:
                    db.session.add(RolePermission(
                        role_id=role.id,
                        permission_id=perm_index[code].id,
                    ))
        db.session.commit()
        print(f'[init_rbac] seeded {len(PRESET_ROLES)} roles')

    # 4. 给现有 admin 用户授权 admin 角色（如果还没有）
    admin_role = Role.query.filter_by(code='admin').first()
    if admin_role:
        admin_user = User.query.filter_by(openid='admin').first()
        if admin_user and not UserRole.query.filter_by(user_id=admin_user.id, role_id=admin_role.id).first():
            db.session.add(UserRole(user_id=admin_user.id, role_id=admin_role.id))
            db.session.commit()
            print(f'[init_rbac] granted admin role to user {admin_user.openid}')
