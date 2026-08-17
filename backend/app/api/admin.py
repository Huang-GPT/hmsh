from flask import request, jsonify, g, Response
from sqlalchemy.orm import joinedload
from app.api import bp
from app.services.auth_service import login_required, role_required, hash_password
from app.models.user import User
from app.models.service_point import ServicePoint, Engineer
from app.models.work_order import WorkOrder
from app.models.common_fault import FaultCategory, CommonFault
from app.models.product import Product
from app.models.system import SystemConfig, LegacyRolePermission
from app.models.rbac import Permission as RbacPermission, Role as RbacRole, RolePermission as RbacRolePermission, UserRole as RbacUserRole
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

    # 校验 service_point_id 必须存在
    sp_id = data.get('service_point_id')
    if sp_id is not None and not ServicePoint.query.get(sp_id):
        return jsonify({'error': '服务点不存在'}), 400

    init_password = data.get('password', '123456')
    user = User(
        openid=data['account'],
        nickname=data['nickname'],
        role=data['role'],
        phone=data.get('phone'),
        password_hash=hash_password(init_password),
        service_point_id=sp_id,
        email=data.get('email'),
        real_name=data.get('real_name'),
        department=data.get('department'),
        remark=data.get('remark'),
        status='active',
    )
    db.session.add(user)
    db.session.flush()
    # 自动按 role 绑同名 RBAC 角色（找不到不阻断）
    rbac_role = RbacRole.query.filter_by(code=data['role']).first()
    if rbac_role:
        db.session.add(RbacUserRole(user_id=user.id, role_id=rbac_role.id))
    # 也支持直接传 rbac_role_ids（多角色）
    for rid in (data.get('rbac_role_ids') or []):
        if rid == (rbac_role.id if rbac_role else None):
            continue
        if RbacRole.query.get(rid):
            db.session.add(RbacUserRole(user_id=user.id, role_id=rid))
    db.session.commit()
    return jsonify({'message': '创建成功', 'user': user.to_dict()})

@bp.route('/admin/users/<int:user_id>', methods=['PUT'])
@login_required
@role_required('admin')
def update_user(user_id):
    """编辑用户（含 email/real_name/department/remark）"""
    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}
    if 'nickname' in data: user.nickname = data['nickname']
    if 'phone' in data: user.phone = data['phone']
    if 'email' in data: user.email = data['email']
    if 'real_name' in data: user.real_name = data['real_name']
    if 'department' in data: user.department = data['department']
    if 'remark' in data: user.remark = data['remark']
    if 'service_point_id' in data: user.service_point_id = data['service_point_id']
    if 'role' in data and data['role'] in ['admin','dispatcher','service_point','engineer','operator','customer']:
        user.role = data['role']
    db.session.commit()
    return jsonify({'message': '更新成功', 'user': user.to_dict()})

@bp.route('/admin/users/<int:user_id>/status', methods=['PUT'])
@login_required
@role_required('admin')
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    user.status = 'disabled' if user.status == 'active' else 'active'
    db.session.commit()
    return jsonify({'message': 'ok', 'status': user.status})

