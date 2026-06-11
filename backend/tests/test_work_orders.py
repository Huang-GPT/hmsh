import pytest
from datetime import datetime
from app import create_app, db
from app.models.user import User
from app.models.product import Product, UserProduct
from app.services.work_order_service import WorkOrderService
from config import TestConfig

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def test_data(app):
    with app.app_context():
        user = User(openid='test_openid', nickname='测试用户', role='customer')
        db.session.add(user)
        db.session.commit()
        
        product = Product(serial_number='SN12345678', model='HM-001')
        db.session.add(product)
        db.session.commit()
        
        user_product = UserProduct(user_id=user.id, product_id=product.id, bind_method='manual')
        db.session.add(user_product)
        db.session.commit()
        
        return {'user_id': user.id, 'product_id': product.id}

def test_create_work_order(app, test_data):
    with app.app_context():
        order = WorkOrderService.create_work_order(
            user_id=test_data['user_id'],
            product_id=test_data['product_id'],
            fault_type='无法启动',
            fault_desc='设备无法正常启动',
            contact_name='张三',
            contact_phone='13800138000'
        )
        assert order is not None
        assert order.status == 'pending_assign'
        assert order.order_no.startswith('WO')