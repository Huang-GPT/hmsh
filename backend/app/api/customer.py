from flask import request, jsonify, g
from app.api import bp
from app.services.auth_service import login_required
from app.models.user import User
from app.models.product import Product, UserProduct
from app.models.work_order import WorkOrder, OrderStatusLog
from app.models.common_fault import FaultCategory, CommonFault
from app.models.system import SystemConfig
from app import db
from datetime import datetime

# ========== 品牌服务主页 ==========
@bp.route('/customer/home', methods=['GET'])
@login_required
def customer_home():
    user = User.query.get(g.current_user_id)
    bound_count = UserProduct.query.filter_by(user_id=user.id).count()
    open_orders = WorkOrder.query.filter(
        WorkOrder.user_id == user.id,
        WorkOrder.status.notin_(['completed','closed','cancelled'])
    ).count()
    phone = SystemConfig.get_value('customer_service_phone', '400-123-4567')
    return jsonify({
        'bound_count': bound_count,
        'open_orders': open_orders,
        'customer_service_phone': phone,
        'user': user.to_dict()
    })

# ========== 产品绑定 ==========
@bp.route('/customer/products', methods=['GET'])
@login_required
def my_products():
    ups = UserProduct.query.filter_by(user_id=g.current_user_id).all()
    return jsonify({'products': [up.to_dict() for up in ups]})

@bp.route('/customer/products/bind', methods=['POST'])
@login_required
def bind_product():
    """终端用户绑定产品。必须先在产品库存在。
       后端不再自动创建 Product —— 防止终端绕过产品库直接"造"产品。"""
    data = request.get_json() or {}
    serial = (data.get('serial_number') or '').strip()
    method = data.get('bind_method', 'manual')
    if not serial:
        return jsonify({'error': '请输入产品序列号'}), 400

    product = Product.query.filter_by(serial_number=serial).first()
    if not product:
        return jsonify({
            'error': '产品库中未找到该序列号',
            'detail': f'serial_number={serial} 不存在，请联系客服补录后再绑定'
        }), 404

    existing = UserProduct.query.filter_by(user_id=g.current_user_id, product_id=product.id).first()
    if existing:
        return jsonify({'error': '该产品已绑定', 'bound_at': existing.bind_time.isoformat() if existing.bind_time else None}), 400

    up = UserProduct(user_id=g.current_user_id, product_id=product.id, bind_method=method)
    db.session.add(up)
    db.session.commit()
    return jsonify({'message': '绑定成功', 'product': product.to_dict()})

@bp.route('/customer/products/<int:product_id>/unbind', methods=['POST'])
@login_required
def unbind_product(product_id):
    up = UserProduct.query.filter_by(user_id=g.current_user_id, product_id=product_id).first()
    if not up:
        return jsonify({'error': '未绑定'}), 400
    db.session.delete(up)
    db.session.commit()
    return jsonify({'message': '解绑成功'})

@bp.route('/customer/products/scan-sap', methods=['POST'])
@login_required
def bind_by_sap():
    data = request.get_json()
    sap_order_no = data.get('sap_order_no')
    sap_line_item = data.get('sap_line_item')
    if not sap_order_no or not sap_line_item:
        return jsonify({'error': '缺少参数'}), 400

    product = Product.query.filter_by(sap_order_no=sap_order_no, sap_line_item=sap_line_item).first()
    if not product:
        return jsonify({'error': '未找到对应产品'}), 404

    existing = UserProduct.query.filter_by(user_id=g.current_user_id, product_id=product.id).first()
    if existing:
        return jsonify({'error': '该产品已绑定'}), 400

    up = UserProduct(user_id=g.current_user_id, product_id=product.id, bind_method='qrcode_sap')
    db.session.add(up)
    db.session.commit()
    return jsonify({'message': '绑定成功', 'product': product.to_dict()})

