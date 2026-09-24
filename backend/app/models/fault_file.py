"""故障文件库（2026-09 重构 v2：平铺的 PDF/图片/文档库）

设计要点：
- 不依赖 FaultCategory / CommonFault，直接挂附件
- 单文件一行记录；前端平铺展示
- 保留历史数据：旧的 fault_categories / common_faults / common_fault_attachments 表不动
- 仅 UI 不再调用旧表数据
"""
from datetime import datetime
from app import db


class FaultFile(db.Model):
    """故障文件库 v2 — 平铺结构（按用户 2026-09 新需求）

    kind 分类：
    - pdf       PDF 文档
    - image     图片（jpg/jpeg/png/gif/webp/bmp）
    - doc       doc / docx 文档
    """
    __tablename__ = 'fault_files'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(512), nullable=False)
    size = db.Column(db.Integer, nullable=False, default=0)
    mime = db.Column(db.String(128))
    kind = db.Column(db.Enum('pdf', 'image', 'doc'), nullable=False)
    description = db.Column(db.String(500))  # 可选描述
    sort_order = db.Column(db.Integer, default=0)
    status = db.Column(db.Enum('active', 'disabled'), default='active', nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deleted_at = db.Column(db.DateTime)  # 软删；NULL = 可见

    uploader = db.relationship('User', foreign_keys=[uploaded_by])

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'url': self.url,
            'size': self.size,
            'mime': self.mime,
            'kind': self.kind,
            'description': self.description,
            'sort_order': self.sort_order,
            'status': self.status,
            'uploaded_by': self.uploaded_by,
            'uploader_name': self.uploader.nickname if self.uploader else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }