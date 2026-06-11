from datetime import datetime
from app import db

class WorkOrder(db.Model):
    __tablename__ = 'work_orders'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_no = db.Column(db.String(32), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    fault_type = db.Column(db.String(32), nullable=False)
    fault_desc = db.Column(db.Text, nullable=False)
    images = db.Column(db.JSON)
    contact_name = db.Column(db.String(32), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    expected_time = db.Column(db.DateTime)
    status = db.Column(db.Enum('pending_assign', 'pending_process', 'processing', 
                               'pending_confirm', 'completed', 'closed'), 
                       default='pending_assign', nullable=False)
    handler_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    product = db.relationship('Product', backref='work_orders')
    handler = db.relationship('User', foreign_keys=[handler_id])
    status_logs = db.relationship('OrderStatusLog', backref='work_order', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_no': self.order_no,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'fault_type': self.fault_type,
            'fault_desc': self.fault_desc,
            'images': self.images,
            'contact_name': self.contact_name,
            'contact_phone': self.contact_phone,
            'expected_time': self.expected_time.isoformat() if self.expected_time else None,
            'status': self.status,
            'handler_id': self.handler_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class OrderStatusLog(db.Model):
    __tablename__ = 'order_status_logs'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('work_orders.id'), nullable=False)
    from_status = db.Column(db.String(32))
    to_status = db.Column(db.String(32), nullable=False)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    remark = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    operator = db.relationship('User', foreign_keys=[operator_id])