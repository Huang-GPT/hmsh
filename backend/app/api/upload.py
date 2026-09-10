"""文件上传接口
   - 路径: POST /api/upload/media   (图片，仅 jpg/png/... — 工单/用户头像等)
   - 路径: POST /api/upload/fault   (常见故障文件 — PDF/DOC/DOCX/图片)
   - 表单: file=<binary>
   - 返回: { url, filename, size, content_type, kind }
   - 存储: <UPLOAD_DIR>/<yyyy-mm-dd>/<uuid>.<ext>
   - 访问: /uploads/<yyyy-mm-dd>/<uuid>.<ext>
   - 视频上传已禁用（节省磁盘空间）
"""
import os
import uuid
from datetime import datetime
from flask import request, jsonify, current_app, send_from_directory

from app.api import bp
from app.services.auth_service import login_required, permission_required


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


def _save_path(ext):
    """生成按日期分目录的存储路径，返回 (rel_path, abs_path)"""
    base = current_app.config.get('UPLOAD_DIR') or os.path.join(
        os.path.dirname(current_app.root_path), 'uploads'
    )
    date_dir = datetime.now().strftime('%Y-%m-%d')
    target_dir = os.path.join(base, date_dir)
    os.makedirs(target_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{ext}"
    return f"{date_dir}/{filename}", os.path.join(target_dir, filename)


@bp.route('/upload/media', methods=['POST'])
@login_required
def upload_media():
    if 'file' not in request.files:
        return jsonify({'error': '请选择文件'}), 400
    f = request.files['file']
    if not f or not f.filename:
        return jsonify({'error': '文件为空'}), 400

    # 拒绝所有视频上传（系统不再支持视频功能）
    if _ext_ok(f.filename, ALLOWED_VIDEO):
        return jsonify({
            'error': '系统暂不支持视频上传（节省磁盘空间），请改用图片',
        }), 400

    # 默认按图片处理
    if not _ext_ok(f.filename, ALLOWED_IMAGE):
        return jsonify({
            'error': f'不支持的图片格式，仅允许：{", ".join(sorted(ALLOWED_IMAGE))}',
        }), 400

    # 单文件大小限制：图片 10MB（视频参数已废除）
    f.seek(0, os.SEEK_END)
    size = f.tell()
    f.seek(0)
    if size > IMAGE_MAX_SIZE:
        return jsonify({'error': f'文件超过 {IMAGE_MAX_SIZE // (1024*1024)} MB 限制'}), 400

    ext = f.filename.rsplit('.', 1)[1].lower()
    rel_path, abs_path = _save_path(ext)
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
    """常见故障文件上传 — 后台 AdminFaults 专用
       支持: PDF / DOC (Office 2003) / DOCX (Office 2007) / 图片 (jpg/png/jpeg)
       存储在 <UPLOAD_DIR>/faults/<yyyy-mm-dd>/<uuid>.<ext> 子目录下便于清理。
    """
    if 'file' not in request.files:
        return jsonify({'error': '请选择文件'}), 400
    f = request.files['file']
    if not f or not f.filename:
        return jsonify({'error': '文件为空'}), 400

    # 拒绝视频
    if _ext_ok(f.filename, ALLOWED_VIDEO):
        return jsonify({
            'error': '常见故障不支持视频文件，请改用 PDF / Word / 图片',
        }), 400

    if not _ext_ok(f.filename, ALLOWED_FAULT):
        return jsonify({
            'error': f'不支持的文件格式，仅允许：{", ".join(sorted(ALLOWED_FAULT))}',
        }), 400

    f.seek(0, os.SEEK_END)
    size = f.tell()
    f.seek(0)
    if size > FAULT_MAX_SIZE:
        return jsonify({'error': f'文件超过 {FAULT_MAX_SIZE // (1024*1024)} MB 限制'}), 400

    ext = f.filename.rsplit('.', 1)[1].lower()
    # fault 文件单独放子目录（<UPLOAD_DIR>/faults/<date>/）
    base = current_app.config.get('UPLOAD_DIR') or os.path.join(
        os.path.dirname(current_app.root_path), 'uploads'
    )
    date_dir = datetime.now().strftime('%Y-%m-%d')
    target_dir = os.path.join(base, 'faults', date_dir)
    os.makedirs(target_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{ext}"
    rel_path = f"faults/{date_dir}/{filename}"
    abs_path = os.path.join(target_dir, filename)
    f.save(abs_path)

    # 推断 content_type（手机端据此决定 browser-open vs download）
    mime = f.mimetype or ''
    if ext in ('jpg', 'jpeg'):
        mime = mime or 'image/jpeg'
        kind = 'image'
    elif ext == 'png':
        mime = mime or 'image/png'
        kind = 'image'
    elif ext == 'pdf':
        mime = mime or 'application/pdf'
        kind = 'pdf'
    elif ext == 'doc':
        mime = mime or 'application/msword'
        kind = 'doc'
    elif ext == 'docx':
        mime = mime or 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        kind = 'docx'
    else:
        kind = 'file'

    return jsonify({
        'url': f'/uploads/{rel_path}',
        'filename': f.filename,
        'size': size,
        'content_type': mime,
        'kind': kind,
    })


@bp.route('/upload/fault/<filename>', methods=['DELETE'])
@login_required
@permission_required('fault:edit')
def delete_fault_file(filename):
    """删除已上传的常见故障文件（仅限 faults/ 子目录下）
       防止误删其他上传文件。
    """
    base = current_app.config.get('UPLOAD_DIR') or os.path.join(
        os.path.dirname(current_app.root_path), 'uploads'
    )
    # 路径安全：filename 不允许包含 .. 或 /，避免目录穿越
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
    """提供上传文件的公开访问（图片/视频）
       注意：后端可能仍有历史视频文件，前端已不展示；
       若需彻底删除视频文件，服务器跑 cleanup 脚本
    """
    base = current_app.config.get('UPLOAD_DIR') or os.path.join(
        os.path.dirname(current_app.root_path), 'uploads'
    )
    return send_from_directory(base, filename, as_attachment=False)


# CLI 工具：清理历史视频文件（节省磁盘）
@bp.cli.command('cleanup-videos')
def cleanup_videos():
    """清理 /app/uploads 下的所有视频文件，输出释放空间"""
    from flask import current_app
    base = current_app.config.get('UPLOAD_DIR') or os.path.join(
        os.path.dirname(current_app.root_path), 'uploads'
    )
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