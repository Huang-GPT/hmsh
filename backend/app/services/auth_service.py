import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app, g
from app.models.user import User
from app.models.system import TokenBlacklist, LegacyRolePermission

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(current_app.config['BCRYPT_LOG_ROUNDS'])).decode('utf-8')

def check_password(password, password_hash):
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

# ---- RBAC：从 user_roles + role_permissions_v2 + permissions 三表聚合 ----
def get_user_permissions_from_rbac(user):
    """从新 RBAC 表聚合用户的权限 code 列表。
       - 多个角色合并去重
       - role.status='disabled' 的角色忽略
       - permission 不区分 enabled/disabled（seed 时所有 permission 都是有效的）"""
    try:
        codes = set()
        for ur in user.user_roles.all():
            role = ur.role
            if not role or role.status != 'active':
                continue
            for rp in role.role_permissions.all():
                if rp.permission and rp.permission.code:
                    codes.add(rp.permission.code)
        return sorted(codes)
    except Exception as e:
        # RBAC 表未 seed 完 / 关系未建立等情况兜底
        print(f'[rbac] get_user_permissions failed for user {getattr(user, "id", "?")}: {e}')
        return []

def get_role_permissions(role):
    """兼容老入口：现在只走 LegacyRolePermission（旧 JSON 表）。
       新代码请用 get_user_permissions_from_rbac(user)。"""
    rp = LegacyRolePermission.query.filter_by(role=role).first()
    if rp:
        return rp.permissions or []
    return []

def generate_token(user):
    """签发 JWT。permissions 字段优先从 RBAC 表聚合；如果该用户没有任何 RBAC 角色绑定，
       退回 LegacyRolePermission（旧 JSON 表），最后再退回 user.permissions JSON 字段。
       这样既保证新系统生效，又不会让没迁完数据的账号立刻登不进。"""
    now = datetime.utcnow()
    permissions = get_user_permissions_from_rbac(user)
    if not permissions:
        permissions = get_role_permissions(user.role)
    if not permissions and user.permissions:
        permissions = user.permissions
    payload = {
        'user_id': user.id,
        'role': user.role,
        'nickname': user.nickname,
        'permissions': permissions,
        'service_point_id': user.service_point_id,
        'iat': now,
        'exp': now + timedelta(hours=current_app.config['JWT_EXPIRY_HOURS']),
        'jti': str(user.id) + '_' + str(now.timestamp())
    }
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    return token

def decode_token(token):
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        if TokenBlacklist.is_blacklisted(payload.get('jti')):
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
        if not token:
            token = request.cookies.get('access_token')
        if not token:
            return jsonify({'error': '未登录'}), 401
        payload = decode_token(token)
        if not payload:
            return jsonify({'error': '登录已过期'}), 401
        g.current_user_id = payload['user_id']
        g.current_user_role = payload['role']
        g.current_user_nickname = payload.get('nickname')
        g.current_user_permissions = payload.get('permissions', [])
        g.current_user_service_point_id = payload.get('service_point_id')
        g.token_jti = payload['jti']
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if g.current_user_role not in roles:
                return jsonify({'error': '无权限'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if permission not in g.current_user_permissions:
                return jsonify({'error': '无权限'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

def refresh_token(token):
    payload = decode_token(token)
    if not payload:
        return None
    user = User.query.get(payload['user_id'])
    if not user or user.status != 'active':
        return None
    TokenBlacklist(token_jti=payload['jti'], expired_at=datetime.utcfromtimestamp(payload['exp']))
    from app import db
    db.session.commit()
    return generate_token(user)
