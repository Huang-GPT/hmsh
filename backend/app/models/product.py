from datetime import datetime
from app import db


class Product(db.Model):
    """产品库（出厂出货记录）

    一条记录 = 一个产品实例，绑定二维码和销售单。
    同一销售单/产品型号可以有多行（每个产品实例独立二维码）。
    二维码（qr_code）是唯一标识。
    """
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # === 原有字段（保留兼容老数据） ===
    serial_number = db.Column(db.String(64), unique=True, index=True, nullable=True)
    model = db.Column(db.String(64), index=True)
    product_family = db.Column(db.String(64), index=True)
    production_date = db.Column(db.Date)
    sap_order_no = db.Column(db.String(32))
    sap_line_item = db.Column(db.String(16))
    status = db.Column(db.Enum('active', 'inactive'), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # === CSV 导入字段（销售订单 17~19） ===
    sales_no = db.Column(db.String(32), index=True, comment='销售单号')
    customer_name = db.Column(db.String(128), index=True, comment='客户名称')
    dealer_name = db.Column(db.String(128), index=True, comment='经销商名称')
    dealer_contact = db.Column(db.String(64), comment='经销商联系人')
    dealer_phone = db.Column(db.String(32), comment='经销商电话')
    product_no = db.Column(db.String(64), index=True, comment='产品编号（型号代码）')
    product_name = db.Column(db.String(256), index=True, comment='产品名称')
    shipping_address = db.Column(db.String(512), comment='发货地址')
    qr_code = db.Column(db.String(64), unique=True, index=True, comment='二维码（一码一物）')
    receiver = db.Column(db.String(64), comment='收货人')
    receiver_phone = db.Column(db.String(32), comment='联系电话')
    order_date = db.Column(db.DateTime, comment='下单日期')
    delivery_date = db.Column(db.DateTime, comment='交货日期')

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
            # CSV 字段
            'sales_no': self.sales_no,
            'customer_name': self.customer_name,
            'dealer_name': self.dealer_name,
            'dealer_contact': self.dealer_contact,
            'dealer_phone': self.dealer_phone,
            'product_no': self.product_no,
            'product_name': self.product_name,
            'shipping_address': self.shipping_address,
            'qr_code': self.qr_code,
            'receiver': self.receiver,
            'receiver_phone': self.receiver_phone,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'delivery_date': self.delivery_date.isoformat() if self.delivery_date else None,
        }


class UserProduct(db.Model):
    __tablename__ = 'user_products'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    bind_time = db.Column(db.DateTime, default=datetime.utcnow)
    bind_method = db.Column(db.Enum('manual', 'qrcode_product', 'qrcode_sap'), nullable=False)

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