@bp.route('/admin/users/<int:user_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_user(user_id):
    """硬删除用户 — 业务校验：
       1. 不能删除自己
       2. 不能删除最后一个 admin 用户（防止系统无人管理）
       3. 不能删除有工单关联的用户（保留可追溯性）
    """
    user = User.query.get_or_404(user_id)

    # 1. 自我保护
    if hasattr(g, 'user_id') and g.user_id == user_id:
        return jsonify({'error': '不能删除当前登录用户'}), 400

    # 2. 最后一个 admin 保护
    if user.role == 'admin':
        admin_count = User.query.filter_by(role='admin', status='active').count()
        if admin_count <= 1:
            return jsonify({'error': '不能删除唯一的管理员账号，请先创建其他管理员'}), 400

    # 3. 工单关联保护
    order_count = WorkOrder.query.filter_by(user_id=user_id).count()
    if order_count > 0:
        return jsonify({
            'error': f'该用户有 {order_count} 个工单关联，无法删除',
            'order_count': order_count,
        }), 400

    # 4. 执行删除（user_roles 由 cascade='all, delete-orphan' 自动级联）
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': '用户已删除', 'id': user_id})

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


# ========== 服务点维护（admin 增强） ==========
@bp.route('/admin/service-points/all', methods=['GET'])
@login_required
@role_required('admin')
def list_all_service_points():
    """维护页：含禁用，全量返回"""
    points = ServicePoint.query.order_by(ServicePoint.id.asc()).all()
    return jsonify({'items': [p.to_dict() for p in points]})

@bp.route('/admin/service-points/<int:sp_id>/restore', methods=['POST'])
@login_required
@role_required('admin')
def restore_service_point(sp_id):
    sp = ServicePoint.query.get_or_404(sp_id)
    sp.status = 'active'
    db.session.commit()
    return jsonify({'message': '已启用', 'service_point': sp.to_dict()})

@bp.route('/admin/service-points/<int:sp_id>/hard-delete', methods=['DELETE'])
@login_required
@role_required('admin')
def hard_delete_service_point(sp_id):
    """硬删除：检查是否有关联用户/工程师/工单，有则拒绝"""
    sp = ServicePoint.query.get_or_404(sp_id)
    # 关联用户
    if User.query.filter_by(service_point_id=sp_id).count() > 0:
        return jsonify({'error': '该服务点下有用户，无法删除'}), 400
    # 关联工程师
    if Engineer.query.filter_by(service_point_id=sp_id).count() > 0:
        return jsonify({'error': '该服务点下有工程师，无法删除'}), 400
    # 关联工单
    if WorkOrder.query.filter_by(service_point_id=sp_id).count() > 0:
        return jsonify({'error': '该服务点有工单记录，无法删除'}), 400
    db.session.delete(sp)
    db.session.commit()
    return jsonify({'message': '已彻底删除'})

@bp.route('/admin/service-points/import', methods=['POST'])
@login_required
@role_required('admin')
def import_service_points():
    """CSV 导入：列顺序 名称,联系人,联系电话,地区,地址
       第二行起为数据，跳过表头；同名校验：已存在则覆盖更新"""
    if 'file' not in request.files:
        return jsonify({'error': '未上传文件'}), 400
    f = request.files['file']
    raw = f.read()
    # 兼容 utf-8-sig / gbk
    for enc in ('utf-8-sig', 'utf-8', 'gbk', 'gb18030'):
        try:
            text = raw.decode(enc)
            break
        except Exception:
            continue
    else:
        return jsonify({'error': '文件编码不支持'}), 400
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return jsonify({'error': '文件为空'}), 400

    # 跳过表头（若第一行包含"名称"）
    start = 1 if rows and any('名称' in c for c in rows[0]) else 0
    created = 0
    updated = 0
    skipped = 0
    errors = []
    for i, row in enumerate(rows[start:], start=start + 1):
        if not row or not any(c.strip() for c in row):
            continue
        if len(row) < 1 or not row[0].strip():
            errors.append(f'第{i}行：名称为空')
            skipped += 1
            continue
        name = row[0].strip()
        contact_person = (row[1] if len(row) > 1 else '').strip()
        contact_phone  = (row[2] if len(row) > 2 else '').strip()
        region         = (row[3] if len(row) > 3 else '').strip()
        address        = (row[4] if len(row) > 4 else '').strip()
        try:
            sp = ServicePoint.query.filter_by(name=name).first()
            if sp:
                sp.contact_person = contact_person or sp.contact_person
                sp.contact_phone  = contact_phone or sp.contact_phone
                sp.region         = region or sp.region
                sp.address        = address or sp.address
                sp.status = 'active'
                updated += 1
            else:
                sp = ServicePoint(
                    name=name,
                    contact_person=contact_person,
                    contact_phone=contact_phone,
                    region=region,
                    address=address,
                )
                db.session.add(sp)
                created += 1
        except Exception as e:
            errors.append(f'第{i}行：{e}')
            skipped += 1
    db.session.commit()
    return jsonify({
        'message': f'导入完成：新增 {created} 条，更新 {updated} 条，跳过 {skipped} 条',
        'created': created,
        'updated': updated,
        'skipped': skipped,
        'errors': errors[:20],
    })

@bp.route('/admin/service-points/export', methods=['GET'])
@login_required
@role_required('admin')
def export_service_points():
    """导出 CSV：列 名称,联系人,联系电话,地区,地址,状态"""
    points = ServicePoint.query.order_by(ServicePoint.id.asc()).all()
    buf = io.StringIO()
    # 写入 UTF-8 BOM 让 Excel 打开中文不乱码
    writer = csv.writer(buf)
    writer.writerow(['名称', '联系人', '联系电话', '地区', '地址', '状态'])
    for p in points:
        writer.writerow([
            p.name or '',
            p.contact_person or '',
            p.contact_phone or '',
            p.region or '',
            p.address or '',
            '启用' if p.status == 'active' else '停用',
        ])
    csv_text = '﻿' + buf.getvalue()
    filename = 'service_points_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.csv'
    return Response(
        csv_text.encode('utf-8'),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )

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

@bp.route('/admin/orders/<int:order_id>/accept', methods=['POST'])
@login_required
@role_required('admin','dispatcher','operator')
def accept_order(order_id):
    """受理工单：pending_accept → pending_dispatch（转待派单）"""
    order = WorkOrder.query.get_or_404(order_id)
    if order.status != 'pending_accept':
        return jsonify({'error': f'当前状态不能受理: {order.status}'}), 400
    from app.models.work_order import OrderStatusLog
    order.status = 'pending_dispatch'
    log = OrderStatusLog(order_id=order.id, from_status='pending_accept', to_status='pending_dispatch',
                         operator_id=g.current_user_id, operator_name=g.current_user_nickname, remark='受理工单')
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': '受理成功', 'order': order.to_dict()})


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
@role_required('admin','service_point','service_point_admin')
def service_point_orders():
    """经销商视角工单台：service_point 用户按自己服务点过滤，空则全看"""
    user = User.query.get(g.current_user_id)
    is_sp_user = user and user.role in ('service_point', 'service_point_admin')
    if is_sp_user:
        sp_id = user.service_point_id
        # sp_id 为空：透传全量（status 限定在售后台关心的几个）
        if not sp_id:
            orders = WorkOrder.query.filter(
                WorkOrder.service_point_id.isnot(None),
                WorkOrder.status.in_(['dispatched','assigned_engineer','processing'])
            ).order_by(WorkOrder.created_at.asc()).all()
            return jsonify({'orders': [o.to_dict() for o in orders]})
    else:
        sp_id = request.args.get('service_point_id', type=int)
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



# ========== 经销商文本分配工程师 ==========
@bp.route('/admin/orders/<int:order_id>/assign-engineer-text', methods=['POST'])
@login_required
@role_required('service_point')
def assign_engineer_text(order_id):
    order = WorkOrder.query.get_or_404(order_id)
    if order.status != 'dispatched':
        return jsonify({'error': '当前状态不能分配工程师'}), 400
    user = User.query.get(g.current_user_id)
    if not user.service_point_id or order.service_point_id != user.service_point_id:
        return jsonify({'error': '无权操作该工单'}), 403
    data = request.get_json() or {}
    engineer_name = (data.get('engineer_name') or '').strip()
    engineer_phone = (data.get('engineer_phone') or '').strip()
    if not engineer_name or not engineer_phone:
        return jsonify({'error': '请填写工程师姓名和电话'}), 400
    order.assigned_engineer_name = engineer_name
    order.assigned_engineer_phone = engineer_phone
    order.status = 'assigned_engineer'
    from app.models.work_order import OrderStatusLog
    log = OrderStatusLog(order_id=order.id, from_status='dispatched', to_status='assigned_engineer',
                         operator_id=g.current_user_id, operator_name=g.current_user_nickname,
                         remark='指定工程师: ' + engineer_name + ' ' + engineer_phone)
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': '分配成功', 'order': order.to_dict()})
@bp.route('/admin/orders/<int:order_id>/confirm', methods=['POST'])
@login_required
@role_required('admin','dispatcher','operator')
def admin_confirm_order(order_id):
    """管理员代客确认：pending_confirm → completed"""
    order = WorkOrder.query.get_or_404(order_id)
    if order.status != 'pending_confirm':
        return jsonify({'error': f'当前状态不能确认: {order.status}'}), 400
    from app.models.work_order import OrderStatusLog
    data = request.get_json() or {}
    order.status = 'completed'
    log = OrderStatusLog(order_id=order.id, from_status='pending_confirm', to_status='completed',
                         operator_id=g.current_user_id, operator_name=g.current_user_nickname,
                         remark=data.get('remark', '管理员代客确认'))
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': '已确认完成', 'order': order.to_dict()})

# ========== 故障库管理 ==========
@bp.route('/admin/fault-categories', methods=['GET'])
@login_required
def get_fault_categories():
    """后台获取所有故障分类（含已停用），附 fault_count"""
    keyword = request.args.get('keyword', '').strip()
    q = FaultCategory.query
    if keyword:
        q = q.filter(FaultCategory.name.like(f'%{keyword}%'))
    cats = q.order_by(FaultCategory.sort_order, FaultCategory.id).all()
    # 一次聚合查询补全 fault_count
    cat_ids = [c.id for c in cats]
    count_map = {}
    if cat_ids:
        from sqlalchemy import func
        rows = (db.session.query(CommonFault.category_id, func.count(CommonFault.id))
                .filter(CommonFault.category_id.in_(cat_ids))
                .group_by(CommonFault.category_id).all())
        count_map = {cid: cnt for cid, cnt in rows}
    items = []
    for c in cats:
        d = c.to_dict()
        d['fault_count'] = int(count_map.get(c.id, 0))
        items.append(d)
    return jsonify({'categories': items})

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
        product_model=data.get('product_model'), images=data.get('images'),
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
    for k in ['category_id','title','content','product_model','images','sort_order','status']:
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
    page = max(1, request.args.get('page', default=1, type=int))
    page_size = min(200, max(1, request.args.get('page_size', default=30, type=int)))

    query = WorkOrder.query
    if status:
        # 支持逗号分隔多状态
        statuses = [s.strip() for s in status.split(',') if s.strip()]
        if len(statuses) == 1:
            query = query.filter(WorkOrder.status == statuses[0])
        elif len(statuses) > 1:
            query = query.filter(WorkOrder.status.in_(statuses))
    if keyword:
        like = f'%{keyword}%'
        query = query.join(User, WorkOrder.user_id == User.id).filter(
            db.or_(
                WorkOrder.order_no.like(like),
                WorkOrder.contact_name.like(like),
                WorkOrder.contact_phone.like(like),
                WorkOrder.fault_type.like(like),
                WorkOrder.fault_desc.like(like),
                User.nickname.like(like),
                User.phone.like(like),
            )
        )

    total = query.count()
    orders = (query.order_by(WorkOrder.created_at.desc())
              .options(joinedload(WorkOrder.product))
              .offset((page - 1) * page_size).limit(page_size).all())

    # KPI 统计
    kpi_rows = (db.session.query(WorkOrder.status, db.func.count(WorkOrder.id))
                .group_by(WorkOrder.status).all())
    kpi = {s: c for s, c in kpi_rows}

    return jsonify({
        'items': [o.to_dict() for o in orders],
        'orders': [o.to_dict() for o in orders],
        'total': total,
        'page': page,
        'page_size': page_size,
        'kpi': kpi,
    })

@bp.route('/admin/orders/<int:order_id>', methods=['GET'])
@login_required
def get_order_detail(order_id):
    order = WorkOrder.query.options(
        joinedload(WorkOrder.user),
        joinedload(WorkOrder.product),
        joinedload(WorkOrder.fault_category),
        joinedload(WorkOrder.service_point),
        joinedload(WorkOrder.engineer),
    ).get_or_404(order_id)
    logs = order.status_logs.all()
    return jsonify({
        'order': order.to_dict(),
        'status_logs': [l.to_dict() for l in logs],
    })


# ============================================================
#  产品库（销售订单 17~19 CSV 导入格式）
# ============================================================
def _parse_csv_date(s):
    """解析 '2026/7/6' 或 '2026/7/6 10:44:15'，返回 datetime 或 None。
       所有日期列都是 DATE/DATETIME，datetime 落到 DATE 列由 MySQL 自动截断时分秒。"""
    if not s or not str(s).strip():
        return None
    s = str(s).strip()
    for fmt in ('%Y/%m/%d %H:%M:%S', '%Y-%m-%d %H:%M:%S',
                '%Y/%m/%d', '%Y-%m-%d'):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _parse_int(v):
    """把任意输入尽量转成整数，转不动返回 None。用于 SAP 行项目号。"""
    if v is None or v == '':
        return None
    try:
        return int(str(v).strip())
    except (ValueError, TypeError):
        return None


def _coerce_csv_row(row):
    """把 CSV 一行（dict）规范成 Product 字段 dict。
       容错：缺列、空白、非法日期返回 None，不抛异常。
       表头兼容中文（用户友好）和英文（DB 列名）。"""
    def s(v):
        if v is None:
            return None
        v = str(v).strip()
        return v if v else None

    # pick(*keys) — 多个表头任选其一（向后兼容老 CSV 表头）
    def pick(*keys):
        for k in keys:
            v = row.get(k)
            if v is not None and str(v).strip():
                return s(v)
        return None

    sales_no_val = pick('销售单号', 'sales_no')
    return {
        'sales_no':         sales_no_val,
        # 销售单号同时写到 sap_order_no，兼容历史绑定端点查询
        'sap_order_no':     sales_no_val,
        'sap_line_item':    _parse_int(pick('行项目', 'sap_line_item')),
        'customer_name':    pick('客户名称', 'customer_name'),
        'dealer_name':      pick('经销商名称', 'dealer_name'),
        'dealer_contact':   pick('经销商联系人', 'dealer_contact'),
        'dealer_phone':     pick('经销商电话', 'dealer_phone'),
        'product_no':       pick('产品编号', 'product_no'),
        'product_name':     pick('产品名称', 'product_name'),
        'shipping_address': pick('发货地址', 'shipping_address'),
        'qr_code':          pick('二维码', 'qr_code'),
        'receiver':         pick('收货人', 'receiver'),
        'receiver_phone':   pick('联系电话', 'receiver_phone'),
        'order_date':       _parse_csv_date(pick('下单日期', 'order_date')),
        'delivery_date':    _parse_csv_date(pick('交货日期', 'delivery_date')),
        'production_date':  _parse_csv_date(pick('生产日期', 'production_date')),
        'activation_date':  _parse_csv_date(pick('激活日期', 'activation_date', '保修日期', 'warranty_date')),
        'expiry_date':      _parse_csv_date(pick('截至日期', 'expiry_date')),
        # 兼容老字段：product_name → model（CSV 没这列就用 product_name）
        'model':            pick('产品名称', 'product_name'),
    }


@bp.route('/admin/products', methods=['GET'])
@login_required
def admin_list_products():
    """产品库列表，支持关键词搜索 + 分页 + 绑定统计"""
    from app.models.product import UserProduct
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

    # 一次聚合查询补全已绑定计数（避免 N+1）
    item_ids = [p.id for p in items]
    count_map = {}
    if item_ids:
        from sqlalchemy import func
        rows = (db.session.query(UserProduct.product_id, func.count(UserProduct.id))
                .filter(UserProduct.product_id.in_(item_ids))
                .group_by(UserProduct.product_id).all())
        count_map = {pid: cnt for pid, cnt in rows}

    serialized = []
    for p in items:
        d = p.to_dict()
        d['bound_count'] = int(count_map.get(p.id, 0))
        serialized.append(d)

    return jsonify({
        'items': serialized,
        'total': total,
        'page': page,
        'page_size': page_size,
    })


@bp.route('/admin/products/<int:product_id>/bindings', methods=['GET'])
@login_required
def admin_product_bindings(product_id):
    """单个产品的全部绑定用户列表（手机号 + 昵称 + 绑定时间 + 方式）"""
    from app.models.product import UserProduct
    from app.models.user import User
    p = Product.query.get_or_404(product_id)
    ups = (UserProduct.query.filter_by(product_id=product_id)
           .order_by(UserProduct.bind_time.desc()).all())
    bindings = []
    for up in ups:
        u = User.query.get(up.user_id)
        bindings.append({
            'user_id': up.user_id,
            'phone': u.phone if u else None,
            'nickname': u.nickname if u else None,
            'bind_time': up.bind_time.isoformat() if up.bind_time else None,
            'bind_method': up.bind_method,
            'binding_id': up.id,
        })
    return jsonify({
        'product': p.to_dict(),
        'bindings': bindings,
        'bound_count': len(bindings),
    })


@bp.route('/admin/bindings', methods=['GET'])
@login_required
def admin_list_bindings():
    """所有用户绑定记录列表（管理后台总览用）
       支持按 qr_code / phone / bind_method 过滤"""
    from app.models.product import UserProduct
    from app.models.user import User
    keyword = request.args.get('keyword', '').strip()
    method = request.args.get('method', '').strip()
    page = max(1, request.args.get('page', default=1, type=int))
    page_size = min(200, max(1, request.args.get('page_size', default=50, type=int)))

    q = UserProduct.query.join(Product, UserProduct.product_id == Product.id)
    if keyword:
        like = f'%{keyword}%'
        from sqlalchemy import or_
        q = q.join(User, UserProduct.user_id == User.id).filter(or_(
            Product.qr_code.like(like),
            Product.sales_no.like(like),
            Product.product_name.like(like),
            User.phone.like(like),
            User.nickname.like(like),
        ))
    if method:
        q = q.filter(UserProduct.bind_method == method)

    total = q.count()
    items = (q.order_by(UserProduct.bind_time.desc())
             .offset((page - 1) * page_size).limit(page_size).all())

    serialized = []
    for up in items:
        u = User.query.get(up.user_id)
        p = Product.query.get(up.product_id)
        serialized.append({
            'binding_id': up.id,
            'bind_time': up.bind_time.isoformat() if up.bind_time else None,
            'bind_method': up.bind_method,
            'user_id': up.user_id,
            'phone': u.phone if u else None,
            'nickname': u.nickname if u else None,
            'user_status': u.status if u else None,
            'product_id': up.product_id,
            'qr_code': p.qr_code if p else None,
            'sales_no': p.sales_no if p else None,
            'product_name': p.product_name if p else (p.model if p else None),
            'production_date': p.production_date.isoformat() if (p and p.production_date) else None,
        })

    return jsonify({
        'items': serialized,
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

    try:
        # qr_code 唯一（可能因表缺列抛异常，放 try 里）
        exists = Product.query.filter_by(qr_code=qr).first()
        if exists:
            return jsonify({'error': f'二维码 {qr} 已存在'}), 400

        p = Product(
            sales_no=data.get('sales_no'),
            # 销售单号同时填到 sap_order_no（兼容历史绑定端点查询）
            sap_order_no=data.get('sap_order_no') or data.get('sales_no'),
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
            order_date=_parse_csv_date(data.get('order_date')),
            delivery_date=_parse_csv_date(data.get('delivery_date')),
            production_date=_parse_csv_date(data.get('production_date')),
            sap_line_item=_parse_int(data.get('sap_line_item')),
            activation_date=_parse_csv_date(data.get('activation_date')),
            expiry_date=_parse_csv_date(data.get('expiry_date')),
            status=data.get('status') or 'active',
        )
        db.session.add(p)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': '写入失败',
            'detail': str(e)[:500],
            'hint': '服务器跑: docker exec hongmen-db mysql -uroot -phongmen123 '
                    'hongmen_after_sales -e "ALTER TABLE products ADD COLUMN '
                    'sales_no VARCHAR(32)" …（补全所有新字段）'
        }), 500
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
            v = data[k] or None
            setattr(p, k, v)
            # 编辑时改 sales_no 同步到 sap_order_no（绑定查询需要）
            if k == 'sales_no' and v:
                p.sap_order_no = v
    for k in ('order_date', 'delivery_date', 'activation_date', 'expiry_date'):
        if k in data:
            setattr(p, k, _parse_csv_date(data[k]))
    if 'production_date' in data:
        p.production_date = _parse_csv_date(data['production_date'])
    if 'sap_line_item' in data:
        p.sap_line_item = _parse_int(data['sap_line_item'])
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


@bp.route('/admin/bindings/<int:binding_id>', methods=['DELETE'])
@login_required
@role_required('admin', 'operator')
def admin_unbind(binding_id):
    """管理员强制解绑单条用户绑定记录"""
    from app.models.product import UserProduct
    up = UserProduct.query.get_or_404(binding_id)
    product_id = up.product_id
    user_id = up.user_id
    UserProduct.query.filter_by(id=binding_id).delete()
    db.session.commit()
    return jsonify({
        'message': '解绑成功',
        'unbound': {'user_id': user_id, 'product_id': product_id, 'binding_id': binding_id},
    })

# ========== 角色权限管理 ==========
@bp.route('/admin/role-permissions', methods=['GET'])
@login_required
@role_required('admin')
def get_role_permissions():
    roles = LegacyRolePermission.query.all()
    return jsonify({'items': [r.to_dict() for r in roles]})

@bp.route('/admin/role-permissions/<string:role>', methods=['PUT'])
@login_required
@role_required('admin')
def update_role_permissions(role):
    valid_roles = ['admin','dispatcher','service_point','engineer','operator','customer']
    if role not in valid_roles: return jsonify({'error': '无效角色'}), 400
    data = request.get_json(); permissions = data.get('permissions', [])
    rp = LegacyRolePermission.query.filter_by(role=role).first()
    if rp: rp.permissions = permissions
    else:
        rp = LegacyRolePermission(role=role, permissions=permissions); db.session.add(rp)
    db.session.commit()
    return jsonify({'message': '权限已更新', 'role': role, 'permissions': permissions})

@bp.route('/admin/users/<int:user_id>/permissions', methods=['PUT'])
@login_required
@role_required('admin')
def update_user_permissions(user_id):
    user = User.query.get_or_404(user_id)
    user.permissions = request.get_json().get('permissions', [])
    db.session.commit()
    return jsonify({'message': '权限已更新', 'user_id': user_id, 'permissions': user.permissions})
@bp.route('/dealer/orders/<int:order_id>/accept', methods=['POST'])
@login_required
@role_required('service_point', 'admin', 'dispatcher')
def dealer_accept_order(order_id):
    """经销商接单（dispatched → processing 一步完成）

    流程：总部 dispatch 把工单派给某个 service_point 后，
    经销商用户登录进入"工单服务"，点击接单按钮，
    填写工程师姓名 + 电话，一次提交后工单状态直接进入 processing。
    """
    order = WorkOrder.query.get_or_404(order_id)
    if order.status != 'dispatched':
        return jsonify({'error': f'当前状态({order.status})不能接单'}), 400

    user = User.query.get(g.current_user_id)
    if user.role == 'service_point':
        if not user.service_point_id or order.service_point_id != user.service_point_id:
            return jsonify({'error': '无权操作该工单'}), 403
    elif user.role not in ('admin', 'dispatcher'):
        return jsonify({'error': '无接单权限'}), 403

    data = request.get_json() or {}
    engineer_name = (data.get('engineer_name') or '').strip()
    engineer_phone = (data.get('engineer_phone') or '').strip()
    if not engineer_name:
        return jsonify({'error': '请填写工程师姓名'}), 400
    if not engineer_phone or not engineer_phone.isdigit() or len(engineer_phone) < 7:
        return jsonify({'error': '请填写正确的工程师电话（至少 7 位数字）'}), 400

    from app.models.work_order import OrderStatusLog
    order.assigned_engineer_name = engineer_name
    order.assigned_engineer_phone = engineer_phone
    order.status = 'processing'

    log = OrderStatusLog(
        order_id=order.id,
        from_status='dispatched',
        to_status='processing',
        operator_id=g.current_user_id,
        operator_name=g.current_user_nickname,
        remark='经销商接单，工程师: ' + engineer_name + ' ' + engineer_phone
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        'message': '接单成功，工单已进入处理中',
        'order': order.to_dict()
    })


