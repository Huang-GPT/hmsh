import uuid
from datetime import datetime
from app import db
from app.models.work_order import WorkOrder, OrderStatusLog
from app.models.user import User

class WorkOrderService:
    
    STATUS_FLOW = {
        'pending_assign': ['pending_process'],
        'pending_process': ['processing', 'pending_assign'],
        'processing': ['pending_confirm', 'pending_process'],
        'pending_confirm': ['completed', 'processing'],
        'completed': ['closed'],
        'closed': []
    }
    
    @classmethod
    def generate_order_no(cls):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = uuid.uuid4().hex[:6].upper()
        return f"WO{timestamp}{random_suffix}"
    
    @classmethod
    def create_work_order(cls, user_id, product_id, fault_type, fault_desc, 
                         contact_name, contact_phone, images=None, expected_time=None):
        order_no = cls.generate_order_no()
        
        order = WorkOrder(
            order_no=order_no,
            user_id=user_id,
            product_id=product_id,
            fault_type=fault_type,
            fault_desc=fault_desc,
            images=images,
            contact_name=contact_name,
            contact_phone=contact_phone,
            expected_time=expected_time,
            status='pending_assign'
        )
        db.session.add(order)
        db.session.commit()
        
        log = OrderStatusLog(
            order_id=order.id,
            from_status=None,
            to_status='pending_assign',
            operator_id=user_id,
            remark='工单创建'
        )
        db.session.add(log)
        db.session.commit()
        
        return order
    
    @classmethod
    def update_order_status(cls, order_id, new_status, operator_id, remark=''):
        order = WorkOrder.query.get(order_id)
        if not order:
            raise ValueError('Work order not found')
        
        if new_status not in cls.STATUS_FLOW.get(order.status, []):
            raise ValueError(f'Cannot transition from {order.status} to {new_status}')
        
        old_status = order.status
        order.status = new_status
        order.updated_at = datetime.utcnow()
        
        if new_status == 'pending_process':
            order.handler_id = operator_id
        
        log = OrderStatusLog(
            order_id=order.id,
            from_status=old_status,
            to_status=new_status,
            operator_id=operator_id,
            remark=remark
        )
        db.session.add(log)
        db.session.commit()
        
        return order
    
    @classmethod
    def get_user_orders(cls, user_id, status=None):
        query = WorkOrder.query.filter_by(user_id=user_id)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(WorkOrder.created_at.desc()).all()
    
    @classmethod
    def get_order_detail(cls, order_id):
        order = WorkOrder.query.get(order_id)
        if not order:
            raise ValueError('Work order not found')
        
        logs = OrderStatusLog.query.filter_by(order_id=order_id)\
            .order_by(OrderStatusLog.created_at.desc()).all()
        
        return {
            'order': order.to_dict(),
            'logs': [
                {
                    'from_status': log.from_status,
                    'to_status': log.to_status,
                    'operator': User.query.get(log.operator_id).nickname if log.operator_id else None,
                    'remark': log.remark,
                    'created_at': log.created_at.isoformat()
                }
                for log in logs
            ]
        }
    
    @classmethod
    def assign_order(cls, order_id, handler_id):
        return cls.update_order_status(order_id, 'pending_process', handler_id, '工单分配')
    
    @classmethod
    def start_processing(cls, order_id, handler_id):
        return cls.update_order_status(order_id, 'processing', handler_id, '开始处理')
    
    @classmethod
    def complete_processing(cls, order_id, handler_id, remark='处理完成'):
        return cls.update_order_status(order_id, 'pending_confirm', handler_id, remark)
    
    @classmethod
    def confirm_completion(cls, order_id, user_id, remark='客户确认'):
        return cls.update_order_status(order_id, 'completed', user_id, remark)
    
    @classmethod
    def close_order(cls, order_id, user_id, remark='工单关闭'):
        return cls.update_order_status(order_id, 'closed', user_id, remark)