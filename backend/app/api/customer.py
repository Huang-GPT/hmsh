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
       后端不再自动创建 Product —— 防止终端绕过产品库直接"造"产品。
       支持两种输入：serial_number 或 qr_code，任意一种命中即可。"""
    data = request.get_json() or {}
    serial = (data.get('serial_number') or '').strip()
    qr = (data.get('qr_code') or '').strip()
    method = data.get('bind_method', 'qrcode_product')
    if not serial and not qr:
        return jsonify({'error': '请输入产品序列号或二维码'}), 400

    product = None
    if serial:
        product = Product.query.filter_by(serial_number=serial).first()
    if not product and qr:
        product = Product.query.filter_by(qr_code=qr).first()
    if not product:
        return jsonify({
            'error': '产品库中未找到该序列号或二维码',
            'detail': '请在管理后台录入后再绑定，或联系客服',
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
    """扫码 / 手动输入销售单 + 行项目号 绑定。
       兼容 sap_order_no 与 sales_no 两个字段（CSV 导入只填了 sales_no）"""
    data = request.get_json() or {}
    order_no = (data.get('sap_order_no') or '').strip()
    sap_line_item = data.get('sap_line_item')
    if not order_no or sap_line_item in (None, ''):
        return jsonify({'error': '缺少参数'}), 400

    try:
        line_item_int = int(str(sap_line_item).strip())
    except (ValueError, TypeError):
        return jsonify({'error': '行项目号必须是整数'}), 400

    from sqlalchemy import or_
    product = Product.query.filter(
        or_(
            Product.sap_order_no == order_no,
            Product.sales_no == order_no,
        ),
        Product.sap_line_item == line_item_int,
    ).first()
    if not product:
        return jsonify({
            'error': '产品库中未找到该销售单+行项目号',
            'detail': f'订单 {order_no} 行项目 {line_item_int} 不存在，请先在管理后台录入',
        }), 404

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
    """P0+P1 重构：每个分类返回 fault_count + attachment_count（P1 加分）
    使用单次聚合查询，避免 N+1。
    """
    from sqlalchemy import func
    from app.models.common_fault import FaultAttachment

    cats = FaultCategory.query.filter_by(status='active', parent_id=0)\
        .order_by(FaultCategory.sort_order).all()
    cat_ids = [c.id for c in cats]
    # 子分类 id 也要算进去（手机端点击顶级分类时也展示二级）
    children_map = {}
    if cat_ids:
        children = FaultCategory.query.filter(
            FaultCategory.parent_id.in_(cat_ids),
            FaultCategory.status == 'active',
        ).all()
        for ch in children:
            children_map.setdefault(ch.parent_id, []).append(ch.id)

    # 一次聚合：每个 cat_id 下的 active fault 数 + active attachment 数
    all_cat_ids = set(cat_ids) | {cid for ids in children_map.values() for cid in ids}
    fault_count = {}
    att_count = {}
    if all_cat_ids:
        rows = db.session.query(
            CommonFault.category_id,
            func.count(CommonFault.id),
        ).filter(
            CommonFault.category_id.in_(all_cat_ids),
            CommonFault.status == 'active',
        ).group_by(CommonFault.category_id).all()
        fault_count = {cid: cnt for cid, cnt in rows}

        rows2 = db.session.query(
            CommonFault.category_id,
            func.count(FaultAttachment.id),
        ).join(
            FaultAttachment,
            db.and_(
                FaultAttachment.fault_id == CommonFault.id,
                FaultAttachment.deleted_at.is_(None),
            ),
        ).filter(
            CommonFault.category_id.in_(all_cat_ids),
            CommonFault.status == 'active',
        ).group_by(CommonFault.category_id).all()
        att_count = {cid: cnt for cid, cnt in rows2}

    result = []
    for cat in cats:
        d = cat.to_dict()
        ch_ids = children_map.get(cat.id, [])
        # 顶级分类的计数 = 自己 + 所有子分类
        total_faults = fault_count.get(cat.id, 0) + sum(fault_count.get(c, 0) for c in ch_ids)
        total_atts = att_count.get(cat.id, 0) + sum(att_count.get(c, 0) for c in ch_ids)
        d['fault_count'] = int(total_faults)
        d['attachment_count'] = int(total_atts)
        d['children'] = []
        for ch in FaultCategory.query.filter_by(parent_id=cat.id, status='active')\
                .order_by(FaultCategory.sort_order).all():
            cd = ch.to_dict()
            cd['fault_count'] = int(fault_count.get(ch.id, 0))
            cd['attachment_count'] = int(att_count.get(ch.id, 0))
            d['children'].append(cd)
        result.append(d)
    return jsonify({'categories': result})


@bp.route('/customer/faults', methods=['GET'])
@login_required
def customer_faults():
    """P0+P1 重构：to_dict 默认含 attachments 列表（来自 common_fault_attachments 关系）
    手机端可同时读 attachments[]（新）和 files[]（兼容老数据，迁移后为空数组）。
    """
    cat_id = request.args.get('category_id', type=int)
    model = request.args.get('product_model')
    query = CommonFault.query.filter_by(status='active')
    if cat_id:
        query = query.filter_by(category_id=cat_id)
    if model:
        query = query.filter(db.or_(CommonFault.product_model == model, CommonFault.product_model.is_(None)))
    faults = query.order_by(CommonFault.sort_order).all()
    return jsonify({'faults': [f.to_dict(with_attachments=True) for f in faults]})


@bp.route('/customer/faults/<int:fault_id>', methods=['GET'])
@login_required
def customer_fault_detail(fault_id):
    fault = CommonFault.query.get_or_404(fault_id)
    fault.view_count += 1
    db.session.commit()
    return jsonify({'fault': fault.to_dict(with_attachments=True)})

# ========== 客服电话 ==========
@bp.route('/customer/service-phone', methods=['GET'])
@login_required
def service_phone():
    phone = SystemConfig.get_value('customer_service_phone', '400-123-4567')
    return jsonify({'phone': phone})
