import requests
from flask import current_app

class NotificationService:
    TEMPLATE_MESSAGE_URL = 'https://api.weixin.qq.com/cgi-bin/message/template/send'
    
    @classmethod
    def get_access_token(cls):
        url = 'https://api.weixin.qq.com/cgi-bin/token'
        params = {
            'grant_type': 'client_credential',
            'appid': current_app.config['WECHAT_APP_ID'],
            'secret': current_app.config['WECHAT_APP_SECRET']
        }
        resp = requests.get(url, params=params)
        data = resp.json()
        return data.get('access_token')
    
    @classmethod
    def send_template_message(cls, openid, template_id, data, url=None):
        access_token = cls.get_access_token()
        
        payload = {
            'touser': openid,
            'template_id': template_id,
            'data': data
        }
        if url:
            payload['url'] = url
        
        resp = requests.post(
            f'{cls.TEMPLATE_MESSAGE_URL}?access_token={access_token}',
            json=payload
        )
        return resp.json()
    
    @classmethod
    def notify_order_status_change(cls, order, new_status, handler_name=None):
        status_text = {
            'pending_assign': '待分配',
            'pending_process': '待处理',
            'processing': '处理中',
            'pending_confirm': '待确认',
            'completed': '已完成',
            'closed': '已关闭'
        }
        
        from app.models.user import User
        user = User.query.get(order.user_id)
        
        template_id = current_app.config.get('WECHAT_TEMPLATE_ORDER_STATUS')
        data = {
            'first': {'value': '您的工单状态已更新'},
            'keyword1': {'value': order.order_no},
            'keyword2': {'value': status_text.get(new_status, new_status)},
            'keyword3': {'value': handler_name or '系统'},
            'remark': {'value': '如有疑问请联系客服'}
        }
        
        return cls.send_template_message(
            openid=user.openid,
            template_id=template_id,
            data=data,
            url=f'{current_app.config.get("FRONTEND_URL")}/order/{order.id}'
        )