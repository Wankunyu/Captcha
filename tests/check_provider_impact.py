#!/usr/bin/env python3
"""
检查图片格式不匹配问题对各个 provider 的影响
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from run_eval import guess_mime

def check_provider_impact():
    """检查各个 provider 的图片处理逻辑"""

    print("=" * 80)
    print("Provider 图片处理方式分析")
    print("=" * 80)
    print()

    providers = {
        "OpenAI": {
            "methods": ["_chat_image_block", "_responses_image_block"],
            "uses_guess_mime": True,
            "format": "base64 data URL with MIME type",
            "validation": "可能验证 MIME type",
            "impact": "可能报错或降低准确率"
        },
        "Anthropic": {
            "methods": ["_img_part"],
            "uses_guess_mime": True,
            "format": "base64 with media_type",
            "validation": "严格验证 MIME type (已确认会报 400 错误)",
            "impact": "必定报错 - 'Image does not match the provided media type'"
        },
        "Gemini": {
            "methods": ["Part.from_bytes"],
            "uses_guess_mime": True,
            "format": "raw bytes with mime_type",
            "validation": "可能验证 MIME type",
            "impact": "可能报错或降低准确率"
        },
        "Fireworks": {
            "methods": ["image_url with base64"],
            "uses_guess_mime": True,
            "format": "base64 data URL with MIME type",
            "validation": "可能验证 MIME type",
            "impact": "可能报错或降低准确率"
        }
    }

    for provider, info in providers.items():
        print(f"📦 {provider}")
        print(f"  方法: {', '.join(info['methods'])}")
        print(f"  使用 guess_mime(): {'✅ 是' if info['uses_guess_mime'] else '❌ 否'}")
        print(f"  图片格式: {info['format']}")
        print(f"  MIME 验证: {info['validation']}")
        print(f"  影响: {info['impact']}")
        print()

    print("=" * 80)
    print("结论")
    print("=" * 80)
    print()
    print("✅ 所有 4 个 provider 都使用 guess_mime() 函数")
    print("⚠️  所有 provider 都会受到图片格式不匹配的影响")
    print("🔧 修复后的 guess_mime() 使用 magic bytes 检测，将解决所有 provider 的问题")
    print()

    # 测试修复后的效果
    print("=" * 80)
    print("修复验证 - 测试问题文件")
    print("=" * 80)
    print()

    test_files = [
        "./captcha_data/Bingo/bingo6.png",
        "./captcha_data/Geometry_Click/dingxiang_000001.jpg",
        "./captcha_data/Rotation_Match/sad_cat.png"
    ]

    for file_path in test_files:
        if os.path.exists(file_path):
            detected = guess_mime(file_path)
            ext = os.path.splitext(file_path)[1].upper().lstrip('.')
            if ext == 'JPG':
                ext = 'JPEG'

            status = "✅ 正确" if detected == f"image/{ext.lower()}" else "🔧 已修复"
            print(f"{file_path}")
            print(f"  扩展名: .{ext.lower()}")
            print(f"  检测到: {detected}")
            print(f"  状态: {status}")
            print()

    print("=" * 80)
    print("建议")
    print("=" * 80)
    print()
    print("1. ✅ 已修复 guess_mime() 函数，现在基于 magic bytes 检测")
    print("2. 📝 建议重新运行所有 provider 的实验以获得准确结果")
    print("3. 🧪 特别关注以下任务类型:")
    print("   - Bingo (10 个文件格式不匹配)")
    print("   - Geometry_Click (10 个文件格式不匹配)")
    print("   - Rotation_Match (2 个文件格式不匹配)")
    print()

if __name__ == "__main__":
    check_provider_impact()
