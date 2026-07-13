from flask import request, jsonify, g
from app.api import bp
from app.services.auth_service import login_required, role_required, hash_password
from app.models.user import User
from app.models.service_point import ServicePoint, Engineer
from app.models.work_order import WorkOrder
from app.models.common_fault import FaultCategory, CommonFault
from app.models.product import Product
from app.models.system import SystemConfig
from app import db
import csv
import io
from datetime import datetime

# ========== 工作台统计 ==========
@bp.route('/admin/dashboard', methods=['GET'])
@login_required
def dashboard():
    total = WorkOrder.query.count()
    pending_dispatch = WorkOrder.query.filter_by(status='pending_dispatch').count()
    processing = WorkOrder.query.filter_by(status='processing').count()
    completed = WorkOrder.query.filter_by(status='completed').count()

    from datetime import datetime, timedelta
    today = datetime.now().date()
    today_orders = WorkOrder.query.filter(WorkOrder.created_at >= str(today)).count()

    return jsonify({
        'total_orders': total,
        'pending_dispatch': pending_dispatch,
        'processing': processing,
        'completed': completed,
        'today_orders': today_orders,
    })

# ========== 用户管理 ==========
@bp.route('/admin/users', methods=['GET'])
@login_required
@role_required('admin')
def get_users():
    role = request.args.get('role')
    query = User.query
    if role:
        query = query.filter_by(role=role)
    users = query.order_by(User.created_at.desc()).all()
    return jsonify({'users': [u.to_dict() for u in users]})

