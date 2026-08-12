from datetime import datetime
from app import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    openid = db.Column(db.String(64), unique=True, index=True)
    phone = db.Column(db.String(20), unique=True, index=True)
    nickname = db.Column(db.String(64))
    avatar = db.Column(db.String(255))
    password_hash = db.Column(db.String(128))
    role = db.Column(db.Enum('customer','dispatcher','service_point','engineer','operator','admin'), default='customer', nullable=False)
    status = db.Column(db.Enum('active','disabled'), default='active', nullable=False)
    service_point_id = db.Column(db.Integer, db.ForeignKey('service_points.id'))
    permissions = db.Column(db.JSON, comment='菜单权限列表')
    # === RBAC 扩展字段 ===
    email = db.Column(db.String(128))
    real_name = db.Column(db.String(64), comment='真实姓名')
    department = db.Column(db.String(64), comment='部门')
    remark = db.Column(db.String(255), comment='备注')
    last_login_at = db.Column(db.DateTime, comment='最近登录时间')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    service_point = db.relationship('ServicePoint', backref='users', foreign_keys=[service_point_id])
    # 多对多：用户-角色
    user_roles = db.relationship('UserRole', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'openid': self.openid,
            'account': self.openid,  # 别名
            'phone': self.phone,
            'nickname': self.nickname,
            'real_name': self.real_name,
            'email': self.email,
            'department': self.department,
            'remark': self.remark,
            'avatar': self.avatar,
            'role': self.role,
            'status': self.status,
            'service_point_id': self.service_point_id,
            'service_point_name': self.service_point.name if self.service_point else None,
            'permissions': self.permissions,
            'roles': [ur.role.to_dict() for ur in self.user_roles.all()],
            'role_ids': [ur.role_id for ur in self.user_roles.all()],
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
