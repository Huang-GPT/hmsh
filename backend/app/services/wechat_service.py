import requests
from flask import current_app

class WechatService:
    OAUTH_URL = 'https://open.weixin.qq.com/connect/oauth2/authorize'
    ACCESS_TOKEN_URL = 'https://api.weixin.qq.com/sns/oauth2/access_token'
    USER_INFO_URL = 'https://api.weixin.qq.com/sns/userinfo'
    
    @classmethod
    def get_oauth_url(cls, redirect_uri, state=''):
        app_id = current_app.config['WECHAT_APP_ID']
        params = {
            'appid': app_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'snsapi_userinfo',
            'state': state
        }
        query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        return f"{cls.OAUTH_URL}?{query_string}#wechat_redirect"
    
    @classmethod
    def get_access_token(cls, code):
        app_id = current_app.config['WECHAT_APP_ID']
        app_secret = current_app.config['WECHAT_APP_SECRET']
        
        params = {
            'appid': app_id,
            'secret': app_secret,
            'code': code,
            'grant_type': 'authorization_code'
        }
        resp = requests.get(cls.ACCESS_TOKEN_URL, params=params)
        return resp.json()
    
    @classmethod
    def get_user_info(cls, access_token, openid):
        params = {
            'access_token': access_token,
            'openid': openid,
            'lang': 'zh_CN'
        }
        resp = requests.get(cls.USER_INFO_URL, params=params)
        return resp.json()