@bp.route('/admin/users', methods=['POST'])
@login_required
@role_required('admin')
def create_user():
    data = request.get_json()
    required = ['account', 'nickname', 'role']
    for f in required:
        if f not in data:
            return jsonify({'error': f'缺少{f}'}), 400

    if User.query.filter_by(openid=data['account']).first():
        return jsonify({'error': '账号已存在'}), 400

    init_password = data.get('password', '123456')
    user = User(
        openid=data['account'],
        nickname=data['nickname'],
        role=data['role'],
        phone=data.get('phone'),
        password_hash=hash_password(init_password),
        service_point_id=data.get('service_point_id'),
        status='active'
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': '创建成功', 'user': user.to_dict()})

@bp.route('/admin/users/<int:user_id>/status', methods=['PUT'])
@login_required
@role_required('admin')
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    user.status = 'disabled' if user.status == 'active' else 'active'
    db.session.commit()
    return jsonify({'message': 'ok', 'status': user.status})

@bp.route('/admin/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@role_required('admin')
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    new_password = data.get('password', '123456')
    user.password_hash = hash_password(new_password)
    db.session.commit()
    return jsonify({'message': '密码已重置'})

# ========== 服务点管理 ==========
@bp.route('/admin/service-points', methods=['GET'])
@login_required
def get_service_points():
    points = ServicePoint.query.filter_by(status='active').all()
    return jsonify({'service_points': [p.to_dict() for p in points]})

@bp.route('/admin/service-points', methods=['POST'])
@login_required
@role_required('admin')
def create_service_point():
    data = request.get_json()
    sp = ServicePoint(
        name=data['name'],
        contact_person=data.get('contact_person'),
        contact_phone=data.get('contact_phone'),
        address=data.get('address'),
        region=data.get('region'),
    )
    db.session.add(sp)
    db.session.commit()
    return jsonify({'message': '创建成功', 'service_point': sp.to_dict()})

@bp.route('/admin/service-points/<int:sp_id>', methods=['PUT'])
@login_required
@role_required('admin')
def update_service_point(sp_id):
    sp = ServicePoint.query.get_or_404(sp_id)
    data = request.get_json()
    for k in ['name','contact_person','contact_phone','address','region']:
        if k in data:
            setattr(sp, k, data[k])
    db.session.commit()
    return jsonify({'message': '更新成功', 'service_point': sp.to_dict()})

@bp.route('/admin/service-points/<int:sp_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_service_point(sp_id):
    sp = ServicePoint.query.get_or_404(sp_id)
    sp.status = 'disabled'
    db.session.commit()
    return jsonify({'message': '已删除'})

# ========== 工程师管理 ==========
@bp.route('/admin/engineers', methods=['GET'])
@login_required
def get_engineers():
    sp_id = request.args.get('service_point_id', type=int)
    query = Engineer.query
    if sp_id:
        query = query.filter_by(service_point_id=sp_id)
    engineers = query.all()
    return jsonify({'engineers': [e.to_dict() for e in engineers]})

@bp.route('/admin/engineers', methods=['POST'])
@login_required
@role_required('admin','service_point')
def create_engineer():
    data = request.get_json()
    e = Engineer(
        name=data['name'],
        phone=data['phone'],
        service_point_id=data['service_point_id'],
        specialty=data.get('specialty'),
    )
    db.session.add(e)
    db.session.commit()
    return jsonify({'message': '创建成功', 'engineer': e.to_dict()})

@bp.route('/admin/engineers/<int:e_id>', methods=['PUT'])
@login_required
@role_required('admin','service_point')
def update_engineer(e_id):
    e = Engineer.query.get_or_404(e_id)
    data = request.get_json()
    for k in ['name','phone','service_point_id','specialty','status']:
        if k in data:
            setattr(e, k, data[k])
    db.session.commit()
    return jsonify({'message': '更新成功', 'engineer': e.to_dict()})

@bp.route('/admin/engineers/<int:e_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_engineer(e_id):
    e = Engineer.query.get_or_404(e_id)
    e.status = 'disabled'
    db.session.commit()
    return jsonify({'message': '已删除'})

# ========== 派单员工作台 ==========
@bp.route('/admin/orders/pending-dispatch', methods=['GET'])
@login_required
@role_required('admin','dispatcher')
def pending_dispatch_orders():
    query = WorkOrder.query.filter_by(status='pending_dispatch')
    family = request.args.get('product_family')
    sp_id = request.args.get('service_point_id', type=int)
    if family:
        query = query.join(Product).filter(Product.product_family == family)
    if sp_id:
        query = query.filter_by(service_point_id=sp_id)
    orders = query.order_by(WorkOrder.created_at.asc()).all()
    return jsonify({'orders': [o.to_dict() for o in orders]})

@bp.route('/admin/orders/<int:order_id>/dispatch', methods=['POST'])
@login_required
@role_required('admin','dispatcher')
def dispatch_order(order_id):
    order = WorkOrder.query.get_or_404(order_id)
    if order.status != 'pending_dispatch':
        return jsonify({'error': f'当前状态不能派单: {order.status}'}), 400
    data = request.get_json()
    sp_id = data.get('service_point_id')
    if not sp_id:
        return jsonify({'error': '请选择服务点'}), 400

    from app.models.work_order import OrderStatusLog
    order.service_point_id = sp_id
    order.status = 'dispatched'
    log = OrderStatusLog(order_id=order.id, from_status='pending_dispatch', to_status='dispatched',
                         operator_id=g.current_user_id, operator_name=g.current_user_nickname, remark='派单')
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': '派单成功', 'order': order.to_dict()})

@bp.route('/admin/orders/<int:order_id>/reject', methods=['POST'])
@login_required
@role_required('admin','dispatcher')
def reject_order(order_id):
    order = WorkOrder.query.get_or_404(order_id)
    if order.status not in ['pending_dispatch','pending_accept']:
        return jsonify({'error': '当前状态不能拒绝'}), 400
    data = request.get_json()
    reason = data.get('reason', '')
    order.status = 'closed'
    order.reject_reason = reason

    from app.models.work_order import OrderStatusLog
    log = OrderStatusLog(order_id=order.id, from_status=order.status, to_status='closed',
                         operator_id=g.current_user_id, operator_name=g.current_user_nickname, remark=f'拒绝: {reason}')
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': '已关闭', 'order': order.to_dict()})

# ========== 撤销审核 ==========
@bp.route('/admin/orders/pending-cancel', methods=['GET'])
@login_required
@role_required('admin','dispatcher')
def pending_cancel_orders():
    from app.models.work_order import OrderStatusLog
    cancel_logs = OrderStatusLog.query.filter_by(to_status='cancelled').all()
    order_ids = [log.order_id for log in cancel_logs]
    orders = WorkOrder.query.filter(WorkOrder.id.in_(order_ids), WorkOrder.status == 'cancelled').all()
    return jsonify({'orders': [o.to_dict() for o in orders]})

@bp.route('/admin/orders/<int:order_id>/approve-cancel', methods=['POST'])
@login_required
@role_required('admin','dispatcher')
def approve_cancel(order_id):
    order = WorkOrder.query.get_or_404(order_id)
    if order.status != 'cancelled':
        return jsonify({'error': '工单未申请撤销'}), 400
    order.status = 'closed'
    from app.models.work_order import OrderStatusLog
    log = OrderStatusLog(order_id=order.id, from_status='cancelled', to_status='closed',
                         operator_id=g.current_user_id, operator_name=g.current_user_nickname, remark='同意撤销')
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': '已关闭'})

@bp.route('/admin/orders/<int:order_id>/reject-cancel', methods=['POST'])
@login_required
@role_required('admin','dispatcher')
def reject_cancel(order_id):
    order = WorkOrder.query.get_or_404(order_id)
    if order.status != 'cancelled':
        return jsonify({'error': '工单未申请撤销'}), 400
    order.status = 'pending_accept'
    from app.models.work_order import OrderStatusLog
    log = OrderStatusLog(order_id=order.id, from_status='cancelled', to_status='pending_accept',
                         operator_id=g.current_user_id, operator_name=g.current_user_nickname, remark='拒绝撤销，恢复待受理')
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': '已恢复'})

# ========== 服务点工作台 ==========
@bp.route('/admin/orders/service-point', methods=['GET'])
@login_required
@role_required('admin','service_point')
def service_point_orders():
    user = User.query.get(g.current_user_id)
    sp_id = user.service_point_id if user.role == 'service_point' else request.args.get('service_point_id', type=int)
    if not sp_id:
        return jsonify({'error': '无服务点'}), 400
    orders = WorkOrder.query.filter(WorkOrder.service_point_id == sp_id, WorkOrder.status.in_(['dispatched','assigned_engineer','processing'])).order_by(WorkOrder.created_at.asc()).all()
    return jsonify({'orders': [o.to_dict() for o in orders]})

@bp.route('/admin/orders/<int:order_id>/assign-engineer', methods=['POST'])
@login_required
@role_required('admin','service_point')
def assign_engineer(order_id):
    order = WorkOrder.query.get_or_404(order_id)
    if order.status != 'dispatched':
        return jsonify({'error': '当前状态不能分配工程师'}), 400
    data = request.get_json()
    eng_id = data.get('engineer_id')
    if not eng_id:
        return jsonify({'error': '请选择工程师'}), 400
    eng = Engineer.query.get_or_404(eng_id)
    order.engineer_id = eng_id
    order.status = 'assigned_engineer'
    from app.models.work_order import OrderStatusLog
    log = OrderStatusLog(order_id=order.id, from_status='dispatched', to_status='assigned_engineer',
                         operator_id=g.current_user_id, operator_name=g.current_user_nickname,
                         remark=f'分配工程师: {eng.name}')
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': '分配成功', 'order': order.to_dict()})

@bp.route('/admin/orders/<int:order_id>/start-processing', methods=['POST'])
@login_required
@role_required('admin','service_point','engineer')
def start_processing(order_id):
    order = WorkOrder.query.get_or_404(order_id)
    if order.status != 'assigned_engineer':
        return jsonify({'error': '当前状态不能开始处理'}), 400
    order.status = 'processing'
    from app.models.work_order import OrderStatusLog
    data = request.get_json() or {}
    log = OrderStatusLog(order_id=order.id, from_status='assigned_engineer', to_status='processing',
                         operator_id=g.current_user_id, operator_name=g.current_user_nickname,
                         remark=data.get('remark', '开始处理'))
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': '开始处理', 'order': order.to_dict()})

@bp.route('/admin/orders/<int:order_id>/progress', methods=['POST'])
@login_required
@role_required('admin','service_point','engineer')
def update_progress(order_id):
    order = WorkOrder.query.get_or_404(order_id)
    if order.status != 'processing':
        return jsonify({'error': '当前状态不能更新进度'}), 400
    data = request.get_json()
    from app.models.work_order import OrderStatusLog
    log = OrderStatusLog(order_id=order.id, from_status='processing', to_status='processing',
                         operator_id=g.current_user_id, operator_name=g.current_user_nickname,
                         remark=data.get('remark', ''), images=data.get('images'))
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': '进度已更新'})

@bp.route('/admin/orders/<int:order_id>/complete', methods=['POST'])
@login_required
@role_required('admin','service_point','engineer')
def complete_order(order_id):
    order = WorkOrder.query.get_or_404(order_id)
    if order.status != 'processing':
        return jsonify({'error': '当前状态不能完成'}), 400
    order.status = 'pending_confirm'
    from app.models.work_order import OrderStatusLog
    data = request.get_json() or {}
    log = OrderStatusLog(order_id=order.id, from_status='processing', to_status='pending_confirm',
                         operator_id=g.current_user_id, operator_name=g.current_user_nickname,
                         remark=data.get('remark', '处理完成'), images=data.get('images'))
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': '已完成，等待客户确认', 'order': order.to_dict()})

# ========== 故障库管理 ==========
@bp.route('/admin/fault-categories', methods=['GET'])
@login_required
def get_fault_categories():
    cats = FaultCategory.query.filter_by(status='active').order_by(FaultCategory.sort_order).all()
    return jsonify({'categories': [c.to_dict() for c in cats]})

@bp.route('/admin/fault-categories', methods=['POST'])
@login_required
@role_required('admin','operator')
def create_fault_category():
    data = request.get_json()
    cat = FaultCategory(parent_id=data.get('parent_id', 0), name=data['name'], icon=data.get('icon'), sort_order=data.get('sort_order', 0))
    db.session.add(cat)
    db.session.commit()
    return jsonify({'message': '创建成功', 'category': cat.to_dict()})

@bp.route('/admin/fault-categories/<int:cat_id>', methods=['PUT'])
@login_required
@role_required('admin','operator')
def update_fault_category(cat_id):
    cat = FaultCategory.query.get_or_404(cat_id)
    data = request.get_json()
    for k in ['name','icon','sort_order','status']:
        if k in data:
            setattr(cat, k, data[k])
    db.session.commit()
    return jsonify({'message': '更新成功', 'category': cat.to_dict()})

@bp.route('/admin/fault-categories/<int:cat_id>', methods=['DELETE'])
@login_required
@role_required('admin','operator')
def delete_fault_category(cat_id):
    cat = FaultCategory.query.get_or_404(cat_id)
    cat.status = 'disabled'
    db.session.commit()
    return jsonify({'message': '已删除'})

@bp.route('/admin/faults', methods=['GET'])
@login_required
def get_all_faults():
    keyword = request.args.get('keyword')
    cat_id = request.args.get('category_id', type=int)
    query = CommonFault.query
    if cat_id:
        query = query.filter_by(category_id=cat_id)
    if keyword:
        query = query.filter(db.or_(CommonFault.title.like(f'%{keyword}%'), CommonFault.content.like(f'%{keyword}%')))
    faults = query.order_by(CommonFault.sort_order).all()
    return jsonify({'faults': [f.to_dict() for f in faults]})

@bp.route('/admin/faults', methods=['POST'])
@login_required
@role_required('admin','operator')
def create_fault():
    data = request.get_json()
    fault = CommonFault(
        category_id=data['category_id'], title=data['title'], content=data.get('content'),
        product_model=data.get('product_model'), images=data.get('images'), videos=data.get('videos'),
        sort_order=data.get('sort_order', 0)
    )
    db.session.add(fault)
    db.session.commit()
    return jsonify({'message': '创建成功', 'fault': fault.to_dict()})

@bp.route('/admin/faults/<int:fault_id>', methods=['PUT'])
@login_required
@role_required('admin','operator')
def update_fault(fault_id):
    fault = CommonFault.query.get_or_404(fault_id)
    data = request.get_json()
    for k in ['category_id','title','content','product_model','images','videos','sort_order','status']:
        if k in data:
            setattr(fault, k, data[k])
    db.session.commit()
    return jsonify({'message': '更新成功', 'fault': fault.to_dict()})

@bp.route('/admin/faults/<int:fault_id>', methods=['DELETE'])
@login_required
@role_required('admin','operator')
def delete_fault(fault_id):
    fault = CommonFault.query.get_or_404(fault_id)
    fault.status = 'disabled'
    db.session.commit()
    return jsonify({'message': '已删除'})

# ========== 系统配置 ==========
@bp.route('/admin/config/<key>', methods=['GET'])
@login_required
@role_required('admin')
def get_config(key):
    val = SystemConfig.get_value(key)
    return jsonify({'value': val})

@bp.route('/admin/config/<key>', methods=['PUT'])
@login_required
@role_required('admin')
def set_config(key):
    data = request.get_json()
    SystemConfig.set_value(key, data.get('value'), data.get('description'))
    return jsonify({'message': 'ok'})

# ========== 工单列表（通用） ==========
@bp.route('/admin/orders', methods=['GET'])
@login_required
def get_all_orders():
    status = request.args.get('status')
    keyword = request.args.get('keyword')
    query = WorkOrder.query
    if status:
        query = query.filter_by(status=status)
    if keyword:
        query = query.join(User, WorkOrder.user_id == User.id).filter(
            db.or_(WorkOrder.order_no.like(f'%{keyword}%'), WorkOrder.contact_name.like(f'%{keyword}%'), User.nickname.like(f'%{keyword}%'))
        )
    orders = query.order_by(WorkOrder.created_at.desc()).limit(200).all()
    return jsonify({'orders': [o.to_dict() for o in orders]})

@bp.route('/admin/orders/<int:order_id>', methods=['GET'])
@login_required
def get_order_detail(order_id):
    order = WorkOrder.query.get_or_404(order_id)
    logs = order.status_logs.all()
    return jsonify({'order': order.to_dict(), 'logs': [l.to_dict() for l in logs]})


# ============================================================
#  产品库（销售订单 17~19 CSV 导入格式）
# ============================================================
def _parse_csv_date(s, with_time=False):
    """解析 '2026/7/6' 或 '2026/7/6 10:44:15'"""
    if not s or not str(s).strip():
        return None
    s = str(s).strip()
    for fmt in ('%Y/%m/%d %H:%M:%S', '%Y-%m-%d %H:%M:%S',
                '%Y/%m/%d', '%Y-%m-%d'):
        try:
            d = datetime.strptime(s, fmt)
            if '%H' not in fmt and with_time:
                return None
            return d
        except ValueError:
            continue
    return None


def _coerce_csv_row(row):
    """把 CSV 一行（dict）规范成 Product 字段 dict。
       容错：缺列、空白、非法日期返回 None，不抛异常。"""
    def s(v):
        if v is None:
            return None
        v = str(v).strip()
        return v if v else None

    return {
        'sales_no':         s(row.get('销售单号')),
        'customer_name':    s(row.get('客户名称')),
        'dealer_name':      s(row.get('经销商名称')),
        'dealer_contact':   s(row.get('经销商联系人')),
        'dealer_phone':     s(row.get('经销商电话')),
        'product_no':       s(row.get('产品编号')),
        'product_name':     s(row.get('产品名称')),
        'shipping_address': s(row.get('发货地址')),
        'qr_code':          s(row.get('二维码')),
        'receiver':         s(row.get('收货人')),
        'receiver_phone':   s(row.get('联系电话')),
        'order_date':       _parse_csv_date(row.get('下单日期'), with_time=True),
        'delivery_date':    _parse_csv_date(row.get('交货日期'), with_time=True),
        'production_date':  _parse_csv_date(row.get('生产日期')),
        # 兼容老字段：product_name → model（CSV 没这列就用 product_name）
        'model':            s(row.get('产品名称')),
    }


@bp.route('/admin/products', methods=['GET'])
@login_required
def admin_list_products():
    """产品库列表，支持关键词搜索 + 分页"""
    keyword = request.args.get('keyword', '').strip()
    status = request.args.get('status', '').strip()
    page = max(1, request.args.get('page', default=1, type=int))
    page_size = min(200, max(1, request.args.get('page_size', default=50, type=int)))

    q = Product.query
    if keyword:
        like = f'%{keyword}%'
        from sqlalchemy import or_
        q = q.filter(or_(
            Product.sales_no.like(like),
            Product.qr_code.like(like),
            Product.serial_number.like(like),
            Product.customer_name.like(like),
            Product.product_no.like(like),
            Product.model.like(like),
            Product.product_name.like(like),
        ))
    if status:
        q = q.filter(Product.status == status)

    total = q.count()
    items = q.order_by(Product.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return jsonify({
        'items': [p.to_dict() for p in items],
        'total': total,
        'page': page,
        'page_size': page_size,
    })


@bp.route('/admin/products', methods=['POST'])
@login_required
@role_required('admin', 'operator')
def admin_create_product():
    """单条新建产品记录"""
    data = request.get_json() or {}
    qr = (data.get('qr_code') or '').strip()
    if not qr:
        return jsonify({'error': '缺少二维码 qr_code'}), 400

    # qr_code 唯一
    if Product.query.filter_by(qr_code=qr).first():
        return jsonify({'error': f'二维码 {qr} 已存在'}), 400

    p = Product(
        sales_no=data.get('sales_no'),
        customer_name=data.get('customer_name'),
        dealer_name=data.get('dealer_name'),
        dealer_contact=data.get('dealer_contact'),
        dealer_phone=data.get('dealer_phone'),
        product_no=data.get('product_no'),
        product_name=data.get('product_name') or data.get('model'),
        model=data.get('model') or data.get('product_name'),
        shipping_address=data.get('shipping_address'),
        qr_code=qr,
        receiver=data.get('receiver'),
        receiver_phone=data.get('receiver_phone'),
        order_date=_parse_csv_date(data.get('order_date'), with_time=True),
        delivery_date=_parse_csv_date(data.get('delivery_date'), with_time=True),
        production_date=_parse_csv_date(data.get('production_date')),
        status=data.get('status') or 'active',
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({'message': '创建成功', 'product': p.to_dict()}), 201


@bp.route('/admin/products/<int:product_id>', methods=['DELETE'])
@login_required
@role_required('admin', 'operator')
def admin_delete_product(product_id):
    """删除单条产品记录（同时解除用户绑定 UserProduct）"""
    from app.models.product import UserProduct
    p = Product.query.get_or_404(product_id)
    UserProduct.query.filter_by(product_id=product_id).delete()
    db.session.delete(p)
    db.session.commit()
    return jsonify({'message': '删除成功'})


@bp.route('/admin/products/<int:product_id>', methods=['PUT'])
@login_required
@role_required('admin', 'operator')
def admin_update_product(product_id):
    """更新产品字段"""
    p = Product.query.get_or_404(product_id)
    data = request.get_json() or {}
    updatable = [
        'sales_no', 'customer_name', 'dealer_name', 'dealer_contact',
        'dealer_phone', 'product_no', 'product_name', 'shipping_address',
        'qr_code', 'receiver', 'receiver_phone', 'status',
    ]
    for k in updatable:
        if k in data:
            setattr(p, k, data[k] or None)
    for k in ('order_date', 'delivery_date'):
        if k in data:
            setattr(p, k, _parse_csv_date(data[k], with_time=True))
    if 'production_date' in data:
        p.production_date = _parse_csv_date(data['production_date'])
    db.session.commit()
    return jsonify({'message': '更新成功', 'product': p.to_dict()})


@bp.route('/admin/products/import', methods=['POST'])
@login_required
@role_required('admin', 'operator')
def admin_import_products():
    """从 CSV 文件批量导入产品库。
    上传字段名：file（multipart/form-data）。
    CSV 列名（销售订单 17_19 格式）：
        销售单号,客户名称,经销商名称,经销商联系人,经销商电话,
        产品编号,产品名称,发货地址,二维码,收货人,联系电话,
        下单日期,交货日期,生产日期
    返回：
        { inserted: int, skipped: [{row, qr_code, reason}],
          errors: [{row, reason}], total: int }
    """
    if 'file' not in request.files:
        return jsonify({'error': '请上传 CSV 文件（字段名 file）'}), 400

    f = request.files['file']
    if not f or not f.filename:
        return jsonify({'error': '文件为空'}), 400
    if not f.filename.lower().endswith('.csv'):
        return jsonify({'error': '文件必须是 .csv 格式'}), 400

    raw = f.read()
    # 去掉 UTF-8 BOM
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = raw.decode('gbk', errors='ignore')

    reader = csv.DictReader(io.StringIO(text))
    required_keys = ('销售单号', '二维码')
    if not reader.fieldnames or not any(k in (reader.fieldnames or []) for k in required_keys):
        return jsonify({
            'error': 'CSV 表头缺少必要列（需要 含"销售单号"和"二维码" 的列）',
            'columns_found': reader.fieldnames,
        }), 400

    inserted = 0
    skipped = []
    errors = []
    seen_qr_in_file = set()
    existing_qr = {p.qr_code for p in Product.query.with_entities(Product.qr_code)
                   .filter(Product.qr_code.isnot(None)).all()}

    for idx, row in enumerate(reader, start=2):
        try:
            data = _coerce_csv_row(row)
            qr = data.get('qr_code')
            if not qr:
                errors.append({'row': idx, 'reason': '缺少二维码'})
                continue
            if qr in existing_qr or qr in seen_qr_in_file:
                skipped.append({'row': idx, 'qr_code': qr, 'reason': '二维码重复'})
                continue
            p = Product(**data)
            db.session.add(p)
            db.session.flush()
            seen_qr_in_file.add(qr)
            existing_qr.add(qr)
            inserted += 1
        except Exception as e:
            db.session.rollback()
            errors.append({'row': idx, 'reason': str(e)[:200]})

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'提交失败: {e}'}), 500

    return jsonify({
        'inserted': inserted,
        'skipped': skipped,
        'errors': errors,
        'total': inserted + len(skipped) + len(errors),
        'filename': f.filename,
    })
