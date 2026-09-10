from app import db
from app.init_rbac import init_rbac
from app.models.rbac import Permission, Role, RolePermission


def test_reopen_permission_is_seeded_and_assigned_to_admin(app):
    permission = Permission.query.filter_by(code='order:reopen').one_or_none()
    assert permission is not None
    assert permission.module == 'order'
    assert permission.action == 'reopen'

    admin_role = Role.query.filter_by(code='admin').one()
    link = RolePermission.query.filter_by(
        role_id=admin_role.id,
        permission_id=permission.id,
    ).one_or_none()
    assert link is not None


def test_init_rbac_backfills_deleted_permission_and_admin_link(app):
    admin_role = Role.query.filter_by(code='admin').one()
    permission = Permission.query.filter_by(code='order:reopen').one()
    link = RolePermission.query.filter_by(
        role_id=admin_role.id,
        permission_id=permission.id,
    ).one()
    db.session.delete(link)
    db.session.flush()
    db.session.delete(permission)
    db.session.commit()

    init_rbac()

    restored = Permission.query.filter_by(code='order:reopen').one()
    restored_link = RolePermission.query.filter_by(
        role_id=admin_role.id,
        permission_id=restored.id,
    ).one_or_none()
    assert restored_link is not None


def test_init_rbac_is_idempotent_and_preserves_custom_roles(app):
    view_permission = Permission.query.filter_by(code='order:view').one()
    custom_role = Role(
        code='custom-auditor',
        name='自定义审计员',
        builtin=False,
        status='active',
    )
    db.session.add(custom_role)
    db.session.flush()
    custom_link = RolePermission(
        role_id=custom_role.id,
        permission_id=view_permission.id,
    )
    db.session.add(custom_link)
    db.session.commit()

    before_permissions = Permission.query.count()
    before_roles = Role.query.count()
    before_links = RolePermission.query.count()

    init_rbac()
    init_rbac()

    assert Permission.query.count() == before_permissions
    assert Role.query.count() == before_roles
    assert RolePermission.query.count() == before_links
    assert RolePermission.query.filter_by(
        role_id=custom_role.id,
        permission_id=view_permission.id,
    ).one_or_none() is not None