@bp.route('/admin/dealer-orders', methods=['GET'])
@login_required
@role_required('admin', 'dispatcher', 'service_point', 'service_point_admin')
def admin_dealer_orders():
    """总部视角：查看所有经销商（service_point）的工单售后

    可选 query: service_point_id / status
    返回每个工单关联的 service_point_name + assigned_engineer 信息

    权限规则：
    - admin / dispatcher：默认看到全部，可选 service_point_id 过滤
    - service_point / service_point_admin：
        当前用户有 service_point_id → 强制只看到自己服务点的工单
        当前用户 service_point_id 为空 → 看到全部
    """
    me = User.query.get(g.current_user_id)
    me_role = (me.role if me else '') or ''
    sp_id = request.args.get('service_point_id', type=int)
    status = request.args.get('status')

    # 服务点用户：强制按自己服务点过滤（空就全看）
    is_sp_user = me_role in ('service_point', 'service_point_admin')
    if is_sp_user and me and me.service_point_id:
        sp_id = me.service_point_id

    query = WorkOrder.query.options(
        joinedload(WorkOrder.service_point),
    ).filter(WorkOrder.service_point_id.isnot(None))

    if sp_id:
        query = query.filter(WorkOrder.service_point_id == sp_id)
    if status:
        statuses = [s.strip() for s in status.split(',') if s.strip()]
        if len(statuses) == 1:
            query = query.filter(WorkOrder.status == statuses[0])
        elif len(statuses) > 1:
            query = query.filter(WorkOrder.status.in_(statuses))

    orders = query.order_by(WorkOrder.created_at.desc()).limit(500).all()
    return jsonify({'orders': [o.to_dict() for o in orders]})


