from flask import request, jsonify, current_app
from app.api import bp
from app.services.wechat_service import WechatService
from app.models.user import User
from app import db

@bp.route('/auth/wechat/callback', methods=['GET'])
def wechat_callback():
    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'Missing code parameter'}), 400
    
    token_data = WechatService.get_access_token(code)
    if 'access_token' not in token_data:
        return jsonify({'error': 'Failed to get access token'}), 400
    
    user_info = WechatService.get_user_info(
        token_data['access_token'],
        token_data['openid']
    )
    
    user = User.query.filter_by(openid=user_info['openid']).first()
    if not user:
        user = User(
            openid=user_info['openid'],
            nickname=user_info.get('nickname'),
            avatar=user_info.get('headimgurl')
        )
        db.session.add(user)
        db.session.commit()
    
    return jsonify({
        'user': user.to_dict(),
        'access_token': token_data['access_token']
    })

@bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    openid = data.get('openid')
    
    if not openid:
        return jsonify({'error': 'Missing openid'}), 400
    
    user = User.query.filter_by(openid=openid).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()})