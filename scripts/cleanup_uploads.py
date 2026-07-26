#!/usr/bin/env python3
"""清理 /app/uploads 下的历史视频文件（节省磁盘空间）

用法（服务器上）：
    # 1) 复制进容器
    docker cp scripts/cleanup_uploads.py hongmen-backend:/tmp/

    # 2) 在容器内执行（按日期目录遍历，删除所有视频扩展名）
    docker exec hongmen-backend python /tmp/cleanup_uploads.py

    # 3) 也可以查看占用而不删除：
    docker exec hongmen-backend python /tmp/cleanup_uploads.py --dry-run
"""
import os
import sys
import argparse

VIDEO_EXTS = ('.mp4', '.mov', '.avi', '.mkv', '.webm', '.3gp', '.m4v', '.flv', '.wmv', '.ts', '.rmvb')


def find_uploads_dir():
    """智能寻找 uploads 目录"""
    candidates = [
        '/app/uploads',
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app', 'uploads'),
        os.path.join(os.getcwd(), 'uploads'),
    ]
    for c in candidates:
        if os.path.isdir(c):
            return c
    return None


def human_size(n):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024:
            return f'{n:.2f} {unit}'
        n /= 1024
    return f'{n:.2f} TB'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true', help='只统计，不删除')
    ap.add_argument('--dir', help='自定义 uploads 目录')
    args = ap.parse_args()

    base = args.dir or find_uploads_dir()
    if not base:
        print(f'[ERROR] 找不到 uploads 目录（可 --dir 指定）')
        sys.exit(1)
    print(f'[INFO] 扫描目录: {base}')

    total_files = 0
    total_size = 0
    by_ext = {}

    if not os.path.isdir(base):
        print(f'[ERROR] {base} 不存在或不是目录')
        sys.exit(1)

    to_delete = []
    for root, _dirs, files in os.walk(base):
        for fn in files:
            if not fn.lower().endswith(VIDEO_EXTS):
                continue
            fp = os.path.join(root, fn)
            sz = os.path.getsize(fp)
            to_delete.append((fp, sz))
            total_files += 1
            total_size += sz
            ext = os.path.splitext(fn)[1].lower()
            by_ext[ext] = by_ext.get(ext, 0) + 1

    print(f'\n[扫描结果] 共发现 {total_files} 个视频文件，总大小 {human_size(total_size)}')
    if by_ext:
        print('  按扩展名:')
        for ext, n in sorted(by_ext.items(), key=lambda x: -x[1]):
            print(f'    {ext}: {n} 个')

    if not to_delete:
        print('\n[OK] 没有视频文件，无需清理')
        return

    if args.dry_run:
        print(f'\n[DRY-RUN] 上面 {total_files} 个文件将不会删除（指定 --dry-run 模式）')
        return

    deleted = 0
    freed = 0
    errors = []
    for fp, sz in to_delete:
        try:
            os.remove(fp)
            deleted += 1
            freed += sz
        except Exception as e:
            errors.append(f'{fp}: {e}')

    print(f'\n[清理结果] 删除 {deleted}/{total_files} 个视频文件')
    print(f'  释放空间: {human_size(freed)}')
    if errors:
        print(f'  失败 {len(errors)} 个:')
        for e in errors[:10]:
            print(f'    {e}')


if __name__ == '__main__':
    main()