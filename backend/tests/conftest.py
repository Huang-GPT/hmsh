import itertools
from datetime import datetime

import pytest

from app import create_app, db
from app.models.product import Product
from app.models.rbac import Permission, Role, RolePermission, UserRole
from app.models.service_point import ServicePoint
from app.models.user import User
from app.models.work_order import OrderStatusLog, WorkOrder
from app.services.auth_service import generate_token
from config import TestConfig


@pytest.fixture
def app():
    application = create_app(TestConfig)
    context = application.app_context()
    context.push()
    db.drop_all()
    db.create_all()
    from app.init_rbac import init_rbac
    init_rbac()
    yield application
    db.session.remove()
    db.drop_all()
    context.pop()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def counter():
    return itertools.count(1)


@pytest.fixture
def make_auth_identity(counter):
    def factory(permission_codes, nickname='测试操作员'):
        number = next(counter)
        user = User(
            openid=f'test-operator-{number}',
            phone=f'139{number:08d}',
            nickname=nickname,
            password_hash='test-only',
            role='admin',
            status='active',
        )
        role = Role(
            code=f'test-role-{number}',
            name=f'测试角色{number}',
            builtin=False,
            status='active',
            sort_order=999,
        )
        db.session.add_all([user, role])
        db.session.flush()
        for code in permission_codes:
            permission = Permission.query.filter_by(code=code).one()
            db.session.add(RolePermission(role_id=role.id, permission_id=permission.id))
        db.session.add(UserRole(user_id=user.id, role_id=role.id))
        db.session.commit()
        token = generate_token(user)
        return user, {'Authorization': f'Bearer {token}'}
    return factory


@pytest.fixture
def reopen_actor(make_auth_identity):
    return make_auth_identity(
        ['order:view', 'order:reject', 'order:reopen'],
        nickname='恢复操作员',
    )


@pytest.fixture
def auth_headers(reopen_actor):
    return reopen_actor[1]


@pytest.fixture
def no_reopen_headers(make_auth_identity):
    return make_auth_identity(['order:view'], nickname='只读操作员')[1]


@pytest.fixture
def make_order(counter):
    number = next(counter)
    customer = User(
        openid=f'test-customer-{number}',
        phone=f'138{number:08d}',
        nickname=f'测试客户{number}',
        role='customer',
        status='active',
    )
    product = Product(
        qr_code=f'TEST-QR-{number}',
        serial_number=f'TEST-SN-{number}',
        model='测试型号',
        product_name='测试产品',
        status='active',
    )
    db.session.add_all([customer, product])
    db.session.flush()

    def factory(status='closed', **values):
        order_number = next(counter)
        order = WorkOrder(
            order_no=f'RMTEST{order_number:06d}',
            user_id=customer.id,
            product_id=product.id,
            fault_type='测试故障',
            fault_desc='测试故障描述',
            contact_name='测试联系人',
            contact_phone='13700000000',
            status=status,
            **values,
        )
        db.session.add(order)
        db.session.commit()
        return order
    return factory


@pytest.fixture
def make_service_point(counter):
    def factory():
        number = next(counter)
        point = ServicePoint(name=f'测试服务点{number}', status='active')
        db.session.add(point)
        db.session.commit()
        return point
    return factory


@pytest.fixture
def add_log():
    def factory(order, from_status, to_status, created_at=None, remark=''):
        log = OrderStatusLog(
            order_id=order.id,
            from_status=from_status,
            to_status=to_status,
            operator_id=1,
            operator_name='历史操作员',
            remark=remark,
            created_at=created_at or datetime.utcnow(),
        )
        db.session.add(log)
        db.session.commit()
        return log
    return factory
