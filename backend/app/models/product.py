from datetime import datetime
from app import db

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    serial_number = db.Column(db.String(64), unique=True, nullable=False, index=True)
    model = db.Column(db.String(64), nullable=False)
    product_family = db.Column(db.String(64), index=True)
    production_date = db.Column(db.Date)
    sap_order_no = db.Column(db.String(32))
    sap_line_item = db.Column(db.String(16))
    status = db.Column(db.Enum('active','inactive'), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'serial_number': self.serial_number,
            'model': self.model,
            'product_family': self.product_family,
            'production_date': self.production_date.isoformat() if self.production_date else None,
            'sap_order_no': self.sap_order_no,
            'sap_line_item': self.sap_line_item,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class UserProduct(db.Model):
    __tablename__ = 'user_products'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    bind_time = db.Column(db.DateTime, default=datetime.utcnow)
    bind_method = db.Column(db.Enum('manual','qrcode_product','qrcode_sap'), nullable=False)

    product = db.relationship('Product', backref='user_bindings')
    user = db.relationship('User', backref='bound_products')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'product_id', name='uq_user_product'),
    )

    def to_dict(self):
        p = self.product.to_dict() if self.product else {}
        p['bind_time'] = self.bind_time.isoformat() if self.bind_time else None
        p['bind_method'] = self.bind_method
        return p
