from datetime import datetime
from app import db

class CommonFault(db.Model):
    __tablename__ = 'common_faults'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_model = db.Column(db.String(64), nullable=False, index=True)
    fault_type = db.Column(db.String(32), nullable=False)
    fault_desc = db.Column(db.Text, nullable=False)
    solution = db.Column(db.Text, nullable=False)
    view_count = db.Column(db.Integer, default=0)
    helpful_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_model': self.product_model,
            'fault_type': self.fault_type,
            'fault_desc': self.fault_desc,
            'solution': self.solution,
            'view_count': self.view_count,
            'helpful_count': self.helpful_count,
            'created_at': self.created_at.isoformat()
        }