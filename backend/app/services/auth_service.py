import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app, g
from app.models.user import User
from app.models.system import TokenBlacklist

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(current_app.config['BCRYPT_LOG_ROUNDS'])).decode('utf-8')

def check_password(password, password_hash):
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def generate_token(user):
    now = datetime.utcnow()
    payload = {
        'user_id': user.id,
        'role': user.role,
        'nickname': user.nickname,
        'iat': now,
        'exp': now + timedelta(hours=current_app.config['JWT_EXPIRY_HOURS']),
        'jti': f"{user.id}_{now.timestamp()}"
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
