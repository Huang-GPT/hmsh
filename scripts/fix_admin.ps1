import re
c = open('C:/hongmen-after-sales/backend/app/api/admin.py', 'r', encoding='utf-8').read()
ep = '''
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

'''
p = c.find(chr(64) + 'bp.route(' + chr(39) + '/admin/orders/<int:order_id>/confirm' + chr(39))
if p > 0:
    c = c[:p] + ep + c[p:]
c = c.replace(chr(64) + " role_required admin dispatcher operator \\ndef admin_confirm_order\, chr(64) + \role_required admin dispatcher operator service_point \\ndef admin_confirm_order\)
a = '''
# ========== 角色权限管理 ==========
@bp.route('/admin/role-permissions', methods=['GET'])
@login_required
@role_required('admin')
def get_role_permissions():
 roles = RolePermission.query.all()
 return jsonify({'items': [r.to_dict() for r in roles]})

@bp.route('/admin/role-permissions/<string:role>', methods=['PUT'])
@login_required
@role_required('admin')
def update_role_permissions(role):
 valid_roles = ['admin','dispatcher','service_point','engineer','operator','customer']
 if role not in valid_roles:
 return jsonify({'error': '无效角色'}), 400
 data = request.get_json()
 permissions = data.get('permissions', [])
 rp = RolePermission.query.filter_by(role=role).first()
 if rp:
 rp.permissions = permissions
 else:
 rp = RolePermission(role=role, permissions=permissions)
 db.session.add(rp)
 db.session.commit()
 return jsonify({'message': '权限已更新', 'role': role, 'permissions': permissions})

@bp.route('/admin/users/<int:user_id>/permissions', methods=['PUT'])
@login_required
@role_required('admin')
def update_user_permissions(user_id):
 user = User.query.get_or_404(user_id)
 data = request.get_json()
 permissions = data.get('permissions', [])
 user.permissions = permissions
 db.session.commit()
 return jsonify({'message': '权限已更新', 'user_id': user_id, 'permissions': permissions})
'''
c += a
open('C:/hongmen-after-sales/backend/app/api/admin.py', 'w', encoding='utf-8').write(c)
print('admin.py done')
