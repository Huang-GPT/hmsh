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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    service_point = db.relationship('ServicePoint', backref='users', foreign_keys=[service_point_id])

    def to_dict(self):
        return {
            'id': self.id,
            'openid': self.openid,
            'phone': self.phone,
            'nickname': self.nickname,
            'avatar': self.avatar,
            'role': self.role,
            'status': self.status,
            'service_point_id': self.service_point_id,
            'service_point_name': self.service_point.name if self.service_point else None,
            'permissions': self.permissions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }