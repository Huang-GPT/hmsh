import pytest
from unittest.mock import patch, Mock
from app import create_app
from app.services.erp_service import ErpService
from config import TestConfig

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        yield app

def test_verify_product(app):
    with app.app_context():
        with patch('app.services.erp_service.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                'success': True,
                'product': {
                    'serial_number': 'SN12345678',
                    'model': 'HM-001',
                    'production_date': '2024-01-15'
                }
            }
            mock_get.return_value = mock_response
            
            result = ErpService.verify_product('SN12345678')
            assert result['success'] == True
            assert result['product']['serial_number'] == 'SN12345678'