# ========== 产品报修 ==========
@bp.route('/customer/orders', methods=['POST'])
@login_required
def create_order():
    data = request.get_json()
    required = ['product_id', 'fault_type', 'fault_desc', 'contact_name', 'contact_phone']
    for f in required:
        if f not in data:
            return jsonify({'error': f'缺少{f}'}), 400

    today = datetime.now().strftime('%Y%m%d')
    last = WorkOrder.query.filter(WorkOrder.order_no.like(f'RM{today}%')).order_by(WorkOrder.id.desc()).first()
    if last:
        seq = int(last.order_no[-4:]) + 1
    else:
        seq = 1
    order_no = f"RM{today}{seq:04d}"

    order = WorkOrder(
        order_no=order_no,
        user_id=g.current_user_id,
        product_id=data['product_id'],
        fault_category_id=data.get('fault_category_id'),
        fault_type=data['fault_type'],
        fault_desc=data['fault_desc'],
        images=data.get('images'),
        videos=data.get('videos'),
        fault_address=data.get('fault_address'),
        appointment_date=data.get('appointment_date'),
        appointment_period=data.get('appointment_period'),
        contact_name=data['contact_name'],
        contact_phone=data['contact_phone'],
        status='pending_accept'
    )
    db.session.add(order)
    db.session.commit()

    log = OrderStatusLog(order_id=order.id, from_status=None, to_status='pending_accept',
                         operator_id=g.current_user_id, operator_name=g.current_user_nickname, remark='提交报修')
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': '报修成功', 'order_no': order_no, 'order': order.to_dict()})

@bp.route('/customer/orders', methods=['GET'])
@login_required
def my_orders():
    status = request.args.get('status')
    query = WorkOrder.query.filter_by(user_id=g.current_user_id)
    if status:
        query = query.filter_by(status=status)
    orders = query.order_by(WorkOrder.created_at.desc()).all()
    return jsonify({'orders': [o.to_dict() for o in orders]})

@bp.route('/customer/orders/<int:order_id>', methods=['GET'])
@login_required
def my_order_detail(order_id):
    order = WorkOrder.query.get_or_404(order_id)
    if order.user_id != g.current_user_id:
        return jsonify({'error': '无权查看'}), 403
    logs = order.status_logs.all()
    return jsonify({'order': order.to_dict(), 'logs': [l.to_dict() for l in logs]})

@bp.route('/customer/orders/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    order = WorkOrder.query.get_or_404(order_id)
    if order.user_id != g.current_user_id:
        return jsonify({'error': '无权操作'}), 403
    if order.status != 'pending_accept':
        return jsonify({'error': '当前状态不能撤销'}), 400
    data = request.get_json() or {}
    order.status = 'cancelled'
    order.cancel_reason = data.get('reason', '')
    log = OrderStatusLog(order_id=order.id, from_status='pending_accept', to_status='cancelled',
                         operator_id=g.current_user_id, operator_name=g.current_user_nickname,
                         remark=data.get('reason', '申请撤销'))
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': '已提交撤销申请'})

# ========== 常见故障 ==========
@bp.route('/customer/fault-categories', methods=['GET'])
@login_required
def customer_fault_categories():
    cats = FaultCategory.query.filter_by(status='active', parent_id=0).order_by(FaultCategory.sort_order).all()
    result = []
    for cat in cats:
        children = FaultCategory.query.filter_by(parent_id=cat.id, status='active').order_by(FaultCategory.sort_order).all()
        result.append({**cat.to_dict(), 'children': [c.to_dict() for c in children]})
    return jsonify({'categories': result})

@bp.route('/customer/faults', methods=['GET'])
@login_required
def customer_faults():
    cat_id = request.args.get('category_id', type=int)
    model = request.args.get('product_model')
    query = CommonFault.query.filter_by(status='active')
    if cat_id:
        query = query.filter_by(category_id=cat_id)
    if model:
        query = query.filter(db.or_(CommonFault.product_model == model, CommonFault.product_model.is_(None)))
    faults = query.order_by(CommonFault.sort_order).all()
    return jsonify({'faults': [f.to_dict() for f in faults]})

@bp.route('/customer/faults/<int:fault_id>', methods=['GET'])
@login_required
def customer_fault_detail(fault_id):
    fault = CommonFault.query.get_or_404(fault_id)
    fault.view_count += 1
    db.session.commit()
    return jsonify({'fault': fault.to_dict()})

# ========== 客服电话 ==========
@bp.route('/customer/service-phone', methods=['GET'])
@login_required
def service_phone():
    phone = SystemConfig.get_value('customer_service_phone', '400-123-4567')
    return jsonify({'phone': phone})
