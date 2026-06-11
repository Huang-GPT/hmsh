from datetime import datetime, timedelta
from app import db
from app.models.user import User
from app.models.work_order import WorkOrder

class AdminService:
    
    @classmethod
    def create_user(cls, openid, nickname, role, phone=None):
        existing_user = User.query.filter_by(openid=openid).first()
        if existing_user:
            raise ValueError('User already exists')
        
        user = User(
            openid=openid,
            nickname=nickname,
            role=role,
            phone=phone
        )
        db.session.add(user)
        db.session.commit()
        return user
    
    @classmethod
    def update_user_role(cls, user_id, new_role):
        user = User.query.get(user_id)
        if not user:
            raise ValueError('User not found')
        
        user.role = new_role
        db.session.commit()
        return user
    
    @classmethod
    def get_users_by_role(cls, role):
        return User.query.filter_by(role=role).all()
    
    @classmethod
    def get_statistics(cls):
        total_orders = WorkOrder.query.count()
        pending_orders = WorkOrder.query.filter(
            WorkOrder.status.in_(['pending_assign', 'pending_process', 'processing'])
        ).count()
        completed_orders = WorkOrder.query.filter_by(status='completed').count()
        closed_orders = WorkOrder.query.filter_by(status='closed').count()
        
        today = datetime.now().date()
        today_orders = WorkOrder.query.filter(
            db.func.date(WorkOrder.created_at) == today
        ).count()
        
        week_ago = datetime.now() - timedelta(days=7)
        weekly_orders = WorkOrder.query.filter(
            WorkOrder.created_at >= week_ago
        ).count()
        
        return {
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
            'closed_orders': closed_orders,
            'today_orders': today_orders,
            'weekly_orders': weekly_orders
        }
    
    @classmethod
    def get_order_statistics_by_status(cls):
        stats = db.session.query(
            WorkOrder.status,
            db.func.count(WorkOrder.id)
        ).group_by(WorkOrder.status).all()
        
        return {status: count for status, count in stats}