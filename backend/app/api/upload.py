"""文件上传接口（行业标准 P0+P1 重构 2026-09）
   - 路径: POST /api/upload/media         (图片 — 工单/用户头像等，独立保存)
   - 路径: POST /api/upload/fault         (常见故障文件 — 兼容老接口，单独写文件不入库)
   - 路径: POST /api/admin/faults/<id>/attachments   (新 — 事务化上传：disk→DB→失败回滚)
   - 路径: GET  /api/admin/faults/<id>/attachments   (列出故障附件)
   - 路径: DELETE /api/admin/faults/<id>/attachments/<att_id>  (软删+清文件)
   - 路径: GET  /api/uploads/<path:filename>          (静态访问)
   - 存储: <UPLOAD_DIR>/<kind>/<yyyy-mm-dd>/<uuid>.<ext>
   - 视频上传已禁用（节省磁盘空间）
"""
import os
import uuid
from datetime import datetime
from flask import request, jsonify, current_app, send_from_directory, g

from app.api import bp
from app import db
from app.services.auth_service import login_required, permission_required
from app.models.common_fault import FaultAttachment, CommonFault


# 允许的图片扩展名（视频格式不允许上传）
ALLOWED_IMAGE = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'}
# 常见故障允许的文档/图片扩展名（PDF + Office 2003/2007 + 图片）
ALLOWED_FAULT = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
# 视频扩展名（仅用于识别拒绝，不要上传）
ALLOWED_VIDEO = {'mp4', 'mov', 'avi', 'mkv', 'webm', '3gp', 'm4v'}

# 单文件大小上限
IMAGE_MAX_SIZE = 10 * 1024 * 1024     # 10MB — 图片
FAULT_MAX_SIZE = 20 * 1024 * 1024     # 20MB — 故障文件（PDF 文档可能较大）


def _ext_ok(filename, allowed):
    if '.' not in filename:
        return False
    return filename.rsplit('.', 1)[1].lower() in allowed


def _upload_base():
    return current_app.config.get('UPLOAD_DIR') or os.path.join(
        os.path.dirname(current_app.root_path), 'uploads'
    )


def _save_path_by_kind(kind, ext):
    """按 kind 生成按日期分目录的存储路径，返回 (rel_path, abs_path)
       kind: 'media' (工单图片) | 'fault' (故障附件) | 其他
    """
    base = _upload_base()
    date_dir = datetime.now().strftime('%Y-%m-%d')
    if kind == 'fault':
        target_dir = os.path.join(base, 'faults', date_dir)
    else:
        target_dir = os.path.join(base, date_dir)
    os.makedirs(target_dir, exist_ok=True)
    fname = f"{uuid.uuid4().hex}.{ext}"
    rel_path = f"{kind}/{date_dir}/{fname}" if kind == 'fault' else f"{date_dir}/{fname}"
    return rel_path, os.path.join(target_dir, fname)


def _infer_kind_and_mime(ext, mimetype):
    """根据扩展名推断 kind + mime；返回 (kind, mime)"""
    mime = mimetype or ''
    ext = ext.lower()
    if ext in ('jpg', 'jpeg'):
        return 'image', mime or 'image/jpeg'
    if ext == 'png':
        return 'image', mime or 'image/png'
    if ext == 'pdf':
        return 'pdf', mime or 'application/pdf'
    if ext == 'doc':
        return 'doc', mime or 'application/msword'
    if ext == 'docx':
        return 'docx', mime or 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    return 'file', mime or 'application/octet-stream'


