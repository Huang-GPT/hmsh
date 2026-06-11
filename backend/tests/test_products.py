import pytest
from app import create_app, db
from app.models.user import User
from app.models.product import Product, UserProduct
from app.services.product_service import ProductService
from config import TestConfig

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def test_user(app):
    with app.app_context():
        user = User(openid='test_openid', nickname='测试用户', role='customer')
        db.session.add(user)
        db.session.commit()
        return user.id

def test_bind_product_manually(app, test_user):
    with app.app_context():
        product = ProductService.bind_product_manually(
            user_id=test_user,
            serial_number='SN12345678',
            model='HM-001',
            bind_method='manual'
        )
        assert product is not None
        assert product.serial_number == 'SN12345678'
        
        user_product = UserProduct.query.filter_by(user_id=test_user).first()
        assert user_product is not None
        assert user_product.bind_method == 'manual'