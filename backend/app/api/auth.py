from flask import request, jsonify, g, make_response
from app.api import bp
from app import db
from app.services.auth_service import hash_password, check_password, generate_token, login_required, refresh_token
from app.models.user import User

@bp.route('/auth/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    account = data.get('account')
    password = data.get('password')

    if not account or not password:
        return jsonify({'error': '请输入账号和密码'}), 400

    user = User.query.filter_by(openid=account).first()
    if not user:
        return jsonify({'error': '账号不存在'}), 404

    if user.status == 'disabled':
        return jsonify({'error': '账号已禁用'}), 403

    if not user.password_hash:
        return jsonify({'error': '账号未设置密码'}), 400

    if not check_password(password, user.password_hash):
        return jsonify({'error': '密码错误'}), 401

    if user.role not in ['dispatcher','service_point','service_point_admin','engineer','operator','admin']:
        return jsonify({'error': '无管理端权限'}), 403

    token = generate_token(user)
    resp = make_response(jsonify({'user': user.to_dict()}))
    resp.set_cookie('access_token', token, httponly=True, samesite='Lax', max_age=7200)
    resp.headers['Authorization'] = f'Bearer {token}'
    return resp

@bp.route('/auth/bootstrap', methods=['POST'])
def bootstrap():
    admin_exists = User.query.filter_by(role='admin').first()
    if admin_exists:
        return jsonify({'error': '管理员已存在，请使用管理员账号登录'}), 400

    data = request.get_json() or {}
    account = data.get('account', 'admin')
    password = data.get('password', '123456')
    nickname = data.get('nickname', '系统管理员')

    user = User(
        openid=account,
        nickname=nickname,
        password_hash=hash_password(password),
        role='admin',
        status='active'
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': '管理员创建成功', 'account': account})

@bp.route('/auth/customer/login', methods=['POST'])
def customer_login():
    data = request.get_json()
    openid = data.get('openid')
    if not openid:
        return jsonify({'error': 'Missing openid'}), 400

    user = User.query.filter_by(openid=openid).first()
    if not user:
        user = User(openid=openid, nickname=data.get('nickname', '用户'), role='customer')
        from app import db
        db.session.add(user)
        db.session.commit()

    token = generate_token(user)
    resp = make_response(jsonify({'user': user.to_dict()}))
    resp.set_cookie('access_token', token, httponly=True, samesite='Lax', max_age=7200)
    resp.headers['Authorization'] = f'Bearer {token}'
    return resp


@bp.route('/auth/customer/login-by-phone', methods=['POST'])
def customer_login_by_phone():
    """终端手机页面：用手机号登录。自动绑定 User.phone 与现有 user_id 体系。
       第一次登录若 phone 不存在则创建一条 customer 记录（role=customer, phone=X），
       后续绑定通过 user_id 关联到该手机号 —— 同手机号登录即看到自己所有绑定。"""
    from app.models.user import User
    from app import db
    data = request.get_json() or {}
    phone = (data.get('phone') or '').strip()
    if not phone:
        return jsonify({'error': '请输入手机号'}), 400
    if not phone.isdigit() or len(phone) < 7:
        return jsonify({'error': '手机号格式不正确'}), 400

    user = User.query.filter_by(phone=phone).first()
    if not user:
        # 自动创建 customer；openid 字段留空（无微信场景），用 phone 唯一标识
        user = User(
            phone=phone,
            nickname=f'用户{phone[-4:]}',
            role='customer',
        )
        db.session.add(user)
        db.session.commit()
    elif user.status == 'disabled':
        return jsonify({'error': '账号已停用，请联系管理员'}), 403

    token = generate_token(user)
    resp = make_response(jsonify({'token': token, 'user': user.to_dict()}))
    resp.set_cookie('access_token', token, httponly=True, samesite='Lax', max_age=7200)
    resp.headers['Authorization'] = f'Bearer {token}'
    return resp

@bp.route('/auth/refresh', methods=['POST'])
@login_required
def refresh():
    auth_header = request.headers.get('Authorization', '')
    token = auth_header[7:] if auth_header.startswith('Bearer ') else request.cookies.get('access_token')
    new_token = refresh_token(token)
    if not new_token:
        return jsonify({'error': 'refresh failed'}), 401
    resp = make_response(jsonify({'message': 'ok'}))
    resp.set_cookie('access_token', new_token, httponly=True, samesite='Lax', max_age=7200)
    resp.headers['Authorization'] = f'Bearer {new_token}'
    return resp

@bp.route('/auth/logout', methods=['POST'])
@login_required
def logout():
    from app.models.system import TokenBlacklist
    from app import db
    from datetime import datetime
    import jwt
    auth_header = request.headers.get('Authorization', '')
    token = auth_header[7:] if auth_header.startswith('Bearer ') else request.cookies.get('access_token')
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'], options={"verify_exp": False})
        tb = TokenBlacklist(token_jti=payload['jti'], expired_at=datetime.utcfromtimestamp(payload.get('exp', 0)))
        db.session.add(tb)
        db.session.commit()
    except:
        pass
    resp = make_response(jsonify({'message': 'ok'}))
    resp.delete_cookie('access_token')
    return resp

from flask import current_app
