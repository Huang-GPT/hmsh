from datetime import datetime
from app import db

class WorkOrder(db.Model):
    __tablename__ = 'work_orders'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_no = db.Column(db.String(32), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    fault_category_id = db.Column(db.Integer, db.ForeignKey('fault_categories.id'))
    fault_type = db.Column(db.String(64), nullable=False)
    fault_desc = db.Column(db.Text, nullable=False)
    images = db.Column(db.JSON)
    videos = db.Column(db.JSON)
    fault_address = db.Column(db.String(255))
    fault_location_lat = db.Column(db.Numeric(10,7))
    fault_location_lng = db.Column(db.Numeric(10,7))
    appointment_date = db.Column(db.Date)
    appointment_period = db.Column(db.Enum('AM','PM'))
    contact_name = db.Column(db.String(32), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    status = db.Column(db.Enum(
        'pending_accept','pending_dispatch','dispatched',
        'assigned_engineer','processing','pending_confirm',
        'completed','closed','cancelled'
    ), default='pending_accept', nullable=False, index=True)
    service_point_id = db.Column(db.Integer, db.ForeignKey('service_points.id'))
    engineer_id = db.Column(db.Integer, db.ForeignKey('engineers.id'))
    reject_reason = db.Column(db.String(255))
    cancel_reason = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id], backref='work_orders')
    product = db.relationship('Product', backref='work_orders')
    service_point = db.relationship('ServicePoint', backref='work_orders')
    engineer = db.relationship('Engineer', backref='work_orders')
    fault_category = db.relationship('FaultCategory')
    status_logs = db.relationship('OrderStatusLog', backref='work_order', lazy='dynamic', order_by='OrderStatusLog.created_at.desc()')

    STATUS_FLOW = {
        'pending_accept':  ['pending_dispatch', 'cancelled'],
        'pending_dispatch':['dispatched', 'closed'],
        'dispatched':      ['assigned_engineer', 'closed'],
        'assigned_engineer':['processing'],
        'processing':      ['pending_confirm', 'closed'],
        'pending_confirm': ['completed', 'processing'],
        'completed':       ['closed'],
        'closed':          [],
        'cancelled':       [],
    }

    STATUS_CN = {
        'pending_accept': '待受理',
        'pending_dispatch': '待派单',
        'dispatched': '已派单',
        'assigned_engineer': '已分配工程师',
        'processing': '处理中',
        'pending_confirm': '待确认',
        'completed': '已完成',
        'closed': '已关闭',
        'cancelled': '已撤销',
    }

    def to_dict(self):
        return {
            'id': self.id,
            'order_no': self.order_no,
            'user_id': self.user_id,
            'user_name': self.user.nickname if self.user else None,
            'user_phone': self.user.phone if self.user else None,
            'product_id': self.product_id,
            'product_model': self.product.model if self.product else None,
            'product_name': (self.product.product_name or self.product.model) if self.product else None,
            'product_serial': self.product.serial_number if self.product else None,
            'product_family': self.product.product_family if self.product else None,
            'product_qr_code': self.product.qr_code if self.product else None,
            'product_sales_no': self.product.sales_no if self.product else None,
            'product_customer_name': self.product.customer_name if self.product else None,
            'fault_category_id': self.fault_category_id,
            'fault_category_name': self.fault_category.name if self.fault_category else None,
            'fault_type': self.fault_type,
            'fault_desc': self.fault_desc,
            'images': self.images or [],
            'fault_address': self.fault_address,
            'appointment_date': self.appointment_date.isoformat() if self.appointment_date else None,
            'appointment_period': self.appointment_period,
            'contact_name': self.contact_name,
            'contact_phone': self.contact_phone,
            'status': self.status,
            'status_cn': self.STATUS_CN.get(self.status, self.status),
            'service_point_id': self.service_point_id,
            'service_point_name': self.service_point.name if self.service_point else None,
            'engineer_id': self.engineer_id,
            'engineer_name': self.engineer.name if self.engineer else None,
            'engineer_phone': self.engineer.phone if self.engineer else None,
            'reject_reason': self.reject_reason,
            'cancel_reason': self.cancel_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class OrderStatusLog(db.Model):
    __tablename__ = 'order_status_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('work_orders.id'), nullable=False)
    from_status = db.Column(db.String(32))
    to_status = db.Column(db.String(32), nullable=False)
    operator_id = db.Column(db.Integer)
    operator_name = db.Column(db.String(50))
    remark = db.Column(db.Text)
    images = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'from_status': self.from_status,
            'to_status': self.to_status,
            'to_status_cn': WorkOrder.STATUS_CN.get(self.to_status, self.to_status),
            'operator_id': self.operator_id,
            'operator_name': self.operator_name,
            'remark': self.remark,
            'images': self.images,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
