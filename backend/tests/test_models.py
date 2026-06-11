import pytest
from app import create_app, db
from app.models.user import User
from config import TestConfig

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

def test_create_user(app):
    user = User(
        openid='test_openid',
        nickname='测试用户',
        avatar='https://example.com/avatar.jpg',
        phone='13800138000',
        role='customer'
    )
    db.session.add(user)
    db.session.commit()
    
    assert user.id is not None
    assert user.openid == 'test_openid'
    assert user.role == 'customer'