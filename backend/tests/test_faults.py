import pytest
from app import create_app, db
from app.models.common_fault import CommonFault
from app.services.fault_service import FaultService
from config import TestConfig

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

def test_create_fault(app):
    with app.app_context():
        fault = FaultService.create_fault(
            product_model='HM-001',
            fault_type='无法启动',
            fault_desc='设备按下电源键无反应',
            solution='检查电源连接，确认电池有电'
        )
        assert fault is not None
        assert fault.product_model == 'HM-001'
        assert fault.view_count == 0

def test_search_faults(app):
    with app.app_context():
        FaultService.create_fault(
            product_model='HM-001',
            fault_type='无法启动',
            fault_desc='设备按下电源键无反应',
            solution='检查电源连接'
        )
        FaultService.create_fault(
            product_model='HM-001',
            fault_type='运行异常',
            fault_desc='设备运行时有异响',
            solution='检查是否有异物卡住'
        )
        
        results = FaultService.search_faults('HM-001', '启动')
        assert len(results) == 1
        assert results[0].fault_type == '无法启动'