# ========== RBAC：权限管理 ==========
@bp.route('/admin/permissions', methods=['GET'])
@login_required
@role_required('admin')
def list_permissions():
    """列出所有权限（按 module 分组排序）"""
    perms = RbacPermission.query.order_by(RbacPermission.sort_order, RbacPermission.id).all()
    # 按模块分组
    grouped = {}
    for p in perms:
        grouped.setdefault(p.module, []).append(p.to_dict())
    return jsonify({
        'items': [p.to_dict() for p in perms],
        'grouped': grouped,
        'modules': [
            {'code': m, 'label': MODULE_LABELS.get(m, m), 'count': len(items)}
            for m, items in grouped.items()
        ],
    })


# ========== RBAC：角色管理 ==========
MODULE_LABELS = {
    'dashboard': '工作台',
    'order': '工单管理',
    'dealer_order': '工单售后',
    'user': '用户管理',
    'role': '角色权限',
    'product': '产品管理',
    'binding': '绑定记录',
    'fault': '故障库',
    'service_point': '服务点',
    'statistics': '数据统计',
    'system': '系统设置',
}


@bp.route('/admin/roles', methods=['GET'])
@login_required
@role_required('admin')
def list_roles():
    """列出所有角色（含 permission_ids）"""
    roles = RbacRole.query.order_by(RbacRole.sort_order, RbacRole.id).all()
    return jsonify({'items': [r.to_dict(include_permissions=False) for r in roles]})