@bp.route('/upload/media', methods=['POST'])
@login_required
def upload_media():
    """工单/头像图片上传（独立保存，不入库故障附件）"""
    if 'file' not in request.files:
        return jsonify({'error': '请选择文件'}), 400
    f = request.files['file']
    if not f or not f.filename:
        return jsonify({'error': '文件为空'}), 400

    if _ext_ok(f.filename, ALLOWED_VIDEO):
        return jsonify({
            'error': '系统暂不支持视频上传（节省磁盘空间），请改用图片',
        }), 400

    if not _ext_ok(f.filename, ALLOWED_IMAGE):
        return jsonify({
            'error': f'不支持的图片格式，仅允许：{", ".join(sorted(ALLOWED_IMAGE))}',
        }), 400

    f.seek(0, os.SEEK_END)
    size = f.tell()
    f.seek(0)
    if size > IMAGE_MAX_SIZE:
        return jsonify({'error': f'文件超过 {IMAGE_MAX_SIZE // (1024*1024)} MB 限制'}), 400

    ext = f.filename.rsplit('.', 1)[1].lower()
    rel_path, abs_path = _save_path_by_kind('media', ext)
    f.save(abs_path)

    return jsonify({
        'url': f'/uploads/{rel_path}',
        'filename': f.filename,
        'size': size,
        'content_type': f.mimetype or 'image/' + ext,
        'kind': 'image',
    })


@bp.route('/upload/fault', methods=['POST'])
@login_required
@permission_required('fault:edit')
def upload_fault():
    """【兼容老接口】常见故障文件独立上传 — 只写文件不入库
       ⚠️ 新代码请用 POST /api/admin/faults/<id>/attachments（事务化）。
       此接口保留用于「暂存」场景：管理员先上传文件占位，再绑定到具体故障条目。
    """
    if 'file' not in request.files:
        return jsonify({'error': '请选择文件'}), 400
    f = request.files['file']
    if not f or not f.filename:
        return jsonify({'error': '文件为空'}), 400

    if _ext_ok(f.filename, ALLOWED_VIDEO):
        return jsonify({'error': '常见故障不支持视频文件，请改用 PDF / Word / 图片'}), 400

    if not _ext_ok(f.filename, ALLOWED_FAULT):
        return jsonify({'error': f'不支持的文件格式，仅允许：{", ".join(sorted(ALLOWED_FAULT))}'}), 400

    f.seek(0, os.SEEK_END)
    size = f.tell()
    f.seek(0)
    if size > FAULT_MAX_SIZE:
        return jsonify({'error': f'文件超过 {FAULT_MAX_SIZE // (1024*1024)} MB 限制'}), 400

    ext = f.filename.rsplit('.', 1)[1].lower()
    rel_path, abs_path = _save_path_by_kind('fault', ext)
    f.save(abs_path)

    kind, mime = _infer_kind_and_mime(ext, f.mimetype)
    return jsonify({
        'url': f'/uploads/{rel_path}',
        'filename': f.filename,
        'size': size,
        'content_type': mime,
        'kind': kind,
        '_deprecated': '请改用 POST /api/admin/faults/<id>/attachments',
    })


# ========== 新：故障附件事务化 CRUD（行业标准 P0 重构） ==========

@bp.route('/admin/faults/<int:fault_id>/attachments', methods=['POST'])
@login_required
@permission_required('fault:edit')
def create_fault_attachment(fault_id):
    """事务化上传故障附件：disk → DB → 失败自动清孤儿文件"""
    fault = CommonFault.query.get_or_404(fault_id)

    if 'file' not in request.files:
        return jsonify({'error': '请选择文件'}), 400
    f = request.files['file']
    if not f or not f.filename:
        return jsonify({'error': '文件为空'}), 400

    if _ext_ok(f.filename, ALLOWED_VIDEO):
        return jsonify({'error': '常见故障不支持视频文件'}), 400
    if not _ext_ok(f.filename, ALLOWED_FAULT):
        return jsonify({'error': f'不支持的文件格式，仅允许：{", ".join(sorted(ALLOWED_FAULT))}'}), 400

    f.seek(0, os.SEEK_END)
    size = f.tell()
    f.seek(0)
    if size > FAULT_MAX_SIZE:
        return jsonify({'error': f'文件超过 {FAULT_MAX_SIZE // (1024*1024)} MB 限制'}), 400

    ext = f.filename.rsplit('.', 1)[1].lower()
    kind, mime = _infer_kind_and_mime(ext, f.mimetype)

    # 1. 写磁盘
    rel_path, abs_path = _save_path_by_kind('fault', ext)
    try:
        f.save(abs_path)
    except Exception as e:
        return jsonify({'error': f'文件保存失败: {e}'}), 500

    # 2. 写 DB；失败则删磁盘文件回滚
    try:
        att = FaultAttachment(
            fault_id=fault_id,
            filename=f.filename,
            url=f'/uploads/{rel_path}',
            size=size,
            mime=mime,
            kind=kind,
            uploaded_by=getattr(g, 'current_user_id', None),
        )
        db.session.add(att)
        db.session.commit()
    except Exception as e:
        try:
            os.remove(abs_path)
        except OSError:
            pass
        db.session.rollback()
        return jsonify({'error': f'数据库写入失败，文件已清理: {e}'}), 500

    return jsonify({'message': '上传成功', 'attachment': att.to_dict()}), 201


