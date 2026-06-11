import pytest
from app import create_app, db
from app.models.user import User
from app.services.admin_service import AdminService
from config import TestConfig

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

def test_create_service_user(app):
    with app.app_context():
        user = AdminService.create_user(
            openid='service_openid',
            nickname='客服小王',
            role='service',
            phone='13800138000'
        )
        assert user is not None
        assert user.role == 'service'

def test_get_statistics(app):
    with app.app_context():
        stats = AdminService.get_statistics()
        assert 'total_orders' in stats
        assert 'pending_orders' in stats
        assert 'completed_orders' in stats