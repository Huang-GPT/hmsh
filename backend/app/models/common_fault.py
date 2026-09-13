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


class FaultAttachment(db.Model):
    """故障附件（2026-09 重构：files JSON → 独立 attachments 表）
    后台上传，手机端 CommonFaults 页面按分类展示。
    """
    __tablename__ = 'common_fault_attachments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fault_id = db.Column(db.Integer, db.ForeignKey('common_faults.id', ondelete='CASCADE'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(512), nullable=False)
    size = db.Column(db.Integer, nullable=False, default=0)
    mime = db.Column(db.String(128))
    kind = db.Column(db.Enum('pdf', 'doc', 'docx', 'image', 'file'), nullable=False, default='file')
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    sort_order = db.Column(db.Integer, default=0)
    deleted_at = db.Column(db.DateTime)  # 软删；NULL = 可见

    def to_dict(self):
        return {
            'id': self.id,
            'fault_id': self.fault_id,
            'filename': self.filename,
            'url': self.url,
            'size': self.size,
            'mime': self.mime,
            'kind': self.kind,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'sort_order': self.sort_order,
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
    # files: 历史遗留 JSON 字段；重构后由 common_fault_attachments 替代，保留作为冗余备份
    files = db.Column(db.JSON)
    sort_order = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)
    helpful_count = db.Column(db.Integer, default=0)
    status = db.Column(db.Enum('active','disabled'), default='active', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = db.relationship('FaultCategory', backref='faults')
    # attachments 关系：默认排除软删（deleted_at IS NULL）
    attachments = db.relationship(
        'FaultAttachment',
        primaryjoin='and_(CommonFault.id==FaultAttachment.fault_id, FaultAttachment.deleted_at.is_(None))',
        order_by='FaultAttachment.sort_order, FaultAttachment.id',
        viewonly=True,
    )

    def to_dict(self, with_attachments=True):
        d = {
            'id': self.id,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'title': self.title,
            'content': self.content,
            'product_model': self.product_model,
            'images': self.images,
            'files': self.files or [],  # 兼容老前端
            'sort_order': self.sort_order,
            'view_count': self.view_count,
            'helpful_count': self.helpful_count,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if with_attachments:
            d['attachments'] = [a.to_dict() for a in self.attachments]
        return d