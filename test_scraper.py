#!/usr/bin/env python3
"""
Simple test script for TikTok scraper without full dependencies.
Tests basic functionality without LLM integration.
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import List, Dict, Any


class MockComment:
    """Simple mock comment for testing."""

    def __init__(self, comment_id: str, text: str, likes: int = 0):
        self.comment_id = comment_id
        self.text = text
        self.likes = likes
        self.created_at = datetime.now()

    def to_dict(self):
        return {
            "comment_id": self.comment_id,
            "text": self.text,
            "likes": self.likes,
            "created_at": self.created_at.isoformat(),
        }


async def test_douyin_url(url: str):
    """Test parsing Douyin URL."""
    print("=" * 60)
    print("抖音评论爬虫 - 测试脚本")
    print("=" * 60)
    print(f"\n测试URL: {url}")

    # Extract video ID
    if "modal_id=" in url:
        video_id = url.split("modal_id=")[-1].split("&")[0]
        print(f"✓ 视频ID: {video_id}")
    else:
        print("✗ 无法提取视频ID")
        return False

    # Parse user ID
    if "/user/" in url:
        user_id = url.split("/user/")[-1].split("?")[0]
        print(f"✓ 用户ID: {user_id}")

    # Check modal_id parameter
    if "modal_id=" in url:
        print(f"✓ 发现modal_id参数")

    print("\n" + "=" * 60)
    print("依赖检查")
    print("=" * 60)

    dependencies = [
        ("httpx", "HTTP客户端"),
        ("playwright", "浏览器自动化"),
        ("pydantic", "数据验证"),
        ("zai", "Z.ai SDK"),
    ]

    missing = []
    for module, desc in dependencies:
        try:
            __import__(module)
            print(f"✓ {module} - {desc}")
        except ImportError:
            print(f"✗ {module} - {desc} [未安装]")
            missing.append(module)

    if missing:
        print(f"\n⚠ 缺少依赖: {', '.join(missing)}")
        print("\n安装命令:")
        print("python3 -m pip install " + " ".join(missing))
    else:
        print("\n✓ 所有依赖已安装")

    print("\n" + "=" * 60)
    print("模拟爬取结果")
    print("=" * 60)

    # Create mock comments
    mock_comments = [
        MockComment("1", "这个视频太棒了！学到了很多", 128),
        MockComment("2", "博主讲得很清楚，点赞！", 89),
        MockComment("3", "建议下次可以讲得更深入一点", 45),
        MockComment("4", "请问有字幕吗？", 23),
        MockComment("5", "内容很有价值，已分享", 67),
    ]

    print(f"\n模拟爬取到 {len(mock_comments)} 条评论:\n")

    for comment in mock_comments:
        print(f"  [{comment.comment_id}] {comment.text}")
        print(f"       👍 {comment.likes} 点赞\n")

    # Save to file
    output_file = "output/test_results.json"
    import os
    os.makedirs("output", exist_ok=True)

    result = {
        "video_id": video_id,
        "url": url,
        "total_comments": len(mock_comments),
        "comments": [c.to_dict() for c in mock_comments],
        "status": "test_mode",
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("=" * 60)
    print(f"✓ 测试结果已保存到: {output_file}")
    print("=" * 60)

    print("\n下一步:")
    print("1. 安装所有依赖包")
    print("2. 配置Z.ai API密钥")
    print("3. 运行完整爬虫: python3 -m tiktok_comment_scraper.cli <URL>")

    return True


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else None

    if not url:
        print("用法: python3 test_scraper.py <抖音视频URL>")
        print("\n示例URL:")
        print("https://www.douyin.com/user/MS4wLjABAAA...?modal_id=7597795827700487787")
        sys.exit(1)

    try:
        asyncio.run(test_douyin_url(url))
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
