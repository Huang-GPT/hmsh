from datetime import datetime
from app import db


class Permission(db.Model):
    """权限资源 — resource:action 形式，按 module 分组"""
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(64), unique=True, nullable=False, index=True, comment='权限编码，如 order:view')
    name = db.Column(db.String(64), nullable=False, comment='权限名称')
    module = db.Column(db.String(32), nullable=False, index=True, comment='所属模块')
    action = db.Column(db.String(32), nullable=False, comment='操作类型')
    description = db.Column(db.String(255))
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'module': self.module,
            'action': self.action,
            'description': self.description,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Role(db.Model):
    """角色"""
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(32), unique=True, nullable=False, index=True, comment='角色编码')
    name = db.Column(db.String(64), nullable=False, comment='角色名称')
    description = db.Column(db.String(255))
    builtin = db.Column(db.Boolean, default=False, comment='内置角色（不可删除）')
    status = db.Column(db.Enum('active', 'disabled'), default='active', nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 多对多：角色-权限
    role_permissions = db.relationship('RolePermission', backref='role', lazy='dynamic', cascade='all, delete-orphan')
    # 多对多：用户-角色
    user_roles = db.relationship('UserRole', backref='role', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, include_permissions=True):
        d = {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'builtin': self.builtin,
            'status': self.status,
            'sort_order': self.sort_order,
            'permission_ids': [rp.permission_id for rp in self.role_permissions.all()],
            'permission_count': self.role_permissions.count(),
            'user_count': self.user_roles.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_permissions:
            d['permissions'] = [rp.permission.to_dict() for rp in self.role_permissions.all()]
        return d


class RolePermission(db.Model):
    """角色-权限 多对多关联"""
    __tablename__ = 'role_permissions_v2'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False, index=True)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('role_id', 'permission_id', name='uk_role_permission'),
    )

    permission = db.relationship('Permission')


class UserRole(db.Model):
    """用户-角色 多对多关联"""
    __tablename__ = 'user_roles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'role_id', name='uk_user_role'),
    )
