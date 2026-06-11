from datetime import datetime
from app import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    openid = db.Column(db.String(64), unique=True, nullable=False, index=True)
    nickname = db.Column(db.String(64))
    avatar = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    role = db.Column(db.Enum('customer', 'service', 'admin'), default='customer', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    products = db.relationship('UserProduct', backref='user', lazy='dynamic')
    work_orders = db.relationship('WorkOrder', foreign_keys='WorkOrder.user_id', backref='user', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'openid': self.openid,
            'nickname': self.nickname,
            'avatar': self.avatar,
            'phone': self.phone,
            'role': self.role,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }