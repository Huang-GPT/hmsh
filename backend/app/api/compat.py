"""
后端 URL 兼容层

为旧的/不一致的前端 API 调用提供兼容路由。
每个兼容函数内部调用真实业务接口，返回相同响应。
"""
from flask import request, jsonify, g
from app.api import bp
from app.services.auth_service import login_required
from app.api.customer import (
    my_products, bind_product, unbind_product, bind_by_sap,
    my_orders, my_order_detail, cancel_order, create_order,
    customer_faults, customer_fault_detail,
)
from app.api.admin import (
    dashboard, get_users,
    create_fault,
)
from app import db
from app.models.work_order import WorkOrder
from app.models.common_fault import CommonFault


# ============ 客户/产品兼容 ============

@bp.route('/products', methods=['GET'])
@login_required
def compat_my_products():
    """旧: GET /api/products -> 转发到 GET /api/customer/products"""
    return my_products()


@bp.route('/products/bind', methods=['POST'])
@login_required
def compat_bind_product():
    """旧: POST /api/products/bind body={serial_number, model, bind_method, user_id}
       新: POST /api/customer/products/bind body={serial_number, model, bind_method}"""
    return bind_product()


@bp.route('/products/unbind', methods=['POST'])
@login_required
def compat_unbind_product():
    """旧: POST /api/products/unbind body={user_id, product_id}
       新: POST /api/customer/products/<id>/unbind"""
    data = request.get_json() or {}
    product_id = data.get('product_id')
    if not product_id:
        return jsonify({'error': '缺少product_id'}), 400
    return unbind_product(product_id)


@bp.route('/products/<int:product_id>/unbind', methods=['POST'])
@login_required
def compat_unbind_product_path(product_id):
    """支持 path 形式的解绑"""
    return unbind_product(product_id)


# ============ 工单兼容 ============

@bp.route('/work-orders', methods=['GET'])
@login_required
def compat_list_orders():
    return my_orders()


@bp.route('/work-orders', methods=['POST'])
@login_required
def compat_create_order():
    return create_order()


@bp.route('/work-orders/<int:order_id>', methods=['GET'])
@login_required
def compat_get_order(order_id):
    return my_order_detail(order_id)


# ============ 故障库兼容 ============

@bp.route('/faults', methods=['GET'])
@login_required
def compat_list_faults():
    return customer_faults()


@bp.route('/faults/<int:fault_id>', methods=['GET'])
@login_required
def compat_get_fault(fault_id):
    return customer_fault_detail(fault_id)


@bp.route('/faults/popular', methods=['GET'])
@login_required
def compat_popular_faults():
    """旧: GET /api/faults/popular?limit=10
       替代: 按 view_count desc 取前 N 条"""
    limit = request.args.get('limit', default=10, type=int)
    faults = CommonFault.query.filter_by(status='active')\
        .order_by(CommonFault.view_count.desc())\
        .limit(limit).all()
    return jsonify({'faults': [f.to_dict() for f in faults]})


@bp.route('/faults/<int:fault_id>/helpful', methods=['POST'])
@login_required
def compat_mark_helpful(fault_id):
    """前端 CommonFaults.vue 调用的有帮助接口"""
    fault = CommonFault.query.get_or_404(fault_id)
    fault.helpful_count = (fault.helpful_count or 0) + 1
    db.session.commit()
    return jsonify({'fault': fault.to_dict()})


@bp.route('/faults', methods=['POST'])
@login_required
def compat_create_fault():
    """旧: POST /api/faults (客户提交故障案例)
       实际: 创建到 admin 故障库（需要 admin 角色；前端目前未传角色会 403）"""
    from app.services.auth_service import role_required
    if g.current_user_role not in ('admin', 'operator'):
        return jsonify({'error': '无权限'}), 403
    return create_fault()


# ============ 管理后台统计兼容 ============

@bp.route('/admin/statistics', methods=['GET'])
@login_required
def compat_admin_statistics():
    """前端调用: 期望返回 {total_orders, pending_orders, completed_orders, today_orders}
       真实接口 /admin/dashboard 字段稍有差异，做归一化"""
    resp = dashboard()
    data = resp.get_json() or {}
    return jsonify({
        'total_orders': data.get('total_orders', 0),
        'pending_orders': data.get('pending_dispatch', 0),
        'completed_orders': data.get('completed', 0),
        'today_orders': data.get('today_orders', 0),
    })


@bp.route('/admin/statistics/by-status', methods=['GET'])
@login_required
def compat_statistics_by_status():
    """前端期望: {status_name: count} 字典"""
    rows = db.session.query(WorkOrder.status, db.func.count(WorkOrder.id))\
        .group_by(WorkOrder.status).all()
    return jsonify({s: c for s, c in rows})


@bp.route('/admin/service-staff', methods=['GET'])
@login_required
def compat_service_staff():
    """前端期望: {users: [...]} 列出客服/服务点/工程师/操作员"""
    from app.models.user import User
    users = User.query.filter(
        User.role.in_(['dispatcher', 'service_point', 'engineer', 'operator', 'admin'])
    ).all()
    return jsonify({'users': [u.to_dict() for u in users]})


# ============ 工单分配/状态变更兼容 ============

@bp.route('/admin/orders/<int:order_id>/assign', methods=['POST'])
@login_required
def compat_assign_order(order_id):
    """旧: POST /admin/orders/<id>/assign body={handler_id, remark}
       简化: 若工单为 pending_dispatch，自动派单到 handler 对应的 service_point 并分配
       若已 dispatched/assigned_engineer，更新 engineer_id"""
    from app.models.user import User
    from app.models.service_point import Engineer
    from app.models.work_order import OrderStatusLog

    data = request.get_json() or {}
    handler_id = data.get('handler_id')
    if not handler_id:
        return jsonify({'error': '缺少handler_id'}), 400
    order = WorkOrder.query.get_or_404(order_id)

    handler = User.query.get(handler_id)
    eng = Engineer.query.filter_by(user_id=handler_id).first() if handler else None
    if not eng:
        return jsonify({'error': '该用户不是工程师'}), 400

    if order.status == 'pending_dispatch':
        order.service_point_id = eng.service_point_id
        order.status = 'dispatched'
        db.session.add(OrderStatusLog(
            order_id=order.id, from_status='pending_dispatch', to_status='dispatched',
            operator_id=g.current_user_id, operator_name=g.current_user_nickname,
            remark=f'分配服务点 {eng.service_point_id}'))

    if order.status == 'dispatched':
        order.engineer_id = eng.id
        order.status = 'assigned_engineer'
        db.session.add(OrderStatusLog(
            order_id=order.id, from_status='dispatched', to_status='assigned_engineer',
            operator_id=g.current_user_id, operator_name=g.current_user_nickname,
            remark=f'分配工程师: {eng.name}'))
    else:
        return jsonify({'error': f'当前状态({order.status})不能分配'}), 400

    db.session.commit()
    return jsonify({'message': '分配成功', 'order': order.to_dict()})


@bp.route('/admin/orders/<int:order_id>/status', methods=['PUT'])
@login_required
def compat_update_order_status(order_id):
    """旧: PUT /admin/orders/<id>/status body={status, remark, operator_id}
       新: 根据目标 status 路由到对应逻辑（直接内联实现避免 request 上下文嵌套）"""
    from app.models.work_order import OrderStatusLog

    data = request.get_json() or {}
    target = data.get('status')
    remark = data.get('remark', '')
    order = WorkOrder.query.get_or_404(order_id)

    transitions = {
        'processing': ('assigned_engineer', 'processing'),
        'pending_confirm': ('processing', 'pending_confirm'),
        'completed': ('pending_confirm', 'completed'),
    }
    if target not in transitions:
        return jsonify({'error': f'不支持的状态变更: {target}'}), 400

    from_s, to_s = transitions[target]
    if order.status != from_s:
        return jsonify({'error': f'当前状态({order.status})不能变更为{target}'}), 400

    order.status = to_s
    db.session.add(OrderStatusLog(
        order_id=order.id, from_status=from_s, to_status=to_s,
        operator_id=g.current_user_id, operator_name=g.current_user_nickname,
        remark=remark))
    db.session.commit()
    return jsonify({'message': f'状态已更新为 {to_s}', 'order': order.to_dict()})


# ============ 微信OAuth 兼容 ============

@bp.route('/auth/wechat/oauth', methods=['GET'])
def compat_wechat_oauth():
    """前端调用: GET /auth/wechat/oauth?redirect_uri=...
       占位: 返回登录页 URL（前端目前未真正使用）"""
    redirect_uri = request.args.get('redirect_uri', '')
    appid = 'PLACEHOLDER_APPID'
    oauth_url = (
        f'https://open.weixin.qq.com/connect/oauth2/authorize'
        f'?appid={appid}&redirect_uri={redirect_uri}&response_type=code'
        f'&scope=snsapi_base&state=STATE#wechat_redirect'
    )
    return jsonify({'url': oauth_url, 'appId': appid})


@bp.route('/auth/wechat/callback', methods=['GET'])
def compat_wechat_callback():
    """占位: 真实场景应通过 code 换 openid"""
    code = request.args.get('code', '')
    return jsonify({'openid': f'mock_openid_{code}', 'nickname': '微信用户', 'code': code})


@bp.route('/auth/login', methods=['POST'])
def compat_auth_login():
    """旧: POST /auth/login body={openid}
       新: POST /auth/customer/login body={openid}"""
    from app.api.auth import customer_login
    return customer_login()


@bp.route('/auth/user', methods=['PUT'])
@login_required
def compat_update_user():
    """旧: PUT /auth/user body={nickname, phone, avatar}
       新: 直接更新 User 模型"""
    from app.models.user import User
    user = User.query.get(g.current_user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    data = request.get_json() or {}
    for f in ('nickname', 'phone', 'avatar'):
        if f in data:
            setattr(user, f, data[f])
    db.session.commit()
    return jsonify({'user': user.to_dict()})


@bp.route('/wechat/config', methods=['GET'])
def compat_wechat_config():
    """前端 wechat.js 调用: GET /api/wechat/config?url=...
       占位: 返回 wx.config 所需签名（生产应真实生成）"""
    url = request.args.get('url', '')
    return jsonify({
        'appId': 'PLACEHOLDER_APPID',
        'timestamp': 0,
        'nonceStr': 'placeholder',
        'signature': 'placeholder',
        'url': url,
    })
