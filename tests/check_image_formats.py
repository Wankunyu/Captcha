#!/usr/bin/env python3
"""
检查 captcha_data 目录中的图片文件，验证文件扩展名是否与实际格式匹配
"""

import os
import glob
from pathlib import Path

def detect_image_format(path: str) -> str:
    """基于 magic bytes 检测图片实际格式"""
    try:
        with open(path, "rb") as f:
            header = f.read(12)

        if header[:8] == b'\x89PNG\r\n\x1a\n':
            return "PNG"
        if header[:3] == b'\xff\xd8\xff':
            return "JPEG"
        if header[:6] in (b'GIF87a', b'GIF89a'):
            return "GIF"
        if header[:4] == b'RIFF' and header[8:12] == b'WEBP':
            return "WEBP"
        if header[:2] == b'BM':
            return "BMP"
        if header[:2] in (b'II\x2a\x00', b'MM\x00\x2a'):
            return "TIFF"

        return "UNKNOWN"
    except Exception as e:
        return f"ERROR: {e}"

def main():
    """扫描所有图片文件，检查格式不匹配的情况"""
    captcha_data_root = "./captcha_data"

    if not os.path.exists(captcha_data_root):
        print(f"❌ 目录不存在: {captcha_data_root}")
        return

    print("🔍 扫描图片文件格式...\n")

    mismatches = []
    total_images = 0

    # 扫描所有子目录
    for task_type in os.listdir(captcha_data_root):
        task_dir = os.path.join(captcha_data_root, task_type)
        if not os.path.isdir(task_dir):
            continue

        # 查找所有图片文件
        for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']:
            pattern = os.path.join(task_dir, f"*{ext}")
            for img_path in glob.glob(pattern):
                total_images += 1

                # 获取文件扩展名
                file_ext = Path(img_path).suffix.upper().lstrip('.')
                if file_ext == 'JPG':
                    file_ext = 'JPEG'

                # 检测实际格式
                actual_format = detect_image_format(img_path)

                # 检查是否匹配
                if file_ext != actual_format:
                    mismatches.append({
                        'path': img_path,
                        'declared': file_ext,
                        'actual': actual_format
                    })

    # 输出结果
    print(f"📊 扫描完成：共检查 {total_images} 个图片文件\n")

    if mismatches:
        print(f"⚠️  发现 {len(mismatches)} 个格式不匹配的文件：\n")
        for item in mismatches:
            print(f"  文件: {item['path']}")
            print(f"  扩展名声明: {item['declared']}")
            print(f"  实际格式: {item['actual']}")
            print()

        print("💡 这些文件会导致 Anthropic API 报错：")
        print("   'Image does not match the provided media type'")
        print("\n✅ 已修复 guess_mime() 函数，现在会检测实际格式而非依赖扩展名")
    else:
        print("✅ 所有图片文件格式与扩展名一致！")

if __name__ == "__main__":
    main()
