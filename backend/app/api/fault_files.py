"""故障文件库 v2 API（2026-09 新增）

端点：
- GET    /api/admin/fault-files           后台列表（按类型筛选 + 搜索）
- POST   /api/admin/fault-files           上传（multipart，单文件）
- DELETE /api/admin/fault-files/<id>      软删
- PATCH  /api/admin/fault-files/<id>      修改描述
- GET    /api/fault-files                 移动端公开列表（无需登录）

文件存储：复用 backend/app/uploads/faults/<yyyy-mm-dd>/<uuid>.<ext>
- 与旧 FaultAttachment 同目录，文件物理共存；但 FaultFile 用独立 URL 路径 /uploads/faults2/<date>/<uuid>.<ext> 区分
"""
import os
import uuid
from datetime import datetime
from flask import request, jsonify, current_app, g

from app.api import bp
from app import db
from app.services.auth_service import login_required, permission_required
from app.models.fault_file import FaultFile
from app.models.user import User


# 允许的扩展名（按 kind 分组）
KIND_BY_EXT = {
    'pdf':  'pdf',
    'jpg':  'image', 'jpeg': 'image', 'png': 'image',
    'gif':  'image', 'webp': 'image', 'bmp': 'image',
    'doc':  'doc',  'docx':  'doc',
}
ALLOWED_EXTS = sorted(KIND_BY_EXT.keys())
FILE_MAX_SIZE = 30 * 1024 * 1024  # 30MB 单文件上限（PDF/文档可能较大）


def _ext_of(filename):
    if '.' not in filename:
        return None
    return filename.rsplit('.', 1)[1].lower()


def _upload_base():
    return current_app.config.get('UPLOAD_DIR') or os.path.join(
        os.path.dirname(current_app.root_path), 'uploads'
    )


def _save_fault_file(filename):
    """保存到 <UPLOAD_DIR>/faults2/<yyyy-mm-dd>/<uuid>.<ext>
    返回 (rel_path, abs_path)
    """
    ext = _ext_of(filename)
    base = _upload_base()
    date_dir = datetime.now().strftime('%Y-%m-%d')
    target_dir = os.path.join(base, 'faults2', date_dir)
    os.makedirs(target_dir, exist_ok=True)
    fname = f"{uuid.uuid4().hex}.{ext}"
    rel = f"faults2/{date_dir}/{fname}"
    return rel, os.path.join(target_dir, fname)


# ========== 后台端点（需登录 + fault:view/edit 权限） ==========

@bp.route('/admin/fault-files', methods=['GET'])
@login_required
@permission_required('fault:view')
def list_admin_fault_files():
    """后台列表（默认排除软删）
    Query: kind=pdf|image|doc (optional), include_deleted=1 (optional), keyword=...
    """
    kind = request.args.get('kind', '').strip()
    include_deleted = request.args.get('include_deleted', '0') == '1'
    keyword = request.args.get('keyword', '').strip()

    q = FaultFile.query
    if not include_deleted:
        q = q.filter(FaultFile.deleted_at.is_(None))
    if kind and kind in ('pdf', 'image', 'doc'):
        q = q.filter(FaultFile.kind == kind)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(
            db.or_(
                FaultFile.filename.like(like),
                FaultFile.description.like(like),
            )
        )

    rows = q.order_by(FaultFile.sort_order, FaultFile.id.desc()).all()
    return jsonify({'files': [r.to_dict() for r in rows], 'total': len(rows)})


@bp.route('/admin/fault-files', methods=['POST'])
@login_required
@permission_required('fault:edit')
def create_admin_fault_file():
    """上传文件 — 事务化：disk → DB → 失败回滚清孤儿"""
    if 'file' not in request.files:
        return jsonify({'error': '请选择文件'}), 400
    f = request.files['file']
    if not f or not f.filename:
        return jsonify({'error': '文件为空'}), 400

    ext = _ext_of(f.filename)
    if not ext or ext not in KIND_BY_EXT:
        return jsonify({
            'error': f'不支持的文件格式，仅允许：{", ".join(ALLOWED_EXTS)}',
        }), 400

    # 大小校验
    f.seek(0, os.SEEK_END)
    size = f.tell()
    f.seek(0)
    if size > FILE_MAX_SIZE:
        return jsonify({
            'error': f'文件超过 {FILE_MAX_SIZE // (1024*1024)} MB 限制',
        }), 400
    if size <= 0:
        return jsonify({'error': '文件为空'}), 400

    kind = KIND_BY_EXT[ext]

    # 描述（可选）
    description = (request.form.get('description') or '').strip()[:500]

    # 1. 写磁盘
    rel_path, abs_path = _save_fault_file(f.filename)
    try:
        f.save(abs_path)
    except Exception as e:
        return jsonify({'error': f'文件保存失败: {e}'}), 500

    # 2. 写 DB；失败则删磁盘文件回滚
    try:
        row = FaultFile(
            filename=f.filename,
            url=f'/uploads/{rel_path}',
            size=size,
            mime=f.mimetype or '',
            kind=kind,
            description=description or None,
            uploaded_by=getattr(g, 'current_user_id', None),
        )
        db.session.add(row)
        db.session.commit()
    except Exception as e:
        try:
            os.remove(abs_path)
        except OSError:
            pass
        db.session.rollback()
        return jsonify({'error': f'数据库写入失败，文件已清理: {e}'}), 500

    return jsonify({'message': '上传成功', 'file': row.to_dict()}), 201


@bp.route('/admin/fault-files/<int:fid>', methods=['DELETE'])
@login_required
@permission_required('fault:edit')
def delete_admin_fault_file(fid):
    """软删（设 deleted_at）；物理清理由 cleanup CLI 处理"""
    row = FaultFile.query.filter_by(id=fid).first_or_404()
    if row.deleted_at is not None:
        return jsonify({'error': '文件已被删除'}), 400
    row.deleted_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': '已删除', 'id': fid})


@bp.route('/admin/fault-files/<int:fid>', methods=['PATCH'])
@login_required
@permission_required('fault:edit')
def update_admin_fault_file(fid):
    """修改描述 / 排序 / 状态（不修改文件名/物理文件）"""
    row = FaultFile.query.filter_by(id=fid).first_or_404()
    if row.deleted_at is not None:
        return jsonify({'error': '文件已被删除'}), 400
    data = request.get_json() or {}
    if 'description' in data:
        row.description = (data.get('description') or '').strip()[:500] or None
    if 'sort_order' in data:
        try:
            row.sort_order = int(data.get('sort_order') or 0)
        except (TypeError, ValueError):
            return jsonify({'error': 'sort_order 必须为整数'}), 400
    if 'status' in data and data['status'] in ('active', 'disabled'):
        row.status = data['status']
    db.session.commit()
    return jsonify({'message': '更新成功', 'file': row.to_dict()})


# ========== 移动端公开端点（无需登录） ==========

@bp.route('/fault-files', methods=['GET'])
def list_public_fault_files():
    """移动端公开列表（仅显示 active + 未软删，按类型可选筛选）"""
    kind = request.args.get('kind', '').strip()

    q = FaultFile.query.filter(
        FaultFile.deleted_at.is_(None),
        FaultFile.status == 'active',
    )
    if kind and kind in ('pdf', 'image', 'doc'):
        q = q.filter(FaultFile.kind == kind)

    rows = q.order_by(FaultFile.sort_order, FaultFile.id.desc()).all()
    return jsonify({'files': [r.to_dict() for r in rows], 'total': len(rows)})