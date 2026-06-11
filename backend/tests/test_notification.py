import pytest
from unittest.mock import patch, Mock
from app import create_app
from app.services.notification_service import NotificationService
from config import TestConfig

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        yield app

def test_send_template_message(app):
    with app.app_context():
        with patch('app.services.notification_service.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {'errcode': 0, 'errmsg': 'ok'}
            mock_post.return_value = mock_response
            
            result = NotificationService.send_template_message(
                openid='test_openid',
                template_id='test_template_id',
                data={
                    'first': {'value': '工单状态更新'},
                    'keyword1': {'value': 'WO20240115123456'},
                    'keyword2': {'value': '处理中'},
                    'remark': {'value': '您的工单正在处理中'}
                }
            )
            assert result['errcode'] == 0