@bp.route('/admin/faults/<int:fault_id>/attachments', methods=['GET'])
@login_required
@permission_required('fault:view')
def list_fault_attachments(fault_id):
    """列出故障的所有附件（含软删；前端可按 deleted_at 过滤）"""
    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
    q = FaultAttachment.query.filter_by(fault_id=fault_id)
    if not include_deleted:
        q = q.filter(FaultAttachment.deleted_at.is_(None))
    rows = q.order_by(FaultAttachment.sort_order, FaultAttachment.id).all()
    return jsonify({'attachments': [a.to_dict() for a in rows]})


@bp.route('/admin/faults/<int:fault_id>/attachments/<int:att_id>', methods=['DELETE'])
@login_required
@permission_required('fault:edit')
def soft_delete_fault_attachment(fault_id, att_id):
    """软删附件（设 deleted_at）；物理删除由 cleanup CLI 在保留期后执行"""
    att = FaultAttachment.query.filter_by(fault_id=fault_id, id=att_id).first_or_404()
    if att.deleted_at is not None:
        return jsonify({'error': '附件已被删除'}), 400
    att.deleted_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': '已删除', 'attachment': att.to_dict()})


@bp.route('/upload/fault/<filename>', methods=['DELETE'])
@login_required
@permission_required('fault:edit')
def delete_fault_file(filename):
    """【兼容老接口】按文件名直接删 faults/ 下的文件（无 DB 关联）
       ⚠️ 新代码请用 DELETE /api/admin/faults/<id>/attachments/<att_id>。
    """
    base = _upload_base()
    if '/' in filename or '\\' in filename or '..' in filename:
        return jsonify({'error': '非法的文件名'}), 400
    abs_path = os.path.join(base, 'faults', filename)
    if not os.path.isfile(abs_path):
        return jsonify({'error': '文件不存在'}), 404
    try:
        os.remove(abs_path)
    except Exception as e:
        return jsonify({'error': f'删除失败: {e}'}), 500
    return jsonify({'message': '已删除', 'filename': filename})


@bp.route('/uploads/<path:filename>', methods=['GET'])
def serve_upload(filename):
    """提供上传文件的公开访问（图片/文档/历史视频）
       注意：系统已不展示视频文件；老视频由 cleanup-videos 清理。
    """
    base = _upload_base()
    return send_from_directory(base, filename, as_attachment=False)


# ========== CLI 工具 ==========

@bp.cli.command('cleanup-videos')
def cleanup_videos():
    """清理 /app/uploads 下的所有视频文件（节省磁盘）"""
    base = _upload_base()
    video_exts = tuple(ALLOWED_VIDEO)
    deleted = 0
    freed = 0
    if not os.path.isdir(base):
        print(f"[cleanup-videos] {base} 不存在，跳过")
        return
    for root, dirs, files in os.walk(base):
        for fn in files:
            if fn.lower().endswith(video_exts):
                fp = os.path.join(root, fn)
                try:
                    sz = os.path.getsize(fp)
                    os.remove(fp)
                    deleted += 1
                    freed += sz
                except Exception as e:
                    print(f"[cleanup-videos] 删除失败: {fp} - {e}")
    print(f"[cleanup-videos] 删除 {deleted} 个视频文件，释放 {freed / 1024 / 1024:.2f} MB")