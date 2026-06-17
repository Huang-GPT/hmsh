from datetime import datetime
from app import db

class FaultCategory(db.Model):
    __tablename__ = 'fault_categories'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    parent_id = db.Column(db.Integer, default=0)
    name = db.Column(db.String(50), nullable=False)
    icon = db.Column(db.String(255))
    sort_order = db.Column(db.Integer, default=0)
    status = db.Column(db.Enum('active','disabled'), default='active', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'parent_id': self.parent_id,
            'name': self.name,
            'icon': self.icon,
            'sort_order': self.sort_order,
            'status': self.status,
        }

class CommonFault(db.Model):
    __tablename__ = 'common_faults'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_id = db.Column(db.Integer, db.ForeignKey('fault_categories.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text)
    product_model = db.Column(db.String(64))
    images = db.Column(db.JSON)
    videos = db.Column(db.JSON)
    sort_order = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)
    helpful_count = db.Column(db.Integer, default=0)
    status = db.Column(db.Enum('active','disabled'), default='active', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = db.relationship('FaultCategory', backref='faults')

    def to_dict(self):
        return {
            'id': self.id,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'title': self.title,
            'content': self.content,
            'product_model': self.product_model,
            'images': self.images,
            'videos': self.videos,
            'sort_order': self.sort_order,
            'view_count': self.view_count,
            'helpful_count': self.helpful_count,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
