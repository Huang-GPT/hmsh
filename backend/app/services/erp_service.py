import requests
from flask import current_app

class ErpService:
    
    @classmethod
    def _get_headers(cls):
        return {
            'Authorization': f'Bearer {current_app.config["ERP_API_KEY"]}',
            'Content-Type': 'application/json'
        }
    
    @classmethod
    def verify_product(cls, serial_number):
        url = f'{current_app.config["ERP_API_URL"]}/products/verify'
        params = {'serial_number': serial_number}
        
        try:
            resp = requests.get(url, headers=cls._get_headers(), params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def verify_order(cls, sap_order_no, sap_line_item):
        url = f'{current_app.config["ERP_API_URL"]}/orders/verify'
        params = {
            'order_no': sap_order_no,
            'line_item': sap_line_item
        }
        
        try:
            resp = requests.get(url, headers=cls._get_headers(), params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def sync_products(cls, last_sync_time=None):
        url = f'{current_app.config["ERP_API_URL"]}/products/sync'
        params = {}
        if last_sync_time:
            params['last_sync_time'] = last_sync_time
        
        try:
            resp = requests.get(url, headers=cls._get_headers(), params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def get_product_info(cls, sap_order_no, sap_line_item):
        url = f'{current_app.config["ERP_API_URL"]}/products/info'
        params = {
            'order_no': sap_order_no,
            'line_item': sap_line_item
        }
        
        try:
            resp = requests.get(url, headers=cls._get_headers(), params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            return {'success': False, 'error': str(e)}