@bp.route('/admin/roles/<int:role_id>', methods=['GET'])
@login_required
@role_required('admin')
def get_role(role_id):
    """角色详情（含完整权限列表）"""
    role = RbacRole.query.get_or_404(role_id)
    return jsonify(role.to_dict(include_permissions=True))


@bp.route('/admin/roles', methods=['POST'])
@login_required
@role_required('admin')
def create_role():
    """新建角色"""
    data = request.get_json() or {}
    if not data.get('code') or not data.get('name'):
        return jsonify({'error': '编码和名称必填'}), 400
    if RbacRole.query.filter_by(code=data['code']).first():
        return jsonify({'error': '角色编码已存在'}), 400

    role = RbacRole(
        code=data['code'],
        name=data['name'],
        description=data.get('description', ''),
        builtin=False,
        sort_order=data.get('sort_order', 99),
        status=data.get('status', 'active'),
    )
    db.session.add(role)
    db.session.flush()

    # 设置权限
    permission_ids = data.get('permission_ids', [])
    for pid in permission_ids:
        if RbacRolePermission.query.get(pid):
            db.session.add(RbacRolePermission(role_id=role.id, permission_id=pid))
    db.session.commit()
    return jsonify({'message': '角色创建成功', 'role': role.to_dict(include_permissions=True)})


