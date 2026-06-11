import pytest
from app import create_app, db
from app.services.wechat_service import WechatService
from config import TestConfig

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

def test_get_oauth_url(app):
    with app.app_context():
        url = WechatService.get_oauth_url('http://example.com/callback')
        assert 'open.weixin.qq.com' in url
        assert 'appid=' in url
        assert 'redirect_uri=' in url