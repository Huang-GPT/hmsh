from datetime import datetime
from app import db

# 关联表：故障-标签 many-to-many
common_fault_tag_map = db.Table(
    'common_fault_tag_map',
    db.Column('fault_id', db.Integer, db.ForeignKey('common_faults.id', ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('common_fault_tags.id', ondelete='CASCADE'), primary_key=True),
)


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
    """故障附件（行业标准 P0+P1 重构 2026-09）
    独立于 common_faults，支持事务化上传 + 审计 + 软删。
    """
    __tablename__ = 'common_fault_attachments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fault_id = db.Column(db.Integer, db.ForeignKey('common_faults.id', ondelete='CASCADE'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(512), nullable=False)
    size = db.Column(db.Integer, nullable=False, default=0)
    mime = db.Column(db.String(128))
    kind = db.Column(db.Enum('pdf', 'doc', 'docx', 'image', 'file'), nullable=False, default='file')
    uploaded_by = db.Column(db.Integer)  # user_id
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
            'uploaded_by': self.uploaded_by,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'sort_order': self.sort_order,
        }


class FaultRevision(db.Model):
    """故障版本历史（P1 加分项）
    每次 update_fault 自动 snapshot 当前完整数据（含 attachments），便于回溯。
    """
    __tablename__ = 'common_fault_revisions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fault_id = db.Column(db.Integer, db.ForeignKey('common_faults.id', ondelete='CASCADE'), nullable=False)
    version = db.Column(db.Integer, nullable=False)
    snapshot = db.Column(db.JSON, nullable=False)
    change_note = db.Column(db.String(255))
    created_by = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('fault_id', 'version', name='uk_fault_version'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'fault_id': self.fault_id,
            'version': self.version,
            'change_note': self.change_note,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            # snapshot 体较大，默认不返回，前端按需 GET
        }


class FaultTag(db.Model):
    """故障标签字典（P1 加分项）"""
    __tablename__ = 'common_fault_tags'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(50), nullable=False, unique=True)
    color = db.Column(db.String(20), default='#909399')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'color': self.color,
            'created_at': self.created_at.isoformat() if self.created_at else None,
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
    # files: 历史遗留 JSON 字段，重构后由 common_fault_attachments 替代；保留 1-2 周便于回滚
    files = db.Column(db.JSON)
    sort_order = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)
    helpful_count = db.Column(db.Integer, default=0)
    status = db.Column(db.Enum('active','disabled'), default='active', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # 审计字段（P0+P1 新增）
    created_by = db.Column(db.Integer)
    updated_by = db.Column(db.Integer)

    category = db.relationship('FaultCategory', backref='faults')
    # attachments 关系：默认排除软删（deleted_at IS NULL）；admin 后台需要看全部时另写 query
    attachments = db.relationship(
        'FaultAttachment',
        primaryjoin='and_(CommonFault.id==FaultAttachment.fault_id, FaultAttachment.deleted_at.is_(None))',
        order_by='FaultAttachment.sort_order, FaultAttachment.id',
        viewonly=True,
    )
    revisions = db.relationship(
        'FaultRevision',
        backref='fault',
        order_by='FaultRevision.version.desc()',
    )
    tags = db.relationship(
        'FaultTag',
        secondary=common_fault_tag_map,
        backref=db.backref('faults', lazy='dynamic'),
    )

    def to_dict(self, with_attachments=True, with_tags=False):
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
            'created_by': self.created_by,
            'updated_by': self.updated_by,
        }
        if with_attachments:
            d['attachments'] = [a.to_dict() for a in self.attachments]
        if with_tags:
            d['tags'] = [t.to_dict() for t in self.tags]
        return d
