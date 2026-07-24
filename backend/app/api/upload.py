"""文件上传接口（图片 / 视频）
   - 路径: POST /api/upload/media
   - 表单: file=<binary>, kind=image|video
   - 返回: { url, filename, size, content_type }
   - 存储: <UPLOAD_DIR>/<yyyy-mm-dd>/<uuid>.<ext>
   - 访问: /uploads/<yyyy-mm-dd>/<uuid>.<ext>
"""
import os
import uuid
from datetime import datetime
from flask import request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename

from app.api import bp
from app.services.auth_service import login_required


# 允许的文件扩展名
ALLOWED_IMAGE = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'}
ALLOWED_VIDEO = {'mp4', 'mov', 'avi', 'mkv', 'webm', '3gp'}


def _ext_ok(filename, allowed):
    if '.' not in filename:
        return False
    return filename.rsplit('.', 1)[1].lower() in allowed


def _save_path(kind, ext):
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

    kind = (request.form.get('kind') or 'image').strip().lower()
    allowed = ALLOWED_VIDEO if kind == 'video' else ALLOWED_IMAGE
    if not _ext_ok(f.filename, allowed):
        return jsonify({
            'error': f'不支持的{kind}格式，仅允许：{", ".join(sorted(allowed))}',
        }), 400

    # 单文件大小限制：图片 10MB / 视频 100MB
    f.seek(0, os.SEEK_END)
    size = f.tell()
    f.seek(0)
    max_size = 100 * 1024 * 1024 if kind == 'video' else 10 * 1024 * 1024
    if size > max_size:
        return jsonify({'error': f'文件超过 {max_size // (1024*1024)} MB 限制'}), 400

    ext = f.filename.rsplit('.', 1)[1].lower()
    rel_path, abs_path = _save_path(kind, ext)
    f.save(abs_path)

    # 公开访问 URL：相对路径，前端拼上 baseURL
    return jsonify({
        'url': f'/uploads/{rel_path}',
        'filename': f.filename,
        'size': size,
        'content_type': f.mimetype or ('video/' + ext if kind == 'video' else 'image/' + ext),
        'kind': kind,
    })


@bp.route('/uploads/<path:filename>', methods=['GET'])
def serve_upload(filename):
    """提供上传文件的公开访问（图片/视频）"""
    base = current_app.config.get('UPLOAD_DIR') or os.path.join(
        os.path.dirname(current_app.root_path), 'uploads'
    )
    return send_from_directory(base, filename, as_attachment=False)