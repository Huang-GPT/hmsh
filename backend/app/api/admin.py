from flask import request, jsonify
from app.api import bp
from app.services.admin_service import AdminService

@bp.route('/admin/users', methods=['POST'])
def create_user():
    data = request.get_json()
    required_fields = ['openid', 'nickname', 'role']
    
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing {field}'}), 400
    
    try:
        user = AdminService.create_user(
            openid=data['openid'],
            nickname=data['nickname'],
            role=data['role'],
            phone=data.get('phone')
        )
        return jsonify({
            'message': 'User created',
            'user': user.to_dict()
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/admin/users/<int:user_id>/role', methods=['PUT'])
def update_user_role(user_id):
    data = request.get_json()
    new_role = data.get('role')
    
    if not new_role:
        return jsonify({'error': 'Missing role'}), 400
    
    try:
        user = AdminService.update_user_role(user_id, new_role)
        return jsonify({
            'message': 'Role updated',
            'user': user.to_dict()
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/admin/users', methods=['GET'])
def get_users():
    role = request.args.get('role')
    if role:
        users = AdminService.get_users_by_role(role)
    else:
        from app.models.user import User
        users = User.query.all()
    
    return jsonify({
        'users': [user.to_dict() for user in users]
    })

@bp.route('/admin/statistics', methods=['GET'])
def get_statistics():
    stats = AdminService.get_statistics()
    return jsonify(stats)

@bp.route('/admin/statistics/by-status', methods=['GET'])
def get_statistics_by_status():
    stats = AdminService.get_order_statistics_by_status()
    return jsonify(stats)