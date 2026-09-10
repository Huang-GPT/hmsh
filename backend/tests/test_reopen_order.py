from datetime import datetime, timedelta

from app.models.work_order import OrderStatusLog


def option_values(state):
    return [item['value'] for item in state['options']]


def test_no_history_only_allows_pending_accept(app, make_order):
    from app.api.admin import _build_reopen_state

    order = make_order(status='closed')
    state = _build_reopen_state(order)

    assert state['recommended_status'] == 'pending_accept'
    assert option_values(state) == ['pending_accept']


def test_dispatched_requires_history_and_service_point(
    app,
    make_order,
    make_service_point,
    add_log,
):
    from app.api.admin import _build_reopen_state

    order = make_order(status='closed')
    add_log(order, 'pending_accept', 'pending_dispatch')
    add_log(order, 'pending_dispatch', 'dispatched')
    add_log(order, 'dispatched', 'closed')

    assert 'dispatched' not in option_values(_build_reopen_state(order))

    point = make_service_point()
    order.service_point_id = point.id
    from app import db
    db.session.commit()

    assert 'dispatched' in option_values(_build_reopen_state(order))


def test_engineer_states_require_valid_assignment(app, make_order, add_log):
    from app import db
    from app.api.admin import _build_reopen_state

    order = make_order(status='closed')
    add_log(order, 'dispatched', 'assigned_engineer')
    add_log(order, 'assigned_engineer', 'processing')
    add_log(order, 'processing', 'closed')

    values = option_values(_build_reopen_state(order))
    assert 'assigned_engineer' not in values
    assert 'processing' not in values

    order.assigned_engineer_name = '张工'
    order.assigned_engineer_phone = '12A4567'
    db.session.commit()
    values = option_values(_build_reopen_state(order))
    assert 'assigned_engineer' not in values
    assert 'processing' not in values

    order.assigned_engineer_phone = '13800000001'
    db.session.commit()
    values = option_values(_build_reopen_state(order))
    assert 'assigned_engineer' in values
    assert 'processing' in values


def test_unreached_late_states_are_not_offered(app, make_order, add_log):
    from app.api.admin import _build_reopen_state

    order = make_order(status='closed')
    add_log(order, 'pending_accept', 'pending_dispatch')
    add_log(order, 'pending_dispatch', 'closed')

    values = option_values(_build_reopen_state(order))
    assert 'pending_confirm' not in values
    assert 'completed' not in values


def test_recommended_state_uses_latest_valid_close_source(app, make_order, add_log):
    from app.api.admin import _build_reopen_state

    started = datetime(2026, 8, 19, 9, 0, 0)
    order = make_order(status='closed')
    add_log(order, 'pending_accept', 'pending_dispatch', created_at=started)
    add_log(
        order,
        'pending_dispatch',
        'closed',
        created_at=started + timedelta(minutes=1),
    )

    state = _build_reopen_state(order)
    assert state['recommended_status'] == 'pending_dispatch'
    assert state['options'][0] == {
        'value': 'pending_dispatch',
        'label': '待派单',
        'recommended': True,
    }


def test_recommended_state_skips_bad_closed_to_closed_log(app, make_order, add_log):
    from app.api.admin import _build_reopen_state

    started = datetime(2026, 8, 19, 9, 0, 0)
    order = make_order(status='closed')
    add_log(order, 'pending_accept', 'pending_dispatch', created_at=started)
    add_log(
        order,
        'pending_dispatch',
        'closed',
        created_at=started + timedelta(minutes=1),
    )
    add_log(
        order,
        'closed',
        'closed',
        created_at=started + timedelta(minutes=2),
    )

    state = _build_reopen_state(order)
    assert state['recommended_status'] == 'pending_dispatch'


def test_reject_order_logs_real_previous_status(
    app,
    client,
    auth_headers,
    make_order,
):
    order = make_order(status='pending_dispatch')

    response = client.post(
        f'/api/admin/orders/{order.id}/reject',
        json={'reason': '拒绝测试'},
        headers=auth_headers,
    )

    assert response.status_code == 200
    log = OrderStatusLog.query.filter_by(
        order_id=order.id,
        to_status='closed',
    ).one()
    assert log.from_status == 'pending_dispatch'


def test_reopen_options_requires_login(client, make_order):
    order = make_order(status='closed')
    response = client.get(f'/api/admin/orders/{order.id}/reopen-options')
    assert response.status_code == 401