@bp.route('/admin/roles/<int:role_id>', methods=['PUT'])
@login_required
@role_required('admin')
def update_role(role_id):
    """更新角色（含权限）"""
    role = RbacRole.query.get_or_404(role_id)
    data = request.get_json() or {}

    if 'name' in data:
        role.name = data['name']
    if 'description' in data:
        role.description = data['description']
    if 'status' in data and not role.builtin:
        role.status = data['status']
    if 'sort_order' in data:
        role.sort_order = data['sort_order']

    # 更新权限（全量替换）
    if 'permission_ids' in data:
        # 先删后加
        RoleRbacPermission.query.filter_by(role_id=role.id).delete()
        for pid in data['permission_ids']:
            if RbacRolePermission.query.get(pid):
                db.session.add(RbacRolePermission(role_id=role.id, permission_id=pid))

    db.session.commit()
    return jsonify({'message': '角色更新成功', 'role': role.to_dict(include_permissions=True)})


@bp.route('/admin/roles/<int:role_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_role(role_id):
    """删除角色（内置角色保护）"""
    role = RbacRole.query.get_or_404(role_id)
    if role.builtin:
        return jsonify({'error': '内置角色不可删除'}), 400
    # 检查是否还有用户绑定
    if role.user_roles.count() > 0:
        return jsonify({'error': f'还有 {role.user_roles.count()} 个用户绑定此角色，请先解绑'}), 400
    db.session.delete(role)
    db.session.commit()
    return jsonify({'message': '角色已删除', 'id': role_id})


# ========== RBAC：用户角色分配 ==========
@bp.route('/admin/users/<int:user_id>/roles', methods=['GET'])
@login_required
@role_required('admin')
def get_user_roles(user_id):
    """查用户的角色"""
    user = User.query.get_or_404(user_id)
    return jsonify({
        'user_id': user_id,
        'roles': [ur.role.to_dict(include_permissions=False) for ur in user.user_roles],
        'role_ids': [ur.role_id for ur in user.user_roles],
    })


@bp.route('/admin/users/<int:user_id>/roles', methods=['PUT'])
@login_required
@role_required('admin')
def set_user_roles(user_id):
    """设置用户的角色（全量替换）"""
    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}
    role_ids = data.get('role_ids', [])

    # 删除旧绑定
    RbacUserRole.query.filter_by(user_id=user_id).delete()
    # 加新绑定
    for rid in role_ids:
        if RbacRole.query.get(rid):
            db.session.add(RbacUserRole(user_id=user_id, role_id=rid))

    # 同步 user.role 字段（取第一个角色 code 作为主角色）
    if role_ids:
        first_role = RbacRole.query.get(role_ids[0])
        if first_role:
            user.role = first_role.code if first_role.code in ['admin','dispatcher','service_point','engineer','operator','customer'] else user.role

    db.session.commit()
    return jsonify({
        'message': '角色分配成功',
        'user_id': user_id,
        'role_ids': role_ids,
        'roles': [ur.role.to_dict(include_permissions=False) for ur in user.user_roles],
    })
