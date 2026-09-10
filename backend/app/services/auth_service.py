import jwt
import bcrypt
import time
import redis
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
        # P1.1: 主动撤销检查 — admin 改权限后立即让旧 token 失效
        if _is_token_revoked(payload['user_id'], payload.get('iat')):
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


# ========== P1.1: JWT 主动撤销（Redis 版）==========
# 当 admin 修改用户/角色权限时，让该用户的所有现存 JWT 立即失效。
# 做法：在 Redis 记一个 revoked_user:{id} = 撤权时刻；
#       decode_token 时若 token.iat < 撤权时刻则视为无效。
# TTL 默认 = JWT_EXPIRY_HOURS * 3600（自然过期后无需保留）。
# Redis 是临时存储，重启会丢 — 但 JWT 本2 2h 也就过期了，可接受。
_redis_client = None

def _get_redis():
    """懒初始化 Redis 连接；复用 current_app 配置的 REDIS_URL"""
    global _redis_client
    if _redis_client is None:
        url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
        _redis_client = redis.from_url(url, decode_responses=True)
    return _redis_client

def _revoke_user_tokens(user_id, ttl_seconds=None):
    """标记 user 的现存 token 全部失效。下次 decode_token 校验时拒绝。"""
    if ttl_seconds is None:
        ttl_seconds = current_app.config.get('JWT_EXPIRY_HOURS', 2) * 3600
    _get_redis().set(f'revoked_user:{user_id}', int(time.time()), ex=ttl_seconds)

def _revoke_role_tokens(role_id, ttl_seconds=None):
    """角色权限/成员变化时：让该角色下所有现存用户的 token 失效。"""
    from app.models.rbac import UserRole
    for ur in UserRole.query.filter_by(role_id=role_id).all():
        _revoke_user_tokens(ur.user_id, ttl_seconds)

def _is_token_revoked(user_id, token_iat):
    """检查 token 是否被主动撤销。token_iat 早于撤销时刻则视为无效。"""
    if token_iat is None:
        return False
    revoked_at = _get_redis().get(f'revoked_user:{user_id}')
    if revoked_at is None:
        return False
    try:
        return int(token_iat) < int(revoked_at)
    except (TypeError, ValueError):
        return False


# ========== P1.2: /auth/admin/login rate limit（Redis 计数器 + 锁定）==========
# 防暴力破解：5 分钟内同 IP 连续失败 5 次 → 锁定 15 分钟。
ADMIN_LOGIN_WINDOW_SEC = 300     # 失败计数滑动窗口
ADMIN_LOGIN_MAX_FAILS = 5         # 窗口内允许的最大失败次数
ADMIN_LOGIN_LOCK_SEC = 900        # 锁定时长

def _check_admin_login_lock(ip):
    """检查 IP 是否被锁定；True = 已被锁"""
    return _get_redis().get(f'admin_login_lock:{ip}') is not None

def _record_admin_login_failure(ip):
    """记录一次失败；超过阈值则锁定。返回当前失败计数。"""
    r = _get_redis()
    fail_key = f'admin_login_fail:{ip}'
    count = r.incr(fail_key)
    if count == 1:
        r.expire(fail_key, ADMIN_LOGIN_WINDOW_SEC)
    if count >= ADMIN_LOGIN_MAX_FAILS:
        r.set(f'admin_login_lock:{ip}', '1', ex=ADMIN_LOGIN_LOCK_SEC)
        r.delete(fail_key)
        return count
    return count

def _clear_admin_login_failures(ip):
    """登录成功时清空失败计数"""
    _get_redis().delete(f'admin_login_fail:{ip}')


def admin_login_rate_limit(f):
    """装饰器：套在登录视图上 — 锁定检查 + 失败计数 + 锁定触发。
       视图返回 (response, status) 或 response object，本装饰器按 status 判断成败。
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        ip = request.remote_addr or 'unknown'
        # 1) 已锁定 → 直接 429
        if _check_admin_login_lock(ip):
            return jsonify({'error': '登录尝试过多，请稍后再试'}), 429
        # 2) 调登录视图本身
        result = f(*args, **kwargs)
        # 3) 判 status
        if isinstance(result, tuple):
            status = result[1]
        else:
            status = getattr(result, 'status_code', 200)
        # 4) 失败计数 / 成功清零
        if status and int(status) >= 400:
            _record_admin_login_failure(ip)
        elif status and int(status) == 200:
            _clear_admin_login_failures(ip)
        return result
    return wrapped