def test_reopen_options_requires_permission(
    client,
    no_reopen_headers,
    make_order,
):
    order = make_order(status='closed')
    response = client.get(
        f'/api/admin/orders/{order.id}/reopen-options',
        headers=no_reopen_headers,
    )
    assert response.status_code == 403


def test_reopen_options_returns_404(client, auth_headers):
    response = client.get(
        '/api/admin/orders/999999/reopen-options',
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_reopen_options_rejects_non_closed(
    client,
    auth_headers,
    make_order,
):
    order = make_order(status='pending_dispatch')
    response = client.get(
        f'/api/admin/orders/{order.id}/reopen-options',
        headers=auth_headers,
    )
    assert response.status_code == 409
    assert response.get_json()['code'] == 'ORDER_NOT_CLOSED'


def test_reopen_options_returns_recommended_state(
    client,
    auth_headers,
    make_order,
    add_log,
):
    order = make_order(status='closed')
    add_log(order, 'pending_accept', 'pending_dispatch')
    add_log(order, 'pending_dispatch', 'closed')

    response = client.get(
        f'/api/admin/orders/{order.id}/reopen-options',
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['order_id'] == order.id
    assert data['order_no'] == order.order_no
    assert data['current_status'] == 'closed'
    assert data['recommended_status'] == 'pending_dispatch'
    assert data['options'][0]['label'] == '待派单'


def test_reopen_rejects_invalid_payload(
    client,
    auth_headers,
    make_order,
    add_log,
):
    order = make_order(status='closed')
    add_log(order, 'pending_accept', 'pending_dispatch')
    add_log(order, 'pending_dispatch', 'closed')
    url = f'/api/admin/orders/{order.id}/reopen'

    cases = [
        {},
        {'target_status': 'pending_dispatch', 'reason': '   '},
        {'target_status': '', 'reason': '恢复'},
        {'target_status': 'pending_dispatch', 'reason': '原' * 501},
        {'target_status': 'completed', 'reason': '非法跳转'},
    ]
    for payload in cases:
        response = client.post(url, json=payload, headers=auth_headers)
        assert response.status_code == 400


def test_reopen_returns_404(client, auth_headers):
    response = client.post(
        '/api/admin/orders/999999/reopen',
        json={'target_status': 'pending_accept', 'reason': '恢复'},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_reopen_rejects_non_closed(
    client,
    auth_headers,
    make_order,
):
    order = make_order(status='processing')
    response = client.post(
        f'/api/admin/orders/{order.id}/reopen',
        json={'target_status': 'pending_accept', 'reason': '恢复'},
        headers=auth_headers,
    )
    assert response.status_code == 409
    assert response.get_json()['code'] == 'ORDER_NOT_CLOSED'


def test_reopen_updates_status_preserves_reason_and_writes_audit_log(
    client,
    auth_headers,
    reopen_actor,
    make_order,
    add_log,
):
    from app import db

    order = make_order(status='closed', reject_reason='原关闭原因')
    add_log(order, 'pending_accept', 'pending_dispatch')
    add_log(order, 'pending_dispatch', 'closed')

    response = client.post(
        f'/api/admin/orders/{order.id}/reopen',
        json={
            'target_status': 'pending_dispatch',
            'reason': '  误操作关闭，继续派单  ',
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.get_json()
    db.session.refresh(order)
    assert order.status == 'pending_dispatch'
    assert order.reject_reason == '原关闭原因'
    assert data['order']['status'] == 'pending_dispatch'
    assert data['log']['from_status'] == 'closed'
    assert data['log']['to_status'] == 'pending_dispatch'
    assert data['log']['operator_id'] == reopen_actor[0].id
    assert data['log']['operator_name'] == '恢复操作员'
    assert data['log']['remark'] == '取消关闭：误操作关闭，继续派单'


def test_reopen_double_submit_writes_one_reopen_log(
    client,
    auth_headers,
    make_order,
    add_log,
):
    order = make_order(status='closed')
    add_log(order, 'pending_accept', 'pending_dispatch')
    add_log(order, 'pending_dispatch', 'closed')
    url = f'/api/admin/orders/{order.id}/reopen'
    payload = {'target_status': 'pending_dispatch', 'reason': '恢复'}

    first = client.post(url, json=payload, headers=auth_headers)
    second = client.post(url, json=payload, headers=auth_headers)

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.get_json()['code'] == 'ORDER_NOT_CLOSED'
    assert OrderStatusLog.query.filter_by(
        order_id=order.id,
        from_status='closed',
        to_status='pending_dispatch',
    ).count() == 1
