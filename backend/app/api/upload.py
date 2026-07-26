"""文件上传接口（仅图片）
   - 路径: POST /api/upload/media
   - 表单: file=<binary>, kind=image
   - 返回: { url, filename, size, content_type }
   - 存储: <UPLOAD_DIR>/<yyyy-mm-dd>/<uuid>.<ext>
   - 访问: /uploads/<yyyy-mm-dd>/<uuid>.<ext>
   - 视频上传已禁用（节省磁盘空间）
"""
import os
import uuid
from datetime import datetime
from flask import request, jsonify, current_app, send_from_directory

from app.api import bp
from app.services.auth_service import login_required


# 允许的图片扩展名（视频格式不允许上传）
ALLOWED_IMAGE = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'}
# 视频扩展名（仅用于识别拒绝，不要上传）
ALLOWED_VIDEO = {'mp4', 'mov', 'avi', 'mkv', 'webm', '3gp', 'm4v'}


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
    max_size = 10 * 1024 * 1024
    if size > max_size:
        return jsonify({'error': f'文件超过 {max_size // (1024*1024)} MB 限制'}), 400

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